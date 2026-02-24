#!/usr/bin/env python3
"""
Must-Cover Template Generator

Generates a simple list of problem avenues that should be covered
by supplement recommendations for a given patient profile.

Usage:
    python scripts/must_cover_generator.py outputs/user_folder/user_profile.json
"""

import json
import sys
import os
from typing import Dict, Any, List


class MustCoverGenerator:
    """Extracts all problem avenues from a patient profile."""

    def __init__(self, profile_data: Dict[str, Any]):
        """Initialize with user_profile.json data."""
        if isinstance(profile_data, list):
            profile_data = profile_data[0]
        if "user_full_data" in profile_data:
            profile_data = profile_data["user_full_data"]

        self.data = profile_data
        self.patient_data = self.data.get("patient_data", {})
        self.phase1 = self.patient_data.get("phase1_basic_intake", {})
        self.phase2 = self.patient_data.get("phase2_detailed_intake", {})
        self.flagged = self.data.get("flagged_biomarkers", [])

        self.biomarker_issues: List[str] = []
        self.other_problems: List[str] = []
        self.safety_constraints: List[str] = []

    def extract_all(self) -> Dict[str, Any]:
        """Extract all problem avenues."""
        self._extract_demographics()
        self._extract_biomarkers()
        self._extract_conditions()
        self._extract_symptoms()
        self._extract_sleep()
        self._extract_dental()
        self._extract_lifestyle()
        self._extract_hormonal()
        self._extract_exposures()
        self._extract_family_history()
        self._extract_childhood()
        self._extract_safety()

        return self._compile_output()

    def _extract_demographics(self):
        demo = self.phase1.get("demographics", {})
        self.age = demo.get("age", 0)
        self.sex = demo.get("biological_sex", "").lower()
        self.email = self.data.get("metadata", {}).get("email", "unknown")

    def _extract_biomarkers(self):
        """Append flagged biomarkers directly."""
        for biomarker in self.flagged:
            name = biomarker.get("name", "")
            status = biomarker.get("category", "").lower()
            if status in ["low", "high", "very low", "very high", "critical"]:
                self.biomarker_issues.append(f"{name} ({status})")

    def _extract_conditions(self):
        """Extract diagnosed conditions."""
        med_history = self.phase1.get("medical_history", {})
        for diagnosis in med_history.get("diagnoses", []):
            if diagnosis and diagnosis.lower() not in ["none", "other"]:
                self.other_problems.append(diagnosis.replace("_", "").strip())

        other = med_history.get("diagnoses_other", "")
        if other:
            self.other_problems.append(other)

    def _extract_symptoms(self):
        """Extract symptoms."""
        pain_skin = self.phase2.get("pain_and_skin_health", {})

        if pain_skin.get("headaches", {}).get("frequent_headaches_migraines"):
            self.other_problems.append("Frequent headaches/migraines")

        if pain_skin.get("chronic_pain", {}).get("has_chronic_pain"):
            self.other_problems.append("Chronic pain")

        if pain_skin.get("skin_health", {}).get("has_skin_issues"):
            self.other_problems.append("Skin issues")

        digestive = self.phase2.get("systems_review", {}).get("digestive_symptoms", "")
        if digestive and digestive.lower() != "none":
            self.other_problems.append(f"Digestive: {digestive}")

    def _extract_sleep(self):
        """Extract sleep issues."""
        sleep = self.phase2.get("sleep_patterns", {})

        if sleep.get("trouble_falling_asleep"):
            self.other_problems.append("Trouble falling asleep")
        if sleep.get("trouble_staying_asleep"):
            self.other_problems.append("Trouble staying asleep")
        if sleep.get("wake_feeling_refreshed") == False:
            self.other_problems.append("Unrefreshing sleep")
        if sleep.get("snoring_sleep_apnea", "").lower() in ["yes", "not_sure"]:
            self.other_problems.append("Possible sleep apnea")

        hours = sleep.get("hours_category", "")
        if hours in ["less_than_5", "5_to_6"]:
            self.other_problems.append("Insufficient sleep")

    def _extract_dental(self):
        """Extract dental issues."""
        dental = self.phase2.get("dental_health", {})
        oral = dental.get("oral_health_issues", {})

        if oral.get("tmj_disorder"):
            self.other_problems.append("TMJ disorder")
        if oral.get("bleeding_gums") or oral.get("gingivitis"):
            self.other_problems.append("Gum disease")
        if oral.get("tooth_pain"):
            self.other_problems.append("Tooth pain")

        other = oral.get("other_dental_work", "")
        if other and other.lower() not in ["no", "none", ""]:
            self.other_problems.append(f"Dental: {other[:50]}")

        work = dental.get("dental_work", {})
        if work.get("root_canals", 0) > 0:
            self.other_problems.append("Root canal(s)")
        if work.get("silver_mercury_fillings", 0) > 0:
            self.other_problems.append("Mercury fillings")

    def _extract_lifestyle(self):
        """Extract lifestyle issues."""
        occupation = self.phase2.get("occupation_wellness", {})
        stress = occupation.get("work_stress_level", 0)
        if stress and int(stress) >= 6:
            self.other_problems.append(f"High stress (level {stress})")

        dietary = self.phase2.get("dietary_habits", {})
        diet_style = dietary.get("diet_style", "")
        if diet_style and diet_style.lower() != "none":
            self.other_problems.append(f"Diet: {diet_style}")

        substances = self.phase2.get("lifestyle_factors", {}).get("recreational_drugs", {})
        if substances.get("uses_substances"):
            self.other_problems.append("Recreational substance use")

        alcohol = self.phase2.get("lifestyle_factors", {}).get("alcohol", {})
        if alcohol.get("frequency", "") in ["daily", "4_6_per_week"]:
            self.other_problems.append("Frequent alcohol use")

    def _extract_hormonal(self):
        """Extract hormonal issues."""
        hormonal = self.phase2.get("reproductive_hormonal_health", {})

        female = hormonal.get("female_specific", {})
        if female:
            if female.get("menstrual_concerns", "").lower() == "yes":
                self.other_problems.append("Menstrual concerns")
            concern = female.get("concern_details", "")
            if concern and any(k in concern.lower() for k in ["menopause", "hot flash", "perimenopause"]):
                self.other_problems.append("Menopause/perimenopause")

        male = hormonal.get("male_specific", {})
        if male and male.get("hormonal_concerns", "").lower() == "yes":
            self.other_problems.append("Male hormonal concerns")

    def _extract_exposures(self):
        """Extract environmental exposures."""
        exposures = self.phase2.get("environmental_exposures", {})
        if exposures.get("mold_exposure"):
            self.other_problems.append("Mold exposure")
        chemicals = exposures.get("chemical_exposures", "")
        if chemicals and chemicals.lower() not in ["none", ""]:
            self.other_problems.append(f"Chemical exposure: {chemicals[:30]}")

    def _extract_family_history(self):
        """Extract family history conditions."""
        family = self.phase2.get("family_medical_history", {})
        if not family.get("has_family_history"):
            return
        conditions = family.get("conditions_detail", {})
        if isinstance(conditions, dict):
            for condition in conditions.keys():
                self.other_problems.append(f"Family history: {condition.replace('_', ' ')}")

    def _extract_childhood(self):
        """Extract childhood factors."""
        if self.phase2.get("childhood_antibiotics", {}).get("took_antibiotics_as_child"):
            self.other_problems.append("Childhood antibiotic use")

    def _extract_safety(self):
        """Extract safety constraints."""
        allergies = self.phase1.get("allergies", {})
        if allergies.get("has_allergies"):
            for allergy in allergies.get("known_allergies", []):
                allergen = allergy.get("allergen") or allergy.get("allergen_other", "")
                if allergen:
                    self.safety_constraints.append(allergen)

        meds = self.phase1.get("medications", {})
        if meds.get("has_medications"):
            for med in meds.get("current_medications", []):
                if med.get("name"):
                    self.safety_constraints.append(f"Med: {med['name']}")

    def _compile_output(self) -> Dict[str, Any]:
        """Compile simple output."""
        # Deduplicate
        biomarkers = list(dict.fromkeys(self.biomarker_issues))
        problems = list(dict.fromkeys(self.other_problems))

        return {
            "patient_id": self.email,
            "age": self.age,
            "sex": self.sex,
            "biomarker_issues": biomarkers,
            "other_problems": problems,
            "safety_constraints": self.safety_constraints,
            "total": len(biomarkers) + len(problems)
        }


def generate_must_cover(input_path: str) -> Dict[str, Any]:
    with open(input_path, 'r') as f:
        data = json.load(f)
    return MustCoverGenerator(data).extract_all()


def print_report(result: Dict[str, Any]):
    print("=" * 60)
    print(f"MUST-COVER: {result['patient_id']} ({result['age']}yo {result['sex']})")
    print("=" * 60)

    print(f"\nBIOMARKER ISSUES ({len(result['biomarker_issues'])})")
    for item in result['biomarker_issues']:
        print(f"  • {item}")

    print(f"\nOTHER PROBLEMS ({len(result['other_problems'])})")
    for item in result['other_problems']:
        print(f"  • {item}")

    if result['safety_constraints']:
        print(f"\nSAFETY CONSTRAINTS ({len(result['safety_constraints'])})")
        for item in result['safety_constraints']:
            print(f"  ⚠ {item}")

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {result['total']} items")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/must_cover_generator.py <user_profile.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    result = generate_must_cover(input_file)
    print_report(result)

    output_file = input_file.replace(".json", "_must_cover.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to: {output_file}")

