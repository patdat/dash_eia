"""The root entrypoints must resolve their whole import graph.

`python run.py` is still an operator workflow, and it can reach modules the
wheel does not ship (top-level `src.*`, `scripts.*`). Those resolve only when the
repository root is on `sys.path`.

Each entrypoint is imported in a subprocess rather than in-process, because
pytest's `pythonpath` setting would put the root on `sys.path` for us and hide
exactly the breakage this guards against. The module is executed under a name
other than `__main__`, so the `if __name__ == "__main__"` guard keeps the
pipeline itself from running.

**The conftest guard cannot reach inside this subprocess.** `block_network_and_aws`
is process-local: it patches `botocore` and `requests` in the pytest interpreter
only. A child process gets a fresh interpreter with unpatched libraries, and
until this file passed an explicit ``env=`` it also inherited the parent's real
environment -- so an import-time side effect that read `EIA_API_KEY` and called
out to api.eia.gov would have done so for real, with the developer's own key,
and this test would still have reported a green pass. No in-process fixture can
close that hole by construction. It is closed here instead, by controlling what
the child is given.

**Deliberately absent: the `boto3.DEFAULT_SESSION is None` assertion** that the
sibling repos carry beside this one. It is not an oversight and it should not be
added. This repo has no AWS surface at all: `boto3` is not a declared dependency,
is not in `uv.lock`, is not installed in the venv, and the string does not appear
in `src/`, `eia_downloads/`, `pages/` or `run.py`. The probe would die on
`import boto3` before reaching its assertion, so the only way to make it green
would be an `importorskip` -- a test that always skips, or worse, passes because
its subject failed to load. That is the exact failure mode this project exists to
remove. If AWS is ever introduced here, add the assertion then; the scrubbed
environment below is already in place for it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = ["run.py"]

# Prefixes that carry real credentials. `EIA_API_KEY` is the only secret this
# repo reads (`.env.example` declares it and nothing else).
_SECRET_PREFIXES = ("EIA_",)


def _scrubbed_env() -> dict[str, str]:
    """The parent environment with every credential-bearing variable removed.

    This is a **deny-list**: start from the whole environment and drop what is
    sensitive. It must not become an allow-list that rebuilds the environment
    from a handful of known-good names. An allow-list is wrong twice over --
    it drops OS-essential variables (on Windows, losing ``SYSTEMROOT`` stops the
    interpreter from starting at all) and it silently *keeps* any credential
    variable whose name does not match a known prefix.
    ``test_scrub_is_a_deny_list`` pins this.
    """
    return {k: v for k, v in os.environ.items() if not k.startswith(_SECRET_PREFIXES)}


SCRUBBED = _scrubbed_env()

_IMPORT_WITHOUT_RUNNING = """
import importlib.util
import sys

root, target = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
spec = importlib.util.spec_from_file_location("_entrypoint_under_test", target)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
"""


def test_scrubbed_env_carries_no_real_credentials() -> None:
    """The scrubber must be why the child is safe, not luck.

    If this fails, the subprocess test below is running against a real API key
    and is proving less than it claims.
    """
    leaked = sorted(k for k in SCRUBBED if k.startswith(_SECRET_PREFIXES))
    assert not leaked, f"credential-bearing variables survived the scrub: {leaked}"


def test_scrub_is_a_deny_list() -> None:
    """Everything not credential-bearing must survive into the child.

    Guards against the scrubber being rewritten as an allow-list (keep PATH plus
    a few names, drop the rest). That breaks the interpreter on Windows, where
    dropping SYSTEMROOT prevents startup outright.

    Asserting the general property rather than a hardcoded list of names means
    this fails on Linux and macOS too, instead of only on Windows.
    """
    # Call the scrubber fresh rather than inspecting the module-level SCRUBBED.
    # The property under test belongs to the function, and os.environ legitimately
    # changes between import and now -- pytest injects PYTEST_CURRENT_TEST once a
    # test starts, which a snapshot comparison would report as a dropped variable.
    fresh = _scrubbed_env()

    should_survive = {k for k in os.environ if not k.startswith(_SECRET_PREFIXES)}
    dropped = sorted(should_survive - set(fresh))
    assert not dropped, f"scrub dropped non-sensitive variables: {dropped}"

    # Named spot-check for the ones whose loss is catastrophic rather than merely
    # confusing. Only assert on those the current platform actually defines.
    for essential in ("PATH", "SYSTEMROOT", "COMSPEC", "TEMP", "TMP", "LANG", "HOME"):
        if essential in os.environ:
            assert fresh.get(essential) == os.environ[essential], (
                f"{essential} must reach the child unchanged"
            )


@pytest.mark.parametrize("name", ENTRYPOINTS)
def test_root_entrypoint_imports_without_running(name: str) -> None:
    target = ROOT / name
    assert target.is_file(), f"missing entrypoint: {name}"
    result = subprocess.run(
        [sys.executable, "-c", _IMPORT_WITHOUT_RUNNING, str(ROOT), str(target)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=SCRUBBED,
        timeout=300,
    )
    assert result.returncode == 0, f"`python {name}` failed to import:\n{result.stderr}"
