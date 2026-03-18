import os
import pandas as pd
from eia_downloads.cli.findallupdates import updatecompiler
from eia_downloads.cli.download import main as download
from eia_downloads import config

def checkIfFileExists():
    path = config.get_data_path("cli", "companylevelimports.parquet")
    if not os.path.exists(path):
        df = download()
        df.to_parquet(str(path), index=False, compression='zstd', engine='pyarrow')
        df = df[df['PROD_NAME']=='Crude Oil']
        df.to_parquet(str(config.get_data_path("cli", "companylevelimports_crude.parquet")), index=False, compression='zstd', engine='pyarrow')


def main():

    checkIfFileExists()

    dfUpdater = updatecompiler()
    release_date = dfUpdater['new_release_date'][0]
    needsUpdating = dfUpdater['needsUpdating'][0]

    if needsUpdating:
        try:
            print('New data available. Updating...')
            df = download()
            df.to_parquet(str(config.get_data_path("cli", "companylevelimports.parquet")), index=False, compression='zstd', engine='pyarrow')

            df = df[df['PROD_NAME']=='Crude Oil']
            df.to_parquet(str(config.get_data_path("cli", "companylevelimports_crude.parquet")), index=False, compression='zstd', engine='pyarrow')

            releaseFile = pd.DataFrame({'category': ['cli'], 'release_date': [release_date]})
            releaseFile.to_csv(config.get_lookup_path("release_dates.csv"), index=False)

        except:
            print('Error updating data.')
    else:
        print('No new data available. Using existing data.')

if __name__ == '__main__':
    main()
