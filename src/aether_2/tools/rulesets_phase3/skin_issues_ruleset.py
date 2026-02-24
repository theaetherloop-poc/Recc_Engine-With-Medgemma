"""
Skin Issues Ruleset (Phase 3)

Conditional on Phase 2: has_skin_issues == true

Ask: "You mentioned you had skin issues. Please describe location, triggers, and timing."
Record as: free text (single multiline string)
Scope: Adults ≥18 y only

Analyzes skin conditions (psoriasis, eczema, rosacea, acne), triggers, and timing
to determine focus area weights.

Legend:
CM=Cardiometabolic · COG=Cognitive · DTX=Detox/Biotransformation · IMM=Immune/Inflammation
MITO=Mitochondrial/Energy · SKN=Skin/Barrier · STR=Stress‑axis · HRM=Hormonal · GA=Gut/Assimilation

Weight scale: 0.1 small · 0.2 moderate · 0.3 strong · 0.4 very strong
Clip each focus total from this field to ≤ +1.0 (protective deductions allowed)
"""

from typing import Dict, List, Tuple


class SkinIssuesRuleset:
    """Analyzes skin issues, triggers, and timing for focus area scoring."""

    # NLP Lexicons
    AUTOIMMUNE_SKIN = ["psoriasis", "psoriatic", "eczema", "atopic dermatitis", 
                       "urticaria", "autoimmune", "atopic"]
    
    ACNE_TERMS = ["acne", "adult acne", "hormonal acne", "cystic acne", 
                  "jawline acne", "cystic", "comedones", "pimples"]
    
    ROSACEA_TERMS = ["rosacea", "flushing", "telangiectasia", "facial redness"]
    
    STRESS_TERMS = ["stress", "anxiety", "burnout", "nervous", "tension", "worried"]
    
    HISTAMINE_FOODS = ["histamine", "aged cheese", "wine", "fermented", "sauerkraut",
                       "kombucha", "cured meats", "aged", "vinegar", "pickled"]
    
    DIET_ACNE = ["dairy", "milk", "whey", "ice cream", "skim milk", "sugar",
                 "high glycemic", "white bread", "soda", "refined carbs", "sweets"]
    
    GI_TERMS = ["bloating", "bloat", "constipation", "diarrhea", "ibs", "sibo",
                "reflux", "gerd", "heartburn", "gas", "indigestion"]
    
    HEAT_SPICY_ALCOHOL = ["hot drink", "hot beverage", "hot coffee", "hot tea",
                          "spicy", "chili", "pepper", "alcohol", "red wine", "beer"]
    
    COSMETICS_IRRITANT = ["fragrance", "perfume", "scented", "essential oil",
                          "new skincare", "harsh cleanser", "retinoid", "product",
                          "makeup", "cosmetic", "soap"]
    
    ANTIBIOTICS = ["antibiotic", "doxycycline", "minocycline", "amoxicillin",
                   "azithromycin", "recent antibiotics", "antibiotics"]
    
    CYCLE_TERMS = ["pre-period", "premenstrual", "around menses", "ovulation",
                   "monthly cycle", "period", "menstrual", "pms", "before period"]
    
    SUN_HEAT_SWEAT = ["sun", "sunlight", "uv", "heat", "sauna", "sweat", "exercise",
                      "hot weather", "summer", "humid"]
    
    PCOS_ANDROGEN = ["pcos", "androgen excess", "hyperandrogen", "low shbg",
                     "elevated testosterone", "hirsutism", "polycystic"]
    
    # Protective/improvement terms
    LOW_GLYCEMIC_DAIRY_FREE = ["low glycemic", "reduced sugar", "cut dairy", "dairy-free",
                               "dairy free", "no dairy", "quit dairy", "stopped dairy"]
    
    ELIMINATION_DIET = ["elimination diet helped", "gluten-free helped", "low fodmap helped",
                        "elimination diet", "food elimination", "diet helped"]
    
    MIND_BODY = ["yoga", "meditation", "mindfulness", "breathing exercises", "relaxation"]
    
    SLEEP_FATIGUE = ["poor sleep", "insomnia", "fatigue", "tired", "exhausted",
                     "sleep deprivation", "lack of sleep"]
    
    # Safety red flags (route to clinician)
    RED_FLAGS = ["spreading rapidly", "fever", "mucosal", "eye", "blisters",
                 "target lesions", "saddle", "neurological", "painful blisters",
                 "rapidly evolving", "melanoma", "changing mole", "bleeding"]

    def __init__(self):
        """Initialize the skin issues ruleset."""
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

    def _count_matches(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords are present in text."""
        if not text:
            return 0
        text_lower = text.lower()
        return sum(1 for keyword in keywords if keyword in text_lower)

    def get_skin_issues_weights(
        self,
        skin_text: str,
        age: int,
        biological_sex: str = None,
        phase2_digestive_symptoms: List[str] = None
    ) -> Tuple[Dict[str, float], List[str], List[Dict[str, str]]]:
        """
        Calculate focus area weights based on skin issues description.
        
        Args:
            skin_text: Free text describing skin issues, triggers, and timing
            age: Patient age (must be ≥18)
            biological_sex: Biological sex (for hormonal context)
            phase2_digestive_symptoms: List of digestive symptoms from Phase 2
            
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
            flags.append("Age <18: skin issues ruleset not applied")
            return scores, flags, alerts
        
        # Normalize text
        text_normalized = self._normalize_text(skin_text)
        
        if not text_normalized or len(text_normalized) < 5:
            flags.append("No skin issue details provided")
            return scores, flags, alerts
        
        # ================================================================
        # SAFETY FLAGS (route to clinician; no scoring)
        # ================================================================
        if self._contains_any(text_normalized, self.RED_FLAGS):
            alerts.append({
                "severity": "urgent",
                "message": "Dermatologic red-flag features detected → escalate for clinician review."
            })
            flags.append("⚠️  RED FLAG: Urgent dermatologic features detected")

        # ================================================================
        # 1) AUTOIMMUNE/IMMUNE-TYPE DERMATOSES
        # ================================================================
        autoimmune_detected = self._contains_any(text_normalized, self.AUTOIMMUNE_SKIN)
        if autoimmune_detected:
            scores["IMM"] += 0.30
            scores["SKN"] += 0.25
            flags.append("Autoimmune/barrier dermatosis (psoriasis/eczema/AD) → IMM +0.30, SKN +0.25")

            # If pattern fluctuates with stress
            if self._contains_any(text_normalized, self.STRESS_TERMS):
                scores["STR"] += 0.20
                flags.append("Stress-linked flares → STR +0.20 (brain-skin/HPA axis)")

        # ================================================================
        # 2) ADULT ACNE / "HORMONAL ACNE"
        # ================================================================
        acne_detected = self._contains_any(text_normalized, self.ACNE_TERMS)
        if acne_detected:
            scores["HRM"] += 0.25
            scores["DTX"] += 0.15
            scores["SKN"] += 0.15
            flags.append("Adult/hormonal acne → HRM +0.25, DTX +0.15, SKN +0.15")

            # Dietary triggers (dairy, high-glycemic)
            if self._contains_any(text_normalized, self.DIET_ACNE):
                scores["GA"] += 0.20
                flags.append("Acne + dietary triggers (dairy/high-glycemic) → GA +0.20")

            # PCOS/androgen signals
            if self._contains_any(text_normalized, self.PCOS_ANDROGEN):
                # Replace HRM +0.25 with +0.30
                scores["HRM"] = max(scores["HRM"], 0.30)  # Ensure at least 0.30
                flags.append("PCOS/androgen excess detected → HRM bumped to +0.30")

        # ================================================================
        # 3) ROSACEA & CLASSIC TRIGGERS
        # ================================================================
        rosacea_detected = self._contains_any(text_normalized, self.ROSACEA_TERMS)
        if rosacea_detected:
            scores["SKN"] += 0.25
            scores["IMM"] += 0.15
            scores["GA"] += 0.25
            flags.append("Rosacea → SKN +0.25, IMM +0.15, GA +0.25 (gut-skin axis)")

            # Hot drinks, spicy food, alcohol triggers (max +0.20)
            trigger_count = self._count_matches(text_normalized, self.HEAT_SPICY_ALCOHOL)
            if trigger_count > 0:
                trigger_bump = min(0.10 * trigger_count, 0.20)  # Cap at +0.20
                scores["GA"] += trigger_bump
                flags.append(f"Rosacea triggers (hot/spicy/alcohol, n={trigger_count}) → GA +{trigger_bump:.2f}")

        # ================================================================
        # 4) STRESS-LINKED FLARES
        # ================================================================
        if self._contains_any(text_normalized, self.STRESS_TERMS) and not autoimmune_detected:
            # Only add if not already added in autoimmune section
            scores["STR"] += 0.20
            scores["COG"] += 0.10
            flags.append("Stress-linked flares → STR +0.20, COG +0.10")

            # If also sleep debt
            if self._contains_any(text_normalized, self.SLEEP_FATIGUE):
                scores["MITO"] += 0.10
                flags.append("Stress + sleep debt → MITO +0.10 (fatigue load)")

        # ================================================================
        # 5) ANTIBIOTIC-ASSOCIATED FLARES
        # ================================================================
        if self._contains_any(text_normalized, self.ANTIBIOTICS):
            scores["GA"] += 0.20
            flags.append("Antibiotic-associated flares → GA +0.20 (dysbiosis signal)")

            # Long courses
            if any(word in text_normalized for word in ["long", "months", "chronic", "years"]):
                scores["IMM"] += 0.10
                flags.append("Long antibiotic courses → IMM +0.10 (mucosal immunity shift)")

        # ================================================================
        # 6) FOOD/HISTAMINE TERMS
        # ================================================================
        if self._contains_any(text_normalized, self.HISTAMINE_FOODS):
            scores["GA"] += 0.20
            scores["IMM"] += 0.10
            flags.append("Histamine foods/intolerance → GA +0.20, IMM +0.10 (mast-cell pathway)")

        # ================================================================
        # 7) SKIN-GUT COUPLING
        # ================================================================
        gi_symptoms_present = False
        if phase2_digestive_symptoms:
            gi_symptoms_present = len(phase2_digestive_symptoms) > 0

        # Also check if GI terms mentioned in skin text
        if self._contains_any(text_normalized, self.GI_TERMS):
            gi_symptoms_present = True

        if (autoimmune_detected or rosacea_detected) and gi_symptoms_present:
            scores["GA"] += 0.20
            flags.append("Skin-gut coupling (eczema/psoriasis/rosacea + GI symptoms) → GA +0.20")

        # ================================================================
        # 8) HORMONAL TIMING
        # ================================================================
        if self._contains_any(text_normalized, self.CYCLE_TERMS):
            scores["HRM"] += 0.20
            scores["STR"] += 0.10
            flags.append("Menstrual cycle-linked flares → HRM +0.20, STR +0.10")

        # ================================================================
        # 9) BARRIER/IRRITANT & PHOTO TRIGGERS
        # ================================================================
        if self._contains_any(text_normalized, self.COSMETICS_IRRITANT):
            scores["SKN"] += 0.20
            scores["IMM"] += 0.10
            flags.append("Cosmetic/fragrance/irritant triggers → SKN +0.20, IMM +0.10")

        if self._contains_any(text_normalized, self.SUN_HEAT_SWEAT):
            scores["SKN"] += 0.10
            scores["IMM"] += 0.10
            flags.append("Sun/heat/sweat triggers → SKN +0.10, IMM +0.10 (thermoregulatory)")

        # ================================================================
        # 10) PROTECTIVE SIGNALS (deductions)
        # ================================================================

        # Low-glycemic / dairy reduction improved acne
        if acne_detected and self._contains_any(text_normalized, self.LOW_GLYCEMIC_DAIRY_FREE):
            # Check for improvement context
            improvement_words = ["helped", "improved", "better", "cleared", "reduced", "less"]
            if any(word in text_normalized for word in improvement_words):
                scores["GA"] -= 0.20
                scores["HRM"] -= 0.10
                flags.append("Low-glycemic/dairy-free improved acne → GA -0.20, HRM -0.10")

        # Elimination diet reduced eczema/rosacea
        if (autoimmune_detected or rosacea_detected) and self._contains_any(text_normalized, self.ELIMINATION_DIET):
            improvement_words = ["helped", "improved", "better", "cleared", "reduced", "less"]
            if any(word in text_normalized for word in improvement_words):
                scores["GA"] -= 0.20
                flags.append("Elimination diet improved skin → GA -0.20 (diet-responsive phenotype)")

        # Mind-body practices reduce stress-linked flares
        if self._contains_any(text_normalized, self.STRESS_TERMS) and self._contains_any(text_normalized, self.MIND_BODY):
            improvement_words = ["helped", "improved", "better", "reduced", "less", "calms"]
            if any(word in text_normalized for word in improvement_words):
                scores["STR"] -= 0.20
                flags.append("Mind-body practices reduce flares → STR -0.20 (stress-buffer)")

        # ================================================================
        # APPLY CAPS
        # ================================================================

        # Cap each focus area at +1.0
        for domain in scores:
            if scores[domain] > 1.0:
                flags.append(f"{domain} capped at +1.0 (was {scores[domain]:.2f})")
                scores[domain] = 1.0

        # ================================================================
        # SUMMARY FLAGS
        # ================================================================

        # Identify primary skin condition
        conditions = []
        if autoimmune_detected:
            conditions.append("autoimmune/barrier (psoriasis/eczema)")
        if acne_detected:
            conditions.append("acne")
        if rosacea_detected:
            conditions.append("rosacea")

        if conditions:
            flags.append(f"Primary skin condition(s): {', '.join(conditions)}")

        # Identify key triggers
        triggers = []
        if self._contains_any(text_normalized, self.STRESS_TERMS):
            triggers.append("stress")
        if self._contains_any(text_normalized, self.DIET_ACNE):
            triggers.append("diet (dairy/high-glycemic)")
        if self._contains_any(text_normalized, self.HISTAMINE_FOODS):
            triggers.append("histamine foods")
        if self._contains_any(text_normalized, self.HEAT_SPICY_ALCOHOL):
            triggers.append("heat/spicy/alcohol")
        if self._contains_any(text_normalized, self.COSMETICS_IRRITANT):
            triggers.append("cosmetics/irritants")
        if self._contains_any(text_normalized, self.CYCLE_TERMS):
            triggers.append("menstrual cycle")

        if triggers:
            flags.append(f"Key triggers: {', '.join(triggers)}")

        return scores, flags, alerts

