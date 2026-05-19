"""
Apify Examine.com Supplement Research Scraper - Connection Test & Usage Guide
Actor: hanamira/examine-com-supplement-research

Run: .venv/bin/python test_apify_examine.py

Requires: APIFY_API_TOKEN in .env

IMPORTANT - Actual data structure (differs from actor docs):
  Dataset items are WRAPPED objects, not flat supplement records.
  Each item has: {searchType, query, resultCount, results: [...]}
  The actual supplement/condition data is in item["results"].

Available modes:
  1. Direct URLs  → Full supplement data (MOST RELIABLE)
  2. searchType=conditions → List of recommended supplement URLs for a condition
  3. searchType=supplements → Unreliable, often lands on general page

Actual fields returned for supplements (direct URL):
  name, url, summary, dosage (long text), safety, researchSummaries,
  citationCount, categories, scrapedAt, source

Fields NOT actually returned (listed in docs but missing):
  effectMatrix, benefits, sideEffects, drugInteractions, dosageRange

Best usage pattern for this project:
  Step 1: conditions search → get supplement URLs for patient's conditions/biomarkers
  Step 2: direct URL scrape → get full structured data for those supplements
"""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = Path("test_outputs/apify_examine")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RUN_TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
if not APIFY_API_TOKEN:
    raise EnvironmentError(
        "APIFY_API_TOKEN not found. Add it to your .env file.\n"
        "Get your token at: https://console.apify.com/account/integrations"
    )

try:
    from apify_client import ApifyClient
except ImportError:
    raise ImportError("apify-client not installed. Run: .venv/bin/uv pip install apify-client")

ACTOR_ID = "hanamira/examine-com-supplement-research"
client = ApifyClient(APIFY_API_TOKEN)


def run_actor(run_input: dict, label: str) -> list:
    """Run the actor, save raw dataset items to disk, and return them."""
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"Input: {json.dumps(run_input, indent=2)}")
    print("Running... (~15-30s)")
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"Status: {run['status']} | Apify dataset: {run['defaultDatasetId']} | Items: {len(items)}")

    # Save raw output
    safe_label = label.lower().replace(" ", "_").replace("-", "_").replace(":", "")[:50]
    out_file = OUTPUT_DIR / f"{RUN_TIMESTAMP}_{safe_label}.json"
    with open(out_file, "w") as f:
        json.dump({"label": label, "input": run_input, "apify_dataset_id": run["defaultDatasetId"], "items": items}, f, indent=2)
    print(f"Saved → {out_file}")
    return items


def extract_results(items: list) -> list:
    """
    Extract actual records from the wrapped dataset items.
    Each dataset item has a 'results' list — this flattens them all.
    """
    records = []
    for item in items:
        results = item.get("results", [])
        for r in results:
            # Filter out generic/homepage entries
            if r.get("name") not in ("Supplements", "Health Conditions and Goals"):
                records.append(r)
    return records


def print_supplement(r: dict):
    print(f"  [{r.get('type', '?')}] {r.get('name', 'N/A')}")
    print(f"    URL: {r.get('url', 'N/A')}")
    if r.get("summary"):
        print(f"    Summary: {r['summary'][:120]}...")
    if r.get("dosage"):
        print(f"    Dosage: {r['dosage'][:100]}...")
    if r.get("citationCount"):
        print(f"    Citations: {r['citationCount']}")
    if r.get("categories"):
        print(f"    Categories: {r['categories'][:5]}")
    if r.get("researchSummaries"):
        print(f"    Research snippets: {len(r['researchSummaries'])}")
    # Condition-specific fields
    if r.get("recommendedSupplements"):
        supps = [s["name"] for s in r["recommendedSupplements"] if s["name"] != "Supplements"]
        print(f"    Recommended supplements: {supps[:8]}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1: Direct URL (RECOMMENDED MODE - most reliable)
# Best for: enriching already-discovered supplement names with full data
# ─────────────────────────────────────────────────────────────────────────────
items1 = run_actor(
    run_input={"supplementUrls": ["https://examine.com/supplements/magnesium/"]},
    label="Direct URL - Magnesium"
)
records1 = extract_results(items1)
print(f"\nExtracted {len(records1)} records:")
for r in records1:
    print_supplement(r)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2: Condition search → get supplement URLs
# Best for: patient has a diagnosis/condition → find relevant supplements
# Then use the returned URLs for direct scraping (Test 3 pattern)
# ─────────────────────────────────────────────────────────────────────────────
items2 = run_actor(
    run_input={"query": "anxiety", "searchType": "conditions", "maxResults": 3},
    label="Condition search - Anxiety"
)
records2 = extract_results(items2)
print(f"\nExtracted {len(records2)} records:")
for r in records2:
    print_supplement(r)

# Show which supplement URLs we'd use for the next step
condition_records = [r for r in records2 if r.get("type") == "condition"]
if condition_records:
    supp_urls = [
        s["url"] for s in condition_records[0].get("recommendedSupplements", [])
        if s["name"] != "Supplements"
    ][:5]
    print(f"\n  → Would scrape these URLs for full data: {supp_urls}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3: Two-step pattern (how to actually use this in the project)
# Step 1: condition search → get URLs
# Step 2: direct URL scrape → get full structured data
# ─────────────────────────────────────────────────────────────────────────────
if condition_records and supp_urls:
    items3 = run_actor(
        run_input={"supplementUrls": supp_urls[:3]},  # Scrape top 3
        label=f"Two-step: scraping top supplements for anxiety"
    )
    records3 = extract_results(items3)
    print(f"\nExtracted {len(records3)} records:")
    for r in records3:
        print_supplement(r)


# ─────────────────────────────────────────────────────────────────────────────
# Summary — save combined report
# ─────────────────────────────────────────────────────────────────────────────
summary = {
    "run_timestamp": RUN_TIMESTAMP,
    "tests": [
        {"label": "Direct URL - Magnesium", "records_extracted": len(records1), "records": records1},
        {"label": "Condition search - Anxiety", "records_extracted": len(records2), "records": records2},
        {
            "label": "Two-step - Anxiety supplements",
            "records_extracted": len(records3) if (condition_records and supp_urls) else 0,
            "records": records3 if (condition_records and supp_urls) else [],
        },
    ],
    "notes": {
        "reliable_modes": ["supplementUrls (direct)", "searchType=conditions"],
        "unreliable_modes": ["searchType=supplements (lands on homepage)"],
        "actual_fields": ["name", "url", "summary", "dosage", "safety", "researchSummaries", "citationCount", "categories"],
        "missing_fields_vs_docs": ["effectMatrix", "benefits", "sideEffects", "drugInteractions", "dosageRange"],
        "data_structure": "Items are wrapped: item['results'] contains actual records",
    }
}

summary_file = OUTPUT_DIR / f"{RUN_TIMESTAMP}_summary.json"
with open(summary_file, "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*60}")
print("SUMMARY")
print(f"  Test 1 (direct URL):       {len(records1)} supplement(s)")
print(f"  Test 2 (condition search): {len(records2)} records")
print(f"  Test 3 (two-step):         {len(records3) if (condition_records and supp_urls) else 'skipped'} supplements")
print(f"\nAll outputs saved to: {OUTPUT_DIR}/")
print(f"  Summary file: {summary_file.name}")
