"""
Field 42: Unintentional Weight Change Details (Free Text)

This field captures the details of unintentional weight change if Field 41 = "Yes".
Format: "Gained 10 lb in 2 months" or "Lost 5 kg over 6 months"

Entities to extract (NLP):
- Direction: gain | loss
- Magnitude: number + unit (kg, lb, lbs, pounds, stone)
- Time window: days | weeks | months | years → normalized to months
- Intention: must be unintentional (if clearly intentional, set to neutral)

Scoring based on:
- % change (if baseline weight known) or absolute thresholds
- Rate of change (kg/month)
- Direction (loss vs gain)
- Severity tiers
- Amplifiers from cross-field context
"""

import re
from typing import Dict, List, Tuple, Optional


class UnintentionalWeightChangeDetailsRuleset:
    """
    Ruleset for Field 42: Unintentional Weight Change Details
    
    Parses free-text weight change description and scores based on:
    - Direction (gain vs loss)
    - Magnitude and rate
    - Clinical significance thresholds
    - Cross-field amplifiers
    """
    
    # Unit conversion to kg
    UNIT_TO_KG = {
        "kg": 1.0,
        "kgs": 1.0,
        "kilogram": 1.0,
        "kilograms": 1.0,
        "lb": 0.453592,
        "lbs": 0.453592,
        "pound": 0.453592,
        "pounds": 0.453592,
        "stone": 6.35029,
        "st": 6.35029,
    }
    
    # Time conversion to months
    TIME_TO_MONTHS = {
        "day": 1/30.0,
        "days": 1/30.0,
        "week": 1/4.0,
        "weeks": 1/4.0,
        "wk": 1/4.0,
        "wks": 1/4.0,
        "month": 1.0,
        "months": 1.0,
        "mo": 1.0,
        "mos": 1.0,
        "year": 12.0,
        "years": 12.0,
        "yr": 12.0,
        "yrs": 12.0,
    }
    
    def __init__(self):
        """Initialize the ruleset."""
        pass
    
    def _parse_weight_change(self, text: str) -> Dict[str, any]:
        """
        Parse weight change text to extract direction, magnitude, and timeframe.
        
        Args:
            text: Free-text description (e.g., "Gained 10 lb in 2 months")
            
        Returns:
            Dict with keys: direction, magnitude_kg, months, raw_text, is_intentional
        """
        result = {
            "direction": None,  # "gain" or "loss"
            "magnitude_kg": 0.0,
            "months": 0.0,
            "raw_text": text,
            "is_intentional": False
        }
        
        if not text:
            return result
        
        text_lower = text.lower().strip()
        
        # Check for intentional keywords (dieting, trying to lose, etc.)
        intentional_keywords = [
            "diet", "dieting", "trying to lose", "trying to gain",
            "intentional", "on purpose", "working out", "gym"
        ]
        if any(kw in text_lower for kw in intentional_keywords):
            result["is_intentional"] = True
            return result
        
        # Extract direction
        gain_keywords = ["gain", "gained", "put on", "up", "increase", "increased"]
        loss_keywords = ["loss", "lost", "lose", "drop", "dropped", "down", "decrease", "decreased"]
        
        if any(kw in text_lower for kw in gain_keywords):
            result["direction"] = "gain"
        elif any(kw in text_lower for kw in loss_keywords):
            result["direction"] = "loss"
        
        # Extract magnitude and unit
        # Pattern: number + optional decimal + unit
        # Examples: "10 lb", "5.5 kg", "2 pounds"
        magnitude_pattern = r'(\d+(?:\.\d+)?)\s*(kg|kgs|kilogram|kilograms|lb|lbs|pound|pounds|stone|st)\b'
        magnitude_match = re.search(magnitude_pattern, text_lower)
        
        if magnitude_match:
            number = float(magnitude_match.group(1))
            unit = magnitude_match.group(2)
            conversion_factor = self.UNIT_TO_KG.get(unit, 1.0)
            result["magnitude_kg"] = number * conversion_factor
        
        # Extract timeframe
        # Pattern: number + time unit
        # Examples: "in 2 months", "over 6 weeks", "past year"
        time_pattern = r'(\d+(?:\.\d+)?)\s*(day|days|week|weeks|wk|wks|month|months|mo|mos|year|years|yr|yrs)\b'
        time_match = re.search(time_pattern, text_lower)
        
        if time_match:
            number = float(time_match.group(1))
            unit = time_match.group(2)
            conversion_factor = self.TIME_TO_MONTHS.get(unit, 1.0)
            result["months"] = number * conversion_factor
        
        return result

    def _calculate_percent_change(
        self,
        magnitude_kg: float,
        months: float,
        baseline_kg: Optional[float] = None
    ) -> Optional[float]:
        """
        Calculate % weight change over 6 months (annualized rate).

        Args:
            magnitude_kg: Weight change in kg
            months: Time period in months
            baseline_kg: Baseline weight in kg (if known)

        Returns:
            % change over 6 months, or None if baseline unknown
        """
        if baseline_kg is None or baseline_kg <= 0 or months <= 0:
            return None

        # Normalize to 6-month rate
        pct_change_6mo = (magnitude_kg / baseline_kg) * (6.0 / months) * 100.0
        return pct_change_6mo

    def _get_severity_tier(
        self,
        direction: str,
        magnitude_kg: float,
        months: float,
        pct_change_6mo: Optional[float] = None
    ) -> str:
        """
        Determine severity tier based on thresholds.

        Tiers:
        - "none": No significant change
        - "mild": 2-5% in 6-12 mo OR 2-5 kg in 6 mo
        - "moderate": ≥5% in 6-12 mo
        - "severe": ≥10% in 6 mo OR ≥5% in 1 mo
        - "rapid": ≥5 kg in ≤1 mo OR ≥2 kg/week

        Args:
            direction: "gain" or "loss"
            magnitude_kg: Weight change in kg
            months: Time period in months
            pct_change_6mo: % change over 6 months (if known)

        Returns:
            Severity tier string
        """
        if not direction or magnitude_kg <= 0 or months <= 0:
            return "none"

        # Calculate rate
        rate_kg_per_mo = magnitude_kg / months
        rate_kg_per_week = rate_kg_per_mo / 4.0

        # Severe thresholds (highest priority)
        if pct_change_6mo is not None:
            if pct_change_6mo >= 10.0:  # ≥10% in 6 mo
                return "severe"
            if months <= 1.0 and pct_change_6mo >= 5.0:  # ≥5% in 1 mo
                return "severe"

        # Rapid change (fluid shifts, acute illness)
        if months <= 1.0 and magnitude_kg >= 5.0:  # ≥5 kg in ≤1 mo
            return "rapid"
        if rate_kg_per_week >= 2.0:  # ≥2 kg/week
            return "rapid"

        # Moderate threshold
        if pct_change_6mo is not None and pct_change_6mo >= 5.0:
            return "moderate"

        # Mild threshold (use absolute thresholds if % unknown)
        if pct_change_6mo is not None:
            if 2.0 <= pct_change_6mo < 5.0:
                return "mild"
        else:
            # Fallback to absolute thresholds
            if months <= 6.0 and 2.0 <= magnitude_kg < 5.0:
                return "mild"
            if months <= 12.0 and magnitude_kg >= 2.0:
                return "mild"

        return "none"

    def get_weight_change_details_weights(
        self,
        text: str,
        baseline_weight_kg: Optional[float] = None,
        has_diarrhea: bool = False,
        has_steatorrhea: bool = False,
        has_abdominal_pain: bool = False,
        has_ibd_celiac: bool = False,
        has_thyrotoxic_symptoms: bool = False,
        has_post_infectious: bool = False,
        has_reflux: bool = False,
        has_late_meals: bool = False,
        on_steroids: bool = False,
        on_antipsychotics: bool = False,
        has_central_adiposity: bool = False,
        has_edema: bool = False,
        has_sob: bool = False,
        has_blood_in_stool: bool = False,
        has_night_sweats: bool = False,
        has_fever: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Score Field 42: Unintentional Weight Change Details.

        Args:
            text: Free-text description of weight change
            baseline_weight_kg: Baseline weight in kg (if known from demographics)
            has_diarrhea: Diarrhea present (from Phase 2 GI symptoms)
            has_steatorrhea: Steatorrhea/fatty stools (from Phase 2)
            has_abdominal_pain: Persistent abdominal pain (from Phase 2)
            has_ibd_celiac: IBD or celiac history (from diagnoses)
            has_thyrotoxic_symptoms: Heat intolerance, tremor (from symptoms)
            has_post_infectious: Recent infection onset (from trigger events)
            has_reflux: Reflux/heartburn (from Phase 2 or Field 29)
            has_late_meals: Late meals mentioned (from Field 16)
            on_steroids: Steroid use (from medications)
            on_antipsychotics: Antipsychotic use (from medications)
            has_central_adiposity: Central adiposity described (from Phase 1)
            has_edema: Edema/ankle swelling (from Phase 2)
            has_sob: Shortness of breath (from Phase 2)
            has_blood_in_stool: Blood in stool (from Phase 2)
            has_night_sweats: Night sweats (from Phase 2)
            has_fever: Fever (from Phase 2)

        Returns:
            Tuple of (scores_dict, flags_list)
        """
        scores = {
            "GA": 0.0,
            "CM": 0.0,
            "HRM": 0.0,
            "MITO": 0.0,
            "COG": 0.0,
            "STR": 0.0,
            "IMM": 0.0,
            "DTX": 0.0,
            "SKN": 0.0
        }

        flags = []

        # Parse the text
        parsed = self._parse_weight_change(text)

        direction = parsed["direction"]
        magnitude_kg = parsed["magnitude_kg"]
        months = parsed["months"]
        is_intentional = parsed["is_intentional"]

        # If intentional, return neutral scores
        if is_intentional:
            flags.append("ℹ️  Field 42: Weight change appears intentional (dieting/exercise) → neutral scoring")
            return scores, flags

        # If no valid data extracted, return neutral
        if not direction or magnitude_kg <= 0 or months <= 0:
            flags.append("⚠️  Field 42: Could not parse weight change details from text")
            return scores, flags

        # Calculate % change if baseline known
        pct_change_6mo = self._calculate_percent_change(magnitude_kg, months, baseline_weight_kg)

        # Determine severity tier
        severity = self._get_severity_tier(direction, magnitude_kg, months, pct_change_6mo)

        # Log parsed data
        flags.append(f"ℹ️  Field 42: Parsed → {direction} {magnitude_kg:.1f} kg over {months:.1f} months")
        if pct_change_6mo is not None:
            flags.append(f"ℹ️  Field 42: % change (6-mo rate): {pct_change_6mo:.1f}%")
        flags.append(f"ℹ️  Field 42: Severity tier: {severity}")

        # Apply base scores based on direction and severity
        if direction == "loss":
            scores = self._score_weight_loss(severity, scores, flags)
            scores = self._apply_loss_amplifiers(
                scores, flags,
                has_diarrhea, has_steatorrhea, has_abdominal_pain, has_ibd_celiac,
                has_thyrotoxic_symptoms, has_post_infectious
            )
        elif direction == "gain":
            scores = self._score_weight_gain(severity, scores, flags)
            scores = self._apply_gain_amplifiers(
                scores, flags,
                has_reflux, has_late_meals, on_steroids, on_antipsychotics,
                has_central_adiposity
            )

        # Red-flag routing
        self._check_red_flags(
            severity, direction, magnitude_kg, months,
            has_edema, has_sob, on_steroids,
            has_diarrhea, has_blood_in_stool, has_night_sweats, has_fever,
            flags
        )

        return scores, flags

    def _score_weight_loss(
        self,
        severity: str,
        scores: Dict[str, float],
        flags: List[str]
    ) -> Dict[str, float]:
        """
        Apply base scores for unintentional weight loss.

        Severity tiers:
        - mild: Loss 2-5% in ≤6-12 mo OR 2-5 kg in ≤6 mo
        - moderate: Loss ≥5% in ≤6-12 mo
        - severe: Loss ≥10%/6 mo or ≥5%/1 mo
        """
        if severity == "mild":
            scores["GA"] += 0.2
            scores["CM"] += 0.1
            scores["HRM"] += 0.1
            scores["MITO"] += 0.3
            scores["COG"] += 0.1
            scores["STR"] += 0.1
            scores["IMM"] += 0.1
            flags.append("→ Weight loss (mild): Early catabolic signal; screen GI/endocrine")

        elif severity == "moderate":
            scores["GA"] += 0.4
            scores["CM"] += 0.2
            scores["HRM"] += 0.2
            scores["MITO"] += 0.6
            scores["COG"] += 0.2
            scores["STR"] += 0.2
            scores["IMM"] += 0.3
            flags.append("→ Weight loss (moderate): Clinically significant; consider malignancy, GI, endocrine, infection")

        elif severity in ["severe", "rapid"]:
            scores["GA"] += 0.6
            scores["CM"] += 0.3
            scores["HRM"] += 0.2
            scores["MITO"] += 0.8
            scores["COG"] += 0.3
            scores["STR"] += 0.3
            scores["IMM"] += 0.4
            flags.append("→ Weight loss (severe): Severe nutritional risk; escalate for medical review")

        return scores

    def _score_weight_gain(
        self,
        severity: str,
        scores: Dict[str, float],
        flags: List[str]
    ) -> Dict[str, float]:
        """
        Apply base scores for unintentional weight gain.

        Severity tiers:
        - mild: Gain 2-5% in ≤6-12 mo OR 2-5 kg in ≤6 mo
        - moderate: Gain >5% in ≤6-12 mo
        - severe: Gain ≥10% in 6 mo (very high cardiometabolic risk)
        - rapid: Rapid gain ≥5 kg in ≤1 mo or ≥2 kg/week
        """
        if severity == "mild":
            scores["GA"] += 0.1
            scores["CM"] += 0.3
            scores["HRM"] += 0.1
            scores["MITO"] += 0.1
            flags.append("→ Weight gain (mild): Early insulin-resistance risk; reinforce lifestyle")

        elif severity == "moderate":
            scores["GA"] += 0.2
            scores["CM"] += 0.6
            scores["HRM"] += 0.2
            scores["MITO"] += 0.2
            flags.append("→ Weight gain (moderate): Higher cardiometabolic risk; NAFLD watch")

        elif severity == "severe":
            # Severe weight gain (≥10% in 6 mo) - very high cardiometabolic risk
            scores["GA"] += 0.3
            scores["CM"] += 0.9
            scores["HRM"] += 0.3
            scores["MITO"] += 0.3
            scores["STR"] += 0.1
            flags.append("→ Weight gain (severe): Very high cardiometabolic risk; screen for metabolic syndrome, NAFLD")

        elif severity == "rapid":
            scores["GA"] += 0.2
            scores["CM"] += 0.8
            scores["HRM"] += 0.2
            scores["MITO"] += 0.3
            scores["STR"] += 0.1
            flags.append("→ Weight gain (rapid): Screen for fluid retention (cardiac/renal/hepatic), hypothyroidism, meds")

        return scores

    def _apply_loss_amplifiers(
        self,
        scores: Dict[str, float],
        flags: List[str],
        has_diarrhea: bool,
        has_steatorrhea: bool,
        has_abdominal_pain: bool,
        has_ibd_celiac: bool,
        has_thyrotoxic_symptoms: bool,
        has_post_infectious: bool
    ) -> Dict[str, float]:
        """Apply amplifiers for weight loss based on cross-field context."""

        # Malabsorption/IBD amplifier
        if has_diarrhea or has_steatorrhea or has_abdominal_pain or has_ibd_celiac:
            scores["GA"] += 0.2
            flags.append("  + Amplifier: GI symptoms/IBD → GA +0.2 (malabsorption risk)")

        # Hyperthyroidism amplifier
        if has_thyrotoxic_symptoms:
            scores["HRM"] += 0.2
            flags.append("  + Amplifier: Thyrotoxic symptoms → HRM +0.2 (hyperthyroidism screen)")

        # Post-infectious amplifier
        if has_post_infectious:
            scores["IMM"] += 0.1
            scores["GA"] += 0.1
            flags.append("  + Amplifier: Post-infectious onset → IMM +0.1, GA +0.1")

        return scores

    def _apply_gain_amplifiers(
        self,
        scores: Dict[str, float],
        flags: List[str],
        has_reflux: bool,
        has_late_meals: bool,
        on_steroids: bool,
        on_antipsychotics: bool,
        has_central_adiposity: bool
    ) -> Dict[str, float]:
        """Apply amplifiers for weight gain based on cross-field context."""

        # Reflux + late meals amplifier
        if has_reflux and has_late_meals:
            scores["GA"] += 0.1
            flags.append("  + Amplifier: Reflux + late meals → GA +0.1 (aerodigestive)")

        # Medication amplifier (steroids, antipsychotics)
        if on_steroids or on_antipsychotics:
            scores["CM"] += 0.1
            scores["MITO"] += 0.1
            flags.append("  + Amplifier: Steroid/antipsychotic use → CM +0.1, MITO +0.1 (appetite/fluid effects)")

        # Central adiposity amplifier
        if has_central_adiposity:
            scores["CM"] += 0.1
            flags.append("  + Amplifier: Central adiposity → CM +0.1 (visceral fat risk)")

        return scores

    def _check_red_flags(
        self,
        severity: str,
        direction: str,
        magnitude_kg: float,
        months: float,
        has_edema: bool,
        has_sob: bool,
        on_steroids: bool,
        has_diarrhea: bool,
        has_blood_in_stool: bool,
        has_night_sweats: bool,
        has_fever: bool,
        flags: List[str]
    ) -> None:
        """Check for red-flag conditions requiring medical review."""

        # Severe weight loss
        if direction == "loss" and severity in ["severe", "rapid"]:
            flags.append("🚨 RED FLAG: Severe weight loss (≥10% in 6 mo or ≥5% in 1 mo) → suggest medical review")

        # Rapid weight gain with fluid retention
        if direction == "gain" and severity == "rapid":
            if has_edema or has_sob:
                flags.append("🚨 RED FLAG: Rapid weight gain + edema/SOB → evaluate for cardiac/renal/hepatic fluid retention")
            if on_steroids:
                flags.append("🚨 RED FLAG: Rapid weight gain + high-dose steroids → evaluate for medication effect")

        # Weight loss with concerning symptoms
        if direction == "loss":
            if has_diarrhea and has_blood_in_stool:
                flags.append("🚨 RED FLAG: Weight loss + diarrhea + blood in stool → evaluate for GI disease, IBD, malignancy")
            if has_night_sweats or has_fever:
                flags.append("🚨 RED FLAG: Weight loss + night sweats/fever → evaluate for infection, malignancy")


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("FIELD 42: UNINTENTIONAL WEIGHT CHANGE DETAILS - TEST SUITE")
    print("="*80)

    ruleset = UnintentionalWeightChangeDetailsRuleset()

    test_cases = [
        # Weight loss cases
        {
            "text": "Lost 10 lb in 2 months",
            "baseline_kg": 70.0,
            "description": "Moderate weight loss (10 lb / 2 mo)",
            "context": {}
        },
        {
            "text": "Dropped 5 kg over 6 months",
            "baseline_kg": 80.0,
            "description": "Mild weight loss (5 kg / 6 mo)",
            "context": {"has_diarrhea": True}
        },
        {
            "text": "Lost 15 pounds in 1 month",
            "baseline_kg": 90.0,
            "description": "Severe rapid weight loss",
            "context": {"has_night_sweats": True, "has_fever": True}
        },
        # Weight gain cases
        {
            "text": "Gained 10 lb in 3 months",
            "baseline_kg": 70.0,
            "description": "Moderate weight gain",
            "context": {}
        },
        {
            "text": "Put on 6 kg in 1 month",
            "baseline_kg": 75.0,
            "description": "Rapid weight gain",
            "context": {"has_edema": True, "has_sob": True}
        },
        # Edge cases
        {
            "text": "Trying to lose weight, lost 5 lb in 2 months",
            "baseline_kg": 80.0,
            "description": "Intentional weight loss (should be neutral)",
            "context": {}
        },
        {
            "text": "Not sure, maybe a few pounds",
            "baseline_kg": 70.0,
            "description": "Vague description (should fail to parse)",
            "context": {}
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {test['description']}")
        print(f"{'='*80}")
        print(f"Input: '{test['text']}'")
        print(f"Baseline weight: {test['baseline_kg']} kg")

        scores, flags = ruleset.get_weight_change_details_weights(
            test["text"],
            baseline_weight_kg=test["baseline_kg"],
            **test["context"]
        )

        print("\nScores:")
        for fa, score in scores.items():
            if score > 0:
                print(f"  {fa}: {score:+.2f}")
        if all(s == 0 for s in scores.values()):
            print("  (All zeros)")

        if flags:
            print("\nFlags:")
            for flag in flags:
                print(f"  {flag}")

    print("\n" + "="*80)
    print("✅ Field 42 test suite complete")
    print("="*80)

