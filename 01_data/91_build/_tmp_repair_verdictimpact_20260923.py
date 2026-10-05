"""Would the repair change any family VERDICT if the page were rebuilt? Measured, not guessed.

The page's payload was built from the 180-row file. The repair moved four rows from one band to two,
two of them brake_shoe. This recomputes the page's own verdict rule for every family against the
repaired file, on the page's own billing cache, and reports any verdict that would flip.

The page is NOT rebuilt. This is a measurement to decide whether a rebuild is needed.
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

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

n = lambda s: str(s).strip().lstrip("0") or "0"  # noqa: E731
CAT_KEYS = ["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter", "brake_pad",
            "brake_shoe", "brake_rotor", "clutch_kit", "clutch_disc", "clutch_pressure_plate",
            "clutch_booster", "release_bearing", "pilot_bearing"]


def payload(p: Path) -> dict:
    return json.loads(re.search(r'<script id="pmfe2-data" type="application/json">(.*?)</script>',
                                p.read_text(encoding="utf-8"), re.S).group(1))


def verdict_for(rows, single: set[str], deg: dict) -> tuple[str, float, int]:
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


def main() -> int:
    leg = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str, low_memory=False).fillna("")
    leg["k"] = leg.pn.map(n)
    leg["nb"] = leg.n_bands.astype(int)
    single = set(leg[leg.nb == 1].k)
    deg = {}
    for cat, g in leg.groupby("category"):
        if str(cat).strip():
            deg[cat] = {"pns": int(len(g)), "singleBand": int((g.nb == 1).sum()),
                        "placeable": bool((g.nb == 1).any())}

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
    bill["cat"] = bill.pn.map(lambda p: pipe.get(p, ""))
    ns = bill[bill.fam == "n_series_truck"]

    pay = payload(HTML)
    print("=" * 100)
    print("PAGE PAYLOAD (built from the 180-row file) vs THE REPAIRED FILE")
    print("=" * 100)
    for clock, col, base in (("CY", "y", 2025), ("FY", "fy", 2026)):
        comp = (pay.get("comparability") or {}).get(clock) or {}
        print(f"  --- {clock} (base {base})")
        for cat in CAT_KEYS:
            rows = ns[(ns[col] == base) & (ns.cat == cat)]
            if rows.empty or rows.net_sales_value.sum() <= 0:
                continue
            v, share, nsing = verdict_for(rows, single, deg.get(cat, {}))
            pv = comp.get(cat, {})
            if v != pv.get("verdict"):
                print(f"      VERDICT WOULD MOVE  {cat:24s} payload {str(pv.get('verdict')):8s} "
                      f"-> repaired file {v:8s}  (share {share:.4f})")
            elif abs(share - float(pv.get("shareShared") or 0)) > 0.0005:
                print(f"      share only          {cat:24s} payload "
                      f"{pv.get('shareShared')} -> {round(share, 4)}  verdict stays {v}")
        print()

    print("=" * 100)
    print("brake_shoe IN DETAIL")
    print("=" * 100)
    cy = (pay.get("comparability") or {}).get("CY", {}).get("brake_shoe", {})
    print(f"  payload says : verdict {cy.get('verdict')} shareShared {cy.get('shareShared')} "
          f"singleBandPns {cy.get('singleBandPns')}")
    rows = ns[(ns.y == 2025) & (ns.cat == "brake_shoe")]
    v, share, nsing = verdict_for(rows, single, deg.get("brake_shoe", {}))
    print(f"  repaired file: verdict {v} shareShared {round(share, 4)} single-band in family "
          f"{nsing}")
    print(f"  verdict identical: {v == cy.get('verdict')}")
    print()
    print("  the two brake_shoe rows the repair moved, and their billing in the page's base year:")
    for k in ("5876103260", "5878320470"):
        r = bill[(bill.pn == k) & (bill.y == 2025)]
        print(f"      {k:>12s} euro CY2025 {float(r.net_sales_value.sum()):,.2f}  "
              f"shareShared now counts it as {r.pn.iloc[0] not in single if len(r) else '?'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
