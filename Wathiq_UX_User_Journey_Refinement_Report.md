# Wathiq — User Journey & Information Architecture Refinement

Short report per instructions — UX findings and what was actually implemented, not a theoretical proposal.

## المشكلة UX التي وجدتها

The DOM/visual order didn't match the user's mental journey. The page rendered 8 major sections in this order: **Overview → Compliance → Operational Excellence → Evidence Repository → Visual Evidence Repository → MQ Cards → Gaps → Recommendations**. Two consequences:

1. **Two sections unrelated to the maturity story (Compliance, Operational Excellence — both explicitly documented in their own code comments as separate, prototype/simulation layers, not part of official maturity calculation) sat between "Overview" and "MQ Cards"**, interrupting the story before the user even saw a maturity result.
2. **Both Evidence sections appeared before MQ Cards**, so "here's the proof" showed up before "here's the result being proven" — backwards from Current State → Maturity → Evidence → Gaps → Recommendations.
3. **Inside the Visual Evidence Repository specifically**: three separate KPI/analytics panels (Evidence Health Dashboard alone renders 6 tiles) sat above the search bar and the actual evidence list — for a dataset I confirmed at 6 total items (`data/evidence_visual_catalog.json`). That's roughly one summary tile per item, shown before the items themselves.

All of this is independent of whether any individual card/badge/color was "correct" — which is why the prior four passes (all of which were real, necessary fixes) didn't resolve the "scattered" feeling: the problem was sequencing, not styling.

## ماذا غيّرت فعليًا

1. **Reordered 4 section-injection points in `js/app.js`** (`injectComplianceSection`, `injectOperationalExcellenceSection`, `injectEvidenceRepositorySection`, `injectVisualEvidenceRepositorySection`) — each now targets a different DOM anchor (`afterend` of a specific section) instead of all four targeting `beforebegin(#mq-cards)`. **No render function, no data field, no business logic touched** — only *where* each section's already-existing HTML gets inserted.
2. **New final order**: Overview → **MQ Cards (Maturity)** → **Evidence Repository → Visual Evidence Repository (Evidence)** → Gaps → Recommendations → **[tier divider] → Compliance → Operational Excellence (Additional Information)** → Footer.
3. **Added `.wq-tier-divider`** (`css/layout.css`) — a plain thin rule + small muted label ("معلومات إضافية") marking the transition from the core journey to supplementary content. No new icon, no color, no card — deliberately quiet.
4. **Wrapped the Visual Evidence Repository's 3 pre-list KPI panels** (Health Dashboard, Analytics, Center) in a `<details>` disclosure, **collapsed by default** — unlike the filter bar (kept open by default from the prior pass, since filtering is an immediate action; these three are investigative/meta information about the evidence, not the evidence itself). Reused the exact same `.wq-evidence-more-details` component already shipped — no new visual language. Zero change to `renderEvidenceHealthDashboard()`/`renderEvidenceAnalytics()`/`renderEvidenceCenter()` — they still write to the same three `id`s, which still exist in the DOM, just inside a collapsed wrapper.

## لماذا غيّرته

Grounded in the actual data, not assumption: I read `data/sample_maturity_report.json` and `data/evidence_visual_catalog.json` before deciding anything. 3 MQs, 18 evaluated-evidence entries, 6 gap entries, 6 visual-evidence items. At this scale, per-section card/list density was **not** the dominant problem (3 MQ cards and ~6 gap cards aren't "overload" by any reasonable measure) — the scatter came from (a) page-level sequencing fighting the natural question order, and (b) one specific spot (Visual Evidence Repository) where meta-analytics-about-6-items outweighed the 6 items.

## ماذا تعمدت عدم تغييره (وسبب كل واحد)

- **Overview's 3 stats** (evaluated count / completion status / domain maturity level) — reviewed for a "hero stat" treatment, then checked the actual data: `domain_level_calculation` is genuinely `"NOT_AVAILABLE"` (no official cross-MQ aggregation rule exists yet). Making that stat visually dominant would spotlight an absence, not a result — worse, not better. Left as three equal-weight stats, which is already correct at n=3.
- **Plain Evidence Repository's 23-item list** — no search/filter exists there. Adding one would mean writing new interactive filtering logic, which starts to cross from "presentation" into new frontend functionality I wasn't asked to build, and the Visual Evidence Repository (immediately adjacent, one step later in the journey) already provides full search + 13 filter groups. Left as a fully-visible list, consistent with "if the user needs it to understand current state, show it" — this section's whole job is showing the official evaluated-evidence record.
- **MQ Card internal structure** — re-checked against this pass's own journey questions (What/Status/Level/Evidence/Next-step); already confirmed correct in a prior pass (level number is the dominant element, ID de-emphasized, detail panel is progressive disclosure). No change needed.
- **Primary CTA / button competition** — checked for "5 buttons that all look primary"; found none. The only filled/bold-primary-styled button in the whole app is the single upload-submit button inside its own modal. Everything else is intentionally secondary-weight (outline pills), so there's no competing-CTA problem to fix.

## الملفات التي تم تعديلها فقط

- `wathiq_maturity_dashboard/js/app.js`
- `wathiq_maturity_dashboard/css/layout.css`

No other file was touched in this pass. No backend, Python, scoring, RAG, compliance logic, data contract, JSON structure, or field name was changed. Nothing was deleted — Compliance and Operational Excellence are still fully present and fully functional, only relocated and given a quieter entry point.

## Verification — **STATIC VERIFICATION ONLY**

Actually checked: `node --check js/app.js` (pass), CSS brace balance across all 5 CSS files (all balanced), `var(--token)` resolution (102 used / 121 defined / 0 dangling), new class references (`wq-tier-divider`, `wq-tier-divider__label`) confirmed present in CSS, and `git status`/`git diff` scoped to the relevant directories confirming only the 2 files above changed (plus the same pre-existing, unrelated `src/scoring`/`src/evidence_assessment` working-tree state from before any UI/UX pass, still untouched). I also confirmed structurally that the reorder is safe: no CSS sibling-combinator selectors (`~`, `+`) reference any of the reordered section IDs, and no JS uses `nextElementSibling`/`previousElementSibling`/DOM-position-dependent logic anywhere in `app.js` — every render/event-binding call is `getElementById`-based, so it doesn't care where in the DOM its target sits.

**No browser automation tool is available in this environment.** I have not seen this reorder rendered, scrolled through, or navigated on any device size, in either theme. The logic above (anchor/`insertAdjacentHTML` order tracing) is correct by code reading, not by having watched it happen.

## أي شيء ما زال يحتاج اختبارًا بصريًا يدويًا

- **The single most important thing to check by eye**: scroll through the page top to bottom in an actual browser and confirm the section order really reads as Overview → MQ Cards → Evidence Repository → Visual Evidence Repository → Gaps → Recommendations → [divider] → Compliance → Operational Excellence → Footer, and that the `.wq-tier-divider` reads as a clear, quiet "you've left the core story" cue rather than looking like a stray line.
- Open the Visual Evidence Repository's new collapsed disclosure and confirm the Health/Analytics/Center panels still render correctly once expanded (their render functions were never touched, but the wrapping was — worth a click-through).
- Confirm the reorder looks correct in both light and dark themes and at mobile width (no code-level reason it wouldn't, since nothing about the sections' own internal responsive CSS changed — but unverified visually).

## Final Verdict

**READY WITH MINOR POLISH** — same standing as the prior pass, now with the added journey-sequencing fix this report covers. The one open item is the same as always: nothing here has been seen rendered.
