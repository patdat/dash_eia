#######################################################################
### MANUAL INPUTS #####################################################

commodity = "Jet: "

idents = {
    # Jet Stocks
    "WKJSTUS1": "US Jet Stocks (kb)",
    "WKJSTP11": "P1 Jet Stocks (kb)",
    "WKJSTP21": "P2 Jet Stocks (kb)",
    "WKJSTP31": "P3 Jet Stocks (kb)",
    "WKJSTP41": "P4 Jet Stocks (kb)",
    "WKJSTP51": "P5 Jet Stocks (kb)",
    # Jet Imports
    "WKJIMUS2": "US Jet Imports (kbd)",
    "WKJIM_R10-Z00_2": "P1 Jet Imports (kbd)",
    "WKJIM_R20-Z00_2": "P2 Jet Imports (kbd)",
    "WKJIM_R30-Z00_2": "P3 Jet Imports (kbd)",
    "WKJIM_R40-Z00_2": "P4 Jet Imports (kbd)",
    "WKJIM_R50-Z00_2": "P5 Jet Imports (kbd)",
    # Jet Production
    "WKJRPUS2": "US Jet Production (kbd)",
    "WKJRPP12": "P1 JetProduction (kbd)",
    "WKJRPP22": "P2 Jet Production (kbd)",
    "WKJRPP32": "P3 Jet Production (kbd)",
    "WKJRPP42": "P4 Jet Production (kbd)",
    "WKJRPP52": "P5 Jet Production (kbd)",
    # Jet Exports
    "WKJEXUS2": "US Jet Exports (kbd)",
}


def graph_sections_input(page_id):
    return [
        # Stocks, 6 graphs
        ("Stocks", [f"{page_id}-graph-{i}" for i in range(1, 7)]),
        # Imports, 6 graphs
        ("Imports", [f"{page_id}-graph-{i}" for i in range(7, 13)]),
        # Production, 6 graphs
        ("Production", [f"{page_id}-graph-{i}" for i in range(13, 19)]),
        # Exports, 1 graph
        ("Exports", [f"{page_id}-graph-19"]),
    ]


### END MANUAL INPUTS #################################################
#######################################################################

from app import app
import os
from utils_wps.calculation import create_callbacks,create_layout

idents_list = list(idents.keys())


# Page-specific variables
page_id = os.path.basename(__file__).split(".")[0]
num_graphs = len(idents_list)

# Create the layout for the current page
layout = create_layout(page_id, commodity, graph_sections_input(page_id))

# Create callbacks for the app
create_callbacks(app, page_id, num_graphs, idents_list)

if __name__ == "__main__":
    app.layout = layout
    app.run_server(debug=True, port=8051)
