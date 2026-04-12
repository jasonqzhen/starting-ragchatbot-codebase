#!/usr/bin/env bash
# Auto-format all frontend files with Prettier.
# Usage: ./scripts/format-frontend.sh
set -euo pipefail

cd "$(dirname "$0")/../frontend"

if ! command -v npx >/dev/null 2>&1; then
    echo "error: npx not found. Install Node.js (>=18) to use the frontend quality tools." >&2
    exit 1
fi

echo "Formatting frontend files with Prettier..."
npx --yes prettier@^3.3.3 --write "**/*.{html,css,js,json,md}"
echo "Done."
