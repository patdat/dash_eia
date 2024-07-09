from utils.mapping import production_mapping
from utils.download import main as download_raw_file
from utils.download_csv import main as fast_download
from utils.table_mapping import *
import dash
from dash import html, dash_table, Input, Output
from app import app
import pandas as pd


layout = html.Div([
    html.Button('Generate and Save Data', id='generate-data-btn'),
    html.Div(style={'height': '20px'}),  # Buffer separator
    html.Div(id='tables-container')  # Container to hold the tables
])

@app.callback(
    Output('data-store', 'data'),
    Input('generate-data-btn', 'n_clicks'),
    prevent_initial_call=True
)
def generate_data(n_clicks):
    if n_clicks is not None and n_clicks > 0:
        df = fast_download()
        # df = download_raw_file()
        return df.to_dict('records')
    else:
        initial_loadout = pd.read_csv('./data/wps_gte_2015_pivot.csv').to_dict('records')
        df = pd.DataFrame(initial_loadout)
    return df.to_dict('records')

def generate_main_table(df):
    df['period'] = pd.to_datetime(df['period'])
    df['period'] = df['period'].dt.strftime('%m/%d')
    df = df.tail(2)
    df = df.set_index('period')
    df = df.T.reset_index()
    df['change'] = df.iloc[:, 2] - df.iloc[:, 1]
    df = df.rename(columns={'index': 'name'})
    df.columns.name = None
    return df

def generate_dash_table(df, idents, table_id):
    df = df.copy()

    def format_number(num):
        # Force all to numeric
        num = pd.to_numeric(num, errors='coerce')
        num = round(num, 1)
        return num
    
    col_first = df.columns[0]
    col_second = df.columns[1]
    col_third = df.columns[2]
    col_fourth = df.columns[3]
    cols = [col_second, col_third, col_fourth]
    
    for col in cols:
        df[col] = df[col].apply(format_number)
    
    idents_ids = list(idents.keys())
    idents_names = list(idents.values())
    df = df[df['name'].isin(idents_ids)]

    df = df.set_index('name')
    df = df.reindex(idents_ids)
    df = df.reset_index()
    
    df['name'] = df['name'].replace(idents_ids, idents_names)
    
    df = df.rename(columns={'name': table_id})
    df = df.reset_index(drop=True)

    col_first = table_id

    return html.Div(
        dash_table.DataTable(
            id=table_id,
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_table={
                'border': 'none', 
                'borderRadius': '15px', 
                # 'overflow': 'hidden', 
                'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '5px',
                'fontFamily': 'Arial',
                'fontSize': '12px',
                'border': '1px solid lightgrey',
                'borderRadius': '10px'
            },
            style_header={
                'backgroundColor': '#bfbec4',
                'color': 'black',
                'fontWeight': 'bold'
            },
            style_cell_conditional=[
                {'if': {'column_id': col_first}, 'width': '200px'},
                {'if': {'column_id': col_second}, 'width': '70px', 'textAlign': 'right'},
                {'if': {'column_id': col_third}, 'width': '70px', 'textAlign': 'right'},
                {'if': {'column_id': col_fourth}, 'width': '70px', 'textAlign': 'right'},
            ],
            style_data_conditional=[
                {
                    'if': {
                        'filter_query': f'{{{col_fourth}}} > 0',
                        'column_id': col_fourth
                    },
                    'backgroundColor': 'lightgreen', # 'lightgreen'
                    'color': 'green',
                },
                {
                    'if': {
                        'filter_query': f'{{{col_fourth}}} < 0',
                        'column_id': col_fourth
                    },
                    'backgroundColor': 'lightpink', # 'lightpink'
                    'color': 'red',
                }
            ]
        ),
        style={'margin-bottom': '20px'}
    )

