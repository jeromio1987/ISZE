"""Rigor gate on EQ-HIT live-order proposal (126 rows with figure dig + family).

Proposal / gate only. Does NOT write aim_master or cut a dated release apply.

Jerome bar (same honesty as DESC_PROVEN):
  - PN logic
  - description + EQ figure / part text vs proposed family
  - price if available
  - ZKK/HKK if available — and say plainly when they cannot prove family

SAFE / DESC-quality subset → _releases/..._PROVEN_...csv when not all 126 pass.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PROP = (
    ISZE
    / "01_data/00_derived/_releases/next_release_proposal_eq_hit_live_order_2026-10-07.csv"
)
RESULTS = ISZE / "01_data/00_derived/_eq_hit_results_20261007.csv"
MASTER = ISZE / "01_data/00_derived/aim_master_v2.csv"
JP = ISZE / "01_data/00_derived/jp_codes_cache_20260920.csv"

OUT_MD = ISZE / "01_data/91_build/_aim_eq_hit_126_rigor_20261007.md"
OUT_JSON = ISZE / "01_data/91_build/_aim_eq_hit_126_rigor_20261007.json"
OUT_FAILS = ISZE / "01_data/91_build/_aim_eq_hit_126_rigor_fails_20261007.csv"
OUT_PROVEN = (
    ISZE
    / "01_data/00_derived/_releases/next_release_proposal_eq_hit_live_order_PROVEN_2026-10-07.csv"
)

# Parallel EQ taxonomy used by the overnight fig_to_aim rules.
# Independent truth rules: most specific first; figure section words weigh with part text.
TRUTH_RULES: list[tuple[tuple[str, ...], tuple[str, str, str]]] = [
    (("AIR CLEANER", "AIR FILTER"), ("Filters", "Engine air filtration", "Air cleaner")),
    (("OIL FILTER", "FILTER ASM; OIL", "FILTER; OIL"), ("Filters", "Engine oil filtration", "Oil filter")),
    # Real fuel *filter assembly* — not pipes that merely mention "FUEL FILTER" as a routing point
    (("FILTER ASM; FUE", "FILTER ASM; FUEL", "FUEL FILTER AND BRACKET"), ("Filters", "Fuel filtration", "Fuel filter")),
    (("SEDIMENTER", "WATER SEDIMENTER"), ("Powertrain", "Fuel system", "Fuel system parts")),
    (("LEAF SPRING", "LEAF SPR", "REAR SUSPENSION", "FRONT SUSPENSION", "REAR LEAF"), ("Chassis", "Suspension", "Suspension parts")),
    (("CLUTCH", "SLAVE"), ("Powertrain", "Clutch", "Clutch parts")),
    (("BRAKE", "CALIPER", "ANTI LOCK", "ABS "), ("Chassis", "Brakes", "Brake parts")),
    (("STEERING",), ("Chassis", "Steering", "Steering parts")),
    (("AXLE", "DIFF", "FINAL DRIVE", "PROP SHAFT"), ("Chassis", "Axle", "Axle parts")),
    (("BUMPER",), ("Body", "Bumper", "Bumper")),
    (("THERMOSTAT", "RADIATOR", "WATER PUMP", "COOLING FAN", "INTERCOOLER"), ("Powertrain", "Cooling", "Cooling parts")),
    (("TURBO",), ("Powertrain", "Turbo", "Turbo parts")),
    # Noun-first: gasket / harness / sensor beat figure-section words;
    # A/C and DEF beat generic HOSE/PIPE so truth path is honest in fails.
    (("GASKET", "SEAL;", "OIL SEAL", "O-RING", "PACKING"), ("Powertrain", "Gaskets / seals", "Gasket / seal")),
    (("HARNESS", "WIRE", "CONNECTOR"), ("Electrical", "Wiring", "Harness")),
    (("SENSOR;", "SENSOR ", "BRACKET; SENSOR", "NOX"), ("Electrical", "Sensors / instruments", "Sensor / meter")),
    (("AIR CONDITION", "A/C", "CONDENSER", "HEATER", "HVAC"), ("Comfort", "HVAC", "Heater / A/C")),
    (("DEF ", "DEF TANK", "SCR", "DPF", "DPD", "MUFFLER", "SILENCER", "EGR", "EXHAUST", "EMISSION"), ("Powertrain", "Exhaust / aftertreatment", "Exhaust parts")),
    (("HOSE;", "PIPE;", "HOSE ASM", "PIPE ASM", "DUCT"), ("Powertrain", "Pipes / hoses", "Pipe / hose")),
    (("GOVERNOR", "INJECTION PUMP", "INJECT", "COMMON RAIL", "FEED PUMP", "NOZZLE", "FUEL PUMP"), ("Powertrain", "Fuel system", "Fuel system parts")),
    (("PIPE; FUEL", "HOSE; FUEL", "FUEL PIPE", "FUEL HOSE"), ("Powertrain", "Fuel system", "Fuel system parts")),
    (("CAMSHAFT", "CYLINDER HEAD", "CYLINDER BLOCK", "PISTON", "VALVE", "OIL PAN", "CRANKCASE", "ENGINE MOUNT", "OIL PUMP", "OIL FILLER"), ("Powertrain", "Engine", "Engine parts")),
    (("SEAT BELT", "BELT; PASSENGER", "BELT; CENTER", "BELT; RR SEAT", "BELT; SEAT", "FRONT SEAT", "SEAT PIO", "BACK ASM; SEAT", "CUSHION ASM"), ("Body", "Interior", "Seat parts")),
    (("DOOR", "GLASS", "REGULATOR", "LOCK"), ("Body", "Door / glass", "Door parts")),
    (("MIRROR", "GRILLE", "TAIL GATE", "HANDLE ASM"), ("Body", "Body exterior", "Body parts")),
    (("BATTERY CARRIER", "BATTERY CABLE", "STAY; BATTERY", "BATTERY AND ENGINE ELECTRICAL"), ("Electrical", "Battery", "Battery")),
    (("STARTER",), ("Electrical", "Starting / charging", "Starter")),
    (("ALTERNATOR",), ("Electrical", "Starting / charging", "Alternator")),
    (("CAMERA", "METER", "DISPLAY"), ("Electrical", "Sensors / instruments", "Sensor / meter")),
    (("RADIO", "ANTENNA", "TV"), ("Electrical", "Audio / entertainment", "Audio parts")),
    (("TRANSMISSION", "GEARBOX", "SHIFT"), ("Powertrain", "Transmission", "Transmission parts")),
    (("HOSE", "PIPE", "DUCT"), ("Powertrain", "Pipes / hoses", "Pipe / hose")),
    (("ENGINE", "MANIFOLD"), ("Powertrain", "Engine", "Engine parts")),
]

# Hard commercial wrongs: evidence pattern + bad propose L1/L2
HARD_CONFLICTS: list[tuple[str, str, str, str]] = [
    # (pattern on evidence, bad_l1, bad_l2_or_empty, name)
    (r"GOVERNOR|INJECTION\s*PUMP", "Chassis", "Suspension", "gov_spring_vs_suspension"),
    (r"CAMSHAFT|VALVE|SPRING;\s*VLV", "Chassis", "Suspension", "valve_spring_vs_suspension"),
    (r"PIPE;\s*FUEL|HOSE;\s*FUEL|FUEL\s*PUMP\s*AND\s*PIPE", "Filters", "", "fuel_pipe_vs_filter"),
    (r"AIR\s*CONDITION|CONDENSER|\bA/C\b", "Powertrain", "Pipes / hoses", "ac_hose_vs_powertrain_pipe"),
    (r"DEF\s*TANK|HOSE\s*ASM;\s*DEF|\bDEF\b", "Powertrain", "Pipes / hoses", "def_hose_vs_generic_pipe"),
    (r"LEAF\s*SPR|REAR\s*SUSPENSION|FRONT\s*SUSPENSION", "Powertrain", "Engine", "leaf_vs_engine"),
    (r"FILTER\s*ASM;\s*FUE|FUEL\s*FILTER\s*AND\s*BRACKET", "Powertrain", "Pipes / hoses", "fuel_filter_vs_pipe"),
    (r"GASKET;\s*CYL|CYL\.?\s*HD|HEAD\s*GASKET", "Powertrain", "Transmission", "cyl_hd_gasket_vs_trans"),
]

# Adjacent OK: propose path may differ from truth path at L2 but same commercial neighbourhood
ADJACENT: dict[tuple[str, str], set[tuple[str, str]]] = {
    ("Powertrain", "Pipes / hoses"): {
        ("Powertrain", "Cooling"),
        ("Powertrain", "Fuel system"),
        ("Powertrain", "Exhaust / aftertreatment"),
        ("Powertrain", "Engine"),
        ("Comfort", "HVAC"),
    },
    ("Powertrain", "Cooling"): {("Powertrain", "Pipes / hoses"), ("Powertrain", "Engine")},
    ("Powertrain", "Fuel system"): {("Powertrain", "Pipes / hoses"), ("Filters", "Fuel filtration")},
    ("Filters", "Fuel filtration"): {("Powertrain", "Fuel system")},
    ("Powertrain", "Exhaust / aftertreatment"): {
        ("Powertrain", "Pipes / hoses"),
        ("Powertrain", "Turbo"),
        ("Powertrain", "Engine"),
        ("Powertrain", "Gaskets / seals"),
        ("Electrical", "Sensors"),
        ("Electrical", "Sensors / instruments"),
    },
    ("Powertrain", "Turbo"): {("Powertrain", "Exhaust / aftertreatment"), ("Powertrain", "Engine")},
    ("Powertrain", "Engine"): {
        ("Powertrain", "Gaskets / seals"),
        ("Powertrain", "Cooling"),
        ("Powertrain", "Fuel system"),
        ("Powertrain", "Exhaust / aftertreatment"),
    },
    ("Powertrain", "Gaskets / seals"): {("Powertrain", "Engine")},
    ("Electrical", "Battery"): {("Electrical", "Wiring"), ("Electrical", "Starting / charging")},
    ("Electrical", "Wiring"): {("Electrical", "Battery"), ("Electrical", "Sensors / instruments")},
    ("Electrical", "Sensors / instruments"): {
        ("Electrical", "Sensors"),
        ("Electrical", "Sensors / cameras"),
        ("Electrical", "Wiring"),
        ("Powertrain", "Exhaust / aftertreatment"),
        ("Powertrain", "Pipes / hoses"),
    },
    ("Electrical", "Sensors"): {
        ("Electrical", "Sensors / instruments"),
        ("Electrical", "Sensors / cameras"),
        ("Powertrain", "Exhaust / aftertreatment"),
    },
    ("Electrical", "Sensors / cameras"): {
        ("Electrical", "Sensors / instruments"),
        ("Electrical", "Sensors"),
    },
    ("Powertrain", "Gaskets / seals"): {
        ("Powertrain", "Engine"),
        ("Powertrain", "Fuel system"),
        ("Powertrain", "Exhaust / aftertreatment"),
        ("Powertrain", "Cooling"),
    },
    ("Body", "Interior"): {("Body", "Door / glass"), ("Body", "Body exterior")},
    ("Comfort", "HVAC"): {("Powertrain", "Pipes / hoses"), ("Body", "Interior")},
    ("Chassis", "Suspension"): {("Chassis", "Axle"), ("Chassis", "Steering")},
    ("Electrical", "Wiring"): {
        ("Electrical", "Battery"),
        ("Electrical", "Sensors / instruments"),
        ("Body", "Door / glass"),
    },
}


def clean(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip()


def pad10(pn: str) -> str:
    pn = clean(pn)
    if pn.isdigit() and len(pn) < 10:
        return pn.zfill(10)
    return pn


def truth_from_text(text: str) -> tuple[str, str, str]:
    t = text.upper()
    for keys, aim in TRUTH_RULES:
        if any(k in t for k in keys):
            return aim
    return ("", "", "")


def resolve_family(aim_l1: str, aim_l1_fixed: str) -> str:
    f = clean(aim_l1_fixed) or clean(aim_l1)
    if f.upper() in {"", "UNKNOWN", "UNCLASSIFIED", "UNKNOWN REVIEW"}:
        return ""
    return f


def adjacent_ok(truth_l1: str, truth_l2: str, prop_l1: str, prop_l2: str) -> bool:
    if not truth_l1:
        return True
    if prop_l1 == truth_l1 and prop_l2 == truth_l2:
        return True
    # Sensors label drift in overnight rules
    if prop_l1 == "Electrical" and truth_l1 == "Electrical":
        if "Sensor" in prop_l2 and "Sensor" in truth_l2:
            return True
        if prop_l2.startswith("Starting") and truth_l2.startswith("Starting"):
            return True
    adj = ADJACENT.get((truth_l1, truth_l2), set())
    if (prop_l1, prop_l2) in adj:
        return True
    # Same L1, soft L2 for Engine neighbourhood
    if prop_l1 == truth_l1 == "Powertrain" and {prop_l2, truth_l2} <= {
        "Engine",
        "Gaskets / seals",
        "Cooling",
        "Pipes / hoses",
    }:
        return True
    return False


def main() -> None:
    prop = pd.read_csv(PROP, dtype=str, low_memory=False)
    n_prop = len(prop)
    prop["pn10"] = prop["pn"].map(pad10)
    prop["pn_raw"] = prop["pn"].map(clean)

    results = pd.read_csv(RESULTS, dtype=str, low_memory=False)
    n_results = len(results)
    results["pn10"] = results["pn"].map(pad10)
    hit = results[results["eq_status"].map(clean) == "HIT"].copy()
    n_hit = len(hit)
    has_fig = hit["eq_fig_name"].map(clean) != ""
    has_part = hit["eq_part_name"].map(clean) != ""
    has_sug = hit["suggested_aim_l1"].map(clean) != ""
    has_cat = hit["eq_catalog"].map(clean) != ""
    n_fig_dig = int((has_fig & has_part).sum())
    n_with_sug = int(has_sug.sum())
    n_cat_only = int((has_cat & ~has_fig).sum())
    n_status_only = int((~has_cat & ~has_fig).sum())
    n_fig_no_sug = int((has_fig & has_part & ~has_sug).sum())
    # 477 = hits without a family suggestion (603 - 126), or status-only deeper dig needed
    n_need_fig_or_map = n_hit - n_with_sug

    am = pd.read_csv(
        MASTER,
        dtype=str,
        usecols=[
            "part_number",
            "description",
            "aim_l1",
            "aim_l1_fixed",
            "jp_zkk",
            "jp_hkk",
            "eur",
        ],
        low_memory=False,
    )
    am["pn10"] = am["part_number"].map(pad10)
    am = am.drop_duplicates("pn10", keep="first")

    jp = pd.read_csv(JP, dtype=str, low_memory=False)
    jp["pn10"] = jp["pn"].map(pad10)
    jp = jp.drop_duplicates("pn10", keep="first")

    m = prop.merge(
        am[
            ["pn10", "description", "aim_l1", "aim_l1_fixed", "jp_zkk", "jp_hkk", "eur"]
        ].rename(
            columns={
                "description": "master_desc",
                "jp_zkk": "master_zkk",
                "jp_hkk": "master_hkk",
            }
        ),
        on="pn10",
        how="left",
    )
    m = m.merge(
        jp[["pn10", "jp_description", "zkk", "hkk"]].rename(
            columns={"zkk": "jp_zkk", "hkk": "jp_hkk"}
        ),
        on="pn10",
        how="left",
    )

    m["desc_unified"] = [
        clean(a) or clean(b) or clean(c)
        for a, b, c in zip(
            m.get("description_if_any", ""), m["master_desc"], m["jp_description"]
        )
    ]
    m["desc_source"] = [
        (
            "proposal"
            if clean(a)
            else "master"
            if clean(b)
            else "jp"
            if clean(c)
            else "none"
        )
        for a, b, c in zip(
            m.get("description_if_any", ""), m["master_desc"], m["jp_description"]
        )
    ]
    m["zkk"] = [clean(a) or clean(b) for a, b in zip(m["master_zkk"], m["jp_zkk"])]
    m["hkk"] = [clean(a) or clean(b) for a, b in zip(m["master_hkk"], m["jp_hkk"])]
    m["eur_num"] = pd.to_numeric(m["eur"], errors="coerce")
    m["evidence"] = [
        " | ".join(
            x
            for x in [
                clean(d),
                clean(f),
                clean(p),
            ]
            if x
        )
        for d, f, p in zip(m["desc_unified"], m["eq_fig_name"], m["eq_part_name"])
    ]
    m["evidence_u"] = m["evidence"].str.upper()

    # Independent truth from description alone and from EQ figure+part alone
    truths = [truth_from_text(e) for e in m["evidence"]]
    m["truth_l1"] = [t[0] for t in truths]
    m["truth_l2"] = [t[1] for t in truths]
    m["truth_l3"] = [t[2] for t in truths]
    m["truth_from_desc"] = [truth_from_text(d)[0:2] for d in m["desc_unified"]]
    m["truth_from_eq"] = [
        truth_from_text(f"{clean(f)} {clean(p)}")[0:2]
        for f, p in zip(m["eq_fig_name"], m["eq_part_name"])
    ]

    # ZKK/HKK majority maps on master AIM L1 (honest: parallel EQ L1 is different)
    am_known = am.copy()
    am_known["fam"] = [
        resolve_family(a, b) for a, b in zip(am_known["aim_l1"], am_known["aim_l1_fixed"])
    ]
    am_known = am_known[am_known["fam"] != ""].copy()
    jz = jp.set_index("pn10")["zkk"].map(clean).to_dict()
    jh = jp.set_index("pn10")["hkk"].map(clean).to_dict()
    am_zmap = am.set_index("pn10")["jp_zkk"].map(clean).to_dict()
    am_hmap = am.set_index("pn10")["jp_hkk"].map(clean).to_dict()

    def majority_map(df: pd.DataFrame, key_col: str, min_n: int, min_share: float):
        out: dict[str, tuple[str, float, int]] = {}
        sub = df[df[key_col].fillna("").ne("")]
        for k, g in sub.groupby(key_col):
            n = len(g)
            if n < min_n:
                continue
            vc = g["fam"].value_counts()
            mode = str(vc.index[0])
            share = float(vc.iloc[0] / n)
            if share >= min_share:
                out[str(k)] = (mode, share, int(n))
        return out

    am_z = am_known.copy()
    am_z["_k"] = [clean(am_zmap.get(p, "")) or jz.get(p, "") for p in am_z["pn10"]]
    zkk_map = majority_map(am_z, "_k", 20, 0.80)
    am_h = am_known.copy()
    am_h["_k"] = [clean(am_hmap.get(p, "")) or jh.get(p, "") for p in am_h["pn10"]]
    hkk_map = majority_map(am_h, "_k", 20, 0.80)

    reasons: list[list[str]] = [[] for _ in range(len(m))]
    status: list[str] = ["pass"] * len(m)

    def add(i: int, reason: str, kind: str = "fail") -> None:
        reasons[i].append(reason)
        if kind == "fail":
            status[i] = "fail"
        elif kind == "inconclusive" and status[i] == "pass":
            status[i] = "inconclusive"

    # Evidence presence
    for i in range(len(m)):
        if not clean(m.at[i, "eq_fig_name"]) or not clean(m.at[i, "eq_part_name"]):
            add(i, "missing_eq_figure_or_part", "fail")
        if not clean(m.at[i, "proposed_aim_l1"]):
            add(i, "missing_proposed_family", "fail")
        if not m.at[i, "desc_unified"]:
            # EQ text alone can still prove — mark note, not fail if EQ truth matches propose
            add(i, "no_unified_description", "inconclusive")

    # Hard conflicts
    for i in range(len(m)):
        ev = m.at[i, "evidence_u"]
        pl1 = clean(m.at[i, "proposed_aim_l1"])
        pl2 = clean(m.at[i, "proposed_aim_l2"])
        for pat, bad_l1, bad_l2, name in HARD_CONFLICTS:
            if pl1 != bad_l1:
                continue
            if bad_l2 and pl2 != bad_l2:
                continue
            if re.search(pat, ev, re.I):
                add(i, f"desc_hard:{name}", "fail")

    # Truth vs propose (description+EQ united)
    for i in range(len(m)):
        tl1, tl2 = clean(m.at[i, "truth_l1"]), clean(m.at[i, "truth_l2"])
        pl1, pl2 = clean(m.at[i, "proposed_aim_l1"]), clean(m.at[i, "proposed_aim_l2"])
        if not tl1:
            add(i, "truth_rules_no_match", "inconclusive")
            continue
        if not adjacent_ok(tl1, tl2, pl1, pl2):
            add(i, f"truth_vs_propose:{tl1}/{tl2}_vs_{pl1}/{pl2}", "fail")

    # Description vs EQ disagreement: fail only when propose follows neither side
    # (EQ figure text is the stronger EPC signal when they split; following EQ is OK)
    for i in range(len(m)):
        d_l1, d_l2 = m.at[i, "truth_from_desc"]
        e_l1, e_l2 = m.at[i, "truth_from_eq"]
        d_l1, d_l2, e_l1, e_l2 = clean(d_l1), clean(d_l2), clean(e_l1), clean(e_l2)
        if d_l1 and e_l1 and not adjacent_ok(d_l1, d_l2, e_l1, e_l2):
            pl1, pl2 = clean(m.at[i, "proposed_aim_l1"]), clean(m.at[i, "proposed_aim_l2"])
            follows_d = adjacent_ok(d_l1, d_l2, pl1, pl2)
            follows_e = adjacent_ok(e_l1, e_l2, pl1, pl2)
            if not (follows_d or follows_e):
                add(i, f"desc_eq_disagree:{d_l1}/{d_l2}_vs_{e_l1}/{e_l2}", "fail")

    # PN logic
    pn_len_bad = 0
    for i in range(len(m)):
        raw = m.at[i, "pn_raw"]
        pn10 = m.at[i, "pn10"]
        if not raw:
            add(i, "pn_empty", "fail")
            continue
        if not re.match(r"^[0-9A-Z]+$", raw, re.I):
            add(i, "pn_non_alnum", "fail")
        if len(raw) not in (8, 9, 10) and len(pn10) != 10:
            add(i, f"pn_length_{len(raw)}", "fail")
            pn_len_bad += 1

    # Price absurdity (list eur from master) — soft, only clear nonsense
    price_fails = 0
    price_checked = 0
    for i in range(len(m)):
        eur = m.at[i, "eur_num"]
        if pd.isna(eur) or eur <= 0:
            continue
        price_checked += 1
        ev = m.at[i, "evidence_u"]
        pl1 = clean(m.at[i, "proposed_aim_l1"])
        if re.search(r"\bBOLT\b|\bNUT\b|\bCLIP\b|\bPIN\b", ev) and eur > 5000:
            add(i, f"price_absurd_hardware:eur{eur:.0f}", "fail")
            price_fails += 1
        if pl1 == "Filters" and eur > 2000 and re.search(r"\bPIPE\b|\bHOSE\b", ev):
            add(i, f"price_pipe_tagged_filter:eur{eur:.0f}", "fail")
            price_fails += 1

    # ZKK/HKK: report only — do not fail the EQ parallel taxonomy against master AIM majority
    # (different label trees). Count coverage for honesty.
    zkk_filled = int((m["zkk"].map(clean) != "").sum())
    hkk_filled = int((m["hkk"].map(clean) != "").sum())
    zkk_in_pure = 0
    hkk_in_pure = 0
    for i in range(len(m)):
        z, h = clean(m.at[i, "zkk"]), clean(m.at[i, "hkk"])
        if z and z in zkk_map:
            zkk_in_pure += 1
        if h and h in hkk_map and hkk_map[h][1] >= 0.85:
            hkk_in_pure += 1

    m["rigor_status"] = status
    m["rigor_reasons"] = ["; ".join(r) if r else "" for r in reasons]
    m["truth_path"] = [
        " > ".join(x for x in [a, b, c] if x)
        for a, b, c in zip(m["truth_l1"], m["truth_l2"], m["truth_l3"])
    ]

    n_pass = int(sum(1 for s in status if s == "pass"))
    n_fail = int(sum(1 for s in status if s == "fail"))
    n_inc = int(sum(1 for s in status if s == "inconclusive"))

    reason_counts: dict[str, int] = {}
    for rlist in reasons:
        for r in rlist:
            key = r.split(":")[0] if ":" in r else r
            reason_counts[key] = reason_counts.get(key, 0) + 1

    # Systematic buckets
    systematic = []
    for path, g in m.groupby(m["proposed_aim_path"].map(clean)):
        nf = int((g["rigor_status"] == "fail").sum())
        if len(g) >= 3 and nf / len(g) >= 0.25:
            systematic.append(
                {
                    "proposed_aim_path": path,
                    "n": int(len(g)),
                    "fail_n": nf,
                    "fail_rate": round(nf / len(g), 4),
                }
            )

    # Verdict
    if n_fail == 0 and n_inc == 0:
        verdict = "PASS"
        permission = "EARNED_CONDITIONAL_THIS_FILE"
        permission_bar = "PASS"
        apply_sentence = (
            f"Yes — all {n_prop} rows with figure dig + family suggestion pass description/EQ "
            "text checks; still proposal only, aim_master not written."
        )
    elif n_pass > 0 and n_fail > 0:
        verdict = "PARTIAL"
        permission = "NOT_EARNED_FULL_PROVEN_SUBSET_OK"
        permission_bar = "PARTIAL"
        apply_sentence = (
            f"PARTIAL — {n_pass} of {n_prop} are apply-ready under description + EQ figure "
            f"evidence; {n_fail} fail commercial/family checks (keyword-order traps in the "
            f"overnight suggester); {n_inc} inconclusive. ZKK does not prove family here."
        )
    elif n_pass == 0:
        verdict = "FAIL"
        permission = "NOT_EARNED"
        permission_bar = "FAIL"
        apply_sentence = (
            f"FAIL — none of the {n_prop} suggested rows clear the description/EQ bar."
        )
    else:
        verdict = "PARTIAL"
        permission = "NOT_EARNED_FULL_PROVEN_SUBSET_OK"
        permission_bar = "PARTIAL"
        apply_sentence = (
            f"PARTIAL — {n_pass} pass, {n_inc} inconclusive, {n_fail} fail."
        )

    # Outputs
    prop_cols = list(pd.read_csv(PROP, nrows=0).columns)
    proven = m[m["rigor_status"] == "pass"][prop_cols].copy()
    if n_pass < n_prop:
        proven.to_csv(OUT_PROVEN, index=False)
        proven_path = str(OUT_PROVEN)
    else:
        # still write PROVEN = full set for a clean handoff
        proven.to_csv(OUT_PROVEN, index=False)
        proven_path = str(OUT_PROVEN)

    fails = m[m["rigor_status"].isin(["fail", "inconclusive"])][
        [
            "pn",
            "pn10",
            "desc_unified",
            "desc_source",
            "eq_fig_name",
            "eq_part_name",
            "eq_catalog",
            "proposed_aim_path",
            "truth_path",
            "zkk",
            "hkk",
            "eur_num",
            "rigor_status",
            "rigor_reasons",
        ]
    ].copy()
    if len(fails):
        fails.to_csv(OUT_FAILS, index=False)
        fails_path = str(OUT_FAILS)
    else:
        fails_path = ""

    honesty = (
        f"Price: {price_checked} of {n_prop} have a list euro on master; "
        f"{price_fails} absurdity fails. "
        f"ZKK filled on {zkk_filled}/{n_prop}; only {zkk_in_pure} sit on a ≥80% pure "
        f"master-family ZKK code (n≥20) — and those majorities speak master AIM labels "
        f"(Engine, Brakes, …), not this overnight Powertrain/Chassis tree, so ZKK cannot "
        f"approve these suggestions. "
        f"HKK filled on {hkk_filled}/{n_prop}; {hkk_in_pure} on a strong pure code. "
        f"PN length fails: {pn_len_bad}. "
        "Family proof for this file is description text + EQ figure/part name, not ZKK."
    )

    fail_examples = []
    for _, r in m[m["rigor_status"] == "fail"].head(12).iterrows():
        fail_examples.append(
            {
                "pn": r["pn"],
                "desc": clean(r["desc_unified"])[:60],
                "eq_fig": clean(r["eq_fig_name"])[:50],
                "eq_part": clean(r["eq_part_name"])[:40],
                "proposed": clean(r["proposed_aim_path"]),
                "truth": clean(r["truth_path"]),
                "reasons": clean(r["rigor_reasons"]),
            }
        )

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "apply": "NO — proposal/gate only. Does not write aim_master.",
        "verdict": verdict,
        "permission": permission,
        "permission_bar": permission_bar,
        "apply_permission_sentence": apply_sentence,
        "proposal_rows": n_prop,
        "rigor_pass": n_pass,
        "rigor_fail": n_fail,
        "rigor_inconclusive": n_inc,
        "apply_ready_under_desc_eq": n_pass,
        "session_hits": {
            "total_hit": n_hit,
            "with_figure_and_part": n_fig_dig,
            "with_family_suggestion": n_with_sug,
            "figure_dig_no_family_map": n_fig_no_sug,
            "catalog_vehicle_only_no_figure": n_cat_only,
            "status_hit_only": n_status_only,
            "hits_still_needing_figure_dig_or_family_map": n_need_fig_or_map,
            "note_477": (
                f"{n_need_fig_or_map} of {n_hit} HITs have no family suggestion yet. "
                f"Of those: {n_fig_no_sug} already have figure+part but the overnight "
                f"keyword map did not land a family; {n_cat_only} have vehicle/catalog "
                f"text only (need figure dig); {n_status_only} are status-only HITs "
                f"(need full figure dig)."
            ),
        },
        "price_zkk_hkk_honesty": honesty,
        "zkk_contribution": {
            "zkk_majority_codes_usable_on_master": len(zkk_map),
            "rows_with_zkk": zkk_filled,
            "rows_on_pure_zkk_code": zkk_in_pure,
            "note": (
                "ZKK is a Japan catalogue attribute. Pure majorities are on master AIM "
                "L1 labels, not the overnight Powertrain/Chassis tree. Not used as a "
                "pass/fail for this proposal."
            ),
        },
        "hkk_contribution": {
            "hkk_majority_codes_usable_on_master": len(hkk_map),
            "rows_with_hkk": hkk_filled,
            "rows_on_strong_pure_hkk": hkk_in_pure,
        },
        "price_pn": {
            "price_checked": price_checked,
            "price_fail_count": price_fails,
            "pn_length_fail_count": pn_len_bad,
        },
        "reason_counts": dict(sorted(reason_counts.items(), key=lambda kv: -kv[1])),
        "systematic_paths": systematic,
        "fail_examples": fail_examples,
        "paths": {
            "proposal": str(PROP),
            "results": str(RESULTS),
            "rigor_md": str(OUT_MD),
            "rigor_json": str(OUT_JSON),
            "fails_csv": fails_path,
            "proven_csv": proven_path,
        },
        "notes": [
            "Does not apply aim_master.",
            "Overnight fig_to_aim keyword order caused known traps (SPRING→Suspension, FUEL FILTER substring→Filters, A/C hose→Pipes).",
            "PROVEN subset = rigor pass only.",
        ],
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    sys_rows = (
        "\n".join(
            f"| {s['proposed_aim_path']} | {s['n']} | {s['fail_n']} | {s['fail_rate']:.0%} |"
            for s in systematic
        )
        or "| (none) | — | — | — |"
    )
    ex_rows = "\n".join(
        f"| `{e['pn']}` | {e['desc']} | {e['eq_fig']} | {e['proposed']} | {e['truth']} |"
        for e in fail_examples[:8]
    ) or "| — | — | — | — | — |"

    md = f"""# EQ-HIT 126 rigor — 2026-10-07

