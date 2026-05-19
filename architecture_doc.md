====
7. SYSTEM ARCHITECTURE
========================================================================


The system follows a multi-agent architecture powered by Gemini 2.5 Flash LLM with the following components:

LLM CONFIGURATION:
- Primary LLM: Google Gemini 2.5 Flash (via Vertex AI)
- Model ID: gemini-2.5-flash-preview-04-17
- Configuration: Temperature 0.3 for consistent clinical reasoning

KEY CONFIGURATION FILES AND THEIR PURPOSES:


CREW.PY - Core Orchestration Engine:
This is the central file that defines the entire AI crew structure and orchestrates the multi-agent workflow. It serves as the main configuration hub where:
- All AI agents are defined with their specific roles, goals, and backstories
- Agent tools are assigned and configured (SerperDevTool for web search)
- Task definitions are created with input/output specifications
- Pydantic models are imported for data validation
- The overall crew workflow is orchestrated
- Agent dependencies and task sequences are established


The file uses CrewAI decorators (@agent, @task, @crew) to define the multi-agent system structure. Each agent is configured with specific tools and capabilities, while tasks define the work each agent performs and how they pass data to subsequent agents.
 
 
PYPROJECT.TOML - Project Configuration and Dependencies: 
This file serves as the project's configuration manifest and dependency management system: 
- Defines project metadata (name, version, description, authors) 
- Specifies Python version requirements (>=3.10,<3.14) 
- Lists all project dependencies with version constraints 
- Defines project scripts and entry points 
- Configures build system requirements 
- Sets up CrewAI-specific project configuration 
 
 
Key dependencies include CrewAI framework, OpenAI/Vertex AI libraries, machine learning libraries (scikit-learn, numpy, torch), vector database (ChromaDB), and data processing tools (pandas, openpyxl). 
 
 
AGENTS.YAML - Agent Definitions and Roles: 
This configuration file defines the personality, expertise, and behavior of each AI agent: 
- Agent roles and specializations (e.g., "Focus Area Prioritizer", "Medical Supplement Recommendation Specialist") 
- Detailed goals and objectives for each agent 
- Backstories that establish agent expertise and decision-making approach 
- LLM model assignments (Vertex AI Gemini, Azure OpenAI GPT-4o) 
- Agent-specific instructions and constraints 
 
 
Each agent is designed with a specific medical or technical expertise, ensuring that complex health decisions are made by agents with appropriate domain knowledge. 
 
 
TASKS.YAML - Task Definitions and Workflow: 
This file defines the specific tasks each agent performs and how they connect: 
- Task descriptions with detailed instructions 
- Expected output formats and validation requirements 
- Agent assignments for each task 
- Input/output specifications 
- Task dependencies and sequencing 
- Output file configurations 
 
 
Tasks are designed to create a logical flow where each agent builds upon the work of previous agents, ensuring comprehensive analysis and personalized recommendations. 
 
 
MODELS.PY - Data Structure Definitions: 
This file contains all Pydantic model definitions that ensure data consistency and validation throughout the system: 
- UserProfile: Complete patient data structure 
- FocusAreaScores: Health focus area scoring results 
- SupplementRecommendation: Individual supplement recommendations 
- FlaggedBiomarker: Biomarker analysis results 
- RankedIngredient: RAG search results 
- And other data models for system-wide consistency 
 
 
These models ensure that data passed between agents maintains proper structure and validation, preventing errors and ensuring reliable data flow. 
 
 
 
 
FULL WORKFLOW:
**Preprocessing Pipeline (Python Functions):**
1. Biomarker Evaluation: Analyzes lab results against reference ranges and flags abnormalities
2. Focus Area Scoring: Uses modular rulesets to score and prioritize health focus areas
3. User Profile Compilation: Combines patient demographics, medical history, and biomarker analysis
4. Patient Issues Extraction: Extracts structured health issues from user profile for agent consumption

**CrewAI Pipeline (AI Agents):**
5. Profile Summarizer: Creates concise natural language summary of patient profile (Gemini reasoning)
6. Web Ingredient Discovery: Real-time search using SerperDevTool targeting PubMed, Examine.com, NIH
7. RAG Ingredient Ranking: Vector database search for evidence-based ingredients from NIH ODS
8. Supplement Recommendation: Clinical reasoning to prioritize and filter ingredients (Gemini)
9. Focus Area Assignment: Maps each supplement to health focus area codes (Gemini reasoning)
10. Final Protocol Compilation: Web search for evidence-based dosages using SerperDevTool

