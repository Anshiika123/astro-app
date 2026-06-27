"""
ephemeris/nakshatras.py
=======================
Nakshatra (lunar mansion) and Pada (quarter) calculation for Vedic / sidereal charts.

Background for code reviewers unfamiliar with Jyotish:
  - The zodiac is divided into 27 nakshatras of 13°20' each (360 / 27 = 13.333...°).
  - Each nakshatra is further divided into 4 padas (quarters) of 3°20' each.
  - Nakshatra placement is calculated from a planet's SIDEREAL longitude (i.e. after
    subtracting the ayanamsa).  Always pass sidereal longitudes to these functions.
  - The Moon's nakshatra is the most important in Vedic astrology — it determines
    the Janma Nakshatra (birth star) used in Guna Milan compatibility matching.
  - Each nakshatra has a ruling planet (lord) used in Vimshottari Dasha periods
    and in Guna Milan's Tara koota.

Reference: standard Jyotish texts (Brihat Parashara Hora Shastra).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Nakshatra data table
# ---------------------------------------------------------------------------
# Each entry: (name, lord)
# Lords follow the Vimshottari sequence: Ketu, Venus, Sun, Moon, Mars,
# Rahu, Jupiter, Saturn, Mercury — cycling 3 times through 27 nakshatras.

NAKSHATRAS: list[tuple[str, str]] = [
    ("Ashwini",       "Ketu"),
    ("Bharani",       "Venus"),
    ("Krittika",      "Sun"),
    ("Rohini",        "Moon"),
    ("Mrigashira",    "Mars"),
    ("Ardra",         "Rahu"),
    ("Punarvasu",     "Jupiter"),
    ("Pushya",        "Saturn"),
    ("Ashlesha",      "Mercury"),
    ("Magha",         "Ketu"),
    ("Purva Phalguni","Venus"),
    ("Uttara Phalguni","Sun"),
    ("Hasta",         "Moon"),
    ("Chitra",        "Mars"),
    ("Swati",         "Rahu"),
    ("Vishakha",      "Jupiter"),
    ("Anuradha",      "Saturn"),
    ("Jyeshtha",      "Mercury"),
    ("Mula",          "Ketu"),
    ("Purva Ashadha", "Venus"),
    ("Uttara Ashadha","Sun"),
    ("Shravana",      "Moon"),
    ("Dhanishtha",    "Mars"),
    ("Shatabhisha",   "Rahu"),
    ("Purva Bhadrapada","Jupiter"),
    ("Uttara Bhadrapada","Saturn"),
    ("Revati",        "Mercury"),
]

# Span of each nakshatra in degrees (360 / 27)
NAKSHATRA_SPAN: float = 360.0 / 27.0   # = 13.3333...

# Span of each pada (quarter) in degrees
PADA_SPAN: float = NAKSHATRA_SPAN / 4.0  # = 3.3333...


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def get_nakshatra(sidereal_longitude: float) -> dict:
    """
    Calculate the nakshatra and pada for a given sidereal ecliptic longitude.

    Parameters
    ----------
    sidereal_longitude : float
        Ecliptic longitude in degrees (0-360) already corrected for ayanamsa
        (i.e. the sidereal longitude, NOT tropical).  Use the longitude from
        get_planet_positions() called with mode="sidereal".

    Returns
    -------
    dict:
        index        (int)  -- 0-based nakshatra index (0=Ashwini, 26=Revati)
        name         (str)  -- nakshatra name
        lord         (str)  -- ruling planet of this nakshatra
        pada         (int)  -- pada number 1-4
        longitude    (float)-- the input longitude (for reference)
        degrees_in   (float)-- degrees elapsed within this nakshatra (0-13.33)
        degrees_in_pada (float) -- degrees elapsed within this pada (0-3.33)
    """
    # Normalise to 0-360
    lon = sidereal_longitude % 360.0

    # Which nakshatra (0-26)?
    nak_index = int(lon / NAKSHATRA_SPAN)
    nak_index = min(nak_index, 26)   # guard against floating-point 360.0

    name, lord = NAKSHATRAS[nak_index]

    # Degrees elapsed within this nakshatra
    degrees_in = lon - nak_index * NAKSHATRA_SPAN

    # Which pada (1-4)?
    pada = int(degrees_in / PADA_SPAN) + 1
    pada = min(pada, 4)   # guard against floating-point at boundary

    degrees_in_pada = degrees_in - (pada - 1) * PADA_SPAN

    return {
        "index":           nak_index,
        "name":            name,
        "lord":            lord,
        "pada":            pada,
        "longitude":       round(lon, 6),
        "degrees_in":      round(degrees_in, 6),
        "degrees_in_pada": round(degrees_in_pada, 6),
    }


def get_all_planet_nakshatras(sidereal_planet_positions: dict) -> dict[str, dict]:
    """
    Calculate nakshatra placement for every planet in a sidereal chart.

    Parameters
    ----------
    sidereal_planet_positions : dict
        The "planets" dict returned by calculate_chart(..., mode="sidereal").
        Each value must have a "longitude" key (sidereal longitude).

    Returns
    -------
    dict keyed by planet name, each value the nakshatra dict from get_nakshatra().
    """
    return {
        name: get_nakshatra(pos["longitude"])
        for name, pos in sidereal_planet_positions.items()
    }
