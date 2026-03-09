BRAND = {
    "name": "Socar",
    "href": "https://www.google.com",
    "logo_src": "/assets/company_logo.png",
}


NAV_SECTIONS = [
    {
        "id": "market",
        "label": "Market Intelligence",
        "initial_open": True,
        "links": [
            {"label": "Overview", "href": "/market/overview"},
            {"label": "Signals", "href": "/market/signals"},
            {"label": "Alert Center", "href": "/market/alerts"},
        ],
    },
    {
        "id": "operations",
        "label": "Operations",
        "initial_open": True,
        "links": [
            {"label": "Supply Chain", "href": "/operations/supply-chain"},
            {"label": "Assets", "href": "/operations/assets"},
            {"label": "Performance", "href": "/operations/performance"},
        ],
    },
    {
        "id": "research",
        "label": "Research",
        "initial_open": False,
        "links": [
            {"label": "Scenario Lab", "href": "/research/scenario-lab"},
            {"label": "Comparisons", "href": "/research/comparisons"},
        ],
    },
]


PAGE_CONTENT = {
    "/": {
        "title": "Executive Home",
        "eyebrow": "Reusable Shell",
        "summary": "A layout-first Dash starter extracted from the original app.",
        "highlights": [],
    },
    "/market/overview": {
        "title": "Market Overview",
        "eyebrow": "Market Intelligence",
        "summary": "Use this page template for a chart grid, KPI row, or narrative dashboard.",
        "highlights": [
            "Top summary band",
            "Content cards with clean spacing",
            "Consistent page title treatment",
        ],
    },
    "/market/signals": {
        "title": "Signals",
        "eyebrow": "Market Intelligence",
        "summary": "A placeholder for time-sensitive metrics, signal badges, or anomaly summaries.",
        "highlights": [
            "Signal tables",
            "Threshold alerts",
            "Short-form narrative blocks",
        ],
    },
    "/market/alerts": {
        "title": "Alert Center",
        "eyebrow": "Market Intelligence",
        "summary": "A placeholder for operational alerts, watchlists, and escalation status.",
        "highlights": [
            "Priority queue",
            "Owner assignments",
            "Status chips",
        ],
    },
    "/operations/supply-chain": {
        "title": "Supply Chain",
        "eyebrow": "Operations",
        "summary": "Use this page for flows, logistics status, and bottleneck tracking.",
        "highlights": [
            "Map modules",
            "Transit status",
            "Dependency summaries",
        ],
    },
    "/operations/assets": {
        "title": "Assets",
        "eyebrow": "Operations",
        "summary": "A shell for inventory, maintenance, or portfolio health views.",
        "highlights": [
            "Card grids",
            "Owner breakdowns",
            "Health trends",
        ],
    },
    "/operations/performance": {
        "title": "Performance",
        "eyebrow": "Operations",
        "summary": "Use this page for scorecards, benchmarking, or throughput views.",
        "highlights": [
            "Scorecards",
            "Benchmark rows",
            "Variance commentary",
        ],
    },
    "/research/scenario-lab": {
        "title": "Scenario Lab",
        "eyebrow": "Research",
        "summary": "A sandbox page for assumptions, what-if logic, and scenario cards.",
        "highlights": [
            "Scenario panels",
            "Sensitivity cards",
            "Decision notes",
        ],
    },
    "/research/comparisons": {
        "title": "Comparisons",
        "eyebrow": "Research",
        "summary": "Use this page for competitor, region, or option comparison modules.",
        "highlights": [
            "Matrix layouts",
            "Comparison cards",
            "Compact notes",
        ],
    },
}
