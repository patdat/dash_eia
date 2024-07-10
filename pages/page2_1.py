from utils.mapping import production_mapping
from utils.download_xlsx import main as download_xlsx
from utils.download_csv import main as download_csv
from utils.table_mapping import *
import dash
from dash import html, dash_table, Input, Output
from dash.dash_table.Format import Format, Group, Sign, Symbol
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
        # df = download_xlsx()
        df = download_csv()
        return df.to_dict('records')
    else:
        initial_loadout = pd.read_csv('./data/wps_gte_2015_pivot.csv').to_dict('records')
        df = pd.DataFrame(initial_loadout)
        return df.to_dict('records')

def generate_main_table(df):
    df['period'] = pd.to_datetime(df['period']).dt.strftime('%m/%d')
    df = df.tail(2).set_index('period').T.reset_index()
    df['change'] = df.iloc[:, 2] - df.iloc[:, 1]
    df.rename(columns={'index': 'name'}, inplace=True)
    return df

def generate_dash_table(df, idents, table_id):
    df = df.copy()
    df[df.columns[1:]] = df[df.columns[1:]].apply(pd.to_numeric, errors='coerce').round(1)
    
    idents_ids = list(idents.keys())
    idents_names = list(idents.values())
    df = df[df['name'].isin(idents_ids)].set_index('name').reindex(idents_ids).reset_index()
    df['name'] = df['name'].replace(idents_ids, idents_names)
    df.rename(columns={'name': table_id}, inplace=True)
    
    number_format = Format(
        symbol=Symbol.yes, 
        symbol_suffix='',
        groups=3,
        group=Group.yes,
        group_delimiter=',',
        decimal_delimiter='.',
        nully='N/A',
        sign=Sign.parantheses
    )
    
    columns = [
        {"name": i, "id": i, "type": "numeric", "format": number_format} if i in df.columns[1:] else {"name": i, "id": i}
        for i in df.columns
    ]

    return html.Div(
        dash_table.DataTable(
            id=table_id,
            columns=columns,
            data=df.to_dict('records'),
            style_table={'border': 'none', 'borderRadius': '15px', 'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19)'},
            style_cell={'textAlign': 'left', 'padding': '5px', 'fontFamily': 'Arial', 'fontSize': '12px', 'border': '1px solid lightgrey', 'borderRadius': '10px'},
            style_header={'backgroundColor': '#bfbec4', 'color': 'black', 'fontWeight': 'bold'},
            style_cell_conditional=[
                {'if': {'column_id': table_id}, 'width': '200px'},
                {'if': {'column_id': df.columns[1]}, 'width': '70px', 'textAlign': 'right'},
                {'if': {'column_id': df.columns[2]}, 'width': '70px', 'textAlign': 'right'},
                {'if': {'column_id': df.columns[3]}, 'width': '70px', 'textAlign': 'right'}
            ],
            style_data_conditional=[
                {'if': {'filter_query': f'{{{df.columns[3]}}} > 0', 'column_id': df.columns[3]}, 'backgroundColor': 'lightgreen', 'color': 'green'},
                {'if': {'filter_query': f'{{{df.columns[3]}}} < 0', 'column_id': df.columns[3]}, 'backgroundColor': 'lightpink', 'color': '#c00000'}
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

    table_ids = {
        'Headline': headline,
        'Products Supplied': products_supplied,
        'Crude Stocks': crude_stocks,
        'Crude Other Stocks': crude_other_stocks,
        'Crude Production': crude_production,
        'Crude Imports': crude_imports,
        'Crude Adjustment': crude_adjustment,
        'Crude Runs': crude_runs,
        'Crude Exports': crude_exports,
        'Gasoline Stocks': gasoline_stocks,
        'Gasoline Imports': gasoline_imports,
        'Gasoline Production': gasoline_production,
        'Gasoline Exports': gasoline_exports,
        'Distillate Stocks': distillate_stocks,
        'Distillate Imports': distillate_imports,
        'Distillate Production': distillate_production,
        'Distillate Exports': distillate_exports,
        'Jet Stocks': jet_stocks,
        'Jet Imports': jet_imports,
        'Jet Production': jet_production,
        'Jet Exports': jet_exports,
        'Fuel Oil Stocks': fueloil_stocks,
        'Fuel Oil Imports': fueloil_imports,
        'Fuel Oil Production': fueloil_production,
        'Fuel Oil Exports': fueloil_exports,
        'Propane/Propylene Stocks': propane_propylene_stocks,
        'Propane/Propylene Imports': propane_propylene_imports,
        'Propane/Propylene Production': propane_propylene_production,
        'Propane/Propylene Exports': propane_propylene_exports,
        'CDU Utilization': refinery_utilization,
        'Feedstock Runs': refinery_feedstock_runs,
        'Gross Runs': refinery_gross_runs,
        'Operable CDU Capacity': refinery_operable_cdu_capacity
    }

    tables = []
    for table_id, idents in table_ids.items():
        tables.append(generate_dash_table(main_table, idents, table_id))

    return html.Div(
        html.Div([
            html.Div([
                html.H1('Headline', className='eia_h1_header'),                
                tables[0],
                tables[1],
            ], className='eia_table_style'),

            html.Div([
                html.H1('Crude', className='eia_h1_header'),  
                *tables[2:9],
            ], className='eia_table_style'),  
            
            html.Div([
                html.H1('Gasoline', className='eia_h1_header'),  
                *tables[9:13],
            ], className='eia_table_style'),
            
            html.Div([
                html.H1('Distillate', className='eia_h1_header'),  
                *tables[13:17],
            ], className='eia_table_style'),
            
            html.Div([
                html.H1('Jet', className='eia_h1_header'),  
                *tables[17:21],
            ], className='eia_table_style'),
            
            html.Div([
                html.H1('Fuel Oil', className='eia_h1_header'),  
                *tables[21:25],
            ], className='eia_table_style'),
            
            html.Div([
                html.H1('Propane/Propylene', className='eia_h1_header'),  
                *tables[25:29],
            ], className='eia_table_style'),  

            html.Div([
                html.H1('Refining', className='eia_h1_header'),  
                *tables[29:33],
            ], className='eia_table_style'),  
        ], style={'display': 'flex', 'width': '3280px'}),
        style={'display': 'flex', 'justify-content': 'left'}
    )
