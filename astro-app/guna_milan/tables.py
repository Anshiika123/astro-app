"""
guna_milan/tables.py
====================
Pure reference data for the Guna Milan (Ashtakoot) compatibility system.

No logic lives here — only lookup tables and constants.  All scoring rules
and algorithms are in kootas.py.  This separation makes it easy to audit
the tables against a classical reference without wading through code.

Sources: Brihat Parashara Hora Shastra (BPHS), cross-checked against
Drik Panchang, AstroSage, and standard modern Jyotish texts.
Any disputed value is noted in a comment with the chosen convention.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. Nakshatra attribute table
# ---------------------------------------------------------------------------
# Indexed 0-26, matching the NAKSHATRAS list in ephemeris/nakshatras.py.
# Each row: (name, gana, varna, nadi, yoni_animal, yoni_gender)
#
# Yoni gender: 'M' = male (purush), 'F' = female (stri).
# Nadi: 'Aadi' (first), 'Madhya' (middle), 'Antya' (last).
# Gana: 'Deva', 'Manushya', 'Rakshasa'.
# Varna: 'Brahmin', 'Kshatriya', 'Vaishya', 'Shudra'.
#
# Gana assignments verified against user-confirmed list:
#   Deva (9):      Ashwini, Mrigashira, Punarvasu, Pushya, Hasta, Swati,
#                  Anuradha, Shravana, Revati
#   Manushya (9):  Bharani, Rohini, Ardra, Purva Phalguni, Uttara Phalguni,
#                  Purva Ashadha, Uttara Ashadha, Purva Bhadrapada, Uttara Bhadrapada
#   Rakshasa (9):  Krittika, Ashlesha, Magha, Chitra, Vishakha, Jyeshtha,
#                  Mula, Dhanishtha, Shatabhisha

NAKSHATRA_ATTRIBUTES: list[dict] = [
    # idx 0
    {"name": "Ashwini",            "gana": "Deva",      "varna": "Vaishya",   "nadi": "Aadi",   "yoni_animal": "Horse",      "yoni_gender": "M"},
    # idx 1
    {"name": "Bharani",            "gana": "Manushya",  "varna": "Brahmin",   "nadi": "Madhya", "yoni_animal": "Elephant",   "yoni_gender": "M"},
    # idx 2
    {"name": "Krittika",           "gana": "Rakshasa",  "varna": "Brahmin",   "nadi": "Antya",  "yoni_animal": "Sheep",      "yoni_gender": "F"},
    # idx 3
    {"name": "Rohini",             "gana": "Manushya",  "varna": "Shudra",    "nadi": "Antya",  "yoni_animal": "Serpent",    "yoni_gender": "M"},
    # idx 4
    {"name": "Mrigashira",         "gana": "Deva",      "varna": "Vaishya",   "nadi": "Madhya", "yoni_animal": "Serpent",    "yoni_gender": "F"},
    # idx 5
    {"name": "Ardra",              "gana": "Manushya",  "varna": "Brahmin",   "nadi": "Aadi",   "yoni_animal": "Dog",        "yoni_gender": "F"},
    # idx 6
    {"name": "Punarvasu",          "gana": "Deva",      "varna": "Vaishya",   "nadi": "Aadi",   "yoni_animal": "Cat",        "yoni_gender": "F"},
    # idx 7
    {"name": "Pushya",             "gana": "Deva",      "varna": "Kshatriya", "nadi": "Madhya", "yoni_animal": "Sheep",      "yoni_gender": "M"},
    # idx 8
    {"name": "Ashlesha",           "gana": "Rakshasa",  "varna": "Brahmin",   "nadi": "Antya",  "yoni_animal": "Cat",        "yoni_gender": "M"},
    # idx 9
    {"name": "Magha",              "gana": "Rakshasa",  "varna": "Shudra",    "nadi": "Aadi",   "yoni_animal": "Rat",        "yoni_gender": "M"},
    # idx 10
    {"name": "Purva Phalguni",     "gana": "Manushya",  "varna": "Brahmin",   "nadi": "Madhya", "yoni_animal": "Rat",        "yoni_gender": "F"},
    # idx 11
    {"name": "Uttara Phalguni",    "gana": "Manushya",  "varna": "Kshatriya", "nadi": "Antya",  "yoni_animal": "Cow",        "yoni_gender": "M"},
    # idx 12
    {"name": "Hasta",              "gana": "Deva",      "varna": "Vaishya",   "nadi": "Madhya", "yoni_animal": "Buffalo",    "yoni_gender": "F"},
    # idx 13
    {"name": "Chitra",             "gana": "Rakshasa",  "varna": "Brahmin",   "nadi": "Madhya", "yoni_animal": "Tiger",      "yoni_gender": "F"},
    # idx 14
    {"name": "Swati",              "gana": "Deva",      "varna": "Shudra",    "nadi": "Aadi",   "yoni_animal": "Buffalo",    "yoni_gender": "M"},
    # idx 15
    {"name": "Vishakha",           "gana": "Rakshasa",  "varna": "Brahmin",   "nadi": "Antya",  "yoni_animal": "Tiger",      "yoni_gender": "M"},
    # idx 16
    {"name": "Anuradha",           "gana": "Deva",      "varna": "Kshatriya", "nadi": "Madhya", "yoni_animal": "Deer",       "yoni_gender": "F"},
    # idx 17
    {"name": "Jyeshtha",           "gana": "Rakshasa",  "varna": "Vaishya",   "nadi": "Aadi",   "yoni_animal": "Deer",       "yoni_gender": "M"},
    # idx 18
    {"name": "Mula",               "gana": "Rakshasa",  "varna": "Kshatriya", "nadi": "Antya",  "yoni_animal": "Dog",        "yoni_gender": "M"},
    # idx 19
    {"name": "Purva Ashadha",      "gana": "Manushya",  "varna": "Brahmin",   "nadi": "Aadi",   "yoni_animal": "Monkey",     "yoni_gender": "M"},
    # idx 20
    {"name": "Uttara Ashadha",     "gana": "Manushya",  "varna": "Kshatriya", "nadi": "Madhya", "yoni_animal": "Mongoose",   "yoni_gender": "M"},
    # idx 21
    {"name": "Shravana",           "gana": "Deva",      "varna": "Kshatriya", "nadi": "Antya",  "yoni_animal": "Monkey",     "yoni_gender": "F"},
    # idx 22
    {"name": "Dhanishtha",         "gana": "Rakshasa",  "varna": "Vaishya",   "nadi": "Madhya", "yoni_animal": "Lion",       "yoni_gender": "F"},
    # idx 23
    {"name": "Shatabhisha",        "gana": "Rakshasa",  "varna": "Shudra",    "nadi": "Aadi",   "yoni_animal": "Horse",      "yoni_gender": "F"},
    # idx 24
    {"name": "Purva Bhadrapada",   "gana": "Manushya",  "varna": "Brahmin",   "nadi": "Madhya", "yoni_animal": "Lion",       "yoni_gender": "M"},
    # idx 25
    {"name": "Uttara Bhadrapada",  "gana": "Manushya",  "varna": "Kshatriya", "nadi": "Antya",  "yoni_animal": "Cow",        "yoni_gender": "F"},
    # idx 26
    {"name": "Revati",             "gana": "Deva",      "varna": "Shudra",    "nadi": "Aadi",   "yoni_animal": "Elephant",   "yoni_gender": "F"},
]

# ---------------------------------------------------------------------------
# 2. Varna order (for Varna koota comparison)
# ---------------------------------------------------------------------------
# Higher index = higher varna rank.
# Brahmin > Kshatriya > Vaishya > Shudra (index 3 > 2 > 1 > 0)

VARNA_RANK: dict[str, int] = {
    "Shudra":    0,
    "Vaishya":   1,
    "Kshatriya": 2,
    "Brahmin":   3,
}

# ---------------------------------------------------------------------------
# 3. Vashya groups by zodiac sign
# ---------------------------------------------------------------------------
# Vashya (control/dominance) is assessed from the Moon's sign, not nakshatra.
# This is a whole-sign approach (each sign belongs to exactly one group).
#
# Groups: Manav (human), Chatushpad (four-legged), Jalchar (water-dweller),
#         Vanchar (wild/forest), Keet (insect/reptile)

SIGN_TO_VASHYA: dict[str, str] = {
    "Aries":       "Chatushpad",
    "Taurus":      "Chatushpad",
    "Gemini":      "Manav",
    "Cancer":      "Jalchar",
    "Leo":         "Vanchar",
    "Virgo":       "Manav",
    "Libra":       "Manav",
    "Scorpio":     "Keet",
    "Sagittarius": "Chatushpad",
    "Capricorn":   "Jalchar",
    "Aquarius":    "Manav",
    "Pisces":      "Jalchar",
}

# Vashya control relationships: VASHYA_CONTROLS[A] = set of groups that A controls.
# "Controls" means A can attract/dominate B — used for partial-score (1 pt) cases.
VASHYA_CONTROLS: dict[str, set[str]] = {
    "Manav":      {"Chatushpad", "Vanchar"},
    "Chatushpad": set(),
    "Vanchar":    {"Jalchar"},
    "Jalchar":    {"Keet"},
    "Keet":       {"Manav"},   # circular per classical sources
}

# ---------------------------------------------------------------------------
# 4. Yoni animal compatibility
# ---------------------------------------------------------------------------
# Yoni enemy pairs (bidirectional).  An animal's enemy is the one with
# the most hostile relationship for yoni scoring.
# Tiger's enemy = Cow (confirmed).  Dog's enemy = Deer (separate pair).
#
# These are the 14 yoni animals used in all 27 nakshatras (some animals
# appear twice with different genders, but animal-type pairing drives scoring).

YONI_ENEMIES: dict[str, str] = {
    "Horse":     "Buffalo",
    "Buffalo":   "Horse",
    "Elephant":  "Lion",
    "Lion":      "Elephant",
    "Sheep":     "Mongoose",
    "Mongoose":  "Sheep",      # Mongoose also hostile to Serpent & Monkey — see note below
    "Serpent":   "Mongoose",
    "Dog":       "Deer",
    "Deer":      "Dog",
    "Cat":       "Rat",
    "Rat":       "Cat",
    "Cow":       "Tiger",
    "Tiger":     "Cow",
    "Monkey":    "Mongoose",
}
# NOTE: Mongoose is classically hostile to Serpent, Sheep, AND Monkey.
# For scoring purposes we use the primary enemy pair.  If boy/girl involve
# Mongoose vs Serpent, Sheep, or Monkey, all are treated as enemy (score 1).

# Full set of Mongoose enemies for the lookup in kootas.py:
MONGOOSE_ENEMIES: frozenset[str] = frozenset({"Serpent", "Sheep", "Monkey"})

# Yoni scoring lookup: (same animal) → 4, (enemy) → 1, (other) → 3
# "Same animal, same/opposite sex" convention: 4 pts regardless of gender
# (dominant modern convention per Drik Panchang / AstroSage; classical texts
# occasionally give 3 for same-sex same-animal, but 4 is the user-confirmed choice).
YONI_SCORES: dict[str, int] = {
    "same":   4,  # same animal (any gender combination)
    "enemy":  1,  # natural enemy pair
    "other":  3,  # all other combinations
}

# ---------------------------------------------------------------------------
# 5. Gana scoring matrix
# ---------------------------------------------------------------------------
# Rows = boy's gana, columns = girl's gana.
# Direction-dependent asymmetry confirmed: Deva(boy)+Manushya(girl)=6,
# but Manushya(boy)+Deva(girl)=5.

GANA_SCORES: dict[str, dict[str, int]] = {
    #            girl: Deva  Manushya  Rakshasa
    "Deva":     {"Deva": 6, "Manushya": 6, "Rakshasa": 1},
    "Manushya": {"Deva": 5, "Manushya": 6, "Rakshasa": 0},
    "Rakshasa": {"Deva": 1, "Manushya": 0, "Rakshasa": 6},
}

# ---------------------------------------------------------------------------
# 6. Planetary friendship table (Naisargika Maitri — natural friendships)
# ---------------------------------------------------------------------------
# Used for Graha Maitri koota: compare lords of boy's and girl's Moon nakshatras.
# Values: 'F' = Friend, 'N' = Neutral, 'E' = Enemy.
# Source: BPHS Chapter on Naisargika Maitri.
#
# Rahu and Ketu are included because they are valid nakshatra lords in
# the Vimshottari sequence.  Their classical friendship assignments follow
# the widely-used convention in BPHS and most modern Jyotish references.

PLANET_FRIENDSHIP: dict[str, dict[str, str]] = {
    "Sun": {
        "Sun": "N", "Moon": "F", "Mars": "F", "Mercury": "N",
        "Jupiter": "F", "Venus": "E", "Saturn": "E",
        "Rahu": "E", "Ketu": "E",
    },
    "Moon": {
        "Sun": "F", "Moon": "N", "Mars": "N", "Mercury": "F",
        "Jupiter": "N", "Venus": "N", "Saturn": "N",
        "Rahu": "E", "Ketu": "E",
    },
    "Mars": {
        "Sun": "F", "Moon": "F", "Mars": "N", "Mercury": "E",
        "Jupiter": "F", "Venus": "N", "Saturn": "N",
        "Rahu": "N", "Ketu": "N",
    },
    "Mercury": {
        "Sun": "F", "Moon": "E", "Mars": "N", "Mercury": "N",
        "Jupiter": "N", "Venus": "F", "Saturn": "N",
        "Rahu": "F", "Ketu": "N",
    },
    "Jupiter": {
        "Sun": "F", "Moon": "F", "Mars": "F", "Mercury": "E",
        "Jupiter": "N", "Venus": "E", "Saturn": "N",
        "Rahu": "N", "Ketu": "N",
    },
    "Venus": {
        "Sun": "E", "Moon": "E", "Mars": "N", "Mercury": "F",
        "Jupiter": "N", "Venus": "N", "Saturn": "F",
        "Rahu": "F", "Ketu": "N",
    },
    "Saturn": {
        "Sun": "E", "Moon": "E", "Mars": "E", "Mercury": "F",
        "Jupiter": "N", "Venus": "F", "Saturn": "N",
        "Rahu": "F", "Ketu": "N",
    },
    "Rahu": {
        "Sun": "E", "Moon": "E", "Mars": "E", "Mercury": "F",
        "Jupiter": "N", "Venus": "F", "Saturn": "F",
        "Rahu": "N", "Ketu": "N",
    },
    "Ketu": {
        "Sun": "E", "Moon": "E", "Mars": "F", "Mercury": "N",
        "Jupiter": "F", "Venus": "N", "Saturn": "N",
        "Rahu": "N", "Ketu": "N",
    },
}

# Graha Maitri score from the combination of two friendship values.
# Key = (A_views_B, B_views_A), Value = points awarded (max 5).
GRAHA_MAITRI_SCORES: dict[tuple[str, str], float] = {
    ("F", "F"): 5.0,   # mutual friends
    ("F", "N"): 4.0,   # one friend, one neutral
    ("N", "F"): 4.0,
    ("N", "N"): 3.0,   # both neutral
    ("F", "E"): 2.0,   # one friend, one enemy
    ("E", "F"): 2.0,
    ("N", "E"): 1.0,   # one neutral, one enemy
    ("E", "N"): 1.0,
    ("E", "E"): 0.0,   # mutual enemies
}

# ---------------------------------------------------------------------------
# 7. Tara auspiciousness
# ---------------------------------------------------------------------------
# Count from reference nakshatra to target, 1-indexed.
# Divide by 9, take remainder (0 = 9th).
# Auspicious remainders: 2, 4, 6, 8, 0 (Sampat, Kshema, Sadhaka, Mitra, Ati-Mitra)
# Inauspicious: 1, 3, 5, 7 (Janma, Vipat, Pratyak, Vadha)

TARA_AUSPICIOUS_REMAINDERS: frozenset[int] = frozenset({0, 2, 4, 6, 8})

# Each auspicious direction scores 1.5 pts; max 3 pts total (both directions auspicious).

# ---------------------------------------------------------------------------
# 8. Bhakoot inauspicious sign-count pairs
# ---------------------------------------------------------------------------
# Count from girl's Moon sign to boy's Moon sign (1-indexed, same sign = 1).
# If either the (girl→boy) count or (boy→girl) count forms a forbidden pair,
# the Bhakoot is inauspicious = 0 pts.  Otherwise = 7 pts.
#
# Forbidden combinations (expressed as {count_a, count_b} unordered pairs):
BHAKOOT_INAUSPICIOUS: list[frozenset[int]] = [
    frozenset({2, 12}),   # 2nd-12th axis
    frozenset({5, 9}),    # 5th-9th axis
    frozenset({6, 8}),    # 6th-8th axis
]

# ---------------------------------------------------------------------------
# 9. Mangal Dosha houses
# ---------------------------------------------------------------------------
# Mars in any of these house positions (counted from the reference lagna)
# constitutes Mangal Dosha from that lagna.

MANGAL_DOSHA_HOUSES: frozenset[int] = frozenset({1, 2, 4, 7, 8, 12})

# ---------------------------------------------------------------------------
# 10. Zodiac sign order (for house counting)
# ---------------------------------------------------------------------------
SIGN_ORDER: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
