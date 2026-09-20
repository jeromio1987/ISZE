# -*- coding: utf-8 -*-
"""Re-score Not-on-AIM residual on FIVE signals, EQ last resort.

Signals (Jerome bar):
  1. Description (specific rules + noun modal — not generic hose/pipe alone)
  2. HS6 modal from classified master
  3. Fig-key modal from classified master
  4. Price (list/unit) + price class as corroboration
  5. Product / parts dimension (catalog + BVP PN tables → AIM L1/L2/L3)

    EQ hit is used ONLY when the five leave the PN unassigned or in hard conflict.

Does NOT patch aim_master_v2 unless --apply-agree3 is passed.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
PRICING = ISZE / "01_data" / "01_Pricing"
INBOX = ISZE / "01_data" / "90_INBOX"

OUT_CSV = D / "pricing_not_on_aim_4signal_20260919.csv"
OUT_XLSX = PRICING / "Not_on_AIM_spine_4SIGNAL_classify_20260919.xlsx"
OUT_PATCH = D / "aim_gap_4signal_agree3_patch_20260919.csv"
OPEN_CMD = PRICING / "OPEN_Not_on_AIM_spine_4SIGNAL_20260919.cmd"

CATALOG_DIM = D / "parts_catalog_dimension.parquet"
BVP_DIM = D / "bvp_pn_dimension.csv"

PLACEHOLDER = {"", "Unknown", "Unknown Review", "nan", "None", "NaN", "Not on AIM spine"}

# Description rules that are too weak to count as a full signal alone
GENERIC_DESC_IDS = {
    "hose_generic",
    "pipe_generic",
    "cover_generic",
    "rubber_generic",
    "pin_generic",
    "spring_generic",
    "sensor_generic",
    "repair_kit_gen",
    "molding",
    "plate",
    "bearing",  # often wrong L3
    "gasket_eng",
}

# Price-class soft L1 hints (only corroboration, never sole vote)
CLASS_HINT = {
    "P": "Accident & Body",  # 100% on known book
}

# ---------------------------------------------------------------------------
# Dimension → AIM maps
# Prefer specific labels (pms_category / pr00_level3_type / fig_key_label /
# BVP product_family). Group-level alone is marked weak. Skip Review needed /
# Miscellaneous / Hardware — too coarse to drive assignment.
# ---------------------------------------------------------------------------

# PMS service category → AIM (strong when present; rare on residual)
DIM_PMS_MAP: dict[str, tuple[str, str, str]] = {
    "air_filter": ("Maintenance Service", "Air Filter", "Air Cleaner Filter"),
    "oil_filter": ("Maintenance Service", "Oil Filter", "Oil Filter Element"),
    "fuel_filter": ("Maintenance Service", "Fuel Filter", "Fuel Filter Element"),
    "urea_filter": ("Intake Exhaust Emission", "DEF System", "DEF Tank"),
    "blower_filter": ("Maintenance Service", "Filters", "Filter"),
    "brake_pad": ("Brakes", "Pads & Shoes", "Brake Pad"),
    "brake_pad_front": ("Brakes", "Pads & Shoes", "Brake Pad"),
    "brake_pad_rear": ("Brakes", "Pads & Shoes", "Brake Pad"),
    "brake_shoe": ("Brakes", "Pads & Shoes", "Brake Shoe"),
    "brake_shoe_front": ("Brakes", "Pads & Shoes", "Brake Shoe"),
    "brake_shoe_rear": ("Brakes", "Pads & Shoes", "Brake Shoe"),
    "brake_lining_front": ("Brakes", "Pads & Shoes", "Brake Lining"),
    "brake_lining_rear": ("Brakes", "Pads & Shoes", "Brake Lining"),
    "brake_rotor": ("Brakes", "Discs & Drums", "Brake Rotor"),
    "clutch_disc": ("Clutch", "Clutch Kit", "Clutch Kit"),
    "clutch_kit": ("Clutch", "Clutch Kit", "Clutch Kit"),
    "clutch_pressure_plate": ("Clutch", "Clutch Kit", "Clutch Kit"),
    "clutch_booster": ("Clutch", "Release System", "Pivot"),
    "release_bearing": ("Clutch", "Release System", "Pivot"),
    "pilot_bearing": ("Clutch", "Release System", "Pivot"),
    "leaf_spring": ("Suspension", "Leaf Springs", "Leaf Spring Asm"),
    "shock_absorber": ("Suspension", "Shock Absorber", "Damper"),
    "water_pump": ("Cooling", "Water Pump", "Water Pump"),
    "fan_belt": ("Maintenance Service", "Belts", "Drive Belt"),
    "bushing": ("Suspension", "Bush & Mount", "Bushing"),
}

# BVP product_family / product_group_label → AIM (strong corroboration on match)
DIM_BVP_FAMILY: dict[str, tuple[str, str, str]] = {
    "Brakes": ("Brakes", "Pads & Shoes", "Brake Friction"),
    "Clutch_Driveline": ("Clutch", "Clutch Kit", "Clutch Kit"),
    "Suspension_Chassis": ("Suspension", "Leaf Springs", "Leaf Spring Asm"),
    "Cab_Misc": ("Cabin Interior", "Trim", "Trim"),
    "Filters": ("Maintenance Service", "Filters", "Filter"),
}

# Catalog level-3 / fig_key_label → AIM (curated; overrides noisy empirical)
DIM_L3_MAP: dict[str, tuple[str, str, str, bool]] = {
    # bool = weak (coarse / hose-pipe / other-*)
    "Brake pad": ("Brakes", "Pads & Shoes", "Brake Pad", False),
    "Brake shoe / lining": ("Brakes", "Pads & Shoes", "Brake Shoe", False),
    "Brake disc": ("Brakes", "Discs & Drums", "Brake Disc", False),
    "Brake drum": ("Brakes", "Discs & Drums", "Brake Drum", False),
    "Brake booster": ("Brakes", "Booster & Control", "Brake Valve", False),
    "Brake hose / pipe": ("Brakes", "Hydraulic", "Brake Hose", False),
    "ABS component": ("Brakes", "ABS Control", "ABS Sensor", False),
    "Other brake": ("Brakes", "Actuation", "Brake Assembly", True),
    "Parking brake component": ("Brakes", "Actuation", "Brake Assembly", True),
    "Clutch disc": ("Clutch", "Clutch Kit", "Clutch Kit", False),
    "Clutch kit": ("Clutch", "Clutch Kit", "Clutch Kit", False),
    "Clutch booster": ("Clutch", "Release System", "Pivot", False),
    "Clutch cylinder": ("Clutch", "Release System", "Pivot", False),
    "Clutch linkage / cable": ("Clutch", "Release System", "Pivot", True),
    "Other clutch": ("Clutch", "Clutch Kit", "Clutch Kit", True),
    "Air filter": ("Maintenance Service", "Air Filter", "Air Cleaner Filter", False),
    "Oil filter": ("Maintenance Service", "Oil Filter", "Oil Filter Element", False),
    "Fuel filter": ("Maintenance Service", "Fuel Filter", "Fuel Filter Element", False),
    "Drive belt": ("Maintenance Service", "Belts", "Drive Belt", False),
    "Shock absorber": ("Suspension", "Shock Absorber", "Damper", False),
    "Leaf / suspension spring": ("Suspension", "Leaf Springs", "Leaf Spring Asm", False),
    "Air spring": ("Suspension", "Air Suspension", "Air Spring", False),
    "Bushing / mount": ("Suspension", "Bush & Mount", "Bushing", False),
    "Hanger / shackle": ("Suspension", "Spring", "Shackle", False),
    "Steering gear / unit": ("Steering", "Steering Gear", "Steering Unit", False),
    "Steering pump": ("Steering", "Control & Sensors", "Valve", False),
    "Tie rod end": ("Steering", "Linkage", "Tie Rod End", False),
    "Other steering": ("Steering", "Steering Gear", "Steering Unit", True),
    "Coolant hose / pipe": ("Cooling", "Cooling Hoses & Pipes", "Water Pipe", False),
    "Cooling fan": ("Cooling", "Radiator", "Radiator Assembly", True),
    "Cooler / intercooler": ("Cooling", "Radiator", "Radiator Assembly", True),
    "Blower / fan": ("Cooling", "Radiator", "Radiator Assembly", True),
    "Radiator": ("Cooling", "Radiator", "Radiator Assembly", False),
    "Thermostat": ("Cooling", "Thermostat & Control", "Thermostat", False),
    "Water pump": ("Cooling", "Water Pump", "Water Pump", False),
    "Fuel hose / pipe": ("Fuel System", "Fuel Lines & Hoses", "Fuel Hose", False),
    "Fuel pump": ("Fuel System", "Injection Pump", "Fuel Pump", False),
    "Fuel tank / cap": ("Fuel System", "Tank & Supply", "Fuel Tank", False),
    "Fuel sender / gauge": ("Fuel System", "Fuel Control", "Fuel Sensor", True),
    "Common rail": ("Fuel System", "Fuel Rail", "Common Rail", False),
    "Injector pipe": ("Fuel System", "Injection", "Injector / Rail", False),
    "Other fuel system": ("Fuel System", "Injection", "Injector / Rail", True),
    "Exhaust pipe": ("Intake Exhaust Emission", "Exhaust", "Exhaust Pipe", False),
    "Aftertreatment": ("Intake Exhaust Emission", "DEF System", "DEF Tank", False),
    "Catalyst": ("Intake Exhaust Emission", "Emission Control", "Catalyst", False),
    "EGR component": ("Intake Exhaust Emission", "EGR", "EGR Component", False),
    "Turbo hose / pipe": ("Intake Exhaust Emission", "Turbo", "Turbocharger", False),
    "Air duct / intake": ("Intake Exhaust Emission", "Air Intake", "Air Duct", False),
    "Door": ("Accident & Body", "Panels", "Door", False),
    "Panel": ("Accident & Body", "Panels", "Panel", False),
    "Bumper": ("Accident & Body", "Panels", "Bumper", False),
    "Fender": ("Accident & Body", "Panels", "Fender", False),
    "Grille": ("Accident & Body", "Panels", "Grille", False),
    "Step / guard": ("Accident & Body", "Panels", "Step", False),
    "Mirror assembly": ("Accident & Body", "Mirrors", "Mirror", False),
    "Glass / window": ("Accident & Body", "Glass", "Windshield", False),
    "Handle / lock": ("Accident & Body", "Locks & Handles", "Handle", False),
    "Other body": ("Accident & Body", "Panels", "Panel", True),
    "Body structure": ("Chassis Frame", "Crossmember & Brackets", "Reinforcement", True),
    "Interior trim": ("Cabin Interior", "Trim", "Trim", False),
    "Trim / molding": ("Cabin Interior", "Trim", "Trim", True),
    "Heater core / heater": ("Cabin Interior", "HVAC", "Heater", False),
    "A/C compressor": ("Cabin Interior", "HVAC", "A/C", False),
    "A/C hose / pipe": ("Cabin Interior", "HVAC", "A/C", True),
    "A/C electrical": ("Cabin Interior", "HVAC", "A/C", True),
    "Condenser": ("Cabin Interior", "HVAC", "A/C", False),
    "Evaporator": ("Cabin Interior", "HVAC", "A/C", False),
    "Shift linkage / cable": ("Cabin Interior", "Pedals & Controls", "Cable", False),
    "Headlamp": ("Lighting", "Lamps", "Headlamp Assembly", False),
    "Tail / combination lamp": ("Lighting", "Lamps", "Rear Combination Lamp", False),
    "Fog lamp": ("Lighting", "Lighting", "Lamp", False),
    "Marker / signal lamp": ("Lighting", "Lighting", "Lamp", False),
    "Other lighting": ("Lighting", "Lighting", "Lamp", True),
    "Bulb": ("Lighting", "Lighting", "Bulb", False),
    "Control unit": ("Electrical", "Control Units", "Control Unit", False),
    "Harness / cable": ("Electrical", "Harness & Connectors", "Connector", True),
    "Switch": ("Electrical", "Switch Relay Fuse", "Switch", False),
    "Relay / solenoid / fuse": ("Electrical", "Switch Relay Fuse", "Fuse", False),
    "Meter / gauge": ("Electrical", "Instruments", "Instrument Cluster", False),
    "Alternator / generator": ("Electrical", "Charging", "Alternator/Generator", False),
    "Starter motor": ("Electrical", "Charging", "Starter", False),
    "Differential / axle": ("Driveline Axle", "Differential", "Pinion", False),
    "Propeller shaft / PTO": ("Driveline Axle", "Axle Shaft", "Drive Shaft", False),
    "Gear": ("Transmission", "Geartrain", "Gear", False),
    "Gear set / gear": ("Transmission", "Geartrain", "Gear", False),
    "Gearbox case / housing": ("Transmission", "Geartrain", "Gear", True),
    "Shaft": ("Transmission", "Geartrain", "Gear", True),
    "Piston": ("Engine", "Internal Rotating", "Piston", False),
    "Cylinder head": ("Engine", "Cylinder Head", "Head Cover", False),
    "Engine assembly": ("Engine", "Complete Assembly", "Engine Assembly", False),
    "Engine bearing": ("Engine", "Internal Rotating", "Piston", True),
    "Engine pump": ("Lubrication", "Oil Pump", "Oil Pump", True),
    "Valve / valvetrain": ("Engine", "Cylinder Head", "Head Cover", True),
    "Oil seal / seal": ("Engine", "Gasket & Sealing", "Oil Seal", True),
    "Gasket set": ("Transmission", "Bearings & Seals", "Gasket", True),
    "Other gasket / seal": ("Transmission", "Bearings & Seals", "Gasket", True),
    "Bolt": ("Chassis Frame", "Mounting Hardware", "Bolt", False),
    "Nut": ("Chassis Frame", "Mounting Hardware", "Nut", False),
    "Washer": ("Chassis Frame", "Mounting Hardware", "Plate", True),
    "Bracket / stay": ("Chassis Frame", "Crossmember & Brackets", "Bracket", False),
    "Clip": ("Chassis Frame", "Mounting Hardware", "Fastener", True),
    "Fastener": ("Chassis Frame", "Mounting Hardware", "Fastener", True),
    "Air compressor": ("Chassis Frame", "Mounting Hardware", "Hose / Pipe", True),
    "Air dryer": ("Chassis Frame", "Mounting Hardware", "Hose / Pipe", True),
    "Air hose / pipe": ("Chassis Frame", "Mounting Hardware", "Hose / Pipe", True),
    "Air valve": ("Chassis Frame", "Mounting Hardware", "Hose / Pipe", True),
    "Other air system": ("Chassis Frame", "Mounting Hardware", "Hose / Pipe", True),
    "Air tank / reservoir": ("Chassis Frame", "Mounting Hardware", "Hose / Pipe", True),
    "Reservoir tank": ("Chassis Frame", "Mounting Hardware", "Hose / Pipe", True),
    "Grease": ("Fluids Chemicals", "Grease", "Grease", False),
}

# pr00_group → AIM L1 only (always weak; L2/L3 blank unless known)
DIM_GROUP_WEAK: dict[str, tuple[str, str, str]] = {
    "Brake parts": ("Brakes", "Actuation", "Brake Assembly"),
    "Clutch parts": ("Clutch", "Clutch Kit", "Clutch Kit"),
    "Steering": ("Steering", "Steering Gear", "Steering Unit"),
    "Suspension": ("Suspension", "Leaf Springs", "Leaf Spring Asm"),
    "Cooling": ("Cooling", "Cooling Hoses & Pipes", "Water Pipe"),
    "Fuel system": ("Fuel System", "Injection", "Injector / Rail"),
    "Injectors": ("Fuel System", "Injection", "Injector / Rail"),
    "Exhaust": ("Intake Exhaust Emission", "Exhaust", "Exhaust Pipe"),
    "Turbo": ("Intake Exhaust Emission", "Turbo", "Turbocharger"),
    "Filters": ("Maintenance Service", "Filters", "Filter"),
    "Belts": ("Maintenance Service", "Belts", "Drive Belt"),
    "Lighting": ("Lighting", "Lighting", "Lamp"),
    "Mirrors": ("Accident & Body", "Mirrors", "Mirror"),
    "Air conditioning": ("Cabin Interior", "HVAC", "A/C"),
    "Engine parts": ("Engine", "Internal Rotating", "Piston"),
    "Transmission parts": ("Transmission", "Geartrain", "Gear"),
    "Starter / alternator": ("Electrical", "Charging", "Alternator/Generator"),
    "Body parts": ("Accident & Body", "Panels", "Panel"),
    "Electrical sensors": ("Electrical", "Switch Relay Fuse", "Switch"),
}

# Labels that must never vote (too ambiguous)
DIM_SKIP_LABELS = {
    "Review needed",
    "Miscellaneous",
    "Hardware",
    "Consumables",
    "Other / review",
    "Linkage / lever",  # spans steering / cabin / brake
    "Pin",
    "Spring",
    "Bearing",
    "Spacer / retainer",
    "Cap / plug",
    "Case / housing / coupling",
    "Rubber / grommet",
    "Other mechanical",
}


def _norm_pn(s: object) -> str:
    t = "" if s is None or (isinstance(s, float) and np.isnan(s)) else str(s).strip()
    t = re.sub(r"\.0$", "", t)
    if t.isdigit():
        return t.zfill(10)
    return t


def _is_ph(val: object) -> bool:
    s = "" if val is None or (isinstance(val, float) and np.isnan(val)) else str(val).strip()
    return s in PLACEHOLDER


def _modal_triple(trips: list, min_n: int, min_share: float):
    if len(trips) < min_n:
        return None
    c = Counter(trips)
    (l1, l2, l3), n = c.most_common(1)[0]
    share = n / len(trips)
    if share < min_share or n < min_n:
        return None
    return l1, l2, l3, share, n


def _clean_label(val: object) -> str:
    s = "" if val is None or (isinstance(val, float) and np.isnan(val)) else str(val).strip()
    if s in PLACEHOLDER or s.lower() == "none":
        return ""
    return s


def load_dimension_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load catalog dimension (main) + BVP PN dimension (strong when PN hits)."""
    if CATALOG_DIM.exists():
        cat = pd.read_parquet(CATALOG_DIM)
    else:
        cat = pd.read_csv(D / "parts_catalog_dimension.csv", dtype=str, low_memory=False)
    cat = cat.copy()
    cat["pn"] = cat["part_number"].map(_norm_pn)
    cat = cat.drop_duplicates("pn", keep="first")

    bvp = pd.DataFrame(columns=["pn"])
    if BVP_DIM.exists():
        bvp = pd.read_csv(BVP_DIM, dtype=str, low_memory=False)
        bvp = bvp.copy()
        bvp["pn"] = bvp["part_number"].map(_norm_pn)
        bvp = bvp.drop_duplicates("pn", keep="first")
    return cat, bvp


