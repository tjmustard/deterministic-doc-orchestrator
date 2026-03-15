# MiniPRD: Audit State Script
**Hypergraph Node ID:** `audit_state`
**Parent Node:** `orchestrator_core`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As an operator, I want `python audit_state.py --workspace <path>` to reconcile `state_graph.yml` against the actual filesystem so that a crash or manual file move doesn't corrupt the pipeline.
* **US-002:** As an operator, I want a human-readable diff of any status changes made so that I know exactly what was corrected.
* **US-003:** As an operator, I want `failed` modules to be detected and reported clearly so that I know which modules need intervention.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Parse `--workspace <path>` CLI arg. Load `state_graph.yml` using `load_state()`.
- [ ] Task 2: Collect the pre-audit snapshot of all module statuses.
- [ ] Task 3: For each module, apply reconciliation rules in priority order:
  - **Rule 1 (Compiled exists):** If `compiled/final_<module_id>.md` exists AND status is not `integrated`, force status to `integrated`. Log: `"AUDIT FIX: {module_id} — compiled file exists, forced to 'integrated'."`.
  - **Rule 2 (Draft missing):** If status is in `[extracted, pending_interview, pending_integration]` AND `active/draft_<module_id>.md` does not exist, revert status to `pending_extraction`. Log: `"AUDIT FIX: {module_id} — draft file missing, reverted to 'pending_extraction'."`.
  - **Rule 3 (Failed detected):** If status is `failed`, log: `"AUDIT ALERT: {module_id} — module is in 'failed' state. Manual intervention required."`. Do not auto-recover failed modules.
  - **Rule 4 (Stale lock):** If `.orchestrator.lock` exists in the workspace, log: `"AUDIT ALERT: Stale lockfile found at {path}. If no orchestrator is running, delete it manually."`. Do not auto-delete the lockfile.
- [ ] Task 4: Save updated state atomically if any changes were made.
- [ ] Task 5: Print a diff summary:
  - List all modules with status changes: `"{module_id}: {old_status} → {new_status}"`.
  - List all AUDIT ALERTs.
  - If no changes: `"Audit complete. State graph is consistent with filesystem."`.

## 4. The Negative Space (Constraints)
* **DO NOT** auto-recover `failed` modules — only report them.
* **DO NOT** auto-delete the stale lockfile — only report it.
* **DO NOT** write to `state_graph.yml` non-atomically.
* **DO NOT** modify any files other than `state_graph.yml`.

## 5. Integration Tests & Verification
* **Test 1 (Deterministic):** Set a module status to `extracted` then delete `active/draft_<module_id>.md`. Run `audit_state.py`. Expected: status reverted to `pending_extraction`; diff log shows the change.
* **Test 2 (Deterministic):** Create `compiled/final_<module_id>.md` with a module status of `pending_integration`. Run `audit_state.py`. Expected: status forced to `integrated`; diff log shows the change.
* **Test 3 (Deterministic):** Set a module status to `failed`. Run `audit_state.py`. Expected: AUDIT ALERT printed; status NOT changed.
* **Test 4 (Deterministic):** Create a stale `.orchestrator.lock` file. Run `audit_state.py`. Expected: AUDIT ALERT printed; lockfile NOT deleted.
* **Test 5 (Deterministic):** Run `audit_state.py` on a consistent workspace (no issues). Expected: prints "State graph is consistent" message; `state_graph.yml` unchanged.
