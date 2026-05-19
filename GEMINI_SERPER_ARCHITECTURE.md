# Gemini + Serper + RAG Architecture

## Overview

This document describes the **Gemini-Only Mode** architecture that uses Google's Gemini 2.5 Flash LLM with Serper (Google Search API) and RAG (Retrieval-Augmented Generation) for supplement ingredient discovery and recommendations.

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              SYSTEM ARCHITECTURE                                          │
│                          Gemini + Serper + RAG Pipeline                                   │
└──────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │   Patient Data  │
                                    │   (JSON Input)  │
                                    └────────┬────────┘
                                             │
                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: PREPROCESSING (Python Functions)                         │
│                                                                                           │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐              │
│  │  Biomarker   │──▶│ User Profile │──▶│  Focus Area  │──▶│   Patient    │              │
│  │  Evaluation  │   │ Compilation  │   │  Evaluation  │   │   Issues     │              │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘              │
│                                                                                           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 2: CREWAI AGENT PIPELINE (Sequential)                       │
│                                                                                           │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ AGENT 1: Profile Summarizer                                                        │  │
│  │ ├─ LLM: Gemini 2.5 Flash                                                           │  │
│  │ └─ Output: Natural language patient summary (100-150 words)                        │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                             │                                             │
│                                             ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ AGENT 2: Web Ingredient Discovery (Serper)                                         │  │
│  │ ├─ Tool: SerperDevTool (Google Search API)                                         │  │
│  │ ├─ LLM: Gemini 2.5 Flash (extraction)                                              │  │
│  │ ├─ Sources: PubMed, Examine.com, NIH/NCCIH                                         │  │
│  │ └─ Output: 10-15 web-discovered ingredients                                        │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                             │                                             │
│                                             ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ AGENT 3: RAG Ingredient Ranker                                                     │  │
│  │ ├─ Tool: IngredientRankerRAGTool                                                   │  │
│  │ ├─ DB: ChromaDB Vector Store                                                       │  │
│  │ ├─ Search: Hybrid (Semantic 40% + BM25 30% + Biomarker Boost 30%)                  │  │
│  │ └─ Output: 15 ranked ingredients from curated database                            │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                             │                                             │
│                                             ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ AGENT 4: Supplement Recommender (Clinical Reasoning)                               │  │
│  │ ├─ LLM: Gemini 2.5 Flash                                                           │  │
│  │ ├─ Input: Patient summary + Web ingredients + RAG ingredients                      │  │
│  │ └─ Output: 8-12 ranked recommendations with clinical justification                 │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                             │                                             │
│                                             ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ AGENT 5: Focus Area Mapper                                                         │  │
│  │ ├─ LLM: Gemini 2.5 Flash                                                           │  │
│  │ ├─ Input: Recommendations + Focus area scores                                      │  │
│  │ └─ Output: Supplements mapped to focus area codes (CM, COG, DTX, IMM, etc.)        │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                             │                                             │
│                                             ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ AGENT 6: Dosage & Protocol Compiler                                                │  │
│  │ ├─ Tool: SerperDevTool (dosage research)                                           │  │
│  │ ├─ LLM: Gemini 2.5 Flash                                                           │  │
│  │ └─ Output: Complete protocol with dosages, frequency, timing                       │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
                                ┌─────────────────────┐
                                │   Final Protocol    │
                                │   (JSON Output)     │
                                └─────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SERVICES                                            │
│                                                                                           │
│  ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐            │
│  │   Google Vertex AI  │   │    Serper API       │   │   ChromaDB          │            │
│  │   (Gemini 2.5)      │   │    (Web Search)     │   │   (Vector Store)    │            │
│  └─────────────────────┘   └─────────────────────┘   └─────────────────────┘            │
│                                                                                           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Pipeline Flow Summary

```
Patient Data
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ PREPROCESSING: Biomarker → Profile → Focus Areas → Issues      │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 1: Summarizer ──▶ Patient Summary (text)                  │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 2: Web Discovery (Serper) ──▶ Web Ingredients             │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 3: RAG Ranker (ChromaDB) ──▶ RAG Ingredients              │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 4: Recommender ──▶ Ranked Supplements + Reasoning         │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 5: Focus Area Mapper ──▶ Focus Area Assignments           │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 6: Dosage Compiler (Serper) ──▶ Final Protocol (JSON)     │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. LLM Configuration

```python
from crewai import LLM

