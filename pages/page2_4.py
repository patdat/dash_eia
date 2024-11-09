#######################################################################
### MANUAL INPUTS #####################################################

commodity = "Distillate: "

idents = {
    # Distillate Stocks
    "WDISTUS1": "US Distillate Stocks (kb)",
    "WDISTP11": "P1 Distillate Stocks (kb)",
    "WDISTP21": "P2 Distillate Stocks (kb)",
    "WDISTP31": "P3 Distillate Stocks (kb)",
    "WDISTP41": "P4 Distillate Stocks (kb)",
    "WDISTP51": "P5 Distillate Stocks (kb)",
    # Distillate Imports
    "WDIIMUS2": "US Distillate Imports (kbd)",
    "WDIIM_R10-Z00_2": "P1 Distillate Imports (kbd)",
    "WDIIM_R20-Z00_2": "P2 Distillate Imports (kbd)",
    "WDIIM_R30-Z00_2": "P3 Distillate Imports (kbd)",
    "WDIIM_R40-Z00_2": "P4 Distillate Imports (kbd)",
    "WDIIM_R50-Z00_2": "P5 Distillate Imports (kbd)",
    # Distillate Production
    "WDIRPUS2": "US Distillate Production (kbd)",
    "WDIRPP12": "P1 Distillate Production (kbd)",
    "WDIRPP22": "P2 Distillate Production (kbd)",
    "WDIRPP32": "P3 Distillate Production (kbd)",
    "WDIRPP42": "P4 Distillate Production (kbd)",
    "WDIRPP52": "P5 Distillate Production (kbd)",
    # Distillate Exports
    "WDIEXUS2": "US Distillate Exports (kbd)",
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
from utils_wps.calculation import create_callbacks, create_layout

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
