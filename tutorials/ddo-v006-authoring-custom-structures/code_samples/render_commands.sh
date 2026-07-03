#!/usr/bin/env bash
# DDO v0.0.6 — Tutorial 2 (Authoring Custom Structures) render commands.
# Run from the repo root. Renders all four new document types (blog_post,
# meeting_notes, meeting_agenda, project_report) to HTML and Markdown, using
# this tutorial's own `input_files/*_example.yaml` (byte-identical copies of
# tests/data/*_example.yaml) and writing into this tutorial's `output_files/`.
#
# This is the render step referenced by tutorial.md — running it end-to-end
# from a clean checkout is exactly what a newcomer following the tutorial
# would do, and it must exit 0.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

TUTORIAL_DIR="tutorials/ddo-v006-authoring-custom-structures"
IN_DIR="${TUTORIAL_DIR}/input_files"
OUT_DIR="${TUTORIAL_DIR}/output_files"

mkdir -p "${OUT_DIR}"

# blog_post — walked from scratch in tutorial.md.
uv run --locked ddo/build.py \
  --data     "${IN_DIR}/blog_post_example.yaml" \
  --template blog_post \
  --format   html \
  --output   "${OUT_DIR}/blog_post.html"

uv run --locked ddo/build.py \
  --data     "${IN_DIR}/blog_post_example.yaml" \
  --template blog_post \
  --format   md \
  --output   "${OUT_DIR}/blog_post.md"

# meeting_notes — worked example.
uv run --locked ddo/build.py \
  --data     "${IN_DIR}/meeting_notes_example.yaml" \
  --template meeting_notes \
  --format   html \
  --output   "${OUT_DIR}/meeting_notes.html"

uv run --locked ddo/build.py \
  --data     "${IN_DIR}/meeting_notes_example.yaml" \
  --template meeting_notes \
  --format   md \
  --output   "${OUT_DIR}/meeting_notes.md"

# meeting_agenda — worked example.
uv run --locked ddo/build.py \
  --data     "${IN_DIR}/meeting_agenda_example.yaml" \
  --template meeting_agenda \
  --format   html \
  --output   "${OUT_DIR}/meeting_agenda.html"

uv run --locked ddo/build.py \
  --data     "${IN_DIR}/meeting_agenda_example.yaml" \
  --template meeting_agenda \
  --format   md \
  --output   "${OUT_DIR}/meeting_agenda.md"

# project_report — worked example.
uv run --locked ddo/build.py \
  --data     "${IN_DIR}/project_report_example.yaml" \
  --template project_report \
  --format   html \
  --output   "${OUT_DIR}/project_report.html"

uv run --locked ddo/build.py \
  --data     "${IN_DIR}/project_report_example.yaml" \
  --template project_report \
  --format   md \
  --output   "${OUT_DIR}/project_report.md"

echo "Rendered all four types (HTML + Markdown) to ${OUT_DIR}/"
