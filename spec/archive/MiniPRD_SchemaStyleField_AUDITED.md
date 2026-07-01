# MiniPRD: SchemaStyleField — add `meta.style_profile` + live defaults

**Hypergraph Node ID:** ddo_schemas  *(EXISTS — mark needs_review, modify; do NOT add)*
**Parent Node:** ddo_system
**DAG:** **ATOMIC with MP-1 (Styles)** — must land in the same change (RT-6). Blocked-by MP-1.

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Additive optional field; `validation.py` ignores unknown
  top-level keys (verified `validation.py:155`), so no validation change is needed or allowed.
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-007:** As a document author, I want per-doc-type defaults so new docs are styled out of the box.

## 3. Implementation Plan (Task List)
- [ ] In `ddo/schemas/prd.yaml`, add optional `style_profile: "formal_professional"` to `meta`,
      placed **immediately after `persona`**.
- [ ] In `ddo/schemas/scientific_report.yaml`, add optional
      `style_profile: "technical_precise"` to `meta`, immediately after `persona`.
- [ ] Confirm both referenced profiles (`formal_professional.md`, `technical_precise.md`)
      exist in `ddo/styles/` **in this same change** — a default MUST NOT reference an absent
      profile (RT-6 atomic-landing rule).
- [ ] Add a brief schema comment noting: absent ⇒ no-op; present-but-invalid ⇒ hard-fail (RT-8);
      resolves to `ddo/styles/<stem>.md`; stem must match `^[a-z][a-z0-9_]*$`.

## 4. The Negative Space (Constraints)
- **DO NOT** land this MiniPRD without MP-1 (Styles) in the same change — the live default would
  hard-fail every new ingest (RT-6).
- **DO NOT** modify `validation.py`, `build.py`, or any Python module — `style_profile` is
  render-invisible and passes validation as an ignored unknown key.
- **DO NOT** make the field required — it is optional; absent ⇒ clean no-op (US-003).
- **DO NOT** add a machine-parsed style schema or enumerate profiles in the schema (D4).

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** A `document_data.yaml` using `prd.yaml`'s default validates and
  renders byte-identically to v0.0.4 (the field is render-invisible; golden baselines unchanged).
- **Test 2 (Deterministic):** Both shipped defaults resolve to an existing
  `ddo/styles/<stem>.md` — a script/agent check confirms no dangling default reference (RT-6).
