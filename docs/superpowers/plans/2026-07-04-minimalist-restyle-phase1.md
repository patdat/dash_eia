# Minimalist Restyle — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `dash_eia` quant_dash's minimalist look — neutral flat design tokens, a light config-driven sidebar, and a muted accent+gray chart palette — without changing any page behavior or route.

**Architecture:** Rework the shared layers every page depends on: `assets/styles.css` (tokens + reskin), a new config-driven sidebar (`src/config/navigation.py` + `src/components/shell.py` wired into `src/index.py` with one collapse callback), the central `src/utils/colors.py` palette, and a new `src/utils/plotly_theme.py` chrome helper applied by the four graph modules. Routing and page bodies are untouched.

**Tech Stack:** Python 3.11, Dash 3.2, dash-bootstrap-components, Plotly, pytest 9.

## Global Constraints

- Do **not** change any route href or the `display_page` routing callback — sidebar links must resolve to the exact same paths that exist today.
- No behavior changes to page bodies or data loading in this phase.
- No CDN dependencies for fonts or icons — Inter and FontAwesome load from local `assets/`.
- Single muted-blue accent `#0072ab`; bright `#00ADEF` used only for the logo/brand.
- Base font: local Inter, 13px. Flat design: no box-shadows, no hover-lift, radii 6–8px.
- Multi-year chart palette = accent + progressively lighter grays (current year = accent).
- Keep the public names exported by `src/utils/colors.py` unchanged (only values change).
- Reference repo to port idioms from: `/Users/patrickmarable/Documents/GitHub/quant_dash`.

---

## Setup (before Task 1)

Execution happens in an isolated worktree. Using the `superpowers:using-git-worktrees` skill, create a worktree off `main` (proposed branch `minimalist-restyle`, path `.worktrees/minimalist-restyle`). Run all tasks there. First, move the already-written spec + this plan into the branch history:

```bash
git add docs/superpowers/specs/2026-07-04-minimalist-restyle-phase1-design.md \
        docs/superpowers/plans/2026-07-04-minimalist-restyle-phase1.md
git commit -m "docs: add Phase 1 minimalist restyle spec and plan"
```

Sanity-check the app boots before changing anything: `python run.py` → open http://localhost:8052 → confirm home loads → stop.

---

## File Structure

- `assets/fonts/InterVariable.woff2` — **create** (copied from quant_dash)
- `assets/fontawesome/` — **create** (css + webfonts copied from quant_dash)
- `assets/styles.css` — **modify** (tokens + reskin, remove @imports)
- `assets/styles.css.bak` — **delete**
- `src/app.py` — **modify** (drop 9 Google-font external_stylesheets)
- `src/config/__init__.py` — **create** (empty)
- `src/config/navigation.py` — **create** (`BRAND`, `NAV_SECTIONS`)
- `src/components/__init__.py` — **create** (empty)
- `src/components/shell.py` — **create** (`build_sidebar`, `_nav_link`, `compute_collapse_state`)
- `src/index.py` — **modify** (use `build_sidebar`, one collapse callback)
- `src/utils/colors.py` — **modify** (retune palette values)
- `src/utils/plotly_theme.py` — **create** (`apply_minimal_chrome`)
- `src/wps/graph_line.py`, `src/wps/graph_seag.py`, `src/wps/graph_optionality.py`, `src/steo/chart_dpr.py` — **modify** (wrap layout in `apply_minimal_chrome`)
- `tests/` — **create** (`test_navigation.py`, `test_shell.py`, `test_colors.py`, `test_plotly_theme.py`)

---

## Task 1: Local fonts & icons (kill CDN font/icon deps)

**Files:**
- Create: `assets/fonts/InterVariable.woff2`, `assets/fontawesome/css/all.min.css`, `assets/fontawesome/webfonts/*`
- Modify: `src/app.py:11-23`, `assets/styles.css:35-46` (the `@import` block)

**Interfaces:**
- Produces: local `Inter` font available via `@font-face`; local FontAwesome CSS; `src/app.py` `external_stylesheets` reduced to `[dbc.themes.BOOTSTRAP]`.

- [ ] **Step 1: Copy local assets from quant_dash**

```bash
mkdir -p assets/fonts assets/fontawesome/css assets/fontawesome/webfonts
cp /Users/patrickmarable/Documents/GitHub/quant_dash/src/assets/fonts/InterVariable.woff2 assets/fonts/
cp /Users/patrickmarable/Documents/GitHub/quant_dash/src/assets/fontawesome/css/all.min.css assets/fontawesome/css/
cp /Users/patrickmarable/Documents/GitHub/quant_dash/src/assets/fontawesome/webfonts/* assets/fontawesome/webfonts/
ls assets/fonts assets/fontawesome/css assets/fontawesome/webfonts
```

