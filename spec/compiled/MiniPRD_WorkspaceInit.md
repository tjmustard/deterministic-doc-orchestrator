# MiniPRD: Workspace Initialization
**Hypergraph Node ID:** `workspace_init`
**Parent Node:** `orchestrator_core`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As an operator, I want to run `python init_workspace.py <job_name>` so that a fully structured, isolated workspace is created for a new document generation job.
* **US-002:** As an operator, I want `init_workspace.py` to validate all referenced template and persona files before creating the workspace so that I catch config errors before the pipeline runs.
* **US-003:** As an operator, I want `init_workspace.py` to refuse to overwrite an existing workspace unless I pass `--force` so that I never accidentally destroy an in-progress job.
* **US-004:** As an operator, I want every new workspace automatically registered in `.agents/workspace_registry.yml` so that other tools can discover all known jobs.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Parse CLI args: `<job_name>` (required), `--workspace-root <path>` (optional, default: current directory), `--force` (flag).
- [ ] Task 2: Check if `<workspace_root>/<job_name>/` already exists and contains a non-empty `state_graph.yml`. If yes and `--force` not set, abort with: `"ERROR: Workspace '<job_name>' already initialized. Use --force to overwrite."` If `--force`, wipe directory and proceed.
- [ ] Task 3: Validate all persona IDs and template IDs provided via CLI args exist in `.agents/schemas/personas/` and `.agents/schemas/templates/` respectively. Fail loudly with a specific missing-file list if any are not found.
- [ ] Task 4: Implement `validate_template(path)` — reads a template `.md` file and checks: (a) at least one `##` section heading exists, (b) at least one `[Insert from transcript]` placeholder exists. Returns `True` or raises `ValueError` with the failing check.
- [ ] Task 5: Create the full workspace directory structure: `transcripts/`, `active/`, `compiled/`, `archive/`, `personas_snapshot/`.
- [ ] Task 6: Write a minimal valid `state_graph.yml` to the workspace root with `global_status: "in_progress"` and `confidence_score: 0` (operator must set this).
- [ ] Task 7: Create `tests/candidate_outputs/` and `tests/fixtures/` directories at the repo root if they do not already exist.
- [ ] Task 8: Append the new workspace absolute path to `.agents/workspace_registry.yml`. Create the file if it does not exist.
- [ ] Task 9: Print a success summary listing all created directories and the registered workspace path.

## 4. The Negative Space (Constraints)
* **DO NOT** create the workspace if any validation step fails — fail before touching the filesystem.
* **DO NOT** use `shutil.rmtree` on `--force` without first confirming the directory is a valid workspace (contains `state_graph.yml`) to avoid accidentally wiping unrelated directories.
* **DO NOT** write to `.agents/workspace_registry.yml` until all other steps have succeeded.
* **DO NOT** introduce any database or external dependency — stdlib only.

## 5. Integration Tests & Verification
* **Test 1 (Deterministic):** Run `python init_workspace.py test_job` in a clean repo. Expected: directory `test_job/` created with all 5 subdirectories; `test_job/state_graph.yml` exists and is valid YAML; `.agents/workspace_registry.yml` contains the absolute path to `test_job/`.
* **Test 2 (Deterministic):** Run `python init_workspace.py test_job` a second time. Expected: exits with non-zero code and prints error message containing `"already initialized"`. No files modified.
* **Test 3 (Deterministic):** Run `python init_workspace.py test_job --force`. Expected: workspace is wiped and recreated cleanly.
* **Test 4 (Deterministic):** Run `python init_workspace.py test_job` with a persona ID that does not exist in `.agents/schemas/personas/`. Expected: exits with non-zero code and prints the missing file path.
* **Test 5 (Deterministic):** Run `validate_template()` on a file with no `[Insert from transcript]` placeholder. Expected: raises `ValueError`.
