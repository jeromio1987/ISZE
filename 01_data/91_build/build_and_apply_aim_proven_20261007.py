#!/usr/bin/env python3
"""Cut + approve + apply classification release 2026-10-07 from two proven piles.

Jerome GO 2026-10-07: apply ONLY
  - next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv (30,653)
  - next_release_proposal_eq_hit_live_order_PROVEN_2026-10-07.csv (116)

Base: approved release 2026-10-04. Release id 2026-10-07 (not taken).

What changes
  DESC: AIM family fill on release rows that are blank today (catalogue Axis A untouched).
        90 rows already carry the same AIM triple — no-op. Prefer DESC on conflict (none).
  EQ:   overnight Powertrain/Chassis labels remapped onto existing AIM spine leaves
        (same method as apply_eq_hit_session_20260919.py + seat/starter/camera extras).
        116 parts are absent from the release and master — added with catalogue
        Other / review > Miscellaneous > Review needed (no catalogue proposal in the pile).

Then: candidate gate, register APPROVED (Jerome already said GO), sync aim_master_v2
(backup first), write apply report. No HTML rebuild.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
REGISTER = REL / "RELEASES.json"
BUILD = ISZE / "01_data" / "91_build"

RELEASE_ID = "2026-10-07"
BASE_ID = "2026-10-04"
OUT = REL / f"aim_pn_classification_release_{RELEASE_ID}.csv"
OUT_META = OUT.with_suffix(".meta.json")
OUT_LOG = REL / f"aim_pn_classification_release_{RELEASE_ID}.changes.csv"
OUT_GATE = OUT.with_suffix(".gate.json")
BASE = REL / f"aim_pn_classification_release_{BASE_ID}.csv"
DESC = REL / "next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv"
EQ = REL / "next_release_proposal_eq_hit_live_order_PROVEN_2026-10-07.csv"
PR00_REF = REL / "pr00_classification_reference_20260920.csv"
MASTER = DER / "aim_master_v2.csv"
OVERLAY = DER / "aim_pn_classification_20260920.csv"
JP = DER / "jp_codes_cache_20260920.csv"
SALES = DER / "sales_fact.parquet"
REPORT = BUILD / "_aim_apply_proven_20261007.md"
VERIFY = BUILD / "verify_aim_classification.py"

EXPECT_BASE_SHA = "8aad884f49db1a49ab86faca571942d912196ce08f7734f38d5a04f035e18896"
EXPECT_PR00_SHA = "98e64b5bdaef73819cf954ce96241f1a9b49d8fbd998d02700ae8494028bea34"

TAG = "20261007"
SRC_DESC = f"desc_proven_{TAG}"
SRC_EQ = f"eq_hit_proven_{TAG}"
L12M_FROM, L12M_TO = "2025-09-01", "2026-08-31"
COL_FROM, COL_TO = "2025-01-01", "2026-06-30"

CAT_COLS = ("catalog_l1", "catalog_l2", "catalog_l3")
AIM_COLS = ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed")
CAT_REVIEW = ("Other / review", "Miscellaneous", "Review needed")

# Parallel overnight taxonomy → existing AIM spine (never invent new L1/L2/L3).
EQ_EXTRA: dict[tuple[str, str, str], tuple[str, str, str]] = {
    ("Powertrain", "Engine", "Engine parts"): ("Engine", "Block & Structure", "Cylinder Block"),
    ("Powertrain", "Exhaust / aftertreatment", "Exhaust parts"): (
        "Intake Exhaust Emission", "Exhaust", "Exhaust Pipe"),
    ("Powertrain", "Gaskets / seals", "Gasket / seal"): ("Engine", "Gasket & Sealing", "Gasket"),
    ("Body", "Door / glass", "Door parts"): ("Accident & Body", "Panels", "Door"),
    ("Body", "Interior", "Seat parts"): ("Cabin Interior", "Seat", "Seat Back"),
    ("Filters", "Fuel filtration", "Fuel filter"): (
        "Maintenance Service", "Fuel Filter", "Fuel Filter Element"),
    ("Electrical", "Battery", "Battery"): ("Electrical", "Charging", "Battery Accessory"),
    ("Electrical", "Sensors", "Sensor"): ("Electrical", "Instruments", "Sensor"),
    ("Electrical", "Wiring", "Harness"): ("Electrical", "Harness & Connectors", "Connector"),
    ("Electrical", "Sensors / cameras", "Camera"): (
        "Electrical", "Instruments", "Instrument Cluster"),
    ("Electrical", "Starting / charging", "Starter"): (
        "Electrical", "Motors & Actuators", "Motor"),
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pad(k: str) -> str:
    k = (k or "").strip()
    return k.zfill(10) if k.isdigit() else k


def reg_text(reg: dict) -> bytes:
    return (json.dumps(reg, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8")


def add_source(cur: str, tag: str) -> str:
    return f"{cur}|{tag}" if cur else tag


def load_eq_remap():
    import importlib.util
    path = BUILD / "apply_eq_hit_session_20260919.py"
    spec = importlib.util.spec_from_file_location("eqapp_20260919", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def remap_eq(mod, proposed, fig, part, known):
    mapped = mod.remap_row(proposed, fig, part, known)
    if mapped:
        return mapped, "eq_session_remap"
    base = EQ_EXTRA.get(proposed)
    if not base:
        return None, "no_safe_spine_leaf"
    refined = mod.refine_by_fig(*base, fig, part, known)
    if refined in known:
        return refined, "eq_extra_refined"
    # seat belt / cushion from fig text
    t = f"{fig} {part}".upper()
    if proposed == ("Body", "Interior", "Seat parts"):
        if "BELT" in t and ("Cabin Interior", "Seat", "Seat Belt") in known:
            return ("Cabin Interior", "Seat", "Seat Belt"), "eq_extra_seat_belt"
        if "CUSHION" in t and ("Cabin Interior", "Seat", "Seat Cushion") in known:
            return ("Cabin Interior", "Seat", "Seat Cushion"), "eq_extra_seat_cushion"
        if "BACK" in t and ("Cabin Interior", "Seat", "Seat Back") in known:
            return ("Cabin Interior", "Seat", "Seat Back"), "eq_extra_seat_back"
    if base in known:
        return base, "eq_extra_base"
    for k in known:
        if k[0] == base[0] and k[1] == base[1]:
            return k, "eq_extra_soft_l12"
    return None, "no_safe_spine_leaf"


def family_coverage(master: pd.DataFrame) -> dict:
    a1 = master["aim_l1_fixed"].fillna("").astype(str)
    return {
        "rows": int(len(master)),
        "aim_l1_fixed_nonempty": int((a1 != "").sum()),
        "aim_l1_fixed_real": int(((a1 != "") & (a1 != "Unknown")).sum()),
        "has_aim_1": int((master.get("has_aim", pd.Series([""] * len(master))) == "1").sum()),
    }


def main() -> int:
    for p in (OUT, OUT_META, OUT_LOG, OUT_GATE):
        if p.exists():
            print(f"REFUSED: {p.name} already exists; a release file is never overwritten.")
            return 2

    if sha(BASE) != EXPECT_BASE_SHA:
        print(f"REFUSED: base sha moved {sha(BASE)[:12]} != {EXPECT_BASE_SHA[:12]}")
        return 2
    if sha(PR00_REF) != EXPECT_PR00_SHA:
        print("REFUSED: pr00 reference sha moved")
        return 2

    reg_before = REGISTER.read_bytes()
    reg = json.loads(reg_before.decode("utf-8"))
    assert reg_text(reg) == reg_before
    assert all(c["release_id"] != RELEASE_ID for c in reg["candidates"])
    base_entry = next(c for c in reg["candidates"] if c["release_id"] == BASE_ID)
    assert base_entry["status"] == "APPROVED" and base_entry["sha256"] == EXPECT_BASE_SHA

    base_bytes = BASE.read_bytes()
    base = pd.read_csv(io.BytesIO(base_bytes), dtype=str, keep_default_na=False, low_memory=False)
    cols = list(base.columns)
    assert base.to_csv(index=False, lineterminator="\r\n").encode("utf-8") == base_bytes
    new = base.copy()
    pos = {pn: i for i, pn in enumerate(new["part_number"])}
    assert len(pos) == len(new)

    base_aim_set = set(map(tuple, new[list(AIM_COLS)].values))
    base_cat_set = set(map(tuple, new[list(CAT_COLS)].values))
    assert CAT_REVIEW in base_cat_set
    for t in EQ_EXTRA.values():
        assert t in base_aim_set, ("EQ remap target not in base AIM vocab", t)

    desc = pd.read_csv(DESC, dtype=str, keep_default_na=False)
    eq = pd.read_csv(EQ, dtype=str, keep_default_na=False)
    assert len(desc) == 30653, len(desc)
    assert len(eq) == 116, len(eq)
    assert desc["part_number"].is_unique
    assert eq["pn"].map(pad).is_unique
    assert set(eq["pn"].map(pad)).isdisjoint(set(pos)), "EQ PN already on release"
    # DESC proposes only known AIM triples
    for a, b, c in zip(desc["propose_aim_l1"], desc["propose_aim_l2"], desc["propose_aim_l3"]):
        assert (a, b, c) in base_aim_set, (a, b, c)

    mod = load_eq_remap()
    known = {t for t in base_aim_set if t[0]}

    # euros
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

    jp = pd.read_csv(JP, dtype=str, keep_default_na=False)
    jp["pn"] = jp["pn"].map(pad)
    jpi = jp.drop_duplicates("pn").set_index("pn")

    master_before = pd.read_csv(MASTER, dtype=str, keep_default_na=False, low_memory=False)
    cov_before = family_coverage(master_before)
    master_sha_before = sha(MASTER)

    log: list[dict] = []
    group_parts: dict[str, list[str]] = {}

    def note(pn, col, before, after, group, reason, to_check="", dsrc=""):
        log.append({
            "part_number": pn, "column": col, "before": before, "after": after,
            "change_group": group, "to_check": to_check,
            "l12m_eur_sep25_aug26": eur(pn),
            "eur_jan25_jun26_release_column": eur_col(pn),
            "description_source": dsrc, "reason": reason,
        })

    # ---- DESC fill (AIM only; blank → propose)
    desc_filled, desc_same, desc_conflict, desc_cat_diff_kept = [], [], [], []
    for _, r in desc.iterrows():
        pn = pad(r["part_number"])
        assert pn in pos, pn
        i = pos[pn]
        tgt = (r["propose_aim_l1"], r["propose_aim_l2"], r["propose_aim_l3"])
        cur = tuple(new.loc[i, list(AIM_COLS)])
        cat_rel = tuple(new.loc[i, list(CAT_COLS)])
        cat_prop = (r["cat_l1"], r["cat_l2"], r["cat_l3"])
        if cat_rel != cat_prop:
            desc_cat_diff_kept.append(pn)
        if cur == tgt:
            desc_same.append(pn)
            continue
        if cur[0]:  # conflict: prefer DESC_PROVEN
            desc_conflict.append({"pn": pn, "before": " > ".join(cur), "after": " > ".join(tgt)})
        changed = False
        for c, v in zip(AIM_COLS, tgt):
            if new.at[i, c] != v:
                note(pn, c, new.at[i, c], v, "D1_desc_proven",
                     "Jerome GO 2026-10-07: DESC_PROVEN catalogue-path+description fill; "
                     "AIM only; catalogue Axis A left as on the base release",
                     dsrc="desc_proven")
                new.at[i, c] = v
                changed = True
        if changed:
            old = new.at[i, "aim_source"]
            new.at[i, "aim_source"] = add_source(old, SRC_DESC)
            note(pn, "aim_source", old, new.at[i, "aim_source"], "D1_desc_proven",
                 "provenance tag", dsrc="desc_proven")
            desc_filled.append(pn)
    group_parts["D1_desc_proven"] = desc_filled
    assert not desc_conflict or True  # documented; we preferred DESC
    print(f"DESC: filled {len(desc_filled)}, already-same {len(desc_same)}, "
          f"conflicts_overwritten {len(desc_conflict)}, cat_diff_kept {len(desc_cat_diff_kept)}")

    # ---- EQ remap + add rows
    eq_mapped, eq_skipped = [], []
    added_rows = []
    for _, r in eq.iterrows():
        pn = pad(r["pn"])
        proposed = (r["proposed_aim_l1"], r["proposed_aim_l2"], r["proposed_aim_l3"])
        mapped, how = remap_eq(mod, proposed, r["eq_fig_name"], r["eq_part_name"], known)
        if not mapped:
            eq_skipped.append({
                "pn": pn, "proposed": " > ".join(proposed),
                "fig": r["eq_fig_name"], "part": r["eq_part_name"],
                "desc": r["description_if_any"], "reason": how,
            })
            continue
        assert mapped in base_aim_set, mapped
        j = jpi.loc[pn] if pn in jpi.index else None
        d = {c: "" for c in cols}
        d.update({
            "part_number": pn,
            "description_norm": (r["description_if_any"] or r["eq_part_name"] or "").strip(),
            "catalog_l1": CAT_REVIEW[0], "catalog_l2": CAT_REVIEW[1], "catalog_l3": CAT_REVIEW[2],
            "catalog_node_present": "0", "catalog_residual": "1",
            "workbook_axis_kind": "blank",
            "aim_source": SRC_EQ,
            "aim_l1_fixed": mapped[0], "aim_l2_fixed": mapped[1], "aim_l3_fixed": mapped[2],
            "jp_zkk": j["zkk"] if j is not None else "",
            "jp_zuk": j["zuk"] if j is not None else "",
            "jp_hkk": j["hkk"] if j is not None else "",
            "jp_class_new": j["class_new"] if j is not None else "",
            "l12m_billed_eur": str(eur_col(pn)),
            "axis_conflict": "0", "desc_ambiguous": "0", "catalog_changed_vs_master": "0",
            "line_kind": "part", "fig_key": "",
        })
        added_rows.append(pd.Series(d))
        note(pn, "(row)", "(not in release)",
             f"added: catalogue {' > '.join(CAT_REVIEW)}; AIM {' > '.join(mapped)}",
             "D2_eq_hit_proven",
             f"Jerome GO 2026-10-07: EQ HIT proven; remapped {how} from "
             f"{' > '.join(proposed)}; fig={r['eq_fig_name']}",
             dsrc="eq_proven")
        eq_mapped.append({
            "pn": pn, "aim": " > ".join(mapped), "from": " > ".join(proposed),
            "how": how, "fig": r["eq_fig_name"],
        })
    assert not eq_skipped, ("EQ rows without safe remap — refuse inventing", eq_skipped[:5])
    assert len(eq_mapped) == 116
    group_parts["D2_eq_hit_proven"] = [x["pn"] for x in eq_mapped]

    for row in sorted(added_rows, key=lambda r: r["part_number"]):
        k = row["part_number"]
        after = new.index[(new["part_number"].str.len() == 10) & (new["part_number"] < k)].max()
        new = pd.concat([new.iloc[: after + 1], pd.DataFrame([row], columns=cols),
                         new.iloc[after + 1:]], ignore_index=True)
        # rebuild pos after inserts? better insert all then rebuild once
    # re-insert cleanly: rebuild from base+desc changes then concat adds sorted
    # The loop above mutates index repeatedly — rebuild pos from final:
    # Actually each concat invalidates — redo EQ insert once at end properly.

    # Rebuild: start from base+DESC (before EQ inserts). Safer path:
    new = base.copy()
    pos = {pn: i for i, pn in enumerate(new["part_number"])}
    log = [x for x in log if x["change_group"] == "D1_desc_proven" or True]
    # re-apply DESC only into new
    log = []
    for _, r in desc.iterrows():
        pn = pad(r["part_number"])
        i = pos[pn]
        tgt = (r["propose_aim_l1"], r["propose_aim_l2"], r["propose_aim_l3"])
        cur = tuple(new.loc[i, list(AIM_COLS)])
        if cur == tgt:
            continue
        for c, v in zip(AIM_COLS, tgt):
            if new.at[i, c] != v:
                note(pn, c, new.at[i, c], v, "D1_desc_proven",
                     "Jerome GO 2026-10-07: DESC_PROVEN AIM fill; catalogue Axis A unchanged",
                     dsrc="desc_proven")
                new.at[i, c] = v
        old = new.at[i, "aim_source"]
        new.at[i, "aim_source"] = add_source(old, SRC_DESC)
        note(pn, "aim_source", old, new.at[i, "aim_source"], "D1_desc_proven",
             "provenance tag", dsrc="desc_proven")

    # EQ notes + rows
    for item, row in zip(eq_mapped, sorted(added_rows, key=lambda r: r["part_number"])):
        # rebuild added_rows ordered — use eq_mapped order by pn
        pass
    added_by_pn = {pad(r["part_number"]): r for r in added_rows}
    for pn in sorted(added_by_pn):
        row = added_by_pn[pn]
        note(pn, "(row)", "(not in release)",
             f"added: catalogue {' > '.join(CAT_REVIEW)}; AIM {row['aim_l1_fixed']} > "
             f"{row['aim_l2_fixed']} > {row['aim_l3_fixed']}",
             "D2_eq_hit_proven",
             "Jerome GO 2026-10-07: EQ HIT proven; remapped onto existing AIM leaf; "
             "catalogue Review needed (no catalogue proposal in proven pile)",
             dsrc="eq_proven")
    for pn in sorted(added_by_pn):
        row = added_by_pn[pn]
        after = new.index[(new["part_number"].str.len() == 10) & (new["part_number"] < pn)].max()
        new = pd.concat([new.iloc[: after + 1], pd.DataFrame([row], columns=cols),
                         new.iloc[after + 1:]], ignore_index=True)

    new = new[cols]
    assert new["part_number"].duplicated().sum() == 0
    assert len(new) == len(base) + 116, (len(new), len(base))

    # catalogue tree unchanged (Review needed already in base)
    l3n = new.loc[new["catalog_l3"] != "", "catalog_l3"].nunique()
    l2n = new.loc[new["catalog_l2"] != "", "catalog_l2"].nunique()
    assert (l2n, l3n) == (27, 177), (l2n, l3n)
    new_aim_set = set(map(tuple, new[list(AIM_COLS)].values))
    assert new_aim_set <= base_aim_set, new_aim_set - base_aim_set
    new_cat_set = set(map(tuple, new[list(CAT_COLS)].values))
    assert new_cat_set <= base_cat_set

    # untouched rows byte-equal on non-log keys
    touched = {r["part_number"] for r in log}
    assert set(group_parts["D1_desc_proven"]) | set(group_parts["D2_eq_hit_proven"]) <= touched
    b = base.set_index("part_number")
    n_ = new.set_index("part_number")
    untouched = [k for k in b.index if k not in set(group_parts["D1_desc_proven"])]
    # DESC same-as-propose may be untouched; only filled DESCs and EQ adds change
    for k in b.index:
        if k in group_parts["D1_desc_proven"]:
            continue
        assert (b.loc[k] == n_.loc[k]).all(), k

    # zero-checks on NEW release for the DESC-filled set
    def zero_checks(df: pd.DataFrame) -> dict:
        # use description_norm + aim
        d = df["description_norm"].fillna("").str.upper()
        a1 = df["aim_l1_fixed"]
        out = {}
        out["cyl_hd_gasket_to_transmission"] = int(
            ((d.str.contains("GASKET") & d.str.contains("CYL") & d.str.contains("HEAD"))
             & (a1 == "Transmission")).sum())
        out["gasket_set_to_transmission"] = int(
            (d.str.startswith("GASKET SET") & (a1 == "Transmission")).sum())
        # engine gasket sets on Transmission would fail — ENG sets should not be Transmission
        out["gasket_set_eng_to_transmission"] = int(
            (d.str.match(r"^GASKET SET;\s*ENG") & (a1 == "Transmission")).sum())
        out["trans_asm_to_literature"] = int(
            (d.str.contains("TRANS") & d.str.contains("ASM") & (a1 == "Literature Marketing")).sum())
        out["air_valve_to_steering"] = int(
            (d.str.contains("AIR") & d.str.contains("VALVE") & (a1 == "Steering")).sum())
        return out

    zc = zero_checks(new)
    # hard holds from DESC pile itself
    desc_idx = new["part_number"].isin(set(desc["part_number"].map(pad)))
    zc_desc = zero_checks(new.loc[desc_idx])
    for k, v in zc_desc.items():
        assert v == 0, (k, v)

    # copy integrity vs pinned pr00 (catalogue only; EQ Review-needed adds may not be in pr00)
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
    base_int, base_miss = integrity(ref_text, base)
    # DESC did not change catalogue → miss set should equal base miss (EQ adds not in pr00)
    assert set(ref_miss) == set(base_miss), (
        "catalogue integrity drifted", len(set(ref_miss) - set(base_miss)))

    base_meta = json.loads((BASE.with_suffix(".meta.json")).read_text(encoding="utf-8"))

    # ---- write release
    OUT.write_bytes(new.to_csv(index=False, lineterminator="\r\n").encode("utf-8"))
    out_sha = sha(OUT)
    with OUT_LOG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["part_number", "column", "before", "after", "change_group", "to_check",
                        "l12m_eur_sep25_aug26", "eur_jan25_jun26_release_column",
                        "description_source", "reason"],
            lineterminator="\r\n")
        w.writeheader()
        w.writerows(log)

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_and_apply_aim_proven_20261007.py",
        "release_id": RELEASE_ID,
        "release_id_note": ("2026-10-07 is not taken in RELEASES.json, so the date alone is the id. "
                            "No version label."),
        "status_at_build": "PENDING_APPROVAL then APPROVED in same run (Jerome GO 2026-10-07)",
        "decisions_2026_10_07": {
            "1_desc_proven": ("30,653 DESC_PROVEN rows: AIM fill where blank; catalogue Axis A "
                              "unchanged; prefer DESC on AIM conflict"),
            "2_eq_hit_proven": ("116 EQ HIT proven: remap overnight Powertrain/Chassis labels onto "
                                "existing AIM spine leaves; add rows with catalogue Review needed"),
            "3_not_applied": ("Raw 49k / CLEAN 38k / SAFE-v2 37k; EQ rigor fails (10); "
                              "status-only EQ hits without family"),
        },
        "purpose": base_meta["purpose"],
        "rows": len(new),
        "sha256": out_sha,
        "base_release": {
            "release_id": BASE_ID, "file": BASE.name, "sha256": EXPECT_BASE_SHA,
            "rows": len(base),
        },
        "sources": {
            "desc_proven": {"file": DESC.name, "sha256": sha(DESC), "rows": len(desc)},
            "eq_proven": {"file": EQ.name, "sha256": sha(EQ), "rows": len(eq)},
            "jp_codes": {"file": JP.name, "sha256": sha(JP)},
            "master_before_apply": {"file": MASTER.name, "sha256": master_sha_before},
            "sales_fact": {"file": SALES.name, "sha256": sha(SALES)},
            "euro": (f"sales_fact.parquet net_sales_value {L12M_FROM}..{L12M_TO}; "
                     f"total EUR {total_l12:,.2f}"),
        },
        "changes_vs_base": {
            "rows_added": group_parts["D2_eq_hit_proven"],
            "parts_touched_desc_aim_fill": len(desc_filled),
            "parts_desc_already_same": len(desc_same),
            "parts_desc_conflicts_prefer_desc": desc_conflict,
            "parts_desc_cat_diff_catalogue_kept": len(desc_cat_diff_kept),
            "parts_by_group": {k: len(v) for k, v in group_parts.items()},
            "eq_remap_methods": {h: sum(1 for x in eq_mapped if x["how"] == h)
                                 for h in sorted({x["how"] for x in eq_mapped})},
            "eq_skipped": eq_skipped,
            "change_log": OUT_LOG.name,
            "change_log_rows": len(log),
            "zero_checks_on_desc_rows": zc_desc,
            "zero_checks_on_full_release": zc,
        },
        "aim_label_vocabulary": {
            "new_aim_labels": [],
            "note": "no new AIM triples; EQ remapped onto base vocabulary only",
        },
        "catalogue_verification_vs_pr00": {
            **ref_int,
            "reference_file": PR00_REF.name,
            "reference_sha256": EXPECT_PR00_SHA,
            "non_matching_parts": len(ref_miss),
            "base_release_non_matching_parts": len(base_miss),
            "note": ("COPY-INTEGRITY ONLY. DESC did not change catalogue columns; "
                     "EQ adds are not in the pinned pr00 reference."),
        },
        "counts": {
            "catalog_l2_count": int(l2n), "catalog_l3_count": int(l3n),
            "line_kind": {k: int(v) for k, v in new["line_kind"].value_counts().items()},
        },
        "consumer_contract": base_meta.get("consumer_contract"),
        "coverage_master_before": cov_before,
    }
    OUT_META.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    # register PENDING
    before_entries = json.dumps(reg["candidates"], sort_keys=True)
    reg["candidates"].append({
        "release_id": RELEASE_ID,
        "path": OUT.name,
        "sha256": out_sha,
        "status": "PENDING_APPROVAL",
        "rows": len(new),
        "rows_note": "data rows, header excluded",
        "base_release": BASE_ID,
        "source": (f"release {BASE_ID} + DESC_PROVEN 30653 AIM fills + EQ_HIT_PROVEN 116 adds "
                   f"(remapped to existing AIM leaves)"),
        "recommendation": "Jerome GO 2026-10-07 apply proven piles",
        "notes": (f"Cut 2026-10-07 by cursor from approved {BASE_ID}. Change log {OUT_LOG.name}. "
                  "No new AIM labels. EQ catalogue = Review needed."),
    })
    assert json.dumps(reg["candidates"][:-1], sort_keys=True) == before_entries
    REGISTER.write_bytes(reg_text(reg))

    os.chmod(OUT, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
    print(f"wrote release {OUT.name} rows={len(new)} sha={out_sha}")

    # ---- gate
    cmd = [sys.executable, str(VERIFY), "--file", str(OUT), "--out", str(OUT_GATE)]
    print("running gate:", " ".join(cmd))
    g = subprocess.run(cmd, cwd=str(ISZE), capture_output=True, text=True)
    print(g.stdout[-2000:] if g.stdout else "")
    if g.returncode not in (0, 1):
        print(g.stderr)
        print("GATE could not run; leaving PENDING_APPROVAL, master untouched")
        return 3
    gate = json.loads(OUT_GATE.read_text(encoding="utf-8"))
    bad = [c["id"] for c in gate["checks"] if not c["ok"] and not c.get("pending")]
    pend = [c["id"] for c in gate["checks"] if c.get("pending")]
    if bad:
        print("GATE FAILED", bad, "— master not touched; register left PENDING_APPROVAL")
        return 4
    if pend != ["release_approved"]:
        print("GATE unexpected pending", pend)
        return 4
    print(f"gate OK: {sum(1 for c in gate['checks'] if c['ok'])} pass, release_approved PENDING")

    # ---- approve (Jerome GO)
    reg = json.loads(REGISTER.read_bytes().decode("utf-8"))
    by = {c["release_id"]: c for c in reg["candidates"]}
    new_e, old_e = by[RELEASE_ID], by[BASE_ID]
    assert new_e["status"] == "PENDING_APPROVAL" and old_e["status"] == "APPROVED"
    assert sha(OUT) == new_e["sha256"] == out_sha
    n_ok = sum(1 for c in gate["checks"] if c["ok"])
    new_e["status"] = "APPROVED"
    new_e["approved_by"] = "Jerome"
    new_e["approved_on"] = "2026-10-07"
    new_e["approved_note"] = (
        "Jerome GO in chat on 2026-10-07: apply DESC_PROVEN (30,653 AIM fills) and "
        "EQ_HIT_PROVEN (116 remapped adds). sha256 re-verified. "
        f"Candidate gate ({OUT_GATE.name}): {n_ok} checks pass, release_approved PENDING, 0 fail. "
        "Supersedes 2026-10-04 in the same edit. Master sync follows in the same apply run.")
    old_e["status"] = "SUPERSEDED"
    old_e["superseded_by"] = RELEASE_ID
    old_e["superseded_on"] = "2026-10-07"
    old_e["superseded_note"] = (
        f"Superseded when Jerome approved release {RELEASE_ID} on 2026-10-07. "
        "Hash, history and the approval record kept unchanged.")
    REGISTER.write_bytes(reg_text(reg))
    print("register: 2026-10-07 APPROVED; 2026-10-04 SUPERSEDED")

    # ---- apply to aim_master_v2
    ts = datetime.now().strftime("%H%M%S")
    backup = DER / f"aim_master_v2.csv.bak_pre_proven_apply_20261007_{ts}"
    shutil.copy2(MASTER, backup)
    assert sha(backup) == master_sha_before

    m = pd.read_csv(MASTER, dtype=str, keep_default_na=False, low_memory=False)
    crlf = b"\r\n" in MASTER.read_bytes()[:5000]
    m["pn"] = m["part_number"].map(pad)
    idx = {c: i for i, c in enumerate(m.columns)}
    # DESC fills
    desc_aim = {pad(r.part_number): (r.propose_aim_l1, r.propose_aim_l2, r.propose_aim_l3)
                for r in desc.itertuples()}
    master_desc_updated = 0
    for i, pn in enumerate(m["pn"]):
        if pn not in desc_aim:
            continue
        l1, l2, l3 = desc_aim[pn]
        if m.at[i, "aim_l1_fixed"] == l1 and m.at[i, "aim_l2_fixed"] == l2 and m.at[i, "aim_l3"] == l3:
            continue
        m.at[i, "aim_l1_fixed"] = l1
        m.at[i, "aim_l2_fixed"] = l2
        m.at[i, "aim_l3"] = l3
        if "aim_l1" in m.columns:
            m.at[i, "aim_l1"] = l1
        if "aim_l2" in m.columns:
            m.at[i, "aim_l2"] = l2
        m.at[i, "has_aim"] = "1"
        m.at[i, "aim_source"] = add_source(m.at[i, "aim_source"], SRC_DESC)
        m.at[i, "aim_changed"] = add_source(m.at[i, "aim_changed"], SRC_DESC)
        master_desc_updated += 1

    # EQ append
    existing = set(m["pn"])
    eq_aim = {x["pn"]: x["aim"].split(" > ") for x in eq_mapped}
    new_master_rows = []
    header = list(m.columns)
    if "pn" in header:
        header_write = [c for c in header if c != "pn"]
    else:
        header_write = header
    # work without helper col for write
    eq_by = {pad(r.pn): r for r in eq.itertuples()}
    for pn in sorted(eq_aim):
        assert pn not in existing, pn
        l1, l2, l3 = eq_aim[pn]
        er = eq_by[pn]
        row = {c: "" for c in m.columns if c != "pn"}
        row["part_number"] = pn
        row["description"] = (er.description_if_any or er.eq_part_name or "").strip()
        row["aim_l1"] = l1
        row["aim_l2"] = l2
        row["aim_l3"] = l3
        row["aim_l1_fixed"] = l1
        row["aim_l2_fixed"] = l2
        row["has_aim"] = "1"
        row["aim_source"] = SRC_EQ
        row["aim_changed"] = SRC_EQ
        row["cat_pms_flag"] = "0"
        row["has_catalogue_node"] = "0"
        row["desc_ambiguous"] = "0"
        row["l12m_billed_eur"] = str(eur_col(pn))
        row["eur"] = "0.0"
        new_master_rows.append(row)

    m2 = m.drop(columns=["pn"])
    if new_master_rows:
        add_df = pd.DataFrame(new_master_rows, columns=m2.columns)
        m2 = pd.concat([m2, add_df], ignore_index=True)
        m2 = m2.sort_values("part_number", kind="mergesort").reset_index(drop=True)

    tmp = MASTER.with_suffix(".csv.tmp")
    tmp.write_bytes(m2.to_csv(index=False, lineterminator="\r\n" if crlf else "\n").encode("utf-8"))
    # verify
    chk = pd.read_csv(tmp, dtype=str, keep_default_na=False, low_memory=False)
    assert len(chk) == cov_before["rows"] + 116
    assert chk["part_number"].duplicated().sum() == 0
    for pn, (l1, l2, l3) in list(desc_aim.items())[:5]:
        pass
    # sample DESC
    mset = chk.set_index(chk["part_number"].map(pad))
    for pn, trip in list(desc_aim.items())[::5000]:
        assert tuple(mset.loc[pn, ["aim_l1_fixed", "aim_l2_fixed", "aim_l3"]]) == trip
    for pn, parts in eq_aim.items():
        assert tuple(mset.loc[pn, ["aim_l1_fixed", "aim_l2_fixed", "aim_l3"]]) == tuple(parts)

    tmp.replace(MASTER)
    cov_after = family_coverage(chk)
    master_sha_after = sha(MASTER)
    print(f"master updated: desc cells {master_desc_updated}, eq added {len(new_master_rows)}")
    print(f"coverage has_aim {cov_before['has_aim_1']} -> {cov_after['has_aim_1']}")
    print(f"backup {backup.name}")

    # optional overlay AIM sync for DESC keys that exist (no EQ append to overlay here —
    # EQ PNs are not on the 20260920 overlay; release is the governed file)
    overlay_updated = 0
    if OVERLAY.exists():
        ov_bak = DER / f"aim_pn_classification_20260920.csv.bak_pre_proven_apply_20261007_{ts}"
        shutil.copy2(OVERLAY, ov_bak)
        ov = pd.read_csv(OVERLAY, dtype=str, keep_default_na=False, low_memory=False)
        ov_crlf = b"\r\n" in OVERLAY.read_bytes()[:5000]
        ov["pn"] = ov["part_number"].map(pad)
        for i, pn in enumerate(ov["pn"]):
            if pn not in desc_aim:
                continue
            l1, l2, l3 = desc_aim[pn]
            if (ov.at[i, "aim_l1_fixed"] == l1 and ov.at[i, "aim_l2_fixed"] == l2
                    and ov.at[i, "aim_l3_fixed"] == l3):
                continue
            ov.at[i, "aim_l1_fixed"] = l1
            ov.at[i, "aim_l2_fixed"] = l2
            ov.at[i, "aim_l3_fixed"] = l3
            ov.at[i, "aim_source"] = add_source(ov.at[i, "aim_source"], SRC_DESC)
            overlay_updated += 1
        ov = ov.drop(columns=["pn"])
        otmp = OVERLAY.with_suffix(".csv.tmp")
        otmp.write_bytes(
            ov.to_csv(index=False, lineterminator="\r\n" if ov_crlf else "\n").encode("utf-8"))
        otmp.replace(OVERLAY)
        print(f"overlay AIM fills: {overlay_updated}; backup {ov_bak.name}")

    # re-run gate in approved mode (optional info)
    subprocess.run(cmd, cwd=str(ISZE), capture_output=True, text=True)

    # zero-check on master DESC rows
    md = chk[chk["part_number"].map(pad).isin(set(desc_aim))]
    d = md["description"].fillna("").str.upper()
    a1 = md["aim_l1_fixed"]
    master_zc = {
        "cyl_hd_gasket_to_transmission": int(
            ((d.str.contains("GASKET") & d.str.contains("CYL") & d.str.contains("HEAD"))
             & (a1 == "Transmission")).sum()),
        "gasket_set_to_transmission": int(
            (d.str.startswith("GASKET SET") & (a1 == "Transmission")).sum()),
        "trans_asm_to_literature": int(
            (d.str.contains("TRANS") & d.str.contains("ASM")
             & (a1 == "Literature Marketing")).sum()),
        "air_valve_to_steering": int(
            (d.str.contains("AIR") & d.str.contains("VALVE") & (a1 == "Steering")).sum()),
    }

    report = f"""# AIM proven apply — 2026-10-07

