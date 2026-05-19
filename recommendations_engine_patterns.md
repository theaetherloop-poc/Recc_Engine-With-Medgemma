# Recommendations Engine — Patterns & Improvement Notes
*Synthesized from all SME call summaries (Jan 12 – Mar 9, 2026)*

---

## SECTION 1: Core Failure Modes (What the AI Is Getting Wrong)

### 1.1 — Over-treating Mild / Borderline Biomarkers
**Pattern:** The engine triggers supplement recommendations for values that are technically "low/high" but clinically insignificant.
**Example:** HbA1c of 5.1 was flagged as needing intervention. SMEs called this "excellent" and removed chromium, zinc, green tea extract, and niacin that were downstream of this false flag.
**Fix:**
- Build **biomarker-specific "actionable" thresholds** — not a single flag for "above/below normal range"
- Add a **severity band** per marker: `normal → low-normal → borderline → elevated → high`
- Only trigger supplement recommendations at `borderline` or above; at `low-normal`, use monitoring/lifestyle suggestions
- Add **cushioning logic** so values barely out of range don't get the same treatment as clearly abnormal ones

---

### 1.2 — Segmented Thinking (Recommending Per-Marker Instead of Per-Person)
**Pattern:** The engine maps 1 biomarker → 1 supplement repeatedly, resulting in a fragmented stack of single-purpose nutrients that SMEs pruned heavily.
**Example:** chromium (glucose) + niacin (lipids) + zinc (metabolic) + B5 (general) recommended instead of berberine, which addresses all of these at once.
**Fix:**
- Implement **"multi-benefit coverage"** scoring: prefer supplements that address multiple active signals over several single-target ones
- Add a **domain-grouping step** before output: group all active signals by system (metabolic, liver, thyroid, etc.), then pick the highest-leverage intervention per group
- Model should think in **"big picture" axes** (metabolic axis, liver axis, thyroid axis) rather than individual biomarkers

---

### 1.3 — Missing High-Salience Signals (Misses)
**Pattern:** AI omits clinically important recommendations when certain signals are present — SMEs had to add them back every time.
**Recurring misses across calls:**

| Signal Present | Expected Recommendation | Why Missed |
|---|---|---|
| Elevated liver enzymes (AST/ALT) | Milk thistle (silymarin) | Engine doesn't connect liver enzymes → hepatoprotective |
| Low DHEA / low testosterone | DHEA supplementation | Endocrine axis not tracked |
| Allergy symptoms (itchy skin, sneezing) | Quercetin | Symptom-to-supplement mapping incomplete |
| Elevated TSH | Selenium | Thyroid-selenium pathway not encoded |
| GI symptoms (acid reflux / heartburn) | Ginger, licorice root | Symptom-specific mapping missing |
| Migraines/headaches | Feverfew + Butterbur + B6 | Headache cluster not recognized |
| High iron / ferritin | "Retest + investigate" flag | No follow-up logic; not just supplement it |
| Mold exposure reported | Detox pathway flag | Environmental signal ignored |

**Fix:** Build a **"signal coverage checklist"** — before outputting recommendations, verify that each high-salience symptom/biomarker has a corresponding recommendation or a documented reason why it was excluded.

---

### 1.4 — Hallucination / Demographic Mismatch
**Pattern:** Engine recommends supplements that are inappropriate for the user's demographic or biomarker profile.
**Example:** DIM (an estrogen-metabolism supplement) was recommended for a 42-year-old male with testosterone ~750 and no estrogen issues found. This is a hallucination — the model appears to have generated a "detox" recommendation without checking demographic fit.
**Fix:**
- Before recommending any hormone-axis supplement, gate on:
  - User's biological sex
  - Relevant hormone biomarkers being present and actually abnormal
- Create a **"biological plausibility check"** layer that flags demographically implausible suggestions before output

---

### 1.5 — Redundancy Without Sequencing
**Pattern:** Multiple supplements targeting the same domain are recommended simultaneously with no "try this first, add that later" logic.
**Example:** Omega-3 + green tea extract + berberine + red rice yeast for lipids — all in Round 1.
**Fix:**
- Build **explicit sequencing**: Pick 1 first-line intervention per domain → retest in 3–6 months → escalate only if needed
- Use a **"Round 1 / Round 2 / Optional"** output tier instead of a flat list

