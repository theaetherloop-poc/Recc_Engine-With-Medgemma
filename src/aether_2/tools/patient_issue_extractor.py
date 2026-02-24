"""
Patient Issue Extractor Tool

Extracts and prioritizes patient health issues from user_profile JSON.
Creates a condensed, token-efficient representation of patient health data.
"""

from crewai.tools import BaseTool
from typing import Type, Union, Dict, Any, List
from pydantic import BaseModel, Field
import json


class PatientIssueExtractorInput(BaseModel):
    """Input schema for PatientIssueExtractorTool"""
    user_profile: Union[str, dict, None] = Field(
        default=None,
        description="JSON string OR dict containing the user profile."
    )


class PatientIssueExtractorTool(BaseTool):
    """
    Extracts and prioritizes patient health issues from user_profile JSON.
    Returns structured list of biomarkers, conditions, symptoms, allergies,
    exposures, and other health factors.
    """
    name: str = "patient_issue_extractor"
    description: str = (
        "Extracts patient health issues from user profile including flagged biomarkers, "
        "conditions, allergies, symptoms, environmental exposures, and hormonal issues. "
        "Returns a condensed, structured representation for supplement research."
    )
    args_schema: Type[BaseModel] = PatientIssueExtractorInput
    kickoff_inputs: dict = {}

    def _run(self, user_profile: Union[str, dict, None] = None) -> str:
        """Extract patient issues from user_profile JSON."""
        try:
            # Get user_profile from parameter or kickoff_inputs
            if user_profile is None or user_profile == "":
                user_profile = self.kickoff_inputs.get("user_profile")
            
            if not user_profile:
                return json.dumps({"status": "error", "message": "No user_profile provided"})
            
            # Parse input
            if isinstance(user_profile, str):
                user_profile_parsed = json.loads(user_profile)
            else:
                user_profile_parsed = user_profile
            
            # Extract all categories
            demographics = self._extract_demographics(user_profile_parsed)
            biomarkers = self._extract_biomarkers(user_profile_parsed)
            conditions = self._extract_conditions(user_profile_parsed)
            allergies = self._extract_allergies(user_profile_parsed)
            symptoms = self._extract_symptoms(user_profile_parsed)
            digestive = self._extract_digestive_symptoms(user_profile_parsed)
            sleep = self._extract_sleep_issues(user_profile_parsed)
            exposures = self._extract_environmental_exposures(user_profile_parsed)
            hormonal = self._extract_hormonal_issues(user_profile_parsed)
            current_supplements = self._extract_current_supplements(user_profile_parsed)
            lifestyle = self._extract_lifestyle_factors(user_profile_parsed)
            dental = self._extract_dental_health(user_profile_parsed)
            family_history = self._extract_family_history(user_profile_parsed)
            childhood = self._extract_childhood_factors(user_profile_parsed)

            # Count total issues
            total_issues = (
                len(biomarkers) +
                len(conditions) +
                len(allergies) +
                len(symptoms) +
                len(digestive) +
                len(sleep) +
                (1 if exposures.get("mold") else 0) +
                (1 if exposures.get("chemical") else 0) +
                (1 if hormonal else 0) +
                len(dental) +
                len(family_history) +
                (1 if childhood.get("childhood_antibiotics") else 0)
            )

            # Compile response
            response = {
                "status": "success",
                "total_issues": total_issues,
                "demographics": demographics,
                "biomarkers": biomarkers,
                "conditions": conditions,
                "allergies": allergies,
                "symptoms": symptoms,
                "digestive": digestive,
                "sleep_issues": sleep,
                "exposures": exposures,
                "hormonal": hormonal,
                "current_supplements": current_supplements,
                "lifestyle": lifestyle,
                "dental_health": dental,
                "family_history": family_history,
                "childhood_factors": childhood
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Error: {str(e)}"})

    # =========================================================================
    # Demographics
    # =========================================================================
    
    def _extract_demographics(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic demographics (age, sex)"""
        demographics = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("demographics", {})
        
        return {
            "age": demographics.get("age"),
            "sex": demographics.get("biological_sex"),
            "ancestry": demographics.get("ancestry", [])
        }

    # =========================================================================
    # Biomarkers (existing - enhanced)
    # =========================================================================
    
    def _extract_biomarkers(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract flagged biomarkers with high/low status"""
        biomarkers = []
        flagged_biomarkers = user_profile.get("flagged_biomarkers", [])

        for biomarker in flagged_biomarkers:
            name = biomarker.get("name", "")
            category = biomarker.get("category", "").lower()
            value = biomarker.get("value", "")
            unit = biomarker.get("unit", "")

            # Only include high/low biomarkers
            if name and category in ["high", "low", "very high", "very low", "critical"]:
                biomarkers.append({
                    "name": name,
                    "status": category,
                    "value": value,
                    "unit": unit
                })

        return biomarkers

    # =========================================================================
    # Conditions (enhanced to include diagnoses_other)
    # =========================================================================
    
    def _extract_conditions(self, user_profile: Dict[str, Any]) -> List[str]:
        """Extract diagnosed medical conditions including free-text diagnoses"""
        medical_history = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("medical_history", {})
        diagnoses = medical_history.get("diagnoses", [])
        diagnoses_other = medical_history.get("diagnoses_other", "")
        
        # Filter out "none", "other" and empty values
        conditions = [c for c in diagnoses if c and c.lower() not in ["none", "other"]]
        
        # Add free-text diagnosis if present
        if diagnoses_other and diagnoses_other.strip():
            conditions.append(diagnoses_other.strip())
        
        return conditions

    # =========================================================================
    # Allergies (NEW)
    # =========================================================================
    
    def _extract_allergies(self, user_profile: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract known allergies"""
        allergies_data = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("allergies", {})
        
        if not allergies_data.get("has_allergies", False):
            return []
        
        allergies = []
        known_allergies = allergies_data.get("known_allergies", [])
        
        for allergy in known_allergies:
            if isinstance(allergy, dict):
                allergen = allergy.get("allergen") or allergy.get("allergen_other")
                reaction = allergy.get("reaction", "")
                if allergen:
                    allergies.append({
                        "allergen": allergen,
                        "reaction": reaction
                    })
            elif isinstance(allergy, str) and allergy:
                allergies.append({"allergen": allergy, "reaction": ""})
        
        return allergies

    # =========================================================================
    # Symptoms (existing - enhanced to include all pain/skin)
    # =========================================================================
    
    def _extract_symptoms(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract pain, skin, and headache symptoms"""
        symptoms = []
        pain_skin_health = user_profile.get("patient_data", {}).get("phase2_detailed_intake", {}).get("pain_and_skin_health", {})
        
        # Headaches
        headaches_data = pain_skin_health.get("headaches", {})
        if isinstance(headaches_data, dict):
            has_headaches = headaches_data.get("frequent_headaches_migraines", False)
            if has_headaches:
                details = headaches_data.get("headache_details", "")
                symptoms.append({
                    "type": "headaches",
                    "details": details if details else "frequent headaches/migraines"
                })
        
        # Chronic Pain
        chronic_pain_data = pain_skin_health.get("chronic_pain", {})
        if isinstance(chronic_pain_data, dict):
            has_chronic_pain = chronic_pain_data.get("has_chronic_pain", False)
            if has_chronic_pain:
                details = chronic_pain_data.get("pain_details", "")
                symptoms.append({
                    "type": "chronic_pain",
                    "details": details if details else "chronic pain reported"
                })

        # Skin Issues
        skin_health_data = pain_skin_health.get("skin_health", {})
        if isinstance(skin_health_data, dict):
            has_skin_issues = skin_health_data.get("has_skin_issues", False)
            if has_skin_issues:
                details = skin_health_data.get("skin_condition_details", "")
                symptoms.append({
                    "type": "skin_issues",
                    "details": details if details else "skin issues reported"
                })

        return symptoms

    # =========================================================================
    # Digestive Symptoms (NEW)
    # =========================================================================
    
    def _extract_digestive_symptoms(self, user_profile: Dict[str, Any]) -> List[str]:
        """Extract digestive symptoms"""
        systems_review = user_profile.get("patient_data", {}).get("phase2_detailed_intake", {}).get("systems_review", {})
        digestive_symptoms = systems_review.get("digestive_symptoms", "")
        
        if not digestive_symptoms or digestive_symptoms.lower() == "none":
            return []
        
        # Handle comma-separated list or single value
        if isinstance(digestive_symptoms, str):
            symptoms = [s.strip() for s in digestive_symptoms.split(",") if s.strip()]
            return symptoms
        elif isinstance(digestive_symptoms, list):
            return digestive_symptoms
        
        return []

    # =========================================================================
    # Sleep Issues (NEW)
    # =========================================================================
    
    def _extract_sleep_issues(self, user_profile: Dict[str, Any]) -> List[str]:
        """Extract sleep-related issues"""
        sleep_data = user_profile.get("patient_data", {}).get("phase2_detailed_intake", {}).get("sleep_patterns", {})
        
        if not sleep_data:
            return []
        
        issues = []
        
        # Check each sleep issue flag
        if sleep_data.get("trouble_falling_asleep", False):
            issues.append("trouble_falling_asleep")
        
        if sleep_data.get("trouble_staying_asleep", False):
            issues.append("trouble_staying_asleep")
        
        if sleep_data.get("wake_feeling_refreshed", False) == False and "wake_feeling_refreshed" in sleep_data:
            issues.append("not_waking_refreshed")
        
        if sleep_data.get("snoring_sleep_apnea", "").lower() == "yes":
            issues.append("snoring_or_sleep_apnea")
        
        # Check sleep hours
        hours_category = sleep_data.get("hours_category", "")
        if hours_category in ["less_than_5", "5_to_6"]:
            issues.append("insufficient_sleep")
        
        # Night wake frequency
        night_wakes = sleep_data.get("night_wake_frequency", 0)
        if night_wakes and int(night_wakes) >= 2:
            issues.append(f"wakes_{night_wakes}x_per_night")
        
        return issues

    # =========================================================================
    # Environmental Exposures (NEW)
    # =========================================================================
    
    def _extract_environmental_exposures(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract mold and chemical exposure history"""
        exposures_data = user_profile.get("patient_data", {}).get("phase2_detailed_intake", {}).get("environmental_exposures", {})
        
        result = {
            "mold": None,
            "chemical": None
        }
        
        # Mold exposure
        if exposures_data.get("mold_exposure", False):
            mold_details = exposures_data.get("mold_details", "mold exposure reported")
            result["mold"] = mold_details if mold_details else "mold exposure reported"
        
        # Chemical exposure
        chemical = exposures_data.get("chemical_exposures", "none")
        if chemical and chemical.lower() != "none":
            other_details = exposures_data.get("chemical_exposure_other", "")
            result["chemical"] = other_details if other_details else chemical
        
        return result

    # =========================================================================
    # Hormonal Issues (enhanced with concern details)
    # =========================================================================
    
    def _extract_hormonal_issues(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract hormonal health concerns with details"""
        hormonal_data = user_profile.get("patient_data", {}).get("phase2_detailed_intake", {}).get("reproductive_hormonal_health", {})
        
        if not hormonal_data:
            return {}
        
        result = {}
        
        # Male-specific
        male_data = hormonal_data.get("male_specific", {})
        if male_data and isinstance(male_data, dict):
            if male_data.get("hormonal_concerns", "").lower() == "yes":
                details = male_data.get("concern_details", "hormonal concerns reported")
                result["male_concerns"] = details if details else "hormonal concerns reported"
        
        # Female-specific
        female_data = hormonal_data.get("female_specific", {})
        if female_data and isinstance(female_data, dict):
            concerns = []
            
            # Check menstrual concerns flag
            if female_data.get("menstrual_concerns", "").lower() == "yes":
                concerns.append("menstrual_concerns")
            if female_data.get("irregular_periods", False):
                concerns.append("irregular_periods")
            if female_data.get("pms_symptoms", False):
                concerns.append("pms_symptoms")
            if female_data.get("menopause_symptoms", False):
                concerns.append("menopause_symptoms")
            if female_data.get("pcos", False):
                concerns.append("pcos")
            if female_data.get("endometriosis", False):
                concerns.append("endometriosis")
            
            if concerns:
                result["female_concerns"] = concerns
            
            # Capture concern details text (patient's own description)
            concern_details = female_data.get("concern_details", "")
            if concern_details and concern_details.strip():
                result["concern_details"] = concern_details.strip()
        
        return result

    # =========================================================================
    # Current Supplements (NEW)
    # =========================================================================
    
    def _extract_current_supplements(self, user_profile: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract current supplements patient is taking"""
        supplements_data = user_profile.get("patient_data", {}).get("phase1_basic_intake", {}).get("supplements", {})
        
        if not supplements_data.get("has_supplements", False):
            return []
        
        supplements = []
        current_supplements = supplements_data.get("current_supplements", [])
        
        for supp in current_supplements:
            if isinstance(supp, dict):
                name = supp.get("name", "")
                if name:
                    supplements.append({
                        "name": name,
                        "dose": supp.get("dose", ""),
                        "frequency": supp.get("frequency", ""),
                        "purpose": supp.get("purpose", "")
                    })
            elif isinstance(supp, str) and supp:
                supplements.append({"name": supp, "dose": "", "frequency": "", "purpose": ""})
        
        return supplements

    # =========================================================================
    # Lifestyle Factors (NEW) - diet, stress
    # =========================================================================
    
    def _extract_lifestyle_factors(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract diet style and stress factors"""
        phase2_data = user_profile.get("patient_data", {}).get("phase2_detailed_intake", {})
        
        result = {}
        
        # Diet style
        dietary_habits = phase2_data.get("dietary_habits", {})
        diet_style = dietary_habits.get("diet_style", "")
        if diet_style and diet_style.lower() != "none":
            result["diet"] = diet_style
        
        # Stress level
        occupation = phase2_data.get("occupation_wellness", {})
        stress_level = occupation.get("work_stress_level")
        if stress_level is not None:
            result["stress_level"] = stress_level
            if int(stress_level) >= 7:
                result["high_stress"] = True

        # Diet-based nutrient needs
        diet_nutrient_map = {
            "vegetarian": ["B12", "Iron", "Zinc"],
            "vegan": ["B12", "Iron", "Omega-3", "Zinc", "Calcium"],
            "keto": ["Electrolytes", "Fiber", "Magnesium"],
            "pescatarian": ["B12", "Iron"],
            "paleo": ["Calcium", "Fiber"]
        }
        if diet_style:
            diet_lower = diet_style.lower()
            for diet_key, nutrients in diet_nutrient_map.items():
                if diet_key in diet_lower:
                    result["diet_nutrient_needs"] = nutrients
                    break

        return result

    # =========================================================================
    # Dental Health (NEW)
    # =========================================================================

    def _extract_dental_health(self, user_profile: Dict[str, Any]) -> List[str]:
        """Extract dental health issues that may impact supplement needs"""
        dental_data = user_profile.get("patient_data", {}).get("phase2_detailed_intake", {}).get("dental_health", {})

        if not dental_data:
            return []

        issues = []

        # Dental work with potential health impacts
        dental_work = dental_data.get("dental_work", {})
        if dental_work.get("root_canals", 0) > 0:
            issues.append(f"root_canals ({dental_work.get('root_canals')})")
        if dental_work.get("silver_mercury_fillings", 0) > 0:
            issues.append(f"mercury_fillings ({dental_work.get('silver_mercury_fillings')})")
        if dental_work.get("implants", 0) > 0:
            issues.append(f"dental_implants ({dental_work.get('implants')})")

        # Oral health issues
        oral_issues = dental_data.get("oral_health_issues", {})
        if isinstance(oral_issues, dict):
            if oral_issues.get("gingivitis"):
                issues.append("gingivitis")
            if oral_issues.get("tooth_pain"):
                issues.append("tooth_pain")
            if oral_issues.get("tmj_disorder"):
                issues.append("tmj_disorder")
            if oral_issues.get("bleeding_gums"):
                issues.append("bleeding_gums")
            if oral_issues.get("chewing_problems"):
                issues.append("chewing_problems")
            other_dental = oral_issues.get("other_dental_work", "")
            if other_dental and other_dental.strip():
                issues.append(f"other: {other_dental.strip()}")

        return issues

    # =========================================================================
    # Family History (NEW)
    # =========================================================================

    def _extract_family_history(self, user_profile: Dict[str, Any]) -> List[str]:
        """Extract family medical history conditions for preventive consideration"""
        family_data = user_profile.get("patient_data", {}).get("phase2_detailed_intake", {}).get("family_medical_history", {})

        if not family_data:
            return []

        conditions = []
        conditions_detail = family_data.get("conditions_detail", {})

        if isinstance(conditions_detail, dict):
            for condition, relatives in conditions_detail.items():
                if relatives:
                    # Format: "condition (relative1, relative2)"
                    relatives_str = ", ".join(relatives) if isinstance(relatives, list) else str(relatives)
                    conditions.append(f"{condition} ({relatives_str})")

        return conditions

    # =========================================================================
    # Childhood Factors (NEW)
    # =========================================================================

    def _extract_childhood_factors(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract childhood factors that may impact gut health"""
        phase2_data = user_profile.get("patient_data", {}).get("phase2_detailed_intake", {})

        result = {}

        # Childhood antibiotics
        childhood_antibiotics = phase2_data.get("childhood_antibiotics", {})
        if childhood_antibiotics.get("took_antibiotics_as_child", False):
            result["childhood_antibiotics"] = True

        # Childhood development factors
        childhood_dev = phase2_data.get("childhood_development", {})
        if childhood_dev.get("born_via_c_section", "").lower() == "yes":
            result["c_section_birth"] = True
        if childhood_dev.get("high_sugar_childhood_diet", "").lower() == "yes":
            result["high_sugar_childhood"] = True

        return result