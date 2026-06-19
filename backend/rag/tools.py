import os
from datetime import datetime, timezone
from functools import lru_cache

import httpx
from langchain_core.tools import tool

from rag.schemas import (
    CalculateInput,
    CalculateOutput,
    CoordinatesOutput,
    CurrentTimeOutput,
    LocalHourOutput,
    WeatherInput,
    WeatherOutput,
)

WMO_WEATHER_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@lru_cache(maxsize=1)
def _lookup_coordinates_from_ip() -> tuple[float, float] | str:
    try:
        response = httpx.get(
            "http://ip-api.com/json/?fields=status,message,lat,lon",
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        return f"Error: could not determine location ({exc})"
    except ValueError:
        return "Error: could not parse location response."

    if data.get("status") != "success":
        message = data.get("message", "unknown error")
        return f"Error: could not determine location ({message})"

    return float(data["lat"]), float(data["lon"])


def _resolve_coordinates() -> tuple[float, float, str] | str:
    lat_env = os.getenv("LOCAL_LATITUDE")
    lon_env = os.getenv("LOCAL_LONGITUDE")
    if lat_env and lon_env:
        try:
            return float(lat_env), float(lon_env), "env"
        except ValueError:
            return "Error: LOCAL_LATITUDE and LOCAL_LONGITUDE must be valid numbers."

    ip_coords = _lookup_coordinates_from_ip()
    if isinstance(ip_coords, str):
        return ip_coords

    lat, lon = ip_coords
    return lat, lon, "ip"


@tool(response_format="content_and_artifact")
def get_current_time() -> tuple[str, CurrentTimeOutput]:
    """Return the current UTC date and time."""
    output = CurrentTimeOutput(
        datetime_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        timezone="UTC",
    )
    return output.model_dump_json(exclude_none=True), output


@tool(response_format="content_and_artifact")
def get_local_hour() -> tuple[str, LocalHourOutput]:
    """Return the current local date, time, and timezone."""
    now = datetime.now().astimezone()
    output = LocalHourOutput(
        datetime_local=now.strftime("%Y-%m-%d %H:%M:%S"),
        timezone_name=now.tzname() or "local",
        utc_offset=now.strftime("%z"),
    )
    return output.model_dump_json(exclude_none=True), output


@tool(response_format="content_and_artifact")
def get_local_coordinates() -> tuple[str, CoordinatesOutput]:
    """Return the local latitude and longitude."""
    coords = _resolve_coordinates()
    if isinstance(coords, str):
        output = CoordinatesOutput(error=coords)
        return output.model_dump_json(exclude_none=True), output

    lat, lon, source = coords
    output = CoordinatesOutput(
        latitude=lat,
        longitude=lon,
        source=source,
    )
    return output.model_dump_json(exclude_none=True), output


@tool(args_schema=WeatherInput, response_format="content_and_artifact")
def get_weather(latitude: float, longitude: float) -> tuple[str, WeatherOutput]:
    """Return the current weather for the given latitude and longitude."""
    try:
        response = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,apparent_temperature,relative_humidity_2m,"
                    "precipitation,weather_code,wind_speed_10m,wind_direction_10m"
                ),
                "timezone": "auto",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        output = WeatherOutput(
            latitude=latitude,
            longitude=longitude,
            condition="unknown",
            error=f"could not fetch weather ({exc})",
        )
        return output.model_dump_json(exclude_none=True), output
    except ValueError:
        output = WeatherOutput(
            latitude=latitude,
            longitude=longitude,
            condition="unknown",
            error="could not parse weather response",
        )
        return output.model_dump_json(exclude_none=True), output

    current = data.get("current")
    if not current:
        output = WeatherOutput(
            latitude=latitude,
            longitude=longitude,
            condition="unknown",
            error="weather data is unavailable for this location",
        )
        return output.model_dump_json(exclude_none=True), output

    weather_code = current.get("weather_code")
    condition = WMO_WEATHER_DESCRIPTIONS.get(weather_code, "Unknown conditions")

    output = WeatherOutput(
        latitude=latitude,
        longitude=longitude,
        condition=condition,
        temperature_c=current.get("temperature_2m"),
        feels_like_c=current.get("apparent_temperature"),
        humidity_percent=current.get("relative_humidity_2m"),
        precipitation_mm=current.get("precipitation"),
        wind_speed_kmh=current.get("wind_speed_10m"),
        wind_direction_deg=current.get("wind_direction_10m"),
    )
    return output.model_dump_json(exclude_none=True), output


@tool(args_schema=CalculateInput, response_format="content_and_artifact")
def calculate(expression: str) -> tuple[str, CalculateOutput]:
    """Evaluate a basic math expression, e.g. (12 + 8) * 2."""
    allowed = set("0123456789+-*/().% ")
    if not expression or not all(char in allowed for char in expression):
        output = CalculateOutput(
            expression=expression,
            error="only basic math expressions are allowed",
        )
        return output.model_dump_json(exclude_none=True), output

    try:
        result = eval(expression, {"__builtins__": {}}, {})
    except Exception as exc:
        output = CalculateOutput(
            expression=expression,
            error=str(exc),
        )
        return output.model_dump_json(exclude_none=True), output

    output = CalculateOutput(
        expression=expression,
        result=str(result),
    )
    return output.model_dump_json(exclude_none=True), output


AGENT_TOOLS = [
    get_current_time,
    get_local_hour,
    get_local_coordinates,
    get_weather,
    calculate,
]
