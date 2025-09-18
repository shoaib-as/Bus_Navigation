import requests
from django.conf import settings

def get_address_from_coordinates(lat, lon):
    url = f"https://api.tomtom.com/search/2/reverseGeocode/{lat},{lon}.json?key={settings.TOMTOM_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if "addresses" in data and len(data["addresses"]) > 0:
            return data["addresses"][0]["address"].get("freeformAddress", "Unknown Location")
        return "Unknown Location"
    except Exception as e:
        return f"Error: {str(e)}"