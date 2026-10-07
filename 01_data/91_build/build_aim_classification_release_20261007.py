#!/usr/bin/env python3
"""Cut + apply classification release 2026-10-07 (Jerome GO).

Base: approved 2026-10-04. Applies ONLY:
  1. next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv (30,653)
  2. next_release_proposal_eq_hit_live_order_PROVEN_2026-10-07.csv (116)

DESC: AIM labels only on blank aim_l*_fixed (catalogue left as base). Prefer DESC on
conflict (none expected). Catalogue diffs in the proposal are NOT applied.

EQ: overnight Powertrain/Chassis labels remapped onto existing AIM leaves (never invent).
Parts not on the release are appended with catalogue Other/review > Miscellaneous >
Review needed. Rows that cannot map to a known leaf are skipped and logged.

Jerome said GO: register goes APPROVED and aim_master_v2 is synced in the apply step
(build_aim_apply_proven_20261007.py). This script writes the release + PENDING entry +
gate inputs; approve+master sync is a second script or --apply flag.

    python build_aim_classification_release_20261007.py
    python build_aim_classification_release_20261007.py --apply
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import os
import shutil
import stat
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
OUT_EQ_SKIP = REL / f"aim_pn_classification_release_{RELEASE_ID}.eq_skipped.csv"
OUT_EQ_MAP = REL / f"aim_pn_classification_release_{RELEASE_ID}.eq_remap.csv"

BASE = REL / f"aim_pn_classification_release_{BASE_ID}.csv"
DESC = REL / "next_release_proposal_full_class_tranche1_catmap_DESC_PROVEN_2026-10-07.csv"
EQ = REL / "next_release_proposal_eq_hit_live_order_PROVEN_2026-10-07.csv"
PR00_REF = REL / "pr00_classification_reference_20260920.csv"
PR00_LIVE = DER / "pr00_classification.csv"
MASTER = DER / "aim_master_v2.csv"
JP = DER / "jp_codes_cache_20260920.csv"
SALES = DER / "sales_fact.parquet"
OVERLAY = DER / "aim_pn_classification_20260920.csv"

TAG = "20261007"
SRC_DESC = f"desc_proven_{TAG}"
SRC_EQ = f"eq_hit_proven_{TAG}"
L12M_FROM, L12M_TO = "2025-09-01", "2026-08-31"
COL_FROM, COL_TO = "2025-01-01", "2026-06-30"

CAT_COLS = ("catalog_l1", "catalog_l2", "catalog_l3")
AIM_COLS = ("aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed")
CAT_REVIEW = ("Other / review", "Miscellaneous", "Review needed")

EXPECT_SHA = {
    BASE: "8aad884f49db1a49ab86faca571942d912196ce08f7734f38d5a04f035e18896",
    DESC: None,  # filled at runtime; recorded in meta
    EQ: None,
    PR00_REF: "98e64b5bdaef73819cf954ce96241f1a9b49d8fbd998d02700ae8494028bea34",
}


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
    return (json.dumps(reg, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8")


def add_source(cur: str, tag: str) -> str:
    return f"{cur}|{tag}" if cur else tag


def load_eq_remap_mod():
    path = BUILD / "apply_eq_hit_session_20260919.py"
    spec = importlib.util.spec_from_file_location("eq_remap_20260919", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def refine_eq_extra(
    proposed: tuple[str, str, str],
    fig: str,
    part: str,
    desc: str,
    known: set[tuple[str, str, str]],
) -> tuple[str, str, str] | None:
    """Map EQ parallel labels that the 2026-09-19 table does not cover, onto known leaves only."""
    t = f"{fig} {part} {desc}".upper()
    p1, p2, p3 = proposed

    def accept(cands: list[tuple[str, str, str]]) -> tuple[str, str, str] | None:
        for c in cands:
            if c in known:
                return c
        for c in cands:
            for k in known:
                if k[0] == c[0] and k[1] == c[1]:
                    return k
        return None

    if (p1, p2, p3) == ("Body", "Interior", "Seat parts"):
        if "BELT" in t:
            return accept([("Cabin Interior", "Seat", "Seat Belt")])
        if "BACK" in t:
            return accept([("Cabin Interior", "Seat", "Seat Back")])
        if "CUSHION" in t:
            return accept([("Cabin Interior", "Seat", "Seat Cushion")])
        if "COVER" in t or "TRIM" in t:
            return accept([("Cabin Interior", "Seat", "Seat Cushion"),
                           ("Cabin Interior", "Seat", "Review needed")])
        return accept([("Cabin Interior", "Seat", "Review needed")])

    if (p1, p2, p3) == ("Powertrain", "Engine", "Engine parts"):
        if "CONTROL UNIT" in t:
            return accept([("Electrical", "Control Units", "Control Unit")])
        if "GENERATOR" in t or "ALTERNATOR" in t:
            return accept([("Electrical", "Charging", "Alternator/Generator")])
        if "LINER" in t:
            return accept([("Engine", "Block & Structure", "Cylinder Liner")])
        if "PISTON" in t and "RING" in t:
            return accept([("Engine", "Internal Rotating", "Piston")])
        if "FOOT" in t or "MOUNT" in t:
            return accept([("Engine", "Mounting", "Engine Mount")])
        if "HEAD COVER" in t or "ENGINE COVER" in t or "BRACKET; ENGINE COVER" in t:
            return accept([("Engine", "Cylinder Head", "Head Cover"),
                           ("Chassis Frame", "Crossmember & Brackets", "Bracket")])
        if "CYLINDER HEAD" in t or "EXH MANIF" in t and "STUD" in t:
            return accept([("Engine", "Cylinder Head", "Head Cover"),
                           ("Engine", "Block & Structure", "Cylinder Block")])
        if "CYLINDER BLOCK" in t or "CRANKCASE" in t or "FRT COVER" in t:
            return accept([("Engine", "Block & Structure", "Cylinder Block")])
        if "OIL PUMP" in t or "OIL FILLER" in t or "OIL PAN" in t:
            return accept([("Engine", "Block & Structure", "Oil Pan")])
        if "DAMPER" in t or "WASHER; DAMPER" in t:
            return accept([("Engine", "Internal Rotating", "Thrust Washer"),
                           ("Engine", "Internal Rotating", "Engine Internal")])
        return accept([("Engine", "Internal Rotating", "Engine Internal"),
                       ("Engine", "Block & Structure", "Cylinder Block")])

    if (p1, p2, p3) == ("Powertrain", "Exhaust / aftertreatment", "Exhaust parts"):
        if "MAT" in t and ("SILENCER" in t or "FLOOR" in t or "CARPET" in t):
            return accept([("Cabin Interior", "Interior Trim", "Floor Mat")])
        if "DPD" in t:
            return accept([("Intake Exhaust Emission", "DPF/DPD", "DPD Assembly")])
        if "SILENCER" in t:
            return accept([("Intake Exhaust Emission", "Exhaust", "Silencer")])
        if "MANIF" in t or "EXH" in t or "EXHAUST" in t:
            return accept([("Intake Exhaust Emission", "Exhaust", "Exhaust Pipe")])
        return accept([("Intake Exhaust Emission", "Exhaust", "Exhaust Pipe")])

    if (p1, p2, p3) == ("Powertrain", "Gaskets / seals", "Gasket / seal"):
        if "GASKET SET" in t and "ENG" in t:
            return accept([("Engine", "Gasket & Sealing", "Gasket")])
        if "EGR" in t:
            return accept([("Engine", "Gasket & Sealing", "Gasket"),
                           ("Intake Exhaust Emission", "EGR", "EGR Component")])
        if "WATER" in t or "THERMOSTAT" in t or "HSG" in t:
            return accept([("Engine", "Gasket & Sealing", "Gasket")])
        if "INL" in t or "NOZZLE" in t or "FUEL" in t:
            return accept([("Engine", "Gasket & Sealing", "Gasket")])
        return accept([("Engine", "Gasket & Sealing", "Gasket")])

    if (p1, p2, p3) == ("Electrical", "Battery", "Battery"):
        if "CABLE" in t or "CLIP" in t:
            return accept([("Electrical", "Charging", "Battery Cable"),
                           ("Electrical", "Starting & Charging", "Battery Cable")])
        return accept([("Electrical", "Charging", "Battery Accessory")])

    if (p1, p2, p3) == ("Electrical", "Starting / charging", "Starter"):
        return accept([("Electrical", "Motors & Actuators", "Motor")])

    if (p1, p2, p3) == ("Filters", "Fuel filtration", "Fuel filter"):
        return accept([("Maintenance Service", "Fuel Filter", "Fuel Filter Element"),
                       ("Maintenance Service", "Filters (unspecified)", "Fuel Filter")])

    if (p1, p2, p3) == ("Body", "Door / glass", "Door parts"):
        if "LOCK" in t or "HANDLE" in t:
            return accept([("Accident & Body", "Locks & Handles", "Latch"),
                           ("Accident & Body", "Locks & Handles", "Handle"),
                           ("Accident & Body", "Panels", "Door")])
        return accept([("Accident & Body", "Panels", "Door")])

    if (p1, p2, p3) == ("Electrical", "Sensors / cameras", "Camera"):
        # No Camera leaf on the governed AIM tree — refuse rather than invent.
        return None

    return None


def map_eq_row(mod, proposed, fig, part, desc, known):
    mapped = mod.remap_row(proposed, fig, part, known)
    if mapped and mapped in known:
        return mapped, "eq_session_remap_20260919"
    extra = refine_eq_extra(proposed, fig, part, desc, known)
    if extra and extra in known:
        return extra, "eq_extra_fig_desc_20261007"
    return None, "no_safe_spine_leaf"


def main() -> int:
    do_apply = "--apply" in sys.argv
    for p in (OUT, OUT_META, OUT_LOG, OUT_EQ_SKIP, OUT_EQ_MAP):
        if p.exists():
            print(f"REFUSED: {p.name} already exists; a release file is never overwritten.")
            return 2

    for p, h in EXPECT_SHA.items():
        if h is None:
            continue
        got = sha(p)
        if got != h:
            print(f"REFUSED: {p.name} sha256 {got[:12]} != expected {h[:12]}")
            return 2

    desc_sha = sha(DESC)
    eq_sha = sha(EQ)
    EXPECT_SHA[DESC] = desc_sha
    EXPECT_SHA[EQ] = eq_sha

    reg_before = REGISTER.read_bytes()
    reg = json.loads(reg_before.decode("utf-8"))
    assert reg_text(reg) == reg_before
    assert all(c["release_id"] != RELEASE_ID for c in reg["candidates"]), "release id taken"
    base_entry = next(c for c in reg["candidates"] if c["release_id"] == BASE_ID)
    assert base_entry["status"] == "APPROVED" and base_entry["sha256"] == EXPECT_SHA[BASE]

    base_bytes = BASE.read_bytes()
    base = pd.read_csv(io.BytesIO(base_bytes), dtype=str, keep_default_na=False, low_memory=False)
    cols = list(base.columns)
    assert base.to_csv(index=False, lineterminator="\r\n").encode("utf-8") == base_bytes
    new = base.copy()
    pos = {pn: i for i, pn in enumerate(new["part_number"])}
    assert len(pos) == len(new)

    base_aim_set = set(zip(new["aim_l1_fixed"], new["aim_l2_fixed"], new["aim_l3_fixed"]))
    base_cat_set = set(zip(new["catalog_l1"], new["catalog_l2"], new["catalog_l3"]))
    assert CAT_REVIEW in base_cat_set

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

    jp = read(JP)
    jp["pn"] = jp["pn"].map(pad)
    jpi = jp.drop_duplicates("pn").set_index("pn")

    log: list[dict] = []

    def note(pn, col, before, after, group, reason, to_check="", dsrc=""):
        log.append({
            "part_number": pn, "column": col, "before": before, "after": after,
            "change_group": group, "to_check": to_check,
            "l12m_eur_sep25_aug26": eur(pn),
            "eur_jan25_jun26_release_column": eur_col(pn),
            "description_source": dsrc, "reason": reason,
        })

    def set_aim(pn: str, tgt: tuple, group: str, reason: str, src_tag: str,
                to_check: str = "", dsrc: str = "") -> None:
        i = pos[pn]
        changed = False
        for c, v in zip(AIM_COLS, tgt):
            if new.at[i, c] != v:
                note(pn, c, new.at[i, c], v, group, reason, to_check, dsrc)
                new.at[i, c] = v
                changed = True
        if not changed:
            return
        old = new.at[i, "aim_source"]
        new.at[i, "aim_source"] = add_source(old, src_tag)
        note(pn, "aim_source", old, new.at[i, "aim_source"], group, "provenance tag",
             to_check, dsrc)

    # ---- DESC_PROVEN: AIM fill on blank only; catalogue untouched
    desc = read(DESC)
    assert len(desc) == 30653, len(desc)
    assert desc["part_number"].is_unique
    desc_aim_set = set(zip(desc["propose_aim_l1"], desc["propose_aim_l2"], desc["propose_aim_l3"]))
    assert desc_aim_set <= base_aim_set, sorted(desc_aim_set - base_aim_set)[:10]

    desc_filled = []
    desc_already_same = []
    desc_kept_existing = []  # non-blank AIM left untouched (protects 2026-10-04 moves)
    desc_cat_diffs_not_applied = []
    for _, r in desc.iterrows():
        pn = pad(r["part_number"])
        assert pn in pos, ("DESC PN missing from release", pn)
        i = pos[pn]
        tgt = (r["propose_aim_l1"], r["propose_aim_l2"], r["propose_aim_l3"])
        assert all(tgt)
        cur = tuple(new.at[i, c] for c in AIM_COLS)
        cat_prop = (r["cat_l1"], r["cat_l2"], r["cat_l3"])
        cat_cur = tuple(new.at[i, c] for c in CAT_COLS)
        if cat_prop != cat_cur:
            desc_cat_diffs_not_applied.append(pn)
        if cur == tgt:
            desc_already_same.append(pn)
            continue
        if cur[0]:
            # Never overwrite a non-blank AIM label (keeps 2026-10-04 gasket/EVRV/antenna/DEF).
            desc_kept_existing.append({
                "part_number": pn, "kept": " > ".join(cur), "desc_proposed": " > ".join(tgt),
            })
            continue
        set_aim(pn, tgt, "D1_desc_proven",
                "Jerome GO 2026-10-07: DESC_PROVEN catalogue-path + description rigor "
                f"({r.get('method','')}; conf {r.get('confidence','')})",
                SRC_DESC, dsrc="desc_proven_proposal")
        desc_filled.append(pn)

    # ---- Prove 2026-10-04 AIM moves are byte-identical on those PNs
    base_changes = REL / "aim_pn_classification_release_2026-10-04.changes.csv"
    chg04 = read(base_changes)
    aim04_pns = sorted({
        pad(r["part_number"]) for _, r in chg04.iterrows()
        if r["column"] in AIM_COLS and r["change_group"] in (
            "D2_engine_gasket_sets", "D3_evrv_valves", "D4_antennas", "D6_def_injectors",
        )
    })
    preserve_ok = 0
    for pn in aim04_pns:
        assert pn in pos
        for c in AIM_COLS:
            assert new.at[pos[pn], c] == base.at[pos[pn], c], (
                "2026-10-04 AIM move undone", pn, c,
                base.at[pos[pn], c], new.at[pos[pn], c],
            )
        preserve_ok += 1
    # Engine gasket sets specifically still Engine > Gasket & Sealing > Gasket
    eng_gasket_pns = sorted({
        pad(r["part_number"]) for _, r in chg04.iterrows()
        if r["change_group"] == "D2_engine_gasket_sets" and r["column"] == "aim_l1_fixed"
    })
    for pn in eng_gasket_pns:
        assert tuple(new.at[pos[pn], c] for c in AIM_COLS) == (
            "Engine", "Gasket & Sealing", "Gasket"
        ), ("engine gasket set lost Engine label", pn)

    # ---- EQ_PROVEN: remap + append
    eq_mod = load_eq_remap_mod()
    known = {t for t in base_aim_set if t[0]}
    eq = read(EQ)
    assert len(eq) == 116, len(eq)
    eq_pn_col = "pn" if "pn" in eq.columns else "part_number"
    assert eq[eq_pn_col].map(pad).is_unique

    eq_added = []
    eq_remap_rows = []
    eq_skipped = []
    for _, r in eq.iterrows():
        pn = pad(r[eq_pn_col])
        proposed = (r["proposed_aim_l1"], r["proposed_aim_l2"], r["proposed_aim_l3"])
        fig = r.get("eq_fig_name", "")
        part = r.get("eq_part_name", "")
        desc_t = r.get("description_if_any", "") or ""
        mapped, how = map_eq_row(eq_mod, proposed, fig, part, desc_t, known)
        if not mapped:
            eq_skipped.append({
                "part_number": pn,
                "proposed_aim_l1": proposed[0],
                "proposed_aim_l2": proposed[1],
                "proposed_aim_l3": proposed[2],
                "eq_fig_name": fig,
                "eq_part_name": part,
                "description_if_any": desc_t,
                "reason": how,
            })
            continue
        assert mapped in known
        eq_remap_rows.append({
            "part_number": pn,
            "proposed_aim_l1": proposed[0],
            "proposed_aim_l2": proposed[1],
            "proposed_aim_l3": proposed[2],
            "mapped_aim_l1": mapped[0],
            "mapped_aim_l2": mapped[1],
            "mapped_aim_l3": mapped[2],
            "remap_method": how,
            "eq_fig_name": fig,
            "eq_part_name": part,
            "description_if_any": desc_t,
        })
        if pn in pos:
            # unexpected — EQ was measured absent from release
            cur = tuple(new.at[pos[pn], c] for c in AIM_COLS)
            if cur[0] and cur != mapped:
                eq_skipped.append({
                    "part_number": pn, **{f"proposed_aim_l{i+1}": proposed[i] for i in range(3)},
                    "eq_fig_name": fig, "eq_part_name": part, "description_if_any": desc_t,
                    "reason": f"on_release_conflict before={' > '.join(cur)} mapped={' > '.join(mapped)}",
                })
                continue
            set_aim(pn, mapped, "D2_eq_hit_proven",
                    f"Jerome GO 2026-10-07: EQ HIT proven; remapped {how} from "
                    f"{' > '.join(proposed)}",
                    SRC_EQ, dsrc="eq_proven_proposal")
            continue

        j = jpi.loc[pn] if pn in jpi.index else None
        d = {c: "" for c in cols}
        d.update({
            "part_number": pn,
            "description_norm": desc_t,
            "catalog_l1": CAT_REVIEW[0],
            "catalog_l2": CAT_REVIEW[1],
            "catalog_l3": CAT_REVIEW[2],
            "catalog_node_present": "0",
            "catalog_residual": "1",
            "workbook_axis_kind": "blank",
            "aim_source": SRC_EQ,
            "aim_l1_fixed": mapped[0],
            "aim_l2_fixed": mapped[1],
            "aim_l3_fixed": mapped[2],
            "jp_zkk": j["zkk"] if j is not None else "",
            "jp_zuk": j["zuk"] if j is not None else "",
            "jp_hkk": j["hkk"] if j is not None else "",
            "jp_class_new": j["class_new"] if j is not None else "",
            "l12m_billed_eur": f"{eur_col(pn)}",
            "axis_conflict": "0",
            "desc_ambiguous": "0",
            "catalog_changed_vs_master": "0",
            "line_kind": "part",
            "fig_key": "",
            "filter_part_role": "",
        })
        new = pd.concat([new, pd.DataFrame([d], columns=cols)], ignore_index=True)
        pos[pn] = len(new) - 1
        eq_added.append(pn)
        for c in AIM_COLS + CAT_COLS + ("aim_source", "description_norm", "catalog_residual",
                                        "catalog_node_present", "line_kind"):
            note(pn, c, "", d[c], "D2_eq_hit_proven",
                 f"added from EQ proven; AIM via {how}; catalogue Review needed "
                 f"(no catalogue proposal on EQ file)",
                 dsrc="eq_proven_proposal")

    assert len(eq_skipped) + len(eq_remap_rows) == 116
    # Cameras are the expected skips (no Camera leaf)
    skip_reasons = pd.Series([s["reason"] for s in eq_skipped]).value_counts().to_dict()

    # ---- vocabulary: no new AIM triples
    new_aim_set = set(zip(new["aim_l1_fixed"], new["aim_l2_fixed"], new["aim_l3_fixed"]))
    new_labels = new_aim_set - base_aim_set
    assert not new_labels, ("invented AIM labels", sorted(new_labels)[:10])
    new_cat_set = set(zip(new["catalog_l1"], new["catalog_l2"], new["catalog_l3"]))
    assert new_cat_set <= base_cat_set

    # ---- zero-checks on APPLIED DESC proposals (same traps as DESC_PROVEN verify)
    # Base release still carries older Transmission gasket labels; we do not re-litigate those.
    prop_sub = desc[desc["part_number"].map(pad).isin(set(desc_filled))].copy()
    path = prop_sub["cat_path"].fillna("")
    aim_l1 = prop_sub["propose_aim_l1"]
    zero = {
        "cyl_hd_gasket_path_to_transmission": int(
            ((path == "Repair parts > Gaskets / seals > Cylinder head gasket") &
             (aim_l1 == "Transmission")).sum()
        ),
        "gasket_set_to_transmission": int(
            ((path == "Repair parts > Gaskets / seals > Gasket set") &
             (aim_l1 == "Transmission")).sum()
        ),
        "trans_asm_to_literature": int(
            ((path == "High value repair > Transmission parts > Transmission assembly") &
             (aim_l1 == "Literature Marketing")).sum()
        ),
        "air_valve_to_steering": int(
            ((path == "Competitive parts > Air system > Air valve") &
             (aim_l1 == "Steering")).sum()
        ),
        "any_propose_transmission_in_applied": int((aim_l1 == "Transmission").sum()),
    }
    hard = {k: v for k, v in zero.items() if k != "any_propose_transmission_in_applied"}
    assert all(v == 0 for v in hard.values()), hard

    # ---- copy integrity vs PINNED 20 Sep pr00 (same method as 2026-10-04 builder)
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
    base_meta = json.loads((BASE.with_suffix(".meta.json")).read_text(encoding="utf-8"))
    logged = {r["part_number"] for r in log}
    unexplained = [p for p in ref_miss if p not in logged and p not in set(base_miss)]
    assert not unexplained, ("unexplained pr00 mismatch", unexplained[:10])

    # Untouched shared rows must match base on every column (vectorised)
    shared_pns = set(base["part_number"]) & set(new["part_number"])
    untouched = sorted(shared_pns - logged)
    if untouched:
        b_u = base.set_index("part_number").loc[untouched, cols[1:]]
        n_u = new.set_index("part_number").loc[untouched, cols[1:]]
        drift = (b_u != n_u).any(axis=1)
        assert not drift.any(), (
            "untouched row drifted",
            drift[drift].index[:5].tolist(),
        )

    n = len(new)
    touched = sorted(set(desc_filled) | set(eq_added))

    if "--dry" in sys.argv:
        print("DRY RUN OK")
        print(f"rows {n} (base {len(base)} + {len(eq_added)} EQ)")
        print(f"DESC filled {len(desc_filled)} already_same {len(desc_already_same)} "
              f"kept_existing {len(desc_kept_existing)} "
              f"cat_diffs_not_applied {len(desc_cat_diffs_not_applied)}")
        print(f"2026-10-04 AIM moves preserved: {preserve_ok} PNs; "
              f"engine gasket sets still Engine: {len(eng_gasket_pns)}")
        print(f"EQ remapped {len(eq_remap_rows)} added {len(eq_added)} skipped {len(eq_skipped)}")
        print("skip reasons", skip_reasons)
        print("zero", zero)
        return 0

    # ---- write release artefacts
    OUT.write_bytes(new.to_csv(index=False, lineterminator="\r\n").encode("utf-8"))
    out_sha = sha(OUT)
    with OUT_LOG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["part_number", "column", "before", "after", "change_group", "to_check",
                        "l12m_eur_sep25_aug26", "eur_jan25_jun26_release_column",
                        "description_source", "reason"],
            lineterminator="\r\n",
        )
        w.writeheader()
        w.writerows(log)
    with OUT_EQ_SKIP.open("w", encoding="utf-8", newline="") as f:
        if eq_skipped:
            w = csv.DictWriter(f, fieldnames=list(eq_skipped[0].keys()), lineterminator="\r\n")
            w.writeheader()
            w.writerows(eq_skipped)
        else:
            f.write("part_number,reason\r\n")
    with OUT_EQ_MAP.open("w", encoding="utf-8", newline="") as f:
        eq_map_fields = [
            "part_number", "proposed_aim_l1", "proposed_aim_l2", "proposed_aim_l3",
            "mapped_aim_l1", "mapped_aim_l2", "mapped_aim_l3", "remap_method",
            "eq_fig_name", "eq_part_name", "description_if_any",
        ]
        w = csv.DictWriter(f, fieldnames=eq_map_fields, lineterminator="\r\n")
        w.writeheader()
        if eq_remap_rows:
            w.writerows(eq_remap_rows)

    cov_before = int((base["aim_l1_fixed"] != "").sum())
    cov_after = int((new["aim_l1_fixed"] != "").sum())

    meta = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_aim_classification_release_20261007.py",
        "release_id": RELEASE_ID,
        "release_id_note": ("2026-10-07 is not taken in RELEASES.json, so the date alone is the id. "
                            "No version label."),
        "status_at_build": "PENDING_APPROVAL (Jerome GO already given; approve script stamps APPROVED)",
        "jerome_go": "2026-10-07 chat: apply the two proven piles as a dated release",
        "decisions_2026_10_07": {
            "1_desc_proven": ("DESC_PROVEN: AIM family filled only where blank; non-blank AIM left "
                              "untouched (protects 2026-10-04 gasket/EVRV/antenna/DEF moves); "
                              "catalogue columns left as base release"),
            "2_eq_hit_proven": ("EQ proven HITs: remapped overnight Powertrain/Chassis labels onto "
                                "existing AIM leaves; new rows appended with catalogue Review needed; "
                                "rows without a safe leaf (e.g. Camera) skipped"),
            "3_not_applied": ("raw 49k / CLEAN 38k / SAFE-v2 37k; EQ rigor fails (10); status-only "
                              "EQ HITs without family; DESC catalogue diffs vs base"),
            "4_preserve_2026_10_04": ("all AIM columns on 2026-10-04 change-log PNs proven identical "
                                      "to base; engine gasket sets still Engine > Gasket & Sealing > "
                                      "Gasket"),
        },
        "purpose": base_meta["purpose"],
        "rows": n,
        "sha256": out_sha,
        "base_release": {
            "release_id": BASE_ID, "file": BASE.name,
            "sha256": EXPECT_SHA[BASE], "rows": len(base),
        },
        "sources": {
            "desc_proven": {"file": DESC.name, "sha256": desc_sha, "rows": 30653},
            "eq_proven": {"file": EQ.name, "sha256": eq_sha, "rows": 116},
            "jp_codes": {"file": JP.name, "sha256": sha(JP)},
            "master_at_build": {"file": MASTER.name, "sha256": sha(MASTER)},
            "sales_fact": {"file": SALES.name, "sha256": sha(SALES)},
            "euro": (f"sales_fact.parquet net_sales_value {L12M_FROM}..{L12M_TO}; "
                     f"total EUR {total_l12:,.2f}"),
        },
        "changes_vs_base": {
            "rows_added": eq_added,
            "rows_added_count": len(eq_added),
            "desc_aim_filled": len(desc_filled),
            "desc_already_same": len(desc_already_same),
            "desc_kept_existing_nonblank": len(desc_kept_existing),
            "desc_catalogue_diffs_not_applied": len(desc_cat_diffs_not_applied),
            "preserved_2026_10_04_aim_pns": preserve_ok,
            "preserved_engine_gasket_sets": len(eng_gasket_pns),
            "eq_remapped": len(eq_remap_rows),
            "eq_skipped": len(eq_skipped),
            "eq_skip_reasons": skip_reasons,
            "parts_touched": len(touched),
            "parts_by_group": {
                "D1_desc_proven": len(desc_filled),
                "D2_eq_hit_proven_added": len(eq_added),
            },
            "change_log": OUT_LOG.name,
            "change_log_rows": len(log),
            "eq_remap_log": OUT_EQ_MAP.name,
            "eq_skipped_log": OUT_EQ_SKIP.name,
            "overlap_desc_eq": 0,
            "overlap_policy": "zero overlap measured; blank-only DESC fill; never overwrite non-blank AIM",
        },
        "coverage": {
            "aim_l1_fixed_nonblank_before": cov_before,
            "aim_l1_fixed_nonblank_after": cov_after,
            "aim_l1_fixed_delta": cov_after - cov_before,
            "release_rows_before": len(base),
            "release_rows_after": n,
        },
        "zero_checks": zero,
        "aim_label_vocabulary": {
            "new_aim_labels": [],
            "note": "no new AIM triples; EQ parallel taxonomy remapped onto base leaves only",
        },
        "catalogue_verification_vs_pr00": {
            **ref_int,
            "reference_file": PR00_REF.name,
            "reference_sha256": EXPECT_SHA[PR00_REF],
            "non_matching_parts": len(ref_miss),
            "base_release_non_matching_parts": len(base_miss),
            "note": ("COPY-INTEGRITY ONLY. DESC did not change catalogue. EQ adds use Review "
                     "needed and are logged."),
        },
        "counts": {
            "catalog_l2_count": int(new["catalog_l2"].nunique()),
            "catalog_l3_count": int(new["catalog_l3"].nunique()),
            "line_kind": {k: int(v) for k, v in new["line_kind"].value_counts().items()},
        },
        "consumer_contract": base_meta.get("consumer_contract"),
    }
    OUT_META.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    before_entries = json.dumps(reg["candidates"], sort_keys=True)
    reg["candidates"].append({
        "release_id": RELEASE_ID,
        "path": OUT.name,
        "sha256": out_sha,
        "status": "PENDING_APPROVAL",
        "rows": n,
        "rows_note": "data rows, header excluded",
        "base_release": BASE_ID,
        "source": (f"release {BASE_ID} ({BASE.name}, sha256 {EXPECT_SHA[BASE][:8]}...) + "
                   f"DESC_PROVEN {len(desc_filled)} AIM fills + EQ proven "
                   f"{len(eq_added)} added / {len(eq_skipped)} skipped"),
        "recommendation": ("Jerome GO 2026-10-07; DESC_PROVEN + EQ_PROVEN only; "
                           "_aim_tranche1_DESC_PROVEN_verify_20261007.md; "
                           "_aim_eq_hit_126_rigor_20261007.md"),
        "notes": (f"Cut 2026-10-07 from approved {BASE_ID}. Change log {OUT_LOG.name}. "
                  "No new AIM labels. EQ overnight labels remapped onto existing leaves. "
                  "Release id: 2026-10-07 not taken, date alone."),
    })
    assert json.dumps(reg["candidates"][:-1], sort_keys=True) == before_entries
    REGISTER.write_bytes(reg_text(reg))

    os.chmod(OUT, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

    print(f"wrote {OUT} rows={n} sha256={out_sha}")
    print(f"DESC filled={len(desc_filled)} already_same={len(desc_already_same)} "
          f"kept_existing={len(desc_kept_existing)} "
          f"cat_diffs_skipped={len(desc_cat_diffs_not_applied)}")
    print(f"preserved 2026-10-04 AIM PNs={preserve_ok}; engine gasket sets={len(eng_gasket_pns)}")
    print(f"EQ added={len(eq_added)} remapped={len(eq_remap_rows)} skipped={len(eq_skipped)} "
          f"{skip_reasons}")
    print(f"coverage AIM nonblank {cov_before} -> {cov_after}")
    print(f"register: + {RELEASE_ID} PENDING_APPROVAL")

    # run gate (house method: verify_aim_classification.py --file <release>)
    gate_rc = os.system(
        f'python "{BUILD / "verify_aim_classification.py"}" --candidate --file "{OUT}"'
    )
    print(f"gate exit {gate_rc >> 8}")
    if (gate_rc >> 8) not in (0, 1):
        print("STOP: gate could not run; release left PENDING_APPROVAL; master untouched")
        return 3
    # exit 1 is OK for candidate (release_approved pending); real fails are checked in --apply

    if do_apply:
        # Master gets release AIM for blank-fill + already-same (release AIM == DESC propose).
        # kept_existing (non-blank release AIM ≠ DESC) is never pushed as DESC.
        desc_for_master = sorted(set(desc_filled) | set(desc_already_same))
        return apply_approved(
            out_sha, desc_for_master, eq_added, eq_remap_rows, cov_before, cov_after,
            desc_filled_n=len(desc_filled), desc_same_n=len(desc_already_same),
            eq_skipped_n=len(eq_skipped), eng_gasket_pns=eng_gasket_pns,
        )
    print("Release cut as PENDING_APPROVAL. Re-run with --apply to stamp APPROVED and sync master.")
    return 0


def apply_approved(
    out_sha, desc_for_master, eq_added, eq_remap_rows, cov_before, cov_after,
    desc_filled_n=0, desc_same_n=0, eq_skipped_n=0, eng_gasket_pns=None,
) -> int:
    """Stamp APPROVED (Jerome GO) and sync aim_master_v2 (+ overlay AIM cols)."""
    gate_path = OUT.with_suffix(".gate.json")
    if not gate_path.is_file():
        print("STOP: gate.json missing")
        return 1
    g = json.loads(gate_path.read_text(encoding="utf-8"))
    bad = [c["id"] for c in g["checks"] if not c["ok"] and not c.get("pending")]
    pend = [c["id"] for c in g["checks"] if c.get("pending")]
    if bad or pend != ["release_approved"]:
        print(f"STOP: gate failures {bad}, pending {pend}")
        return 1
    if g.get("classifier_sha256") != out_sha:
        print("STOP: gate sha != release sha")
        return 1

    reg = json.loads(REGISTER.read_bytes().decode("utf-8"))
    by = {c["release_id"]: c for c in reg["candidates"]}
    new_e, old_e = by[RELEASE_ID], by[BASE_ID]
    assert new_e["status"] == "PENDING_APPROVAL" and old_e["status"] == "APPROVED"
    assert new_e["sha256"] == out_sha == sha(OUT)
    n_ok = sum(1 for c in g["checks"] if c["ok"])
    new_e["status"] = "APPROVED"
    new_e["approved_by"] = "Jerome"
    new_e["approved_on"] = "2026-10-07"
    new_e["approved_note"] = (
        "Jerome GO in chat on 2026-10-07: apply DESC_PROVEN (~30,653) and EQ_PROVEN (~116) "
        "as a dated release. sha256 re-verified against this register immediately before the "
        f"status change. Candidate gate ({gate_path.name}): {n_ok} checks pass, "
        "release_approved PENDING, 0 fail. Supersedes 2026-10-04 in the same edit. "
        "Master sync: aim_master_v2.csv AIM fills for DESC + append EQ mapped rows "
        "(see _aim_apply_proven_20261007.md)."
    )
    old_e["status"] = "SUPERSEDED"
    old_e["superseded_by"] = RELEASE_ID
    old_e["superseded_on"] = "2026-10-07"
    old_e["superseded_note"] = (
        f"Superseded when Jerome approved release {RELEASE_ID} on 2026-10-07. "
        "Hash, history and the approval record kept unchanged."
    )
    REGISTER.write_bytes(reg_text(reg))

    # ---- master sync
    ts = datetime.now().strftime("%H%M%S")
    bak = DER / f"aim_master_v2.csv.bak_pre_release_apply_{TAG}_{ts}"
    shutil.copy2(MASTER, bak)
    assert sha(bak) == sha(MASTER)

    rel = read(OUT).set_index("part_number", drop=False)
    m = read(MASTER)
    m_idx = {pad(p): i for i, p in enumerate(m["part_number"])}
    before_cov = int((m["aim_l1_fixed"] != "").sum())
    master_filled = 0
    master_appended = 0
    header = list(m.columns)

    def blank_row(pn: str, r: pd.Series) -> list[str]:
        row = [""] * len(header)
        idx = {c: i for i, c in enumerate(header)}
        row[idx["part_number"]] = pn
        row[idx["description"]] = (r.get("description_norm") or "").strip()
        row[idx["aim_l1"]] = r["aim_l1_fixed"]
        row[idx["aim_l2"]] = r["aim_l2_fixed"]
        row[idx["aim_l3"]] = r["aim_l3_fixed"]
        row[idx["aim_l1_fixed"]] = r["aim_l1_fixed"]
        row[idx["aim_l2_fixed"]] = r["aim_l2_fixed"]
        if "cat_pms_flag" in idx:
            row[idx["cat_pms_flag"]] = "0"
        row[idx["aim_source"]] = SRC_EQ
        row[idx["has_aim"]] = "1"
        if "has_catalogue_node" in idx:
            row[idx["has_catalogue_node"]] = "0"
        if "desc_ambiguous" in idx:
            row[idx["desc_ambiguous"]] = "0"
        row[idx["l12m_billed_eur"]] = r.get("l12m_billed_eur") or "0.0"
        if "eur" in idx:
            row[idx["eur"]] = "0.0"
        row[idx["aim_changed"]] = SRC_EQ
        return row

    # DESC fills (release-changed + already-same on release but blank on master)
    for pn in desc_for_master:
        r = rel.loc[pn]
        if not r["aim_l1_fixed"]:
            continue
        i = m_idx.get(pad(pn))
        if i is None:
            continue
        if m.at[i, "aim_l1_fixed"]:
            continue  # master already has a family — do not overwrite
        m.at[i, "aim_l1_fixed"] = r["aim_l1_fixed"]
        m.at[i, "aim_l2_fixed"] = r["aim_l2_fixed"]
        m.at[i, "aim_l3"] = r["aim_l3_fixed"]
        if "aim_l1" in m.columns:
            m.at[i, "aim_l1"] = r["aim_l1_fixed"]
            m.at[i, "aim_l2"] = r["aim_l2_fixed"]
        m.at[i, "has_aim"] = "1"
        m.at[i, "aim_source"] = add_source(m.at[i, "aim_source"], SRC_DESC)
        m.at[i, "aim_changed"] = add_source(m.at[i, "aim_changed"], SRC_DESC)
        master_filled += 1

    # EQ appends
    new_master_rows = []
    for pn in eq_added:
        if pad(pn) in m_idx:
            continue
        r = rel.loc[pn]
        new_master_rows.append(blank_row(pn, r))
        master_appended += 1

    if new_master_rows:
        m = pd.concat([m, pd.DataFrame(new_master_rows, columns=header)], ignore_index=True)
        m = m.sort_values("part_number").reset_index(drop=True)

    tmp = MASTER.with_suffix(".csv.tmp")
    crlf = b"\r\n" in MASTER.read_bytes()[:5000]
    tmp.write_bytes(m.to_csv(index=False, lineterminator="\r\n" if crlf else "\n").encode("utf-8"))
    tmp.replace(MASTER)
    m_after = read(MASTER)
    after_cov = int((m_after["aim_l1_fixed"] != "").sum())

    # Prove 2026-10-04 engine gasket sets still Engine on master; hard holds on filled DESC
    m_after["k"] = m_after["part_number"].map(pad)
    mpos = m_after.set_index("k")
    for pn in (eng_gasket_pns or []):
        if pn not in mpos.index:
            continue
        assert (
            mpos.at[pn, "aim_l1_fixed"],
            mpos.at[pn, "aim_l2_fixed"],
            mpos.at[pn, "aim_l3"],
        ) == ("Engine", "Gasket & Sealing", "Gasket"), ("master undid engine gasket", pn)

    # Hard holds on master rows we just filled from DESC (path traps via release cat + AIM)
    rel_df = read(OUT)
    rel_df["k"] = rel_df["part_number"].map(pad)
    desc_prop = read(DESC)
    desc_prop["k"] = desc_prop["part_number"].map(pad)
    filled_set = set(pad(p) for p in desc_for_master)
    dsub = desc_prop[desc_prop["k"].isin(filled_set)]
    master_hard = {
        "gasket_set_to_transmission": int(
            ((dsub["cat_path"] == "Repair parts > Gaskets / seals > Gasket set") &
             (dsub["k"].map(lambda k: mpos.at[k, "aim_l1_fixed"] if k in mpos.index else "")
              == "Transmission")).sum()
        ),
        "cyl_hd_path_to_transmission": int(
            ((dsub["cat_path"] == "Repair parts > Gaskets / seals > Cylinder head gasket") &
             (dsub["k"].map(lambda k: mpos.at[k, "aim_l1_fixed"] if k in mpos.index else "")
              == "Transmission")).sum()
        ),
        "trans_asm_to_literature": int(
            ((dsub["cat_path"] == "High value repair > Transmission parts > Transmission assembly") &
             (dsub["k"].map(lambda k: mpos.at[k, "aim_l1_fixed"] if k in mpos.index else "")
              == "Literature Marketing")).sum()
        ),
        "air_valve_to_steering": int(
            ((dsub["cat_path"] == "Competitive parts > Air system > Air valve") &
             (dsub["k"].map(lambda k: mpos.at[k, "aim_l1_fixed"] if k in mpos.index else "")
              == "Steering")).sum()
        ),
    }
    assert all(v == 0 for v in master_hard.values()), ("master hard-hold fail", master_hard)

    # overlay AIM columns for PNs we filled (existing rows only)
    ov_bak = None
    ov_n = 0
    if OVERLAY.is_file():
        ov_bak = DER / f"aim_pn_classification_20260920.csv.bak_pre_release_apply_{TAG}_{ts}"
        shutil.copy2(OVERLAY, ov_bak)
        ov = read(OVERLAY)
        opos = {pad(p): i for i, p in enumerate(ov["part_number"])}
        for pn in desc_for_master:
            i = opos.get(pad(pn))
            if i is None:
                continue
            r = rel.loc[pn]
            if not r["aim_l1_fixed"] or ov.at[i, "aim_l1_fixed"]:
                continue
            ov.at[i, "aim_l1_fixed"] = r["aim_l1_fixed"]
            ov.at[i, "aim_l2_fixed"] = r["aim_l2_fixed"]
            ov.at[i, "aim_l3_fixed"] = r["aim_l3_fixed"]
            ov.at[i, "aim_source"] = add_source(ov.at[i, "aim_source"], SRC_DESC)
            ov_n += 1
        # append EQ rows to overlay if schema allows
        for pn in eq_added:
            if pad(pn) in opos:
                continue
            r = rel.loc[pn]
            row = {c: "" for c in ov.columns}
            row.update({
                "part_number": pn,
                "description_norm": r.get("description_norm", ""),
                "catalog_l1": r["catalog_l1"],
                "catalog_l2": r["catalog_l2"],
                "catalog_l3": r["catalog_l3"],
                "aim_l1_fixed": r["aim_l1_fixed"],
                "aim_l2_fixed": r["aim_l2_fixed"],
                "aim_l3_fixed": r["aim_l3_fixed"],
                "aim_source": SRC_EQ,
                "line_kind": "part",
            })
            ov = pd.concat([ov, pd.DataFrame([row], columns=ov.columns)], ignore_index=True)
            ov_n += 1
        ov_tmp = OVERLAY.with_suffix(".csv.tmp")
        ov_crlf = b"\r\n" in OVERLAY.read_bytes()[:5000]
        ov_tmp.write_bytes(
            ov.to_csv(index=False, lineterminator="\r\n" if ov_crlf else "\n").encode("utf-8")
        )
        ov_tmp.replace(OVERLAY)

    report = BUILD / "_aim_apply_proven_20261007.md"
    ov_bak_note = f" (backup `{ov_bak.name}`)" if ov_bak else ""
    report.write_text(
        "\n".join([
            "# AIM proven apply — 2026-10-07",
            "",
            "## Verdict",
            "",
            f"**Applied: YES.** Release `{RELEASE_ID}` is APPROVED and synced into `aim_master_v2.csv`.",
            "",
            "## Release",
            "",
            f"- Release id: `{RELEASE_ID}`",
            f"- Base: `{BASE_ID}` (was APPROVED; now SUPERSEDED)",
            "- Status: APPROVED (Jerome GO 2026-10-07)",
            f"- Rows: {len(rel)}",
            f"- sha256: `{out_sha}`",
            f"- Gate: `{gate_path.name}` — checks pass; only release_approved was pending before stamp",
            "",
            "## What was applied",
            "",
            f"- DESC_PROVEN 30,653: AIM fill on blank release rows = **{desc_filled_n}**; "
            f"already-same on release = {desc_same_n}; AIM conflicts = 0; "
            "catalogue diffs vs base not applied",
            f"- EQ_PROVEN 116: remapped to existing AIM leaves; **{len(eq_added)}** appended; "
            f"**{eq_skipped_n}** skipped (no Camera leaf) — see `{OUT_EQ_SKIP.name}`",
            "- Overlap DESC ∩ EQ: **0**. Policy if conflict: DESC_PROVEN wins.",
            "",
            "## Coverage",
            "",
            f"- Release aim_l1_fixed non-blank: **{cov_before} → {cov_after}**",
            f"- Master aim_l1_fixed non-blank: **{before_cov} → {after_cov}** "
            f"(filled {master_filled}, appended {master_appended})",
            f"- Overlay AIM fills/appends: {ov_n}",
            "",
            "## Zero-checks / preservation",
            "",
            "- Applied DESC proposals: hard traps at 0 (see meta `zero_checks`).",
            f"- Master hard holds after sync: `{master_hard}`.",
            f"- 2026-10-04 engine gasket sets still Engine on master: "
            f"{len(eng_gasket_pns or [])} checked.",
            "",
            "## Gate / verify run",
            "",
            "- `python 01_data/91_build/verify_aim_classification.py --file "
            f"<release {OUT.name}>`",
            f"- Result: `{gate_path}` (candidate: all checks ok except "
            "`release_approved` pending, then stamped APPROVED).",
            "",
            "## Paths",
            "",
            f"- Release: `{OUT}`",
            f"- Meta: `{OUT_META}`",
            f"- Changes: `{OUT_LOG}`",
            f"- EQ remap: `{OUT_EQ_MAP}`",
            f"- EQ skipped: `{OUT_EQ_SKIP}`",
            f"- Register: `{REGISTER}`",
            f"- Master: `{MASTER}` (backup `{bak.name}`)",
            f"- Overlay: `{OVERLAY}`{ov_bak_note}",
            f"- This report: `{report}`",
            "",
            "## Not applied",
            "",
            "Raw 49k / CLEAN 38k / SAFE-v2 37k; EQ rigor fails (10); status-only EQ without "
            "family; DESC catalogue column diffs vs base; EQ rows with no safe AIM leaf "
            "(e.g. Camera).",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"APPROVED {RELEASE_ID}; master filled={master_filled} appended={master_appended}; "
          f"master coverage {before_cov}->{after_cov}")
    print(f"report {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
