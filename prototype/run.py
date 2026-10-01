"""Prototype runner.

Usage:
    python -m prototype.run inputs/test_user3.json
    python -m prototype.run inputs/test_user3.json --goal "live longer, more energy"

Loads a patient JSON, runs the EXISTING rule-based preprocessing, populates the
shared context, then lets the autonomous Knowledge Repo Creator agent build an
Enriched Knowledge Package. Prints the result and saves it under prototype_out/.
"""
import argparse
import json
import os
import re
import sys

# Ensure repo root is importable (so `src.aether_2...` resolves).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402
load_dotenv()  # picks up NCBI_EMAIL / NCBI_API_KEY (and others) from .env

from prototype import context  # noqa: E402
from src.aether_2.utils.data_processing import load_and_combine_inputs  # noqa: E402
from src.aether_2.utils.preprocessing import (  # noqa: E402
    evaluate_biomarkers,
    compile_user_profile,
    evaluate_focus_areas,
)

FOCUS_AREA_NAMES = {
    "CM": "Cardiometabolic & Metabolic Health",
    "STR": "Stress-Axis & Nervous System Resilience",
    "HRM": "Hormonal Health",
    "IMM": "Immune Function & Inflammation",
    "SKN": "Skin & Barrier Function",
    "COG": "Cognitive & Mental Health",
    "MITO": "Mitochondrial & Energy Metabolism",
    "DTX": "Detoxification & Biotransformation",
    "GA": "Gut Health & Assimilation",
}


def parse_focus_scores(markdown: str) -> dict:
    """Robustly parse '(CODE)**: 3.50' style lines.

    NOTE: preprocessing.evaluate_focus_areas() has a parsing bug that returns all
    zeros (it looks for '(CODE):' but the markdown emits '(CODE)**:'). We re-parse
    the markdown here so the prototype gets the real scores.
    """
    scores = {}
    for code, val in re.findall(r"\(([A-Z]+)\)\**:\s*([\d.]+)", markdown):
        scores[code] = float(val)
    return scores


def build_patient_facts(ctx: dict) -> tuple:
    """Build an AUTHORITATIVE, deterministic facts block from preprocessing.

    Core lesson from the experiments: the LLM must NOT be the source of truth for
    patient data. We compute the facts here and inject them; the agent reasons over
    them but may not contradict or invent them.
    Returns (human_readable_text, structured_dict).
    """
    sig = ctx.get("signals", {})
    scores = ctx.get("focus_area_scores", {})
    names = ctx.get("focus_area_names", {})
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)

    facts = {
        "goals": ctx.get("goals") or "(none stated — infer from biology)",
        "demographics": sig.get("demographics", {}),
        "diagnoses": sig.get("diagnoses", []),
        "medications": sig.get("medications", []),
        "current_supplements": sig.get("current_supplements", []),
        "allergies": sig.get("allergies", []),
        "flagged_biomarkers": sig.get("flagged_biomarkers", []),
        "focus_areas_ranked": [
            {"code": c, "name": names.get(c, c), "score": s} for c, s in ranked
        ],
    }

    def _fmt_list(x):
        return ", ".join(map(str, x)) if x else "NONE"

    text = (
        "AUTHORITATIVE PATIENT FACTS (computed from intake + labs — treat as ground "
        "truth; do not contradict or invent):\n"
        f"- Stated goals: {facts['goals']}\n"
        f"- Demographics: {facts['demographics']}\n"
        f"- Diagnoses: {_fmt_list(facts['diagnoses'])}\n"
        f"- Current medications: {_fmt_list(facts['medications'])}\n"
        f"- Current supplements: {_fmt_list(facts['current_supplements'])}\n"
        f"- Allergies: {_fmt_list(facts['allergies'])}\n"
        f"- Flagged biomarkers: {_fmt_list(facts['flagged_biomarkers'])}\n"
        f"- Focus-area scores (high→low): "
        + "; ".join(f"{f['code']}={f['score']}" for f in facts['focus_areas_ranked'])
        + "\n"
    )
    return text, facts


def _names(items, key):
    out = []
    for it in items or []:
        if isinstance(it, dict):
            v = it.get(key) or it.get("name") or it.get("allergen")
            if v:
                out.append(str(v))
        elif it:
            out.append(str(it))
    return out


