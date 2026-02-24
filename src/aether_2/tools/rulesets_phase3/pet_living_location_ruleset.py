"""
Ruleset for Field 40: Pet Living Location (Where do your pets/animals primarily live?)

Parent question: "Pets/Animals at home?" (Yes/No)
Child question (shown only if Yes): "Where do your pets/animals primarily live?"

Options: "Inside" | "Outside" | "Both"

This ruleset applies multipliers to the base pet scores computed from the Animal Types field.
It also adds context-specific adjustments based on air filtration, cleaning practices, and environmental factors.

Focus areas affected:
- IMM (Immune Function & Inflammation): Primary - allergen exposure, vector-borne diseases
- SKN (Skin & Barrier Function): Secondary - allergen contact
- GA (Gut Health & Assimilation): Tertiary - fecal-oral transmission, cleaning exposure
- DTX (Detoxification): Minor - outdoor endotoxin/ammonia exposure

Evidence base:
- Indoor pets increase allergen concentration (EPA guidance)
- HEPA/charcoal filtration reduces particulate/VOC exposure
- Outdoor livestock increases vector-borne disease risk (CDC/NIOSH)
- Litter box/coop cleaning increases fecal-oral exposure
- Mold/damp + indoor pets = allergen stacking
"""

from typing import Dict, List, Tuple


