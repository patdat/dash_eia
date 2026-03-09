# Export Project Codex

This folder is a portable Dash shell extracted from the current app's layout patterns.

It includes:

- fixed left sidebar
- collapsible navigation groups
- shared brand/color tokens
- reusable stat and feature cards
- sample routed pages
- copied logo asset

## Structure

```text
export_project_codex/
├── app.py
├── index.py
├── requirements.txt
├── assets/
│   ├── company_logo.png
│   ├── font-loader.js
│   └── styles.css
├── components/
│   ├── __init__.py
│   ├── cards.py
│   └── shell.py
├── config/
│   ├── __init__.py
│   └── navigation.py
├── pages/
│   ├── __init__.py
│   ├── home.py
│   └── placeholder.py
└── utils/
    ├── __init__.py
    └── colors.py
```

## Run

```bash
pip install -r requirements.txt
python index.py
```

## Customize

1. Edit `config/navigation.py` to change the brand name, links, and sidebar groups.
2. Replace `assets/company_logo.png` with your own logo.
3. Adjust theme tokens in `utils/colors.py` and `assets/styles.css`.
4. Replace placeholder page content with your real pages.

## Notes

- This export is intentionally data-free. It preserves the visual shell without carrying over EIA-specific loaders, datasets, or page logic.
- The sidebar collapse behavior uses one pattern-matching callback, so adding groups only requires updating config.
