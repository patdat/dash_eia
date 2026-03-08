import dash
from dash import html, dcc, Input, Output, State

from src.utils.variables import year_1_string, year_2_string, year_3_string, year_4_string, year_5_string, full_year_range_normal_string, full_year_range_last_five_years_string
from src.utils.colors import BLACK, BLUE, RED, GREEN, ORANGE

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
chart_seag = create_button_style(30, 475, "black", "white")
chart_line = create_button_style(30, 475, "black", "white")
toggler_on = create_button_style(30, 200, "black", "white")
toggler_off = create_button_style(30, 200, "black", "white")
button_year_5 = create_button_style(30, 50, ORANGE, "white")
button_year_4 = create_button_style(30, 50, GREEN, "white")
button_year_3 = create_button_style(30, 50, BLACK, "white")
button_year_2 = create_button_style(30, 50, BLUE, "white")
button_year_1 = create_button_style(30, 50, RED, "white")
off_button = create_button_style(30, 50, "white", "grey")
line_buttons = create_button_style(30, 91, "white", "grey")
active_line_button = create_button_style(30, 91, BLACK, "white")
button_main_line = create_button_style(30, 80, BLACK, "white")
button_ma_1m = create_button_style(30, 80, BLUE, "white")
button_ma_3m = create_button_style(30, 80, RED, "white")
button_ma_12m = create_button_style(30, 80, GREEN, "white")
off_button_ma = create_button_style(30, 80, "white", "grey")


