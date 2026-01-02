import pandas as pd
import numpy as np

def generate_refinery_yields(df):
    """Calculate TRUE refinery yields (excluding ethanol) from production and gross runs data

    Following EIA methodology:
    - For gasoline: subtract ethanol production from adjusted production
    - For distillate: use production as-is (biodiesel adjustments not available in weekly data)
    """
    df = df.copy()

    # Define the series we need
    gasoline_production = ['WGFRPUS2', 'WGFRPP12', 'WGFRPP22', 'WGFRPP32', 'WGFRPP42', 'WGFRPP52']
    ethanol_production = ['W_EPOOXE_YOP_NUS_MBBLD', 'W_EPOOXE_YOP_R10_MBBLD', 'W_EPOOXE_YOP_R20_MBBLD',
                         'W_EPOOXE_YOP_R30_MBBLD', 'W_EPOOXE_YOP_R40_MBBLD', 'W_EPOOXE_YOP_R50_MBBLD']
    distillate_production = ['WDIRPUS2', 'WDIRPP12', 'WDIRPP22', 'WDIRPP32', 'WDIRPP42', 'WDIRPP52']
    jet_production = ['WKJRPUS2', 'WKJRPP12', 'WKJRPP22', 'WKJRPP32', 'WKJRPP42', 'WKJRPP52']
    fueloil_production = ['WRERPUS2', 'WRERPP12', 'WRERPP22', 'WRERPP32', 'WRERPP42', 'WRERPP52']
    propane_production = ['WPRTP_NUS_2', 'WPRNPP12', 'WPRNPP22', 'WPRNPP32', 'W_EPLLPZ_YPT_R4N5_MBBLD']  # P4P5 combined
    gross_runs = ['WGIRIUS2', 'WGIRIP12', 'WGIRIP22', 'WGIRIP32', 'WGIRIP42', 'WGIRIP52']

    # Collect all needed IDs
    idsToInclude = gasoline_production + ethanol_production + distillate_production + jet_production + fueloil_production + propane_production + gross_runs
    df = df[df['id'].isin(idsToInclude)]
    df = df.pivot(index='period', columns='id', values='value')

    # Fill NaN ethanol values with 0 (some PADDs may have no ethanol production)
    for col in ethanol_production:
        if col in df.columns:
            df[col] = df[col].fillna(0)
        else:
            df[col] = 0

    # Calculate TRUE Refinery Gasoline Yields (excluding ethanol)
    # This represents what the refinery actually produces from crude oil
    # NOTE: All data is in daily averages (kbd)
    df['gasolineYieldUS'] = ((df['WGFRPUS2'] - df['W_EPOOXE_YOP_NUS_MBBLD']) / df['WGIRIUS2']) * 100
    df['gasolineYieldP1'] = ((df['WGFRPP12'] - df['W_EPOOXE_YOP_R10_MBBLD']) / df['WGIRIP12']) * 100
    df['gasolineYieldP2'] = ((df['WGFRPP22'] - df['W_EPOOXE_YOP_R20_MBBLD']) / df['WGIRIP22']) * 100
    df['gasolineYieldP3'] = ((df['WGFRPP32'] - df['W_EPOOXE_YOP_R30_MBBLD']) / df['WGIRIP32']) * 100
    df['gasolineYieldP4'] = ((df['WGFRPP42'] - df['W_EPOOXE_YOP_R40_MBBLD']) / df['WGIRIP42']) * 100
    df['gasolineYieldP5'] = ((df['WGFRPP52'] - df['W_EPOOXE_YOP_R50_MBBLD']) / df['WGIRIP52']) * 100

    # Calculate Blended Gasoline Yields (including ethanol) for comparison
    # This is what was incorrectly calculated before
    df['gasolineBlendedYieldUS'] = (df['WGFRPUS2'] / df['WGIRIUS2']) * 100
    df['gasolineBlendedYieldP1'] = (df['WGFRPP12'] / df['WGIRIP12']) * 100
    df['gasolineBlendedYieldP2'] = (df['WGFRPP22'] / df['WGIRIP22']) * 100
    df['gasolineBlendedYieldP3'] = (df['WGFRPP32'] / df['WGIRIP32']) * 100
    df['gasolineBlendedYieldP4'] = (df['WGFRPP42'] / df['WGIRIP42']) * 100
    df['gasolineBlendedYieldP5'] = (df['WGFRPP52'] / df['WGIRIP52']) * 100

    # Distillate Yields
    # NOTE: All data is in daily averages (kbd)
    df['distillateYieldUS'] = (df['WDIRPUS2'] / df['WGIRIUS2']) * 100
    df['distillateYieldP1'] = (df['WDIRPP12'] / df['WGIRIP12']) * 100
    df['distillateYieldP2'] = (df['WDIRPP22'] / df['WGIRIP22']) * 100
    df['distillateYieldP3'] = (df['WDIRPP32'] / df['WGIRIP32']) * 100
    df['distillateYieldP4'] = (df['WDIRPP42'] / df['WGIRIP42']) * 100
    df['distillateYieldP5'] = (df['WDIRPP52'] / df['WGIRIP52']) * 100

    # Jet Fuel Yields
    # NOTE: All data is in daily averages (kbd)
    df['jetYieldUS'] = (df['WKJRPUS2'] / df['WGIRIUS2']) * 100
    df['jetYieldP1'] = (df['WKJRPP12'] / df['WGIRIP12']) * 100
    df['jetYieldP2'] = (df['WKJRPP22'] / df['WGIRIP22']) * 100
    df['jetYieldP3'] = (df['WKJRPP32'] / df['WGIRIP32']) * 100
    df['jetYieldP4'] = (df['WKJRPP42'] / df['WGIRIP42']) * 100
    df['jetYieldP5'] = (df['WKJRPP52'] / df['WGIRIP52']) * 100

    # Fuel Oil Yields
    # NOTE: All data is in daily averages (kbd)
    df['fueloilYieldUS'] = (df['WRERPUS2'] / df['WGIRIUS2']) * 100
    df['fueloilYieldP1'] = (df['WRERPP12'] / df['WGIRIP12']) * 100
    df['fueloilYieldP2'] = (df['WRERPP22'] / df['WGIRIP22']) * 100
    df['fueloilYieldP3'] = (df['WRERPP32'] / df['WGIRIP32']) * 100
    df['fueloilYieldP4'] = (df['WRERPP42'] / df['WGIRIP42']) * 100
    df['fueloilYieldP5'] = (df['WRERPP52'] / df['WGIRIP52']) * 100

    # Propane/Propylene Yields (Note: P4 and P5 are combined for propane)
    # NOTE: All data is in daily averages (kbd)
    df['propaneYieldUS'] = (df['WPRTP_NUS_2'] / df['WGIRIUS2']) * 100
    df['propaneYieldP1'] = (df['WPRNPP12'] / df['WGIRIP12']) * 100
    df['propaneYieldP2'] = (df['WPRNPP22'] / df['WGIRIP22']) * 100
    df['propaneYieldP3'] = (df['WPRNPP32'] / df['WGIRIP32']) * 100
    # For P4 and P5, we need to combine gross runs since propane production is combined
    df['propaneYieldP4P5'] = (df['W_EPLLPZ_YPT_R4N5_MBBLD'] / (df['WGIRIP42'] + df['WGIRIP52'])) * 100

    # Calculate P9 yields (P2+P3+P4)
    # NOTE: All data is in daily averages (kbd)
    df['grossRunsP9'] = df['WGIRIP22'] + df['WGIRIP32'] + df['WGIRIP42']
    df['gasolineProductionP9'] = df['WGFRPP22'] + df['WGFRPP32'] + df['WGFRPP42']
    df['ethanolProductionP9'] = df['W_EPOOXE_YOP_R20_MBBLD'] + df['W_EPOOXE_YOP_R30_MBBLD'] + df['W_EPOOXE_YOP_R40_MBBLD']
    df['distillateProductionP9'] = df['WDIRPP22'] + df['WDIRPP32'] + df['WDIRPP42']
    df['jetProductionP9'] = df['WKJRPP22'] + df['WKJRPP32'] + df['WKJRPP42']
    df['fueloilProductionP9'] = df['WRERPP22'] + df['WRERPP32'] + df['WRERPP42']

    # TRUE refinery yields for P9 (excluding ethanol)
    df['gasolineYieldP9'] = ((df['gasolineProductionP9'] - df['ethanolProductionP9']) / df['grossRunsP9']) * 100
    df['gasolineBlendedYieldP9'] = (df['gasolineProductionP9'] / df['grossRunsP9']) * 100
    df['distillateYieldP9'] = (df['distillateProductionP9'] / df['grossRunsP9']) * 100
    df['jetYieldP9'] = (df['jetProductionP9'] / df['grossRunsP9']) * 100
    df['fueloilYieldP9'] = (df['fueloilProductionP9'] / df['grossRunsP9']) * 100

    # Create dictionary for yield mappings
    yield_dicts = {
        # TRUE Refinery Gasoline Yields (excluding ethanol)
        'gasolineYieldUS': 'US Gasoline Yield (pct)',
        'gasolineYieldP1': 'P1 Gasoline Yield (pct)',
        'gasolineYieldP2': 'P2 Gasoline Yield (pct)',
        'gasolineYieldP3': 'P3 Gasoline Yield (pct)',
        'gasolineYieldP4': 'P4 Gasoline Yield (pct)',
        'gasolineYieldP5': 'P5 Gasoline Yield (pct)',
        'gasolineYieldP9': 'P9 Gasoline Yield (pct)',
        # Blended Gasoline Yields (including ethanol)
        'gasolineBlendedYieldUS': 'US Gasoline Blended Yield (pct)',
        'gasolineBlendedYieldP1': 'P1 Gasoline Blended Yield (pct)',
        'gasolineBlendedYieldP2': 'P2 Gasoline Blended Yield (pct)',
        'gasolineBlendedYieldP3': 'P3 Gasoline Blended Yield (pct)',
        'gasolineBlendedYieldP4': 'P4 Gasoline Blended Yield (pct)',
        'gasolineBlendedYieldP5': 'P5 Gasoline Blended Yield (pct)',
        'gasolineBlendedYieldP9': 'P9 Gasoline Blended Yield (pct)',
        # Distillate Yields
        'distillateYieldUS': 'US Distillate Yield (pct)',
        'distillateYieldP1': 'P1 Distillate Yield (pct)',
        'distillateYieldP2': 'P2 Distillate Yield (pct)',
        'distillateYieldP3': 'P3 Distillate Yield (pct)',
        'distillateYieldP4': 'P4 Distillate Yield (pct)',
        'distillateYieldP5': 'P5 Distillate Yield (pct)',
        'distillateYieldP9': 'P9 Distillate Yield (pct)',
        # Jet Yields
        'jetYieldUS': 'US Jet Yield (pct)',
        'jetYieldP1': 'P1 Jet Yield (pct)',
        'jetYieldP2': 'P2 Jet Yield (pct)',
        'jetYieldP3': 'P3 Jet Yield (pct)',
        'jetYieldP4': 'P4 Jet Yield (pct)',
        'jetYieldP5': 'P5 Jet Yield (pct)',
        'jetYieldP9': 'P9 Jet Yield (pct)',
        # Fuel Oil Yields
        'fueloilYieldUS': 'US Fuel Oil Yield (pct)',
        'fueloilYieldP1': 'P1 Fuel Oil Yield (pct)',
        'fueloilYieldP2': 'P2 Fuel Oil Yield (pct)',
        'fueloilYieldP3': 'P3 Fuel Oil Yield (pct)',
        'fueloilYieldP4': 'P4 Fuel Oil Yield (pct)',
        'fueloilYieldP5': 'P5 Fuel Oil Yield (pct)',
        'fueloilYieldP9': 'P9 Fuel Oil Yield (pct)',
        # Propane Yields
        'propaneYieldUS': 'US Propane Yield (pct)',
        'propaneYieldP1': 'P1 Propane Yield (pct)',
        'propaneYieldP2': 'P2 Propane Yield (pct)',
        'propaneYieldP3': 'P3 Propane Yield (pct)',
        'propaneYieldP4P5': 'P4P5 Propane Yield (pct)',
    }

    yield_df = pd.DataFrame(yield_dicts.items(), columns=['id', 'name'])

    # Select only the yield columns and reshape
    df = df[yield_dicts.keys()]
    # Replace inf and -inf with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    # Round to 1 decimal place
    df = df.round(1)
    df = df.reset_index()
    df = pd.melt(df, id_vars=['period'], value_vars=yield_dicts.keys())
    df = pd.merge(df, yield_df, on='id', how='left')

    return df

