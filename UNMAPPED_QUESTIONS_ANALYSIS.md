# Unmapped Questions Analysis

## Summary

**Total Questions in New Schema:** 93 (q001 - q093)
**Questions Mapped to 47 Fields:** 67 questions
**Questions NOT Mapped (Unmapped):** 26 questions

---

## Mapped Questions (67 total)

### Used as Primary Questions (47):
q001, q002, q003, q005, q006, q007, q008, q010, q012, q014, q015, q018, q019, q020, q022, q023, q024, q025, q027, q029, q030, q031, q032, q034, q036, q038, q040, q042, q044, q046, q048, q050, q052, q054, q056, q057, q060, q062, q064, q066, q067, q068, q069, q075, q091, q092, q093

### Used as Follow-ups (20):
q009, q011, q013, q016, q017, q021, q026, q028, q033, q035, q037, q039, q041, q043, q045, q047, q049, q051, q053, q055, q058, q061, q063, q065

**Note:** Some questions appear in both lists (used as both primary and follow-up in different contexts)

---

## Unmapped Questions (26 total)

### 1. **q004** - Lifestyle Willingness Follow-up
- **Category:** Goals & Narrative
- **Question:** "If people are not sure about the response or say No - Anything else you'd like to share about it?"
- **Why Unmapped:** Intentionally skipped - Field 2 uses "simple" strategy (only q003 Yes/No)
- **Status:** ⚠️ Intentional - ruleset only needs Yes/No

### 2. **q059** - Hygiene Products
- **Category:** Environment & Exposures
- **Subcategory:** Hygiene Products
- **Question:** "Now I'll read the hygiene step you usually may do in your daily life and I'd like you to share the brand or product you use for it. Example for Toothpaste would be Colgate. Options: Bodywash, Soap, Scrub, Shampoo, Conditioner, Toothpaste, Mouthwash"
- **Why Unmapped:** No ruleset exists yet
- **Status:** 🆕 New field - needs ruleset

### 3-7. **q070-q074** - Digestive Follow-ups (5 questions)
- **Category:** Systems Check
- **Subcategory:** Digestive follow-up

**q070:** "If user selected Bloating, Bloating timing: 'When do you feel bloated—within 2 hours of eating, after 2 hours, or variable?'"
**q071:** "If user selected Heartburn 'Is it reflux/GERD or occasional heartburn?'"
**q072:** "If user selected constipation 'Any known triggers (e.g., after trauma, travel, foods)?'"
**q073:** "Stool analysis: 'Any foul smell, notable color, or blood/mucus?'"
**q074:** "Anorectal symptoms: 'Any hemorrhoids, fissures, or prolapse?'"

- **Why Unmapped:** No rulesets exist yet - these are detailed digestive follow-ups
- **Status:** 🆕 New fields - need rulesets
- **Potential Impact:** GA (Gut Health) focus area

### 8-9. **q076-q077** - Hormonal Birth Control (2 questions)
- **Category:** Hormone / Sex-Specific
- **Subcategory:** Hormone Therapy / Birth Control

**q076:** "Are you using hormonal birth control?"
**q077:** "Please explain the type, dosage, start, reason and duration for which you have taken it?"

- **Why Unmapped:** No ruleset exists yet
- **Status:** 🆕 New fields - need rulesets
- **Potential Impact:** HRM (Hormonal Health), GA (Gut Health)

### 10-11. **q078-q079** - HRT Details (2 questions)
- **Category:** Hormone / Sex-Specific
- **Subcategory:** HRT Details

**q078:** "Do you receive any HRT (Hormone Replacement Therapy)."
**q079:** "If yes, please explain"

- **Why Unmapped:** No ruleset exists yet
- **Status:** 🆕 New fields - need rulesets
- **Potential Impact:** HRM (Hormonal Health)

### 12-13. **q080-q081** - Pregnancy History (2 questions)
- **Category:** Hormone / Sex-Specific
- **Subcategory:** Pregnancy History, Timing Between Pregnancies/Miscarriages

**q080:** "You can choose to skip the following question if you'd like. How many pregnancies, births, miscarriages or complications?"
**q081:** "If Pregnancy or Miscarriages selected/shared, ask - What was the time between each pregnancy/miscarriage/complication?"

- **Why Unmapped:** No ruleset exists yet
- **Status:** 🆕 New fields - need rulesets
- **Potential Impact:** HRM, IMM, MITO

### 14-15. **q082-q083** - Breast Cancer Risk (2 questions)
- **Category:** Hormone / Sex-Specific
- **Subcategory:** Breast Cancer Risk

**q082:** "Have you ever been diagnosed of breast cancer or considered high-risk?"
**q083:** "If yes, Please explain."

- **Why Unmapped:** No ruleset exists yet
- **Status:** 🆕 New fields - need rulesets
- **Potential Impact:** HRM, DTX, IMM

