from utils_wps.mapping import production_mapping
from utils_wps.calculation import get_initial_data 
import pandas as pd

def format_value(val, column_name):
    if "stocks" in column_name.lower():
        val = val/1000
    return val

def generate_line_data():
    df = get_initial_data()
    df.set_index('period', inplace=True)
    cols = df.columns
    df.columns = [production_mapping[col] for col in cols]
    for column in df.columns:
        df[column] = df[column].apply(lambda x: format_value(x, column))
    reversed_mapping = {v: k for k, v in production_mapping.items()}
    df.columns = [reversed_mapping[col] for col in df.columns]
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.round(1)
    df.reset_index(inplace=True)
    df.to_feather('./data/wps/graph_line_data.feather')
    
if __name__ == "__main__":
    generate_line_data()    