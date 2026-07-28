# Standardization Plan

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