Expected: `InterVariable.woff2`, `all.min.css`, and `fa-solid-900.woff2` / `fa-regular-400.woff2` listed.

- [ ] **Step 2: Remove the 9 Google-font entries from `src/app.py`**

Replace the `external_stylesheets=[...]` list (lines 11-23) so only Bootstrap remains:

```python
app = Dash(__name__, suppress_callback_exceptions=True,
           assets_folder=os.path.join(PROJECT_ROOT, 'assets'),
           external_stylesheets=[dbc.themes.BOOTSTRAP])
```

- [ ] **Step 3: Replace the `@import` block at the top of `assets/styles.css`**

Delete the 9 Google-font `@import`s and the FontAwesome CDN `@import` (lines 35-46) and put this at the very top of the file:

```css
@font-face {
    font-family: "Inter";
    src: url("/assets/fonts/InterVariable.woff2") format("woff2-variations");
    font-weight: 100 900;
    font-style: normal;
    font-display: swap;
}
@import url("/assets/fontawesome/css/all.min.css");
```

- [ ] **Step 4: Verify no CDN font/icon references remain**

Run:
```bash
grep -nE "fonts.googleapis|cloudflare|cdnjs" src/app.py assets/styles.css; echo "exit=$?"
```
Expected: no matches (grep prints nothing; `exit=1`).

- [ ] **Step 5: Boot the app**

Run: `python run.py` → open http://localhost:8052 → confirm the home page still renders (fonts may look default until Task 2) → stop the server.
Expected: no console 404s for `InterVariable.woff2` or `all.min.css`.

- [ ] **Step 6: Commit**

```bash
git add assets/fonts assets/fontawesome src/app.py assets/styles.css
git commit -m "chore(assets): serve Inter + FontAwesome locally, drop font CDNs"
```

---

## Task 2: Design tokens & flat CSS reskin

**Files:**
- Modify: `assets/styles.css` (`:root`, `body`, component rules, EIA layout rules)
- Delete: `assets/styles.css.bak`

**Interfaces:**
- Produces: the token variables (`--bg`, `--surface`, `--border`, `--border-strong`, `--text`, `--text-secondary`, `--text-muted`, `--hover`, `--row-hover`, `--accent`, `--accent-hover`, `--accent-soft`, `--brand-blue`, `--positive`, `--negative`, `--warning`, `--radius-lg`, `--radius-md`, `--sidebar-width`) that Task 3's sidebar CSS and all component rules consume.

- [ ] **Step 1: Replace the `:root` block** (the old `--color-*`, `--shadow-*`, big-radius block) with:

```css
:root {
    --bg: #fafbfc;
    --surface: #ffffff;
    --border: #e5e8ec;
    --border-strong: #d3d8de;
    --text: #1a2332;
    --text-secondary: #5c6b7f;
    --text-muted: #8b97a6;
    --hover: #f2f4f7;
    --row-hover: #f7f9fb;
    --accent: #0072ab;
    --accent-hover: #005f8f;
    --accent-soft: #eaf5fb;
    --brand-blue: #00ADEF;
    --positive: #1a7f42;
    --negative: #c8102e;
    --warning: #b45d0e;
    --radius-lg: 8px;
    --radius-md: 6px;
    --sidebar-width: 15rem;
}
```

- [ ] **Step 2: Set the base typography** — replace the `body` font rule:

```css
body {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 13px;
    color: var(--text);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    letter-spacing: 0;
}
```

- [ ] **Step 3: Flatten the card/hero/button/alert rules.** For every rule that currently sets `box-shadow: var(--shadow-*)`, `transform: translateY(...)`, big radii, or `--color-*` values, change to: `box-shadow: none;`, remove the transform (or `transform: none;`), radii → `var(--radius-lg)`/`var(--radius-md)`, colors → the `--text*`/`--surface`/`--border`/`--accent` tokens. Specifically neutralize:
  - `.metric-card, .feature-card, .surface-card` → `border: 1px solid var(--border); box-shadow: none;` and their `:hover` → `transform: none; box-shadow: none;`
  - `.page-hero` → `background: none; border-bottom: 1px solid var(--border); box-shadow: none; padding: 0 0 1rem;` (remove the radial gradients)
  - `.page-title` → `font-size: 20px; font-weight: 650; color: var(--text);`
  - `.page-eyebrow` → `color: var(--text-muted); font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;`
  - `.metric-value` → `font-size: 22px; color: var(--text); font-variant-numeric: tabular-nums;`
  - `.metric-blue/green/orange/red` helper classes → point all to `color: var(--text);` except keep `.delta`-style semantics via `--positive`/`--negative` where used.

