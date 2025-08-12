from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from app import app  # Ensure this import points to where your Dash app is initialized
from app import initial_data

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
import pages.page3_1    # regional_charts
import pages.page3_2    # bakken
import pages.page3_3    # eagleford
import pages.page3_4    # haynesville
import pages.page3_5    # permian
import pages.page3_6    # other

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
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-2",
                        is_open=True,
                    ),
                ]),  
                
                # EIA StEO
                dbc.NavItem([
                    dbc.Button("EIA DPR", id="toggle-page-3", className="sidebar-button page-button closed", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavLink("DPR Charts", href="/dpr/dpr_charts", active='exact', className="nav-link"),  
                                dbc.NavLink("DPR Table", href="/dpr/dpr_table", active='exact', className="nav-link"),                                
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-3",
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


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/home':
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
    elif pathname == '/dpr/dpr_charts':
        return pages.page3_1.layout
    elif pathname == '/dpr/dpr_table':
        return pages.page3_2.layout
    
    else:
        return "404 Page Not Found"
if __name__ == '__main__':
    app.run(debug=False)
