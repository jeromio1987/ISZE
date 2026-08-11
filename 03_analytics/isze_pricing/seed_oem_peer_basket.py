"""Seed oem_peer_basket.csv from top PMS filter/brake/clutch PNs.

Does not invent OE PNs or street prices — leaves those blank (status=needs_map).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ENGINE = Path(__file__).resolve().parent
OUT = ENGINE / "oem_peer_basket.csv"
RAW_MIRROR = ROOT / "01_data" / "01_Pricing" / "_raw" / "oem_peer_basket_seed_20260810.csv"

WANT = {
    "oil_filter",
    "fuel_filter",
    "air_filter",
    "blower_filter",
    "urea_filter",
    "brake_pad",
    "brake_rotor",
    "brake_shoe",
    "clutch_disc",
    "clutch_kit",
    "clutch_pressure_plate",
}

AIM_MAP = {
    "Oil Filter": "oil_filter",
    "Fuel Filter": "fuel_filter",
    "Air Filter": "air_filter",
    "Cabin Filter": "blower_filter",
    "Blower Filter": "blower_filter",
    "Urea Filter": "urea_filter",
    "Brake Pads": "brake_pad",
    "Brake Pad": "brake_pad",
    "Brake Rotors": "brake_rotor",
    "Brake Rotor": "brake_rotor",
    "Brake Shoes": "brake_shoe",
    "Clutch Disc": "clutch_disc",
    "Clutch Kit": "clutch_kit",
    "Pressure Plate": "clutch_pressure_plate",
}

PEERS = [
    ("LCV", "Toyota", "Hilux"),
    ("LCV", "Ford", "Ranger"),
    ("LCV", "Mitsubishi", "L200"),
    ("IUK", "Ford", "Transit"),
    ("IUK", "Mercedes-Benz", "Sprinter"),
    ("IUK", "DAF", "LF/CF class"),
    ("GERMANY", "Mercedes-Benz", "Sprinter / light truck"),
    ("GERMANY", "MAN", "TGL/TGM"),
    ("GERMANY", "VW", "Crafter"),
    ("GERMANY", "DAF", "LF/CF class"),
]

TOP_N = 5


def _infer(desc, cur):
    if pd.notna(cur):
        return cur
    d = str(desc).upper()
    rules = [
        ("oil_filter", ["OIL FILTER", "FILTER OIL", " OIL FIL"]),
        ("fuel_filter", ["FUEL FILTER", "FILTER FUEL"]),
        ("air_filter", ["AIR FILTER", "FILTER AIR"]),
        ("blower_filter", ["CABIN", "BLOWER", "POLLEN"]),
        ("urea_filter", ["UREA", "ADBLUE"]),
        ("brake_pad", ["BRAKE PAD", "PAD "]),
        ("brake_rotor", ["ROTOR", "BRAKE DISC", "DISC BRAKE"]),
        ("brake_shoe", ["SHOE"]),
        ("clutch_kit", ["CLUTCH KIT"]),
        ("clutch_disc", ["CLUTCH DISC", "DISC CLUTCH"]),
        ("clutch_pressure_plate", ["PRESSURE PLATE"]),
    ]
    for cat_name, keys in rules:
        if any(k in d for k in keys):
            return cat_name
    if "CLUTCH" in d:
        return "clutch_disc"
    return None


def main() -> None:
    ad = pd.read_csv(
        ROOT / "04_tools" / "autodoc_scraper" / "autodoc_results.csv",
        dtype={"PN": str},
    )
    ad["PN"] = ad["PN"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
    ad["Rev_CY2025_EUR"] = pd.to_numeric(ad["Rev_CY2025_EUR"], errors="coerce").fillna(0)
    ad["Qty_CY2025"] = pd.to_numeric(ad.get("Qty_CY2025"), errors="coerce").fillna(0)

    cat = pd.read_csv(
        ROOT / "01_data" / "00_derived" / "parts_catalog_dimension.csv",
        dtype={"part_number": str},
        low_memory=False,
    )
    cat["part_number"] = (
        cat["part_number"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
    )

    m = ad.merge(
        cat[["part_number", "pms_category"]].drop_duplicates("part_number"),
        left_on="PN",
        right_on="part_number",
        how="left",
    )
    m["pms_category"] = m["pms_category"].fillna(m["AIM_Category"].map(AIM_MAP))
    m["pms_category"] = [
        _infer(d, c) for d, c in zip(m["Description"], m["pms_category"])
    ]
    m = m[m["pms_category"].isin(WANT)].copy()

    eu = pd.read_csv(
        ROOT / "01_data" / "00_derived" / "eucon_price_gap.csv", dtype={"pn": str}
    )
    eu["pn"] = eu["pn"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
    eu_set = set(eu["pn"])
    m["in_eucon"] = m["PN"].isin(eu_set)
    m = m.sort_values(
        ["pms_category", "in_eucon", "Rev_CY2025_EUR"], ascending=[True, False, False]
    )
    seed = m.groupby("pms_category", as_index=False).head(TOP_N).copy()

    rows = []
    for _, r in seed.iterrows():
        src = (
            "eucon_price_gap+autodoc_top_rev" if r["in_eucon"] else "autodoc_top_rev"
        )
        for market, oem, model in PEERS:
            rows.append(
                {
                    "isze_pn": r["PN"],
                    "pms_category": r["pms_category"],
                    "description": r["Description"],
                    "isze_rev_cy2025_eur": round(float(r["Rev_CY2025_EUR"]), 2),
                    "isze_qty_cy2025": float(r["Qty_CY2025"]),
                    "peer_market": market,
                    "peer_oem": oem,
                    "peer_model": model,
                    "peer_oe_pn": "",
                    "peer_street_eur": "",
                    "source": src,
                    "notes": "OE PN + street EUR blank until map/scrape; do not invent",
                    "status": "needs_map",
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    RAW_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(RAW_MIRROR, index=False)
    print(f"wrote {OUT} rows={len(out)} unique_pn={out.isze_pn.nunique()}")
    print("by_market", out.peer_market.value_counts().to_dict())


if __name__ == "__main__":
    main()