---

### 1.6 — Ignoring "Already Taking" Context
**Pattern:** If a patient is already taking a supplement, the engine either ignores it or adds it again.
**Example:** Patient was already taking selenium. Engine should detect and retain it, not ignore it.
**Fix:**
- Intake form must capture **current supplements**
- Engine must explicitly output one of: `keep (already taking)`, `replace with X`, `add to existing stack`, `consolidate into combo product`
- This avoids the "what do I stop?" confusion for users

---

---

## SECTION 2: Clinical Reasoning Patterns to Encode

### 2.1 — Severity-Based Intervention Intensity
```
biomarker_value → severity_band → intervention_tier

normal         → no action / lifestyle note
low-normal     → monitor + lifestyle suggestion
borderline     → 1 supplement max, low-dose, retest in 3 months
elevated       → 1–2 supplements, standard dose, retest in 3 months
high           → stronger intervention (e.g., red rice yeast > green tea for severe cholesterol), consider referral
```

---

### 2.2 — Signal Hierarchy (What Overrides What)
When both a questionnaire answer and a lab value are available for the same issue, **lab value wins** as the primary classifier. Questionnaire data shifts to "contextual tailoring."

Example:
- Sunlight exposure question + serum Vitamin D available → use serum Vitamin D as classifier; sunlight data informs dosing/form choice only
- Patient self-reports GI issues but no symptoms documented → favor diagnostic/monitoring steps over stacking gut supplements

---

### 2.3 — Multivitamin Baseline Logic
Before recommending any isolated vitamin or mineral, ask:
> "Is this nutrient likely already covered by a quality multivitamin, or obtainable in adequate amounts from a typical diet?"

If yes → **deprioritize** unless there is a specific documented deficiency or a clinical indication beyond general replenishment.

Nutrients commonly caught by this filter:
- Zinc (unless vegan + high phytic acid, or specific testosterone context)
- Vitamin C (unless severely depleted)
- Vitamin E (typically unnecessary)
- Pantothenic acid (B5)
- Many B vitamins at standard levels

---

### 2.4 — "Diet-First / Lifestyle-First" Gate for Mild Signals
For mild biomarker abnormalities or patient goals without clear symptom documentation:
1. Suggest behavioral change first (CGM, food journaling, elimination diet, iodized salt)
2. Add supplements only if behavioral steps are already in place or if the signal is clear enough to warrant direct intervention

---

### 2.5 — Organ Axis Scanning (What to Check Before Outputting)
The engine should mentally scan each of these axes and ask "do I have a recommendation here if the signal exists?"

| Axis | Key Signal(s) | Default First-Line Supplement |
|---|---|---|
| Metabolic / Glucose | HbA1c, fasting glucose, insulin | Berberine (preferred over chromium/niacin combo) |
| Lipid | LDL, TG, cholesterol ratios | Berberine (first-line), Red Rice Yeast (escalation) |
| Liver | Elevated AST, ALT, AST:ALT ratio | Milk thistle (silymarin) |
| Thyroid | Elevated TSH | Selenium; iodine via diet (iodized salt), not supplement |
| Adrenal / Androgen | Low DHEA, low testosterone | DHEA |
| Allergy / Mast Cell | Allergy symptoms (itching, sneezing) | Quercetin |
| GI / Reflux | Heartburn, reflux symptoms | Ginger, licorice root (DGL) |
| Migraine / Headache | Migraine/headache complaint | Feverfew + Butterbur + B6 (often as a combo) |
| Inflammation | High hsCRP | Curcumin, Omega-3 |
| Mitochondrial / Energy | Fatigue, mitochondrial markers | CoQ10, L-Carnitine |
| Perimenopause / Hormonal Sleep | Female + sleep/mood issues | Vitex (Chaste Tree), not apigenin |

---

### 2.6 — Gating Rules for High-Risk / Complex Supplements

