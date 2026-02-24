"""
Chronic Pain Modifiers Ruleset (Phase 3)

Conditional on Phase 2: has_chronic_pain == true

Ask: "You mentioned chronic pain previously. Where is the pain, and what makes it worse/better?"
Record as: free text (single multiline string)
Scope: Adults ≥18 y only

Analyzes pain patterns (mechanical, inflammatory, neuropathic, visceral) and modifiers
to determine focus area weights.

Legend:
CM=Cardiometabolic · COG=Cognitive · DTX=Detox/Biotransformation · IMM=Immune/Inflammation
MITO=Mitochondrial/Energy · SKN=Skin/Barrier · STR=Stress‑axis · HRM=Hormonal · GA=Gut/Assimilation

Weight scale: 0.1 small · 0.2 moderate · 0.3 strong · 0.4 very strong
Clip each focus total from this field to ≤ +1.0 (protective deductions can reduce up to −0.3)
"""

from typing import Dict, List, Tuple
import re


class ChronicPainModifiersRuleset:
    """Analyzes chronic pain patterns and modifiers for focus area scoring."""

    # NLP Lexicons
    MECHANICAL_CUES = ["stairs", "lifting", "bending", "twisting", "carrying", "standing", "walking"]
    WEATHER_CUES = ["cold", "humidity", "humid", "barometric", "storm", "rain", "weather", "damp"]
    VISCERAL_CUES = ["after meals", "with meals", "post-meal", "post meal", "bloating", "bloat",
                     "constipation", "reflux", "heartburn", "gerd", "nausea"]
    NEUROPATHIC_CUES = ["burning", "electric", "shooting", "pins and needles", "pins-and-needles",
                        "tingling", "allodynia", "widespread", "numbness", "prickling"]
    STRESS_SLEEP_CUES = ["stress", "poor sleep", "insomnia", "late nights", "sleep loss",
                         "lack of sleep", "sleep deprivation", "anxiety"]
    
    # "Better with" cues (protective)
    HELPS_MAGNESIUM = ["magnesium", " mg ", "epsom", "epsom salt"]
    HELPS_ACUPUNCTURE = ["acupuncture", "needling", "acupressure"]
    HELPS_ACETAMINOPHEN = ["acetaminophen", "paracetamol", "tylenol"]
    HELPS_NSAID = ["ibuprofen", "advil", "naproxen", "aleve", "nsaid", "motrin"]
    
    # Medication keywords
    OPIOIDS = ["opioid", "oxycodone", "hydrocodone", "morphine", "fentanyl", "methadone",
               "buprenorphine", "tramadol", "codeine"]
    GABAPENTINOIDS = ["gabapentin", "pregabalin", "lyrica", "neurontin"]
    ANTIDEPRESSANTS_PAIN = ["duloxetine", "amitriptyline", "cymbalta", "elavil"]
    
    # IBS/Diet keywords
    IBS_DIET = ["low fodmap", "fodmap", "elimination diet", "gluten-free", "dairy-free",
                "trigger foods", "food triggers", "ibs", "ibs diet"]
    
    # Reflux keywords (for NSAID interaction)
    REFLUX_WORDS = ["heartburn", "reflux", "gerd", "acid reflux", "indigestion"]
    
    # Location keywords (for future routing, no scoring change)
    LOCATIONS = {
        "low_back": ["low back", "lower back", "lumbar", "l-spine"],
        "neck": ["neck", "cervical", "c-spine"],
        "shoulder": ["shoulder"],
        "knee_hip": ["knee", "hip", "joint"],
        "pelvic": ["pelvic", "pelvis", "groin"],
        "widespread": ["widespread", "all over", "everywhere", "whole body"],
        "abdominal": ["ruq", "luq", "llq", "rlq", "abdomen", "abdominal", "belly", "stomach"],
        "headache": ["headache", "head pain", "migraine"]
    }
    
    # Chronicity markers
    CHRONICITY_MARKERS = ["daily", "constant", "most days", "every day", "all the time",
                          "chronic", "persistent", "ongoing"]

    def __init__(self):
        """Initialize the chronic pain modifiers ruleset."""
        pass

    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, preserve negations."""
        if not text:
            return ""
        return text.lower().strip()

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords."""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def _contains_all(self, text: str, keyword_lists: List[List[str]]) -> bool:
        """Check if text contains at least one keyword from each list."""
        if not text:
            return False
        text_lower = text.lower()
        return all(any(kw in text_lower for kw in kw_list) for kw_list in keyword_lists)

    def _extract_location(self, text: str) -> List[str]:
        """Extract pain location(s) from text."""
        if not text:
            return []
        
        text_lower = text.lower()
        locations = []
        
        for location_key, keywords in self.LOCATIONS.items():
            if any(kw in text_lower for kw in keywords):
                locations.append(location_key)
        
        return locations

    def _is_chronic(self, text: str) -> bool:
        """Check if pain is described as chronic/constant."""
        if not text:
            return False
        return self._contains_any(text, self.CHRONICITY_MARKERS)

    def _check_negation(self, text: str, keyword: str, window: int = 5) -> bool:
        """
        Check if keyword is negated within a window of tokens.
        Returns True if keyword is present AND NOT negated.
        """
        if not text or keyword not in text.lower():
            return False
        
        # Simple negation check: look for "no", "not", "never" within ±5 words
        negation_words = ["no ", "not ", "never ", "without ", "doesn't ", "don't "]
        
        # Find keyword position
        text_lower = text.lower()
        keyword_pos = text_lower.find(keyword)
        
        # Check window before keyword
        start = max(0, keyword_pos - (window * 6))  # Approximate 6 chars per word
        end = min(len(text_lower), keyword_pos + len(keyword) + (window * 6))
        context = text_lower[start:end]
        
        # If negation found in context, keyword is negated
        if any(neg in context for neg in negation_words):
            return False
        
        return True

    def get_chronic_pain_weights(
        self,
        pain_text: str,
        age: int,
        phase2_digestive_symptoms: List[str] = None,
        phase2_medications: List[str] = None
    ) -> Tuple[Dict[str, float], List[str], List[Dict[str, str]]]:
        """
        Calculate focus area weights based on chronic pain modifiers.

        Args:
            pain_text: Free text describing pain location and modifiers
            age: Patient age (must be ≥18)
            phase2_digestive_symptoms: List of digestive symptoms from Phase 2
            phase2_medications: List of current medications from Phase 2

        Returns:
            Tuple of (scores_dict, flags_list, alerts_list)
        """
        scores = {
            "CM": 0.0, "COG": 0.0, "DTX": 0.0, "IMM": 0.0,
            "MITO": 0.0, "SKN": 0.0, "STR": 0.0, "HRM": 0.0, "GA": 0.0
        }
        flags = []
        alerts = []

        # Age gate: only apply if age ≥18
        if age < 18:
            flags.append("Age <18: chronic pain ruleset not applied")
            return scores, flags, alerts

        # Normalize text
        text_normalized = self._normalize_text(pain_text)

        if not text_normalized or len(text_normalized) < 5:
            flags.append("No chronic pain details provided")
            return scores, flags, alerts

        # Extract location (for logging, no scoring impact)
        locations = self._extract_location(text_normalized)
        if locations:
            flags.append(f"Pain location(s): {', '.join(locations)}")

        # Check chronicity
        is_chronic = self._is_chronic(text_normalized)
        if is_chronic:
            flags.append("Chronic pain pattern detected (daily/constant)")

        # ================================================================
        # 1) PATTERN OF PAIN (mechanical vs inflammatory vs neuropathic vs visceral)
        # ================================================================

        # Mechanical cues: stairs, lifting, bending, twisting
        if self._contains_any(text_normalized, self.MECHANICAL_CUES):
            scores["MITO"] += 0.20
            scores["CM"] += 0.20
            flags.append("Mechanical pain pattern → MITO +0.20, CM +0.20 (deconditioning/energy demand)")

        # Weather-related terms
        if self._contains_any(text_normalized, self.WEATHER_CUES):
            scores["IMM"] += 0.15
            flags.append("Weather-sensitive pain → IMM +0.15 (inflammatory sensitivity)")

        # Neuropathic/central sensitization cues
        if self._contains_any(text_normalized, self.NEUROPATHIC_CUES):
            scores["STR"] += 0.20
            scores["COG"] += 0.10
            scores["MITO"] += 0.10
            flags.append("Neuropathic pain pattern → STR +0.20, COG +0.10, MITO +0.10 (central sensitization)")

        # Visceral/gut-linked cues
        visceral_detected = self._contains_any(text_normalized, self.VISCERAL_CUES)
        if visceral_detected:
            scores["GA"] += 0.25
            flags.append("Visceral pain pattern (meal/GI-related) → GA +0.25 (brain-gut axis)")

            # Additional bump if IBS/FODMAP mentioned
            if self._contains_any(text_normalized, self.IBS_DIET):
                scores["GA"] += 0.10
                flags.append("IBS/FODMAP keywords detected → GA +0.10 additional")

        # ================================================================
        # 2) "BETTER WITH..." (protective deductions; floor at -0.3 total)
        # ================================================================

        # Magnesium helps
        if self._contains_any(text_normalized, self.HELPS_MAGNESIUM):
            scores["STR"] -= 0.10
            scores["MITO"] -= 0.05
            flags.append("Magnesium helps → STR -0.10, MITO -0.05 (relaxation/NMDA effects)")

        # Acupuncture helps
        if self._contains_any(text_normalized, self.HELPS_ACUPUNCTURE):
            scores["STR"] -= 0.15
            scores["COG"] -= 0.10
            flags.append("Acupuncture helps → STR -0.15, COG -0.10 (chronic pain RCT evidence)")

        # Acetaminophen helps
        if self._contains_any(text_normalized, self.HELPS_ACETAMINOPHEN):
            scores["IMM"] -= 0.05
            flags.append("Acetaminophen helps → IMM -0.05 (nociceptive component)")

        # NSAIDs help
        nsaid_helps = self._contains_any(text_normalized, self.HELPS_NSAID)
        reflux_present = self._contains_any(text_normalized, self.REFLUX_WORDS)

        if nsaid_helps:
            scores["IMM"] -= 0.05
            flags.append("NSAIDs help → IMM -0.05 (inflammatory component responsive)")

            # Check for NSAID + reflux interaction
            if reflux_present:
                scores["GA"] += 0.15
                flags.append("Daily NSAIDs + reflux/GERD → GA +0.15 (foregut injury risk)")
                alerts.append({
                    "severity": "warning",
                    "message": "NSAID use with reflux symptoms: gastropathy risk. Consider PPI or alternative analgesia."
                })

        # ================================================================
        # 3) "WORSE WITH..." (additive risks)
        # ================================================================

        # Stress/poor sleep
        if self._contains_any(text_normalized, self.STRESS_SLEEP_CUES):
            scores["STR"] += 0.20
            scores["COG"] += 0.10
            flags.append("Worse with stress/poor sleep → STR +0.20, COG +0.10 (pain-sleep-stress loop)")

        # ================================================================
        # 4) MEDICATION-LINKED PAIN CONTEXT
        # ================================================================

        # Opioids mentioned
        if self._contains_any(text_normalized, self.OPIOIDS):
            scores["GA"] += 0.30
            scores["DTX"] += 0.10
            flags.append("Opioid use detected → GA +0.30, DTX +0.10 (opioid-induced bowel dysfunction)")
            alerts.append({
                "severity": "warning",
                "message": "Chronic opioid use: screen for constipation, gastroparesis, and opioid-induced hyperalgesia."
            })

        # Gabapentinoids/antidepressants (tag only, no score change)
        if self._contains_any(text_normalized, self.GABAPENTINOIDS):
            flags.append("Gabapentin/pregabalin mentioned → neuropathic phenotype likely")

        if self._contains_any(text_normalized, self.ANTIDEPRESSANTS_PAIN):
            flags.append("Duloxetine/amitriptyline mentioned → neuropathic/central pain phenotype")

        # ================================================================
        # 5) DIET-RESPONSE (integrative)
        # ================================================================

        # Better on elimination/low-FODMAP
        if self._contains_any(text_normalized, self.IBS_DIET):
            # Check if it's described as helpful (not just mentioned)
            helpful_context = ["better", "helped", "helps", "improved", "relief", "reduced"]
            if any(word in text_normalized for word in helpful_context):
                scores["GA"] -= 0.20
                flags.append("Better with elimination/low-FODMAP diet → GA -0.20 (dietary response)")

        # Multiple food triggers (≥4) + pain flare
        food_trigger_keywords = ["dairy", "gluten", "wheat", "soy", "eggs", "nuts", "corn",
                                 "nightshades", "tomatoes", "peppers", "sugar", "alcohol",
                                 "caffeine", "chocolate", "citrus", "spicy"]
        food_trigger_count = sum(1 for kw in food_trigger_keywords if kw in text_normalized)

        if food_trigger_count >= 4:
            pain_flare_keywords = ["flare", "worse", "trigger", "aggravate", "worsen"]
            if any(kw in text_normalized for kw in pain_flare_keywords):
                scores["GA"] += 0.10
                flags.append(f"Multiple food triggers (n={food_trigger_count}) + pain flare → GA +0.10 (permeability/mast-cell)")

        # ================================================================
        # APPLY CAPS AND FLOOR
        # ================================================================

        # Cap each focus area at +1.0
        for domain in scores:
            if scores[domain] > 1.0:
                flags.append(f"{domain} capped at +1.0 (was {scores[domain]:.2f})")
                scores[domain] = 1.0

        # Floor protective deductions at -0.3 total per domain
        for domain in scores:
            if scores[domain] < -0.3:
                flags.append(f"{domain} floored at -0.3 (was {scores[domain]:.2f})")
                scores[domain] = -0.3

        # ================================================================
        # CROSS-VALIDATION WITH PHASE 2
        # ================================================================

        # If Phase 2 digestive symptoms present and visceral pain detected
        if phase2_digestive_symptoms and visceral_detected:
            phase2_gi_symptoms = [s.lower() for s in phase2_digestive_symptoms]
            overlap_count = sum(1 for symptom in ["bloating", "constipation", "reflux", "nausea"]
                               if any(symptom in s for s in phase2_gi_symptoms))
            if overlap_count >= 2:
                flags.append(f"Phase 2 GI symptoms ({overlap_count}) align with visceral pain pattern")

        # If Phase 2 medications include opioids/NSAIDs
        if phase2_medications:
            # Handle both list of strings and list of dicts
            phase2_meds_lower = []
            for m in phase2_medications:
                if isinstance(m, dict):
                    # Extract medication name from dict
                    med_name = m.get("name", "")
                    if med_name:
                        phase2_meds_lower.append(med_name.lower())
                elif isinstance(m, str):
                    phase2_meds_lower.append(m.lower())

            # Check for opioids in Phase 2
            if any(opioid in " ".join(phase2_meds_lower) for opioid in self.OPIOIDS):
                if not self._contains_any(text_normalized, self.OPIOIDS):
                    flags.append("⚠️  Phase 2 shows opioid use but not mentioned in pain details")

            # Check for NSAIDs in Phase 2
            if any(nsaid in " ".join(phase2_meds_lower) for nsaid in self.HELPS_NSAID):
                if not nsaid_helps:
                    flags.append("Phase 2 shows NSAID use (not mentioned in pain details)")

        return scores, flags, alerts