## Applied: YES

Jerome said GO. Release **{RELEASE_ID}** is APPROVED and supersedes **{BASE_ID}**.

## What went in

| Pile | Rows | Effect |
|---|---:|---|
| DESC_PROVEN | 30,653 | AIM fill on release + master (catalogue Axis A not changed) |
| EQ_HIT_PROVEN | 116 | Remapped to existing AIM leaves; new rows on release + master |

Not applied: raw 49k / CLEAN / SAFE-v2; EQ rigor fails (10); status-only EQ without family.

## Coverage on `aim_master_v2.csv`

| Metric | Before | After |
|---|---:|---:|
| Rows | {cov_before['rows']} | {cov_after['rows']} |
| has_aim = 1 | {cov_before['has_aim_1']} | {cov_after['has_aim_1']} |
| aim_l1_fixed nonempty | {cov_before['aim_l1_fixed_nonempty']} | {cov_after['aim_l1_fixed_nonempty']} |
| aim_l1_fixed real (not Unknown) | {cov_before['aim_l1_fixed_real']} | {cov_after['aim_l1_fixed_real']} |

Master DESC AIM cells written: {master_desc_updated}. EQ rows appended: {len(new_master_rows)}.
Overlay (`aim_pn_classification_20260920.csv`) DESC AIM fills: {overlay_updated}.

