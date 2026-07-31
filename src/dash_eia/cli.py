"""Canonical dashboard command line."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from dash_eia.apps.runner import APP_NAMES
from dash_eia.config.paths import WorkspacePaths


def _bootstrap(args: argparse.Namespace) -> int:
    from dash_eia.pipelines.bootstrap import run

    return run(WorkspacePaths.discover(args.workspace))


def _app(args: argparse.Namespace) -> int:
    from dash_eia.apps.runner import run_app

    paths = WorkspacePaths.discover(args.workspace)
    return run_app(
        args.name,
        root=paths.root,
        host=args.host,
        port=args.port,
        debug=args.debug,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dash-eia")
    parser.add_argument("--workspace")
    commands = parser.add_subparsers(dest="command")
    bootstrap = commands.add_parser("bootstrap")
    bootstrap.set_defaults(handler=_bootstrap)
    app = commands.add_parser("app")
    app.add_argument("name", choices=APP_NAMES)
    app.add_argument("--host", default="127.0.0.1")
    app.add_argument("--port", type=int)
    app.add_argument("--debug", action="store_true")
    app.set_defaults(handler=_app)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)
