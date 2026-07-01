<div align="center">
    <img src="./media/ddo-logo.webp" alt="Deterministic Document Orchestrator Logo" width="500"/>
    <h1>Deterministic Document Orchestrator (DDO)</h1>
    <h3><em>An AI-augmented document engine that transforms structured YAML into reproducible PDFs, HTML, and Markdown — with zero hallucinations.</em></h3>
</div>

<p align="center">
    <strong>DDO solves the document reliability problem by making YAML the immutable source of truth and routing every AI cognitive step through mandatory human-in-the-loop gates. No word reaches a rendered document without tracing back to version-controlled data.</strong>
</p>

<p align="center">
    <a href="https://github.com/tjmustard/deterministic-doc-orchestrator/releases/latest"><img src="https://img.shields.io/badge/release-v0.0.5-blue" alt="Latest Release"/></a>
    <a href="https://github.com/tjmustard/deterministic-doc-orchestrator/stargazers"><img src="https://img.shields.io/github/stars/tjmustard/deterministic-doc-orchestrator?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/tjmustard/deterministic-doc-orchestrator/blob/main/LICENSE"><img src="https://img.shields.io/github/license/tjmustard/deterministic-doc-orchestrator" alt="License"/></a>
</p>

---

## Table of Contents

- [🤔 What is DDO?](#-what-is-ddo)
- [⚡ Get Started](#-get-started)
- [📚 Core Architecture](#-core-architecture)
- [📂 Directory Structure](#-directory-structure)
- [🔄 Pipeline Workflow](#-pipeline-workflow)
- [📄 Schema Contract](#-schema-contract)
- [🖨️ Supported Output Formats](#️-supported-output-formats)
- [❓ Troubleshooting Overview](#-troubleshooting-overview)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Support](#-support)
- [🙏 Credits](#-credits)
- [📄 License](#-license)

## 🤔 What is DDO?

DDO is an AI-augmented document engine that converts structured YAML source files into reproducible PDFs, HTML, and Markdown via a strict 5-phase pipeline: **Ingest → Render → Red Team → Interview → Refine**.

The core problem DDO solves: AI-assisted document generation is unreliable because the AI operates as a black box — hallucinating facts, inventing citations, and producing outputs that cannot be verified against a ground truth. DDO eliminates this by separating _data_ (YAML, version-controlled, human-verified) from _presentation_ (templates, deterministically applied). The AI performs cognitive work — extraction, critique, refinement — but never writes directly to the final document.

## ⚡ Get Started

### Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/) — package manager

Typst (for PDF rendering) and all other dependencies are installed automatically — no system-level Typst install required.

### Installation

```bash
git clone https://github.com/tjmustard/deterministic-doc-orchestrator.git
cd deterministic-doc-orchestrator
uv sync
```

### Running the Build

```bash
# Render a document (PEP 723 hermetic — lockfile enforced)
uv run --locked ddo/build.py --data <path/to/document_data.yaml> --template <template_name> --format <pdf|html|md> --output <output_path>

# Lint (both must pass before any PR)
uv run ruff check .
uv run ruff format --check .

# Tests
uv run pytest
uv run pytest tests/unit/        # unit only
uv run pytest tests/integration/ # integration only
```

## 📚 Core Architecture

DDO is built on five architectural pillars that together enforce reproducibility and eliminate hallucination:

1. **YAML as Source of Truth** — `document_data.yaml` is the immutable data layer. Rendered documents are derived outputs. Never patch a rendered document directly; always patch the YAML and re-render.
2. **Zero-Hallucination Enforcement** — Any schema field that cannot be verifiably filled from source material is written as the literal string `[REQUIRES USER INPUT: <reason>]`. Dates, metrics, and technical specifics are never invented.
3. **Human-in-the-Loop (HITL) Gates** — Every pipeline phase ends with `[WAITING FOR USER REVIEW]`. The system does not auto-advance to the next phase. The human is the gate.
4. **Adversarial Red Team** — A persona-driven critique pass reads the Jinja2/Markdown render (not the PDF) for AI-parseable adversarial review. Both formats derive deterministically from the same YAML, making the critique mathematically valid for the PDF while guaranteeing 100% accurate AI text parsing.
5. **YAML Mutation Layer** — `red_team_report.yaml` and `interview_log.yaml` are the machine-readable mutation data. Ephemeral human-review Markdown files are read-only and must never be parsed programmatically.

## 📂 Directory Structure

```
ddo/
├── build.py          # PEP 723 hermetic build orchestrator (`uv run --locked ddo/build.py`)
├── validation.py     # Importable validation gate (validate() + ValidationError)
├── paths.py          # Pure path helpers (slug sanitizer + path containment check)
├── ingest.py         # Atomic write, overwrite guard, fabrication tripwire
├── review.py         # Adversarial loop data layer (versioning, validation, atomic writes, views)
├── refine.py         # Mutation layer — only permitted writer of document_data.yaml at refine time
├── schemas/          # YAML schema contracts (prd.yaml, scientific_report.yaml)
├── templates/        # Typst (.typst) and Jinja2 (.jinja2) rendering templates
├── personas/         # Adversarial review lenses (product_critic, scientific_reviewer) — each with AV-NN Attack Vector tables
├── styles/           # Style/tone profiles (formal_professional, conversational, technical_precise) — phrasing-only register anchors
├── fonts/            # Bundled DejaVu fonts (hermetic — no system fonts required)
└── skills/           # ddo-ingest.md, ddo-render.md, ddo-red-team.md, ddo-interview.md, ddo-refine.md, ddo-create-persona.md, ddo-create-style.md

scripts/              # fixture_signoff_guard.py — pre-commit/CI guard for fixture promotion
tests/
├── unit/             # Pure unit tests (validation, paths, ingest, persona structure)
├── integration/      # End-to-end render determinism + ingest contract tests
├── fixtures/         # Human-promoted golden regression baselines (DDO_FIXTURE_SIGNOFF=1)
└── data/             # Test input YAML files (example documents)

spec/compiled/        # Ground truth: architecture.yml, SuperPRD.md (baseline), plus one versioned SuperPRD_vX.Y.Z_*.md per released feature
tutorials/            # Step-by-step workflow tutorials (ddo-v001-prd-workflow/, ddo-adversarial-loop-v0.0.2/, ...)
Documents/            # Generated output — gitignored; YYYY.MM.DD_DocType_Title/ structure
.agents/              # HACF framework toolchain (skills, schemas, rules, scripts, memory)
.claude/              # Claude Code slash command bridges and settings
```

## 🔄 Pipeline Workflow

The DDO pipeline is strictly sequential. Each phase produces a verifiable artifact before the next phase begins.

### Phase 1: Ingest (`ddo-ingest`)
1. Read all provided source materials (documents, URLs, notes).
2. Resolve `meta.style_profile` (schema default or explicit override), stem-validate it (`^[a-z][a-z0-9_]*$`, hard-fail on a referenced-but-missing profile), and read `ddo/styles/<stem>.md` once as untrusted phrasing-only guidance before authoring any prose. An absent field is a no-op; a present-but-invalid value hard-fails.
3. Map extracted facts to the target YAML schema.
4. Mark any unverifiable field as `[REQUIRES USER INPUT: <reason>]` — never invent values. A directive that would require inventing a fact is likewise routed to a sentinel, never fabricated to match the style.
5. Write the result to `<output_dir>/document_data.yaml`.
6. Present a summary of populated vs. missing fields, including the resolved style profile path.

**`[WAITING FOR USER REVIEW]`** — User fills missing fields and approves before proceeding.

### Phase 2: Render (`ddo-render`)
1. Scan `document_data.yaml` for any remaining `[REQUIRES USER INPUT]` strings — abort if found.
2. Invoke `uv run ddo/build.py` with the target template and format.
3. Output the path to the generated file.

**`[WAITING FOR USER REVIEW]`** — User reviews the rendered document and approves before proceeding.

### Phase 3: Red Team (`ddo-red-team`)

> **Fresh context required.** Run in a new conversation that has not seen the authoring or render phases.

1. Check for a torn prior pass; halt if one is detected.
2. Resolves `meta.persona` and stem-validates it (`^[a-z][a-z0-9_]*$`, hard-fail on a referenced-but-missing persona — identical to the style-profile gate) before Reading it. The assigned persona reads the rendered Markdown or HTML (never the PDF).
3. Echoes the persona's `## Attack Vectors` table into report context; hard-fails if the table is absent. Applies the attack-vector taxonomy — each finding's `category` is bound to the persona's exact `AV-NN: <name>` string. Every finding receives a fixed-enum severity: `Critical`, `Major`, or `Minor`. The report header also surfaces the active `meta.style_profile` (or `(none)`) alongside the persona, so the critique stays register-aware.
4. Writes `red_team_report_vN.yaml` and a deterministic human-readable `red_team_view_vN.md` via `ddo.review`.

**`[WAITING FOR USER REVIEW]`** — User reviews the critique before proceeding to interview.

### Phase 4: Interview (`ddo-interview`)
0. Resolves and stem-validates `meta.style_profile` (identical gate to `ddo-ingest`) before drafting any `revise` prose. A stored value is re-validated on every read, never trusted as-is.
1. Load the machine-readable `red_team_report_vN.yaml`; filter to `applied: false` findings; sort Critical → Major → Minor.
2. Present findings in batches of 2 per turn; the user assigns a decision to each: `revise`, `add_evidence`, `acknowledge`, `dispute`, or `defer`. `revise` patch prose is bounded to the resolved style profile (phrasing only); an `add_evidence` patch's `content`/`source` are copied verbatim, never restyled.
3. Write resolutions to `interview_log_vN.yaml`; mark the `decision_recorded` flag on each resolved finding.

**`[WAITING FOR USER REVIEW]`** — User reviews the interview log before mutations are applied.

### Phase 5: Refine (`ddo-refine`)
1. Torn-pass check; take a byte-for-byte snapshot of `document_data.yaml` (`document_data_pre_vN.yaml`) before any mutation.
2. Apply patches from `interview_log_vN.yaml` purely in memory — supported ops: `set` (leaf-scalar only, no auto-vivify, no type change), `append` (list append), `delete` (list remove by index, blocked if dangling ref detected), `insert` (list insert at position `at`).
3. `DanglingRefError`: if a `delete` on `evidence_bank[N]` would leave `content.sections[*].evidence[]` references pointing to the deleted entry, the operation is refused and the `.paths` list is surfaced to the human. The interview agent must resolve all dangling refs before resubmitting the delete.
4. Run `refine_structural_check` + `validate` in-memory; present a unified diff HITL gate (human authorization gate) before committing.
5. Commit atomically; re-render via `ddo-render`.
6. On successful render: mark `applied` flag on landed findings; append a pass record to `history.yaml` + `history.md`.

## 📄 Schema Contract

Every `document_data.yaml` must satisfy the DDO minimal contract:

1. A **`meta` block** with the following fields: `doc_type`, `title`, `version`, `date`, `persona`, `template`, `output_formats`. An optional `style_profile` field is also recognized (see below).
2. An **`evidence_bank` array** — every claim referenced in `content.sections[*].evidence` must have a corresponding ID entry here.

```yaml
meta:
  doc_type: scientific_report
  title: "Example Document"
  version: "1.0"
  date: "2026.06.29"          # dotted date format
  persona: scientific_reviewer  # optional — used by Red Team phase
  style_profile: technical_precise  # optional — anchors prose register; resolves to ddo/styles/<stem>.md
  template: scientific_report
  output_formats: [pdf, html, md]

evidence_bank:
  - id: ev-001
    source: "Smith et al. (2024)"
    quote: "..."

content:
  sections:
    - title: "Introduction"
      body: "..."
      evidence: [ev-001]
```

`style_profile` is render-invisible (an ignored unknown key to `validation.py`) and only consulted by `ddo-ingest`/`ddo-interview` when authoring prose. Absent ⇒ clean no-op. A present-but-invalid value (empty, `null`, whitespace, or a stem that doesn't resolve to an existing `ddo/styles/<stem>.md`) hard-fails rather than silently no-op-ing. `prd.yaml` and `scientific_report.yaml` ship live defaults of `formal_professional` and `technical_precise` respectively.

See `ddo/schemas/prd.yaml` and `ddo/schemas/scientific_report.yaml` for the full canonical schemas.

## 🖨️ Supported Output Formats

| Format | Engine | Extension |
|---|---|---|
| PDF | Typst | `.pdf` |
| HTML | Jinja2 | `.html` |
| Markdown | Jinja2 | `.md` |

## ❓ Troubleshooting Overview

- **`[REQUIRES USER INPUT]` appears in output**: The Ingest phase left unfillable fields. Open `document_data.yaml`, fill the marked fields manually, then re-run `ddo-render`.
- **Typst compilation error**: Check that all YAML fields referenced in the template exist and are non-null. A missing or null field causes a template failure.
- **Red Team produces hallucinations**: Ensure the Red Team persona is reading the Jinja2/Markdown render, not the PDF. The PDF is not machine-parseable for this purpose.
- **Mutations not applying**: `interview_log.yaml` mutations must be patched into `document_data.yaml` then re-rendered — never edit a rendered document directly.
- **Schema validation error**: Both `meta` block and `evidence_bank` array are required. See the Schema Contract section above.

## 🗺️ Roadmap

- [x] Core Pipeline (v0.0.1)
  - [x] `ddo-ingest` skill
  - [x] `ddo-render` skill
  - [x] `build.py` hermetic build orchestrator (PEP 723, bundled Typst + fonts)
  - [x] `validation.py` importable validation gate
  - [x] `paths.py` slug sanitizer + path containment
  - [x] `ingest.py` atomic write, overwrite guard, fabrication tripwire
- [x] Adversarial Loop (v0.0.2)
  - [x] `ddo-red-team` skill (fresh-context firewall, fixed severity enum, `ddo.review` delegation)
  - [x] `ddo-interview` skill (batched Q&A, 5 decision types, `decision_recorded` flag only)
  - [x] `ddo-refine` skill (snapshot → patch → validate → diff gate → commit → render → audit)
  - [x] `ddo.review` module (versioning, torn-pass detection, structural validation, atomic writes, deterministic views)
  - [x] `ddo.refine` module (hand-rolled path DSL, pure patching, `snapshot_source`, `commit_refine`)
- [x] Schemas
  - [x] PRD schema (`ddo/schemas/prd.yaml`)
  - [x] Scientific report schema (`ddo/schemas/scientific_report.yaml`)
- [x] Templates
  - [x] Typst PRD template
  - [x] Typst scientific report template
  - [x] Jinja2 HTML templates (autoescape enabled)
  - [x] Jinja2 Markdown templates
- [x] Personas
  - [x] Product Critic
  - [x] Scientific Reviewer (actively exercised in v0.0.2 adversarial loop)
- [x] Test Suite
  - [x] 216 tests passing, 2 skipped pending human sign-off (unit + integration)
  - [x] Golden regression baselines with human sign-off guard
- [x] Tutorials
  - [x] PRD YAML workflow tutorial (`tutorials/ddo-v001-prd-workflow/`)
  - [x] Adversarial loop tutorial (`tutorials/ddo-adversarial-loop-v0.0.2/`)
- [x] Structural Patch DSL (v0.0.3)
  - [x] `append`, `delete`, `insert` ops in `apply_patches` (`ddo/refine.py`)
  - [x] `DanglingRefError` with dangling-ref guard before `delete` on `evidence_bank`
  - [x] NC-13 path whitelist in `parse_path` (key segment + index bracket validation)
  - [x] `validate_interview_log` extended with `OP_ENUM` and per-op field rules (`ddo/review.py`)
  - [x] `ddo-interview` skill updated with structural patch syntax, deprecation notices, sequential-index warning
  - [x] `ddo-refine` skill updated with `DanglingRefError` handling and human authorization gate framing
- [x] Structured Persona Nomenclature (v0.0.4)
  - [x] AV-NN Attack Vector tables in `product_critic` and `scientific_reviewer` personas
  - [x] `ddo-red-team` skill binds `category` to persona's `AV-NN: <name>`; hard-fails on missing table
  - [x] `ddo-create-persona` skill — interactive guided authoring for new personas
  - [x] `tests/unit/test_personas.py` rewritten as glob-based AV-table validator
  - [x] `append_evidence` and `append_review_log` ops removed (`ddo/refine.py`, `ddo/review.py`)
- [x] Style and Tone Configuration (v0.0.5)
  - [x] `ddo/styles/` module — `formal_professional`, `conversational`, `technical_precise` profiles (5-section phrasing-only contract, mirrors `ddo/personas/`)
  - [x] `ddo-create-style` skill — interactive guided authoring, mirrors `ddo-create-persona`
  - [x] Optional `meta.style_profile` schema field (`prd.yaml`, `scientific_report.yaml`) with live defaults; render-invisible
  - [x] `ddo-ingest` / `ddo-interview` style injection — stem-validated, untrusted phrasing-only guidance, body-scoped, sentinel-routed on would-be fabrication
  - [x] `ddo-red-team` register-aware critique — active style surfaced in report header; persona stem-validation gap closed
  - [x] `tests/unit/test_styles.py` glob-based structural validator with negative-case parity
- [ ] Scientific report workflow tutorial

## 🤝 Support

For support, bug reports, or feature requests, please open a GitHub issue.

## 🙏 Credits

DDO is derived from and built upon **[Aegis](https://github.com/tjmustard/Aegis)**, a personal
document-processing framework authored by Thomas Mustard. Aegis is the upstream predecessor that
established the core architectural concepts this codebase implements: YAML as source of truth,
deterministic rendering pipelines, and an AI-augmented editorial loop with mandatory
human-in-the-loop gates.

**DDO is a personal project.** All architectural patterns and conceptual foundations originate
in Aegis, which was authored prior to this work.

> The Aegis repository is currently private and will be made public in an upcoming release.

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