def build_empirical_l3_modals(master: pd.DataFrame, cat: pd.DataFrame) -> dict[str, tuple]:
    """High-confidence pr00_level3_type → AIM from already-classified master.

    Only keeps labels with n>=8 and share>=0.55, and skips curated/skip sets.
    Used as fallback when curated DIM_L3_MAP misses a label.
    """
    m = master.copy()
    m["part_number"] = m["part_number"].map(_norm_pn)
    m["L1"] = m["aim_l1_fixed"].where(~m["aim_l1_fixed"].map(_is_ph), m.get("aim_l1"))
    m["L2"] = m["aim_l2_fixed"].where(~m["aim_l2_fixed"].map(_is_ph), m.get("aim_l2"))
    m["L3"] = m["aim_l3"]
    ok = m[~m["L1"].map(_is_ph)].copy()
    j = ok.merge(
        cat[["pn", "pr00_level3_type"]],
        left_on="part_number",
        right_on="pn",
        how="inner",
    )
    out: dict[str, tuple] = {}
    for lab, g in j.groupby(j["pr00_level3_type"].map(_clean_label)):
        if not lab or lab in DIM_SKIP_LABELS or lab in DIM_L3_MAP:
            continue
        trips = list(zip(g["L1"], g["L2"], g["L3"]))
        hit = _modal_triple(trips, min_n=8, min_share=0.55)
        if hit:
            l1, l2, l3, share, n = hit
            # mark weak if share is only middling
            out[lab] = (l1, l2, l3, share, n, share < 0.70)
    return out


