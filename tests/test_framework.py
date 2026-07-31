import ast
import importlib
import re
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from dash_eia.apps import launchers, runner
from dash_eia.apps.compat import working_directory
from dash_eia.cli import main
from dash_eia.config.paths import WORKSPACE_ENV_VAR, WorkspacePaths


def _workspace(path: Path) -> Path:
    (path / "pyproject.toml").write_text(
        '[project]\nname = "dash-eia"\nversion = "0.0.0"\n',
        encoding="utf-8",
    )
    return path


def test_workspace_discovery(tmp_path):
    root = _workspace(tmp_path)
    child = root / "child"
    child.mkdir()
    assert WorkspacePaths.discover(cwd=child).root == root


def test_workspace_discovery_tolerates_a_utf8_bom(tmp_path):
    """PowerShell and Windows editors write pyproject.toml with a BOM."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "dash-eia"\nversion = "0.0.0"\n',
        encoding="utf-8-sig",
    )
    assert WorkspacePaths.discover(cwd=tmp_path).root == tmp_path


def test_bootstrap_creates_canonical_layout(tmp_path):
    root = _workspace(tmp_path)
    assert main(["--workspace", str(root), "bootstrap"]) == 0
    assert (root / "data" / "reference").is_dir()
    assert (root / "data" / "raw").is_dir()
    assert (root / "data" / "processed").is_dir()


def test_help_is_credential_free(capsys):
    assert main([]) == 0
    assert "eia-dashboard" not in capsys.readouterr().out


def test_app_registry_has_stable_name_and_port():
    from dash_eia.apps.runner import APP_SPECS

    assert APP_SPECS["eia-dashboard"].default_port == 8052


# ---------------------------------------------------------------------------
# `eia-dashboard` argument routing.
#
# The console script wraps `dash-eia app eia-dashboard`, appending the caller's
# arguments *after* the subcommand. `--workspace` is registered on the
# top-level parser, so argparse rejected the documented invocation outright:
#
#     $ eia-dashboard --workspace /checkout
#     dash-eia: error: unrecognized arguments: --workspace /checkout
#
# That left `DASH_EIA_WORKSPACE` and CWD discovery as the only ways to reach a
# workspace from an installed wheel, while CLAUDE.md documents the flag. These
# tests drive the launcher, not the parser, because the defect was in how the
# launcher composed argv -- a parser-level test would have passed throughout.
# ---------------------------------------------------------------------------
def _capture_run_app(monkeypatch) -> dict[str, object]:
    """Record what `cli._app` hands `run_app`, without importing or serving the app."""
    captured: dict[str, object] = {}

    def fake_run_app(name, *, root, host, port, debug):
        captured.update(name=name, root=root, host=host, port=port, debug=debug)
        return 0

    monkeypatch.setattr(runner, "run_app", fake_run_app)
    return captured


def _isolated_workspace(tmp_path: Path, monkeypatch) -> Path:
    """A workspace that neither the env var nor CWD discovery could have supplied.

    The CWD is moved to a sibling directory and the env var cleared, so a root
    that still arrives at `run_app` can only have come from the flag.
    """
    root = tmp_path / "workspace"
    root.mkdir()
    _workspace(root)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.delenv(WORKSPACE_ENV_VAR, raising=False)
    monkeypatch.chdir(elsewhere)
    return root.resolve()


@pytest.mark.parametrize(
    "spelling",
    [
        pytest.param(["--workspace", "{root}"], id="two-token"),
        pytest.param(["--workspace={root}"], id="single-token"),
    ],
)
def test_eia_dashboard_accepts_workspace_before_the_subcommand(tmp_path, monkeypatch, spelling):
    """`eia-dashboard --workspace X` must resolve the workspace to X.

    Both spellings argparse accepts for the top-level option are covered; the
    single-token `--workspace=X` form never reaches the two-token branch.
    """
    root = _isolated_workspace(tmp_path, monkeypatch)
    captured = _capture_run_app(monkeypatch)

    assert launchers.eia_dashboard([token.format(root=root) for token in spelling]) == 0
    assert captured["root"] == root
    assert captured["name"] == "eia-dashboard"


def test_eia_dashboard_still_forwards_subcommand_arguments(tmp_path, monkeypatch):
    """Lifting `--workspace` out must not swallow the options around it.

    `--host`/`--port`/`--debug` belong to the `app` subparser and have to stay
    behind; `run.py` passes `--debug` this way on every operator launch.
    """
    root = _isolated_workspace(tmp_path, monkeypatch)
    captured = _capture_run_app(monkeypatch)

    arguments = ["--host", "0.0.0.0", "--workspace", str(root), "--port", "9101", "--debug"]
    assert launchers.eia_dashboard(arguments) == 0
    assert captured["root"] == root
    assert (captured["host"], captured["port"], captured["debug"]) == ("0.0.0.0", 9101, True)


def test_eia_dashboard_still_honours_the_workspace_environment_variable(tmp_path, monkeypatch):
    """`DASH_EIA_WORKSPACE` keeps working when no flag is given."""
    root = _isolated_workspace(tmp_path, monkeypatch)
    captured = _capture_run_app(monkeypatch)
    monkeypatch.setenv(WORKSPACE_ENV_VAR, str(root))

    assert launchers.eia_dashboard([]) == 0
    assert captured["root"] == root


def test_eia_dashboard_still_discovers_the_workspace_from_the_cwd(tmp_path, monkeypatch):
    """Walking up from the CWD keeps working when no flag and no env var is given."""
    root = _isolated_workspace(tmp_path, monkeypatch)
    captured = _capture_run_app(monkeypatch)
    monkeypatch.chdir(root)

    assert launchers.eia_dashboard([]) == 0
    assert captured["root"] == root


def test_working_directory_puts_the_workspace_on_the_import_path(tmp_path):
    """The dashboard is reached as `src.index`, which lives in the workspace.

    Changing directory does not affect `sys.path`, so without this the installed
    command raises ModuleNotFoundError for `src` while sitting in the right
    directory. The entry must also be removed again on exit.
    """
    (tmp_path / "dash_eia_compat_probe.py").write_text("VALUE = 42\n", encoding="utf-8")
    before = list(sys.path)
    try:
        with working_directory(tmp_path):
            assert str(tmp_path.resolve()) in sys.path
            assert importlib.import_module("dash_eia_compat_probe").VALUE == 42
    finally:
        sys.modules.pop("dash_eia_compat_probe", None)
    assert sys.path == before


def test_src_references_stay_inside_the_compat_layer():
    """The wheel ships only `src/dash_eia`, so `src.index` is reachable via compat alone.

    `apps/runner.py` holds the transitional app spec and imports it inside
    `working_directory`. A `src.` reference anywhere else would resolve in a
    checkout and fail once installed.
    """
    allowed = {"apps/runner.py"}
    package = Path(__file__).resolve().parents[1] / "src" / "dash_eia"
    reference = re.compile(r"""(?:from|import)\s+src\.|["']src\.[A-Za-z_]""")
    offenders = {
        path.relative_to(package).as_posix()
        for path in package.rglob("*.py")
        if reference.search(path.read_text(encoding="utf-8"))
    }
    assert offenders <= allowed


