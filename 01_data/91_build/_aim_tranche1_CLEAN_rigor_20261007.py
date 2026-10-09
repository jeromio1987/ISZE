"""Rigor gate on CLEAN tranche-1 catmap proposal — proposal/gate only.

Does NOT write aim_master or cut a dated release CSV.
Reads CLEAN proposal; joins aim_master + jp_codes_cache; flags per-row conflicts
on description, PN logic, price, ZKK/HKK (where usable), and teaching bugs.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
CLEAN = ISZE / "01_data/00_derived/_releases/next_release_proposal_full_class_tranche1_catmap_CLEAN_2026-10-07.csv"
MASTER = ISZE / "01_data/00_derived/aim_master_v2.csv"
JP = ISZE / "01_data/00_derived/jp_codes_cache_20260920.csv"
PR00 = ISZE / "01_data/00_derived/pr00_classification.csv"
PR00_REF = ISZE / "01_data/00_derived/_releases/pr00_classification_reference_20260920.csv"

OUT_JSON = ISZE / "01_data/91_build/_aim_tranche1_CLEAN_rigor_20261007.json"
OUT_FAILS = ISZE / "01_data/91_build/_aim_tranche1_CLEAN_rigor_fails_20261007.csv"
OUT_SAFE = ISZE / "01_data/91_build/_aim_tranche1_CLEAN_rigor_SAFE_20261007.csv"
OUT_MD = ISZE / "01_data/91_build/_aim_tranche1_CLEAN_rigor_20261007.md"

# Teaching bugs that must not appear in CLEAN (path-level hard holds from Shard A)
TEACHING_HOLDS = [
    ("Repair parts > Gaskets / seals > Gasket set", "Transmission", "engine_gasket_to_transmission"),
    ("Repair parts > Gaskets / seals > Cylinder head gasket", "Transmission", "cyl_head_gasket_to_transmission"),
    ("High value repair > Transmission parts > Transmission assembly", "Literature Marketing", "trans_asm_to_literature"),
    ("Competitive parts > Air system > Air valve", "Steering", "air_valve_to_steering"),
]

# Strong noun → expected AIM L1. First match wins. Order = most specific first.
# also_ok = adjacent families that are commercially acceptable, not fails.
NOUN_RULES: list[tuple[str, str, set[str]]] = [
    # Lighting before body/grille (GRILLE; HEADLAMP is Lighting)
    (r"HEAD.?LAMP|TAIL.?LAMP|HEADL|\bLAMP\b|\bBULB\b|\bLENS\b|\bFOG\b.*LAMP", "Lighting", {"Electrical", "Accident & Body"}),
    # Clutch before generic PISTON (PISTON; CLU BOO = clutch booster)
    (r"\bCLUTCH\b|\bCLU\b.?BOO|PRESSURE PLATE|CLUTCH.?DISC", "Clutch", {"Transmission"}),
    (r"\bBRAKE\b|CALIPER|\bDRUM\b.*BRAKE|BRAKE.*\bPAD\b|BRAKE.*\bSHOE\b|BRAKE.*\bDISC\b|\bABS\b", "Brakes", {"Wheels Hub", "Electrical"}),
    (r"\bFILTER\b.*OIL|OIL.?FILTER|ELEMENT.?OIL|ELEMENT;?\s*OIL", "Lubrication", {"Engine", "Maintenance Service"}),
    # Generic SEAL/GASKET: many are Engine, but seals on mirrors/brakes/body are fine elsewhere.
    # Hard conflict rule still catches ENG / CYL HD gasket → Transmission.
    (r"\bGASKET\b|\bSEAL\b|O-?RING|PACKING", "Engine", {
        "Transmission", "Cooling", "Fuel System", "Intake Exhaust Emission", "Lubrication",
        "Clutch", "Accident & Body", "Brakes", "Chassis Frame", "Cabin Interior",
    }),
    (r"\bTRANSMISSION\b|\bGEARBOX\b|\bTRANS\b(?!FER)|\bGEAR\b.*ASM", "Transmission", {"Clutch", "Driveline Axle", "Chassis Frame", "Accident & Body", "Electrical"}),
    (r"\bRADIATOR\b|\bTHERMOSTAT\b|WATER.?PUMP|COOLING.?FAN|\bCOOLANT\b", "Cooling", {"Engine"}),
    (r"\bINJECTOR\b|\bFUEL\b.*PUMP|FUEL.?FILTER|\bCARBURET|\bTHROTTLE\b", "Fuel System", {"Engine", "Electrical"}),
    (r"\bTURBO\b|\bEXHAUST\b|\bMUFFLER\b|\bEGR\b|\bCATALYST|\bINTAKE\b.*MANIFOLD", "Intake Exhaust Emission", {"Engine", "Fuel System", "Electrical"}),
    (r"\bPISTON\b|\bCYLINDER\b.*HEAD|HEAD.?ASM.*CYL|LINER.?SET|\bCRANKSHAFT\b|\bCAMSHAFT\b|ENGINE.?ASM|\bENGINE\b", "Engine", {
        "Cooling", "Lubrication", "Intake Exhaust Emission", "Fuel System", "Clutch",
        "Maintenance Service", "Chassis Frame", "Lighting", "Brakes", "Accident & Body", "Electrical",
    }),
    (r"\bHARNESS\b|\bRELAY\b|\bSENSOR\b|\bSWITCH\b|\bECU\b|CONTROL UNIT|\bFUSE\b|GENERATOR|ALTERNATOR|STARTER", "Electrical", {
        "Lighting", "Engine", "Fuel System", "Brakes", "Accident & Body", "Cabin Interior",
        "Intake Exhaust Emission", "Cooling",
    }),
    (r"\bSHOCK\b|ABSORBER|\bSPRING\b.*SUSP|\bSUSPENSION\b|\bSTABILIZER\b", "Suspension", {"Chassis Frame", "Wheels Hub"}),
    (r"\bSTEERING\b|\bPITMAN\b|POWER.?STEER|\bRACK\b.*STEER", "Steering", {"Chassis Frame"}),
    (r"\bHUB\b|\bWHEEL\b|\bTYRE\b|\bTIRE\b|\bAXLE\b.*SHAFT", "Wheels Hub", {
        "Brakes", "Driveline Axle", "Suspension", "Accident & Body", "Engine", "Chassis Frame", "Clutch",
    }),
    (r"\bBUMPER\b|\bFENDER\b|\bBONNET\b|\bHOOD\b|\bDOOR\b|\bMIRROR\b|\bGRILLE\b|\bCAB\b(?!LE)", "Accident & Body", {"Chassis Frame", "Cabin Interior", "Lighting", "Electrical"}),
    (r"\bPANEL\b", "Accident & Body", {"Chassis Frame", "Cabin Interior", "Wheels Hub"}),
    (r"\bMANUAL\b|\bHANDBOOK\b|\bCATALOG\b|\bLITERATURE\b|\bBOOK\b", "Literature Marketing", {"Engine"}),
    (r"\bSEAT\b|\bDASHBOARD\b|\bTRIM\b|\bCARPET\b|\bCONSOLE\b", "Cabin Interior", {"Accident & Body", "Brakes"}),
    (r"\bCHASSIS\b|\bFRAME\b|\bCROSSMEMBER\b", "Chassis Frame", {"Accident & Body", "Suspension", "Transmission"}),
]

# Hard conflicts: noun family vs propose that are commercially wrong even with adjacency
HARD_CONFLICTS: list[tuple[str, str, str]] = [
    # if desc matches pattern AND propose == bad → fail
    # Cylinder-head / ENG gasket language must not land on Transmission (same teaching as gasket-set hold)
    (r"GASKET;?\s*CYL|CYL.?HD|GASKET;?\s*HEAD|HD OVERHAUL|HEAD OVERHAUL|\bGASKET\b.*\bENG|\bENG\b.*\bGASKET", "Transmission", "engine_gasket_language_vs_transmission"),
    (r"\bTRANSMISSION\b|\bGEARBOX\b|TRANS.?ASM", "Literature Marketing", "transmission_hardware_vs_literature"),
    (r"\bAIR\b.*\bVALVE\b|VALVE;?\s*AIR", "Steering", "air_valve_vs_steering"),
    (r"ENGINE.?ASM|COMPLETE.?ENGINE|\bENGINE\b.*ASM", "Literature Marketing", "engine_asm_vs_literature"),
    # "PISTON; MANUAL" is a piston type, not literature — do not hard-fail Engine on MANUAL alone
    (r"\bHANDBOOK\b|\bCATALOG(?:UE)?\b|\bLITERATURE\b", "Engine", "literature_vs_engine"),
    (r"\bHANDBOOK\b|\bMANUAL\b|\bCATALOG(?:UE)?\b", "Transmission", "literature_vs_transmission"),
    (r"LAMP.?ASM|HEAD.?LAMP|TAIL.?LAMP", "Fluids Chemicals", "lamp_vs_fluids"),
    (r"\bCLUTCH\b", "Lighting", "clutch_vs_lighting"),
    (r"\bBRAKE\b", "Lighting", "brake_vs_lighting"),
]


def clean(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip()


def pad10(pn: str) -> str:
    pn = clean(pn)
    if pn.isdigit() and len(pn) < 10:
        return pn.zfill(10)
    return pn


def resolve_family(aim_l1: str, aim_l1_fixed: str) -> str:
    f = clean(aim_l1_fixed) or clean(aim_l1)
    if f.upper() in {"", "UNKNOWN", "UNCLASSIFIED", "UNKNOWN REVIEW"}:
        return ""
    return f


def main() -> None:
    prop = pd.read_csv(CLEAN, dtype=str, low_memory=False)
    n_rows = len(prop)
    prop["pn10"] = prop["part_number"].map(pad10)
    prop["pn_raw"] = prop["part_number"].map(clean)
    prop["pn_len"] = prop["pn_raw"].str.len()

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
            "jp_zuk",
            "jp_class_new",
            "jp_class_current",
            "eur",
            "l12m_billed_eur",
            "price_class_iml",
        ],
        low_memory=False,
    )
    am["pn10"] = am["part_number"].map(pad10)
    am = am.drop_duplicates("pn10", keep="first")

    jp = pd.read_csv(JP, dtype=str, low_memory=False)
    jp["pn10"] = jp["pn"].map(pad10)
    jp = jp.drop_duplicates("pn10", keep="first")

    pr00_path = PR00 if PR00.exists() else PR00_REF
    pr00 = pd.read_csv(pr00_path, dtype=str, low_memory=False)
    pr00_pn = "pn_norm" if "pn_norm" in pr00.columns else "part_number"
    pr00["pn10"] = pr00[pr00_pn].map(pad10)
    pr00 = pr00.drop_duplicates("pn10", keep="first")

    # Join
    m = prop.merge(
        am[
            [
                "pn10",
                "description",
                "aim_l1",
                "aim_l1_fixed",
                "jp_zkk",
                "jp_hkk",
                "jp_zuk",
                "jp_class_new",
                "jp_class_current",
                "eur",
                "l12m_billed_eur",
                "price_class_iml",
            ]
        ].rename(
            columns={
                "description": "master_desc",
                "jp_zkk": "master_zkk",
                "jp_hkk": "master_hkk",
                "jp_zuk": "master_zuk",
            }
        ),
        on="pn10",
        how="left",
    )
    m = m.merge(
        jp[["pn10", "jp_description", "zkk", "hkk", "zuk", "class_new", "class_current"]].rename(
            columns={"zkk": "jp_zkk", "hkk": "jp_hkk", "zuk": "jp_zuk"}
        ),
        on="pn10",
        how="left",
    )
    m = m.merge(
        pr00[["pn10", "family", "group", "level3_type"]].rename(
            columns={"family": "pr00_family", "group": "pr00_group", "level3_type": "pr00_l3"}
        ),
        on="pn10",
        how="left",
    )

    # Unified description: proposal → master → JP
    m["desc"] = [
        clean(a) or clean(b) or clean(c)
        for a, b, c in zip(m.get("description", ""), m["master_desc"], m["jp_description"])
    ]
    m["desc_u"] = m["desc"].str.upper()
    m["desc_source"] = [
        ("proposal" if clean(a) else "master" if clean(b) else "jp" if clean(c) else "none")
        for a, b, c in zip(m.get("description", ""), m["master_desc"], m["jp_description"])
    ]
    m["zkk"] = [
        clean(a) or clean(b) for a, b in zip(m["master_zkk"].fillna(""), m["jp_zkk"].fillna(""))
    ]
    m["hkk"] = [
        clean(a) or clean(b) for a, b in zip(m["master_hkk"].fillna(""), m["jp_hkk"].fillna(""))
    ]
    m["zuk"] = [
        clean(a) or clean(b) for a, b in zip(m["master_zuk"].fillna(""), m["jp_zuk"].fillna(""))
    ]
    m["eur_num"] = pd.to_numeric(m["eur"], errors="coerce")
    m["propose"] = m["propose_aim_l1"].map(clean)

    # --- Build known-family maps from master (for ZKK/HKK/desc-stem/PN-prefix) ---
    am_known = am.copy()
    am_known["fam"] = [
        resolve_family(a, b) for a, b in zip(am_known["aim_l1"], am_known["aim_l1_fixed"])
    ]
    am_known = am_known[am_known["fam"] != ""].copy()
    am_known = am_known.merge(
        jp[["pn10", "jp_description"]], on="pn10", how="left"
    )
    am_known["kdesc"] = [
        clean(a) or clean(b) for a, b in zip(am_known["description"], am_known["jp_description"])
    ]
    am_known["kdesc_u"] = am_known["kdesc"].str.upper()
    am_known["dstem"] = am_known["kdesc_u"].str[:24]
    am_known["p4"] = am_known["pn10"].str[:4]
    am_known["eur_num"] = pd.to_numeric(am_known["eur"], errors="coerce")

    def majority_map(df: pd.DataFrame, key: str, min_n: int, min_share: float) -> dict[str, tuple[str, float, int]]:
        out: dict[str, tuple[str, float, int]] = {}
        sub = df[df[key].fillna("").ne("")]
        for k, g in sub.groupby(key):
            n = len(g)
            if n < min_n:
                continue
            vc = g["fam"].value_counts()
            mode = vc.index[0]
            share = float(vc.iloc[0] / n)
            if share >= min_share:
                out[str(k)] = (str(mode), share, int(n))
        return out

    jz = jp.set_index("pn10")["zkk"].map(clean).to_dict()
    jh = jp.set_index("pn10")["hkk"].map(clean).to_dict()
    am_zmap = am.set_index("pn10")["jp_zkk"].map(clean).to_dict()
    am_hmap = am.set_index("pn10")["jp_hkk"].map(clean).to_dict()
    am_z = am_known.copy()
    am_z["_k"] = [clean(am_zmap.get(p, "")) or jz.get(p, "") for p in am_z["pn10"]]
    zkk_map = majority_map(am_z, "_k", 20, 0.80)
    am_h = am_known.copy()
    am_h["_k"] = [clean(am_hmap.get(p, "")) or jh.get(p, "") for p in am_h["pn10"]]
    hkk_map = majority_map(am_h, "_k", 20, 0.80)

    stem_map = majority_map(
        am_known[am_known["dstem"].str.len() >= 8], "dstem", 5, 0.90
    )
    p4_map = majority_map(am_known, "p4", 20, 0.80)

    fam_price = (
        am_known.dropna(subset=["eur_num"])
        .groupby("fam")["eur_num"]
        .agg(median="median", p95=lambda s: s.quantile(0.95), n="count")
        .to_dict("index")
    )

    m = m.reset_index(drop=True)
    reasons: list[list[str]] = [[] for _ in range(len(m))]
    status: list[str] = ["pass"] * len(m)  # pass | fail | inconclusive

    def add(i: int, reason: str, kind: str = "fail") -> None:
        reasons[i].append(reason)
        if kind == "fail":
            status[i] = "fail"
        elif kind == "inconclusive" and status[i] == "pass":
            status[i] = "inconclusive"

    # 5) Teaching bugs (path × propose)
    teaching_hits = {name: 0 for _, _, name in TEACHING_HOLDS}
    for i in range(len(m)):
        cat = clean(m.at[i, "cat_path"])
        prop_l1 = clean(m.at[i, "propose"])
        for path, bad_l1, name in TEACHING_HOLDS:
            if cat == path and prop_l1 == bad_l1:
                teaching_hits[name] += 1
                add(i, f"teaching_bug:{name}", "fail")

    # 1) Description noun rules + hard conflicts
    desc_scored = 0
    for i in range(len(m)):
        d = m.at[i, "desc_u"]
        prop_l1 = m.at[i, "propose"]
        if not d:
            continue
        # hard conflicts first
        hard_hit = False
        for pat, bad, name in HARD_CONFLICTS:
            if prop_l1 == bad and re.search(pat, d, re.I):
                add(i, f"desc_hard:{name}", "fail")
                hard_hit = True
                break
        if hard_hit:
            desc_scored += 1
            continue
        matched = False
        for pat, expected, also_ok in NOUN_RULES:
            if re.search(pat, d, re.I):
                matched = True
                desc_scored += 1
                if prop_l1 != expected and prop_l1 not in also_ok:
                    add(i, f"desc_noun:{expected}_vs_{prop_l1}", "fail")
                break
        # literature / handbook price language on assembly propose already covered

    # Description stem majority from known
    stem_checked = 0
    for i in range(len(m)):
        d = m.at[i, "desc_u"]
        if len(d) < 8:
            continue
        stem = d[:24]
        if stem not in stem_map:
            continue
        mode, share, n = stem_map[stem]
        stem_checked += 1
        prop_l1 = m.at[i, "propose"]
        if prop_l1 != mode:
            # allow Chassis Frame ↔ Accident & Body adjacency on body stems
            adj = {mode, prop_l1} <= {"Chassis Frame", "Accident & Body", "Cabin Interior"}
            if not adj:
                add(i, f"desc_stem_majority:{mode}_share{share:.2f}_n{n}", "fail")

    # 2) PN logic
    pn_len_bad = 0
    pn_prefix_out = 0
    for i in range(len(m)):
        raw = m.at[i, "pn_raw"]
        pn10 = m.at[i, "pn10"]
        if not raw:
            add(i, "pn_empty", "fail")
            continue
        if not raw.isdigit() and not re.match(r"^[0-9A-Z]+$", raw):
            add(i, "pn_non_alnum", "fail")
        if len(raw) not in (8, 9, 10) and len(pn10) != 10:
            add(i, f"pn_length_{len(raw)}", "fail")
            pn_len_bad += 1
        # leading-zero: raw shorter than pad is OK (preserved by pad); flag if master lost zeros
        p4 = pn10[:4]
        if p4 in p4_map:
            mode, share, n = p4_map[p4]
            prop_l1 = m.at[i, "propose"]
            if prop_l1 != mode and {mode, prop_l1} - {"Chassis Frame", "Accident & Body"}:
                # only flag strong prefixes
                if share >= 0.90 and n >= 25:
                    add(i, f"pn_prefix_outlier:{p4}->{mode}_vs_{prop_l1}", "fail")
                    pn_prefix_out += 1

    # 3) Price absurdity (list/eur from master)
    price_fails = 0
    for i in range(len(m)):
        eur = m.at[i, "eur_num"]
        d = m.at[i, "desc_u"]
        prop_l1 = m.at[i, "propose"]
        if pd.isna(eur) or eur <= 0:
            continue
        # handbook / literature text with high assembly price proposing Literature is OK;
        # assembly language + very low price proposing Engine Complete-like is soft
        if re.search(r"ENGINE.?ASM|COMPLETE.?ENGINE", d) and eur < 80 and prop_l1 == "Engine":
            add(i, f"price_low_for_engine_asm:eur{eur:.0f}", "fail")
            price_fails += 1
        if re.search(r"\bHANDBOOK\b|\bMANUAL\b|\bCATALOG\b|\bLITERATURE\b", d) and eur > 500 and prop_l1 not in (
            "Literature Marketing",
            "Maintenance Service",
        ):
            # expensive "manual" might be a mistagged hardware part — inconclusive not fail
            add(i, f"price_high_on_literature_text:eur{eur:.0f}", "inconclusive")
        # propose Literature with hardware assembly desc + mid/high price
        if prop_l1 == "Literature Marketing" and re.search(r"\bASM\b|ASSEMBLY|\bENGINE\b|\bTRANS", d) and eur >= 50:
            add(i, f"price_hardware_on_literature_propose:eur{eur:.0f}", "fail")
            price_fails += 1
        # extreme vs family p95 when known
        if prop_l1 in fam_price and fam_price[prop_l1]["n"] >= 50:
            p95 = fam_price[prop_l1]["p95"]
            med = fam_price[prop_l1]["median"]
            # only flag if description also contradicts (already handled) OR absurd high on Fluids
            if prop_l1 == "Fluids Chemicals" and eur > 5000:
                add(i, f"price_absurd_fluids:eur{eur:.0f}", "fail")
                price_fails += 1
            if prop_l1 == "Literature Marketing" and eur > max(2000, 5 * (p95 or 100)):
                add(i, f"price_absurd_literature:eur{eur:.0f}", "fail")
                price_fails += 1

    # 4) ZKK / HKK majority conflict
    zkk_checked = 0
    zkk_conflict = 0
    hkk_checked = 0
    hkk_conflict = 0
    for i in range(len(m)):
        prop_l1 = m.at[i, "propose"]
        z = m.at[i, "zkk"]
        h = m.at[i, "hkk"]
        if z and z in zkk_map:
            mode, share, n = zkk_map[z]
            zkk_checked += 1
            if prop_l1 != mode and {mode, prop_l1} - {"Chassis Frame", "Accident & Body"}:
                add(i, f"zkk_majority:{z}->{mode}_share{share:.2f}_n{n}", "fail")
                zkk_conflict += 1
        if h and h in hkk_map:
            mode, share, n = hkk_map[h]
            hkk_checked += 1
            # HKK 1110 is huge and impure in practice — only trust if map says so
            if prop_l1 != mode and share >= 0.85 and n >= 30:
                if {mode, prop_l1} <= {"Chassis Frame", "Accident & Body", "Cabin Interior"}:
                    continue
                add(i, f"hkk_majority:{h}->{mode}_share{share:.2f}_n{n}", "fail")
                hkk_conflict += 1

    # Rows with no description AND no usable ZKK/HKK majority → inconclusive (if still pass)
    no_desc = 0
    for i in range(len(m)):
        if not m.at[i, "desc"]:
            no_desc += 1
            z = m.at[i, "zkk"]
            h = m.at[i, "hkk"]
            has_code_signal = (z in zkk_map) or (h in hkk_map and hkk_map[h][1] >= 0.85)
            if not has_code_signal and status[i] == "pass":
                add(i, "no_description_no_strong_commodity_signal", "inconclusive")

    m["rigor_status"] = status
    m["rigor_reasons"] = ["; ".join(r) if r else "" for r in reasons]

    n_pass = int(sum(1 for s in status if s == "pass"))
    n_fail = int(sum(1 for s in status if s == "fail"))
    n_inc = int(sum(1 for s in status if s == "inconclusive"))

    # Reason tallies
    reason_counts: dict[str, int] = {}
    for rlist in reasons:
        for r in rlist:
            key = r.split(":")[0] if ":" in r else r
            reason_counts[key] = reason_counts.get(key, 0) + 1

    # Systematic family errors: any propose_l1 with fail rate > 15% on described rows
    systematic = []
    described = m[m["desc"] != ""]
    for fam, g in described.groupby("propose"):
        nf = int((g["rigor_status"] == "fail").sum())
        if len(g) >= 50 and nf / len(g) >= 0.15:
            systematic.append(
                {
                    "propose_aim_l1": fam,
                    "described_n": int(len(g)),
                    "fail_n": nf,
                    "fail_rate": round(nf / len(g), 4),
                }
            )

    # Path-level systematic
    path_sys = []
    for path, g in described.groupby("cat_path"):
        nf = int((g["rigor_status"] == "fail").sum())
        if len(g) >= 100 and nf / len(g) >= 0.10:
            path_sys.append(
                {
                    "cat_path": path,
                    "propose_aim_l1": clean(g["propose"].iloc[0]),
                    "described_n": int(len(g)),
                    "fail_n": nf,
                    "fail_rate": round(nf / len(g), 4),
                }
            )

    teaching_total = sum(teaching_hits.values())
    fail_rate_all = n_fail / n_rows if n_rows else 0
    fail_rate_described = (
        int((described["rigor_status"] == "fail").sum()) / len(described) if len(described) else 0
    )

    # Verdict rule
    if teaching_total > 0 or systematic or (fail_rate_described >= 0.05 and n_fail >= 200):
        verdict = "FAIL"
        permission = "NOT_EARNED"
        permission_sentence = (
            "No — we have not earned apply permission; the CLEAN file still has material "
            "per-part conflicts (or teaching bugs) under description / commodity checks."
        )
    elif n_fail > 0 and fail_rate_all < 0.02 and not systematic:
        verdict = "PARTIAL"
        permission = "NOT_EARNED_FULL_SAFE_SUBSET_OK"
        permission_sentence = (
            "Not yet for the full 38,213 — only a SAFE subset that passed per-part checks "
            "could be considered, and that still needs your OK before any apply."
        )
    elif n_fail == 0 and n_inc > 0 and (n_inc / n_rows) > 0.05:
        verdict = "PARTIAL"
        permission = "NOT_EARNED_FULL_SAFE_SUBSET_OK"
        permission_sentence = (
            "Not yet for the full CLEAN file — a large inconclusive tail has no description "
            "or strong ZKK/HKK signal; SAFE subset size is below."
        )
    elif n_fail == 0 and desc_scored >= 0.5 * n_rows:
        verdict = "PASS"
        permission = "EARNED_CONDITIONAL"
        permission_sentence = (
            "Yes — rigor on description (and commodity where it can speak) holds; "
            "conditional apply permission is earned for the SAFE/pass set."
        )
    else:
        verdict = "PARTIAL"
        permission = "NOT_EARNED_FULL_SAFE_SUBSET_OK"
        permission_sentence = (
            "Not yet for the full CLEAN file — rigor is only partial; use the SAFE subset "
            "and keep the fail/inconclusive rows out until eyes or better text."
        )

    # If ZKK unusable and many rows only catalogue-path: force not full PASS
    zkk_usable_codes = len(zkk_map)
    if verdict == "PASS" and zkk_usable_codes < 5 and no_desc > 5000:
        verdict = "PARTIAL"
        permission = "NOT_EARNED_FULL_SAFE_SUBSET_OK"
        permission_sentence = (
            "Not yet for the full 38,213 — description rigor covers most rows with JP text, "
            "but ZKK/HKK cannot define family at scale and a blank-description tail remains."
        )

    safe_df = m[m["rigor_status"] == "pass"].copy()
    # SAFE proposal columns = original CLEAN cols
    clean_cols = list(pd.read_csv(CLEAN, nrows=0).columns)
    safe_out = safe_df[[c for c in clean_cols if c in safe_df.columns]]
    safe_out.to_csv(OUT_SAFE, index=False)

    fails_df = m[m["rigor_status"].isin(["fail", "inconclusive"])][
        [
            "part_number",
            "pn10",
            "desc",
            "desc_source",
            "cat_path",
            "propose_aim_l1",
            "propose_aim_l2",
            "propose_aim_l3",
            "zkk",
            "hkk",
            "zuk",
            "eur_num",
            "pr00_family",
            "pr00_group",
            "confidence",
            "agree_share",
            "rigor_status",
            "rigor_reasons",
        ]
    ]
    fails_df.to_csv(OUT_FAILS, index=False)

    coverage = {
        "rows_checked": n_rows,
        "grain": "per_row",
        "master_join_hit": int(m["master_desc"].notna().sum()) if "master_desc" in m else n_rows,
        "jp_desc_hit": int((m["jp_description"].fillna("").map(clean) != "").sum()),
        "unified_desc_hit": int((m["desc"] != "").sum()),
        "unified_desc_blank": int(no_desc),
        "zkk_filled": int((m["zkk"] != "").sum()),
        "hkk_filled": int((m["hkk"] != "").sum()),
        "zkk_majority_codes_usable": zkk_usable_codes,
        "hkk_majority_codes_usable": len(hkk_map),
        "zkk_rows_checked_against_majority": zkk_checked,
        "hkk_rows_checked_against_majority": hkk_checked,
        "desc_noun_or_hard_scored": desc_scored,
        "desc_stem_checked": stem_checked,
        "pr00_join_hit": int((m["pr00_family"].fillna("").map(clean) != "").sum()),
        "note_zkk": (
            "ZKK is a Japan catalogue attribute, not an AIM family. On known master rows, "
            f"only {zkk_usable_codes} ZKK code(s) reach >=80% single-family purity at n>=20. "
            "Commodity/ZKK cannot define what each part is for most of this proposal; "
            "description text is the primary rigor signal."
        ),
    }

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "permission": permission,
        "permission_sentence_for_jerome": permission_sentence,
        "proposal_csv": str(CLEAN),
        "apply": "NO — rigor gate only; did not write aim_master or release CSV",
        "rows_checked": n_rows,
        "grain": "per_row (with path-level teaching-bug and systematic-rate rollups)",
        "pass": n_pass,
        "fail": n_fail,
        "inconclusive": n_inc,
        "fail_rate_all": round(fail_rate_all, 5),
        "fail_rate_described": round(fail_rate_described, 5),
        "safe_to_apply_count": n_pass,
        "safe_csv": str(OUT_SAFE),
        "fails_csv": str(OUT_FAILS),
        "by_reason": dict(sorted(reason_counts.items(), key=lambda x: -x[1])),
        "teaching_bugs": teaching_hits,
        "teaching_bugs_total": teaching_total,
        "systematic_family_errors": systematic,
        "systematic_path_errors": sorted(path_sys, key=lambda x: -x["fail_rate"]),
        "coverage": coverage,
        "price_fail_count": price_fails,
        "pn_length_fail_count": pn_len_bad,
        "pn_prefix_outlier_count": pn_prefix_out,
        "zkk_conflict_count": zkk_conflict,
        "hkk_conflict_count": hkk_conflict,
        "checks_performed": [
            "description_noun_fit (JP+master+proposal)",
            "description_stem_majority_vs_known",
            "description_hard_teaching_patterns",
            "pn_length_and_prefix_outlier",
            "price_absurdity_vs_desc_and_family",
            "zkk_hkk_majority_where_pure",
            "teaching_bug_path_leak_reverify",
            "blank_desc_without_commodity_signal -> inconclusive",
        ],
    }

    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Markdown for Jerome
    lines = [
        f"# CLEAN tranche-1 rigor check — {verdict}",
        "",
        permission_sentence,
        "",
        f"Checked **{n_rows:,}** rows in the CLEAN proposal, **per part number** "
        f"(not only per catalogue path). Pass **{n_pass:,}**, fail **{n_fail:,}**, "
        f"inconclusive **{n_inc:,}**. Estimated safe-to-apply count (pass only): **{n_pass:,}**.",
        "",
        "## Did we define what each part is?",
        "",
        f"Description text was joined from the proposal, aim_master, and the Japan code file "
        f"(`jp_codes_cache_20260920.csv`). **{coverage['unified_desc_hit']:,}** of {n_rows:,} rows "
        f"have usable part text; **{no_desc:,}** still have none.",
        "",
        f"ZKK / HKK: filled on **{coverage['zkk_filled']:,}** / **{coverage['hkk_filled']:,}** rows. "
        + coverage["note_zkk"],
        "",
        f"Usable majority maps: **{zkk_usable_codes}** ZKK codes, **{len(hkk_map)}** HKK codes "
        f"(≥80% one family, n≥20 on already-named master rows). That is too thin to call "
        f"commodity-code proof for the whole proposal.",
        "",
        "## Teaching bugs (must be zero in CLEAN)",
        "",
    ]
    for path, bad, name in TEACHING_HOLDS:
        lines.append(f"- `{name}` ({path} → {bad}): **{teaching_hits[name]}** rows")
    lines.extend(
        [
            "",
            "## Fail / inconclusive reasons (top)",
            "",
        ]
    )
    for k, v in sorted(reason_counts.items(), key=lambda x: -x[1])[:25]:
        lines.append(f"- {k}: {v:,}")
    if systematic:
        lines.extend(["", "## Systematic family error rates (described rows)", ""])
        for s in systematic:
            lines.append(
                f"- {s['propose_aim_l1']}: {s['fail_n']:,}/{s['described_n']:,} "
                f"({100*s['fail_rate']:.1f}%)"
            )
    if path_sys:
        lines.extend(["", "## Catalogue paths with high fail rate (described)", ""])
        for s in path_sys[:15]:
            lines.append(
                f"- {s['cat_path']} → {s['propose_aim_l1']}: "
                f"{s['fail_n']:,}/{s['described_n']:,} ({100*s['fail_rate']:.1f}%)"
            )
    lines.extend(
        [
            "",
            "## Apply permission",
            "",
            f"**Verdict: {verdict}.** Permission flag: `{permission}`.",
            "",
            "This run did **not** apply anything to aim_master and did **not** cut a release CSV.",
            "",
            "## Files",
            "",
            f"- Summary JSON: `{OUT_JSON}`",
            f"- Fail / inconclusive rows: `{OUT_FAILS}`",
            f"- SAFE proposal (CLEAN minus fail/inconclusive): `{OUT_SAFE}`",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "verdict": verdict,
        "permission": permission,
        "pass": n_pass,
        "fail": n_fail,
        "inconclusive": n_inc,
        "teaching": teaching_hits,
        "desc_hit": coverage["unified_desc_hit"],
        "zkk_usable": zkk_usable_codes,
        "top_reasons": dict(list(sorted(reason_counts.items(), key=lambda x: -x[1]))[:12]),
        "systematic": systematic[:5],
        "path_sys_n": len(path_sys),
        "out_json": str(OUT_JSON),
        "out_md": str(OUT_MD),
        "out_fails": str(OUT_FAILS),
        "out_safe": str(OUT_SAFE),
        "sentence": permission_sentence,
    }, indent=2))


if __name__ == "__main__":
    main()
