import requests
import time
import os

YOUR_OPENWEATHERMAP_API_KEY = "6c9676cf98ccabb0fccf37ff740afc31"


def fetch_weather(city_name):
    api_key = YOUR_OPENWEATHERMAP_API_KEY
    base_url = "http://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city_name,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(base_url, params=params)
        # Raise an exception if response status code is not 200 (OK)
        response.raise_for_status()
        weather_data = response.json()
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


def display_weather_info(weather_data):
    if weather_data is None:
        return

    if "cod" in weather_data and weather_data["cod"] == "404":
        print("City not found. Please check the city name and try again.")
        return

    city_name = weather_data["name"]
    weather_description = weather_data["weather"][0]["description"]
    temperature = weather_data["main"]["temp"]
    humidity = weather_data["main"]["humidity"]

    print(f"Weather forecast for {city_name}:")
    print("Description:", weather_description)
    print("Temperature:", temperature, "°C")
    print("Humidity:", humidity, "%")


def main():
    city_name = input("Enter the city name: ")

    try:
        print("Fetching weather data...")

        weather_data = fetch_weather(city_name)

        if weather_data:
            os.system("cls" if os.name == "nt" else "clear")
            display_weather_info(weather_data)
        else:
            print(
                "Failed to fetch weather data. Please check your input or try again later.")

    except KeyboardInterrupt:
        print("\nProcess interrupted.")

    except Exception as e:
        print("An unexpected error occurred:", str(e))


if __name__ == "__main__":
    main()
