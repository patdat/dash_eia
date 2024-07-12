import dash
from dash import html, Input, Output, State

app = dash.Dash(__name__)

# Style dictionaries
button_style_base = {
    'height': '30px',
    'width': '150px',
    'margin-top': '20px',
    'margin-left': '20px',
    'margin-right': '-15px',
    'border-radius': '10px',
    'box-shadow': '0px 4px 8px rgba(0, 0, 0, 0.2)',
    'border': 'none',
    'position': 'relative',
    'z-index': '1'
}

toggler_on = {
    **button_style_base,
    'background-color': 'black',
    'color': 'white'
}

toggler_off = {
    **button_style_base,
    'background-color': 'grey',
    'color': 'black'
}

small_button_style_base = {
    'height': '30px',
    'width': '50px',
    'margin-top': '20px',
    'margin-left': '20px',
    'margin-right': '-15px',
    'border-radius': '10px',
    'box-shadow': '0px 4px 8px rgba(0, 0, 0, 0.2)',
    'border': 'none',
    'position': 'relative',
    'z-index': '1'
}

button_2024 = {
    **small_button_style_base,
    'background-color': '#c00000',
    'color': 'white'
}

button_2023 = {
    **small_button_style_base,
    'background-color': '#e97132',
    'color': 'white'
}

button_2022 = {
    **small_button_style_base,
    'background-color': '#bfbec4',
    'color': 'white'
}

off_button = {
    **small_button_style_base,
    'background-color': 'white',
    'color': 'grey'
}

def checklist_header(app, chart_toggle, seasonality_buttons, toggle_2022, toggle_2023, toggle_2024):
    html_container = html.Div([
        html.Div([
            html.Button(id=chart_toggle, children='Graph: Seasonality', n_clicks=0, style=toggler_on),
        ], id='graph_toggle', style={'margin-bottom': '-10px'}),
        
        html.Div([
            html.Button(id='range_toggle', children='Range: 2018-2023', n_clicks=0, style=toggler_on),
            html.Button(id=toggle_2022, children='2022', n_clicks=0, style=button_2022),
            html.Button(id=toggle_2023, children='2023', n_clicks=0, style=button_2023),            
            html.Button(id=toggle_2024, children='2024', n_clicks=0, style=button_2024),
            
        ], id=seasonality_buttons, style={'display': 'block'}),
        html.Div(id='hidden-div', style={'display':'none'}),
    ])

    @app.callback(
        [Output(chart_toggle, 'style'), Output(chart_toggle, 'children'), Output(seasonality_buttons, 'style')],
        [Input(chart_toggle, 'n_clicks')],
        [State(chart_toggle, 'children')]
    )
    def toggle_chart_button(n_clicks, current_text):
        state = n_clicks % 2 == 1
        print(f"chart_toggle clicked: {n_clicks} times, current state: {state}")
        if state:
            return toggler_off, 'Graph: Line', {'display': 'none'}
        else:
            return toggler_on, 'Graph: Seasonality', {'display': 'block'}

    @app.callback(
        [Output('range_toggle', 'style'), Output('range_toggle', 'children')],
        [Input('range_toggle', 'n_clicks')],
        [State('range_toggle', 'children')]
    )
    def toggle_range_button(n_clicks, current_text):
        state = n_clicks % 2 == 1
        print(f"range_toggle clicked: {n_clicks} times, current state: {state}")
        return (toggler_off, 'Range: 2015-2019') if state else (toggler_on, 'Range: 2018-2023')

    @app.callback(
        Output(toggle_2024, 'style'),
        [Input(toggle_2024, 'n_clicks')],
        [State(toggle_2024, 'style')]
    )
    def toggle_2024_button(n_clicks, current_style):
        state = n_clicks % 2 == 1
        print(f"toggle_2024 clicked: {n_clicks} times, current state: {state}")
        return off_button if state else button_2024

    @app.callback(
        Output(toggle_2023, 'style'),
        [Input(toggle_2023, 'n_clicks')],
        [State(toggle_2023, 'style')]
    )
    def toggle_2023_button(n_clicks, current_style):
        state = n_clicks % 2 == 1
        print(f"toggle_2023 clicked: {n_clicks} times, current state: {state}")
        return off_button if state else button_2023

    @app.callback(
        Output(toggle_2022, 'style'),
        [Input(toggle_2022, 'n_clicks')],
        [State(toggle_2022, 'style')]
    )
    def toggle_2022_button(n_clicks, current_style):
        state = n_clicks % 2 == 1
        print(f"toggle_2022 clicked: {n_clicks} times, current state: {state}")
        return off_button if state else button_2022
    
    return html_container

if __name__ == '__main__':
    app.layout = html.Div([
        checklist_header(app, 'chart_toggle', 'seasonality_buttons', 'toggle_2022', 'toggle_2023', 'toggle_2024')
    ])
    
    app.run_server(debug=True, port=8051)
