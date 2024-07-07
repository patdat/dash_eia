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
        ], className='eia-weekly-graph-container'),
        html.H1(f'{commodity} Imports', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-6'),
            create_loading_graph(f'{page_id}-graph-7'),
            create_loading_graph(f'{page_id}-graph-8'),
            create_loading_graph(f'{page_id}-graph-9'),
            create_loading_graph(f'{page_id}-graph-10'),
        ], className='eia-weekly-graph-container'),
        html.H1(f'{commodity} Production', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-11'),
            create_loading_graph(f'{page_id}-graph-12'),
            create_loading_graph(f'{page_id}-graph-13'),
            create_loading_graph(f'{page_id}-graph-14'),
            create_loading_graph(f'{page_id}-graph-15'),
        ], className='eia-weekly-graph-container'),
        html.H1(f'{commodity} Exports', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-16'),
        ], className='eia-weekly-graph-container'),
    ], className='eia-weekly-graph-page-layout')
    return layout

####################################################################################################

idents = {
    #Propane Stocks
    'WPRSTUS1' : 'US Propane and Propylene Stocks (kb)',
    'WPRSTP11' : 'P1 Propane and Propylene Stocks (kb)',
    'WPRSTP21' : 'P2 Propane and Propylene Stocks (kb)',
    'WPRSTP31' : 'P3 Propane and Propylene Stocks (kb)',
    'WPRST_R4N5_1' : 'P4 and P5 Propane and Propylene Stocks (kb)',
    #Propane Imports
    'WPRIM_NUS-Z00_2' : 'US Propane and Propylene Imports (kbd)',
    'WPRIMP12' : 'P1 Propane and Propylene Imports (kbd)',
    'WPRIMP22' : 'P2 Propane and Propylene Imports (kbd)',
    'WPRIMP32' : 'P3 Propane and Propylene Imports (kbd)',
    'W_EPLLPZ_IM0_R45-Z00_MBBLD' : 'P4 and P5 Propane and Propylene Imports (kbd)',
    #Propane Produciton
    'WPRTP_NUS_2' : 'US Propane and Propylene Production (kbd)',
    'WPRNPP12' : 'P1 Propane and Propylene Production (kbd)',
    'WPRNPP22' : 'P2 Propane and Propylene Production (kbd)',
    'WPRNPP32' : 'P3 Propane and Propylene Production (kbd)',
    'W_EPLLPZ_YPT_R4N5_MBBLD' : 'P4 and P5 Propane and Propylene Production (kbd)',
    #Propane Exports
    'W_EPLLPZ_EEX_NUS-Z00_MBBLD' : 'US Propane and Propylene Exports (kbd)', 
}

idents = list(idents.keys())

raw_data = get_initial_data()
raw_data = raw_data[['period'] + idents]

page_id = os.path.basename(__file__).split('.')[0]
num_graphs = len(idents)

layout = create_layout(page_id, 'Propane and Propylene')

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
