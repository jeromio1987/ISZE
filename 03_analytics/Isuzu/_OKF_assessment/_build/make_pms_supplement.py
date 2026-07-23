# Build the PMS capture supplement: the genuine OE PMS PNs the BVP dimension misses.
# Source: pms_missing_pns_figkey.csv (catalog pms_category, sold CY2025, not in capture universe).
# Selection: in-scope categories + brake_rotor (Jerome-approved 2026-06-15).
# Output: prism/data/pms_capture_supplement.csv — read by build_bvp_p0_p1.main() and
# concatenated into the in-memory dimension for the capture build ONLY (mix/BVP/GPS untouched).

import pandas as pd
from pathlib import Path

SRC = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\_OKF_assessment\pms_missing_pns_figkey.csv")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data\pms_capture_supplement.csv")

LABEL = {
    "oil_filter": "Oil Filter", "fuel_filter": "Fuel Filter", "air_filter": "Air Filter",
    "urea_filter": "Urea (AdBlue) Filter", "blower_filter": "Blower Unit Filter",
    "brake_pad": "Brake Pad", "brake_shoe": "Brake Shoe", "clutch_disc": "Clutch Disc",
    "clutch_pressure_plate": "Clutch Pressure Plate", "clutch_kit": "Clutch Kit",
    "release_bearing": "Release Bearing", "pilot_bearing": "Pilot Bearing",
    "clutch_booster": "Clutch Booster", "brake_rotor": "Brake Rotor",
}

df = pd.read_csv(SRC, dtype={"pn": str})
keep = df[(df.scope == "in_scope") | (df.pms_category == "brake_rotor")].copy()

supp = pd.DataFrame({
    "part_number": keep.pn.astype(str).str.strip(),
    "pms_flag": True,
    "line_type": "genuine",
    "pms_category": keep.pms_category,
    "category_label": keep.pms_category.map(LABEL).fillna(keep.pms_category),
    "pms_capture_eligible": True,
    "in_bvp_catalog": False,
    "pms_registry": False,
    "source": "catalog_pms_supplement_v1_2026-06-15",
}).drop_duplicates("part_number")

supp.to_csv(OUT, index=False, encoding="utf-8")
print(f"wrote {OUT}  ({len(supp)} PNs)")
print(supp.pms_category.value_counts().to_string())
