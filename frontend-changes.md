# Testing Framework Enhancements

> Note: This task produced backend testing infrastructure (not frontend code).
> Per the task instructions, the summary of changes is recorded here in
> `frontend-changes.md`.

## Summary

Added API-level testing infrastructure for the RAG system so the FastAPI
endpoints (`/api/query`, `/api/courses`, `/`) are exercised in CI without
pulling in the real `RAGSystem`, ChromaDB, or the `../frontend` static mount.

All 19 new tests pass via `uv run pytest`.

## Files added

### `backend/tests/__init__.py`
Empty marker so `backend/tests` is importable as a package.

### `backend/tests/conftest.py`
Shared pytest fixtures:

- **`sample_course_titles`, `sample_analytics`, `sample_query_answer`** —
  canned test data used across endpoint tests.
- **`mock_rag_system`** — `MagicMock` that mirrors the surface of
  `RAGSystem` the API touches (`session_manager.create_session`, `query`,
  `get_course_analytics`).
- **`test_app`** — builds a standalone `FastAPI` app in
  `_build_test_app(rag_system)` that mirrors the endpoints in
  `backend/app.py` but:
  - omits the `StaticFiles` mount on `../frontend` (which doesn't exist
    in the test environment and would break `TestClient` startup),
  - injects the mocked RAG system instead of constructing the real one,
  - adds a simple `GET /` route so tests can cover the root path without
    loading the real frontend assets.
- **`client`** — a `fastapi.testclient.TestClient` bound to `test_app`.

`conftest.py` also prepends `backend/` to `sys.path` so the tests can
import backend modules when invoked from the repo root.

### `backend/tests/test_api_endpoints.py`
19 tests across 6 classes:

- **`TestQueryEndpoint`** — `/api/query`
  - creates a session when none provided
  - reuses an explicit `session_id`
  - returns 422 on missing field / wrong type
  - returns 500 when `rag_system.query` raises
  - response schema shape check
  - accepts empty-string query
- **`TestCoursesEndpoint`** — `/api/courses`
  - returns analytics payload
  - delegates to `rag_system.get_course_analytics`
  - returns 500 on backend error
  - handles empty catalog
  - rejects `POST` with 405
- **`TestRootEndpoint`** — `/` returns ok status
- **`TestCORS`** — CORS middleware emits `access-control-allow-origin`
- **`TestFixtures`** — sanity checks on the fixtures themselves, plus a
  parametrized smoke test that every route is reachable via the client

## Files modified

### `pyproject.toml`
- Added a `[dependency-groups]` `dev` group with `pytest>=8.0` and
  `httpx>=0.27` (httpx is required by `fastapi.testclient.TestClient`).
- Added `[tool.pytest.ini_options]`:
  - `testpaths = ["backend/tests"]`
  - `pythonpath = ["backend"]` so tests can `import` backend modules
    without needing an installed package
  - `python_files`/`python_classes`/`python_functions` conventions
  - `addopts = ["-ra", "--strict-markers", "--tb=short"]`
  - `filterwarnings` to silence deprecation noise from dependencies

## How to run

```bash
uv sync --group dev
uv run pytest
```

Expected: `19 passed`.

## Design notes

- **Why a separate test app instead of importing `backend/app.py`?**
  `backend/app.py` constructs `RAGSystem(config)` at import time (which
  spins up ChromaDB and needs an `ANTHROPIC_API_KEY`) and mounts
  `../frontend` as static files. Both break cleanly under `TestClient`.
  A standalone app that mirrors the route definitions lets us inject a
  mock and keeps the tests hermetic.
- **Why `MagicMock` instead of a real `RAGSystem`?** The endpoint tests
  are about request/response handling — schema validation, status codes,
  error propagation, session wiring — not retrieval quality. Unit tests
  for the RAG internals belong in separate test modules.
- **Fixture scope.** All fixtures are function-scoped so each test gets a
  fresh mock and a fresh client; this avoids cross-test bleed on the
  `MagicMock` call history that tests assert against.

---

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

---

# Frontend Changes — Code Quality Tooling

## Summary

Added a code quality / auto-formatting workflow scoped to the **frontend** (`frontend/`).
The original task asked for `black`, but `black` is a Python formatter and does not
apply to the frontend — the frontend in this repo is vanilla HTML, CSS, and JavaScript.
The equivalent industry-standard tool for those file types is **Prettier**, which is
what was wired up.