| Supplement | Gate Condition | Behavior |
|---|---|---|
| Potassium | Never supplement by default if low | Prompt "investigate cause first"; treat as nutrition/electrolyte issue |
| Iodine | Thyroid concern | Prefer iodized salt first; only supplement if diet clearly insufficient |
| Calcium | Bone/deficiency concern | Check dietary intake; carbonate for reflux, citrate for bone health; don't auto-add |
| Iron | High ferritin / iron | Do NOT add iron; flag for retest + investigate cause (metabolic syndrome, hemochromatosis, etc.) |
| Hormones (DHEA, testosterone-related) | Any endocrine suggestion | Gate on biological sex + relevant biomarkers being clearly abnormal |
| Melatonin | Sleep issues | Effective for sleep onset, NOT for sleep apnea-type unrefreshed sleep |

---

### 2.7 — Supplement Form and Timing Specificity
These should be encoded as hard rules in the output layer:

| Supplement | Form / Timing Rule |
|---|---|
| Magnesium (for relaxation/sleep) | Glycinate or orotate; ~200 mg nightly |
| Magnesium (for constipation) | Citrate or oxide |
| Magnesium (for cognitive/neurological) | Threonate |
| Magnesium (for active/daytime use) | Glycerophosphate (non-sedating) |
| Magnesium (for cramping) | Malate |
| Red Rice Yeast | Take at night (mimics statin timing) |
| Probiotics | Empty stomach, 20–30 min before breakfast (avoid gastric acid inactivation) |
| Vitamin D | With fatty meal (fat-soluble); weekly high-dose (e.g., 10,000 IU/week) is equivalent to ~1,400 IU/day |
| Zinc | Consider "pulsing" (higher dose for a period, then reassess) rather than continuous |
| Vitamin B6 | Use P-5-P form (active form) |

---

### 2.8 — Combo Product Equivalencies
When multiple supplements address the same complaint and are commonly sold together, the engine should recognize these clusters and note they may be available as a single product:

| Complaint | Common Combo Cluster |
|---|---|
| Migraines | B6 + Feverfew + Butterbur |
| GI / Heartburn | Ginger + Licorice root (DGL) + Silymarin |
| Metabolic support | Berberine + Omega-3 |
| Thyroid | Selenium + Iodine (diet-sourced) |
| Sleep / Stress | Ashwagandha + Magnesium glycinate |

---

### 2.9 — Composite Biomarker Interpretation
A single biomarker in isolation can be misleading. The engine should implement **"pair logic"** where combinations of markers produce a modified interpretation:

| Marker Combination | Modified Interpretation |
|---|---|
| Low Vitamin D + high calcium | Do NOT supplement vitamin D aggressively; check for granulomatous disease (sarcoidosis) |
| High iron + metabolic syndrome | Likely secondary iron overload; treat metabolic root cause first |
| Low DHEA + low testosterone | Same pathway; address together, not separately |
| Low Vitamin D + low TSH | Consider compounding thyroid-metabolism connection |
| High BUN:Creatinine + low albumin | Dehydration + protein insufficiency; address both simultaneously |
| Elevated AST + high ferritin | Likely liver involvement; milk thistle + retest ferritin after addressing metabolic issues |

---

---

## SECTION 3: Output Architecture Recommendations

### 3.1 — Tiered Output Model
Replace the flat list with an explicit tiered structure:

```
TIER 1 — "Core / Spot-On" (2–3 items)
  → Directly tied to primary complaint + clearest biomarker signals

TIER 2 — "Supportive" (3–5 items)
  → Addresses secondary signals and deficiencies; mostly kept

TIER 3 — "Round 2 / Escalation" (0–3 items, clearly labeled)
  → Only if Tier 1+2 don't produce improvement after 3–6 months

TIER 4 — "Optional / Nice-to-Have"
  → Low-priority; flag as "can add later"; better as part of multivitamin

TIER 5 — "Not Recommended / Better Alternative Exists"
  → Explicitly label substitutions (e.g., "Niacin → replaced by Berberine")

TIER 6 — "Avoid / Contraindicated" (rare — only for genuine safety issues)
```

---

### 3.2 — Pill Burden Management Rule
- **Hard soft-cap: ~8–10 total supplements**
- Preferred distribution: 2–3 core + 3–5 supportive
- If the engine would exceed this, it must prune lowest-value items first
- Pruning priority: remove items that are (a) covered by a multivitamin, (b) targeting an axis already covered by a higher-leverage supplement, (c) mild-biomarker-only with no symptom corroboration