# ---------------------------------------------------------------------------
# Guard A — no module-scope credential loading.
#
# Importing a module must never put a secret into ``os.environ`` and must never
# require one to be there already. For a pytest session, "import time" is
# *collection* time: it happens before any fixture runs, so nothing a test does
# can undo it, and a module that hard-indexes a credential turns a missing
# ``.env`` into a collection error rather than a test failure.
#
# ``ROOTS`` is derived from ``__file__``, not from the process CWD. A relative
# ``Path("src")`` would resolve to nothing when pytest is invoked from anywhere
# but the repository root, and a guard that walks zero files passes.
#
# Both importable top-level trees are walked, not just ``src/``. ``pythonpath``
# is ``["src", "."]``, so ``eia_downloads`` is importable too, and it carries a
# near-verbatim copy of the ``src/steo`` downloaders. Walking only one of the
# two would leave the guard reporting green on half the code it claims to cover.
# ---------------------------------------------------------------------------
_REPO = Path(__file__).resolve().parents[1]
ROOTS = (_REPO / "src", _REPO / "eia_downloads")

# Substrings that make an environment variable name credential-shaped.
_CREDENTIAL_NAME = re.compile(
    r"ACCESS|AUTH|AWS|BUCKET|CREDENTIAL|KEY|PASS|SECRET|TOKEN|USER|^DB_|^PG|POSTGRES"
)


