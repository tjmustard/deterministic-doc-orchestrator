# MiniPRD: ddo-render Skill

**Hypergraph Node ID:** `skill_render`
**Parent Node:** `skills`
**Implements (atomic):** `path_deriver`
**Depends on:** `build_orchestrator`

## 1. The Confidence Mandate
- **Confidence Score:** 9/10. Thin wrapper; routing + path rules fixed during resolution (#2, #10). No open questions.

## 2. Atomic User Stories
- **US-005:** As an author, the skill derives the correct output path from `meta` and invokes `build.py`, so I don't manage paths by hand.

## 3. Implementation Plan (Task List)
- [ ] Read `document_data.yaml`; extract `meta.date`, `meta.doc_type`, `meta.title`.
- [ ] Compute the **sanitized slug** (`path_deriver`): lowercase → whitelist `[a-z0-9-]` → strip leading dots → forbid `..` → length cap 80.
- [ ] Build folder `Documents/<date>_<doc_type>_<slug>/` and `output/<slug>.<ext>`; **assert realpath containment within `Documents/`** before proceeding.
- [ ] Derive `--template`/`--format` **from `meta`** (CLI flags computed from `meta`, never the reverse).
- [ ] Invoke `uv run --locked ddo/build.py …` with the fully-resolved `--output`; report success/failure (and the gate's precise message on failure).
- [ ] End at `[WAITING FOR USER REVIEW]`.

## 4. The Negative Space (Constraints)
- **DO NOT** write any file or hand-edit a rendered artifact — only invoke `build.py`.
- **DO NOT** duplicate the validation gate's checks.
- **DO NOT** let a derived path escape `Documents/`.
- **DO NOT** pass `meta` to `build.py` for routing — pass resolved CLI flags.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** `meta.title="My Plan"` → slug `my-plan`, path `Documents/<date>_<doc_type>/output/my-plan.<ext>`.
- **Test 2 (Deterministic):** `meta.title="../../etc/passwd"` → sanitized slug; containment assertion holds (`test_slug_containment`).
- **Test 3 (Novel):** skill is invoked by an agent → it produces a path + build invocation and halts at `[WAITING FOR USER REVIEW]` (Candidate Artifact routing: human reviews before trust).
