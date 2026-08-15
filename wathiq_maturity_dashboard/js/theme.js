/**
 * Wathiq — Theme Toggle (Light/Dark).
 *
 * Presentation-only, completely separate from js/app.js and
 * js/recommendation_engine.js: touches no assessment data, no
 * maturity/gap/recommendation rendering, no fetch. Its only job is
 * flipping <html data-theme="..."> between "light"/"dark" and persisting
 * the choice -- css/theme.css already maps every semantic token (bg,
 * surface, cards, text, borders, accent, status colors, and the header
 * logo via var(--brand-primary)/var(--accent)) to both values, so no other
 * file needs to change when this attribute flips.
 *
 * The initial value is applied synchronously by a small inline <script> in
 * index.html's <head> (before first paint, to avoid a flash of the wrong
 * theme) -- this file only wires the toggle button's click handling and
 * keeps its icon/label in sync with the current theme.
 */

(function () {
  "use strict";

  const STORAGE_KEY = "wathiq-theme";
  const root = document.documentElement;

  function storeTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      // localStorage unavailable (private mode, disabled storage, ...) --
      // the toggle still works for the current page load, it just won't
      // persist across a reopen.
    }
  }

  function currentTheme() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function updateToggleUI(theme) {
    const btn = document.getElementById("wq-theme-toggle");
    if (!btn) return;
    const isDark = theme === "dark";
    btn.setAttribute("aria-pressed", String(isDark));
    btn.setAttribute("aria-label", isDark ? "التبديل إلى الوضع الفاتح" : "التبديل إلى الوضع الداكن");
    btn.textContent = isDark ? "☀" : "🌙";
  }

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    updateToggleUI(theme);
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Sync the button's icon/label with whatever the head script already
    // applied (default: light, per the task's explicit default rule).
    updateToggleUI(currentTheme());

    const btn = document.getElementById("wq-theme-toggle");
    if (!btn) return;

    btn.addEventListener("click", function () {
      const next = currentTheme() === "dark" ? "light" : "dark";
      setTheme(next);
      storeTheme(next);
    });
  });
})();