def _is_main_guard(node: ast.If) -> bool:
    """True for ``if __name__ == "__main__":``, which never runs on import."""
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _runs_at_import(tree: ast.Module) -> Iterator[ast.stmt | ast.expr]:
    """Yield every node evaluated while the module is being imported.

    Walking only ``tree.body`` -- the top-level statement list -- is not
    sufficient, and the gap is not hypothetical: it is exactly how this repo hid
    a ``load_dotenv()`` at ``src/steo/meta.py``. Nested one level inside a
    ``try:``, it executed at precisely the same moment as one at column 0 while
    reading as though it were guarded. ``try``/``if``/``with``/loops/class
    bodies all run on import, so this descends through them.

    It stops at two boundaries, both of which genuinely do not run on import:
    a ``def`` body (its decorators and default values do, so those are kept),
    and ``if __name__ == "__main__":`` (an ``else:`` branch on that guard *does*
    run, so it is kept).
    """
    stack: list[ast.AST] = list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            stack.extend(node.decorator_list)
            stack.extend(d for d in [*node.args.defaults, *node.args.kw_defaults] if d)
            continue
        if isinstance(node, ast.Lambda):
            continue
        if isinstance(node, ast.If) and _is_main_guard(node):
            stack.extend(node.orelse)
            continue
        # Traversal covers every child; only statements and expressions are
        # yielded, because they are the nodes that carry a `lineno` to report.
        if isinstance(node, ast.stmt | ast.expr):
            yield node
        stack.extend(ast.iter_child_nodes(node))


def _import_time_offenders(check) -> list[str]:
    """Apply ``check`` to every import-time node of every module under ``ROOTS``."""
    offenders: list[str] = []
    for root in ROOTS:
        assert root.is_dir(), f"guard root is missing: {root}"
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            where = path.relative_to(_REPO).as_posix()
            for node in _runs_at_import(tree):
                finding = check(node)
                if finding is not None:
                    offenders.append(f"{where}:{node.lineno}: {finding}")
    return sorted(offenders)


def test_no_module_scope_load_dotenv():
    """Importing anything importable must not read `.env`.

    A module-scope `load_dotenv()` puts real credentials into `os.environ` the
    moment the module is imported -- which, for a test session, is collection
    time. `monkeypatch.setenv`/`delenv` cannot undo that: the loader is
    idempotent behind a module global, so the values are already there and stay
    there for every test that follows. Load `.env` inside the function that
    needs the value, as `steo/meta.py::_load_dotenv` now does.
    """

    def check(node: ast.stmt | ast.expr) -> str | None:
        if not isinstance(node, ast.Call):
            return None
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        return "load_dotenv()" if name == "load_dotenv" else None

    offenders = _import_time_offenders(check)
    assert not offenders, f"import-time load_dotenv(): {offenders}"


def test_no_module_scope_credential_environ_reads():
    """Importing anything importable must not index `os.environ` for a secret.

    `os.environ["EIA_API_KEY"]` at module scope is the defect that left a
    sibling repo's CI red for four consecutive runs: with no `.env` on a runner
    the subscript raises `KeyError` during collection, so *no* test in that file
    ever executed and every green result it had came from a developer machine.
    Read credentials inside the function that needs them.

    A non-literal key (`os.environ[NAME]`) is reported too -- it cannot be shown
    to be safe from the source alone, so it is not assumed to be.
    """

    def check(node: ast.stmt | ast.expr) -> str | None:
        if not isinstance(node, ast.Subscript):
            return None
        target = node.value
        is_environ = (isinstance(target, ast.Attribute) and target.attr == "environ") or (
            isinstance(target, ast.Name) and target.id == "environ"
        )
        if not is_environ:
            return None
        key = node.slice.value if isinstance(node.slice, ast.Constant) else None
        if key is None:
            return "environ[<non-literal>]"
        if _CREDENTIAL_NAME.search(str(key).upper()):
            return f"environ[{key!r}]"
        return None

    offenders = _import_time_offenders(check)
    assert not offenders, f"import-time credential read: {offenders}"
