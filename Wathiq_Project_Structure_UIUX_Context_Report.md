# Wathiq — Project Structure & UI/UX Context Report

**READ-ONLY CONFIRMED — NO PROJECT FILES WILL BE MODIFIED.**

**Purpose:** a reference document for a future Lovable UI/UX redesign prompt — describing what exists today, not what should be built.
**Date:** 2026-08-09

---

## 1. Executive Summary

`Wathiq-Data-Management-Platform` is a real, working (not just illustrative) Arabic-first compliance/maturity-assessment system for Saudi Arabia's National Data Indicator (NDI) framework, currently scoped to one domain: **DC (Data Classification / تصنيف البيانات)**. It is not one UI — it is **three separate, independently-branded frontend surfaces** sitting on top of a large Python backend (`src/`, 50+ modules: RAG, knowledge graph, evidence assessment, scoring, recommendations, Word report generation) and a JSON-file data layer (`data/`):

1. **`dashboard/`** — a 2-page Streamlit app, wired to live backend logic. Page 1 (`app.py`) is titled **"NDI-Sentinel"** in the browser tab and on-screen (confirmed from code) and runs a real, interactive single-evidence assessment pipeline. Page 2 (`pages/1_نظرة_عامة_والنضج.py`) is titled **"وثيق | Wathiq"** and shows aggregate executive/coverage analytics read from pre-computed JSON results.
2. **`wathiq_maturity_dashboard/`** — a large, self-contained static HTML/CSS/JS application (~7,400 lines across its CSS+JS), consistently branded **"وثيق / Wathiq"**, with by far the most mature design-token system of the three surfaces. It is **not wired to the live backend** — it fetches its own local, explicitly-named `data/sample_maturity_report.json` and `data/operational_excellence_simulation.json`.
3. **`wathiq_portfolio_package/`** — a synthetic evidence/prototype deliverable package (already exhaustively audited in prior sessions of this project; summarized here only for completeness, not re-analyzed) containing 4 static HTML mockups branded **SGSA** (fictitious client organization) as the entity, **Wathiq** as the product.

No React/Vue/Next.js/Tailwind, no database, and **no REST API layer** were found anywhere (`src/api/` exists but contains only an empty `__init__.py`). This report documents exactly what was found in each surface, distinguishing **CONFIRMED FROM CODE** facts from **INFERRED** interpretations and **UNCERTAIN/NOT FOUND** items — nothing below was invented.

---

## 2. Project Architecture

Actual structure, as found (not assumed in advance):

```text
Wathiq-Data-Management-Platform/
│
├── dashboard/                    Streamlit UI (2 pages) — LIVE, wired to src/ + data/
│   ├── app.py                    Page 1: "NDI-Sentinel" — evidence upload & assessment
│   ├── data_layer.py             Read-only pandas layer over data/assessment_results/
│   └── pages/
│       └── 1_نظرة_عامة_والنضج.py  Page 2: "وثيق | Wathiq" — executive overview & MQ coverage
│
├── wathiq_maturity_dashboard/    Static HTML/CSS/JS app — STANDALONE, sample data only
│   ├── index.html                "وثيق — منصة إدارة البيانات"
│   ├── css/ (tokens/theme/layout/components/animations)
│   ├── js/ (app.js, theme.js, recommendation_engine.js)
│   └── data/ (its own local JSON — sample_maturity_report.json, etc.)
│
├── wathiq_portfolio_package/     Synthetic evidence + 4 HTML prototypes — SGSA-branded
│   (previously, separately audited in full — see prior session reports)
│
├── src/                          Python backend (no HTTP API — called in-process)
│   ├── evidence_assessment/, maturity_assessment/, scoring/, recommendations/
│   ├── rag/, knowledge/, knowledge_graph/, knowledge_map/, llm/
│   ├── catalog/, compliance/, dashboard/ (adapters), reports/, services/
│   └── api/                      Empty placeholder (__init__.py only) — NOT a real API
│
├── data/                         JSON data consumed by dashboard/ (assessment results,
│                                  evidence catalog, knowledge graph/map, RAG index, rules)
├── evidence_repository/          Real evidence intake (data_classification/MQ1/MQ2/MQ3/current_evidence)
├── knowledge_base/                Source PDFs (laws, policies, standards, NDI framework guides)
├── vector_db/                    ChromaDB (2 collections: dc_rag_chroma, ndi_rag_v2_chroma)
├── reports/                      Generated DOCX compliance reports, one per Evidence Code
├── temp_uploads/                 Scratch upload area used by dashboard/app.py
└── root-level *.py               _mk_dc_*.py / _patch_dc_*.py generator/patch scripts
                                   (NOT investigated in this pass — see Section 19)
```

