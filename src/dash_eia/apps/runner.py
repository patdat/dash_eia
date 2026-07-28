"""Import-safe application registry with legacy compatibility."""

from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppSpec:
    module: str
    default_port: int
    attribute: str = "app"


APP_SPECS = {
    # Transitional import while characterized pages move under
    # dash_eia.apps.eia_dashboard.
    "eia-dashboard": AppSpec("src.index", 8052),
}
APP_NAMES = tuple(APP_SPECS)


def run_app(
    name: str,
    *,
    host: str = "127.0.0.1",
    port: int | None = None,
    debug: bool = False,
) -> int:
    try:
        spec = APP_SPECS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown app {name!r}; choose one of: {', '.join(APP_NAMES)}") from exc
    app = getattr(importlib.import_module(spec.module), spec.attribute)
    app.run(host=host, port=port or spec.default_port, debug=debug)
    return 0
