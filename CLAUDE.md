# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup

`python -m venv`, never `uv venv` (see the section below):

```bash
python -m venv .venv
uv sync --locked --extra apps          # `apps` extra holds dash/plotly/ag-grid
cp .env.example .env
```

### Quality gate

Same steps and same arguments as `.github/workflows/ci.yml`:

```bash
uv lock --check
uv run python -m ruff check src/dash_eia tests
uv run python -m ruff format --check src/dash_eia tests
uv run python -m pyright
uv run python -m pytest -m "not live"
uv build --wheel --no-sources
```

`ruff` and `pyright` only look at `src/dash_eia` (plus `tests/`). `pages/**`,
`src/wps/**`, `src/steo/**`, `src/cli/**`, `src/msg/**`, `src/utils/**`, and
`eia_downloads/**` are all in `extend-exclude` / outside `pyright.include`, so a
green run says nothing about the dashboard or the data modules.

### Running the application

```bash
uv run python -m dash_eia app eia-dashboard          # http://127.0.0.1:8052
uv run python -m dash_eia app eia-dashboard --debug --port 8060
uv run python -m dash_eia bootstrap                 # create canonical data/ + logs/ dirs
python run.py                                       # shim: same launcher, --debug on
```

`--workspace PATH` goes before the subcommand (or set `DASH_EIA_WORKSPACE`);
otherwise the workspace is found by walking up from the CWD for a `pyproject.toml`
whose `project.name` is `dash-eia`. `pyproject.toml` also installs an
`eia-dashboard` console script — a wrapper for `dash_eia app eia-dashboard` — but
like every console script here it is blocked by the ASR rule; use the
`python -m dash_eia` form. `run.bat` activates the venv, opens Chrome, and runs
`run.py`.

### Module-specific data updates

No CLI equivalent — these are legacy modules run directly from the repo root:

```bash
python -m src.wps.download_xlsx     # Weekly petroleum data (WPS)
python -m src.steo.download         # STEO forecast data
python -m src.cli.main              # Company-level import data
python -m src.cli.download          # CLI raw download
python -m src.msg.download_xlsx     # MSG data
```

There is **no `main.py`** in this repo and no single "refresh everything" command:
each module is refreshed on its own, or from the "Generate and Save Data" button
on the WPS headline page.

## Windows: "Access is denied" running tools

