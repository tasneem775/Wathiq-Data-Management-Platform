# Wathiq — Sidebar App Shell (Long Single-Page → Multi-View Platform)

Unlike every prior UI/UX pass in this engagement, this one was **actually verified in a real browser** (Playwright driving headless Microsoft Edge against a local static server), not just statically analyzed. Screenshots and DOM/geometry assertions were captured at multiple viewports, in light and dark mode. One real bug was found this way and fixed. Details below.

## What changed

The page is no longer a long single scroll containing all 8 sections at once. It's now an app shell: a right-side sidebar (RTL-native) + header + a main content area that shows exactly one section ("view") at a time, matching the requested navigation groups:

- **الرئيسية** → نظرة عامة
- **النضج** → متطلبات النضج
- **الأدلة** → مستودع الأدلة، الأدلة المرئية
- **التحسين** → الفجوات، التوصيات
- **معلومات إضافية** (visually and typographically quieter) → Compliance، Operational Excellence

Clicking a nav link updates `location.hash`, and a small router (`showView()` in `js/app.js`) hides every section except the target one via the native `hidden` attribute — no section's internal HTML, ids, or render function changed. Every existing render function (`renderOverview`, `renderMqCards`, `renderEvidenceRepository`, etc.) still writes to the exact same DOM ids it always did.

- **Desktop (>900px)**: sidebar fixed on the right, always visible.
- **Tablet + Mobile (≤900px)**: sidebar becomes an off-canvas drawer (slides in from the right, scrim behind it, closes on scrim click / Escape / navigating). I deliberately used one drawer breakpoint instead of a third "icon-only collapsed" tablet state, since I had no way to visually tune that intermediate state — documented as a simplification, not an oversight.
- Header now shows the **current page name** (dynamic, updates on navigation) instead of a static app title, plus the existing domain-context subtitle and theme toggle — brand identity moved to the sidebar, which is where it's requested.
- The `wq-tier-divider` element from the previous (single-scroll) pass was removed — it existed to mark "you've left the core story" mid-scroll, which is meaningless now that Compliance/Operational Excellence are their own separate nav destinations. Superseded by the sidebar's own "معلومات إضافية" group.

## Real verification performed (not claimed — actually done)

- Started a local static server, drove it with Playwright/Edge headless.
- **Confirmed only one section is unhidden at a time**: initial load shows only `overview`; clicking گar→`gaps`→`recommendations`→`compliance` correctly hides all others and shows only the target, every time (`document.querySelectorAll('main section.wq-section')` checked programmatically after each click).
- **Confirmed page title + active nav state update correctly** on every navigation.
- **Confirmed zero horizontal overflow** at 375/390/768/1024/1440px (`document.documentElement.scrollWidth` measured directly, not eyeballed).
- **Confirmed the mobile drawer**: closed by default (`translateX` pushes it fully off-canvas), opens via the hamburger button, closes automatically after clicking a nav link inside it.
- **Confirmed dark mode** renders correctly — sidebar, active nav indicator (teal, not filled background), MQ cards, status icons all checked via screenshot.
- **Confirmed the Evidence Viewer modal** (from an earlier pass) still opens correctly, still gets the wide-modal class, and still shows Audit Summary → Overview → Assessment Relation in the same order as before — nothing about the modal logic was touched by this pass, and this confirms it wasn't broken by it either.
- **Confirmed keyboard focus-visible rings render correctly** (visibly, in the screenshot) on sidebar nav links.
- Only console message on load: a `favicon.ico` 404 — the browser's automatic favicon request, unrelated to any change made here.

### One real bug found and fixed this way
At 768px (tablet), four Evidence Repository rows whose status text is long ("غير مُقيّم في المصدر الحالي") had their status badge overflow **past the left edge of the page** (confirmed via `getBoundingClientRect()`: negative X position). This is a **pre-existing bug**, not something this pass introduced — the container/list-item code was never touched by any pass before this one. Root cause: `.wq-evrepo-item__meta` and its children had no `min-width: 0`, so flexbox's default `min-width: auto` prevented the long badge text from ever wrapping, and it overflowed instead. Fixed by adding `min-width: 0` (+ `max-width: 100%` as a hard backstop) to `.wq-evrepo-item__meta`, `.wq-evrepo-item__field`, and `.wq-status-badge` — re-tested and confirmed fixed (badge now wraps cleanly onto its own line inside the card, verified both by geometry and screenshot).

## Files modified
- `wathiq_maturity_dashboard/index.html`
- `wathiq_maturity_dashboard/css/layout.css`
- `wathiq_maturity_dashboard/css/components.css`
- `wathiq_maturity_dashboard/js/app.js`

## Files untouched
No backend, Python logic, scoring, maturity/compliance calculation, recommendation engine, RAG, data contract, JSON schema, or field name was touched. `git status` scoped to the relevant directories confirms only the 4 files above changed this pass (plus the same pre-existing, unrelated `src/scoring`/`src/evidence_assessment` working-tree state that has predated every UI/UX pass in this engagement and was never opened for writing).

## What I did not do
- Did not add search, analytics, charts, KPIs, notifications, a user profile, or settings pages — none of that was requested or existed before.
- Did not add a third "collapsed icon-rail" sidebar state for tablet — drawer covers tablet + mobile, a deliberate simplification.
- Did not add a breadcrumb — with a flat one-level sidebar (no nested pages), a breadcrumb would just repeat the sidebar's own group label, so it was judged unnecessary rather than added to "fill the header."
- Did not implement a full focus-trap inside the mobile drawer (Escape-to-close and visible focus rings exist, but focus doesn't get programmatically moved into/out of the drawer on open/close) — consistent with the existing modal's own level of keyboard handling elsewhere in this app, not a new gap introduced here.

## Remaining risk
Verification this pass was real (actual rendering, actual clicks, actual screenshots) but not exhaustive — I did not click through every one of the 8 views, did not test every interactive control inside every view (filters, uploads, exports), and did not test on an actual mobile device or a real Chrome/Safari build (only headless Edge). Recommend a normal manual pass before presenting this to a stakeholder, but this is now a meaningfully more confident starting point than any prior pass in this engagement.
