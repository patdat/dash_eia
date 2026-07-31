"""Page-level coverage for the dashboard's tables.

Before this file the suite had none: `pages/**` is excluded from ruff and sits
outside `pyright.include`, so nothing checked it at all, and a page could raise
on import without a single test going red.

Two things are covered here.

Guard C (`test_number_formats_name_a_scheme`) pins the fix for a bug that made
every number in every `dash_table` unreadable -- see the docstring on that test.

The rest is smoke coverage: each page that builds a table must import, expose a
layout that renders, and -- where a callback feeds the table -- return the
shape the layout expects.

These tests read the generated data under `data/`, which is tracked precisely
so that a fresh clone and CI can run them. If that data is ever untracked
again, these tests go red, which is the intended alarm rather than a nuisance:
`src/index.py` imports all 40 page modules eagerly and ~19 read data at module
scope, so untracking it also breaks importing the dashboard at all.
"""

import ast
import importlib
from pathlib import Path

import pytest

from dash_eia.apps.compat import working_directory

_REPO = Path(__file__).resolve().parents[1]
_PAGES = _REPO / "pages"

# Pages that build a dash_table.DataTable. Kept explicit rather than globbed so
# that adding a table to a new page is a deliberate edit here too.
TABLE_PAGES = [
    "page2_1",
    "page5_1",
    "page5_2",
    "page5_3",
    "page5_4",
    "page5_5",
    "page5_6",
    "page5_7",
    "page5_8",
    "page5_9",
    "page5_10",
]


def _import_page(name: str):
    """Import a page module with the workspace on sys.path and as the CWD.

    Both halves matter. `pages` resolves only because the repo root is
    importable, and the page modules load `data/` and `lookup/` through paths
    relative to the process working directory.
    """
    with working_directory(_REPO):
        return importlib.import_module(f"pages.{name}")


def _render(layout):
    """`page5_2` exports a callable layout; every other page exports a value."""
    return layout() if callable(layout) else layout


# ---------------------------------------------------------------------------
# Guard C — a number format must name its scheme.
# ---------------------------------------------------------------------------
def test_number_formats_name_a_scheme():
    """`Format(precision=N)` does not mean "N decimal places".

    dash_table hands the specifier straight to d3-format, and d3 treats a
    specifier whose type character is missing as `~g` -- *significant digits*.
    dash_table's own bundle does this explicitly:

        rn[g] || (void 0 === v && (v = 12), b = !0, g = "g")

    (`g` = type, `v` = precision, `b` = trim). Because these call sites all pass
    a precision, the 12-digit default never applied and the specifier became
    `.1~g`: `Format(precision=1)` rendered 439279 as "4e+5" and 12.7 as "1e+1",
    and `Format(precision=0)` rendered a count of 77 as "8e+1". 55 of the 58
    Format() calls in `pages/` were affected -- i.e. very nearly every number
    the dashboard displayed in a table.

    Naming the scheme (`scheme=Scheme.fixed` -> `.1f`) is what makes precision
    mean decimal places. A precision with no scheme is always this bug, so it
    is banned outright.

    The one legitimate schemeless case is a Format with *no* precision, which d3
    reads as `.12~g` and renders as a plain grouped number; `page2_1` relies on
    that for its non-yield tables. So the rule is conditional on precision being
    supplied, not on the scheme being absent.
    """
    offenders: list[str] = []
    for path in sorted(_PAGES.glob("page*.py")):
        source = path.read_text(encoding="utf-8")
        if "dash_table" not in source:
            continue
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if getattr(node.func, "id", None) != "Format":
                continue
            keywords = {kw.arg for kw in node.keywords}
            if "precision" in keywords and "scheme" not in keywords:
                where = path.relative_to(_REPO).as_posix()
                offenders.append(f"{where}:{node.lineno}: Format(precision=...) without scheme=")

    assert not offenders, (
        "a Format() that sets precision but no scheme renders in scientific "
        f"notation (e.g. 439279 -> '4e+5'): {offenders}"
    )


# ---------------------------------------------------------------------------
# Smoke coverage
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", TABLE_PAGES)
def test_page_imports_and_builds_its_layout(name):
    """A page must import and produce a layout without touching a callback.

    All 40 live pages are imported eagerly by `src/index.py`, so an import-time
    error in any one of them takes down the whole app.
    """
    module = _import_page(name)
    layout = _render(module.layout)
    assert layout is not None
    assert hasattr(layout, "to_plotly_json"), f"pages.{name}.layout is not a Dash component"


def test_headline_tables_render_from_store_records():
    """`page2_1` builds its 39 tables from `dcc.Store` records, not from a frame.

    The distinction is load-bearing. `generate_main_table` transposes and calls
    `reset_index()`, and the name of the resulting column depends on whether the
    columns Index carried a name: a feather-loaded frame yields `id` and the
    rename to `name` silently does nothing, while the records round-trip the
    Store performs yields `index`, which renames correctly. Feeding this
    function a frame straight off disk raises KeyError('name'), so the test has
    to go through the same records path the callback does.
    """
    import pandas as pd

    module = _import_page("page2_1")
    with working_directory(_REPO):
        raw = pd.read_feather("./data/wps/wps_gte_2015_pivot.feather")
        result = module.update_tables(raw.to_dict("records"))

    assert hasattr(result, "to_plotly_json")
    payload = str(result.to_plotly_json())
    assert "US Commercial Stocks (kb)" in payload


@pytest.mark.parametrize(
    ("name", "callback", "expected_outputs"),
    [
        ("page5_1", "update_overview_charts", 8),
        ("page5_5", "update_country_risk_charts", 3),
        ("page5_10", "update_alerts_dashboard", 6),
    ],
)
def test_table_callbacks_return_one_component_per_output(name, callback, expected_outputs):
    """The table callbacks fan a single dropdown value out to several children.

    Each returned item lands in a `html.Div(id=...)`'s `children`, so every one
    of them has to be a renderable component -- a callback that quietly returns
    a DataFrame or a tuple of the wrong length fails at render time in the
    browser, where nothing in this suite would have seen it.
    """
    module = _import_page(name)
    with working_directory(_REPO):
        result = getattr(module, callback)("US")

    assert isinstance(result, tuple)
    assert len(result) == expected_outputs
    for item in result:
        assert hasattr(item, "to_plotly_json"), f"{callback} returned a non-component: {type(item)}"


def test_padd_filter_changes_the_rendered_table():
    """Filtering by PADD must actually narrow the data, not silently no-op.

    `page5_5` rebinds `filtered_processor` to the module-level processor on the
    'US' branch, so a filter that failed to apply would still return a valid
    table -- identical to the unfiltered one. Comparing the two catches that.
    """
    module = _import_page("page5_5")
    with working_directory(_REPO):
        national = module.generate_country_risk_table("US")
        gulf = module.generate_country_risk_table("PADD 3")

    assert national.data != gulf.data, "PADD 3 returned the same rows as All US"
    assert gulf.data, "PADD 3 returned no rows at all"
