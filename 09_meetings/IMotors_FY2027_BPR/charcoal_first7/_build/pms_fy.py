"""PMS service-demand cover for Portugal, fiscal years, on the fleet counted from I Motors' registration file.

Denominator: ISZE service-demand model (prism modules/pms_engine.expected_by_category_bucketed), with the Portugal
             vehicle buckets set to each fiscal year's fleet (light trucks / F-Series / D-Max) instead of the fixed
             2025 fleet-workbook figure (2,206 / 269 / 4,733).
Fleet:       ISZE/01_data/07_UIO/Matriculas Isuzu SAP.xlsx, scrap-rate model (fleet-model survival curves) and,
             for comparison, the 10-year car park.
Numerator:   ISZE billed units to I Motors (sold-to 519 + 92), credit notes / returns excluded, service family from
             parts_catalog_dimension.csv (pad = pad + front/rear pad; shoe = shoe + front/rear shoe + linings).
             Reconciles within 3% of the model's own calendar-year unit counts.
"""
import os, sys, pathlib
import pandas as pd

R = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRISM = R / "03_analytics" / "Isuzu" / "prism"
CATS = ["air_filter", "oil_filter", "fuel_filter", "brake_pad", "clutch_kit", "brake_shoe"]
FYS = (2024, 2025, 2026)

def _regs():
    F = R / "01_data" / "07_UIO" / "Matriculas Isuzu SAP.xlsx"
    a = pd.read_excel(F, sheet_name="2005-2019", header=None, skiprows=2).iloc[:, 1:16]
    a.columns = ["vin", "model", "family", "Rodeo", "TF190", "RT56", "RT88", "RG", "N3.5", "N5", "N7.5", "F11", "F14", "plate", "reg_date"]
    b = pd.read_excel(F, sheet_name="2019-2026", header=None, skiprows=2).iloc[:, 1:16]
    b.columns = ["vin", "family", "Rodeo", "TF190", "RT56", "RT88", "RG", "N3.5", "N5", "N7.5", "F11", "F14", "model", "reg_date", "plate"]
    df = pd.concat([a, b], ignore_index=True)
    df = df[df.vin.notna()].drop_duplicates("vin").copy()
    df["reg_date"] = pd.to_datetime(df.reg_date, errors="coerce")
    seg = {"Rodeo": "LCV", "TF190": "LCV", "RT56": "LCV", "RT88": "LCV", "RG": "LCV", "N3.5": "LD", "N5": "LD", "N7.5": "LD", "F11": "F", "F14": "F"}
    def cls(r):
        for c, k in seg.items():
            if pd.notna(r[c]) and str(r[c]).strip() not in ("", "0"): return k
        m = str(r["model"]).upper()
        return "LCV" if m.startswith("D-MAX") else ("LD" if m.startswith("N") else ("F" if m.startswith("F") else None))
    df["cls"] = df.apply(cls, axis=1)
    df = df[df.cls.notna()].copy()
    df["fy"] = df.reg_date.dt.year + (df.reg_date.dt.month >= 4).astype(int)
    return df.groupby(["cls", "fy"]).size().rename("n").reset_index()

CV = [1, .99, .98, .97, .96, .95, .9, .8, .7, .55, .4, .3, .2, .1, .05]
LCV_C = [1, .98, .95, .92, .89, .84, .8, .65, .5, .4, .2]
def _surv(c, age):
    cur = LCV_C if c == "LCV" else CV
    return cur[age - 1] if 1 <= age <= len(cur) else 0.0

def _fleet(coh, fy, method):
    out = {}
    for c in ("LD", "F", "LCV"):
        k = coh[(coh.cls == c) & (coh.fy <= fy)]
        out[c] = (sum(r.n * _surv(c, fy - r.fy + 1) for r in k.itertuples()) if method == "scrap"
                  else float(k[k.fy > fy - 10].n.sum()))
    return out

def _fam(c):
    c = str(c)
    if c.startswith("brake_pad"): return "brake_pad"
    if c.startswith("brake_shoe") or c.startswith("brake_lining"): return "brake_shoe"
    return c if c in CATS else None

def build():
    sys.path.insert(0, str(PRISM)); cwd = os.getcwd(); os.chdir(PRISM)
    try:
        import modules.pms_capture_config as cc
        from modules.pms_engine import parc_config_for_distributor, expected_by_category_bucketed
        cfg = parc_config_for_distributor("PORTUGAL")
        saved = cc.UIO_BY_BUCKET.get("PORTUGAL")
        coh = _regs()
        fleets, exp = {}, {}
        for fy in FYS:
            for m in ("scrap", "ten"):
                f = _fleet(coh, fy, m); fleets[(fy, m)] = f
                cc.UIO_BY_BUCKET["PORTUGAL"] = {"cv_std": f["LD"], "f_series": f["F"], "lcv": f["LCV"]}
                e = expected_by_category_bucketed("PORTUGAL", cfg)
                for c in CATS: exp[(fy, m, c)] = e[c]["qty"]
        cc.UIO_BY_BUCKET["PORTUGAL"] = saved
    finally:
        os.chdir(cwd)
    def norm(s): return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.lstrip("0").replace("", "0")
    cat = pd.read_csv(R / "01_data" / "00_derived" / "parts_catalog_dimension.csv", dtype=str, usecols=["part_number", "pms_category"])
    cat["pn"] = norm(cat.part_number); cat = cat.drop_duplicates("pn"); cat["fam"] = cat.pms_category.map(_fam)
    sf = pd.read_parquet(R / "01_data" / "00_derived" / "sales_fact.parquet", columns=["billing_date", "sold_to_sap", "part_number", "billed_qty", "saty"])
    pt = sf[sf.sold_to_sap.isin([519, 92]) & ~sf.saty.isin(["CR", "RE"])].copy()
    pt["pn"] = norm(pt.part_number); pt = pt.merge(cat[cat.fam.notna()][["pn", "fam"]], on="pn")
    pt["fy"] = pt.billing_date.dt.year + (pt.billing_date.dt.month >= 4).astype(int)
    units = pt.pivot_table(index="fy", columns="fam", values="billed_qty", aggfunc="sum")
    rows = []
    for c in CATS:
        for fy in FYS:
            rows.append(dict(cat=c, fy=fy, units=float(units.loc[fy, c]), exp_scrap=exp[(fy, "scrap", c)], exp_ten=exp[(fy, "ten", c)]))
    t = pd.DataFrame(rows)
    t["cov_scrap"] = t.units / t.exp_scrap; t["cov_ten"] = t.units / t.exp_ten
    return t, fleets

if __name__ == "__main__":
    t, fl = build()
    pd.set_option("display.width", 200)
    print(t.round(3).to_string())
    print({k: round(sum(v.values())) for k, v in fl.items()})
