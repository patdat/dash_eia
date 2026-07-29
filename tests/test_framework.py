import importlib
import re
import sys
from pathlib import Path

from dash_eia.apps.compat import working_directory
from dash_eia.cli import main
from dash_eia.config.paths import WorkspacePaths


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