@app.callback(
    Output('tables-container', 'children'),
    Input('data-store', 'data')
)
def update_tables(data):
    if data is None:
        return dash.no_update
    df = pd.DataFrame(data)
    main_table = generate_main_table(df)
    headline_table = generate_dash_table(main_table, headline, 'Headline')
    products_supplied_table = generate_dash_table(main_table, products_supplied, 'Products Supplied')
    crude_stocks_table = generate_dash_table(main_table, crude_stocks, 'Crude Stocks')
    crude_other_stocks_table = generate_dash_table(main_table, crude_other_stocks, 'Crude Other Stocks')
    crude_production_table = generate_dash_table(main_table, crude_production, 'Crude Production')
    crude_imports_table = generate_dash_table(main_table, crude_imports, 'Crude Imports')
    crude_adjustment_table = generate_dash_table(main_table, crude_adjustment, 'Crude Adjustment')
    crude_runs_table = generate_dash_table(main_table, crude_runs, 'Crude Runs')
    crude_exports_table = generate_dash_table(main_table, crude_exports, 'Crude Exports')
    gasoline_stocks_table = generate_dash_table(main_table, gasoline_stocks, 'Gasoline Stocks')
    gasoline_imports_table = generate_dash_table(main_table, gasoline_imports, 'Gasoline Imports')
    gasoline_production_table = generate_dash_table(main_table, gasoline_production, 'Gasoline Production')
    gasoline_exports_table = generate_dash_table(main_table, gasoline_exports, 'Gasoline Exports')
    distillate_stocks_table = generate_dash_table(main_table, distillate_stocks, 'Distillate Stocks')
    distillate_imports_table = generate_dash_table(main_table, distillate_imports, 'Distillate Imports')
    distillate_production_table = generate_dash_table(main_table, distillate_production, 'Distillate Production')
    distillate_exports_table = generate_dash_table(main_table, distillate_exports, 'Distillate Exports')
    jet_stocks_table = generate_dash_table(main_table, jet_stocks, 'Jet Stocks')
    jet_imports_table = generate_dash_table(main_table, jet_imports, 'Jet Imports')
    jet_production_table = generate_dash_table(main_table, jet_production, 'Jet Production')
    jet_exports_table = generate_dash_table(main_table, jet_exports, 'Jet Exports')
    fueloil_stocks_table = generate_dash_table(main_table, fueloil_stocks, 'Fuel Oil Stocks')
    fueloil_imports_table = generate_dash_table(main_table, fueloil_imports, 'Fuel Oil Imports')
    fueloil_production_table = generate_dash_table(main_table, fueloil_production, 'Fuel Oil Production')
    fueloil_exports_table = generate_dash_table(main_table, fueloil_exports, 'Fuel Oil Exports')
    propane_propylene_stocks_table = generate_dash_table(main_table, propane_propylene_stocks, 'Propane/Propylene Stocks')
    propane_propylene_imports_table = generate_dash_table(main_table, propane_propylene_imports, 'Propane/Propylene Imports')
    propane_propylene_production_table = generate_dash_table(main_table, propane_propylene_production, 'Propane/Propylene Production')
    propane_propylene_exports_table = generate_dash_table(main_table, propane_propylene_exports, 'Propane/Propylene Exports')
    refinery_utilization_table = generate_dash_table(main_table, refinery_utilization, 'CDU Utilization')
    refinery_feedstock_runs_table = generate_dash_table(main_table, refinery_feedstock_runs, 'Feedstock Runs')
    refinery_gross_runs_table = generate_dash_table(main_table, refinery_gross_runs, 'Gross Runs')
    refinery_operable_cdu_capacity_table = generate_dash_table(main_table, refinery_operable_cdu_capacity, 'Operable CDU Capacity')

    html_object = html.Div([
        html.Div([
            html.Div([
                html.H1('Headline', className='eia_h1_header'),                
                headline_table,
                products_supplied_table,
            ], className='eia_table_style'),
    
            html.Div([
                html.H1('Crude', className='eia_h1_header'),  
                crude_stocks_table,
                crude_other_stocks_table,
                crude_production_table,
                crude_imports_table,
                crude_adjustment_table,
                crude_runs_table,
                crude_exports_table,              
            ], className='eia_table_style'),  
            
            html.Div([
                html.H1('Gasoline', className='eia_h1_header'),  
                gasoline_stocks_table,
                gasoline_imports_table,
                gasoline_production_table,
                gasoline_exports_table,
            ], className='eia_table_style'),
            
            html.Div([
                html.H1('Distillate', className='eia_h1_header'),  
                distillate_stocks_table,
                distillate_imports_table,
                distillate_production_table,
                distillate_exports_table,
            ], className='eia_table_style'),
            
            html.Div([
                html.H1('Jet', className='eia_h1_header'),  
                jet_stocks_table,
                jet_imports_table,
                jet_production_table,
                jet_exports_table,
            ], className='eia_table_style'),
            
            html.Div([
                html.H1('Fuel Oil', className='eia_h1_header'),  
                fueloil_stocks_table,
                fueloil_imports_table,
                fueloil_production_table,
                fueloil_exports_table,
            ], className='eia_table_style'),
            
            html.Div([
                html.H1('Propane/Propylene', className='eia_h1_header'),  
                propane_propylene_stocks_table,
                propane_propylene_imports_table,
                propane_propylene_production_table,
                propane_propylene_exports_table,
            ], className='eia_table_style'),  

            html.Div([
                html.H1('Refining', className='eia_h1_header'),  
                refinery_utilization_table,
                refinery_feedstock_runs_table,
                refinery_gross_runs_table,
                refinery_operable_cdu_capacity_table,
            ], className='eia_table_style'),  

    
        ], style={'display': 'flex', 'width': '3280px'}),
    ], style={'display': 'flex', 'justify-content': 'left'})

    
    
    return html_object
    
    