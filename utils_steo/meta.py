import requests
import pandas as pd


def download_api():
    base_url = "https://api.eia.gov/v2/steo/data/"
    api_key = "6EF7F9D5C3541865CEC21B793BAC4433"  # Replace with your EIA API key
    params = {
        "api_key": api_key,
        "frequency": "monthly",
        "data[0]": "value",
        "start": "2015-01",
        "offset": 0,  # Start with an offset of 0
        "length": 5000,  # Number of records per request (adjust as needed)
    }
    all_data = []
    while True:
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            series_data = data.get("response", {}).get("data", [])
            all_data.extend(series_data)
            if len(series_data) < params["length"]:
                break
            else:
                params["offset"] += params["length"]
                print(f"Downloading steo via API Call | Offset: {params['offset']}")

        else:
            print("Error:", response.status_code)
            break
    df = pd.DataFrame(all_data)
    return df


def create_csv(df):
    df = df.rename(
        columns={"seriesId": "id", "seriesDescription": "name", "unit": "uom"}
    )
    df = df[["id", "name", "uom", "period", "value"]]
    df["release_date"] = "1900-01-01"
    df["id"] = df["id"].str.upper()
    df = df.sort_values(by=["id", "period"])
    df['period'] = pd.to_datetime(df['period'])
    df['id'] = df['id'].str.upper()
    df['name'] = df['name'].str.lower()
    df['uom'] = df['uom'].str.lower()    
    shorthand_replacement = pd.read_csv('./lookup/steo/unit_shorthand_steo.csv')
    df['uom'] = df['uom'].replace(shorthand_replacement.set_index('unit')['shorthand'].to_dict())  
    
    df = df[~df['name'].str.contains('retail padd')]
    df.loc[(df['uom'].isnull()) & (df['name'].str.contains('wells')), 'uom'] = 'count'
    df.loc[(df['uom'].isnull()) & (df['name'].str.contains('rigs')), 'uom'] = 'count'
      
    return df


def create_meta(df):
    df = df.copy()
    df = df[["id", "name", "uom"]]
    df = df.drop_duplicates()
    return df


def main():
    df = download_api()
    df = create_csv(df)
    meta = create_meta(df)
    meta.to_csv("./lookup/steo/metadata_steo.csv", index=False)
    
    return df


if __name__ == "__main__":
    df = main()