## What was added

### 1. Prettier configuration — `frontend/.prettierrc.json`

Opinionated defaults, tuned to match the existing 4-space indentation in the codebase
so the initial reformat is minimally disruptive:

- `tabWidth: 4`, `useTabs: false`
- `semi: true`
- `singleQuote: true` (matches existing JS style)
- `printWidth: 100`
- `trailingComma: "es5"`
- `arrowParens: "always"`
- `bracketSameLine: false`, `htmlWhitespaceSensitivity: "css"`
- `endOfLine: "lf"`
- Markdown override: `tabWidth: 2`, `proseWrap: "preserve"`

### 2. Prettier ignore file — `frontend/.prettierignore`

Excludes `node_modules`, `package-lock.json`, and any minified assets from formatting.

### 3. Frontend `package.json` — `frontend/package.json`

Declares Prettier as a dev dependency and exposes npm scripts:

- `npm run format` — auto-format all frontend files in place
- `npm run format:check` — verify formatting without modifying files (CI-friendly)
- `npm run quality` — alias for `format:check`, the umbrella quality-gate command

### 4. Dev shell scripts

Two shell wrappers under `scripts/` for users who want to run checks without
cd-ing into `frontend/` and without requiring a local `npm install`:

- `scripts/format-frontend.sh` — runs `npx prettier --write` over frontend files
- `scripts/check-frontend.sh` — runs `npx prettier --check`; exits non-zero on any
  formatting drift, making it suitable for CI or a pre-push hook

Both scripts use `npx --yes prettier@^3.3.3` so they work on any machine with
Node.js (>=18) installed, with no prior `npm install` needed.

## Formatting pass applied to existing files

All three frontend source files were brought into compliance with the new Prettier
config. Changes are formatting-only — no behavior changes.

### `frontend/script.js`

- Removed trailing whitespace on many lines
- Collapsed stray double-blank-line gaps to single blank lines
- Added trailing commas on multi-line object/array literals (`trailingComma: "es5"`)
- Wrapped the long `addMessage(...)` welcome call across multiple lines to respect
  `printWidth: 100`
- Arrow-function parameters consistently parenthesized (e.g., `forEach((button) => …)`)
- Removed a stale `// Removed removeMessage function …` comment that referenced
  deleted code

### `frontend/style.css`

- Expanded the three single-line header rules (`.message-content h1/h2/h3 { … }`)
  into standard multi-line block form, matching Prettier's CSS output and the rest
  of the stylesheet

### `frontend/index.html`

- Indented `<head>` and `<body>` under `<html>` (Prettier's default)
- Self-closed void elements (`<meta …/>`, `<link …/>`, `<input …/>`)
- Wrapped the four long `.suggested-item` `<button>` elements across multiple lines
  so their `data-question` attribute no longer blows past `printWidth: 100`
- Reformatted the send-button `<svg>` attributes onto one attribute per line

## How to use

From a shell (frontend-scoped, no global install required):

```bash
# Format all frontend files in place
./scripts/format-frontend.sh

# Check formatting (no writes) — fails if anything is off
./scripts/check-frontend.sh
```

Or, from inside `frontend/` once you have run `npm install`:

```bash
cd frontend
npm install          # one-time, installs prettier as a devDependency
npm run format       # format in place
npm run format:check # verify only
npm run quality      # alias for format:check
```

## Why Prettier (not Black)

- `black` formats Python only. None of the files under `frontend/` are Python, so
  running `black` there would be a no-op.
- Prettier is the de-facto formatter for HTML, CSS, and JavaScript and fills the
  same role for the frontend that `black` fills for a Python backend: opinionated,
  low-config, auto-fix on save, consistent across contributors.
- If Python quality tooling is also desired, `black` can be added to the **backend**
  as a separate follow-up (out of scope for this frontend-only task).

## Files touched

```
frontend/.prettierrc.json      (new)
frontend/.prettierignore       (new)
frontend/package.json          (new)
frontend/script.js             (reformatted)
frontend/style.css             (reformatted)
frontend/index.html            (reformatted)
scripts/format-frontend.sh     (new)
scripts/check-frontend.sh      (new)
frontend-changes.md            (new — this file)
```
