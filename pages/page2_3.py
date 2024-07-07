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
        html.H1(f'{commodity} Runs', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-1'),
            create_loading_graph(f'{page_id}-graph-2'),
            create_loading_graph(f'{page_id}-graph-3'),
            create_loading_graph(f'{page_id}-graph-4'),
            create_loading_graph(f'{page_id}-graph-5'),
            create_loading_graph(f'{page_id}-graph-6'),
        ], className='eia-weekly-graph-container'),
        html.H1(f'{commodity} Refinery Utilization', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-7'),
            create_loading_graph(f'{page_id}-graph-8'),
            create_loading_graph(f'{page_id}-graph-9'),
            create_loading_graph(f'{page_id}-graph-10'),
            create_loading_graph(f'{page_id}-graph-11'),
            create_loading_graph(f'{page_id}-graph-12'),
        ], className='eia-weekly-graph-container'),
        html.H1(f'Feedstock Runs', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-13'),
            create_loading_graph(f'{page_id}-graph-14'),
            create_loading_graph(f'{page_id}-graph-15'),
            create_loading_graph(f'{page_id}-graph-16'),
            create_loading_graph(f'{page_id}-graph-17'),
            create_loading_graph(f'{page_id}-graph-18'),
        ], className='eia-weekly-graph-container'),
        html.H1(f'Gross Runs', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-19'),
            create_loading_graph(f'{page_id}-graph-20'),
            create_loading_graph(f'{page_id}-graph-21'),
            create_loading_graph(f'{page_id}-graph-22'),
            create_loading_graph(f'{page_id}-graph-23'),
            create_loading_graph(f'{page_id}-graph-24'),
        ], className='eia-weekly-graph-container'),
    ], className='eia-weekly-graph-page-layout')
    return layout

####################################################################################################

idents = {
    # Crude Runs
    'WCRRIUS2': 'US Refinery Runs (kbd)',
    'WCRRIP12': 'P1 Refinery Runs (kbd)',
    'WCRRIP22': 'P2 Refinery Runs (kbd)',
    'WCRRIP32': 'P3 Refinery Runs (kbd)',
    'WCRRIP42': 'P4 Refinery Runs (kbd)',
    'WCRRIP52': 'P5 Refinery Runs (kbd)',
    # Crude Refinery Utilization
    'WPULEUS3': 'US Refinery Utilization (%)',
    'W_NA_YUP_R10_PER': 'P1 Refinery Utilization (%)',
    'W_NA_YUP_R20_PER': 'P2 Refinery Utilization (%)',
    'W_NA_YUP_R30_PER': 'P3 Refinery Utilization (%)',
    'W_NA_YUP_R40_PER': 'P4 Refinery Utilization (%)',
    'W_NA_YUP_R50_PER': 'P5 Refinery Utilization (%)',
    # Feedstock Runs
    'feedstockRunsUS': 'US Feedstock Runs (kbd)',
    'feddStockRunsP1': 'P1 Feedstock Runs (kbd)',
    'feedstockRunsP2': 'P2 Feedstock Runs (kbd)',
    'feedstockRunsP3': 'P3 Feedstock Runs (kbd)',
    'feedstockRunsP4': 'P4 Feedstock Runs (kbd)',
    'feedstockRunsP5': 'P5 Feedstock Runs (kbd)',
    # Gross Runs
    'WGIRIUS2': 'US Gross Runs (kbd)',
    'WGIRIP12': 'P1 Gross Runs (kbd)',
    'WGIRIP22': 'P2 Gross Runs (kbd)',
    'WGIRIP32': 'P3 Gross Runs (kbd)',
    'WGIRIP42': 'P4 Gross Runs (kbd)',
    'WGIRIP52': 'P5 Gross Runs (kbd)',
}

idents = list(idents.keys())
raw_data = get_initial_data()
raw_data = raw_data[['period'] + idents]

page_id = os.path.basename(__file__).split('.')[0]
num_graphs = len(idents)

layout = create_layout(page_id, 'Crude Oil')

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
