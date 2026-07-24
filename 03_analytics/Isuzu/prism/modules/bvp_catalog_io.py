"""
Shared BVP PARTS CATALOG.xlsx helpers (normalization, sheet taxonomy).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

PN_CELL_RE = re.compile(r"^0*(\d{10})$")

SKIP_SHEETS = {"INDEX", "WARRANTY", "Sheet1", "Sheet2", "Sheet3"}

SHEET_MAP: dict[str, tuple[str, str, bool, str | None]] = {
    "OIL FILTER": ("PMS_Filters", "oil_filter", True, "oil_filter"),
    "FUEL FILTER": ("PMS_Filters", "fuel_filter", True, "fuel_filter"),
    "AIR FILTER": ("PMS_Filters", "air_filter", True, "air_filter"),
    "UREA FILTER": ("PMS_Filters", "urea_filter", True, "urea_filter"),
    "BLOWER UNIT FILTER": ("PMS_Filters", "blower_filter", True, "blower_filter"),
    "BRAKE PAD KIT": ("Brakes", "brake_pad", True, "brake_pad"),
    "BRAKE SHOE KIT": ("Brakes", "brake_shoe", True, "brake_shoe"),
    "BRAKE LINING KIT": ("Brakes", "brake_lining", False, None),
    "BRAKE ROTOR": ("Brakes", "brake_rotor", False, None),
    "CLUTCH DISC": ("Clutch_Driveline", "clutch_disc", True, "clutch_disc"),
    "CLUTCH COVER": ("Clutch_Driveline", "clutch_pressure_plate", True, "clutch_pressure_plate"),
    "CLUTCH KIT": ("Clutch_Driveline", "clutch_kit", True, "clutch_kit"),
    "RELEASE BEARING": ("Clutch_Driveline", "release_bearing", True, "release_bearing"),
    "PILOT BEARING": ("Clutch_Driveline", "pilot_bearing", True, "pilot_bearing"),
    "CLUTCH BOOSTER": ("Clutch_Driveline", "clutch_booster", True, "clutch_booster"),
    "WATER PUMP": ("Belts_Cooling", "water_pump", False, None),
    "BELT": ("Belts_Cooling", "fan_belt", False, None),
    "GENERATOR": ("Electrical", "generator", False, None),
    "STARTER": ("Electrical", "starter", False, None),
    "WIPER BLADE": ("Cab_Misc", "wiper_blade", False, None),
    "ENG FOOT RUBBER": ("Cab_Misc", "engine_mount", False, None),
    "SHOCK ABSORBER": ("Suspension_Chassis", "shock_absorber", False, None),
    "LEAF SPRING ASM": ("Suspension_Chassis", "leaf_spring", False, None),
    "BUSHING": ("Suspension_Chassis", "bushing", False, None),
    "CENTER BEARING": ("Suspension_Chassis", "center_bearing", False, None),
    "HUB BRG": ("Suspension_Chassis", "hub_bearing", False, None),
    "HUB OIL SEAL": ("Suspension_Chassis", "hub_oil_seal", False, None),
    "KING PIN KIT": ("Suspension_Chassis", "king_pin", False, None),
    "WHEEL PIN SET": ("Suspension_Chassis", "wheel_pin", False, None),
}


def normalize_pn(raw) -> str | None:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return None
    if isinstance(raw, (int, np.integer)):
        s = str(int(raw))
    elif isinstance(raw, float):
        try:
            s = str(int(round(raw)))
        except (ValueError, OverflowError):
            s = str(raw).strip()
    else:
        s = str(raw).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    s = s.replace(" ", "")
    m = PN_CELL_RE.match(s)
    if m:
        return m.group(1)
    if s.isdigit() and len(s) == 10:
        return s
    if s.isdigit() and len(s) < 10:
        return s.zfill(10)
    return None


# Subgroup slugs that count as PMS when the sheet is PMS-flagged but pms_category was omitted.
PMS_SUBGROUP_AS_CATEGORY = frozenset(
    {
        "oil_filter",
        "fuel_filter",
        "air_filter",
        "urea_filter",
        "blower_filter",
        "brake_pad",
        "brake_shoe",
        "clutch_disc",
        "clutch_pressure_plate",
        "clutch_kit",
        "release_bearing",
        "pilot_bearing",
        "clutch_booster",
    }
)


def coalesce_pms_category(
    pms_cat: str | None, subgroup: str, pms_flag: bool
) -> str | None:
    if pms_cat:
        return pms_cat
    if pms_flag and subgroup in PMS_SUBGROUP_AS_CATEGORY:
        return subgroup
    return None


def resolve_sheet_meta(sheet_name: str) -> tuple[str, str, bool, str | None]:
    key = sheet_name.upper().strip()
    for pattern, meta in SHEET_MAP.items():
        if pattern in key or key in pattern:
            return meta
    slug = key.replace(" ", "_").lower()
    return ("Other", slug, False, None)


def _cell_text(val) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return str(val).replace("\n", " ").strip().upper()


@dataclass
class CatalogColumns:
    header_row: int
    data_start_row: int
    col_no: int | None
    col_genuine: int
    col_bvp: int
    col_type: int | None
    col_vehicle: int | None
    col_engine: int | None
    col_origin: int | None


def detect_catalog_columns(rows: list[tuple]) -> CatalogColumns | None:
    """Find genuine/BVP column indices from first few header rows."""
    for ri, row in enumerate(rows[:6]):
        texts = [_cell_text(c) for c in row]
        gen_idx = bvp_idx = None
        no_idx = type_idx = veh_idx = eng_idx = origin_idx = None
        for i, t in enumerate(texts):
            if "GENUINE" in t and "PART" in t:
                gen_idx = i
            elif "BVP" in t and "PART" in t:
                bvp_idx = i
            elif t in ("NO.", "NO"):
                no_idx = i
            elif t == "TYPE":
                type_idx = i
            elif "VEHICLE" in t and "MODEL" in t:
                veh_idx = i
            elif "ENGINE" in t and "TYPE" in t:
                eng_idx = i
            elif t == "ORIGIN":
                origin_idx = i
        if gen_idx is not None and bvp_idx is not None:
            data_start = ri + 1
            if ri + 1 < len(rows):
                sub = [_cell_text(c) for c in rows[ri + 1]]
                if any(x in ("INNER", "OUTER", "RIGHT", "LEFT") for x in sub):
                    data_start = ri + 2
            return CatalogColumns(
                header_row=ri,
                data_start_row=data_start,
                col_no=no_idx,
                col_genuine=gen_idx,
                col_bvp=bvp_idx,
                col_type=type_idx,
                col_vehicle=veh_idx,
                col_engine=eng_idx,
                col_origin=origin_idx,
            )
    return None


def _row_val(row: tuple, idx: int | None):
    if idx is None or idx >= len(row):
        return None
    return row[idx]
