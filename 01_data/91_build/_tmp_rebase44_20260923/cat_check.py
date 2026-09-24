import pathlib
import pandas as pd

R = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = R / "01_data" / "00_derived"
key = lambda s: str(s).strip().lstrip("0") or "0"

c = pd.read_csv(R / "01_data" / "90_INBOX" / "PUBLISHED_BAND_PN_DIFF_44_2026-09-23.csv",
                dtype=str).fillna("")
print("44 rows; pms_category currently populated on", int((c.pms_category != "").sum()))

srcs = [
    ("vehicle_band_applicability", "vehicle_band_applicability.csv", "pms_category"),
    ("epc_decode_nseries_banded", "epc_decode_nseries_banded.csv", "pms_category"),
    ("vehicle_family_bands", "vehicle_family_bands.csv", "pms_category"),
    ("tonnage_capable(legacy)", "tonnage_capable_part_numbers.csv", "category"),
    ("tonnage_capable(live)", "tonnage_capable_part_numbers.csv", "category"),
]
for lbl, fn, col in srcs:
    if fn == "tonnage_capable_part_numbers.csv" and lbl.endswith("(legacy)"):
        continue
    d = pd.read_csv(DER / fn, dtype=str).fillna("")
    if col not in d.columns:
        print(f"{lbl:28s} no {col} column")
        continue
    m = dict(zip(d.pn.map(key), d[col]))
    got = c.pn.map(m).fillna("")
    print(f"{lbl:28s} covers {int((got != '').sum()):2d} of {len(c)}")

# combine
d1 = pd.read_csv(DER / "vehicle_band_applicability.csv", dtype=str).fillna("")
d2 = pd.read_csv(DER / "epc_decode_nseries_banded.csv", dtype=str).fillna("")
d3 = pd.read_csv(DER / "vehicle_family_bands.csv", dtype=str).fillna("")
d4 = pd.read_csv(DER / "tonnage_capable_part_numbers.csv", dtype=str).fillna("")
m1 = dict(zip(d1.pn.map(key), d1.pms_category))
m2 = dict(zip(d2.pn.map(key), d2.pms_category))
m3 = dict(zip(d3.pn.map(key), d3.pms_category))
m4 = dict(zip(d4.pn.map(key), d4.category))


def best(pn):
    for m in (m1, m2, m3, m4):
        if m.get(pn):
            return m[pn]
    return ""


c["resolved_category"] = c.pn.map(best)
print()
print("combined coverage:", int((c.resolved_category != "").sum()), "of", len(c))
print("still blank:")
print(c.loc[c.resolved_category == "", ["pn", "published_band_list", "corrected_band"]].to_string(index=False))
print()
print("agreement between sources where more than one has a value:")
dis = [p for p in c.pn if len({m[p] for m in (m1, m2, m3, m4) if m.get(p)}) > 1]
print("  rows where the four sources disagree:", len(dis))
for p in dis:
    print(f"    {p}: " + " | ".join(f"{v}" for v in
                                   ({'ap': m1.get(p), 'ep': m2.get(p), 'fam': m3.get(p),
                                     'tc': m4.get(p)}).items()))
