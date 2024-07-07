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
        html.H1(f'{commodity} Exports', className='eia-weekly-header-title'),
        html.Br(),
        html.Div([
            create_loading_graph(f'{page_id}-graph-1'),
        ], className='eia-weekly-graph-container'),
    ], className='eia-weekly-graph-page-layout')
    return layout

####################################################################################################

idents = {
    #Crude Exports
    'WCREXUS2' : 'US Crude Exports (kbd)',    
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
