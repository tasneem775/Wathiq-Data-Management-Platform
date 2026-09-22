# Wathiq — Visual Refinement Pass (Token-Level)

Third pass. This round computed actual WCAG contrast ratios from the token hex values (Node script, math shown below) instead of relying on visual impression, since no browser is available. Fixes applied at the token layer only, per instruction — no ad-hoc colors added to components.

## A — Problems found (measured, not assumed)

1. **Light-mode cards are mathematically near-flat**: `--bg` vs `--surface` = **1.05:1** contrast (surface is 88%-opacity white over an already near-white background); the card's default `--border-subtle` vs surface = **1.15:1**. With `--shadow-card` also very faint (0.06 alpha), cards had almost nothing giving them visual lift. Confirms the "cards تبدو مسطحة" concern with numbers.
2. **Light-mode focus-visible ring fails WCAG 1.4.11**: `--accent` (teal) on white/surface = **1.88:1**, below the 3:1 minimum for non-text UI indicators. This affected 8 separate `:focus-visible` rules across the whole file (theme toggle, MQ card, filter buttons, modal close, accordion summary, evidence viewer buttons, search input, etc.) — every keyboard-focus outline in light mode was under-contrast. Dark mode was already fine (accent on dark bg = 9.98:1).
3. **`--border-focus` semantic token existed but was dead** — defined in `theme.css` for both modes, never actually consumed anywhere in `components.css` (all 8 focus rules hardcoded `var(--accent)` directly instead).
4. Checked and found **not** to be problems (no change made): accent-color usage is proportionate (13 occurrences in ~3,000 lines, zero use as text color — all borders/backgrounds); disabled states exist on the two button types that need them; empty-state styling is reasonable (dashed border, centered, muted).
5. **`--border-strong-light` measured at 1.59:1** against surface (below the 3:1 UI-boundary guideline) — used in 19 places, a mix of real interactive-hover boundaries and purely decorative dashed dividers (the latter aren't subject to that WCAG criterion). See §C — flagged, not changed.

## B — Implemented

- `tokens.css`: `--shadow-card` 0.06→**0.09** alpha, `--shadow-card-hover` 0.08→**0.13** alpha. Same hue/spread, just enough to read as elevation given how close surface/bg colors are by design.
- `theme.css` (light block only): `--border-focus` changed from `var(--accent)` to `var(--brand-primary)` (navy, 14.8:1 contrast) — dark block untouched (already correct at `var(--accent)`, 9.98:1).
- `components.css`: all 8 `outline: 2px solid var(--accent);` focus-visible rules now read `outline: 2px solid var(--border-focus);` — wires them to the (previously unused) semantic alias instead of the raw primitive, so light and dark modes each get the contrast-correct color automatically.

## C — OUT OF UI/UX SCOPE / not changed (with reason)

- **`--border-strong-light` (1.59:1)**: not changed. It's shared across 19 usages, most of which are decorative dashed dividers exempt from the 3:1 non-text-contrast rule, mixed with a smaller number of real interactive-hover boundaries I can't cleanly separate without visual QA. Changing the shared primitive risks a visible, unverified shift across many unrelated contexts with no browser available to confirm the result looks right — flagged for a future pass with visual verification, not pushed through blind.
- Everything flagged `OUT OF UI/UX SCOPE` in the two prior passes (recommendation-engine's fixed action list; no priority field in gap data) still stands — nothing new of that kind found this pass.

## D — Files Modified
- `wathiq_maturity_dashboard/css/tokens.css`
- `wathiq_maturity_dashboard/css/theme.css`
- `wathiq_maturity_dashboard/css/components.css`

## E — Files Protected
No backend/business-logic/scoring/RAG/compliance/data-contract file was opened for writing: `src/scoring/*`, `src/evidence_assessment/*`, `src/compliance/*`, `src/maturity_assessment/*`, `dashboard/data_layer.py`, `src/api/*`, `data/*`, `js/recommendation_engine.js`. `git status` confirms only the 3 files above changed this pass (pre-existing, unrelated `src/scoring`/`src/evidence_assessment` working-tree state from before either UI/UX pass is still present and still untouched — same as reported previously).

## F — Verification (STATIC ONLY — no browser tool available)
- `node --check js/app.js` → pass (unchanged this round, re-verified).
- CSS brace balance: `components.css` 386/386, `tokens.css` 3/3, `theme.css` 4/4 → balanced.
- `var(--token)` resolution across all 5 CSS files → 101 used, 121 defined, 0 dangling.
- Light/dark token parity re-checked → unchanged from prior passes (only `--z-header` intentionally shared, as before).
- Contrast ratios computed via WCAG relative-luminance formula (script shown in this session), not estimated.
- `git status`/`git diff --stat` scoped to the relevant directories → only the 3 files listed changed.

## G — Remaining Visual Check (could not be done here)
No browser automation tool exists in this environment, so none of the following were actually seen rendered: the strengthened card shadows at 1440/1280/1024/768/390/375px, the corrected focus ring color in an actual tab-through, dark mode, or RTL layout. The math confirms the fix is correct in principle; an actual look (or a quick manual pass with a local server) is the only way to confirm it feels right, not just measures right.
