# MiniPRD: Archive Manager Script
**Hypergraph Node ID:** `archive_manager`
**Parent Node:** `orchestrator_core`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As the orchestrator, I want `archive_draft(module_id, workspace_path)` to move a module's active draft to the archive with a microsecond-precision timestamp so that the integration agent never reads stale drafts.
* **US-002:** As the orchestrator, I want archive filenames to be collision-proof so that rapid sequential archival operations never overwrite each other.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Implement `archive_draft(module_id: str, workspace_path: Path) -> None`:
  - Resolve `src_file = workspace_path / "active" / f"draft_{module_id}.md"`.
  - Resolve `archive_dir = workspace_path / "archive"`.
  - If `src_file` does not exist, print: `"INFO: No active draft found for {module_id} at {src_file}. Skipping archive."` Return without error.
  - Ensure `archive_dir` exists (`mkdir(parents=True, exist_ok=True)`).
  - Generate timestamp: `datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")` (microsecond precision via `%f`).
  - Construct `archived_filename = f"{timestamp}_draft_{module_id}.md"`.
  - Call `shutil.move(str(src_file), str(archive_dir / archived_filename))`.
  - Print: `"SUCCESS: Archived {src_file.name} → {archive_dir / archived_filename}"`.
- [ ] Task 2: Implement CLI entrypoint: `python archive_manager.py --module <module_id> --workspace <path>`. Calls `archive_draft()` and exits.
- [ ] Task 3: Ensure the function is importable as a module (called by `orchestrator.py` and `/promote` skill without subprocess overhead).

## 4. The Negative Space (Constraints)
* **DO NOT** use second-precision timestamps (`%Y%m%d_%H%M%S` without `_%f`) — microsecond precision is required.
* **DO NOT** write to `archive/` from any skill — only this module may do so.
* **DO NOT** raise an exception if the source file is missing — log and return gracefully.
* **DO NOT** delete files from `archive/` — it is append-only.

## 5. Integration Tests & Verification
* **Test 1 (Deterministic):** Call `archive_draft("novelty", workspace_path)` with `active/draft_novelty.md` present. Expected: file moved to `archive/<timestamp_us>_draft_novelty.md`; `active/draft_novelty.md` no longer exists.
* **Test 2 (Deterministic):** Call `archive_draft("novelty", workspace_path)` twice within the same second. Expected: two distinct files in `archive/` (microsecond suffixes differ); no overwrite.
* **Test 3 (Deterministic):** Call `archive_draft("nonexistent", workspace_path)` with no draft file present. Expected: prints INFO message; no exception raised; exits cleanly.
* **Test 4 (Deterministic):** Verify archived filename matches the pattern `^\d{8}_\d{6}_\d{6}_draft_\w+\.md$`.
