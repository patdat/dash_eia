from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from app import app  # Ensure this import points to where your Dash app is initialized

import pages.page1

import pages.page2_1 #stocks
import pages.page2_2 #runs
import pages.page2_4 #movements
import pages.page2_5 #production
import pages.page2_6 #other
import pages.page2_7 #p9






# Layout with fixed-width sidebar
sidebar = html.Div(
    [ 
                        
        #add a blank div to give the sidebar some height space
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
                            'margin-bottom': '0px'
                        }
                    ),
                    href="https://www.google.com"  # Makes the image clickable
                ),
                html.A("PCIA", href="https://www.google.com", style={
                    'text-decoration': 'none',
                    'color': 'black',
                    'font-size': '40px',
                    'font-family': "'Open Sans', sans-serif",
                    'margin-left': '10px',  # Adds minimal space between the image and text
                    'align-self': 'center',  # Aligns the text vertically center with the image
                }),
            ], style={
                'flex': '1',
                'display': 'flex',
                'justify-content': 'flex-start',  # Aligns the image and text to the left
                'align-items': 'center',  # Aligns the image and text vertically center
            }),
        ], style={'display': 'flex', 'border-bottom': '0px solid white', 'border-top': '0px solid white'}),

        #add a blank div to give the sidebar some height space
        html.Div(style={'height': '25px'}),


        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact", className="sidebar-button page-button"),

                #LEVEL 2 PAGE
                dbc.NavItem([
                    dbc.Button("Balances", id="toggle-page-1", className="sidebar-button page-button", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [                             
                                dbc.NavLink("Cushing", href="/balances/cushing", active='exact', className="nav-link"),
                                dbc.NavLink("PADD9", href="/balances/padd9", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-1",
                    ),
                ]),
                #LEVEL 2 PAGE
                dbc.NavItem([
                    dbc.Button("EIA Weekly", id="toggle-page-2", className="sidebar-button page-button", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavLink("Headline", href="/stats/headline", active='exact', className="nav-link"),
                                dbc.NavLink("Crude", href="/stats/crude", active='exact', className="nav-link"),                                
                                dbc.NavLink("Gasoline", href="/stats/gasoline", active='exact', className="nav-link"),                                
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-2",
                    ),
                ]),            
                       
                #LEVEL 3 PAGE                                    
                dbc.NavItem([
                    dbc.Button("Production", id="toggle-page-3", className="sidebar-button page-button", n_clicks=0),
                    dbc.Collapse(
                        #SUB LEVEL PAGE 1
                        dbc.Nav(
                            [                             
                                dbc.NavLink("Rig Count", href="/production/rig_count", active='exact', className="nav-link"),
                                dbc.NavLink("US Production", href="/production/us_production", active='exact', className="nav-link"),
                                dbc.NavLink("Natural Gas", href="/production/natural_gas", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-3",
                    ),                    
                ]),

                #LEVEL 4 PAGE
                dbc.NavItem([
                    dbc.Button("Refining", id="toggle-page-4", className="sidebar-button page-button", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [                             
                             dbc.NavLink("Turnarounds", href="/refining/turnarounds", active='exact', className="nav-link"),
                             dbc.NavLink("Margins", href="/refining/margins", active='exact', className="nav-link"),
                                dbc.NavLink("Runs", href="/refining/runs", active='exact', className="nav-link"),
                                dbc.NavLink("Other Indicators", href="/refining/other_indicators", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-4",
                    ),                    
                ]),

                #LEVEL 5 PAGE
                dbc.NavItem([
                    dbc.Button("Trade Flows", id="toggle-page-5", className="sidebar-button page-button", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [                             
                             dbc.NavLink("Iran", href="/trade_flows/iran", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-5",
                    ),                    
                ]),

                #LEVEL 6 PAGE
                dbc.NavItem([
                    dbc.Button("Prices", id="toggle-page-6", className="sidebar-button page-button", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [                             
                             dbc.NavLink("US Forwards", href="/prices/us_forwards", active='exact', className="nav-link"),
                                dbc.NavLink("Brent", href="/prices/brent", active='exact', className="nav-link"),
                                dbc.NavLink("US Map", href="/prices/us_map", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-6",
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

app.layout = html.Div([dcc.Location(id='url', refresh=False), sidebar, content])

@app.callback(
    Output("collapse-page-1", "is_open"),
    [Input("toggle-page-1", "n_clicks")],
    [State("collapse-page-1", "is_open")]
)
def toggle_collapse_page_1(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("collapse-page-2", "is_open"),
    [Input("toggle-page-2", "n_clicks")],
    [State("collapse-page-2", "is_open")]
)
def toggle_collapse_page_2(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("collapse-page-3", "is_open"),
    [Input("toggle-page-3", "n_clicks")],
    [State("collapse-page-3", "is_open")]
)
def toggle_collapse_page_3(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("collapse-page-4", "is_open"),
    [Input("toggle-page-4", "n_clicks")],
    [State("collapse-page-4", "is_open")]
)
def toggle_collapse_page_4(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("collapse-page-5", "is_open"),
    [Input("toggle-page-5", "n_clicks")],
    [State("collapse-page-5", "is_open")]
)
def toggle_collapse_page_5(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("collapse-page-6", "is_open"),
    [Input("toggle-page-6", "n_clicks")],
    [State("collapse-page-6", "is_open")]
)
def toggle_collapse_page_6(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    #Balances
    if pathname == '/balances/cushing':
        return pages.page1_1.layout
    elif pathname == '/balances/padd9':
        return pages.page1_2.layout
    
    #EIA Weekly
    elif pathname == '/stats/headline':
        return pages.page2_1.layout        
    elif pathname == '/stats/crude':
        return pages.page2_2.layout
    elif pathname == '/stats/gasoline':
        return pages.page2_3.layout

    #Produciton
    elif pathname == '/stats/production/rig_count':
        return pages.page3_1.layout
    elif pathname == '/stats/production/us_production':
        return pages.page3_2.layout
    elif pathname == '/stats/production/natural_gas':
        return pages.page3_3.layout
    
    #Refining
    elif pathname == '/stats/refining/turnarounds':
        return pages.page4_1.layout
    elif pathname == '/stats/refining/margins':
        return pages.page4_2.layout
    elif pathname == '/stats/refining/runs':
        return pages.page4_3.layout
    elif pathname == '/stats/refining/other_indicators':
        return pages.page4_4.layout
    
    #Trade Flows
    elif pathname == '/stats/trade_flows/iran':
        return pages.page5_1.layout
    
    #Prices
    elif pathname == '/stats/prices/us_forwards':
        return pages.page6_1.layout
    elif pathname == '/stats/prices/brent':
        return pages.page6_2.layout
    elif pathname == '/stats/prices/us_map':
        return pages.page6_3.layout
    
    elif pathname == '/':
        return html.Div([
            html.H3("Home Page"),
            html.P("Welcome to the home page of the multi-page app.")
        ])
    else:
        return "404 Page Not Found"

if __name__ == '__main__':
    app.run_server(debug=True)
