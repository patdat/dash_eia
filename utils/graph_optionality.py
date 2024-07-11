import dash
from dash import html, Input, Output

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

# Layout
app.layout = html.Div([
    html.Button(id='chart_toggle', children=['chart_toggle'], n_clicks=0, style=toggler_on),
    html.Button(id='range_toggle', children=['range_toggle'], n_clicks=0, style=toggler_on),
    html.Button(id='2024_toggle', children=['2024'], n_clicks=0, style=button_2024),
    html.Button(id='2023_toggle', children=['2023'], n_clicks=0, style=button_2023),
    html.Button(id='2022_toggle', children=['2022'], n_clicks=0, style=button_2022),
])

# Callbacks
@app.callback(
    [Output('chart_toggle', 'style'), Output('chart_toggle', 'children')],
    [Input('chart_toggle', 'n_clicks')]
)
def toggle_chart_button(n_clicks):
    return (toggler_off, 'Graph: Line') if n_clicks % 2 == 1 else (toggler_on, 'Graph: Seasonality')

@app.callback(
    [Output('range_toggle', 'style'), Output('range_toggle', 'children')],
    [Input('range_toggle', 'n_clicks')]
)
def toggle_range_button(n_clicks):
    return (toggler_off, 'Range: 2015-2019') if n_clicks % 2 == 1 else (toggler_on, 'Range: 2018-2023')

@app.callback(
    Output('2024_toggle', 'style'),
    [Input('2024_toggle', 'n_clicks')]
)
def toggle_2024_button(n_clicks):
    return off_button if n_clicks % 2 == 1 else button_2024

@app.callback(
    Output('2023_toggle', 'style'),
    [Input('2023_toggle', 'n_clicks')]
)
def toggle_2023_button(n_clicks):
    return off_button if n_clicks % 2 == 1 else button_2023

@app.callback(
    Output('2022_toggle', 'style'),
    [Input('2022_toggle', 'n_clicks')]
)
def toggle_2022_button(n_clicks):
    return off_button if n_clicks % 2 == 1 else button_2022

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
