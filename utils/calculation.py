from utils.mapping import production_mapping
import dash
from dash import Output, Input, dcc, html
import pandas as pd
from utils.graph_seag import chart_seasonality
from utils.graph_line import chart_trend
import plotly.graph_objects as go
from utils.graph_optionality import checklist_header
from app import app

### data retrieval functions ############################################

def get_initial_data():
    df = pd.read_feather("./data/wps_gte_2015_pivot.feather")
    df["period"] = pd.to_datetime(df["period"])
    return df[df["period"] > "2015-01-01"].reset_index(drop=True)

def get_data(df, id):
    filtered_df = df[["period", id]].rename(columns={id: "value"})
    mapping_name = production_mapping.get(id).replace("(kbd)", "(kb/d)")
    stocks_in_name = "stocks" in mapping_name.lower()
    if stocks_in_name:
        filtered_df["value"] /= 1000
        mapping_name = mapping_name.replace("(kb)", "(mb)").lower().replace("thousands", "Millions")
    return filtered_df, mapping_name, stocks_in_name

### graph creation functions ###########################################

def create_loading_graph(graph_id):
    blank_graph = go.Figure().update_layout(
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
    )
    return html.Div(dcc.Graph(id=graph_id, figure=blank_graph), className="graph-container")

### layout creation functions ###########################################

def create_layout(page_id, commodity, graph_sections_input):
    def generate_ids(page_id):
        return {key: f"{page_id}-{key}" for key in [
            "chart_toggle", "seasonality_buttons", "line_buttons_div", 
            "toggle_seag_range", "toggle_2022", "toggle_2023", "toggle_2024", 
            "btn_1m", "btn_6m", "btn_12m", "btn_36m", "btn_all"]}

    def create_graph_section(title, graph_ids):
        return html.Div([
            html.H1(title, className="eia-weekly-header-title"),
            html.Div([create_loading_graph(graph_id) for graph_id in graph_ids], className="eia-weekly-graph-container")
        ])

    ids = generate_ids(page_id)
    return html.Div([
        checklist_header(app, ids["chart_toggle"], ids["seasonality_buttons"], ids["line_buttons_div"], ids["toggle_seag_range"], ids["toggle_2022"], ids["toggle_2023"], ids["toggle_2024"], ids["btn_1m"], ids["btn_6m"], ids["btn_12m"], ids["btn_36m"], ids["btn_all"]),
        html.Div(className="eia-weekly-top-spacing"),
        *[create_graph_section(f"{commodity} {title}", graph_ids) for title, graph_ids in graph_sections_input]
    ], className="eia-weekly-graph-page-layout")

### callback functions #################################################

def create_callbacks(app, page_id, num_graphs, idents):



    @app.callback(
        [Output(f"{page_id}-graph-{i}", "figure") for i in range(1, num_graphs + 1)],
        [Input(f"{page_id}-chart_toggle-state", "data"),
         Input(f"{page_id}-toggle_seag_range-state", "data"),
         Input(f"{page_id}-toggle_2022-state", "data"),
         Input(f"{page_id}-toggle_2023-state", "data"),
         Input(f"{page_id}-toggle_2024-state", "data"),
         Input(f"{page_id}-btn_1m-state", "data"),
         Input(f"{page_id}-btn_6m-state", "data"),
         Input(f"{page_id}-btn_12m-state", "data"),
         Input(f"{page_id}-btn_36m-state", "data"),
         Input(f"{page_id}-btn_all-state", "data"),]
    )
    def update_graphs(chart_toggle, toggle_seag_range, toggle_2022, toggle_2023, toggle_2024, btn_1m, btn_6m, btn_12m, btn_36m, btn_all):

        raw_data = pd.read_feather('./data/wps_gte_2015_pivot.feather')
        raw_data = raw_data[['period'] + idents]    
        seag_data = pd.read_feather('data/seasonality_data.feather')
        seag_data = seag_data[seag_data['id'].isin(idents)]

        # ctx = dash.callback_context
        # if not ctx.triggered:
        #     print("No changes triggered the callback.")
        #     return [dash.no_update] * num_graphs

        # triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]
        # print(f"Callback triggered by: {triggered_input}")

        # if triggered_input == 'data-store':
        #     print("Data store got updated.")

            
        def create_chart(df, seag_data, id, chart_toggle, toggle_seag_range, toggle_2022, toggle_2023, toggle_2024, btn_1m, btn_6m, btn_12m, btn_36m, btn_all):
            filtered_df, mapping_name, stocks_in_name = get_data(df, id)
            
            if chart_toggle:
                # return chart_seasonality(filtered_df, mapping_name, stocks_in_name, toggle_seag_range, toggle_2022, toggle_2023, toggle_2024)
                return chart_seasonality(seag_data, id, toggle_seag_range, toggle_2022,toggle_2023,toggle_2024)
            else:
                return chart_trend(filtered_df, mapping_name, stocks_in_name, btn_1m, btn_6m, btn_12m, btn_36m, btn_all)
            
        return [create_chart(raw_data, seag_data, ident, chart_toggle, toggle_seag_range, toggle_2022, toggle_2023, toggle_2024, btn_1m, btn_6m, btn_12m, btn_36m, btn_all) for ident in idents]