- [ ] **Step 4: Reskin the EIA-specific & tab rules** — keep selectors and grid dimensions (`.eia-weekly-graph-container`, `.eia-dpr-graph-container`, `.graph-container`, `.eia_table_style`, date-picker, AG-Grid, `#p15-tabs`, `#wps-combined-tabs`, `#dpr-table-tabs`) but:
  - `.graph-container` → `box-shadow: none; border: 1px solid var(--border); border-radius: var(--radius-lg); background: var(--surface);`
  - Tab bars (`#wps-combined-tabs`, `#dpr-table-tabs`, `#p15-tabs`) → `background: var(--surface); border-bottom: 1px solid var(--border);`; `.nav-link` text `var(--text-secondary)`; `.nav-link.active` → `color: var(--accent) !important; border-bottom: 2px solid var(--accent); background: transparent !important;`
  - AG-Grid `.ag-theme-alpine .ag-row.ag-row-selected` → `background-color: var(--accent-soft) !important; color: var(--text);`
  - Date-picker `--color-red` references → `var(--accent)`.

- [ ] **Step 5: Delete the backup file**

```bash
git rm assets/styles.css.bak
```

- [ ] **Step 6: Verify no stale tokens remain**

Run:
```bash
grep -nE "shadow-soft|shadow-hover|--color-red|translateY|Montserrat" assets/styles.css; echo "exit=$?"
```
Expected: no matches (`exit=1`). (Sidebar rules referencing old tokens are rewritten in Task 3.)

- [ ] **Step 7: Visual check** — `python run.py` → load `/home` and `/stats/headline` → confirm flat white cards, no drop shadows, Inter font, neutral palette → stop.

- [ ] **Step 8: Commit**

```bash
git add assets/styles.css
git commit -m "style(css): flat minimalist tokens, neutral palette, remove shadows"
```

---

## Task 3: Navigation config

**Files:**
- Create: `src/config/__init__.py` (empty), `src/config/navigation.py`
- Test: `tests/test_navigation.py`

**Interfaces:**
- Produces:
  - `BRAND: dict` with keys `name`, `href`, `logo_src`.
  - `HOME: dict` with keys `label`, `href`, `icon`.
  - `NAV_SECTIONS: list[dict]`, each with `id: str`, `label: str`, `icon: str`, `initial_open: bool`, `links: list[dict]` where each link has `label: str`, `href: str`.
  - Consumed by `src/components/shell.py::build_sidebar` (Task 4) and `src/index.py` (Task 5).

- [ ] **Step 1: Write the failing test** — `tests/test_navigation.py`:

```python
from src.config.navigation import BRAND, HOME, NAV_SECTIONS

# The exact set of hrefs the routing callback in src/index.py serves today.
KNOWN_ROUTES = {
    "/home",
    "/stats/headline", "/stats/graphing", "/stats/stats_table",
    "/stats/padd_regional", "/stats/cushing_analysis", "/stats/runs_analysis",
    "/stats/supply_demand", "/stats/time_series_analytics",
    "/dpr/dpr_charts", "/dpr/dpr_table", "/dpr/efficiency_heatmap",
    "/dpr/duc_waterfall", "/dpr/productivity_matrix", "/dpr/performance_radar",
    "/steo/tbd1", "/steo/tbd2", "/steo/tbd3", "/steo/tbd4", "/steo/tbd5", "/steo/tbd6",
    "/cli/market_overview", "/cli/company_analysis", "/cli/quality_analysis",
    "/cli/regional_padd", "/cli/country_risk", "/cli/seasonal_patterns",
    "/cli/forecasting", "/cli/port_analysis", "/cli/trade_flow", "/cli/market_alerts",
    "/psm/tbd1", "/psm/tbd2", "/psm/tbd3", "/psm/tbd4", "/psm/tbd5", "/psm/tbd6",
}

def test_brand_and_home_shape():
    assert set(BRAND) >= {"name", "href", "logo_src"}
    assert set(HOME) >= {"label", "href", "icon"}
    assert HOME["href"] == "/home"

def test_sections_shape():
    ids = [s["id"] for s in NAV_SECTIONS]
    assert ids == ["weekly", "dpr", "steo", "cli", "psm"]
    for s in NAV_SECTIONS:
        assert set(s) >= {"id", "label", "icon", "initial_open", "links"}
        assert s["links"], f"{s['id']} has no links"
        for link in s["links"]:
            assert set(link) >= {"label", "href"}

def test_every_nav_href_is_a_known_route():
    hrefs = {HOME["href"]}
    for s in NAV_SECTIONS:
        hrefs.update(link["href"] for link in s["links"])
    assert hrefs == KNOWN_ROUTES
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_navigation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.config'`.

