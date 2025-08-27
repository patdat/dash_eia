from dash import html, dcc, callback, Output, Input, ctx, State
import dash_ag_grid as dag
import dash_daq as daq
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Load data and mapping
df = pd.read_feather('data/steo/steo_pivot_dpr_other.feather')
mapping_df = pd.read_csv('lookup/steo/mapping_dpr_other.csv')

# Get date columns (all columns that are not metadata)
metadata_cols = ['id', 'name', 'release_date', 'uom']
date_columns = [col for col in df.columns if col not in metadata_cols]

# Melt the dataframe to have delivery_month as a column
df_melted = pd.melt(df, 
                    id_vars=metadata_cols,
                    value_vars=date_columns,
                    var_name='delivery_month',
                    value_name='value')

# Convert delivery_month to datetime
df_melted['delivery_month'] = pd.to_datetime(df_melted['delivery_month'])

# Merge with mapping to get region information
df_melted = df_melted.merge(mapping_df[['id', 'region']], on='id', how='left')

# Get unique release dates sorted (most recent first)
release_dates = sorted(df_melted['release_date'].unique(), reverse=True)
current_release_index = 0  # Start with most recent

def prepare_data(release_date, show_evolution=False, prior_release_date=None):
    """Prepare data for the selected release date"""
    # Filter data for the selected release date
    filtered_df = df_melted[df_melted['release_date'] == release_date].copy()
    
    # Pivot back to wide format for display
    pivot_df = filtered_df.pivot_table(
        index=['id', 'name', 'region', 'uom'],
        columns='delivery_month',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Get the delivery months for this release
    delivery_months = sorted([col for col in pivot_df.columns if isinstance(col, pd.Timestamp)])
    
    # If evolution mode is on and we have a prior release
    if show_evolution and prior_release_date is not None:
        # Get prior release data
        prior_filtered = df_melted[df_melted['release_date'] == prior_release_date].copy()
        prior_pivot = prior_filtered.pivot_table(
            index=['id', 'name', 'region', 'uom'],
            columns='delivery_month',
            values='value',
            aggfunc='first'
        ).reset_index()
        
        # Calculate differences for each delivery month
        for col in delivery_months:
            if col in pivot_df.columns and col in prior_pivot.columns:
                # Merge on index columns to align data
                merged = pivot_df[['id', 'name', 'region', 'uom']].copy()
                merged['current'] = pivot_df[col]
                merged['prior'] = pivot_df[['id']].merge(
                    prior_pivot[['id', col]], 
                    on='id', 
                    how='left'
                )[col]
                # Calculate difference
                pivot_df[col] = merged['current'] - merged['prior']
    
    # Round numeric values to 2 decimal places
    for col in delivery_months:
        if col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].round(2)
    
    return pivot_df, delivery_months

def create_column_defs(delivery_months):
    """Create AG Grid column definitions"""
    columnDefs = []
    
    # Fixed columns (pinned to left)
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
    
    # Delivery month columns (scrollable)
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
    
    # Convert timestamp columns to string format
    for month in delivery_months:
        if month in result_df.columns:
            # Convert column name to string format
            month_str = month.strftime('%Y-%m-%d')
            result_df[month_str] = result_df[month]
            if month_str != month:
                result_df = result_df.drop(columns=[month])
    
    return result_df

# Initialize with most recent release date
current_df, delivery_months = prepare_data(release_dates[0])
current_df_serializable = convert_to_serializable(current_df, delivery_months)
columnDefinitions = create_column_defs(delivery_months)

