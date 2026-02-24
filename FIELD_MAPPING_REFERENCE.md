# Phase 3 Field Mapping Reference

This document shows the complete mapping between the old 47-field format and the new 93-question schema.

## Mapping Overview

| Position | Primary Q | Follow-ups | Strategy | Description |
|----------|-----------|------------|----------|-------------|
| 0 | q001 | - | simple | Top health goals |
| 1 | q002 | - | simple | Patient reasoning |
| 2 | q003 | - | simple | Lifestyle willingness (Yes/No only) |
| 3 | q005 | - | simple | Last felt well |
| 4 | q006 | - | simple | Trigger event |
| 5 | q007 | - | simple | What makes worse |
| 6 | q008 | q009 | concatenate | Time of day worse + explanation |
| 7 | q010 | q011 | concatenate | Where symptoms worse + explanation |
| 8 | q012 | q013 | concatenate | Food/drink triggers + details |
| 9 | q014 | - | simple | What helps |
| 10 | q015 | q016, q017 | concatenate | Long-term meds + which/how long + year |
| 11 | q018 | - | simple | Activity intensity |
| 12 | q019 | - | simple | Sunlight exposure ranking |
| 13 | q020 | q021 | concatenate | Sleep aids + details |
| 14 | q022 | - | simple | Consistent bedtime |
| 15 | q023 | - | simple | Consistent wake time |
| 16 | q024 | - | simple | Typical meals |
| 17 | q025 | q026 | concatenate | Food sensitivities + details |
| 18 | q027 | q028 | concatenate | Cravings + other cravings |
| 19 | q029 | - | simple | Mood |
| 20 | q030 | - | simple | Stress level (1-10) |
| 21 | q031 | - | simple | Stress sources |
| 22 | q032 | q033 | concatenate | Relaxation techniques + other |
| 23 | q034 | q035 | concatenate | Support sources + other |
| 24 | q036 | q037 | concatenate | Trauma history + details |
| 25 | q038 | q039 | concatenate | Childhood illnesses + details |
| 26 | q040 | q041 | concatenate | Childhood home security + details |
| 27 | q042 | q043 | concatenate | Breastfeeding + duration |
| 28 | q044 | q045 | concatenate | Early environmental exposures + details |
| 29 | q046 | q047 | concatenate | Tooth sensitivity + details |
| 30 | q048 | q049 | concatenate | Indoor environment factors + other |
| 31 | q050 | q051 | concatenate | Chemical sensitivity + triggers |
| 32 | q052 | q053 | concatenate | Caffeine use + sensitivity |
| 33 | q054 | q055 | concatenate | Alcohol flush + details |
| 34 | q056 | - | simple | Synthetic fiber wear |
| 35 | q057 | q058 | concatenate | Seasonal allergies + details |
| 36 | q060 | q061 | concatenate | Air filter + brand/model |
| 37 | q062 | q063 | concatenate | Water filter + brand/model |
| 38 | q064 | q065 | concatenate | Animal types + other |
| 39 | q066 | - | simple | Pet living location |
| 40 | q067 | - | simple | Unintentional weight change |
| 41 | q068 | - | simple | Weight change details |
| 42 | q069 | - | simple | Bowel movement frequency |
| 43 | q075 | - | simple | Transit time |
| 44 | q091 | - | simple | Headache/migraine details |
| 45 | q092 | - | simple | Chronic pain details |
| 46 | q093 | - | simple | Skin issues details |

## Questions Not Yet Mapped (26 questions)

These questions are new in the schema and don't have corresponding rulesets yet:

- **q004**: Lifestyle willingness follow-up (intentionally skipped - using simple strategy for q003)
- **q059**: Hygiene products
- **q070-q074**: Digestive follow-ups (bloating timing, heartburn, constipation triggers, stool analysis, anorectal symptoms)
- **q076-q090**: Hormone/Sex-specific questions (birth control, HRT, pregnancy history, breast cancer risk, male concerns, gynecomastia, prostate issues)

These can be added as positions 47+ when rulesets are created for them.

## Merge Strategy Details

### Simple (27 fields)
Returns only the primary question value. Follow-ups are ignored.

**Example:**
- Input: `q003 = "Yes"`, `q004 = "Open to small changes..."`
- Output: `"Yes"`

### Concatenate (20 fields)
Combines primary + follow-up values with `"; "` separator.

**Example:**
- Input: `q020 = "Yes"`, `q021 = "Melatonin 3mg, helps with sleep"`
- Output: `"Yes; Melatonin 3mg, helps with sleep"`

## Usage in Code

```python
from .rulesets_phase3.constants import PHASE3_SCHEMA

# Get question metadata
question_info = PHASE3_SCHEMA["q003"]
print(question_info["question"])  # "Are you willing to make lifestyle changes?"
print(question_info["category"])  # "Goals & Narrative"

# The FIELD_MAPPING is used automatically by _extract_phase3_to_dataframe()
# No manual intervention needed - just pass new format data
```

## Testing

To test the mapping:
```bash
python test_focus_areas.py phase3
```

This will:
1. Load new schema format from `sample.json`
2. Use FIELD_MAPPING to extract 47 fields
3. Pass to rulesets in expected format
4. Generate focus area scores

