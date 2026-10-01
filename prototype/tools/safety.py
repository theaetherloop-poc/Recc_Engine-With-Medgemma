"""check_safety — MINIMAL v0 safety screen for the prototype.

Reads the patient's current meds / diagnoses / allergies / current supplements
from prototype.context.CTX and flags obvious concerns from a tiny curated table.
This is intentionally small — real DrugBank / Natural Medicines data is deferred.
"""
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from prototype import context

# Tiny curated interaction table (supplement -> {meds/conditions of concern}).
# Keyed by lowercased substrings. PROTOTYPE ONLY.
_INTERACTIONS = {
    "vitamin k": {
        "meds": ["warfarin", "coumadin"],
        "note": "Vitamin K antagonises warfarin — caution / avoid without supervision.",
    },
    "vitamin d": {
        "conditions": ["hypercalcemia", "sarcoidosis"],
        "note": "High-dose vitamin D inappropriate with hypercalcemia/sarcoidosis.",
    },
    "potassium": {
        "meds": ["lisinopril", "enalapril", "spironolactone", "ace inhibitor"],
        "conditions": ["kidney disease", "renal"],
        "note": "Potassium + ACE inhibitors / K-sparing diuretics / renal impairment "
                "risks hyperkalemia.",
    },
    "st johns wort": {
        "meds": ["ssri", "sertraline", "fluoxetine"],
        "note": "St John's Wort + SSRIs risks serotonin syndrome and reduces many drug "
                "levels.",
    },
    "iron": {
        "conditions": ["hemochromatosis"],
        "note": "Iron contraindicated in iron-overload conditions.",
    },
    "fish oil": {
        "meds": ["warfarin", "aspirin", "clopidogrel"],
        "note": "High-dose omega-3 + anticoagulants/antiplatelets — additive bleeding "
                "risk.",
    },
}


class SafetyInput(BaseModel):
    supplement: str = Field(..., description="Supplement / ingredient name to screen "
                                             "for this specific patient.")


class CheckSafetyTool(BaseTool):
    name: str = "check_safety"
    description: str = (
        "Screen a candidate supplement against THIS patient's medications, diagnoses, "
        "allergies, and current supplement stack. Returns interaction warnings, "
        "duplication notes, and allergy flags. Call this before finalising any "
        "candidate. (Prototype: covers a small curated set of common interactions.)"
    )
    args_schema: Type[BaseModel] = SafetyInput

    def _run(self, supplement: str) -> str:
        s = (supplement or "").lower()
        sig = context.get("signals", {})
        meds = [m.lower() for m in sig.get("medications", [])]
        conditions = [c.lower() for c in sig.get("diagnoses", [])]
        allergies = [a.lower() for a in sig.get("allergies", [])]
        current = [c.lower() for c in sig.get("current_supplements", [])]

        warnings = []

        for key, rule in _INTERACTIONS.items():
            if key in s or s in key:
                for med in rule.get("meds", []):
                    if any(med in m for m in meds):
                        warnings.append(f"⚠ INTERACTION with medication '{med}': "
                                        f"{rule['note']}")
                for cond in rule.get("conditions", []):
                    if any(cond in c for c in conditions):
                        warnings.append(f"⚠ CONTRAINDICATION with condition '{cond}': "
                                        f"{rule['note']}")

        if any(s in c or c in s for c in current):
            warnings.append("ℹ DUPLICATION: patient already takes this or a close match.")

        for alg in allergies:
            if alg and (alg in s):
                warnings.append(f"⚠ ALLERGY flag: patient reports allergy to '{alg}'.")

        if not warnings:
            return (f"No flags found for '{supplement}' against this patient's profile "
                    f"(prototype curated set). Confirm form/dose downstream.")
        return f"Safety screen for '{supplement}':\n" + "\n".join(warnings)
