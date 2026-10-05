"""Measure what a proper two-source family banding would place, before writing the builder.

Reproduces the defect, then measures the fix on the PMS part universe, on the same 18-market
scope and the same 2025 denominator the shipped page uses (EUR 5,787,696 of service-part billing).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
DER = ROOT + r"\01_data\00_derived"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

N, H, L = "n_series_truck", "heavy_truck", "light_vehicle"
BAND2FAMILY = {"LCV_D-Max": L, "3.5t_N35": N, "7.5t_N50_N62_N75": N, "F_series_MD_heavy": H}
EPC_FAMILY_MAP = {
    "PASSENGER VEHICLE PICK UP": L, "PASSENGER VEHICLE SUV": L,
    "TRUCKS N": N, "TRUCKS Q": N, "TRUCKS F&G": H, "TRUCKS C&E": H,
}
FRAGMENTS = {"190", "400/450/500/600", "4X2", "4X4", "CHINA", "LV280", "RG", "RT",
             "S", "R", "D", "E", "Z", "X2", "X4", "UC", "TF", "C", "ELF", ""}

CODE_FAMILY: dict[str, str] = {}
for c in ("TFR", "TFS", "UCR", "UCS", "UBS", "UB"):
    CODE_FAMILY[c] = L
for c in ("NLR", "NKR", "NMR", "NNR", "NPR", "NPS", "NQR", "NRR", "NHR", "NJR", "NKS", "NJS",
          "NLS", "NMS", "NQS", "NK", "NL", "NJ", "NN", "NP", "NQ", "QKR", "QLR", "QMR", "PHR"):
    CODE_FAMILY[c] = N
for c in ("FRR", "FRD", "FRS", "FSR", "FSS", "FTS", "FTR", "FVR", "FVM", "FVZ", "FXM", "FXR",
          "FXZ", "FYH", "GVR", "GVZ", "GXZ", "GXR", "PFR", "TBR",
          "CVR", "CXH", "CXZ", "CYH", "CYZ", "CHR", "EXR", "EXZ"):
    CODE_FAMILY[c] = H
WILDCARDS = [(r"^TF\*$", L), (r"^UC\*$", L), (r"^UB\*$", L), (r"^UE\*$", L),
             (r"^N\*R$", N), (r"^N\*S$", N), (r"^N\*$", N), (r"^NK\*$", N), (r"^NN\*$", N),
             (r"^NP\*$", N), (r"^NQ\*$", N), (r"^NL\*$", N),
             (r"^F\*$", H), (r"^F\*R$", H), (r"^F\*D$", H), (r"^F\*S$", H),
             (r"^FR\*$", H), (r"^FS\*$", H), (r"^FT\*$", H), (r"^FV\*$", H),
             (r"^FX\*$", H), (r"^FY\*$", H), (r"^GV\*$", H), (r"^GX\*$", H), (r"^GX$", H),
             (r"^C\*$", H), (r"^C\*Z$", H), (r"^CV\*$", H), (r"^CX\*$", H), (r"^CY\*$", H),
             (r"^E\*$", H), (r"^EX\*$", H)]


def token_family(tok: str) -> str | None:
    t = tok.strip().upper()
    if not t or t in FRAGMENTS:
        return None
    if t in CODE_FAMILY:
        return CODE_FAMILY[t]
    if t in ("TF", "UC", "UB", "UE"):
        return None
    for pat, fam in WILDCARDS:
        if re.match(pat, t):
            return fam
    return None


def split_tokens(value: str) -> list[str]:
    s = str(value or "")
    for sep in ("/", "\uff0c", "\u3001", "\n", ";", ".", "(", ")", "[", "]", "{", "}", "\r"):
        s = s.replace(sep, ",")
    return [t for t in (p.strip() for p in s.split(",")) if t]


def crossref_families(value: str) -> tuple[set[str], list[str]]:
    fams: set[str] = set()
    unknown: list[str] = []
    for tok in split_tokens(value):
        f = token_family(tok)
        if f:
            fams.add(f)
        elif tok.upper() not in FRAGMENTS:
            unknown.append(tok)
    return fams, unknown


def main() -> int:
    sf = pd.read_parquet(DER + r"\sales_fact.parquet")
    sf["pn"] = sf.part_number.map(norm)
    sf["date"] = pd.to_datetime(sf.billing_date, errors="coerce")
    sf["year"] = sf.date.dt.year
    dim0 = pd.read_csv(DER + r"\distributor_dimension.csv")
    sf["db"] = sf.sold_to_sap.map(dict(zip(dim0.sold_to_sap, dim0.distributor_code)))

    core = pd.read_csv(DER + r"\pms_capture_by_family.csv")
    MARKETS = sorted(core.distributor_code.unique())
    print(f"scope: {len(MARKETS)} markets on the shipped page")

    dim = pd.read_csv(DER + r"\bvp_pn_dimension.csv", dtype=str, low_memory=False)
    supp = pd.read_csv(ROOT + r"\03_analytics\Isuzu\prism\data\pms_capture_supplement.csv",
                       dtype=str, low_memory=False)
    d = pd.concat([dim, supp], ignore_index=True)
    d["pn"] = d.part_number.map(norm)
    d = d[d.pms_category.notna() & (d.pms_category.astype(str).str.strip() != "")]
    pms_pn = d.drop_duplicates("pn")[["pn", "pms_category"]]
    print(f"PMS part numbers with a service category : {len(pms_pn):,}")

    # the denominator the shipped page uses: 18 markets, 2025, published service-part actual euro
    pub = pd.read_csv(DER + r"\pms_capture_by_db_year.csv")
    p25 = pub[(pub.line_type == "total") & (pub.year == 2025) & pub.distributor_code.isin(MARKETS)]
    tot25 = p25.actual_rev_eur.sum()
    print(f"2025 service-part billed euro (18 mk)    : EUR {tot25:,.0f}")

    y25 = sf[(sf.year == 2025) & sf.db.isin(MARKETS)]
    y25 = y25[y25.pn.isin(set(pms_pn.pn))]
    print(f"2025 rows joined to the PMS universe     : EUR {y25.net_sales_value.sum():,.0f}")

    # ── crossref source
    xr = pd.read_csv(DER + r"\genuine_bvp_crossref.csv", dtype=str, low_memory=False).fillna("")
    rows = []
    unk = Counter()
    for r in xr.itertuples():
        fams, unknown = crossref_families(r.vehicle_model)
        for u in unknown:
            unk[u] += 1
        for pn in {norm(r.genuine_pn), norm(r.bvp_pn)}:
            if pn and pn != "0":
                rows.append({"pn": pn, "fams": frozenset(fams)})
    xrdf = pd.DataFrame(rows)
    xr_set = xrdf.groupby("pn").fams.agg(lambda s: set().union(*s))
    print(f"crossref part numbers                    : {len(xr_set):,}")
    print(f"  crossref -> exactly one family         : {sum(1 for v in xr_set if len(v) == 1):,}")
    print(f"  crossref -> more than one              : {sum(1 for v in xr_set if len(v) > 1):,}")

    # ── EPC band source
    b1 = pd.read_csv(DER + r"\epc_decode_batch1_banded_20260919.csv")
    b1["pn"] = b1.pn.map(norm)
    band: dict[str, frozenset[str]] = {}
    for r in b1.itertuples():
        fams = frozenset(BAND2FAMILY[p] for p in str(r.tonnage_band or "").split("|")
                         if p in BAND2FAMILY)
        if not fams and r.band_status == "no_vehicle_epc_not_found":
            continue
        band[r.pn] = fams
    b2 = json.load(open(DER + r"\epc_decode_batch2_20260919.json", encoding="utf-8"))
    for r in b2:
        fams = frozenset(EPC_FAMILY_MAP[f] for f in (r.get("families") or []) if f in EPC_FAMILY_MAP)
        if fams:
            band.setdefault(norm(r["pn"]), fams)
    print(f"EPC banded part numbers                  : {len(band):,}")

    def decide(pn: str):
        bf = band.get(pn, frozenset())
        xf = frozenset(xr_set.get(pn, ()))
        fams = set(bf) | set(xf)
        if bf and xf and len(bf) == 1 and len(xf) == 1 and set(bf) != set(xf):
            return "conflict", fams, "band and crossref disagree"
        if len(fams) == 1:
            return next(iter(fams)), fams, ("both agree" if bf and xf
                                            else ("band only" if bf else "crossref only"))
        if len(fams) > 1:
            return "shared_across_families", fams, "fits more than one family"
        return "unattributed", fams, "no vehicle named"

    universe = set(pms_pn.pn)
    dec = pd.DataFrame([{"pn": p, **dict(zip(("family", "families", "source"), decide(p)))}
                        for p in sorted(universe)])
    e25 = y25.groupby("pn").net_sales_value.sum()
    dec["eur_2025"] = dec.pn.map(e25).fillna(0.0)
    print()
    print("=" * 100)
    print("2025 SERVICE-PART EURO BY FAMILY, NEW BANDING (18 markets)")
    print("=" * 100)
    g = dec.groupby("family").agg(pns=("pn", "size"), eur=("eur_2025", "sum"))
    g = g.sort_values("eur", ascending=False)
    for k, r in g.iterrows():
        print(f"  {k:26s} {int(r.pns):5d} PNs  EUR {r.eur:13,.0f}  {100*r.eur/tot25:6.2f}%")
    named = g.loc[[i for i in g.index if i in (N, H, L)], "eur"].sum()
    print(f"  {'PLACEABLE (3 named families)':26s}        EUR {named:13,.0f}  {100*named/tot25:6.2f}%")

    print()
    print("=" * 100)
    print("SAME UNIVERSE, OLD BANDING (as shipped)")
    print("=" * 100)
    old = pd.read_csv(DER + r"\pms_family_part_number_map.csv")
    old["pn"] = old.pn.map(norm)
    omap = dict(zip(old.pn, old.resolution))
    dec["old"] = dec.pn.map(omap).fillna("unattributed")
    go = dec.groupby("old").eur_2025.sum().sort_values(ascending=False)
    for k, v in go.items():
        print(f"  {k:26s}        EUR {v:13,.0f}  {100*v/tot25:6.2f}%")
    oldn = go.reindex(["single_family"]).fillna(0).sum()
    print(f"  {'PLACEABLE (old)':26s}        EUR {oldn:13,.0f}  {100*oldn/tot25:6.2f}%")

    print()
    print("=" * 100)
    print("MOVEMENT, 2025 EUR: old family value -> new family value")
    print("=" * 100)
    piv = dec.pivot_table(index="old", columns="family", values="eur_2025", aggfunc="sum").fillna(0)
    order = ["n_series_truck", "heavy_truck", "light_vehicle", "shared_across_families",
             "unattributed", "conflict"]
    piv = piv.reindex(columns=[c for c in order if c in piv.columns])
    print(piv.round(0).to_string())
    print()
    print(f"crossref tokens that still resolve to no family: {unk.most_common(30)}")
    print()
    print("heavy by category, new banding, 2025:")
    dam = pms_pn.merge(dec[["pn", "family", "eur_2025"]], on="pn", how="left")
    print(dam[dam.family == H].groupby("pms_category")
          .agg(pns=("pn", "size"), eur=("eur_2025", "sum")).sort_values("eur", ascending=False)
          .round(0).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
