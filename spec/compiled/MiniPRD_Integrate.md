# MiniPRD: Integrate Skill (Final Synthesis)
**Hypergraph Node ID:** `skill_integrate`
**Parent Node:** `orchestrator_core`

## 1. The Confidence Mandate
**Agent Instruction:** Before generating any plans or writing code, analyze this document and output a Confidence Score (1-10). If the score is below 9, list strictly the clarifying questions needed to reach 10.

## 2. Atomic User Stories
* **US-001:** As an operator, I want `/integrate [module_id] --workspace <path>` to synthesize the baseline draft and Q&A answers into a final, defensible document section.
* **US-002:** As an operator, I want the integrated output routed to `tests/candidate_outputs/` so that I review it before it is promoted to compiled.

## 3. Implementation Plan (Task List)
- [ ] Task 1: Read `module_id` from CLI args. Load `state_graph.yml`. Resolve paths: `active/draft_<module_id>.md`, `transcripts/module_<module_id>_answers.md`, `associated_files.template`.
- [ ] Task 2: Validate that `transcripts/module_<module_id>_answers.md` is non-empty. If empty, abort with: `"ERROR: No answers transcript found for module '{module_id}'. Run /interview first."`.
- [ ] Task 3: Construct the integration prompt:
  - System instruction: "You are a Resolution Agent. Your role is to synthesize a baseline document draft with adversarial Q&A answers into a final, precise, and defensible document section. Follow the template schema strictly. DO NOT hallucinate. DO NOT introduce claims not supported by either the draft or the answers transcript."
  - Include: original template structure.
  - Include: `active/draft_<module_id>.md` content (labeled "Baseline Draft").
  - Include: `transcripts/module_<module_id>_answers.md` content (labeled "Adversarial Q&A Answers").
  - Instruction: "Update each section of the baseline draft using the relevant Q&A answers. Strengthen claims, fill `[NEEDS_CLARIFICATION]` gaps where answers are available, and document any remaining gaps that still lack answers."
- [ ] Task 4: Invoke the LLM and capture integrated content.
- [ ] Task 5: Write output to `tests/candidate_outputs/final_<module_id>.md` (candidate output — not yet compiled).
- [ ] Task 6: Print: `"Integration complete. Review the output at tests/candidate_outputs/final_{module_id}.md. Run /promote {module_id} to approve and move to compiled/."`.
- [ ] Task 7: Do NOT update `state_graph.yml` status here — status advances to `integrated` only after `/promote` approves the output. (The orchestrator calls `/integrate` and then waits for `/promote` before marking `integrated`.)

**Note:** The orchestrator's post-integrate flow is: invoke `/integrate` → halt and instruct operator to run `/promote` → operator runs `/promote` → on APPROVE, orchestrator advances status to `integrated` and calls `archive_manager`.

## 4. The Negative Space (Constraints)
* **DO NOT** write to `compiled/final_<module_id>.md` directly — output goes to `tests/candidate_outputs/` only.
* **DO NOT** advance module status to `integrated` — that is `/promote`'s responsibility.
* **DO NOT** introduce content not present in the draft or answers transcript.
* **DO NOT** write to `state_graph.yml` in this skill.

## 5. Integration Tests & Verification
* **Test 1 (Novel):** Run `/integrate novelty --workspace ./test_job` with a valid draft and answers transcript. Expected: `tests/candidate_outputs/final_novelty.md` created; file is structured according to the template; print instruction to run `/promote` — Candidate Artifact routing protocol triggered.
* **Test 2 (Deterministic):** Run with an empty answers transcript. Expected: aborts with non-zero exit and missing-answers error message.
* **Test 3 (Deterministic):** Verify that `compiled/final_novelty.md` does NOT exist after running `/integrate` (output is in `candidate_outputs/` only).
* **Test 4 (Deterministic):** Verify `state_graph.yml` module status is still `pending_integration` after `/integrate` completes (status does not advance until `/promote`).