---

### 3.3 — "Not Wrong vs Wrong" Labeling
When removing a supplement, the engine should classify the reason explicitly:

| Category | Meaning | Example |
|---|---|---|
| `contra` | Biologically wrong / mismatched | DIM for estrogen in males with no estrogen issue |
| `unnecessary` | Not wrong, just not needed | Zinc when no deficiency, covered by multivitamin |
| `redundant` | A better alternative covers the same ground | Chromium when berberine is already chosen |
| `too-early` | Right supplement, wrong timing (should be Round 2) | Red rice yeast when green tea would suffice for mild cholesterol |
| `unsupported` | No symptom or biomarker to justify it | Digestive enzymes when no digestive symptoms reported |

---

### 3.4 — Retest / Follow-Up Flags
For these categories, output should always include a follow-up note rather than just a supplement:

- High ferritin / iron → "Retest in 6–8 weeks; if persists, investigate hemochromatosis or metabolic causes"
- Elevated TSH → "Retest TSH + free T3/T4 in 3 months; if no improvement on selenium/iodine, escalate"
- Borderline HbA1c → "Monitor with CGM; retest HbA1c in 3 months before adding metabolic supplements"
- Low Vitamin D (mild) → "Retest after 3 months of supplementation"

---

---

## SECTION 4: Biomarker Reference Framework (IFM-Style Approach)

*Based on Feb 11 call with Arno Kroner — system-level thinking*

### 4.1 — Organize Markers into Functional Axes
Rather than a flat list of lab values, group and interpret markers by system:

| Functional Axis | Key Markers |
|---|---|
| Cardiometabolic | LDL, HDL, TG, ApoB, Lp(a), fasting glucose, HbA1c, insulin |
| Liver / Detox | AST, ALT, AST:ALT ratio, GGT, bilirubin, ferritin, albumin |
| Thyroid | TSH, free T3, free T4, reverse T3 |
| Adrenal / Androgen | DHEA-S, testosterone (free/total), cortisol |
| Kidney | eGFR, creatinine, BUN, BUN:Creatinine ratio |
| Inflammation | hsCRP, fibrinogen, homocysteine |
| Micronutrient Status | Vitamin D, B12, folate, ferritin, zinc, magnesium (RBC) |

### 4.2 — Relationship Rules Between Axes
- An abnormality in one axis should prompt a check of related axes before finalizing recommendations
- Example: metabolic syndrome → check liver axis → check iron/ferritin → check inflammation markers

---

---

## SECTION 5: Quick-Reference Decision Rules

```
IF   HbA1c < 5.7 AND no glucose symptoms
THEN do NOT recommend glucose-specific supplements

IF   TSH elevated
THEN recommend selenium; suggest iodized salt; schedule retest in 3 months

IF   AST or ALT elevated
THEN recommend milk thistle (silymarin)

IF   allergy symptoms present (itching, sneezing, histamine signs)
THEN recommend quercetin

IF   DHEA low OR testosterone low
THEN check other androgen markers; consider DHEA supplement; note pathway connection to user

IF   potassium low
THEN do NOT supplement; flag for dietary review and cause investigation

IF   ferritin high OR iron high
THEN do NOT add more iron; flag for retest; note possible metabolic syndrome connection

IF   sleep issue = "unrefreshed" OR snoring present
THEN flag for sleep apnea evaluation; melatonin alone is insufficient

IF   patient reports mold exposure
THEN surface as high-priority detox pathway; add targeted recommendation or follow-up prompt

IF   supplement X is being recommended AND patient already takes X
THEN output: "keep existing [X]" rather than adding a duplicate

IF   recommendation count > 10
THEN prune: remove lowest-value items (multivitamin-covered, mild-biomarker-only, redundant)

IF   a symptom is reported (reflux, headache, allergy) AND no supplement addresses it
THEN this is a coverage gap — add symptom-targeted recommendation

IF   supplement recommended for hormone axis
THEN gate on: biological sex match + biomarker confirmation + clinical plausibility check
```

---

---

---

## SECTION 6: Red-Flag STOP Pathway (Safety Escalation)

