"""
Generates Examine.com API Integration documentation as a Word (.docx) file.
Run: .venv/bin/python generate_examine_doc.py
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

doc = Document()

# ── Styles ────────────────────────────────────────────────────────────────────

def set_heading(paragraph, level=1):
    colors = {1: RGBColor(0x1A, 0x1A, 0x2E), 2: RGBColor(0x16, 0x21, 0x3E), 3: RGBColor(0x0F, 0x3A, 0x5F)}
    sizes  = {1: 18, 2: 14, 3: 12}
    run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
    run.bold = True
    run.font.size = Pt(sizes[level])
    run.font.color.rgb = colors[level]

def h1(text):
    p = doc.add_heading(text, level=1)
    set_heading(p, 1)
    return p

def h2(text):
    p = doc.add_heading(text, level=2)
    set_heading(p, 2)
    return p

def h3(text):
    p = doc.add_heading(text, level=3)
    set_heading(p, 3)
    return p

def body(text, bold_prefix=None):
    p = doc.add_paragraph()
    if bold_prefix:
        r = p.add_run(bold_prefix + " ")
        r.bold = True
    p.add_run(text)
    p.paragraph_format.space_after = Pt(4)
    return p

def bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        r = p.add_run(bold_prefix + " ")
        r.bold = True
    p.add_run(text)
    p.paragraph_format.space_after = Pt(3)
    return p

def add_table(headers, rows, col_widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.text = h
        run = cell.paragraphs[0].runs[0]
        run.bold = True
        run.font.size = Pt(9)
        cell._tc.get_or_add_tcPr()
        shading = OxmlElement('w:shd')
        shading.set(qn('w:fill'), '1A1A2E')
        shading.set(qn('w:color'), 'FFFFFF')
        cell._tc.tcPr.append(shading)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row_data in rows:
        row = table.add_row()
        for i, val in enumerate(row_data):
            cell = row.cells[i]
            cell.text = str(val)
            cell.paragraphs[0].runs[0].font.size = Pt(9)
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(w)
    doc.add_paragraph()

def divider():
    p = doc.add_paragraph("─" * 80)
    p.runs[0].font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    p.runs[0].font.size = Pt(8)

# ── Cover ─────────────────────────────────────────────────────────────────────

title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title_p.add_run("Examine.com API Integration")
run.bold = True
run.font.size = Pt(24)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run2 = sub_p.add_run("Research, Experiments & Workflow Integration — Aether AI Engine")
run2.font.size = Pt(12)
run2.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

date_p = doc.add_paragraph()
date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
date_p.add_run(f"Prepared: {datetime.date.today().strftime('%B %d, %Y')}").font.size = Pt(10)

doc.add_paragraph()
divider()
doc.add_paragraph()

# ── 1. Overview ───────────────────────────────────────────────────────────────

h1("1. Overview")
body(
    "This document covers the end-to-end work done integrating the Examine.com Apify scraper "
    "into the Aether AI supplement recommendation engine. It includes the initial API exploration, "
    "condition-level coverage analysis (benchmarked against NatMed Pro), profile-level integration "
    "experiments, current limitations, and the path forward."
)
doc.add_paragraph()

# ── 2. About the API ─────────────────────────────────────────────────────────

h1("2. About the Examine.com Apify Actor")

h2("2.1 What It Is")
body(
    "Apify actor hanamira/examine-com-supplement-research is a cloud-hosted scraper that extracts "
    "structured, evidence-based supplement data from Examine.com — the largest independent database "
    "of nutritional supplement research. Unlike a raw web search, it returns fully structured records "
    "per supplement."
)

h2("2.2 Input Modes")
add_table(
    ["Mode", "Input", "Best For", "Reliability"],
    [
        ["Condition search", 'query + searchType: "conditions"',
         "Find all supplements Examine recommends for a health condition", "✅ Reliable"],
        ["Direct URL scrape", "supplementUrls list",
         "Fetch full data for known supplement pages", "✅ Most reliable"],
        ["Supplement search", 'query + searchType: "supplements"',
         "Search by supplement name", "⚠️ Unreliable — lands on homepage"],
    ],
    col_widths=[1.2, 2.0, 2.5, 1.1]
)

h2("2.3 Output Fields (per supplement — Direct URL mode)")
add_table(
    ["Field", "Description", "Notes"],
    [
        ["name", "Supplement name", ""],
        ["summary", "Evidence overview", "300–500 chars typically"],
        ["dosage", "Full dosage text", "Long — trimmed to 200 chars in pipeline"],
        ["citationCount", "Number of cited studies", "Proxy for evidence strength; scraping occasionally returns 0"],
        ["categories", "Examine health categories", 'e.g. "Brain Health", "Sleep"'],
        ["researchSummaries", "Key study snippets", "Up to 2 included in pipeline"],
        ["url", "Direct Examine.com page URL", ""],
        ["source", "Always Examine.com", ""],
    ],
    col_widths=[1.4, 2.2, 2.6]
)

body("Fields listed in actor documentation but NOT actually returned: effectMatrix, benefits, sideEffects, drugInteractions, dosageRange.")

h2("2.4 Key Structural Finding")
body(
    "The Apify actor wraps results in a container object — each dataset item has the shape "
    '{searchType, query, resultCount, results: [...]}. The actual supplement/condition records '
    "are nested inside item[\"results\"], not at the top level as the actor documentation implies. "
    "All integration code accounts for this."
)
doc.add_paragraph()

# ── 3. Experiments ────────────────────────────────────────────────────────────

h1("3. Experiments")

h2("3.1 Initial API Connection & Mode Testing")
body("Three connection tests were run to validate the API and discover its actual behaviour:")

add_table(
    ["Test", "Input", "Status", "Key Finding"],
    [
        ["Direct URL — Magnesium",
         "supplementUrls: [examine.com/supplements/magnesium/]",
         "✅ Pass", "Full data returned: 96 citations, dosage text, 5 categories"],
        ["Condition search — Anxiety",
         'query: "anxiety", searchType: "conditions"',
         "✅ Pass", "Returned 12 recommended supplement URLs for anxiety condition page"],
        ["Two-step — Anxiety supplements",
         "Condition search → scrape top 3 URLs",
         "✅ Pass", "Ashwagandha (37 cit.), Kava (liver warning), Saffron (80 cit.) returned with full data"],
    ],
    col_widths=[1.5, 2.2, 0.8, 2.2]
)
body("Output files saved to: test_outputs/apify_examine/ (timestamped JSON per test + summary.json)")

h2("3.2 Condition Coverage Evaluation (vs NatMed Pro)")
body(
    "All 84 conditions from NatMed_Pro_Conditions.xlsx were searched against Examine.com using "
    "the condition search mode. The goal was to benchmark Examine's condition taxonomy coverage "
    "against the NatMed Pro database."
)

h3("Coverage Results")
add_table(
    ["Metric", "Value"],
    [
        ["Total conditions queried", "84"],
        ["Conditions found on Examine", "44 (52%)"],
        ["— Exact match", "23"],
        ["— Partial match (related condition)", "15"],
        ["— Unrelated match (wrong page returned)", "6"],
        ["Conditions not found", "40 (48%)"],
        ["Avg supplements per found condition", "6.5"],
        ["Max supplements (single condition)", "19 (CKD, Prediabetes, CAD, NAFLD)"],
    ],
    col_widths=[3.2, 3.0]
)

h3("Top Conditions by Supplement Count")
add_table(
    ["Condition (searched)", "Examine Match", "Supplements", "Match Type"],
    [
        ["Chronic kidney disease (CKD)", "Chronic Kidney Disease (CKD)", "19", "Exact"],
        ["Prediabetes", "Prediabetes", "19", "Exact"],
        ["Coronary artery disease (CAD)", "Coronary Artery Disease (CAD)", "19", "Exact"],
        ["NAFLD", "Nonalcoholic Fatty Liver Disease (NAFLD)", "19", "Exact"],
        ["Type 1 diabetes mellitus", "Type 1 Diabetes", "17", "Exact"],
        ["PCOS", "Polycystic Ovary Syndrome (PCOS)", "16", "Exact"],
        ["Rheumatoid arthritis", "Joint Pain (symptom page)", "2", "Unrelated"],
        ["Hypothyroidism", "Hair Loss (symptom page)", "3", "Unrelated"],
        ["Insulin resistance", "(not found)", "0", "Not found"],
    ],
    col_widths=[2.2, 2.4, 0.9, 0.9]
)

h3("Examine vs NatMed Pro — Comparison")
body(
    "NatMed Pro organises supplements by clinical efficacy tiers (Effective, Likely Effective, "
    "Possibly Effective, Insufficient Evidence). Examine.com does not use tiers — it lists all "
    "supplements that have any research for a condition."
)
add_table(
    ["Dimension", "NatMed Pro", "Examine.com"],
    [
        ["Coverage (conditions)", "Comprehensive clinical database", "52% of our condition list found"],
        ["Supplement count per condition", "Up to 170 (Rheumatoid Arthritis)", "Avg 6.5 per found condition"],
        ["Evidence tiers", "Yes — Effective → Insufficient", "No tiers; citation count only"],
        ["Dosage data", "Yes, detailed", "Yes, in text form"],
        ["Structured output", "Proprietary API", "Structured JSON via Apify"],
        ["Condition taxonomy", "Clinical (ICD-aligned)", "Consumer-friendly (symptom-based)"],
        ["Access model", "Subscription", "Pay-per-use (Apify credits)"],
        ["Availability", "Subscription required", "Publicly accessible via Apify"],
    ],
    col_widths=[1.8, 2.3, 2.2]
)
body(
    "Conclusion: Examine.com is comparatively better than NatMed Pro in terms of open availability "
    "and structured data access. For well-known conditions (CKD, PCOS, Prediabetes, NAFLD, CAD), "
    "Examine returns strong results with 15–19 supplements per condition. However, it does not cover "
    "highly specific clinical sub-conditions (e.g. Antiretroviral-induced insulin resistance, "
    "Hypertensive nephrosclerosis) and its condition taxonomy differs from clinical nomenclature, "
    "causing mismatches for roughly 48% of our condition list."
)
doc.add_paragraph()
body("Output file: test_outputs/examine_coverage/examine_coverage.xlsx")
doc.add_paragraph()

# ── 4. Workflow Integration ────────────────────────────────────────────────────

h1("4. Workflow Integration")

h2("4.1 Architecture Overview")
body("The Examine API has been integrated as a two-agent step within the existing CrewAI pipeline, replacing the previous Serper-based web search for ingredient discovery. Dosage research (final step) continues to use Serper.")

h3("Previous Flow")
bullet("profile_summarizer → web_ingredient_discovery (Serper → raw text → LLM extracts names) → supplement_recommender → focus_area_specialist → final_supplement_compiler (Serper for dosages)")

h3("New Flow")
for step in [
    "profile_summarizer — unchanged",
    "patient_examine_mapper (NEW) — LLM maps clinical patient data to Examine-compatible search terms",
    "web_ingredient_discovery (MODIFIED) — uses ExamineApifyTool; returns structured supplement data",
    "supplement_recommender — unchanged in structure; now receives richer evidence context",
    "focus_area_specialist — unchanged",
    "final_supplement_compiler — unchanged; Serper still used for dosage research",
]:
    bullet(step)

h2("4.2 New Components")

h3("patient_examine_mapper Agent")
body(
    "A pure LLM agent (no tools) that converts clinical patient data — flagged biomarkers, diagnoses, "
    "symptoms — into 5–8 consumer health terms that map to Examine.com condition pages. "
    "It applies explicit mapping rules: e.g. high TSH → hypothyroidism, low ferritin → iron deficiency "
    "anemia, trouble sleeping → insomnia. It deduplicates and limits output to the most clinically "
    "urgent terms."
)
body("File: src/aether_2/config/agents.yaml (patient_examine_mapper section)")
body("Task: src/aether_2/config/tasks.yaml (map_patient_to_examine_terms section)")

h3("ExamineApifyTool")
body("A CrewAI BaseTool that encapsulates the two-step Apify pattern:")
bullet("Step A — Condition search: one Apify run per search term → collects supplement URLs, tracking which conditions each supplement was found under")
bullet("Step B — Batch URL scrape: one Apify run for all unique URLs (capped at 10) → returns full structured supplement data")
body("File: src/aether_2/tools/examine_apify_tool.py")

h3("Updated DiscoveredIngredient Model")
body("src/aether_2/models.py — DiscoveredIngredient now carries:")
add_table(
    ["Field", "Type", "Description"],
    [
        ["ingredient_name", "str", "Supplement name"],
        ["reasons", "List[str]", "Which Examine conditions recommended it"],
        ["summary", "str", "Examine.com evidence summary (first 300 chars)"],
        ["dosage_hint", "str", "Dosage text from Examine (first 200 chars)"],
        ["citation_count", "int", "Number of cited studies — evidence strength proxy"],
        ["categories", "List[str]", "Examine health categories"],
        ["research_summaries", "List[str]", "Up to 2 research finding snippets"],
        ["examine_url", "str", "Direct link to supplement page"],
        ["source", "str", "Always Examine.com"],
    ],
    col_widths=[1.4, 0.9, 3.9]
)

h2("4.3 Apify API Cost & Latency")
body("Each full pipeline run makes the following Apify calls:")
add_table(
    ["Step", "Apify Runs", "Time (approx)"],
    [
        ["Condition search (per term, 5–8 terms)", "5–8 runs", "~25s each → 2–3 min"],
        ["Batch URL scrape (all unique URLs)", "1 run", "~30–45s"],
        ["Total per patient profile", "6–9 runs", "~3–4 min"],
    ],
    col_widths=[2.5, 1.5, 1.8]
)
body(
    "Latency note: The Apify-based discovery step adds ~3–4 minutes per profile compared to the "
    "Serper approach (~30–45 seconds). This is a known disadvantage. Mitigation options include "
    "caching condition→supplement URL mappings locally (most conditions are stable), and running "
    "condition searches in parallel using async Apify calls."
)
doc.add_paragraph()

# ── 5. Profile-Level Experiments ─────────────────────────────────────────────

h1("5. Profile-Level Experiments")
body("Three patient profiles were tested end-to-end through the new Examine-integrated pipeline.")

h2("Profile 1 — test_user18 (Asthma + Metabolic Risk)")
body("Patient: Asthma diagnosis; flagged biomarkers include low Vitamin D, high Lp(a), high VLDL, high HbA1c, abnormal liver markers.")

h3("Examine Terms Generated")
body('"asthma", "insulin resistance", "high cholesterol", "heart health", "vitamin D deficiency", "liver health"')
body("Comment: Good mapping. The LLM correctly grouped multiple lipid markers under high cholesterol and heart health, and identified insulin resistance from HbA1c.")

h3("Discovered Ingredients (10 from Examine)")
add_table(
    ["Supplement", "Condition(s) Found Under"],
    [
        ["Magnesium", "asthma"],
        ["Vitamin D", "asthma, vitamin D deficiency"],
        ["Probiotics", "asthma"],
        ["Pycnogenol", "asthma"],
        ["Saffron", "asthma, high cholesterol, liver health"],
        ["Black seed (Nigella sativa)", "asthma"],
        ["Boswellia", "asthma"],
        ["Caffeine", "asthma"],
        ["Citrulline", "asthma"],
        ["Coleus forskohlii", "asthma"],
    ],
    col_widths=[2.0, 4.2]
)
body("Note: Insulin resistance, high cholesterol, heart health, and liver health conditions returned no supplement URLs — Examine's condition search did not resolve those terms to specific condition pages in this run.")

h3("Final Recommendations (4 supplements)")
add_table(
    ["Supplement", "Dosage", "Focus Area", "Source"],
    [
        ["Vitamin D3", "2000 IU daily + K2 MK-7", "IMM, CM", "Examine + clinical reasoning"],
        ["Magnesium Glycinate", "200 mg nightly", "IMM, CM", "Examine + clinical reasoning"],
        ["N-Acetyl Cysteine", "600 mg twice daily", "DTX, IMM", "Existing supplement retained"],
        ["Quercetin", "500 mg daily", "IMM", "Existing supplement retained"],
    ],
    col_widths=[1.8, 1.8, 1.0, 2.6]
)

h2("Profile 2 — test_user19 (PCOS + Hypothyroidism + Metabolic)")
body("Patient: PCOS, diabetes, hypothyroidism diagnoses; 21 flagged biomarkers including high TSH, high DHEA-S, high LDL, high HbA1c, low Vitamin D, high hsCRP.")

h3("Examine Terms Generated")
body('"PCOS", "insulin resistance", "diabetes", "hypothyroidism", "high cholesterol", "fertility", "vitamin D deficiency", "insomnia" (8 terms)')
body("Comment: Strong mapping. PCOS, hypothyroidism, and diabetes mapped correctly. Fertility was a reasonable addition given PCOS context.")

h3("Discovered Ingredients (10 from Examine)")
add_table(
    ["Supplement", "Condition(s) Found Under"],
    [
        ["Chromium", "PCOS, diabetes"],
        ["Inositol", "PCOS, diabetes"],
        ["Resveratrol", "PCOS"],
        ["Magnesium", "PCOS, insomnia"],
        ["Berberine", "PCOS"],
        ["L-Carnitine", "PCOS"],
        ["Coenzyme Q10", "PCOS"],
        ["Curcumin", "PCOS"],
        ["N-Acetylcysteine", "PCOS"],
        ["Vitamin D", "PCOS, vitamin D deficiency"],
    ],
    col_widths=[2.0, 4.2]
)
body("Note: Hypothyroidism and high cholesterol conditions did not resolve to supplement URLs in this run — a limitation of the condition search matching.")

h3("Final Recommendations (8 supplements)")
add_table(
    ["Supplement", "Focus Area"],
    [
        ["Vitamin D3", "HRM, CM"],
        ["N-Acetylcysteine", "DTX, HRM"],
        ["Coenzyme Q10", "MITO, HRM"],
        ["Curcumin (standardized extract ≥95%)", "IMM, CM"],
        ["Berberine", "CM, HRM"],
        ["Inositol", "HRM, CM"],
        ["Magnesium Glycinate", "STR, CM"],
        ["Selenium", "HRM"],
    ],
    col_widths=[3.0, 3.2]
)

h2("Profile 3 — test_user17 (reference run, pre-integration)")
body("Run with the previous Serper-based pipeline as reference baseline. Results are in outputs/test_user17_at_example_com/.")

h2("Overall Result Assessment")
body(
    "The Examine-integrated pipeline produces clinically sound, accurate recommendations. "
    "The supplement_recommender agent correctly uses the Examine data as input signal and applies "
    "patient-specific clinical reasoning to filter and rank. Final protocols are qualitatively "
    "on par with previous Serper-based outputs."
)
body("Coverage gap: The discovery step is constrained by which Examine condition search terms resolve to actual condition pages. In Profile 1, only 'asthma' and 'vitamin D deficiency' yielded supplement URLs — the other 4 terms did not, leaving insulin resistance, lipid, and liver conditions unaddressed in discovery. Profile 2 fared better with PCOS dominating the discovery output.")
body("This means coverage is lower than the Serper-based approach, which would find supplements for each biomarker individually via targeted PubMed/NIH searches. The improvement is in data quality (structured evidence, dosage hints, citation counts) but not yet in breadth.")
doc.add_paragraph()

# ── 6. Current Limitations ────────────────────────────────────────────────────

h1("6. Current Limitations")

h2("6.1 Condition Mapping (Primary Limitation)")
body(
    "The patient_examine_mapper agent is a proof-of-concept that works well for common conditions "
    "(PCOS, hypothyroidism, asthma, vitamin D deficiency) but has insufficient coverage for the "
    "full range of biomarker-to-condition mappings the Aether engine encounters. Specifically:"
)
bullet("Many biomarker combinations do not have a direct consumer-facing Examine condition (e.g. high Lp(a), low SHBG, abnormal AST:ALT ratio)")
bullet("Examine's condition search (Step A of the tool) sometimes fails to match — returning homepage or unrelated condition pages for ~48% of conditions tested")
bullet("The mapper's rule set covers the most common cases but needs to be expanded systematically, condition by condition, with verified Examine URL slugs")
bullet("A production-grade solution would pre-build a curated mapping table: {clinical term → examine.com/conditions/slug/} rather than relying on search matching")
body(
    "The priority agent is built and functional — it will need to be worked on in more detail, "
    "with a curated mapping dictionary of biomarker states and diagnoses → exact Examine condition slugs, "
    "to achieve full coverage. "
    "Work is currently in progress on a dedicated condition mapping script that derives Examine-compatible "
    "search terms directly from raw patient biomarker values and flags."
)

h2("6.2 Latency")
body(
    "Each profile run requires 6–9 sequential Apify calls, adding ~3–4 minutes to pipeline execution. "
    "The previous Serper approach completed discovery in ~30–45 seconds. "
    "This is acceptable for offline/async processing but would be a bottleneck in real-time API usage. "
    "Mitigation: local caching of condition → supplement URL mappings (Examine data is stable week-to-week)."
)

h2("6.3 Citation Count Scraping")
body(
    "The citationCount field returns 0 for most supplements in the current scraping — the actor "
    "only captures the count displayed in a specific page element that is not consistently present. "
    "This limits its use as an evidence-strength signal. The summary and researchSummaries fields "
    "are more reliable proxies."
)

h2("6.4 Missing Fields")
body(
    "effectMatrix, benefits, sideEffects, drugInteractions, and dosageRange are documented in the "
    "Apify actor but are not returned in the actual output. These would significantly enrich the "
    "recommendation context if available."
)
doc.add_paragraph()

# ── 7. Path Forward ────────────────────────────────────────────────────────────

h1("7. Path Forward")
bullet("Build a curated biomarker → Examine condition slug mapping table to replace search-based matching")
bullet("Explore parallel Apify calls (async) to reduce per-profile latency from ~4 min to ~1 min")
bullet("Add local caching layer for condition → supplement URL results (TTL: 7 days)")
bullet("Investigate alternative Apify actors or direct Examine API for missing fields (effectMatrix, sideEffects)")
bullet("Run broader profile testing across all 18 test users to validate coverage and recommendation quality")
doc.add_paragraph()

# ── 8. Output Files Reference ─────────────────────────────────────────────────

h1("8. Output Files Reference")
add_table(
    ["File / Location", "Contents"],
    [
        ["test_outputs/apify_examine/", "Initial API connection test results (3 tests, JSON + summary)"],
        ["test_outputs/examine_coverage/progress.json", "Condition coverage evaluation — all 84 conditions"],
        ["test_outputs/examine_coverage/examine_coverage.xlsx", "Coverage comparison Excel report"],
        ["outputs/test_user18_at_example_com/", "Profile 1 full pipeline outputs (all 6 agent files + xlsx)"],
        ["outputs/test_user18_at_example_com/map_patient_to_examine_terms.md", "Profile 1 — mapped Examine terms"],
        ["outputs/test_user18_at_example_com/discovered_ingredients_web.json", "Profile 1 — Examine discoveries"],
        ["outputs/test_user19_at_example_com/", "Profile 2 full pipeline outputs"],
        ["outputs/test_user19_at_example_com/map_patient_to_examine_terms.md", "Profile 2 — mapped Examine terms"],
        ["outputs/test_user19_at_example_com/discovered_ingredients_web.json", "Profile 2 — Examine discoveries"],
        ["[LINK PLACEHOLDER]", "Excel comparison report — profiles 18 & 19 recommendations"],
        ["src/aether_2/tools/examine_apify_tool.py", "ExamineApifyTool source code"],
        ["evaluate_examine_coverage.py", "Condition coverage evaluation script (resumable)"],
        ["test_apify_examine.py", "Initial API test script"],
    ],
    col_widths=[3.2, 3.0]
)

# ── Save ──────────────────────────────────────────────────────────────────────

out_path = "Examine_API_Integration_Documentation.docx"
doc.save(out_path)
print(f"Saved: {out_path}")
