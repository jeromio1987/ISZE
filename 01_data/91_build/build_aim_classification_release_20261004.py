#!/usr/bin/env python3
"""Cut classification release 2026-10-04 (status PENDING_APPROVAL; Jerome approves).

Jerome's decisions of 4 Oct 2026, applied to the approved release 2026-10-02-chassis-frame
(sha256 9bb86a9b...). Nothing else changes.

Release id: 2026-10-04 is not taken in RELEASES.json, so the date alone is the id (the
register's rule: date; a hyphen suffix only if the date is already taken). No version label.

  1  Missing billed parts: the 24 HIGH-confidence parts of
     next_release_proposal_missing_billed_2026-10-02.csv (EUR 24,789) are added as new rows
     with that file's catalogue-tree and AIM labels. Medium (15) and Low (17) are not added;
     unbilled 8974923852 is not added.
  2  Engine gasket sets (GASKET SET; ENG ..., incl. ENG HD / HEAD OVERHAUL): AIM family
     Transmission > Bearings & Seals > Gasket  ->  Engine > Gasket & Sealing > Gasket.
     GASKET SET; TRANS OVERHAUL (and CARB) stay. Catalogue tree unchanged.
  3  EVRV valves (VALVE; EVRV): AIM family -> Intake Exhaust Emission > EGR > EGR Component.
     Catalogue tree unchanged.
  4  Antennas (ANTENNA, ANTENNA ASM, ROD; ANTENNA, plus ANTENNA; GPS and ANTENNA; KEYLESS
     ENTRY): AIM family Instrument Cluster / Unknown / blank -> Electrical > Audio > Radio.
     A part that already carries another label (Radio, Switch) keeps it.
  5  Cameras, CATALOGUE TREE ONLY: parts with CAMERA in the description that sit on
     Engine parts > Other engine -> Repair parts > Electrical sensors > Other electrical.
     AIM family untouched. HARNESS; CAMERA (already Harness / cable) is not moved; the AEBS
     camera-aiming TARGET parts are not moved (a target board is not a camera).
  6  DEF dosing injectors: INJECTOR ASM; DEF DCM (3), CONNECTOR KIT; COOLANT,INJECTOR ASM DEF
     and GASKET; INJECTOR ASM,DEF DCM -> NEW AIM label Intake Exhaust Emission > DEF System >
     DEF Injector (Jerome approved this one new label). Catalogue tree stays Injectors > Injector.
  7  Everything else stays byte-for-byte as in the base release.

A part belongs to a group by its description: the release's own description_norm, and where
the release has none (137,702 rows), the description in jp_codes_cache_20260920.csv (the
method the 2026-10-02 body filing used). Within a group a part changes only if it currently
carries the label Jerome named as wrong (gasket: Transmission Gasket; antennas: Instrument
Cluster / Unknown / blank; cameras: Other engine; EVRV: all, "any other EVRV valve"). Parts of
the same descriptions with no AIM family at all are not touched (counted in the meta).

    python build_aim_classification_release_20261004.py   # refuses to overwrite
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
REGISTER = REL / "RELEASES.json"

RELEASE_ID = "2026-10-04"
BASE_ID = "2026-10-02-chassis-frame"
OUT = REL / f"aim_pn_classification_release_{RELEASE_ID}.csv"
OUT_META = OUT.with_suffix(".meta.json")
OUT_LOG = REL / f"aim_pn_classification_release_{RELEASE_ID}.changes.csv"

BASE = REL / f"aim_pn_classification_release_{BASE_ID}.csv"
PROPOSAL = REL / "next_release_proposal_missing_billed_2026-10-02.csv"
PR00_REF = REL / "pr00_classification_reference_20260920.csv"
PR00_LIVE = DER / "pr00_classification.csv"
MASTER = DER / "aim_master_v2.csv"
JP = DER / "jp_codes_cache_20260920.csv"
SALES = DER / "sales_fact.parquet"

EXPECT_SHA = {
    BASE: "9bb86a9b4d89c5954cd6dd15fdc977db44e66cddaa15e3e70bd0285e3bf3e65b",
    PROPOSAL: "c451c1318d2d415cfc2cf5c8c98c2cb1e4284fcbdf6dd07aaee909c6230e342e",
    PR00_REF: "98e64b5bdaef73819cf954ce96241f1a9b49d8fbd998d02700ae8494028bea34",
    MASTER: "8add555669baf1f75b3bb2d203d58960fff7596b26ec5d8645d7ffee45604acf",
    JP: "2277fa0363861decdcffeb57913db1e4b1903c1e96d713bd420938771630fad5",
}
TAG = "20261004"
SRC_ADDED = f"missing_billed_{TAG}"
SRC_FIX = f"label_fix_{TAG}"
L12M_FROM, L12M_TO = "2025-09-01", "2026-08-31"   # euro window of the approval summaries
COL_FROM, COL_TO = "2025-01-01", "2026-06-30"     # the release column l12m_billed_eur's own window

CAT_COLS = ("catalog_l1", "catalog_l2", "catalog_l3")
AIM_COLS = ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed")

AIM_TRANS_GASKET = ("Transmission", "Bearings & Seals", "Gasket")
AIM_ENG_GASKET = ("Engine", "Gasket & Sealing", "Gasket")
AIM_STEER_VALVE = ("Steering", "Control & Sensors", "Valve")
AIM_EGR = ("Intake Exhaust Emission", "EGR", "EGR Component")
AIM_IC = ("Electrical", "Instruments", "Instrument Cluster")
AIM_RADIO = ("Electrical", "Audio", "Radio")
AIM_UNKNOWN = ("Unknown", "Unknown", "Unknown")
AIM_BLANK = ("", "", "")
AIM_FUEL_INJ = ("Fuel System", "Fuel Control", "Injector")
AIM_DEF_INJ = ("Intake Exhaust Emission", "DEF System", "DEF Injector")   # the ONE new label
CAT_OTHER_ENGINE = ("Repair parts", "Engine parts", "Other engine")
CAT_OTHER_ELEC = ("Repair parts", "Electrical sensors", "Other electrical")
CAT_INJECTOR = ("High value repair", "Injectors", "Injector")

EXACT_ANTENNA = {"ANTENNA", "ANTENNA ASM", "ROD; ANTENNA"}
GPS_ANTENNA = {"ANTENNA; GPS"}
KEYLESS_RE = re.compile(r"^ANTENNA; KEYLES")      # JP file text is cut at 15 characters
GASKET_ENG_RE = re.compile(r"^GASKET SET;\s*ENG")  # also the no-space spelling GASKET SET;ENG
DEF_INJ_DESCS = {"INJECTOR ASM; DEF DCM": 3,
                 "CONNECTOR KIT; COOLANT,INJECTOR ASM DEF": 1,
                 "GASKET; INJECTOR ASM,DEF DCM": 1}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)


def pad(k: str) -> str:
    k = (k or "").strip()
    return k.zfill(10) if k.isdigit() else k


def reg_text(reg: dict) -> bytes:
    """RELEASES.json as it sits on disk: indent 2, CRLF, trailing newline."""
    return (json.dumps(reg, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8")


def add_source(cur: str, tag: str) -> str:
    return f"{cur}|{tag}" if cur else tag


def main() -> int:
    for p in (OUT, OUT_META, OUT_LOG):
        if p.exists():
            print(f"REFUSED: {p.name} already exists; a release file is never overwritten.")
            return 2
    for p, h in EXPECT_SHA.items():
        got = sha(p)
        if got != h:
            print(f"REFUSED: {p.name} sha256 {got[:12]} != expected {h[:12]} (input moved)")
            return 2
    reg_before = REGISTER.read_bytes()
    reg = json.loads(reg_before.decode("utf-8"))
    assert reg_text(reg) == reg_before, "register re-serialisation does not round-trip"
    assert all(c["release_id"] != RELEASE_ID for c in reg["candidates"]), "release id taken"
    base_entry = next(c for c in reg["candidates"] if c["release_id"] == BASE_ID)
    assert base_entry["status"] == "APPROVED" and base_entry["sha256"] == EXPECT_SHA[BASE]

    base_bytes = BASE.read_bytes()
    base = pd.read_csv(io.BytesIO(base_bytes), dtype=str, keep_default_na=False, low_memory=False)
    cols = list(base.columns)
    assert base.to_csv(index=False, lineterminator="\r\n").encode("utf-8") == base_bytes, \
        "writer does not round-trip the approved release byte-for-byte"
    new = base.copy()
    pos = {pn: i for i, pn in enumerate(new["part_number"])}
    assert len(pos) == len(new)

    # ---- parts billed per part: euro window of the approval summaries, plus the column window
    sf = pd.read_parquet(SALES, columns=["billing_date", "part_number", "net_sales_value"])
    sf["pn"] = sf["part_number"].astype(str).map(pad)
    w12 = sf[(sf.billing_date >= L12M_FROM) & (sf.billing_date <= L12M_TO)]
    l12 = w12.groupby("pn")["net_sales_value"].sum()
    wcol = sf[(sf.billing_date >= COL_FROM) & (sf.billing_date <= COL_TO)]
    l_col = wcol.groupby("pn")["net_sales_value"].sum()
    total_l12 = float(w12["net_sales_value"].sum())
    del sf

    def eur(pn: str) -> float:
        return round(float(l12.get(pad(pn), 0.0)), 2)

    def eur_col(pn: str) -> float:
        return round(float(l_col.get(pad(pn), 0.0)), 2)

    ms = read(MASTER).drop_duplicates("part_number").set_index("part_number")
    jp = read(JP)
    jp["pn"] = jp["pn"].map(pad)
    jpi = jp.drop_duplicates("pn").set_index("pn")
    assert not jp["pn"].duplicated().any()

    # description used for grouping: the release's own, else the Japanese code file's
    jpd = new["part_number"].map(lambda k: jpi["jp_description"].get(pad(k), ""))
    rel_d = new["description_norm"]
    anyd = rel_d.where(rel_d != "", jpd)
    d_src = pd.Series(["release" if x else "japanese code file" for x in rel_d], index=new.index)
    base_cat = {i: tuple(new.loc[i, list(CAT_COLS)]) for i in new.index}
    base_aim = {i: tuple(new.loc[i, list(AIM_COLS)]) for i in new.index}

    # ---- label vocabulary of the base release
    base_cat_set = set(base_cat.values())
    base_aim_set = set(base_aim.values())
    for t in (AIM_ENG_GASKET, AIM_EGR, AIM_RADIO, AIM_TRANS_GASKET, AIM_STEER_VALVE, AIM_IC,
              AIM_FUEL_INJ):
        assert t in base_aim_set, ("AIM label not in the base release", t)
    for t in (CAT_OTHER_ENGINE, CAT_OTHER_ELEC, CAT_INJECTOR):
        assert t in base_cat_set, ("catalogue label not in the base release", t)
    assert AIM_DEF_INJ not in base_aim_set, "DEF Injector already exists: not a new label"
    def_l3 = sorted({t[2] for t in base_aim_set if t[:2] == AIM_DEF_INJ[:2]})
    assert def_l3 == ["DEF Pump", "DEF Sensor", "DEF Tank"], def_l3
    aim_l3_before = len({t[2] for t in base_aim_set if t[2]})
    aim_triples_before = len(base_aim_set)

    log: list[dict] = []

    def note(pn, col, before, after, group, reason, to_check="", dsrc=""):
        log.append({"part_number": pn, "column": col, "before": before, "after": after,
                    "change_group": group, "to_check": to_check,
                    "l12m_eur_sep25_aug26": eur(pn), "eur_jan25_jun26_release_column": eur_col(pn),
                    "description_source": dsrc, "reason": reason})

    def set_catalog(pn: str, tgt: tuple, group: str, reason: str, to_check: str = "",
                    dsrc: str = "") -> None:
        i = pos[pn]
        for c, v in zip(CAT_COLS, tgt):
            if new.at[i, c] != v:
                note(pn, c, new.at[i, c], v, group, reason, to_check, dsrc)
                new.at[i, c] = v
        # derived columns, same rules the release carries on every row
        resid = "1" if tgt[2] == "Review needed" else "0"
        node = "0" if tgt[2] == "Review needed" else "1"
        for c, v in (("catalog_residual", resid), ("catalog_node_present", node)):
            if new.at[i, c] != v:
                note(pn, c, new.at[i, c], v, group, "derived: Review needed <-> named leaf",
                     to_check, dsrc)
                new.at[i, c] = v
        if pn in ms.index:
            m = ms.loc[pn]
            chg = "0" if (m["cat_l1"], m["cat_l2"], m["cat_l3"]) == tgt else "1"
            if new.at[i, "catalog_changed_vs_master"] != chg:
                note(pn, "catalog_changed_vs_master", new.at[i, "catalog_changed_vs_master"], chg,
                     group, "recomputed: catalogue vs the master's cat_* copy", to_check, dsrc)
                new.at[i, "catalog_changed_vs_master"] = chg

    def set_aim(pn: str, tgt: tuple, group: str, reason: str, to_check: str = "",
                dsrc: str = "") -> None:
        i = pos[pn]
        changed = False
        for c, v in zip(AIM_COLS, tgt):
            if new.at[i, c] != v:
                note(pn, c, new.at[i, c], v, group, reason, to_check, dsrc)
                new.at[i, c] = v
                changed = True
        assert changed, ("set_aim called on a part that already has the label", pn)
        old = new.at[i, "aim_source"]
        new.at[i, "aim_source"] = add_source(old, SRC_FIX)
        note(pn, "aim_source", old, new.at[i, "aim_source"], group, "provenance tag", to_check, dsrc)

    review: dict = {}      # lists and counts for the approval summary (not release content)
    group_parts: dict[str, list[str]] = {}

    # ---------------------------------------------------------------- 2: engine gasket sets
    m_g = anyd.map(lambda s: bool(GASKET_ENG_RE.match(s)))
    rows_g = new.index[m_g]
    g_change, g_nolabel, g_other = [], [], []
    for i in rows_g:
        a = base_aim[i]
        (g_change if a == AIM_TRANS_GASKET else g_nolabel if a == AIM_BLANK else g_other).append(i)
    assert not g_other, ("engine gasket set with a label that is neither Transmission Gasket nor "
                         "blank", [new.at[i, "part_number"] for i in g_other][:5])
    for i in g_change:
        pn = new.at[i, "part_number"]
        set_aim(pn, AIM_ENG_GASKET, "D2_engine_gasket_sets",
                f"Jerome 2026-10-04: engine gasket set ({anyd[i]}) carried the transmission label "
                "Transmission > Bearings & Seals > Gasket", dsrc=d_src[i])
    group_parts["D2_engine_gasket_sets"] = [new.at[i, "part_number"] for i in g_change]
    review["gasket_sets"] = {
        "engine_sets_changed": len(g_change),
        "engine_sets_changed_by_description": anyd[g_change].value_counts().to_dict(),
        "engine_sets_changed_description_from_japanese_file": int((d_src[g_change] != "release").sum()),
        "engine_sets_no_aim_family_not_touched": len(g_nolabel),
        "engine_sets_no_aim_family_billed_eur_sep25_aug26": round(sum(eur(new.at[i, "part_number"]) for i in g_nolabel), 2),
        "engine_sets_no_aim_family_billed_parts": int(sum(eur(new.at[i, "part_number"]) > 0 for i in g_nolabel)),
    }
    # what stays: the other GASKET SET families on the transmission label
    other_gs = new.index[anyd.str.match(r"^GASKET SET") & ~m_g & (pd.Series(
        [base_aim[i] == AIM_TRANS_GASKET for i in new.index], index=new.index))]
    review["gasket_sets"]["other_gasket_sets_left_on_transmission_label"] = {
        k: int(v) for k, v in anyd[other_gs].value_counts().items()}

    # ---------------------------------------------------------------- 3: EVRV valves
    m_e = anyd.str.contains("EVRV")
    rows_e = new.index[m_e]
    assert set(anyd[rows_e]) == {"VALVE; EVRV"}, set(anyd[rows_e])
    e_by_before: dict[str, int] = {}
    for i in rows_e:
        pn = new.at[i, "part_number"]
        e_by_before[" > ".join(base_aim[i]) or "(blank)"] = e_by_before.get(" > ".join(base_aim[i]) or "(blank)", 0) + 1
        set_aim(pn, AIM_EGR, "D3_evrv_valves",
                "Jerome 2026-10-04: EVRV valve is an engine vacuum valve on the EGR figure; "
                "AIM family Intake Exhaust Emission > EGR > EGR Component (any EVRV valve in the "
                f"release; {'description from the release' if rel_d[i] else 'description from the Japanese code file'})",
                dsrc=d_src[i])
    group_parts["D3_evrv_valves"] = [new.at[i, "part_number"] for i in rows_e]
    review["evrv"] = {"parts": len(rows_e), "by_label_before": e_by_before,
                      "description_from_japanese_file": int((d_src[rows_e] != "release").sum())}

    # ---------------------------------------------------------------- 4: antennas
    def a_kind(s: str) -> str:
        if s in EXACT_ANTENNA:
            return "antenna"
        if s in GPS_ANTENNA:
            return "gps"
        if KEYLESS_RE.match(s):
            return "keyless"
        return ""

    kinds = anyd.map(a_kind)
    ant_changed, ant_kept, ant_already = [], [], []
    for i in new.index[kinds != ""]:
        a = base_aim[i]
        if a == AIM_RADIO:
            ant_already.append(i)
        elif a in (AIM_IC, AIM_UNKNOWN, AIM_BLANK):
            ant_changed.append(i)
        else:
            ant_kept.append(i)
    for i in ant_changed:
        pn = new.at[i, "part_number"]
        k = kinds[i]
        tc = "Jerome to look at (GPS antenna)" if k == "gps" else (
            "Jerome to look at (keyless entry antenna)" if k == "keyless" else "")
        set_aim(pn, AIM_RADIO, "D4_antennas",
                f"Jerome 2026-10-04: antenna ({anyd[i]}) to Electrical > Audio > Radio; was "
                f"{' > '.join(base_aim[i]) or 'blank'}", tc, d_src[i])
    group_parts["D4_antennas"] = [new.at[i, "part_number"] for i in ant_changed]

    def plist(idx):
        return [{"part_number": new.at[i, "part_number"], "description": anyd[i],
                 "description_source": d_src[i], "aim_before": " > ".join(base_aim[i]) or "(blank)",
                 "aim_after": " > ".join(AIM_RADIO) if i in set(ant_changed) else (
                     " > ".join(base_aim[i]) or "(blank)"),
                 "catalogue": " > ".join(base_cat[i]), "eur_sep25_aug26": eur(new.at[i, "part_number"])}
                for i in idx]

    review["antennas"] = {
        "parts_changed": len(ant_changed),
        "by_kind_changed": {k: int(sum(kinds[i] == k for i in ant_changed)) for k in ("antenna", "gps", "keyless")},
        "by_label_before": {(" > ".join(base_aim[i]) or "(blank)"): 0 for i in ant_changed},
        "changed_description_from_japanese_file": int(sum(d_src[i] != "release" for i in ant_changed)),
        "already_radio_unchanged": len(ant_already),
        "kept_existing_label": plist(ant_kept),
        "gps_and_keyless_changed": plist([i for i in ant_changed if kinds[i] in ("gps", "keyless")]),
    }
    for i in ant_changed:
        review["antennas"]["by_label_before"][" > ".join(base_aim[i]) or "(blank)"] += 1
    # antenna-related descriptions that are NOT in Jerome's list: not changed, listed
    m_rel = anyd.str.contains("ANTENNA") & (kinds == "")
    review["antennas"]["other_antenna_descriptions_not_changed"] = [
        {"description": k[0], "aim_family_today": k[1], "parts": int(v)}
        for k, v in pd.Series(list(zip(anyd[m_rel], [" > ".join(base_aim[i]) or "(blank)" for i in new.index[m_rel]]))).value_counts().items()]
    review["antennas"]["pole_antenna_rows"] = plist([i for i in new.index[m_rel] if anyd[i] == "POLE; ANTENNA"])

    # ---------------------------------------------------------------- 5: cameras (catalogue only)
    m_c = anyd.str.contains("CAMERA")
    on_oe = pd.Series([base_cat[i] == CAT_OTHER_ENGINE for i in new.index], index=new.index)
    is_target = anyd.str.startswith("TARGET")
    cam_move = new.index[m_c & on_oe & ~is_target]
    for i in cam_move:
        pn = new.at[i, "part_number"]
        set_catalog(pn, CAT_OTHER_ELEC, "D5_cameras_catalogue",
                    f"Jerome 2026-10-04: camera part ({anyd[i]}) filed under Engine parts > Other "
                    "engine; catalogue tree only, AIM family left as it is",
                    dsrc=d_src[i])
    group_parts["D5_cameras_catalogue"] = [new.at[i, "part_number"] for i in cam_move]
    cam_all = new.index[m_c]

    def clist(idx):
        return [{"part_number": new.at[i, "part_number"], "description": anyd[i],
                 "description_source": d_src[i], "catalogue_today": " > ".join(base_cat[i]),
                 "aim_today": " > ".join(base_aim[i]) or "(blank)",
                 "eur_sep25_aug26": eur(new.at[i, "part_number"])} for i in idx]

    review["cameras"] = {
        "parts_with_camera_in_release_description": int((m_c & (rel_d != "")).sum()),
        "eur_those_sep25_aug26": round(sum(eur(new.at[i, "part_number"]) for i in new.index[m_c & (rel_d != "")]), 2),
        "eur_those_jan25_jun26_release_column": round(sum(eur_col(new.at[i, "part_number"]) for i in new.index[m_c & (rel_d != "")]), 2),
        "parts_moved": len(cam_move),
        "moved_by_description": anyd[cam_move].value_counts().to_dict(),
        "moved_description_from_japanese_file": int((d_src[cam_move] != "release").sum()),
        "moved_from_release_description_only": int((d_src[cam_move] == "release").sum()),
        "aebs_target_parts_not_moved": clist([i for i in new.index[m_c & is_target]]),
        "camera_parts_not_on_other_engine_not_moved": clist([i for i in new.index[m_c & ~on_oe & ~is_target]]),
    }

    # ---------------------------------------------------------------- 6: DEF dosing injectors
    def_rows = []
    for dsc, n_exp in DEF_INJ_DESCS.items():
        r = new.index[new["description_norm"] == dsc]
        assert len(r) == n_exp, (dsc, len(r))
        def_rows += list(r)
    for i in def_rows:
        assert base_aim[i] == AIM_FUEL_INJ and base_cat[i] == CAT_INJECTOR, (new.at[i, "part_number"], base_aim[i], base_cat[i])
        set_aim(new.at[i, "part_number"], AIM_DEF_INJ, "D6_def_injectors",
                f"Jerome 2026-10-04: DEF dosing injector part ({rel_d[i]}) was filed as a fuel "
                "injector; NEW label Intake Exhaust Emission > DEF System > DEF Injector (approved "
                "by Jerome)", "new AIM label", d_src[i])
    group_parts["D6_def_injectors"] = [new.at[i, "part_number"] for i in def_rows]
    # same family, text cut in the Japanese code file, not changed: listed
    m_trunc = (rel_d == "") & jpd.str.startswith("INJECTOR ASM; D")
    review["def_injectors"] = {
        "parts_changed": len(def_rows),
        "injector_assemblies": [new.at[i, "part_number"] for i in def_rows if rel_d[i] == "INJECTOR ASM; DEF DCM"],
        "similar_parts_not_changed": [
            {"part_number": new.at[i, "part_number"], "japanese_file_description": jpd[i],
             "catalogue": " > ".join(base_cat[i]), "aim": " > ".join(base_aim[i]) or "(blank)",
             "eur_sep25_aug26": eur(new.at[i, "part_number"])} for i in new.index[m_trunc]],
    }

    # ---------------------------------------------------------------- 1: missing billed parts, High
    prop = read(PROPOSAL)
    high = prop[prop["confidence"] == "high"].copy()
    assert len(high) == 24, len(high)
    assert prop["confidence"].value_counts().to_dict() == {"high": 24, "low": 17, "medium": 15}
    assert high["part_number"].is_unique and all(len(p) == 10 and p.isdigit() for p in high["part_number"])
    assert not set(high["part_number"]) & set(pos), "a High part is already in the release"
    assert "8974923852" not in set(high["part_number"])
    added: list[pd.Series] = []
    added_view: list[dict] = []
    jp_fig_mismatch = []
    for _, p in high.iterrows():
        pn = p["part_number"]
        cat_t = (p["proposed_catalog_l1"], p["proposed_catalog_l2"], p["proposed_catalog_l3"])
        aim_t = (p["proposed_aim_l1"], p["proposed_aim_l2"], p["proposed_aim_l3"])
        assert cat_t in base_cat_set and aim_t in base_aim_set, (pn, cat_t, aim_t)
        j = jpi.loc[pn] if pn in jpi.index else None
        fk = p["fig_key"]
        if j is not None and j["jp_fig_key"]:
            jfk = f"{j['jp_fig_key'][:3]}-{j['jp_fig_key'][3:]}"
            if jfk != fk:
                jp_fig_mismatch.append((pn, fk, jfk))
        d = {c: "" for c in cols}
        d.update({
            "part_number": pn,
            "description_norm": p["description"],
            "catalog_l1": cat_t[0], "catalog_l2": cat_t[1], "catalog_l3": cat_t[2],
            "catalog_node_present": "1", "catalog_residual": "0",
            "workbook_axis_kind": "blank",
            "aim_source": SRC_ADDED,
            "aim_l1_fixed": aim_t[0], "aim_l2_fixed": aim_t[1], "aim_l3_fixed": aim_t[2],
            "jp_zkk": j["zkk"] if j is not None else "",
            "jp_zuk": j["zuk"] if j is not None else "",
            "jp_hkk": j["hkk"] if j is not None else "",
            "jp_class_new": j["class_new"] if j is not None else "",
            "l12m_billed_eur": str(round(float(l_col.get(pn, 0.0)), 2)),
            "axis_conflict": "0", "desc_ambiguous": "0", "catalog_changed_vs_master": "0",
            "line_kind": "part", "fig_key": fk,
        })
        if pn in ms.index:
            m = ms.loc[pn]
            d["catalog_changed_vs_master"] = "0" if (m["cat_l1"], m["cat_l2"], m["cat_l3"]) == cat_t else "1"
        added.append(pd.Series(d))
        src = ("sales_fact description + proposal file; JP code file codes" if j is not None
               else "sales_fact description + proposal file; no JP code on file")
        note(pn, "(row)", "(not in release)",
             f"added: catalogue {' > '.join(cat_t)}; AIM {' > '.join(aim_t)}",
             "D1_missing_billed_added",
             f"billed Sep 2025-Aug 2026 but missing from the release; High confidence in "
             f"{PROPOSAL.name} (fig key {fk}; {p['fig_key_source']}); {src}; l12m_billed_eur = the "
             f"column's own window Jan 2025-Jun 2026", dsrc="sales_fact")
        added_view.append({"part_number": pn, "description": p["description"], "fig_key": fk,
                           "catalogue": " > ".join(cat_t), "aim": " > ".join(aim_t),
                           "in_aim_master_spine": pn in ms.index,
                           "aim_master_label": (" > ".join(ms.loc[pn, ["aim_l1", "aim_l2", "aim_l3"]])
                                                if pn in ms.index else ""),
                           "eur_sep25_aug26": eur(pn)})
    group_parts["D1_missing_billed_added"] = [r["part_number"] for r in added]
    review["added"] = {
        "parts": len(added), "eur_sep25_aug26": round(sum(eur(r["part_number"]) for r in added), 2),
        "eur_proposal_file": round(float(high["l12m_billed_eur"].astype(float).sum()), 2),
        "in_aim_master_spine": sum(v["in_aim_master_spine"] for v in added_view),
        "aim_label_differs_from_master": [v for v in added_view if v["in_aim_master_spine"] and v["aim_master_label"] != v["aim"]],
        "jp_fig_key_mismatch": jp_fig_mismatch,
        "not_added": {"medium": int((prop["confidence"] == "medium").sum()),
                      "medium_eur": round(float(prop.loc[prop["confidence"] == "medium", "l12m_billed_eur"].astype(float).sum()), 2),
                      "low": int((prop["confidence"] == "low").sum()),
                      "low_eur": round(float(prop.loc[prop["confidence"] == "low", "l12m_billed_eur"].astype(float).sum()), 2),
                      "unbilled_8974923852": "not added (Jerome)"},
        "medium_def_injector_7552973320": {
            "in_proposal_as": prop.loc[prop["part_number"] == "7552973320", "confidence"].tolist(),
            "eur_sep25_aug26": eur("7552973320")},
        "parts": added_view,
    }
    assert abs(review["added"]["eur_sep25_aug26"] - 24789.31) < 0.02, review["added"]["eur_sep25_aug26"]
    assert not jp_fig_mismatch, jp_fig_mismatch

    # insert added rows in key order (sorted by part_number apart from the lubricant 9-digit twins)
    for row in sorted(added, key=lambda r: r["part_number"]):
        k = row["part_number"]
        after = new.index[(new["part_number"].str.len() == 10) & (new["part_number"] < k)].max()
        new = pd.concat([new.iloc[:after + 1], pd.DataFrame([row], columns=cols),
                         new.iloc[after + 1:]], ignore_index=True)
    new = new[cols]

    # ---- invariants
    assert new["part_number"].duplicated().sum() == 0
    assert len(new) == len(base) + 24
    l3n = new.loc[new["catalog_l3"] != "", "catalog_l3"].nunique()
    l2n = new.loc[new["catalog_l2"] != "", "catalog_l2"].nunique()
    assert (l2n, l3n) == (27, 177), (l2n, l3n)        # catalogue tree: no new group or type
    new_aim_set = set(map(tuple, new[list(AIM_COLS)].values))
    new_labels = new_aim_set - base_aim_set
    assert new_labels == {AIM_DEF_INJ}, new_labels      # the ONE new AIM label, nothing else
    aim_l3_after = len({t[2] for t in new_aim_set if t[2]})
    new_cat_set = set(map(tuple, new[list(CAT_COLS)].values))
    assert new_cat_set <= base_cat_set, new_cat_set - base_cat_set
    touched = {r["part_number"] for r in log}
    assert touched == {p for ps in group_parts.values() for p in ps}, "log and groups disagree"
    assert len(touched) == sum(len(v) for v in group_parts.values()), "a part is in two groups"
    b = base.set_index("part_number")
    n_ = new.set_index("part_number")
    untouched = [k for k in b.index if k not in touched]
    assert (b.loc[untouched] == n_.loc[untouched]).all().all()
    # changed columns are only the intended ones
    chg_cols = set()
    for k in touched & set(b.index):
        chg_cols |= {c for c in cols[1:] if b.at[k, c] != n_.at[k, c]}
    allowed = set(CAT_COLS) | set(AIM_COLS) | {"aim_source", "catalog_residual", "catalog_node_present",
                                                "catalog_changed_vs_master"}
    assert chg_cols <= allowed, chg_cols - allowed
    # AIM-only groups leave the catalogue tree alone; camera group leaves the AIM family alone
    for gname, cols_forbidden in (("D2_engine_gasket_sets", CAT_COLS), ("D3_evrv_valves", CAT_COLS),
                                  ("D4_antennas", CAT_COLS), ("D6_def_injectors", CAT_COLS),
                                  ("D5_cameras_catalogue", AIM_COLS + ("aim_source",))):
        for pn in group_parts[gname]:
            for c in cols_forbidden:
                assert b.at[pn, c] == n_.at[pn, c], (gname, pn, c)

    # ---- copy integrity vs the PINNED 20 Sep pr00 reference (gate method)
    def integrity(text: str, df: pd.DataFrame):
        pm = {}
        for r in csv.DictReader(io.StringIO(text)):
            k = pad(r.get("pn_norm") or "")
            if k:
                pm[k] = ((r.get("family") or "").strip(), (r.get("group") or "").strip(),
                         (r.get("level3_type") or "").strip())
        chk = ok = 0
        miss = []
        for pn, a, b_, c in zip(df["part_number"], df["catalog_l1"], df["catalog_l2"],
                                df["catalog_l3"]):
            k = pad(pn)
            if k in pm:
                chk += 1
                if pm[k] == (a.strip(), b_.strip(), c.strip()):
                    ok += 1
                else:
                    miss.append(pn)
        return {"rows_checked": chk, "rows_matching": ok,
                "match_pct": round(100 * ok / chk, 4) if chk else None}, miss

    ref_text = PR00_REF.read_text(encoding="utf-8")
    ref_int, ref_miss = integrity(ref_text, new)
    base_int, base_miss = integrity(ref_text, base)       # the approved release, same method
    live_int, live_miss = integrity(PR00_LIVE.read_text(encoding="utf-8"), new)
    base_meta = json.loads((BASE.with_suffix(".meta.json")).read_text(encoding="utf-8"))
    assert base_int == {k: base_meta["catalogue_verification_vs_pr00"][k]
                        for k in ("rows_checked", "rows_matching", "match_pct")}, base_int
    assert len(base_miss) == base_meta["catalogue_verification_vs_pr00"]["non_matching_parts"]
    logged = {r["part_number"] for r in log}
    # every non-matching row is one the base release already carried (its 44: the review
    # proposal, the 2 wrong-in-both fixes, 8980913940) or a change logged here
    unexplained = [p for p in ref_miss if p not in logged and p not in set(base_miss)]
    assert not unexplained, ("a reference mismatch that is not a logged change", unexplained[:10])
    newly_non_matching = sorted(set(ref_miss) - set(base_miss))
    assert set(newly_non_matching) <= logged
    n = len(new)

    if "--dry" in sys.argv:
        print("DRY RUN: all invariants passed, nothing written")
        print(f"rows {len(new)} (base {len(base)} + 24); parts touched {len(touched)}")
        print({k: len(v) for k, v in group_parts.items()})
        print({k: round(sum(eur(p) for p in v), 2) for k, v in group_parts.items()})
        print("new AIM labels:", sorted(new_labels), "| log rows:", len(log))
        print("copy integrity vs pinned 20 Sep pr00:", ref_int, "| base:", base_int,
              "| newly non-matching:", len(newly_non_matching))
        return 0

    # ---- write (CRLF, utf-8: the writer proven above to round-trip the approved file)
    OUT.write_bytes(new.to_csv(index=False, lineterminator="\r\n").encode("utf-8"))
    out_sha = sha(OUT)
    with OUT_LOG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["part_number", "column", "before", "after", "change_group",
                                          "to_check", "l12m_eur_sep25_aug26",
                                          "eur_jan25_jun26_release_column", "description_source",
                                          "reason"], lineterminator="\r\n")
        w.writeheader()
        w.writerows(log)
    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_aim_classification_release_20261004.py",
        "release_id": RELEASE_ID,
        "release_id_note": ("2026-10-04 is not taken in RELEASES.json, so the date alone is the id "
                            "(register rule: date; a hyphen suffix only if the date is taken). No "
                            "version label."),
        "status_at_build": "PENDING_APPROVAL (Jerome approves; this script never sets APPROVED)",
        "decisions_2026_10_04": {
            "1_missing_billed_parts": ("the 24 High-confidence parts of "
                                       f"{PROPOSAL.name} added, with that file's catalogue and AIM "
                                       "labels; Medium (15) and Low (17) not added; unbilled "
                                       "8974923852 not added"),
            "2_engine_gasket_sets": ("GASKET SET; ENG ... AIM family Transmission > Bearings & "
                                     "Seals > Gasket -> Engine > Gasket & Sealing > Gasket; "
                                     "GASKET SET; TRANS OVERHAUL not touched; catalogue unchanged"),
            "3_evrv_valves": ("VALVE; EVRV AIM family -> Intake Exhaust Emission > EGR > EGR "
                              "Component; catalogue unchanged"),
            "4_antennas": ("ANTENNA, ANTENNA ASM, ROD; ANTENNA, ANTENNA; GPS, ANTENNA; KEYLESS "
                           "ENTRY: Instrument Cluster / Unknown / blank -> Electrical > Audio > "
                           "Radio; a part with another label keeps it"),
            "5_cameras_catalogue_only": ("CAMERA parts on Engine parts > Other engine -> Repair "
                                         "parts > Electrical sensors > Other electrical; AIM "
                                         "family untouched; HARNESS; CAMERA and the AEBS aiming "
                                         "targets not moved"),
            "6_def_injectors": ("INJECTOR ASM; DEF DCM (3) + CONNECTOR KIT; COOLANT,INJECTOR ASM "
                                "DEF + GASKET; INJECTOR ASM,DEF DCM -> NEW AIM label Intake "
                                "Exhaust Emission > DEF System > DEF Injector (Jerome approved "
                                "this one new label); catalogue stays Injectors > Injector"),
            "7_not_changed": ("PCV element kits 8981065790 / 8980023462, radiator skid plates "
                              "8983941570 / 8983941544, rear modulator 8982154541, their "
                              "siblings, and every other row"),
        },
        "purpose": base_meta["purpose"],
        "rows": n,
        "sha256": out_sha,
        "base_release": {"release_id": BASE_ID, "file": BASE.name, "sha256": EXPECT_SHA[BASE],
                         "rows": len(base)},
        "sources": {
            "missing_billed_proposal": {"file": PROPOSAL.name, "sha256": EXPECT_SHA[PROPOSAL]},
            "jp_codes": {"file": JP.name, "sha256": EXPECT_SHA[JP]},
            "master": {"file": MASTER.name, "sha256": EXPECT_SHA[MASTER]},
            "sales_fact": {"file": SALES.name, "sha256": sha(SALES)},
            "euro": (f"sales_fact.parquet net_sales_value {L12M_FROM}..{L12M_TO}, all sold-to, "
                     f"10-digit padded key (same window as APPROVAL_SUMMARY_2026-10-02-candidate); "
                     f"total parts billed in that window EUR {total_l12:,.2f}. The release column "
                     f"l12m_billed_eur is a different window ({COL_FROM}..{COL_TO}); the figures "
                     "in Jerome's brief (camera EUR 125,967, DEF injectors EUR 267,132, EVRV 44k) "
                     "are that column."),
            "description_rule": ("a part's description = release description_norm, else the "
                                 "description in jp_codes_cache_20260920.csv (137,702 release rows "
                                 "have no release description); a part changes only if it carries "
                                 "the label Jerome named as wrong"),
        },
        "changes_vs_base": {
            "rows_added": group_parts["D1_missing_billed_added"],
            "parts_touched": len(touched),
            "parts_by_group": {k: len(v) for k, v in group_parts.items()},
            "eur_sep25_aug26_by_group": {k: round(sum(eur(p) for p in v), 2) for k, v in group_parts.items()},
            "eur_sep25_aug26_total": round(sum(eur(p) for p in touched), 2),
            "change_log": OUT_LOG.name,
            "change_log_rows": len(log),
            "review": review,
        },
        "aim_label_vocabulary": {
            "new_aim_labels": [" > ".join(t) for t in sorted(new_labels)],
            "aim_triples_before": aim_triples_before, "aim_triples_after": len(new_aim_set),
            "aim_l3_values_before": aim_l3_before, "aim_l3_values_after": aim_l3_after,
            "def_system_leaves_before": def_l3,
            "note": ("the verify gate has no AIM-label check (it checks the catalogue tree only: "
                     "27 groups, 177 types, unchanged); this builder asserts that the only AIM "
                     "triple not in the base release is the approved DEF Injector"),
        },
        "catalogue_verification_vs_pr00": {
            **ref_int,
            "reference_file": PR00_REF.name,
            "reference_sha256": EXPECT_SHA[PR00_REF],
            "reference_source": base_meta["catalogue_verification_vs_pr00"]["reference_source"],
            "reference_reason": base_meta["catalogue_verification_vs_pr00"]["reference_reason"],
            "non_matching_parts": len(ref_miss),
            "note": ("COPY-INTEGRITY ONLY, measured on THIS file: catalogue columns vs the pinned "
                     "20 Sep pr00 reference on the zero-padded key (method of "
                     "build_aim_classification_v2.py). Every non-matching row is a deliberate "
                     "change listed in the change log (the camera parts and the 24 added rows "
                     "where pr00 has them), a change carried from the base release, or the "
                     "8980913940 air-filter fix. Does not prove correctness vs customs, figures "
                     "or part text."),
            "base_release_non_matching_parts": len(base_miss),
            "newly_non_matching_vs_base_release": len(newly_non_matching),
            "newly_non_matching_are_logged_changes": True,
            "vs_pr00_today_information_only": {
                **live_int, "pr00_file": str(PR00_LIVE), "pr00_sha256": sha(PR00_LIVE),
                "non_matching_parts": len(live_miss),
                "note": ("today's pr00 file, information only; not edited by this script")},
        },
        "counts": {
            "catalog_l2_count": int(l2n), "catalog_l3_count": int(l3n),
            "line_kind": {k: int(v) for k, v in new["line_kind"].value_counts().items()},
        },
        "consumer_contract": base_meta["consumer_contract"],
    }
    OUT_META.write_text(
        json.dumps(meta, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)),
        encoding="utf-8")

    # ---- register: append a PENDING_APPROVAL entry; existing entries untouched
    assert REGISTER.read_bytes() == reg_before, "RELEASES.json changed while building; rerun"
    before_entries = json.dumps(reg["candidates"], sort_keys=True)
    reg["candidates"].append({
        "release_id": RELEASE_ID,
        "path": OUT.name,
        "sha256": out_sha,
        "status": "PENDING_APPROVAL",
        "rows": n,
        "rows_note": "data rows, header excluded (same as 2026-10-02)",
        "base_release": BASE_ID,
        "source": (f"release {BASE_ID} ({BASE.name}, sha256 {EXPECT_SHA[BASE][:8]}...) + 24 "
                   "High-confidence missing billed parts + engine gasket sets, EVRV valves, "
                   "antennas and DEF injectors on AIM labels + camera parts on the catalogue tree"),
        "recommendation": ("APPROVAL_SUMMARY_2026-10-04.md; Jerome decisions 2026-10-04; "
                           "MISSING_BILLED_REVIEW.md"),
        "notes": (f"Cut 2026-10-04 by claude from the approved {BASE_ID}. Change log "
                  f"{OUT_LOG.name}. One new AIM label: Intake Exhaust Emission > DEF System > DEF "
                  "Injector (Jerome approved). Release id: 2026-10-04 not taken, date alone."),
    })
    assert json.dumps(reg["candidates"][:-1], sort_keys=True) == before_entries
    REGISTER.write_bytes(reg_text(reg))
    after = json.loads(REGISTER.read_bytes().decode("utf-8"))
    assert json.dumps(after["candidates"][:-1], sort_keys=True) == before_entries

    os.chmod(OUT, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

    print(f"wrote {OUT}  rows={n}  sha256={out_sha}")
    print(f"copy integrity vs pinned 20 Sep pr00 = {ref_int}  non-matching {len(ref_miss)}")
    print(f"parts touched {len(touched)}; by group {meta['changes_vs_base']['parts_by_group']}")
    print(f"EUR by group {meta['changes_vs_base']['eur_sep25_aug26_by_group']}")
    print(f"wrote {OUT_LOG.name}  {len(log)} change rows")
    print(f"new AIM label(s): {sorted(new_labels)}")
    print(f"register: + {RELEASE_ID} PENDING_APPROVAL; earlier entries unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
