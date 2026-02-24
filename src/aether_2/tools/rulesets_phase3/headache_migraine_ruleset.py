"""
Headache/Migraine Frequency & Triggers Ruleset (Field 44) - Phase 3

Evaluates headache/migraine patterns, frequency, triggers, and medication overuse.
Only applies if Phase 2 frequent_headaches_migraines == true.

UI: Free text field with prompt:
"You previously mentioned you had frequent headaches/migraines. How often and any known triggers?"

Audience: ≥18 years only

Scoring framework:
- Frequency severity (days/month): chronic (≥15), episodic (8-14), infrequent (1-7)
- Triggers: 14+ categories (alcohol, chocolate, cheese, sleep, stress, allergens, etc.)
- Headache type: migraine with/without aura, tension-type, cluster
- Medication overuse: daily analgesics/triptans (MOH screening)
- Gut-brain axis synergies: IBS/GERD comorbidity, histamine burden
"""

from typing import Dict, Tuple, List, Any, Optional
import re
from collections import defaultdict

from .constants import (
    FOCUS_AREAS,
    get_spacy_model,
    lemmatize_text,
    match_keyword_fuzzy,
    RAPIDFUZZ_AVAILABLE
)


class HeadacheMigraineRuleset:
    """
    Ruleset for evaluating headache/migraine patterns and triggers.
    
    Pre-filtered by Phase 2 frequent_headaches_migraines field.
    Only applies if that field is true.
    
    Features:
    - Frequency parsing (days/month normalization)
    - Multi-trigger detection (14+ categories)
    - Headache subtype classification (ICHD-3 mapping)
    - Medication overuse screening (MOH flag)
    - Cross-field synergies (digestive symptoms, sleep, allergies)
    - Per-domain caps (STR ≤ 1.2, COG ≤ 1.2, etc.)
    """
    
    # Domain caps for this field
    DOMAIN_CAPS = {
        "STR": 1.2,
        "COG": 1.2,
        "MITO": 1.2,
        "DTX": 1.2,
        "IMM": 1.2,
        "GA": 1.2,
        "HRM": 1.2,
        "CM": 1.2,
        "SKN": 1.2
    }
    
    # Negation words to avoid false positives
    NEGATION_WORDS = ["no", "not", "without", "never", "denies", "none", "absent", "doesn't", "don't"]
    
    def __init__(self):
        """Initialize the ruleset with NLP model and trigger lexicons."""
        self.nlp = get_spacy_model()
        self._build_trigger_lexicons()
        self._build_headache_type_patterns()
        self._build_medication_patterns()
    
    def _build_trigger_lexicons(self):
        """
        Build comprehensive trigger lexicons with keywords and base weights.
        
        Structure: {
            "trigger_name": {
                "keywords": [...],
                "scores": {"DTX": 0.30, ...},
                "category": "food" | "lifestyle" | "environmental" | "hormonal"
            }
        }
        """
        self.triggers = {
            # ===== FOOD & BEVERAGE TRIGGERS =====
            "red_wine_alcohol": {
                "keywords": ["red wine", "wine", "beer", "liquor", "alcohol", "drinking"],
                "scores": {"DTX": 0.30, "IMM": 0.15, "GA": 0.20},
                "category": "food"
            },
            "aged_cheese_fermented": {
                "keywords": ["aged cheese", "blue cheese", "parmesan", "fermented", "sauerkraut", 
                            "kimchi", "salami", "tyramine", "histamine"],
                "scores": {"DTX": 0.25, "IMM": 0.15, "GA": 0.20},
                "category": "food"
            },
            "chocolate": {
                "keywords": ["chocolate", "cocoa", "dark chocolate"],
                "scores": {"DTX": 0.15, "COG": 0.10, "GA": 0.15},
                "category": "food"
            },
            "processed_meats": {
                "keywords": ["processed meat", "bacon", "ham", "salami", "hot dog", "deli meat", 
                            "cured", "nitrate", "nitrite"],
                "scores": {"DTX": 0.25, "STR": 0.10, "COG": 0.10},
                "category": "food"
            },
            "msg": {
                "keywords": ["msg", "monosodium glutamate", "chinese food"],
                "scores": {"COG": 0.10, "STR": 0.10},
                "category": "food"
            },
            "aspartame": {
                "keywords": ["aspartame", "diet soda", "diet coke", "acesulfame", "sucralose", 
                            "artificial sweetener"],
                "scores": {"COG": 0.10, "STR": 0.10},
                "category": "food"
            },
            "caffeine": {
                "keywords": ["coffee", "espresso", "energy drink", "caffeine", "tea", "withdrawal", 
                            "skip", "craving", "too much"],
                "scores": {"STR": 0.20, "HRM": 0.10, "GA": 0.10},
                "category": "food"
            },
            "dehydration_skipped_meals": {
                "keywords": ["dehydration", "low water", "skipped meal", "skip meal", "hypoglycemia",
                            "low blood sugar", "fasting", "hungry"],
                "scores": {"MITO": 0.15, "STR": 0.10},
                "category": "lifestyle"
            },

            # ===== LIFESTYLE & PHYSIOLOGICAL TRIGGERS =====
            "poor_sleep": {
                "keywords": ["poor sleep", "late night", "irregular sleep", "insomnia", "all-nighter",
                            "sleep deprivation", "lack of sleep"],
                "scores": {"STR": 0.30, "COG": 0.20},
                "category": "lifestyle"
            },
            "stress": {
                "keywords": ["stress", "stressed", "anxiety", "anxious", "tension", "worry",
                            "overwhelmed"],
                "scores": {"STR": 0.25, "COG": 0.15},
                "category": "lifestyle"
            },

            # ===== ENVIRONMENTAL TRIGGERS =====
            "odor_voc": {
                "keywords": ["fragrance", "perfume", "paint", "voc", "chemical smell", "strong smell",
                            "odor", "scent"],
                "scores": {"DTX": 0.15, "IMM": 0.10, "SKN": 0.05},
                "category": "environmental"
            },
            "allergens": {
                "keywords": ["pollen", "dust", "mold", "seasonal", "allergy"],
                "scores": {"IMM": 0.20, "SKN": 0.10, "GA": 0.10},
                "category": "environmental"
            },
            "weather": {
                "keywords": ["weather", "barometric", "storm", "pressure change", "humidity"],
                "scores": {"STR": 0.10, "COG": 0.10},
                "category": "environmental"
            },

            # ===== HORMONAL TRIGGERS (female-specific) =====
            "menstrual": {
                "keywords": ["menstrual", "period", "ovulation", "before period", "pms", "cycle"],
                "scores": {"HRM": 0.25, "STR": 0.10},
                "category": "hormonal"
            },

            # ===== GUT-RELATED FOOD TRIGGERS =====
            "gluten_dairy_fodmap": {
                "keywords": ["gluten", "dairy", "fodmap", "lactose", "wheat", "milk", "cheese"],
                "scores": {"GA": 0.25, "IMM": 0.10},
                "category": "food"
            }
        }

    def _build_headache_type_patterns(self):
        """
        Build headache subtype classification patterns (ICHD-3 mapping).
        """
        self.headache_types = {
            "migraine_with_aura": {
                "keywords": ["aura", "visual aura", "sensory aura", "speech aura", "zigzag",
                            "flashing lights", "blind spot", "tingling", "numbness before"],
                "scores": {"COG": 0.25, "STR": 0.10},
                "safety_flag": "aura_estrogen_flag"  # Would check estrogen contraception if available
            },
            "migraine_no_aura": {
                "keywords": ["throbbing", "pulsating", "unilateral", "one side", "nausea", "vomit",
                            "photophobia", "light sensitive", "phonophobia", "sound sensitive",
                            "moderate to severe", "severe pain"],
                "scores": {"COG": 0.15, "STR": 0.10},
                "safety_flag": None
            },
            "tension_type": {
                "keywords": ["band-like", "pressure", "bilateral", "both sides", "tight",
                            "squeezing", "mild to moderate", "no nausea"],
                "scores": {"STR": 0.20},
                "safety_flag": None
            },
            "cluster": {
                "keywords": ["excruciating", "orbital", "eye pain", "temple pain", "lacrimation",
                            "tearing", "nasal congestion", "restless", "short attack", "cluster"],
                "scores": {"STR": 0.30, "COG": 0.15},
                "safety_flag": None
            }
        }

    def _build_medication_patterns(self):
        """
        Build medication patterns for MOH (medication overuse headache) screening.
        """
        # Analgesic keywords (NSAIDs, acetaminophen)
        self.analgesic_keywords = [
            "ibuprofen", "advil", "naproxen", "aleve", "acetaminophen", "paracetamol",
            "tylenol", "aspirin", "excedrin", "motrin"
        ]

        # Triptan keywords
        self.triptan_keywords = [
            "triptan", "sumatriptan", "imitrex", "rizatriptan", "maxalt", "zolmitriptan",
            "zomig", "eletriptan", "relpax"
        ]

        # Daily use patterns
        self.daily_use_patterns = [
            r"daily", r"every day", r"everyday", r"each day", r"all the time",
            r"constantly", r"\d+\s*times?\s*(?:a|per)\s*day"
        ]

    def _parse_frequency(self, text: str) -> int:
        """
        Parse headache frequency from text and normalize to days/month.

        Args:
            text: Free text response

        Returns:
            Estimated days per month (0-31)

        Examples:
            "daily" → 30
            "3-4 times per week" → 16
            "once a month" → 1
            "15+ days/month" → 15
        """
        text_lower = text.lower()

        # Daily patterns
        daily_patterns = [
            r"daily", r"every day", r"everyday", r"q\.?d\.?",
            r"15\+?\s*(?:days?|d)?\s*(?:/|per)?\s*month",
            r"chronic", r"constant", r"all the time"
        ]
        for pattern in daily_patterns:
            if re.search(pattern, text_lower):
                return 30

        # Weekly patterns (multiply by 4 to get days/month)
        weekly_match = re.search(r"(\d+)[-–]?(\d+)?\s*(?:times?|days?|x)?\s*(?:/|per)?\s*(?:week|wk)", text_lower)
        if weekly_match:
            lower = int(weekly_match.group(1))
            upper = int(weekly_match.group(2)) if weekly_match.group(2) else lower
            return upper * 4  # Use upper bound for severity

        # Monthly patterns
        monthly_match = re.search(r"(\d+)[-–]?(\d+)?\s*(?:times?|days?|x)?\s*(?:/|per)?\s*(?:month|mo)", text_lower)
        if monthly_match:
            lower = int(monthly_match.group(1))
            upper = int(monthly_match.group(2)) if monthly_match.group(2) else lower
            return upper  # Use upper bound

        # Default: if no pattern found, assume infrequent
        return 0

    def _detect_triggers(self, text: str, biological_sex: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect headache triggers from text using NLP-based matching.

        Args:
            text: Free text response
            biological_sex: "male" or "female" (for menstrual trigger filtering)

        Returns:
            Dict with:
                - matched_triggers: List of trigger names
                - trigger_scores: Aggregated scores by domain
                - food_trigger_count: Count of food triggers (for synergy bonus)
        """
        text_lower = text.lower()
        matched_triggers = []
        trigger_scores = {code: 0.0 for code in FOCUS_AREAS}
        food_trigger_count = 0

        # Lemmatize text if spaCy available
        if self.nlp:
            text_lemma = lemmatize_text(text_lower, self.nlp)
        else:
            text_lemma = text_lower

        # Check each trigger
        for trigger_name, trigger_data in self.triggers.items():
            keywords = trigger_data["keywords"]
            scores = trigger_data["scores"]
            category = trigger_data["category"]

            # Skip menstrual triggers for males
            if trigger_name == "menstrual" and biological_sex == "male":
                continue

            # Check for keyword matches
            matched = False
            for keyword in keywords:
                # Check for negation context
                negation_pattern = r"(?:" + "|".join(self.NEGATION_WORDS) + r")\s+\w*\s*" + re.escape(keyword)
                if re.search(negation_pattern, text_lower):
                    continue  # Skip if negated

                # Exact substring match
                if keyword in text_lower or keyword in text_lemma:
                    matched = True
                    break

                # Fuzzy match (if available)
                if RAPIDFUZZ_AVAILABLE and match_keyword_fuzzy(keyword, text_lower, threshold=85):
                    matched = True
                    break

            if matched:
                matched_triggers.append(trigger_name)

                # Add scores
                for domain, weight in scores.items():
                    trigger_scores[domain] += weight

                # Count food triggers
                if category == "food":
                    food_trigger_count += 1

        return {
            "matched_triggers": matched_triggers,
            "trigger_scores": trigger_scores,
            "food_trigger_count": food_trigger_count
        }

    def _classify_headache_type(self, text: str) -> Optional[str]:
        """
        Classify headache subtype based on ICHD-3 criteria.

        Args:
            text: Free text response

        Returns:
            Headache type name or None if no confident match
        """
        text_lower = text.lower()

        # Lemmatize text if spaCy available
        if self.nlp:
            text_lemma = lemmatize_text(text_lower, self.nlp)
        else:
            text_lemma = text_lower

        # Check each headache type (priority order: aura > cluster > migraine > tension)
        for headache_type, type_data in self.headache_types.items():
            keywords = type_data["keywords"]
            match_count = 0

            for keyword in keywords:
                if keyword in text_lower or keyword in text_lemma:
                    match_count += 1

            # Require at least 2 keyword matches for confident classification
            if match_count >= 2:
                return headache_type

        return None

    def _check_medication_overuse(
        self,
        text: str,
        phase2_medications: Optional[List[Dict]] = None
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Screen for medication overuse headache (MOH).

        Checks both:
        1. Free text mentions of daily analgesic/triptan use
        2. Phase 2 medications list for daily pain relievers

        Args:
            text: Free text response
            phase2_medications: List of medication dicts from Phase 2

        Returns:
            Tuple of (MOH_flag: bool, scores: dict)
        """
        text_lower = text.lower()
        moh_flag = False
        scores = {code: 0.0 for code in FOCUS_AREAS}

        # Check for daily use pattern in text
        daily_use_detected = False
        for pattern in self.daily_use_patterns:
            if re.search(pattern, text_lower):
                daily_use_detected = True
                break

        # Check for analgesic/triptan mentions in text
        analgesic_in_text = any(keyword in text_lower for keyword in self.analgesic_keywords)
        triptan_in_text = any(keyword in text_lower for keyword in self.triptan_keywords)

        # If daily use + analgesic/triptan mentioned in text → MOH
        if daily_use_detected and (analgesic_in_text or triptan_in_text):
            moh_flag = True
            scores["STR"] += 0.25
            scores["COG"] += 0.15

        # Check Phase 2 medications for daily pain relievers
        if phase2_medications:
            for med in phase2_medications:
                med_name = med.get("name", "").lower()
                med_frequency = med.get("frequency", "").lower()

                # Check if it's an analgesic or triptan
                is_analgesic = any(keyword in med_name for keyword in self.analgesic_keywords)
                is_triptan = any(keyword in med_name for keyword in self.triptan_keywords)

                # Check if it's daily
                is_daily = "daily" in med_frequency or "every day" in med_frequency

                if (is_analgesic or is_triptan) and is_daily:
                    moh_flag = True
                    scores["STR"] += 0.25
                    scores["COG"] += 0.15
                    break  # Only count once

        return moh_flag, scores

    def get_headache_migraine_weights(
        self,
        headache_text: str,
        age: Optional[int] = None,
        biological_sex: Optional[str] = None,
        phase2_digestive_symptoms: Optional[str] = None,
        phase2_sleep_hours_category: Optional[str] = None,
        phase2_medications: Optional[List[Dict]] = None,
        phase1_known_allergies: Optional[List[Dict]] = None
    ) -> Tuple[Dict[str, float], List[str], List[Dict[str, Any]]]:
        """
        Main scoring method for headache/migraine field.

        Args:
            headache_text: Free text response about headache frequency and triggers
            age: Patient age (for age filtering)
            biological_sex: "male" or "female" (for menstrual trigger filtering)
            phase2_digestive_symptoms: Digestive symptoms from Phase 2 (for gut-brain synergy)
            phase2_sleep_hours_category: Sleep hours category from Phase 2 (for sleep trigger synergy)
            phase2_medications: List of current medications from Phase 2 (for MOH screening)
            phase1_known_allergies: List of known allergies from Phase 1 (for allergen trigger synergy)

        Returns:
            Tuple of (scores, flags, alerts)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        flags = []
        alerts = []

        # Validate input
        if not headache_text or not headache_text.strip():
            return scores, flags, alerts

        text = headache_text.strip()

        # Age filter (≥18 only)
        if age and age < 18:
            flags.append("Age <18: headache/migraine field skipped")
            return scores, flags, alerts

        # ===== A) FREQUENCY SEVERITY =====
        days_per_month = self._parse_frequency(text)

        if days_per_month >= 15:
            # Chronic pattern (≥15 days/month)
            scores["STR"] += 0.45
            scores["COG"] += 0.35
            scores["MITO"] += 0.25
            flags.append(f"Chronic headache pattern (≥15 days/month)")
        elif days_per_month >= 8:
            # Episodic frequent (8-14 days/month)
            scores["STR"] += 0.25
            scores["COG"] += 0.20
            scores["MITO"] += 0.15
            flags.append(f"Frequent episodic headaches (8-14 days/month)")
        elif days_per_month >= 1:
            # Infrequent (1-7 days/month)
            scores["STR"] += 0.10
            scores["COG"] += 0.10
            flags.append(f"Infrequent headaches (1-7 days/month)")

        # ===== B) TRIGGERS =====
        trigger_results = self._detect_triggers(text, biological_sex=biological_sex)
        matched_triggers = trigger_results["matched_triggers"]
        trigger_scores = trigger_results["trigger_scores"]
        food_trigger_count = trigger_results["food_trigger_count"]

        # Add trigger scores
        for domain, weight in trigger_scores.items():
            scores[domain] += weight

        if matched_triggers:
            flags.append(f"Triggers detected: {', '.join(matched_triggers)}")

        # Multiple food triggers synergy (≥4 unique food triggers → GA +0.20)
        if food_trigger_count >= 4:
            scores["GA"] += 0.20
            flags.append(f"Multiple food triggers (n={food_trigger_count}) → permeability/mast-cell phenotype")

        # ===== C) HEADACHE TYPE REFINEMENT =====
        headache_type = self._classify_headache_type(text)

        if headache_type:
            type_data = self.headache_types[headache_type]
            type_scores = type_data["scores"]

            for domain, weight in type_scores.items():
                scores[domain] += weight

            flags.append(f"Headache type: {headache_type}")

            # Safety flag for aura (would check estrogen contraception if available)
            if headache_type == "migraine_with_aura":
                alerts.append({
                    "type": "migraine_with_aura",
                    "severity": "info",
                    "message": "Migraine with aura detected. If patient uses estrogen-containing contraception or smokes, discuss stroke risk with clinician."
                })

        # ===== D) GUT-BRAIN AXIS SYNERGIES =====

        # D1) IBS/GERD comorbidity
        if phase2_digestive_symptoms:
            digestive_lower = phase2_digestive_symptoms.lower()
            ibs_gerd_keywords = ["ibs", "bloating", "gerd", "reflux", "bowel", "constipation", "diarrhea"]

            if any(keyword in digestive_lower for keyword in ibs_gerd_keywords):
                # Check if headaches are meal-linked
                meal_linked_keywords = ["after eating", "after meal", "food", "eating"]
                if any(keyword in text.lower() for keyword in meal_linked_keywords):
                    scores["GA"] += 0.20
                    scores["STR"] += 0.10
                    flags.append("Gut-brain axis: IBS/GERD + meal-linked headaches")

        # D2) Histamine burden phenotype (histamine-rich food triggers + seasonal allergies)
        histamine_triggers = ["red_wine_alcohol", "aged_cheese_fermented"]
        has_histamine_triggers = any(trigger in matched_triggers for trigger in histamine_triggers)

        if has_histamine_triggers and phase1_known_allergies:
            # Check for seasonal/environmental allergies
            for allergy in phase1_known_allergies:
                allergen = allergy.get("allergen", "").lower()
                allergen_other = allergy.get("allergen_other", "").lower()

                seasonal_keywords = ["pollen", "dust", "mold", "seasonal", "grass", "tree", "ragweed"]
                if any(keyword in allergen or keyword in allergen_other for keyword in seasonal_keywords):
                    scores["IMM"] += 0.10
                    flags.append("Histamine burden phenotype: histamine-rich food triggers + seasonal allergies")
                    break

        # D3) Poor sleep synergy (if Phase 2 sleep <6 hours)
        if phase2_sleep_hours_category == "less_than_6":
            # Check if sleep is mentioned as a trigger in text
            sleep_trigger_keywords = ["sleep", "late night", "insomnia", "tired"]
            if any(keyword in text.lower() for keyword in sleep_trigger_keywords):
                scores["STR"] += 0.30
                scores["COG"] += 0.20
                flags.append("Sleep deprivation synergy: Phase 2 <6h sleep + sleep-triggered headaches")

        # ===== E) MEDICATION OVERUSE HEADACHE (MOH) =====
        moh_flag, moh_scores = self._check_medication_overuse(text, phase2_medications)

        if moh_flag:
            for domain, weight in moh_scores.items():
                scores[domain] += weight

            flags.append("⚠️  MOH screening: Daily analgesic/triptan use detected (≥10-15 d/mo for >3 mo)")

            alerts.append({
                "type": "medication_overuse_headache",
                "severity": "warning",
                "message": "Medication overuse headache (MOH) risk detected. Screen for rebound headaches in follow-up."
            })

        # E2) NSAID + reflux synergy
        if moh_flag and phase2_digestive_symptoms:
            reflux_keywords = ["heartburn", "reflux", "gerd"]
            if any(keyword in phase2_digestive_symptoms.lower() for keyword in reflux_keywords):
                scores["GA"] += 0.15
                flags.append("NSAID gastropathy risk: Daily NSAID use + reflux symptoms")

        # ===== F) APPLY DOMAIN CAPS =====
        for domain in FOCUS_AREAS:
            if scores[domain] > self.DOMAIN_CAPS[domain]:
                scores[domain] = self.DOMAIN_CAPS[domain]

        return scores, flags, alerts

