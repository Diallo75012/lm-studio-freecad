import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry

from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class OpenMeteoJapan(Plugin):
  def __call__(self, latitude: str, longitude: str):
    self.longitude = longitude
    print("SELF LONGITUDE: ", self.longitude)
    self.latitude = latitude
    print("SELF LATITUDE: ", self.latitude)
    # self.latitude =  35.65
    # self.longitude =  139.83
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/jma" # jma for Japan ;)
    params = {
      "latitude": self.latitude, # self.latitude
      "longitude": self.longitude, # self.longitude
      "hourly": "temperature_2m"
    }
    responses = openmeteo.weather_api(url, params=params)
    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°E {response.Longitude()}°N")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")
    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    # print("HOURLY: ", hourly, "\n")
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    # print("HOURLY_TEMPERATURE_2M: ", hourly_temperature_2m, "\n")
    hourly_data = {
      "date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s"),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
      )
    }
    # print("HOURLY_DATA: ", hourly_data, "\n")
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_dataframe = pd.DataFrame(data = hourly_data)
    # print("HOURLY_DATAFRAME: ", "\n" , hourly_dataframe)
    # We can add here the part that will return to the LLM the answer
    try:
      if len(hourly_dataframe) == 0:
        return f"Hourly_dataframe: {hourly_dataframe}\n The longitude `{longitude}` and latitude `{latitude}` didn't returned anything..\n Are you sure the city that you have choosen was situated in Japan?\n The result is empty... Sorry mate! Learn Geography first!"
      else:
        return f"Hourly_dataframe: {hourly_dataframe}\n Based on the longitude `{longitude}` and latitude `{latitude}` extracted.\n There are {len(hourly_dataframe)} rows in the result.\n The rows are:\n{hourly_dataframe.to_markdown()}"
    except Exception as e:
        return f"They were an error: '{e}'"
