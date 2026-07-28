from pathlib import Path

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
