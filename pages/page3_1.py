#######################################################################
### MANUAL INPUTS #####################################################

idents = [
# Main    
    'COPRPUS',
    'PAPRPGLF',    
    'PAPR48NGOM',        
    'PAPRPAK',    
    # Permian
    'COPRPM',
    'RIGSPM',
    'NWDPM',
    'NWRPM',
    'NWCPM',
    'DUCSPM',
    'CONWPM',
    'CONWRPM',
    'COEOPPM',
    'NGMPPM',
    'NGNWPM',
    'NGNWRPM',
    'NGEOPPM',   
    # Bakken
    'COPRBK',
    'RIGSBK',
    'NWDBK',
    'NWRBK',
    'NWCBK',
    'DUCSBK',
    'CONWBK',
    'CONWRBK',
    'COEOPBK',
    'NGMPBK',
    'NGNWBK',
    'NGNWRBK',
    'NGEOPBK',    
    # Eagle Ford
    'COPREF',
    'RIGSEF',
    'NWDEF',
    'NWREF',
    'NWCEF',
    'DUCSEF',
    'CONWEF',
    'CONWREF',
    'COEOPEF',
    'NGMPEF',
    'NGNWEF',
    'NGNWREF',
    'NGEOPEF',    
    # Appalachia
    "COPRAP",
    "RIGSAP",
    "NWDAP",
    "NWRAP",
    "NWCAP",
    "DUCSAP",
    "CONWAP",
    "CONWRAP",
    "COEOPAP",
    "NGMPAP",
    "NGNWAP",
    "NGNWRAP",
    "NGEOPAP",
    # Rest of L48 ex GOM
    'COPRR48',
    'RIGSR48',
    'NWDR48',
    'NWRR48',
    'NWCR48',
    'DUCSR48',
    'CONWR48',
    'CONWRR48',
    'COEOPR48',
    'NGMPR48',
    'NGNWR48',
    'NGNWRR48',
    'NGEOPR48',    
    # Haynesville
    'COPRHA',
    'RIGSHA',
    'NWDHA',
    'NWRHA',
    'NWCHA',
    'DUCSHA',
    'CONWHA',
    'CONWRHA',
    'COEOPHA',
    'NGMPHA',
    'NGNWHA',
    'NGNWRHA',
    'NGEOPHA',
]

def graph_sections_input(page_id):
    return [
        ("Totals by Crude Production", [f"{page_id}-graph-{i}" for i in range(1, 5)]),
        ("Permian", [f"{page_id}-graph-{i}" for i in range(5, 18)]),
        ("Bakken", [f"{page_id}-graph-{i}" for i in range(18, 31)]),
        ("Eagle Ford", [f"{page_id}-graph-{i}" for i in range(31, 44)]),
        ("Appalachia", [f"{page_id}-graph-{i}" for i in range(44, 57)]),
        ("Rest of L48 ex GOM", [f"{page_id}-graph-{i}" for i in range(57, 70)]),
        ("Haynesville", [f"{page_id}-graph-{i}" for i in range(70, 83)]),        
    ]
    
### END MANUAL INPUTS #################################################
#######################################################################


from app import app
import os
from utils_steo.calcs import create_callbacks, create_layout
from utils_steo.chart_dpr import get_regional_dict_data

region_dct = get_regional_dict_data(None)

idents_list = idents


# Page-specific variables
page_id = os.path.basename(__file__).split(".")[0]

num_graphs = len(idents_list)

# Create the layout for the current page
layout = create_layout(page_id, "Region: ", graph_sections_input(page_id))

# Create callbacks for the app
create_callbacks(app, page_id, num_graphs, idents_list, region_dct)

if __name__ == "__main__":
    # region_dct = get_regional_dict_data(None)
    # print(region_dct)
    app.layout = layout
    app.run_server(debug=True, port=8051)
    
        