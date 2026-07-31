# Development

```powershell
uv sync --locked --extra apps
uv lock --check
uv run --locked ruff check src/dash_eia tests
uv run --locked ruff format --check src/dash_eia tests
uv run --locked pyright
uv run --locked pytest -m "not live"
uv build --wheel --no-sources
```

Legacy modules are outside the strict formatting gate until their behavior is
characterized. New modules and migrated pages must use business names rather
than numeric filenames.
