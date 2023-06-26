##!pip install chart_studio
##!pip install config
## !pip install requirement.txt
import config
import requests
import pickle
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
import warnings
import requests
import argparse
from datetime import date
import time
import statistics

import plotly.express as px 
from chart_studio import plotly as py
from plotly.graph_objs import *
import plotly.graph_objects as go

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

warnings.filterwarnings('ignore')


API_KEY = config.api_key

def geo_data(CITY_NAME):
  URL="http://api.openweathermap.org/geo/1.0/direct?q={}&limit=5&appid={}".format(CITY_NAME, API_KEY)

  response = requests.get(URL)
  data = response.json()

  if response.status_code == 200:
    name = data[0]['name']
    local_name = data[0]['local_names']['en']
    latitude = data[0]['lat']
    longitude = data[0]['lon']
    country = data[0]['country']
    state = data[0]['state']
    geocode_data = {"name":name,
                  "local_name":local_name,
                  "latitude":latitude,
                  "longitude":longitude,
                  "country":country,
                  "state":state,
                  "city":CITY_NAME}

    return geocode_data


def most_common(lst):
    return max(set(lst), key=lst.count)


def prev_data(lat,lon,CITY_NAME):
        
    
    today = date.today()
    unix = time.mktime(today.timetuple())
    unix_today = int(unix)-86400 #4th June
    unix_month = unix_today - 2419200 #4th May

    unix_today = str(unix_today)
    unix_month = str(unix_month)

    weather_data_list=[]
    for i in range(4):
        start=int(unix_month) +(i*604800)
        start = str(start)
        end= int(start)+604800
        end=str(end)

        HIST_URL = f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=day&start={start}&end={end}&appid={API_KEY}"
        response_hist = requests.get(HIST_URL)

        hist = response_hist.json()
        data = hist['list']


        for i in data:

            weather_data = {
                    "date": pd.Timestamp.utcfromtimestamp(i["dt"]).strftime("%Y-%m-%d %H:%M:%S"),
                    "city": CITY_NAME,
                    "pressure": i['main']["pressure"],
                    "temperature_Min": i['main']["temp_min"],
                    "temperature_Max": i['main']["temp_max"],
                    "humidity": i['main']["humidity"],
                    "description": i["weather"][0]["description"]
                }
            weather_data_list.append(weather_data)

    df = pd.DataFrame(weather_data_list)
    df['temperature_Min'] = df['temperature_Min'] - 273.15
    df['temperature_Max'] = df['temperature_Max'] - 273.15
    df =df.drop_duplicates()
    df = df.reset_index(drop=True)

    #Past One month Data houtly timed

    weather_data_list_new=[]

    for day in range(28):
        npressure = []
        ntemp_max =[]
        ntemp_min=[]
        nhumidity=[]
        ndescription=[]
        for hr in range(day*24,((day*24)+24)):
            npressure.append(df['pressure'][hr])
            ntemp_max.append(df['temperature_Max'][hr])
            ntemp_min.append(df['temperature_Min'][hr])
            nhumidity.append(df['humidity'][hr])
            ndescription.append(df['description'][hr])

        pr = statistics.mean(npressure)
        tmin=statistics.mean(ntemp_min)
        tmax =statistics.mean(ntemp_max)
        hum = statistics.mean(nhumidity)
        desc = most_common(ndescription)
        weather_data = {
                    "date": df['date'][day*24][:10],
                    "city": CITY_NAME,
                    "pressure": pr,
                    "temperature": (tmin+tmax)/2,
                    "humidity": hum,
                    "description": desc
                }
        weather_data_list_new.append(weather_data)

    df_update = pd.DataFrame(weather_data_list_new)
    df_update.shape

    return df_update

def seven_day_predict(df_update, lat, lon):
  df_update['date'] = pd.to_datetime(df_update['date'])
  encoded_df = pd.get_dummies(df_update, columns=['city', 'description'])

  X = encoded_df[['pressure', 'temperature', 'humidity']]
  y = encoded_df[['pressure', 'temperature', 'humidity']]

  # Split the data into training and testing sets
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

  # Select and train the model
  model = RandomForestRegressor()
  model.fit(X_train, y_train)

  seven_day_actual = next_seven(lon, lat, API_KEY)
  col = seven_day_actual.columns
  sev = seven_day_actual.iloc[:8,1:4]
  predictions = model.predict(sev)

  # Convert predictions to a DataFrame
  predictions_df = pd.DataFrame(predictions, columns=['pressure', 'temperature', 'humidity'])

  # Add date column from `seven_day_actual`
  predictions_df['date'] = seven_day_actual['date'].values

  # Add random description from api
  descriptions = seven_day_actual['description'].unique() # Unique descriptions in the api data
  predictions_df['description'] = np.random.choice(descriptions, size=len(predictions_df))

  # Rearrange columns
  predictions_df = predictions_df[['date', 'pressure', 'temperature', 'humidity', 'description']]

  return predictions_df


