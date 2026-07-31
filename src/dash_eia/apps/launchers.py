"""Console-script entry points for the registered applications."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from dash_eia import cli

# `--workspace` is registered on the *top-level* parser in `cli.build_parser`,
# not on the `app` subparser, so argparse only accepts it ahead of the
# subcommand. This launcher supplies `app eia-dashboard` itself and appends the
# caller's arguments after it, which is why `eia-dashboard --workspace X` died
# with "unrecognized arguments" (exit 2) while the equivalent
# `dash-eia --workspace X app eia-dashboard` worked. Lift the option back over
# the subcommand before handing argv on.
_WORKSPACE = "--workspace"


def _hoist_workspace(argv: Sequence[str]) -> tuple[list[str], list[str]]:
    """Split ``argv`` into a top-level ``--workspace`` pair and the remainder.

    Both spellings argparse accepts for a value-taking option are supported:
    ``--workspace VALUE`` and ``--workspace=VALUE``. The option is recognised
    anywhere ahead of a bare ``--`` separator, and a later occurrence replaces an
    earlier one, mirroring argparse's own last-one-wins behaviour.

    Two things are deliberately *not* recognised, because handling them would
    change what the CLI accepts rather than merely where it accepts it:

    - ``-w``. No such short option exists on the parser, so emitting one would
      build an argv that argparse rejects, and inventing it here would give
      `eia-dashboard` a flag that `dash-eia` does not have.
    - Unambiguous abbreviations such as ``--work``, which argparse resolves for
      `dash-eia`. They stay with the subcommand and are reported there.

    A malformed pair -- no value, or a value that reads as another option -- is
    left in place so argparse raises its own error rather than this function
    inventing one.
    """
    workspace: list[str] = []
    remainder: list[str] = []
    tokens = list(argv)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            remainder.extend(tokens[index:])
            break
        if token.startswith(f"{_WORKSPACE}="):
            workspace = [_WORKSPACE, token.split("=", 1)[1]]
            index += 1
            continue
        follows = tokens[index + 1] if index + 1 < len(tokens) else None
        if token == _WORKSPACE and follows is not None and not follows.startswith("-"):
            workspace = [_WORKSPACE, follows]
            index += 2
            continue
        remainder.append(token)
        index += 1
    return workspace, remainder


def eia_dashboard(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    workspace, remainder = _hoist_workspace(arguments)
    return cli.main([*workspace, "app", "eia-dashboard", *remainder])
