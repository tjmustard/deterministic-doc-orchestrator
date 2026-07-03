"""Shared fixtures for the DDO render-determinism integration tests.

These tests drive the real ``build.py`` orchestrator end-to-end, invoking it
exactly as a user would -- ``uv run --locked ddo/build.py ...`` -- so the pinned
PEP 723 lockfile (``ddo/build.py.lock``) is enforced on every render. The
``render`` fixture is a thin subprocess wrapper; ``repo_root`` resolves inputs
relative to the repository, never the caller's working directory.
"""

import subprocess
from pathlib import Path

import pytest

# (template name, input-YAML basename under tests/data/) for each shipped example
# document. These are test INPUTS, not human-gated fixtures.
EXAMPLES = [
    ("prd", "prd_example.yaml"),
    ("scientific_report", "scientific_report_example.yaml"),
    ("blog_post", "blog_post_example.yaml"),
    ("meeting_notes", "meeting_notes_example.yaml"),
    ("meeting_agenda", "meeting_agenda_example.yaml"),
    ("project_report", "project_report_example.yaml"),
]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root (the parent of ``tests/``)."""
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def example_path(repo_root):
    """Return a resolver mapping an example basename to its absolute YAML path.

    Args:
        repo_root: The repository root fixture.

    Returns:
        A callable ``(basename) -> Path`` that returns the absolute, existing
        path under ``tests/data/``.
    """

    def _resolve(basename: str) -> Path:
        path = (repo_root / "tests" / "data" / basename).resolve()
        assert path.is_file(), f"missing example input: {path}"
        return path

    return _resolve


@pytest.fixture
def render(repo_root):
    """Return a callable that renders via ``uv run --locked ddo/build.py``.

    The callable signature is ``render(template, fmt, data_path, out_path,
    timestamp=None, timeout=None)`` and returns the completed process without
    asserting success, so a test can inspect the exit code and stderr directly.

    Args:
        repo_root: The repository root fixture (used as the subprocess CWD).

    Returns:
        The render callable described above.
    """

    def _render(template, fmt, data_path, out_path, *, timestamp=None, timeout=None):
        cmd = [
            "uv",
            "run",
            "--locked",
            "ddo/build.py",
            "--data",
            str(data_path),
            "--template",
            template,
            "--format",
            fmt,
            "--output",
            str(out_path),
        ]
        if timestamp is not None:
            cmd += ["--timestamp", str(timestamp)]
        if timeout is not None:
            cmd += ["--timeout", str(timeout)]
        return subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)

    return _render
