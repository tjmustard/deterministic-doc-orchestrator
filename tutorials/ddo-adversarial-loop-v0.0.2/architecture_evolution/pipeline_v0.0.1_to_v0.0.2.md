# Pipeline Evolution: v0.0.1 → v0.0.2

How the DDO state model grows when the adversarial loop lands. v0.0.1 is a
one-way street (YAML → document). v0.0.2 closes the street into a loop without
changing a single v0.0.1 guarantee — the new code *reuses* the v0.0.1 primitives
(`ingest.atomic_write`, `paths.assert_within_documents`, `validation.validate`)
rather than re-implementing them.

## Before — v0.0.1 (deterministic backbone)

```
            ddo-ingest                         ddo-render
 source ──▶ (ddo.ingest) ──▶ document_data.yaml ──▶ (build.py) ──▶ output/*.{pdf,html,md}
 material      │                  ▲  (source of truth)    │
              fills sentinels     │                       validate() gate
              [[DDO::REQUIRES_     │                       (minimal contract)
                INPUT: ...]]       └───────── HITL [WAITING FOR USER REVIEW] gates
```

- **One direction.** Material flows in; a document flows out. Nothing flows back.
- **A faithful render of a flawed document is still flawed** — there is no
  mechanism to make the document *better*.

## After — v0.0.2 (adversarial loop layered on top)

```
                          ┌──────────────────── loop until finalized ───────────────────┐
                          │                                                              │
 document_data.yaml ─render─▶ output/*.md ──▶ ddo-red-team ──▶ red_team_report_vN.yaml   │
   (source of truth)         (MD/HTML only,      (FRESH ctx)     + red_team_view_vN.md    │
        ▲                     never the PDF)         │                                    │
        │                                            ▼                                    │
        │                                      ddo-interview ──▶ interview_log_vN.yaml    │
        │                                      (batched Q&A)      (decision_recorded)     │
        │                                            │                                    │
        │   snapshot  ┌── document_data_pre_vN.yaml  ▼                                    │
        └─ ddo-refine ◀──────────────────────── apply_patches ──▶ validate() + structural │
            (commit)   constrained set / append_*   (pure)        check  ──▶ re-render ───┘
                          │
                          └──▶ history.yaml (+ history.md), findings marked applied:true
```

### What's new

| Concern | v0.0.1 | v0.0.2 |
|---------|--------|--------|
| Direction | One-way (ingest → render) | Closed loop (critique → resolve → refine → re-render) |
| Writers of `document_data.yaml` | `ddo-ingest` (create) | + `ddo.refine` (the *only* refine-time writer) |
| New code modules | `ddo.ingest`, `ddo.paths`, `ddo.validation`, `build.py` | + `ddo.review`, `ddo.refine` |
| New skills | `ddo-ingest`, `ddo-render` | + `ddo-red-team`, `ddo-interview`, `ddo-refine` |
| Personas | Shipped, "smoke-tested only" | **Actively exercised** as critique lenses |
| Reversibility of a bad edit | n/a (no edits) | `document_data_pre_vN.yaml` byte-for-byte snapshot |
| Audit trail | rendered output | versioned `review_history/` + `history.yaml`/`.md` |

### Invariants carried forward unchanged

- **YAML is the source of truth.** Never patch a rendered artifact; patch the
  parsed dict via structured patches, then re-render.
- **Zero hallucination.** Findings must be grounded in the rendered text; the
  `[[DDO::REQUIRES_INPUT: ...]]` sentinel still blocks the validation gate.
- **HITL gates are mandatory.** Every phase still ends at
  `[WAITING FOR USER REVIEW]` / `[WAITING FOR USER RESPONSE]`.
- **Reuse, not modify.** `validation_gate`, `ingest_helpers`, and `path_deriver`
  gain new inbound edges only — their blast radius is unchanged (SuperPRD D5).

### The one new firewall

A **fresh conversation context is mandated only at the `ddo-red-team` boundary**.
The critique's value depends on not inheriting the authoring/ingest rationale;
the `red_team_report_vN.yaml` artifact is the clean hand-off. `ddo-interview` and
`ddo-refine` are collaborative and may share one context.
