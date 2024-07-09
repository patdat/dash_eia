#######################################################################
### MANUAL INPUTS #####################################################

commodity = 'Crude: '

idents = {
    #Crude Stocks
    'WCESTUS1' : 'US Commercial Stocks (kb)',
    'WCESTP11' : 'P1 Commercial Stocks (kb)',
    'WCESTP21' : 'P2 Commercial Stocks (kb)',
    'WCESTP31' : 'P3 Commercial Stocks (kb)',
    'WCESTP41' : 'P4 Commercial Stocks (kb)',
    'WCESTP51' : 'P5 Commercial Stocks (kb)',
    #Other Crude Stocks
    'W_EPC0_SAX_YCUOK_MBBL' : 'Cushing Stocks (kb)',
    'crudeStocksP2E' : 'P2E Stocks (kb)',
    'WCSSTUS1' : 'SPR Stocks (kb)',
    'W_EPC0_SKA_NUS_MBBL' : 'Alaska Stocks (kb)',
    'WCRSTUS1' : 'Total Stocks (kb)',
    #Crude Production
    'WCRFPUS2': 'US Production (kbd)',
    'W_EPC0_FPF_R48_MBBLD': 'L48 Production (kbd)',
    'W_EPC0_FPF_SAK_MBBLD': 'AK Production (kbd)',        
    #Crude Imports
    'WCEIMUS2' : 'US Imports (kbd)',
    'WCEIMP12' : 'P1 Imports (kbd)',
    'WCEIMP22' : 'P2 Imports (kbd)',
    'WCEIMP32' : 'P3 Imports (kbd)',
    'WCEIMP42' : 'P4 Imports (kbd)',
    'WCEIMP52' : 'P5 Imports (kbd)',    
    #Crude Adjustments
    'crudeOriginalAdjustment' : 'OG Adjustment Factor (kbd)',
    #Crude Runs
    'WCRRIUS2' : 'US Refinery Runs (kbd)',
    'WCRRIP12' : 'P1 Refinery Runs (kbd)',
    'WCRRIP22' : 'P2 Refinery Runs (kbd)',
    'WCRRIP32' : 'P3 Refinery Runs (kbd)',
    'WCRRIP42' : 'P4 Refinery Runs (kbd)',
    'WCRRIP52' : 'P5 Refinery Runs (kbd)',
    #Crude Exports
    'WCREXUS2' : 'US Crude Exports (kbd)',
    #PADD9 Stats
    'crudeStocksP9' : 'P9 Stocks (kb)',
    'crudeRunsP9' : 'P9 Crude Runs (kbd)',
    'grossRunsP9' : 'P9 Gross Runs (kbd)',
    'feedstockRunsP9' : 'P9 Feedstock Runs (kbd)',
    'crudeImportsP9' : 'P9 Crude Imports (kbd)',
}


def graph_sections_input(page_id):
    return [
        #Stocks, 6 graphs
        ('Stocks', [f'{page_id}-graph-{i}' for i in range(1, 7)]),
        #Other Stocks, 5 graphs
        ('Other Stocks', [f'{page_id}-graph-{i}' for i in range(7, 12)]),        
        #Production, 3 graphs
        ('Production', [f'{page_id}-graph-{i}' for i in range(12, 15)]),
        #Imports, 6 graphs
        ('Imports', [f'{page_id}-graph-{i}' for i in range(15, 21)]),
        #Adjustments, 1 graph
        ('Adjustments', [f'{page_id}-graph-21']),
        #Runs, 6 graphs
        ('Runs', [f'{page_id}-graph-{i}' for i in range(22, 28)]),
        #Exports, 1 graph
        ('Exports', [f'{page_id}-graph-28']),
        #PADD 9 Stats, 5 Graphs
        ('PADD 9', [f'{page_id}-graph-{i}' for i in range(29, 34)]),        
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