- [ ] **Step 3: Create the package + config** — `src/config/__init__.py` empty; `src/config/navigation.py`:

```python
"""Declarative sidebar navigation config (labels, hrefs, icons)."""

BRAND = {
    "name": "Socar",
    "href": "https://www.socartrading.com/",
    "logo_src": "/assets/company_logo.png",
}

HOME = {"label": "Home", "href": "/home", "icon": "fa-house"}

NAV_SECTIONS = [
    {
        "id": "weekly", "label": "EIA Weekly", "icon": "fa-calendar-week",
        "initial_open": True,
        "links": [
            {"label": "Headline", "href": "/stats/headline"},
            {"label": "Graphing", "href": "/stats/graphing"},
            {"label": "Stats Table", "href": "/stats/stats_table"},
            {"label": "PADD Analysis", "href": "/stats/padd_regional"},
            {"label": "Cushing Analysis", "href": "/stats/cushing_analysis"},
            {"label": "Runs Analysis", "href": "/stats/runs_analysis"},
            {"label": "Balance Analysis", "href": "/stats/supply_demand"},
            {"label": "Advanced Time Series", "href": "/stats/time_series_analytics"},
        ],
    },
    {
        "id": "dpr", "label": "EIA DPR", "icon": "fa-oil-well",
        "initial_open": True,
        "links": [
            {"label": "DPR Charts", "href": "/dpr/dpr_charts"},
            {"label": "DPR Table", "href": "/dpr/dpr_table"},
            {"label": "Efficiency Heatmap", "href": "/dpr/efficiency_heatmap"},
            {"label": "DUC Analysis", "href": "/dpr/duc_waterfall"},
            {"label": "Productivity Matrix Analysis", "href": "/dpr/productivity_matrix"},
            {"label": "Performance Radar Analysis", "href": "/dpr/performance_radar"},
        ],
    },
    {
        "id": "steo", "label": "EIA STEO", "icon": "fa-chart-line",
        "initial_open": True,
        "links": [
            {"label": "TBD", "href": f"/steo/tbd{i}"} for i in range(1, 7)
        ],
    },
    {
        "id": "cli", "label": "EIA CLI", "icon": "fa-ship",
        "initial_open": True,
        "links": [
            {"label": "Market Overview", "href": "/cli/market_overview"},
            {"label": "Company Analysis", "href": "/cli/company_analysis"},
            {"label": "Quality Analysis", "href": "/cli/quality_analysis"},
            {"label": "Regional/PADD", "href": "/cli/regional_padd"},
            {"label": "Country Risk", "href": "/cli/country_risk"},
            {"label": "Seasonal Patterns", "href": "/cli/seasonal_patterns"},
            {"label": "Time Series Forecasting", "href": "/cli/forecasting"},
            {"label": "Port Analysis", "href": "/cli/port_analysis"},
            {"label": "Trade Flow Analysis", "href": "/cli/trade_flow"},
            {"label": "Market Alerts", "href": "/cli/market_alerts"},
        ],
    },
    {
        "id": "psm", "label": "EIA PSM", "icon": "fa-gauge",
        "initial_open": True,
        "links": [
            {"label": "TBD", "href": f"/psm/tbd{i}"} for i in range(1, 7)
        ],
    },
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_navigation.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/config tests/test_navigation.py
git commit -m "feat(nav): declarative sidebar navigation config"
```

---

## Task 4: Sidebar builder component

**Files:**
- Create: `src/components/__init__.py` (empty), `src/components/shell.py`
- Test: `tests/test_shell.py`

**Interfaces:**
- Consumes: `BRAND`, `HOME`, `NAV_SECTIONS` from `src/config/navigation.py`.
- Produces:
  - `build_sidebar(brand: dict, home: dict, nav_sections: list) -> html.Aside` — the sidebar with a Home link plus one collapsible group per section. Toggle button IDs are `{"type": "nav-toggle", "index": <section id>}`; collapse IDs are `{"type": "nav-collapse", "index": <section id>}`.
  - `compute_collapse_state(nav_sections, is_open_list, triggered_index) -> tuple[list[bool], list[str]]` — pure helper the collapse callback (Task 5) uses; flips the triggered section's open state and returns `(new_open, new_classnames)` where classnames are `"sidebar-button page-button open|closed"`.

- [ ] **Step 1: Write the failing test** — `tests/test_shell.py`:

