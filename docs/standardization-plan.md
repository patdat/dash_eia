# Standardization Plan

## Blueprint decision (authoritative)

`dash_eia` should become an installable dashboard product with all app code and
assets under `src/dash_eia/apps/`. `eia_api` should own reusable EIA acquisition
and publication. Duplicate downloader trees, root pages, numbered filenames,
and tracked generated dashboard data are migration debt.

```text
dash_eia/
|-- data/
|   |-- README.md
|   |-- reference/                 # tracked
|   |   |-- release_calendars/
|   |   |-- mappings/{wps,steo,cli}/
|   |   `-- vendor/
|   |-- raw/
|   |-- interim/
|   |-- processed/
|   |-- exports/
|   |-- state/
|   `-- cache/
|-- docs/{adr,operations}/
|-- notebooks/
|-- scripts/
|-- scratch/
|-- src/dash_eia/
|   |-- cli.py
|   |-- config/{paths,settings,runtime,logging}.py
|   |-- ingestion/                 # artifact clients; no duplicate EIA SDK
|   |-- modeling/                  # dashboard-specific view transforms
|   |-- pipelines/{bootstrap,refresh_views}.py
|   |-- storage/{artifacts,hydration}.py
|   `-- apps/
|       |-- runner.py
|       |-- launchers.py
|       |-- shared/{assets,components,theme}/
|       `-- eia_dashboard/
|           |-- app.py
|           |-- index.py
|           |-- config/{navigation,settings}.py
|           |-- engine/{loader,compute,types}.py
|           |-- components/
|           |-- pages/
|           |   |-- weekly_petroleum_status/
|           |   |-- short_term_energy_outlook/
|           |   |-- drilling_productivity/
|           |   `-- company_level_imports/
|           |       `-- {page,callbacks,ids}.py
|           |-- selectors/
|           `-- state/
`-- tests/
```

### Reference-data and artifact migration

- Move root `lookup/` and the selected canonical lookup copy to
  `data/reference/mappings/`; move release dates to
  `data/reference/release_calendars/`.
- Move the mapping workbook under `data/reference/vendor/` or
  `data/reference/mappings/` according to ownership.
- Current tracked XLS/Feather/Parquet dashboard outputs under `data/wps`,
  `data/steo`, and `data/cli` become generated `raw`/`processed` artifacts and
  leave Git after hydration/publication is available.
- `.gitignore` enumerates generated data subtrees but leaves
  `data/reference/**` tracked.

### Installed command surface

```toml
[project.scripts]
dash-eia = "dash_eia.cli:main"
eia-dashboard = "dash_eia.apps.launchers:eia_dashboard"
```

Canonical commands are `dash-eia bootstrap`, `dash-eia refresh-views`, and
`dash-eia app eia-dashboard`; the direct `eia-dashboard` command launches the
browser. `run.py` becomes a time-limited delegate and is then removed.

### Page and package naming

- Replace `page2_10.py`-style names with business-purpose packages.
- Each page package uses `page.py`, with `callbacks.py`, `ids.py`, `state.py`,
  or `charts.py` only when needed.
- Archived pages are not importable runtime modules. Preserve useful history
  in Git history or documentation, not `pages/archived`.
- Assets are wheel package data under `apps/shared/assets`, verified by a wheel
  smoke test.
- Loaders resolve paths through the runtime context and load lazily; importing
  the app cannot read Feather/Parquet or require an API key.

### Completion contract

Completion requires one canonical ingestion dependency, no root `pages`,
`assets`, `lookup`, `models`, or `eia_downloads` runtime trees, meaningful page
names, installed command/app smokes, and contract tests proving dashboard view
schemas match the selected EIA artifacts.

## Target

Make `dash_eia` a named, tested EIA dashboard consumer with one ingestion
contract. It must not remain a second, divergent EIA ingestion product.

## Delivery phases

1. **Freeze and discover.** Compare `src/{wps,steo,cli}` with
   `eia_downloads/{wps,steo,cli}` output-by-output; inventory active pages,
   routes, assets, and archives. Establish fixture parity before deletion.
2. **Choose ownership.** Use `eia_api` as the canonical ingestion producer;
   consume its stable published artifacts/contracts. Retain only dashboard
   specific transforms in this repository.
3. **Package and consolidate.** Create `src/dash_eia/`, PEP 621/uv metadata,
   lock/Python pin, settings/workspace paths, and profiles for apps/EIA/
   notebooks. Migrate the selected pipeline modules, one lookup source, and
   compatibility reads during transition.
4. **Rebuild app boundary.** Move pages into `apps/dashboard/{wps,dpr,steo,
   cli}`, add a declarative route registry/shared theme, lazy schema-checked
   loaders, and isolate archived pages. Replace `run.py` with a compatibility
   delegate to `dash-eia bootstrap|pipeline MODULE|app`.
5. **Quality and docs.** Add fixture transform/schema/route tests, dashboard
   smoke, live EIA marker, CI/tooling and architecture/operations/ADR docs.

## Risk controls

The duplicate trees and 50+ manually routed pages are the first risk. No code
is removed until parity and active-route evidence are captured.
