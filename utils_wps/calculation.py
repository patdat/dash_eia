from utils_wps.mapping import production_mapping
import dash
from dash import Output, Input, dcc, html
import pandas as pd
from utils_wps.graph_seag import chart_seasonality
from utils_wps.graph_line import chart_trend
import plotly.graph_objects as go
from utils_wps.graph_optionality import checklist_header
from app import app

from utils.variables import year_1_string, year_2_string, year_3_string, full_year_range_normal_string, full_year_range_last_five_years_string


### data retrieval functions ############################################


def get_initial_data():
    df = pd.read_feather("./data/wps/wps_gte_2015_pivot.feather")
    df["period"] = pd.to_datetime(df["period"])
    return df[df["period"] > "2015-01-01"].reset_index(drop=True)


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
                "btn_1m",
                "btn_6m",
                "btn_12m",
                "btn_36m",
                "btn_all",
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
                ids["btn_1m"],
                ids["btn_6m"],
                ids["btn_12m"],
                ids["btn_36m"],
                ids["btn_all"],
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
            Input(f"{page_id}-chart_toggle-state", "data"),
            Input(f"{page_id}-toggle_seag_range-state", "data"),
            Input(f"{page_id}-toggle_{year_1_string}-state", "data"),
            Input(f"{page_id}-toggle_{year_2_string}-state", "data"),
            Input(f"{page_id}-toggle_{year_3_string}-state", "data"),
            Input(f"{page_id}-btn_1m-state", "data"),
            Input(f"{page_id}-btn_6m-state", "data"),
            Input(f"{page_id}-btn_12m-state", "data"),
            Input(f"{page_id}-btn_36m-state", "data"),
            Input(f"{page_id}-btn_all-state", "data"),
        ],
    )
    def update_graphs(
        chart_toggle,
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

        seag_data = pd.read_feather("./data/wps/seasonality_data.feather")
        seag_data = seag_data[seag_data["id"].isin(idents)]
        line_data = pd.read_feather("./data/wps/graph_line_data.feather")
        line_data["period"] = pd.to_datetime(line_data["period"])
        line_data = line_data[["period"] + idents]

        def create_chart(
            df,
            seag_data,
            id,
            chart_toggle,
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
                )
            else:
                return chart_trend(
                    line_data_individual, id, btn_1m, btn_6m, btn_12m, btn_36m, btn_all
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
                btn_1m,
                btn_6m,
                btn_12m,
                btn_36m,
                btn_all,
            )
            for ident in idents
        ]