def checklist_header(
    app,
    chart_toggle,
    seasonality_buttons,
    line_buttons_div,
    toggle_seag_range,
    toggle_year_1,
    toggle_year_2,
    toggle_year_3,
    toggle_year_4,
    toggle_year_5,
    btn_1m,
    btn_3m,
    btn_12m,
    btn_36m,
    btn_60m,
    toggle_main_line=None,
    toggle_ma_1m=None,
    toggle_ma_3m=None,
    toggle_ma_12m=None,
):
    seasonality_visible_style = {"display": "block"}
    seasonality_hidden_style = {"display": "none"}
    line_controls_visible_style = {
        "display": "flex",
        "height": "72px",
        "alignItems": "flex-start",
    }
    line_controls_hidden_style = {
        "display": "none",
        "height": "72px",
        "alignItems": "flex-start",
    }

    line_overlay_buttons = []
    if toggle_main_line:
        line_overlay_buttons.append(
            html.Button("Main", id=toggle_main_line, n_clicks=0, style=button_main_line)
        )

    if toggle_ma_1m and toggle_ma_3m and toggle_ma_12m:
        line_overlay_buttons.extend(
            [
                html.Button("1m MA", id=toggle_ma_1m, n_clicks=0, style=off_button_ma),
                html.Button("3m MA", id=toggle_ma_3m, n_clicks=0, style=off_button_ma),
                html.Button("12m MA", id=toggle_ma_12m, n_clicks=0, style=off_button_ma),
            ]
        )

    technical_analysis_section = []
    if line_overlay_buttons:
        technical_analysis_section = html.Div(
            [
                html.Div(
                    "Technical Analysis",
                    style={
                        "width": "335px",
                        "padding-bottom": "2px",
                        "border-bottom": f"1px solid {BLACK}",
                        "font-size": "12px",
                        "font-weight": "600",
                        "color": BLACK,
                        "text-align": "center",
                    },
                ),
                html.Div(
                    line_overlay_buttons,
                    style={"display": "flex"},
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "margin-left": "50px",
                "margin-top": "-18px",
                "width": "335px",
            },
        )

    html_container = html.Div(
        [
            # State storage for line button radio group only
            *[dcc.Store(id=f"{id}-state", data=(id == btn_60m)) for id in [
                btn_1m, btn_3m, btn_12m, btn_36m, btn_60m]
            ],
            # Main layout
            html.Div(
                html.Button("Graph: Seasonality", id=chart_toggle, n_clicks=0, style=chart_seag),
                style={"margin-bottom": "-10px"}
            ),
            html.Div(
                [
                    html.Button(f"Range: {full_year_range_last_five_years_string}", id=toggle_seag_range, n_clicks=0, style=toggler_on),
                    html.Button(year_3_string, id=toggle_year_3, n_clicks=0, style=button_year_3),
                    html.Button(year_2_string, id=toggle_year_2, n_clicks=0, style=button_year_2),
                    html.Button(year_1_string, id=toggle_year_1, n_clicks=0, style=button_year_1),
                    html.Button(year_4_string, id=toggle_year_4, n_clicks=0, style=button_year_4),
                    html.Button(year_5_string, id=toggle_year_5, n_clicks=0, style=button_year_5),
                ],
                id=seasonality_buttons, style={"display": "block"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Button("-1m", id=btn_1m, n_clicks=0, style=line_buttons),
                            html.Button("-3m", id=btn_3m, n_clicks=0, style=line_buttons),
                            html.Button("-12m", id=btn_12m, n_clicks=0, style=line_buttons),
                            html.Button("-36m", id=btn_36m, n_clicks=0, style=line_buttons),
                            html.Button("-60m", id=btn_60m, n_clicks=0, style=active_line_button),
                        ],
                        style={"display": "flex"},
                    ),
                    technical_analysis_section,
                ],
                id=line_buttons_div,
                style=line_controls_hidden_style,
            ),
        ],
        style={"height": "60px"},
    )

    # Callbacks
    @app.callback(
        [Output(chart_toggle, "style"), Output(chart_toggle, "children"),
         Output(seasonality_buttons, "style"), Output(line_buttons_div, "style")],
        [Input(chart_toggle, "n_clicks")],
        prevent_initial_call=True,
    )
    def toggle_chart_button(n_clicks):
        state = n_clicks % 2 == 0
        return (
            chart_seag if state else chart_line,
            "Graph: Seasonality" if state else "Graph: Line",
            seasonality_visible_style if state else seasonality_hidden_style,
            line_controls_hidden_style if state else line_controls_visible_style,
        )

    @app.callback(
        [Output(toggle_seag_range, "style"), Output(toggle_seag_range, "children")],
        [Input(toggle_seag_range, "n_clicks")],
        prevent_initial_call=True,
    )
    def toggle_range_button(n_clicks):
        state = n_clicks % 2 == 1
        return (
            toggler_off if state else toggler_on,
            f"Range: {full_year_range_normal_string}" if state else f"Range: {full_year_range_last_five_years_string}",
        )

    def create_toggle_callback(button_id, active_style, inactive_style=None):
        if inactive_style is None:
            inactive_style = off_button

        @app.callback(
            Output(button_id, "style"),
            [Input(button_id, "n_clicks")],
            prevent_initial_call=True,
        )
        def toggle_button(n_clicks):
            state = n_clicks % 2 == 1
            return inactive_style if state else active_style
        return toggle_button

    # Create callbacks for year toggle buttons
    create_toggle_callback(toggle_year_3, button_year_3)
    create_toggle_callback(toggle_year_2, button_year_2)
    create_toggle_callback(toggle_year_1, button_year_1)
    create_toggle_callback(toggle_year_4, button_year_4)
    create_toggle_callback(toggle_year_5, button_year_5)

    # Single style-only callback for MA buttons (no stores)
    if toggle_main_line and toggle_ma_1m and toggle_ma_3m and toggle_ma_12m:
        @app.callback(
            [Output(toggle_main_line, "style"),
             Output(toggle_ma_1m, "style"),
             Output(toggle_ma_3m, "style"),
             Output(toggle_ma_12m, "style")],
            [Input(toggle_main_line, "n_clicks"),
             Input(toggle_ma_1m, "n_clicks"),
             Input(toggle_ma_3m, "n_clicks"),
             Input(toggle_ma_12m, "n_clicks")],
            prevent_initial_call=True,
        )
        def update_ma_styles(main_clicks, n1, n2, n3):
            return [
                button_main_line if main_clicks % 2 == 0 else off_button_ma,
                button_ma_1m if n1 % 2 == 1 else off_button_ma,
                button_ma_3m if n2 % 2 == 1 else off_button_ma,
                button_ma_12m if n3 % 2 == 1 else off_button_ma,
            ]

    @app.callback(
        [Output(btn_id, "style") for btn_id in [btn_1m, btn_3m, btn_12m, btn_36m, btn_60m]] +
        [Output(f"{btn_id}-state", "data") for btn_id in [btn_1m, btn_3m, btn_12m, btn_36m, btn_60m]],
        [Input(btn_id, "n_clicks") for btn_id in [btn_1m, btn_3m, btn_12m, btn_36m, btn_60m]],
        prevent_initial_call=True,
    )
    def toggle_line_buttons(*btn_clicks):
        ctx = dash.callback_context
        button_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else btn_60m
        styles = {btn: line_buttons for btn in [btn_1m, btn_3m, btn_12m, btn_36m, btn_60m]}
        states = {btn: False for btn in [btn_1m, btn_3m, btn_12m, btn_36m, btn_60m]}
        styles[button_id] = active_line_button
        states[button_id] = True
        return tuple(styles.values()) + tuple(states.values())

    return html_container


if __name__ == "__main__":
    app.layout = html.Div(
        checklist_header(
            app, "chart_toggle", "seasonality_buttons", "line_buttons_div",
            "toggle_seag_range", f"toggle_{year_1_string}", f"toggle_{year_2_string}", f"toggle_{year_3_string}",
            f"toggle_{year_4_string}", f"toggle_{year_5_string}",
            "btn_1m", "btn_3m", "btn_12m", "btn_36m", "btn_60m"
        )
    )
    app.run_server(debug=True, port=8051)
