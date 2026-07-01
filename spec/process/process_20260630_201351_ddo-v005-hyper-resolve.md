# Process Document: DDO v0.0.5 — Resolution Phase (Red Team → SuperPRD + MiniPRDs)

**Generated:** 2026-06-30T20:13:51-07:00
**Session Focus:** `/hyper-resolve` — mediate the v0.0.5 Red Team findings with the human, adjudicate every Critical/Major/Minor item, and compile the final SuperPRD + MiniPRDs for the "Style and Tone Configuration" feature.

## Problem Statement

DDO v0.0.5 ("Style and Tone Configuration") had already been through `/hyper-architect` (Draft PRD) and `/hyper-redteam` (an adversarial critique producing 10 findings — 2 Critical, 4 Major, 4 Minor). Those findings needed to be triaged with the human into definitive architectural decisions, and the specification needed to be finalized into a compiled SuperPRD plus one MiniPRD per implementation module. Without this resolution step, the Draft's cognitive-only enforcement design had known holes (chiefly: a style directive could induce an unsourced fact that ships past every automated guard) and no executable, dependency-ordered plan.

## Starting State

- Git HEAD: `a9172f0 v0.0.4` — v0.0.4 (Structured Persona Nomenclature) shipped and audited; 183 tests passing; all 26 hypergraph nodes `clean`.
- `spec/active/Draft_PRD.md` — the v0.0.5 Draft (9 confirmed decisions A1–A9; execution checklist MP-1..MP-6).
- `spec/active/RedTeam_Report.md` — 10 findings RT-1..RT-10 with a grounding pass that had already *verified* three load-bearing safety claims against source (render-invisibility TRUE, validation-permissiveness TRUE, parallel `meta.persona` traversal gap TRUE).
- `spec/compiled/` — prior SuperPRDs (v0.0.1–v0.0.4) and `architecture.yml`; no v0.0.5 artifacts yet.
- The MiniPRD/SuperPRD templates in `.agents/schemas/` are deprecated stubs that defer to `AGENTS.md → Schema Definitions` (the canonical schema).

## Approach & Methodology

Spec-driven, human-in-the-loop mediation following the `/hyper-resolve` state machine (Phase 1 high-severity collisions → Phase 2 NFRs/edge cases → Phase 3 candidate-artifact check → Phase 4 compilation & archival). The pacing rule (≤2 questions per turn, always as forced trade-offs framed around Cost vs Risk vs Time) was honored strictly: findings were presented via `AskUserQuestion` with labelled options and code-preview mockups so the human could *select* rather than free-type. Sequencing rationale: adjudicate the two Criticals first (they change the safety posture), then the architectural Majors, then batch the Minors as proposed defaults, and only compile once every flag had a documented decision.

## Steps Taken

1. Read `.agents/skills/hyper-resolve/SKILL.md` to load the state-machine and the critical rules (≤2 questions/turn; forced trade-offs via `AskUserQuestion`; strict scope = only Red Team items).
2. Gathered context: read `spec/active/RedTeam_Report.md` (10 findings + grounding pass) and `spec/active/Draft_PRD.md` (A1–A9, MP-1..MP-6), and confirmed `spec/compiled/` had no v0.0.5 artifacts. Reason: the report and draft are the sole in-scope inputs.
3. **Phase 1, turn 1 — the two Criticals.** Presented RT-1 (style-induced fabrication is undetectable — `validation.py` scans for *sentinels*, not *fabrications*) and RT-2 (style file is an un-content-scanned injection channel). Human chose **RT-1 → route into the sentinel channel** and **RT-2 → sandbox at read-time + document**.
4. **Phase 1, turn 2 — architectural Majors.** Presented RT-3 (persona⊥style decoupling → non-convergent loop) and RT-4 (refine can store a traversal payload in `meta.style_profile`). Human chose **RT-3 → surface style in the Red Team header** and **RT-4 → distrust stored values (cognitive re-validation)**.
5. **Phase 1, turn 3 — remaining Majors.** Presented RT-5 (style over-application to `evidence_bank` verbatim quotes) and RT-6 (live-default bootstrapping deadlock). Human chose **RT-5 → body-only scope** and **RT-6 → keep live defaults + atomic MP-1/MP-2 landing + ordered DAG**.
6. **Phase 2 — Minors.** Grouped RT-7/8/9 as proposed standard defaults (falsifiable US-001 + metric split; present-but-invalid = hard-fail; `test_style_dir_has_files` guard + negative parity) → human **approved all**. Surfaced RT-10 separately, noting RT-3 already edits `ddo-red-team.md` so closing the parallel `meta.persona` gap is nearly free → human chose **close it now** (superseding Draft decision A6).
7. **Phase 3 — candidate-artifact check.** Confirmed A7 already routes the one non-deterministic surface (style-bounded prose) to HITL review, and `style_profile` is render-invisible so no golden baselines change. No new routing needed; no conflict.
8. **Phase 4 — compilation.** Loaded the canonical schema from `AGENTS.md → Schema Definitions` (the `.agents/schemas` templates are deprecated), and read two v0.0.4 archived MiniPRDs (`SkillCreatePersona`, `TestPersonas`) plus the v0.0.4 SuperPRD header to match the established format and detail level. Extracted exact node IDs from `architecture.yml`. Wrote `SuperPRD_v0.0.5_StyleAndToneConfiguration.md` (with a §5.2 Resolved Trade-offs Log covering all 10 findings and a DAG execution checklist) and 7 MiniPRDs to `spec/compiled/`.
9. **Phase 4 — archival.** Ran the archival script; `python` was not on PATH (exit 127), so fell back to `python3`. It moved `Draft_PRD.md` + `RedTeam_Report.md` to `spec/archive/20260630_201130_DDO_v0_0_5_StyleAndToneConfiguration/` and restored `spec/active/.gitkeep`.
10. Updated project memory (`project_ddo_v005.md` + the `MEMORY.md` index line) to record RESOLVE COMPLETE and the 7-MiniPRD DAG.

