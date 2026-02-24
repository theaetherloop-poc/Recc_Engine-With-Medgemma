"""
Field 41: Unintentional Weight Change (Radio: Yes/No)

This field captures whether the patient has experienced unintentional weight change.
If "Yes", Field 42 will contain the details (magnitude, direction, timeframe).

This ruleset only handles the radio selection. The actual scoring is done in Field 42.
"""

from typing import Dict, List, Tuple


class UnintentionalWeightChangeRuleset:
    """
    Ruleset for Field 41: Unintentional Weight Change (Radio: Yes/No)
    
    This field only captures the Yes/No response. The actual weight change details
    and scoring are handled by Field 42 (UnintentionalWeightChangeDetailsRuleset).
    """

    def get_unintentional_weight_change_weights(
        self,
        choice: str
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Process Field 41: Unintentional Weight Change radio selection.
        
        Args:
            choice: Radio selection ("Yes" or "No")
            
        Returns:
            Tuple of (scores_dict, flags_list)
            - scores_dict: All zeros (scoring happens in Field 42)
            - flags_list: Validation warnings
            
        Examples:
            >>> ruleset = UnintentionalWeightChangeRuleset()
            >>> scores, flags = ruleset.get_unintentional_weight_change_weights("Yes")
            >>> # scores will be all zeros; actual scoring in Field 42
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
        
        # Normalize choice
        choice_norm = choice.strip().lower() if choice else ""
        
        # Validate choice
        if choice_norm not in ["yes", "no", ""]:
            flags.append(f"⚠️  Field 41: Unexpected choice '{choice}' (expected Yes/No)")
        
        # If "Yes", expect Field 42 to contain details
        if choice_norm == "yes":
            flags.append("ℹ️  Field 41: User reported weight change → see Field 42 for details and scoring")
        
        # If "No", no further action needed
        if choice_norm == "no":
            flags.append("ℹ️  Field 41: No unintentional weight change reported")
        
        return scores, flags


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("FIELD 41: UNINTENTIONAL WEIGHT CHANGE (RADIO) - TEST SUITE")
    print("="*80)
    
    ruleset = UnintentionalWeightChangeRuleset()
    
    test_cases = [
        ("Yes", "User reports weight change"),
        ("No", "No weight change"),
        ("", "Empty input"),
        ("Maybe", "Invalid choice"),
    ]
    
    for choice, description in test_cases:
        print(f"\n--- Test: {description} ---")
        print(f"Input: '{choice}'")
        
        scores, flags = ruleset.get_unintentional_weight_change_weights(choice)
        
        print("\nScores:")
        for fa, score in scores.items():
            if score > 0:
                print(f"  {fa}: {score:+.2f}")
        if all(s == 0 for s in scores.values()):
            print("  (All zeros - scoring happens in Field 42)")
        
        if flags:
            print("\nFlags:")
            for flag in flags:
                print(f"  {flag}")
    
    print("\n" + "="*80)
    print("✅ Field 41 test suite complete")
    print("="*80)

