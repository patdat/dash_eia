import pandas as pd
from eia_downloads import config

def get_dpr_ids():
    df = pd.read_feather(str(config.get_data_path("steo", "steo_pivot.feather")))
    mapping_dpr = pd.read_csv(config.get_lookup_path("steo", "mapping_dpr.csv"))

    lst = mapping_dpr['id'].tolist()
    lst = list(dict.fromkeys(lst))

    df = df[df['id'].isin(lst)]
    df = df.reset_index(drop=True)

    df.to_feather(str(config.get_data_path("steo", "steo_pivot_dpr.feather")))

    return df

def get_other_dpr_ids():
    df = pd.read_feather(str(config.get_data_path("steo", "steo_pivot.feather")))
    mapping_dpr = pd.read_csv(config.get_lookup_path("steo", "mapping_dpr_other.csv"))

    lst = mapping_dpr['id'].tolist()
    lst = list(dict.fromkeys(lst))

    df = df[df['id'].isin(lst)]
    df = df.reset_index(drop=True)

    df.to_feather(str(config.get_data_path("steo", "steo_pivot_dpr_other.feather")))

def main():
    df = get_dpr_ids()
    get_other_dpr_ids()
    return df

if __name__ == '__main__':
    df = main()
