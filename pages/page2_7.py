#######################################################################
### MANUAL INPUTS #####################################################

commodity = "Propane/Propylene: "

idents = {
    # C3/C3= Stocks
    "WPRSTUS1": "US C3/C3= Stocks (kb)",
    "WPRSTP11": "P1 C3/C3= Stocks (kb)",
    "WPRSTP21": "P2 C3/C3= Stocks (kb)",
    "WPRSTP31": "P3 C3/C3= Stocks (kb)",
    "WPRST_R4N5_1": "P4P5 C3/C3= Stocks (kb)",
    # C3/C3= Imports
    "WPRIM_NUS-Z00_2": "US C3/C3= Imports (kbd)",
    "WPRIMP12": "P1 C3/C3= Imports (kbd)",
    "WPRIMP22": "P2 C3/C3= Imports (kbd)",
    "WPRIMP32": "P3 C3/C3= Imports (kbd)",
    "W_EPLLPZ_IM0_R45-Z00_MBBLD": "P4P5 C3/C3= Imports (kbd)",
    # C3/C3= Production
    "WPRTP_NUS_2": "US C3/C3= Production (kbd)",
    "WPRNPP12": "P1 C3/C3= Production (kbd)",
    "WPRNPP22": "P2 C3/C3= Production (kbd)",
    "WPRNPP32": "P3 C3/C3= Production (kbd)",
    "W_EPLLPZ_YPT_R4N5_MBBLD": "P4P5 C3/C3= Production (kbd)",
    # C3/C3= Exports
    "W_EPLLPZ_EEX_NUS-Z00_MBBLD": "US C3/C3= Exports (kbd)",
}


def graph_sections_input(page_id):
    return [
        # Stocks, 5 graphs
        ("Stocks", [f"{page_id}-graph-{i}" for i in range(1, 6)]),
        # Imports, 5 graphs
        ("Imports", [f"{page_id}-graph-{i}" for i in range(6, 11)]),
        # Production, 5 graphs
        ("Production", [f"{page_id}-graph-{i}" for i in range(11, 16)]),
        # Exports, 1 graph
        ("Exports", [f"{page_id}-graph-16"]),
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
