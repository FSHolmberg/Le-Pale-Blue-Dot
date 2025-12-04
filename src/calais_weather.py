"""
Calais environmental system for LPBD.
Fetches real weather and calculates lighting conditions.
Agents reference this to ground the bar in actual time/place.
"""

from dotenv import load_dotenv
load_dotenv()  # This loads .env file

import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from functools import lru_cache
from typing import Dict, Optional

# Calais coordinates (agents never reveal this explicitly)
CALAIS_LAT = 50.9513
CALAIS_LON = 1.8587
CALAIS_TZ = ZoneInfo("Europe/Paris")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")


@lru_cache(maxsize=1)
def _fetch_weather_cached(cache_key: str) -> Optional[Dict]:
    """
    Fetch weather from OpenWeatherMap API.
    Cached for 30 minutes (cache_key is timestamp rounded to 30min).
    Returns None if API key missing or request fails.
    """
    if not OPENWEATHER_API_KEY:
        return None
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": CALAIS_LAT,
        "lon": CALAIS_LON,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"  # Celsius
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def get_current_weather() -> Optional[Dict]:
    """
    Get current Calais weather with 30-minute caching.
    Returns dict with: temp, feels_like, conditions, description, wind_speed
    """
    # Round current time to nearest 30 minutes for cache key
    now = datetime.now(CALAIS_TZ)
    cache_key = now.strftime("%Y-%m-%d-%H") + ("-00" if now.minute < 30 else "-30")
    
    data = _fetch_weather_cached(cache_key)
    if not data:
        return None
    
    return {
        "temp": round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "conditions": data["weather"][0]["main"],  # "Rain", "Clear", "Clouds", etc.
        "description": data["weather"][0]["description"],  # "light rain", "overcast clouds"
        "wind_speed": round(data["wind"]["speed"] * 3.6),  # Convert m/s to km/h
        "humidity": data["main"]["humidity"]
    }


def get_sun_times() -> Dict[str, datetime]:
    """
    Calculate sunrise/sunset for Calais today.
    Uses simple algorithm (accurate to ~2 minutes).
    """
    from math import sin, cos, tan, asin, acos, radians, degrees
    
    now = datetime.now(CALAIS_TZ)
    day_of_year = now.timetuple().tm_yday
    
    # Simplified sunrise/sunset calculation
    # (For production, consider using 'astral' library for precision)
    lat_rad = radians(CALAIS_LAT)
    
    # Solar declination
    declination = 23.45 * sin(radians(360 / 365 * (day_of_year - 81)))
    declination_rad = radians(declination)
    
    # Hour angle at sunrise/sunset
    try:
        cos_hour_angle = -tan(lat_rad) * tan(declination_rad)
        cos_hour_angle = max(-1, min(1, cos_hour_angle))  # Clamp for polar regions
        hour_angle = degrees(acos(cos_hour_angle))
    except ValueError:
        # Polar day/night - shouldn't happen in Calais but handle it
        hour_angle = 0
    
    # Solar noon is approximately at 12:00 + longitude correction
    solar_noon = 12 - (CALAIS_LON / 15)
    
    sunrise_hour = solar_noon - (hour_angle / 15)
    sunset_hour = solar_noon + (hour_angle / 15)
    
    sunrise = now.replace(hour=int(sunrise_hour), minute=int((sunrise_hour % 1) * 60), second=0, microsecond=0)
    sunset = now.replace(hour=int(sunset_hour), minute=int((sunset_hour % 1) * 60), second=0, microsecond=0)
    
    return {
        "sunrise": sunrise,
        "sunset": sunset,
        "solar_noon": now.replace(hour=int(solar_noon), minute=int((solar_noon % 1) * 60), second=0, microsecond=0)
    }


