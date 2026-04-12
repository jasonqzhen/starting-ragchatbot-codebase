#!/usr/bin/env bash
# Check frontend formatting without modifying files.
# Fails (exit != 0) if any file would be reformatted. Suitable for CI.
# Usage: ./scripts/check-frontend.sh
set -euo pipefail

cd "$(dirname "$0")/../frontend"

if ! command -v npx >/dev/null 2>&1; then
    echo "error: npx not found. Install Node.js (>=18) to use the frontend quality tools." >&2
    exit 1
fi

echo "Checking frontend formatting with Prettier..."
npx --yes prettier@^3.3.3 --check "**/*.{html,css,js,json,md}"
