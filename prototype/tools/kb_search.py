"""search_kb — hybrid-ish search over the existing ingredients ChromaDB.

For the prototype we reuse the seed vector store at ./ingredients_vector_db
(collection "ingredients"). The collection has a built-in embedding function,
so we can query with `query_texts` directly (same pattern as the existing
ingredient_ranker_rag tool).
"""
import os
from typing import Any, Dict, List, Optional, Type

import chromadb
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

DB_PATH = os.environ.get("KB_DB_PATH", "ingredients_vector_db")
COLLECTION = os.environ.get("KB_COLLECTION", "ingredients")


class SearchKBInput(BaseModel):
    query: str = Field(..., description="Free-text search query. Describe the goal, "
                                        "biomarker, mechanism, or ingredient you want "
                                        "evidence about.")
    top_k: int = Field(8, description="How many passages to return (1-20).")
    medicine_category: Optional[str] = Field(
        None,
        description="Optional metadata filter, e.g. 'Functional', 'Conventional'. "
                    "Omit to search everything."
    )


def _connect():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_collection(COLLECTION)


class SearchKBTool(BaseTool):
    name: str = "search_kb"
    description: str = (
        "Search the internal supplement knowledge base for passages relevant to a "
        "query. Returns ingredient passages with their text and metadata "
        "(core_health_problems, biomarkers_mentioned, cases_when_not_recommended). "
        "Write your own queries; call repeatedly with refined queries until you have "
        "enough evidence. This is your PRIMARY source of candidate ingredients."
    )
    args_schema: Type[BaseModel] = SearchKBInput

    def _run(self, query: str, top_k: int = 8,
             medicine_category: Optional[str] = None) -> str:
        import sys
        print(f"🔧 KB_SEARCH CALLED: query={query!r} top_k={top_k}", file=sys.stderr)
        top_k = max(1, min(int(top_k), 20))
        try:
            collection = _connect()
        except Exception as e:  # pragma: no cover - environment dependent
            return f"ERROR connecting to knowledge base: {e}"

        where = {"medicine_category": medicine_category} if medicine_category else None
        try:
            res = collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:  # pragma: no cover
            return f"ERROR querying knowledge base: {e}"

        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        if not docs:
            return f"No knowledge-base passages found for query: {query!r}"

        out: List[Dict[str, Any]] = []
        for doc, meta, dist in zip(docs, metas, dists):
            meta = meta or {}
            out.append({
                "ingredient_name": meta.get("ingredient_name", "?"),
                "similarity": round(1 - float(dist), 3),
                "medicine_category": meta.get("medicine_category"),
                "core_health_problems": meta.get("core_health_problems"),
                "biomarkers_mentioned": meta.get("biomarkers_mentioned"),
                "cases_when_not_recommended": meta.get("cases_when_not_recommended"),
                "special_cases": meta.get("special_cases"),
                "text": (doc or "")[:1200],
                "source": "internal_kb (ODS-derived)",
            })

        lines = [f"Found {len(out)} passages for query {query!r}:\n"]
        for i, r in enumerate(out, 1):
            lines.append(
                f"[{i}] {r['ingredient_name']} (sim={r['similarity']}, "
                f"cat={r['medicine_category']})\n"
                f"    core_health_problems: {r['core_health_problems']}\n"
                f"    biomarkers_mentioned: {r['biomarkers_mentioned']}\n"
                f"    not_recommended_when: {r['cases_when_not_recommended']}\n"
                f"    text: {r['text']}\n"
            )
        return "\n".join(lines)
