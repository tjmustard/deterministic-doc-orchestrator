---
name: promote
description: Presents each candidate output for a module for operator APPROVE/REJECT review. APPROVE moves to tests/fixtures/; REJECT logs reason and resets module. Never promotes automatically.
---

# Promote Skill

**Invocation:** `claude /promote [module_id] --workspace <path>`

This skill is run interactively by the operator after `/integrate` completes. It presents each candidate output file for review. APPROVE moves the file to `tests/fixtures/` and logs the event. REJECT logs a reason and reverts the module to `pending_integration` for re-run.

## Mode Detection

Parse `$ARGUMENTS` to extract:
- `module_id` — first positional argument
- `--workspace <path>` — the workspace directory path

If either is missing, print an error and exit with code 1.

## Candidate Output Files

The three candidate outputs for a module are reviewed in this fixed order:
1. `tests/candidate_outputs/draft_<module_id>.md`
2. `tests/candidate_outputs/module_<module_id>_questions.md`
3. `tests/candidate_outputs/final_<module_id>.md`

Present only those that actually exist. If none exist, print:
`"No candidate outputs are pending review for module '{module_id}'."` Exit with code 0.

## Execution Steps

**Step 1 — Load context**
- Resolve `workspace_path` from `--workspace`.
- Read `state_graph.yml`. Find the module matching `module_id`. If not found, abort.
- Identify which of the three candidate output files exist in `<workspace>/tests/candidate_outputs/`.

**Step 2 — Review loop**
For each existing candidate output file (in order: draft → questions → final):

**Display:**
- Print the filename and full file contents to the operator.
- Print: `"Type APPROVE to accept this output, or REJECT <reason> to flag it for re-run."`

**On APPROVE:**
- Move the file from `tests/candidate_outputs/<filename>` to `tests/fixtures/<filename>` using a file move (read + write + delete original). Create `tests/fixtures/` if it does not exist.
- Update the corresponding approval flag in `state_graph.yml` atomically:
  - `draft_<module_id>.md` → set `module.candidate_outputs.draft_approved = true`
  - `module_<module_id>_questions.md` → set `module.candidate_outputs.questions_approved = true`
  - `final_<module_id>.md` → set `module.candidate_outputs.compiled_approved = true`
- Print: `"APPROVED: {filename} moved to tests/fixtures/."`

**On REJECT:**
- Parse rejection reason: everything after `"REJECT "` in the operator's input.
- Update `state_graph.yml` atomically:
  1. Append to `module.rejections` list: `{file: "<filename>", reason: "<reason>", timestamp: "<ISO8601>"}`.
  2. Set `module.status = "pending_integration"`.
- Print:
  `"REJECTED: {filename}. Module reset to pending_integration. Reason logged. Fix the issue and re-run /integrate."`
- STOP processing remaining candidate outputs for this module. Exit with code 0.

**Step 3 — Full approval**
If all presented candidate outputs were APPROVED:
- Update `state_graph.yml` atomically: set `module.status = "integrated"`.
- Call `archive_manager.archive_draft(module_id, workspace_path)` by running:
  ```
  python archive_manager.py --archive-draft <module_id> --workspace <workspace_path>
  ```
  (If `archive_manager.py` does not expose a CLI, read `archive_manager.py` to invoke the correct function, or import and call `archive_draft` directly via a Python subprocess.)
- Print: `"Module '{module_id}' fully approved and integrated."`

## Atomic State Write Pattern

Always write `state_graph.yml` via tmp → rename:
1. Read current YAML.
2. Modify the target field(s).
3. Write to `state_graph.yml.tmp`.
4. Rename `state_graph.yml.tmp` → `state_graph.yml`.

## Constraints

- DO NOT automatically approve any output — require explicit `APPROVE` input.
- DO NOT advance status to `integrated` unless ALL applicable candidate outputs are approved.
- DO NOT modify `tests/fixtures/` contents — only add files, never delete.
- DO NOT write to `state_graph.yml` non-atomically.
- DO NOT continue reviewing remaining files after a rejection — halt immediately.
