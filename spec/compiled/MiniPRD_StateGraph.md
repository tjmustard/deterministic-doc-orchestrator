# MiniPRD: State Graph Schema & YAML Parser
**Hypergraph Node ID:** `state_graph`
**Parent Node:** `orchestrator_core`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As the orchestrator, I want a canonical `state_graph.yml` schema so that all tools read and write state consistently.
* **US-002:** As the orchestrator, I want atomic read/write functions so that a crash during a write never corrupts the state file.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Define the canonical `state_graph.yml` schema (see SuperPRD §5.5). Document each field, type, and allowed values in a schema comment block at the top of a `state_graph_schema.py` module.
- [ ] Task 2: Implement `load_state(workspace_path: Path) -> dict` — reads `<workspace_path>/state_graph.yml` using `yaml.safe_load()`. Raises `SystemExit(1)` with a clear error if the file is not found or is not valid YAML.
- [ ] Task 3: Implement `save_state(workspace_path: Path, state_data: dict) -> None` — writes to `<workspace_path>/state_graph.yml.tmp` first, then calls `os.replace()` to atomically rename it to `state_graph.yml`. This ensures a crash during write never corrupts the live file.
- [ ] Task 4: Implement `get_module(state: dict, module_id: str) -> dict` — returns the module dict for a given ID, or raises `KeyError` with a clear message if not found.
- [ ] Task 5: Implement `set_module_status(state: dict, module_id: str, status: str) -> dict` — validates `status` is one of the allowed values before writing. Returns updated state dict (caller must call `save_state()`).
- [ ] Task 6: Write a `VALID_STATUSES` constant: `["pending_extraction", "extracted", "pending_interview", "pending_integration", "integrated", "failed"]`.

## 4. The Negative Space (Constraints)
* **DO NOT** write to `state_graph.yml` directly — always write to `.tmp` then `os.replace()`.
* **DO NOT** allow any status value outside `VALID_STATUSES` — raise `ValueError` immediately.
* **DO NOT** use any external library beyond `pyyaml` and stdlib.
* **DO NOT** implement graph traversal logic in this module — this module is purely data access.

## 5. Integration Tests & Verification
* **Test 1 (Deterministic):** Call `save_state()` and send `SIGKILL` mid-write (simulate via truncation). Expected: `state_graph.yml` is unchanged; `.tmp` file may exist but is incomplete.
* **Test 2 (Deterministic):** Call `load_state()` with a missing file. Expected: `SystemExit(1)` with message containing `"State graph not found"`.
* **Test 3 (Deterministic):** Call `set_module_status()` with `status="invalid_status"`. Expected: `ValueError` raised.
* **Test 4 (Deterministic):** Call `get_module()` with a non-existent `module_id`. Expected: `KeyError` raised with module ID in message.
