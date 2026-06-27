"""
guna_milan/kootas.py
====================
Guna Milan (Ashtakoot matching) — all 8 koota scoring functions and Mangal Dosha.

How to read this module:
  Each koota has a dedicated function that accepts the precomputed nakshatra
  data for both individuals and returns a dict containing the score, the
  maximum possible score, and enough detail to render a meaningful explanation.

  The top-level function `calculate_guna_milan` wires everything together and
  returns the full 36-point compatibility report.

Convention throughout: "boy" and "girl" follow the traditional Vedic labelling
used in all reference tables.  In practice these map to "person A" and
"person B" — the labels carry no other significance in the code.

All table lookups use guna_milan/tables.py, which was reviewed and confirmed
before this file was written.  Do NOT change scoring values here — change
them in tables.py and document the source.
"""

from __future__ import annotations

from ephemeris.nakshatras import get_nakshatra, NAKSHATRA_SPAN
from guna_milan.tables import (
    NAKSHATRA_ATTRIBUTES,
    VARNA_RANK,
    SIGN_TO_VASHYA,
    VASHYA_CONTROLS,
    YONI_ENEMIES,
    MONGOOSE_ENEMIES,
    YONI_SCORES,
    GANA_SCORES,
    PLANET_FRIENDSHIP,
    GRAHA_MAITRI_SCORES,
    TARA_AUSPICIOUS_REMAINDERS,
    BHAKOOT_INAUSPICIOUS,
    MANGAL_DOSHA_HOUSES,
    SIGN_ORDER,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nak_attrs(nak_index: int) -> dict:
    """Return the attribute row for a nakshatra index (0-26)."""
    return NAKSHATRA_ATTRIBUTES[nak_index]


def _sign_index(sign_name: str) -> int:
    """Return 0-based sign index (Aries=0, Pisces=11)."""
    return SIGN_ORDER.index(sign_name)


def _house_from(from_sign: str, planet_sign: str) -> int:
    """
    Count house position of planet_sign measured from from_sign (Whole Sign).
    Returns 1-12 (same sign = house 1).
    """
    return (_sign_index(planet_sign) - _sign_index(from_sign)) % 12 + 1


# ---------------------------------------------------------------------------
# 1. Varna (max 1 point)
# ---------------------------------------------------------------------------

def score_varna(boy_nak_index: int, girl_nak_index: int) -> dict:
    """
    Varna koota: compare ritual/social varna of boy's and girl's nakshatras.

    Scoring:
      Boy's varna rank >= girl's varna rank  →  1 point
      Boy's varna rank <  girl's varna rank  →  0 points

    Rationale: In Vedic tradition the groom's varna should be equal to or
    higher than the bride's.  The reverse is considered inauspicious.
    """
    boy_varna  = _nak_attrs(boy_nak_index)["varna"]
    girl_varna = _nak_attrs(girl_nak_index)["varna"]

    score = 1.0 if VARNA_RANK[boy_varna] >= VARNA_RANK[girl_varna] else 0.0

    return {
        "koota":     "Varna",
        "max":       1,
        "score":     score,
        "boy_varna": boy_varna,
        "girl_varna": girl_varna,
    }


# ---------------------------------------------------------------------------
# 2. Vashya (max 2 points)
# ---------------------------------------------------------------------------

def score_vashya(boy_moon_sign: str, girl_moon_sign: str) -> dict:
    """
    Vashya koota: control/dominance relationship between Moon signs.

    Scoring:
      Same Vashya group          →  2 points
      Boy's group controls girl's →  1 point
      Girl's group controls boy's →  0.5 points (partial mutual)
      No relationship             →  0 points
    """
    boy_group  = SIGN_TO_VASHYA[boy_moon_sign]
    girl_group = SIGN_TO_VASHYA[girl_moon_sign]

    if boy_group == girl_group:
        score = 2.0
        relation = "same group"
    elif girl_group in VASHYA_CONTROLS.get(boy_group, set()):
        score = 1.0
        relation = f"{boy_group} controls {girl_group}"
    elif boy_group in VASHYA_CONTROLS.get(girl_group, set()):
        score = 0.5
        relation = f"{girl_group} controls {boy_group} (partial)"
    else:
        score = 0.0
        relation = "no relationship"

    return {
        "koota":      "Vashya",
        "max":        2,
        "score":      score,
        "boy_group":  boy_group,
        "girl_group": girl_group,
        "relation":   relation,
    }


# ---------------------------------------------------------------------------
# 3. Tara (max 3 points)
# ---------------------------------------------------------------------------

def score_tara(boy_nak_index: int, girl_nak_index: int) -> dict:
    """
    Tara koota: auspiciousness of star-count from each partner's nakshatra.

    Method:
      Count steps from girl's nakshatra to boy's (1-indexed, same = 1).
      Divide by 9, take remainder (0 represents the 9th position).
      Auspicious remainders: 0, 2, 4, 6, 8.
      Repeat counting from boy's nakshatra to girl's.
      Each auspicious direction contributes 1.5 points → max 3.
    """
    def _count(from_idx: int, to_idx: int) -> int:
        return (to_idx - from_idx) % 27 + 1

    def _remainder(count: int) -> int:
        r = count % 9
        return r   # 0 = 9th position (Ati-Mitra), also auspicious

    g_to_b = _count(girl_nak_index, boy_nak_index)
    b_to_g = _count(boy_nak_index, girl_nak_index)

    rem_gb = _remainder(g_to_b)
    rem_bg = _remainder(b_to_g)

    auspi_gb = rem_gb in TARA_AUSPICIOUS_REMAINDERS
    auspi_bg = rem_bg in TARA_AUSPICIOUS_REMAINDERS

    score = (1.5 if auspi_gb else 0.0) + (1.5 if auspi_bg else 0.0)

    return {
        "koota":              "Tara",
        "max":                3,
        "score":              score,
        "girl_to_boy_count":  g_to_b,
        "girl_to_boy_rem":    rem_gb,
        "girl_to_boy_auspi":  auspi_gb,
        "boy_to_girl_count":  b_to_g,
        "boy_to_girl_rem":    rem_bg,
        "boy_to_girl_auspi":  auspi_bg,
    }


# ---------------------------------------------------------------------------
# 4. Yoni (max 4 points)
# ---------------------------------------------------------------------------

def score_yoni(boy_nak_index: int, girl_nak_index: int) -> dict:
    """
    Yoni koota: sexual/instinctive compatibility based on nakshatra animals.

    Scoring (confirmed convention — gender ignored for same-animal matching):
      Same animal (any gender combination)  →  4 points
      Natural enemy pair                    →  1 point
      All other combinations                →  3 points

    Note on Mongoose: classically hostile to Serpent, Sheep, and Monkey
    (not just one enemy), so all three are treated as enemy pairings.
    """
    boy_attrs  = _nak_attrs(boy_nak_index)
    girl_attrs = _nak_attrs(girl_nak_index)

    boy_animal  = boy_attrs["yoni_animal"]
    girl_animal = girl_attrs["yoni_animal"]

    if boy_animal == girl_animal:
        category = "same"
    else:
        # Check enemy relationship (bidirectional)
        primary_enemy = YONI_ENEMIES.get(boy_animal)
        is_enemy = (
            primary_enemy == girl_animal
            or YONI_ENEMIES.get(girl_animal) == boy_animal
            # Special Mongoose multi-enemy handling
            or (boy_animal == "Mongoose" and girl_animal in MONGOOSE_ENEMIES)
            or (girl_animal == "Mongoose" and boy_animal in MONGOOSE_ENEMIES)
        )
        category = "enemy" if is_enemy else "other"

    score = float(YONI_SCORES[category])

    return {
        "koota":       "Yoni",
        "max":         4,
        "score":       score,
        "boy_animal":  boy_animal,
        "girl_animal": girl_animal,
        "category":    category,
    }


# ---------------------------------------------------------------------------
# 5. Graha Maitri (max 5 points)
# ---------------------------------------------------------------------------

def score_graha_maitri(boy_nak_index: int, girl_nak_index: int) -> dict:
    """
    Graha Maitri koota: friendship between the lords of each partner's
    Moon nakshatra.

    Scoring matrix (A's view of B, B's view of A):
      F-F = 5, F-N or N-F = 4, N-N = 3,
      F-E or E-F = 2, N-E or E-N = 1, E-E = 0
    """

    # Nakshatra lords live in ephemeris/nakshatras.py (NAKSHATRAS list, index [1]).
    from ephemeris.nakshatras import NAKSHATRAS as NAK_LIST
    boy_lord  = NAK_LIST[boy_nak_index][1]
    girl_lord = NAK_LIST[girl_nak_index][1]

    if boy_lord == girl_lord:
        # Same lord = same nakshatra group = treated as mutual friends
        boy_view  = "F"
        girl_view = "F"
    else:
        boy_view  = PLANET_FRIENDSHIP[boy_lord][girl_lord]
        girl_view = PLANET_FRIENDSHIP[girl_lord][boy_lord]

    score = GRAHA_MAITRI_SCORES[(boy_view, girl_view)]

    return {
        "koota":      "Graha Maitri",
        "max":        5,
        "score":      score,
        "boy_lord":   boy_lord,
        "girl_lord":  girl_lord,
        "boy_view":   boy_view,    # how boy's lord views girl's lord
        "girl_view":  girl_view,   # how girl's lord views boy's lord
    }


# ---------------------------------------------------------------------------
# 6. Gana (max 6 points)
# ---------------------------------------------------------------------------

def score_gana(boy_nak_index: int, girl_nak_index: int) -> dict:
    """
    Gana koota: temperament compatibility (Deva / Manushya / Rakshasa).

    Scoring matrix (direction-dependent, confirmed):
      D-D = 6, D-M = 6, D-R = 1
      M-D = 5, M-M = 6, M-R = 0
      R-D = 1, R-M = 0, R-R = 6
    (boy's gana as row, girl's gana as column)
    """
    boy_gana  = _nak_attrs(boy_nak_index)["gana"]
    girl_gana = _nak_attrs(girl_nak_index)["gana"]

    score = float(GANA_SCORES[boy_gana][girl_gana])

    return {
        "koota":     "Gana",
        "max":       6,
        "score":     score,
        "boy_gana":  boy_gana,
        "girl_gana": girl_gana,
    }


# ---------------------------------------------------------------------------
# 7. Bhakoot (max 7 points)
# ---------------------------------------------------------------------------

def score_bhakoot(boy_moon_sign: str, girl_moon_sign: str) -> dict:
    """
    Bhakoot koota: sign-count relationship between partners' Moon signs.

    Method:
      Count from girl's sign to boy's sign (same sign = 1, wrap at 12).
      Count from boy's sign to girl's sign.
      If either count forms a forbidden pair {2,12}, {5,9}, or {6,8} → 0 pts.
      Otherwise → 7 pts.

    Note: Bhakoot dosha can be cancelled if Graha Maitri is strong or both
    partners share the same Nadi lord — this exception is noted in the return
    dict but not applied automatically (the caller / UI layer should decide).
    """
    g_to_b = (_sign_index(boy_moon_sign)  - _sign_index(girl_moon_sign)) % 12 + 1
    b_to_g = (_sign_index(girl_moon_sign) - _sign_index(boy_moon_sign))  % 12 + 1

    pair = frozenset({g_to_b, b_to_g})
    is_inauspicious = pair in BHAKOOT_INAUSPICIOUS

    score = 0.0 if is_inauspicious else 7.0

    # Identify which forbidden pattern triggered (if any)
    dosha_type = None
    if is_inauspicious:
        if frozenset({2, 12}) == pair:
            dosha_type = "2-12"
        elif frozenset({5, 9}) == pair:
            dosha_type = "5-9"
        elif frozenset({6, 8}) == pair:
            dosha_type = "6-8"

    return {
        "koota":            "Bhakoot",
        "max":              7,
        "score":            score,
        "boy_sign":         boy_moon_sign,
        "girl_sign":        girl_moon_sign,
        "girl_to_boy":      g_to_b,
        "boy_to_girl":      b_to_g,
        "dosha":            is_inauspicious,
        "dosha_type":       dosha_type,
        "cancellation_note": (
            "Bhakoot dosha may be cancelled if Graha Maitri score is 5 "
            "or both partners share the same nakshatra lord." if is_inauspicious else None
        ),
    }


# ---------------------------------------------------------------------------
# 8. Nadi (max 8 points)
# ---------------------------------------------------------------------------

def score_nadi(
    boy_nak_index: int,
    girl_nak_index: int,
    boy_moon_sign: str,
    girl_moon_sign: str,
    boy_pada: int,
    girl_pada: int,
) -> dict:
    """
    Nadi koota: elemental/pulse compatibility (Aadi / Madhya / Antya).

    Scoring:
      Different Nadi  →  8 points
      Same Nadi       →  0 points (Nadi Dosha)

    Nadi Dosha cancellation conditions (confirmed):
      C1: Same nakshatra, different pada          → dosha cancelled
      C2: Same nakshatra, same sign (rashi), diff pada → cancelled (subset of C1)
      C3: Different nakshatra, same Moon sign     → cancelled
      C4: Different nakshatra, different sign but same sign lord (rashi lord) → cancelled
      NOT cancelled: same nakshatra + same pada = Padavedha (strongest dosha)
    """
    boy_nadi  = _nak_attrs(boy_nak_index)["nadi"]
    girl_nadi = _nak_attrs(girl_nak_index)["nadi"]

    same_nadi = (boy_nadi == girl_nadi)

    if not same_nadi:
        return {
            "koota":     "Nadi",
            "max":       8,
            "score":     8.0,
            "boy_nadi":  boy_nadi,
            "girl_nadi": girl_nadi,
            "dosha":     False,
            "dosha_cancelled": False,
            "cancellation_rule": None,
        }

    # --- Nadi Dosha: check cancellation conditions ---
    same_nak = (boy_nak_index == girl_nak_index)
    same_sign = (boy_moon_sign == girl_moon_sign)
    same_pada = (boy_pada == girl_pada)

    # Padavedha: same nakshatra AND same pada — FULL dosha, no cancellation.
    if same_nak and same_pada:
        return {
            "koota":             "Nadi",
            "max":               8,
            "score":             0.0,
            "boy_nadi":          boy_nadi,
            "girl_nadi":         girl_nadi,
            "dosha":             True,
            "dosha_cancelled":   False,
            "cancellation_rule": None,
            "padavedha":         True,
            "note": "Padavedha — same nakshatra and same pada. Nadi dosha is fully active.",
        }

    cancelled = False
    rule = None

    if same_nak and not same_pada:
        # C1: same nakshatra, different pada
        cancelled = True
        rule = "C1: same nakshatra, different pada"
    elif same_sign and not same_nak:
        # C3: different nakshatra, same Moon sign
        cancelled = True
        rule = "C3: different nakshatra, same Moon sign"
    elif not same_sign and not same_nak:
        # C4: check if sign lords are the same
        boy_sign_lord  = _get_sign_lord(boy_moon_sign)
        girl_sign_lord = _get_sign_lord(girl_moon_sign)
        if boy_sign_lord == girl_sign_lord:
            cancelled = True
            rule = f"C4: different sign but same sign lord ({boy_sign_lord})"

    score = 8.0 if cancelled else 0.0

    return {
        "koota":             "Nadi",
        "max":               8,
        "score":             score,
        "boy_nadi":          boy_nadi,
        "girl_nadi":         girl_nadi,
        "dosha":             True,
        "dosha_cancelled":   cancelled,
        "cancellation_rule": rule,
        "padavedha":         False,
    }


# Sign lord (traditional, used for Nadi C4 cancellation)
_SIGN_LORDS: dict[str, str] = {
    "Aries":       "Mars",
    "Taurus":      "Venus",
    "Gemini":      "Mercury",
    "Cancer":      "Moon",
    "Leo":         "Sun",
    "Virgo":       "Mercury",
    "Libra":       "Venus",
    "Scorpio":     "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn":   "Saturn",
    "Aquarius":    "Saturn",
    "Pisces":      "Jupiter",
}

def _get_sign_lord(sign: str) -> str:
    return _SIGN_LORDS[sign]


# ---------------------------------------------------------------------------
# Mangal Dosha (Kuja Dosha)
# ---------------------------------------------------------------------------

def check_mangal_dosha(
    mars_sign: str,
    lagna_sign: str,
    moon_sign: str,
    venus_sign: str,
) -> dict:
    """
    Check for Mangal Dosha from three reference points: Lagna, Moon, Venus.

    Mangal Dosha is present when Mars occupies houses 1, 2, 4, 7, 8, or 12
    counted (Whole Sign) from a given reference point.

    Severity convention:
      1 of 3 reference points afflicted  →  mild
      2 of 3                             →  moderate
      3 of 3                             →  strong (full Manglik)
      0 of 3                             →  no dosha

    Dosha cancellation between partners: if both individuals have Mangal Dosha
    (at any severity level), the dosha is considered mutually cancelled.
    This is checked at the Milan level (calculate_guna_milan), not here.

    Parameters
    ----------
    mars_sign  : sidereal sign of Mars (from sidereal planet positions)
    lagna_sign : Ascendant sign
    moon_sign  : Moon sign
    venus_sign : Venus sign

    Returns
    -------
    dict:
        has_dosha  (bool)    -- True if Mars afflicts any reference point
        severity   (str)     -- 'none', 'mild', 'moderate', 'strong'
        count      (int)     -- how many of the 3 reference points are afflicted
        from_lagna (dict)    -- {house, afflicted}
        from_moon  (dict)    -- {house, afflicted}
        from_venus (dict)    -- {house, afflicted}
    """
    def _check(ref_sign: str) -> dict:
        house = _house_from(ref_sign, mars_sign)
        afflicted = house in MANGAL_DOSHA_HOUSES
        return {"house": house, "afflicted": afflicted}

    from_lagna = _check(lagna_sign)
    from_moon  = _check(moon_sign)
    from_venus = _check(venus_sign)

    count = sum([
        from_lagna["afflicted"],
        from_moon["afflicted"],
        from_venus["afflicted"],
    ])

    severity_map = {0: "none", 1: "mild", 2: "moderate", 3: "strong"}

    return {
        "has_dosha":  count > 0,
        "severity":   severity_map[count],
        "count":      count,
        "from_lagna": from_lagna,
        "from_moon":  from_moon,
        "from_venus": from_venus,
    }


# ---------------------------------------------------------------------------
# Top-level: Full Guna Milan report
# ---------------------------------------------------------------------------

def calculate_guna_milan(
    boy_sidereal_chart: dict,
    girl_sidereal_chart: dict,
) -> dict:
    """
    Run the complete Guna Milan (Ashtakoot) analysis for two individuals.

    Parameters
    ----------
    boy_sidereal_chart  : return value of calculate_chart(..., mode="sidereal")
    girl_sidereal_chart : same for the girl/second partner

    Returns
    -------
    dict:
        kootas        -- list of 8 koota result dicts (in order)
        total_score   -- sum of all 8 koota scores
        max_score     -- 36 (fixed)
        percentage    -- total / 36 * 100
        mangal_dosha  -- {boy: ..., girl: ..., mutual_cancellation: bool}
        summary       -- plain-text one-line verdict
    """
    bp = boy_sidereal_chart["planets"]
    gp = girl_sidereal_chart["planets"]
    bh = boy_sidereal_chart["houses"]
    gh = girl_sidereal_chart["houses"]

    # Extract Moon nakshatras (all Guna Milan is driven by the Moon position)
    boy_moon_nak  = get_nakshatra(bp["Moon"]["longitude"])
    girl_moon_nak = get_nakshatra(gp["Moon"]["longitude"])

    boy_nak_idx  = boy_moon_nak["index"]
    girl_nak_idx = girl_moon_nak["index"]

    boy_moon_sign  = bp["Moon"]["sign"]
    girl_moon_sign = gp["Moon"]["sign"]

    boy_pada  = boy_moon_nak["pada"]
    girl_pada = girl_moon_nak["pada"]

    # --- Score all 8 kootas ---
    kootas = [
        score_varna(boy_nak_idx, girl_nak_idx),
        score_vashya(boy_moon_sign, girl_moon_sign),
        score_tara(boy_nak_idx, girl_nak_idx),
        score_yoni(boy_nak_idx, girl_nak_idx),
        score_graha_maitri(boy_nak_idx, girl_nak_idx),
        score_gana(boy_nak_idx, girl_nak_idx),
        score_bhakoot(boy_moon_sign, girl_moon_sign),
        score_nadi(boy_nak_idx, girl_nak_idx, boy_moon_sign, girl_moon_sign, boy_pada, girl_pada),
    ]

    total = sum(k["score"] for k in kootas)
    max_score = 36

    # --- Mangal Dosha for both ---
    boy_mangal = check_mangal_dosha(
        mars_sign  = bp["Mars"]["sign"],
        lagna_sign = bh["ascendant_sign"],
        moon_sign  = bp["Moon"]["sign"],
        venus_sign = bp["Venus"]["sign"],
    )
    girl_mangal = check_mangal_dosha(
        mars_sign  = gp["Mars"]["sign"],
        lagna_sign = gh["ascendant_sign"],
        moon_sign  = gp["Moon"]["sign"],
        venus_sign = gp["Venus"]["sign"],
    )

    # Mutual cancellation: both partners have dosha
    mutual_cancellation = boy_mangal["has_dosha"] and girl_mangal["has_dosha"]

    # --- Summary verdict ---
    pct = total / max_score * 100
    if pct >= 72:
        verdict = "Excellent match (>= 26/36)"
    elif pct >= 61:
        verdict = "Good match (22-25.5/36)"
    elif pct >= 50:
        verdict = "Average match (18-21.5/36)"
    else:
        verdict = "Poor match (< 18/36) — further analysis recommended"

    return {
        "boy_nakshatra":  boy_moon_nak,
        "girl_nakshatra": girl_moon_nak,
        "kootas":         kootas,
        "total_score":    total,
        "max_score":      max_score,
        "percentage":     round(pct, 1),
        "mangal_dosha": {
            "boy":                boy_mangal,
            "girl":               girl_mangal,
            "mutual_cancellation": mutual_cancellation,
        },
        "summary": f"{total:.1f} / {max_score} ({pct:.1f}%) — {verdict}",
    }
