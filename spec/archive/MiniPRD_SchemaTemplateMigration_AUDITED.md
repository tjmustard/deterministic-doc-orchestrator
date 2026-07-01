# MiniPRD: Schema + Template Migration

**Hypergraph Node ID:** `schemas`, `templates`
**Parent Node:** `ddo_pipeline`

## 1. The Confidence Mandate
- **Confidence Score:** 8/10.
- **Clarifying Question:** Do the six template stubs render against the canonical schemas without field-name edits? Verified on migration (US-006 of this module).

## 2. Atomic User Stories
- **Migration:** As a maintainer, I move + rename the two schemas and six template stubs into `ddo/` with short doc-type names.
- **Parity:** As a maintainer, each template renders against its schema with a complete example before wiring.
- **Hermeticity:** As a maintainer, I bundle pinned fonts into `ddo/fonts/` so Typst never falls back to system fonts.

## 3. Implementation Plan (Task List)
- [ ] Move/rename `PRDs/*schema*.yaml` → `ddo/schemas/{prd,scientific_report}.yaml`.
- [ ] Move/rename Typst stubs → `ddo/templates/typst/{prd,scientific_report}.typst`.
- [ ] Move/rename Jinja2 stubs → `ddo/templates/jinja2/{prd,scientific_report}.{html,md}.jinja2`.
- [ ] Audit each template's referenced keys against its schema; fix mismatches (record any field renames).
- [ ] Add `|dictsort` to any dict iteration; remove any clock/host/PRNG usage (determinism, RT #7).
- [ ] Confirm autoescape-on works for the `.html` template with `<`, `&`, `>` in values.
- [ ] Add `ddo/fonts/` with pinned font files; document the licenses.
- [ ] Move `product_critic`, `scientific_reviewer` → `ddo/personas/` (forward-compat, unused).

## 4. The Negative Space (Constraints)
- **DO NOT** introduce non-deterministic template constructs (clock, host, PRNG, unordered dict).
- **DO NOT** wire a template before it renders cleanly against its schema.
- **DO NOT** exercise the personas in any v0.0.1 code path (smoke test only — see Test Suite MiniPRD).
- **DO NOT** rely on system fonts — only `ddo/fonts/`.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** each `(template, format)` pair renders a complete example to a non-empty artifact, exit 0.
- **Test 2 (Deterministic):** HTML render of a value containing `<script>` is escaped (no raw HTML injection).
- **Test 3 (Deterministic):** each migrated persona file parses / is well-formed (`test_personas_well_formed`).
