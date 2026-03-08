from src.wps.mapping import production_mapping
import dash
from dash import Output, Input, dcc, html
import pandas as pd
from src.wps.graph_seag import chart_seasonality
from src.wps.graph_line import chart_trend
import plotly.graph_objects as go
from src.wps.graph_optionality import checklist_header
from app import app

from src.utils.variables import year_1_string, year_2_string, year_3_string, year_4_string, year_5_string, full_year_range_normal_string, full_year_range_last_five_years_string

from src.utils.data_loader import loader, get_seasonality_data_for_ids, get_line_data_for_ids


### data retrieval functions ############################################


def get_initial_data():
    """Load initial data"""
    return loader.get_filtered_data("wps_pivot", "2015-01-01")


### graph creation functions ###########################################


def create_loading_graph(graph_id):
    blank_graph = go.Figure().update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return html.Div(
        dcc.Graph(id=graph_id, figure=blank_graph), className="graph-container"
    )


### layout creation functions ###########################################


def create_layout(page_id, commodity, graph_sections_input):
    def generate_ids(page_id):
        return {
            key: f"{page_id}-{key}"
            for key in [
                "chart_toggle",
                "seasonality_buttons",
                "line_buttons_div",
                "toggle_seag_range",
                f"toggle_{year_1_string}",
                f"toggle_{year_2_string}",
                f"toggle_{year_3_string}",
                f"toggle_{year_4_string}",
                f"toggle_{year_5_string}",
                "btn_1m",
                "btn_3m",
                "btn_12m",
                "btn_36m",
                "btn_60m",
                "toggle_main_line",
                "toggle_ma_1m",
                "toggle_ma_3m",
                "toggle_ma_12m",
            ]
        }

    def create_graph_section(title, graph_ids):
        return html.Div(
            [
                html.H1(title, className="eia-weekly-header-title"),
                html.Div(
                    [create_loading_graph(graph_id) for graph_id in graph_ids],
                    className="eia-weekly-graph-container",
                ),
            ]
        )

    ids = generate_ids(page_id)
    return html.Div(
        [
            checklist_header(
                app,
                ids["chart_toggle"],
                ids["seasonality_buttons"],
                ids["line_buttons_div"],
                ids["toggle_seag_range"],
                ids[f"toggle_{year_1_string}"],
                ids[f"toggle_{year_2_string}"],
                ids[f"toggle_{year_3_string}"],
                ids[f"toggle_{year_4_string}"],
                ids[f"toggle_{year_5_string}"],
                ids["btn_1m"],
                ids["btn_3m"],
                ids["btn_12m"],
                ids["btn_36m"],
                ids["btn_60m"],
                ids["toggle_main_line"],
                ids["toggle_ma_1m"],
                ids["toggle_ma_3m"],
                ids["toggle_ma_12m"],
            ),
            html.Div(className="eia-weekly-top-spacing"),
            *[
                create_graph_section(f"{commodity} {title}", graph_ids)
                for title, graph_ids in graph_sections_input
            ],
        ],
        className="eia-weekly-graph-page-layout",
    )


### callback functions #################################################


def create_callbacks(app, page_id, num_graphs, idents):

    @app.callback(
        [Output(f"{page_id}-graph-{i}", "figure") for i in range(1, num_graphs + 1)],
        [
            Input(f"{page_id}-chart_toggle", "n_clicks"),
            Input(f"{page_id}-toggle_seag_range", "n_clicks"),
            Input(f"{page_id}-toggle_{year_1_string}", "n_clicks"),
            Input(f"{page_id}-toggle_{year_2_string}", "n_clicks"),
            Input(f"{page_id}-toggle_{year_3_string}", "n_clicks"),
            Input(f"{page_id}-toggle_{year_4_string}", "n_clicks"),
            Input(f"{page_id}-toggle_{year_5_string}", "n_clicks"),
            Input(f"{page_id}-btn_1m-state", "data"),
            Input(f"{page_id}-btn_3m-state", "data"),
            Input(f"{page_id}-btn_12m-state", "data"),
            Input(f"{page_id}-btn_36m-state", "data"),
            Input(f"{page_id}-btn_60m-state", "data"),
            Input(f"{page_id}-toggle_main_line", "n_clicks"),
            Input(f"{page_id}-toggle_ma_1m", "n_clicks"),
            Input(f"{page_id}-toggle_ma_3m", "n_clicks"),
            Input(f"{page_id}-toggle_ma_12m", "n_clicks"),
        ],
    )
    def update_graphs(
        chart_toggle,
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
        toggle_main_line,
        toggle_ma_1m,
        toggle_ma_3m,
        toggle_ma_12m,
    ):
        # Convert n_clicks to booleans (handles None from suppress_callback_exceptions)
        chart_toggle = ((chart_toggle or 0) % 2) == 0        # even=True (seasonality mode)
        toggle_seag_range = ((toggle_seag_range or 0) % 2) == 1  # odd=True (toggled)
        toggle_year_1 = ((toggle_year_1 or 0) % 2) == 1
        toggle_year_2 = ((toggle_year_2 or 0) % 2) == 1
        toggle_year_3 = ((toggle_year_3 or 0) % 2) == 1
        toggle_year_4 = ((toggle_year_4 or 0) % 2) == 1
        toggle_year_5 = ((toggle_year_5 or 0) % 2) == 1
        toggle_main_line = ((toggle_main_line or 0) % 2) == 0
        toggle_ma_1m = ((toggle_ma_1m or 0) % 2) == 1
        toggle_ma_3m = ((toggle_ma_3m or 0) % 2) == 1
        toggle_ma_12m = ((toggle_ma_12m or 0) % 2) == 1

        seag_data = get_seasonality_data_for_ids(tuple(idents))
        line_data = get_line_data_for_ids(tuple(idents))

        def create_chart(
            df,
            seag_data,
            id,
            chart_toggle,
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
            toggle_main_line,
            toggle_ma_1m,
            toggle_ma_3m,
            toggle_ma_12m,
        ):
            seag_data_individual = seag_data[seag_data["id"] == id]
            line_data_individual = line_data[["period", id]]

            if chart_toggle:
                return chart_seasonality(
                    seag_data_individual,
                    id,
                    toggle_seag_range,
                    toggle_year_1,
                    toggle_year_2,
                    toggle_year_3,
                    toggle_year_4,
                    toggle_year_5,
                )
            else:
                return chart_trend(
                    line_data_individual, id, btn_1m, btn_3m, btn_12m, btn_36m, btn_60m,
                    toggle_main_line,
                    toggle_ma_1m, toggle_ma_3m, toggle_ma_12m,
                )

        return [
            create_chart(
                line_data,
                seag_data,
                ident,
                chart_toggle,
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
                toggle_main_line,
                toggle_ma_1m,
                toggle_ma_3m,
                toggle_ma_12m,
            )
            for ident in idents
        ]
