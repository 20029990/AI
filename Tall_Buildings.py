import requests
import pandas as pd
import sqlite3
from datetime import datetime

def get_hourly_weather(city_name, api_key):
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city_name,
        "appid": api_key,
        "units": "metric"
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code == 200:
        hourly_forecast = []
        for forecast in data['list']:
            time = datetime.strptime(forecast['dt_txt'], '%Y-%m-%d %H:%M:%S')
            weather_description = forecast['weather'][0]['description']
            temperature = forecast['main']['temp']
            humidity = forecast['main']['humidity']
            wind_speed = forecast['wind']['speed']
            hourly_forecast.append({
                'time': time,
                'weather_description': weather_description,
                'temperature': temperature,
                'humidity': humidity,
                'wind_speed': wind_speed
            })
        return hourly_forecast
    else:
        return None

def preprocess_hourly_weather(hourly_weather_data):
    df = pd.DataFrame(hourly_weather_data)

    df.dropna(inplace=True)

    df['time'] = pd.to_datetime(df['time'])

    df['temperature'] = df['temperature'].round(2)

    df['humidity'] = df['humidity'].astype(int)
    df['wind_speed'] = df['wind_speed'].astype(int)

    return df

def create_sqlite_table(df, db_name, table_name):
    conn = sqlite3.connect(db_name)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

city = "Dublin"
api_key = "56549c0f2ba37c783450e6bff8d8951c"
hourly_weather_data = get_hourly_weather(city, api_key)

if hourly_weather_data:

    df = preprocess_hourly_weather(hourly_weather_data)

    print(df)

    db_name = 'weather_data.db'
    table_name = 'hourly_weather'
    create_sqlite_table(df, db_name, table_name)

    print("\nWeather data successfully stored in SQLite database.\n")
else:
    print("\nFailed to fetch weather data.\n")
