import pandas as pd
from utils_steo import calcs

def get_dpr_regions():
    df = calcs.read_pivot_master()
    mask1 = df['name'].str.contains('active rigs',case=False)
    mask2 = ~df['name'].str.contains('per rig',case=False)
    regions = df[mask1 & mask2][['id','name']].drop_duplicates()
    regions = regions['name'].tolist()
    regions = [x.replace(' active rigs','') for x in regions]
    return regions


def get_dpr_ids():
    df = calcs.read_pivot_master()
    regions = get_dpr_regions()

    dff_region = pd.DataFrame()
    for region in regions:
        mask1 = df['name'].str.contains(f'{region}',case=False)
        mask2 = ~df['name'].str.contains('per rig',case=False)
        mask3 = ~df['name'].str.contains('coal',case=False)    
        df_region = df[mask1 & mask2 & mask3][['id','name']].drop_duplicates().reset_index(drop=True)
        df_region = df[mask1 & mask3][['id','name']].drop_duplicates().reset_index(drop=True)
        df_region['region'] = region
        dff_region = pd.concat([dff_region,df_region],axis=0)
    dff_region = dff_region.drop_duplicates().reset_index(drop=True)

    lst = dff_region['id'].tolist()
    
    df = df[df['id'].isin(lst)]    
    
    df.to_feather('data/steo/steo_pivot_dpr.feather')

    return df


def main():
    df = get_dpr_ids()