```python
from src.components.shell import build_sidebar, compute_collapse_state
from src.config.navigation import BRAND, HOME, NAV_SECTIONS


def test_build_sidebar_returns_aside_with_toggle_ids():
    side = build_sidebar(BRAND, HOME, NAV_SECTIONS)
    assert "sidebar" in side.className
    text = str(side)
    for s in NAV_SECTIONS:
        assert f"'index': '{s['id']}'" in text or f'"index": "{s["id"]}"' in text


def test_compute_collapse_state_toggles_only_triggered():
    sections = [{"id": "a"}, {"id": "b"}]
    open_list = [True, True]
    new_open, classes = compute_collapse_state(sections, open_list, "a")
    assert new_open == [False, True]
    assert classes[0].endswith("closed")
    assert classes[1].endswith("open")


def test_compute_collapse_state_reopens():
    sections = [{"id": "a"}]
    new_open, classes = compute_collapse_state(sections, [False], "a")
    assert new_open == [True]
    assert classes[0].endswith("open")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_shell.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.components'`.

- [ ] **Step 3: Create the component** — `src/components/__init__.py` empty; `src/components/shell.py`:

```python
"""Sidebar shell built from the declarative navigation config."""

from dash import html
import dash_bootstrap_components as dbc


def _nav_link(label, href, icon=None):
    children = []
    if icon:
        children.append(html.I(className=f"fa-solid {icon} nav-icon"))
    children.append(html.Span(label, className="nav-label"))
    extra = "" if icon else " nav-link-child"
    return dbc.NavLink(children, href=href, active="exact", className=f"nav-link{extra}")


def build_sidebar(brand, home, nav_sections):
    nav_items = [_nav_link(home["label"], home["href"], home["icon"])]

    for section in nav_sections:
        state = "open" if section["initial_open"] else "closed"
        nav_items.append(
            dbc.NavItem([
                dbc.Button(
                    [
                        html.Span([
                            html.I(className=f"fa-solid {section['icon']} nav-section-icon"),
                            html.Span(section["label"], className="nav-section-label"),
                        ], className="nav-section-left"),
                        html.I(className="fa-solid fa-chevron-down nav-section-chevron"),
                    ],
                    id={"type": "nav-toggle", "index": section["id"]},
                    className=f"sidebar-button page-button {state}",
                    n_clicks=0,
                ),
                dbc.Collapse(
                    dbc.Nav(
                        [_nav_link(l["label"], l["href"]) for l in section["links"]],
                        vertical=True, pills=True,
                    ),
                    id={"type": "nav-collapse", "index": section["id"]},
                    is_open=section["initial_open"],
                ),
            ])
        )

    return html.Aside(
        [
            html.Div([
                html.A(
                    html.Img(src=brand["logo_src"], alt=brand["name"], className="brand-logo"),
                    href=brand["href"], target="_blank", rel="noopener noreferrer",
                    className="brand-logo-link",
                ),
                html.A(
                    brand["name"], href=brand["href"], target="_blank",
                    rel="noopener noreferrer", className="brand-name",
                ),
            ], className="brand-lockup"),
            dbc.Nav(nav_items, vertical=True, pills=True, className="sidebar-nav"),
        ],
        className="sidebar d-flex flex-column vh-100",
    )


def compute_collapse_state(nav_sections, is_open_list, triggered_index):
    """Flip the triggered section; return (new_open_list, new_classnames)."""
    new_open = list(is_open_list)
    classes = []
    for i, section in enumerate(nav_sections):
        if section["id"] == triggered_index:
            new_open[i] = not new_open[i]
        classes.append(f"sidebar-button page-button {'open' if new_open[i] else 'closed'}")
    return new_open, classes
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_shell.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Replace the sidebar/tab CSS** — in `assets/styles.css`, **remove the old dash_eia sidebar and dark-tab rules** (`.sidebar` with `--color-sidebar-bg`, `.sidebar-button.page-button` with the `::after` triangles, `.sidebar .nav-link*`, and the dark `#p15-tabs` block if it duplicates the reskinned one) and **replace them** with quant_dash's sidebar rules (light background, brand lockup, nav sections, chevrons, active accent border). Copy the `.sidebar`, `.brand-lockup`, `.brand-logo`, `.brand-logo-link`, `.brand-name`, `.sidebar-nav`, `.nav-item`, `.sidebar-button.page-button`, `.nav-section-left`, `.nav-section-icon`, `.nav-section-label`, `.nav-section-chevron`, `.nav-link`, `.nav-link-child`, `.nav-icon`, `.nav-link:hover`, `.nav-link.active`, and `.content-area` blocks from `quant_dash/src/assets/styles.css` (lines ~73-228). The chevron rotates via `.sidebar-button.page-button.closed .nav-section-chevron { transform: rotate(-90deg); }`. Afterwards confirm no `--color-` variables remain referenced anywhere in the file: `grep -n "var(--color-" assets/styles.css; echo "exit=$?"` should print nothing (`exit=1`).