def generate_additional_calculation(df):
    df = df.copy()
    crudeRuns = ['WCRRIUS2','WCRRIP12','WCRRIP22','WCRRIP32','WCRRIP42','WCRRIP52',]
    grossRuns = ['WGIRIUS2','WGIRIP12','WGIRIP22','WGIRIP32','WGIRIP42','WGIRIP52',]    
    crudeStocks = ['WCESTUS1','WCESTP11','WCESTP21','WCESTP31','WCESTP41','WCESTP51','W_EPC0_SAX_YCUOK_MBBL']    
    crudeImports = ['WCEIMUS2','WCEIMP12','WCEIMP22','WCEIMP32','WCEIMP42','WCEIMP52',]
    idsToInclude = crudeRuns + grossRuns + crudeStocks + crudeImports
    df = df[df['id'].isin(idsToInclude)]
    df = df.pivot(index='period',columns='id',values='value')
    
    #Feedstock Inputs into Refineries
    df['feedstockRunsUS'] = df['WGIRIUS2'] - df['WCRRIUS2']
    df['feddStockRunsP1'] = df['WGIRIP12'] - df['WCRRIP12']
    df['feedstockRunsP2'] = df['WGIRIP22'] - df['WCRRIP22']
    df['feedstockRunsP3'] = df['WGIRIP32'] - df['WCRRIP32']
    df['feedstockRunsP4'] = df['WGIRIP42'] - df['WCRRIP42']
    df['feedstockRunsP5'] = df['WGIRIP52'] - df['WCRRIP52']
    
    #P9 Crude Runs
    df['crudeRunsP9'] = df['WCRRIP22'] + df['WCRRIP32'] + df['WCRRIP42']
    #P9 Gross Runs
    df['grossRunsP9'] = df['WGIRIP22'] + df['WGIRIP32'] + df['WGIRIP42']
    #P9 Feedstock Runs
    df['feedstockRunsP9'] = df['grossRunsP9'] - df['crudeRunsP9']
    #P9 Crude Stocks
    df['crudeStocksP9'] = df['WCESTP21'] + df['WCESTP31'] + df['WCESTP41']
    #P9 Crude Imports
    df['crudeImportsP9'] = df['WCEIMP22'] + df['WCEIMP32'] + df['WCEIMP42']
    #P2E crudeStocksP2E
    df['crudeStocksP2E'] = df['WCESTP21'] - df['W_EPC0_SAX_YCUOK_MBBL']    

    wps_dicts = {
        'feedstockRunsUS' : 'US Feedstock Runs (kbd)',
        'feddStockRunsP1' : 'P1 Feedstock Runs (kbd)',
        'feedstockRunsP2' : 'P2 Feedstock Runs (kbd)',
        'feedstockRunsP3' : 'P3 Feedstock Runs (kbd)',
        'feedstockRunsP4' : 'P4 Feedstock Runs (kbd)',
        'feedstockRunsP5' : 'P5 Feedstock Runs (kbd)',
        'crudeRunsP9' : 'P9 Crude Runs (kbd)',
        'grossRunsP9' : 'P9 Gross Runs (kbd)',
        'feedstockRunsP9' : 'P9 Feedstock Runs (kbd)',
        'crudeStocksP9' : 'P9 Stocks (kb)',
        'crudeImportsP9' : 'P9 Crude Imports (kbd)',
        'crudeStocksP2E' : 'P2E Stocks (kb)',
        }
    wps_df = pd.DataFrame(wps_dicts.items(), columns=['id','name'])

    df = df[wps_dicts.keys()]
    df = df.reset_index()
    df = pd.melt(df, id_vars=['period'], value_vars=wps_dicts.keys())
    df = pd.merge(df, wps_df, on='id', how='left')
    return df

