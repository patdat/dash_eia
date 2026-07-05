from dash import Dash, dcc, html, Input, Output, State
from dash import ALL, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from src.app import app
from src.app import initial_data
from src.config.navigation import BRAND, HOME, NAV_SECTIONS
from src.components.shell import build_sidebar, compute_collapse_state

import pages.page1      # Home
import pages.page2_1    # Headline
import pages.page2_2    # Graphing (Combined WPS)
import pages.page2_3    # Stats Table
import pages.page2_4    # PADD Regional Stock Analysis
import pages.page2_5    # Cushing
import pages.page2_6    # Refinery Utilization & Crack Spreads
import pages.page2_7    # Supply/Demand Balance & Trade
import pages.page2_8    # Advanced Time Series & Anomaly Detection
import pages.page3_1    # regional_charts
import pages.page3_2    # bakken
import pages.page3_4    # haynesville
import pages.page3_5    # permian
import pages.page3_6    # other
import pages.page3_7    # Efficiency Heatmap
import pages.page3_8    # DUC Analysis
import pages.page3_9    # Drilling Productivity Matrix Analysis
import pages.page3_10   # Regional Performance Radar Analysis
import pages.page4_1    # EIA STEO - TBD
import pages.page4_2    # EIA STEO - TBD
import pages.page4_3    # EIA STEO - TBD
import pages.page4_4    # EIA STEO - TBD
import pages.page4_5    # EIA STEO - TBD
import pages.page4_6    # EIA STEO - TBD
import pages.page5_1    # EIA CLI - Market Overview
import pages.page5_2    # EIA CLI - Company Analysis
import pages.page5_3    # EIA CLI - Quality Analysis
import pages.page5_4    # EIA CLI - Regional/PADD
import pages.page5_5    # EIA CLI - Country Risk
import pages.page5_6    # EIA CLI - Seasonal Patterns
import pages.page5_7    # EIA CLI - Time Series Forecasting
import pages.page5_8    # EIA CLI - Port Analysis
import pages.page5_9    # EIA CLI - Trade Flow Analysis
import pages.page5_10   # EIA CLI - Market Alerts Dashboard
import pages.page6_1    # EIA PSM - TBD
import pages.page6_2    # EIA PSM - TBD
import pages.page6_3    # EIA PSM - TBD
import pages.page6_4    # EIA PSM - TBD
import pages.page6_5    # EIA PSM - TBD
import pages.page6_6    # EIA PSM - TBD

sidebar = build_sidebar(BRAND, HOME, NAV_SECTIONS)

content = html.Div(id="page-content", className="content-area")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    sidebar,
    content,
    dcc.Store(id='data-store', data=initial_data, storage_type='session'),
])

@app.callback(
    Output({"type": "nav-collapse", "index": ALL}, "is_open"),
    Output({"type": "nav-toggle", "index": ALL}, "className"),
    Input({"type": "nav-toggle", "index": ALL}, "n_clicks"),
    State({"type": "nav-collapse", "index": ALL}, "is_open"),
    prevent_initial_call=True,
)
def toggle_nav_section(n_clicks_list, is_open_list):
    triggered = ctx.triggered_id
    if not triggered:
        raise PreventUpdate
    return compute_collapse_state(NAV_SECTIONS, is_open_list, triggered["index"])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    # Default to home page if root path or None
    if pathname == '/' or pathname is None:
        return pages.page1.layout
    elif pathname == '/home':
        return pages.page1.layout
    # EIA Weekly
    elif pathname == '/stats/headline':
        return pages.page2_1.layout
    elif pathname == '/stats/graphing':
        return pages.page2_2.layout
    elif pathname == '/stats/stats_table':
        return pages.page2_3.layout
    elif pathname == '/stats/padd_regional':
        return pages.page2_4.layout
    elif pathname == '/stats/cushing_analysis':
        return pages.page2_5.layout
    elif pathname == '/stats/runs_analysis':
        return pages.page2_6.layout
    elif pathname == '/stats/supply_demand':
        return pages.page2_7.layout
    elif pathname == '/stats/time_series_analytics':
        return pages.page2_8.layout
    elif pathname == '/dpr/dpr_charts':
        return pages.page3_1.layout
    elif pathname == '/dpr/dpr_table':
        return pages.page3_2.layout
    elif pathname == '/dpr/efficiency_heatmap':
        return pages.page3_7.layout
    elif pathname == '/dpr/duc_waterfall':
        return pages.page3_8.layout
    elif pathname == '/dpr/productivity_matrix':
        return pages.page3_9.layout
    elif pathname == '/dpr/performance_radar':
        return pages.page3_10.layout
    # EIA STEO
    elif pathname == '/steo/tbd1':
        return pages.page4_1.layout
    elif pathname == '/steo/tbd2':
        return pages.page4_2.layout
    elif pathname == '/steo/tbd3':
        return pages.page4_3.layout
    elif pathname == '/steo/tbd4':
        return pages.page4_4.layout
    elif pathname == '/steo/tbd5':
        return pages.page4_5.layout
    elif pathname == '/steo/tbd6':
        return pages.page4_6.layout
    # EIA CLI
    elif pathname == '/cli/market_overview':
        return pages.page5_1.layout
    elif pathname == '/cli/company_analysis':
        return pages.page5_2.layout() if callable(pages.page5_2.layout) else pages.page5_2.layout
    elif pathname == '/cli/quality_analysis':
        return pages.page5_3.layout
    elif pathname == '/cli/regional_padd':
        return pages.page5_4.layout
    elif pathname == '/cli/country_risk':
        return pages.page5_5.layout
    elif pathname == '/cli/seasonal_patterns':
        return pages.page5_6.layout
    elif pathname == '/cli/forecasting':
        return pages.page5_7.layout
    elif pathname == '/cli/port_analysis':
        return pages.page5_8.layout
    elif pathname == '/cli/trade_flow':
        return pages.page5_9.layout
    elif pathname == '/cli/market_alerts':
        return pages.page5_10.layout
    # EIA PSM
    elif pathname == '/psm/tbd1':
        return pages.page6_1.layout
    elif pathname == '/psm/tbd2':
        return pages.page6_2.layout
    elif pathname == '/psm/tbd3':
        return pages.page6_3.layout
    elif pathname == '/psm/tbd4':
        return pages.page6_4.layout
    elif pathname == '/psm/tbd5':
        return pages.page6_5.layout
    elif pathname == '/psm/tbd6':
        return pages.page6_6.layout

    else:
        # Default to home page for any unrecognized path
        return pages.page1.layout
