from dash import html, dcc, callback, Output, Input
import dash_ag_grid as dag
from utils_wps.ag_calculations import DataProcessor
from utils.variables import default_start_date_eia_wps_table, default_end_date_eia_wps_table

# Initialize the data processor
processor = DataProcessor()

# Default date range
default_start_date = default_start_date_eia_wps_table
default_end_date = default_end_date_eia_wps_table

# Process data and column definitions
df, columnDefinitions = processor.get_data(default_start_date, default_end_date)

# AgGrid component
grid = dag.AgGrid(
    id="export-data-grid",
    columnDefs=columnDefinitions,
    defaultColDef={
        "filter": True,
        "floatingFilter": True,
        "sortable": False,
    },
    rowData=df.to_dict('records'),
    csvExportParams={
        "fileName": "eia_stats_data.csv",
    },
    dashGridOptions={
        "rowSelection": "single",
        "animateRows": False,
    },
    className="ag-theme-alpine",
    style={"height": "85vh", "width": "100%"}
)

# Page layout for page 2_10
layout = html.Div([
    # Header and Grid Section here...
    html.Div([
        html.Div([
            html.H1("EIA Stats Table", style={"fontSize": "3em", "color": "#c00000", "margin": "0"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-start"}),

        html.Div([
            dcc.DatePickerRange(
                id='date-picker-range',
                min_date_allowed='2010-01-01',
                max_date_allowed='2030-12-31',
                initial_visible_month=default_start_date,
                start_date=default_start_date,
                end_date=default_end_date,
                display_format='YYYY-MM-DD',
                style={"padding": "10px"},
                className="custom-date-picker"
            ),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "center"}),

        html.Div([
            html.Button("Download CSV", id="csv-button", n_clicks=0, style={"fontSize": "1.3em", "padding": "10px", "margin": "0", "backgroundColor": "white", "border": "2px solid #f0f0f0", "color": "#c00000", "cursor": "pointer"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"})
    ], style={"height": "6vh", "display": "flex", "alignItems": "center", "justifyContent": "space-between", "padding": "0 0px"}),

    html.Div([grid], style={"height": "100%", "width": "100%", "display": "flex", "flexDirection": "column"})
], style={"height": "100vh", "display": "flex", "flexDirection": "column", "paddingRight": "0px"})

# Callbacks for page 2_10
@callback(
    Output("export-data-grid", "exportDataAsCsv"),
    Input("csv-button", "n_clicks"),
)
def export_data_as_csv(n_clicks):
    if n_clicks > 0:
        return True
    return False

@callback(
    [Output("export-data-grid", "rowData"),
     Output("export-data-grid", "columnDefs")],
    [Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")]
)
def update_grid_data(start_date, end_date):
    df, updated_columnDefinitions = processor.get_data(start_date, end_date)
    return df.to_dict('records'), updated_columnDefinitions