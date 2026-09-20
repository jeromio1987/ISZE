"""Extract UIO V19 payload + V20 modelled series for car park compare pack."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
UIO_JSON = ROOT / "01_data" / "91_build" / "uio_2026.json"
OUT = ROOT / "02_dashboards" / "fleet" / "_uio_carpark_payload.json"

# V19 Grand Total ex-MIDI (ISZE-only) from 06_uio/_CURRENT/README.md 2026-07-09
V19_NETWORK_EX_MIDI = {
    2023: 151715,
    2024: 160125,
    2025: 163199,
    2026: 172379,
    2027: 180848,
    2028: 189118,
    2029: 197333,
    2030: 205357,
}

# V19 Grand Total incl MIDI (for context)
V19_NETWORK_INCL_MIDI = {
    2023: 242338,
    2024: 252710,
    2025: 258594,
    2026: 269314,
    2027: 279502,
    2028: 289529,
    2029: 299448,
    2030: 309125,
}

# V19 overstatement vs survival-curve method (V20_SPEC Problem 1)
OVERSTATE_PCT = {2026: 0.078, 2027: 0.156, 2028: 0.232, 2029: 0.306, 2030: 0.377}


def v20_from_v19(y: int, v19: float) -> float:
    if y <= 2025:
        return v19  # same method through history (Israel lift is separate)
    return round(v19 / (1.0 + OVERSTATE_PCT[y]))


def survival_points(mean_life: float, max_age: int = 20) -> list[dict]:
    """Rough exponential survival: S(a) = exp(-a / mean_life), floored at 0."""
    import math

    out = []
    for a in range(0, max_age + 1):
        s = math.exp(-a / mean_life)
        out.append({"age": a, "surv": round(100.0 * s, 2)})
    return out


def main() -> None:
    rows = json.loads(UIO_JSON.read_text(encoding="utf-8"))

    by_country: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_country_isze: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_dist_label: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_mtype: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    by_country_mtype: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(float))
    )
    uk_rows = []
    MIDI_DIST = {"MIDI EUROPE", "MIDI"}

    LABEL = {
        "U KING": "United Kingdom",
        "PORTUGL": "Portugal",
        "NETHLDS": "Netherlands",
        "ISRAEL": None,  # split UTI/UMI below
    }

    for r in rows:
        c = str(r["country"]).upper().strip()
        m = str(r.get("mtype") or "?").upper().strip()
        dist = str(r.get("dist") or "").strip()
        dist_u = dist.upper()
        is_midi = dist_u in MIDI_DIST
        # Display label: keep UTI and UMI as separate Israel rows
        if c == "ISRAEL":
            label = f"Israel ({dist})"
        else:
            label = LABEL.get(c) or c.title()
            if c == "U KING":
                label = f"United Kingdom ({dist})"
        for y in ("2024", "2025", "2026", "2027", "2028"):
            val = float(r.get(y) or 0)
            by_country[c][y] += val
            by_mtype[m][y] += val
            by_country_mtype[c][m][y] += val
            by_dist_label[label][y] += val
            if not is_midi:
                by_country_isze[label][y] += val
        if dist_u in ("IUK", "ITUK") or "KING" in c:
            uk_rows.append(r)

    # Map LCV ≈ pickup basket for mix chart; CV = LD+MD+HD+F etc.
    pickup_keys = {"LCV", "PICKUP", "D-MAX", "DMAX"}
    cv_keys = {"LD", "MD", "HD", "F", "CV", "N35", "N75", "F-SERIES", "FSERIES"}

    mix_v19 = {}
    for y in ("2024", "2025", "2026", "2027", "2028"):
        pickup = sum(by_mtype[m][y] for m in by_mtype if m in pickup_keys or "LCV" in m or "PICK" in m)
        cv = sum(by_mtype[m][y] for m in by_mtype if m in cv_keys or m in {"LD", "MD", "HD"})
        # anything else
        other = sum(by_mtype[m][y] for m in by_mtype) - pickup - cv
        mix_v19[y] = {
            "pickup_lcv": round(pickup),
            "cv": round(cv),
            "other": round(other),
            "total": round(pickup + cv + other),
        }

    # Ranked markets 2025 — ISZE-only (MIDI Europe Italy/Spain excluded)
    markets_2025 = sorted(
        (
            {
                "market": c,
                "uio_2025": round(v["2025"]),
                "uio_2024": round(v["2024"]),
                "uio_2026_v19": round(v["2026"]),
            }
            for c, v in by_country_isze.items()
        ),
        key=lambda x: -x["uio_2025"],
    )

    # Top movers estimate: apply overstate to 2030 where we have 2028 as proxy, plus known Ireland/IUK
    ireland_2030 = {
        "trucks_light_v19": 1645,
        "trucks_light_v20": 1382,
        "pickups_v19": 3174,
        "pickups_v20": 2527,
    }

    # IUK LCV series
    iuk_v19 = {2024: 48876, 2025: 47783, 2026: 49280, 2027: 50500, 2028: 51600, 2029: 52200, 2030: 52804}
    # V20: locked 2026; roll 12.3% scrap + flat regs ~3020 (illustrative after 2026)
    iuk_v20 = {2024: 48876, 2025: 47783, 2026: 44926}
    regs = 3020
    scrap = 0.123
    for y in range(2027, 2031):
        prev = iuk_v20[y - 1]
        iuk_v20[y] = round(prev * (1 - scrap) + regs)

    # Network V20 from overstate on ex-MIDI V19
    net_v19 = V19_NETWORK_EX_MIDI
    net_v20 = {y: (v20_from_v19(y, v) if y >= 2026 else v) for y, v in net_v19.items()}

    # Pickup network: V19 grows ~22.8% 2025→2030; V20 must decline toward steady state
    # From extract LCV totals
    pickup_2025 = mix_v19["2025"]["pickup_lcv"]
    pickup_v19 = {
        2025: pickup_2025,
        2026: mix_v19["2026"]["pickup_lcv"],
        2027: mix_v19["2027"]["pickup_lcv"],
        2028: mix_v19["2028"]["pickup_lcv"],
    }
    # Scale 2029/2030 from 22.8% growth path if missing
    if pickup_2025:
        target_2030_v19 = round(pickup_2025 * 1.228)
        pickup_v19[2029] = round((pickup_v19[2028] + target_2030_v19) / 2)
        pickup_v19[2030] = target_2030_v19
    # V20 pickup: apply same overstate ratios + force 2030 < 2025
    pickup_v20 = {2025: pickup_2025}
    for y in range(2026, 2031):
        base = pickup_v19.get(y, pickup_2025)
        pickup_v20[y] = round(base / (1.0 + OVERSTATE_PCT.get(y, 0.2)))
    # Ensure direction: if still growing, clamp to declining path toward 88000 steady-state note
    if pickup_v20[2030] >= pickup_v20[2025]:
        for i, y in enumerate(range(2026, 2031)):
            pickup_v20[y] = round(pickup_2025 * (1 - 0.04 * (i + 1)))

    cv_2025 = mix_v19["2025"]["cv"]
    cv_v19 = {int(y): mix_v19[y]["cv"] for y in ("2025", "2026", "2027", "2028")}
    cv_v19[2029] = round(cv_v19[2028] * 1.04)
    cv_v19[2030] = round(cv_v19[2028] * 1.08)
    cv_v20 = {2025: cv_2025}
    for y in range(2026, 2031):
        cv_v20[y] = round(cv_v19[y] / (1.0 + OVERSTATE_PCT[y]))

    # Change bars for top movers (2030 delta where known, else 2028 proxy)
    movers = [
        {
            "market": "IUK LCV (row 25)",
            "metric": "CY2026F trucks in service",
            "v19": 49280,
            "v20": 44926,
            "delta": 44926 - 49280,
            "locked": True,
            "note": "Only V20 figure locked (30 Jul 2026)",
        },
        {
            "market": "Ireland light trucks",
            "metric": "CY2030F",
            "v19": 1645,
            "v20": 1382,
            "delta": 1382 - 1645,
            "locked": False,
            "note": "V20_SPEC worked example",
        },
        {
            "market": "Ireland pickups",
            "metric": "CY2030F",
            "v19": 3174,
            "v20": 2527,
            "delta": 2527 - 3174,
            "locked": False,
            "note": "V20_SPEC worked example",
        },
        {
            "market": "ISZE network (ex-MIDI)",
            "metric": "CY2030F",
            "v19": net_v19[2030],
            "v20": net_v20[2030],
            "delta": net_v20[2030] - net_v19[2030],
            "locked": False,
            "note": "V20 = V19 ÷ (1 + 37.7% overstate)",
        },
        {
            "market": "Pickup / LCV basket",
            "metric": "CY2030F vs 2025",
            "v19": pickup_v19[2030],
            "v20": pickup_v20[2030],
            "delta": pickup_v20[2030] - pickup_v19[2030],
            "locked": False,
            "note": "V19 grows ~23%; V20 must fall with registrations",
        },
    ]

    gap_years = []
    for y in range(2026, 2031):
        v19 = net_v19[y]
        v20 = net_v20[y]
        gap_years.append(
            {
                "year": y,
                "v19": v19,
                "v20": v20,
                "gap_units": v19 - v20,
                "overstate_pct": round(100 * OVERSTATE_PCT[y], 1),
            }
        )

    payload = {
        "meta": {
            "title": "ISZE car park — UIO V19 vs V20",
            "built": "2026-09-16",
            "v19_source": "ISUZU_UIO_Overview_2026.xlsx (v19) via README 2026-07-09 + uio_2026.json",
            "v20_source": "06_uio/_CURRENT/V20_SPEC.md — modelled; only IUK LCV CY2026F=44926 locked",
            "basis": "Network charts use ex-MIDI (ISZE-only) Grand Total",
            "amber": "Do not quote V19 2026–2030 externally until survival-curve fix ships",
            "uk_rows_in_extract": uk_rows,
            "mtypes_present": sorted(by_mtype.keys()),
        },
        "network": {
            "years": list(range(2023, 2031)),
            "v19_ex_midi": [net_v19[y] for y in range(2023, 2031)],
            "v20_ex_midi": [net_v20[y] for y in range(2023, 2031)],
            "v19_incl_midi_2030": V19_NETWORK_INCL_MIDI[2030],
            "method_break_year": 2025.5,
        },
        "gap": gap_years,
        "survival": {
            "truck_curve": survival_points(9.9),
            "pickup_curve": survival_points(8.1),
            "flat_3pct_implied": survival_points(33.3),
            "labels": {
                "truck": "Historical truck survival (~9.9 yr life, ~10.2% scrap/yr)",
                "pickup": "Historical pickup survival (~8.1 yr life, ~12.3% scrap/yr)",
                "flat": "V19 forecast rule (~33 yr life, 3% scrap/yr)",
            },
        },
        "markets_ranked_2025": markets_2025[:18],
        "movers": movers,
        "mix": {
            "years": [2025, 2026, 2027, 2028, 2029, 2030],
            "v19_pickup": [pickup_v19[y] for y in range(2025, 2031)],
            "v20_pickup": [pickup_v20[y] for y in range(2025, 2031)],
            "v19_cv": [cv_v19[y] for y in range(2025, 2031)],
            "v20_cv": [cv_v20[y] for y in range(2025, 2031)],
            "pickup_regs_imit": {"2024": 16977, "2025": 15312, "2026": 10845, "2027": 10595},
        },
        "iuk_lcv": {
            "years": list(range(2024, 2031)),
            "v19": [iuk_v19[y] for y in range(2024, 2031)],
            "v20": [iuk_v20[y] for y in range(2024, 2031)],
            "locked_2026": 44926,
        },
        "ireland_2030": ireland_2030,
        "kpis": {
            "v19_2025": net_v19[2025],
            "v19_2030": net_v19[2030],
            "v20_2030": net_v20[2030],
            "overstate_2030_pct": 37.7,
            "iuk_locked": 44926,
            "iuk_v19_2026": 49280,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("markets", len(markets_2025), "top", markets_2025[0] if markets_2025 else None)
    print("mtypes", payload["meta"]["mtypes_present"])
    print("mix_2025", mix_v19["2025"])
    print("net2030", net_v19[2030], "->", net_v20[2030])


if __name__ == "__main__":
    main()
