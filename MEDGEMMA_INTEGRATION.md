# Personalized Supplement Recommendation System

## Introduction

This project presents an AI-driven personalized supplement recommendation system that generates clinically-grounded supplement protocols. The system supports **two workflow modes**:

1. **MedGemma Mode**: Uses Google's specialized medical AI (MedGemma-27b) deployed on Vertex AI for clinical reasoning
2. **Gemini-Only Mode**: Uses Gemini 2.5 Flash for all reasoning (no external medical AI)

Both modes use a multi-agent orchestration framework (CrewAI) to analyze patient biomarkers, medical conditions, symptoms, and lifestyle factors to produce actionable supplement protocols with clinical reasoning.

## Problem Statement

Personalized nutrition and supplementation is complex. Patients often receive generic recommendations that don't account for their unique health profile. Key challenges include:

- Interpreting biomarker data in clinical context
- Identifying which supplements address specific deficiencies or conditions
- Prioritizing recommendations when multiple health issues exist
- Determining appropriate dosages based on individual factors
- Providing clear reasoning that builds patient trust

## Our Solution

We built a two-stage pipeline: first we prepare and organize the patient's health data, then we use AI agents to generate personalized recommendations.

Think of it like visiting a specialist clinic:
1. **Stage 1 (Preprocessing):** The nurse reviews your lab reports, flags abnormal values, and prepares your file
2. **Stage 2 (AI Agents):** Multiple specialists review your case (optionally consulting MedGemma for medical guidance)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────┤
│   STAGE 1: PREPROCESSING (Prepare Patient Data)                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │ Step 1: Review blood work → Flag abnormal biomarkers            │   │
│   │ Step 2: Compile full profile → Demographics, conditions, meds   │   │
│   │ Step 3: Score health domains → 9 focus areas ranked by need     │   │
│   │ Step 4: Extract issues → Comprehensive list of problems:        │   │
│   │         - Biomarkers, conditions, symptoms                      │   │
│   │         - Dental health (root canals, mercury fillings, TMJ)    │   │
│   │         - Family history (cancer, diabetes, heart disease)      │   │
│   │         - Childhood factors (antibiotics, C-section)            │   │
│   │         - Lifestyle (diet type, stress level)                   │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   STAGE 2: AI AGENTS (5 Sequential Tasks)                               │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                                                                 │   │
│   │ Agent 1: Profile Summarizer                                     │   │
│   │    └── Creates concise natural language patient summary         │   │
│   │                                                                 │   │
│   │ Agent 2: Ingredient Discovery                                   │   │
│   │    └── [MedGemma Mode] Calls MedGemma for each health issue     │   │
│   │    └── [Gemini Mode] Uses Gemini clinical reasoning             │   │
│   │    └── Returns 15-25 candidate supplements                      │   │
│   │                                                                 │   │
│   │ Agent 3: Clinical Recommender                                   │   │
│   │    └── Prioritizes supplements with anti-overlap rule           │   │
│   │    └── Returns top 8-12 with patient-specific reasoning         │   │
│   │                                                                 │   │
│   │ Agent 4: Focus Area Specialist                                  │   │
│   │    └── Maps each supplement to 1-2 health focus areas           │   │
│   │    └── (CM, COG, DTX, IMM, MITO, SKN, STR, HRM, GA)            │   │
│   │                                                                 │   │
│   │ Agent 5: Dosage Compiler                                        │   │
│   │    └── Determines evidence-based dosages and timing             │   │
│   │    └── Compiles final protocol                                  │   │
│   │                                                                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              ▼                                          │
│                    FINAL SUPPLEMENT PROTOCOL                            │
└─────────────────────────────────────────────────────────────────────────┘
```

## Stage 1: Preprocessing Pipeline

Before any AI agent runs, we prepare the patient's data. This happens automatically using rule-based logic (no AI needed here).

### What Preprocessing Does

**Step 1: Biomarker Evaluation**
We scan the patient's blood work and flag anything outside normal ranges. For example:
- Vitamin D at 21 ng/mL → Flagged as "low" (optimal is 30-50)
- TSH at 4.5 mIU/L → Flagged as "high" (suggests thyroid issues)
- HbA1c at 6.2% → Flagged as "elevated" (pre-diabetic range)

**Step 2: User Profile Compilation**
We gather everything about the patient into one structured profile:
- Demographics (age, sex, weight)
- Medical conditions (diabetes, thyroid issues, etc.)
- Current medications and supplements
- Symptoms (fatigue, headaches, digestive issues)
- Lifestyle factors (diet type, stress level, sleep quality)
- Allergies and sensitivities

**Step 3: Focus Area Scoring**
We score 9 health domains based on the patient's data:
- Cardiometabolic Health
- Cognitive & Mental Health
- Immune Function
- Gut Health
- Hormonal Balance
- And 4 more...

Each domain gets a score (0-100) based on how many issues the patient has in that area. This helps prioritize recommendations.

**Step 4: Patient Issue Extraction (Enhanced)**
We extract ALL problems that need addressing. The extractor now captures:
```
Issues to address:
- Biomarkers: low vitamin D, high TSH, elevated HbA1c
- Conditions: hypothyroidism, kidney stones history
- Symptoms: chronic fatigue, frequent headaches, poor sleep
- Lifestyle: high stress (8/10), vegetarian diet → needs B12, Iron, Zinc
- Exposures: mold exposure at home
- Dental: root canals, mercury fillings, TMJ, bleeding gums
- Family history: cancer (mother), diabetes (father)
- Childhood factors: antibiotic use, C-section birth
```

Output is saved to `outputs/<user_id>/extracted_patient_issues.json` for verification.

---

## Stage 2: AI Agents Pipeline

We have **5 AI agents** that work in sequence. In MedGemma mode, agents call MedGemma tools for clinical reasoning. In Gemini-only mode, agents use their own clinical knowledge.

### How the Orchestration Works

We use **Gemini 2.5 Flash** as the orchestrating LLM that coordinates agents. In MedGemma mode, agents also call MedGemma tools for specialized medical reasoning:

- **Gemini** = The coordinator who reads the patient file and formulates questions
- **MedGemma** = The medical expert who answers each question

This separation is important: Gemini is good at understanding context and breaking down problems, while MedGemma is trained specifically on medical literature.

---

## MedGemma Integration

MedGemma is deployed on Google Cloud Vertex AI. We built three custom tools that let our agents consult MedGemma for different purposes.

### Tool 1: MedGemmaTool (Ingredient Discovery)

**Purpose:** Find which supplements might help with each health issue.

**How the agent uses it:**

The agent receives the patient's issue list and breaks it down into individual queries. For a patient with multiple problems, the agent might make 10-15 separate calls to MedGemma:

```
Patient issues: low vitamin D, high cholesterol, poor sleep, high stress,
                hypothyroidism, frequent headaches, mold exposure