def next_seven(lon, lat, API_KEY):
  #actual 7 days forcast as fetched by the api

  weather_url = f'http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,current&appid={API_KEY}&units=metric'
  response = requests.get(weather_url)

  if response.status_code == 200:
      hist = response.json()

      # Fetch daily forecast for 7 days
      data = hist['daily']

      weather_data_list=[]

      for i in data:

        weather_data = {
                  "date": pd.Timestamp.utcfromtimestamp(i["dt"]).strftime("%Y-%m-%d"),
                  "pressure": i["pressure"],
                  "temperature": (i["temp"]["min"]+i["temp"]["max"])/2,
                  "humidity": i["humidity"],
                  "description": i["weather"][0]["description"]
              }

        weather_data_list.append(weather_data)

      seven = pd.DataFrame(weather_data_list)


  else:
    print('Error:', response.status_code)

  return seven
      

def plot(plt_type, df_actual, df_pred, df, df_final):
    if plt_type==0:
        df.plot(x ='city', y='temperature', kind = 'bar')
        #x =df_update['city']
        #y=df_update['temperature']
        plt.title('Temperature trend in Delhi over the last 28 days')
        plt.ylabel('temperature')
        plt.xlabel('City')

        plt.show()

    elif plt_type==1:
        fig, ax = plt.subplots()
        ax2 = ax.twinx()

        df_actual.plot(x="Date", y=["Temperature (Â°C)"], ax=ax)
        df_pred.plot(x="date", y=["temperature"], ax=ax2, ls="--")
        fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax.transAxes)
        plt.show()


    elif plt_type==2:
        plot_data = [
            go.Scatter(
                x=df_final['Date'],
                y=df_final['Actual_temperature'],
                name='Actual'
            ),
            go.Scatter(
                x=df_final['Date'],
                y=df_final['Pred_temperature'],
                name='Prediction'
            )
        ]

        plot_layout = go.Layout(
                title='Plotting predictions against actual values'
            )
        fig = go.Figure(data=plot_data, layout=plot_layout)

        fig 






def fetch_weather(city_name):
    api_key = API_KEY
    base_url = "http://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city_name,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params)
        # Raise an exception if response status code is not 200 (OK)
        response.raise_for_status()
        data = response.json()
        name = data['name']
        temperature = data['main']['temp']
        pressure = data['main']['pressure']
        humidity = data['main']['humidity']
        description = data['weather'][0]['description']
        weather_data = {"name":name,
                      "temperature":temperature,
                      "pressure":pressure,
                      "humidity":humidity,
                      "description":description}

        return weather_data

    except requests.exceptions.RequestException as e:
        print("Error occurred during the request:", str(e))
        return None

    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", str(e))
        return None

    except ValueError as e:
        print("Invalid response received:", str(e))
        return None




def main():
    CITY_NAME = input("Enter the city name: ")

    geocode_data = geo_data(CITY_NAME)
    lat = geocode_data['latitude']
    lon = geocode_data['longitude']

    past_weather = prev_data(lat,lon,CITY_NAME)
    seven_day_pred = seven_day_predict(past_weather, lat, lon)
    seven_day_actual = next_seven(lon, lat, API_KEY)


    df_final=pd.DataFrame([seven_day_actual['date'], seven_day_actual['temperature'],seven_day_pred['temperature'],seven_day_actual['pressure'],seven_day_actual['humidity']],
                        index=['date', 'Actual_temperature','Pred_temperature','Pressure','Humidity(%)']).T
    

    print("Use the following options to display weather information:")
    print(" 1. Display current weather information\n 2. Check past 28 days forecast histor \n 3. Predict weather for next 7 days\n 4. Data Analysis through interactive plots", end="\n\n")  
    choose = int(input("Enter your choice: "))
    
    try:
        if choose == 1:
            print("Fetching weather data...")

            weather_data = fetch_weather(CITY_NAME)

            if weather_data:
                print(weather_data)
            else:
                print(
                    "Failed to fetch weather data. Please check your input or try again later.")
            
        elif choose == 2:
            past_weather = prev_data(lat,lon,CITY_NAME)    
            print("\n",past_weather,"\n")

        elif choose == 3:
            seven_day_pred = seven_day_predict(past_weather, lat, lon)
            print("\n Seven Day actual forecast \n",seven_day_actual,"\n")
            print("\n Seven Day predicted forecast \n",seven_day_pred,"\n")

        elif choose == 4:
            type_plot = int(input("Enter the type of plot: (1-3)"))
            plot(type_plot, seven_day_actual, seven_day_pred, past_weather, df_final)

        else:
            print("Invalid choice. Please try again.")

    except KeyboardInterrupt:
        print("\nProcess interrupted.")

    except Exception as e:
        print("An unexpected error occurred:", str(e))



if __name__ == "__main__":
    main()

