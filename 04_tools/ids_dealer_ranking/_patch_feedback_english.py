#!/usr/bin/env python3
"""English bands + GPS capture % on dealer feedback packs."""

from __future__ import annotations

from pathlib import Path

P = Path(__file__).resolve().parent / "build_ids_dealer_feedback.py"


def main() -> None:
    if not P.is_file():
        print("missing", P)
        return
    t = P.read_text(encoding="utf-8")
    t = t.replace('"Goed"', '"Good"').replace('"Slecht"', '"Bad"')
    t = t.replace("Strengths (goed)", "Strengths (good)")
    t = t.replace("Weak points (slecht)", "Weak points (bad)")
    t = t.replace("weak wedges = slecht", "weak wedges = bad")
    t = t.replace("section slecht", "section bad")
    t = t.replace("no slecht section", "no bad section")
    t = t.replace("'slecht'", "'bad'")

    if "def _pct(" not in t:
        t = t.replace(
            "def _eur(",
            'def _pct(v):\n'
            "    if v is None:\n"
            '        return "—"\n'
            "    try:\n"
            "        x = float(v)\n"
            '        return f"{x * 100:.0f}%" if x <= 1.5 else f"{x:.0f}%"\n'
            "    except (TypeError, ValueError):\n"
            '        return "—"\n\n'
            "def _eur(",
        )

    if 'row["gps_capture_vs_max"]' not in t:
        t = t.replace(
            'row["gps_spu_eur"] = gps[prism].get("gps_spu_eur")',
            'row["gps_spu_eur"] = gps[prism].get("gps_spu_eur")\n'
            '            row["gps_capture_vs_max"] = gps[prism].get("gps_capture_vs_max")',
        )
    t = t.replace(
        '"gps_spu_eur": None,\n            "gps_traffic": None,',
        '"gps_spu_eur": None,\n            "gps_capture_vs_max": None,\n            "gps_traffic": None,',
    )

    old = (
        '<div class="stat"><strong>{_eur(db_kpi.get("gps_spu_eur"))}</strong>'
        "<span>GPS €/UIO 2025</span></div>"
    )
    new = (
        '<div class="stat"><strong>'
        '{_pct(db_kpi.get("gps_capture_vs_max")) if db_kpi.get("gps_capture_vs_max") is not None else _eur(db_kpi.get("gps_spu_eur"))}'
        "</strong><span>"
        '{"GPS capture % 2025" if db_kpi.get("gps_capture_vs_max") is not None else "GPS €/UIO 2025"}'
        "</span></div>"
    )
    if old in t:
        t = t.replace(old, new)
        print("gps card -> capture % preferred")
    else:
        print("WARN gps card pattern not found")

    P.write_text(t, encoding="utf-8")
    low = t.lower()
    print("feedback done; goed=", low.count("goed"), "slecht=", low.count("slecht"))


if __name__ == "__main__":
    main()