## Key Decisions & Rationale

| Decision | Alternatives Considered | Reason Chosen |
|---|---|---|
| RT-1: Route fabrication into the `[[DDO::REQUIRES_INPUT:]]` sentinel channel | Accept & downgrade the claim; add a mechanical scan | Converts an undetectable failure (silent fabrication) into a render-blocking one, using the gate validation *does* enforce; stays cognitive-only (no Python change) |
| RT-2: Read-time sandbox (untrusted phrasing-only) + documented accepted risk | Also add a create-style content scan; accept undocumented | Read-time framing covers *all* authoring paths (hand-authored/edited/create-style), not just one; names HITL-review-at-merge as the accepted residual |
| RT-3: Surface `style_profile` in the Red Team report header | Document pairings only; enforce persona↔style coupling in schema | Makes the critique register-aware for ~1 line; schema coupling would violate the cognitive-only / no-Python scope |
| RT-4: Read-time gate re-validates *stored* values on every read | Forbid `set`/`insert` on `meta.style_profile` in refine; both | Keeps the "no `refine.py` / no Python change" invariant; the read-time boundary is already there and just needs to distrust provenance |
| RT-5: Scope style to `content.sections[*].body` only | Style all authored prose | Protects verbatim `evidence_bank` quotes/citations and traceability |
| RT-6: Keep live defaults + atomic MP-1/MP-2 + ordered DAG | Conservative absent/commented default; keep live w/ no ordering | Preserves out-of-box register while closing the bootstrapping deadlock; `--force` re-ingest restyle surfaced as an accepted caveat |
| RT-7/8/9: Adopt proposed defaults | Custom handling | Cheap, high-value hardening (falsifiable AC, hard-fail on invalid, non-vacuous tests) |
| RT-10: Close the `meta.persona` traversal gap now | Defer + document; defer silently | RT-3 already edits `ddo-red-team.md`, so the marginal cost is ~3 lines; eliminates asymmetric hardening (supersedes A6) |
| 7 MiniPRDs (added `RedTeamStyleAware`) vs the Draft's 6 | Fold RT-3/RT-10 into an existing MiniPRD | `skill_red_team` is a distinct modified node; it deserves its own executable unit |

## Artifacts Created / Modified

| Artifact | Path | Change |
|---|---|---|
| SuperPRD v0.0.5 | `spec/compiled/SuperPRD_v0.0.5_StyleAndToneConfiguration.md` | created |
| MiniPRD — Styles module | `spec/compiled/MiniPRD_Styles.md` | created |
| MiniPRD — schema field + live defaults | `spec/compiled/MiniPRD_SchemaStyleField.md` | created |
| MiniPRD — style injection | `spec/compiled/MiniPRD_StyleInjection.md` | created |
| MiniPRD — create-style skill | `spec/compiled/MiniPRD_SkillCreateStyle.md` | created |
| MiniPRD — test_styles.py | `spec/compiled/MiniPRD_TestStyles.md` | created |
| MiniPRD — red-team register-awareness + persona gate | `spec/compiled/MiniPRD_RedTeamStyleAware.md` | created |
| MiniPRD — hypergraph reconciliation | `spec/compiled/MiniPRD_Hypergraph.md` | created |
| Draft PRD (archived) | `spec/archive/20260630_201130_DDO_v0_0_5_StyleAndToneConfiguration/Draft_PRD.md` | moved |
| Red Team report (archived) | `spec/archive/20260630_201130_DDO_v0_0_5_StyleAndToneConfiguration/RedTeam_Report.md` | moved |
| Project memory | `~/.claude/.../memory/project_ddo_v005.md` + `MEMORY.md` | updated |

