# Wellness Supplement Agent — Architecture Redesign

> Status: design in progress. This document captures the agreed direction, the
> open decisions, and the recommended choices. It supersedes the disease-first
> / MedGemma / Serper pipeline for the purposes of the new agentic design.

---

## 1. Vision & Principles

We are building a **wellness and longevity supplement agent**, *not* a doctor.

- It reads a user's data, understands their **stated health goals**, and recommends
  supplements that support those goals.
- Diseases, medications, and allergies are a **safety overlay** — they constrain and
  flavour recommendations, they never drive them.
- Language is **structure/function** ("supports healthy glucose metabolism"), never
  disease claims ("treats diabetes"). This is both product identity and a regulatory
  line (US DSHEA).

**The single most important design goal: agent autonomy.** The agent decides what to
look for, which tools to call, how to phrase its queries, and when it has enough
evidence. We do not hardcode retrieval order, result counts, or candidate lists.

---

## 2. The Three Signals

Every recommendation reasons over three structured signals we already collect:

| Signal | Source | Nature |
|---|---|---|
| **Stated goals** (free text) | Phase 2 (goals question moved here) | Open-ended, user's own words |
| **Focus area scores** (9 domains) | Preprocessing (rule-based) | Quantified biological need + *reasons* |
| **Biomarkers + lifestyle** | Phase 1 + Phase 2 intake + lab panel | Specific triggers & contraindications |

The **focus area scores are the bridge** between vague user language and structured
knowledge: they tell the agent *where the biology is asking for support*, and their
*reason breakdown* (which rules fired and why) is itself a retrieval signal.

The 9 focus areas: CM (cardiometabolic), STR (stress/nervous system), HRM (hormonal),
IMM (immune/inflammation), SKN (skin/barrier), COG (cognitive/mental), MITO
(mitochondrial/energy), DTX (detox), GA (gut/assimilation).

---

## 3. Pipeline

```
PREPROCESSING (rule-based, no LLM — unchanged)
  ├─ Biomarker evaluation        → flagged biomarkers (direction + severity)
  ├─ Focus area scoring          → 9 scores + REASON BREAKDOWN
  └─ User profile compilation    → canonical UserProfile
       ↓
PROFILE SUMMARIZER + GOAL INTERPRETER  (merged — first AI agent)
  Inputs: stated goals (Phase 2), focus area scores + reasons, flagged biomarkers,
          demographics, current meds/supplements/diagnoses
  Output: a goal-aware patient summary + a structured "signal vector"
          (which focus areas to prioritise, which biomarker triggers, lifestyle factors)
       ↓
KNOWLEDGE REPO CREATOR AGENT  (autonomous retrieval engine)
  Composes its own searches over the KB + PubMed.
  Decides what to query, when to refine, when it has enough.
  Output: enriched candidate evidence (passages + citations + provenance)
       ↓
SAFETY SCREEN  (agent calls safety tools per candidate)
  Drug–nutrient interactions, condition contraindications, allergy/form exclusions,
  duplication with current stack.
       ↓
SUPPLEMENT RECOMMENDER
  Ranks by: goal alignment → focus-area need → biomarker trigger → evidence strength.
  Produces wellness-framed rationale tied to the user's actual goals.
       ↓
FOCUS AREA ASSIGNMENT  →  FINAL PROTOCOL COMPILER (dose/form/timing)  →  output
```

---

## 4. Knowledge Base Design

**The KB is a searchable corpus of verbatim source passages — NOT normalized records.**

We do not pre-slice sources into `primary_supplements[]` / `goal_themes[]` / etc. That
forces the agent to consume *our* interpretation. Instead we store the raw text and let
the agent read and reason.

### Storage unit: a passage

```jsonc
{
  "passage_id": "lpi_omega3_overview_p3",
  "text": "<verbatim passage, ~300–800 tokens>",
  "embedding": [...],
  "metadata": {
    "source_type": "lpi",                 // ods | lpi | examine | textbook | curated
    "source_id": "lpi_omega3_fatty_acids",
    "source_title": "Essential Fatty Acids",
    "source_url": "https://lpi.oregonstate.edu/...",
    "section_path": "Disease Prevention > Cardiovascular",
    "mentioned_ingredients": ["EPA", "DHA"],   // soft hints, not constraints
    "mentioned_biomarkers": ["triglycerides", "hs-CRP"],
    "mentioned_focus_areas": ["CM", "COG"],
    "passage_kind": ["mechanism", "evidence"]  // dosing|mechanism|evidence|safety|adequacy|interaction
  }
}
```

Metadata exists only to let the agent **narrow** a search when it wants — it never
dictates what answers exist. The agent can also ignore metadata and search semantically.

### RECOMMENDED SIMPLIFICATION (opinionated)

