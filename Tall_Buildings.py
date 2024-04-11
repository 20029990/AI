import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3

def scrape_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', class_='wikitable')

    data = []
    for row in table.findthere_all('tr')[1:]:
        columns = row.find_all('td')
        building_name = columns[0].text.strip()
        height = columns[1].text.strip()
        location = columns[2].text.strip()
        data.append({'Building Name': building_name, 'Height': height, 'Location': location})

    return data

def preprocess_data(data):
    df = pd.DataFrame(data)

    return df

def save_to_database(df, db_file, table_name):
    conn = sqlite3.connect(db_file)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

def main():
    url = 'https://en.wikipedia.org/wiki/List_of_tallest_buildings_and_structures_in_the_world'
    data = scrape_data(url)
    df = preprocess_data(data)

    db_file = 'tallest_buildings_data.db'
    table_name = 'tallest_buildings'
    save_to_database(df, db_file, table_name)
    print("Data saved to SQLite database successfully.")

if __name__ == "__main__":
    main()
