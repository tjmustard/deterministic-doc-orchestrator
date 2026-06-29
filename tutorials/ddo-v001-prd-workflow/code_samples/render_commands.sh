#!/usr/bin/env bash
# DDO v0.0.1 — render commands reference
# Run from the repo root. Replace my_document_data.yaml and the --output
# paths with your actual file and desired destination.

set -euo pipefail

DATA="my_document_data.yaml"
SLUG="my-doc"
OUT_DIR="Documents/${SLUG}/output"

# Render HTML
uv run --locked ddo/build.py \
  --data     "${DATA}" \
  --template prd \
  --format   html \
  --output   "${OUT_DIR}/${SLUG}.html"

# Render Markdown
uv run --locked ddo/build.py \
  --data     "${DATA}" \
  --template prd \
  --format   md \
  --output   "${OUT_DIR}/${SLUG}.md"

# Render PDF
uv run --locked ddo/build.py \
  --data     "${DATA}" \
  --template prd \
  --format   pdf \
  --output   "${OUT_DIR}/${SLUG}.pdf"

# Render PDF with pinned timestamp for byte-identical output (optional)
# uv run --locked ddo/build.py \
#   --data      "${DATA}" \
#   --template  prd \
#   --format    pdf \
#   --output    "${OUT_DIR}/${SLUG}.pdf" \
#   --timestamp 1000000000

echo "Rendered to ${OUT_DIR}/"
