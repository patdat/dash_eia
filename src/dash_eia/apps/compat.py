"""Adapters for established modules during package migration.

The dashboard still lives at `src/index.py` in the workspace and loads its CSVs
relative to the process working directory, so it is reached through the
workspace rather than through the installed wheel.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def working_directory(path: Path) -> Iterator[None]:
    """Temporarily provide the checkout-relative contract the legacy app expects.

    The workspace root also joins `sys.path` for the duration, because `src.*`
    lives in the workspace and not in the installed wheel. Changing directory
    alone is not enough: `sys.path` is fixed at startup, so the installed
    command would raise ModuleNotFoundError for `src` while running from the
    right directory.
    """
    previous = Path.cwd()
    root = str(Path(path).resolve())
    added = root not in sys.path
    if added:
        sys.path.insert(0, root)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)
        if added and root in sys.path:
            sys.path.remove(root)