def generate_adjustment_factor(raw):
    df = raw.copy()
    ids = ['WCRSTUS1','WCRFPUS2','WCEIMUS2','WCRRIUS2','WCREXUS2']
    df = df[df['id'].isin(ids)]
    pv = df.pivot(index='period',columns='id',values='value')
    pv['stock_change'] = pv['WCRSTUS1'].diff() / 7
    pv['adjustment_factor'] = (pv['WCRFPUS2'] + pv['WCEIMUS2'] - pv['WCRRIUS2'] - pv['WCREXUS2'] - pv['stock_change']) * -1
    pv = pv.dropna(subset=['adjustment_factor'])
    pv['adjustment_factor'] = pd.to_numeric(pv['adjustment_factor'], errors='coerce').round(0)
    pv['adjustment_factor'] = pv['adjustment_factor'].astype(int)
    pv['adjustment_factor'] = pv['adjustment_factor'].astype(object)
    pv = pv[['adjustment_factor']].reset_index()
    pv = pv.rename_axis(None, axis=1)
    pv = pv.rename(columns={'adjustment_factor':'value'})
    pv['name'] = 'OG Adjustment Factor (kbd)'
    pv['id'] = 'crudeOriginalAdjustment'
    raw = pd.concat([raw, pv])
    return raw

def generate_additional_tickers(df):
    df = df.copy()
    # Generate feedstock and P9 calculations
    dff = generate_additional_calculation(df)
    df = pd.concat([df, dff])
    # Generate adjustment factor
    df = generate_adjustment_factor(df)
    # Generate refinery yields
    yields_df = generate_refinery_yields(df)
    df = pd.concat([df, yields_df])
    # Clean up
    df = df.drop(columns=['name'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df