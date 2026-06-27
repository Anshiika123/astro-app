"""
geo.py
======
Geocoding and timezone helpers.
Converts a place name to coordinates and resolves the historical UTC offset
for a given local date/time (DST-aware via pytz).
"""

from __future__ import annotations

from datetime import datetime

import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

_geolocator = Nominatim(user_agent="astro-app-v1", timeout=10)
_tf = TimezoneFinder()


def get_location_data(place_name: str) -> dict:
    """
    Geocode a place name and resolve its timezone.

    Returns
    -------
    dict:
        latitude   (float)
        longitude  (float)
        timezone   (str)   -- IANA timezone name, e.g. "Asia/Kolkata"
        address    (str)   -- full resolved address from OpenStreetMap
    """
    location = _geolocator.geocode(place_name)
    if location is None:
        raise ValueError(f"Location not found: {place_name!r}. Try a more specific name.")

    tz_name = _tf.timezone_at(lat=location.latitude, lng=location.longitude)
    if tz_name is None:
        raise ValueError(
            f"Could not determine timezone for ({location.latitude}, {location.longitude})."
        )

    return {
        "latitude":  location.latitude,
        "longitude": location.longitude,
        "timezone":  tz_name,
        "address":   location.address,
    }


def get_tz_offset_hours(
    tz_name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int = 0,
) -> float:
    """
    Return the UTC offset in fractional hours for the given IANA timezone
    at the specified local date/time.  DST transitions are handled by pytz.
    """
    tz = pytz.timezone(tz_name)
    local_dt = datetime(year, month, day, hour, minute, second)
    offset = tz.localize(local_dt, is_dst=None).utcoffset()
    return offset.total_seconds() / 3600.0
