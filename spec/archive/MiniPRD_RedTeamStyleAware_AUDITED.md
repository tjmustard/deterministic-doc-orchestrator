# MiniPRD: RedTeamStyleAware — register-aware critique + persona stem gate

**Hypergraph Node ID:** skill_red_team  *(EXISTS — mark needs_review, modify)*
**Parent Node:** ddo_skills
**DAG:** independent of MP-1..MP-3; feeds MP-7. Carries RT-3 + RT-10.

## 1. The Confidence Mandate
- **Confidence Score:** 10/10. Two additive, cognitive-only edits to one skill file. RT-10 reuses
  the exact `^[a-z][a-z0-9_]*$` gate already specified for style (verified-real gap in
  `ddo-red-team.md` §3 — persona Read has no stem validation today).
- **Clarifying Questions:** None.

## 2. Atomic User Stories
- **US-008:** As a loop operator, I want the adversarial critique to be register-aware and the
  persona sink hardened, so the loop does not oscillate and both file-resolution sinks are safe.

## 3. Implementation Plan (Task List)
- [ ] **RT-3 — surface style in the report header:** add the active `meta.style_profile` to the
      Red Team report header, mirroring the existing persona AV table (e.g. a `| Style | <stem> |`
      row alongside `| Persona | <stem> |`), so the critique is **aware** of the intended register
      even though the render hides it. If `style_profile` is absent, render `(none)`.
- [ ] **RT-3 — document recommended pairings:** add a short note recommending aligned pairings
      (e.g. `formal_professional` + `product_critic`, `technical_precise` + `scientific_reviewer`)
      and warning that a mismatched pair can oscillate the loop.
- [ ] **RT-10 — close the persona traversal gap:** before Reading `ddo/personas/<stem>.md`,
      validate the `persona` stem against `^[a-z][a-z0-9_]*$` (reject `.`/`/`/`..`), and hard-fail
      (name the file, list available `ddo/personas/*.md`) on a referenced-but-missing persona —
      the **identical** gate + hard-fail used for `style_profile`. Treat a stored value as untrusted.
- [ ] Add a one-line note that A6's deferral of this gap is **superseded** by v0.0.5 (RT-10), so
      both sinks are now hardened identically — no divergent doors.

## 4. The Negative Space (Constraints)
- **DO NOT** couple persona↔style in schema/validation — the header surfacing + pairing note are
  documentary/cognitive only (RT-3 rejected schema coupling).
- **DO NOT** machine-parse the style profile in the Red Team skill — the header shows the *stem*,
  not parsed style rules (Red Team still reads the style-invisible render).
- **DO NOT** Read a `persona` (or `style_profile`) path before validating its stem (RT-10).
- **DO NOT** modify any Python module — cognitive-only skill edit.

## 5. Integration Tests & Verification
- **Test 1 (Deterministic):** a `persona` value containing `.`/`/`/`..` is rejected before any
  Read; a referenced-but-missing persona hard-fails naming the file + listing available personas.
- **Test 2 (HITL):** the Red Team report header shows the active `style_profile` (or `(none)`),
  and the critique does not file findings that contradict the intended register.