# Page layout
layout = html.Div([
    # Header section
    html.Div([
        html.Div([
            html.H1("STEO DPR Other Data Table", style={"fontSize": "3em", "color": "#c00000", "margin": "0"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-start"}),
        
        html.Div([
            html.Button("◄", id="prev-release-btn-other", n_clicks=0, 
                       style={"fontSize": "1.5em", "padding": "5px 15px", "margin": "0 5px",
                              "backgroundColor": "white", "border": "2px solid #c00000",
                              "color": "#c00000", "cursor": "pointer", "borderRadius": "4px"}),
            html.Div(id="release-date-display-other", 
                    children=f"Release: {release_dates[0].strftime('%B %Y')}",
                    style={"fontSize": "1.3em", "padding": "0 20px", "color": "#333"}),
            html.Button("►", id="next-release-btn-other", n_clicks=0,
                       style={"fontSize": "1.5em", "padding": "5px 15px", "margin": "0 5px",
                              "backgroundColor": "white", "border": "2px solid #c00000",
                              "color": "#c00000", "cursor": "pointer", "borderRadius": "4px"}),
            html.Div([
                html.Label("Evolution: ", style={"marginLeft": "30px", "marginRight": "10px", "fontSize": "1.1em"}),
                daq.BooleanSwitch(
                    id="evolution-switch-other",
                    on=False,
                    color="#c00000",
                    disabled=False
                )
            ], style={"display": "flex", "alignItems": "center", "marginLeft": "20px"})
        ], style={"flex": "2", "display": "flex", "alignItems": "center", "justifyContent": "center"}),
        
        html.Div([
            html.Button("📊 Graphs", id="graph-view-btn-other", n_clicks=0,
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0 10px",
                              "backgroundColor": "white", "border": "2px solid #c00000",
                              "color": "#c00000", "cursor": "pointer"}),
            html.Button("Download CSV", id="csv-button-dpr-other", n_clicks=0, 
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0",
                              "backgroundColor": "white", "border": "2px solid #f0f0f0",
                              "color": "#c00000", "cursor": "pointer"}),
        ], style={"flex": "1", "display": "flex", "alignItems": "center", "justifyContent": "flex-end"})
    ], style={"height": "6vh", "display": "flex", "alignItems": "center",
              "justifyContent": "space-between", "padding": "0 20px"}),
    
    # Main content area with AG Grid and Graphs
    html.Div([
        # AG Grid container
        html.Div([
            dag.AgGrid(
                id="steo-dpr-grid-other",
                columnDefs=columnDefinitions,
                defaultColDef={
                    "sortable": True,
                    "resizable": True,
                },
                rowData=current_df_serializable.to_dict('records'),
                csvExportParams={
                    "fileName": "steo_dpr_other_data.csv",
                },
                dashGridOptions={
                    "rowSelection": "single",
                    "animateRows": False,
                    "domLayout": "normal",
                },
                className="ag-theme-alpine",
                style={"height": "100%", "width": "100%"}
            )
        ], id="grid-container-other", style={"height": "100%", "width": "100%", "transition": "width 0.3s ease"}),
        
        # Graph panel (initially hidden)
        html.Div([
            html.Div([
                html.H3("Data Visualization", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Button("✕", id="close-graph-btn-other", n_clicks=0,
                           style={"position": "absolute", "top": "10px", "right": "10px",
                                  "background": "transparent", "border": "none",
                                  "fontSize": "1.5em", "cursor": "pointer", "color": "#666"})
            ], style={"position": "relative", "padding": "0 20px", "height": "50px"}),
            
            # Line graph
            html.Div([
                html.H4("Historical Trend", style={"margin": "5px 0", "fontSize": "1.1em", "color": "#333"}),
                dcc.Graph(id="line-graph-other", style={"height": "calc(100% - 30px)"})
            ], style={"padding": "0 20px", "height": "calc(50% - 25px)"}),
            
            # Seasonality graph
            html.Div([
                html.H4("Seasonality (All Years)", style={"margin": "5px 0", "fontSize": "1.1em", "color": "#333"}),
                dcc.Graph(id="seasonality-graph-other", style={"height": "calc(100% - 30px)"})
            ], style={"padding": "0 20px", "height": "calc(50% - 25px)"})
        ], id="graph-panel-other", style={"height": "100%", "width": "0%", "backgroundColor": "#f8f8f8",
                                    "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                                    "transition": "width 0.3s ease", "display": "none"}),
    ], style={"height": "85vh", "display": "flex", "padding": "0 20px"}),
    
    # Hidden stores
    dcc.Store(id='current-release-index-other', data=0),
    dcc.Store(id='graph-view-state-other', data=False)
    
], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

# Callbacks
@callback(
    Output("steo-dpr-grid-other", "exportDataAsCsv"),
    Input("csv-button-dpr-other", "n_clicks"),
)
def export_data_as_csv(n_clicks):
    if n_clicks > 0:
        return True
    return False

@callback(
    [Output("steo-dpr-grid-other", "rowData"),
     Output("steo-dpr-grid-other", "columnDefs"),
     Output("release-date-display-other", "children"),
     Output("current-release-index-other", "data"),
     Output("prev-release-btn-other", "disabled"),
     Output("next-release-btn-other", "disabled"),
     Output("evolution-switch-other", "disabled")],
    [Input("prev-release-btn-other", "n_clicks"),
     Input("next-release-btn-other", "n_clicks"),
     Input("evolution-switch-other", "on")],
    [State("current-release-index-other", "data")]
)
def update_release_date(prev_clicks, next_clicks, evolution_on, current_index):
    # Determine which button was clicked
    if not ctx.triggered:
        # Initial load
        new_index = 0
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "prev-release-btn-other":
            # Go to previous (older) release
            new_index = min(current_index + 1, len(release_dates) - 1)
        elif button_id == "next-release-btn-other":
            # Go to next (newer) release
            new_index = max(current_index - 1, 0)
        else:
            new_index = current_index
    
    # Get data for the selected release date
    selected_release = release_dates[new_index]
    
    # Check if we can show evolution (not at oldest release)
    can_show_evolution = new_index < len(release_dates) - 1
    prior_release = release_dates[new_index + 1] if can_show_evolution else None
    
    # Prepare data with or without evolution
    if evolution_on and can_show_evolution:
        updated_df, delivery_months = prepare_data(selected_release, show_evolution=True, prior_release_date=prior_release)
        evolution_text = f" (vs {prior_release.strftime('%B %Y')})"
    else:
        updated_df, delivery_months = prepare_data(selected_release, show_evolution=False)
        evolution_text = ""
    
    updated_df_serializable = convert_to_serializable(updated_df, delivery_months)
    updated_columnDefs = create_column_defs(delivery_months)
    
    # Format display text
    display_text = f"Release: {selected_release.strftime('%B %Y')}{evolution_text}"
    
    # Disable buttons at boundaries
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

# Callback for toggling graph panel
@callback(
    [Output("grid-container-other", "style"),
     Output("graph-panel-other", "style"),
     Output("graph-view-state-other", "data")],
    [Input("graph-view-btn-other", "n_clicks"),
     Input("close-graph-btn-other", "n_clicks")],
    [State("graph-view-state-other", "data")]
)
def toggle_graph_panel(graph_btn_clicks, close_btn_clicks, graph_state):
    if not ctx.triggered:
        return ({"height": "100%", "width": "100%", "transition": "width 0.3s ease"},
                {"height": "100%", "width": "0%", "backgroundColor": "#f8f8f8",
                 "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                 "transition": "width 0.3s ease", "display": "none"},
                False)
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "graph-view-btn-other":
        # Toggle graph view
        new_state = not graph_state
    elif button_id == "close-graph-btn-other":
        # Close graph view
        new_state = False
    else:
        new_state = graph_state
    
    if new_state:
        # Show graphs - grid takes 70%, graphs take 30%
        grid_style = {"height": "100%", "width": "70%", "transition": "width 0.3s ease"}
        graph_style = {"height": "100%", "width": "30%", "backgroundColor": "#f8f8f8",
                      "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                      "transition": "width 0.3s ease", "display": "block"}
    else:
        # Hide graphs - grid takes 100%
        grid_style = {"height": "100%", "width": "100%", "transition": "width 0.3s ease"}
        graph_style = {"height": "100%", "width": "0%", "backgroundColor": "#f8f8f8",
                      "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                      "transition": "width 0.3s ease", "display": "none"}
    
    return grid_style, graph_style, new_state

# Callback for updating graphs based on selected row
@callback(
    [Output("line-graph-other", "figure"),
     Output("seasonality-graph-other", "figure")],
    [Input("steo-dpr-grid-other", "selectedRows"),
     Input("current-release-index-other", "data")]
)
def update_graphs(selected_rows, current_index):
    # Default empty figures
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
    
    # Get selected row data
    selected_row = selected_rows[0]
    item_id = selected_row.get('id')
    item_name = selected_row.get('name', '')
    item_uom = selected_row.get('uom', '')
    
    # Filter data for the selected item across ALL releases
    item_data_all = df_melted[df_melted['id'] == item_id].copy()
    
    # Create line graph with all release dates
    line_fig = go.Figure()
    
    # Create a color palette for releases
    import plotly.express as px
    colors = px.colors.qualitative.Set1 + px.colors.qualitative.Set2
    
    # Plot each release date as a separate line (most recent first for color priority)
    for idx, release in enumerate(sorted(item_data_all['release_date'].unique(), reverse=True)):
        release_data = item_data_all[item_data_all['release_date'] == release].copy()
        release_data = release_data.sort_values('delivery_month')
        
        # Determine line style - solid for current release, dashed for others
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
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1,
            showline=True,
            linecolor='black',
            linewidth=1
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1,
            showline=True,
            linecolor='black',
            linewidth=1
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=9)
        )
    )
    
    # Create seasonality graph (all available years) - using current selected release
    selected_release = release_dates[current_index]
    item_data = item_data_all[item_data_all['release_date'] == selected_release].copy()
    
    if len(item_data) > 0:
        # Group by year and month for seasonality
        item_data['year'] = item_data['delivery_month'].dt.year
        item_data['month'] = item_data['delivery_month'].dt.month
        
        seasonality_fig = go.Figure()
        
        # Get all unique years (reverse order so latest year gets first color)
        years = sorted(item_data['year'].unique(), reverse=True)
        
        # Create a color palette for years
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
                showgrid=True,
                gridcolor='lightgrey',
                gridwidth=1,
                zeroline=True,
                zerolinecolor='black',
                zerolinewidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            ),
            yaxis=dict(
                title=item_uom,
                showgrid=True,
                gridcolor='lightgrey',
                gridwidth=1,
                zeroline=True,
                zerolinecolor='black',
                zerolinewidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            ),
            hovermode='x unified',
            height=None,
            margin=dict(l=50, r=20, t=40, b=40),
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center", 
                x=0.5,
                font=dict(size=10)
            )
        )
    else:
        seasonality_fig = empty_fig
    
    return line_fig, seasonality_fig