class PetLivingLocationRuleset:
    """
    Evaluates pet living location and applies multipliers to base pet scores.
    
    This ruleset:
    1. Takes base pet scores from Animal Types field
    2. Applies location-based multipliers (Inside/Outside/Both)
    3. Adds context-specific adjustments (HEPA, cleaning, mold, livestock)
    4. Returns modified scores
    """
    
    # Location multipliers
    # Global Pet Exposure Factor (PEF) - affects IMM, SKN
    PEF_INSIDE = 1.15
    PEF_BOTH = 1.30
    PEF_OUTSIDE = 1.00
    
    # GA-specific factor
    GA_INSIDE = 1.25
    GA_BOTH = 1.10
    GA_OUTSIDE = 1.00
    
    # Context adjustments
    HEPA_GA_REDUCTION = 0.10
    CLEANING_GA_ADDITION = 0.05
    LIVESTOCK_OUTSIDE_IMM = 0.20
    LIVESTOCK_OUTSIDE_DTX = 0.10
    MOLD_INDOOR_IMM = 0.10
    MOLD_INDOOR_GA = 0.05
    
    def __init__(self):
        """Initialize the pet living location ruleset."""
        pass
    
    def _normalize_location(self, location: str) -> str:
        """
        Normalize location input.
        
        Returns: 'inside', 'outside', 'both', or 'unknown'
        """
        if not location:
            return 'unknown'
        
        loc = str(location).lower().strip()
        
        if loc in ['inside', 'indoor', 'indoors']:
            return 'inside'
        elif loc in ['outside', 'outdoor', 'outdoors']:
            return 'outside'
        elif loc in ['both', 'inside and outside', 'indoor and outdoor']:
            return 'both'
        else:
            return 'unknown'
    
    def apply_pet_location_adjustments(
        self,
        pet_base_scores: Dict[str, float],
        location: str,
        has_pets: bool = True,
        has_livestock: bool = False,
        air_filter: str = "None",
        cleans_litter_coops: bool = False,
        has_mold_damp: bool = False,
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Apply pet living location multipliers and context adjustments to base pet scores.
        
        Args:
            pet_base_scores: Base scores from Animal Types field, e.g., {'IMM': 0.35, 'SKN': 0.25, 'GA': 0.10}
            location: "Inside" | "Outside" | "Both"
            has_pets: Parent field "Pets/Animals at home?" (Yes/No)
            has_livestock: User has livestock (from Animal Types field)
            air_filter: "HEPA" | "Charcoal/Carbon" | "Both" | "None/Unknown"
            cleans_litter_coops: User regularly cleans litter box/coops
            has_mold_damp: Mold/damp home (from Phase 2)
        
        Returns:
            Tuple of (adjusted_scores_dict, flags_list)
            adjusted_scores_dict: {focus_area: adjusted_weight}
            flags_list: Human-readable explanations
        """
        flags = []
        adjusted_scores = {}
        
        # Check prerequisite: has_pets must be True
        if not has_pets:
            flags.append("No pets/animals at home → skipping pet location scoring")
            return {}, flags
        
        # Check if base scores exist
        if not pet_base_scores:
            flags.append("No base pet scores provided → skipping pet location adjustments")
            return {}, flags
        
        # Normalize location
        loc = self._normalize_location(location)
        
        if loc == 'unknown':
            flags.append(f"⚠️ Unknown pet location: '{location}' → defaulting to 'Inside' multipliers")
            loc = 'inside'
        
        flags.append(f"Pet living location: {loc.capitalize()}")
        
        # Copy base scores
        adjusted_scores = pet_base_scores.copy()
        
        # =================================================================
        # SECTION 1: APPLY LOCATION MULTIPLIERS
        # =================================================================
        
        # Get multipliers based on location
        if loc == 'inside':
            pef = self.PEF_INSIDE
            ga_factor = self.GA_INSIDE
        elif loc == 'both':
            pef = self.PEF_BOTH
            ga_factor = self.GA_BOTH
        else:  # outside
            pef = self.PEF_OUTSIDE
            ga_factor = self.GA_OUTSIDE
        
        # Apply global PEF to IMM and SKN
        if 'IMM' in adjusted_scores:
            original_imm = adjusted_scores['IMM']
            adjusted_scores['IMM'] *= pef
            if pef != 1.0:
                flags.append(f"IMM: {original_imm:.2f} × {pef:.2f} = {adjusted_scores['IMM']:.2f} (location multiplier)")
        
        if 'SKN' in adjusted_scores:
            original_skn = adjusted_scores['SKN']
            adjusted_scores['SKN'] *= pef
            if pef != 1.0:
                flags.append(f"SKN: {original_skn:.2f} × {pef:.2f} = {adjusted_scores['SKN']:.2f} (location multiplier)")

        # Apply GA-specific factor to GA
        if 'GA' in adjusted_scores:
            original_ga = adjusted_scores['GA']
            adjusted_scores['GA'] *= ga_factor
            if ga_factor != 1.0:
                flags.append(f"GA: {original_ga:.2f} × {ga_factor:.2f} = {adjusted_scores['GA']:.2f} (GA-specific location multiplier)")

        # =================================================================
        # SECTION 2: CONTEXT-SPECIFIC ADJUSTMENTS
        # =================================================================

        # 2A) HEPA/Charcoal mitigation (reduces GA)
        if loc in ['inside', 'both']:
            air_filter_norm = str(air_filter).lower().strip()
            has_hepa_or_carbon = any(x in air_filter_norm for x in ['hepa', 'charcoal', 'carbon', 'both'])

            if has_hepa_or_carbon and 'GA' in adjusted_scores:
                original_ga = adjusted_scores['GA']
                adjusted_scores['GA'] = max(0, adjusted_scores['GA'] - self.HEPA_GA_REDUCTION)
                flags.append(f"HEPA/Charcoal filter → GA: {original_ga:.2f} - {self.HEPA_GA_REDUCTION:.2f} = {adjusted_scores['GA']:.2f} (reduced particulate/VOC exposure)")

        # 2B) Indoor cleaning duty (increases GA)
        if loc in ['inside', 'both'] and cleans_litter_coops:
            adjusted_scores['GA'] = adjusted_scores.get('GA', 0) + self.CLEANING_GA_ADDITION
            flags.append(f"Cleans litter/coops indoors → GA +{self.CLEANING_GA_ADDITION:.2f} (fecal-oral contact route)")

        # 2C) Livestock outside (vector-borne/zoonotic)
        if loc == 'outside' and has_livestock:
            adjusted_scores['IMM'] = adjusted_scores.get('IMM', 0) + self.LIVESTOCK_OUTSIDE_IMM
            adjusted_scores['DTX'] = adjusted_scores.get('DTX', 0) + self.LIVESTOCK_OUTSIDE_DTX
            flags.append(f"Livestock outside → IMM +{self.LIVESTOCK_OUTSIDE_IMM:.2f}, DTX +{self.LIVESTOCK_OUTSIDE_DTX:.2f} (vector-borne/zoonotic + endotoxin/ammonia)")

        # 2D) Mold/damp synergy (indoor allergen stacking)
        if loc in ['inside', 'both'] and has_mold_damp:
            adjusted_scores['IMM'] = adjusted_scores.get('IMM', 0) + self.MOLD_INDOOR_IMM
            adjusted_scores['GA'] = adjusted_scores.get('GA', 0) + self.MOLD_INDOOR_GA
            flags.append(f"Mold/damp + indoor pets → IMM +{self.MOLD_INDOOR_IMM:.2f}, GA +{self.MOLD_INDOOR_GA:.2f} (allergen stacking, histamine/MCAS overlap)")

        # =================================================================
        # SECTION 3: CLEANUP
        # =================================================================

        # Remove near-zero weights
        adjusted_scores = {fa: w for fa, w in adjusted_scores.items() if abs(w) >= 0.01}

        return adjusted_scores, flags

