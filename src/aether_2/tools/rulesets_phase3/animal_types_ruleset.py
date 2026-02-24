"""
Ruleset for Field 39: Animal Types (What kind of animals do you have?)

Parent question: "Pets/Animals at home?" (Yes/No)
Child question (shown only if Yes): "What kind of animals do you have?" (multi-select)

Options: Dog, Cat, Bird, Reptile, Livestock, Other (with free text)

This ruleset provides animal-specific overlays on top of the baseline "any pet" scoring.
It assumes the parent Yes/No field already handled baseline pet exposure.

Focus areas affected:
- IMM (Immune Function & Inflammation): Primary - aeroallergens, bioaerosols, zoonotic exposure
- SKN (Skin & Barrier Function): Secondary - allergen contact, scratches
- GA (Gut Health & Assimilation): Tertiary - fecal-oral transmission (Salmonella, Toxoplasma)
- DTX (Detoxification): Minor - barn dust, ammonia

Evidence base:
- Dog allergens (Can f) drive upper-airway sensitization
- Cat allergens (Fel d 1) are potent & persistent; litter boxes = Toxoplasma exposure
- Bird bioaerosols (bird-fancier's lung/HP, psittacosis)
- Reptile & poultry fecal-oral Salmonella transmission
- Livestock: barn dust, ammonia, Q-fever (ruminant birthing)
"""

import re
from typing import Dict, List, Tuple


