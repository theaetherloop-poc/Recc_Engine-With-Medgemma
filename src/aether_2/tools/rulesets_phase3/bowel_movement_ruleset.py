"""
Bowel Movement Frequency & Characteristics Ruleset (Field 42) - Phase 3

Evaluates bowel movement patterns, stool characteristics, and associated symptoms.
Uses Phase 2 digestive_symptoms as pre-filter to determine what to parse.

UI: Free text field with prompts for:
- Frequency (e.g., "every 2-3 days", "3x/day")
- Bristol type (stool form)
- Symptoms (bloating, heartburn, blood, mucus, etc.)
- Context (travel, stress, foods)
- Anorectal symptoms (hemorrhoids, fissures, prolapse)
"""

from typing import Dict, List, Tuple, Any, Optional
import re


class BowelMovementRuleset:
    """
    Ruleset for evaluating bowel movement patterns and characteristics.
    
    Pre-filtered by Phase 2 digestive_symptoms field.
    Only parses relevant sections based on what symptoms are present.
    """
    
    # Domain caps for this field
    DOMAIN_CAPS = {
        "GA": 2.5,
        "DTX": 1.0,
        "CM": 0.5,
        "IMM": 0.5,
        "MITO": 0.5,
        "HRM": 0.3,
        "STR": 0.3
    }
    
    # Bristol type keywords (Type 1-7)
    BRISTOL_KEYWORDS = {
        1: ["rabbit pellets", "hard lumps", "pebbles", "marbles", "separate hard lumps",
            "nuts", "hard balls", "like rocks"],
        2: ["lumpy sausage", "hard lumpy log", "bumpy sausage", "lumpy log",
            "sausage-shaped but lumpy", "hard sausage"],
        3: ["sausage with cracks", "cracked log", "sausage-like with cracks on surface",
            "cracked sausage"],
        4: ["smooth snake", "smooth sausage", "like a snake", "smooth and soft",
            "smooth log", "normal sausage"],
        5: ["soft blobs", "soft pieces", "clear-cut edges", "soft blobs with clear edges",
            "mushy blobs"],
        6: ["mushy", "porridge stool", "fluffy pieces", "ragged edges", "mushy stool"],
        7: ["watery", "liquid", "diarrhea", "no solid pieces", "entirely liquid",
            "water-like", "explosive"]
    }
    
    # Negation words to avoid false positives
    NEGATION_WORDS = ["no", "not", "without", "never", "denies", "none", "absent"]
    
    # Stool modifier keywords
    STEATORRHEA_KEYWORDS = ["greasy", "oily", "floats", "hard to flush", "foul smelling",
                            "fatty stool", "shiny", "sticks to toilet"]
    BLOOD_KEYWORDS = ["blood", "bloody", "bright red", "red streaks"]
    MELENA_KEYWORDS = ["black tarry", "jet black stool", "tarry", "black stool", "melena"]
    MUCUS_KEYWORDS = ["mucus", "slimy", "mucousy", "jelly-like"]
    
    # Bloating timing keywords
    BLOATING_EARLY_KEYWORDS = ["within 2 hours", "right after eating", "immediately after",
                               "soon after", "after meals", "≤2 h", "<2 h", "within 1 hour"]
    BLOATING_LATE_KEYWORDS = ["more than 2 hours", "3 hours after", "hours after eating",
                              ">2 h", "evening bloating", "4 hours after", "later in day"]
    BLOATING_VARIABLE_KEYWORDS = ["variable", "sometimes", "inconsistent", "depends"]
    
    # Heartburn keywords
    GERD_KEYWORDS = ["gerd", "persistent reflux", "chronic reflux", "daily heartburn",
                     "constant heartburn", "severe heartburn"]
    OCCASIONAL_HEARTBURN_KEYWORDS = ["occasional heartburn", "sometimes heartburn",
                                     "rare heartburn", "infrequent heartburn"]
    
    # Constipation context keywords
    TRAVEL_KEYWORDS = ["after travel", "when traveling", "during travel", "trip", "vacation"]
    STRESS_KEYWORDS = ["after stress", "when stressed", "high stress", "anxiety", "anxious"]
    TRAUMA_KEYWORDS = ["after trauma", "traumatic event", "post-trauma"]
    FOOD_KEYWORDS = ["after eating", "dairy", "gluten", "wheat", "fodmap", "certain foods"]
    
    # Anorectal keywords
    HEMORRHOIDS_KEYWORDS = ["hemorrhoids", "haemorrhoids", "piles"]
    FISSURES_KEYWORDS = ["fissure", "anal tear", "painful bowel", "tear", "anal fissure"]
    PROLAPSE_KEYWORDS = ["prolapse", "rectal prolapse", "tissue protruding"]
    
    # Loose/watery keywords (for diarrhea classification)
    LOOSE_WATERY_KEYWORDS = ["loose", "watery", "liquid", "runny", "diarrhea", "diarrhoea",
                             "urgent", "explosive", "can't hold it"]
    
    # Variability keywords
    VARIABILITY_KEYWORDS = ["variable", "varies", "alternating",
                            "sometimes constipated sometimes diarrhea",
                            "inconsistent", "unpredictable", "changes", "fluctuates"]
    
    def __init__(self):
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, strip extra whitespace."""
        if not text:
            return ""
        return text.lower().strip()
    
    def _check_negation(self, text: str, keyword_pos: int, window_size: int = 35) -> bool:
        """
        Check if a keyword is negated by looking at words before it.

        Args:
            text: Full text
            keyword_pos: Position of keyword in text
            window_size: Number of characters to look back

        Returns:
            True if negation found, False otherwise
        """
        start_pos = max(0, keyword_pos - window_size)
        window = text[start_pos:keyword_pos]
        window_words = window.split()

        return any(neg in window_words for neg in self.NEGATION_WORDS)

    def _parse_frequency(self, text: str) -> Optional[float]:
        """
        Parse bowel movement frequency from text.

        Returns:
            BMs per day (float) or None if not parseable

        Examples:
            "every 2-3 days" → 0.41 (midpoint of 1/3 and 1/2)
            "3/day" → 3.0
            "twice a day" → 2.0
            "every other day" → 0.5
        """
        text_l = self._normalize_text(text)

        # Pattern 1: "every N days" or "every N-M days"
        m = re.search(r'every\s+(\d+(?:\.\d+)?)\s*[-–]?\s*(\d+(?:\.\d+)?)?\s*days?', text_l)
        if m:
            if m.group(2):  # Range
                low = 1 / float(m.group(1))
                high = 1 / float(m.group(2))
                return (low + high) / 2
            else:  # Single value
                return 1 / float(m.group(1))

        # Pattern 2: "N/day" or "N per day"
        m = re.search(r'(\d+(?:\.\d+)?)\s*/\s*(?:d|day)\b', text_l)
        if m:
            return float(m.group(1))

        # Pattern 3: "N times per day/week"
        m = re.search(r'(\d+)\s*(?:x|times?)\s*(?:per\s*)?(day|week)', text_l)
        if m:
            n = float(m.group(1))
            unit = m.group(2)
            return n if unit == 'day' else n / 7

        # Pattern 4: Colloquial phrases
        if re.search(r'\bdaily\b|\bevery day\b|\bonce a day\b', text_l):
            return 1.0
        if re.search(r'\btwice a day\b|\bbid\b|2x\s*(?:a\s*)?day', text_l):
            return 2.0
        if re.search(r'\bevery other day\b|\bqod\b', text_l):
            return 0.5

        # Pattern 5: Acute constipation
        m = re.search(r'no bm for\s*(\d+)\s*days?', text_l)
        if m:
            return 0.0

        # Pattern 6: Diarrhea phrases
        if re.search(r'many loose stools|going all day|constant diarrhea', text_l):
            return 3.5

        return None

    def _detect_bristol(self, text: str) -> Optional[int]:
        """
        Detect Bristol stool type from text.

        Returns:
            Bristol type (1-7) or None if not detected
        """
        text_l = self._normalize_text(text)
        hits = []

        for bristol_type in range(1, 8):
            for keyword in self.BRISTOL_KEYWORDS[bristol_type]:
                # Find all occurrences
                for match in re.finditer(re.escape(keyword), text_l):
                    # Check for negation
                    if self._check_negation(text_l, match.start()):
                        continue

                    hits.append(bristol_type)
                    break  # Move to next type

        if not hits:
            return None

        # Return most common (or first if tie)
        return max(set(hits), key=hits.count)

    def _detect_stool_modifiers(self, text: str) -> Dict[str, bool]:
        """
        Detect stool modifiers (steatorrhea, blood, melena, mucus).

        Returns:
            Dict with boolean flags for each modifier
        """
        text_l = self._normalize_text(text)
        detected = {}

        # Steatorrhea
        for keyword in self.STEATORRHEA_KEYWORDS:
            if keyword in text_l:
                idx = text_l.find(keyword)
                if not self._check_negation(text_l, idx):
                    detected["steatorrhea"] = True
                    break

        # Blood
        for keyword in self.BLOOD_KEYWORDS:
            if keyword in text_l:
                idx = text_l.find(keyword)
                if not self._check_negation(text_l, idx):
                    detected["blood"] = True
                    break

        # Melena
        for keyword in self.MELENA_KEYWORDS:
            if keyword in text_l:
                idx = text_l.find(keyword)
                if not self._check_negation(text_l, idx):
                    detected["melena"] = True
                    break

        # Mucus
        for keyword in self.MUCUS_KEYWORDS:
            if keyword in text_l:
                idx = text_l.find(keyword)
                if not self._check_negation(text_l, idx):
                    detected["mucus"] = True
                    break

        return detected

    def _detect_bloating_timing(self, text: str) -> Optional[str]:
        """
        Detect bloating timing (early/late/variable).

        Returns:
            "early" (≤2h), "late" (>2h), "variable", or None
        """
        text_l = self._normalize_text(text)

        # Check for specific time mentions first
        m = re.search(r'(\d+)\s*(?:h|hr|hours?)\s*after', text_l)
        if m:
            hours = int(m.group(1))
            return "early" if hours <= 2 else "late"

        # Check keyword categories
        for keyword in self.BLOATING_EARLY_KEYWORDS:
            if keyword in text_l:
                return "early"

        for keyword in self.BLOATING_LATE_KEYWORDS:
            if keyword in text_l:
                return "late"

        for keyword in self.BLOATING_VARIABLE_KEYWORDS:
            if keyword in text_l:
                return "variable"

        return None

    def _detect_heartburn_type(self, text: str) -> Optional[str]:
        """
        Detect heartburn type (gerd/occasional).

        Returns:
            "gerd", "occasional", or None
        """
        text_l = self._normalize_text(text)

        for keyword in self.GERD_KEYWORDS:
            if keyword in text_l:
                return "gerd"

        for keyword in self.OCCASIONAL_HEARTBURN_KEYWORDS:
            if keyword in text_l:
                return "occasional"

        # If just "heartburn" mentioned without qualifier
        if "heartburn" in text_l:
            return "occasional"

        return None

    def _detect_constipation_context(self, text: str) -> List[str]:
        """
        Detect constipation context triggers.

        Returns:
            List of contexts: ["travel", "stress", "trauma", "foods"]
        """
        text_l = self._normalize_text(text)
        detected = []

        if any(kw in text_l for kw in self.TRAVEL_KEYWORDS):
            detected.append("travel")

        if any(kw in text_l for kw in self.STRESS_KEYWORDS):
            detected.append("stress")

        if any(kw in text_l for kw in self.TRAUMA_KEYWORDS):
            detected.append("trauma")

        if any(kw in text_l for kw in self.FOOD_KEYWORDS):
            detected.append("foods")

        return detected

    def _detect_anorectal_symptoms(self, text: str) -> List[str]:
        """
        Detect anorectal symptoms.

        Returns:
            List of symptoms: ["hemorrhoids", "fissures", "prolapse"]
        """
        text_l = self._normalize_text(text)
        detected = []

        if any(kw in text_l for kw in self.HEMORRHOIDS_KEYWORDS):
            detected.append("hemorrhoids")

        if any(kw in text_l for kw in self.FISSURES_KEYWORDS):
            detected.append("fissures")

        if any(kw in text_l for kw in self.PROLAPSE_KEYWORDS):
            detected.append("prolapse")

        return detected

    def _detect_loose_watery(self, text: str) -> bool:
        """Detect loose/watery stool indicators."""
        text_l = self._normalize_text(text)
        return any(kw in text_l for kw in self.LOOSE_WATERY_KEYWORDS)

    def _detect_variability(self, text: str) -> bool:
        """Detect variability in bowel patterns."""
        text_l = self._normalize_text(text)
        return any(kw in text_l for kw in self.VARIABILITY_KEYWORDS)

    def _score_frequency(self, bms_per_day: float, loose_watery: bool, variability: bool) -> Dict[str, float]:
        """
        Score based on bowel movement frequency.

        Returns:
            Dict of focus area weights
        """
        scores = {}

        # Branch 1: Constipation
        if bms_per_day < 1.0:
            if bms_per_day >= 5/7:  # ≥5/week (0.71/day) - MILD
                scores["GA"] = 0.40
                scores["DTX"] = 0.20
                scores["CM"] = 0.10
                scores["MITO"] = 0.10
            elif bms_per_day >= 4/7:  # ≤4/week (0.57/day) - MODERATE
                scores["GA"] = 0.55
                scores["DTX"] = 0.25
                scores["CM"] = 0.15
                scores["MITO"] = 0.15
                scores["HRM"] = 0.10
            else:  # ≤2/week (0.29/day) - SEVERE
                scores["GA"] = 0.70
                scores["DTX"] = 0.30
                scores["CM"] = 0.20
                scores["MITO"] = 0.20
                scores["HRM"] = 0.15

        # Branch 2: Diarrhea
        elif bms_per_day > 3.0 and loose_watery:
            scores["GA"] = 0.50
            scores["IMM"] = 0.25
            scores["MITO"] = 0.30
            scores["DTX"] = 0.15

        # Branch 3: Variability
        if variability:
            scores["GA"] = scores.get("GA", 0) + 0.45
            scores["STR"] = 0.15

        return scores

    def _score_bristol(self, bristol_type: int) -> Dict[str, float]:
        """Score based on Bristol stool type."""
        scores = {}

        if bristol_type in [1, 2]:  # Hard/constipated
            scores["GA"] = 0.30
            scores["DTX"] = 0.10
        elif bristol_type == 5:  # Borderline loose
            scores["GA"] = 0.05
        elif bristol_type == 6:  # Mushy
            scores["GA"] = 0.30
            scores["IMM"] = 0.10
        elif bristol_type == 7:  # Watery
            scores["GA"] = 0.40
            scores["IMM"] = 0.15
        elif bristol_type in [3, 4]:  # Normal (protective)
            scores["GA"] = -0.10

        return scores

    def _score_stool_modifiers(self, modifiers: Dict[str, bool]) -> Tuple[Dict[str, float], List[Dict]]:
        """
        Score stool modifiers and generate safety alerts.

        Returns:
            Tuple of (scores dict, alerts list)
        """
        scores = {}
        alerts = []

        if modifiers.get("steatorrhea"):
            scores["GA"] = 0.30
            scores["DTX"] = 0.10

        if modifiers.get("blood"):
            scores["IMM"] = 0.20
            alerts.append({
                "type": "blood_in_stool",
                "severity": "urgent",
                "message": "Visible blood in stool requires urgent clinical evaluation"
            })

        if modifiers.get("melena"):
            scores["IMM"] = 0.20
            alerts.append({
                "type": "melena",
                "severity": "urgent",
                "message": "Black/tarry stool may indicate GI bleeding - urgent evaluation needed"
            })

        if modifiers.get("mucus"):
            scores["GA"] = 0.20
            scores["IMM"] = 0.15

        return scores, alerts

    def _score_symptoms(
        self,
        bloating_timing: Optional[str],
        heartburn_type: Optional[str],
        constipation_context: List[str],
        anorectal: List[str]
    ) -> Dict[str, float]:
        """Score based on symptoms."""
        scores = {}

        # Bloating
        if bloating_timing == "early":  # ≤2h
            scores["GA"] = scores.get("GA", 0) + 0.20
            scores["DTX"] = scores.get("DTX", 0) + 0.05
        elif bloating_timing == "late":  # >2h
            scores["GA"] = scores.get("GA", 0) + 0.25
            scores["DTX"] = scores.get("DTX", 0) + 0.05
        elif bloating_timing == "variable":
            scores["GA"] = scores.get("GA", 0) + 0.20

        # Heartburn
        if heartburn_type == "gerd":
            scores["GA"] = scores.get("GA", 0) + 0.25
            scores["DTX"] = scores.get("DTX", 0) + 0.10
        elif heartburn_type == "occasional":
            scores["GA"] = scores.get("GA", 0) + 0.10

        # Constipation context
        if "travel" in constipation_context:
            scores["GA"] = scores.get("GA", 0) + 0.20
        if "stress" in constipation_context or "trauma" in constipation_context:
            scores["STR"] = scores.get("STR", 0) + 0.20
            scores["GA"] = scores.get("GA", 0) + 0.10
        if "foods" in constipation_context:
            scores["GA"] = scores.get("GA", 0) + 0.20

        # Anorectal
        if "hemorrhoids" in anorectal:
            scores["GA"] = scores.get("GA", 0) + 0.10
        if "fissures" in anorectal:
            scores["GA"] = scores.get("GA", 0) + 0.15
        if "prolapse" in anorectal:
            scores["GA"] = scores.get("GA", 0) + 0.30

        return scores

    def _should_parse_bowel_details(self, phase2_digestive_symptoms: str) -> Dict[str, bool]:
        """
        Check Phase 2 digestive_symptoms to determine what to parse.

        Args:
            phase2_digestive_symptoms: Comma-separated symptoms from Phase 2

        Returns:
            Dict with parse flags for each section
        """
        if not phase2_digestive_symptoms:
            return {
                "parse_frequency": False,
                "parse_bloating": False,
                "parse_heartburn": False,
                "has_any_gi_symptoms": False
            }

        symptoms_lower = phase2_digestive_symptoms.lower()

        has_bloating = "bloating" in symptoms_lower
        has_heartburn = "heartburn" in symptoms_lower
        has_constipation = "constipation" in symptoms_lower
        has_diarrhea = "diarrhea" in symptoms_lower or "diarrhoea" in symptoms_lower

        return {
            "parse_frequency": has_constipation or has_diarrhea,
            "parse_bloating": has_bloating,
            "parse_heartburn": has_heartburn,
            "has_any_gi_symptoms": any([has_bloating, has_heartburn, has_constipation, has_diarrhea])
        }

    def get_bowel_movement_weights(
        self,
        bowel_text: str,
        phase2_digestive_symptoms: str = ""
    ) -> Tuple[Dict[str, float], List[str], List[Dict]]:
        """
        Calculate focus area weights based on bowel movement patterns.

        Args:
            bowel_text: Free text describing bowel movements
            phase2_digestive_symptoms: Comma-separated symptoms from Phase 2 (pre-filter)

        Returns:
            Tuple of (weights dict, flags list, alerts list)

        Example:
            >>> ruleset = BowelMovementRuleset()
            >>> weights, flags, alerts = ruleset.get_bowel_movement_weights(
            ...     "Every 2-3 days; hard lumpy sausage; bloating 3 hours after meals",
            ...     phase2_digestive_symptoms="bloating,constipation"
            ... )
            >>> weights["GA"]
            2.00
        """
        weights = {}
        flags = []
        alerts = []

        # Handle empty input
        if not bowel_text or bowel_text.strip() == "":
            return (weights, flags, alerts)

        # Pre-filter: Check Phase 2 to see what to parse
        parse_flags = self._should_parse_bowel_details(phase2_digestive_symptoms)

        # If no GI symptoms in Phase 2, skip parsing
        if not parse_flags["has_any_gi_symptoms"]:
            return (weights, flags, alerts)

        # ALWAYS parse (safety-critical)
        bristol_type = self._detect_bristol(bowel_text)
        stool_modifiers = self._detect_stool_modifiers(bowel_text)
        anorectal = self._detect_anorectal_symptoms(bowel_text)

        # CONDITIONAL parsing based on Phase 2
        frequency = None
        loose_watery = False
        variability = False
        bloating_timing = None
        heartburn_type = None
        constipation_context = []

        if parse_flags["parse_frequency"]:
            frequency = self._parse_frequency(bowel_text)
            loose_watery = self._detect_loose_watery(bowel_text)
            variability = self._detect_variability(bowel_text)
            constipation_context = self._detect_constipation_context(bowel_text)

        if parse_flags["parse_bloating"]:
            bloating_timing = self._detect_bloating_timing(bowel_text)

        if parse_flags["parse_heartburn"]:
            heartburn_type = self._detect_heartburn_type(bowel_text)

        # SCORING

        # Frequency scoring (only if parsed)
        if frequency is not None:
            freq_scores = self._score_frequency(frequency, loose_watery, variability)
            for domain, score in freq_scores.items():
                weights[domain] = weights.get(domain, 0) + score

        # Bristol scoring (always if detected)
        if bristol_type is not None:
            bristol_scores = self._score_bristol(bristol_type)
            for domain, score in bristol_scores.items():
                weights[domain] = weights.get(domain, 0) + score

        # Stool modifiers (always)
        modifier_scores, modifier_alerts = self._score_stool_modifiers(stool_modifiers)
        for domain, score in modifier_scores.items():
            weights[domain] = weights.get(domain, 0) + score
        alerts.extend(modifier_alerts)

        # Symptoms (conditional)
        symptom_scores = self._score_symptoms(
            bloating_timing,
            heartburn_type,
            constipation_context,
            anorectal
        )
        for domain, score in symptom_scores.items():
            weights[domain] = weights.get(domain, 0) + score

        # Apply domain caps
        for domain in weights:
            if domain in self.DOMAIN_CAPS:
                weights[domain] = min(weights[domain], self.DOMAIN_CAPS[domain])

        # Generate flags
        if frequency is not None and frequency < 4/7:
            flags.append(f"Moderate-severe constipation detected ({frequency:.2f} BMs/day)")
        if frequency is not None and frequency > 3.0 and loose_watery:
            flags.append(f"Diarrhea detected ({frequency:.2f} BMs/day)")
        if "prolapse" in anorectal:
            flags.append("Rectal prolapse - consider referral to colorectal specialist")

        return (weights, flags, alerts)

