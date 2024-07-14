import dash
from dash import html, Input, Output, State, dcc

app = dash.Dash(__name__)

chart_button_style_base = {
    'height': '30px',
    'width': '365px',
    'margin-top': '20px',
    'margin-left': '20px',
    'margin-right': '-15px',
    'border-radius': '10px',
    'box-shadow': '0px 4px 8px rgba(0, 0, 0, 0.2)',
    'border': 'none',
    'position': 'relative',
    'z-index': '1'
}

chart_seag = {
    **chart_button_style_base,
    'background-color': 'black',
    'color': 'white'
}

chart_line = {
    **chart_button_style_base,
    'background-color': 'black',
    'color': 'white'
}

# Style dictionaries
button_style_base = {
    'height': '30px',
    'width': '200px',
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
    'background-color': 'black',
    'color': 'white'
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


small_button_style_base_line_graph = {
    'height': '30px',
    'width': '69px',
    'margin-top': '20px',
    'margin-left': '20px',
    'margin-right': '-15px',
    'border-radius': '10px',
    'box-shadow': '0px 4px 8px rgba(0, 0, 0, 0.2)',
    'border': 'none',
    'position': 'relative',
    'z-index': '1'
}

line_buttons = {
    **small_button_style_base_line_graph,
    'background-color': 'white',
    'color': 'grey'
}

active_line_button = {
    **small_button_style_base_line_graph,
    'background-color': '#c00000',
    'color': 'white'
}

def checklist_header(app, chart_toggle, seasonality_buttons, line_buttons_div, toggle_seag_range, toggle_2022, toggle_2023, toggle_2024,btn_1m, btn_6m, btn_12m, btn_36m, btn_all):
    html_container = html.Div([
        dcc.Store(id=f'{chart_toggle}-state', data=True, storage_type='session'),
        dcc.Store(id=f'{seasonality_buttons}-state', data=True, storage_type='session'),
        dcc.Store(id=f'{line_buttons_div}-state', data=True, storage_type='session'),
        dcc.Store(id=f'{toggle_seag_range}-state', data=True, storage_type='session'),
        dcc.Store(id=f'{toggle_2022}-state', data=True, storage_type='session'),
        dcc.Store(id=f'{toggle_2023}-state', data=True, storage_type='session'),
        dcc.Store(id=f'{toggle_2024}-state', data=True, storage_type='session'),
        dcc.Store(id=f'{btn_1m}-state', data=False, storage_type='session'),
        dcc.Store(id=f'{btn_6m}-state', data=False, storage_type='session'),
        dcc.Store(id=f'{btn_12m}-state', data=False, storage_type='session'),
        dcc.Store(id=f'{btn_36m}-state', data=False, storage_type='session'),
        dcc.Store(id=f'{btn_all}-state', data=True, storage_type='session'),  # Default to 'all' active

        html.Div([
            html.Button(id=chart_toggle, children='Graph: Seasonality', n_clicks=0, style=chart_seag),
        ], id='graph_toggle', style={'margin-bottom': '-10px'}),

        #CENTER THIS
        html.Div([
            html.Button(id=toggle_seag_range, children='Range: 2018-2023', n_clicks=0, style=toggler_on),
            html.Button(id=toggle_2022, children='2022', n_clicks=0, style=button_2022),
            html.Button(id=toggle_2023, children='2023', n_clicks=0, style=button_2023),
            html.Button(id=toggle_2024, children='2024', n_clicks=0, style=button_2024),
        ], id=seasonality_buttons, style={'display': 'block'}),

        #CENTER THIS
        html.Div([
            html.Button(id=btn_1m, children='-1m', n_clicks=0, style=line_buttons),
            html.Button(id=btn_6m, children='-6m', n_clicks=0, style=line_buttons),
            html.Button(id=btn_12m, children='-12m', n_clicks=0, style=line_buttons),
            html.Button(id=btn_36m, children='-36m', n_clicks=0, style=line_buttons),
            html.Button(id=btn_all, children='all', n_clicks=0, style=active_line_button),  # Default to 'all' active
        ], id=line_buttons_div, style={'display': 'none'}),

        html.Div(id='hidden-div', style={'display':'none'}),
    ], style={'height': '60px'})

    @app.callback(
        [Output(chart_toggle, 'style'), Output(chart_toggle, 'children'), Output(seasonality_buttons, 'style'), Output(line_buttons_div, 'style'), Output(f'{chart_toggle}-state', 'data')],
        [Input(chart_toggle, 'n_clicks')],
        [State(chart_toggle, 'children')]
    )
    def toggle_chart_button(n_clicks, current_text):
        state = n_clicks % 2 == 1
        # print(f"chart_toggle clicked: {n_clicks} times, current state: {state}")
        if state:
            return chart_line, 'Graph: Line', {'display': 'none'}, {'display': 'block'}, False
        else:
            return chart_seag, 'Graph: Seasonality', {'display': 'block'}, {'display': 'none'}, True

    @app.callback(
        [Output(toggle_seag_range, 'style'), Output(toggle_seag_range, 'children'), Output(f'{toggle_seag_range}-state', 'data')],
        [Input(toggle_seag_range, 'n_clicks')],
        [State(toggle_seag_range, 'children')]
    )
    def toggle_range_button(n_clicks, current_text):
        state = n_clicks % 2 == 1
        # print(f"range_toggle clicked: {n_clicks} times, current state: {state}")
        return (toggler_off, 'Range: 2015-2019', False) if state else (toggler_on, 'Range: 2018-2023', True)

    @app.callback(
        [Output(toggle_2024, 'style'), Output(f'{toggle_2024}-state', 'data')],
        [Input(toggle_2024, 'n_clicks')],
        [State(toggle_2024, 'style')]
    )
    def toggle_2024_button(n_clicks, current_style):
        state = n_clicks % 2 == 1
        # print(f"toggle_2024 clicked: {n_clicks} times, current state: {state}")
        return (off_button if state else button_2024), state

    @app.callback(
        [Output(toggle_2023, 'style'), Output(f'{toggle_2023}-state', 'data')],
        [Input(toggle_2023, 'n_clicks')],
        [State(toggle_2023, 'style')]
    )
    def toggle_2023_button(n_clicks, current_style):
        state = n_clicks % 2 == 1
        # print(f"toggle_2023 clicked: {n_clicks} times, current state: {state}")
        return (off_button if state else button_2023), state

    @app.callback(
        [Output(toggle_2022, 'style'), Output(f'{toggle_2022}-state', 'data')],
        [Input(toggle_2022, 'n_clicks')],
        [State(toggle_2022, 'style')]
    )
    def toggle_2022_button(n_clicks, current_style):
        state = n_clicks % 2 == 1
        # print(f"toggle_2022 clicked: {n_clicks} times, current state: {state}")
        return (off_button if state else button_2022), state

    @app.callback(
        [Output(btn_1m, 'style'), Output(btn_6m, 'style'), Output(btn_12m, 'style'), Output(btn_36m, 'style'), Output(btn_all, 'style'),
         Output(f'{btn_1m}-state', 'data'), Output(f'{btn_6m}-state', 'data'), Output(f'{btn_12m}-state', 'data'), Output(f'{btn_36m}-state', 'data'), Output(f'{btn_all}-state', 'data')],
        [Input(f'{btn_1m}', 'n_clicks'), Input(f'{btn_6m}', 'n_clicks'), Input(f'{btn_12m}', 'n_clicks'), Input(f'{btn_36m}', 'n_clicks'), Input(f'{btn_all}', 'n_clicks')]
    )
    def toggle_line_buttons(btn_1m_clicks, btn_6m_clicks, btn_12m_clicks, btn_36m_clicks, btn_all_clicks):
        ctx = dash.callback_context

        if not ctx.triggered:
            button_id = f'{btn_all}'  # Default button
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        styles = {button_id: active_line_button}
        states = {button_id: True}
        for button in [f'{btn_1m}', f'{btn_6m}', f'{btn_12m}', f'{btn_36m}', f'{btn_all}']:
            if button != button_id:
                styles[button] = line_buttons
                states[button] = False

        return (styles[f'{btn_1m}'], styles[f'{btn_6m}'], styles[f'{btn_12m}'], styles[f'{btn_36m}'], styles[f'{btn_all}'],
                states[f'{btn_1m}'], states[f'{btn_6m}'], states[f'{btn_12m}'], states[f'{btn_36m}'], states[f'{btn_all}'])

    return html_container

if __name__ == '__main__':
    app.layout = html.Div([
        checklist_header(app, 'chart_toggle', 'seasonality_buttons', 'line_buttons_div', 'toggle_seag_range', 'toggle_2022', 'toggle_2023', 'toggle_2024')
    ])

    app.run_server(debug=True, port=8051)