llm = LLM(
    model="vertex_ai/gemini-2.5-flash",
    temperature=0,
    seed=42
)
```

### 2. Serper Integration (Web Search)

The `GoogleSerperAPIWrapper` from LangChain is used for searching credible scientific sources.

**Environment Variable Required:**
```
SERPER_API_KEY=your_serper_api_key
```

**Search Sources:**
- PubMed (site:pubmed.ncbi.nlm.nih.gov)
- Examine.com (site:examine.com)
- NIH/NCCIH (site:nccih.nih.gov)

### 3. Agent Architecture (Sequential Pipeline)

| # | Agent | Tool | LLM | Output |
|---|-------|------|-----|--------|
| 1 | Profile Summarizer | None | Gemini 2.5 Flash | Patient summary (100-150 words) |
| 2 | Web Ingredient Discovery | SerperDevTool | Gemini 2.5 Flash | 10-15 web-discovered ingredients |
| 3 | RAG Ingredient Ranker | IngredientRankerRAGTool | Gemini 2.5 Flash | 15 ranked ingredients from database |
| 4 | Supplement Recommender | None | Gemini 2.5 Flash | 8-12 ranked recommendations |
| 5 | Focus Area Mapper | None | Gemini 2.5 Flash | Focus area code assignments |
| 6 | Dosage & Protocol Compiler | SerperDevTool | Gemini 2.5 Flash | Final protocol with dosages |

### 4. RAG Agent Details

The RAG (Retrieval-Augmented Generation) agent uses a **hybrid search** approach:

```python
# Hybrid Search Scoring Formula
final_score = (semantic_score * 0.4) + (bm25_score * 0.3) + (biomarker_boost * 0.3)
```

**Components:**
- **ChromaDB Vector Store**: Pre-indexed ingredient database with embeddings
- **Semantic Search**: Vector similarity using embeddings
- **BM25 Search**: TF-IDF keyword matching with bigrams
- **Biomarker Boosting**: 15% boost per flagged biomarker mention

```python
from chromadb import PersistentClient

# Connect to vector database
client = PersistentClient(path="./ingredients_vector_db")
collection = client.get_collection("ingredients")

# Perform semantic search
results = collection.query(
    query_texts=[search_query],
    n_results=50,
    include=["documents", "metadatas", "distances"]
)
```

## Data Flow (Sequential)

### Step 1: Preprocessing (Python Functions)
```
Patient Data → Biomarker Evaluation → User Profile → Focus Areas → Patient Issues
```

### Step 2: Profile Summarizer (Agent 1)
Creates concise natural language summary of patient profile for downstream agents.

### Step 3: Web Ingredient Discovery (Agent 2)
```python
# Serper searches scientific sources
queries = [
    f"site:pubmed.ncbi.nlm.nih.gov {biomarker_status} {biomarker_name} supplements",
    f"site:examine.com {condition} natural nutrients herbs",
    f"site:nccih.nih.gov {condition} dietary supplements"
]
search_wrapper = GoogleSerperAPIWrapper()
results = search_wrapper.run(query)
# Gemini extracts ingredients from results
web_ingredients = llm.call(extraction_prompt)
```

### Step 4: RAG Ingredient Ranker (Agent 3)
```python
# Hybrid search on ChromaDB
semantic_results = collection.query(query_texts=[search_query], n_results=50)
bm25_results = tfidf_cosine_search(search_query, documents)
rag_ingredients = hybrid_rank(semantic_results, bm25_results, flagged_biomarkers)
```

### Step 5: Supplement Recommender (Agent 4)
Analyzes patient summary + web ingredients + RAG ingredients using clinical reasoning.

### Step 6: Focus Area Mapper (Agent 5)
Maps each supplement to focus area codes (CM, COG, DTX, IMM, MITO, SKN, STR, HRM, GA).

### Step 7: Dosage & Protocol Compiler (Agent 6)
Uses Serper to research evidence-based dosages, then compiles final protocol with dosages, frequencies, and timing.

## Key Files

| File | Purpose |
|------|---------|
| `src/aether_2/crew.py` | CrewAI agent/task definitions |
| `src/aether_2/tools/web_ingredient_discovery.py` | Serper search + Gemini extraction |
| `src/aether_2/tools/ingredient_ranker_rag.py` | RAG hybrid search (ChromaDB + BM25) |
| `src/aether_2/tools/supplement_recommender.py` | Final recommendation logic |
| `src/aether_2/pipeline.py` | Main execution pipeline |
| `src/aether_2/config/agents.yaml` | Agent role definitions |
| `src/aether_2/config/tasks.yaml` | Task descriptions |
| `ingredients_vector_db/` | ChromaDB vector database |

## Environment Variables

```bash
# Google Cloud / Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id

# Serper API
SERPER_API_KEY=your_serper_api_key
```

## Enabling Gemini + Serper + RAG Mode

In `src/aether_2/crew.py`, uncomment SerperDevTool and IngredientRankerRAGTool:

```python
from crewai_tools import SerperDevTool
from src.aether_2.tools.ingredient_ranker_rag import IngredientRankerRAGTool

@agent
def web_ingredient_discovery(self) -> Agent:
    return Agent(
        config=self.agents_config['web_ingredient_discovery'],
        tools=[SerperDevTool()],
        llm=llm
    )

@agent
def ingredient_ranker_rag(self) -> Agent:
    return Agent(
        config=self.agents_config['ingredient_ranker_rag'],
        tools=[IngredientRankerRAGTool(kickoff_inputs=self.kickoff_inputs)],
        llm=llm
    )
```

## Advantages

- **Dual-source discovery**: Combines real-time web search with curated database
- **Hybrid RAG scoring**: Semantic + BM25 + biomarker boosting for relevance
- **Real-time data**: Serper searches current scientific literature
- **Cost-effective**: Gemini 2.5 Flash is cheaper than specialized medical models
- **Transparent**: Search results are traceable to source URLs

## Limitations

- Depends on search result quality for web discovery
- RAG quality depends on vector database maintenance
- Requires Serper API quota management

