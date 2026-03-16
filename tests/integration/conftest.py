"""Pytest configuration for integration tests."""

import sys
from pathlib import Path

# Make the repo root importable so tests can do `from init_workspace import ...`
sys.path.insert(0, str(Path(__file__).parents[2]))