*New from Feb 22, Feb 23 calls — critical safety logic*

### 6.1 — When to Refuse a Supplement Protocol Entirely
Not every profile should receive supplements. When lab values show extreme abnormalities with high differential-diagnosis severity, the engine must **stop, flag, and refer** instead of generating a protocol.

**Trigger conditions:**
- Extremely high ferritin/iron (off-chart) + elevated liver enzymes → could indicate hemochromatosis, malignancy, or other serious medical conditions
- SME quote: "too many red flags," "not ethical," "lawsuit risk" if not referred

**Correct engine behavior:**
1. Generate NO supplement recommendations
2. Output a clear, non-alarming referral message: "These findings need further investigation. Please see your primary care provider for additional evaluation before starting any supplement protocol."
3. Do NOT speculate on diagnoses
4. Log internally as a "red-flag case" for quality review

---

### 6.2 — Hard Contraindications (Supplement × Medication/Condition)
These are absolute rules — the engine must never violate them:

| Supplement | Contraindicated With | Reason |
|---|---|---|
| Chromium | Insulin therapy / Type 1 diabetes | Dangerous blood sugar interaction; "shouldn't be taking chromium" |
| Licorice / DGL | Hypertension medications | Licorice can raise blood pressure; "big red" contraindication |
| Red Rice Yeast | Statin medications | Duplicates statin mechanism; can worsen muscle pain/myopathy |
| Iron supplements | High ferritin / iron overload | Worsens existing overload; investigate cause first |
| Aggressive Vitamin D dosing | High serum calcium | Can worsen hypercalcemia and vascular calcification risk |
| Potassium supplements | Without clinical supervision | Cardiac risk from excess potassium |
| "Estrogen metabolism" products | Males without confirmed estrogen elevation | Biologically irrelevant |

---

### 6.3 — Medication Coverage Suppression
When a user is already on a disease-specific medication, do NOT add redundant supplement "solutions" for the same condition:

| Medication | Condition | Engine Behavior |
|---|---|---|
| Allopurinol | Gout | Suppress gout-specific supplements (cherry extract, etc.); emphasize diet-based gout management instead |
| Statins | Hyperlipidemia | Do NOT add red rice yeast (same mechanism); use different pathways (omega-3, berberine) if additional support needed |
| Insulin | Diabetes | Suppress chromium; be cautious with glucose-lowering supplements |
| Levothyroxine | Hypothyroidism | Be cautious stacking thyroid support; selenium is OK but avoid excessive iodine |

---

---

## SECTION 7: Input Validation & Data Quality Rules

### 7.1 — Self-Report Consistency Checks
Users frequently mislabel their conditions. The engine must validate self-reported diagnoses against expected physiology and biomarker patterns.

