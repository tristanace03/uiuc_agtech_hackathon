import openmeteo_requests
import pandas as pd
import requests_cache
import json
from retry_requests import retry
from pathlib import Path


def fetch_weather(latitude, longitude, year_start, year_end):
    """
    Fetch weather data from Open-Meteo and save to wind_data/latest_weather.json
    """

    # ---------------- Setup API client ----------------

    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # ---------------- API parameters ----------------

    start_date = f"{year_start}-01-01"
    end_date = f"{year_end}-12-31"

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": [
            "temperature_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
        ],
        "wind_speed_unit": "mph",
    }

    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]

    # ---------------- Extract hourly variables ----------------

    hourly = response.Hourly()

    hourly_temperature = hourly.Variables(0).ValuesAsNumpy()
    hourly_wind_speed = hourly.Variables(1).ValuesAsNumpy()
    hourly_wind_direction = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_gusts = hourly.Variables(3).ValuesAsNumpy()

    # ---------------- Build dataframe ----------------

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }

    hourly_data["temperature_2m"] = hourly_temperature
    hourly_data["wind_speed_10m"] = hourly_wind_speed
    hourly_data["wind_direction_10m"] = hourly_wind_direction
    hourly_data["wind_gusts_10m"] = hourly_wind_gusts

    df = pd.DataFrame(hourly_data)
    df["date"] = pd.to_datetime(df["date"])

    df = df[
        (df["date"].dt.month.isin([9, 10])) &
        (df["date"].dt.day.between(1, 30))
    ]
    # ---------------- Convert to records ----------------

    records = df.to_dict(orient="records")

    # ---------------- Ensure output folder exists ----------------

    output_path = Path("wind_data")
    output_path.mkdir(exist_ok=True)

    # ---------------- Save JSON ----------------

    with open(output_path / "latest_weather.json", "w") as f:
        json.dump(records, f, indent=4, default=str)