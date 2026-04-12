# Frontend Changes — Dark/Light Theme Toggle

Adds an accessible, icon-based theme toggle that switches between the existing
dark theme and a new light theme. Theme state is persisted across reloads and
respects the user's OS preference on first visit.

## Files changed

- `frontend/index.html`
- `frontend/style.css`
- `frontend/script.js`

No backend files were touched.

## 1. `frontend/index.html`

Added a `<button id="themeToggle">` as the first child of `<body>` (so it sits
above all layout content and is rendered fixed to the top-right via CSS). The
button contains two inline SVG icons (sun + moon); CSS shows whichever is
appropriate for the active theme.

Accessibility:
- Native `<button>` element — keyboard-focusable and activatable with
  Enter/Space by default.
- `aria-label` describing the action (updated dynamically by JS to reflect the
  current state, e.g. "Switch to light theme" / "Switch to dark theme").
- `aria-pressed` reflects whether light mode is active (toggle semantics).
- `title` attribute for hover tooltip.
- Decorative SVGs marked `aria-hidden="true"`.

## 2. `frontend/style.css`

### Light theme variables
The existing `:root` block (dark theme) is left intact and remains the default.
Added a `[data-theme="light"]` selector that overrides the same CSS custom
properties with a light palette:

- `--background: #f8fafc` (light app background)
- `--surface: #ffffff` (cards, sidebar, input)
- `--surface-hover: #e2e8f0`
- `--text-primary: #0f172a` (dark text on light bg — high contrast)
- `--text-secondary: #475569` (meets WCAG AA on light surfaces)
- `--border-color: #cbd5e1`
- `--assistant-message: #e2e8f0`
- `--welcome-bg: #dbeafe`, `--welcome-border: #2563eb`
- `--shadow` softened for light surfaces
- `--focus-ring` slightly stronger for visibility on light backgrounds

A new `--code-bg` variable was added to both themes so that inline `code` and
`<pre>` blocks adapt automatically — the previous hard-coded
`rgba(0, 0, 0, 0.2)` would have looked muddy on a light background. The
existing `.message-content code` and `.message-content pre` rules were updated
to use `var(--code-bg)`.

The primary blue (`--primary-color`, `--user-message`) is intentionally kept
across both themes to preserve brand identity and the visual hierarchy.

### Smooth transitions
Added a `transition: background-color 0.3s ease, color 0.3s ease,
border-color 0.3s ease, box-shadow 0.3s ease` to the major surface elements
(`body`, sidebar, chat container, messages, inputs, buttons, etc.) so the
theme swap animates instead of snapping.

### Theme toggle button styling
- `position: fixed; top: 1.25rem; right: 1.25rem; z-index: 100;` — pinned to
  the top-right of the viewport, above everything else.
- 44×44 circular button (meets the 44px minimum touch target guideline).
- Uses `var(--surface)`, `var(--border-color)`, `var(--text-primary)`, and
  `var(--shadow)` so it inherits theme colors automatically.
- Hover state: lifts 1px and brightens to `--surface-hover`.
- `:focus-visible` shows the standard `--focus-ring` outline (visible to
  keyboard users, hidden from mouse users).
- Both SVG icons are stacked via `position: absolute` inside the button.
- Icons cross-fade with a combined opacity + rotate/scale transform
  (0.4s ease) — sun rotates in / moon rotates out (and vice versa) for a
  subtle but noticeable swap animation.
- Icon visibility is driven entirely by the `[data-theme="light"]` selector,
  so the JS only has to flip the attribute.

## 3. `frontend/script.js`

Added theme bootstrapping and a toggle handler:

- `themeToggle` is captured alongside the other DOM references on
  `DOMContentLoaded`.
- `initTheme()` runs before anything else paints content. It reads
  `localStorage.getItem('theme')`; if absent, it falls back to
  `window.matchMedia('(prefers-color-scheme: light)')`. Both reads are wrapped
  in `try/catch` so private-mode / storage-disabled browsers still work.
- `toggleTheme()` flips between `'light'` and `'dark'`.
- `applyTheme(theme)` is the single place that mutates state:
  - Sets `data-theme` on `<html>` (`document.documentElement`) — chosen over
    `<body>` so the attribute is available to any future top-level styling
    and matches common conventions.
  - Updates `aria-pressed` and `aria-label` on the toggle button so screen
    readers announce the new state.
  - Persists the choice to `localStorage` (also wrapped in `try/catch`).
- `setupEventListeners()` wires `themeToggle.addEventListener('click', ...)`.
  Keyboard activation (Enter / Space) is handled natively because the toggle
  is a real `<button>`, so no extra keydown handler is needed.

## Behavior summary

- First visit: theme follows OS `prefers-color-scheme`, defaulting to dark.
- Click (or Enter/Space when focused): theme flips and is saved.
- Reload: saved theme is restored.
- All colors are driven by CSS custom properties, so every existing element —
  sidebar, chat bubbles, code blocks, suggested-question chips, scrollbars,
  inputs, error/success messages — adapts automatically without per-component
  overrides.
