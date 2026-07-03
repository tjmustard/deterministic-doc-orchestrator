# Process Document: DDO v0.0.6 — Resolution Phase (Red Team → SuperPRD + MiniPRDs)

**Generated:** 2026-07-02T22:43:41Z
**Session Focus:** Running `/hyper-resolve` for DDO v0.0.6 "Expanded Ecosystem Tutorials" — mediating 15 Red Team findings into user-adjudicated decisions, then compiling the final SuperPRD and MiniPRDs and archiving the active specs.

## Problem Statement

DDO v0.0.6 had passed the Architect and Red Team phases: a Draft PRD existed and an adversarial review had produced `RedTeam_Report.md` with 15 findings (2 Critical, 5 Major, 8 Minor). The specification could not advance to implementation until every finding had a documented decision and the working drafts were compiled into the ground-truth `spec/compiled/` artifacts (SuperPRD + executable MiniPRDs). This session ran the resolution (mediation → compilation → archival) phase.

## Starting State

- **Git HEAD:** `6f36c47 v0.0.5` — the repo was released through v0.0.5; v0.0.6 was spec-only, nothing committed.
- **`spec/active/`** held the two Phase-1 working drafts: `Draft_PRD.md` (Architect output) and `RedTeam_Report.md` (15 findings RT-01..RT-15, with a consolidated ledger prioritizing the two Critical guard findings).
- **`spec/compiled/`** held the prior versions' SuperPRDs (v0.0.1–v0.0.5) and `architecture.yml` (28 clean nodes); no v0.0.6 artifacts yet.
- **The central risk** flagged by the Red Team: the anti-rot guard (`test_tutorial_refs.py`) was the PRD's only *new* enforcement surface, and as drafted it could pass green while checking nothing (RT-01 scope miss, RT-02 unspecified pairing).

## Approach & Methodology

Spec-driven mediation following the `/hyper-resolve` state machine (Phase 1 high-severity collisions → Phase 2 NFRs/edge cases → Phase 3 Candidate-Artifact routing → Phase 4 compilation & archival). Two hard rules governed the interaction: **no more than two questions per turn**, and **forced trade-offs framed as Cost/Risk/Time** presented via `AskUserQuestion` rather than open-ended prompts. Before mediating, the session re-verified the Red Team's load-bearing ground-truth claims against the actual repo so the trade-offs were framed on facts, not prose.

## Steps Taken

1. **Read the skill + both drafts.** Loaded `hyper-resolve/SKILL.md`, then `Draft_PRD.md` and `RedTeam_Report.md` to reconstruct the 15 findings and their suggested dispositions. Confirmed the pipeline position (Architect + Red Team done; Resolve pending).

2. **Verified ground-truth facts before framing trade-offs.** Ran targeted checks rather than trusting the report at face value: `ddo/validation.py:106` (confirmed it raises on `total_refs == 0` → RT-04 real); `EXAMPLES` defined twice in `conftest.py` and `test_render_determinism.py` (RT-03 real); `pyproject.toml` ruff `exclude = ["PRDs/"]` only (RT-06 real); existing tutorial directory layout and `code_samples/` contents.

3. **Phase 1, turn 1 — the two most load-bearing decisions.** Presented the anti-rot guard design (RT-01/02/05) and the zero-hallucination collision (RT-04) as forced trade-offs. User chose **explicit `EXPECTED_MIRRORS` map** (walk `input_files/`, cover both `tests/data/` and `tests/fixtures/`, assert map non-empty + Tutorial-1 anchor present) and **casual evidence sourced from each tutorial's narrative doc** (no `validation.py` change).

4. **Phase 1, turn 2 — RT-06 and RT-07.** Asked how `code_samples` interact with ruff, and how to resolve the unguarded `output_files/` claim. User answered RT-06 with a *counter-question* ("can we skip MD files from ruff while keeping the folder?") and chose "add `output_files` determinism guard" for RT-07.

5. **Corrected a misconception on RT-06.** Verified with `uv run ruff check tutorials/ --show-files` that ruff only lints `.py` files under `tutorials/` (the three existing green samples) and never touches `.md`/`.sh`. Explained that "skip MD" is a no-op and that excluding the folder would silently drop the existing samples from coverage — so the real decision was only about `.py` samples.

6. **Phase 1, turn 3 — RT-06 (corrected) + RT-08.** With the misconception cleared, user confirmed **ruff-clean `.py` samples, no dir exclusion**, and chose **add `test_schema_meta_refs.py`** to give persona/style resolution a CI surface.

