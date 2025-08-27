import pandas as pd
# from src.cli.uploader import cloud
from src.cli.findallupdates import updatecompiler
from src.cli.download import main as download

def checkIfFileExists():
    import os
    if not os.path.exists('./data/cli/companylevelimports.parquet'):
        df = download()
        df.to_parquet('./data/cli/companylevelimports.parquet', index=False, compression='zstd', engine='pyarrow')
        df = df[df['PROD_NAME']=='Crude Oil']
        df.to_parquet('./data/cli/companylevelimports_crude.parquet', index=False, compression='zstd', engine='pyarrow')


def main():

    checkIfFileExists()

    dfUpdater = updatecompiler()
    release_date = dfUpdater['new_release_date'][0]
    needsUpdating = dfUpdater['needsUpdating'][0]

    if needsUpdating:
        try:
            print('New data available. Updating...')
            df = download()
            df.to_parquet('data/companylevelimports.parquet', index=False, compression='zstd', engine='pyarrow')
            # cloud(df, 'regulatory/eia/companylevel', 'companylevelimports.csv',df_index=False)
            
            df = df[df['PROD_NAME']=='Crude Oil']
            df.to_parquet('data/companylevelimports_crude.parquet', index=False, compression='zstd', engine='pyarrow')
            # cloud(df, 'regulatory/eia/companylevel', 'companylevelimports_crude.csv',df_index=False)

            releaseFile = pd.DataFrame({'category': ['wps'], 'release_date': [release_date]})
            releaseFile.to_csv('./lookup/release_dates.csv', index=False)
            
            # Clear cache after updating data
            try:
                from src.utils.data_loader import invalidate_data_cache
                print("Clearing cache after CLI data update...")
                invalidate_data_cache()
            except Exception as e:
                print(f"Cache invalidation notice: {e}")        
            
        except:
            print('Error updating data.')
    else:
        print('No new data available. Using existing data.')
        
if __name__ == '__main__':
    main()