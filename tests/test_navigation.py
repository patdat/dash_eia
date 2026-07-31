from src.config.navigation import BRAND, HOME, NAV_SECTIONS

# The exact set of hrefs the routing callback in src/index.py serves today.
KNOWN_ROUTES = {
    "/home",
    "/stats/headline",
    "/stats/graphing",
    "/stats/stats_table",
    "/stats/padd_regional",
    "/stats/cushing_analysis",
    "/stats/runs_analysis",
    "/stats/supply_demand",
    "/stats/time_series_analytics",
    "/dpr/dpr_charts",
    "/dpr/dpr_table",
    "/dpr/efficiency_heatmap",
    "/dpr/duc_waterfall",
    "/dpr/productivity_matrix",
    "/dpr/performance_radar",
    "/steo/tbd1",
    "/steo/tbd2",
    "/steo/tbd3",
    "/steo/tbd4",
    "/steo/tbd5",
    "/steo/tbd6",
    "/cli/market_overview",
    "/cli/company_analysis",
    "/cli/quality_analysis",
    "/cli/regional_padd",
    "/cli/country_risk",
    "/cli/seasonal_patterns",
    "/cli/forecasting",
    "/cli/port_analysis",
    "/cli/trade_flow",
    "/cli/market_alerts",
    "/psm/tbd1",
    "/psm/tbd2",
    "/psm/tbd3",
    "/psm/tbd4",
    "/psm/tbd5",
    "/psm/tbd6",
}


def test_brand_and_home_shape():
    assert set(BRAND) >= {"name", "href", "logo_src"}
    assert set(HOME) >= {"label", "href", "icon"}
    assert HOME["href"] == "/home"


def test_sections_shape():
    ids = [s["id"] for s in NAV_SECTIONS]
    assert ids == ["weekly", "dpr", "steo", "cli", "psm"]
    for s in NAV_SECTIONS:
        assert set(s) >= {"id", "label", "icon", "initial_open", "links"}
        assert s["links"], f"{s['id']} has no links"
        for link in s["links"]:
            assert set(link) >= {"label", "href"}


def test_every_nav_href_is_a_known_route():
    hrefs = {HOME["href"]}
    for s in NAV_SECTIONS:
        hrefs.update(link["href"] for link in s["links"])
    assert hrefs == KNOWN_ROUTES
