# MiniPRD: Promote Skill (Candidate Output Review)
**Hypergraph Node ID:** `skill_promote`
**Parent Node:** `candidate_output_protocol`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As an operator, I want `/promote [module_id] --workspace <path>` to present each candidate output for the module so that I can review and approve or reject each one.
* **US-002:** As an operator, I want `APPROVE` to move the file to `tests/fixtures/` and log the event so that approved outputs are traceable.
* **US-003:** As an operator, I want `REJECT` to log a reason and flag the module for re-run so that I can track why an output was rejected.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Read `module_id` from CLI args. Load `state_graph.yml`. Identify the three candidate outputs for this module:
  - `tests/candidate_outputs/draft_<module_id>.md`
  - `tests/candidate_outputs/module_<module_id>_questions.md`
  - `tests/candidate_outputs/final_<module_id>.md`
  Present only those that exist.
- [ ] Task 2: For each candidate output file (in order: draft → questions → final):
  - Print the filename and full file contents to the operator.
  - Prompt: `"Type APPROVE to accept this output, or REJECT <reason> to flag it for re-run."`.
  - Accept operator input.
- [ ] Task 3: **On APPROVE:**
  - Move file from `tests/candidate_outputs/<filename>` to `tests/fixtures/<filename>` using `shutil.move()`.
  - Update the corresponding approval flag in `state_graph.yml` (`candidate_outputs.draft_approved`, `candidate_outputs.questions_approved`, or `candidate_outputs.compiled_approved`). Use atomic write.
  - Print: `"APPROVED: <filename> moved to tests/fixtures/."`.
- [ ] Task 4: **On REJECT:**
  - Parse rejection reason from input (everything after `REJECT `).
  - Log to `state_graph.yml`: append `{"file": "<filename>", "reason": "<reason>", "timestamp": "<ISO8601>"}` to a `rejections` list on the module. Use atomic write.
  - Set module status to `pending_integration` (revert for re-run).
  - Print: `"REJECTED: <filename>. Module reset to pending_integration. Reason logged. Fix the issue and re-run /integrate."`.
  - Stop processing remaining candidate outputs for this module (operator must re-run after fix).
- [ ] Task 5: If all three candidate outputs are approved, update module status to `integrated` in `state_graph.yml`. Call `archive_manager.archive_draft(module_id)` to flush the active draft. Print: `"Module '{module_id}' fully approved and integrated."`.

## 4. The Negative Space (Constraints)
* **DO NOT** automatically approve any output — require explicit `APPROVE` input.
* **DO NOT** advance status to `integrated` unless ALL three applicable candidate outputs are approved.
* **DO NOT** modify `tests/fixtures/` contents — only add files, never delete.
* **DO NOT** write to `state_graph.yml` non-atomically.
* **DO NOT** continue reviewing remaining files if one is rejected — halt and wait for re-run.

## 5. Integration Tests & Verification
* **Test 1 (Deterministic):** Run `/promote novelty` with all three candidate output files present. Type `APPROVE` for all three. Expected: all three files moved to `tests/fixtures/`; all three approval flags `true` in `state_graph.yml`; module status = `integrated`; archive called.
* **Test 2 (Deterministic):** Run `/promote novelty`. Type `APPROVE` for draft and questions, then `REJECT The integration missed the edge case about X` for the final. Expected: draft and questions approved and moved; final NOT moved; `rejections` list in `state_graph.yml` contains the reason; module status = `pending_integration`.
* **Test 3 (Deterministic):** Run `/promote novelty` when no candidate output files exist for the module. Expected: prints informative message that no candidates are pending; exits cleanly.
* **Test 4 (Deterministic):** Verify that `tests/fixtures/` contains the approved files after a successful `/promote` run, and `tests/candidate_outputs/` no longer contains those files.
