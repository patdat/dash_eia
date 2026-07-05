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
