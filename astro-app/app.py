"""
app.py
======
Flask application: API routes + template rendering.

Routes
------
GET  /                      — main single-page UI
POST /api/chart             — natal chart calculation + AI interpretation
POST /api/compatibility     — Guna Milan compatibility + AI interpretation
"""

from __future__ import annotations

import os
import sys

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

# Load .env before importing llm (which reads ANTHROPIC_API_KEY at import time)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ephemeris.calculations import calculate_chart
from ephemeris.nakshatras import get_all_planet_nakshatras
from ephemeris.aspects import get_aspects
from guna_milan.kootas import calculate_guna_milan
from geo import get_location_data, get_tz_offset_hours
from ephemeris.synastry import get_synastry_aspects
from ephemeris.transits import get_transits_for_chart
from llm.interpreter import interpret_natal_chart, interpret_compatibility

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_birth(data: dict, prefix: str = "") -> dict:
    """Extract and coerce birth fields from a JSON body."""
    p = prefix
    return {
        "name":   str(data.get(f"{p}name", "")).strip(),
        "year":   int(data[f"{p}year"]),
        "month":  int(data[f"{p}month"]),
        "day":    int(data[f"{p}day"]),
        "hour":   int(data[f"{p}hour"]),
        "minute": int(data[f"{p}minute"]),
        "second": int(data.get(f"{p}second", 0)),
        "place":  str(data[f"{p}place"]).strip(),
    }


def _compute(birth: dict) -> dict:
    """Geocode, calculate tropical + sidereal charts, nakshatras, aspects."""
    loc = get_location_data(birth["place"])
    tz_off = get_tz_offset_hours(
        loc["timezone"],
        birth["year"], birth["month"], birth["day"],
        birth["hour"], birth["minute"], birth["second"],
    )
    kwargs = dict(
        year=birth["year"], month=birth["month"], day=birth["day"],
        hour=birth["hour"], minute=birth["minute"], second=birth["second"],
        tz_offset_hours=tz_off,
        latitude=loc["latitude"], longitude=loc["longitude"],
    )
    sidereal = calculate_chart(**kwargs, mode="sidereal")
    tropical = calculate_chart(**kwargs, mode="tropical")
    nakshatras = get_all_planet_nakshatras(sidereal["planets"])
    aspects = get_aspects(tropical["planets"])

    return {
        "location":   loc,
        "tz_offset":  tz_off,
        "sidereal":   sidereal,
        "tropical":   tropical,
        "nakshatras": nakshatras,
        "aspects":    aspects,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chart", methods=["POST"])
def api_chart():
    try:
        data = request.get_json(force=True) or {}
        birth = _parse_birth(data)
        if not birth["place"]:
            return jsonify({"error": "Place of birth is required."}), 400

        payload = _compute(birth)
        birth_info = {
            "date":  f"{birth['day']:02d}/{birth['month']:02d}/{birth['year']}",
            "time":  f"{birth['hour']:02d}:{birth['minute']:02d}",
            "place": payload["location"]["address"],
        }

        interpretation = interpret_natal_chart(
            payload["sidereal"],
            payload["nakshatras"],
            payload["aspects"],
            birth["name"] or "Native",
            birth_info,
        )

        return jsonify({
            "name":           birth["name"],
            "birth_info":     birth_info,
            "location":       payload["location"],
            "tropical":       payload["tropical"],
            "sidereal":       payload["sidereal"],
            "nakshatras":     payload["nakshatras"],
            "aspects":        payload["aspects"][:12],
            "interpretation": interpretation,
        })

    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Chart error")
        return jsonify({"error": "Internal calculation error — check server logs."}), 500


@app.route("/api/compatibility", methods=["POST"])
def api_compatibility():
    try:
        data = request.get_json(force=True) or {}
        p1 = _parse_birth(data, prefix="p1_")
        p2 = _parse_birth(data, prefix="p2_")

        if not p1["place"] or not p2["place"]:
            return jsonify({"error": "Place of birth is required for both persons."}), 400

        pay1 = _compute(p1)
        pay2 = _compute(p2)

        milan = calculate_guna_milan(pay1["sidereal"], pay2["sidereal"])
        interpretation = interpret_compatibility(
            milan,
            p1["name"] or "Person 1",
            p2["name"] or "Person 2",
        )

        return jsonify({
            "person1":        {"name": p1["name"], "location": pay1["location"]},
            "person2":        {"name": p2["name"], "location": pay2["location"]},
            "sidereal1":      pay1["sidereal"],
            "sidereal2":      pay2["sidereal"],
            "nakshatras1":    pay1["nakshatras"],
            "nakshatras2":    pay2["nakshatras"],
            "milan":          milan,
            "interpretation": interpretation,
        })

    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Compatibility error")
        return jsonify({"error": "Internal calculation error — check server logs."}), 500


@app.route("/api/synastry", methods=["POST"])
def api_synastry():
    try:
        data = request.get_json(force=True) or {}
        p1 = _parse_birth(data, prefix="p1_")
        p2 = _parse_birth(data, prefix="p2_")
        if not p1["place"] or not p2["place"]:
            return jsonify({"error": "Place of birth is required for both persons."}), 400

        pay1 = _compute(p1)
        pay2 = _compute(p2)

        inter_aspects = get_synastry_aspects(
            pay1["tropical"]["planets"],
            pay2["tropical"]["planets"],
        )

        return jsonify({
            "person1":       {"name": p1["name"], "location": pay1["location"]},
            "person2":       {"name": p2["name"], "location": pay2["location"]},
            "tropical1":     pay1["tropical"],
            "tropical2":     pay2["tropical"],
            "inter_aspects": inter_aspects,
        })
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Synastry error")
        return jsonify({"error": "Internal calculation error."}), 500


@app.route("/api/transits", methods=["POST"])
def api_transits():
    try:
        data = request.get_json(force=True) or {}
        birth = _parse_birth(data)
        if not birth["place"]:
            return jsonify({"error": "Place of birth is required."}), 400

        payload = _compute(birth)
        transits = get_transits_for_chart(payload["tropical"])

        return jsonify({
            "name":          birth["name"],
            "natal":         payload["tropical"],
            "current":       transits["current"],
            "transit_aspects": transits["aspects"],
        })
    except (KeyError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        app.logger.exception("Transits error")
        return jsonify({"error": "Internal calculation error."}), 500



# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