7. **Phase 2 — batched the 8 minors into two default bundles.** Bundle A (RT-03, RT-07-scoping, RT-09, RT-10, RT-11, RT-12) and Bundle B (RT-13, RT-14, RT-15, tutorials-node semantics), each presented as approve/modify/reject per the skill's Phase 2 template. User **approved all defaults** for both bundles.

8. **Phase 3 + MiniPRD split.** Confirmed Candidate-Artifact routing (tutorial prose, personas, styles are HITL-gated, never auto-promoted; golden-baseline promotion stays `DDO_FIXTURE_SIGNOFF`-gated and out of execution scope) and resolved the token-budget question: user chose **4 self-contained per-type MiniPRDs**, which structurally eliminates the RT-08 US-004/US-005 ordering hazard.

9. **Phase 4 — compilation.** Read the canonical SuperPRD/MiniPRD schemas (AGENTS.md §"Schema Definitions"; the standalone `MiniPRD_template.md` is deprecated) and a real archived MiniPRD to match house format. Inspected the concrete template layout (`ddo/templates/typst/<t>.typst` + `jinja2/<t>.<fmt>.jinja2`) and the `EXAMPLES` structure. Wrote `SuperPRD_v0.0.6_ExpandedEcosystemTutorials.md` (with a full RT-01..15 decision log in §5.2) and 9 MiniPRDs (MP-00 through MP-08) in DAG order.

10. **Phase 4 — archival.** First attempt `python .agents/scripts/archive_specs.py ...` failed — `python` is not on this shell's PATH. Re-ran with `python3`; the script archived both active drafts to `spec/archive/20260702_113543_DDO_v0_0_6_ExpandedEcosystemTutorials/` and flushed `spec/active/`.

11. **Updated memory.** Marked `project_ddo_v006.md` and `MEMORY.md` as RESOLVE-complete with the full decision set and next step (`/hyper-execute`).

## Key Decisions & Rationale

