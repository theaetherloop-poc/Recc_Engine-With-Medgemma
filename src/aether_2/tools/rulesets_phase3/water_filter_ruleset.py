"""
Ruleset for Field 38: Water Filter/Bottled Water Usage

Question: "Do you drink bottled water or use a water filter?"
Record as: Yes / No
If Yes → "What brand/model?" (free text)

This ruleset evaluates water filtration practices and bottled water usage,
considering technology type, certifications, maintenance, and source context.

Focus areas affected:
- DTX (Detoxification & Biotransformation): Primary - DBPs, PFAS, contaminants, microplastics
- IMM (Immune Function & Inflammation): Secondary - microbial exposure, contaminant burden
- GA (Gut Health & Assimilation): Tertiary - mineral content, microbiome effects

Evidence base:
- EPA guidance on drinking water treatment and DBPs
- NSF/ANSI standards (42/53/58/401) for filter certifications
- 2024 PNAS study on microplastics in bottled water (~240,000 particles/L)
- WHO guidance on desalinated/RO water remineralization
"""

import re
from typing import Dict, List, Tuple


class WaterFilterRuleset:
    """
    Evaluates water filtration and bottled water usage patterns.
    
    Caps: DTX, IMM, GA each ±0.6 to prevent single-field dominance.
    """
    
    # Weight magnitude tiers
    MAJOR = 0.30
    MODERATE = 0.20
    MINOR = 0.10
    PROTECTIVE_SMALL = -0.05
    PROTECTIVE_MEDIUM = -0.10
    PROTECTIVE_LARGE = -0.15
    PROTECTIVE_MAJOR = -0.25
    
    # Caps per focus area
    MAX_CAP = 0.6
    MIN_CAP = -0.6
    
    def __init__(self):
        """Initialize the water filter ruleset."""
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, strip whitespace, keep alphanumeric and basic punctuation."""
        if not text:
            return ""
        # Convert to lowercase and strip
        text = str(text).lower().strip()
        # Remove emojis and special characters (keep A-Z, 0-9, space, hyphen, slash, parentheses)
        text = re.sub(r'[^a-z0-9\s\-/().]', '', text)
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _detect_technology(self, text: str) -> Dict[str, bool]:
        """
        Detect water filtration technology from brand/model text.
        
        Returns dict with technology flags:
        - has_ro: Reverse osmosis
        - has_carbon: Activated carbon (GAC/carbon block)
        - has_ceramic: Ceramic/gravity filter
        - has_uv: UV disinfection
        - is_pitcher: Pitcher/carafe filter
        - is_berkey: Berkey brand (gravity carbon/ceramic)
        """
        text_norm = self._normalize_text(text)
        
        return {
            'has_ro': bool(re.search(r'\b(ro|reverse osmosis|nf membrane)\b', text_norm)),
            'has_carbon': bool(re.search(r'\b(activated carbon|gac|carbon block|coconut shell|carbon filter)\b', text_norm)),
            'has_ceramic': bool(re.search(r'\b(ceramic|gravity)\b', text_norm)),
            'has_uv': bool(re.search(r'\b(uv|ultraviolet)\b', text_norm)),
            'is_pitcher': bool(re.search(r'\b(pitcher|carafe|brita|pur)\b', text_norm)),
            'is_berkey': bool(re.search(r'\bberkey\b', text_norm)),
        }
    
    def _detect_certifications(self, text: str) -> Dict[str, bool]:
        """
        Detect third-party certifications from text.
        
        Returns dict with certification flags:
        - has_nsf_42: Aesthetic effects (taste, odor, chlorine)
        - has_nsf_53: Health effects (lead, cysts, VOCs, PFAS)
        - has_nsf_58: Reverse osmosis systems
        - has_nsf_401: Emerging contaminants (PPCPs, pharmaceuticals)
        - has_wqa: Water Quality Association Gold Seal
        - has_pfas_cert: Specifically certified for PFAS removal
        """
        text_norm = self._normalize_text(text)
        
        return {
            'has_nsf_42': bool(re.search(r'\b(nsf 42|nsf42|nsf/ansi 42)\b', text_norm)),
            'has_nsf_53': bool(re.search(r'\b(nsf 53|nsf53|nsf/ansi 53)\b', text_norm)),
            'has_nsf_58': bool(re.search(r'\b(nsf 58|nsf58|nsf/ansi 58)\b', text_norm)),
            'has_nsf_401': bool(re.search(r'\b(nsf 401|nsf401|nsf/ansi 401)\b', text_norm)),
            'has_wqa': bool(re.search(r'\b(wqa|water quality association|gold seal)\b', text_norm)),
            'has_pfas_cert': bool(re.search(r'\b(pfas certified|pfas removal|pfas tested)\b', text_norm)),
        }
    
    def _detect_maintenance_issues(self, text: str) -> Dict[str, bool]:
        """
        Detect maintenance issues from text.
        
        Returns dict with maintenance flags:
        - overdue: Filter change overdue (>12 months or light on)
        - remineralized: RO water is remineralized
        """
        text_norm = self._normalize_text(text)
        
        return {
            'overdue': bool(re.search(r'\b(12 months|1 year|overdue|light on|never changed|havent changed)\b', text_norm)),
            'remineralized': bool(re.search(r'\b(reminerali|mineral drops|mineral cartridge|alkaline filter)\b', text_norm)),
        }
    
    def _detect_bottled_water_usage(self, text: str) -> str:
        """
        Detect bottled water usage pattern from text.
        
        Returns: 'exclusive' (≥80%), 'occasional' (≤20%), or 'none'
        """
        text_norm = self._normalize_text(text)
        
        # Exclusive patterns
        if re.search(r'\b(only bottled|exclusively bottled|all bottled|100 bottled|always bottled)\b', text_norm):
            return 'exclusive'
        if re.search(r'\b(80|90|95|100)(%| percent) bottled\b', text_norm):
            return 'exclusive'
        
        # Occasional patterns
        if re.search(r'\b(sometimes bottled|occasionally bottled|rarely bottled)\b', text_norm):
            return 'occasional'
        if re.search(r'\b(10|15|20)(%| percent) bottled\b', text_norm):
            return 'occasional'
        
        # Check for any bottled water mention
        if re.search(r'\bbottled\b', text_norm):
            return 'occasional'  # Default to occasional if mentioned but not quantified
        
        return 'none'

    def get_water_filter_weights(
        self,
        choice: str,
        brand_model_text: str = "",
        water_source: str = "municipal",  # 'municipal', 'well', 'unknown'
        has_pfas_advisory: bool = False,
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for water filter/bottled water usage.

        Args:
            choice: "Yes" or "No" (uses filter/bottled water)
            brand_model_text: Free text describing brand/model/usage
            water_source: 'municipal' (chlorinated), 'well', or 'unknown'
            has_pfas_advisory: Whether there's a local PFAS advisory

        Returns:
            Tuple of (weights_dict, flags_list)
            weights_dict: {focus_area: weight_delta}
            flags_list: Human-readable explanations
        """
        weights = {}
        flags = []

        # Normalize inputs
        choice_norm = self._normalize_text(choice)
        brand_model_norm = self._normalize_text(brand_model_text)

        # Handle empty/invalid input
        if not choice_norm:
            return {}, []

        # Detect patterns
        tech = self._detect_technology(brand_model_norm)
        certs = self._detect_certifications(brand_model_norm)
        maint = self._detect_maintenance_issues(brand_model_norm)
        bottled_usage = self._detect_bottled_water_usage(brand_model_norm)

        # Track if user has a filter
        has_filter = 'yes' in choice_norm

        # =================================================================
        # SECTION 1: NO FILTER CASES
        # =================================================================
        if not has_filter or 'no' in choice_norm:
            flags.append("No water filter in use")

            # Municipal (chlorinated) water without filter
            if water_source == 'municipal':
                weights['DTX'] = weights.get('DTX', 0) + 0.20
                weights['IMM'] = weights.get('IMM', 0) + 0.10
                weights['GA'] = weights.get('GA', 0) + 0.10
                flags.append("Municipal water without filter → DTX +0.20, IMM +0.10, GA +0.10 (DBP exposure risk)")

            # Private well without filter
            elif water_source == 'well':
                weights['DTX'] = weights.get('DTX', 0) + 0.15
                weights['IMM'] = weights.get('IMM', 0) + 0.10
                flags.append("Well water without filter → DTX +0.15, IMM +0.10 (contaminants vary; test recommended)")

        # =================================================================
        # SECTION 2: YES - HAS FILTER
        # =================================================================
        else:
            flags.append("Water filter in use")

            # Check for certifications (any NSF or WQA)
            has_any_cert = any([
                certs['has_nsf_42'], certs['has_nsf_53'],
                certs['has_nsf_58'], certs['has_nsf_401'],
                certs['has_wqa']
            ])

            # ---------------------------------------------------------------
            # Technology-based scoring
            # ---------------------------------------------------------------

            # RO (Reverse Osmosis) with NSF/ANSI 58
            if tech['has_ro'] and certs['has_nsf_58']:
                weights['DTX'] = weights.get('DTX', 0) - 0.25
                weights['IMM'] = weights.get('IMM', 0) - 0.10
                weights['GA'] = weights.get('GA', 0) - 0.10
                flags.append("RO with NSF/ANSI 58 → DTX -0.25, IMM -0.10, GA -0.10 (broad spectrum removal)")

            # RO without certification
            elif tech['has_ro'] and not certs['has_nsf_58']:
                weights['DTX'] = weights.get('DTX', 0) - 0.15
                weights['IMM'] = weights.get('IMM', 0) - 0.05
                flags.append("RO without NSF 58 certification → DTX -0.15, IMM -0.05 (reduced credit)")

            # Carbon block/GAC with NSF/ANSI 53 and/or 401
            if tech['has_carbon'] and (certs['has_nsf_53'] or certs['has_nsf_401']):
                weights['DTX'] = weights.get('DTX', 0) - 0.20
                weights['IMM'] = weights.get('IMM', 0) - 0.05
                weights['GA'] = weights.get('GA', 0) - 0.10
                flags.append("Carbon filter with NSF 53/401 → DTX -0.20, IMM -0.05, GA -0.10 (health effects/emerging contaminants)")

            # Carbon without health certifications (only NSF 42 or none)
            elif tech['has_carbon'] and not (certs['has_nsf_53'] or certs['has_nsf_401']):
                weights['DTX'] = weights.get('DTX', 0) - 0.10
                flags.append("Carbon filter without NSF 53/401 → DTX -0.10 (basic chlorine/taste only)")

            # Gravity ceramic/carbon (e.g., Berkey)
            if (tech['has_ceramic'] or tech['is_berkey']) and has_any_cert:
                weights['DTX'] = weights.get('DTX', 0) - 0.15
                weights['GA'] = weights.get('GA', 0) - 0.05
                flags.append("Gravity ceramic/carbon with certification → DTX -0.15, GA -0.05")

            # Gravity ceramic/carbon WITHOUT certification but marketing as "purifier"
            elif (tech['has_ceramic'] or tech['is_berkey']) and not has_any_cert:
                if re.search(r'(purif|clean|remov)', brand_model_norm):
                    weights['DTX'] = weights.get('DTX', 0) + 0.10
                    flags.append("⚠️ Gravity filter without certification but marketing claims → DTX +0.10 (withhold credits)")

            # Pitcher filters (assume carbon; check certifications)
            if tech['is_pitcher']:
                if certs['has_nsf_53']:
                    weights['DTX'] = weights.get('DTX', 0) - 0.15
                    weights['GA'] = weights.get('GA', 0) - 0.05
                    flags.append("Pitcher filter with NSF 53 → DTX -0.15, GA -0.05")
                else:
                    weights['DTX'] = weights.get('DTX', 0) - 0.10
                    flags.append("Pitcher filter (basic) → DTX -0.10 (chlorine/taste only)")

            # UV only (no carbon/RO)
            if tech['has_uv'] and not tech['has_carbon'] and not tech['has_ro']:
                weights['IMM'] = weights.get('IMM', 0) - 0.05
                flags.append("UV only → IMM -0.05 (microbial disinfection; no chemical removal)")

            # ---------------------------------------------------------------
            # Source-specific synergies
            # ---------------------------------------------------------------

            # Municipal + certified carbon or RO
            if water_source == 'municipal' and (
                (tech['has_carbon'] and (certs['has_nsf_53'] or certs['has_nsf_401'])) or
                (tech['has_ro'] and certs['has_nsf_58'])
            ):
                weights['DTX'] = weights.get('DTX', 0) - 0.10
                weights['GA'] = weights.get('GA', 0) - 0.05
                flags.append("Municipal water + certified filter → DTX -0.10, GA -0.05 (DBP/chlorine reduction)")

            # PFAS advisory + PFAS-certified device
            if has_pfas_advisory and (certs['has_pfas_cert'] or certs['has_nsf_53'] or certs['has_nsf_58']):
                weights['DTX'] = weights.get('DTX', 0) - 0.15
                flags.append("PFAS advisory + PFAS-certified filter → DTX -0.15 (extra protection)")

            # PFAS advisory + NOT PFAS-certified
            elif has_pfas_advisory and not (certs['has_pfas_cert'] or certs['has_nsf_53'] or certs['has_nsf_58']):
                weights['DTX'] = weights.get('DTX', 0) + 0.10
                flags.append("⚠️ PFAS advisory + filter not certified for PFAS → DTX +0.10 (potential under-treatment)")

            # ---------------------------------------------------------------
            # Maintenance issues
            # ---------------------------------------------------------------

            # Filter overdue
            if maint['overdue']:
                weights['DTX'] = weights.get('DTX', 0) + 0.10
                weights['IMM'] = weights.get('IMM', 0) + 0.05
                flags.append("⚠️ Filter overdue (>12 months or light on) → DTX +0.10, IMM +0.05 (reduced efficacy, biofilm risk)")

            # RO remineralized
            if tech['has_ro'] and maint['remineralized']:
                weights['GA'] = weights.get('GA', 0) - 0.05
                flags.append("RO remineralized → GA -0.05 (palatability/electrolyte support)")

        # =================================================================
        # SECTION 3: BOTTLED WATER USAGE (applies regardless of filter)
        # =================================================================

        if bottled_usage == 'exclusive':
            # If has filter, reduce bottled deltas by 50%
            if has_filter:
                weights['DTX'] = weights.get('DTX', 0) + 0.15  # 50% of 0.30
                weights['GA'] = weights.get('GA', 0) + 0.05   # 50% of 0.10
                weights['IMM'] = weights.get('IMM', 0) + 0.05  # 50% of 0.10
                flags.append("Exclusive bottled water (≥80%) + filter → DTX +0.15, GA +0.05, IMM +0.05 (microplastics; reduced impact)")
            else:
                weights['DTX'] = weights.get('DTX', 0) + 0.30
                weights['GA'] = weights.get('GA', 0) + 0.10
                weights['IMM'] = weights.get('IMM', 0) + 0.10
                flags.append("Exclusive bottled water (≥80%) → DTX +0.30, GA +0.10, IMM +0.10 (microplastics ~240k particles/L)")

        elif bottled_usage == 'occasional':
            weights['DTX'] = weights.get('DTX', 0) + 0.10
            flags.append("Occasional bottled water (≤20%) → DTX +0.10 (lower microplastic exposure)")

        # =================================================================
        # SECTION 4: APPLY CAPS
        # =================================================================

        for fa in ['DTX', 'IMM', 'GA']:
            if fa in weights:
                if weights[fa] > self.MAX_CAP:
                    weights[fa] = self.MAX_CAP
                    flags.append(f"⚠️ {fa} capped at +{self.MAX_CAP}")
                elif weights[fa] < self.MIN_CAP:
                    weights[fa] = self.MIN_CAP
                    flags.append(f"⚠️ {fa} capped at {self.MIN_CAP}")

                # Remove near-zero weights
                if abs(weights[fa]) < 0.01:
                    del weights[fa]

        return weights, flags

