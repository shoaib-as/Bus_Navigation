import requests

API_KEY = "89afe5ffe616a7ebd13ea70c3db89e45"
BASE_URL = "http://api.weatherstack.com/current"

def get_weather(lat, lon):
    params = {
        "access_key": API_KEY,
        "query": f"{lat},{lon}",
        "units": "m"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if "current" in data:
        current = data["current"]
        return {
            "temperature": current.get("temperature", 0),
            "humidity": current.get("humidity", 0),
            "precipitation": current.get("precip", 0),
            "weather_desc": current.get("weather_descriptions", [""])[0]
        }
    return {"temperature": 0, "humidity": 0, "precipitation": 0, "weather_desc": ""}
