#######################################################################
### MANUAL INPUTS #####################################################

region = "permian"

idents = [
    # first row
    "COPRAP",
    "RIGSAP",
    "NWDAP",
    "NWRAP",
    "NWCAP",
    "DUCSAP",
    # second row
    "CONWAP",
    "CONWRAP",
    "COEOPAP",
    "NGMPAP",
    "NGNWAP",
    "NGNWRAP",
    # third row
    "NGEOPAP",
]


def graph_sections_input(page_id):
    return [
        # Stocks, 6 graphs
        ("Stocks", [f"{page_id}-graph-{i}" for i in range(1, 7)]),
        # Imports, 6 graphs
        ("Imports", [f"{page_id}-graph-{i}" for i in range(7, 13)]),
        # Exports, 1 graph
        ("Exports", [f"{page_id}-graph-13"]),
    ]


### END MANUAL INPUTS #################################################
#######################################################################


from app import app
import os
from utils_steo.calcs import create_callbacks, create_layout
from utils_steo.chart_dpr import get_regional_dict_data

region_dct = get_regional_dict_data(region)

idents_list = idents


# Page-specific variables
page_id = os.path.basename(__file__).split(".")[0]
num_graphs = len(idents_list)

# Create the layout for the current page
layout = create_layout(page_id, region, graph_sections_input(page_id))

# Create callbacks for the app
create_callbacks(app, page_id, num_graphs, idents_list, region_dct)

if __name__ == "__main__":
    app.layout = layout
    app.run_server(debug=True, port=8051)
