"""
ephemeris/transits.py
=====================
Transit module: current planetary positions vs a natal chart.

A "transit" is when a currently-moving planet forms an aspect to a planet's
position at birth.  This module:
  1. Calculates current planetary positions for right now (UTC)
  2. Compares them to any natal chart
  3. Returns the resulting transit-to-natal aspects

Transits use the tropical zodiac (Western convention).
"""

from __future__ import annotations

from datetime import datetime, timezone

import swisseph as swe

from ephemeris.calculations import get_planet_positions
from ephemeris.aspects import (
    _angular_distance,
    _is_applying,
    MAJOR_ASPECTS,
    DEFAULT_ORB,
    AspectDef,
)


def get_current_julian_day() -> float:
    """Return the Julian Day number for the current UTC moment."""
    now = datetime.now(timezone.utc)
    ut_hour = now.hour + now.minute / 60.0 + now.second / 3600.0
    return swe.julday(now.year, now.month, now.day, ut_hour)


def get_current_positions(mode: str = "tropical") -> dict:
    """
    Calculate current planetary positions.

    Returns
    -------
    dict:
        julian_day  (float) — JD of calculation
        datetime    (str)   — human-readable UTC string
        planets     (dict)  — planet positions (same structure as calculate_chart)
    """
    jd = get_current_julian_day()
    planets = get_planet_positions(jd, mode=mode)
    now = datetime.now(timezone.utc)
    return {
        "julian_day": jd,
        "datetime":   now.strftime("%Y-%m-%d %H:%M UTC"),
        "planets":    planets,
    }


def get_transit_aspects(
    natal_planets: dict[str, dict],
    transit_planets: dict[str, dict],
    orb: float = DEFAULT_ORB,
    aspect_list: list[AspectDef] | None = None,
) -> list[dict]:
    """
    Find aspects between transiting planets and natal chart planets.

    The transiting planet is the "faster" body (it's currently moving).
    The natal planet is treated as stationary (it's a birth position).

    Parameters
    ----------
    natal_planets   : "planets" from natal calculate_chart() (tropical)
    transit_planets : "planets" from get_current_positions()
    orb             : degree tolerance (default 6°)
    aspect_list     : aspects to check (default: 5 major Ptolemaic)

    Returns
    -------
    list[dict] sorted by abs(orb_diff). Each dict:
        transit_planet (str)  — name of the currently transiting planet
        natal_planet   (str)  — name of the natal planet being aspected
        aspect         (str)  — aspect name
        angle          (float)— exact aspect angle
        orb_used       (float)— actual separation
        orb_diff       (float)— separation minus exact angle
        applying       (bool) — transit planet moving toward natal point
        separating     (bool)
    """
    if aspect_list is None:
        aspect_list = MAJOR_ASPECTS

    results: list[dict] = []

    for t_name, t_pos in transit_planets.items():
        for n_name, n_pos in natal_planets.items():
            lon_t   = t_pos["longitude"]
            lon_n   = n_pos["longitude"]
            speed_t = t_pos.get("speed", 0.0)
            # Natal positions are fixed — treat speed as zero for applying check
            speed_n = 0.0

            separation = _angular_distance(lon_t, lon_n)

            for asp in aspect_list:
                orb_diff = separation - asp.angle
                if abs(orb_diff) <= orb:
                    applying = _is_applying(lon_t, lon_n, speed_t, speed_n, asp.angle)
                    results.append({
                        "transit_planet": t_name,
                        "natal_planet":   n_name,
                        "aspect":         asp.name,
                        "angle":          asp.angle,
                        "orb_used":       round(separation, 4),
                        "orb_diff":       round(orb_diff, 4),
                        "applying":       applying,
                        "separating":     not applying,
                    })

    results.sort(key=lambda r: abs(r["orb_diff"]))
    return results


def get_transits_for_chart(natal_chart: dict, orb: float = DEFAULT_ORB) -> dict:
    """
    Convenience: get current transits for a natal chart.

    Parameters
    ----------
    natal_chart : return value of calculate_chart(..., mode="tropical")
    orb         : degree tolerance

    Returns
    -------
    dict:
        current  — current positions (datetime, julian_day, planets)
        aspects  — list of transit-to-natal aspects
    """
    current = get_current_positions(mode="tropical")
    aspects = get_transit_aspects(natal_chart["planets"], current["planets"], orb=orb)
    return {"current": current, "aspects": aspects}
