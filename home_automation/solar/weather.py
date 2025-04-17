import requests
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

class Weather:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

        self.headers = {
            "User-Agent": "lucas@meyerperin.org"
        }

    def convert_to_central(self, time_utc):

        # Convert to U.S. Central Time (automatically handles CST/CDT)
        central = time_utc.astimezone(ZoneInfo("America/Chicago"))

        # Format the time as a string
        central_time = central.strftime("%Y-%m-%d %H:%M:%S %Z")
        return central_time


    def get_sky_cover(self):
        # Get the forecast grid data for the given latitude and longitude
        lat = self.lat
        lon = self.lon

        # Get the forecast grid data from the weather API
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_resp = requests.get(points_url, headers=self.headers)
        points_resp.raise_for_status()
        grid_data = points_resp.json()["properties"]

        grid_url = grid_data["forecastGridData"]
        forecast_resp = requests.get(grid_url, headers=self.headers)
        forecast_resp.raise_for_status()
        forecast_data = forecast_resp.json()["properties"]["skyCover"]["values"]

        # for each item, convert the validTime to a datetime UTC object, the value is an integer

        return_data = []
        for item in forecast_data:
            # remove the duration from the validTime string
            valid_time = item["validTime"].split("/")[0]  # Remove the duration part
            valid_time = datetime.fromisoformat(valid_time)  # Convert to datetime object
            value = item["value"]
            return_data.append((valid_time, value))
            
        return return_data

    def sunrise_sunset(self):
        # Get the forecast grid data for the given latitude and longitude
        lat = self.lat
        lon = self.lon

        # Call sunrise-sunset.org
        resp = requests.get(f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0")
        data = resp.json()["results"]

        # Parse times in UTC
        sunrise_utc = datetime.fromisoformat(data["sunrise"])
        sunset_utc = datetime.fromisoformat(data["sunset"])

        return sunrise_utc, sunset_utc

    def get_uv_index(self):
        # Get the forecast grid data for the given latitude and longitude
        lat = self.lat
        lon = self.lon

        # Get the forecast grid data from the weather API
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_resp = requests.get(points_url, headers=self.headers)
        points_resp.raise_for_status()
        grid_data = points_resp.json()["properties"]

        grid_url = grid_data["forecastGridData"]
        forecast_resp = requests.get(grid_url, headers=self.headers)
        forecast_resp.raise_for_status()
        forecast_data = forecast_resp.json()["properties"]

        return forecast_data

    def get_filtered_sky_cover(self):
        sunrise, sunset = self.sunrise_sunset()

        sky_cover = self.get_sky_cover()
        
        # filter only for times between sunrise and sunset (converting k to datetime)
        filtered_sky_cover_d1 = {k: v for k, v in sky_cover if k >= sunrise and k <= sunset}
        filtered_sky_cover_d2 = {k: v for k, v in sky_cover if k >= (sunrise + timedelta(days=1)) and k <= (sunset + timedelta(days=1))}
        filtered_sky_cover_d3 = {k: v for k, v in sky_cover if k >= (sunrise + timedelta(days=2)) and k <= (sunset + timedelta(days=2))}

        # append the filtered data to a list
        filtered_sky_cover = []
        for k, v in filtered_sky_cover_d1.items():
            filtered_sky_cover.append((w.convert_to_central(k), v))
        for k, v in filtered_sky_cover_d2.items():
            filtered_sky_cover.append((w.convert_to_central(k), v)) 
        for k, v in filtered_sky_cover_d3.items():
            filtered_sky_cover.append((w.convert_to_central(k), v))
        
        return filtered_sky_cover

if __name__ == "__main__":
    w = Weather(29.7157469, -95.8567807)

    uv = w.get_uv_index()
    print("UV Index:")
    for item in uv:
        print(item)
    

