# MiniPRD: RedTeam Skill (Multi-Persona Fan-In)
**Hypergraph Node ID:** `skill_redteam`
**Parent Node:** `orchestrator_core`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As an operator, I want `/redteam [module_id] [persona_id] --workspace <path>` to load the specified persona and have it interrogate the module draft, appending adversarial questions to the master questionnaire.
* **US-002:** As an operator, I want the total question count across all personas capped at 50 so that the interview phase remains manageable.
* **US-003:** As an operator, I want `[NEEDS_CLARIFICATION]` markers in the draft to be treated as valid interrogation targets so that gaps are explicitly challenged.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Read `module_id` and `persona_id` from CLI args. Load `state_graph.yml`. Resolve paths for the module draft (`active/draft_<module_id>.md`) and persona snapshot (`personas_snapshot/<persona_id>.md`). Fall back to global persona path if snapshot does not exist (first run before orchestrator copies snapshot).
- [ ] Task 2: Read the current master questionnaire file (`active/module_<module_id>_questions.md`) if it exists. Count existing questions (lines matching `^\d+\.` pattern). Calculate remaining capacity: `max_questions - current_count`. Default `max_questions` to 50 if not set in `state_graph.yml`.
- [ ] Task 3: If `remaining_capacity <= 0`, print: `"WARNING: Question cap of {max_questions} reached. Skipping persona '{persona_id}'."` Exit with code 0 (not a failure).
- [ ] Task 4: Construct the red-team prompt:
  - Load persona file content as the system instruction.
  - Include the full draft content.
  - Instruction: `"Generate adversarial questions targeting every claim, assumption, and `[NEEDS_CLARIFICATION]` marker in the draft. Output strictly a numbered Markdown list. Maximum {remaining_capacity} questions. DO NOT output conversational filler."`
- [ ] Task 5: Invoke the LLM and capture the question list.
- [ ] Task 6: Count generated questions. If count > `remaining_capacity`, truncate to `remaining_capacity` and print: `"WARNING: Persona '{persona_id}' generated {count} questions. Truncated to {remaining_capacity} to stay within cap."`.
- [ ] Task 7: Append a persona header and the (possibly truncated) question list to `active/module_<module_id>_questions.md`. Format: `\n## Persona: <persona_id>\n<question_list>`.
- [ ] Task 8: Copy the full questionnaire to `tests/candidate_outputs/module_<module_id>_questions.md` (overwrite with latest).
- [ ] Task 9: Update `state_graph.yml`: set `adversarial_state.status` to `interview_in_progress`. Use atomic write.
- [ ] Task 10: Print confirmation: persona ID, questions added, total count, remaining capacity.

## 4. The Negative Space (Constraints)
* **DO NOT** deduplicate questions automatically — human reviews the full list.
* **DO NOT** fail the pipeline if the cap is reached — skip gracefully with a warning.
* **DO NOT** use the live global persona file if a snapshot exists — always prefer the snapshot.
* **DO NOT** write non-atomically to `state_graph.yml`.

## 5. Integration Tests & Verification
* **Test 1 (Novel):** Run `/redteam novelty document_examiner_adversary --workspace ./test_job` with a valid draft. Expected: questions appended to `active/module_novelty_questions.md` under a `## Persona: document_examiner_adversary` header; questionnaire copied to `tests/candidate_outputs/`; `adversarial_state.status = interview_in_progress` — Candidate Artifact routing protocol triggered.
* **Test 2 (Deterministic):** Run `/redteam novelty commercial_lead --workspace ./test_job` when the questionnaire already has 50 questions. Expected: prints cap-reached warning; no questions appended; exits with code 0.
* **Test 3 (Deterministic):** Run with a persona that generates 40 questions when only 15 capacity remains. Expected: output is truncated to 15; truncation warning printed.
* **Test 4 (Deterministic):** Verify `[NEEDS_CLARIFICATION]` in the draft is included in the prompt context and results in at least one question targeting the unclear section.