Agent breaks this into questions:
  → Call 1: "supplements for low vitamin D"
  → Call 2: "supplements for high cholesterol and cardiovascular risk"
  → Call 3: "supplements for poor sleep quality"
  → Call 4: "supplements for high stress and anxiety"
  → Call 5: "supplements for hypothyroidism and thyroid support"
  → Call 6: "supplements for frequent headaches and migraines"
  → Call 7: "supplements for mold exposure and detoxification"
```

**Each MedGemma response returns 2-3 supplement names:**
```
Query:   "supplements for high stress and anxiety"
Response: "Ashwagandha, L-Theanine, Magnesium"
```

After all calls complete, the agent combines and deduplicates the results. If Magnesium appeared in 3 different responses (stress, sleep, headaches), it gets noted as addressing multiple issues — making it a higher priority candidate.

**Final output:** 15-25 candidate supplements with all reasons each was suggested (no truncation).

### Tool 2: MedGemmaRecommenderTool (Clinical Reasoning)

**Purpose:** Prioritize supplements and provide patient-specific explanations.

**How the agent uses it:**

This tool receives the full picture — patient summary plus all candidate supplements with ALL their reasons — and asks MedGemma to select the best 8-12:

```
Input to MedGemma:
  Patient: 50yo female, vegetarian, perimenopause, Vitamin D 21 ng/mL,
           TSH 4.5, high stress (8/10), poor sleep, mold exposure...

  Candidates: Vitamin D3, Magnesium, Ashwagandha, Selenium, NAC,
              Omega-3, Probiotics, CoQ10, B-Complex...
              (each with all associated reasons)
```

**Anti-Overlap Rule:** The tool includes a rule to prevent selecting supplements that cover the exact same problems unless they complement each other (e.g., Vitamin D + K2).

MedGemma analyzes the full context and returns prioritized recommendations:

```
1. Vitamin D3
   Why: Your level of 21.4 ng/mL is below optimal. As a vegetarian with
   limited dietary sources, supplementation is essential for immune
   function and hormonal balance during perimenopause.

2. Magnesium Glycinate
   Why: Addresses multiple concerns — your high stress (8/10), sleep
   difficulties, and frequent headaches. Glycinate form is gentle on
   digestion.
```

**Final output:** Top 8-12 supplements ranked by priority with clear explanations.

### Tool 3: MedGemmaDosageTool (Dosage & Frequency)

**Purpose:** Determine the right dosage for each supplement based on patient context.

**How the agent uses it:**

The agent takes the prioritized supplement list and calls MedGemma for each one, asking for dosage guidance:

```
For 10 recommended supplements, agent makes 10 calls:
  → Call 1: "Vitamin D3 dosage for 50yo female with level 21 ng/mL"
  → Call 2: "Magnesium Glycinate dosage for adult with high stress and poor sleep"
  → Call 3: "Selenium dosage for patient with elevated TSH 4.5"
  → Call 4: "Ashwagandha dosage for perimenopausal woman with high stress"
  ... and so on for each supplement
```

**Each MedGemma response returns dosage and timing:**
```
Query:   "Vitamin D3 dosage for 50yo female with level 21 ng/mL"
Response: "2000-4000 IU once daily with fatty meal"