- [ ] **Step 6: Commit**

```bash
git add src/components tests/test_shell.py assets/styles.css
git commit -m "feat(shell): config-driven light sidebar builder + CSS"
```

---

## Task 5: Wire sidebar into index.py with one collapse callback

**Files:**
- Modify: `src/index.py` (replace inline `sidebar`, replace 5 collapse callbacks with 1)

**Interfaces:**
- Consumes: `build_sidebar`, `compute_collapse_state` (Task 4); `BRAND`, `HOME`, `NAV_SECTIONS` (Task 3).
- Produces: `app.layout` with the new sidebar; a single `toggle_nav_section` callback. `display_page` and all page imports unchanged.

- [ ] **Step 1: Add imports** near the top of `src/index.py` (after existing imports):

```python
from dash import ALL, ctx
from dash.exceptions import PreventUpdate
from src.config.navigation import BRAND, HOME, NAV_SECTIONS
from src.components.shell import build_sidebar, compute_collapse_state
```

- [ ] **Step 2: Replace the inline sidebar** — delete the entire `sidebar = html.Div([...])` block (the ~200-line block currently at lines 48-206) and replace with:

```python
sidebar = build_sidebar(BRAND, HOME, NAV_SECTIONS)
```

- [ ] **Step 3: Replace the five collapse callbacks** — delete `toggle_collapse_page_2` through `toggle_collapse_page_6` (all five) and add one:

```python
@app.callback(
    Output({"type": "nav-collapse", "index": ALL}, "is_open"),
    Output({"type": "nav-toggle", "index": ALL}, "className"),
    Input({"type": "nav-toggle", "index": ALL}, "n_clicks"),
    State({"type": "nav-collapse", "index": ALL}, "is_open"),
    prevent_initial_call=True,
)
def toggle_nav_section(n_clicks_list, is_open_list):
    triggered = ctx.triggered_id
    if not triggered:
        raise PreventUpdate
    return compute_collapse_state(NAV_SECTIONS, is_open_list, triggered["index"])
```

Leave `app.layout` (with `dcc.Location`, `sidebar`, `content`, and the `data-store` `dcc.Store`) and the `display_page` routing callback exactly as they are.

- [ ] **Step 4: Verify the module imports cleanly**

Run:
```bash
python -c "import src.index; print('layout ok:', src.index.app.layout is not None)"
```
Expected: prints `layout ok: True` with no exceptions.

- [ ] **Step 5: Manual smoke test** — `python run.py` → http://localhost:8052:
  - Sidebar is light with the brand lockup, section icons, and chevrons.
  - Each of the 5 sections collapses/expands independently when its header is clicked (chevron rotates).
  - Clicking links navigates and the active link shows the accent left-border.
  - Spot-check one page per section (Weekly/DPR/STEO/CLI/PSM) loads without error.
  - Stop the server.

- [ ] **Step 6: Commit**

```bash
git add src/index.py
git commit -m "refactor(index): build sidebar from config, single collapse callback"
```

---

## Task 6: Retune the chart palette

**Files:**
- Modify: `src/utils/colors.py`
- Test: `tests/test_colors.py`

**Interfaces:**
- Produces: same public names (`BLACK, BLUE, RED, GREEN, ORANGE, PURPLE, WHITE, GRAY_50, GRAY_200, GRAY_300, GRAY_500, GRAY_800, YEAR_COLORS, MA_COLORS, EVOLUTION_COLORS, CHART_SEQUENCE, POSITIVE, NEGATIVE, COLORSCALE_*`) plus new grays `GRAY_400`, `GRAY_600`. `BLUE` becomes the muted accent `#0072ab`; a new `BRAND_BLUE = "#00ADEF"` exists for the logo. `YEAR_COLORS[0]` is the accent; the rest are progressively lighter grays.

- [ ] **Step 1: Write the failing test** — `tests/test_colors.py`:

```python
import re
from src.utils import colors

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

def test_accent_is_muted_blue():
    assert colors.BLUE == "#0072ab"
    assert colors.BRAND_BLUE == "#00ADEF"

def test_year_colors_accent_then_grays():
    assert len(colors.YEAR_COLORS) == 5
    assert colors.YEAR_COLORS[0] == colors.BLUE
    for c in colors.YEAR_COLORS:
        assert HEX.match(c)

def test_public_names_present():
    for name in ["MA_COLORS", "EVOLUTION_COLORS", "CHART_SEQUENCE",
                 "POSITIVE", "NEGATIVE", "COLORSCALE_DIVERGING"]:
        assert hasattr(colors, name)
    assert len(colors.MA_COLORS) == 3
    assert len(colors.EVOLUTION_COLORS) == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_colors.py -v`