**Post-Processing:**
11. Excel Report Generation: Structured clinical reports for healthcare professionals
 
 
WORKFLOW COORDINATION: 
The system uses CrewAI's task orchestration to ensure proper data flow between agents. Each agent receives structured input from previous agents and produces validated output for subsequent agents. The crew.py file manages this coordination, ensuring that: 
- Data validation occurs at each step using Pydantic models 
- Error handling prevents workflow interruption 
- Output files are properly generated and saved 
- Agent dependencies are respected 
- Parallel processing occurs where possible for efficiency 
 
 
This architecture ensures that complex medical decisions are made through a systematic, evidence-based approach while maintaining the flexibility to adapt to different patient profiles and health conditions. 
 
 
 
DATA FLOW:
Input Data → Biomarker Evaluation → Focus Area Scoring → User Profile Compilation → Patient Issues Extraction
→ Profile Summary (Gemini) → Web Discovery (Serper) → RAG Ranking → Supplement Recommendations (Gemini)
→ Focus Area Assignment (Gemini) → Dosage Compilation (Serper) → Excel Output
 
 
 
======================================================================== 
8. Code Explaination and summary 
======================================================================== 
 
BIOMARKER EVALUATION TOOL(biomarker_evaluation.py): 
- Evaluates lab results against reference ranges 
- Flags abnormal values (high/low) 
- Generates summary statistics 
Rule based(No LLM Call Required) 
 
 
FOCUS AREAS GENERATOR TOOL(focus_areas_generator.py): 
- Modular ruleset system for scoring health focus areas 
- Integrates multiple lifestyle and health factors 
- Provides weighted scores for 9 focus areas 
- Generates detailed breakdown logs 
-Rule based(No LLM Call Required) 
 
 
 
USER PROFILE COMPILER TOOL(user_profile_compiler.py): 
- Combines patient demographics with flagged biomarkers to create an overall patient profile 
- Validates data structure using Pydantic models 
- Creates unified user profile for downstream agents 
-Rule based(No LLM Call Required) 
 
 
 