Query:   "Magnesium Glycinate dosage for adult with high stress and poor sleep"
Response: "300-400 mg once daily before bedtime"
```

**Final output:** Complete protocol with dosages, frequencies, and timing for each supplement.

### Tool 4: MedGemmaFocusAreaTool (Focus Area Assignment)

**Purpose:** Map each supplement to 1-2 health focus area codes.

**Focus Area Codes:**
- CM: Cardiometabolic & Metabolic Health
- COG: Cognitive & Mental Health
- DTX: Detoxification & Biotransformation
- IMM: Immune Function & Inflammation
- MITO: Mitochondrial & Energy Metabolism
- SKN: Skin & Barrier Function
- STR: Stress-Axis & Nervous System Resilience
- HRM: Hormonal Health
- GA: Gut Health and Assimilation

---

## Gemini-Only Mode

When MedGemma tools are disabled, the same 5-agent pipeline runs using Gemini's clinical knowledge:

```python
# crew.py - Gemini-only configuration
@agent
def medgemma_ingredient_discovery(self) -> Agent:
    return Agent(
        config=self.agents_config['medgemma_ingredient_discovery'],
        tools=[],  # GEMINI-ONLY: No external tools
        llm=llm
    )
```

This allows A/B comparison of protocol quality between MedGemma and Gemini-only approaches.

---

## Why This Architecture Works

**The key insight:** We break down the patient's health profile into focused questions rather than one big prompt. This approach:

1. **Gets better answers** — Focused questions yield more accurate responses
2. **Covers everything** — Iterating through each issue ensures completeness
3. **Provides transparency** — Every question and answer is logged
4. **Enables personalization** — Each query includes patient-specific context
5. **Prevents overlap** — Anti-overlap rule ensures diverse coverage

**The flow (MedGemma mode):**
```
Patient with 30+ health issues
    ↓
Agent breaks into focused questions for supplement discovery
    ↓
MedGemma returns 2-3 supplements per question
    ↓
Agent deduplicates to 15-25 candidates (all reasons preserved)
    ↓
MedGemma prioritizes with anti-overlap rule (8-12 final)
    ↓
Focus areas assigned to each supplement
    ↓
Dosages determined with patient context
    ↓
Final protocol saved
```

**Total MedGemma calls per patient:** Typically 20-40 calls, each focused on a specific question.

---

## Technical Implementation

### Vertex AI Configuration

```python
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION", "us-central1")
ENDPOINT_ID = os.getenv("MEDGEMMA_ENDPOINT_ID")
```

### API Parameters

| Tool | max_tokens | temperature | Purpose |
|------|------------|-------------|---------|
| Ingredient Discovery | 30 | 0 | Concise supplement names only |
| Clinical Reasoning | 2048 | 0.3 | Detailed patient-specific reasoning |
| Dosage | 50 | 0 | Precise dosage recommendations |

### Agent Configuration

**MedGemma Mode** - Each agent uses a specific MedGemma tool:

```python
@agent
def medgemma_ingredient_discovery(self) -> Agent:
    return Agent(
        config=self.agents_config['medgemma_ingredient_discovery'],
        tools=[MedGemmaTool()],
        llm=llm  # Gemini for orchestration
    )

@agent
def supplement_recommender(self) -> Agent:
    return Agent(
        config=self.agents_config['supplement_recommender'],
        tools=[MedGemmaRecommenderTool()],
        llm=llm
    )

@agent
def focus_area_specialist(self) -> Agent:
    return Agent(
        config=self.agents_config['focus_area_specialist'],
        tools=[MedGemmaFocusAreaTool()],
        llm=llm
    )

@agent
def final_supplement_compiler(self) -> Agent:
    return Agent(
        config=self.agents_config['final_supplement_compiler'],
        tools=[MedGemmaDosageTool()],
        llm=llm
    )
```

**Gemini-Only Mode** - All agents use `tools=[]`:

```python
# To switch to Gemini-only mode, set tools=[] for all agents
tools=[],  # GEMINI-ONLY: No external tools
```

## Sample Output

**Input:** 50-year-old female, vegetarian, approaching menopause with low Vitamin D (21.4 ng/mL), elevated TSH (3.23), high stress, and digestive issues.

**Final Protocol:**
```json
{
  "supplement_recommendations": [
    {
      "ingredient_name": "Vitamin D3",
      "recommended_dosage": "2000 IU",
      "frequency": "Once daily with breakfast",
      "focus_area": ["IMM", "HRM"],
      "why": "Your Vitamin D level of 21.4 ng/mL is below optimal range. As a vegetarian with limited dietary sources, supplementation supports immune function and hormonal balance during perimenopause."
    },
    {
      "ingredient_name": "Selenium",
      "recommended_dosage": "200 mcg",
      "frequency": "Once daily",
      "focus_area": ["HRM"],
      "why": "Your elevated TSH of 3.23 suggests suboptimal thyroid function. Selenium is essential for thyroid hormone conversion and may help normalize TSH levels."
    }
  ]
}
```



