"""Workspace discovery and canonical EIA dashboard paths."""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

PROJECT_NAME = "dash-eia"
WORKSPACE_ENV_VAR = "DASH_EIA_WORKSPACE"


class WorkspaceNotFoundError(RuntimeError):
    pass


def _is_workspace(path: Path) -> bool:
    project = path / "pyproject.toml"
    if not project.is_file():
        return False
    try:
        return (
            tomllib.loads(project.read_text(encoding="utf-8")).get("project", {}).get("name")
            == PROJECT_NAME
        )
    except (OSError, tomllib.TOMLDecodeError):
        return False


@dataclass(frozen=True, slots=True)
class WorkspacePaths:
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root).expanduser().resolve())

    @classmethod
    def discover(
        cls,
        workspace: str | os.PathLike[str] | None = None,
        *,
        environ: Mapping[str, str] | None = None,
        cwd: str | os.PathLike[str] | None = None,
    ) -> WorkspacePaths:
        environment = os.environ if environ is None else environ
        if workspace is not None:
            candidate = Path(workspace).expanduser().resolve()
            if not _is_workspace(candidate):
                raise WorkspaceNotFoundError(f"Not a {PROJECT_NAME} workspace: {candidate}")
            return cls(candidate)
        configured = environment.get(WORKSPACE_ENV_VAR)
        if configured:
            return cls.discover(configured, environ=environment)
        current = (Path.cwd() if cwd is None else Path(cwd)).resolve()
        for candidate in (current, *current.parents):
            if _is_workspace(candidate):
                return cls(candidate)
        raise WorkspaceNotFoundError(
            f"No workspace found; pass --workspace or set {WORKSPACE_ENV_VAR}."
        )

    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def reference(self) -> Path:
        return self.data / "reference"

    @property
    def raw(self) -> Path:
        return self.data / "raw"

    @property
    def interim(self) -> Path:
        return self.data / "interim"

    @property
    def processed(self) -> Path:
        return self.data / "processed"

    @property
    def exports(self) -> Path:
        return self.data / "exports"

    @property
    def state(self) -> Path:
        return self.data / "state"

    @property
    def cache(self) -> Path:
        return self.data / "cache"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def required_directories(self) -> tuple[Path, ...]:
        return (
            self.reference,
            self.raw,
            self.interim,
            self.processed,
            self.exports,
            self.state,
            self.cache,
            self.logs,
        )
