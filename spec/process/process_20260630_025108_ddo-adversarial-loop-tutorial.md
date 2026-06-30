# Process Document: DDO v0.0.2 Adversarial Loop Tutorial Generation

**Generated:** 2026-06-30T02:51:08Z
**Session Focus:** Generate a complete, verified tutorial for the DDO v0.0.2 adversarial loop using the Biodegradable Polyester Optimization Report as worked example.

## Problem Statement

DDO v0.0.2 added three new pipeline phases (Red Team, Interview, Refine) and two new modules (`ddo.review`, `ddo.refine`). The implementation was complete and tested, but there was no tutorial showing how the phases connect end-to-end with a real, meaningful document. The goal was to produce a tutorial that is both instructionally clear and byte-verified against the actual module APIs.

## Starting State

- Git SHA: `f899a83` (v0.0.1 release — last committed state)
- v0.0.2 files existed as untracked: `ddo/review.py`, `ddo/refine.py`, `ddo/skills/ddo-{red-team,interview,refine}.md`, `tests/unit/test_{review,refine}.py`, `tests/integration/test_loop.py`, `spec/compiled/SuperPRD_v0.0.2_AdversarialLoop.md`
- 159 tests passing (78 from v0.0.1, 81 new)
- No tutorial existed for the adversarial loop phases
- Source material: `PRDs/Biodegradable_Polyester_Optimization_Report.md` — a partially fictional scientific paper about copolyester candidates for biodegradable packaging applications

## Approach & Methodology

Used the `/hyper-tutorial-generator` skill (6-step HITL process) with the polyester report as the worked example. The skill gates each step on user approval before proceeding. The tutorial was designed bottom-up: identify meaningful real flaws in the worked example first, then build all artifacts to match those flaws deterministically. A verification script (`verify_tutorial.py`) was written and run against the actual `ddo` modules to confirm byte-level accuracy of all output artifacts.

## Steps Taken

1. Invoked `/hyper-tutorial-generator` with the polyester report as source material. Read the skill SKILL.md to understand the 6-step process.

2. Read existing project memory (`project_ddo_v002.md`) and the SuperPRD to understand what v0.0.2 actually specifies — particularly the 13 RT resolutions, flag split (`decision_recorded` vs `applied`), path DSL grammar, torn-pass detection, and YAML serialization rule.

3. **Identified the worked example's meaningful flaw:** Applied the Z-formula from the paper itself (`Z = 0.3·S + 0.4·Y − 0.1·T − 0.2·E`) to all five candidate materials using Phase II data. Found that PX-103 ranks 1st (Z=51.12), PX-105 2nd (46.44), and the paper's *recommended* PX-104 is actually 3rd (45.96). This is a genuine `Critical / Overreaching Conclusions` finding — the math contradicts the conclusion using the paper's own formula. Also identified a sign-inversion problem: subtracting LD50 penalizes safety (higher LD50 = safer).

4. **HITL Gate 1 — Name/Outline:** Proposed tutorial name `ddo-adversarial-loop-v0.0.2` and 6-section outline (Overview, Prerequisites, Step-by-Step, Expected Output, Troubleshooting, Related links). User accepted.

5. **HITL Gate 2 — Subdirectories:** Proposed `input_files/`, `output_files/`, `code_samples/`, `architecture_evolution/`. User accepted and asked "Do we need to build a scientific_reviewer persona?" — verified that `ddo/personas/scientific_reviewer.md` already existed from v0.0.1 with all 6 attack vectors needed.

6. **Designed `document_data.yaml`:** Chose title `"Copolyester Optimization"` to control the slug (`copolyester-optimization`, keeping all paths consistent). Set `meta.date: "2026.06.29"` (dotted format, required by `validation.validate()`). Set `meta.persona: scientific_reviewer`. Included one evidence entry (`phase_ii_dataset`) and 5 IMRaD sections. Kept flaws intact (wrong conclusion, sign-inversion, missing GC-MS dataset).

