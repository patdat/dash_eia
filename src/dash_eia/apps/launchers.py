import sys
from collections.abc import Sequence

from dash_eia import cli


def eia_dashboard(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    return cli.main(["app", "eia-dashboard", *arguments])
