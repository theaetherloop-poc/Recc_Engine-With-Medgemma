"""
ExamineApifyTool - CrewAI tool for Examine.com supplement discovery via Apify.

Two-step pattern:
  Step A: Condition searches → collect supplement URLs (one Apify run per term)
  Step B: Batch URL scrape  → structured supplement data (one run for all URLs)

Option 2 design: accepts whatever supplements Examine returns for a condition,
regardless of name-match quality. The supplement_recommender LLM filters appropriately.
"""

import os
import json
from typing import Type, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

ACTOR_ID = "hanamira/examine-com-supplement-research"
SKIP_NAMES = {"Supplements", "Health Conditions and Goals"}
MAX_URLS_PER_BATCH = 10  # Examine pages to scrape in one run


class ExamineApifyInput(BaseModel):
    examine_terms: List[str] = Field(
        ...,
        description="List of consumer health condition terms to search on Examine.com "
                    "(e.g. ['vitamin D deficiency', 'hypothyroidism', 'insomnia'])"
    )


class ExamineApifyTool(BaseTool):
    name: str = "examine_apify_search"
    description: str = (
        "Searches Examine.com via Apify for evidence-based supplement data. "
        "Takes a list of health condition terms, finds recommended supplements for each, "
        "then fetches full structured data (summary, dosage, citations) per supplement. "
        "Returns a list of ingredients with rich evidence information."
    )
    args_schema: Type[BaseModel] = ExamineApifyInput

    def _get_client(self):
        from apify_client import ApifyClient
        token = os.getenv("APIFY_API_TOKEN")
        if not token:
            raise EnvironmentError("APIFY_API_TOKEN not set in environment")
        return ApifyClient(token)

    def _condition_search(self, client, term: str) -> List[str]:
        """
        Step A: Search Examine.com conditions for a term.
        Returns a deduplicated list of supplement URLs found.
        """
        try:
            run = client.actor(ACTOR_ID).call(
                run_input={"query": term, "searchType": "conditions", "maxResults": 5}
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

            urls = []
            for item in items:
                for record in item.get("results", []):
                    if record.get("type") == "condition" and record.get("name") not in SKIP_NAMES:
                        for s in record.get("recommendedSupplements", []):
                            url = s.get("url", "")
                            name = s.get("name", "")
                            if url and name not in SKIP_NAMES and "/supplements/" in url:
                                urls.append(url)
                        break  # Use first valid condition result only

            return urls

        except Exception as e:
            print(f"  [ExamineApify] Condition search failed for '{term}': {e}")
            return []

    def _batch_scrape(self, client, urls: List[str]) -> List[dict]:
        """
        Step B: Scrape a batch of supplement URLs for full structured data.
        Returns list of raw supplement records from Examine.
        """
        try:
            run = client.actor(ACTOR_ID).call(
                run_input={"supplementUrls": urls}
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

            supplements = []
            for item in items:
                for record in item.get("results", []):
                    if record.get("type") == "supplement" and record.get("name") not in SKIP_NAMES:
                        if record.get("name"):
                            supplements.append(record)
            return supplements

        except Exception as e:
            print(f"  [ExamineApify] Batch scrape failed: {e}")
            return []

    def _run(self, examine_terms: List[str]) -> str:
        """
        Main execution: condition searches → deduplicate URLs → batch scrape.
        Returns JSON string matching DiscoveredIngredient list format.
        """
        client = self._get_client()

        print(f"\n[ExamineApify] Searching {len(examine_terms)} conditions...")

        # Step A: collect supplement URLs per term, tracking which terms found each URL
        url_to_reasons: dict[str, List[str]] = {}
        for term in examine_terms:
            print(f"  [ExamineApify] Condition search: '{term}'")
            urls = self._condition_search(client, term)
            print(f"    → {len(urls)} supplement URLs found")
            for url in urls:
                url_to_reasons.setdefault(url, [])
                if term not in url_to_reasons[url]:
                    url_to_reasons[url].append(term)

        all_urls = list(url_to_reasons.keys())
        print(f"\n[ExamineApify] {len(all_urls)} unique supplement URLs across all conditions")

        if not all_urls:
            return json.dumps({"discovered_ingredients": []})

        # Step B: batch scrape (cap at MAX_URLS_PER_BATCH)
        batch_urls = all_urls[:MAX_URLS_PER_BATCH]
        if len(all_urls) > MAX_URLS_PER_BATCH:
            print(f"  [ExamineApify] Capping to {MAX_URLS_PER_BATCH} URLs to limit cost")

        print(f"[ExamineApify] Batch scraping {len(batch_urls)} supplement pages...")
        raw_supplements = self._batch_scrape(client, batch_urls)
        print(f"  [ExamineApify] Got data for {len(raw_supplements)} supplements")

        # Build DiscoveredIngredient-compatible output
        discovered = []
        for supp in raw_supplements:
            url = supp.get("url", "")
            # Normalise URL for key lookup (Apify sometimes adds ?show_conditions=true)
            base_url = url.split("?")[0].rstrip("/") + "/"
            reasons = url_to_reasons.get(url, url_to_reasons.get(base_url, []))

            dosage_raw = supp.get("dosage", "") or ""
            # Trim dosage to first 200 chars to avoid token bloat
            dosage_hint = dosage_raw[:200].strip() if dosage_raw else ""

            research = supp.get("researchSummaries", []) or []
            summary = supp.get("summary", "") or ""

            discovered.append({
                "ingredient_name": supp.get("name", ""),
                "reasons": reasons if reasons else examine_terms,
                "summary": summary[:300] if summary else "",
                "dosage_hint": dosage_hint,
                "citation_count": supp.get("citationCount", 0) or 0,
                "categories": supp.get("categories", []) or [],
                "research_summaries": research[:2],  # max 2 snippets to keep tokens lean
                "examine_url": url,
                "source": "Examine.com"
            })

        result = {"discovered_ingredients": discovered}
        print(f"\n[ExamineApify] Complete: {len(discovered)} supplements with full data\n")
        return json.dumps(result, indent=2)
