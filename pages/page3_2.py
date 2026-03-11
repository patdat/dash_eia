from dash import html, dcc, callback, Output, Input, ctx, State
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import dash_daq as daq
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.utils.data_loader import loader
from src.utils.colors import RED

# Import page3_3 so its callbacks get registered and we can use its layout
import pages.page3_3 as page3_3_module

# ── DPR Data Loading ─────────────────────────────────────────────────────────

df = loader.load_steo_dpr_data()
mapping_df = loader.load_dpr_mapping()

metadata_cols = ['id', 'name', 'release_date', 'uom']
date_columns = [col for col in df.columns if col not in metadata_cols]

df_melted = loader.load_processed_dpr_data(region=None)

release_dates = sorted(df_melted['release_date'].unique(), reverse=True)
current_release_index = 0

def prepare_data(release_date, show_evolution=False, prior_release_date=None):
    """Prepare data for the selected release date"""
    filtered_df = df_melted[df_melted['release_date'] == release_date].copy()

    pivot_df = filtered_df.pivot_table(
        index=['id', 'name', 'region', 'uom'],
        columns='delivery_month',
        values='value',
        aggfunc='first'
    ).reset_index()

    delivery_months = sorted([col for col in pivot_df.columns if isinstance(col, pd.Timestamp)])

    if show_evolution and prior_release_date is not None:
        prior_filtered = df_melted[df_melted['release_date'] == prior_release_date].copy()
        prior_pivot = prior_filtered.pivot_table(
            index=['id', 'name', 'region', 'uom'],
            columns='delivery_month',
            values='value',
            aggfunc='first'
        ).reset_index()

        for col in delivery_months:
            if col in pivot_df.columns and col in prior_pivot.columns:
                merged = pivot_df[['id', 'name', 'region', 'uom']].copy()
                merged['current'] = pivot_df[col]
                merged['prior'] = pivot_df[['id']].merge(
                    prior_pivot[['id', col]],
                    on='id',
                    how='left'
                )[col]
                pivot_df[col] = merged['current'] - merged['prior']

    for col in delivery_months:
        if col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].round(2)

    return pivot_df, delivery_months

def create_column_defs(delivery_months):
    """Create AG Grid column definitions"""
    columnDefs = []

    columnDefs.append({
        "headerName": "ID",
        "field": "id",
        "pinned": "left",
        "width": 120,
        "filter": "agTextColumnFilter",
        "floatingFilter": True
    })

    columnDefs.append({
        "headerName": "Name",
        "field": "name",
        "pinned": "left",
        "width": 700,
        "filter": "agTextColumnFilter",
        "floatingFilter": True,
        "wrapText": True,
        "autoHeight": True
    })

    columnDefs.append({
        "headerName": "Region",
        "field": "region",
        "pinned": "left",
        "width": 190,
        "filter": "agTextColumnFilter",
        "floatingFilter": True
    })

    columnDefs.append({
        "headerName": "UOM",
        "field": "uom",
        "pinned": "left",
        "width": 96,
        "filter": "agTextColumnFilter",
        "floatingFilter": True
    })

    for month in delivery_months:
        header_name = month.strftime('%b-%y')
        field_name = month.strftime('%Y-%m-%d')

        columnDefs.append({
            "headerName": header_name,
            "field": field_name,
            "width": 103,
            "filter": "agNumberColumnFilter",
            "floatingFilter": True,
            "sortable": False,
            "valueFormatter": {"function": "params.value === 0 || params.value === null || params.value === undefined ? '-' : d3.format('.2f')(params.value)"},
            "cellStyle": {"textAlign": "right"},
            "headerClass": "ag-right-aligned-header"
        })

    return columnDefs

def convert_to_serializable(df, delivery_months):
    """Convert dataframe to a format that can be serialized for AG Grid"""
    result_df = df.copy()

    for month in delivery_months:
        if month in result_df.columns:
            month_str = month.strftime('%Y-%m-%d')
            result_df[month_str] = result_df[month]
            if month_str != month:
                result_df = result_df.drop(columns=[month])

    return result_df

# Initialize with most recent release date
current_df, delivery_months = prepare_data(release_dates[0])
current_df_serializable = convert_to_serializable(current_df, delivery_months)
columnDefinitions = create_column_defs(delivery_months)