def get_time_of_day() -> str:
    """
    Determine current lighting period in Calais.
    Returns: "night", "dawn", "day", "dusk"
    """
    now = datetime.now(CALAIS_TZ)
    sun = get_sun_times()
    
    sunrise = sun["sunrise"]
    sunset = sun["sunset"]
    
    # Dawn: 30 min before sunrise to 30 min after
    # Dusk: 30 min before sunset to 30 min after
    from datetime import timedelta
    dawn_start = sunrise - timedelta(minutes=30)
    dawn_end = sunrise + timedelta(minutes=30)
    dusk_start = sunset - timedelta(minutes=30)
    dusk_end = sunset + timedelta(minutes=30)
    
    if dawn_start <= now < dawn_end:
        return "dawn"
    elif dawn_end <= now < dusk_start:
        return "day"
    elif dusk_start <= now < dusk_end:
        return "dusk"
    else:
        return "night"


def get_calais_environment() -> str:
    """
    Generate atmospheric description of current Calais conditions.
    This is what gets injected into Bart's context or shown in the UI.
    
    Returns formatted string like:
    "Cold December night in Calais (4°C), rain against the window, streets empty."
    """
    now = datetime.now(CALAIS_TZ)
    weather = get_current_weather()
    time_period = get_time_of_day()
    sun = get_sun_times()
    
    # Build description parts
    parts = []
    
    # Time and season
    month = now.strftime("%B")
    parts.append(f"{time_period.capitalize()} in {month}, {now.strftime('%H:%M')}")
    
    # Temperature (if weather available)
    if weather:
        temp = weather["temp"]
        if temp < 5:
            temp_desc = f"Cold ({temp}°C)"
        elif temp < 15:
            temp_desc = f"Cool ({temp}°C)"
        elif temp < 25:
            temp_desc = f"Mild ({temp}°C)"
        else:
            temp_desc = f"Warm ({temp}°C)"
        parts.append(temp_desc)
        
        # Weather conditions
        conditions = weather["conditions"].lower()
        description = weather["description"]
        
        if "rain" in conditions or "drizzle" in conditions:
            parts.append(f"{description} against the window")
        elif "snow" in conditions:
            parts.append(f"{description} visible through the glass")
        elif "fog" in conditions or "mist" in conditions:
            parts.append("fog thick enough to blur the streetlights")
        elif "clear" in conditions and time_period == "night":
            parts.append("clear sky above the channel")
        elif "cloud" in conditions:
            parts.append(f"{description} overhead")
        
        # Wind (if notable)
        wind = weather["wind_speed"]
        if wind > 30:
            parts.append(f"wind at {wind} km/h rattling the old windows")
    
    # Lighting quality
    if time_period == "dawn":
        parts.append("grey light just starting to show")
    elif time_period == "dusk":
        parts.append("last light fading over the port")
    elif time_period == "night":
        parts.append("streets mostly empty")
    
    return ", ".join(parts) + "."


def get_environment_for_agent() -> str:
    """
    Shorter version for agent system prompts.
    Just the essentials without being too verbose.
    """
    weather = get_current_weather()
    time_period = get_time_of_day()
    
    if not weather:
        return f"It's {time_period} outside."
    
    temp = weather["temp"]
    conditions = weather["description"]
    
    return f"It's {time_period}, {temp}°C, {conditions} outside the window."


# For testing/debugging
if __name__ == "__main__":
    print("Calais Environment System Test")
    print("=" * 50)
    print(f"\nFull description:\n{get_calais_environment()}")
    print(f"\nAgent version:\n{get_environment_for_agent()}")
    print(f"\nTime of day: {get_time_of_day()}")
    
    sun = get_sun_times()
    print(f"\nSun times today:")
    print(f"  Sunrise: {sun['sunrise'].strftime('%H:%M')}")
    print(f"  Sunset:  {sun['sunset'].strftime('%H:%M')}")
    
    weather = get_current_weather()
    if weather:
        print(f"\nCurrent weather:")
        print(f"  Temp: {weather['temp']}°C (feels like {weather['feels_like']}°C)")
        print(f"  Conditions: {weather['description']}")
        print(f"  Wind: {weather['wind_speed']} km/h")