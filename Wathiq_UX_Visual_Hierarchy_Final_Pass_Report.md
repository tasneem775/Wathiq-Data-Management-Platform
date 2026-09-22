# Wathiq — Visual & Perceptual Hierarchy Pass

Short report, as requested. This pass looked at actual computed visual weight (font-size/weight, reading order, box treatment) rather than DOM order or code correctness, since those were already handled in prior passes.

## المشكلة UX

1. **The first thing a first-time visitor read on the whole site was not a result.** In the Overview section, the DOM order was: title → 2 sentences of hint text → a bordered, icon-bearing note box (explanatory/caveat text) → *then* the 3 KPI numbers that actually answer "أين نحن الآن؟". The note box has its own border + colored accent bar + icon, so it visually competed with (and preceded) the actual answer. A user had to read past a disclaimer before seeing any number.
2. **Compliance and Operational Excellence — already moved to a supplementary position after the core journey in the prior pass — still used the exact same 23px/700 section-title styling as Overview, MQ Cards, Evidence, Gaps, and Recommendations.** Position had changed, but visual loudness hadn't: scrolling down, every section still shouted at the same volume, so "this is core" vs "this is supplementary" wasn't legible from typography alone, only from position + the small tier-divider label.

## ماذا نفّذت

1. **`index.html`**: moved the `<div class="wq-note">…</div>` block to *after* `<div class="wq-overview-grid">` instead of before it. Same content, same element, same id — pure reorder. **`css/components.css`**: swapped `.wq-note`'s `margin-bottom: 22px` for `margin-top: 22px` since it now trails the stats instead of leading them (otherwise it would've sat flush against the cards with no gap).
2. **`js/app.js`**: added a `wq-section--supplementary` class to the `<section>` tags built by `injectComplianceSection()` and `injectOperationalExcellenceSection()` only. **`css/layout.css`**: added `.wq-section--supplementary .wq-section__title { font-size: 18px; font-weight: 600; }` (down from 23px/700) — same color, no new token, just less loud. Nothing else about those two sections changed.

## لماذا

Both changes follow the same principle you stated: primary information first, hierarchy expressed visually not just positionally. The stats-before-note reorder makes the "5 second answer" actually arrive in 5 seconds instead of after two sentences and a disclaimer box. The quieter title on the two supplementary sections makes the Primary/Secondary vs. Tertiary split (which the prior pass already established *positionally*) also read correctly at a glance while scrolling, without touching the five core-journey sections at all — I deliberately did not resize Overview/MQ Cards/Evidence/Gaps/Recommendations against each other, since all five are genuinely part of the one core story (Current State → Maturity → Evidence → Gaps → Recommendations) and I had no way to visually verify a broader resize wouldn't misjudge relative importance among them.

## ما لم أغيّره (ولماذا)

- **Did not touch the note's own content or remove it** — it's a real, data-driven disclaimer (`data.architectural_note`); only its position changed.
- **Did not resize section titles for MQ Cards / Evidence / Gaps / Recommendations** — these are all core-journey chapters, not supplementary; differentiating among them further would be a judgment call I can't safely make without seeing it rendered.
- **Did not add a "kicker" label to MQ Cards/Gaps/Recommendations** (the way Evidence Repository/Visual Evidence Repository already have one) — those two kickers exist specifically because two adjacently-named sections needed disambiguating; MQ Cards/Gaps/Recommendations have no such naming collision, so adding labels there would be decoration without a real problem to solve.
- **Did not add a CTA button near Recommendations** — there's no real click-target to wire up without inventing a business action, which is out of scope.
- No backend, scoring, maturity/recommendation logic, data contract, JSON structure, or field name was touched — confirmed via `git status` scoped to the relevant directories (only `wathiq_maturity_dashboard/index.html`, `css/components.css`, `css/layout.css`, `js/app.js` changed this pass).

## الملفات المعدلة

- `wathiq_maturity_dashboard/index.html`
- `wathiq_maturity_dashboard/css/components.css`
- `wathiq_maturity_dashboard/css/layout.css`
- `wathiq_maturity_dashboard/js/app.js`

## Verification — STATIC ONLY

`node --check js/app.js` passes; CSS brace balance across all 5 CSS files is balanced; `var(--token)` resolution shows 0 dangling references; `<section>` open/close tag count in `index.html` still matches (4/4) after the reorder; `git status` confirms only the 4 files above changed. **I have not opened this in a browser at any point in this engagement — I cannot confirm how the reordered Overview or the quieter supplementary titles actually look or feel, only that the markup/CSS is structurally sound.**

## ما يحتاج اختبارًا يدويًا

- Whether the Overview now genuinely reads as "numbers first" at a glance, and whether the note box feels like a natural footnote in its new position rather than orphaned.
- Whether 18px/600 is the right amount of de-emphasis for the Compliance/Operational Excellence titles — too subtle and it won't register, too different and it might look broken/inconsistent rather than "quieter." This was a judgment call made without rendering it.
- The full scroll-through in both themes and at mobile width, which no pass in this engagement has actually seen.

Not marking this READY — that call should follow an actual look, not another static pass.
