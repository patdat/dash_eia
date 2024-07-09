#######################################################################
### MANUAL INPUTS #####################################################

commodity = 'Gasoline: '

idents = {
    #Gasoline Stocks
    'WGTSTUS1' : 'US Gasoline Stocks (kb)',
    'WGTSTP11' : 'P1 Gasoline Stocks (kb)',
    'WGTSTP21' : 'P2 Gasoline Stocks (kb)',
    'WGTSTP31' : 'P3 Gasoline Stocks (kb)',
    'WGTSTP41' : 'P4 Gasoline Stocks (kb)',
    'WGTSTP51' : 'P5 Gasoline Stocks (kb)',
    #Gasoline Imports
    'WGTIMUS2' : 'US Gasoline Imports (kbd)',
    'WGTIM_R10-Z00_2' : 'P1 Gasoline Imports (kbd)',
    'WGTIM_R20-Z00_2' : 'P2 Gasoline Imports (kbd)',
    'WGTIM_R30-Z00_2' : 'P3 Gasoline Imports (kbd)',
    'WGTIM_R40-Z00_2' : 'P4 Gasoline Imports (kbd)',
    'WGTIM_R50-Z00_2' : 'P5 Gasoline Imports (kbd)',
    #Gasoline Production
    'WGFRPUS2' : 'US Gasoline Production (kbd)',
    'WGFRPP12' : 'P1 Gasoline Production (kbd)',
    'WGFRPP22' : 'P2 Gasoline Production (kbd)',
    'WGFRPP32' : 'P3 Gasoline Production (kbd)',
    'WGFRPP42' : 'P4 Gasoline Production (kbd)',
    'WGFRPP52' : 'P5 Gasoline Production (kbd)',
    #Gasoline Exports
    'W_EPM0F_EEX_NUS-Z00_MBBLD' : 'US Gasoline Exports (kbd)',
}
    
def graph_sections_input(page_id):
    return [
        # Stocks, 6 graphs
        ('Stocks', [f'{page_id}-graph-{i}' for i in range(1, 7)]),
        # Imports, 6 graphs
        ('Imports', [f'{page_id}-graph-{i}' for i in range(7, 13)]),        
        # Production, 6 graphs
        ('Production', [f'{page_id}-graph-{i}' for i in range(13, 19)]),        
        # Exports, 1 graph
        ('Exports', [f'{page_id}-graph-19']),
    ]

### END MANUAL INPUTS #################################################
#######################################################################

from dash import html, Input, Output
from utils.calculation import create_callbacks, get_initial_data, create_loading_graph, generate_ids
from utils.chooser import checklist_header
from app import app
import os

def create_graph_section(title, graph_ids):
    return html.Div([
        html.H1(title, className='eia-weekly-header-title'),
        html.Div([create_loading_graph(graph_id) for graph_id in graph_ids], className='eia-weekly-graph-container')
    ])
    
def create_layout(page_id,commodity):
    ids = generate_ids(page_id)    
    graph_sections = graph_sections_input(page_id)
    return html.Div([
        checklist_header(ids['checklist_graph'], ids['checklist_id'], ids['toggle_id'], ids['checklist_div_id'], ids['toggle_div_id']),
        html.Div(className='eia-weekly-top-spacing'),
        *[create_graph_section(f'{commodity} {title}', graph_ids) for title, graph_ids in graph_sections]
    ], className='eia-weekly-graph-page-layout')

# Get the list of IDs
idents_list = list(idents.keys())

# Initial data fetching and processing
raw_data = get_initial_data()
raw_data = raw_data[['period'] + idents_list]

# Page-specific variables
page_id = os.path.basename(__file__).split('.')[0]
num_graphs = len(idents_list)

# Create the layout for the current page
layout = create_layout(page_id,commodity)

# Create callbacks for the app
create_callbacks(app, page_id, num_graphs, idents_list, 'data-store')

# Callback to toggle the visibility of checklist and toggle divs
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

