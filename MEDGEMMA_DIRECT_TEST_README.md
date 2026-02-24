# MedGemma Direct Test - README

## Overview
This is an **independent test script** to evaluate MedGemma's ability to generate complete supplement protocols directly from user health profiles, bypassing the main Aether AI pipeline.

## Purpose
- Test MedGemma's medical reasoning capabilities when given a complete patient profile
- Compare direct MedGemma output vs. the multi-agent CrewAI pipeline approach
- Evaluate if MedGemma alone can generate clinically relevant supplement recommendations

## Files Created
1. **medgemma_direct_test.py** - Initial version (verbose prompt, had issues with token overflow)
2. **medgemma_direct_test_v2.py** - ✅ **Working version** (concise prompt, saves as markdown)

## How to Run

```bash
python medgemma_direct_test_v2.py
```

### Requirements
- Environment variables set in `.env`:
  - `GCP_PROJECT_ID`
  - `GCP_REGION`
  - `MEDGEMMA_ENDPOINT_ID`
- Python packages:
  - `google-cloud-aiplatform`
  - `python-dotenv`

## What It Does

1. **Loads** a user profile from `outputs/geetahj_at_gmail_com/user_profile.json`
2. **Creates** a concise medical prompt with:
   - Patient demographics
   - Critical biomarker flags (high iron, low vitamin D, thyroid issues, etc.)
   - Symptoms (digestive issues, menopause transition)
3. **Queries** MedGemma endpoint directly
4. **Saves** the response as a markdown file

## Output Format

The script generates a markdown file: `medgemma_protocol_[profile]_[timestamp].md`

Contains:
- Prompt sent to MedGemma
- Full MedGemma response with 10 supplement recommendations
- Each recommendation includes:
  - Supplement name
  - Dosage
  - Frequency
  - Patient-specific reason

## Test Results

✅ **Success!** MedGemma generated:
- 10 relevant supplement recommendations
- Appropriate dosages and frequencies
- Patient-specific reasoning based on biomarkers
- Important clinical considerations and warnings
- Correctly identified need to STOP iron supplementation (high iron levels)

### Sample Recommendations Generated:
1. Vitamin D3 - 2000-5000 IU - Once daily
2. Calcium Citrate - 500-1000 mg - Twice daily with meals
3. Selenium - 100-200 mcg - Once daily (thyroid support)
4. Magnesium Glycinate - 200-400 mg - Once daily before bed
5. Probiotic - Multi-strain - Once daily
6. Black Cohosh - 40-80 mg - For menopause symptoms
7. Milk Thistle - 140-280 mg - For elevated liver enzymes
8. Fiber Supplement - 5-15g - For constipation
9. L-Theanine - 100-200 mg - For stress/sleep
10. **STOP Iron Supplementation** - Patient has high iron

## Key Findings

### What Worked Well:
- ✅ MedGemma understood the complete patient context
- ✅ Generated clinically appropriate recommendations
- ✅ Provided patient-specific reasoning
- ✅ Identified contraindications (stop iron)
- ✅ Included important clinical considerations

### Limitations:
- Prompt needs to be concise (<1000 chars) to avoid token overflow
- Output format is text-based, not structured JSON
- No web research or evidence citations (unlike full pipeline)
- No RAG-based ingredient ranking

## Comparison to Main Pipeline

| Feature | MedGemma Direct | Full Aether Pipeline |
|---------|----------------|---------------------|
| Speed | Fast (~10 sec) | Slower (multi-agent) |
| Evidence | Medical knowledge only | Web research + PubMed |
| Reasoning | Single-pass | Multi-agent collaboration |
| Output | Text/Markdown | Structured JSON + Excel |
| Ingredient Discovery | Limited to training data | MedGemma + Web + RAG |
| Dosage Precision | Ranges | Specific recommendations |

## Conclusion

MedGemma can generate **clinically relevant supplement protocols** when given a complete patient profile. However, the full Aether pipeline adds:
- Evidence-based research
- RAG-powered ingredient ranking
- Structured output formats
- Multi-agent validation

This test demonstrates MedGemma's strong medical reasoning capabilities as a foundation for the pipeline.

## Next Steps

To test with different profiles, modify this line in `medgemma_direct_test_v2.py`:

```python
USER_PROFILE_PATH = "outputs/[profile_folder]/user_profile.json"
```

Available profiles:
- `geetahj_at_gmail_com`
- `hello_at_drantonikachanel_com`
- `ian_at_sturgeoncreative_com`
- `kevin_yar_at_omics-os_com`
- And more in `outputs/` directory

