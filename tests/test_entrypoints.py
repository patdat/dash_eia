"""The root entrypoints must resolve their whole import graph.

`python run.py` is still an operator workflow, and it can reach modules the
wheel does not ship (top-level `src.*`, `scripts.*`). Those resolve only when the
repository root is on `sys.path`.

Each entrypoint is imported in a subprocess rather than in-process, because
pytest's `pythonpath` setting would put the root on `sys.path` for us and hide
exactly the breakage this guards against. The module is executed under a name
other than `__main__`, so the `if __name__ == "__main__"` guard keeps the
pipeline itself from running.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = ["run.py"]

_IMPORT_WITHOUT_RUNNING = """
import importlib.util
import sys

root, target = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
spec = importlib.util.spec_from_file_location("_entrypoint_under_test", target)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
"""


@pytest.mark.parametrize("name", ENTRYPOINTS)
def test_root_entrypoint_imports_without_running(name: str) -> None:
    target = ROOT / name
    assert target.is_file(), f"missing entrypoint: {name}"
    result = subprocess.run(
        [sys.executable, "-c", _IMPORT_WITHOUT_RUNNING, str(ROOT), str(target)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=300,
    )
    assert result.returncode == 0, f"`python {name}` failed to import:\n{result.stderr}"