def build_key_no_modal(master: pd.DataFrame, aud: pd.DataFrame) -> dict[str, tuple]:
    """Optional key_no modal — catches peers fig_key missed (same key, different fig)."""
    m = master.copy()
    m["part_number"] = m["part_number"].map(_norm_pn)
    m["L1"] = m["aim_l1_fixed"].where(~m["aim_l1_fixed"].map(_is_ph), m.get("aim_l1"))
    m["L2"] = m["aim_l2_fixed"].where(~m["aim_l2_fixed"].map(_is_ph), m.get("aim_l2"))
    m["L3"] = m["aim_l3"]
    ok = m[~m["L1"].map(_is_ph)][["part_number", "L1", "L2", "L3"]].copy()
    a = aud.copy()
    a["pn"] = a["pn"].map(_norm_pn)
    if "key_no" not in a.columns:
        return {}
    a_kn = a[["pn", "key_no"]].drop_duplicates("pn")
    a_kn = a_kn.rename(columns={"key_no": "_aud_key_no"})
    j = ok.merge(a_kn, left_on="part_number", right_on="pn", how="inner")
    j["_aud_key_no"] = j["_aud_key_no"].map(_clean_label)
    j = j[j["_aud_key_no"] != ""]
    out: dict[str, tuple] = {}
    for kn, g in j.groupby("_aud_key_no"):
        trips = list(zip(g["L1"], g["L2"], g["L3"]))
        hit = _modal_triple(trips, min_n=4, min_share=0.55)
        if hit:
            out[kn] = hit
    return out