def extract_signals(combined, biomarker_results):
    pdata = combined["patient_form"]["patient_data"]
    p1 = pdata.get("phase1_basic_intake", {})
    flagged = [
        f"{b.get('name')} = {b.get('value')} {b.get('unit')} ({b.get('category')})"
        for b in biomarker_results.get("flagged_biomarkers", [])
    ]
    return {
        "demographics": p1.get("demographics", {}),
        "diagnoses": _names(p1.get("medical_history", {}).get("diagnoses", []), "name"),
        "medications": _names(
            p1.get("medications", {}).get("current_medications", []), "name"),
        "current_supplements": _names(
            p1.get("supplements", {}).get("current_supplements", []), "name"),
        "allergies": _names(
            p1.get("allergies", {}).get("known_allergies", []), "allergen"),
        "flagged_biomarkers": flagged,
        "lifestyle": pdata.get("phase2_detailed_intake", {}),
    }


def extract_goals(combined, override):
    if override:
        return override
    pdata = combined["patient_form"]["patient_data"]
    questions = pdata.get("phase3_detailed_intake", {}).get("questions", [])
    for q in questions:
        if q.get("id") == "q001" or "health goals" in q.get("question", "").lower():
            return q.get("value")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Path to patient JSON (e.g. inputs/test_user3.json)")
    ap.add_argument("--goal", default=None,
                    help="Override / supply stated goals (since goals move to Phase 2).")
    args = ap.parse_args()

    # Vertex AI config (reuse the existing project; ADC supplies credentials).
    os.environ.setdefault("VERTEX_PROJECT", "singular-object-456719-i6")
    os.environ.setdefault("VERTEX_LOCATION", "us-central1")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "singular-object-456719-i6")
    os.environ.setdefault("LITELLM_LOG", "WARNING")

    print(f"📥 Loading {args.input}")
    combined = load_and_combine_inputs(args.input)

    print("⚙️  Running preprocessing (biomarkers, profile, focus areas)…")
    biomarker_results = evaluate_biomarkers(combined)
    _ = compile_user_profile(combined, biomarker_results)
    focus = evaluate_focus_areas(combined)

    # Parse scores from markdown (preprocessing's parsed scores are buggy — all zeros).
    scores_dict = parse_focus_scores(focus["markdown_output"])
    if not scores_dict:  # fallback to the (possibly zeroed) Pydantic scores
        s = focus["scores"]
        scores_dict = s.model_dump() if hasattr(s, "model_dump") else dict(s)

    ctx = {
        "goals": extract_goals(combined, args.goal),
        "signals": extract_signals(combined, biomarker_results),
        "focus_area_scores": scores_dict,
        "focus_area_reasons": focus.get("reasons_data", {}),
        "focus_area_names": FOCUS_AREA_NAMES,
    }
    context.set_context(ctx)

    print("\n=== PATIENT CONTEXT (what the agent can see) ===")
    print("Goals:", ctx["goals"] or "(none — agent will infer from biology)")
    print("Flagged biomarkers:", ctx["signals"]["flagged_biomarkers"])
    print("Diagnoses:", ctx["signals"]["diagnoses"],
          "| Meds:", ctx["signals"]["medications"])
    ranked = sorted(scores_dict.items(), key=lambda kv: kv[1], reverse=True)
    print("Focus areas (ranked):", ranked)
    print("=" * 50, "\n")

    # Build the authoritative facts block and inject it into the agent.
    patient_facts_text, patient_facts = build_patient_facts(ctx)

    # Import after context is set so tools bind correctly.
    from prototype.agent import build_crew
    crew = build_crew(patient_facts_text)

    print("🤖 Kicking off the autonomous agent…\n")
    result = crew.kickoff()

    # Output matches the production schema EXACTLY (FinalSupplementProtocol):
    # {"supplement_recommendations": [{ingredient_name, recommended_dosage,
    #  frequency, focus_area, why}, ...]} — drop-in middle-layer swap.
    payload = result.pydantic.model_dump() if getattr(result, "pydantic", None) else \
        {"raw": str(result)}

    base = os.path.splitext(os.path.basename(args.input))[0]
    out_dir = os.path.join("prototype_out", base)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "final_supplement_recommendations.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    n = len(payload.get("supplement_recommendations", []))
    print(f"\n✅ Saved final protocol ({n} recommendations) → {out_path}")
    print(json.dumps(payload, indent=2)[:3000])


if __name__ == "__main__":
    main()