Expected: FAIL — `AssertionError` on `colors.BLUE` (currently `#00ADEF`).

- [ ] **Step 3: Retune `src/utils/colors.py`** — replace the palette definitions (keep the module docstring and the colorscale section) with:

```python
# === Brand Palette (muted accent scheme) ===
BLACK      = "#000000"
BRAND_BLUE = "#00ADEF"   # logo/brand only
BLUE       = "#0072ab"   # primary accent
RED        = "#c8102e"   # muted semantic negative
GREEN      = "#1a7f42"   # muted semantic positive
ORANGE     = "#b45d0e"   # muted amber
PURPLE     = "#5c6b7f"   # de-emphasized -> slate

# === Neutrals ===
WHITE    = "#FFFFFF"
GRAY_50  = "#fafbfc"
GRAY_200 = "#e5e8ec"
GRAY_300 = "#d3d8de"
GRAY_400 = "#b8c0cb"
GRAY_500 = "#8b97a6"
GRAY_600 = "#5c6b7f"
GRAY_800 = "#1a2332"

# === Chart Color Sequences (accent + grays) ===
YEAR_COLORS      = [BLUE, GRAY_600, GRAY_500, GRAY_400, GRAY_300]
MA_COLORS        = [BLUE, GRAY_500, GRAY_400]
EVOLUTION_COLORS = [BLUE, GRAY_600, GRAY_500, GRAY_400, GRAY_300]
CHART_SEQUENCE   = [BLUE, GRAY_600, GRAY_500, RED, GREEN, GRAY_400]

# === Semantic Aliases ===
POSITIVE = GREEN
NEGATIVE = RED
```

Leave the `# === Plotly Colorscales ===` block (`COLORSCALE_DIVERGING`, `COLORSCALE_SEQUENTIAL`, `COLORSCALE_HEATMAP`, `COLORSCALE_EFFICIENCY`) unchanged.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_colors.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Confirm nothing imports the removed names** — the old module had no other names, but verify importers still resolve:

```bash
python -c "import src.wps.graph_line, src.wps.graph_seag; print('imports ok')"
```
Expected: `imports ok`.

- [ ] **Step 6: Commit**

```bash
git add src/utils/colors.py tests/test_colors.py
git commit -m "style(colors): muted accent+gray chart palette"
```

---

## Task 7: Neutral Plotly chrome helper + apply to graph modules

**Files:**
- Create: `src/utils/plotly_theme.py`
- Modify: `src/wps/graph_line.py`, `src/wps/graph_seag.py`, `src/wps/graph_optionality.py`, `src/steo/chart_dpr.py`
- Test: `tests/test_plotly_theme.py`

**Interfaces:**
- Consumes: `WHITE`, `GRAY_200`, `GRAY_500`, `GRAY_800` from `src/utils/colors.py`.
- Produces: `apply_minimal_chrome(layout: go.Layout) -> go.Layout` — mutates and returns a Plotly `go.Layout`, setting `paper_bgcolor`/`plot_bgcolor` white, Inter font in `--text` slate, and light neutral gridlines/axis lines/spikes on `xaxis`/`yaxis`.

- [ ] **Step 1: Write the failing test** — `tests/test_plotly_theme.py`:

```python
import plotly.graph_objs as go
from src.utils.plotly_theme import apply_minimal_chrome, FONT_FAMILY
from src.utils import colors


def test_chrome_sets_white_bg_and_inter_font():
    layout = go.Layout(xaxis=dict(), yaxis=dict())
    out = apply_minimal_chrome(layout)
    assert out.paper_bgcolor == colors.WHITE
    assert out.plot_bgcolor == colors.WHITE
    assert "Inter" in out.font.family
    assert FONT_FAMILY.startswith("Inter")


def test_chrome_sets_light_gridlines():
    layout = go.Layout(xaxis=dict(), yaxis=dict())
    out = apply_minimal_chrome(layout)
    assert out.xaxis.gridcolor == colors.GRAY_200
    assert out.yaxis.gridcolor == colors.GRAY_200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_plotly_theme.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.utils.plotly_theme'`.

- [ ] **Step 3: Create `src/utils/plotly_theme.py`:**