On SOCAR-managed Windows machines, Microsoft Defender ASR rule
`01443614-cd74-433a-b99e-2ecdc07bfc25` ("block executable files unless they meet
a prevalence, age, or trusted list criterion") blocks the per-venv `.exe`
console-script shims. Each shim embeds its own venv path, so its hash is unique
to this machine and can never build the cloud reputation the rule wants — this is
permanent, not a cold-start delay. It is not a broken install, and it cannot be
fixed locally: Tamper Protection is on and the policy comes from Intune.

Symptoms:

```text
uv run pytest
error: Failed to spawn: `pytest`
  Caused by: Access is denied. (os error 5)

.venv\Scripts\pytest.exe --version
Permission denied
```

**Fix: go through the interpreter.** `python.exe` is hash-stable across venvs, so
it is allowed. Every tool used here supports `-m`:

| instead of | use |
| --- | --- |
| `uv run pytest` | `uv run python -m pytest` |
| `uv run ruff check .` | `uv run python -m ruff check .` |
| `uv run ruff format .` | `uv run python -m ruff format .` |
| `uv run pyright` | `uv run python -m pyright` |
| `uv run dash-eia ...` | `uv run python -m dash_eia ...` |

`python -m dash_eia` is wired to the same entry point as the `dash-eia`
command, so the two are interchangeable.

**Never create a venv with `uv venv`.** uv writes a trampoline `python.exe`
(~45 KB) that the same rule blocks, which leaves the venv unusable. Create it
with the stdlib and let uv populate it:

```bash
python -m venv .venv
uv sync --locked          # safe: leaves python.exe alone
```

`uv sync` into an existing venv is fine — only uv's *create* step writes the
trampoline. `ruff.exe` happens to be allowed (it is a real, hash-stable binary),
but prefer `-m` everywhere for consistency.

CI is unaffected — GitHub runners carry no such policy — so the workflow files
deliberately keep the plain `uv run <tool>` form.

## Architecture Overview

Multi-module Dash application for energy market analysis using EIA data. Four data
modules (WPS, STEO, CLI, MSG) feed 40 live dashboard pages via a single-page app
with manual URL routing.

### Entry Points

The dashboard is reached through a **compat layer**, not directly. Only
`src/dash_eia/` ships in the wheel; the app itself is workspace-resident.

- **`src/dash_eia/`** (installed package) — `cli.py` (argparse: `bootstrap`, `app`),
  `config/paths.py` (`WorkspacePaths.discover()`), `apps/runner.py`
  (`APP_SPECS = {"eia-dashboard": AppSpec("src.index", 8052)}`),
  `apps/compat.py`, `apps/launchers.py`, `pipelines/bootstrap.py`.
- **`apps/compat.py::working_directory(path)`** — the load-bearing piece. It
  `chdir`s into the workspace *and* inserts the workspace root at `sys.path[0]`,
  restoring both on exit. Both halves are needed: `src.index` is not in the wheel
  (so `sys.path`, which is fixed at startup, must gain the root), and the legacy
  modules load their CSV/feather files relative to the CWD (so `chdir` is also
  required). `run_app` imports the app inside that context, then calls `app.run`
  outside it.
- **`src/index.py`** — imports all page modules (registering their callbacks),
  defines the sidebar, URL routing (`display_page` callback), and sidebar collapse
  callbacks. Exports `app`.
- **`src/app.py`** — Dash app initialization; loads initial WPS pivot data into an
  `initial_data` dict. Exports `app` and `initial_data`.
- **`run.py`** — two-line shim onto `dash_eia.apps.launchers.eia_dashboard(["--debug"])`.

Adding an import of a new workspace-resident module outside a `working_directory`
block passes locally and fails from an installed wheel. CI has a dedicated
"Import the dashboard from a foreign working directory" step that chdirs to the
filesystem root, imports the app through the compat layer, and asserts
`sys.path` was restored — that step is the contract.

**`pages/` lives at the repo root, not under `src/`.** It resolves only because
`.` is on the import path when running from the root (and via `pythonpath` for
pytest); `pages/archived/` holds retired pages that are not imported.

### Data Processing Modules

**WPS (Weekly Petroleum Status)** — `src/wps/`
- Downloads `psw09.xls` from EIA, parses all sheets, pivots by series ID
- `download_xlsx.py` → `generate_additional_tickers.py` → `generate_line_data.py` + `generate_seasonality_data.py`
- `mapping.py` contains the master `production_mapping` dict (EIA series ID → human name)
- `ag_mapping.py` defines AG Grid column configurations
- `table_mapping.py` defines table groupings used by page2_1 headline page

**STEO (Short-Term Energy Outlook)** — `src/steo/`
- Downloads monthly STEO Excel archives, tracks forecast evolution across release dates
- `chart_dpr.py` handles DPR (Drilling Productivity Report) chart generation with melted pivot data
- Metadata/mappings in `lookup/steo/` CSV files

**CLI (Company Level Imports)** — `src/cli/`
- `cli_data_processor.py` contains `CLIDataProcessor` class — loads parquet, categorizes by API gravity (Heavy/Medium/Light) and sulfur content (Sweet/Medium/Sour), converts monthly totals to kbd
- Data stored as zstd-compressed Parquet

**MSG** — `src/msg/`
- Parallel structure to WPS (same download/parse pattern) but for a separate data source
- Has its own `mapping.py`, `generate_line_data.py`, `generate_seasonality_data.py`

### WPS Page Pattern (page2_*.py)

Pages 2_2 through 2_8 (the live ones) follow a shared pattern using `src/wps/calculation.py`:

1. Define `idents` dict at top (EIA series IDs → display names for that commodity)
2. Define `graph_sections_input()` grouping graph IDs into named sections
3. Call `create_layout(page_id, commodity, graph_sections_input)` to generate the layout
4. Callbacks are created by `create_callbacks()` in `calculation.py`, which wires up:
   - Chart toggle (seasonality vs line view)
   - Year range toggles via `src/utils/variables.py` constants
   - Time range buttons (1m, 6m, 12m, 36m, all)
   - Graph rendering via `graph_line.py` (trend charts) and `graph_seag.py` (seasonality charts)

### URL Routing

Routes are defined in `src/index.py:display_page()` as a manual if/elif chain:
- `/home` → page1, `/stats/*` → page2_*, `/dpr/*` → page3_*
- `/steo/*` → page4_*, `/cli/*` → page5_*, `/psm/*` → page6_*

### Data Flow

1. `src/app.py` loads WPS pivot data into `initial_data` → stored in `dcc.Store(id='data-store', storage_type='session')`
2. page2_1 (Headline) has a "Generate and Save Data" button that triggers full WPS download + regeneration
3. Other pages load data directly via `src/utils/data_loader.py` → `simple_loader.py`

### Key Configuration

**`src/utils/variables.py`** — Year constants used across all WPS pages:
- `year_1_string`, `year_2_string`, `year_3_string` — the three comparison years
- `range_selector_normal` / `range_selector_last_five_years` — seasonality range keys
- `type_to_remove` — historical year types to filter out
- These need periodic manual updates as years roll forward

### Data Storage

Live data, read by the app:

- `data/wps/` — Feather files (`.feather`) for fast pandas loading
- `data/steo/` — Feather files for STEO pivot tables
- `data/cli/` — Parquet files (`.parquet`) with zstd compression
- `lookup/` — CSV reference data at the repo root (STEO metadata, WPS mappings,
  `release_dates.csv`)
- `models/`, `eia_downloads/`, `assets/` — mapping workbook, raw downloads, Dash
  static assets (also at the repo root)

`dash-eia bootstrap` creates the blueprint tree (`data/raw`, `data/interim`,
`data/processed`, `data/exports`, `data/state`, `data/cache`, `data/reference`).
Those directories are **empty and unused today** — nothing reads or writes them.
Don't move live data into them expecting the app to follow.

### Adding New Pages

1. Create `pages/pageN_X.py` following the naming convention
2. For WPS-style pages: define `idents` dict + `graph_sections_input()`, use `create_layout`/`create_callbacks`
3. Import in `src/index.py` with a descriptive comment
4. Add URL route in the `display_page()` callback chain
5. Add sidebar navigation entry in the appropriate `dbc.Collapse` section

### Adding New Data Sources

1. Create module in `src/` with download and processing scripts
2. Store processed data in `data/{module}/` as Feather or Parquet
3. Add loader methods to `SimpleDataLoader` in `src/utils/simple_loader.py`
4. Document the `python -m src.<module>.<script>` refresh command in this file —
   there is no `main.py` to register it with

## Gotchas

- **The test suite is 15 tests and proves almost nothing about the dashboard.**
  `tests/test_framework.py` (9) covers workspace discovery, `bootstrap`,
  credential-free `--help`, the app registry, the compat layer's `sys.path`
  handling, and the two import-time credential guards below;
  `tests/test_entrypoints.py` (3) asserts `run.py` imports without running, in a
  subprocess with a scrubbed environment, plus two tests on the scrubber;
  `tests/test_guard_contract.py` (3) pins the boundary guard, one of them `live`
  and one **skipped** because `boto3` is not installed. There is **zero**
  coverage of `pages/**`, WPS/STEO/CLI/MSG parsing, or any chart. A green CI run
  means the package shell, the compat layer, and the credential boundary are
  intact — nothing more. Verify dashboard changes by actually loading the page.
- **`load_dotenv()` must never run at import.** `test_framework.py`'s two AST
  guards parse every module under **both** importable trees — `src/` and
  `eia_downloads/`, since `pythonpath` is `["src", "."]` — and fail on an
  import-time `load_dotenv()` or a credential-shaped `os.environ[...]`. Import
  time is pytest *collection* time, before any fixture exists, so a module-scope
  credential read cannot be undone. `steo/meta.py` had exactly this in both
  trees, nested inside a `try:` where a top-level-statements-only scan could not
  see it; it now loads `.env` in `_load_dotenv()`, called from `download_api()`.
  Add new secrets the same way: read them in the function that needs them.
- **This repo has no AWS surface, and the tests say so honestly.** `boto3` is
  not a dependency, not in `uv.lock`, not installed, and appears nowhere in
  `src/`, `eia_downloads/`, `pages/` or `run.py`. The sibling repos' subprocess
  assertion that importing an entrypoint leaves `boto3.DEFAULT_SESSION is None`
  is **deliberately not present here** — see the module docstring of
  `tests/test_entrypoints.py`. Do not add it as an `importorskip`; that yields a
  test that always skips. Add it for real if AWS ever arrives.
- **Year constants are a manual annual chore.** `src/utils/variables.py`
  (`year_1_string`, `year_2_string`, `year_3_string`, `range_selector_*`,
  `type_to_remove`) is hardcoded and read by every WPS page; nothing warns when it
  goes stale.
- **CWD is part of the contract.** The legacy modules resolve `data/`, `lookup/`,
  and `models/` relative to the process working directory, which is why the compat
  layer chdirs. Run from the repo root, or go through the CLI so it does it for you.
- **8 of the 48 page modules are dead.** `pages/` holds 48 `pageN_X.py` files but
  `src/index.py` imports only 40. Not wired in: `page2_9`, `page2_10`–`page2_15`,
  `page3_3`. They are unreachable and untested — check `src/index.py` before
  assuming a page is live.
- **All 40 live pages are imported eagerly** at `src/index.py` module scope, so an
  import-time error in any one of them takes down the whole app, and startup pays
  for all of them.
