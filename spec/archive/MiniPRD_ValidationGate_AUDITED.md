# MiniPRD: Validation Gate

**Hypergraph Node ID:** `validation_gate`
**Parent Node:** `build_orchestrator`

## 1. The Confidence Mandate
- **Confidence Score:** 9/10. All checks fixed during Red Team resolution (#1, #6, #10, #12). No open questions.

## 2. Atomic User Stories
- **US-002:** As an author, the gate refuses to render an invalid document with a precise, first-failure message.
- **Reusability:** As the v0.0.2 loop, I import the gate as a function (not a CLI) to pre-validate without subprocessing.

## 3. Implementation Plan (Task List)
- [ ] Create `validate(data: dict) -> None` (raises a `ValidationError` with a precise message) — **importable**, not CLI-only.
- [ ] **Contract:** require `meta` with `doc_type, title, version, date, template, output_formats`; `title`/`version` non-empty strings; `meta.date` matches `^\d{4}\.\d{2}\.\d{2}$`; `meta.persona` **optional**; `evidence_bank` is an array. **Ignore unknown top-level keys** (forward-compat).
- [ ] **Evidence integrity:** every `content.sections[*].evidence` ID exists in `evidence_bank`; **reject duplicate** `evidence_bank` IDs; **warn** on orphan entries; **reject** a contentless doc (0 sections or 0 evidence refs).
- [ ] **Sentinel scan:** walk parsed string **values only**; fail if `[[DDO::REQUIRES_INPUT:` appears. Never scan raw bytes/keys/comments.
- [ ] Ensure each failure raises with a single, specific message naming the offending field/ID.
- [ ] Write `tests/unit/test_validation_gate.py` covering pass + every fail path.

## 4. The Negative Space (Constraints)
- **DO NOT** scan raw file bytes — parsed string values only.
- **DO NOT** require `meta.persona` (unused in v0.0.1).
- **DO NOT** reject unknown top-level keys (v0.0.2 mutation layer is additive).
- **DO NOT** let an empty/contentless document pass.
- **DO NOT** make orphan-evidence fatal (warn only).

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** complete valid `prd` doc → passes (no raise).
- **Test 2 (Deterministic):** empty `title` / `date: 2026-06-27` / missing `evidence_bank` / duplicate evidence ID / dangling evidence ref / contentless doc / residual `[[DDO::REQUIRES_INPUT:` → each raises a distinct precise message.
- **Test 3 (Deterministic):** value that legitimately quotes "REQUIRES USER INPUT" prose (without the namespaced token) → passes (no false-positive).
- **Test 4 (Deterministic):** doc with an extra unknown top-level key → passes (ignored).
