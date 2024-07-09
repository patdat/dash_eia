from dash import html
import dash_bootstrap_components as dbc
import dash_daq as daq

def checklist_header(toggle_graph, checklist_id, toggle_id, checklist_div_id, toggle_div_id):
    return html.Div([
        
        # blank to center
        html.Div(style={'flex-grow': '1', 'flex-shrink': '1'}),            
        
        html.Div([
            dbc.Checklist(
                id=checklist_id,
                options=[
                    {"label": html.Div(['22'], style={'color': 'white', 'font-size': '20px', 'background-color': '#bfbec4', 'padding': '5px', 'border-radius': '5px', 'height': '33px', 'width': '60px', 'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}), "value": '2022'},
                    {"label": html.Div(['23'], style={'color': 'white', 'font-size': '20px', 'background-color': '#e97132', 'padding': '5px', 'border-radius': '5px', 'height': '33px', 'width': '60px', 'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}), "value": '2023'},
                    {"label": html.Div(['24'], style={'color': 'white', 'font-size': '20px', 'background-color': '#c00000', 'padding': '5px', 'border-radius': '5px', 'height': '33px', 'width': '60px', 'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}), "value": '2024'},
                ],
                label_checked_style={"color": "red"},
                input_checked_style={
                    "backgroundColor": "black",
                    "borderColor": "#ea6258",
                },                    
                value=['2022', '2023', '2024'],
                inline=True,
                labelStyle={"display": "flex", "align-items": "center", "margin-right": "20px", "font-size": "35px"},
                style={'padding': '0px', 'font-size': '25px', 'display': 'flex', 'justify-content': 'right'}
            ),
        ], id=checklist_div_id, style={'padding': '0px', 'flex-grow': '0', 'flex-shrink': '0', 'flex-basis': 'auto', 'min-width': '160px'}),

        # blank to center
        html.Div(style={
            'width': '5px',
            'height': '100vh',  # 100% of the viewport height
            'background-color': 'white',
            'border': 'none',   # Remove any border if not needed
        }),

        html.Div([
            html.Div([
                dbc.Label('18-23', style={'margin-right': '10px', 'margin-top': '10px'}),
                daq.ToggleSwitch(
                    id=toggle_id,
                    value=False,
                    style={
                        'margin-top': '0px',
                        'margin-bottom': '0px',
                        'display': 'inline-block',
                    },
                ),
                dbc.Label('15-19', style={'margin-left': '10px', 'margin-top': '10px'}),
            ], style={
                'display': 'flex',
                'align-items': 'center',
                'justify-content': 'center'
            }),
        ], id=toggle_div_id, style={
            'margin-left': '10px',
            'margin-right': '10px',
            'flex-grow': '0',
            'flex-shrink': '0',
            'flex-basis': 'auto',
            'min-width': '120px',
            'display': 'flex',
            'align-items': 'center',
        }),

        # blank to center
        html.Div(style={
            'width': '5px',
            'height': '100vh',  # 100% of the viewport height
            'background-color': 'white',
            'border': 'none',   # Remove any border if not needed
        }),

        html.Div([
            html.Div([
                dbc.Label('seag', style={'margin-right': '10px', 'margin-top': '10px'}),
                daq.ToggleSwitch(
                    id=toggle_graph,
                    value=False,
                    style={
                        'margin-top': '0px',
                        'margin-bottom': '0px',
                        'display': 'inline-block',
                    },
                ),
                dbc.Label('line', style={'margin-left': '10px', 'margin-top': '10px'}),
            ], style={
                'display': 'flex',
                'align-items': 'center',
                'justify-content': 'center'
            }),
        ], style={
            'margin-left': '10px',
            'margin-right': '10px',
            'flex-grow': '0',
            'flex-shrink': '0',
            'flex-basis': 'auto',
            'min-width': '120px',
            'display': 'flex',
            'align-items': 'center',
        }),
    ], style={'height': '65px', 'border-bottom': '1px solid white', 'display': 'flex', 'flex-direction': 'row', 'align-items': 'center', 'position': 'fixed', 'top': '0', 'left': '0', 'right': '0', 'background-color': '#f4f5f9', 'z-index': '1000', 'box-shadow': '0px 2px 5px rgba(0,0,0,0.2)', 'overflow-x': 'auto'})