### 16. **q084** - Male Concerns Details
- **Category:** Hormone / Sex-Specific
- **Subcategory:** Male Concerns Details (If Yes)
- **Question:** "You previously shared that you had Male hormones/sexual concerns. Please describe—onset, labs, treatments"
- **Why Unmapped:** No ruleset exists yet
- **Status:** 🆕 New field - needs ruleset
- **Potential Impact:** HRM

### 17-18. **q085-q086** - Gynecomastia (2 questions)
- **Category:** Hormone / Sex-Specific
- **Subcategory:** Gynecomastia

**q085:** "Do you have diagnosed or suspected gynecomastia (breast tissue development in males leading to enlarged breasts)?"
**q086:** "If Yes: Explain diagnosis and any ongoing treatment."

- **Why Unmapped:** No ruleset exists yet
- **Status:** 🆕 New fields - need rulesets
- **Potential Impact:** HRM, DTX

### 19-20. **q087-q088** - Prostate Issues (2 questions)
- **Category:** Hormone / Sex-Specific
- **Subcategory:** Prostate Issues

**q087:** "Do you have any prostate related issue?"
**q088:** "If yes, Please explain."

- **Why Unmapped:** No ruleset exists yet
- **Status:** 🆕 New fields - need rulesets
- **Potential Impact:** HRM, IMM

### 21-22. **q089-q090** - Prostate/Testicular Cancer Risk (2 questions)
- **Category:** Hormone / Sex-Specific
- **Subcategory:** Prostate/Testicular Cancer Risk

**q089:** "Have you ever been diagnosed of prostate or testicular cancer or considered high-risk?"
**q090:** "If yes, Please explain."

- **Why Unmapped:** No ruleset exists yet
- **Status:** 🆕 New fields - need rulesets
- **Potential Impact:** HRM, DTX, IMM

---

## Breakdown by Category

### Intentionally Unmapped (1 question):
- **q004** - Lifestyle willingness follow-up (not needed by ruleset)

### New Fields Needing Rulesets (25 questions):

**Environment & Exposures (1):**
- q059 - Hygiene Products

**Systems Check - Digestive (5):**
- q070 - Bloating timing
- q071 - Heartburn/GERD details
- q072 - Constipation triggers
- q073 - Stool analysis
- q074 - Anorectal symptoms

**Hormone / Sex-Specific (19):**
- q076-q077 - Hormonal birth control (2)
- q078-q079 - HRT details (2)
- q080-q081 - Pregnancy history (2)
- q082-q083 - Breast cancer risk (2)
- q084 - Male concerns details (1)
- q085-q086 - Gynecomastia (2)
- q087-q088 - Prostate issues (2)
- q089-q090 - Prostate/testicular cancer risk (2)

---

## Recommendations

### Priority 1: High Impact (Digestive Follow-ups)
**Questions:** q070-q074 (5 questions)
**Reason:** These provide detailed digestive symptom context that could significantly improve GA (Gut Health) scoring
**Suggested Positions:** 47-51
**Estimated Effort:** 2-3 days (need to create 5 new rulesets)

### Priority 2: Medium Impact (Hormonal Health)
**Questions:** q076-q090 (15 questions)
**Reason:** These fill gaps in HRM (Hormonal Health) focus area, which currently has minimal Phase 3 data
**Suggested Positions:** 52-66
**Estimated Effort:** 5-7 days (need to create 8 new rulesets with sex-specific logic)

### Priority 3: Low Impact (Hygiene Products)
**Questions:** q059 (1 question)
**Reason:** Could contribute to DTX/SKN but lower priority
**Suggested Position:** 67
**Estimated Effort:** 1 day

---

## Current Coverage

**Mapped:** 67/93 questions = **72% coverage**
**Unmapped:** 26/93 questions = **28% unmapped**

**By Category:**
- Goals & Narrative: 9/10 mapped (90%)
- Meds & Supplements: 3/3 mapped (100%)
- Lifestyle: 2/2 mapped (100%)
- Sleep: 3/3 mapped (100%)
- Nutrition: 4/4 mapped (100%)
- Stress & Support: 7/7 mapped (100%)
- Childhood & Development: 8/8 mapped (100%)
- Dental History: 2/2 mapped (100%)
- Environment & Exposures: 13/14 mapped (93%)
- Pets & Animals: 3/3 mapped (100%)
- Systems Check: 4/9 mapped (44%) ⚠️
- Hormone / Sex-Specific: 0/19 mapped (0%) ⚠️
- Pain · Headache · Skin: 3/3 mapped (100%)

**Gaps:**
- ⚠️ **Systems Check (Digestive):** 5 unmapped questions
- ⚠️ **Hormone / Sex-Specific:** 19 unmapped questions (entire category!)

---

## Next Steps

1. **Immediate:** Migration is complete and working ✅
2. **Short-term:** Add digestive follow-up rulesets (q070-q074) for better GA scoring
3. **Medium-term:** Add hormonal health rulesets (q076-q090) to improve HRM coverage
4. **Long-term:** Add hygiene products ruleset (q059) for DTX/SKN enhancement