7. **Designed all output artifacts** to match what the real `ddo.review` module would produce:
   - `red_team_report_v1.yaml` — 5 findings; F-001 Critical (Z-score contradiction), F-002 Major (sign inversion), F-003 Major (missing limitations), F-004 Major (GC-MS dataset not cited), F-005 Minor (statistical ambiguity)
   - Post-interview state: F-001 `revise` (set body), F-002/F-003 `acknowledge` (null patch), F-004 `add_evidence` (append_evidence), F-005 `defer` (null patch)
   - F-001 and F-004 end with `applied: true`; others `decision_recorded: true, applied: false`
   - `red_team_view_v1.md` — hand-authored to match `render_report_view()` output format exactly
   - `interview_log_v1.yaml` — 5 resolutions with correct `patch` shapes
   - `history.yaml` + `history.md` — 1 pass record; `history.md` hand-authored to match `render_history_view()` exactly

8. **HITL Gate 3 — Draft review:** Presented the full tutorial text and supporting-file plan. User accepted ("Accept & write all files").

9. **Wrote all 12 files** to `tutorials/ddo-adversarial-loop-v0.0.2/`:
   - `tutorial.md`
   - `input_files/document_data.yaml`
   - `input_files/copolyester-optimization.md`
   - `output_files/red_team_report_v1.yaml`
   - `output_files/red_team_view_v1.md`
   - `output_files/interview_log_v1.yaml`
   - `output_files/history.yaml`
   - `output_files/history.md`
   - `code_samples/red_team_call.py`
   - `code_samples/interview_call.py`
   - `code_samples/refine_call.py`
   - `architecture_evolution/pipeline_v0.0.1_to_v0.0.2.md`

10. **Verification:** Wrote `verify_tutorial.py` in the scratchpad directory. Hit `ModuleNotFoundError: No module named 'ddo'` — fixed by prepending `PYTHONPATH="$(pwd)"` to the `uv run` invocation. All 6 checks passed:
    - `document_data.yaml` → `validate()` clean (no warnings)
    - `red_team_report_v1.yaml` → `validate_report()` passes (5 findings)
    - `red_team_view_v1.md` → matches `render_report_view()` byte-for-byte
    - `interview_log_v1.yaml` → `validate_interview_log()` passes (5 resolutions)
    - `apply_patches` → `refine_structural_check` → `validate()` pipeline clean (set + append_evidence landed)
    - `history.md` → matches `render_history_view()` byte-for-byte

11. **HITL Gate 4 — Finalize:** User chose "Finalize — done" (no docs index, no commit, no follow-up tutorial).

12. **`/hyper-document v0.0.2`** — Updated all project documentation to reflect v0.0.2 completion:
    - `pyproject.toml` version 0.0.1 → 0.0.2
    - `CHANGELOG.md` `## [0.0.2] - 2026-06-29` block
    - `README.md` badge, directory structure, pipeline phases, roadmap
    - `.agents/memory/activeContext.md` — v0.0.2 summary
    - `.agents/memory/systemPatterns.md` — v0.0.2 patterns

## Key Decisions & Rationale

| Decision | Alternatives Considered | Reason Chosen |
|---|---|---|
| Use the Z-formula contradiction as the tutorial's Critical finding | Fabricate a simpler flaw | The real math error is more teachable; demonstrates the persona's "Overreaching Conclusions" vector against actual numbers |
| Title `"Copolyester Optimization"` for the example document | Use the full paper title | Shorter title → simpler slug → shorter paths in all tutorial text |
| `meta.date: "2026.06.29"` (dotted) | ISO format `"2026-06-29"` | `validation.validate()` rejects ISO dashes; dotted is the DDO convention |
| Hand-author views to match code output, then verify with script | Generate views by running the code | Writing by hand first forces deep understanding; the verification script is the ground truth check |
| F-005 is `defer` (null patch) | Acknowledge or dispute | Demonstrates all 5 decision types in the tutorial |
| `acknowledge` decisions carry `patch: null` with audit reconcile via `append_review_log` | Use a separate patch op for each decision type | The `interview_log` structure already supports `patch: null`; routing to `meta.review_log` happens in the skill logic |

## Artifacts Created / Modified

