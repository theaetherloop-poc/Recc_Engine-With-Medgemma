"""get_patient_context — exposes the 3 signals to the agent.

Reads from prototype.context.CTX, which run.py populates by running the existing
rule-based preprocessing (biomarker eval + focus-area scoring) on the input JSON.

aspect:
  "signals"          -> flagged biomarkers + meds + diagnoses + allergies + lifestyle
  "goals"            -> the user's stated health goals (free text)
  "focus_areas"      -> all 9 focus-area scores, ranked
  "focus_area:<CODE>"-> one focus area: score + the REASON breakdown (why it's high)
"""
import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from prototype import context


class PatientContextInput(BaseModel):
    aspect: str = Field(
        ...,
        description="One of: 'signals', 'goals', 'focus_areas', or 'focus_area:<CODE>' "
                    "where CODE is one of CM, STR, HRM, IMM, SKN, COG, MITO, DTX, GA.",
    )


class GetPatientContextTool(BaseTool):
    name: str = "get_patient_context"
    description: str = (
        "Retrieve structured facts about THIS patient. Call with aspect='goals' for "
        "their stated health goals, aspect='signals' for flagged biomarkers / meds / "
        "diagnoses / allergies / lifestyle, aspect='focus_areas' for the 9 ranked "
        "health-domain scores, or aspect='focus_area:MITO' (etc.) to see WHY a domain "
        "scored high (the rule breakdown). Use these signals to decide what to search."
    )
    args_schema: Type[BaseModel] = PatientContextInput

    def _run(self, aspect: str) -> str:
        aspect = (aspect or "").strip()

        if aspect == "goals":
            goals = context.get("goals")
            if not goals:
                return ("No explicit goals stated by this user. (The goals question is "
                        "moving to Phase 2; this record predates it.) Infer likely goals "
                        "from the biological signals via aspect='signals' and "
                        "aspect='focus_areas'.")
            return f"Stated health goals:\n{goals}"

        if aspect == "signals":
            return json.dumps(context.get("signals", {}), indent=2, default=str)

        if aspect == "focus_areas":
            scores = context.get("focus_area_scores", {})
            ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            names = context.get("focus_area_names", {})
            lines = ["Focus-area scores (higher = greater biological need):"]
            for code, score in ranked:
                lines.append(f"  {code} ({names.get(code, code)}): {score}")
            return "\n".join(lines)

        if aspect.startswith("focus_area:"):
            code = aspect.split(":", 1)[1].strip().upper()
            scores = context.get("focus_area_scores", {})
            reasons = context.get("focus_area_reasons", {})
            if code not in scores:
                return f"Unknown focus-area code {code!r}. Valid: {list(scores.keys())}"
            payload = {
                "code": code,
                "score": scores.get(code),
                "reasons": reasons.get(code, "no reason breakdown available"),
            }
            return json.dumps(payload, indent=2, default=str)

        return (f"Unrecognized aspect {aspect!r}. Use 'goals', 'signals', "
                f"'focus_areas', or 'focus_area:<CODE>'.")
