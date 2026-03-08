import dash
from dash import html, Input, Output, dcc
from src.utils.colors import BLUE

app = dash.Dash(__name__)

# Base style for line buttons
small_button_style_base_line_graph = {
    "height": "30px",
    "width": "69px",
    "margin-top": "20px",
    "margin-left": "20px",
    "margin-right": "-15px",
    "border-radius": "10px",
    "box-shadow": "0px 4px 8px rgba(0, 0, 0, 0.2)",
    "border": "none",
    "position": "relative",
    "z-index": "1",
}

# Styles for inactive and active buttons
line_buttons = {
    **small_button_style_base_line_graph,
    "background-color": "white",
    "color": "grey",
}

active_line_button = {
    **small_button_style_base_line_graph,
    "background-color": BLUE,
    "color": "white",
}

# Layout with only line buttons
def checklist_header(
    app,
    btn_2020,
    btn_2021,
    btn_2022,
    btn_2023,
    btn_2024,
    btn_2025,
    btn_2026,
):
    year_buttons = [
        (btn_2020, "2020"),
        (btn_2021, "2021"),
        (btn_2022, "2022"),
        (btn_2023, "2023"),
        (btn_2024, "2024"),
        (btn_2025, "2025"),
        (btn_2026, "2026"),
    ]

    html_container = html.Div(
        [
            dcc.Store(id=f"{btn_2020}-state", data=True, storage_type="session"),
            dcc.Store(id=f"{btn_2021}-state", data=False, storage_type="session"),
            dcc.Store(id=f"{btn_2022}-state", data=False, storage_type="session"),
            dcc.Store(id=f"{btn_2023}-state", data=False, storage_type="session"),
            dcc.Store(id=f"{btn_2024}-state", data=False, storage_type="session"),
            dcc.Store(id=f"{btn_2025}-state", data=False, storage_type="session"),
            dcc.Store(id=f"{btn_2026}-state", data=False, storage_type="session"),
            html.Div(
                [
                    html.Button(
                        id=button_id,
                        children=button_label,
                        n_clicks=0,
                        style=active_line_button if button_id == btn_2020 else line_buttons,
                    )
                    for button_id, button_label in year_buttons
                ],
                style={"display": "flex"},
            ),
        ],
        style={"height": "60px"},
    )
    
    @app.callback(
        [
            Output(btn_2020, "style"),
            Output(btn_2021, "style"),
            Output(btn_2022, "style"),
            Output(btn_2023, "style"),
            Output(btn_2024, "style"),
            Output(btn_2025, "style"),
            Output(btn_2026, "style"),
            Output(f"{btn_2020}-state", "data"),
            Output(f"{btn_2021}-state", "data"),
            Output(f"{btn_2022}-state", "data"),
            Output(f"{btn_2023}-state", "data"),
            Output(f"{btn_2024}-state", "data"),
            Output(f"{btn_2025}-state", "data"),
            Output(f"{btn_2026}-state", "data"),
        ],
        [
            Input(btn_2020, "n_clicks"),
            Input(btn_2021, "n_clicks"),
            Input(btn_2022, "n_clicks"),
            Input(btn_2023, "n_clicks"),
            Input(btn_2024, "n_clicks"),
            Input(btn_2025, "n_clicks"),
            Input(btn_2026, "n_clicks"),
        ],
    )
    def toggle_line_buttons(
        btn_2020_clicks,
        btn_2021_clicks,
        btn_2022_clicks,
        btn_2023_clicks,
        btn_2024_clicks,
        btn_2025_clicks,
        btn_2026_clicks,
    ):
        ctx = dash.callback_context
        if not ctx.triggered:
            button_id = btn_2020
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        styles = {}
        states = {}

        for button in [btn_2020, btn_2021, btn_2022, btn_2023, btn_2024, btn_2025, btn_2026]:
            if button == button_id:
                styles[button] = active_line_button
                states[button] = True
            else:
                styles[button] = line_buttons
                states[button] = False

        return (
            styles[btn_2020],
            styles[btn_2021],
            styles[btn_2022],
            styles[btn_2023],
            styles[btn_2024],
            styles[btn_2025],
            styles[btn_2026],
            states[btn_2020],
            states[btn_2021],
            states[btn_2022],
            states[btn_2023],
            states[btn_2024],
            states[btn_2025],
            states[btn_2026],
        )

    return html_container

if __name__ == "__main__":
    
    app.layout = html.Div(
        checklist_header(
            app, "btn_2020", "btn_2021", "btn_2022", "btn_2023", "btn_2024", "btn_2025", "btn_2026"
        )
    )
    app.run_server(debug=True, port=8051)