| Artifact | Path | Change |
|---|---|---|
| Tutorial main | `tutorials/ddo-adversarial-loop-v0.0.2/tutorial.md` | Created |
| Input document data | `tutorials/ddo-adversarial-loop-v0.0.2/input_files/document_data.yaml` | Created |
| Input rendered MD | `tutorials/ddo-adversarial-loop-v0.0.2/input_files/copolyester-optimization.md` | Created |
| Red team report | `tutorials/ddo-adversarial-loop-v0.0.2/output_files/red_team_report_v1.yaml` | Created |
| Red team view | `tutorials/ddo-adversarial-loop-v0.0.2/output_files/red_team_view_v1.md` | Created |
| Interview log | `tutorials/ddo-adversarial-loop-v0.0.2/output_files/interview_log_v1.yaml` | Created |
| History YAML | `tutorials/ddo-adversarial-loop-v0.0.2/output_files/history.yaml` | Created |
| History MD | `tutorials/ddo-adversarial-loop-v0.0.2/output_files/history.md` | Created |
| Red team code sample | `tutorials/ddo-adversarial-loop-v0.0.2/code_samples/red_team_call.py` | Created |
| Interview code sample | `tutorials/ddo-adversarial-loop-v0.0.2/code_samples/interview_call.py` | Created |
| Refine code sample | `tutorials/ddo-adversarial-loop-v0.0.2/code_samples/refine_call.py` | Created |
| Architecture evolution | `tutorials/ddo-adversarial-loop-v0.0.2/architecture_evolution/pipeline_v0.0.1_to_v0.0.2.md` | Created |
| pyproject.toml | `pyproject.toml` | Version 0.0.1 → 0.0.2 |
| CHANGELOG | `CHANGELOG.md` | `## [0.0.2]` block added |
| README | `README.md` | Badge, directory, pipeline, roadmap |
| Active context | `.agents/memory/activeContext.md` | Full v0.0.2 rewrite |
| System patterns | `.agents/memory/systemPatterns.md` | v0.0.2 patterns added |
| Process document | `spec/process/process_20260630_025108_ddo-adversarial-loop-tutorial.md` | Created (this file) |

## Results & Outcomes

- `tutorials/ddo-adversarial-loop-v0.0.2/` — 12 files, all byte-verified against real `ddo` modules
- `verify_tutorial.py` — 6/6 checks pass: `validate()`, `validate_report()`, `render_report_view()`, `validate_interview_log()`, full patch pipeline, `render_history_view()`
- v0.0.2 documentation complete: README, CHANGELOG, pyproject.toml, memory files all updated
- 159 tests passing, ruff clean

## How to Reproduce

Starting state: branch `main`, `f899a83` as HEAD, all v0.0.2 files untracked.

1. `uv run pytest` — confirm 159 passing
2. `uv run ruff check .` — confirm clean
3. Invoke `/hyper-tutorial-generator` with the polyester report as source
4. At HITL Gate 1 (Name/Outline): accept `ddo-adversarial-loop-v0.0.2`, 6-section outline
5. At HITL Gate 2 (Subdirectories): accept 4 directories; no, you don't need to build the persona
6. At HITL Gate 3 (Draft): accept and write all files
7. Run `PYTHONPATH="$(pwd)" uv run python <scratchpad>/verify_tutorial.py` — all 6 checks pass
8. Choose "Finalize — done"
9. Invoke `/hyper-document v0.0.2`, choose "Yes — bump to v0.0.2"

## Patterns & Lessons

- **Read the real code before writing example artifacts.** The view format, flag names, and serialization details are subtle — `render_report_view()` groups by severity (Critical → Major → Minor) and only shows `[decision_recorded, applied]` tags when the flags are `true`. Hand-authoring these details from memory leads to drift; reading the source first and using a verification script eliminates it.
- **`PYTHONPATH="$(pwd)"` is required** when running scripts outside the project root with `uv run`. The `ddo` package is not installed editably by default; setting `PYTHONPATH` makes it importable without `pip install -e`.
- **The Z-formula error is a real, teachable bug.** The paper's conclusion recommends PX-104, but applying its own Z-formula (`Z = 0.3·S + 0.4·Y − 0.1·T − 0.2·E`) to Phase II data ranks PX-104 third. Using a real mathematical contradiction makes the tutorial more memorable than a fabricated flaw.
- **`acknowledge` decisions route to `meta.review_log` at audit reconcile time, not via a patch in the interview log.** The `patch: null` field signals no document mutation; the skill appends an `append_review_log` patch if needed during the refine phase's audit step.
