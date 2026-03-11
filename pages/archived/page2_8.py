#######################################################################
### MANUAL INPUTS #####################################################

commodity = "Demand: "

idents = {
    "WRPUPUS2": "Products Supplied (kbd)",
    "WGFUPUS2": "Gasoline Supplied (kbd)",
    "WDIUPUS2": "Distillate Supplied (kbd)",
    "WKJUPUS2": "Jet Supplied (kbd)",
    "WREUPUS2": "Fuel Oil Supplied (kbd)",
    "WPRUP_NUS_2": " C3/C3= Supplied (kbd)",
    "WWOUP_NUS_2": "Other Oils Supplied (kbd)",
}


def graph_sections_input(page_id):
    return [
        # Products Supplied, 7 graphs
        ("Products Supplied", [f"{page_id}-graph-{i}" for i in range(1, 8)]),
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