INGREDIENT RANKER RAG TOOL(ingredient_ranker_rag.py): 
Knowledge Base & Data Source: 
The RAG system is built on a comprehensive dataset derived from the NIH Office of Dietary Supplements (ODS) Fact Sheets (https://ods.od.nih.gov/factsheets/list-all/), which provides authoritative, evidence-based information about dietary supplements. The ODS is part of the National Institutes of Health and serves as the federal government's primary source of scientific information on dietary supplements. 
 
 
Data Transformation Process: 
The raw NIH ODS data was restructured into a reverse-indexed format in transformed_ingredients.json for optimal retrieval. Each ingredient entry contains: 
- core_health_problems: Primary health conditions the ingredient addresses 
- secondary_health_problems: Secondary or related health issues 
- key_actions: Specific biological mechanisms and effects 
- relevant_conditions: Medical conditions where the ingredient is beneficial 
- biomarkers_mentioned: Specific biomarkers the ingredient affects 
- biomarker_recommendations: Clinical guidance for biomarker optimization 
- special_cases: Specific populations or situations where the ingredient is particularly relevant 
- cases_when_not_recommended: Contraindications and safety considerations 
- lifestyle_factors: Environmental or lifestyle factors that affect need 
- medicine_category: Classification (Functional, Ayurvedic, etc.) 
- chunk_text: Comprehensive summary for semantic search 
 
 
Vector Database Architecture: 
The transformed data is converted into a vector database stored in ingredients_vector_db/ using ChromaDB with the following structure: 
- Embeddings: Generated using ChromaDB's default embedding model for semantic similarity 
- Metadata: Structured information for filtering and boosting 
- Documents: Comprehensive text chunks combining all ingredient information 
- Collection: Named "ingredients" with 100+ supplement ingredients 
 
 
Hybrid Search Algorithm: 
The tool employs a sophisticated three-tier search approach: 
1. Semantic Search: Vector similarity using ChromaDB embeddings to find conceptually related ingredients 
2. BM25 Keyword Search: Traditional keyword matching for exact term relevance 
3. Biomarker Boosting: Additional scoring for ingredients that specifically mention the user's flagged biomarkers 
 
 
Search Query Generation: 
Creates comprehensive search queries from user profile including: 
- Demographics (age, sex, weight, height) 
- Flagged biomarkers (both high and low values) 
- Medical conditions and symptoms 
- Lifestyle factors (exercise, sleep, stress, smoking, alcohol) 
- Current medications and allergies 
 
 
Scoring and Ranking Logic: 
- Semantic Score: Cosine similarity between query and ingredient embeddings (0-1) 
- BM25 Score: Keyword relevance using TF-IDF weighting (0-1) 
- Biomarker Boost: Additional 0.1-0.3 points for ingredients mentioning flagged biomarkers 
- Final Score: Weighted combination with semantic (0.4) + BM25 (0.3) + biomarker boost (0.3) 
- Ranking: Top 15 ingredients sorted by final score 
 
 
WEB INGREDIENT DISCOVERY (SerperDevTool Integration):
This agent uses CrewAI's SerperDevTool for real-time web search to discover evidence-based supplements.

Scientific Source Targeting:
The agent specifically targets credible scientific sources using site-specific searches:
- PubMed: Peer-reviewed medical literature and clinical studies
- NIH Databases: Official government health information
- Examine.com: Evidence-based supplement research database

Search Execution via SerperDevTool:
Uses Google Serper API (via CrewAI SerperDevTool) to perform site-specific searches:
- "site:examine.com [issue] supplements" for evidence-based supplement data
- "site:pubmed.ncbi.nlm.nih.gov [issue] supplementation" for clinical research
- "site:nih.gov [supplement] recommended intake" for official guidelines

Discovery Process:
1. Receives extracted patient issues (biomarkers, conditions, symptoms)
2. Executes web searches for each health issue using SerperDevTool
3. Extracts ingredient names and maps them to patient reasons
4. Returns structured JSON with discovered_ingredients array

Output Structure (Pydantic Validated):
{
  "discovered_ingredients": [
    {"ingredient_name": "Vitamin D3", "reasons": ["low vitamin D"]},
    {"ingredient_name": "Omega-3", "reasons": ["high cholesterol"]}
  ]
}
 
 
SUPPLEMENT RECOMMENDER (Gemini Clinical Reasoning):
Medical Analysis Framework:
This agent uses Gemini 2.5 Flash for clinical reasoning, combining insights from RAG database and web discovery to create personalized recommendations.

Input Integration:
- Patient Summary: Concise natural language summary from Profile Summarizer agent
- RAG Ingredients: Evidence-based ingredients from NIH ODS database with relevance scores
- Web Ingredients: Discovered ingredients from SerperDevTool web searches
- Biomarker Analysis: Specific flagged biomarkers and their clinical significance

Clinical Decision Logic (Gemini Reasoning):
1. Biomarker Prioritization: Prioritizes ingredients that directly address flagged biomarkers
2. Condition Matching: Matches ingredients to specific medical conditions and symptoms
3. Redundancy Pruning: Removes supplements covered by multivitamin unless specific deficiency documented
4. Safety Evaluation: Considers contraindications, drug interactions, and special populations
5. Clinical Priority Ranking: Ranks ingredients by potential clinical impact for the specific patient

Output Generation (Pydantic Validated):
Creates ranked recommendations with:
- ingredient_name: Exact supplement name
- rank: Clinical priority ranking (1 = highest)
- why: Patient-specific reasoning (2-3 lines max)

FOCUS AREA SPECIALIST (Gemini Reasoning):
Maps each supplement to 1-2 health focus area codes based on mechanism of action.

Focus Area Codes:
- CM: Cardiometabolic & Metabolic Health
- COG: Cognitive & Mental Health
- DTX: Detoxification & Biotransformation
- IMM: Immune Function & Inflammation
- MITO: Mitochondrial & Energy Metabolism
- SKN: Skin & Barrier Function
- STR: Stress-Axis & Nervous System Resilience
- HRM: Hormonal Health
- GA: Gut Health and Assimilation
 
 
FINAL SUPPLEMENT COMPILER (SerperDevTool Dosage Research):
Protocol Development:
This agent uses SerperDevTool to search for evidence-based dosages from credible sources and transforms recommendations into complete clinical protocols.

Dosage Research via SerperDevTool:
For each supplement, the agent executes web searches:
- "site:examine.com [supplement] dosage recommendations"
- "site:pubmed.ncbi.nlm.nih.gov [supplement] clinical dosage"
- "site:nih.gov [supplement] recommended daily intake"

Form Specificity Rules (Applied During Compilation):
- Magnesium: Specifies salt form based on indication (glycinate for sleep, citrate for constipation, threonate for cognitive)
- Vitamin D3: Notes K2 pairing requirement for calcium metabolism
- Vitamin B12: Specifies methylcobalamin form
- Vitamin B6: Specifies P-5-P (pyridoxal-5-phosphate) form
- Curcumin: Notes standardized extract requirement for therapeutic effect
- Probiotics: Specifies strain and CFU count, notes empty stomach timing

Output Structure (Pydantic Validated):
{
  "supplement_recommendations": [
    {
      "ingredient_name": "Calcium",
      "recommended_dosage": "500-600 mg elemental Calcium",
      "frequency": "Twice daily (BID) with meals",
      "focus_area": ["CM", "STR"],
      "why": "Patient-specific reasoning..."
    }
  ]
}