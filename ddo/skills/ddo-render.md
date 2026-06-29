# **Skill: ddo-render**

## **Description**

Renders a validated `document_data.yaml` into its target formats (PDF, HTML, Markdown) by deriving the canonical output path from `meta` and invoking the hermetic `build.py` orchestrator. This skill is a **thin wrapper**: it computes paths and routes flags, but it never writes a file itself and never re-validates the document (`build.py` is the single deterministic gate).

This is the **Render** phase of the DDO pipeline. It is deterministic by construction — given the same YAML and templates, it produces the same artifacts — and it ends at a mandatory human-in-the-loop gate.

## **Inputs**

1. `data_file`: Path to a `document_data.yaml` (the version-controlled source of truth).

Everything else — the template, the formats, the output paths — is **derived from `meta`**. The caller never supplies CLI flags by hand.

## **Invariants (read before acting)**

- **YAML is the source of truth.** Never hand-edit a rendered artifact. If a render is wrong, fix `document_data.yaml` and re-render.
- **Containment is mandatory.** Every derived path must be asserted inside `Documents/` *before* any build runs. A path that escapes is a hard stop, not a warning.
- **CLI flags are computed from `meta`, never the reverse.** `build.py` routes only off `--template`/`--format`; `meta.template`/`meta.output_formats` are descriptive and must be *translated into* flags here. The two cannot disagree because this skill is the only translator.
- **Single gate.** Do not re-implement validation. If `build.py` rejects the document, surface its message verbatim.

## **Execution Logic**

1. **Read the source.** Read `data_file` and extract the `meta` block: `meta.date`, `meta.doc_type`, `meta.title`, `meta.template`, and `meta.output_formats`. If any of these are missing, stop and report which field is absent (do not invent a value).

2. **Derive and contain the paths.** Use the shared `ddo.paths` atomic — do not re-implement slug or path logic:

   ```python
   from ddo.paths import output_path, assert_within_documents

   for fmt in meta["output_formats"]:                 # e.g. ["pdf", "html", "md"]
       out = output_path(meta, fmt)                   # Documents/<date>_<doc_type>_<slug>/output/<slug>.<fmt>
       safe_out = assert_within_documents(out)        # realpath containment; raises PathContainmentError on escape
   ```

   `sanitize_slug` (used internally by `output_path`) lowercases the title, collapses everything outside `[a-z0-9]` to single hyphens, forbids `..`, and caps length at 80; an empty/degenerate title falls back to `untitled`. **If `assert_within_documents` raises, abort the entire render** and report the breach — do not attempt any build for any format.

3. **Translate `meta` into CLI flags.** The `--template` flag is `meta.template`; one `--format` flag per entry in `meta.output_formats`. These are computed *from* `meta` — they are never read back from the CLI into `meta`.

4. **Invoke `build.py` once per format** with the fully-resolved, contained `--output`:

   ```bash
   uv run --locked ddo/build.py \
     --data     <abs path to data_file> \
     --template <meta.template> \
     --format   <pdf|html|md> \
     --output   <safe_out from step 2>
   ```

   Run this once for each format in `meta.output_formats`. `build.py` `mkdir -p`s the `--output` parent, so a missing `output/` directory is not an error. Capture each invocation's exit code and stderr.

5. **Report per format.** For each format, report success with the resolved output path, or failure with `build.py`'s precise single-line `ddo-build: error: <msg>` surfaced verbatim. A failure in one format does not retroactively undo artifacts already written for other formats — report the mixed result honestly.

## **Negative Constraints**

- **DO NOT** write, move, or hand-edit any file from this skill. Only `build.py` writes artifacts.
- **DO NOT** duplicate the validation gate's checks — `build.py` is the single gate.
- **DO NOT** let any derived path escape `Documents/`; the containment assertion is mandatory and must run before any build.
- **DO NOT** pass `meta` to `build.py` for routing. Pass the resolved `--template`/`--format` flags computed from `meta`.
- **DO NOT** invent a missing `meta` field; report the gap and stop.

## **Post-Condition**

Output, per requested format, either the resolved path to the newly rendered document or `build.py`'s exact error message.

```
[WAITING FOR USER REVIEW]
```

Prompt the user to review the rendered document(s). Ask whether they are ready to proceed to the next pipeline phase (`ddo-red-team`, when available) or need to adjust `document_data.yaml` and re-render. Do not auto-advance past this gate.
