"""Which PMS categories can carry a tonnage band, and which cannot?

A category can carry a band only where its part numbers differ by N-series series
(NLR = 3.5 t, NMR = 5.5 t, NPR/NQR/NNR = 7.5 t). Where one part number fits several
series, the category is shared across bands and cannot have a band trend.

Series are matched on ANCHORED tokens, never substring: an earlier error in this session came
from 'F*' also matching 'TF*' (the D-Max pickup), which inflated a heavy-truck figure by EUR 1.8M.
"""

import json
import re

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
PD = ROOT + r"\03_analytics\Isuzu\prism\data"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

# N-series series -> the tonnage band it belongs to. Sourced, not pattern-guessed.
SERIES_BAND = {
    "NLR": "3.5t",
    "NMR": "5.5t",
    "NPR": "7.5t",
    "NQR": "7.5t",
    "NNR": "7.5t",
    "NKR": "5.5t",
    "NHR": "3.5t",
}
SERIES_RE = re.compile(r"(?<![A-Z])(" + "|".join(SERIES_BAND) + r")(?![A-Z])")


def bands_in(text: str) -> set[str]:
    """Anchored match on whole series tokens. 'TF*' does not yield an F-series band."""
    return {SERIES_BAND[s] for s in SERIES_RE.findall(str(text).upper())}


# ---- category per part number
cat = pd.read_csv(DER + r"\bvp_pn_dimension.csv", dtype=str, low_memory=False)
cat["pn"] = cat.part_number.map(norm)
cat = cat[cat.pms_category.notna()].drop_duplicates("pn")[["pn", "pms_category"]]
cmap = dict(zip(cat.pn, cat.pms_category))

# ---- series evidence 1: the cross-reference vehicle_model
xref = pd.read_csv(DER + r"\genuine_bvp_crossref.csv", dtype=str, low_memory=False)
rows = []
for _, r in xref.iterrows():
    for col in ("genuine_pn", "bvp_pn"):
        pn = norm(r.get(col))
        if not pn or pn == "0":
            continue
        rows.append({"pn": pn, "series_text": r.get("vehicle_model"),
                     "engine": r.get("engine_type"), "src": "crossref"})
xr = pd.DataFrame(rows)

# ---- series evidence 2: the EPC editions, both batches
rows = []
for f in ("epc_decode_batch1_20260919.json", "epc_decode_batch2_20260919.json"):
    try:
        dec = json.loads((pd.io.common.Path(DER) / f) if False else open(
            DER + "\\" + f, encoding="utf-8").read())
    except Exception:
        continue
    for r in dec:
        if not isinstance(r, dict):
            continue
        txt = " ".join(r.get("models") or []) + " " + " ".join(r.get("families") or [])
        rows.append({"pn": norm(r.get("pn")), "series_text": txt, "engine": "",
                     "src": "epc"})
epc = pd.DataFrame(rows)

ev = pd.concat([xr, epc], ignore_index=True)
ev = ev[ev.pn.notna() & ev.pn.ne("0")]
ev["bands"] = ev.series_text.map(bands_in)
ev = ev[ev.bands.map(len) > 0]

per_pn = (ev.groupby("pn").bands
          .apply(lambda sets: sorted(set().union(*sets)))
          .rename("band_list").reset_index())
per_pn["n_bands"] = per_pn.band_list.map(len)
per_pn["category"] = per_pn.pn.map(cmap)
per_pn["bands"] = per_pn.band_list.map(lambda b: "+".join(b))

# ---- billing, to weight it
sf = pd.read_parquet(DER + r"\sales_fact.parquet")
sf["pn"] = sf.part_number.map(norm)
money = sf.groupby("pn").net_sales_value.sum().rename("eur")
per_pn = per_pn.merge(money, left_on="pn", right_index=True, how="left")
per_pn["eur"] = per_pn.eur.fillna(0)

print("=" * 104)
print("PER PMS CATEGORY: can it carry a tonnage band?")
print("=" * 104)
print(f"{'category':22s} {'PNs':>5s} {'single-band':>12s} {'shared':>8s} "
      f"{'band-specific EUR':>18s} {'shared EUR':>14s}")
print("-" * 104)
cat_rows = []
for c, g in per_pn[per_pn.category.notna()].groupby("category"):
    single = g[g.n_bands == 1]
    shared = g[g.n_bands > 1]
    print(f"{c:22s} {len(g):5d} {len(single):12d} {len(shared):8d} "
          f"{single.eur.sum():18,.0f} {shared.eur.sum():14,.0f}")
    cat_rows.append({"category": c, "pns": len(g), "single": len(single),
                     "shared": len(shared), "eur_single": single.eur.sum(),
                     "eur_shared": shared.eur.sum()})

print()
print("=" * 104)
print("THE BANDS THEMSELVES — which tonnage is measurable")
print("=" * 104)
for b, g in per_pn[per_pn.n_bands == 1].groupby("bands"):
    print(f"  {b:8s} {len(g):4d} part numbers   EUR {g.eur.sum():14,.0f}")

print()
print("=" * 104)
print("WHERE THE SHARING SITS — the combinations")
print("=" * 104)
for b, g in per_pn[per_pn.n_bands > 1].groupby("bands"):
    print(f"  {b:22s} {len(g):4d} part numbers   EUR {g.eur.sum():14,.0f}")

tot = per_pn.eur.sum()
print()
print(f"  placed on at least one band : {len(per_pn):,} PNs, EUR {tot:,.0f}")
print(f"  of which single-band        : {(per_pn.n_bands==1).sum():,} PNs, "
      f"EUR {per_pn[per_pn.n_bands==1].eur.sum():,.0f} "
      f"({100*per_pn[per_pn.n_bands==1].eur.sum()/tot:.1f}%)")
print(f"  of which shared across bands: {(per_pn.n_bands>1).sum():,} PNs, "
      f"EUR {per_pn[per_pn.n_bands>1].eur.sum():,.0f}")

pd.DataFrame(cat_rows).to_csv(DER + r"\tonnage_capable_categories.csv", index=False)
per_pn.to_csv(DER + r"\tonnage_capable_part_numbers.csv", index=False)
print()
print("  -> tonnage_capable_categories.csv / tonnage_capable_part_numbers.csv")
