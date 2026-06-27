"""
llm/interpreter.py
==================
AI chart interpretation via Claude.

Falls back gracefully when ANTHROPIC_API_KEY is not set so the app
remains fully functional without an API key (interpretations are simply
skipped).
"""

from __future__ import annotations

import os
import anthropic

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic | None:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


_CHART_SYSTEM = """You are an expert astrologer with deep knowledge of both Vedic (Jyotish) and Western astrology.
Provide natal chart interpretations that are specific, insightful, and grounded in the chart data given.
Focus on: Moon sign/nakshatra, Ascendant/Lagna, strong or prominent planets, notable aspects.
Write in a warm, accessible tone. Avoid vague generalities. Limit your response to 3-4 concise paragraphs."""

_COMPAT_SYSTEM = """You are an expert Vedic astrologer specialising in Guna Milan (Ashtakoot) compatibility.
Interpret the compatibility data with nuance — highlight genuine strengths and real challenges.
Explain the score in practical relationship terms. Mention doshas and their real-world implications.
Write warmly but honestly. Limit your response to 3-4 concise paragraphs."""


def _chart_summary(chart: dict, nakshatras: dict, aspects: list, name: str, birth_info: dict) -> str:
    planets = chart["planets"]
    houses = chart["houses"]

    lines = [
        f"Natal Chart for {name}",
        f"Date: {birth_info.get('date', '')}  Time: {birth_info.get('time', '')}",
        f"Place: {birth_info.get('place', '')}",
        f"Mode: {chart['mode'].title()} | Julian Day: {chart['julian_day']:.2f}",
        "",
        f"Ascendant (Lagna): {houses['ascendant_sign']} {houses['ascendant_degree']:.2f}°",
        f"Midheaven (MC): {houses['mc_sign']}",
        "",
        "Planetary Positions:",
    ]

    for planet, pos in planets.items():
        retro = " [Rx]" if pos.get("retrograde") else ""
        nak = nakshatras.get(planet, {})
        nak_str = (
            f" | {nak['name']} nakshatra (lord: {nak['lord']}, pada {nak['pada']})"
            if nak else ""
        )
        lines.append(
            f"  {planet:<10} {pos['sign']:<14} {pos['sign_degree']:.2f}°{retro}{nak_str}"
        )

    lines += ["", "Key Aspects (tightest first):"]
    for asp in aspects[:8]:
        lines.append(
            f"  {asp['planet_a']} {asp['aspect']} {asp['planet_b']}  "
            f"(orb {asp['orb_diff']:+.2f}°, {'applying' if asp['applying'] else 'separating'})"
        )

    return "\n".join(lines)


def _compat_summary(milan: dict, name1: str, name2: str) -> str:
    lines = [
        "Guna Milan (Ashtakoot Compatibility Analysis)",
        f"Person 1 (Boy): {name1}",
        f"Person 2 (Girl): {name2}",
        "",
        f"Person 1 Moon Nakshatra: {milan['boy_nakshatra']['name']} "
        f"(lord: {milan['boy_nakshatra']['lord']}, pada {milan['boy_nakshatra']['pada']})",
        f"Person 2 Moon Nakshatra: {milan['girl_nakshatra']['name']} "
        f"(lord: {milan['girl_nakshatra']['lord']}, pada {milan['girl_nakshatra']['pada']})",
        "",
        "Koota Scores:",
    ]

    for k in milan["kootas"]:
        lines.append(f"  {k['koota']:<18} {k['score']:.1f} / {k['max']}")

    md = milan["mangal_dosha"]
    lines += [
        "",
        f"Total Score: {milan['total_score']:.1f} / {milan['max_score']} ({milan['percentage']:.1f}%)",
        f"Verdict: {milan['summary']}",
        "",
        "Mangal Dosha:",
        f"  Person 1: {'Present' if md['boy']['has_dosha'] else 'Absent'} (severity: {md['boy']['severity']})",
        f"  Person 2: {'Present' if md['girl']['has_dosha'] else 'Absent'} (severity: {md['girl']['severity']})",
    ]
    if md["mutual_cancellation"]:
        lines.append("  Mutual cancellation: YES — both partners carry Mangal Dosha.")

    # Surface notable koota details
    for k in milan["kootas"]:
        if k.get("dosha"):
            lines.append(f"  Note: {k['koota']} dosha present.")
        if k.get("cancellation_note"):
            lines.append(f"  Note: {k['cancellation_note']}")

    return "\n".join(lines)


def interpret_natal_chart(
    chart: dict,
    nakshatras: dict,
    aspects: list,
    name: str,
    birth_info: dict,
) -> str:
    client = _get_client()
    if client is None:
        return "AI interpretation unavailable — add ANTHROPIC_API_KEY to .env to enable."

    summary = _chart_summary(chart, nakshatras, aspects, name, birth_info)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=900,
        system=_CHART_SYSTEM,
        messages=[{"role": "user", "content": f"Please interpret this natal chart:\n\n{summary}"}],
    )
    return msg.content[0].text


def interpret_compatibility(milan: dict, name1: str, name2: str) -> str:
    client = _get_client()
    if client is None:
        return "AI interpretation unavailable — add ANTHROPIC_API_KEY to .env to enable."

    summary = _compat_summary(milan, name1, name2)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=900,
        system=_COMPAT_SYSTEM,
        messages=[{"role": "user", "content": f"Please interpret this compatibility report:\n\n{summary}"}],
    )
    return msg.content[0].text
