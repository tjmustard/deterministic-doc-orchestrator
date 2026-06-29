# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "typst==0.15.0",
#     "jinja2==3.1.6",
#     "pyyaml==6.0.3",
# ]
# ///
"""Hermetic PEP 723 orchestrator: render a validated DDO YAML to PDF/HTML/MD.

``build.py`` is the single deterministic entry point of the DDO rendering
backbone. It loads a ``document_data.yaml``, runs the importable validation gate
(:func:`ddo.validation.validate`), resolves a template strictly from the CLI
``--template``/``--format`` flags (never from ``meta``), and renders:

* ``pdf`` via the in-process ``typst`` package with bundled fonts (hermetic).
* ``html``/``md`` via Jinja2 (autoescape on only for HTML).

The render is bounded by a wall-clock timeout and an output-size cap. Output is
normalised to LF line endings with trailing whitespace stripped so fixtures are
not host-specific. ``build.py`` trusts the fully-resolved ``--output`` path and
performs no path derivation or containment (that is ``skill_render``'s job).

Run via ``uv run --locked ddo/build.py`` so the pinned lockfile is enforced.
"""

import argparse
import sys
import threading
from pathlib import Path

import yaml

# ``build.py`` runs two ways: (1) as a PEP 723 script via ``uv run`` where only
# the script's own dir (``ddo/``) is importable, and (2) under pytest where the
# repo root is on ``sys.path`` and ``ddo`` is a package. Support both.
try:
    from ddo.validation import ValidationError, validate
except ModuleNotFoundError:  # pragma: no cover - exercised only via ``uv run``.
    from validation import ValidationError, validate

# Resolve templates/fonts relative to this file, never the caller's CWD.
_BASE_DIR = Path(__file__).resolve().parent
_TEMPLATE_DIR = _BASE_DIR / "templates"
_FONT_DIR = _BASE_DIR / "fonts"

# Render-guard bounds (Red Team #3 / R6): a runaway template or huge YAML must
# not hang or OOM the orchestrator.
_DEFAULT_TIMEOUT_S = 30
_MAX_OUTPUT_BYTES = 64 * 1024 * 1024  # 64 MiB.

# ``--timestamp`` is UNIX seconds (SOURCE_DATE_EPOCH semantics). Bound it to a
# sane epoch range: [0, 9999-12-31T23:59:59Z].
_MAX_TIMESTAMP = 253402300799


def _fail(message: str) -> "None":
    """Print a single precise error to stderr and exit nonzero.

    Args:
        message: The precise, user-facing reason for the failure. No stack trace
            is emitted.

    Raises:
        SystemExit: Always, with exit code 1.
    """
    print(f"ddo-build: error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    """Parse the ``build.py`` command-line arguments.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        The parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="ddo-build",
        description="Render a validated DDO document_data.yaml to PDF, HTML, or Markdown.",
    )
    parser.add_argument("--data", required=True, help="Path to the document_data.yaml source.")
    parser.add_argument(
        "--template",
        required=True,
        choices=("prd", "scientific_report"),
        help="Template family (CLI-authoritative; meta is never consulted for routing).",
    )
    parser.add_argument(
        "--format",
        required=True,
        choices=("pdf", "html", "md"),
        help="Output format (CLI-authoritative).",
    )
    parser.add_argument("--output", required=True, help="Fully-resolved output file path.")
    parser.add_argument(
        "--timestamp",
        default=None,
        help="Pin the Typst PDF creation timestamp (UNIX seconds) for byte-identical PDFs.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=_DEFAULT_TIMEOUT_S,
        help=f"Render wall-clock cap in seconds (default {_DEFAULT_TIMEOUT_S}).",
    )
    return parser.parse_args(argv)


def _load_yaml(data_path: Path) -> dict:
    """Load and parse the document YAML, failing closed on any error.

    Args:
        data_path: Path to the ``document_data.yaml`` source.

    Returns:
        The parsed document dictionary.

    Raises:
        SystemExit: If the file is missing, unreadable, not valid YAML, or does
            not parse to a mapping. A single precise message is printed; no stack
            trace is shown.
    """
    try:
        raw = data_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        _fail(f"--data file not found: {data_path}")
    except OSError as exc:
        _fail(f"--data file could not be read: {data_path} ({exc.strerror})")

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        detail = str(exc).replace("\n", " ").strip()
        _fail(f"--data is not valid YAML: {detail}")

    if not isinstance(data, dict):
        _fail("--data did not parse to a YAML mapping (expected top-level meta/content keys).")
    return data


def _resolve_template(template: str, fmt: str) -> Path:
    """Resolve the template path strictly from CLI flags (never from ``meta``).

    Args:
        template: The ``--template`` value (``prd`` or ``scientific_report``).
        fmt: The ``--format`` value (``pdf``, ``html``, or ``md``).

    Returns:
        The absolute path to the resolved template file.

    Raises:
        SystemExit: If the resolved template file does not exist.
    """
    if fmt == "pdf":
        path = _TEMPLATE_DIR / "typst" / f"{template}.typst"
    else:
        path = _TEMPLATE_DIR / "jinja2" / f"{template}.{fmt}.jinja2"
    if not path.is_file():
        _fail(f"template not found for --template {template} --format {fmt}: {path}")
    return path


