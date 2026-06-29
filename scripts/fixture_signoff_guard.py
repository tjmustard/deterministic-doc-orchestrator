"""Human sign-off guard for ``tests/fixtures/`` (SuperPRD RT#13 / R1).

``tests/fixtures/`` holds the human-verified golden regression baselines that the
determinism suite compares against. Per the DDO negative constraints an agent
must never write or promote a fixture: promotion is a deliberate human act. This
guard makes that rule mechanical rather than prose -- it rejects any staged diff
that touches ``tests/fixtures/`` unless an explicit human sign-off token is set.

The sign-off mechanism is the environment variable ``DDO_FIXTURE_SIGNOFF``: set
it to a truthy value (``1``/``true``/``yes``/``on``, case-insensitive) only for
the single commit that promotes a fixture. Without it, a staged change under
``tests/fixtures/`` aborts the commit.

Wire it as a pre-commit hook or CI step by running ``python
scripts/fixture_signoff_guard.py``: it reads the staged file list from ``git
diff --cached --name-only`` and exits nonzero with a precise message when
fixtures changed without sign-off. The pure functions :func:`fixtures_touched`
and :func:`assert_fixture_signoff` take their inputs as plain arguments so they
can be unit-tested without git.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterable, Mapping

# Every fixture path lives under this prefix (POSIX separators, as git reports).
FIXTURE_PREFIX = "tests/fixtures/"

# The structural placeholder that keeps the empty dir in git is not a fixture
# payload; changing it never requires sign-off.
_GITKEEP_SUFFIX = "/.gitkeep"

# Environment variable carrying the human sign-off for a fixture-promoting commit.
SIGNOFF_ENV_VAR = "DDO_FIXTURE_SIGNOFF"
_TRUTHY = {"1", "true", "yes", "on"}


class FixtureSignoffError(Exception):
    """Raised when ``tests/fixtures/`` is modified without a human sign-off."""


def fixtures_touched(staged_paths: Iterable[str]) -> list[str]:
    """Return staged paths that modify fixture payloads under ``tests/fixtures/``.

    Args:
        staged_paths: Iterable of repo-relative, POSIX-separated paths (as
            emitted by ``git diff --cached --name-only``).

    Returns:
        Sorted list of the touched paths under ``tests/fixtures/`` excluding the
        structural ``.gitkeep`` placeholder. Empty if no fixture payload changed.
    """
    touched = [
        path
        for path in staged_paths
        if path.startswith(FIXTURE_PREFIX) and not path.endswith(_GITKEEP_SUFFIX)
    ]
    return sorted(touched)


def is_signed_off(environ: Mapping[str, str] | None = None) -> bool:
    """Return whether the human fixture sign-off token is present and truthy.

    Args:
        environ: Optional environment mapping to read from (defaults to
            :data:`os.environ`).

    Returns:
        ``True`` if ``DDO_FIXTURE_SIGNOFF`` holds a truthy value, else ``False``.
    """
    env = os.environ if environ is None else environ
    return str(env.get(SIGNOFF_ENV_VAR, "")).strip().lower() in _TRUTHY


def assert_fixture_signoff(staged_paths: Iterable[str], *, signed_off: bool) -> None:
    """Reject staged fixture changes that lack a human sign-off.

    Args:
        staged_paths: Iterable of staged repo-relative paths.
        signed_off: Whether the human sign-off token is present (see
            :func:`is_signed_off`).

    Raises:
        FixtureSignoffError: If one or more fixture payloads are staged while
            ``signed_off`` is ``False``. The message lists the offending paths
            and names the sign-off mechanism.
    """
    touched = fixtures_touched(staged_paths)
    if touched and not signed_off:
        joined = ", ".join(touched)
        raise FixtureSignoffError(
            f"refusing staged change to human-gated fixtures ({joined}) without sign-off; "
            f"set {SIGNOFF_ENV_VAR}=1 only when a human is deliberately promoting a fixture"
        )


def _staged_paths() -> list[str]:
    """Return staged paths from ``git diff --cached --name-only -z``.

    Returns:
        List of repo-relative, POSIX-separated staged paths (possibly empty).
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [path for path in result.stdout.split("\0") if path]


def main(argv: list[str] | None = None) -> int:
    """Pre-commit/CI entry point: enforce fixture sign-off on the staged diff.

    Args:
        argv: Unused; present for a conventional CLI signature.

    Returns:
        ``0`` if the staged diff is allowed. On a violation a precise message is
        printed to stderr and ``1`` is returned.
    """
    try:
        assert_fixture_signoff(_staged_paths(), signed_off=is_signed_off())
    except FixtureSignoffError as exc:
        print(f"fixture-signoff-guard: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
