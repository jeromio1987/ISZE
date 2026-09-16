#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
FILE="$DIR/ISZE_Exec_Aftersales_Paper.html"
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$FILE" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then
  open "$FILE" || true
fi
echo "Open: $FILE"
