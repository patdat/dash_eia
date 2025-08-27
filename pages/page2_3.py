#######################################################################
### MANUAL INPUTS #####################################################

commodity = "Gasoline: "

idents = {
    # Gasoline Stocks
    "WGTSTUS1": "US Gasoline Stocks (kb)",
    "WGTSTP11": "P1 Gasoline Stocks (kb)",
    "WGTSTP21": "P2 Gasoline Stocks (kb)",
    "WGTSTP31": "P3 Gasoline Stocks (kb)",
    "WGTSTP41": "P4 Gasoline Stocks (kb)",
    "WGTSTP51": "P5 Gasoline Stocks (kb)",
    # Gasoline Imports
    "WGTIMUS2": "US Gasoline Imports (kbd)",
    "WGTIM_R10-Z00_2": "P1 Gasoline Imports (kbd)",
    "WGTIM_R20-Z00_2": "P2 Gasoline Imports (kbd)",
    "WGTIM_R30-Z00_2": "P3 Gasoline Imports (kbd)",
    "WGTIM_R40-Z00_2": "P4 Gasoline Imports (kbd)",
    "WGTIM_R50-Z00_2": "P5 Gasoline Imports (kbd)",
    # Gasoline Production
    "WGFRPUS2": "US Gasoline Production (kbd)",
    "WGFRPP12": "P1 Gasoline Production (kbd)",
    "WGFRPP22": "P2 Gasoline Production (kbd)",
    "WGFRPP32": "P3 Gasoline Production (kbd)",
    "WGFRPP42": "P4 Gasoline Production (kbd)",
    "WGFRPP52": "P5 Gasoline Production (kbd)",
    # Gasoline Exports
    "W_EPM0F_EEX_NUS-Z00_MBBLD": "US Gasoline Exports (kbd)",
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
from src.wps.calculation import create_callbacks, create_layout

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
