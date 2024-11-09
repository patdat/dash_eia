import dash
from dash import html, Input, Output, dcc
import plotly.graph_objects as go
import pandas as pd
from utils_steo.graph_optionality import checklist_header
from utils_steo.chart_dpr import chart_dpr
from app import app



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


def create_layout(page_id, commodity, graph_sections_input):
    def generate_ids(page_id):
        return {
            key: f"{page_id}-{key}"
            for key in [
                "btn_2020",
                "btn_2021",
                "btn_2022",
                "btn_2023",
                "btn_2024",
                "btn_2025",
            ]
        }

    def create_graph_section(title, graph_ids):
        return html.Div(
            [
                html.H1(title, className="eia-weekly-header-title"),
                html.Div(
                    [create_loading_graph(graph_id) for graph_id in graph_ids],
                    className="eia-dpr-graph-container",
                ),
            ]
        )

    def create_graph_section(title, graph_ids):
        return html.Div(
            [
                html.H1(title, className="eia-weekly-header-title"),
                html.Div(
                    [create_loading_graph(graph_id) for graph_id in graph_ids],
                    className="eia-dpr-graph-container",
                ),
            ]
        )

    ids = generate_ids(page_id)

    return html.Div(
        [
            checklist_header(
                app,
                ids["btn_2020"],
                ids["btn_2021"],
                ids["btn_2022"],
                ids["btn_2023"],
                ids["btn_2024"],
                ids["btn_2025"],
            ),
            html.Div(className="eia-weekly-top-spacing"),
            *[
                create_graph_section(f"{commodity} {title}", graph_ids)
                for title, graph_ids in graph_sections_input
            ],
        ],
        className="eia-weekly-graph-page-layout",
    )


def create_callbacks(app, page_id, num_graphs, idents, region_dct):

    @app.callback(
        [Output(f"{page_id}-graph-{i}", "figure") for i in range(1, num_graphs + 1)],
        [
            Input(f"{page_id}-btn_2020-state", "data"),
            Input(f"{page_id}-btn_2021-state", "data"),
            Input(f"{page_id}-btn_2022-state", "data"),
            Input(f"{page_id}-btn_2023-state", "data"),
            Input(f"{page_id}-btn_2024-state", "data"),
            Input(f"{page_id}-btn_2025-state", "data"),
        ],
    )
    def update_graphs(
        btn_2020,
        btn_2021,
        btn_2022,
        btn_2023,
        btn_2024,
        btn_2025,
    ):
        return [
            chart_dpr(
                ident,
                region_dct,
                btn_2020,
                btn_2021,
                btn_2022,
                btn_2023,
                btn_2024,
                btn_2025,
            )
            for ident in idents
        ]
        
if __name__ == "__main__":
    app.layout = create_layout("page3_1", "commodity", [("title", ["graph-1"])])
    app.run_server(debug=True, port=8051)        
