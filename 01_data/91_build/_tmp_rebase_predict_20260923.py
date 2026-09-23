"""Predict the page's own pooling verdict under the interim-band rule, before the write.

Replicates the builder's comparability block (service family, current billing cache, both clocks)
for two candidate re-bases of the legacy file:
  KEEP - the file's 297 rows, three-rung columns rewritten from the corrected mapping
  ADD  - every part number in the corrected mapping that fits a rung, plus the 297
So the three family flips the brief expects can be checked in advance, and a flip that does NOT
happen is found here rather than on the rendered page.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BUILD = ROOT / "02_dashboards" / "sales" / "_build"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
sys.path.insert(0, str(PRISM))
from modules.vehicle_bands import (  # noqa: E402
    N_SERIES_BANDS, NOT_IN_SCOPE, UNRESOLVED, band_for,
)

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
SHORT = {"3.5t_N35": "3.5t", "5.5t_N50_N55": "5.5t", "7.5t_N50_N62_N75": "7.5t"}
CAT_KEYS = ["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter", "brake_pad",
            "brake_shoe", "brake_rotor", "clutch_kit", "clutch_disc", "clutch_pressure_plate",
            "clutch_booster", "release_bearing", "pilot_bearing"]
WATCH = ["air_filter", "brake_rotor", "brake_shoe", "oil_filter", "fuel_filter", "brake_pad",
         "clutch_kit", "clutch_disc", "clutch_pressure_plate", "release_bearing"]


def rungs(app_row) -> list[str]:
    bands = {b for b in str(app_row.n_series_bands).split("|") if b}
    for c in str(app_row.parked_codes).split(";"):
        c = c.strip()
        if not c:
            continue
        b = band_for(c)
        if b in N_SERIES_BANDS:
            bands.add(b)
    return sorted(bands)


def build_frame(interpretation: str, cap_raw: pd.DataFrame, app: pd.DataFrame):
    if interpretation == "KEEP":
        frame = cap_raw.copy()
        frame["pnk"] = frame.pn.map(n)
    else:
        scope = app[app.n_series_bands != ""].copy()
        frame = scope[["pn", "pms_category"]].rename(columns={"pms_category": "category"})
        frame["pnk"] = frame.pn.map(n)
    A = app.set_index("pnk")
    lists = []
    for p in frame.pnk:
        lists.append(A.loc[p] if p in A.index else None)
    frame["_r"] = lists
    frame["n_bands"] = [len(rungs(r)) if r is not None else 0 for r in frame._r]
    frame["category"] = [str(f) for f in frame.get("category", pd.Series([""] * len(frame))).fillna("")]
    return frame


def verdicts(frame: pd.DataFrame, bill: pd.DataFrame, base, col, fam_ok, pn_cat_pipe) -> dict:
    single = set(frame[frame.n_bands == 1].pnk)
    out = {}
    for cat in CAT_KEYS:
        rows = bill[fam_ok & (bill[col] == base) & (bill.pn.map(lambda p: pn_cat_pipe.get(p, "")) == cat)]
        if rows.empty or rows.net_sales_value.sum() <= 0:
            out[cat] = ("none", 0.0, 0)
            continue
        tot = rows.net_sales_value.sum()
        s = rows[rows.pn.isin(single)]
        share = float(rows[~rows.pn.isin(single)].net_sales_value.sum() / tot)
        deg = frame[frame.category == cat]
        placeable = bool((deg.n_bands == 1).any())
        if not placeable or s.empty:
            v = "pooled"
        elif share > 0.5:
            v = "pooled"
        elif share > 0.15:
            v = "thin"
        else:
            v = "ok"
        out[cat] = (v, share, len(s))
    return out


def main() -> int:
    cap_raw = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", low_memory=False)
    app = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str, low_memory=False).fillna("")
    app["pnk"] = app.pn.map(n)

    core = pd.read_csv(DER / "pms_capture_by_family.csv", low_memory=False)
    fam = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str, low_memory=False).fillna("")
    fam["pnk"] = fam.pn.map(n)
    fam = fam.drop_duplicates("pnk")
    pn_fam = {}
    for r in fam.itertuples():
        pn_fam[r.pnk] = (r.family if r.resolution == "single_family"
                         else "shared_across_families" if r.resolution == "shared_across_families"
                         else "unattributed")
    bill = pd.read_parquet(BUILD / "_deep_billing_cache.parquet")
    bill["pn"] = bill.pn.astype(str).map(n)
    mk = set(core.distributor_code.unique())
    bill = bill[bill.db.isin(mk)].copy()
    bill["fam"] = bill.pn.map(pn_fam).fillna("shared_across_families")
    pn_cat_pipe = {}
    for p, c in zip(bill.pn, bill.cat_pipeline):
        if isinstance(c, str) and c and p not in pn_cat_pipe:
            pn_cat_pipe[p] = c
    fam_ok = bill.fam == "n_series_truck"

    print("=" * 100)
    print("PREDICTED VERDICTS ON THE CURRENT BILLING CACHE  (build dir cache: "
          f"{pd.Timestamp((BUILD / '_deep_billing_cache.parquet').stat().st_mtime, unit='s')})")
    print("=" * 100)
    for interp in ("KEEP", "ADD"):
        f = build_frame(interp, cap_raw, app)
        print()
        print(f"--- {interp}: rows {len(f):,}   single-band {int((f.n_bands == 1).sum()):,}")
        for clock, col, base in (("CY", "y", 2025), ("FY", "fy", 2026)):
            v = verdicts(f, bill, base, col, fam_ok, pn_cat_pipe)
            print(f"    {clock} (base {base}):")
            for cat in WATCH:
                vv, share, nsing = v.get(cat, ("?", 0, 0))
                print(f"        {cat:22s} verdict {vv:7s} shareShared {share:6.3f}"
                      f" single PNs {nsing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
