#######################################################################
### MANUAL INPUTS #####################################################

commodity = "Refining: "

idents = {
    # Crude Refinery Utilizaiton
    "WPULEUS3": "US Refinery Utilization (pct)",
    "W_NA_YUP_R10_PER": "P1 Refinery Utilization (pct)",
    "W_NA_YUP_R20_PER": "P2 Refinery Utilization (pct)",
    "W_NA_YUP_R30_PER": "P3 Refinery Utilization (pct)",
    "W_NA_YUP_R40_PER": "P4 Refinery Utilization (pct)",
    "W_NA_YUP_R50_PER": "P5 Refinery Utilization (pct)",
    # Feedstock Runs
    "feedstockRunsUS": "US Feedstock Runs (kbd)",
    "feddStockRunsP1": "P1 Feedstock Runs (kbd)",
    "feedstockRunsP2": "P2 Feedstock Runs (kbd)",
    "feedstockRunsP3": "P3 Feedstock Runs (kbd)",
    "feedstockRunsP4": "P4 Feedstock Runs (kbd)",
    "feedstockRunsP5": "P5 Feedstock Runs (kbd)",
    # Gross Runs
    "WGIRIUS2": "US Gross Runs (kbd)",
    "WGIRIP12": "P1 Gross Runs (kbd)",
    "WGIRIP22": "P2 Gross Runs (kbd)",
    "WGIRIP32": "P3 Gross Runs (kbd)",
    "WGIRIP42": "P4 Gross Runs (kbd)",
    "WGIRIP52": "P5 Gross Runs (kbd)",
    # Operable CDU Capacity
    "WOCLEUS2": "US CDU Capacity (kbd)",
    "W_NA_YRL_R10_MBBLD": "P1 CDU Capacity (kbd)",
    "W_NA_YRL_R20_MBBLD": "P2 CDU Capacity (kbd)",
    "W_NA_YRL_R30_MBBLD": "P3 CDU Capacity (kbd)",
    "W_NA_YRL_R40_MBBLD": "P4 CDU Capacity (kbd)",
    "W_NA_YRL_R50_MBBLD": "P5 CDU Capacity (kbd)",
}


def graph_sections_input(page_id):
    return [
        # utilization, 6 graphs
        ("Refinery Utilization", [f"{page_id}-graph-{i}" for i in range(1, 7)]),
        # feed, 6 graphs
        ("Feedstock Runs", [f"{page_id}-graph-{i}" for i in range(7, 13)]),
        # gross, 6 graphs
        ("Gross Runs", [f"{page_id}-graph-{i}" for i in range(13, 19)]),
        # capacity, 6 graphs
        ("Operable CDU Capacity", [f"{page_id}-graph-{i}" for i in range(19, 25)]),
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
