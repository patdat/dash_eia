from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from app import app  # Ensure this import points to where your Dash app is initialized
from app import initial_data

import pages.page1  # Home
import pages.page2_1  # Headline
import pages.page2_2  # Crude Stocks
# import pages.page2_3  # Crude Production
# import pages.page2_4  # Crude Imports
# import pages.page2_5  # Crude Adjstument
# import pages.page2_6  # Crude Runs
# import pages.page2_7  # Crude Other
# import pages.page2_7  # Crude Exports
# import pages.page2_8  # Other Runs
# import pages.page2_9  # Gasoline
# import pages.page2_10  # Distillate
# import pages.page2_11  # Jet
# import pages.page2_12  # Fuel Oil
# import pages.page2_13  # C3/C3=
# import pages.page2_14  # Product Supplied
# import pages.page2_15  # Other Products

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

        # Add a blank div to give the sidebar some height space
        html.Div(style={'height': '25px'}),

        dbc.Nav(
            [
                dbc.NavLink("Home", href="/home", active="exact", className="nav-link"),
                
                dbc.NavItem([
                    dbc.Button("EIA Weekly", id="toggle-page-2", className="sidebar-button page-button closed", n_clicks=0),
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavLink("Headline", href="/stats/headline", active='exact', className="nav-link"),
                                dbc.NavLink("Crude Stocks", href="/stats/crude_stocks", active='exact', className="nav-link"),
                                dbc.NavLink("Crude Production", href="/stats/crude_production", active='exact', className="nav-link"),
                            ],
                            vertical=True, pills=True
                        ),
                        id="collapse-page-2",
                        is_open=False,
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
    dcc.Store(id='data-store', data=initial_data, storage_type='session'),
    sidebar,
    content
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
            new_class = current_class.replace("closed", "open")
        else:
            new_class = current_class.replace("open", "closed")
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
    elif pathname == '/stats/crude_stocks':
        return pages.page2_2.layout
    elif pathname == '/stats/crude_production':
        return pages.page2_5.layout
    else:
        return "404 Page Not Found"

if __name__ == '__main__':
    app.run_server(debug=True)