class AnimalTypesRuleset:
    """
    Evaluates health impacts of different animal types in the home.
    
    Caps: IMM ≤ +0.60, GA ≤ +0.50, SKN ≤ +0.40, DTX ≤ +0.30
    Field total ≤ +1.60
    """
    
    # Weight magnitude tiers
    TRACE = 0.05
    SMALL = 0.10
    MODERATE = 0.20
    LARGE = 0.30
    
    # Caps per focus area
    MAX_IMM = 0.60
    MAX_GA = 0.50
    MAX_SKN = 0.40
    MAX_DTX = 0.30
    MAX_TOTAL = 1.60
    
    def __init__(self):
        """Initialize the animal types ruleset."""
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, strip whitespace."""
        if not text:
            return ""
        return str(text).lower().strip()
    
    def _parse_animal_list(self, text: str) -> List[str]:
        """
        Parse comma/semicolon-separated animal list.
        
        Returns list of normalized animal types.
        """
        if not text:
            return []
        
        # Split by comma, semicolon, or "and"
        animals = re.split(r'[,;]|\band\b', text)
        
        # Normalize and filter
        return [self._normalize_text(a) for a in animals if a.strip()]
    
    def _detect_animal_type(self, animal_text: str) -> str:
        """
        Detect animal type from text.
        
        Returns: 'dog', 'cat', 'bird', 'reptile', 'livestock', 'rodent', 
                 'rabbit', 'ferret', 'fish', or 'unknown'
        """
        text = self._normalize_text(animal_text)
        
        # Dog
        if re.search(r'\b(dog|puppy|canine)\b', text):
            return 'dog'
        
        # Cat
        if re.search(r'\b(cat|kitten|feline)\b', text):
            return 'cat'
        
        # Bird
        if re.search(r'\b(bird|parrot|parakeet|cockatiel|budgie|finch|canary|macaw|cockatoo|conure)\b', text):
            return 'bird'
        
        # Reptile
        if re.search(r'\b(reptile|turtle|tortoise|lizard|gecko|iguana|snake|bearded dragon)\b', text):
            return 'reptile'
        
        # Livestock
        if re.search(r'\b(livestock|chicken|hen|rooster|duck|goose|goat|sheep|cow|cattle|pig|horse|pony)\b', text):
            return 'livestock'
        
        # Rodent
        if re.search(r'\b(rodent|mouse|mice|rat|hamster|gerbil|guinea pig)\b', text):
            return 'rodent'
        
        # Rabbit
        if re.search(r'\b(rabbit|bunny)\b', text):
            return 'rabbit'
        
        # Ferret
        if re.search(r'\b(ferret)\b', text):
            return 'ferret'
        
        # Fish/Amphibian (neutral)
        if re.search(r'\b(fish|aquarium|frog|toad|salamander|newt)\b', text):
            return 'fish'
        
        return 'unknown'
    
    def _is_psittacine(self, animal_text: str) -> bool:
        """Check if bird is psittacine (parrot family) - higher psittacosis risk."""
        text = self._normalize_text(animal_text)
        return bool(re.search(r'\b(parrot|parakeet|cockatiel|budgie|macaw|cockatoo|conure|lovebird)\b', text))
    
    def _is_poultry(self, animal_text: str) -> bool:
        """Check if livestock is poultry."""
        text = self._normalize_text(animal_text)
        return bool(re.search(r'\b(chicken|hen|rooster|duck|goose|poultry)\b', text))
    
    def _is_ruminant(self, animal_text: str) -> bool:
        """Check if livestock is ruminant (Q-fever risk from birthing)."""
        text = self._normalize_text(animal_text)
        return bool(re.search(r'\b(goat|sheep|cattle|cow)\b', text))

    def get_animal_types_weights(
        self,
        animal_list_text: str,
        has_pets: bool = True,
        handles_litter: bool = False,
        feeds_raw_food: bool = False,
        backyard_poultry_frequent: bool = False,
        litter_daily_cleaning: bool = False,
        poor_hand_hygiene: bool = False,
        good_hand_hygiene: bool = False,
        has_hepa_bedroom: bool = False,
        ruminant_birthing_exposure: bool = False,
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for animal types in the home.

        Args:
            animal_list_text: Comma/semicolon-separated list of animals
            has_pets: Parent field "Pets/Animals at home?" (Yes/No)
            handles_litter: User handles cat litter boxes
            feeds_raw_food: Feeds raw pet food to dogs/cats
            backyard_poultry_frequent: Frequently handles backyard poultry/chicks
            litter_daily_cleaning: Daily cat litter removal
            poor_hand_hygiene: Poor hand hygiene after cleaning
            good_hand_hygiene: Good hand hygiene after cleaning
            has_hepa_bedroom: HEPA/charcoal air cleaner in bedroom/living area
            ruminant_birthing_exposure: Exposure to ruminant birthing/placenta

        Returns:
            Tuple of (weights_dict, flags_list)
            weights_dict: {focus_area: weight_delta}
            flags_list: Human-readable explanations
        """
        weights = {}
        flags = []

        # Check prerequisite: has_pets must be True
        if not has_pets:
            flags.append("No pets/animals at home (parent field) → skipping animal types scoring")
            return {}, flags

        # Parse animal list
        animals = self._parse_animal_list(animal_list_text)

        if not animals:
            return {}, []

        flags.append(f"Animals in home: {', '.join(animals)}")

        # Track counts for multi-animal amplifiers
        num_cats = 0
        num_birds = 0
        has_dog = False
        has_cat = False
        has_bird = False
        has_reptile = False
        has_livestock = False

        # =================================================================
        # SECTION 1: CORE ANIMAL EFFECTS
        # =================================================================

        for animal in animals:
            animal_type = self._detect_animal_type(animal)

            # ---------------------------------------------------------------
            # Dog
            # ---------------------------------------------------------------
            if animal_type == 'dog':
                has_dog = True
                weights['IMM'] = weights.get('IMM', 0) + 0.15
                weights['SKN'] = weights.get('SKN', 0) + 0.10
                weights['GA'] = weights.get('GA', 0) + 0.05
                flags.append("Dog → IMM +0.15, SKN +0.10, GA +0.05 (Can f allergens, minor skin barrier)")

            # ---------------------------------------------------------------
            # Cat
            # ---------------------------------------------------------------
            elif animal_type == 'cat':
                has_cat = True
                num_cats += 1
                weights['IMM'] = weights.get('IMM', 0) + 0.20
                weights['SKN'] = weights.get('SKN', 0) + 0.15
                flags.append("Cat → IMM +0.20, SKN +0.15 (Fel d 1 allergen)")

                # Litter box handling
                if handles_litter:
                    weights['GA'] = weights.get('GA', 0) + 0.10
                    flags.append("Cat + litter handling → GA +0.10 (Toxoplasma exposure)")

            # ---------------------------------------------------------------
            # Bird
            # ---------------------------------------------------------------
            elif animal_type == 'bird':
                has_bird = True
                num_birds += 1
                weights['IMM'] = weights.get('IMM', 0) + 0.25
                weights['GA'] = weights.get('GA', 0) + 0.05
                flags.append("Bird → IMM +0.25, GA +0.05 (bioaerosols, bird-fancier's lung)")

                # Psittacine (parrot family) - psittacosis risk
                if self._is_psittacine(animal):
                    weights['IMM'] = weights.get('IMM', 0) + 0.10
                    flags.append("Psittacine bird (parrot family) → IMM +0.10 (psittacosis risk)")

            # ---------------------------------------------------------------
            # Reptile
            # ---------------------------------------------------------------
            elif animal_type == 'reptile':
                has_reptile = True
                weights['GA'] = weights.get('GA', 0) + 0.20
                weights['IMM'] = weights.get('IMM', 0) + 0.10
                flags.append("Reptile → GA +0.20, IMM +0.10 (Salmonella from animals/tank water)")

            # ---------------------------------------------------------------
            # Livestock
            # ---------------------------------------------------------------
            elif animal_type == 'livestock':
                has_livestock = True
                weights['IMM'] = weights.get('IMM', 0) + 0.25
                weights['GA'] = weights.get('GA', 0) + 0.15
                weights['DTX'] = weights.get('DTX', 0) + 0.10
                flags.append("Livestock → IMM +0.25, GA +0.15, DTX +0.10 (barn dust, ammonia, Salmonella)")

                # Poultry-specific
                if self._is_poultry(animal):
                    flags.append("Poultry detected (Salmonella exposure from handling)")

                # Ruminant birthing exposure (Q-fever)
                if self._is_ruminant(animal) and ruminant_birthing_exposure:
                    weights['IMM'] = weights.get('IMM', 0) + 0.10
                    flags.append("Ruminant + birthing exposure → IMM +0.10 (Q-fever risk)")

            # ---------------------------------------------------------------
            # Other animal types
            # ---------------------------------------------------------------
            elif animal_type == 'rodent':
                weights['IMM'] = weights.get('IMM', 0) + 0.20
                weights['GA'] = weights.get('GA', 0) + 0.05
                flags.append("Rodent → IMM +0.20, GA +0.05 (robust aeroallergens)")

            elif animal_type == 'rabbit':
                weights['IMM'] = weights.get('IMM', 0) + 0.15
                weights['SKN'] = weights.get('SKN', 0) + 0.10
                flags.append("Rabbit → IMM +0.15, SKN +0.10 (allergens)")

            elif animal_type == 'ferret':
                weights['IMM'] = weights.get('IMM', 0) + 0.15
                weights['GA'] = weights.get('GA', 0) + 0.05
                flags.append("Ferret → IMM +0.15, GA +0.05 (allergens)")

            elif animal_type == 'fish':
                flags.append("Fish/amphibian detected (neutral; hygiene tip only)")

            elif animal_type == 'unknown':
                flags.append(f"⚠️ Unknown animal type: '{animal}' (no scoring applied)")

        # =================================================================
        # SECTION 2: CONTEXT AMPLIFIERS & MITIGATORS
        # =================================================================

        # Raw pet food (dogs/cats)
        if feeds_raw_food and (has_dog or has_cat):
            weights['GA'] = weights.get('GA', 0) + 0.10
            weights['IMM'] = weights.get('IMM', 0) + 0.05
            flags.append("Feeds raw pet food → GA +0.10, IMM +0.05 (Salmonella/Listeria risk)")

        # Backyard poultry handled frequently
        if backyard_poultry_frequent and has_livestock:
            weights['GA'] = weights.get('GA', 0) + 0.10
            flags.append("Frequent backyard poultry handling → GA +0.10 (Salmonella exposure)")

        # Litter box cleaning practices
        if litter_daily_cleaning and has_cat:
            weights['GA'] = weights.get('GA', 0) - 0.05
            flags.append("Daily cat litter removal → GA -0.05 (prevents oocyst maturation)")

        # Hand hygiene after cleaning
        if poor_hand_hygiene:
            weights['GA'] = weights.get('GA', 0) + 0.10
            flags.append("⚠️ Poor hand hygiene after cleaning → GA +0.10")
        elif good_hand_hygiene:
            weights['GA'] = weights.get('GA', 0) - 0.05
            flags.append("Good hand hygiene after cleaning → GA -0.05")

        # Multiple same-type sensitizers
        if num_cats >= 2:
            weights['IMM'] = weights.get('IMM', 0) + 0.05
            flags.append(f"Multiple cats ({num_cats}) → IMM +0.05 (higher airborne allergen load)")

        if num_birds >= 2:
            weights['IMM'] = weights.get('IMM', 0) + 0.05
            flags.append(f"Multiple birds ({num_birds}) → IMM +0.05 (higher bioaerosol load)")

        # HEPA air cleaner in bedroom
        if has_hepa_bedroom:
            weights['IMM'] = weights.get('IMM', 0) - 0.05
            weights['SKN'] = weights.get('SKN', 0) - 0.05
            flags.append("HEPA in bedroom → IMM -0.05, SKN -0.05 (reduced particulates/allergen)")

        # =================================================================
        # SECTION 3: APPLY CAPS
        # =================================================================

        # Individual focus area caps
        if 'IMM' in weights and weights['IMM'] > self.MAX_IMM:
            weights['IMM'] = self.MAX_IMM
            flags.append(f"⚠️ IMM capped at +{self.MAX_IMM}")

        if 'GA' in weights and weights['GA'] > self.MAX_GA:
            weights['GA'] = self.MAX_GA
            flags.append(f"⚠️ GA capped at +{self.MAX_GA}")

        if 'SKN' in weights and weights['SKN'] > self.MAX_SKN:
            weights['SKN'] = self.MAX_SKN
            flags.append(f"⚠️ SKN capped at +{self.MAX_SKN}")

        if 'DTX' in weights and weights['DTX'] > self.MAX_DTX:
            weights['DTX'] = self.MAX_DTX
            flags.append(f"⚠️ DTX capped at +{self.MAX_DTX}")

        # Total field cap
        total = sum(weights.values())
        if total > self.MAX_TOTAL:
            scale_factor = self.MAX_TOTAL / total
            for fa in weights:
                weights[fa] *= scale_factor
            flags.append(f"⚠️ Total field score capped at +{self.MAX_TOTAL} (scaled by {scale_factor:.2f})")

        # Remove near-zero weights
        weights = {fa: w for fa, w in weights.items() if abs(w) >= 0.01}

        return weights, flags

