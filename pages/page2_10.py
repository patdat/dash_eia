from dash import html, dcc, callback, Output, Input, ctx, State
import dash_ag_grid as dag
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.wps.ag_calculations import DataProcessor
from src.utils.variables import default_start_date_eia_wps_table, default_end_date_eia_wps_table

# Initialize the data processor
processor = DataProcessor()

# Default date range
default_start_date = default_start_date_eia_wps_table
default_end_date = default_end_date_eia_wps_table

# Process data and column definitions - with error handling
try:
    df, columnDefinitions = processor.get_data(default_start_date, default_end_date)
except Exception as e:
    print(f"Error loading initial data for page2_10: {e}")
    # Create empty dataframe with minimal columns for initial load
    import pandas as pd
    df = pd.DataFrame()
    columnDefinitions = []

# Keep initial data for graph purposes
initial_df = df.copy() if not df.empty else pd.DataFrame()

# Page layout for page 2_10
layout = html.Div([
    # Header section
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
            html.Button("📊 Graphs", id="graph-view-btn-wps", n_clicks=0,
                       style={"fontSize": "1.3em", "padding": "10px", "margin": "0 10px",
                              "backgroundColor": "white", "border": "2px solid #c00000",
                              "color": "#c00000", "cursor": "pointer"}),
            html.Button("Download CSV", id="csv-button", n_clicks=0, 
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
                    "domLayout": "normal",
                },
                className="ag-theme-alpine",
                style={"height": "100%", "width": "100%"}
            )
        ], id="grid-container-wps", style={"height": "100%", "width": "100%", "transition": "width 0.3s ease"}),
        
        # Graph panel (initially hidden)
        html.Div([
            html.Div([
                html.H3("Data Visualization", style={"margin": "10px 0", "color": "#c00000", "fontSize": "1.5em"}),
                html.Button("✕", id="close-graph-btn-wps", n_clicks=0,
                           style={"position": "absolute", "top": "10px", "right": "10px",
                                  "background": "transparent", "border": "none",
                                  "fontSize": "1.5em", "cursor": "pointer", "color": "#666"})
            ], style={"position": "relative", "padding": "0 20px", "height": "50px"}),
            
            # Line graph with 4-week moving average
            html.Div([
                html.H4("Historical Trend", style={"margin": "5px 0", "fontSize": "1.1em", "color": "#333"}),
                dcc.Graph(id="line-graph-wps", style={"height": "calc(100% - 30px)"})
            ], style={"padding": "0 20px", "height": "calc(50% - 25px)"}),
            
            # Seasonality graph (weekly patterns)
            html.Div([
                html.H4("Weekly Seasonality Pattern", style={"margin": "5px 0", "fontSize": "1.1em", "color": "#333"}),
                dcc.Graph(id="seasonality-graph-wps", style={"height": "calc(100% - 30px)"})
            ], style={"padding": "0 20px", "height": "calc(50% - 25px)"})
        ], id="graph-panel-wps", style={"height": "100%", "width": "0%", "backgroundColor": "#f8f8f8",
                                    "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                                    "transition": "width 0.3s ease", "display": "none"}),
    ], style={"height": "85vh", "display": "flex", "padding": "0 20px"}),
    
    # Hidden stores
    dcc.Store(id='graph-view-state-wps', data=False),
    dcc.Store(id='current-data-store', data=df.to_dict('records') if not df.empty else [])
    
], style={"height": "100vh", "display": "flex", "flexDirection": "column"})

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
     Output("export-data-grid", "columnDefs"),
     Output("current-data-store", "data")],
    [Input("date-picker-range", "start_date"),
     Input("date-picker-range", "end_date")]
)
def update_grid_data(start_date, end_date):
    try:
        df, updated_columnDefinitions = processor.get_data(start_date, end_date)
        return df.to_dict('records'), updated_columnDefinitions, df.to_dict('records')
    except Exception as e:
        print(f"Error updating grid data: {e}")
        # Return empty data on error
        return pd.DataFrame().to_dict('records'), [], []

