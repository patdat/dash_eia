import pandas as pd
from utils_steo.find_last_update import updatecompiler
from utils_steo.create_more_files import main as create_more_files

def get_last_release():
    df = updatecompiler()
    end_date = df['new_release_date'][0].replace(day=1)  
    return end_date

def get_download_list(offset_month):
    end_month = get_last_release()
    start_month = end_month - pd.DateOffset(months=offset_month-1)

    months = pd.date_range(start_month,end_month,freq='MS')
    df = pd.DataFrame(months,columns=['date'])
    #df['year'] last two digits of year
    df['year'] = df['date'].dt.strftime('%y').astype(str)
    df['monthStr'] = df['date'].dt.strftime('%b').str.lower()
    df['dates'] = df['monthStr'] + df['year']
    df['url'] = 'https://www.eia.gov/outlooks/steo/archives/' + df['dates'] + '_base.xlsx'
    df = df.sort_values(by='date',ascending=False).reset_index(drop=True)
    df = df.rename(columns={'date':'release_date'})
    return df


class steo:
    def __init__(self):
        self.meta = pd.read_csv("lookup/steo/metadata_steo.csv")

    def _get_file(self, pathname):
        xlsx = pd.read_excel(pathname, sheet_name=None, header=2)
        del xlsx["Dates"]
        del xlsx["Contents"]
        df = pd.concat(xlsx, ignore_index=True)
        return df

    def _clean_data(self, df):

        df = df.rename(columns={"Forecast date:": "id", "Unnamed: 1": "name"})
        df = df.dropna(subset=["id"])

        if df.columns[-1] == 'Unnamed: 0':
            df = df.drop(df.columns[-1], axis=1)

        col = df.columns.tolist()
        col = [str(i) for i in col]
        for i in range(len(col)):
            if "Unnamed" in col[i]:
                col[i] = col[i - 1]
        col = col[2:]
        col = [str(i) for i in col]

        frow = df.iloc[0].tolist()
        frow = frow[2:]

        combined = [str(x) + "-" + str(y) + "-01" for x, y in zip(col, frow)]
        combined = [pd.to_datetime(i, format="%Y-%b-%d") for i in combined]
        combined = [i.strftime("%Y-%m-%d") for i in combined]
        combined = ["id", "name"] + combined

        df.columns = combined

        df.drop(df[df["id"].str.contains("Table of Contents")].index, inplace=True)
        df.drop(df[df["id"].str.contains(df.iloc[0, 0])].index, inplace=True)
        df.drop(df.columns[1], axis=1, inplace=True)
        df.drop_duplicates(inplace=True)

        return df

    def _unpivot_data(self, df):
        df = pd.melt(
            df,
            id_vars="id",
            value_vars=df.columns[1:],
            var_name="period",
            value_name="value",
        )
        df["value"] = df["value"].fillna(0)
        df["value"] = df["value"].apply(pd.to_numeric, errors="coerce")

        return df

    def _add_meta(self, df):
        df = pd.merge(df, self.meta, left_on="id", right_on="id", how="left")
        # move the value column to the last column
        df = df[["id", "name", "uom", "period", "value", "release_date"]]
        return df

    def get_data(self, pathname):
        df = self._get_file(pathname)
        df = self._clean_data(df)
        df = self._unpivot_data(df)
        return df

    def get_all(self,offset_months=3):

        # df = self.get_data('https://www.eia.gov/outlooks/steo/archives/jan24_base.xlsx')

        dfDates = get_download_list(offset_months)

        df = pd.DataFrame()
        for i in range(len(dfDates)):
            pathname = "https://www.eia.gov/outlooks/steo/archives/{}_base.xlsx".format(
                dfDates["dates"][i]
            )
            print(f"downloading: {pathname}")
            try:
                df2 = self.get_data(pathname)
                df2["release_date"] = dfDates["release_date"][i]
                df = pd.concat([df, df2], ignore_index=True)
            except:
                print(f"error: {pathname}")
                break
        df["id"] = df["id"].str.upper()
        df = self._add_meta(df)
        df = df.drop_duplicates()
        df = df.dropna(subset=['value'])
        df = df.dropna(subset=['name'])
        
        df = pd.pivot_table(df, index=['id','name','release_date','uom'], columns='period', values='value').reset_index()
        df.to_feather('./data/steo/steo_pivot.feather')        
        
        create_more_files()
        
        return df

def main(offset_months=3):
    df = steo().get_all(offset_months)
    return df

def read_pivot():
    df = pd.read_feather('./data/steo/steo_pivot.feather')
    return df

def melt_pivot():
    df = pd.read_pivot()
    df = pd.melt(df, id_vars=['id','name','uom','release_date'], var_name='period', value_name='value')
    
    cols = df.columns
    meta = ['id','name','release_date']
    cols = [i for i in cols if i not in meta]

    df = pd.melt(df, id_vars=meta, value_vars=cols, var_name='period', value_name='value')
    return df

if __name__ == "__main__":
    df = main(5)