"""
ephemeris/aspects.py
====================
Aspect calculation between all planet pairs in a natal chart.

Aspects used here are the five Ptolemaic aspects standard in Western astrology.
The orb (degree tolerance) is configurable; default is 6 degrees (tight/traditional).

Background for code reviewers:
  An "aspect" is a significant angular relationship between two planets.
  The "orb" is how many degrees either side of the exact angle still counts.
  A "applying" aspect means the faster planet is moving toward the exact angle;
  "separating" means it's moving away.  This module detects both.
"""

from __future__ import annotations

from typing import NamedTuple

# ---------------------------------------------------------------------------
# Aspect definitions
# ---------------------------------------------------------------------------

class AspectDef(NamedTuple):
    name:  str    # e.g. "Conjunction"
    angle: float  # exact angle in degrees
    symbol: str   # conventional glyph abbreviation

# The five major Ptolemaic aspects.
MAJOR_ASPECTS: list[AspectDef] = [
    AspectDef("Conjunction",  0.0,   "0"),
    AspectDef("Sextile",     60.0,   "*"),
    AspectDef("Square",      90.0,   "[]"),
    AspectDef("Trine",      120.0,   "^"),
    AspectDef("Opposition", 180.0,   "o"),
]

DEFAULT_ORB: float = 6.0   # degrees — tight/traditional Western setting


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def _angular_distance(lon_a: float, lon_b: float) -> float:
    """
    Return the smallest angular distance between two ecliptic longitudes.
    Result is always 0-180 degrees (unsigned shortest arc).
    """
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def get_aspects(
    planet_positions: dict,
    orb: float = DEFAULT_ORB,
    aspect_list: list[AspectDef] | None = None,
) -> list[dict]:
    """
    Find all aspects between planet pairs within the given orb.

    Parameters
    ----------
    planet_positions : dict
        The "planets" dict from calculate_chart() — keys are planet names,
        values have at least "longitude" and "speed" keys.
    orb : float
        Degree tolerance either side of the exact aspect angle.
        Default: 6.0 degrees.
    aspect_list : list[AspectDef] | None
        Which aspects to check.  Defaults to MAJOR_ASPECTS (the 5 Ptolemaic).

    Returns
    -------
    list of dicts, each describing one aspect:
        planet_a   (str)   -- name of first planet
        planet_b   (str)   -- name of second planet
        aspect     (str)   -- aspect name (e.g. "Trine")
        angle      (float) -- exact aspect angle
        orb_used   (float) -- actual angular separation
        orb_diff   (float) -- orb_used minus exact angle (signed, - = applying)
        applying   (bool)  -- True if the faster planet is closing toward exact
        separating (bool)  -- True if the faster planet is moving away

    The list is sorted by abs(orb_diff) ascending (tightest aspects first).
    """
    if aspect_list is None:
        aspect_list = MAJOR_ASPECTS

    planets = list(planet_positions.items())
    results: list[dict] = []

    for i in range(len(planets)):
        name_a, pos_a = planets[i]
        for j in range(i + 1, len(planets)):
            name_b, pos_b = planets[j]

            separation = _angular_distance(pos_a["longitude"], pos_b["longitude"])

            for asp in aspect_list:
                diff = separation - asp.angle   # signed: + means past exact
                if abs(diff) <= orb:
                    # Determine applying vs separating.
                    # The faster planet (higher absolute speed) governs direction.
                    # If the faster planet's motion is reducing the separation, it's applying.
                    speed_a = pos_a.get("speed", 0.0)
                    speed_b = pos_b.get("speed", 0.0)

                    # Net closing rate: positive = separating, negative = applying.
                    # We approximate: if A is ahead of B (lon_a > lon_b short arc),
                    # A moving faster than B increases separation.
                    lon_a = pos_a["longitude"]
                    lon_b = pos_b["longitude"]
                    raw_diff = (lon_a - lon_b) % 360.0
                    a_ahead = raw_diff < 180.0
                    # Closing rate from A's perspective
                    closing = (speed_b - speed_a) if a_ahead else (speed_a - speed_b)
                    applying = closing > 0

                    results.append({
                        "planet_a":   name_a,
                        "planet_b":   name_b,
                        "aspect":     asp.name,
                        "angle":      asp.angle,
                        "orb_used":   round(separation, 4),
                        "orb_diff":   round(diff, 4),
                        "applying":   applying,
                        "separating": not applying,
                    })

    results.sort(key=lambda r: abs(r["orb_diff"]))
    return results
