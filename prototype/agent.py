"""The Knowledge Repo Creator agent — the autonomous retrieval engine.

One CrewAI agent with 4 tools. It decides what to search, when to refine, and when
it has enough evidence. OUTPUT MATCHES PRODUCTION: it emits the exact
FinalSupplementProtocol schema (src/aether_2/models.py) so this is a drop-in
middle-layer swap — same input, same output as the existing pipeline.
"""
import os

from crewai import LLM, Agent, Crew, Process, Task

from prototype.tools.kb_search import SearchKBTool
from prototype.tools.patient_context import GetPatientContextTool
from prototype.tools.pubmed import PubMedSearchTool
from prototype.tools.safety import CheckSafetyTool

# Production output schema — reused verbatim so output is identical to the existing pipeline.
from src.aether_2.models import FinalSupplementProtocol

# Prototype LLM: default to Flash (more quota headroom, cheaper, faster — right tier
# for iterating). Override with PROTOTYPE_LLM=vertex_ai/gemini-2.5-pro for prod-grade
# synthesis. num_retries adds backoff against transient 429s.
MODEL = os.environ.get("PROTOTYPE_LLM", "vertex_ai/gemini-2.5-flash")
llm = LLM(model=MODEL, temperature=0, seed=42, num_retries=3)


# ── Agent + task ─────────────────────────────────────────────────────────────
AUTONOMY_BACKSTORY = """\
You are a wellness and longevity research agent — NOT a doctor. You build a personalised
supplement protocol that supports a user's health goals.

You are fully autonomous over retrieval. You decide which tools to call, how to phrase
your queries, when to refine them, and when you have gathered enough evidence. Nothing
is scripted for you.

Operating principles:
- Start from the patient. Their stated goals lead; if absent, infer from biology (high
  focus-area scores, flagged biomarkers) and say you are inferring.
- Use the focus-area REASON breakdowns to target the true driver (e.g. fatigue from low
  ferritin -> iron-relevant search, not a generic 'energy' search).
- COVER THE PATIENT'S ISSUES. Every materially flagged biomarker and high-scoring focus
  area should be addressed by at least one recommendation, unless safety forbids it.
- search_kb is your primary candidate source. Query it repeatedly with refined terms.
- Reach for pubmed_search to confirm/strengthen evidence when the KB is thin.
- Run check_safety on every candidate you keep. Respect its warnings. Do NOT recommend a
  supplement the patient already takes (check current_supplements) unless you are
  explicitly adjusting dose/form — and say so.
- WELLNESS FRAMING IS MANDATORY: "supports healthy glucose metabolism", never "treats
  diabetes". Conditions/meds inform safety only.

=== GROUNDING RULES (NON-NEGOTIABLE) ===
Do NOT invent facts. Hallucination is a critical failure.
1. PATIENT FACTS: Use ONLY the authoritative facts provided and tool outputs. If a
   medication/allergy/condition is not listed, the patient does NOT have it. Never invent
   a lab value; quote flagged biomarker values exactly.
2. EVIDENCE: Base your reasoning on what search_kb / pubmed_search actually returned. Do
   not embellish with facts the tools did not provide.

PubMed query tips: prefer MeSH terms, e.g. ("Coenzyme Q10"[MeSH]) AND ("Fatigue"[MeSH]).
Set reviews_only=true and years_back=5 for strong, recent evidence.
"""


def build_crew(patient_facts_text: str = "") -> Crew:
    agent = Agent(
        role="Knowledge Repo Creator (Wellness Research Agent)",
        goal="Produce a grounded, wellness-framed supplement protocol that covers this "
             "user's flagged issues and health goals, with safe doses and forms.",
        backstory=AUTONOMY_BACKSTORY,
        tools=[
            GetPatientContextTool(),
            SearchKBTool(),
            PubMedSearchTool(),
            CheckSafetyTool(),
        ],
        llm=llm,
        verbose=True,
        max_iter=25,  # bounded autonomy budget
    )

    task = Task(
        description=(
            f"{patient_facts_text}\n"
            "The facts above are authoritative and complete. Do NOT invent or contradict "
            "them — if a medication/allergy/condition is not listed, the patient does not "
            "have it.\n\n"
            "Produce a personalised supplement protocol for this patient.\n\n"
            "1. You ALREADY have the core facts above. Use get_patient_context only to "
            "drill into a focus area's reason breakdown (aspect='focus_area:<CODE>').\n"
            "2. Identify EVERY materially flagged biomarker and high-scoring focus area "
            "that needs support — aim to cover them all.\n"
            "3. Search the knowledge base for supporting ingredients; refine queries as "
            "needed. Use pubmed_search to strengthen weak evidence.\n"
            "4. Run check_safety on each candidate. Drop or adjust anything unsafe, and do "
            "not duplicate a supplement the patient already takes.\n"
            "5. For each recommendation, assign an evidence-based dose (with units and "
            "specific FORM where it matters — e.g. magnesium glycinate, methyl-B12, "
            "vitamin D3 with K2) and optimal timing/frequency.\n\n"
            "Output EXACTLY the FinalSupplementProtocol schema: a 'supplement_"
            "recommendations' list where each item has: ingredient_name, "
            "recommended_dosage, frequency, focus_area (1-2 focus-area CODES like 'CM', "
            "'IMM'), and why. The 'why' must be patient-specific, reference the relevant "
            "flagged biomarker value(s), and use wellness framing — no disease-treatment "
            "language, no citations or internal source names in the text."
        ),
        expected_output=(
            "A FinalSupplementProtocol: {'supplement_recommendations': [{ingredient_name, "
            "recommended_dosage, frequency, focus_area:[CODE,...], why}, ...]} covering "
            "the patient's flagged issues, safety-screened, wellness-framed."
        ),
        output_pydantic=FinalSupplementProtocol,
        agent=agent,
    )

    return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
