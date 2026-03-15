# MiniPRD: Orchestrator (State Machine CLI)
**Hypergraph Node ID:** `orchestrator_core`
**Parent Node:** `orchestrator_core`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As an operator, I want `python orchestrator.py --workspace <path>` to automatically drive the pipeline forward based on `state_graph.yml` so that I don't manually invoke each skill.
* **US-002:** As an operator, I want the orchestrator to acquire a lockfile at startup so that concurrent runs cannot corrupt the state graph.
* **US-003:** As an operator, I want the orchestrator to perform pre-flight checks before running any skill so that config errors are caught immediately.
* **US-004:** As an operator, I want `python orchestrator.py --reset <module_id> --workspace <path>` to safely revert a module to `pending_integration` so that I can re-run integration without manual YAML editing.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Parse CLI args: `--workspace <path>` (required), `--reset <module_id>` (optional flag).
- [ ] Task 2: Implement lockfile acquisition — create `<workspace>/.orchestrator.lock` at startup. If it already exists, abort with: `"ERROR: Orchestrator is already running for this workspace. If this is incorrect, delete .orchestrator.lock and retry."` Use `try/finally` to guarantee lockfile deletion on exit (including exceptions).
- [ ] Task 3: Implement pre-flight validation:
  - (a) Call `load_state()` and verify YAML is valid.
  - (b) Check `confidence_score` field. If < 7, print warning and prompt operator to type `CONFIRM` to proceed.
  - (c) For every `associated_file` path in `state_graph.yml` (personas, templates, inputs), verify the file exists. Collect all missing files and abort with the full list if any are missing.
  - (d) Scan `active/`, `transcripts/`, `compiled/` for symlinks. If any found, abort with the symlink path.
- [ ] Task 4: Implement `--reset <module_id>` mode: load state, find module, call `archive_manager.archive_draft(module_id)` on the compiled file, set status to `pending_integration`, save state atomically, print confirmation. Exit after reset — do not run the pipeline.
- [ ] Task 5: Implement the main orchestration loop — iterate over modules in order:
  - `pending_extraction` → execute `/extract [module_id]` skill; on success set `extracted`; on failure set `failed` and halt.
  - `extracted` → if `skip_adversarial: true`, set `pending_integration` directly. Otherwise, execute `/redteam [module_id] [persona_id]` for each `applied_persona`; set `pending_interview`; set `adversarial_state.status: interview_in_progress`.
  - `pending_interview` → halt with: `"ACTION REQUIRED: Run /interview [module_id] to complete the Q&A. Re-run orchestrator when done."` Exit with code 0.
  - `pending_integration` → execute `/integrate [module_id]` skill; on success set `integrated`; call `archive_manager.archive_draft(module_id)`; on failure set `failed` and halt.
  - `integrated` → skip (already complete).
  - `failed` → halt with: `"ERROR: Module [module_id] is in failed state. Investigate the error, fix the cause, run audit_state.py, then retry."` Exit with code 1.
- [ ] Task 6: Implement persona snapshot — at pipeline start (after pre-flight, before loop), copy all persona files referenced in `state_graph.yml` into `<workspace>/personas_snapshot/`. Skills must be invoked with the snapshot path, not the global path.
- [ ] Task 7: Wrap all subprocess skill calls in `execute_skill(command_list)` — uses `subprocess.run(check=True)`. On `CalledProcessError`, print `stderr` and return `False`. Never retry.

## 4. The Negative Space (Constraints)
* **DO NOT** use an LLM to decide the next step — routing is purely based on `module.status` from YAML.
* **DO NOT** auto-retry any failed skill invocation.
* **DO NOT** proceed if the lockfile exists at startup.
* **DO NOT** write `state_graph.yml` non-atomically — always use `save_state()` from the state graph module.
* **DO NOT** hardcode workspace paths — always use the `--workspace` argument.

## 5. Integration Tests & Verification
* **Test 1 (Deterministic):** Initialize a workspace with one module at `pending_extraction`. Run orchestrator with a mock `/extract` skill that exits 0. Expected: module status advances to `extracted` in `state_graph.yml`.
* **Test 2 (Deterministic):** Run orchestrator with `.orchestrator.lock` already present. Expected: exits with non-zero code and prints lockfile error message.
* **Test 3 (Deterministic):** Run orchestrator with a referenced persona file deleted. Expected: pre-flight aborts with the missing file path before any skill is invoked.
* **Test 4 (Deterministic):** Run orchestrator with a symlink in `active/`. Expected: pre-flight aborts with the symlink path.
* **Test 5 (Deterministic):** Run `orchestrator.py --reset <module_id>` on an `integrated` module. Expected: compiled file moved to `archive/`, module status set to `pending_integration`, lockfile cleaned up.
* **Test 6 (Deterministic):** Run orchestrator with a mock skill that exits 1. Expected: module status set to `failed`, orchestrator exits with code 1, lockfile cleaned up.
