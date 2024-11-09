import pandas as pd

def get_dpr_ids():
    df = pd.read_feather('./data/steo/steo_pivot.feather')
    mapping_dpr = pd.read_csv('./lookup/steo/mapping_dpr.csv')

    lst = mapping_dpr['id'].tolist()
    lst = list(dict.fromkeys(lst))
    
    df = df[df['id'].isin(lst)]    
    
    df.to_feather('data/steo/steo_pivot_dpr.feather')

def main():
    get_dpr_ids()
    
if __name__ == '__main__':
    main()
