"""Would brake_shoe fall out of the splittable set if the page were rebuilt? Measured directly.

The question only needs one number: brake_shoe's shared-euro share on the repaired file, against the
page's own 50% refusal line. That does not need the page's verdict model at all - just the family's
euro on the single-band set versus the rest, on the page's own billing frame.

The frame and category resolution are copied from the page's builder so the ratio is the page's.
Nothing is written and the page is not touched.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
BUILD = ROOT / "02_dashboards" / "sales" / "_build"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
CATS = {"oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter", "brake_pad",
        "brake_shoe", "brake_rotor", "clutch_kit", "clutch_disc", "clutch_pressure_plate",
        "clutch_booster", "release_bearing", "pilot_bearing"}


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

    results = {}
    for tag, path in (("PRE-REPAIR (180-row file, what the page was built from)",
                       DER / "_backsafe_rebase_20260923_vehbandapplic"
                             / "tonnage_capable_part_numbers.csv.bak_pre_nmr_repair"),
                      ("REPAIRED (176-row file, on disk now)",
                       DER / "tonnage_capable_part_numbers.csv")):
        leg = pd.read_csv(path, dtype=str, low_memory=False).fillna("")
        leg["k"] = leg.pn.map(n)
        cap_cat = dict(zip(leg.k, leg.category))
        single = set(leg[leg.n_bands.astype(int) == 1].k)
        bill["cat"] = bill.pn.map(lambda p: (pipe.get(p) or cap_cat.get(p) or ""))
        sub = bill[(bill.fam == "n_series_truck") & (bill.cat == "brake_shoe")]
        print("=" * 100)
        print(tag)
        print("=" * 100)
        for clock, col, base in (("CY", "y", 2025), ("FY", "fy", 2026)):
            rows = sub[sub[col] == base]
            if rows.empty or rows.net_sales_value.sum() <= 0:
                print(f"  {clock}: no euro in the page's frame")
                continue
            tot = float(rows.net_sales_value.sum())
            on = float(rows[rows.pn.isin(single)].net_sales_value.sum())
            off = float(rows[~rows.pn.isin(single)].net_sales_value.sum())
            share = off / tot
            verdict = "pooled (REFUSED)" if share > 0.5 else ("thin (split, with a caveat)"
                                                              if share > 0.15 else "ok (split)")
            print(f"  {clock}: family euro {tot:>10,.2f} | on single-band {on:>10,.2f} | "
                  f"shared {off:>10,.2f} | shareShared {share:.4f} -> {verdict}")
            results[(tag, clock)] = (share, verdict)
        print()
    print("=" * 100)
    print("ANSWER")
    print("=" * 100)
    for (tag, clock), (share, verdict) in results.items():
        short = "PRE " if tag.startswith("PRE") else "POST"
        print(f"  {short} {clock}  shareShared {share:.4f}  verdict {verdict}")
    print()
    worst = max(v for v, _ in results.values())
    print(f"  worst (highest) shared share across both files and clocks: {worst:.4f}")
    print(f"  the page refuses only above 0.50, so brake_shoe stays in the splittable set: "
          f"{worst <= 0.5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
