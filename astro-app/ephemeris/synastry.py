"""
ephemeris/synastry.py
=====================
Western synastry: inter-aspects between two tropical natal charts.

Synastry measures how the planets in Person A's chart relate to the
planets in Person B's chart.  Unlike a natal aspect calculation (which
only looks inside one chart), synastry looks at every cross-chart pair.

Only tropical mode is used (matching the project spec: Western synastry
for tropical mode).  The caller should pass tropical planet dicts.
"""

from __future__ import annotations

from ephemeris.aspects import (
    _angular_distance,
    _is_applying,
    MAJOR_ASPECTS,
    DEFAULT_ORB,
    AspectDef,
)


def get_synastry_aspects(
    chart_a_planets: dict[str, dict],
    chart_b_planets: dict[str, dict],
    orb: float = DEFAULT_ORB,
    aspect_list: list[AspectDef] | None = None,
) -> list[dict]:
    """
    Calculate inter-aspects between two charts (every A planet vs every B planet).

    Aspects within the same chart are NOT included — use get_aspects() for those.

    Parameters
    ----------
    chart_a_planets : "planets" dict from calculate_chart() for person A (tropical)
    chart_b_planets : "planets" dict from calculate_chart() for person B (tropical)
    orb             : degree tolerance (default 6°)
    aspect_list     : aspects to check (default: 5 major Ptolemaic)

    Returns
    -------
    list[dict] sorted by abs(orb_diff). Each dict:
        planet_a    (str)   -- planet from person A
        planet_b    (str)   -- planet from person B
        aspect      (str)   -- aspect name
        angle       (float) -- exact aspect angle
        orb_used    (float) -- actual separation
        orb_diff    (float) -- separation minus exact angle
        applying    (bool)  -- A's planet moving toward exact with B's
        separating  (bool)
    """
    if aspect_list is None:
        aspect_list = MAJOR_ASPECTS

    results: list[dict] = []

    for name_a, pos_a in chart_a_planets.items():
        for name_b, pos_b in chart_b_planets.items():
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
