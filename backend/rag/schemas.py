from pydantic import BaseModel, Field


class CurrentTimeOutput(BaseModel):
    datetime_utc: str = Field(description="Current UTC datetime (YYYY-MM-DD HH:MM:SS)")
    timezone: str = Field(default="UTC", description="Timezone label")


class LocalHourOutput(BaseModel):
    datetime_local: str = Field(description="Current local datetime")
    timezone_name: str = Field(description="Local timezone name")
    utc_offset: str = Field(description="UTC offset, e.g. +0300")


class CoordinatesOutput(BaseModel):
    latitude: float | None = Field(default=None, description="Latitude in decimal degrees")
    longitude: float | None = Field(default=None, description="Longitude in decimal degrees")
    source: str | None = Field(default=None, description="How the location was resolved")
    error: str | None = Field(default=None, description="Error message when lookup fails")


class WeatherInput(BaseModel):
    latitude: float = Field(description="Latitude in decimal degrees")
    longitude: float = Field(description="Longitude in decimal degrees")


class WeatherOutput(BaseModel):
    latitude: float = Field(description="Latitude in decimal degrees")
    longitude: float = Field(description="Longitude in decimal degrees")
    condition: str = Field(description="Weather condition summary")
    temperature_c: float | None = Field(default=None, description="Air temperature in Celsius")
    feels_like_c: float | None = Field(default=None, description="Apparent temperature in Celsius")
    humidity_percent: float | None = Field(default=None, description="Relative humidity percentage")
    precipitation_mm: float | None = Field(default=None, description="Precipitation in millimeters")
    wind_speed_kmh: float | None = Field(default=None, description="Wind speed in km/h")
    wind_direction_deg: float | None = Field(default=None, description="Wind direction in degrees")
    error: str | None = Field(default=None, description="Error message when lookup fails")


class CalculateInput(BaseModel):
    expression: str = Field(description="Math expression to evaluate, e.g. (12 + 8) * 2")


class CalculateOutput(BaseModel):
    expression: str = Field(description="Submitted math expression")
    result: str | None = Field(default=None, description="Evaluated result as a string")
    error: str | None = Field(default=None, description="Error message when evaluation fails")
