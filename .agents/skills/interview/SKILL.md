---
name: interview
description: Paced 3-question-at-a-time Q&A over a module's adversarial questionnaire. Saves progress to state_graph.yml after each answer, supporting pause (DONE) and resume across sessions.
---

# Interview Skill

**Invocation:** `claude /interview [module_id] --workspace <path>`

This skill is run interactively by the operator. It presents adversarial questions from the master questionnaire in batches of 3, recording each answer and saving progress so the session can be resumed at any time.

## Mode Detection

Parse `$ARGUMENTS` to extract:
- `module_id` — first positional argument
- `--workspace <path>` — the workspace directory path

If either is missing, print an error and exit with code 1.

## Execution Steps

**Step 1 — Load context**
- Resolve `workspace_path` from `--workspace`.
- Read `state_graph.yml`. Find the module matching `module_id`.
- Read `adversarial_state.last_answered_index` from the module (default `0` if not set).
- The questionnaire file path is `<workspace>/active/module_<module_id>_questions.md`.

**Step 2 — Parse questionnaire**
- Read `active/module_<module_id>_questions.md`.
- Extract all numbered questions: lines matching the pattern `^\d+\.` (across all persona sections). Preserve order.
- If the file does not exist or is empty, abort: `"ERROR: No questionnaire found for module '{module_id}'. Run /redteam first."` Exit code 1.

**Step 3 — Resume check**
- Determine starting index = `last_answered_index`.
- Slice the question list from `last_answered_index` onward to get unanswered questions.
- If no unanswered questions remain (slice is empty), print:
  `"All questions have been answered. Run /integrate {module_id} to synthesize the final document."`
  Exit with code 0.

**Step 4 — Paced Q&A loop**
For each batch of up to 3 unanswered questions:

1. For each question in the batch (up to 3):
   - `global_index` = `last_answered_index + 1` (1-based display)
   - `total` = total question count
   - Print: `"Question {global_index} of {total}: {question_text}"`
   - Accept the operator's answer. Use multi-line input: read lines until a blank line is entered.
   - Append to `<workspace>/transcripts/module_<module_id>_answers.md`:
     ```
     ## Q{global_index}: {question_text}
     {answer}

     ```
   - Increment `last_answered_index` by 1.
   - Save `state_graph.yml` atomically with the updated `last_answered_index` value.

2. After every 3rd answer (or if the batch ends naturally):
   - Print: `"3 questions answered. Type DONE to pause, or press Enter to continue."`
   - Read operator input.
   - If operator types `DONE`, print:
     `"Session saved. Re-run /interview {module_id} --workspace {workspace_path} to continue from question {last_answered_index + 1}."`
     Exit with code 0.

**Step 5 — Completion**
When all questions are exhausted naturally (no DONE):
- Validate that `transcripts/module_<module_id>_answers.md` is non-empty and has grown since the session started.
- If no new answers were added (operator typed DONE immediately at the first prompt), do NOT advance status. Exit with code 0.
- Otherwise, update `state_graph.yml` atomically:
  - Set `module.status = "pending_integration"`
  - Set `module.adversarial_state.status = "ready_for_integration"`
- Print: `"Interview complete. All {total} questions answered. Run orchestrator to proceed to integration."`
Exit with code 0.

## Atomic State Write Pattern

Always write `state_graph.yml` via tmp → rename:
1. Read current YAML.
2. Update the target field(s).
3. Write to `state_graph.yml.tmp`.
4. Rename `state_graph.yml.tmp` → `state_graph.yml`.

## Constraints

- DO NOT advance module status to `pending_integration` unless all questions are exhausted or `last_answered_index` equals total question count.
- DO NOT write to `state_graph.yml` non-atomically.
- DO NOT re-present already-answered questions on resume.
- DO NOT modify the master questionnaire file — it is read-only in this skill.
- DO NOT advance status if operator types DONE without answering any new questions.
