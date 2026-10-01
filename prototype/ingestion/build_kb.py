"""Build the redesigned knowledge base.

Ingests Pizzorno condition chapters (+ optionally the 34 ODS seed entries) into a
NEW ChromaDB collection using COSINE space and natural-prose passages — fixing the
negative-similarity problem of the old metadata-blob index.

Usage:
    python -m prototype.ingestion.build_kb --limit-chapters 20            # slice
    python -m prototype.ingestion.build_kb --with-ods                     # + ODS seed
    python -m prototype.ingestion.build_kb --rebuild                      # full, fresh
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import chromadb  # noqa: E402

from prototype.ingestion.extract import iter_condition_passages  # noqa: E402

KB_PATH = os.environ.get("KB_DB_PATH", "kb_vector_db")
KB_COLLECTION = os.environ.get("KB_COLLECTION", "kb_passages")

# Lightweight lexicons for rule-based entity tagging (fast, deterministic).
INGREDIENTS = [
    "magnesium", "potassium", "calcium", "zinc", "iron", "selenium", "chromium",
    "copper", "iodine", "boron", "manganese", "molybdenum", "phosphorus",
    "vitamin a", "vitamin c", "vitamin d", "vitamin e", "vitamin k", "vitamin b6",
    "vitamin b12", "thiamin", "riboflavin", "niacin", "folate", "folic acid",
    "biotin", "pantothenic acid", "choline", "omega-3", "fish oil", "epa", "dha",
    "coenzyme q10", "coq10", "carnitine", "l-carnitine", "alpha-lipoic acid",
    "n-acetylcysteine", "nac", "glutathione", "berberine", "curcumin", "turmeric",
    "probiotics", "ashwagandha", "rhodiola", "valerian", "melatonin", "ginkgo",
    "garlic", "ginger", "green tea", "resveratrol", "quercetin", "milk thistle",
    "saw palmetto", "black cohosh", "st johns wort", "5-htp", "taurine", "creatine",
    "glucosamine", "chondroitin", "vitamin d3", "vitamin k2", "inositol", "betaine",
]
BIOMARKERS = [
    "hba1c", "hemoglobin a1c", "glucose", "insulin", "crp", "c-reactive protein",
    "homocysteine", "cholesterol", "ldl", "hdl", "triglyceride", "triglycerides",
    "apob", "apolipoprotein", "lipoprotein", "lp(a)", "tsh", "thyroid", "cortisol",
    "testosterone", "dhea", "ferritin", "vitamin d", "25-oh", "blood pressure",
    "egfr", "creatinine", "alt", "ast", "albumin", "bilirubin",
]


def _match(text_lower: str, lexicon) -> str:
    hits = []
    for term in lexicon:
        # word-ish boundary match
        if re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", text_lower):
            hits.append(term)
    return ", ".join(sorted(set(hits)))


def build(limit_chapters=None, with_ods=False, rebuild=False):
    client = chromadb.PersistentClient(path=KB_PATH)
    if rebuild:
        try:
            client.delete_collection(KB_COLLECTION)
            print(f"🗑  dropped existing collection {KB_COLLECTION!r}")
        except Exception:
            pass
    col = client.get_or_create_collection(
        KB_COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    docs, metas, ids = [], [], []
    n = 0
    for p in iter_condition_passages(limit_chapters=limit_chapters):
        text_l = p["passage"].lower()
        docs.append(p["passage"])
        metas.append({
            "source_type": "textbook",
            "source_id": "pizzorno_murray_2e",
            "condition": p["condition"],
            "chapter_num": p["chapter_num"],
            "page": p["page"],
            "mentioned_ingredients": _match(text_l, INGREDIENTS),
            "mentioned_biomarkers": _match(text_l, BIOMARKERS),
        })
        ids.append(f"pz_ch{p['chapter_num']}_{p['chunk_idx']}")
        n += 1
        if len(docs) >= 100:                 # batch insert
            col.add(documents=docs, metadatas=metas, ids=ids)
            docs, metas, ids = [], [], []
            print(f"  …indexed {n} passages")
    if docs:
        col.add(documents=docs, metadatas=metas, ids=ids)
    print(f"✅ Textbook: indexed {n} passages")

    if with_ods:
        m = _ingest_ods(col)
        print(f"✅ ODS seed: indexed {m} entries")

    print(f"📦 Collection {KB_COLLECTION!r} now holds {col.count()} passages at {KB_PATH}")


def _ingest_ods(col):
    """Re-ingest the 34-entry ODS seed into the new (cosine) collection."""
    try:
        old = chromadb.PersistentClient(path="ingredients_vector_db").get_collection("ingredients")
    except Exception as e:
        print(f"  (skipping ODS — {e})")
        return 0
    data = old.get(include=["documents", "metadatas"])
    docs, metas, ids = [], [], []
    for i, (doc, meta) in enumerate(zip(data["documents"], data["metadatas"])):
        meta = meta or {}
        docs.append(doc)
        metas.append({
            "source_type": "ods",
            "source_id": "nih_ods_factsheets",
            "condition": meta.get("core_health_problems", ""),
            "ingredient_name": meta.get("ingredient_name", ""),
            "mentioned_ingredients": (meta.get("ingredient_name", "") or "").lower(),
            "mentioned_biomarkers": (meta.get("biomarkers_mentioned", "") or "").lower(),
        })
        ids.append(f"ods_{i}")
    if docs:
        col.add(documents=docs, metadatas=metas, ids=ids)
    return len(docs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-chapters", type=int, default=None)
    ap.add_argument("--with-ods", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()
    build(limit_chapters=args.limit_chapters, with_ods=args.with_ods, rebuild=args.rebuild)