def dim_signal(
    pn: str,
    cat_row: dict | None,
    bvp_row: dict | None,
    emp_l3: dict[str, tuple],
) -> tuple[dict | None, dict]:
    """Return (signal_dict_or_None, dim_fields_for_excel).

    Priority: BVP PN match → PMS category → curated L3/fig label → empirical L3
    → weak pr00_group. Weight 1.0 for specific; 0.55 and weak=True for group-only.
    """
    fields = {
        "dim_source": "",
        "dim_pms_category": "",
        "dim_pr00_group": "",
        "dim_pr00_level3": "",
        "dim_fig_label": "",
        "dim_bvp_family": "",
        "dim_mapped_l1": "",
        "dim_mapped_l2": "",
        "dim_mapped_l3": "",
        "dim_vote_strength": "",
    }
    if cat_row:
        fields["dim_pms_category"] = _clean_label(cat_row.get("pms_category"))
        fields["dim_pr00_group"] = _clean_label(cat_row.get("pr00_group"))
        fields["dim_pr00_level3"] = _clean_label(cat_row.get("pr00_level3_type"))
        fields["dim_fig_label"] = _clean_label(cat_row.get("fig_key_label"))
    if bvp_row:
        fields["dim_bvp_family"] = _clean_label(
            bvp_row.get("product_family") or bvp_row.get("product_group_label")
        )

    def _pack(l1, l2, l3, src, weight, weak):
        fields["dim_source"] = src
        fields["dim_mapped_l1"] = l1 or ""
        fields["dim_mapped_l2"] = l2 or ""
        fields["dim_mapped_l3"] = l3 or ""
        fields["dim_vote_strength"] = "weak" if weak else "strong"
        return {
            "l1": l1,
            "l2": l2,
            "l3": l3,
            "source": f"dim:{src}",
            "weight": weight,
            "weak": weak,
        }

    # 1) BVP PN hit — strong
    if bvp_row:
        fam = _clean_label(bvp_row.get("product_family"))
        pgl = _clean_label(bvp_row.get("product_group_label"))
        sub = _clean_label(bvp_row.get("product_subgroup") or bvp_row.get("subgroup_label"))
        for key in (fam, pgl):
            if key in DIM_BVP_FAMILY:
                l1, l2, l3 = DIM_BVP_FAMILY[key]
                # tighten clutch/brake via subgroup when present
                if key in ("Brakes",) and sub and "lining" in sub.lower():
                    l2, l3 = "Pads & Shoes", "Brake Lining"
                return _pack(l1, l2, l3, f"bvp:{key}", 1.0, False), fields
        pms_b = _clean_label(bvp_row.get("pms_category"))
        if pms_b in DIM_PMS_MAP:
            l1, l2, l3 = DIM_PMS_MAP[pms_b]
            return _pack(l1, l2, l3, f"bvp_pms:{pms_b}", 1.0, False), fields

    if not cat_row:
        return None, fields

    # 2) PMS category on catalog — strong
    pms = fields["dim_pms_category"]
    if pms in DIM_PMS_MAP:
        l1, l2, l3 = DIM_PMS_MAP[pms]
        return _pack(l1, l2, l3, f"pms:{pms}", 1.0, False), fields

    # 3) Curated level-3 / fig label
    for lab, tag in (
        (fields["dim_pr00_level3"], "l3"),
        (fields["dim_fig_label"], "figlab"),
    ):
        if not lab or lab in DIM_SKIP_LABELS:
            continue
        if lab in DIM_L3_MAP:
            l1, l2, l3, weak = DIM_L3_MAP[lab]
            return _pack(l1, l2, l3, f"{tag}:{lab}", 0.85 if weak else 1.0, weak), fields

    # 4) Empirical L3 from classified book
    for lab, tag in (
        (fields["dim_pr00_level3"], "emp_l3"),
        (fields["dim_fig_label"], "emp_figlab"),
    ):
        if lab and lab in emp_l3:
            l1, l2, l3, share, n, weak = emp_l3[lab]
            return (
                _pack(l1, l2, l3, f"{tag}:{lab}", float(share), weak or share < 0.70),
                fields,
            )

    # 5) Weak group-only
    grp = fields["dim_pr00_group"]
    if grp and grp not in DIM_SKIP_LABELS and grp in DIM_GROUP_WEAK:
        l1, l2, l3 = DIM_GROUP_WEAK[grp]
        return _pack(l1, l2, l3, f"group:{grp}", 0.55, True), fields

    return None, fields