## Results & Outcomes

- All 10 Red Team findings (RT-1..RT-10) now carry a documented, human-adjudicated decision, captured in the SuperPRD §5.2 Resolved Trade-offs Log.
- A compiled, executable specification exists: 1 SuperPRD + 7 MiniPRDs, each with a Confidence Mandate (all 10/10), Atomic User Stories, an Implementation Plan, a Negative-Space list, and Integration Tests.
- The execution plan is a DAG (not a flat list): `MiniPRD_Styles` blocks everything; `SchemaStyleField` is atomic with it; `Hypergraph` runs last. This encodes the RT-6 fix directly.
- The keystone safety hole (RT-1) is closed in spec: style-induced fabrication is routed into the sentinel channel that `validation.py` already blocks.
- `spec/active/` is flushed back to `.gitkeep`; the Draft + Red Team report are preserved under `spec/archive/20260630_201130_DDO_v0_0_5_StyleAndToneConfiguration/`.
- Blast radius recorded: +3 new nodes (`ddo_styles`, `skill_create_style`, `test_styles_unit`); 4 nodes → `needs_review` (`ddo_schemas`, `ddo_skills`, `skill_interview`, and — new this session — `skill_red_team`).

## How to Reproduce

Prerequisite state: on a branch at v0.0.4 (`a9172f0`) with `spec/active/Draft_PRD.md` and `spec/active/RedTeam_Report.md` present, and `python3` available (note: `python` may not be on PATH — use `python3` or `uv run`).

1. Invoke `/hyper-resolve`. It reads `.agents/skills/hyper-resolve/SKILL.md` and the two `spec/active/` inputs.
2. Answer the forced-trade-off questions in order (≤2 per turn). The adjudicated set for this feature was: RT-1 route-into-sentinel; RT-2 read-time-sandbox; RT-3 surface-style-in-header; RT-4 distrust-stored-values; RT-5 body-only; RT-6 keep-live+atomic-DAG; RT-7/8/9 approve-defaults; RT-10 close-now.
3. The agent compiles `spec/compiled/SuperPRD_v0.0.5_*.md` + 7 `MiniPRD_*.md` using the schema in `AGENTS.md → Schema Definitions` (the `.agents/schemas/*_Template.md` files are deprecated stubs — do not use them).
4. The agent runs `python3 .agents/scripts/archive_specs.py DDO_v0_0_5_StyleAndToneConfiguration`, which prints the absolute archive path and restores `spec/active/.gitkeep`.
5. Expected end state: 8 new files in `spec/compiled/`, an archive folder under `spec/archive/`, and an empty `spec/active/`.

Gotchas / order-dependencies:
- Pull exact node IDs from `spec/compiled/architecture.yml` before writing the blast radius — do not guess (`skill_red_team`, `skill_interview`, `ddo_schemas`, etc.).
- Do NOT run `/hyper-execute` in the same conversation thread — per CLAUDE.md's context-window rule, start a fresh thread for execution so it doesn't inherit the resolution history.

## Patterns & Lessons

- **Verify against the codebase before compiling.** The Red Team's grounding pass had already checked render-invisibility, validation-permissiveness, and the persona traversal gap against source; trusting those verified verdicts kept the resolution scoped to *real* risk instead of re-litigating settled facts.
- **A cheap adjacency can upgrade a deferral.** RT-10 was a "Minor, deferred" item until RT-3's decision already put us inside `ddo-red-team.md` — at which point closing the parallel `meta.persona` gap became ~3 lines and the right call. Watch for these when two findings touch the same file.
- **Route undetectable failures into a channel a gate already enforces.** RT-1's fix works precisely because it converts "silent fabrication" (nothing catches it) into "emit a sentinel" (validation blocks it) — turning a cognitive hope into a mechanical guard without any new mechanism.
- **Cognitive-only scope shapes the answer.** For RT-4 the more robust option (a deterministic refine-side block) was rejected to preserve the "no Python module changes" invariant; the read-time re-validation achieves the security goal within scope.
- **Encode ordering as a DAG, not prose.** RT-6's bootstrapping deadlock is a sequencing bug; the fix is structural (atomic landing + explicit blocks/blocked-by), which the MiniPRD set now carries so `/hyper-execute` can't land things in a broken order.
- **Environment note:** `python` is not on PATH in this environment; use `python3` (or `uv run`) for the `.agents/scripts/*.py` helpers.
