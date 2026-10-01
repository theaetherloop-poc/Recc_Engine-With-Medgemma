# Agentic Knowledge-Repo Prototype

A "walking skeleton" of the redesign in [../ARCHITECTURE_REDESIGN.md](../ARCHITECTURE_REDESIGN.md).
Proves the **autonomous agent loop**: one CrewAI agent that decides for itself what to
search and produces wellness-framed supplement candidates grounded in the KB + PubMed.

This is isolated from the production pipeline — it imports the existing preprocessing
read-only and touches no `src/` code.

## What it does

```
load patient JSON
  → existing rule-based preprocessing (biomarkers + focus-area scoring)
  → populate shared context (goals, signals, focus-area scores + reasons)
  → autonomous agent with 4 tools:
        get_patient_context   (goals / signals / focus areas + WHY)
        search_kb             (existing 34-entry ChromaDB seed)
        pubmed_search         (NCBI E-utilities via BioPython)
        check_safety          (minimal curated interaction set)
  → Enriched Knowledge Package (JSON) → prototype_out/
```

The agent chooses its own tool sequence. Nothing is hardcoded.

## Setup

```bash
pip install biopython          # PubMed tool dependency

# Vertex AI (reuses the existing project; refresh credentials if expired):
gcloud auth application-default login

# PubMed (NCBI):
export NCBI_EMAIL="you@example.com"     # required by NCBI
export NCBI_API_KEY="..."               # optional, raises rate limit 3 -> 10 req/s
```

## Run

```bash
python -m prototype.run inputs/test_user3.json \
    --goal "live longer and healthier, reduce inflammation, steady energy"
```

`--goal` is optional. The goals question is moving to Phase 2; until then most input
files have no goals and the agent infers them from the biological signals.

Output is printed (with the full tool-call trace, since `verbose=True`) and saved to
`prototype_out/<patient>_enriched.json`.

## Scope (deliberately limited)

In: the agentic retrieval loop, the 4 tools, real preprocessing, structured output.
Out: source ingestion (ODS/LPI/Examine), the downstream Recommender → Compiler stages,
production safety data, Excel output.

## Known issue surfaced

`src/aether_2/utils/preprocessing.py::evaluate_focus_areas` returns all-zero scores
because it parses `(CODE):` but the markdown emits `(CODE)**:`. The prototype re-parses
the markdown correctly (`prototype/run.py::parse_focus_scores`). The production bug
should be fixed separately.