def load_gap_rules():
    spec = importlib.util.spec_from_file_location(
        "gapcls",
        ISZE / "01_data" / "91_build" / "classify_aim_gap_auto_assign_20260918.py",
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.DESC_RULES


def load_assign_rules():
    """Parse medium/high desc rules from assign_aim_gap RULES tuples if present."""
    # Fallback: use DESC_RULES only from classify script
    return []


def build_modals(master: pd.DataFrame, aud: pd.DataFrame):
    # Prefer fixed spine; fall back to aim_l1/aim_l2/aim_l3
    m = master.copy()
    m["part_number"] = m["part_number"].map(_norm_pn)
    m["L1"] = m["aim_l1_fixed"].where(~m["aim_l1_fixed"].map(_is_ph), m.get("aim_l1"))
    m["L2"] = m["aim_l2_fixed"].where(~m["aim_l2_fixed"].map(_is_ph), m.get("aim_l2"))
    m["L3"] = m["aim_l3"]
    ok = m[~m["L1"].map(_is_ph)].copy()
    aud = aud.copy()
    aud["pn"] = aud["pn"].map(_norm_pn)

    hs_join = ok.merge(aud[["pn", "hs6"]], left_on="part_number", right_on="pn", how="inner")
    hs_join = hs_join[hs_join["hs6"].fillna("").astype(str).str.len() >= 6]
    hs_modal = {}
    for hs6, g in hs_join.groupby(hs_join["hs6"].astype(str).str[:6]):
        trips = list(zip(g["L1"], g["L2"], g["L3"]))
        hit = _modal_triple(trips, min_n=3, min_share=0.40)
        if hit:
            hs_modal[str(hs6)[:6]] = hit

    fig_src = ok.merge(aud[["pn", "fig_key"]], left_on="part_number", right_on="pn", how="left")
    if "fig_key_x" in fig_src.columns:
        fig_src["fig_key"] = fig_src["fig_key_x"].fillna(fig_src.get("fig_key_y", ""))
    elif "fig_key" not in fig_src.columns and "fig_key_y" in fig_src.columns:
        fig_src["fig_key"] = fig_src["fig_key_y"]
    fig_src["fig_key"] = fig_src["fig_key"].fillna("").astype(str)
    fig_src = fig_src[fig_src["fig_key"] != ""]
    fig_modal = {}
    for fk, g in fig_src.groupby("fig_key"):
        trips = list(zip(g["L1"], g["L2"], g["L3"]))
        hit = _modal_triple(trips, min_n=3, min_share=0.40)
        if hit:
            fig_modal[fk] = hit

    ok["noun"] = ok["description"].fillna("").astype(str).str.upper().str.split(";").str[0].str.strip()
    noun_modal = {}
    for noun, g in ok.groupby("noun"):
        if not noun or len(noun) < 3:
            continue
        trips = list(zip(g["L1"], g["L2"], g["L3"]))
        hit = _modal_triple(trips, min_n=5, min_share=0.55)
        if hit:
            noun_modal[noun] = hit

    return hs_modal, fig_modal, noun_modal, ok


def price_signal(list_eur: float, price_class: str, desc_u: str):
    """Price corroboration → optional L1 hint."""
    hints = []
    pc = (price_class or "").strip().upper()
    if pc in CLASS_HINT:
        hints.append((CLASS_HINT[pc], "class_hint", 0.5))
    # Expensive complete assemblies by price + desc
    if list_eur and list_eur >= 3000 and re.search(r"ENGINE\s*ASM|BLOCK\s*ASM;\s*CYL", desc_u):
        hints.append(("Engine", "price_floor_engine", 1.0))
    if list_eur and list_eur >= 2000 and re.search(r"CAB\s*ASM", desc_u):
        hints.append(("Accident & Body", "price_floor_cab", 1.0))
    if list_eur and list_eur >= 1500 and re.search(r"TRANSMISSION\s*ASM|TRANSFER\s*ASM", desc_u):
        hints.append(("Transmission" if "TRANS" in desc_u else "Driveline Axle", "price_floor_asm", 0.8))
    if not hints:
        return None
    # strongest
    hints.sort(key=lambda x: -x[2])
    l1, meth, w = hints[0]
    return l1, None, None, meth, w


def desc_signal(desc: str, desc_rules, noun_modal):
    desc_u = (desc or "").strip().upper()
    for rx, l1, l2, l3, meth in desc_rules:
        if rx.search(desc_u):
            rid = meth
            # extract rule id from pattern comment — use l3 label
            generic = any(g in desc_u for g in [])  # evaluated below via method name
            # Map classify DESC_RULES: treat HOSE/PIPE/BOLT generics as weak
            weak = bool(
                re.match(
                    r"^(HOSE;|PIPE;\s*(WATER|FUEL|VAC)|BOLT;|NUT;|WASHER;|SCREW;|CLIP;|CLAMP;)",
                    desc_u,
                )
            )
            return l1, l2, l3, f"desc:{rid}", (0.4 if weak else 1.0), weak
    noun = desc_u.split(";")[0].strip()
    if noun in noun_modal:
        l1, l2, l3, share, n = noun_modal[noun]
        return l1, l2, l3, f"noun:{noun}", float(share), False
    return None


def load_eq_hits() -> dict[str, tuple]:
    """Last-resort EQ hits already on disk (map catalog tree → AIM spine where needed)."""
    cat_to_aim = {
        "Accident parts": "Accident & Body",
        "Body Exterior": "Accident & Body",
        "Comfort parts": "Cabin Interior",
        "Hardware & consumables": "Chassis Frame",
        "Competitive parts": None,  # need L2 hint
        "Repair parts": None,
        "High value repair": None,
        "Other / review": None,
    }
    l2_hint = {
        "Brake parts": ("Brakes", "Pads & Shoes", "Brake Friction"),
        "Brake pad": ("Brakes", "Pads & Shoes", "Brake Friction"),
        "Other brake": ("Brakes", "Actuation", "Brake Assembly"),
        "Exhaust": ("Intake Exhaust Emission", "Exhaust", "Exhaust Pipe"),
        "Aftertreatment": ("Intake Exhaust Emission", "DEF System", "DEF Tank"),
        "Fuel system": ("Fuel System", "Injection", "Injector / Rail"),
        "Other fuel system": ("Fuel System", "Injection", "Injector / Rail"),
        "Filters": ("Maintenance Service", "Filters", "Filter"),
        "Air filter": ("Maintenance Service", "Filters", "Air Filter"),
        "Other filter": ("Maintenance Service", "Filters", "Filter"),
        "Bumper": ("Accident & Body", "Panels", "Bumper"),
        "Other body": ("Accident & Body", "Panels", "Panel"),
        "Body parts": ("Accident & Body", "Panels", "Panel"),
        "High-voltage battery": ("Electrical", "Charging", "HV Battery"),
        "Battery": ("Electrical", "Charging", "Battery"),
    }
    out: dict[str, tuple] = {}
    p = INBOX / "_EQ_HIT_DOUBT_PASS_RESULTS_20260918.csv"
    if not p.exists():
        return out
    df = pd.read_csv(p, dtype=str, low_memory=False)
    for _, r in df.iterrows():
        pn = _norm_pn(r.get("pn"))
        verdict = str(r.get("verdict") or "").upper()
        status = str(r.get("eq_status") or "").upper()
        if "NO_EQ" in verdict or status == "NO_EQ_HIT":
            continue
        if status not in ("FOUND",) and "PROPOSE" not in verdict and "CONFIRM" not in verdict:
            if status != "FOUND":
                continue
        pl1 = str(r.get("proposed_l1") or r.get("current_l1") or "")
        pl2 = str(r.get("proposed_l2") or r.get("current_l2") or "")
        pl3 = str(r.get("proposed_l3") or r.get("current_l3") or "")
        # Prefer L2 hint map
        if pl2 in l2_hint:
            aim = l2_hint[pl2]
            out[pn] = (*aim, f"eq_hit:{p.name}")
            continue
        if pl3 in l2_hint:
            aim = l2_hint[pl3]
            out[pn] = (*aim, f"eq_hit:{p.name}")
            continue
        mapped = cat_to_aim.get(pl1)
        if mapped:
            out[pn] = (mapped, pl2, pl3, f"eq_hit:{p.name}")
    return out


def vote(signals: list[dict]) -> dict:
    """signals: list of {l1,l2,l3,source,weight,weak}"""
    strong = [s for s in signals if s and not s.get("weak")]
    all_s = [s for s in signals if s]
    if not all_s:
        return {
            "status": "needs_eq",
            "agree_n": 0,
            "l1": "",
            "l2": "",
            "l3": "",
            "method": "",
            "notes": "no_signal",
        }

    # Vote on L1 with weights
    l1_votes: Counter = Counter()
    for s in all_s:
        w = float(s.get("weight") or 1.0)
        if s.get("weak"):
            w *= 0.35
        l1_votes[s["l1"]] += w

    best_l1, best_w = l1_votes.most_common(1)[0]
    supporters = [s for s in all_s if s["l1"] == best_l1]
    strong_supporters = [s for s in strong if s["l1"] == best_l1]
    n_sources = len({s["source"].split(":")[0] for s in supporters})
    n_strong = len({s["source"].split(":")[0] for s in strong_supporters})

    # Pick L2/L3 from strongest non-weak supporter, else any
    pick = (strong_supporters or supporters)[0]
    for s in strong_supporters:
        if s.get("l2") and s.get("l3"):
            pick = s
            break

    conflict = [s for s in strong if s["l1"] != best_l1]
    notes = [
        f"sources={','.join(sorted({s['source'] for s in all_s}))}",
        f"agree_sources={n_sources}",
        f"strong_agree={n_strong}",
        f"l1_weight={best_w:.2f}",
    ]
    if conflict:
        notes.append(
            "conflict:"
            + ",".join(f"{s['source']}→{s['l1']}" for s in conflict)
        )

    # Decision
    if n_strong >= 3 or (n_strong >= 2 and n_sources >= 3):
        status = "agree3_high"
    elif n_strong >= 2 or (n_sources >= 2 and n_strong >= 1 and not conflict):
        status = "agree2_review"
    elif n_strong >= 1 and not conflict and not any(s.get("weak") and s["l1"] == best_l1 for s in supporters if len(supporters) == 1):
        # single strong specific desc
        if any(not s.get("weak") and s["source"].startswith("desc") for s in strong_supporters):
            status = "agree1_desc_strong"
        else:
            status = "agree1_weak"
    elif conflict and n_strong >= 1:
        status = "conflict_needs_eq"
    else:
        status = "agree1_weak"

    return {
        "status": status,
        "agree_n": n_sources,
        "strong_n": n_strong,
        "l1": best_l1,
        "l2": pick.get("l2") or "",
        "l3": pick.get("l3") or "",
        "method": "+".join(sorted({s["source"] for s in supporters})),
        "notes": "; ".join(notes),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="5-signal Not-on-AIM scorer (score-only by default)")
    ap.add_argument(
        "--apply-agree3",
        action="store_true",
        help="Write agree3 patch into aim_master_v2 (OFF by default — score only)",
    )
    args = ap.parse_args()
    if args.apply_agree3:
        raise SystemExit(
            "--apply-agree3 is gated: this run refuses to patch aim_master_v2. "
            "Score + Excel only unless Jerome explicitly asks to apply."
        )

    print("Loading …")
    lines = pd.read_parquet(D / "pricing_aim_source_lines.parquet")
    spine = lines[lines["aim_l1"].astype(str).eq("Not on AIM spine")].copy()
    spine["pn"] = spine["part_number"].map(_norm_pn)
    # strip tools/MX2 from scoring target (already out of revision)
    tools = pd.read_csv(D / "special_tools_pns_20260918.csv", dtype=str)
    tool_pns = set(tools["pn"].map(_norm_pn))
    spine["desc_u"] = spine["description"].fillna("").astype(str).str.upper()
    excl = spine["pn"].isin(tool_pns) | spine["desc_u"].str.contains("MX2", regex=False)
    spine = spine[~excl]

    resid = spine.groupby("pn", as_index=False).agg(
        description=("description", "first"),
        billed_eur=("billed_eur", "sum"),
        step_eur=("step_eur", "sum"),
        qty=("qty", "sum"),
        price_class=("price_class", "first"),
    )

    aud = pd.read_csv(D / "_audit_cls_spine.csv", dtype=str, low_memory=False)
    aud["pn"] = aud["pn"].map(_norm_pn)
    aud = aud.drop_duplicates("pn")
    master = pd.read_csv(D / "aim_master_v2.csv", dtype=str, low_memory=False)
    master["part_number"] = master["part_number"].map(_norm_pn)

    cat_dim, bvp_dim = load_dimension_tables()
    emp_l3 = build_empirical_l3_modals(master, cat_dim)
    key_modal = build_key_no_modal(master, aud)
    cat_by_pn = cat_dim.set_index("pn").to_dict(orient="index")
    bvp_by_pn = bvp_dim.set_index("pn").to_dict(orient="index") if len(bvp_dim) else {}

    # price class from master / lines
    pc_map = (
        master.set_index("part_number")["price_class_iml"].to_dict()
        if "price_class_iml" in master.columns
        else {}
    )

    resid = resid.merge(
        aud[["pn", "hs6", "fig_key", "fig_no", "key_no", "list_eur", "noun", "weight_kg"]],
        on="pn",
        how="left",
    )
    resid["list_eur"] = pd.to_numeric(resid["list_eur"], errors="coerce")
    resid["price_class"] = resid.apply(
        lambda r: (r.get("price_class") or pc_map.get(r["pn"]) or ""),
        axis=1,
    )

    # Coverage on residual
    n_cat = sum(1 for pn in resid["pn"] if pn in cat_by_pn)
    n_bvp = sum(1 for pn in resid["pn"] if pn in bvp_by_pn)
    eur_cat = float(resid.loc[resid["pn"].isin(cat_by_pn), "billed_eur"].sum())
    eur_tot = float(resid["billed_eur"].sum())
    print(
        f"  dim coverage: catalog {n_cat}/{len(resid)} PNs "
        f"({n_cat/len(resid):.1%}), EUR {eur_cat:,.0f}/{eur_tot:,.0f} "
        f"({eur_cat/eur_tot if eur_tot else 0:.1%}); BVP hits {n_bvp}"
    )
    print(f"  empirical L3 fallbacks {len(emp_l3)}; key_no modals {len(key_modal)}")

    hs_modal, fig_modal, noun_modal, ok_ref = build_modals(master, aud)
    # attach hs/fig onto classified book for loose on-the-fly lookups
    ok_ref = ok_ref.merge(aud[["pn", "hs6", "fig_key"]], left_on="part_number", right_on="pn", how="left")
    if "hs6_x" in ok_ref.columns:
        ok_ref["_hs6"] = ok_ref["hs6_x"].fillna(ok_ref.get("hs6_y", "")).astype(str).str[:6]
    else:
        ok_ref["_hs6"] = ok_ref["hs6"].fillna("").astype(str).str[:6]
    if "fig_key_x" in ok_ref.columns:
        ok_ref["_fig"] = ok_ref["fig_key_x"].fillna(ok_ref.get("fig_key_y", "")).astype(str)
    elif "fig_key" in ok_ref.columns:
        ok_ref["_fig"] = ok_ref["fig_key"].fillna("").astype(str)
    else:
        ok_ref["_fig"] = ""
    _ok_ref = ok_ref
    desc_rules = load_gap_rules()
    eq_hits = load_eq_hits()
    print(
        f"  residual PNs {len(resid)}  hs_modals {len(hs_modal)}  "
        f"fig_modals {len(fig_modal)}  eq_hits {len(eq_hits)}"
    )

    rows = []
    dim_vote_n = 0
    dim_vote_eur = 0.0
    for r in resid.itertuples(index=False):
        desc = r.description or ""
        desc_u = desc.upper()
        signals = []

        # 1 Description
        dhit = desc_signal(desc, desc_rules, noun_modal)
        if dhit:
            l1, l2, l3, src, w, weak = dhit
            signals.append(
                {"l1": l1, "l2": l2, "l3": l3, "source": src, "weight": w, "weak": weak}
            )

        # 2 HS6
        hs6 = str(r.hs6 or "")[:6]
        if hs6 and hs6 in hs_modal:
            l1, l2, l3, share, n = hs_modal[hs6]
            signals.append(
                {
                    "l1": l1,
                    "l2": l2,
                    "l3": l3,
                    "source": f"hs6:{hs6}",
                    "weight": float(share),
                    "weak": n < 5 or share < 0.55,
                }
            )
        elif hs6 and len(hs6) == 6:
            # on-the-fly loose majority from classified master
            sub = _ok_ref[_ok_ref["_hs6"] == hs6] if "_hs6" in _ok_ref.columns else pd.DataFrame()
            if len(sub) >= 2:
                trips = list(zip(sub["L1"], sub["L2"], sub["L3"]))
                hit = _modal_triple(trips, min_n=2, min_share=0.50)
                if hit:
                    l1, l2, l3, share, n = hit
                    signals.append(
                        {
                            "l1": l1,
                            "l2": l2,
                            "l3": l3,
                            "source": f"hs6_loose:{hs6}",
                            "weight": float(share) * 0.7,
                            "weak": True,
                        }
                    )

        # 3 Fig key
        fk = str(r.fig_key or "")
        if fk and fk in fig_modal:
            l1, l2, l3, share, n = fig_modal[fk]
            signals.append(
                {
                    "l1": l1,
                    "l2": l2,
                    "l3": l3,
                    "source": f"fig:{fk}",
                    "weight": float(share),
                    "weak": n < 5 or share < 0.55,
                }
            )
        elif fk:
            sub = _ok_ref[_ok_ref["_fig"] == fk] if "_fig" in _ok_ref.columns else pd.DataFrame()
            if len(sub) >= 2:
                trips = list(zip(sub["L1"], sub["L2"], sub["L3"]))
                hit = _modal_triple(trips, min_n=2, min_share=0.50)
                if hit:
                    l1, l2, l3, share, n = hit
                    signals.append(
                        {
                            "l1": l1,
                            "l2": l2,
                            "l3": l3,
                            "source": f"fig_loose:{fk}",
                            "weight": float(share) * 0.7,
                            "weak": True,
                        }
                    )

        # 3b key_no — only if fig did not already vote (avoids double-count same peers)
        fig_voted = any(s["source"].startswith("fig") for s in signals)
        kn = _clean_label(getattr(r, "key_no", ""))
        if kn and not fig_voted and kn in key_modal:
            l1, l2, l3, share, n = key_modal[kn]
            signals.append(
                {
                    "l1": l1,
                    "l2": l2,
                    "l3": l3,
                    "source": f"key:{kn}",
                    "weight": float(share) * 0.75,
                    "weak": True,  # corroboration only
                }
            )

        # 4 Price / class
        ph = price_signal(float(r.list_eur or 0) or 0.0, str(r.price_class or ""), desc_u)
        if ph:
            l1, l2, l3, meth, w = ph
            signals.append(
                {
                    "l1": l1,
                    "l2": l2,
                    "l3": l3,
                    "source": f"price:{meth}",
                    "weight": w,
                    "weak": w < 0.8,
                }
            )

        # 5 Dimension (catalog + BVP)
        cat_row = cat_by_pn.get(r.pn)
        bvp_row = bvp_by_pn.get(r.pn)
        dsig, dim_fields = dim_signal(r.pn, cat_row, bvp_row, emp_l3)
        if dsig:
            signals.append(dsig)
            dim_vote_n += 1
            dim_vote_eur += float(r.billed_eur or 0)

        result = vote(signals)

        # EQ last resort
        eq_used = False
        if result["status"] in ("needs_eq", "conflict_needs_eq", "agree1_weak") or not result["l1"]:
            if r.pn in eq_hits:
                el1, el2, el3, emeth = eq_hits[r.pn]
                result = {
                    "status": "eq_last_resort",
                    "agree_n": result.get("agree_n", 0),
                    "strong_n": result.get("strong_n", 0),
                    "l1": el1,
                    "l2": el2 or "",
                    "l3": el3 or "",
                    "method": emeth,
                    "notes": (result.get("notes") or "") + "; EQ_LAST_RESORT",
                }
                eq_used = True

        rows.append(
            {
                "pn": r.pn,
                "description": desc,
                "billed_eur": float(r.billed_eur or 0),
                "step_eur": float(r.step_eur or 0),
                "hs6": hs6,
                "fig_key": fk,
                "key_no": kn,
                "list_eur": r.list_eur,
                "price_class": r.price_class,
                "status": result["status"],
                "agree_n": result.get("agree_n", 0),
                "strong_n": result.get("strong_n", 0),
                "proposed_aim_l1": result["l1"],
                "proposed_aim_l2": result["l2"],
                "proposed_aim_l3": result["l3"],
                "method": result["method"],
                "notes": result["notes"],
                "eq_used": eq_used,
                "n_signals": len(signals),
                **dim_fields,
            }
        )

    out = pd.DataFrame(rows).sort_values("billed_eur", ascending=False)
    out.to_csv(OUT_CSV, index=False)

    # Patch for agree3 (file only — not applied to master)
    patch = out[out["status"].isin(["agree3_high"])].copy()
    patch.to_csv(OUT_PATCH, index=False)

    print(
        f"  dim votes fired: {dim_vote_n}/{len(resid)} PNs "
        f"({dim_vote_n/len(resid):.1%}), EUR {dim_vote_eur:,.0f} "
        f"({dim_vote_eur/eur_tot if eur_tot else 0:.1%} of residual billed)"
    )

    # Excel
    wb = Workbook()
    navy = Font(bold=True, color="FFFFFF")
    head = PatternFill("solid", fgColor="15233C")
    title = Font(bold=True, size=14, color="15233C")
    ov = wb.active
    ov.title = "Overview"
    ov["A1"] = (
        "Not on AIM — 5-signal re-score "
        "(desc + HS6 + fig + price + product dimension), EQ last resort"
    )
    ov["A1"].font = title
    ov["A2"] = (
        "Previous medium was a waterfall (first hit wins). This pass votes five signals. "
        "Dimension vote uses parts_catalog_dimension (pr00 / fig label / PMS) plus "
        "bvp_pn_dimension when the PN hits. agree3_high = 3+ strong sources on same L1 "
        "(ready to apply — not applied in this run). EQ only when signals fail or conflict. "
        "Tools/MX2 already excluded."
    )
    ov.merge_cells("A2:F2")
    ov["A2"].alignment = Alignment(wrap_text=True)
    ov.row_dimensions[2].height = 56

    summ = (
        out.groupby("status")
        .agg(pn=("pn", "nunique"), billed=("billed_eur", "sum"), step=("step_eur", "sum"))
        .reset_index()
        .sort_values("billed", ascending=False)
    )
    ov["A4"] = "Status"
    ov["B4"] = "Part numbers"
    ov["C4"] = "Parts billed EUR"
    ov["D4"] = "Step EUR"
    for c in ov[4]:
        c.fill = head
        c.font = navy
    for i, r in enumerate(summ.itertuples(index=False), 5):
        ov.cell(i, 1, r.status)
        ov.cell(i, 2, int(r.pn))
        c = ov.cell(i, 3, float(r.billed))
        c.number_format = "#,##0.00"
        c2 = ov.cell(i, 4, float(r.step))
        c2.number_format = "#,##0.00"

    cov_row = 5 + len(summ) + 1
    ov.cell(cov_row, 1, "Dimension coverage")
    ov.cell(cov_row + 1, 1, "Catalog join PNs")
    ov.cell(cov_row + 1, 2, n_cat)
    ov.cell(cov_row + 1, 3, f"{n_cat/len(resid):.1%} of residual")
    ov.cell(cov_row + 2, 1, "Catalog join billed EUR")
    c = ov.cell(cov_row + 2, 2, eur_cat)
    c.number_format = "#,##0.00"
    ov.cell(cov_row + 2, 3, f"{eur_cat/eur_tot if eur_tot else 0:.1%} of residual")
    ov.cell(cov_row + 3, 1, "Dim vote fired PNs")
    ov.cell(cov_row + 3, 2, dim_vote_n)
    ov.cell(cov_row + 3, 3, f"{dim_vote_n/len(resid):.1%} of residual")
    ov.cell(cov_row + 4, 1, "Dim vote billed EUR")
    c = ov.cell(cov_row + 4, 2, dim_vote_eur)
    c.number_format = "#,##0.00"
    ov.cell(cov_row + 4, 3, f"{dim_vote_eur/eur_tot if eur_tot else 0:.1%} of residual")
    ov.cell(cov_row + 5, 1, "BVP PN hits")
    ov.cell(cov_row + 5, 2, n_bvp)
    ov.cell(cov_row + 6, 1, "Applied to aim_master?")
    ov.cell(cov_row + 6, 2, "NO — score only")

    ov.column_dimensions["A"].width = 28
    ov.column_dimensions["B"].width = 14
    ov.column_dimensions["C"].width = 22
    ov.column_dimensions["D"].width = 14

    cols = [
        "pn",
        "description",
        "billed_eur",
        "step_eur",
        "status",
        "agree_n",
        "strong_n",
        "proposed_aim_l1",
        "proposed_aim_l2",
        "proposed_aim_l3",
        "method",
        "hs6",
        "fig_key",
        "key_no",
        "list_eur",
        "price_class",
        "dim_source",
        "dim_vote_strength",
        "dim_mapped_l1",
        "dim_mapped_l2",
        "dim_mapped_l3",
        "dim_pms_category",
        "dim_pr00_group",
        "dim_pr00_level3",
        "dim_fig_label",
        "dim_bvp_family",
        "n_signals",
        "eq_used",
        "notes",
    ]
    rename = {
        "pn": "Part number",
        "description": "Description",
        "billed_eur": "Parts billed EUR",
        "step_eur": "Step EUR",
        "status": "Status",
        "agree_n": "Agree sources",
        "strong_n": "Strong agree",
        "proposed_aim_l1": "Proposed AIM L1",
        "proposed_aim_l2": "Proposed AIM L2",
        "proposed_aim_l3": "Proposed AIM L3",
        "method": "Method",
        "hs6": "HS6",
        "fig_key": "Fig key",
        "key_no": "Key no",
        "list_eur": "List EUR",
        "price_class": "Price class",
        "dim_source": "Dim source",
        "dim_vote_strength": "Dim strength",
        "dim_mapped_l1": "Dim → L1",
        "dim_mapped_l2": "Dim → L2",
        "dim_mapped_l3": "Dim → L3",
        "dim_pms_category": "Dim PMS category",
        "dim_pr00_group": "Dim PR00 group",
        "dim_pr00_level3": "Dim PR00 level-3",
        "dim_fig_label": "Dim fig label",
        "dim_bvp_family": "Dim BVP family",
        "n_signals": "Signals fired",
        "eq_used": "EQ used",
        "notes": "Notes",
    }

    def sheet(name, df):
        w = wb.create_sheet(name[:31])
        use = df[[c for c in cols if c in df.columns]].rename(columns=rename)
        for row in dataframe_to_rows(use, index=False, header=True):
            w.append(row)
        for cell in w[1]:
            cell.fill = head
            cell.font = navy
        headers = [c.value for c in w[1]]
        for col_i, h in enumerate(headers, 1):
            for row in range(2, w.max_row + 1):
                cell = w.cell(row, col_i)
                if h in ("Parts billed EUR", "Step EUR", "List EUR") and isinstance(
                    cell.value, (int, float)
                ):
                    cell.number_format = "#,##0.00"
            w.column_dimensions[get_column_letter(col_i)].width = min(28, max(11, len(str(h)) + 2))
        w.auto_filter.ref = w.dimensions
        w.freeze_panes = "A2"

    sheet("1 Agree3 HIGH apply", out[out["status"] == "agree3_high"])
    sheet("2 Agree2 review", out[out["status"] == "agree2_review"])
    sheet("3 Single strong desc", out[out["status"] == "agree1_desc_strong"])
    sheet("4 Weak or conflict", out[out["status"].isin(["agree1_weak", "conflict_needs_eq"])])
    sheet("5 EQ last resort", out[out["status"] == "eq_last_resort"])
    sheet("6 Still needs EQ", out[out["status"] == "needs_eq"])
    sheet("All scored", out)

    wb.save(OUT_XLSX)
    OPEN_CMD.write_text(
        '@echo off\r\nstart "" "%~dp0Not_on_AIM_spine_4SIGNAL_classify_20260919.xlsx"\r\n',
        encoding="ascii",
        newline="",
    )

    print("\nSTATUS")
    print(summ.to_string(index=False))
    print("\nagree3_high billed", float(patch["billed_eur"].sum()), "pns", len(patch))
    print("OUT", OUT_XLSX)
    print("PATCH", OUT_PATCH)
    print("OPEN", OPEN_CMD)
    print("Master NOT patched (score only).")


if __name__ == "__main__":
    main()
