"""
Transit Time Ruleset (Field 43) - Phase 3

Evaluates bowel transit time from beet/charcoal test results.
Parses free text like "24 h beet test", "~2 days", "not measured".

UI: Short text field for transit time measurement results.

Evidence base:
- Lewis & Heaton 1997: Bristol scale correlates with transit time
- Normal whole-gut transit: 12-36 hours in healthy adults
- SIBO risk with slow transit (stasis)
- Malabsorption risk with rapid transit
"""

from typing import Dict, List, Tuple, Optional
import re


class TransitTimeRuleset:
    """
    Ruleset for evaluating bowel transit time from beet/charcoal tests.
    
    Parses text input, classifies transit speed, and generates focus area weights.
    Integrates with Bristol stool type for cross-validation.
    """
    
    # Domain caps for this field
    DOMAIN_CAPS = {
        "GA": 0.80,   # Primary domain for GI transit issues
        "DTX": 0.40,  # Secondary (enterohepatic circulation)
        "IMM": 0.30,  # Inflammation component
        "CM": 0.20,   # Metabolic effects
        "MITO": 0.30  # Energy/catabolic effects
    }
    
    # Bristol type keywords (for cross-signal when time not measured)
    BRISTOL_KEYWORDS = {
        "slow": ["hard", "lumpy", "pebble", "rabbit", "hard to pass", "constipated",
                 "type 1", "type 2", "type1", "type2"],
        "normal": ["smooth sausage", "like a snake", "log", "normal",
                   "type 3", "type 4", "type3", "type4"],
        "rapid": ["soft blobs", "mushy", "watery", "diarrhea", "loose",
                  "type 5", "type 6", "type 7", "type5", "type6", "type7"]
    }
    
    # Colloquial time phrases
    TIME_PHRASES = {
        "couple of hours": 2,
        "few hours": 4,
        "several hours": 6,
        "half a day": 12,
        "half day": 12,
        "one day": 24,
        "a day": 24,
        "two days": 48,
        "three days": 72,
        "weekend": 48,
        "week": 168
    }
    
    # Red flag keywords (safety alerts)
    RED_FLAG_KEYWORDS = {
        "blood": ["blood", "bloody", "bright red", "red streaks"],
        "melena": ["black tarry", "tarry stool", "black stool", "melena"],
        "fever": ["fever", "febrile", "temperature"],
        "weight_loss": ["unintentional weight loss", "losing weight", "weight dropping"]
    }
    
    # Medication keywords
    OPIOID_ANTICHOLINERGIC_KEYWORDS = ["opioid", "morphine", "oxycodone", "hydrocodone",
                                        "anticholinergic", "atropine", "scopolamine"]
    PROKINETIC_KEYWORDS = ["magnesium citrate", "metformin", "caffeine"]
    
    def __init__(self):
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, strip extra whitespace."""
        if not text:
            return ""
        return text.lower().strip()
    
    def _parse_transit_time(self, text: str) -> Optional[float]:
        """
        Parse transit time from text and convert to hours.
        
        Returns:
            Transit time in hours, or None if not measurable
            
        Examples:
            "24 h beet test" → 24.0
            "~2 days" → 48.0
            "18-24 h" → 21.0 (midpoint)
            "not measured" → None
        """
        text_l = self._normalize_text(text)
        
        # Check for "not measured" / "don't know"
        if any(phrase in text_l for phrase in ["not measured", "don't know", "didn't measure",
                                                 "haven't tested", "no test", "unknown"]):
            return None
        
        # Try colloquial phrases first
        for phrase, hours in self.TIME_PHRASES.items():
            if phrase in text_l:
                return float(hours)
        
        # Pattern 1: Range (e.g., "18-24 h", "1-2 days")
        m = re.search(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*(h|hr|hour|d|day)', text_l)
        if m:
            low = float(m.group(1))
            high = float(m.group(2))
            unit = m.group(3)
            
            midpoint = (low + high) / 2
            
            # Convert to hours
            if unit.startswith('d'):
                return midpoint * 24
            else:
                return midpoint
        
        # Pattern 2: Single value with unit (e.g., "24 h", "2 days", "~36 hours")
        m = re.search(r'[~≈]?\s*(\d+(?:\.\d+)?)\s*(h|hr|hour|d|day)', text_l)
        if m:
            value = float(m.group(1))
            unit = m.group(2)
            
            # Convert to hours
            if unit.startswith('d'):
                return value * 24
            else:
                return value
        
        return None
    
    def _detect_bristol_category(self, text: str) -> Optional[str]:
        """
        Detect Bristol stool category from text.
        
        Returns:
            "slow", "normal", "rapid", or None
        """
        text_l = self._normalize_text(text)
        
        for category, keywords in self.BRISTOL_KEYWORDS.items():
            if any(kw in text_l for kw in keywords):
                return category
        
        return None
    
    def _detect_red_flags(self, text: str) -> List[str]:
        """
        Detect red flag symptoms requiring urgent evaluation.

        Returns:
            List of red flag types detected
        """
        text_l = self._normalize_text(text)
        detected = []

        for flag_type, keywords in self.RED_FLAG_KEYWORDS.items():
            if any(kw in text_l for kw in keywords):
                detected.append(flag_type)

        return detected

    def _classify_transit_speed(self, hours: float) -> str:
        """
        Classify transit time into speed categories.

        Args:
            hours: Transit time in hours

        Returns:
            "very_rapid", "rapid", "normal", "slow", or "very_slow"
        """
        if hours < 2:
            return "very_rapid"
        elif hours < 12:
            return "rapid"
        elif hours <= 36:
            return "normal"
        elif hours <= 72:
            return "slow"
        else:
            return "very_slow"

    def _score_transit_time(self, hours: float, bristol_category: Optional[str] = None) -> Dict[str, float]:
        """
        Score based on measured transit time.

        Args:
            hours: Transit time in hours
            bristol_category: Optional Bristol category for cross-validation

        Returns:
            Dict of focus area weights
        """
        scores = {}
        speed = self._classify_transit_speed(hours)

        # Step 1: Base scoring by transit speed
        if speed == "very_rapid":  # < 2 h
            scores["GA"] = 0.45   # Rapid transit → malabsorption, bile-acid/secretory diarrhea
            scores["MITO"] = 0.20  # Catabolic/energy drag from losses
            scores["DTX"] = 0.10   # Reduced enterohepatic time
            scores["IMM"] = 0.10   # Mucosal irritation

        elif speed == "rapid":  # 2-12 h
            scores["GA"] = 0.30
            scores["MITO"] = 0.15
            scores["IMM"] = 0.10

        elif speed == "normal":  # 12-36 h
            # No change (baseline)
            pass

        elif speed == "slow":  # 36-72 h
            scores["GA"] = 0.40   # Stasis/SIBO risk
            scores["DTX"] = 0.25  # Prolonged contact with xenobiotics
            scores["IMM"] = 0.15
            scores["CM"] = 0.10

        elif speed == "very_slow":  # > 72 h
            scores["GA"] = 0.50
            scores["DTX"] = 0.30
            scores["IMM"] = 0.20
            scores["CM"] = 0.15

        # Step 2: Bristol cross-validation bonus
        if bristol_category == "slow" and speed in ["slow", "very_slow"]:
            # Bristol Type 1-2 with slow transit
            scores["GA"] = scores.get("GA", 0) + 0.10

        elif bristol_category == "rapid" and speed in ["rapid", "very_rapid"]:
            # Bristol Type 6-7 with rapid transit
            scores["GA"] = scores.get("GA", 0) + 0.10

        return scores

    def _score_bristol_only(self, bristol_category: str) -> Dict[str, float]:
        """
        Score based on Bristol category when transit time not measured.

        Args:
            bristol_category: "slow", "normal", or "rapid"

        Returns:
            Dict of focus area weights
        """
        scores = {}

        if bristol_category == "slow":  # Type 1-2
            scores["GA"] = 0.20
        elif bristol_category == "rapid":  # Type 6-7
            scores["GA"] = 0.20
        # Normal (Type 3-4) → no change

        return scores

    def _apply_modifiers(
        self,
        scores: Dict[str, float],
        text: str,
        hours: Optional[float],
        cholecystectomy: bool = False,
        diabetes: bool = False,
        medications: List[str] = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Apply contextual modifiers based on medical history and medications.

        Args:
            scores: Current scores dict
            text: Original text input
            hours: Transit time in hours (or None)
            cholecystectomy: History of gallbladder removal
            diabetes: History of diabetes
            medications: List of current medications

        Returns:
            Tuple of (updated scores, flags list)
        """
        flags = []
        text_l = self._normalize_text(text)
        meds_text = " ".join(medications or []).lower()

        # Cholecystectomy + rapid transit → bile-acid diarrhea risk
        if cholecystectomy and hours is not None and hours < 12:
            scores["GA"] = scores.get("GA", 0) + 0.10
            flags.append("Rapid transit post-cholecystectomy - consider bile-acid diarrhea screen")

        # Diabetes + very slow transit → gastroparesis risk
        if diabetes and hours is not None and hours > 72:
            scores["GA"] = scores.get("GA", 0) + 0.10
            flags.append("Very slow transit with diabetes - possible gastroparesis, queue evaluation")

        # Opioids/anticholinergics + slow transit → drug-induced hypomotility
        if hours is not None and hours > 36:
            if any(kw in meds_text for kw in self.OPIOID_ANTICHOLINERGIC_KEYWORDS):
                scores["GA"] = scores.get("GA", 0) + 0.05
                flags.append("Slow transit with opioid/anticholinergic use - drug-induced hypomotility")

        # Prokinetic meds + rapid transit
        if hours is not None and hours < 12:
            if any(kw in meds_text for kw in self.PROKINETIC_KEYWORDS):
                scores["GA"] = scores.get("GA", 0) + 0.05
                flags.append("Rapid transit with prokinetic medication use")

        return scores, flags

    def get_transit_time_weights(
        self,
        transit_text: str,
        cholecystectomy: bool = False,
        diabetes: bool = False,
        medications: List[str] = None,
        phase2_digestive_symptoms: str = ""
    ) -> Tuple[Dict[str, float], List[str], List[Dict]]:
        """
        Calculate focus area weights based on transit time measurement.

        Args:
            transit_text: Free text describing transit time (e.g., "24 h beet test", "~2 days")
            cholecystectomy: History of gallbladder removal
            diabetes: History of diabetes
            medications: List of current medications
            phase2_digestive_symptoms: Digestive symptoms from Phase 2 (for context)

        Returns:
            Tuple of (weights dict, flags list, alerts list)

        Example:
            >>> ruleset = TransitTimeRuleset()
            >>> weights, flags, alerts = ruleset.get_transit_time_weights(
            ...     "24 h beet test",
            ...     cholecystectomy=False,
            ...     diabetes=False
            ... )
            >>> weights["GA"]
            0.0  # Normal transit (12-36h)
        """
        weights = {}
        flags = []
        alerts = []

        # Handle empty input
        if not transit_text or transit_text.strip() == "":
            return (weights, flags, alerts)

        # Step 1: Parse transit time
        hours = self._parse_transit_time(transit_text)

        # Step 2: Detect Bristol category (for cross-validation or fallback)
        bristol_category = self._detect_bristol_category(transit_text)

        # Step 3: Check for red flags (safety alerts)
        red_flags = self._detect_red_flags(transit_text)
        if red_flags:
            for flag_type in red_flags:
                if flag_type == "blood":
                    alerts.append({
                        "type": "blood_in_stool",
                        "severity": "urgent",
                        "message": "Visible blood in stool requires urgent clinical evaluation"
                    })
                elif flag_type == "melena":
                    alerts.append({
                        "type": "melena",
                        "severity": "urgent",
                        "message": "Black/tarry stool may indicate GI bleeding - urgent evaluation needed"
                    })
                elif flag_type == "fever":
                    alerts.append({
                        "type": "fever_with_gi_symptoms",
                        "severity": "urgent",
                        "message": "Fever with GI symptoms requires medical evaluation"
                    })
                elif flag_type == "weight_loss":
                    alerts.append({
                        "type": "unintentional_weight_loss",
                        "severity": "urgent",
                        "message": "Unintentional weight loss with GI symptoms requires evaluation"
                    })

            # Add IMM weight for red flags
            weights["IMM"] = weights.get("IMM", 0) + 0.20

        # Step 4: Score based on transit time or Bristol category
        if hours is not None:
            # Measured transit time available
            transit_scores = self._score_transit_time(hours, bristol_category)
            for domain, score in transit_scores.items():
                weights[domain] = weights.get(domain, 0) + score

            # Add classification flag
            speed = self._classify_transit_speed(hours)
            if speed != "normal":
                flags.append(f"{speed.replace('_', ' ').title()} transit detected ({hours:.1f} hours)")

        elif bristol_category is not None:
            # No measured time, but Bristol category available
            bristol_scores = self._score_bristol_only(bristol_category)
            for domain, score in bristol_scores.items():
                weights[domain] = weights.get(domain, 0) + score

            flags.append(f"Transit time not measured - inferred {bristol_category} transit from stool form")

        # Step 5: Apply modifiers (medical history, medications)
        if hours is not None or bristol_category is not None:
            weights, modifier_flags = self._apply_modifiers(
                weights,
                transit_text,
                hours,
                cholecystectomy,
                diabetes,
                medications
            )
            flags.extend(modifier_flags)

        # Step 6: Apply domain caps
        for domain in weights:
            if domain in self.DOMAIN_CAPS:
                weights[domain] = min(weights[domain], self.DOMAIN_CAPS[domain])

        return (weights, flags, alerts)

