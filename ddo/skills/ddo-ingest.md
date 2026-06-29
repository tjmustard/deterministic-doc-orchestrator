# **Skill: ddo-ingest**

## **Description**

Extracts and structures raw information from **local** source materials into a
schema-shaped `document_data.yaml`, under a strict **zero-hallucination**
constraint. This is the **Ingest** phase of the DDO pipeline and the *only*
non-deterministic step in v0.0.1: you (the agent) perform the cognitive
source -> YAML mapping, while the deterministic safety mechanics — the overwrite
guard, the atomic write, and the fabrication tripwire — live in code
(`ddo.ingest`) and `ddo.paths` and must be used, not re-implemented.

The output is a **Candidate Artifact**: it is human-verified at the review gate
before it is ever trusted. Your job is to map faithfully and to **flag every
gap** rather than fill it from imagination.

## **Inputs**

1. `source_paths`: One or more paths to **local** raw documents or notes. No
   URLs, no network fetches.
2. `doc_type`: The target schema, one of `prd` or `scientific_report`. Its field
   shape is defined in `ddo/schemas/<doc_type>.yaml`.
3. `force` (optional): Allow overwriting an existing `document_data.yaml`.
   Default is **abort** if one already exists.

## **Invariants (read before acting)**

- **YAML is the source of truth.** You are writing the one mutable artifact in
  the system. Treat the write as sacred: atomic, guarded, never partial.
- **Invent nothing.** Every date, metric, citation, name, or technical specific
  must come from a source. If it is not in a source, it is a gap — flag it.
- **Local only.** Read the provided `source_paths` and nothing else. Do not
  access the network.
- **Fail closed on paths.** Every derived path must be asserted inside
  `Documents/` before any write. A path that escapes is a hard stop.
- **Halt at the gate.** End at `[WAITING FOR USER REVIEW]`. Never auto-advance to
  render or any later phase.

## **Execution Logic**

1. **Read the sources (local only).** Read each path in `source_paths`. Keep the
   raw text of every source — you will need it for the fabrication tripwire in
   step 5. Do not fetch anything over the network.

2. **Map to the schema.** Load the field shape from `ddo/schemas/<doc_type>.yaml`
   and map facts from the sources onto the corresponding YAML nodes (`meta`,
   `content.sections[*]`, and `evidence_bank`). For every claim you place in a
   section, add a matching entry to `evidence_bank` and reference its `id` from
   that section's `evidence` list.

3. **Flag every gap (zero hallucination).** For **any** field you cannot fill
   verifiably from the sources, write the literal namespaced token:

   ```
   [[DDO::REQUIRES_INPUT: <short reason>]]
   ```

   Never substitute an invented date, metric, citation, or specific. When in
   doubt, flag it. (The validation gate in `build.py` will refuse to render
   while any such token remains, so nothing half-filled can ship by accident.)

4. **Derive and contain the output path.** Use the shared atomics — do not
   re-implement slug or containment logic:

   ```python
   from ddo.ingest import document_data_path  # composes + asserts containment

   target = document_data_path(meta)  # Documents/<date>_<doc_type>_<slug>/document_data.yaml
   ```

   `document_data_path` derives the folder via `ddo.paths` (sanitized slug,
   whitelist `[a-z0-9-]`, `..` forbidden, length-capped) and runs the result
   through `assert_within_documents`. **If it raises `PathContainmentError`,
   abort** and report the breach — write nothing.

5. **Write atomically, honoring the overwrite guard.** Serialize the mapped
   structure to YAML text and write it with the code-enforced guard:

   ```python
   from ddo.ingest import atomic_write, OverwriteError

   try:
       atomic_write(target, yaml_text, force=force)  # temp -> fsync -> os.replace
   except OverwriteError as exc:
       # default abort: surface the precise message, write nothing
       ...
   ```

   With `force` unset, an existing `document_data.yaml` is **never** overwritten;
   surface `OverwriteError`'s precise message and stop. With `force=True`,
   proceed. The write is atomic — there is no half-written outcome.

6. **Run the fabrication tripwire (advisory).** Scan the produced YAML against
   the raw source texts and surface the "verify these" list:

   ```python
   from ddo.ingest import fabrication_tripwire

   to_verify = fabrication_tripwire(yaml_text, source_texts)  # list[str], never raises
   ```

   This is a **best-effort, non-blocking** advisory: it lists date/number/
   proper-noun tokens not found verbatim in any source. It is **not** a
   guarantee and must never block the write or be treated as validation. The
   `[[DDO::REQUIRES_INPUT: ...]]` markers are intentionally excluded from it.

## **Negative Constraints**

- **DO NOT** invent dates, metrics, citations, or specifics — gap-flag with
  `[[DDO::REQUIRES_INPUT: <reason>]]` instead.
- **DO NOT** overwrite an existing `document_data.yaml` without `--force`; the
  guard is enforced in `atomic_write`, and the default is abort.
- **DO NOT** leave a half-written source of truth — always go through
  `atomic_write` (temp -> fsync -> `os.replace`); never write the target directly.
- **DO NOT** access the network — local sources only.
- **DO NOT** let any derived path escape `Documents/`; the containment assertion
  is mandatory before any write.
- **DO NOT** treat the fabrication tripwire as a guarantee — it is advisory and
  never blocks.
- **DO NOT** auto-advance past this gate.

## **Post-Condition**

Report the resolved `document_data.yaml` path, a summary of fields populated vs.
`[[DDO::REQUIRES_INPUT: ...]]` gaps remaining, and the tripwire's "verify these"
list (advisory).

```
[WAITING FOR USER REVIEW]
```

Prompt the user to manually fill the flagged gaps in the YAML, verify the
extraction against their sources (aided by the tripwire list), and give explicit
approval before proceeding to `ddo-render`. Do not auto-advance past this gate.