Earlier we sketched 5 separate ChromaDB collections. **At v1 scale (tens of conditions,
a few hundred–thousand passages) that is premature.** Use **one collection** with good
metadata and filter by `passage_kind` / `source_type` at query time. One collection is
simpler to build, reindex, and reason about, and ChromaDB filtering is more than fast
enough at this scale. Shard later only if a real performance need appears.

### Sources (v1 → later)

| Source | Role | Priority |
|---|---|---|
| Existing 34-ingredient ChromaDB (ODS-derived) | **Seed data** | v1 |
| NIH ODS fact sheets (expanded) | Foundation — nutrient adequacy, dosing, interactions | v1 |
| Linus Pauling Institute (Micronutrient Info Center) | Wellness-framed mechanism prose | v1 |
| Examine.com outcome pages | Goal-organised evidence summaries | v1 |
| Pizzorno textbook | **Mechanism reference only**, selective | v1, demoted |
| PubMed (live, via tool) | Runtime citation + gap-filling | v1 |
| Cochrane / Semantic Scholar / Natural Medicines | Evidence depth + interactions | v2 |

---

## 5. Agent Tool Surface

**Autonomy comes from a small set of composable, well-described tools — not from many
tools.** Too many tools reduces reliability. Recommended tight set:

```python
search_kb(query, filters=None, top_k=10)
    # hybrid semantic + keyword search over the passage corpus
    # filters: source_type, focus_areas, mentioned_ingredients, passage_kind
    # returns ranked passages with full text + provenance

get_patient_context(aspect)
    # aspect: "signals" | "focus_area:<CODE>" | "goals"
    # returns flagged biomarkers / focus-area score + REASON breakdown / parsed goals

pubmed_search(query, max_results=10, years_back=None, publication_types=None)
    # agentic literature search (see §6); returns title/year/journal/abstract/PMID/DOI

check_safety(supplement)
    # full per-patient safety battery: drug–nutrient interactions, condition
    # contraindications, allergy/form exclusions, duplication with current stack
```

The agent chooses which to call, in what order, what to query, and when to stop. No
hardcoded "always KB then PubMed", no "top-N candidates per focus area."

---

## 6. PubMed Query Tool — Setup & Usage Guide

### What it's for
Two agent-driven purposes (no hardcoded trigger):
1. **Citation enrichment** — back a KB-derived claim with peer-reviewed references.
2. **Gap-filling** — read primary literature when the KB is thin on a topic.

### Recommended implementation: NCBI E-utilities via BioPython (free)

**Step 1 — Get a free NCBI API key**
- Create an NCBI account → Account Settings → "API Key Management" → generate key.
- Raises rate limit from 3 req/s to 10 req/s. Store in env: `NCBI_API_KEY`.

**Step 2 — Install**
```bash
pip install biopython
```

**Step 3 — Tool skeleton**
```python
from Bio import Entrez
import os

Entrez.email = os.environ["NCBI_EMAIL"]        # required by NCBI
Entrez.api_key = os.environ.get("NCBI_API_KEY")  # optional, raises rate limit

def pubmed_search(query, max_results=10, years_back=None, publication_types=None):
    term = query
    if publication_types:
        # e.g. ["Meta-Analysis","Randomized Controlled Trial","Systematic Review"]
        pt = " OR ".join(f'"{p}"[Publication Type]' for p in publication_types)
        term = f"({term}) AND ({pt})"
    if years_back:
        term = f"({term}) AND (\"{2026 - years_back}\"[PDAT] : \"3000\"[PDAT])"
    term = f"({term}) AND humans[MeSH]"

    ids = Entrez.read(Entrez.esearch(db="pubmed", term=term, retmax=max_results))["IdList"]
    if not ids:
        return []
    recs = Entrez.read(Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="xml"))
    out = []
    for art in recs["PubmedArticle"]:
        cit = art["MedlineCitation"]
        a = cit["Article"]
        out.append({
            "pmid": str(cit["PMID"]),
            "title": str(a.get("ArticleTitle", "")),
            "journal": str(a["Journal"]["Title"]),
            "year": a["Journal"]["JournalIssue"].get("PubDate", {}).get("Year"),
            "abstract": " ".join(str(t) for t in a.get("Abstract", {}).get("AbstractText", [])),
        })
    return out
```

**Step 4 — Expose to the agent (CrewAI tool)**
```python
from crewai.tools import BaseTool

class PubMedSearchTool(BaseTool):
    name = "pubmed_search"
    description = (
        "Search peer-reviewed literature on PubMed. Use to attach citations to a "
        "recommendation or to read primary research when the knowledge base is thin. "
        "Write focused queries; prefer MeSH terms; filter to recent reviews/RCTs when "
        "you need strong evidence."
    )
    def _run(self, query, max_results=10, years_back=None, publication_types=None):
        return pubmed_search(query, max_results, years_back, publication_types)
```