```python
"""Shared neutral Plotly chrome (white background, Inter font, light grid)."""

from src.utils.colors import WHITE, GRAY_200, GRAY_500, GRAY_800

FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


def apply_minimal_chrome(layout):
    """Merge neutral chrome onto a go.Layout without dropping existing keys."""
    layout.update(
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=dict(family=FONT_FAMILY, color=GRAY_800),
    )
    layout.xaxis.update(gridcolor=GRAY_200, linecolor=GRAY_200, spikecolor=GRAY_500)
    layout.yaxis.update(gridcolor=GRAY_200, linecolor=GRAY_200, spikecolor=GRAY_500)
    return layout
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_plotly_theme.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Apply in `src/wps/graph_line.py`** — add the import at the top:

```python
from src.utils.plotly_theme import apply_minimal_chrome
```

and change the return (currently `return {'data': traces, 'layout': layout}`) to:

```python
    return {'data': traces, 'layout': apply_minimal_chrome(layout)}
```

- [ ] **Step 6: Apply in the other three modules** — in `src/wps/graph_seag.py`, `src/wps/graph_optionality.py`, and `src/steo/chart_dpr.py`: add `from src.utils.plotly_theme import apply_minimal_chrome`, then locate each function's `go.Layout(...)` / figure `layout` and wrap it with `apply_minimal_chrome(...)` before it is returned or attached to the figure. If a module builds a `go.Figure`, call `fig.update_layout(paper_bgcolor=colors.WHITE, ...)` equivalently by wrapping `fig.layout`: `apply_minimal_chrome(fig.layout)`. Do not change series colors here — those come from `colors.py` (Task 6).

- [ ] **Step 7: Verify modules import and a chart builds** — smoke-test graph_line with the app's data:

```bash
python -c "import src.wps.graph_line, src.wps.graph_seag, src.wps.graph_optionality, src.steo.chart_dpr; print('all graph modules import ok')"
```
Expected: `all graph modules import ok`.

- [ ] **Step 8: Visual check** — `python run.py` → load `/stats/graphing` (WPS line + seasonality), `/stats/cushing_analysis`, and `/dpr/dpr_charts` → confirm charts render on white backgrounds with light gridlines, Inter font, and accent+gray series. Stop.

- [ ] **Step 9: Commit**

```bash
git add src/utils/plotly_theme.py src/wps/graph_line.py src/wps/graph_seag.py src/wps/graph_optionality.py src/steo/chart_dpr.py tests/test_plotly_theme.py
git commit -m "style(charts): neutral Plotly chrome via shared theme helper"
```

---

## Task 8: Full-app verification pass

**Files:** none (verification only)

- [ ] **Step 1: Run the whole test suite**

Run: `python -m pytest tests/ -v`
Expected: all tests PASS (navigation, shell, colors, plotly_theme).

- [ ] **Step 2: Confirm no CDN/legacy references linger**

Run:
```bash
grep -rnE "fonts.googleapis|cloudflare|Montserrat|shadow-soft|--color-red" assets/styles.css src/app.py; echo "exit=$?"
```
Expected: no matches (`exit=1`).

- [ ] **Step 3: Manual tour** — `python run.py` → visit `/home` and one page in each of Weekly, DPR, STEO, CLI, PSM:
  - Light sidebar, icons, chevrons, independent collapse, active accent border.
  - Flat white cards, no shadows, Inter font throughout.
  - Charts: white background, light gridlines, accent+gray palette.
  - No browser-console errors or font/icon 404s.

- [ ] **Step 4: Final commit (if any tidy-ups were needed)**

```bash
git add -A
git commit -m "chore: Phase 1 minimalist restyle verification tidy-ups" || echo "nothing to commit"
```

---

## Self-Review (completed by plan author)

- **Spec coverage:** A (tokens/CSS/`.bak`/fonts) → Tasks 1–2; B (app.py stylesheets + local assets) → Task 1; C (navigation.py + shell.py + index.py + single callback) → Tasks 3–5; D (colors.py retune + graph chrome) → Tasks 6–7; verification → Task 8. All spec sections mapped.
- **Placeholder scan:** no TBD/TODO placeholders; the literal "TBD" nav labels are the app's real current link labels, not plan gaps. All code steps include full code; the four-module graph edit (Task 7 Step 6) gives exact import + wrap instructions with the exact helper name.
- **Type consistency:** `build_sidebar(brand, home, nav_sections)` and `compute_collapse_state(nav_sections, is_open_list, triggered_index)` are defined in Task 4 and consumed with the same signatures in Task 5; `apply_minimal_chrome(layout)` defined in Task 7 Step 3 and used consistently in Steps 5–6; `colors.BLUE`/`BRAND_BLUE`/`YEAR_COLORS` names align across Tasks 6–7.
