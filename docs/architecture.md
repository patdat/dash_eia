# Architecture

Dash EIA is becoming an installable dashboard consumer. New code lives under
`src/dash_eia`; `src` is never an import namespace in the final architecture.
The app registry owns app names and ports, while `eia-dashboard` is a short
launcher for `dash-eia app eia-dashboard`.

The existing `src`, `pages`, `assets`, `lookup`, `models`, and
`eia_downloads` trees remain compatibility surfaces until import, route, and
artifact parity tests identify the canonical implementation. EIA API is the
intended reusable ingestion producer; this repository owns dashboard-specific
view transformations and presentation.
