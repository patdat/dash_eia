#######################################################################
### MANUAL INPUTS #####################################################

commodity = 'Fuel Oil: '

idents = {
    #Fuel Oil Stocks
    'WRESTUS1' : 'US Fuel Oil Stocks (kb)',
    'WRESTP11' : 'P1 Fuel Oil Stocks (kb)',
    'WRESTP21' : 'P2 Fuel Oil Stocks (kb)',
    'WRESTP31' : 'P3 Fuel Oil Stocks (kb)',
    'WRESTP41' : 'P4 Fuel Oil Stocks (kb)',
    'WRESTP51' : 'P5 Fuel Oil Stocks (kb)',
    #Fuel Oil Imports
    'WREIMUS2' : 'US Fuel Oil Imports (kbd)',
    'WREIM_R10-Z00_2' : 'P1 Fuel Oil Imports (kbd)',
    'WREIM_R20-Z00_2' : 'P2 Fuel Oil Imports (kbd)',
    'WREIM_R30-Z00_2' : 'P3 Fuel Oil Imports (kbd)',
    'WREIM_R40-Z00_2' : 'P4 Fuel Oil Imports (kbd)',
    'WREIM_R50-Z00_2' : 'P5 Fuel Oil Imports (kbd)',
    #Fuel Oil Production
    'WRERPUS2' : 'US Fuel Oil Production (kbd)',
    'WRERPP12' : 'P1 Fuel Oil Production (kbd)',
    'WRERPP22' : 'P2 Fuel Oil Production (kbd)',
    'WRERPP32' : 'P3 Fuel Oil Production (kbd)',
    'WRERPP42' : 'P4 Fuel Oil Production (kbd)',
    'WRERPP52' : 'P5 Fuel Oil Production (kbd)',
    #Fuel Oil Exports
    'WREEXUS2' : 'US Fuel Oil Exports (kbd)',   
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

import dash
import pandas as pd
from utils.graph_optionality import checklist_header
from app import app
import os
from dash import html, Input, Output
from utils.calculation import create_loading_graph, get_initial_data, get_data, create_callbacks, create_layout
from utils.graph_seag import chart_seasonality
from utils.graph_line import chart_trend

# Get the list of IDs
idents_list = list(idents.keys())

# Initial data fetching and processing
raw_data = get_initial_data()
raw_data = raw_data[['period'] + idents_list]

# Page-specific variables
page_id = os.path.basename(__file__).split('.')[0]
num_graphs = len(idents_list)

# Create the layout for the current page
layout = create_layout(page_id, commodity,graph_sections_input(page_id))

# Create callbacks for the app
create_callbacks(app, page_id, num_graphs, idents_list, 'data-store')

if __name__ == '__main__':
    app.layout = layout
    app.run_server(debug=True, port=8051)