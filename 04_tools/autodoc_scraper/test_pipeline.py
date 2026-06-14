"""Quick end-to-end test: load -> score -> export HTML previews."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Re-implement the dashboard's load_all without streamlit cache decorator
import pandas as pd

SCRIPT_DIR = Path(__file__).parent
GBP_EUR = 1.17
SEK_EUR = 0.089

SITES = [
    {"key":"AD_UK","file":"autodoc_results.csv","min_col":"Autodoc_MinPrice_GBP",
     "all_prices_col":"Autodoc_AllPrices_GBP","brand_col":"Autodoc_CheapestBrand",
     "url_col":"Autodoc_URL","to_eur":GBP_EUR},
    {"key":"MEK","file":"mekonomen_results.csv","min_col":"MEK_AM_MinPrice_SEK",
     "all_prices_col":None,"brand_col":"MEK_AM_Brands",
     "url_col":"MEK_URL","to_eur":SEK_EUR},
    {"key":"KS_AM","file":"ks_results.csv","min_col":"KS_AM_MinPrice_GBP",
     "all_prices_col":None,"brand_col":"KS_AM_SKUs","url_col":"KS_URL","to_eur":GBP_EUR},
    {"key":"KS_GEN","file":"ks_results.csv","min_col":"KS_GEN_MinPrice_GBP",
     "all_prices_col":None,"brand_col":None,"url_col":"KS_URL","to_eur":GBP_EUR},
]

def _clean_min(all_prices_str, floor):
    if not isinstance(all_prices_str, str) or not all_prices_str.strip(): return None
    vals = []
    for p in all_prices_str.split("|"):
        try:
            v = float(p.strip())
            if v >= floor: vals.append(v)
        except ValueError: pass
    return min(vals) if vals else None


def load_all(floor=3.0):
    loaded = {}
    for site in SITES:
        f = SCRIPT_DIR / site["file"]
        if not f.exists(): continue
        df = pd.read_csv(f, dtype={"PN":str}, low_memory=False)
        df["PN"] = df["PN"].astype(str).str.zfill(10)
        price_col = site["min_col"]
        all_col = site.get("all_prices_col")
        if all_col and all_col in df.columns:
            df[price_col] = df[all_col].apply(lambda s: _clean_min(s, floor))
        elif price_col in df.columns:
            df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
            df.loc[df[price_col] < floor, price_col] = float("nan")
        rename = {}
        if price_col in df.columns: rename[price_col] = f"{site['key']}_min_native"
        if site["brand_col"] and site["brand_col"] in df.columns: rename[site["brand_col"]] = f"{site['key']}_brand"
        if site["url_col"] and site["url_col"] in df.columns: rename[site["url_col"]] = f"{site['key']}_url"
        df = df.rename(columns=rename)
        keep = ["PN"] + list(rename.values())
        if site["key"] == "AD_UK":
            for extra in ("Autodoc_ResultCount", "Autodoc_AllPrices_GBP"):
                if extra in df.columns: keep.append(extra)
        loaded[site["key"]] = df[keep].drop_duplicates("PN")

    # Base = AD_UK with metadata
    base = pd.read_csv(SCRIPT_DIR / "autodoc_results.csv", dtype={"PN":str}, low_memory=False)
    base["PN"] = base["PN"].astype(str).str.zfill(10)
    base["PR00_EUR"] = pd.to_numeric(base["PR00_EUR"], errors="coerce")
    base["Rev_CY2025_EUR"] = pd.to_numeric(base["Rev_CY2025_EUR"], errors="coerce").fillna(0)
    meta = ["PN","Description","PR00_EUR","Rev_CY2025_EUR"]
    for c in ("Qty_CY2025","Class","AIM_Category","Source","AIM_DemandType"):
        if c in base.columns: meta.append(c)
    merged = base[meta].drop_duplicates("PN")

    for key, df in loaded.items():
        merged = merged.merge(df, on="PN", how="left")

    for site in SITES:
        key = site["key"]
        nat = f"{key}_min_native"
        eur = f"{key}_min_eur"
        if nat in merged.columns:
            merged[eur] = pd.to_numeric(merged[nat], errors="coerce") * site["to_eur"]

    eur_cols = [f"{s['key']}_min_eur" for s in SITES if f"{s['key']}_min_eur" in merged.columns]
    if eur_cols:
        merged["best_price_eur"] = merged[eur_cols].min(axis=1)
        best_key = merged[eur_cols].idxmin(axis=1).str.replace("_min_eur","")
        merged["best_site"] = best_key
        merged["best_url"] = pd.NA
        for site in SITES:
            url_col = f"{site['key']}_url"
            if url_col in merged.columns:
                merged.loc[best_key == site["key"], "best_url"] = merged.loc[best_key == site["key"], url_col]

    return merged


if __name__ == "__main__":
    print("Loading merged data...")
    merged = load_all()
    print(f"  -> {len(merged)} PNs")
    print(f"  -> columns: {[c for c in merged.columns if not c.startswith('Unnamed')][:25]}")
    has_brand = merged.get("AD_UK_brand", pd.Series(dtype=object)).notna().sum()
    has_best = merged.get("best_price_eur", pd.Series(dtype=float)).notna().sum()
    print(f"  -> PNs with AD_UK brand: {has_brand} | with best AM price: {has_best}")

    from iam_scoring import compute_scores, summary_table
    scored = compute_scores(merged, db_gm=0.37, dlr_gm=0.25)

    print("\n=== Quadrant counts ===")
    print(scored["quadrant"].value_counts().to_string())

    print("\n=== Top 10 Dangerous ===")
    danger = scored[scored["quadrant"] == "Dangerous"].sort_values(
        ["threat_score","Rev_CY2025_EUR"], ascending=[False, False]).head(10)
    if len(danger):
        print(danger[["PN","Description","primary_threat_brand","brand_tier",
                      "threat_score","quality_score","Rev_CY2025_EUR"]].to_string(index=False))
    else:
        print("  (none)")

    print("\n=== Generating HTML previews ===")
    from html_export import build_both_previews
    paths = build_both_previews(scored, SCRIPT_DIR / "_html_previews")
    for label, p in paths.items():
        print(f"  {label}: {p}  ({p.stat().st_size:,} bytes)")
