import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

def clean_release_date(release_date):
    """Clean and format release date."""
    cleaned_date = release_date.replace('\t', '').replace('\xa0', '').replace('|', '').strip()
    date_formats = ["%b. %d, %Y", "%B %d, %Y"]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(cleaned_date, date_format)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue

def fetch_html(url):
    """Fetch HTML content from the given URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')

def get_release_date_from_soup(soup, category):
    """Retrieve the release date using the appropriate method based on the category."""
    mapping = {
        'cli': lambda s: s.find('div', class_='release-dates').find('span', class_='date').get_text(),
    }
    
    return mapping.get(category)(soup)

def get_release_date(category):
    """Retrieve release date based on the given category."""
    urls = {
        'cli': 'https://www.eia.gov/petroleum/imports/companylevel/',
    }
    
    soup = fetch_html(urls.get(category))
    release_date = get_release_date_from_soup(soup, category)
    
    return clean_release_date(release_date)


def updater():
    """Update and return DataFrame with release dates for each category."""
    categories = ['cli']
    release_dates = {category: get_release_date(category) for category in categories}
    
    df = pd.DataFrame(release_dates, index=[1]).T.reset_index()
    df.columns = ['category', 'release_date']
    #convert 'release_date' to pd.datetime
    df['release_date'] = pd.to_datetime(df['release_date'])
    
    return df

def updatecompiler():
    old = pd.read_csv('./lookup/release_dates.csv',parse_dates=['release_date'])
    old = old.rename(columns={'release_date':'old_release_date'})    
    new = updater()
    new = new.rename(columns={'release_date':'new_release_date'})
    df = pd.merge(old,new,on='category',how='left')
    df['needsUpdating'] = df['old_release_date'] < df['new_release_date']
    return df    

if __name__ == "__main__":
    df = updatecompiler()
    print(df)