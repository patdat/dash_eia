from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from app import app  # Ensure this import points to where your Dash app is initialized
from app import initial_data

# Preload cache for faster performance
from src.utils.data_loader import preload_common_data
import os

# Preload cache only in production or when explicitly enabled
if os.getenv("PRELOAD_CACHE", "true").lower() == "true":
    try:
        preload_common_data()
        print("Cache preloaded successfully!")
    except Exception as e:
        print(f"Cache preloading failed: {e}")

import pages.page1      # Home
import pages.page2_1    # Headline
import pages.page2_2    # Crude
import pages.page2_3    # Gasoline
import pages.page2_4    # Distillate
import pages.page2_5    # Jet
import pages.page2_6    # Fuel Oil
import pages.page2_7    # C3/C3=
import pages.page2_8    # Products Supplied
import pages.page2_9    # Refining
import pages.page2_10   # AgGrid
import pages.page2_11   # PADD Regional Stock Analysis
import pages.page2_12   # Cushing Hub Analysis
import pages.page2_13   # Refinery Utilization & Crack Spreads
import pages.page2_14   # Supply/Demand Balance & Trade
import pages.page2_15   # Advanced Time Series & Anomaly Detection
import pages.page3_1    # regional_charts
import pages.page3_2    # bakken
import pages.page3_3    # eagleford
import pages.page3_4    # haynesville
import pages.page3_5    # permian
import pages.page3_6    # other
import pages.page3_7    # Regional Efficiency Heatmap
import pages.page3_8    # DUC Inventory Waterfall Analysis
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

