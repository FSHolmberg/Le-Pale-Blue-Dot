"""
Calais Tide Information
Fetches daily high/low tide times from StormGlass API
"""

import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import json
from pathlib import Path


# Calais coordinates
CALAIS_LAT = 50.9513
CALAIS_LON = 1.8587

# Cache file location
CACHE_FILE = Path("data/tide_cache.json")
CACHE_FILE.parent.mkdir(exist_ok=True)

# StormGlass API
STORMGLASS_API_KEY = os.getenv("STORMGLASS_API_KEY", "4df2b95c-d4e7-11f0-9b8c-0242ac130003-4df2b9c0-d4e7-11f0-9b8c-0242ac130003")
STORMGLASS_ENDPOINT = "https://api.stormglass.io/v2/tide/extremes/point"


def _fetch_from_api() -> Dict:
    """Fetch tide data from StormGlass API."""
    
    # Get today and tomorrow (24h+ of data)
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=2)
    
    params = {
        'lat': CALAIS_LAT,
        'lng': CALAIS_LON,
        'start': int(start.timestamp()),
        'end': int(end.timestamp())
    }
    
    headers = {
        'Authorization': STORMGLASS_API_KEY
    }
    
    try:
        response = requests.get(
            STORMGLASS_ENDPOINT,
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Tide API error: {e}")
        return {}


def _parse_tide_data(api_response: Dict) -> Dict:
    """Parse API response into simple high/low tide times."""
    
    if not api_response or 'data' not in api_response:
        return {}
    
    high_tides = []
    low_tides = []
    today = datetime.now().date()
    
    for extreme in api_response['data']:
        time_str = extreme.get('time', '')
        tide_type = extreme.get('type', '')
        height = extreme.get('height', 0)
        
        if not time_str:
            continue
            
        # Parse ISO timestamp
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        
        # Only include today's tides
        if dt.date() != today:
            continue
        
        local_time = dt.strftime('%H:%M')
        
        if tide_type == 'high':
            high_tides.append({'time': local_time, 'height': round(height, 1)})
        elif tide_type == 'low':
            low_tides.append({'time': local_time, 'height': round(height, 1)})
    
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'high_tides': high_tides,
        'low_tides': low_tides,
        'fetched_at': datetime.now().isoformat(),
        'next_fetch': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    }


def _load_from_cache() -> Optional[Dict]:
    """Load tide data from cache file."""
    
    if not CACHE_FILE.exists():
        return None
    
    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
        
        # Check if cache is still valid (same day)
        cached_date = data.get('date', '')
        today = datetime.now().strftime('%Y-%m-%d')
        
        if cached_date == today:
            return data
        
        return None
    except (json.JSONDecodeError, IOError):
        return None


def _save_to_cache(data: Dict) -> None:
    """Save tide data to cache file."""
    
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Failed to save tide cache: {e}")


def get_tide_info() -> Dict:
    """
    Get current tide information for Calais.
    Returns cached data if available and fresh, otherwise fetches from API.
    """
    
    # Try cache first
    cached = _load_from_cache()
    if cached:
        return cached
    
    # Fetch from API
    api_response = _fetch_from_api()
    tide_data = _parse_tide_data(api_response)
    
    # Save to cache if valid
    if tide_data:
        _save_to_cache(tide_data)
    
    return tide_data


def get_tide_status() -> str:
    """
    Get human-readable tide status for agents.
    Returns string like: "Low tide at 11:23, high tide at 17:45"
    """
    
    tide_info = get_tide_info()
    
    if not tide_info:
        return "Tide information unavailable"
    
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    
    high_tides = tide_info.get('high_tides', [])
    low_tides = tide_info.get('low_tides', [])
    
    if not high_tides and not low_tides:
        return "Tide information unavailable"
    
    # Find next tide
    all_tides = []
    for ht in high_tides:
        all_tides.append(('high', ht['time'], ht['height']))
    for lt in low_tides:
        all_tides.append(('low', lt['time'], lt['height']))
    
    all_tides.sort(key=lambda x: x[1])
    
    # Simple format: list today's tides
    tide_str_parts = []
    for tide_type, tide_time, height in all_tides:
        tide_str_parts.append(f"{tide_type} tide {tide_time} ({height}m)")
    
    return "Today's tides: " + ", ".join(tide_str_parts)


def get_tide_context_for_agent() -> str:
    """
    Get tide context formatted for agent injection.
    Only used by agents who know tides (Bart, Bernie, JB).
    """
    
    status = get_tide_status()
    
    return f"""
TIDE INFORMATION (Calais):
{status}

You can reference this naturally if relevant—seagulls come in with low tide, 
the air changes, locals know the rhythm. Don't force it into conversation.
"""


if __name__ == "__main__":
    # Test the module
    print("Fetching Calais tide data...")
    tide_info = get_tide_info()
    print(json.dumps(tide_info, indent=2))
    print("\nAgent context:")
    print(get_tide_context_for_agent())