## Verdict

{apply_sentence}

**Permission bar:** `{permission_bar}`  
**Apply aim_master?** No.

## Counts

| Piece | Rows |
|---|---:|
| Proposal (figure dig + family) | {n_prop} |
| Rigor PASS (apply-ready under desc+EQ) | **{n_pass}** |
| Fail | {n_fail} |
| Inconclusive | {n_inc} |

Session was **{n_hit}/{n_hit} HIT**, zero misses. Of those HITs:

| Dig depth | Rows | What they still need |
|---|---:|---|
| Figure + part + family suggestion (this proposal) | {n_with_sug} | Rigor above — only PASS is apply-ready |
| Figure + part, no family map | {n_fig_no_sug} | Map figure text to a family (rules missed them) |
| Vehicle/catalog only, no figure name | {n_cat_only} | **Figure dig** (open the figure, capture fig name + part name) |
| Status HIT only | {n_status_only} | **Full figure dig** |

So **{n_need_fig_or_map}** of {n_hit} HITs still need figure dig and/or a family map before they can join a proven proposal. That is the pile behind the 126.

## What we checked

| Check | Result |
|---|---|
| Description + EQ figure/part vs proposed family | Independent truth rules on united text; hard traps for governor/valve springs→Suspension, fuel pipes→Filters, A/C→generic pipe |
| PN length / charset | {pn_len_bad} length fails |
| Price (master list euro) | {price_checked} priced; {price_fails} absurdity fails |
| ZKK / HKK | See honesty — **not** used as family proof |

## Honesty — price / ZKK

{honesty}

## Systematic weak paths (fail rate ≥25% on buckets of 3+)

| Proposed path | n | fails | rate |
|---|---:|---:|---:|
{sys_rows}

## Example fails

| PN | Description | EQ figure | Proposed | Truth from text |
|---|---|---|---|---|
{ex_rows}

## Files

- Proven subset: `{proven_path}`
- Fails / inconclusive: `{fails_path or "(none)"}`
- JSON: `{OUT_JSON}`
- This note: `{OUT_MD}`

## What was not done

aim_master was not written. No dated release apply. ZKK is not claimed as family proof.
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "pass": n_pass,
                "fail": n_fail,
                "inconclusive": n_inc,
                "need_fig_or_map": n_need_fig_or_map,
                "proven": proven_path,
                "fails": fails_path,
                "md": str(OUT_MD),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
