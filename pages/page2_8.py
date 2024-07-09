#######################################################################
### MANUAL INPUTS #####################################################

commodity = 'Demand: '

idents = {
    'WRPUPUS2' : 'Products Supplied (kbd)',
    'WGFUPUS2' : 'Gasoline Supplied (kbd)',
    'WDIUPUS2' : 'Distillate Supplied (kbd)',
    'WKJUPUS2' : 'Jet Supplied (kbd)',
    'WREUPUS2' : 'Fuel Oil Supplied (kbd)',
    'WPRUP_NUS_2' : ' C3/C3= Supplied (kbd)',
    'WWOUP_NUS_2' : 'Other Oils Supplied (kbd)',
}
    
def graph_sections_input(page_id):
    return [
        # Products Supplied, 8 graphs
        ('Products Supplied', [f'{page_id}-graph-{i}' for i in range(1, 8)]),
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

