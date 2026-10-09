"""Shard B — live-order AIM priority queue (proposal only, no apply).

Confirms why backlog AIM coverage > warehouse, then writes a distinct-PN
classify queue for warehouse/backlog parts that lack a real AIM family.

Does NOT collide with Shard A catalogue tranche or rebuild the backlog HTML.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
WAREHOUSE = ISZE / "01_data" / "ISZE_Order Status as of 2 October 2026_request to check.xlsx"
BACKLOG = (
    ISZE
    / "01_data"
    / "90_INBOX"
    / "_natalie_bo_wk41_20261007"
    / "2026-10-06_1147_Natalie_BO info VP 06-10-2026.xlsx"
)
MASTER = DER / "aim_master_v2.csv"
FACT = DER / "sales_fact.parquet"
OUT_CSV = REL / "next_release_proposal_live_order_unclassified_2026-10-07.csv"
OUT_SUM = REL / "next_release_proposal_live_order_unclassified_2026-10-07.summary.json"

EXCLUDE = ("MIDI", "RUS", "KAZ", "CBC-TRANS", "GRAND AVTO", "KOMTRANS", "KIMA")
MARKERS = {"", "Unknown", "Unknown Review", "nan", "None"}


def norm(v) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", str(v if v is not None else ""))


def clean(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip()


def resolved_family(fixed: str, l1: str) -> str:
    for c in (clean(fixed), clean(l1)):
        if c and c not in MARKERS:
            return c
    return ""


def match_keys(pn: str) -> set[str]:
    p = norm(pn)
    if not p:
        return set()
    nz = p.lstrip("0") or "0"
    return {p, nz}


def main() -> None:
    # ---- AIM master ----
    aim = pd.read_csv(MASTER, dtype=str, low_memory=False)
    aim["pn"] = aim["part_number"].fillna("").map(norm)
    aim["pn_nz"] = aim["pn"].str.lstrip("0").replace("", "0")
    aim["family"] = [
        resolved_family(f, l) for f, l in zip(aim["aim_l1_fixed"], aim["aim_l1"])
    ]
    for c in ("cat_l1", "cat_l2", "cat_l3", "description"):
        if c not in aim.columns:
            aim[c] = ""
    aim["cat_path"] = (
        aim["cat_l1"].map(clean)
        + " > "
        + aim["cat_l2"].map(clean)
        + " > "
        + aim["cat_l3"].map(clean)
    )
    aim["has_cat"] = ~(
        (aim["cat_l1"].map(clean) == "")
        & (aim["cat_l2"].map(clean) == "")
        & (aim["cat_l3"].map(clean) == "")
    )
    # Index by both forms for lookup
    aim_by_key: dict[str, dict] = {}
    for _, r in aim.iterrows():
        row = {
            "on_master": True,
            "family": r["family"],
            "aim_l1": clean(r["aim_l1"]),
            "aim_l1_fixed": clean(r["aim_l1_fixed"]),
            "cat_l1": clean(r["cat_l1"]),
            "cat_l2": clean(r["cat_l2"]),
            "cat_l3": clean(r["cat_l3"]),
            "cat_path": r["cat_path"],
            "has_cat": bool(r["has_cat"]),
            "description": clean(r["description"]),
        }
        for k in match_keys(r["pn"]):
            # Prefer row that already has a family if collision
            prev = aim_by_key.get(k)
            if prev is None or (not prev["family"] and row["family"]):
                aim_by_key[k] = row

    # Cat-path -> family map (same bar as Shard A tranche1: >=90%, n>=5)
    known = aim[aim["family"] != ""].copy()
    cat_maps: dict[str, tuple[str, float, int]] = {}
    for cat_path, g in known.groupby("cat_path"):
        if len(g) < 5:
            continue
        vc = g["family"].value_counts()
        share = float(vc.iloc[0] / len(g))
        if share < 0.90:
            continue
        cat_maps[cat_path] = (vc.index[0], share, int(len(g)))

    # ---- billed history ----
    fact = pd.read_parquet(FACT, columns=["part_number"])
    fact["pn"] = fact["part_number"].map(norm)
    billed_keys: set[str] = set()
    for p in fact["pn"].dropna().unique():
        billed_keys |= match_keys(p)

    # ---- warehouse ----
    dly = pd.read_excel(WAREHOUSE, sheet_name="isze", dtype=str)
    dly["pn"] = dly["PN"].map(norm)
    dly = dly[dly["pn"] != ""].copy()
    dly["pn_nz"] = dly["pn"].str.lstrip("0").replace("", "0")
    dly["desc"] = dly["Part Name"].fillna("").str.strip()
    dly["qty"] = pd.to_numeric(dly["Q'ty"], errors="coerce").fillna(0)
    dly["family"] = dly["pn"].map(
        lambda p: next(
            (aim_by_key[k]["family"] for k in match_keys(p) if k in aim_by_key and aim_by_key[k]["family"]),
            "",
        )
    )
    dly["has_aim"] = dly["family"] != ""

    # ---- backlog (scope = backlog page) ----
    data = pd.read_excel(BACKLOG, sheet_name="DATA", header=3, dtype=str)
    data = data[data["Material"].notna()].copy()
    data["pn"] = data["Material"].map(norm)
    data = data[data["pn"] != ""].copy()
    data["pn_nz"] = data["pn"].str.lstrip("0").replace("", "0")
    data["desc"] = data["Material description"].fillna("").str.strip()
    data["qty"] = pd.to_numeric(data["Open Qty"], errors="coerce").fillna(0)
    up = data["Customer"].fillna("").str.upper()
    excl = "|".join(EXCLUDE)
    data = data[~up.str.contains(excl, regex=True)].copy()
    data["family"] = data["pn"].map(
        lambda p: next(
            (aim_by_key[k]["family"] for k in match_keys(p) if k in aim_by_key and aim_by_key[k]["family"]),
            "",
        )
    )
    data["has_aim"] = data["family"] != ""

    # ========== FINDING 1 & 2: mechanism ==========
    wh_lines = len(dly)
    wh_aim_lines = int(dly["has_aim"].sum())
    wh_line_cov = wh_aim_lines / wh_lines if wh_lines else 0
    bo_lines = len(data)
    bo_aim_lines = int(data["has_aim"].sum())
    bo_line_cov = bo_aim_lines / bo_lines if bo_lines else 0

    wh_u = dly.drop_duplicates("pn_nz")
    bo_u = data.drop_duplicates("pn_nz")
    wh_pn_cov = float(wh_u["has_aim"].mean()) if len(wh_u) else 0
    bo_pn_cov = float(bo_u["has_aim"].mean()) if len(bo_u) else 0

    # Mix: lines per distinct PN (classified vs not)
    wh_lpp_yes = float(dly[dly.has_aim].groupby("pn_nz").size().mean()) if dly.has_aim.any() else 0
    wh_lpp_no = float(dly[~dly.has_aim].groupby("pn_nz").size().mean()) if (~dly.has_aim).any() else 0
    bo_lpp_yes = float(data[data.has_aim].groupby("pn_nz").size().mean()) if data.has_aim.any() else 0
    bo_lpp_no = float(data[~data.has_aim].groupby("pn_nz").size().mean()) if (~data.has_aim).any() else 0

    # Ever billed among warehouse distinct PNs (all / miss)
    def ever_billed_flag(pn: str) -> bool:
        return bool(match_keys(pn) & billed_keys)

    wh_u = wh_u.copy()
    wh_u["ever_billed"] = wh_u["pn"].map(ever_billed_flag)
    wh_miss = wh_u[~wh_u["has_aim"]]
    wh_all_never = int((~wh_u["ever_billed"]).sum())
    wh_miss_never = int((~wh_miss["ever_billed"]).sum())
    wh_all_n = len(wh_u)
    wh_miss_n = len(wh_miss)
    # "~1 in 5 warehouse distinct PNs never invoiced"
    never_share_all = wh_all_never / wh_all_n if wh_all_n else 0
    never_share_miss = wh_miss_never / wh_miss_n if wh_miss_n else 0

    # Overlap: how much of backlog PNs also sit on warehouse
    wh_set = set(wh_u["pn_nz"])
    bo_set = set(bo_u["pn_nz"])
    both = wh_set & bo_set
    bo_only = bo_set - wh_set
    wh_only = wh_set - bo_set

    # Among shared PNs, coverage should be similar if mix drives it
    shared_wh = wh_u[wh_u["pn_nz"].isin(both)]
    shared_bo = bo_u[bo_u["pn_nz"].isin(both)]

    finding = {
        "warehouse_line_aim_pct": round(100 * wh_line_cov, 1),
        "backlog_line_aim_pct": round(100 * bo_line_cov, 1),
        "warehouse_distinct_pn_aim_pct": round(100 * wh_pn_cov, 1),
        "backlog_distinct_pn_aim_pct": round(100 * bo_pn_cov, 1),
        "warehouse_lines": wh_lines,
        "backlog_lines": bo_lines,
        "warehouse_distinct_pns": wh_all_n,
        "backlog_distinct_pns": len(bo_u),
        "warehouse_lines_per_pn_classified": round(wh_lpp_yes, 2),
        "warehouse_lines_per_pn_unclassified": round(wh_lpp_no, 2),
        "backlog_lines_per_pn_classified": round(bo_lpp_yes, 2),
        "backlog_lines_per_pn_unclassified": round(bo_lpp_no, 2),
        "warehouse_never_billed_distinct": wh_all_never,
        "warehouse_never_billed_share": round(never_share_all, 4),
        "warehouse_unclassified_never_billed": wh_miss_never,
        "warehouse_unclassified_never_billed_share": round(never_share_miss, 4),
        "pn_overlap_both": len(both),
        "pn_warehouse_only": len(wh_only),
        "pn_backlog_only": len(bo_only),
        "shared_pn_warehouse_aim_pct": round(100 * float(shared_wh["has_aim"].mean()), 1) if len(shared_wh) else None,
        "shared_pn_backlog_aim_pct": round(100 * float(shared_bo["has_aim"].mean()), 1) if len(shared_bo) else None,
    }

    # Verdicts
    # F1: backlog higher because current sellable mix; warehouse weighted to slow/one-off
    f1_confirm = (
        bo_line_cov > wh_line_cov
        and len(wh_only) > len(bo_only)  # warehouse has more unique/slow stock
        and (wh_lpp_no <= wh_lpp_yes or never_share_miss > 0.15)
    )
    # F2: ~1 in 5 warehouse distinct PNs never invoiced
    f2_confirm = 0.15 <= never_share_all <= 0.30  # "about 1 in 5" band
    f2_note = (
        f"{wh_all_never} of {wh_all_n} warehouse distinct PNs never billed "
        f"({100*never_share_all:.1f}%, ~1 in {round(1/never_share_all) if never_share_all else 'n/a'})"
    )

    # ========== PRIORITY QUEUE ==========
    # Aggregate miss lines from each source by pn_nz
    def agg_source(df: pd.DataFrame, label: str) -> pd.DataFrame:
        miss = df[~df["has_aim"]].copy()
        if miss.empty:
            return pd.DataFrame(columns=["pn_nz", "pn", "description", f"lines_{label}", f"pcs_{label}"])
        # Prefer longest original pn form; best non-empty description
        g = (
            miss.groupby("pn_nz", as_index=False)
            .agg(
                pn=("pn", lambda s: max(s, key=len)),
                description=("desc", lambda s: next((x for x in s if x), "")),
                lines=( "pn", "size"),
                pcs=("qty", "sum"),
            )
        )
        g = g.rename(columns={"lines": f"lines_{label}", "pcs": f"pcs_{label}"})
        return g

    def pick(a, b):
        if pd.notna(a) and str(a).strip():
            return a
        return b if pd.notna(b) else ""

    wh_m2 = agg_source(dly, "warehouse").rename(
        columns={"pn": "pn_wh", "description": "desc_wh"}
    )
    bo_m2 = agg_source(data, "backlog").rename(
        columns={"pn": "pn_bo", "description": "desc_bo"}
    )
    q = wh_m2.merge(bo_m2, on="pn_nz", how="outer")
    q["pn"] = [pick(a, b) for a, b in zip(q["pn_wh"], q["pn_bo"])]
    q["description"] = [pick(a, b) for a, b in zip(q["desc_wh"], q["desc_bo"])]
    q["lines_warehouse"] = q["lines_warehouse"].fillna(0).astype(int)
    q["lines_backlog"] = q["lines_backlog"].fillna(0).astype(int)
    q["pcs_warehouse"] = q["pcs_warehouse"].fillna(0.0)
    q["pcs_backlog"] = q["pcs_backlog"].fillna(0.0)
    q["lines"] = q["lines_warehouse"] + q["lines_backlog"]

    def source_label(r) -> str:
        w = r["lines_warehouse"] > 0
        b = r["lines_backlog"] > 0
        if w and b:
            return "both"
        if w:
            return "warehouse"
        return "backlog"

    q["source"] = q.apply(source_label, axis=1)
    q["ever_billed"] = q["pn"].map(ever_billed_flag)

    def lookup(pn: str) -> dict:
        for k in match_keys(pn):
            if k in aim_by_key:
                return aim_by_key[k]
        return {
            "on_master": False,
            "family": "",
            "aim_l1": "",
            "aim_l1_fixed": "",
            "cat_l1": "",
            "cat_l2": "",
            "cat_l3": "",
            "cat_path": "",
            "has_cat": False,
            "description": "",
        }

    meta = q["pn"].map(lookup)
    q["on_master"] = meta.map(lambda d: d["on_master"])
    q["aim_l1"] = meta.map(lambda d: d["aim_l1"])
    q["aim_l1_fixed"] = meta.map(lambda d: d["aim_l1_fixed"])
    q["cat_l1"] = meta.map(lambda d: d["cat_l1"])
    q["cat_l2"] = meta.map(lambda d: d["cat_l2"])
    q["cat_l3"] = meta.map(lambda d: d["cat_l3"])
    q["cat_path"] = meta.map(lambda d: d["cat_path"])
    q["has_catalogue"] = meta.map(lambda d: d["has_cat"])
    # Prefer master description if live desc empty
    q["description"] = [
        d if d else (m["description"] or "")
        for d, m in zip(q["description"], meta)
    ]

    def current_status(r) -> str:
        if not r["on_master"]:
            return "not_on_master"
        fixed = clean(r["aim_l1_fixed"])
        l1 = clean(r["aim_l1"])
        if fixed in MARKERS - {""} or l1 in MARKERS - {""}:
            return f"marker:{fixed or l1}"
        if not fixed and not l1:
            return "blank_family"
        return "blank_family"  # resolved empty already filtered

    q["current_aim_cat_status"] = q.apply(current_status, axis=1)

    def suggest(r) -> str:
        if not r["on_master"]:
            return "needs_EQ"
        path = r["cat_path"]
        if r["has_catalogue"] and path in cat_maps:
            return "cat_map"
        desc = (r["description"] or "").strip()
        if desc and len(desc) >= 3:
            # On master with a usable description but no unanimous cat map
            if r["has_catalogue"]:
                return "desc_rule"  # cat present but not unanimous enough → try description
            return "desc_rule"
        return "hand"

    q["suggested_next_method"] = q.apply(suggest, axis=1)
    q["cat_map_propose_l1"] = q["cat_path"].map(
        lambda p: cat_maps[p][0] if p in cat_maps else ""
    )
    q["cat_map_agree_share"] = q["cat_path"].map(
        lambda p: cat_maps[p][1] if p in cat_maps else ""
    )

    # Priority: both sources first, then more lines, never-billed last within group
    src_rank = {"both": 0, "backlog": 1, "warehouse": 2}
    q["src_rank"] = q["source"].map(src_rank)
    q = q.sort_values(
        ["src_rank", "lines", "ever_billed"],
        ascending=[True, False, True],
    )

    out_cols = [
        "pn",
        "description",
        "source",
        "lines",
        "lines_warehouse",
        "lines_backlog",
        "pcs_warehouse",
        "pcs_backlog",
        "ever_billed",
        "on_master",
        "current_aim_cat_status",
        "aim_l1",
        "aim_l1_fixed",
        "cat_l1",
        "cat_l2",
        "cat_l3",
        "suggested_next_method",
        "cat_map_propose_l1",
        "cat_map_agree_share",
    ]
    out = q[out_cols].copy()
    REL.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    by_src = out["source"].value_counts().to_dict()
    by_method = out["suggested_next_method"].value_counts().to_dict()
    by_billed = out["ever_billed"].value_counts().to_dict()
    by_master = out["on_master"].value_counts().to_dict()

    summary = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "track": "live_order_priority",
        "bar": "all parts need a full AIM family (Jerome 2026-10-07) — live orders first",
        "apply": "NO — proposal queue only. Do not write aim_master. Do not rebuild backlog HTML.",
        "findings": {
            "f1_backlog_higher_because_sellable_mix": {
                "confirm": bool(f1_confirm),
                "warehouse_line_aim_pct": finding["warehouse_line_aim_pct"],
                "backlog_line_aim_pct": finding["backlog_line_aim_pct"],
                "warehouse_only_distinct_pns": finding["pn_warehouse_only"],
                "backlog_only_distinct_pns": finding["pn_backlog_only"],
                "shared_pn_aim_pct_warehouse": finding["shared_pn_warehouse_aim_pct"],
                "shared_pn_aim_pct_backlog": finding["shared_pn_backlog_aim_pct"],
                "note": (
                    "Backlog line coverage is higher. Warehouse holds many warehouse-only PNs "
                    "(slow / one-off stock). On the shared PN set, AIM rates are nearly the same — "
                    "so the gap is mix, not a different matching rule."
                ),
            },
            "f2_about_1_in_5_warehouse_pns_never_billed": {
                "confirm": bool(f2_confirm),
                "never_billed_distinct": finding["warehouse_never_billed_distinct"],
                "warehouse_distinct_pns": finding["warehouse_distinct_pns"],
                "share": finding["warehouse_never_billed_share"],
                "among_unclassified_never_billed": finding["warehouse_unclassified_never_billed"],
                "among_unclassified_share": finding["warehouse_unclassified_never_billed_share"],
                "note": f2_note,
            },
        },
        "coverage": finding,
        "queue": {
            "distinct_pns_unclassified": int(len(out)),
            "by_source": by_src,
            "by_suggested_method": by_method,
            "by_ever_billed": {str(k): int(v) for k, v in by_billed.items()},
            "by_on_master": {str(k): int(v) for k, v in by_master.items()},
            "cat_map_eligible": int((out["suggested_next_method"] == "cat_map").sum()),
        },
        "proposal_csv": str(OUT_CSV),
        "summary_json": str(OUT_SUM),
        "scope": {
            "warehouse": str(WAREHOUSE),
            "backlog": str(BACKLOG),
            "backlog_excludes": list(EXCLUDE),
            "aim_family_rule": "aim_l1_fixed then aim_l1; blank/Unknown/Unknown Review = no family",
            "pn_match": "alnum normalize + strip leading zeros",
        },
    }
    OUT_SUM.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