# Layout with fixed-width sidebar
sidebar = html.Div(
    [ 
        # Add a blank div to give the sidebar some height space
        html.Div(style={'height': '25px'}),

        html.Div([
            html.Div([
                html.A(
                    html.Img(
                        src="/assets/best.jpg",  # Ensure this path is correct
                        style={
                            'height': 'auto',  # Adjust height to maintain aspect ratio
                            'width': '50px',   # Adjust width to fit your design
                            'object-fit': 'contain',  # Preserve the aspect ratio
                            'display': 'block',  # Makes the image a block to take full width of the line
                            'margin-bottom': '0px',
                            'margin-left': '5px'
                        }
                    ),
                    href="https://www.google.com"  # Makes the image clickable
                ),
                html.A("PCIA", href="https://www.google.com", style={
                    'text-decoration': 'none',
                    'color': 'black',
                    'font-size': '40px',
                    'font-family': "'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                    'margin-left': '10px',  # Adds minimal space between the image and text
                    'align-self': 'center',  # Aligns the text vertically center with the image
                }),
            ], style={
                'flex': '1',
                'display': 'flex',
                'justify-content': 'flex-start',  # Aligns the image and text to the left
                'align-items': 'center',  # Aligns the image and text vertically center
            }),
        ], style={'display': 'flex', 'border-bottom': '0px solid white', 'border-top': '0px solid white','margin-left':'12px'}),

        # Add a blank div to give the sidebar some height space
        html.Div(style={'height': '25px'}),

        dbc.Nav(
            [
                # Home
                dbc.NavLink("Home", href="/home", active="exact", className="nav-link"),
                
                # EIA Weekly
                dbc.NavItem([
                    dbc.Button("EIA Weekly", id="toggle-page-2", className="sidebar-button page-button closed", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavLink("Headline", href="/stats/headline", active='exact', className="nav-link"),                                
                                dbc.NavLink("Crude", href="/stats/crude", active='exact', className="nav-link"),
                                dbc.NavLink("Gasoline", href="/stats/gasoline", active='exact', className="nav-link"),
                                dbc.NavLink("Distillate", href="/stats/distillate", active='exact', className="nav-link"),
                                dbc.NavLink("Jet", href="/stats/jet", active='exact', className="nav-link"),
                                dbc.NavLink("Fuel Oil", href="/stats/fuel_oil", active='exact', className="nav-link"),
                                dbc.NavLink("C3/C3=", href="/stats/propane_propylene", active='exact', className="nav-link"),
                                dbc.NavLink("Products Supplied", href="/stats/products_supplied", active='exact', className="nav-link"),
                                dbc.NavLink("Refining", href="/stats/refining", active='exact', className="nav-link"),
                                dbc.NavLink("Stats Table", href="/stats/stats_table", active='exact', className="nav-link"),
                                dbc.NavLink("PADD Regional Analysis", href="/stats/padd_regional", active='exact', className="nav-link"),
                                dbc.NavLink("Cushing Hub Analysis", href="/stats/cushing_analysis", active='exact', className="nav-link"),
                                dbc.NavLink("Refinery Analytics", href="/stats/refinery_analytics", active='exact', className="nav-link"),
                                dbc.NavLink("Supply/Demand Balance", href="/stats/supply_demand", active='exact', className="nav-link"),
                                dbc.NavLink("Advanced Time Series", href="/stats/time_series_analytics", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-2",
                        is_open=True,
                    ),
                ]),  
                
                # EIA DPR
                dbc.NavItem([
                    dbc.Button("EIA DPR", id="toggle-page-3", className="sidebar-button page-button closed", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavLink("DPR Charts", href="/dpr/dpr_charts", active='exact', className="nav-link"),  
                                dbc.NavLink("DPR Table", href="/dpr/dpr_table", active='exact', className="nav-link"),
                                dbc.NavLink("DPR Other Table", href="/dpr/dpr_other_table", active='exact', className="nav-link"),
                                dbc.NavLink("Regional Efficiency Heatmap", href="/dpr/efficiency_heatmap", active='exact', className="nav-link"),
                                dbc.NavLink("DUC Inventory Waterfall", href="/dpr/duc_waterfall", active='exact', className="nav-link"),
                                dbc.NavLink("Productivity Matrix Analysis", href="/dpr/productivity_matrix", active='exact', className="nav-link"),
                                dbc.NavLink("Performance Radar Analysis", href="/dpr/performance_radar", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-3",
                        is_open=True,
                    ),
                ]),
                
                # EIA STEO
                dbc.NavItem([
                    dbc.Button("EIA STEO", id="toggle-page-4", className="sidebar-button page-button closed", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavLink("TBD", href="/steo/tbd1", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/steo/tbd2", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/steo/tbd3", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/steo/tbd4", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/steo/tbd5", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/steo/tbd6", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-4",
                        is_open=True,
                    ),
                ]),
                
                # EIA CLI
                dbc.NavItem([
                    dbc.Button("EIA CLI", id="toggle-page-5", className="sidebar-button page-button closed", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavLink("Market Overview", href="/cli/market_overview", active='exact', className="nav-link"),
                                dbc.NavLink("Company Analysis", href="/cli/company_analysis", active='exact', className="nav-link"),
                                dbc.NavLink("Quality Analysis", href="/cli/quality_analysis", active='exact', className="nav-link"),
                                dbc.NavLink("Regional/PADD", href="/cli/regional_padd", active='exact', className="nav-link"),
                                dbc.NavLink("Country Risk", href="/cli/country_risk", active='exact', className="nav-link"),
                                dbc.NavLink("Seasonal Patterns", href="/cli/seasonal_patterns", active='exact', className="nav-link"),
                                dbc.NavLink("Time Series Forecasting", href="/cli/forecasting", active='exact', className="nav-link"),
                                dbc.NavLink("Port Analysis", href="/cli/port_analysis", active='exact', className="nav-link"),
                                dbc.NavLink("Trade Flow Analysis", href="/cli/trade_flow", active='exact', className="nav-link"),
                                dbc.NavLink("Market Alerts", href="/cli/market_alerts", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-5",
                        is_open=True,
                    ),
                ]),
                
                # EIA PSM
                dbc.NavItem([
                    dbc.Button("EIA PSM", id="toggle-page-6", className="sidebar-button page-button closed", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavLink("TBD", href="/psm/tbd1", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/psm/tbd2", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/psm/tbd3", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/psm/tbd4", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/psm/tbd5", active='exact', className="nav-link"),
                                dbc.NavLink("TBD", href="/psm/tbd6", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-6",
                        is_open=True,
                    ),
                ]),                                                   
                                                                 
            ],
            vertical=True,
            pills=True,
            className="flex-grow-1"
        ),
    ],
    className="sidebar d-flex flex-column vh-100"
)

content = html.Div(id="page-content", className="content-area")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    sidebar,
    content,
    dcc.Store(id='data-store', data=initial_data, storage_type='session'),    
])

@app.callback(
    Output("collapse-page-2", "is_open"),
    Output("toggle-page-2", "className"),
    [Input("toggle-page-2", "n_clicks")],
    [State("collapse-page-2", "is_open"), State("toggle-page-2", "className")]
)
def toggle_collapse_page_2(n, is_open, current_class):
    if n:
        is_open = not is_open
        if is_open:
            new_class = current_class.replace("closed", "open") if "closed" in current_class else current_class
        else:
            new_class = current_class.replace("open", "closed") if "open" in current_class else current_class
        return is_open, new_class
    return is_open, current_class

@app.callback(
    Output("collapse-page-3", "is_open"),
    Output("toggle-page-3", "className"),
    [Input("toggle-page-3", "n_clicks")],
    [State("collapse-page-3", "is_open"), State("toggle-page-3", "className")]
)
def toggle_collapse_page_3(n, is_open, current_class):
    if n:
        is_open = not is_open
        if is_open:
            new_class = current_class.replace("closed", "open") if "closed" in current_class else current_class
        else:
            new_class = current_class.replace("open", "closed") if "open" in current_class else current_class
        return is_open, new_class
    return is_open, current_class

@app.callback(
    Output("collapse-page-4", "is_open"),
    Output("toggle-page-4", "className"),
    [Input("toggle-page-4", "n_clicks")],
    [State("collapse-page-4", "is_open"), State("toggle-page-4", "className")]
)
def toggle_collapse_page_4(n, is_open, current_class):
    if n:
        is_open = not is_open
        if is_open:
            new_class = current_class.replace("closed", "open") if "closed" in current_class else current_class
        else:
            new_class = current_class.replace("open", "closed") if "open" in current_class else current_class
        return is_open, new_class
    return is_open, current_class

@app.callback(
    Output("collapse-page-5", "is_open"),
    Output("toggle-page-5", "className"),
    [Input("toggle-page-5", "n_clicks")],
    [State("collapse-page-5", "is_open"), State("toggle-page-5", "className")]
)
def toggle_collapse_page_5(n, is_open, current_class):
    if n:
        is_open = not is_open
        if is_open:
            new_class = current_class.replace("closed", "open") if "closed" in current_class else current_class
        else:
            new_class = current_class.replace("open", "closed") if "open" in current_class else current_class
        return is_open, new_class
    return is_open, current_class

@app.callback(
    Output("collapse-page-6", "is_open"),
    Output("toggle-page-6", "className"),
    [Input("toggle-page-6", "n_clicks")],
    [State("collapse-page-6", "is_open"), State("toggle-page-6", "className")]
)
def toggle_collapse_page_6(n, is_open, current_class):
    if n:
        is_open = not is_open
        if is_open:
            new_class = current_class.replace("closed", "open") if "closed" in current_class else current_class
        else:
            new_class = current_class.replace("open", "closed") if "open" in current_class else current_class
        return is_open, new_class
    return is_open, current_class


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
    elif pathname == '/stats/crude':
        return pages.page2_2.layout
    elif pathname == '/stats/gasoline':
        return pages.page2_3.layout
    elif pathname == '/stats/distillate':
        return pages.page2_4.layout
    elif pathname == '/stats/jet':
        return pages.page2_5.layout
    elif pathname == '/stats/fuel_oil':
        return pages.page2_6.layout
    elif pathname == '/stats/propane_propylene':
        return pages.page2_7.layout
    elif pathname == '/stats/products_supplied':
        return pages.page2_8.layout
    elif pathname == '/stats/refining':
        return pages.page2_9.layout
    elif pathname == '/stats/stats_table':
        return pages.page2_10.layout
    elif pathname == '/stats/padd_regional':
        return pages.page2_11.layout
    elif pathname == '/stats/cushing_analysis':
        return pages.page2_12.layout
    elif pathname == '/stats/refinery_analytics':
        return pages.page2_13.layout
    elif pathname == '/stats/supply_demand':
        return pages.page2_14.layout
    elif pathname == '/stats/time_series_analytics':
        return pages.page2_15.layout
    elif pathname == '/dpr/dpr_charts':
        return pages.page3_1.layout
    elif pathname == '/dpr/dpr_table':
        return pages.page3_2.layout
    elif pathname == '/dpr/dpr_other_table':
        return pages.page3_3.layout
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
if __name__ == '__main__':
    app.run(debug=False)
