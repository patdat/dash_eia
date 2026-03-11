import dash_bootstrap_components as dbc
from dash import html, Output, Input
from app import app
from src.wps.graph_optionality import checklist_header
from src.utils.variables import (
    year_1_string, year_2_string, year_3_string,
    year_4_string, year_5_string,
)
import pages.archived.page2_2, pages.archived.page2_3, pages.archived.page2_4
import pages.archived.page2_5, pages.archived.page2_6, pages.archived.page2_7
import pages.archived.page2_8, pages.archived.page2_9

# Page IDs for the 8 WPS commodity pages
PAGE_IDS = [f"page2_{i}" for i in range(2, 10)]

# Build shared control bar with "combined" namespace
shared_ids = {
    key: f"combined-{key}"
    for key in [
        "chart_toggle", "seasonality_buttons", "line_buttons_div",
        "toggle_seag_range",
        f"toggle_{year_1_string}", f"toggle_{year_2_string}",
        f"toggle_{year_3_string}", f"toggle_{year_4_string}",
        f"toggle_{year_5_string}",
        "btn_1m", "btn_3m", "btn_12m", "btn_36m", "btn_60m",
        "toggle_main_line", "toggle_ma_1m", "toggle_ma_3m", "toggle_ma_12m",
    ]
}

shared_controls = checklist_header(
    app,
    shared_ids["chart_toggle"],
    shared_ids["seasonality_buttons"],
    shared_ids["line_buttons_div"],
    shared_ids["toggle_seag_range"],
    shared_ids[f"toggle_{year_1_string}"],
    shared_ids[f"toggle_{year_2_string}"],
    shared_ids[f"toggle_{year_3_string}"],
    shared_ids[f"toggle_{year_4_string}"],
    shared_ids[f"toggle_{year_5_string}"],
    shared_ids["btn_1m"],
    shared_ids["btn_3m"],
    shared_ids["btn_12m"],
    shared_ids["btn_36m"],
    shared_ids["btn_60m"],
    shared_ids["toggle_main_line"],
    shared_ids["toggle_ma_1m"],
    shared_ids["toggle_ma_3m"],
    shared_ids["toggle_ma_12m"],
)

# Controls to sync from shared → all 8 pages
SYNC_CONTROLS = [
    "chart_toggle", "toggle_seag_range",
    f"toggle_{year_1_string}", f"toggle_{year_2_string}",
    f"toggle_{year_3_string}", f"toggle_{year_4_string}",
    f"toggle_{year_5_string}",
    "btn_1m", "btn_3m", "btn_12m", "btn_36m", "btn_60m",
    "toggle_main_line", "toggle_ma_1m", "toggle_ma_3m", "toggle_ma_12m",
]

# Register sync callbacks: shared control n_clicks → all 8 pages' matching controls
for ctrl in SYNC_CONTROLS:
    @app.callback(
        [Output(f"{pid}-{ctrl}", "n_clicks") for pid in PAGE_IDS],
        Input(f"combined-{ctrl}", "n_clicks"),
        prevent_initial_call=True,
    )
    def _sync(n, _ctrl=ctrl):
        return [n] * 8

# Tab definitions
tabs = [
    ("Crude", pages.archived.page2_2.layout),
    ("Gasoline", pages.archived.page2_3.layout),
    ("Distillate", pages.archived.page2_4.layout),
    ("Jet", pages.archived.page2_5.layout),
    ("Fuel Oil", pages.archived.page2_6.layout),
    ("C3/C3=", pages.archived.page2_7.layout),
    ("Products Supplied", pages.archived.page2_8.layout),
    ("Refining", pages.archived.page2_9.layout),
]

layout = html.Div([
    html.Div(shared_controls, className="wps-combined-shared-controls"),
    dbc.Tabs(
        [dbc.Tab(content, label=label) for label, content in tabs],
        id="wps-combined-tabs",
        active_tab="tab-0",
    )
])
