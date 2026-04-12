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
