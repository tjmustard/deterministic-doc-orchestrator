
# Product Context

## Purpose
This file contains the high-level "Why" of the project. It defines the goals, user personas, and core value proposition.

## What It Is

A multi-agent CLI pipeline for generating high-stakes technical documents (patent disclosures, PRDs, legal briefs). LLM reasoning is confined to individual skill steps. All routing, state transitions, and file management are deterministic Python — no AI ever decides what happens next.

## Project Goals

- **Goal 1:** Eliminate hallucination-driven document failures by decoupling LLM generation from pipeline control flow.
- **Goal 2:** Produce adversarially stress-tested documents via multi-persona red-teaming before any content is accepted.
- **Goal 3:** Give operators full auditability — every AI output routes to `tests/candidate_outputs/` before human review via `/promote`.
- **Goal 4:** Reach v0.1.0 with all MiniPRDs implemented (integrate, promote, template-architect, forge-persona remaining).

## User Personas

- **Operator:** Patent attorney, product manager, or technical writer running the pipeline on a real document job. Interacts via CLI and agentic IDE slash commands. Needs resumability, clear state, and no silent failures.
- **Agent/Builder:** Claude Code (or compatible) running skill scripts via `claude /{skill} --workspace` subprocesses. Needs atomic state I/O and deterministic exit codes.

## Success Metrics

- Every document module passes through extract → redteam → interview → integrate → promote without operator intervention beyond intended halts.
- All pipeline state survives crashes and restarts via `audit_state.py`.
- No AI output reaches `tests/fixtures/` without explicit operator APPROVE.
- v0.1.0: All MiniPRDs audited and archived; full end-to-end pipeline runnable on a real job.
