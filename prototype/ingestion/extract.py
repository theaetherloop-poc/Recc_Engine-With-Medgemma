"""PDF → cleaned, chunked condition passages.

Detects chapter boundaries in the Pizzorno textbook (regex `Chapter N - Name`),
slices each chapter's pages, cleans page-number noise, and windows the prose into
~600-token passages with overlap. Each passage carries its condition + page.
"""
import re
from typing import Iterator, List, Optional

import fitz  # PyMuPDF

PDF_DEFAULT = (
    "Textbook of Natural Medicine (2-Volume Set) -- Joseph E Pizzorno; "
    "Michael T Murray; MD Consult LLC -- MD consult, 2nd ed, Edinburgh, St_ Louis, "
    "MO, -- isbn13 9780443059452 -- 9f1ee3a2d21540000ae52311683c618d -- "
    "Anna’s Archive.pdf"
)

CHAPTER_RE = re.compile(r"^Chapter (\d+)\s*[-–]\s*(.+)$", re.M)


def find_chapters(doc) -> List[dict]:
    """Return [{num, name, page}] for every 'Chapter N - Name' marker, by page."""
    out = []
    for i in range(doc.page_count):
        head = doc[i].get_text()[:200]
        m = CHAPTER_RE.search(head)
        if m:
            out.append({"num": int(m.group(1)), "name": m.group(2).strip(),
                        "page": i})  # 0-indexed page
    return out


def _clean(text: str) -> str:
    lines = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s:
            continue
        if s.isdigit():           # standalone page numbers (e.g. "1303")
            continue
        if re.fullmatch(r"[\d\s\-–]+", s):  # stray numeric/dash runs
            continue
        lines.append(s)
    return " ".join(lines)


def chapter_text(doc, start_page: int, end_page: int) -> str:
    parts = [doc[p].get_text() for p in range(start_page, min(end_page, doc.page_count))]
    return _clean("\n".join(parts))


def window(text: str, size_words: int = 450, overlap: int = 60) -> Iterator[str]:
    """Word-window the text (~450 words ≈ ~600 tokens) with overlap."""
    words = text.split()
    if not words:
        return
    step = max(1, size_words - overlap)
    for i in range(0, len(words), step):
        chunk = words[i:i + size_words]
        if len(chunk) < 40 and i != 0:   # skip tiny trailing fragment
            break
        yield " ".join(chunk)


def iter_condition_passages(
    pdf_path: str = PDF_DEFAULT,
    chapter_min: int = 61,        # Section 6 (specific health problems) starts ~108
    chapter_max: int = 200,
    limit_chapters: Optional[int] = None,
) -> Iterator[dict]:
    """Yield {condition, chapter_num, page, passage} for condition chapters."""
    doc = fitz.open(pdf_path)
    chapters = find_chapters(doc)
    # Keep only the condition chapters, in page order, deduped by number.
    seen = set()
    conds = []
    for c in chapters:
        if chapter_min <= c["num"] <= chapter_max and c["num"] not in seen:
            seen.add(c["num"])
            conds.append(c)
    conds.sort(key=lambda c: c["page"])

    if limit_chapters:
        conds = conds[:limit_chapters]

    for idx, c in enumerate(conds):
        start = c["page"]
        end = conds[idx + 1]["page"] if idx + 1 < len(conds) else start + 40
        text = chapter_text(doc, start, end)
        for j, passage in enumerate(window(text)):
            yield {
                "condition": c["name"],
                "chapter_num": c["num"],
                "page": start + 1,   # human 1-indexed
                "chunk_idx": j,
                "passage": passage,
            }
