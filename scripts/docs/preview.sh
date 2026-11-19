#!/usr/bin/env bash
# Render chosen diagrams and take a PNG preview of each, for review while drawing.
# Usage: scripts/docs/preview.sh <out dir> <diagram name>...
set -euo pipefail
out=$1; shift
python3 scripts/docs/gen_diagrams.py "$@" >/dev/null
node scripts/docs/render_diagrams.mjs docs/diagramas/documentacao docs/assets/diagrams >/dev/null
mkdir -p "$out"
for name in "$@"; do
  for lang in pt en; do
    svg="$PWD/docs/assets/diagrams/$lang/$name.svg"
    size=$(grep -o 'width="[0-9]*" height="[0-9]*"' "$svg" | head -1 | tr -dc '0-9 ' | awk '{print $1","$2}')
    google-chrome --headless=new --hide-scrollbars --screenshot="$out/$name-$lang.png" --window-size="$size" "file://$svg" 2>/dev/null
  done
done