| Decision | Alternatives Considered | Reason Chosen |
|---|---|---|
| Anti-rot guard = `input_files/` walk + explicit `EXPECTED_MIRRORS` map spanning `tests/data/` **and** `tests/fixtures/` | Basename walk-and-match; path-existence only | Only design that can't pass green while checking nothing; forces every new copy to be a conscious decision (closes RT-01/02, mitigates RT-05) |
| Casual evidence sourced from a real narrative doc | Relax `validation.py` contract; self-referential synthetic evidence | Preserves zero-hallucination + "no `ddo/*.py` changes"; mirrors the proven adversarial-loop convention |
| `code_samples/*.py` kept ruff-clean; no directory exclusion | Skip `.md` from ruff; exclude `tutorials/` entirely | Ruff never lints `.md`; excluding the folder would silently drop the existing green samples |
| `output_files/` determinism guard for `.html`/`.md` only | Declare `output_files/` illustrative-only | User wanted the stronger reproducibility promise for learners; PDF left illustrative to avoid Typst font/glyph fragility (RT-12) |
| Add `test_schema_meta_refs.py` (persona/style resolution + soft schema-conformance) | Leave AC3 as HITL-only | Gives US-005 AC3 a CI surface; a typo'd `meta.persona` now fails loudly instead of shipping green |
| 4 self-contained per-type MiniPRDs | Concern-grouped (Draft's personas/styles/types split) | Each type ships persona+style+schema+templates+example atomically → structurally eliminates the RT-08 ordering hazard and keeps each MiniPRD under the 50k-token budget |
| Reassign the "render a document" success metric to Tutorial 2 | Add a render step to Tutorial 1 | Tutorial 1 is an evidence/citation lens that inspects, not renders; the metric belonged to the tutorial that actually renders (RT-15) |

## Artifacts Created / Modified

| Artifact | Path | Change |
|---|---|---|
| SuperPRD v0.0.6 | `spec/compiled/SuperPRD_v0.0.6_ExpandedEcosystemTutorials.md` | created |
| MiniPRD MP-00 Harness Prep | `spec/compiled/MiniPRD_00_HarnessPrep.md` | created |
| MiniPRD MP-01 blog_post | `spec/compiled/MiniPRD_01_BlogPost.md` | created |
| MiniPRD MP-02 meeting_notes | `spec/compiled/MiniPRD_02_MeetingNotes.md` | created |
| MiniPRD MP-03 meeting_agenda | `spec/compiled/MiniPRD_03_MeetingAgenda.md` | created |
| MiniPRD MP-04 project_report | `spec/compiled/MiniPRD_04_ProjectReport.md` | created |
| MiniPRD MP-05 Tutorial 1 | `spec/compiled/MiniPRD_05_Tutorial1_EvidenceBank.md` | created |
| MiniPRD MP-06 Tutorial 2 | `spec/compiled/MiniPRD_06_Tutorial2_AuthoringStructures.md` | created |
| MiniPRD MP-07 Tutorial 3 | `spec/compiled/MiniPRD_07_Tutorial3_WritingPersonas.md` | created |
| MiniPRD MP-08 Guard + Hypergraph | `spec/compiled/MiniPRD_08_AntiRotGuard_Hypergraph.md` | created |
| Archived Draft PRD + Red Team Report | `spec/archive/20260702_113543_DDO_v0_0_6_ExpandedEcosystemTutorials/` | created (moved from `spec/active/`) |
| Active spec drafts | `spec/active/Draft_PRD.md`, `spec/active/RedTeam_Report.md` | deleted (flushed by archival) |
| Project memory | `memory/project_ddo_v006.md`, `memory/MEMORY.md` | updated to RESOLVE-complete |

## Results & Outcomes

All 15 Red Team findings (RT-01..RT-15) now have a documented, user-adjudicated decision, captured in SuperPRD §5.2. The specification is compiled into 1 SuperPRD + 9 MiniPRDs in `spec/compiled/`, ordered by an explicit DAG. `spec/active/` is flushed (both drafts safely archived), so the next phase starts without stale context. Confidence is 10/10 with no open questions. The specification is ready for `/hyper-execute`.

The DAG for execution:
`MP-00 HarnessPrep` → `MP-01..04` (blog_post / meeting_notes / meeting_agenda / project_report) → `MP-05 Tutorial 1` (independent) ∥ `MP-06 Tutorial 2` + `MP-07 Tutorial 3` → `MP-08 Guard + Hypergraph` (last).

## How to Reproduce

**Prerequisite state:** on `main` at (or equivalent to) commit `6f36c47`, with `spec/active/Draft_PRD.md` and `spec/active/RedTeam_Report.md` present, and `uv` + `python3` available.

1. `/hyper-resolve` — loads `hyper-resolve/SKILL.md` and begins the state machine.
2. Before mediating, verify the Red Team's load-bearing claims against the repo (e.g. `ddo/validation.py:106`, the duplicated `EXAMPLES` literals, `pyproject.toml` ruff `exclude`, `uv run ruff check tutorials/ --show-files`). This grounds the forced trade-offs.
3. Phase 1: mediate the Critical/Major findings two at a time via `AskUserQuestion`, each option labelled with its Cost/Risk/Time. Expect the guard design (RT-01/02/05), the evidence contract (RT-04), the ruff/`code_samples` question (RT-06), `output_files` (RT-07), and persona/style CI (RT-08).
4. Phase 2: batch the minors into approve/modify/reject default bundles.
5. Phase 3: confirm Candidate-Artifact routing and settle the MiniPRD split.
6. Phase 4: read the canonical schemas from **AGENTS.md** (not the deprecated `MiniPRD_template.md`), match a recent archived MiniPRD for house format, then write `spec/compiled/SuperPRD_v0.0.6_*.md` + the MiniPRDs.
7. Archive: `python3 .agents/scripts/archive_specs.py DDO_v0_0_6_ExpandedEcosystemTutorials` — note the returned absolute archive path and confirm `spec/active/` is empty.

**Gotchas / order-dependencies:**
- `python` is **not** on this environment's PATH — use `python3` (or `uv run`) for `.agents/scripts/*`.
- The archival script must be run *after* all compiled artifacts are written, since it flushes the source drafts.
- Ruff only lints `.py`/`.pyi`/`.ipynb`; do not "fix" a Markdown-lint concern by excluding a directory.

## Patterns & Lessons

- **Verify the report before mediating.** Every Critical/Major decision was framed on a re-checked repo fact (`validation.py:106`, the two `EXAMPLES` literals, the ruff exclude), which kept the trade-offs honest and let a mistaken RT-06 premise be corrected mid-flow rather than baked into the spec.
- **Treat a user's answer that is actually a question as a signal.** When the user asked "can we skip MD files from ruff?", the right move was to verify what ruff actually globs and correct the misconception, not silently pick an option.
- **Restructure to eliminate a hazard, not just document it.** The RT-08 ordering hazard (dangling persona refs) was dissolved by choosing self-contained per-type MiniPRDs, so no execution-discipline note was needed — the structure makes the failure impossible.
- **Make metrics reference tests, not adjectives.** Several success metrics were rewritten to name the specific assertion that proves them (e.g. "guard asserts ≥5 mapped pairs including `ingest_output.yaml`"), per the Red Team's point that a vague metric is satisfiable without the underlying guarantee.
- **The canonical MiniPRD/SuperPRD schemas live in AGENTS.md/CLAUDE.md**, not the `MiniPRD_template.md` file (which is deprecated). Match a recent archived MiniPRD for the real, richer house format.