def _parse_timestamp(raw: "str | None") -> "int | None":
    """Validate and convert the ``--timestamp`` value to UNIX seconds.

    Args:
        raw: The raw ``--timestamp`` string, or ``None`` when omitted.

    Returns:
        The validated integer UNIX timestamp, or ``None`` if not supplied.

    Raises:
        SystemExit: If the value is non-integer or out of the supported range.
    """
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        _fail(f"--timestamp must be an integer of UNIX seconds, got {raw!r}.")
    if value < 0 or value > _MAX_TIMESTAMP:
        _fail(f"--timestamp out of range [0, {_MAX_TIMESTAMP}], got {value}.")
    return value


def _normalize_text(text: str) -> bytes:
    """Normalise rendered text to deterministic, host-agnostic UTF-8 bytes.

    Line endings are forced to LF and trailing whitespace is stripped per line so
    repeated renders are byte-identical regardless of platform.

    Args:
        text: The raw rendered template output.

    Returns:
        The normalised content encoded as UTF-8 (ending with a single LF when
        non-empty).
    """
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    if normalized:
        normalized += "\n"
    return normalized.encode("utf-8")


def _render_jinja(template_path: Path, fmt: str, data: dict) -> bytes:
    """Render an HTML or Markdown document with Jinja2.

    Autoescape is enabled only for HTML. The parsed data is passed positionally
    as top-level keys (``render(**data)``); a data string is never re-rendered,
    so there is no SSTI surface.

    Args:
        template_path: Absolute path to the ``.jinja2`` template.
        fmt: ``html`` or ``md`` (selects autoescape).
        data: The parsed, already-validated document dictionary.

    Returns:
        The normalised rendered output as UTF-8 bytes.
    """
    from jinja2 import Environment, FileSystemLoader

    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=(fmt == "html"),
        keep_trailing_newline=True,
    )
    template = env.get_template(template_path.name)
    rendered = template.render(**data)
    return _normalize_text(rendered)


def _render_typst(template_path: Path, data_path: Path, timestamp: "int | None") -> bytes:
    """Render a PDF in-process with the bundled ``typst`` package.

    The Typst template reads the YAML itself via ``sys.inputs.data_file``; the
    absolute data path is passed there and ``root='/'`` so the template's leading
    ``/`` virtual path resolves to the real file. System fonts are ignored and
    only the bundled ``ddo/fonts`` are used (hermeticity).

    Args:
        template_path: Absolute path to the ``.typst`` template.
        data_path: Absolute path to the ``--data`` YAML (passed as a Typst input).
        timestamp: Validated UNIX-seconds creation timestamp, or ``None`` to use
            the wall clock.

    Returns:
        The compiled PDF bytes.

    Raises:
        SystemExit: On a Typst compilation error (rendered as a single precise
            message, no stack trace).
    """
    import typst

    try:
        return typst.compile(
            str(template_path),
            root="/",
            sys_inputs={"data_file": str(data_path)},
            font_paths=[str(_FONT_DIR)],
            ignore_system_fonts=True,
            timestamp=timestamp,
        )
    except typst.TypstError as exc:
        detail = (getattr(exc, "message", None) or str(exc)).replace("\n", " ").strip()
        _fail(f"Typst render failed: {detail}")


def _run_with_guard(render_fn, timeout: float) -> bytes:
    """Run a render under a wall-clock timeout and an output-size cap.

    ``render_fn`` is executed in a daemon worker thread; the main thread joins
    with ``timeout``. If the worker is still alive after the deadline the process
    aborts (the daemon thread is reaped at interpreter exit). The produced output
    is rejected if it exceeds the size cap.

    Args:
        render_fn: Zero-argument callable returning the rendered ``bytes``.
        timeout: Wall-clock deadline in seconds.

    Returns:
        The rendered bytes.

    Raises:
        SystemExit: On timeout or when the output exceeds the size cap.
    """
    box: dict = {}

    def worker() -> "None":
        try:
            box["value"] = render_fn()
        except SystemExit as exc:  # _fail() inside the worker -> propagate cleanly.
            box["exit"] = exc
        except BaseException as exc:  # noqa: BLE001 - surfaced on the main thread.
            box["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        _fail(f"render exceeded the {timeout:g}s wall-clock timeout (use --timeout to raise it).")
    if "exit" in box:
        raise box["exit"]
    if "error" in box:
        _fail(f"render failed: {box['error']}")

    output = box["value"]
    if output is None:
        _fail("render produced no output.")
    if len(output) > _MAX_OUTPUT_BYTES:
        _fail(f"render output {len(output)} bytes exceeds the {_MAX_OUTPUT_BYTES}-byte size cap.")
    return output


def main(argv: "list[str] | None" = None) -> int:
    """Entry point: load, validate, render, and write the document.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        ``0`` on success. Failures exit nonzero via :func:`_fail` with a single
        precise message rather than returning.
    """
    args = _parse_args(argv)

    data_path = Path(args.data).resolve()
    output_path = Path(args.output)
    timestamp = _parse_timestamp(args.timestamp)

    data = _load_yaml(data_path)

    try:
        validate(data)
    except ValidationError as exc:
        _fail(f"validation failed: {exc}")

    template_path = _resolve_template(args.template, args.format)

    if args.format == "pdf":

        def render_fn() -> bytes:
            return _render_typst(template_path, data_path, timestamp)
    else:

        def render_fn() -> bytes:
            return _render_jinja(template_path, args.format, data)

    output_bytes = _run_with_guard(render_fn, args.timeout)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output_bytes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