# Callback for toggling graph panel
@callback(
    [Output("grid-container-wps", "style"),
     Output("graph-panel-wps", "style"),
     Output("graph-view-state-wps", "data")],
    [Input("graph-view-btn-wps", "n_clicks"),
     Input("close-graph-btn-wps", "n_clicks")],
    [State("graph-view-state-wps", "data")]
)
def toggle_graph_panel(graph_btn_clicks, close_btn_clicks, graph_state):
    if not ctx.triggered:
        return ({"height": "100%", "width": "100%", "transition": "width 0.3s ease"},
                {"height": "100%", "width": "0%", "backgroundColor": "#f8f8f8",
                 "borderLeft": "2px solid #e0e0e0", "overflow": "auto",
                 "transition": "width 0.3s ease", "display": "none"},
                False)
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "graph-view-btn-wps":
        # Toggle graph view
        new_state = not graph_state
    elif button_id == "close-graph-btn-wps":
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
    [Output("line-graph-wps", "figure"),
     Output("seasonality-graph-wps", "figure")],
    [Input("export-data-grid", "selectedRows"),
     Input("current-data-store", "data")]
)
def update_graphs(selected_rows, current_data):
    # Default empty figures
    empty_fig = go.Figure()
    empty_fig.update_layout(
        title="Select a row to view data",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=None,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    if not selected_rows or len(selected_rows) == 0 or not current_data:
        return empty_fig, empty_fig
    
    # Get selected row data
    selected_row = selected_rows[0]
    item_id = selected_row.get('id')
    item_name = selected_row.get('name', '')
    item_uom = selected_row.get('uom', '')
    
    # Convert current data to DataFrame for easier processing
    df = pd.DataFrame(current_data)
    
    # Get date columns (exclude metadata columns)
    metadata_cols = ['id', 'name', 'padd', 'commodity', 'type', 'uom']
    date_cols = [col for col in df.columns if col not in metadata_cols]
    
    # Get the selected item's data
    item_row = df[df['id'] == item_id]
    if item_row.empty:
        return empty_fig, empty_fig
    
    # Prepare data for line graph - all available data
    dates = []
    values = []
    for col in date_cols:
        try:
            # Parse date and get value
            date = pd.to_datetime(col, format='%m/%d/%y')
            value = item_row[col].iloc[0]
            if pd.notna(value):  # Only include non-null values
                dates.append(date)
                values.append(float(value))
        except:
            continue
    
    if not dates:
        return empty_fig, empty_fig
    
    # Sort by date
    sorted_data = sorted(zip(dates, values))
    dates, values = zip(*sorted_data) if sorted_data else ([], [])
    
    # Create line graph with 4-week moving average
    line_fig = go.Figure()
    
    # Add main data line
    line_fig.add_trace(go.Scatter(
        x=dates,
        y=values,
        mode='lines+markers',
        name='Actual',
        line=dict(color='#c00000', width=1.5),
        marker=dict(size=3)
    ))
    
    # Calculate and add 4-week moving average
    if len(values) >= 4:
        df_ma = pd.DataFrame({'date': dates, 'value': values})
        df_ma['ma_4week'] = df_ma['value'].rolling(window=4, min_periods=1).mean()
        
        line_fig.add_trace(go.Scatter(
            x=df_ma['date'],
            y=df_ma['ma_4week'],
            mode='lines',
            name='4-Week Average',
            line=dict(color='#0066cc', width=2, dash='dash')
        ))
    
    line_fig.update_layout(
        title=f"{item_name} - Historical Trend",
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
            showline=True,
            linecolor='black',
            linewidth=1
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
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
            font=dict(size=10)
        )
    )
    
    # Create seasonality graph - last 4 years
    if dates:
        # Convert to DataFrame for easier manipulation
        season_df = pd.DataFrame({'date': dates, 'value': values})
        season_df['year'] = season_df['date'].dt.year
        season_df['week'] = season_df['date'].dt.isocalendar().week
        
        # Get last 4 years
        current_year = season_df['year'].max()
        last_4_years = list(range(max(season_df['year'].min(), current_year - 3), current_year + 1))
        
        seasonality_fig = go.Figure()
        
        # Color palette
        import plotly.express as px
        colors = px.colors.qualitative.Set1
        
        for idx, year in enumerate(reversed(last_4_years)):  # Reverse to give recent years priority colors
            year_data = season_df[season_df['year'] == year].copy()
            if not year_data.empty:
                year_data = year_data.sort_values('week')
                seasonality_fig.add_trace(go.Scatter(
                    x=year_data['week'],
                    y=year_data['value'],
                    mode='lines+markers',
                    name=str(year),
                    marker=dict(size=4),
                    line=dict(color=colors[idx % len(colors)], width=2)
                ))
        
        seasonality_fig.update_layout(
            title=f"Weekly Pattern - {item_name} (Last 4 Years)",
            xaxis=dict(
                title="Week of Year",
                tickmode='linear',
                tick0=1,
                dtick=4,
                range=[1, 52],
                showgrid=True,
                gridcolor='lightgrey',
                gridwidth=1,
                showline=True,
                linecolor='black',
                linewidth=1
            ),
            yaxis=dict(
                title=item_uom,
                showgrid=True,
                gridcolor='lightgrey',
                gridwidth=1,
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