###GASOLINE##

from dash import dcc, html, Input, Output
from utils.calculation import create_callbacks, get_initial_data
from utils.chooser import checklist_header
from app import app
import pandas as pd
import os

def create_loading_graph(graph_id):
    return dcc.Loading(
        id=f'{graph_id}-loading',
        type='dot',
        className='custom-loading',
        children=html.Div(
            dcc.Graph(id=graph_id),
            className='graph-container'
        )
    )
    
def create_layout(page_id, commodity):
    checklist_graph = f'{page_id}-graph-toggle'
    checklist_id = f'{page_id}-year-toggle'
    toggle_id = f'{page_id}-toggle-range'
    checklist_div_id = f'{page_id}-checklist-div'
    toggle_div_id = f'{page_id}-toggle-div'

    layout = html.Div([
        checklist_header(checklist_graph, checklist_id, toggle_id, checklist_div_id, toggle_div_id),
        html.Div(className='eia-weekly-top-spacing'),
        html.H1(f'{commodity} Stocks', className='eia-weekly-header-title'),
        html.Div([
            create_loading_graph(f'{page_id}-graph-1'),
            create_loading_graph(f'{page_id}-graph-2'),
            create_loading_graph(f'{page_id}-graph-3'),
            create_loading_graph(f'{page_id}-graph-4'),
            create_loading_graph(f'{page_id}-graph-5'),
            create_loading_graph(f'{page_id}-graph-6'),
        ], className='eia-weekly-graph-container'),
        html.H1(f'{commodity} Imports', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-7'),
            create_loading_graph(f'{page_id}-graph-8'),
            create_loading_graph(f'{page_id}-graph-9'),
            create_loading_graph(f'{page_id}-graph-10'),
            create_loading_graph(f'{page_id}-graph-11'),
            create_loading_graph(f'{page_id}-graph-12'),            
        ], className='eia-weekly-graph-container'),
        html.H1(f'{commodity} Production', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-13'),
            create_loading_graph(f'{page_id}-graph-14'),
            create_loading_graph(f'{page_id}-graph-15'),
            create_loading_graph(f'{page_id}-graph-16'),
            create_loading_graph(f'{page_id}-graph-17'),
            create_loading_graph(f'{page_id}-graph-18'),
        ], className='eia-weekly-graph-container'),
        html.H1(f'{commodity} Exports', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-19'),
        ], className='eia-weekly-graph-container'),
    ], className='eia-weekly-graph-page-layout')
    return layout

####################################################################################################

idents = {
    #Fuel Oil Stocks
    'WRERPUS2' : 'US Residual Fuel Oil Stocks (kb)',
    'WRERPP12' : 'P1 Residual Fuel Oil Stocks (kb)',
    'WRERPP22' : 'P2 Residual Fuel Oil Stocks (kb)',
    'WRERPP32' : 'P3 Residual Fuel Oil Stocks (kb)',
    'WRERPP42' : 'P4 Residual Fuel Oil Stocks (kb)',
    'WRERPP52' : 'P5 Residual Fuel Oil Stocks (kb)',    
    #Fuel Oil Imports
    'WREIMUS2' : 'US Residual Fuel Oil Imports (kbd)',
    'WREIM_R10-Z00_2' : 'P1 Residual Fuel Oil Imports (kbd)',
    'WREIM_R20-Z00_2' : 'P2 Residual Fuel Oil Imports (kbd)',
    'WREIM_R30-Z00_2' : 'P3 Residual Fuel Oil Imports (kbd)',
    'WREIM_R40-Z00_2' : 'P4 Residual Fuel Oil Imports (kbd)',
    'WREIM_R50-Z00_2' : 'P5 Residual Fuel Oil Imports (kbd)',
    #Fuel Oil Production
    'WRERPUS2' : 'US Residual Fuel Oil Production (kbd)',
    'WRERPP12' : 'P1 Residual Fuel Oil Production (kbd)',
    'WRERPP22' : 'P2 Residual Fuel Oil Production (kbd)',
    'WRERPP32' : 'P3 Residual Fuel Oil Production (kbd)',
    'WRERPP42' : 'P4 Residual Fuel Oil Production (kbd)',
    'WRERPP52' : 'P5 Residual Fuel Oil Production (kbd)',
    #Fuel Oil Exports
    'WREEXUS2' : 'US Residual Fuel Oil Exports (kbd)',    
}

idents = list(idents.keys())

raw_data = get_initial_data()
raw_data = raw_data[['period'] + idents]

page_id = os.path.basename(__file__).split('.')[0]
num_graphs = len(idents)

layout = create_layout(page_id, 'Fuel Oil')

@app.callback(
    [Output(f'{page_id}-checklist-div', 'style'),
     Output(f'{page_id}-toggle-div', 'style')],
    [Input(f'{page_id}-graph-toggle', 'value')]
)
def toggle_visibility(toggle_value):
    if toggle_value:
        return {'display': 'none'}, {'display': 'none'}
    else:
        return {'display': 'block'}, {'display': 'block'}

create_callbacks(app, page_id, num_graphs, idents,raw_data)