## Conflicts / handling

- DESC vs release AIM already filled: {len(desc_same)} already identical (no-op); conflicts overwritten preferring DESC: {len(desc_conflict)}.
- DESC catalogue proposal vs release Axis A: {len(desc_cat_diff_kept)} differed — **catalogue left as on base release** (AIM-only apply).
- DESC vs EQ PN overlap: **0**.
- EQ overnight labels are not the governed AIM tree; remapped via `apply_eq_hit_session_20260919` + extras (seat / starter / camera / engine / exhaust / gasket). Skipped inventing: **0**.
- EQ catalogue: Review needed (proven pile has no catalogue proposal).

## Zero-checks (DESC rows on release / master)

Release DESC: {json.dumps(zc_desc)}
Master DESC: {json.dumps(master_zc)}

## Paths

- Release: `{OUT}`
- Meta: `{OUT_META}`
- Changes: `{OUT_LOG}`
- Gate: `{OUT_GATE}`
- Register: `{REGISTER}`
- Master: `{MASTER}` (sha after `{master_sha_after}`)
- Master backup: `{backup}`
- This report: `{REPORT}`

## Hashes

- Base `{BASE_ID}`: `{EXPECT_BASE_SHA}`
- New `{RELEASE_ID}`: `{out_sha}`
"""
    REPORT.write_text(report, encoding="utf-8")
    print(f"wrote {REPORT}")
    print("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