### Query construction note
PubMed is not natural-language. Good queries use MeSH + filters, e.g.:
```
("Magnesium"[MeSH] OR "magnesium glycinate") AND ("Sleep"[MeSH]) AND humans[MeSH]
  AND ("2018"[PDAT] : "3000"[PDAT])
```
Start by teaching the agent this syntax via few-shot examples in its system prompt
(Claude/Gemini handle it well). Add helper wrappers only if the agent writes poor queries.

### Rate limits & robustness
- 3 req/s without key, 10 req/s with key. Add retry + backoff.
- E-utilities occasionally errors — add **Europe PMC** REST API as a fallback (same
  content, no auth for low volume, often more full-text snippets).

### Note on the senior's design doc
It references "the **PubChem** dataset … indexed into `pubmed_query_vector_db/`."
PubChem is the **chemical-compound** database; the **literature** DB is **PubMed**.
This is almost certainly a typo — confirm with the senior which is intended. A local
bulk PubMed vector index is real but unnecessary for v1; the live API is fast enough.

---

## 7. Safety Overlay

Safety is delivered as **tools the agent calls on demand**, not a static pre-filter.
`check_safety(supplement)` runs the full battery for the specific patient. Backing data
for v1: a curated subset covering the ~30 most common medications and ~20 most common
chronic conditions (≈80% of real cases). Source candidates: DrugBank (free tier) for
drug–nutrient interactions; expand with Natural Medicines later.

---

## 8. Build vs Buy — the Managed-Retrieval Decision

**Recommendation: keep ChromaDB (self-hosted). Do not adopt a managed retrieval
service for v1.** The retrieval *mechanism* is not where this project's difficulty or
value lives. The hard parts are: (1) curating trustworthy wellness sources, (2) the
agent's reasoning & tool orchestration, (3) the safety overlay, (4) wellness
framing/compliance. A managed retrieval service helps with none of these.

### Specific evaluation: Moss (moss.dev)

Moss is a real-time semantic search runtime for AI agents (Rust/WASM, sub-10ms local
lookups, hybrid vector+BM25 search with configurable alpha, metadata filtering,
bring-your-own-embeddings). Proprietary/paid: $5/mo free credits → $30 → $200 →
enterprise. Python/JS SDKs + REST API.

- **Autonomy:** NOT a concern. Moss exposes raw search primitives (you write the query,
  set alpha, filter metadata, get passages). It does not insert a reranker/query-rewrite
  black box. On the autonomy axis it is fine — unlike heavier RAG platforms.
- **Why it's still wrong for v1:**
  1. Moss's reason to exist is **latency** (sub-10ms for agents doing dozens of lookups
     in real-time/voice/browser loops). Our pipeline is server-side multi-stage LLM
     reasoning where a single run takes *seconds* of LLM time; shaving 100ms per KB
     lookup is invisible. Wrong environment for what Moss optimises.
  2. Recurring cost + vendor lock at the core data layer, for features ChromaDB already
     provides free and self-hosted (hybrid search, metadata filter, BYOE).
  3. PHI/data-residency: a third-party managed data service adds a compliance surface
     that self-hosted ChromaDB avoids.
  4. "Simplification" is marginal-to-negative: the `search_kb` wrapper is ~100 lines
     against either backend; Moss adds credentials/billing/dependency in return.
- **When to revisit:** if we ship a consumer app where the agent runs in-browser /
  on-device and the KB must travel to the edge with instant offline search — that is
  Moss's genuine sweet spot. Not v1.

---

## 9. Open Decisions / Questions for Senior

1. **"PubChem vs PubMed"** in the design doc — which is intended? (Almost certainly PubMed.)
2. **Managed retrieval (MOSS/Morphik/etc.) vs build-on-ChromaDB** — confirm we stay lean.
3. **Safety data source & scope** — DrugBank subset acceptable for v1? How many meds/conditions?
4. **Ingestion: chunking strategy** — section-aware chunks (recommended) vs sliding window.
5. **Entity tagging at ingestion** — LLM-tagged (richer, slower) vs rule-based (faster). Recommend LLM-tagged given small corpus.
6. **Tool-call budget per recommendation** — cap to bound cost/latency (recommend ~12–15).
7. **Determinism expectations** — agentic = less deterministic. Agree on golden-case regression testing rather than exact-output tests.
8. **Examine.com licensing** — do we have rights to ingest their content into our KB?

---

## 10. Phased Build Plan (proposed)

- **Phase A — KB foundation:** ingestion pipeline → ChromaDB (seed + ODS + LPI), one
  collection, LLM entity tagging, `search_kb` tool.
- **Phase B — PubMed tool:** E-utilities wrapper + Europe PMC fallback.
- **Phase C — Agent:** merged Profile Summarizer/Goal Interpreter + Knowledge Repo
  Creator with the 4-tool surface; few-shot prompt for query syntax.
- **Phase D — Safety:** `check_safety` + curated interaction data.
- **Phase E — Recommender + compiler:** ranking + wellness-framed output + Excel.
- **Phase F — Eval:** golden patient cases, coverage + framing-compliance checks.
