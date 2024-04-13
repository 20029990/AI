import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
import geocoder

@st.cache_data
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

def push_to_mongodb(data, db_name, collection_name):
    with MongoClient('localhost', 27017) as client:
        db = client[db_name]
        collection = db[collection_name]
        collection.insert_many(data.to_dict('records'))

def suggest_activity(df):
  sunny_conditions = df['weather_description'].str.contains('clear sky', case=False)
  rainy_conditions = df['weather_description'].str.contains('rain', case=False)
  snowy_conditions = df['weather_description'].str.contains('snow', case=False)
  avg_temperature = df['temperature'].mean()
  warm_conditions = (avg_temperature >= 20) & (avg_temperature <= 30)
  cold_conditions = avg_temperature < 0

  if sunny_conditions.any() and warm_conditions:
    return "It's going to be sunny and warm! How about a picnic or a visit to the park?"
  elif rainy_conditions.any():
    return "Looks like it might rain. Don't forget your umbrella! It's a perfect day for visiting a museum or reading a book."
  elif snowy_conditions.any() or cold_conditions:
    return "Brrr, it's going to be cold! How about making a snowman, going skiing, or staying in with a hot cup of cocoa?"
  else:
    return "The weather looks great! You should visit this city."


def plot_weather_distribution(df):
    weather_counts = df['weather_description'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(weather_counts, labels=weather_counts.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.tight_layout()
    st.pyplot(fig)

def plot_temperature_trend(df):
    fig, ax = plt.subplots()
    ax.plot(df['time'], df['temperature'], marker='o', linestyle='-')
    ax.set_xlabel('Time')
    ax.set_ylabel('Temperature (°C)')
    ax.set_title('Temperature Trend')
    st.pyplot(fig)

def plot_weather_map(city_name):

    location = geocoder.osm(city_name).latlng

    m = folium.Map(location=location, zoom_start=13)

    folium.Marker(location, popup=city_name).add_to(m)

    folium_static(m)

def main():
  st.title("Welcome to Weather Forecast!")
   
  city_name = st.sidebar.text_input("Enter city name:")
  api_key = st.sidebar.text_input("Enter OpenWeatherMap API key:")
  get_weather = st.sidebar.button("Get Weather Forecast")

  if get_weather:
    st.write("Fetching weather data...")
    hourly_weather_data = get_hourly_weather(city_name, api_key)
    if hourly_weather_data:
      df = preprocess_hourly_weather(hourly_weather_data)
      st.session_state['df'] = df
      st.write("Hourly Weather Forecast:")
      st.write(df)
       
      st.write("Analysis:")
      suggestion = suggest_activity(df)
      st.write(suggestion)

  if 'df' in st.session_state:
    df = st.session_state['df']

    plot_option = st.sidebar.selectbox("Select Plot", ["Weather Description Distribution", "Temperature Trend", "Interactive Weather Map"])
    if plot_option == "Weather Description Distribution":
      st.write("Weather Description Distribution:")
      plot_weather_distribution(df)
    elif plot_option == "Temperature Trend":
      st.write("Temperature Trend:")
      plot_temperature_trend(df)
    elif plot_option == "Interactive Weather Map":
      st.write("Interactive Weather Map:")
      plot_weather_map(city_name)
       
    if st.sidebar.checkbox("Push to MongoDB"):
      push_to_mongodb(df, 'weather_db', 'hourly_weather')
      st.write("Weather data successfully pushed to MongoDB.")
  else:
    st.write("Failed to fetch weather data.")
   
if __name__ == "__main__":
  main()