# Data Lifecycle

Only `reference/` is tracked in the target layout. Provider downloads and
dashboard views belong in generated `raw`, `interim`, and `processed`
directories; exports, state, and cache are also generated.

The repository currently tracks legacy outputs under `data/wps`, `data/steo`,
and `data/cli`. They remain temporarily while duplicate ingestion trees and
artifact parity are characterized. They must leave Git only after the
canonical EIA producer and hydration contract are operational.