# ── DPR Tab Layout ───────────────────────────────────────────────────────────

dpr_layout = html.Div([
    # Header section
    html.Div([
        html.Div([
            html.H1("STEO DPR", style={"fontSize": "3em", "color": RED, "margin": "0"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-start"}),

        html.Div([
            html.Button("◄", id="prev-release-btn", n_clicks=0,
                       style={"fontSize": "1.5em", "padding": "5px 15px", "margin": "0 5px",
                              "backgroundColor": "white", "border": f"2px solid {RED}",
                              "color": RED, "cursor": "pointer", "borderRadius": "4px"}),
            html.Div(id="release-date-display",
                    children=f"Release: {release_dates[0].strftime('%B %Y')}",
                    style={"fontSize": "1.3em", "padding": "0 20px", "color": "#333"}),
            html.Button("►", id="next-release-btn", n_clicks=0,
                       style={"fontSize": "1.5em", "padding": "5px 15px", "margin": "0 5px",
                              "backgroundColor": "white", "border": f"2px solid {RED}",
                              "color": RED, "cursor": "pointer", "borderRadius": "4px"}),
            html.Div([
                html.Label("Evolution: ", style={"marginLeft": "30px", "marginRight": "10px", "fontSize": "1.1em"}),
                daq.BooleanSwitch(
                    id="evolution-switch",
                    on=False,
                    color=RED,
                    disabled=False
                )
            ], style={"display": "flex", "alignItems": "center", "marginLeft": "20px"})
        ], style={"flex": "2", "display": "flex", "alignItems": "center", "justifyContent": "center"}),

        html.Div([
            html.Button("📊 Graphs", id="graph-view-btn", n_clicks=0,
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0 10px",
                              "backgroundColor": "white", "border": f"2px solid {RED}",
                              "color": RED, "cursor": "pointer"}),
            html.Button("Download CSV", id="csv-button-dpr", n_clicks=0,
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0",
                              "backgroundColor": "white", "border": "2px solid #f0f0f0",
                              "color": RED, "cursor": "pointer"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"})
    ], style={"height": "6vh", "display": "flex", "alignItems": "center",
              "justifyContent": "space-between", "padding": "0 20px"}),

    # Main content area with AG Grid and Graphs
    html.Div([
        # AG Grid container
        html.Div([
            dag.AgGrid(
                id="steo-dpr-grid",
                columnDefs=columnDefinitions,
                defaultColDef={
                    "sortable": True,
                    "resizable": True,
                },
                rowData=current_df_serializable.to_dict('records'),
                csvExportParams={
                    "fileName": "steo_dpr_data.csv",
                },
                dashGridOptions={
                    "rowSelection": "single",
                    "animateRows": False,
                    "domLayout": "normal",
                },
                className="ag-theme-alpine",
                style={"height": "100%", "width": "100%"}
            )
        ], id="grid-container", style={"height": "100%", "width": "100%", "transition": "width 0.3s ease"}),

        # Graph panel (initially hidden)
        html.Div([
            html.Div([
                html.H3("Data Visualization", style={"margin": "10px 0", "color": RED, "fontSize": "1.5em"}),
                html.Button("✕", id="close-graph-btn", n_clicks=0,
                           style={"position": "absolute", "top": "10px", "right": "10px",
                                  "background": "transparent", "border": "none",
                                  "fontSize": "1.5em", "cursor": "pointer", "color": "#666"})
            ], style={"position": "relative", "padding": "0 20px", "height": "50px"}),

            # Line graph
            html.Div([
                html.H4("Historical Trend", style={"margin": "5px 0", "fontSize": "1.1em", "color": "#333"}),
                dcc.Graph(id="line-graph", style={"height": "calc(100% - 30px)"})
            ], style={"padding": "0 20px", "height": "calc(50% - 25px)"}),

            # Seasonality graph
            html.Div([
                html.H4("Seasonality (All Years)", style={"margin": "5px 0", "fontSize": "1.1em", "color": "#333"}),
                dcc.Graph(id="seasonality-graph", style={"height": "calc(100% - 30px)"})
            ], style={"padding": "0 20px", "height": "calc(50% - 25px)"})
        ], id="graph-panel", style={"height": "100%", "width": "0%", "backgroundColor": "#f8f8f8",
                                    "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                                    "transition": "width 0.3s ease", "display": "none"}),
    ], style={"height": "85vh", "display": "flex", "padding": "0 20px"}),

    # Hidden stores
    dcc.Store(id='current-release-index', data=0),
    dcc.Store(id='graph-view-state', data=False)

], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

# ── Combined Tabbed Layout ───────────────────────────────────────────────────

layout = html.Div([
    dbc.Tabs([
        dbc.Tab(dpr_layout, label="STEO DPR Table"),
        dbc.Tab(page3_3_module.layout, label="STEO DPR Other"),
    ], id="dpr-table-tabs", active_tab="tab-0")
])

# ── DPR Callbacks ────────────────────────────────────────────────────────────

@callback(
    Output("steo-dpr-grid", "exportDataAsCsv"),
    Input("csv-button-dpr", "n_clicks"),
)
def export_data_as_csv(n_clicks):
    if n_clicks > 0:
        return True
    return False

@callback(
    [Output("steo-dpr-grid", "rowData"),
     Output("steo-dpr-grid", "columnDefs"),
     Output("release-date-display", "children"),
     Output("current-release-index", "data"),
     Output("prev-release-btn", "disabled"),
     Output("next-release-btn", "disabled"),
     Output("evolution-switch", "disabled")],
    [Input("prev-release-btn", "n_clicks"),
     Input("next-release-btn", "n_clicks"),
     Input("evolution-switch", "on")],
    [State("current-release-index", "data")]
)
def update_release_date(prev_clicks, next_clicks, evolution_on, current_index):
    if not ctx.triggered:
        new_index = 0
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "prev-release-btn":
            new_index = min(current_index + 1, len(release_dates) - 1)
        elif button_id == "next-release-btn":
            new_index = max(current_index - 1, 0)
        else:
            new_index = current_index

    selected_release = release_dates[new_index]

    can_show_evolution = new_index < len(release_dates) - 1
    prior_release = release_dates[new_index + 1] if can_show_evolution else None

    if evolution_on and can_show_evolution:
        updated_df, delivery_months = prepare_data(selected_release, show_evolution=True, prior_release_date=prior_release)
        evolution_text = f" (vs {prior_release.strftime('%B %Y')})"
    else:
        updated_df, delivery_months = prepare_data(selected_release, show_evolution=False)
        evolution_text = ""

    updated_df_serializable = convert_to_serializable(updated_df, delivery_months)
    updated_columnDefs = create_column_defs(delivery_months)

    display_text = f"Release: {selected_release.strftime('%B %Y')}{evolution_text}"

    prev_disabled = (new_index >= len(release_dates) - 1)
    next_disabled = (new_index <= 0)
    evolution_disabled = not can_show_evolution

    return (updated_df_serializable.to_dict('records'),
            updated_columnDefs,
            display_text,
            new_index,
            prev_disabled,
            next_disabled,
            evolution_disabled)

@callback(
    [Output("grid-container", "style"),
     Output("graph-panel", "style"),
     Output("graph-view-state", "data")],
    [Input("graph-view-btn", "n_clicks"),
     Input("close-graph-btn", "n_clicks")],
    [State("graph-view-state", "data")]
)
def toggle_graph_panel(graph_btn_clicks, close_btn_clicks, graph_state):
    if not ctx.triggered:
        return ({"height": "100%", "width": "100%", "transition": "width 0.3s ease"},
                {"height": "100%", "width": "0%", "backgroundColor": "#f8f8f8",
                 "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                 "transition": "width 0.3s ease", "display": "none"},
                False)

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "graph-view-btn":
        new_state = not graph_state
    elif button_id == "close-graph-btn":
        new_state = False
    else:
        new_state = graph_state

    if new_state:
        grid_style = {"height": "100%", "width": "70%", "transition": "width 0.3s ease"}
        graph_style = {"height": "100%", "width": "30%", "backgroundColor": "#f8f8f8",
                      "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                      "transition": "width 0.3s ease", "display": "block"}
    else:
        grid_style = {"height": "100%", "width": "100%", "transition": "width 0.3s ease"}
        graph_style = {"height": "100%", "width": "0%", "backgroundColor": "#f8f8f8",
                      "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                      "transition": "width 0.3s ease", "display": "none"}

    return grid_style, graph_style, new_state

@callback(
    [Output("line-graph", "figure"),
     Output("seasonality-graph", "figure")],
    [Input("steo-dpr-grid", "selectedRows"),
     Input("current-release-index", "data")]
)
def update_graphs(selected_rows, current_index):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        title="Select a row to view data",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=None,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    if not selected_rows or len(selected_rows) == 0:
        return empty_fig, empty_fig

    selected_row = selected_rows[0]
    item_id = selected_row.get('id')
    item_name = selected_row.get('name', '')
    item_uom = selected_row.get('uom', '')

    item_data_all = df_melted[df_melted['id'] == item_id].copy()

    line_fig = go.Figure()

    import plotly.express as px
    colors = px.colors.qualitative.Set1 + px.colors.qualitative.Set2

    for idx, release in enumerate(sorted(item_data_all['release_date'].unique(), reverse=True)):
        release_data = item_data_all[item_data_all['release_date'] == release].copy()
        release_data = release_data.sort_values('delivery_month')

        line_style = 'solid' if release == release_dates[current_index] else 'dash'
        line_width = 2.5 if release == release_dates[current_index] else 1.5

        line_fig.add_trace(go.Scatter(
            x=release_data['delivery_month'],
            y=release_data['value'],
            mode='lines+markers',
            name=f"Release: {release.strftime('%b %Y')}",
            line=dict(color=colors[idx % len(colors)], width=line_width, dash=line_style),
            marker=dict(size=5 if release == release_dates[current_index] else 4)
        ))

    line_fig.update_layout(
        title=f"{item_name} ({item_uom}) - All Releases",
        xaxis_title="Date",
        yaxis_title=item_uom,
        hovermode='x unified',
        height=None,
        margin=dict(l=50, r=20, t=40, b=60),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=True, gridcolor='lightgrey', gridwidth=1,
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            showline=True, linecolor='black', linewidth=1
        ),
        yaxis=dict(
            showgrid=True, gridcolor='lightgrey', gridwidth=1,
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            showline=True, linecolor='black', linewidth=1
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.2,
            xanchor="center", x=0.5, font=dict(size=9)
        )
    )

    selected_release = release_dates[current_index]
    item_data = item_data_all[item_data_all['release_date'] == selected_release].copy()

    if len(item_data) > 0:
        item_data['year'] = item_data['delivery_month'].dt.year
        item_data['month'] = item_data['delivery_month'].dt.month

        seasonality_fig = go.Figure()

        years = sorted(item_data['year'].unique(), reverse=True)

        import plotly.express as px
        colors = px.colors.qualitative.Set1 + px.colors.qualitative.Set2

        for idx, year in enumerate(years):
            year_data = item_data[item_data['year'] == year].sort_values('month')
            seasonality_fig.add_trace(go.Scatter(
                x=year_data['month'],
                y=year_data['value'],
                mode='lines+markers',
                name=str(year),
                marker=dict(size=6),
                line=dict(color=colors[idx % len(colors)], width=2)
            ))

        seasonality_fig.update_layout(
            title=f"Seasonality Pattern - {item_name} (All Years)",
            xaxis=dict(
                title="Month",
                tickmode='array',
                tickvals=list(range(1, 13)),
                ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                showgrid=True, gridcolor='lightgrey', gridwidth=1,
                zeroline=True, zerolinecolor='black', zerolinewidth=1,
                showline=True, linecolor='black', linewidth=1
            ),
            yaxis=dict(
                title=item_uom,
                showgrid=True, gridcolor='lightgrey', gridwidth=1,
                zeroline=True, zerolinecolor='black', zerolinewidth=1,
                showline=True, linecolor='black', linewidth=1
            ),
            hovermode='x unified',
            height=None,
            margin=dict(l=50, r=20, t=40, b=40),
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.25,
                xanchor="center", x=0.5, font=dict(size=10)
            )
        )
    else:
        seasonality_fig = empty_fig

    return line_fig, seasonality_fig
