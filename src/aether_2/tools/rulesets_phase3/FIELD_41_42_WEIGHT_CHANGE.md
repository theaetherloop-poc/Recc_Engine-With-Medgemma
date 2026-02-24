# Fields 41-42: Unintentional Weight Change

## Overview

This is a **two-field system** that captures unintentional weight changes and scores them based on clinical significance.

- **Field 41**: Radio button (Yes/No) - "Any unintentional weight change recently?"
- **Field 42**: Free text (conditional on Field 41 = Yes) - "How much and over what timeframe?"

## Field 41: Unintentional Weight Change (Radio)

### Input Format
- Radio selection: "Yes" or "No"

### Scoring
- **No scoring** - This field only captures the Yes/No response
- All scoring happens in Field 42

### Implementation
- File: `unintentional_weight_change_ruleset.py`
- Class: `UnintentionalWeightChangeRuleset`
- Method: `get_unintentional_weight_change_weights(choice)`

---

## Field 42: Unintentional Weight Change Details

### Input Format
Free-text description of weight change, e.g.:
- "Gained 10 lb in 2 months"
- "Lost 5 kg over 6 months"
- "Dropped 15 pounds in 1 month"

### NLP Extraction

The ruleset extracts:
1. **Direction**: gain | loss (synonyms: gained/put on vs lost/dropped)
2. **Magnitude**: number + unit (kg, lb, lbs, pounds, stone) → converted to kg
3. **Time window**: days | weeks | months | years → normalized to months
4. **Intention**: Detects intentional weight change (dieting, exercise) → neutral scoring

### Severity Tiers

#### Weight Loss
- **Mild**: 2-5% in ≤6-12 mo OR 2-5 kg in ≤6 mo
- **Moderate**: ≥5% in ≤6-12 mo
- **Severe**: ≥10% in 6 mo OR ≥5% in 1 mo
- **Rapid**: ≥5 kg in ≤1 mo OR ≥2 kg/week

#### Weight Gain
- **Mild**: 2-5% in ≤6-12 mo OR 2-5 kg in ≤6 mo
- **Moderate**: >5% in ≤6-12 mo
- **Severe**: ≥10% in 6 mo
- **Rapid**: ≥5 kg in ≤1 mo OR ≥2 kg/week

### Base Scores

#### Weight Loss

| Severity | GA | CM | HRM | MITO | COG | STR | IMM | Notes |
|----------|----|----|-----|------|-----|-----|-----|-------|
| Mild | +0.2 | +0.1 | +0.1 | +0.3 | +0.1 | +0.1 | +0.1 | Early catabolic signal |
| Moderate | +0.4 | +0.2 | +0.2 | +0.6 | +0.2 | +0.2 | +0.3 | Clinically significant |
| Severe/Rapid | +0.6 | +0.3 | +0.2 | +0.8 | +0.3 | +0.3 | +0.4 | Severe nutritional risk |

#### Weight Gain

| Severity | GA | CM | HRM | MITO | STR | Notes |
|----------|----|----|-----|------|-----|-------|
| Mild | +0.1 | +0.3 | +0.1 | +0.1 | 0 | Early insulin-resistance risk |
| Moderate | +0.2 | +0.6 | +0.2 | +0.2 | 0 | Higher cardiometabolic risk |
| Severe | +0.3 | +0.9 | +0.3 | +0.3 | +0.1 | Very high cardiometabolic risk |
| Rapid | +0.2 | +0.8 | +0.2 | +0.3 | +0.1 | Screen for fluid retention |

### Amplifiers

#### Weight Loss Amplifiers
- **Malabsorption/IBD**: If diarrhea, steatorrhea, abdominal pain, or IBD/celiac history → GA +0.2
- **Hyperthyroidism**: If thyrotoxic symptoms (heat intolerance, tremor) → HRM +0.2
- **Post-infectious**: If post-infectious onset → IMM +0.1, GA +0.1

#### Weight Gain Amplifiers
- **Reflux + Late Meals**: If both present → GA +0.1
- **Medications**: If on steroids or antipsychotics → CM +0.1, MITO +0.1
- **Central Adiposity**: If described → CM +0.1

### Red Flags (Medical Review Suggested)

#### Weight Loss
- ≥10% in 6 mo OR ≥5% in 1 mo → Severe nutritional risk
- Loss + diarrhea + blood in stool → GI disease, IBD, malignancy
- Loss + night sweats/fever → Infection, malignancy

#### Weight Gain
- Rapid gain + edema/SOB → Cardiac/renal/hepatic fluid retention
- Rapid gain + high-dose steroids → Medication effect

### Cross-Field Context

The ruleset uses context from:
- **Demographics**: Baseline weight (for % change calculation)
- **Phase 2 GI**: Diarrhea, steatorrhea, abdominal pain, blood in stool
- **Diagnoses**: IBD, celiac history
- **Medications**: Steroids, antipsychotics
- **Phase 2 Symptoms**: Edema, SOB, night sweats, fever, thyrotoxic symptoms
- **Field 16**: Late meals
- **Field 29**: Reflux/heartburn
- **Trigger Events**: Post-infectious onset

### Implementation
- File: `unintentional_weight_change_details_ruleset.py`
- Class: `UnintentionalWeightChangeDetailsRuleset`
- Method: `get_weight_change_details_weights(...)`

### Testing
Both rulesets include comprehensive test suites:
```bash
python -m src.aether_2.tools.rulesets_phase3.unintentional_weight_change_ruleset
python -m src.aether_2.tools.rulesets_phase3.unintentional_weight_change_details_ruleset
```

## Integration Notes

1. **Field 41** should be processed first (returns all zeros)
2. **Field 42** should only be processed if Field 41 = "Yes"
3. Extract baseline weight from demographics if available
4. Extract cross-field context from Phase 2 and other Phase 3 fields
5. Red flags should trigger UI banners/alerts for medical review

## Example Outputs

### Example 1: Moderate Weight Loss
- Input: "Lost 10 lb in 2 months" (baseline: 70 kg)
- Parsed: loss 4.5 kg over 2.0 months
- % change: 19.4% (6-mo rate)
- Severity: severe
- Scores: GA +0.6, CM +0.3, HRM +0.2, MITO +0.8, COG +0.3, STR +0.3, IMM +0.4
- Red flag: Severe weight loss → medical review

### Example 2: Rapid Weight Gain
- Input: "Put on 6 kg in 1 month" (baseline: 75 kg)
- Parsed: gain 6.0 kg over 1.0 months
- % change: 48.0% (6-mo rate)
- Severity: severe
- Scores: GA +0.3, CM +0.9, HRM +0.3, MITO +0.3, STR +0.1
- Note: Very high cardiometabolic risk

### Example 3: Intentional Weight Loss
- Input: "Trying to lose weight, lost 5 lb in 2 months"
- Detected as intentional → neutral scoring (all zeros)

