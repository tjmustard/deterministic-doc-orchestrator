# MiniPRD: Interview Skill (Resumable Paced Q&A)
**Hypergraph Node ID:** `skill_interview`
**Parent Node:** `orchestrator_core`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As an operator, I want `/interview [module_id] --workspace <path>` to present exactly 3 unanswered questions at a time so that I am not overwhelmed.
* **US-002:** As an operator, I want to type `DONE` to pause the session and have my progress saved so that I can resume later.
* **US-003:** As an operator, I want re-running the skill to resume from the next unanswered question so that I never repeat answered questions.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Read `module_id` from CLI args. Load `state_graph.yml`. Read `adversarial_state.last_answered_index` (default `0` if not set). Read `adversarial_state.master_questionnaire` path.
- [ ] Task 2: Parse the master questionnaire file (`active/module_<module_id>_questions.md`) into an ordered list of questions. Questions are identified by numbered list items matching `^\d+\.` across all persona sections.
- [ ] Task 3: Determine the starting index: `last_answered_index`. Slice the question list from this index. If no unanswered questions remain, print: `"All questions have been answered. Run /integrate [module_id] to synthesize the final document."` Exit with code 0.
- [ ] Task 4: Present questions in batches of 3:
  - Print: `"Question {global_index} of {total}: {question_text}"`
  - Accept operator's answer (multi-line input, terminated by a blank line).
  - Append to `transcripts/module_<module_id>_answers.md`: `## Q{global_index}: {question_text}\n{answer}\n`.
  - Increment `last_answered_index` by 1. Save to `state_graph.yml` atomically after each answer.
  - After every 3rd answer, check: does the operator want to continue? Print: `"3 questions answered. Type DONE to pause, or press Enter to continue."`.
  - If operator types `DONE`, print: `"Session saved. Re-run /interview {module_id} to continue from question {last_answered_index + 1}."` Exit with code 0.
- [ ] Task 5: When all questions are exhausted naturally, update `state_graph.yml`: set module status to `pending_integration`, set `adversarial_state.status` to `ready_for_integration`. Print: `"Interview complete. All {total} questions answered. Run orchestrator to proceed to integration."` Exit with code 0.
- [ ] Task 6: Validate that `transcripts/module_<module_id>_answers.md` is non-empty and has grown since the last run before updating `state_graph.yml`. If no new answers were added (operator typed `DONE` immediately), do not advance status.

## 4. The Negative Space (Constraints)
* **DO NOT** advance module status to `pending_integration` unless all questions are exhausted or `last_answered_index` equals total question count.
* **DO NOT** write to `state_graph.yml` non-atomically.
* **DO NOT** re-present already-answered questions on resume.
* **DO NOT** modify the master questionnaire file — it is read-only in this skill.

## 5. Integration Tests & Verification
* **Test 1 (Deterministic):** Run `/interview novelty` with 9 questions and `last_answered_index = 0`. Answer 3 questions, type `DONE`. Expected: `last_answered_index = 3` in `state_graph.yml`; 3 answers in `transcripts/module_novelty_answers.md`; module status unchanged (still `pending_interview`).
* **Test 2 (Deterministic):** Re-run `/interview novelty` with `last_answered_index = 3`. Expected: presents questions 4, 5, 6 — not 1, 2, 3.
* **Test 3 (Deterministic):** Run `/interview novelty` with `last_answered_index = 9` and 9 total questions. Expected: prints "all questions answered" message; exits code 0; module status unchanged (integration is a separate step).
* **Test 4 (Deterministic):** Answer all 9 questions in one sitting (no `DONE`). Expected: `last_answered_index = 9`; module status = `pending_integration`; `adversarial_state.status = ready_for_integration`.
* **Test 5 (Deterministic):** Type `DONE` immediately without answering any questions. Expected: `last_answered_index` unchanged; no status change; answers file unchanged.
