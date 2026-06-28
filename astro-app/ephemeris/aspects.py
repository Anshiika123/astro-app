"""
ephemeris/aspects.py
====================
Aspect calculation between all planet pairs in a natal chart.

Aspects used here are the five Ptolemaic aspects standard in Western astrology.
The orb (degree tolerance) is configurable; default is 6 degrees (tight/traditional).

Background for code reviewers:
  An "aspect" is a significant angular relationship between two planets.
  The "orb" is how many degrees either side of the exact angle still counts.
  "Applying" means the two planets are still moving toward the exact angle;
  "separating" means they have passed exact and are moving apart.

Applying/separating method
--------------------------
We project both planets forward by one day using their current speeds, compute
the new separation, and compare to the current separation measured against the
exact aspect angle.  This single approach correctly handles:
  - Retrograde planets (negative speed reverses the closing direction)
  - All five aspect angles without special-casing
  - Conjunctions and oppositions symmetrically
  - Cases where both planets are retrograde

This avoids the common sign-convention bugs that arise from trying to reason
about "which planet is ahead" combined with signed speed differences.
"""

from __future__ import annotations

from typing import NamedTuple

# ---------------------------------------------------------------------------
# Aspect definitions
# ---------------------------------------------------------------------------

class AspectDef(NamedTuple):
    name:   str     # e.g. "Conjunction"
    angle:  float   # exact angle in degrees
    symbol: str     # conventional abbreviation

MAJOR_ASPECTS: list[AspectDef] = [
    AspectDef("Conjunction",  0.0,  "0"),
    AspectDef("Sextile",     60.0,  "*"),
    AspectDef("Square",      90.0,  "[]"),
    AspectDef("Trine",      120.0,  "^"),
    AspectDef("Opposition", 180.0,  "o"),
]

DEFAULT_ORB: float = 6.0   # degrees — tight/traditional Western setting


# ---------------------------------------------------------------------------
# Angular geometry helpers
# ---------------------------------------------------------------------------

def _angular_distance(lon_a: float, lon_b: float) -> float:
    """
    Smallest angular distance between two ecliptic longitudes.
    Result is always in [0, 180] degrees (unsigned shortest arc).
    """
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def _is_applying(
    lon_a: float,
    lon_b: float,
    speed_a: float,
    speed_b: float,
    asp_angle: float,
    dt: float = 1.0,
) -> bool:
    """
    Determine whether an aspect is applying (planets moving toward exact)
    or separating (planets moving away from exact).

    Method: project both planets forward by `dt` days using their current
    daily speeds, then compare how far each configuration is from the exact
    aspect angle.  If the future configuration is closer → applying;
    if further → separating.

    This projection approach handles all cases correctly:
      - Retrograde planets (negative speed naturally reverses direction)
      - All aspect angles
      - Both planets retrograde simultaneously

    Parameters
    ----------
    lon_a, lon_b   : current ecliptic longitudes (degrees)
    speed_a, speed_b : current daily motion (degrees/day; negative = retrograde)
    asp_angle      : the exact aspect angle being checked (0, 60, 90, 120, 180)
    dt             : projection step in days (default 1.0)

    Returns
    -------
    bool : True if applying, False if separating.
    """
    curr_gap = abs(_angular_distance(lon_a, lon_b) - asp_angle)

    future_lon_a = (lon_a + speed_a * dt) % 360.0
    future_lon_b = (lon_b + speed_b * dt) % 360.0
    future_gap   = abs(_angular_distance(future_lon_a, future_lon_b) - asp_angle)

    return future_gap < curr_gap


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def get_aspects(
    planet_positions: dict[str, dict[str, float]],
    orb: float = DEFAULT_ORB,
    aspect_list: list[AspectDef] | None = None,
) -> list[dict]:
    """
    Find all aspects between planet pairs within the given orb.

    Parameters
    ----------
    planet_positions : dict[str, dict]
        The "planets" dict from calculate_chart() — each value must have at
        least "longitude" (float) and "speed" (float) keys.
    orb : float
        Degree tolerance either side of the exact aspect angle.
        Default: 6.0 degrees (tight/traditional Western).
    aspect_list : list[AspectDef] | None
        Which aspects to check.  Defaults to MAJOR_ASPECTS (5 Ptolemaic).

    Returns
    -------
    list[dict] sorted by abs(orb_diff) ascending (tightest aspects first).
    Each dict:
        planet_a   (str)   -- name of first planet
        planet_b   (str)   -- name of second planet
        aspect     (str)   -- aspect name (e.g. "Trine")
        angle      (float) -- exact aspect angle (e.g. 120.0)
        orb_used   (float) -- actual angular separation between the two planets
        orb_diff   (float) -- orb_used minus exact angle
                              negative = planets haven't reached exact yet
                              positive = planets have passed exact
                              (note: the sign alone does NOT indicate applying/
                               separating — use the `applying` field for that)
        applying   (bool)  -- True if planets are closing toward exact
        separating (bool)  -- True if planets are moving away from exact
    """
    if aspect_list is None:
        aspect_list = MAJOR_ASPECTS

    planets = list(planet_positions.items())
    results: list[dict] = []

    for i in range(len(planets)):
        name_a, pos_a = planets[i]
        for j in range(i + 1, len(planets)):
            name_b, pos_b = planets[j]

            lon_a   = pos_a["longitude"]
            lon_b   = pos_b["longitude"]
            speed_a = pos_a.get("speed", 0.0)
            speed_b = pos_b.get("speed", 0.0)

            separation = _angular_distance(lon_a, lon_b)

            for asp in aspect_list:
                orb_diff = separation - asp.angle

                if abs(orb_diff) <= orb:
                    applying = _is_applying(lon_a, lon_b, speed_a, speed_b, asp.angle)

                    results.append({
                        "planet_a":   name_a,
                        "planet_b":   name_b,
                        "aspect":     asp.name,
                        "angle":      asp.angle,
                        "orb_used":   round(separation, 4),
                        "orb_diff":   round(orb_diff, 4),
                        "applying":   applying,
                        "separating": not applying,
                    })

    results.sort(key=lambda r: abs(r["orb_diff"]))
    return results
