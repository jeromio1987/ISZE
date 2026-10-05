"""Control: does my re-implementation of the page's verdict rule reproduce the payload exactly?

If it reproduces the live payload from the 180-row file (the file the page was built from), then its
predictions on the repaired 176-row file can be trusted. If it does not, the prediction is worthless
and must not be reported.

Nothing is written; the page is not touched.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BUILD = ROOT / "02_dashboards" / "sales" / "_build"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
PRE = DER / "_backsafe_rebase_20260923_vebhandapplic"
PRE2 = DER / "_backsafe_rebase_20260923_vehbandapplic" / \
       "tonnage_capable_part_numbers.csv.bak_pre_nmr_repair"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731


def payload(p: Path) -> dict:
    return json.loads(re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
                                p.read_text(encoding="utf-8"), re.S).group(1))


def verdict_for(rows, single, deg):
    if rows.empty or rows.net_sales_value.sum() <= 0:
        return "none", 0.0, 0
    tot = rows.net_sales_value.sum()
    s = rows[rows.pn.isin(single)]
    share = float(rows[~rows.pn.isin(single)].net_sales_value.sum() / tot)
    if not deg.get("placeable") or s.empty:
        return "pooled", share, len(s)
    if share > 0.5:
        return "pooled", share, len(s)
    if share > 0.15:
        return "thin", share, len(s)
    return "ok", share, len(s)


def state(path):
    leg = pd.read_csv(path, dtype=str, low_memory=False).fillna("")
    leg["k"] = leg.pn.map(n)
    leg["nb"] = leg.n_bands.astype(int)
    single = set(leg[leg.nb == 1].k)
    deg = {}
    for cat, g in leg.groupby("category"):
        if str(cat).strip():
            deg[cat] = {"pns": int(len(g)), "singleBand": int((g.nb == 1).sum()),
                        "placeable": bool((g.nb == 1).any())}
    return single, deg


def main() -> int:
    core = pd.read_csv(DER / "pms_capture_by_family.csv", low_memory=False)
    fam = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str, low_memory=False).fillna("")
    fam["k"] = fam.pn.map(n)
    fam = fam.drop_duplicates("k")
    pn_fam = {}
    for r in fam.itertuples():
        pn_fam[r.k] = (r.family if r.resolution == "single_family"
                       else "shared_across_families" if r.resolution == "shared_across_families"
                       else "unattributed")
    bill = pd.read_parquet(BUILD / "_deep_billing_cache.parquet")
    bill["pn"] = bill.pn.astype(str).map(n)
    bill = bill[bill.db.isin(set(core.distributor_code.unique()))].copy()
    bill["fam"] = bill.pn.map(pn_fam).fillna("shared_across_families")
    pipe = {}
    for p, c in zip(bill.pn, bill.cat_pipeline):
        if isinstance(c, str) and c and p not in pipe:
            pipe[p] = c
    # the builder's own rule: the pipeline's label, the banding table's copy as fallback, and a
    # part number that resolves outside the page's fourteen families is dropped from the frame
    cap_cat = {}
    leg_all = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False)
    leg_all["k"] = leg_all.pn.map(n)
    cap_cat = dict(zip(leg_all.k, leg_all.category.fillna("")))
    CAT_KEYS_ALL = {"oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter",
                    "brake_pad", "brake_shoe", "brake_rotor", "clutch_kit", "clutch_disc",
                    "clutch_pressure_plate", "clutch_booster", "release_bearing", "pilot_bearing"}

    def cell_family(p: str) -> str:
        c = pipe.get(p) or cap_cat.get(p) or ""
        return c if c in CAT_KEYS_ALL else "_outside_the_page"

    bill = bill[bill.pn.map(cell_family) != "_outside_the_page"].copy()
    bill["cat"] = bill.pn.map(cell_family)
    ns = bill[bill.fam == "n_series_truck"]
    pay = payload(HTML)

    print("=" * 100)
    print("CONTROL: my replication on the PRE-REPAIR file vs the live payload")
    print("=" * 100)
    single_pre, deg_pre = state(PRE2)
    cap_cat = {}
    leg_all = pd.read_csv(PRE2, dtype=str, low_memory=False)
    leg_all["k"] = leg_all.pn.map(n)
    cap_cat = dict(zip(leg_all.k, leg_all.category.fillna("")))
    CAT_KEYS_ALL = {"oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter",
                    "brake_pad", "brake_shoe", "brake_rotor", "clutch_kit", "clutch_disc",
                    "clutch_pressure_plate", "clutch_booster", "release_bearing", "pilot_bearing"}

    def cell_family_pre(p: str) -> str:
        # the payload's own family for the pre-repair build: pipeline first, banding table fallback
        c = pipe0.get(p) or cap_cat.get(p) or ""
        return c if c in CAT_KEYS_ALL else "_outside_the_page"

    bill_pre = bill.copy()
    bill_pre["cat"] = bill_pre.pn.map(cell_family_pre)
    bill_pre = bill_pre[bill_pre.cat != "_outside_the_page"]
    ns_pre = bill_pre[bill_pre.fam == "n_series_truck"]
    mism = 0
    checked = 0
    for clock, col, base in (("CY", "y", 2025), ("FY", "fy", 2026)):
        comp = (pay.get("comparability") or {}).get(clock) or {}
        for cat in sorted(comp):
            if comp[cat].get("verdict") == "none":
                continue
            rows = ns[(ns[col] == base) & (ns.cat == cat)]
            v, share, nsing = verdict_for(rows, single_pre, deg_pre.get(cat, {}))
            checked += 1
            if v != comp[cat].get("verdict"):
                mism += 1
                print(f"  MISMATCH {clock} {cat:24s} payload {comp[cat].get('verdict')} "
                      f"vs my {v}  (share {round(share, 4)} vs {comp[cat].get('shareShared')})")
    print(f"  verdicts checked {checked}   mismatches {mism}")
    print(f"  replication faithful: {mism == 0}")
    print()

    if mism:
        print("  REPLICATION IS NOT FAITHFUL - prediction below is not reportable")
        return 1

    print("=" * 100)
    print("PREDICTION ON THE REPAIRED FILE (trustworthy, given the control passed)")
    print("=" * 100)
    single_now, deg_now = state(DER / "tonnage_capable_part_numbers.csv")
    for clock, col, base in (("CY", "y", 2025), ("FY", "fy", 2026)):
        comp = (pay.get("comparability") or {}).get(clock) or {}
        print(f"  --- {clock}")
        for cat in sorted(comp):
            if comp[cat].get("verdict") == "none":
                continue
            rows = ns[(ns[col] == base) & (ns.cat == cat)]
            v, share, nsing = verdict_for(rows, single_now, deg_now.get(cat, {}))
            if v != comp[cat].get("verdict"):
                print(f"      WOULD MOVE  {cat:24s} payload {comp[cat].get('verdict'):8s} "
                      f"-> {v:8s}   share {comp[cat].get('shareShared')} -> {round(share, 4)}"
                      f"   singleBandPns {comp[cat].get('singleBandPns')} -> {nsing}")
            elif abs(share - float(comp[cat].get("shareShared") or 0)) > 0.0005:
                print(f"      share only  {cat:24s} {comp[cat].get('shareShared')} -> "
                      f"{round(share, 4)}   verdict stays {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
