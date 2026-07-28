# Entrypoints

| Operation | Command |
| --- | --- |
| Create canonical directories | `dash-eia bootstrap` |
| Run the dashboard | `dash-eia app eia-dashboard` |
| Run the dashboard directly | `eia-dashboard` |

The temporary `python run.py` command delegates to the installed app launcher.
Its historical port remains 8052. The app itself still uses the characterized
legacy module until pages and assets move under
`dash_eia.apps.eia_dashboard`.
