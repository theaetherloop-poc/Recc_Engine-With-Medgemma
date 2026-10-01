"""pubmed_search — agentic literature lookup via NCBI E-utilities (BioPython).

Requires env vars:
  NCBI_EMAIL    (required by NCBI)
  NCBI_API_KEY  (optional, raises rate limit 3 -> 10 req/s)
"""
import os
import time
from typing import List, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

try:
    from Bio import Entrez
    _BIO_OK = True
except Exception:  # pragma: no cover
    _BIO_OK = False

CURRENT_YEAR = 2026

# Registry of papers actually returned by pubmed_search this run (pmid -> title).
# run.py validates the agent's citations against this so it cannot fabricate them.
SEEN_PAPERS: dict = {}


def reset_seen() -> None:
    SEEN_PAPERS.clear()


def get_seen() -> dict:
    return dict(SEEN_PAPERS)


class PubMedInput(BaseModel):
    query: str = Field(..., description="PubMed query. Prefer MeSH terms and boolean "
                                        "syntax, e.g. '(\"Magnesium\"[MeSH]) AND "
                                        "(\"Sleep\"[MeSH])'.")
    max_results: int = Field(6, description="Max papers to return (1-15).")
    years_back: Optional[int] = Field(
        None, description="Restrict to the last N years (e.g. 5 for recent evidence)."
    )
    reviews_only: bool = Field(
        False, description="If true, restrict to reviews / meta-analyses / systematic "
                           "reviews (stronger evidence)."
    )


def _configure():
    Entrez.email = os.environ.get("NCBI_EMAIL", "")
    key = os.environ.get("NCBI_API_KEY")
    if key:
        Entrez.api_key = key


def pubmed_search(query: str, max_results: int = 6,
                  years_back: Optional[int] = None,
                  reviews_only: bool = False) -> List[dict]:
    _configure()
    term = query
    if reviews_only:
        term = (f"({term}) AND (\"Meta-Analysis\"[Publication Type] OR "
                f"\"Systematic Review\"[Publication Type] OR \"Review\"[Publication Type])")
    if years_back:
        term = f"({term}) AND (\"{CURRENT_YEAR - years_back}\"[PDAT] : \"3000\"[PDAT])"
    term = f"({term}) AND humans[MeSH]"

    handle = Entrez.esearch(db="pubmed", term=term, retmax=max_results)
    ids = Entrez.read(handle)["IdList"]
    handle.close()
    if not ids:
        return []
    time.sleep(0.2)  # be polite to NCBI
    fetch = Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="xml")
    records = Entrez.read(fetch)
    fetch.close()

    out = []
    for art in records.get("PubmedArticle", []):
        cit = art["MedlineCitation"]
        a = cit["Article"]
        abstract = " ".join(str(t) for t in a.get("Abstract", {}).get("AbstractText", []))
        out.append({
            "pmid": str(cit["PMID"]),
            "title": str(a.get("ArticleTitle", "")),
            "journal": str(a["Journal"]["Title"]),
            "year": a["Journal"]["JournalIssue"].get("PubDate", {}).get("Year", "n/a"),
            "abstract": abstract[:600],
        })
    return out


class PubMedSearchTool(BaseTool):
    name: str = "pubmed_search"
    description: str = (
        "Search peer-reviewed literature on PubMed. Use this to (a) attach scientific "
        "citations to a recommendation, or (b) read primary research when the internal "
        "knowledge base is thin on a topic. Write focused queries with MeSH terms. Set "
        "reviews_only=true and years_back=5 when you want strong, recent evidence."
    )
    args_schema: Type[BaseModel] = PubMedInput

    def _run(self, query: str, max_results: int = 6,
             years_back: Optional[int] = None, reviews_only: bool = False) -> str:
        if not _BIO_OK:
            return ("ERROR: biopython not installed. Run `pip install biopython`.")
        if not os.environ.get("NCBI_EMAIL"):
            return ("ERROR: NCBI_EMAIL not set. Set NCBI_EMAIL (and optionally "
                    "NCBI_API_KEY) in the environment.")
        max_results = max(1, min(int(max_results), 15))
        try:
            papers = pubmed_search(query, max_results, years_back, reviews_only)
        except Exception as e:
            return f"ERROR during PubMed search: {e}"
        if not papers:
            return f"No PubMed results for query: {query!r}"
        # Record real papers so citations can be validated against them.
        for p in papers:
            SEEN_PAPERS[str(p["pmid"])] = p["title"]
        lines = [f"Found {len(papers)} papers for {query!r}:\n"]
        for i, p in enumerate(papers, 1):
            lines.append(
                f"[{i}] {p['title']} ({p['journal']}, {p['year']}) PMID:{p['pmid']}\n"
                f"    {p['abstract']}\n"
            )
        return "\n".join(lines)
