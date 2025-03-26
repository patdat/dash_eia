import dash
from dash import html, dcc, Input, Output, State

from utils.variables import year_1_string, year_2_string, year_3_string, full_year_range_normal_string, full_year_range_last_five_years_string

app = dash.Dash(__name__)

# Define button styles
def create_button_style(height, width, background_color, color):
    return {
        "height": f"{height}px",
        "width": f"{width}px",
        "margin-top": "20px",
        "margin-left": "20px",
        "margin-right": "-15px",
        "border-radius": "10px",
        "box-shadow": "0px 4px 8px rgba(0, 0, 0, 0.2)",
        "border": "none",
        "position": "relative",
        "z-index": "1",
        "background-color": background_color,
        "color": color,
    }

# Styles for buttons
chart_seag = create_button_style(30, 365, "black", "white")
chart_line = create_button_style(30, 365, "black", "white")
toggler_on = create_button_style(30, 200, "black", "white")
toggler_off = create_button_style(30, 200, "black", "white")
button_year_3 = create_button_style(30, 50, "#c00000", "white")
button_year_2 = create_button_style(30, 50, "#e97132", "white")
button_year_1 = create_button_style(30, 50, "#bfbec4", "white")
off_button = create_button_style(30, 50, "white", "grey")
line_buttons = create_button_style(30, 69, "white", "grey")
active_line_button = create_button_style(30, 69, "#c00000", "white")


def checklist_header(
    app,
    chart_toggle,
    seasonality_buttons,
    line_buttons_div,
    toggle_seag_range,
    toggle_year_1,
    toggle_year_2,
    toggle_year_3,
    btn_1m,
    btn_6m,
    btn_12m,
    btn_36m,
    btn_all,
):
    html_container = html.Div(
        [
            # State storage for button states
            *[dcc.Store(id=f"{id}-state", data=(id == btn_all)) for id in [
                chart_toggle, seasonality_buttons, line_buttons_div,
                toggle_seag_range, toggle_year_1, toggle_year_2, toggle_year_3,
                btn_1m, btn_6m, btn_12m, btn_36m, btn_all]
            ],
            
            # Main layout
            html.Div(
                html.Button("Graph: Line", id=chart_toggle, n_clicks=0, style=chart_line),
                style={"margin-bottom": "-10px"}
            ),
            html.Div(
                [
                    html.Button(f"Range: {full_year_range_last_five_years_string}", id=toggle_seag_range, n_clicks=0, style=toggler_on),
                    html.Button(year_1_string, id=toggle_year_1, n_clicks=0, style=button_year_1),
                    html.Button(year_2_string, id=toggle_year_2, n_clicks=0, style=button_year_2),
                    html.Button(year_3_string, id=toggle_year_3, n_clicks=0, style=button_year_3),
                ],
                id=seasonality_buttons, style={"display": "block"},
            ),
            html.Div(
                [
                    html.Button("-1m", id=btn_1m, n_clicks=0, style=line_buttons),
                    html.Button("-6m", id=btn_6m, n_clicks=0, style=line_buttons),
                    html.Button("-12m", id=btn_12m, n_clicks=0, style=line_buttons),
                    html.Button("-36m", id=btn_36m, n_clicks=0, style=line_buttons),
                    html.Button("all", id=btn_all, n_clicks=0, style=active_line_button),
                ],
                id=line_buttons_div, style={"display": "none"},
            ),
            html.Div(id="hidden-div", style={"display": "none"}),
        ],
        style={"height": "60px"},
    )

    # Callbacks
    @app.callback(
        [Output(chart_toggle, "style"), Output(chart_toggle, "children"),
         Output(seasonality_buttons, "style"), Output(line_buttons_div, "style"),
         Output(f"{chart_toggle}-state", "data")],
        [Input(chart_toggle, "n_clicks")],
    )
    def toggle_chart_button(n_clicks):
        state = n_clicks % 2 == 0
        return (
            chart_seag if state else chart_line,
            "Graph: Seasonality" if state else "Graph: Line",
            {"display": "block"} if state else {"display": "none"},
            {"display": "none"} if state else {"display": "block"},
            state,
        )

    @app.callback(
        [Output(toggle_seag_range, "style"), Output(toggle_seag_range, "children"),
         Output(f"{toggle_seag_range}-state", "data")],
        [Input(toggle_seag_range, "n_clicks")],
    )
    def toggle_range_button(n_clicks):
        state = n_clicks % 2 == 1
        return (
            toggler_off if state else toggler_on,
            f"Range: {full_year_range_normal_string}" if state else f"Range: {full_year_range_last_five_years_string}",
            state,
        )

    def create_year_toggle_callback(button_id, active_style):
        @app.callback(
            [Output(button_id, "style"), Output(f"{button_id}-state", "data")],
            [Input(button_id, "n_clicks")],
        )
        def toggle_year_button(n_clicks):
            state = n_clicks % 2 == 1
            return (off_button if state else active_style, state)
        return toggle_year_button

    # Create callbacks for year toggle buttons
    create_year_toggle_callback(toggle_year_3, button_year_1)
    create_year_toggle_callback(toggle_year_2, button_year_2)
    create_year_toggle_callback(toggle_year_1, button_year_3)

    @app.callback(
        [Output(btn_id, "style") for btn_id in [btn_1m, btn_6m, btn_12m, btn_36m, btn_all]] +
        [Output(f"{btn_id}-state", "data") for btn_id in [btn_1m, btn_6m, btn_12m, btn_36m, btn_all]],
        [Input(btn_id, "n_clicks") for btn_id in [btn_1m, btn_6m, btn_12m, btn_36m, btn_all]],
    )
    def toggle_line_buttons(*btn_clicks):
        ctx = dash.callback_context
        button_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else btn_all
        styles = {btn: line_buttons for btn in [btn_1m, btn_6m, btn_12m, btn_36m, btn_all]}
        states = {btn: False for btn in [btn_1m, btn_6m, btn_12m, btn_36m, btn_all]}
        styles[button_id] = active_line_button
        states[button_id] = True
        return tuple(styles.values()) + tuple(states.values())

    return html_container


if __name__ == "__main__":
    app.layout = html.Div(
        checklist_header(
            app, "chart_toggle", "seasonality_buttons", "line_buttons_div",
            "toggle_seag_range", f"toggle_{year_1_string}", f"toggle_{year_2_string}", f"toggle_{year_3_string}",
            "btn_1m", "btn_6m", "btn_12m", "btn_36m", "btn_all"
        )
    )
    app.run_server(debug=True, port=8051)