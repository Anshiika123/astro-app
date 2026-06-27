"""
ephemeris/calculations.py
=========================
Core astronomical calculation module wrapping pyswisseph.

Design notes:
  - All public functions accept plain Python types and return dicts — no raw
    swisseph tuples are ever exposed outside this module.
  - Zodiac mode (tropical vs sidereal) is an explicit parameter, not a global
    flag, so callers always know which coordinate system they're getting.
  - Ayanamsa correction (Lahiri) is applied at the calculation layer via the
    FLG_SIDEREAL flag + swe.set_sid_mode(), keeping tropical and sidereal calls
    fully independent.
"""

from __future__ import annotations

import swisseph as swe
from datetime import datetime, timezone, timedelta
from typing import Literal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ZodiacMode = Literal["tropical", "sidereal"]

# Map of planet names to swisseph body IDs.
PLANET_IDS: dict[str, int] = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus":   swe.VENUS,
    "Mars":    swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn":  swe.SATURN,
    # Mean Node = Rahu. Ketu is always exactly 180 degrees opposite.
    "Rahu":    swe.MEAN_NODE,
}

# House systems supported by this application.
HOUSE_SYSTEMS: dict[str, bytes] = {
    "placidus":   b"P",   # used for tropical / Western charts
    "whole_sign": b"W",   # used for sidereal / Vedic charts
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Default calculation flags (speed enabled so we can detect retrograde).
CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sign_info(lon: float) -> tuple[str, float]:
    """Return (sign_name, degrees_within_sign) for an ecliptic longitude."""
    idx = int(lon // 30) % 12   # % 12 guards against floating-point 360.0
    return SIGNS[idx], lon % 30.0


def _set_zodiac_mode(mode: ZodiacMode) -> None:
    """
    Configure swisseph's internal zodiac mode.

    For sidereal charts we use the Lahiri ayanamsa, which is the standard
    reference for Vedic / Jyotish calculation and matches astro.com's Vedic
    output when Lahiri is selected.
    """
    if mode == "sidereal":
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    # Tropical: no sid mode needed. We pass flags without FLG_SIDEREAL below.


def _calc_flags_for_mode(mode: ZodiacMode) -> int:
    """Return the swisseph calculation flags for the requested zodiac mode."""
    flags = CALC_FLAGS
    if mode == "sidereal":
        flags = flags | swe.FLG_SIDEREAL
    return flags


# ---------------------------------------------------------------------------
# 1. Julian Day conversion
# ---------------------------------------------------------------------------

def datetime_to_jd(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    tz_offset_hours: float,
) -> float:
    """
    Convert a local birth date/time + UTC offset to Julian Day in UT.

    Parameters
    ----------
    year, month, day       : birth date (local time)
    hour, minute, second   : birth time (local time, 24-hour)
    tz_offset_hours        : UTC offset in fractional hours, e.g. +5.5 for IST,
                             -5.0 for EST.  Must be the historical offset at the
                             birth moment — callers resolve this with
                             timezonefinder + pytz before calling here.

    Returns
    -------
    float : Julian Day in Universal Time (UT), ready for swe.calc_ut().
    """
    tz = timezone(timedelta(hours=tz_offset_hours))
    local_dt = datetime(year, month, day, hour, minute, second, tzinfo=tz)
    utc_dt = local_dt.astimezone(timezone.utc)

    # Fractional UT hour for swisseph
    ut_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, ut_hour)


# ---------------------------------------------------------------------------
# 2. Planetary positions
# ---------------------------------------------------------------------------

def _format_position(longitude: float, latitude: float, speed: float) -> dict:
    """Build a standardised position dict for a single celestial body."""
    sign, sign_degree = _sign_info(longitude)
    return {
        "longitude":   round(longitude, 6),
        "latitude":    round(latitude, 6),
        "speed":       round(speed, 6),
        "retrograde":  speed < 0,
        "sign":        sign,
        "sign_degree": round(sign_degree, 6),
    }


def get_planet_positions(jd: float, mode: ZodiacMode = "tropical") -> dict[str, dict]:
    """
    Calculate ecliptic positions for all planets in PLANET_IDS plus Ketu.

    Parameters
    ----------
    jd   : Julian Day in UT (from datetime_to_jd).
    mode : "tropical" or "sidereal".

    Returns
    -------
    dict keyed by planet name, each value:
        longitude   (float) -- ecliptic longitude 0-360
        latitude    (float) -- ecliptic latitude
        speed       (float) -- daily motion in longitude (deg/day)
        retrograde  (bool)  -- True when speed < 0
        sign        (str)   -- zodiac sign name
        sign_degree (float) -- degrees within that sign (0-30)
    """
    _set_zodiac_mode(mode)
    flags = _calc_flags_for_mode(mode)

    results: dict[str, dict] = {}

    for name, body_id in PLANET_IDS.items():
        # swe.calc_ut returns ((lon, lat, dist, speed_lon, speed_lat, speed_dist), retflag)
        data, _retflag = swe.calc_ut(jd, body_id, flags)
        results[name] = _format_position(data[0], data[1], data[3])

    # Ketu is the south node: always exactly 180 degrees opposite Rahu.
    rahu_lon = results["Rahu"]["longitude"]
    ketu_lon = (rahu_lon + 180.0) % 360.0
    results["Ketu"] = _format_position(ketu_lon, 0.0, results["Rahu"]["speed"])

    return results


# ---------------------------------------------------------------------------
# 3. House calculations
# ---------------------------------------------------------------------------

def get_houses(
    jd: float,
    latitude: float,
    longitude: float,
    house_system: Literal["placidus", "whole_sign"] = "placidus",
    mode: ZodiacMode = "tropical",
) -> dict:
    """
    Calculate house cusps and the Ascendant (Lagna).

    Parameters
    ----------
    jd           : Julian Day in UT.
    latitude     : geographic latitude in decimal degrees (+N / -S).
    longitude    : geographic longitude in decimal degrees (+E / -W).
    house_system : "placidus" (Western/tropical) or "whole_sign" (Vedic/sidereal).
    mode         : zodiac mode -- must match the mode used for planet positions.

    Returns
    -------
    dict:
        ascendant        (float) -- Ascendant longitude 0-360
        ascendant_sign   (str)   -- sign of Ascendant
        ascendant_degree (float) -- degrees within that sign
        mc               (float) -- Midheaven longitude
        mc_sign          (str)   -- sign of MC
        houses           (list)  -- 12 dicts: {number, cusp, sign, sign_degree}

    Notes on Whole Sign houses
    --------------------------
    In Whole Sign, each house spans one full sign beginning with the
    Ascendant sign.  swisseph's 'W' flag implements this correctly.
    """
    _set_zodiac_mode(mode)
    flags = _calc_flags_for_mode(mode)
    hs_byte = HOUSE_SYSTEMS.get(house_system, b"P")

    # swe.houses_ex returns (cusps_tuple, ascmc_tuple)
    # In pyswisseph the cusps tuple is 0-indexed with 12 elements (houses 1-12).
    # ascmc[0] = Ascendant, ascmc[1] = MC
    cusps, ascmc = swe.houses_ex(jd, latitude, longitude, hs_byte, flags)

    ascendant = ascmc[0]
    mc = ascmc[1]

    asc_sign, asc_deg = _sign_info(ascendant)
    mc_sign, _mc_deg = _sign_info(mc)

    houses = []
    for i in range(12):
        cusp = cusps[i]
        sign, sign_deg = _sign_info(cusp)
        houses.append({
            "number":      i + 1,
            "cusp":        round(cusp, 6),
            "sign":        sign,
            "sign_degree": round(sign_deg, 6),
        })

    return {
        "ascendant":        round(ascendant, 6),
        "ascendant_sign":   asc_sign,
        "ascendant_degree": round(asc_deg, 6),
        "mc":               round(mc, 6),
        "mc_sign":          mc_sign,
        "houses":           houses,
    }


# ---------------------------------------------------------------------------
# 4. Full chart convenience function
# ---------------------------------------------------------------------------

def calculate_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    tz_offset_hours: float,
    latitude: float,
    longitude: float,
    mode: ZodiacMode = "tropical",
) -> dict:
    """
    Calculate a complete natal chart: planetary positions, house cusps, and
    Ascendant.  This is the primary entry-point for the rest of the application.

    Parameters
    ----------
    year ... second     : birth date and time in local time.
    tz_offset_hours     : historical UTC offset at birth location/moment.
    latitude, longitude : geographic coordinates of birth place.
    mode                : "tropical" (Placidus houses) or "sidereal"
                          (Whole Sign houses, Lahiri ayanamsa).

    Returns
    -------
    dict:
        mode       -- zodiac mode used
        julian_day -- JD UT used for all calculations
        planets    -- {planet_name: position_dict}
        houses     -- house info dict (ascendant, mc, houses list)
    """
    jd = datetime_to_jd(year, month, day, hour, minute, second, tz_offset_hours)
    planets = get_planet_positions(jd, mode=mode)
    house_system = "placidus" if mode == "tropical" else "whole_sign"
    houses = get_houses(jd, latitude, longitude, house_system=house_system, mode=mode)

    return {
        "mode":       mode,
        "julian_day": jd,
        "planets":    planets,
        "houses":     houses,
    }
