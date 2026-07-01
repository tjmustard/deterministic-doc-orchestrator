# MiniPRD: ddo-ingest Skill

**Hypergraph Node ID:** `skill_ingest`
**Parent Node:** `skills`

> **Candidate Artifact:** `ddo-ingest` is the **sole non-deterministic output** in v0.0.1. Its output is tested for **contract-validity + render-ability only** (never content equality), is **human-verified** at the HITL gate, and is promoted to `tests/fixtures/` **only after one-time human sign-off**.

## 1. The Confidence Mandate
- **Confidence Score:** 8/10. Zero-hallucination + write-safety fixed during resolution (#5, #11). Extraction fidelity is **human-gated, not machine-verified** (stated limitation, claim (B)).

## 2. Atomic User Stories
- **US-004:** As an author, I ingest raw local sources into a schema-shaped `document_data.yaml` with gaps flagged and nothing invented.

## 3. Implementation Plan (Task List)
- [ ] Read local source files (no network); map content to the chosen schema's fields.
- [ ] For any field not verifiably fillable, write `[[DDO::REQUIRES_INPUT: <reason>]]` — invent nothing.
- [ ] Compute the document folder via the shared `path_deriver` (sanitized slug + containment).
- [ ] **Overwrite guard (in code):** if `document_data.yaml` exists, abort with a precise message unless `--force`; non-interactive default = **abort**.
- [ ] **Atomic write:** write to a temp file in the target dir → `fsync` → `os.replace`.
- [ ] **Fabrication tripwire (advisory):** collect emitted date/number/proper-noun-looking tokens; flag any not found verbatim in a source file; surface as "verify these" (non-blocking).
- [ ] End at `[WAITING FOR USER REVIEW]` with the tripwire summary.

## 4. The Negative Space (Constraints)
- **DO NOT** invent dates, metrics, citations, or specifics — gap-flag instead.
- **DO NOT** overwrite an existing YAML without `--force` (enforced in code, not just instruction).
- **DO NOT** leave a half-written source-of-truth — writes must be atomic.
- **DO NOT** access the network (local sources only).
- **DO NOT** auto-advance — always halt at `[WAITING FOR USER REVIEW]`.
- **DO NOT** treat the tripwire as a guarantee — it is best-effort advisory.

## 5. Integration Tests & Verification
- **Test 1 (Novel → Candidate Artifact):** fixed fixture source → produced YAML **passes the validation gate** and **renders to all three formats**; **no content-equality assertion** (`test_ingest_contract_and_renderability`). Routing: output is a Candidate Artifact → human-verified before fixture promotion.
- **Test 2 (Deterministic):** existing `document_data.yaml` + no `--force` (non-interactive) → abort with a precise message; file unchanged.
- **Test 3 (Deterministic):** a date/number present in the YAML but absent from every source → appears in the tripwire "verify these" list.