**Example:** User selects "overactive thyroid" but TSH is elevated (which implies underactive thyroid / Hashimoto's). Hashimoto's = hypothyroid, not hyperthyroid. The user likely mislabeled.

**Required behavior:**
1. If self-report conflicts with biomarker pattern, flag as inconsistent
2. Ask clarifying follow-up questions rather than interpreting literally
3. Treat the biomarker pattern as more reliable than the label
4. Note in output: "Your self-reported thyroid condition appears inconsistent with your lab values. We recommend confirming your diagnosis with your healthcare provider."

---

### 7.2 — Unit and Reference Range Mismatch Detection
Lab values sometimes arrive in inconsistent units or with reference ranges from a different assay/unit system.

**Example:** Free testosterone "calculated" value appeared inconsistent because the reference range was in a different unit system.

**Required behavior:**
1. Detect when a lab value doesn't match the expected reference range pattern
2. Downgrade confidence in that biomarker interpretation
3. Do NOT make strong supplement claims based on potentially mismatched data
4. Flag for review: "This lab value appears to use a different reference range than expected. Please confirm the unit and range."

---

### 7.3 — Missing Labs: Graceful Degradation
Lab panels vary by kit and gender. Key markers may be absent.

**Required behavior:**
1. Do NOT hallucinate or assume values for missing labs
2. If a cluster inference is incomplete due to missing labs, note the gap
3. Optionally recommend "next labs to consider" to complete the picture (e.g., "Your thyroid cluster would benefit from free T3, free T4, and reverse T3 in your next panel")
4. Reduce confidence in cluster-level conclusions when key markers are missing

---

---

## SECTION 8: Condition-Specific Pathways (New)

### 8.1 — PCOS Pathway
**Trigger:** Female + PCOS diagnosis or symptoms (irregular cycles, weight/BMI concerns, androgen excess signs)
**First-line:**
- Inositol (myo-inositol preferred, often ~2000–4000 mg/day)
- Vitex (Chaste Tree / chaste berry) — supports progesterone and luteal phase balance
**Supportive:** Berberine (if insulin resistance / prediabetes co-occurs), Omega-3, Vitamin D
**Suppress:** Irrelevant "estrogen metabolism" products unless clearly indicated; generic adaptogens without cortisol justification

---

### 8.2 — Neuropathy Pathway
**Trigger:** Neuropathy symptoms (tingling, numbness, burning sensations) — especially in diabetic profiles
**First-line:**
- Benfotiamine (fat-soluble B1 form) — best evidence for diabetic neuropathy
- Alpha-lipoic acid (ALA) — supports nerve health and glucose metabolism
**Supportive:** Magnesium, B12 (methylcobalamin form)
**Gate:** If user is on insulin / Type 1, suppress chromium regardless of glucose markers

---

### 8.3 — No Gallbladder / Post-Cholecystectomy Pathway
**Trigger:** User reports gallbladder removal / cholecystectomy
**First-line:**
- Ox bile — supports fat digestion and bile acid replacement
- Digestive enzyme support (lipase-containing)
**Key logic:** Without a gallbladder, bile is released continuously rather than in concentrated bursts. Fat-soluble nutrients (vitamins A, D, E, K, omega-3) may be poorly absorbed. Fiber-only approaches for GI issues are insufficient without addressing bile deficiency.
**The engine should:** Detect "no gallbladder" → automatically trigger bile/digestion support pathway → flag fat-soluble nutrient absorption risk

---

### 8.4 — Gout Pathway
**Trigger:** Gout diagnosis or uric acid elevated
**If on allopurinol:** Suppress gout-specific supplements; emphasize diet-based management (low-purine diet, hydration, cherry intake via food)
**If NOT on medication:** Consider cherry extract, vitamin C, hydration guidance
**If gout is "managed":** Cherry extract is superfluous; diet-first

---

### 8.5 — Alcohol Use + Liver Elevation Pathway
**Trigger:** Reported regular alcohol use + elevated AST/ALT
**Primary recommendation:** Behavior change — reduce or eliminate alcohol; frame as the most impactful intervention
**Supportive supplements:** Milk thistle (silymarin), NAC (optional), dandelion/artichoke (optional)
**Key rule:** Do NOT just add liver supplements without flagging the behavioral root cause

---

### 8.6 — Migraine / Brain Fog / Fatigue — Mitochondrial Support Pathway
**Trigger:** Chronic headaches/migraines + fatigue + brain fog
**First-line:**
- CoQ10 (mitochondrial energy support)
- Magnesium glycinate (multiple mechanisms: relaxation + migraine prevention)
- Riboflavin (B2) at 400 mg/day (strong migraine prevention evidence)
**Combo cluster:** B6 + Feverfew + Butterbur (often sold as migraine combo products)
**Supportive:** L-Carnitine (~500–1000 mg/day, titrate; caution in kidney disease)
**Gate:** Keep symptom-driven; do not add mitochondrial stack without a clear fatigue/headache/cognition driver

---

---

## SECTION 9: Supplement Specificity Rules (New)

### 9.1 — Vague Categories Must Be Made Specific
The engine must NEVER recommend vague supplement categories. Each must be specified to a form, strain, or standardization level:

| Vague Category | Required Specificity | Why |
|---|---|---|
| "Probiotics" | Named strain(s) + CFU count + timing | "Probiotics" is clinically meaningless; efficacy depends on strain and dysbiosis pattern. Require gut symptoms or stool test data before recommending. |
| "Plant sterols" | Specific product/standardization | Effect depends on formulation; generic mention is not actionable |
| "B complex" | Specify active forms: methylcobalamin (B12), methylfolate (B9/5-MTHF), P5P (B6), benfotiamine (B1) | Common forms (cyanocobalamin, folic acid) are less bioavailable; active forms preferred |
| "Magnesium" | Specify salt: glycinate, citrate, threonate, malate, etc. | Efficacy varies dramatically by form and use case |
| "Curcumin / Turmeric" | Standardized extract with measured curcuminoids (or phytosome/liposomal form) | Dietary turmeric powder is low potency; therapeutic effect requires standardized extract |
| "Garlic" | Aged garlic extract (e.g., Kyolic) with known standardization | Generic garlic is inconsistent; aged/standardized has better evidence |

---

### 9.2 — D3 + K2 Bundling Rule
When recommending Vitamin D3, the engine should also include Vitamin K2 as a cofactor pairing. K2 directs calcium to bones and away from soft tissues/arteries.

**Exception:** If serum calcium is already high, or if there's a vascular calcification / kidney stone risk, add a caution note about calcium status before pairing.

---

### 9.3 — Supplement Duration: Not Everything Is "Forever"
SMEs emphasized that supplement protocols should be time-limited trials, not indefinite regimens.

**Default framing:**
- "Take [supplement] for 3 months, then retest relevant biomarkers and reassess"
- "If symptoms improve and biomarkers normalize, consider tapering or discontinuing"
- Pulsing is appropriate for some (e.g., zinc: higher dose for a period, then stop)

---

---

## SECTION 10: Bloating / GI Diagnostic Logic (New)

Probiotic and gut-supplement recommendations must be gated on the **type and timing** of symptoms:

| Bloating Pattern | Likely Cause | Recommended Action |
|---|---|---|
| Bloating immediately after eating | Low stomach acid (hypochlorhydria) | Consider betaine HCl / digestive bitters; NOT probiotics as first-line |
| Bloating ~2 hours after eating | Dysbiosis or pancreatic enzyme insufficiency | Consider stool test; digestive enzymes; targeted probiotics based on results |
| No bloating / no GI symptoms | N/A | Do NOT recommend probiotics by default; mark as optional at most |

**Rule:** Always ask about bloating timing before recommending probiotics. Suggest stool testing before prescribing bacteria. Do not add probiotics "randomly."

---

---

## SECTION 11: Biomarker Cluster Activation Model (New — from Feb 13 call)

*This is the architectural direction endorsed by SMEs for the next version of the engine.*

### 11.1 — Concept
Instead of treating each biomarker independently, pre-define **biomarker clusters** that represent functional systems. When enough markers in a cluster are abnormal, the cluster "activates" and drives downstream logic (follow-up questions → supplement selection).

### 11.2 — Starter Cluster Taxonomy

| Cluster | Key Biomarkers | Notes |
|---|---|---|
| **Inflammation (general)** | Ferritin, hs-CRP | Keep separate from autoimmune markers |
| **Autoimmune** | TPO antibody, ANA | Do NOT merge with general inflammation by default |
| **Dehydration pattern** | High albumin + high creatinine + high BUN + low eGFR + high hemoglobin/hematocrit | This is a diagnostic cluster: triggers hydration guidance + retest, NOT supplements |
| **Bone & mineral metabolism** | Calcium, Vitamin D, PTH | Natural grouping; D + K2 pairing logic here |
| **Metabolic syndrome** | HDL, LDL, TG, VLDL, HbA1c, Lp(a), ApoB, ApoA1, TG:HDL ratio, total chol:HDL ratio | Not all markers need to be abnormal to activate; cholesterol-heavy vs glucose-heavy sub-patterns drive different supplement choices |
| **Endocrine / hormonal** | Testosterone, free T, free androgen index, SHBG, DHEA, TSH; female: estradiol, FSH, LH; cortisol | Multi-cluster membership allowed (e.g., HbA1c in metabolic AND endocrine) |
| **Liver function** | Total protein, albumin, AST, ALT, total bilirubin, direct bilirubin | Triggers liver-safe supplement choices + alcohol/medication history prompts |
| **Iron / anemia** | Iron, ferritin, UIBC, hemoglobin, hematocrit | High ferritin → different path than low ferritin |
| **Thyroid** | TSH, free T3, free T4, reverse T3, TPO Ab | Missing T3/T4 → suggest completing panel |

### 11.3 — Cluster Activation Flow
```
Step 1: Raw labs → flag abnormals
Step 2: Map flagged labs to clusters → compute cluster activation scores
Step 3: Activated clusters → determine relevant follow-up questions (not all questions for all users)
Step 4: Clusters + questionnaire answers → supplement selection per cluster (1–2 per cluster max)
Step 5: Merge across clusters → deduplicate → enforce pill burden ceiling → tier output
```

### 11.4 — Multi-Cluster Membership
Some biomarkers belong to multiple clusters. This is by design. E.g.:
- HbA1c → Metabolic syndrome cluster AND Endocrine cluster
- Ferritin → Iron/anemia cluster AND Inflammation cluster AND Liver function cluster
- Albumin → Liver function cluster AND Dehydration pattern cluster

---

### 11.5 — Composite Interpretation (Expanded)
Beyond the pairs listed in Section 2.9, add these:

| Marker Combination | Modified Interpretation |
|---|---|
| High albumin + high creatinine + high BUN + low eGFR + high hematocrit | **Dehydration pattern** — recommend hydration repletion + retest; do NOT supplement aggressively |
| Elevated AST + normal ALT (AST:ALT ratio alone) | Absolute enzyme values required before recommending liver support; ratio alone is insufficient to justify milk thistle |
| Low ferritin + vegetarian diet | Iron supplementation is core (not optional); consider liquid iron or iron glycinate; add constipation mitigation |
| Elevated insulin + normal-ish HbA1c | Insulin resistance may be earlier than HbA1c reflects; berberine pathway still justified |
| Normal cortisol + self-reported "high stress" | Ashwagandha/adaptogens are optional at best; do not treat self-reported stress as biochemical cortisol elevation |

---

---

## SECTION 12: Adaptogen Gating Rule (New — Reinforced Across Multiple Calls)

Ashwagandha and other adaptogens appeared in nearly every AI output but were removed by SMEs ~50% of the time. The consistent rule:

**Gate adaptogens on objective stress biomarkers (cortisol curve) and/or clear endocrine disruption:**
- If daytime cortisol is elevated → ashwagandha is justified
- If cortisol is normal → ashwagandha is optional at best; adds unnecessary pill burden and liver/kidney processing load
- Self-reported stress alone is NOT sufficient to justify ashwagandha in a medically complex profile
- In medically complex patients (multiple conditions, multiple meds), ashwagandha adds metabolic processing load — prefer to skip it

---

---

## SECTION 13: Drug–Supplement Interaction Safety Layer (New)

*From Feb 23, Mar 9 calls — this was called out as a missing global safety layer*

The engine MUST implement systematic drug–supplement interaction checking before outputting any recommendation.

**Known critical interactions from SME calls:**

| Supplement | Drug | Interaction | Engine Action |
|---|---|---|---|
| Red Rice Yeast | Statins (atorvastatin, simvastatin, etc.) | Duplicates statin mechanism → increased myopathy/rhabdomyolysis risk | Suppress red rice yeast if user is on a statin |
| Licorice / DGL | Antihypertensives (ACE inhibitors, ARBs, diuretics, etc.) | Licorice raises blood pressure | Suppress licorice; find alternative for heartburn |
| Chromium | Insulin, sulfonylureas | Can potentiate blood sugar lowering → hypoglycemia risk | Suppress chromium for insulin users / Type 1 |
| St. John's Wort | SSRIs, oral contraceptives, anticoagulants | Induces CYP enzymes → reduces drug efficacy | Suppress or flag with strong warning |
| High-dose Vitamin E | Anticoagulants (warfarin, etc.) | Increases bleeding risk | Dose-limit or suppress |
| High-dose Fish Oil | Anticoagulants | Additive anticoagulant effect at high doses | Flag dose caution |

**Implementation:** This should be a pre-output filter layer that runs after supplement selection but before final output, checking each recommendation against the user's medication list.

---

*Last updated: synthesized from SME calls Jan 12, Jan 20, Feb 6, Feb 11, Feb 13, Feb 22, Feb 23, Mar 9, 2026*