**Relationship summary (CONFIRMED FROM CODE):**
- `dashboard/app.py` → `src/dashboard/assessment_dashboard_adapter.py::prepare_dashboard_assessment()` → `src/services/assessment_pipeline_service.py::run_assessment_pipeline()` → (not traced further into individual engines in this pass, per the adapter's own stated boundary).
- `dashboard/pages/1_نظرة_عامة_والنضج.py` → `dashboard/data_layer.py::create_dashboard_dataset()` → reads `data/assessment_results/*.json` + `data/evidence_catalog/*.json` directly (no engine call).
- `wathiq_maturity_dashboard/js/app.js` → `fetch()` → its own `wathiq_maturity_dashboard/data/*.json` files only. **No relationship to `src/` or root `data/` was found** — these are two separate JSON data pools with similar-sounding but distinct locations.

---

## 3. Complete Folder/File Structure

| Area | Files | Role | Source or Generated? |
|---|---:|---|---|
| `dashboard/` | 3 `.py` + 2 `.pyc` (+1 nested `.pyc`) | Streamlit UI | Source |
| `src/` | ~65 `.py` (+ matching `.pyc` caches) across 20 subpackages | Backend logic | Source |
| `wathiq_maturity_dashboard/` | 1 HTML, 5 CSS, 3 JS, 6 JSON | Standalone frontend | Source (HTML/CSS/JS) + data (JSON, explicitly "sample"/"simulation") |
| `wathiq_portfolio_package/` | 136 files (see prior audit reports) | Synthetic evidence package | Mixed source/generated |
| `data/` | 20 JSON + 2 `.txt` + 1 `.md`, across 9 subfolders | Pipeline outputs consumed by `dashboard/` | Generated (by `src/` pipelines, not re-verified this pass) |
| `evidence_repository/` | organized under `data_classification/{MQ1,MQ2,MQ3,current_evidence}` | Real evidence intake | Source (uploaded documents) |
| `knowledge_base/` | 8 PDFs + 1 JSON, across `guides/laws/ndi_framework/policies/standards` | Reference material (laws, policies, NDI framework guides) | Source |
| `vector_db/` | 2 ChromaDB collections (`dc_rag_chroma`, `ndi_rag_v2_chroma`) | RAG vector index | Generated |
| `reports/` | 23 `Compliance_Assessment_Report_DC.*.docx` + 5 `.txt` validation reports | Generated Word reports, one per Evidence Code | Generated |
| `temp_uploads/` | 1 `.docx` | Scratch area for `dashboard/app.py` uploads | Runtime/ephemeral |
| Root scripts | 20 `_mk_dc_*.py` / `_patch_dc_*.py` + 2 loose utility scripts | **UNKNOWN purpose — not opened this pass** | Unknown |

---

## 4. Frontend Entry Points

| UI Area | File | View/ID | Navigation Trigger | JS/Python Controller | CSS Source |
|---|---|---|---|---|---|
| Streamlit — Evidence Assessment | `dashboard/app.py` | Single page, no `id`s (Streamlit-managed DOM) | Streamlit's auto-generated sidebar (multi-page app convention: files in `pages/` become nav entries) | `main()` in `app.py`, calling `prepare_dashboard_assessment()` | Injected `<style>` block inside `app.py` (RTL override only) |
| Streamlit — Overview & Maturity | `dashboard/pages/1_نظرة_عامة_والنضج.py` | Single page | Same Streamlit sidebar, entry #1 | `main()` in the page file, calling `create_dashboard_dataset()` | Injected `<style>` block inside the page file (full custom palette, `_inject_css()`) |
| Static dashboard | `wathiq_maturity_dashboard/index.html` | Single scrolling page, 4 static `<section>` (`#overview`, `#mq-cards`, `#gaps`, `#recommendations`) + up to 4 more sections injected by JS at runtime (Compliance, Operational Excellence, Evidence Repository, Visual Evidence Repository) | None — no router, no tabs; it is one continuously-scrolling page. Deep interaction happens via a single shared **modal** (`#wq-modal-overlay`) opened from cards/buttons | `js/app.js` (3,705 lines), `js/theme.js`, `js/recommendation_engine.js` | `css/tokens.css`, `theme.css`, `layout.css`, `components.css`, `animations.css` (5 separate files, explicitly layered: primitives → semantic → layout → components → motion) |
| Prototype mockups | `wathiq_portfolio_package/04_Platform_Mockups/*.html` (4 files) | Per-file sidebar + `data-view` sections | In-file JS `showView()` per prototype, each file independent | Inline `<script>` per file | Inline `<style>` per file (design tokens duplicated across all 4, previously documented) |

**Is it a Single Page Application?** Only `wathiq_maturity_dashboard/index.html` behaves like one (single HTML document, all content on one scroll + a modal for detail). The Streamlit pages are Streamlit's own multi-page mechanism (server-rendered Python, not a client-side router). The 4 portfolio prototypes are 4 entirely separate HTML files with no cross-linking.

---

## 5. Navigation Map

```text
Wathiq (as a whole project — three separate surfaces, not one navigable app)
│
├── Streamlit dashboard/ (run via `streamlit run dashboard/app.py`)
│   ├── "NDI-Sentinel" (main page)      — upload one DOCX evidence file, run assessment
│   └── "وثيق | Wathiq — نظرة عامة"     — aggregate DC-domain coverage & MQ analytics
│
├── wathiq_maturity_dashboard/index.html (open directly, or serve via local HTTP server)
│   ├── Overview                         — 3 top-line stats for the DC domain
│   ├── MQ Maturity Cards                — one card per Maturity Question (3, per sample data)
│   ├── Gap Identification                — filterable list of missing evidence per MQ
│   ├── Recommendations                   — generated text per MQ (from gaps only)
│   ├── Compliance (injected)             — DC_compliance.json specifications list
│   ├── Operational Excellence (injected) — separate simulated indicator set
│   ├── Evidence Repository (injected)    — evidence_repository_catalog.json browsable list
│   ├── Visual Evidence Repository (injected) — evidence_visual_catalog.json gallery w/ filters
│   └── Evidence Viewer (modal, opened from any evidence item) — up to 8+ sub-panels:
│       overview, assessment link, attachments, metadata, audit summary, validation,
│       lifecycle history, audit trail, version history, package summary, export
│       preview/package, AI-analysis-panel (all confirmed as "display only" in code
│       comments — no scoring/computation happens in any of them)
│
└── wathiq_portfolio_package/04_Platform_Mockups/ (4 independent static files, no nav between them)
    ├── SGSA_Auto_Classifier_DC.M.9_Prototype.html
    ├── SGSA_Data_Catalog_DC.M.7_Prototype.html
    ├── SGSA_DC.M.13_Continuous_Improvement_Prototype.html
    └── SGSA_DC.M.4_Continuous_Improvement_Prototype.html
```

Per-page purpose/data/actions (only for the two **real** interactive surfaces):

| Page | Purpose | Key info shown | Key actions | Expected user | Data source |
|---|---|---|---|---|---|
| Streamlit "NDI-Sentinel" | Assess one uploaded evidence document against its Evidence Code's requirement | Document metrics, text-assessment status/coverage%, supporting-evidence check, critical/medium findings, recommendations | Select Evidence Code, upload `.docx`, click "بدء التقييم", download generated Word report | A compliance officer assessing one document at a time | Live pipeline run (`src/services/assessment_pipeline_service.py`) |
| Streamlit "وثيق \| Wathiq — نظرة عامة" | Executive snapshot of already-assessed evidence across the whole DC domain | 4 KPI cards, PASS/PARTIAL/FAIL donut, per-MQ coverage bar chart | Read-only — no interactive actions | A manager/executive reviewing overall status | `data/assessment_results/DC_domain_progress_after_contradiction_fix.json`, `DC_results.json` |
| `wathiq_maturity_dashboard` | Explore MQ-level maturity, gaps, recommendations, and browse/manage evidence in depth | Everything in Section 6 below | Click MQ card (modal), filter gaps, filter/search visual evidence, "upload" evidence (browser-local simulation only — comments confirm no real file write occurs), export an evidence "package" (client-side ZIP built in JS) | UNCERTAIN — no persona is stated in code; the feature depth (audit trail, lifecycle, AI panel) suggests it targets the same compliance-officer/manager audience as the two Streamlit pages, but this is **INFERRED**, not stated | Its own local `data/*.json` (sample/simulated) |

---

## 6. Page/View Inventory

### `dashboard/app.py` ("NDI-Sentinel")
```text
Page: Evidence Assessment
Purpose: Analyze one uploaded DOCX evidence file against its selected Evidence Code
Current file: dashboard/app.py
Main components: Evidence Code selectbox, file uploader, "بدء التقييم" button, 4 summary
  metric cards, document-metrics row, text-assessment 3-column block, supporting-evidence
  block, findings tabs (critical/medium), recommendations tabs (high/medium priority,
  each an expander), Word-report download button
Data sources: data/evidence_catalog/*.json (Evidence Code list); live pipeline result via
  src/dashboard/assessment_dashboard_adapter.py
Actions: select code, upload file, run assessment, download report
Navigation: Streamlit sidebar (auto-generated) links to the second page
Important business information: "PASS"/"PARTIAL_PASS"/"FAIL" status vocabulary;
  "needs_human_review" flag; explicit note this uses no LLM/OCR/external API
```

### `dashboard/pages/1_نظرة_عامة_والنضج.py` ("وثيق | Wathiq — نظرة عامة")
```text
Page: Executive Overview + MQ Coverage Analytics
Purpose: Show aggregate, already-computed DC-domain evidence coverage — explicitly NOT an
  official SDAIA Compliance or Maturity score (both layers are "قيد الإعداد" / under
  construction per in-code comments)
Current file: dashboard/pages/1_نظرة_عامة_والنضج.py
Main components: topbar (brand + "DC — تصنيف البيانات · NDMO" badge), 4 KPI cards (1 hero +
  3 secondary), donut chart (Plotly) + legend list, bar chart (Plotly) + row-list with
  percentage pills, footer disclaimer note
Data sources: dashboard/data_layer.py -> data/assessment_results/*.json,
  data/evidence_catalog/dc_evidence_catalog.json
Actions: none (read-only page)
Navigation: Streamlit sidebar
Important business information: coverage_percentage is explicitly documented as NOT the
  same as an official compliance percentage; current_level/target_level columns exist in
  the data layer but are placeholders (pd.NA) pending src/scoring/maturity_level_engine.py
  being wired in
```

### `wathiq_maturity_dashboard/index.html` ("وثيق — منصة إدارة البيانات")
```text
Page: DC Domain Maturity Dashboard (single scrolling page + modal)
Purpose: Explore per-MQ maturity level, gaps to the next level, generated recommendations,
  and browse/inspect evidence in depth — explicitly scoped to MQ-level results only, no
  domain-level maturity average (footer: "لا يوجد متوسط نضج للمجال لعدم توفر قاعدة تجميع
  رسمية بين المتطلبات")
Current file: wathiq_maturity_dashboard/index.html (+ css/*, js/*)
Main components: see Section 7 (Component Inventory) — this page has by far the largest
  component set of the three surfaces
Data sources: wathiq_maturity_dashboard/data/*.json (6 files, its own local pool — see
  Section 8)
Actions: click MQ card -> modal; filter gaps by MQ; filter/search visual evidence by type/
  status/MQ; "upload" evidence (localStorage-only simulation, explicitly documented as not
  writing to disk); export one MQ's evidence as a ZIP (built client-side in JS, includes a
  hand-rolled CRC32/ZIP writer)
Navigation: none (single page)
Important business information: explicit, repeated in-code disclaimers that "coverage ≠
  maturity", that the Compliance Decision Layer is out of scope for this UI, and that this
  page's data source file is literally named "sample_maturity_report.json"
```

---

## 7. Component Inventory

Grouped by feature area, all `.wq-*` classes confirmed present in `wathiq_maturity_dashboard/css/components.css` (2,773 lines) and referenced from `js/app.js`:

| Group | Components (CSS classes) | Where used |
|---|---|---|
| Chrome | `.wq-header`, `.wq-theme-toggle` | Header, every page load |
| Overview | `.wq-note`, `.wq-stat` | `#overview` section |
| MQ Cards | `.wq-mq-card`, `.wq-level-badge`, `.wq-level-track`, `.wq-status-badge`, `.wq-detail-block`, `.wq-evidence-list`, `.wq-evidence-file-list`, `.wq-evidence-export-btn`, `.wq-evidence-file-error`, `.wq-export-mq-btn`, `.wq-attach-evidence-btn` | `#mq-cards` section, expands per-card |
| Gaps | `.wq-filter-btn`, `.wq-gap-card`, `.wq-empty-state` | `#gaps` section |
| Recommendations | `.wq-reco-card` (+`--complete`/`--pending` modifiers), `.wq-reco-actions` | `#recommendations` section |
| Modal (shared) | `.wq-modal-overlay`, `.wq-modal` | Evidence detail viewer, opened from many places |
| Upload (simulated) | `.wq-upload-field`, `.wq-upload-file-input`, `.wq-upload-hint`, `.wq-upload-error`, `.wq-upload-submit` | Injected upload modal |
| Compliance | `.wq-compliance-list`, `.wq-compliance-item` | Injected Compliance section |
| Operational Excellence | `.wq-opex-card`, `.wq-opex-badge-row`, `.wq-opex-badge`, `.wq-opex-list`, `.wq-opex-item`, `.wq-opex-meta`, `.wq-opex-disclaimer`, `.wq-opex-placeholder` | Injected Operational Excellence section |
| Evidence Repository | `.wq-evrepo-status-breakdown`, `.wq-evrepo-status-row`, `.wq-evrepo-list`, `.wq-evrepo-item` | Injected Evidence Repository section |
| Visual Evidence Gallery | `.wq-visual-evidence-section/empty/list/card/badge`, `.wq-visual-evidence-filters/filter-group/repo-list/search` | Injected Visual Evidence Repository section |
| Evidence Viewer (modal sub-panels) | `.wq-evidence-preview`, `.wq-evidence-version`, `.wq-evidence-status-badge`, `.wq-evidence-audit-summary`, `.wq-evidence-attachments/attachment-item`, `.wq-evidence-health-dashboard/card/status/filter`, `.wq-evidence-relationships/relationship-card/type/related-item`, `.wq-evidence-audit-trail/item`, `.wq-evidence-export/section`, `.wq-evidence-analytics/card`, `.wq-ai-evidence-panel`, `.wq-evidence-center/card`, `.wq-evidence-management-table` | Opened via `openEvidenceViewerModal()` |

**Not found anywhere in this project:** a dedicated charting library on the JS side (the static dashboard renders no charts — donut/bar charts exist only in the Streamlit page, via Plotly). No component framework (React/Vue) — every component above is a plain JS string-template function returning an HTML string, injected via `innerHTML`.

---

## 8. Data Flow

### Chain 1 — Streamlit "NDI-Sentinel" (live pipeline)
```text
User uploads .docx  →  dashboard/app.py::save_uploaded_file()
  →  src/dashboard/assessment_dashboard_adapter.py::prepare_dashboard_assessment()
  →  src/services/assessment_pipeline_service.py::run_assessment_pipeline()   [not traced further]
  →  Presentation Dict (summary_cards, document_metrics, text_assessment,
     supporting_evidence, findings, recommendations, word_report)
  →  dashboard/app.py::render_result() renders it with st.* calls
```

### Chain 2 — Streamlit "وثيق | Wathiq — نظرة عامة" (precomputed results)
```text
data/assessment_results/DC_domain_progress_after_contradiction_fix.json
data/assessment_results/DC_results.json
data/evidence_catalog/dc_evidence_catalog.json, DC_MQ_*_evidence.json
  →  dashboard/data_layer.py (load_domain_progress / load_mq_progress / load_evidence_results
     / build_risk_table — pure pandas read+reshape, no computation)
  →  pages/1_نظرة_عامة_والنضج.py::main() renders executive_df + mq_progress_df
     (evidence_df and risk_df are built by data_layer.py but NOT currently rendered by
     this page — CONFIRMED unused by this specific page, purpose elsewhere unconfirmed)
```

### Chain 3 — `wathiq_maturity_dashboard` (local sample data)
```text
wathiq_maturity_dashboard/data/sample_maturity_report.json          -> loadMaturityData()
wathiq_maturity_dashboard/data/compliance_models/DC_compliance.json  -> loadComplianceData()
wathiq_maturity_dashboard/data/operational_excellence_simulation.json -> getOperationalExcellenceData()
wathiq_maturity_dashboard/data/evidence_repository_catalog.json     -> loadEvidenceCatalog()
wathiq_maturity_dashboard/data/evidence_visual_catalog.json         -> loadEvidenceVisualCatalog()
wathiq_maturity_dashboard/data/uploaded_evidence.json (seed) + browser localStorage
  -> loadUploadedEvidenceSeed() / readUploadedEvidenceFromStorage()
  →  all fetched in parallel inside the DOMContentLoaded handler, each independently
     rendered by its own render*()/inject*() function (see Section 6 boot sequence)
```

**Data Source → Field → UI table** (sample, from confirmed schema reads):

| Data Source | File | Field | Used By | UI Location |
|---|---|---|---|---|
| `data/assessment_results/...` | `DC_domain_progress_after_contradiction_fix.json` | `domain_compliance_percentage` | `dashboard/data_layer.py::load_domain_progress()` | Streamlit hero KPI card ("متوسط تغطية الأدلة") |
| `data/assessment_results/...` | same file, `.mq_progress[]` | `compliance_percentage` per MQ | `load_mq_progress()` | Streamlit bar chart + row-list pills |
| `wathiq_maturity_dashboard/data/` | `sample_maturity_report.json` | `mq_results[].current_level`, `.level_name`, `.next_level_gaps`, `.evaluated_evidence` | `js/app.js::renderMqCards()`, `renderGapList()` | MQ cards, Gap Identification section |
| `wathiq_maturity_dashboard/data/` | `sample_maturity_report.json` | `mq_results[].current_level`, `.next_level_gaps`, `.level_name` | `js/recommendation_engine.js::generateRecommendation()` | Recommendations section |

---

## 9. Business Concepts

| Concept | Meaning (as used in code) | Where it appears |
|---|---|---|
| **Wathiq / وثيق** | The product/platform name | `wathiq_maturity_dashboard` (consistently), Streamlit page 2, `wathiq_portfolio_package` |
| **SGSA** | Fictitious client organization | `wathiq_portfolio_package` only — **not found** in `dashboard/` or `wathiq_maturity_dashboard` |
| **NDI-Sentinel** | An internal/legacy product name — **still live** in the Streamlit main page's title and browser tab | `dashboard/app.py` only (CONFIRMED, not cleaned up) |
| **NDI** | "المؤشر الوطني للبيانات" (National Data Indicator) — the overall framework this project targets, per `README.md` | `README.md`, project purpose statement |
| **NDMO** | Appears in a UI badge ("DC — تصنيف البيانات · NDMO") and in `wathiq_portfolio_package` as "المكتب الوطني لإدارة البيانات" | Streamlit page 2 badge, `wathiq_portfolio_package`. **Relationship between "NDI" and "NDMO" as used in this codebase is UNCERTAIN** — both appear as if referring to the national data governance authority/framework, but the code never explicitly states whether they are the same entity referenced two ways or two distinct things. Not resolved by this audit — flagged for clarification, not guessed. |
| **Evidence / Evidence Code** | A single document (e.g., `DC.M.2`) assessed against a requirement | Everywhere |
| **MQ (Maturity Question)** | A requirement grouping, e.g. `DC.MQ.1`; the domain "DC" currently has 3 MQs | `data/`, `wathiq_maturity_dashboard/data/`, both dashboards |
| **Domain** | Currently only "DC" (Data Classification / تصنيف البيانات) exists; code explicitly designed to be extensible to more domains later (`index.html`: "قابلة للتوسع لدعم مجالات إدارة بيانات متعددة") | `wathiq_maturity_dashboard`, `data/` folder naming |
| **Coverage % vs. Compliance % vs. Maturity Level** | Explicitly, repeatedly distinguished in code comments: *coverage* = internal text-matching heuristic (what exists today); *compliance* = official SDAIA-approved scoring (**not yet built** — "Compliance Decision Layer قيد الإعداد"); *maturity level* = the 0–5-ish scale from `src/scoring/maturity_level_engine.py` (exists as an engine but **not wired into either dashboard's live rendering** for domain-level scores) | Streamlit page 2 comments + footer; `wathiq_maturity_dashboard` footer |
| **Gap** | `next_level_gaps`: evidence codes still missing to reach the next maturity level for an MQ | `wathiq_maturity_dashboard` |
| **Recommendation** | Pure text reformatting of `current_level`/`next_level_gaps`/`level_name` — explicitly "computes nothing" | `js/recommendation_engine.js` |
| **Operational Excellence** | A separate, explicitly-simulated dataset/section, deliberately kept independent from Compliance ("قسمان مستقلان بالكامل") | `wathiq_maturity_dashboard` only |

**Wathiq = Product, SGSA = Organization** holds true **only within `wathiq_portfolio_package`**. In the two real application surfaces, SGSA does not appear at all, and one Streamlit page still displays a different, unrelated product name ("NDI-Sentinel") — this is a real, code-confirmed inconsistency, not a misunderstanding on the audit's part.

---

## 10. Current Design System

**Three separate, non-unified token sets exist.** None was invented for this report — each is quoted from its source file.

### A. `wathiq_maturity_dashboard/css/tokens.css` + `theme.css` (most complete)
| Token | Light | Dark |
|---|---|---|
| `--brand-primary` | `#1d2740` (`--primary-light`) | `#2ad1d6` (`--accent-teal`) |
| `--accent` | `#2ad1d6` | `#2ad1d6` (same both modes) |
| `--brand-secondary` | `#0fa3b1` | `#2ad1d6` |
| `--bg` | `#f5f9fe` | `#0b1220` |
| `--surface` / `--card` | `rgba(255,255,255,0.88)` | `#162235` (`--dark-card`) |
| `--surface-sunken` | `#f5f9fe` | `#111c2e` (`--dark-surface`) |
| `--surface-highlighted` | `rgba(255,255,255,0.96)` | `#1d3148` (`--dark-highlighted`) |
| `--text-primary` | `#374151` | `#e5e7eb` |
| `--text-soft` | `#6b7280` | `#94a3b8` |
| `--text-numbers` | `#06182c` | `#f8fafc` |
| `--border` | `rgba(15,60,100,0.1)` | `#1d3148` |
| `--status-success` | brand-primary | accent-teal |
| `--status-warning` | `#696969` (gray, WCAG-AA-fixed) | `#b8b8b8` (gray, WCAG-AA-fixed) |
| `--status-error` | `#262626` (gray, no red) | `#ffffff` |
| Radius | sm 8px / md 14px / lg 16px / xl 28px (modal) / card-file 20px (MQ cards) |
| Shadow | `--shadow-card: 0 8px 24px rgba(0,0,0,0.06)`, `--shadow-card-hover: 0 12px 28px rgba(0,0,0,0.08)` |
| Spacing | 4/8/12/16/20/24/32px (`--space-1`..`--space-7`) |
| Motion | `--ease-standard: cubic-bezier(.22,1,.36,1)`, durations 150/180/240ms |
| Font | `"Segoe UI","Tahoma","Arial",sans-serif` (both body and display) |

Note: `--status-warning`/`--status-error` are deliberately **neutral gray, not amber/red** — an explicit design decision documented in the CSS comments, with WCAG AA contrast-ratio fixes noted for two specific gray values.

### B. `dashboard/pages/1_نظرة_عامة_والنضج.py` (hardcoded Python constants, single light palette only)
`PRIMARY_BLUE #3D63DD`, `PRIMARY_BLUE_DEEP #2647B0`, `SURFACE_WHITE #FFFFFF`, `TEXT_DARK #1A1F36`, `TEXT_GRAY #8A94A6`, `BORDER_LIGHT #E7EAF3`, `STATUS_GREEN #34A853`, `STATUS_RED #EA4335`, `STATUS_ORANGE #F4A825`, `PAGE_BG #F4F6FC` — explicitly sourced from "a provided Google Drive reference screenshot" per the file's own docstring, not derived from `wathiq_maturity_dashboard`'s tokens.

### C. `wathiq_portfolio_package` prototypes (previously documented, summarized here)
`--brand:#1B2A4E`, `--accent:#29C79A` — identical across its 4 files, duplicated per-file rather than shared.

**These three systems do not share a single color anywhere.** Unifying them (or picking one as canonical) was explicitly out of scope for this audit and is not proposed here.

---

## 11. Light/Dark Theme

| Surface | Light? | Dark? | Toggle mechanism | Notes |
|---|---|---|---|---|
| `wathiq_maturity_dashboard` | Yes | Yes | Working button (`#wq-theme-toggle`), `data-theme` attribute, `localStorage["wathiq-theme"]`, applied pre-paint via inline `<script>` in `<head>` (CONFIRMED via `js/theme.js`) | **`css/theme.css`'s own top comment says "no toggle UI exists"** — this is stale documentation contradicted by the actual, working code. Flagged as a real finding, not resolved. |
| Streamlit "NDI-Sentinel" | Yes (Streamlit default + RTL override) | Not found | None | No dark-mode CSS present in `app.py` |
| Streamlit "وثيق \| Wathiq" | Yes (hardcoded palette) | Not found | None | Single palette only, no `prefers-color-scheme` or toggle |
| `wathiq_portfolio_package` prototypes | Yes | Yes | `prefers-color-scheme` + manual `data-theme` toggle (previously documented) | Consistent with `wathiq_maturity_dashboard`'s approach in spirit, different token values |

---

## 12. RTL/Arabic Support

- `wathiq_maturity_dashboard/index.html`: `<html lang="ar" dir="rtl">` — native, CONFIRMED.
- Both Streamlit pages: Streamlit itself has no native RTL mode, so **both pages inject a global CSS override** (`html, body, [class*="css"] { direction: rtl; text-align: right; }`) — a workaround, not a framework feature. CONFIRMED in both `app.py` and the page file.
- `README.md` states the project is "Arabic-First" end to end: UI, reports, recommendations, UTF-8 storage; `arabic-reshaper`/`python-bidi` used **only** for PDF/Word/PowerPoint generation, explicitly **not** in the database, ChromaDB, RAG, or JSON files.
- No mixed-direction or numeral-alignment issues were specifically tested in this pass (would require rendering in a browser, which this read-only audit did not perform) — **UNCERTAIN**, not claimed as verified.

---

## 13. Responsive Behavior

**`wathiq_maturity_dashboard` — the only surface with explicit, real breakpoints (CONFIRMED from `layout.css`):**

| Breakpoint | Behavior |
|---|---|
| Default (mobile) | MQ card grid: 1 column |
| `min-width: 640px` | MQ card grid: 2 columns |
| `min-width: 1024px` | MQ card grid: 3 columns (explicitly capped at 3, not 4 — in-code comment explains this was a deliberate trade-off against a fixed card-width spec of 320–360px within the 1180px max container) |
| `max-width: 640px` | Header bar stacks vertically |
| Content container | `max-width: 1180px` |
| Gap list | `repeat(auto-fill, minmax(280px, 1fr))` |
| Recommendation grid | `repeat(auto-fit, minmax(300px, 1fr))` |

**Streamlit pages:** layout relies on Streamlit's own built-in responsive column system (`st.columns(4)`, etc.) — this project adds no custom breakpoint CSS for it. Whether Streamlit's default responsiveness is adequate was **not tested in a browser this pass — UNCERTAIN**.

**`wathiq_portfolio_package` prototypes:** previously documented as having no dedicated mobile-width layout below ~700px (known, disclosed gap from prior sessions).

---

## 14. Component Reuse / Duplication

| Pattern | Classification | Evidence |
|---|---|---|
| `wathiq_maturity_dashboard`'s CSS (5 files: tokens/theme/layout/components/animations) | **SHARED** | One stylesheet set, loaded once, used by the single `index.html` — no duplication within this surface |
| `wathiq_portfolio_package`'s 4 prototypes, each repeating its own ~240-line design-token/component CSS block | **DUPLICATED** | Previously documented; re-confirmed not touched since |
| The 3 separate color-token systems (Section 10) across the 3 surfaces | **PAGE-SPECIFIC / NOT SHARED** | No file references another surface's tokens |
| `js/app.js`'s ~150 render/helper functions | Mostly **PAGE-SPECIFIC** (each targets one section), but a few (`escapeHtml`, `statusBadgeAttr`, `statusLabelAr`) are genuinely **SHARED** utilities reused across many render functions | Grep-confirmed multiple call sites |

---

## 15. UI/UX Current-State Findings

Findings are classified per the requested taxonomy; none were fixed or acted upon.

| Finding | Classification |
|---|---|
| `dashboard/app.py` displays "NDI-Sentinel" while its sibling page displays "وثيق \| Wathiq" | **FUNCTIONAL** (brand identity, not a rendering bug) |
| `theme.css`'s top comment claims no dark-mode toggle exists, while a working one does | **QUALITY** (stale documentation, not a runtime bug) |
| Three unrelated color-token systems across three surfaces | **QUALITY** (consistency debt, not broken) |
| `wathiq_maturity_dashboard` requires an HTTP server (fails silently-then-with-error under `file://`, per its own explicit `renderLoadError()` handling) | **EXPECTED** — the app itself documents and handles this case gracefully with a clear Arabic error message; not a defect |
| Evidence "upload" and evidence "export ZIP" in `wathiq_maturity_dashboard` are client-side-only simulations (no real file write, confirmed in comments) | **EXPECTED** (explicitly by design, clearly commented, not hidden) |
| `evidence_df`/`risk_df` are built by `dashboard/data_layer.py` but not rendered by the one Streamlit page read this pass | **UNKNOWN** — may be used elsewhere (a third page not yet built, or a script) — not confirmed either way |

No `BLOCKER` was found in either live application during this static-code read-only pass (no in-browser/runtime testing was performed, per the read-only mandate).

---

## 16. Important Constraints

- **No backend HTTP API exists.** `src/api/` is an empty placeholder. Any future frontend cannot assume a REST endpoint is available today.
- **No database.** All persistence is JSON files on disk (`data/`, `wathiq_maturity_dashboard/data/`) plus a ChromaDB vector store (`vector_db/`) for RAG only.
- **No React/Vue/Next/Tailwind anywhere in this project.** `wathiq_maturity_dashboard` is vanilla HTML/CSS/JS; `dashboard/` is server-rendered Python (Streamlit).
- **Two of the three UI surfaces are not interchangeable data-wise** — `wathiq_maturity_dashboard` reads its own local sample data, entirely separate from the live `data/assessment_results/` that the Streamlit "Overview" page reads. A redesign that assumes one data source feeds both would be incorrect.
- **The Compliance Decision Layer and Maturity Calculation Layer are explicitly unfinished**, per comments in both the Streamlit page and `wathiq_maturity_dashboard`. Any UI redesign should preserve — not remove — the existing disclaimers that distinguish "coverage" from official "compliance"/"maturity", since this is a deliberate, repeated business decision in the current code, not an oversight.

---

## 17. LOVABLE IMPLEMENTATION CONTEXT

### A. Project Identity
- **Product name:** Wathiq / وثيق (per `README.md`, `wathiq_maturity_dashboard`, and one Streamlit page) — **but** the other Streamlit page currently shows "NDI-Sentinel" instead (a real inconsistency to be aware of, not silently assumed away).
- **Organization:** SGSA is a *fictitious* organization used only inside the separate `wathiq_portfolio_package` evidence-demo package — it is **not** the real product's user-facing organization concept anywhere else.
- **Purpose:** an Arabic-first system helping Saudi government entities track compliance/maturity against NDI (National Data Indicator) requirements, by analyzing evidence documents, detecting gaps, and generating recommendations/reports (per `README.md`).
- **Domain scope today:** one domain only — DC (Data Classification / تصنيف البيانات), across 3 Maturity Questions.
- **Target users:** compliance officers (uploading/assessing individual evidence) and managers/executives (reviewing aggregate coverage) — **INFERRED** from the two Streamlit pages' distinct workflows, not stated explicitly as personas anywhere in code.

### B. Current Architecture
- **Frontend technologies in use today:** (1) Streamlit (Python, server-rendered) for `dashboard/`; (2) vanilla HTML/CSS/JS for `wathiq_maturity_dashboard/`. No other frontend framework exists.
- **Entry points:** `dashboard/app.py` (`streamlit run`), `wathiq_maturity_dashboard/index.html` (needs a local HTTP server, not `file://`).
- **Navigation:** Streamlit's built-in multi-page sidebar (2 pages); `wathiq_maturity_dashboard` is a single scroll + one shared modal, no router.
- **Data sources:** two separate JSON pools (Section 8) — do not assume they are, or should be, merged without asking.

### C. Pages
See Section 6 for the full per-page breakdown (purpose/components/data/actions/navigation/business info) for all 3 real pages.

### D. Design System
See Section 10 for all three literal token sets. **`wathiq_maturity_dashboard`'s token architecture (Section 10-A) is the most complete and best-structured of the three** — it is the only one with a documented primitives→semantic→component layering, explicit dark-mode support, and accessibility-driven color choices.

### E. Components to Preserve Functionality Of
From Section 7: MQ maturity card (with expand/level-track/evidence-list), gap card + filter toolbar, recommendation card (complete/pending states), the shared evidence-detail modal and its 8+ sub-panels, evidence upload flow (even if currently simulated), evidence export-to-ZIP, visual evidence gallery with filters/search, theme toggle. On the Streamlit side: the evidence-code selector + file uploader + assessment-result renderer (`app.py`), and the KPI-card + donut + bar-chart executive overview (`pages/1_...py`).

### F. Data Contracts (field names that should not change without updating every consumer)
- `mq_id`, `current_level`, `level_name`, `next_level`, `next_level_name`, `next_level_gaps`, `evaluated_evidence` (from `sample_maturity_report.json`, consumed by `js/app.js` and `js/recommendation_engine.js`).
- `domain_compliance_percentage`, `assessment_completion_percentage`, `pass_count`, `partial_pass_count`, `fail_count`, `needs_human_review_count`, `total_evidence`, `mq_progress[]` (from `DC_domain_progress_after_contradiction_fix.json`, consumed by `dashboard/data_layer.py`).
- Status vocabulary used throughout: `PASS` / `PARTIAL_PASS` / `FAIL` (and `UNKNOWN` / `FILE_READ_FAILED` / `NOT_PROVIDED` in the adapter's error paths) — this exact 3-way (plus edge-case) status set recurs across both real UIs and should not be silently reduced to a binary pass/fail.

---

## 18. Confirmed Facts vs. Inferences

| # | Statement | Status |
|---|---|---|
| 1 | `dashboard/app.py` displays "NDI-Sentinel" as its title | **CONFIRMED FROM CODE** |
| 2 | `dashboard/pages/1_نظرة_عامة_والنضج.py` displays "وثيق \| Wathiq" | **CONFIRMED FROM CODE** |
| 3 | `wathiq_maturity_dashboard` reads only its own local sample/simulated JSON, not the root `data/` folder | **CONFIRMED FROM CODE** (grep of every `fetch()` call and its URL) |
| 4 | `src/api/` has no real API implementation | **CONFIRMED FROM CODE** (file is empty except `__init__.py`; no Flask/FastAPI/Django import anywhere in `src/`) |
| 5 | `theme.css`'s "no toggle exists" comment is stale/incorrect | **CONFIRMED FROM CODE** (contradicted by working `js/theme.js`) |
| 6 | Real breakpoints are 640px/1024px, 1/2/3-column MQ grid | **CONFIRMED FROM CODE** |
| 7 | `wathiq_maturity_dashboard` is the intended visual reference for a future redesign | **INFERRED** (reasoning given in Section 6, not stated anywhere in the project) |
| 8 | Target users are compliance officers + managers | **INFERRED** (from workflow shape, no persona docs found) |
| 9 | "NDI" and "NDMO" refer to the same or different things | **UNCERTAIN** — not resolved |
| 10 | Purpose of the 20 root-level `_mk_dc_*.py`/`_patch_dc_*.py` scripts | **NOT FOUND / NOT INVESTIGATED** this pass |
| 11 | Whether `evidence_df`/`risk_df` (built by `data_layer.py`) are consumed anywhere | **NOT FOUND** this pass |
| 12 | RTL/mixed-content rendering correctness in an actual browser | **UNCERTAIN** — not tested (static code read only) |

---

## 19. Risks / Unknowns

- **Brand inconsistency risk:** any Lovable prompt built from this project must explicitly decide what to do about the live "NDI-Sentinel" title — carrying it forward silently would perpetuate a known, real inconsistency; removing it without flagging the decision would be an invented assumption.
- **Two disconnected data sources:** a redesign that visually merges `dashboard/`'s live-data views and `wathiq_maturity_dashboard`'s sample-data views must not imply they already share a backend — they don't, today.
- **Root-level `_mk_dc_*.py`/`_patch_dc_*.py` scripts and their relationship to `reports/`'s 23 generated DOCX files were not investigated** — unknown whether they're active tooling or historical/one-off scripts.
- **No runtime/browser verification was performed** (read-only, static-analysis mandate) — CSS computed layout, actual RTL rendering, and JS runtime behavior are all based on source reading, not observation.

---

## 20. READ-ONLY Integrity Verification

Whole-project baseline (excluding `.git`) captured before this audit's file-reading pass began, and independently re-verified after this report file was written:

| Metric | Value |
|---|---:|
| Total files (before) | 463 |
| Total files (after) | 464 |
| Files added | **1** — this report itself, `Wathiq_Project_Structure_UIUX_Context_Report.md`, written per the task's explicit instruction to deliver the final report as a root-level Markdown file |
| Files removed | 0 |
| Files renamed | 0 |
| Files modified (of the original 463) | **0** |

Every one of the 463 pre-existing files was independently re-hashed (SHA-256) after this report was written and confirmed byte-identical to its pre-audit state. The single added file is this report; no other file, generated output, or temporary artifact was created anywhere inside the project.

**READ-ONLY AUDIT COMPLETE — PROJECT UNMODIFIED.**
