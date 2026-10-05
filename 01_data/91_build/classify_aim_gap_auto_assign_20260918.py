#!/usr/bin/env python3
"""Auto-classify pricing-revision AIM gap PNs (Not on AIM spine).

Writes reviewable CSVs only — does NOT patch aim_master_v2.csv.

  python 01_data/91_build/classify_aim_gap_auto_assign_20260918.py
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"

OUT_ASSIGN = D / "aim_gap_auto_assign_20260918.csv"
OUT_SUMMARY = D / "aim_gap_auto_assign_20260918_SUMMARY.md"
OUT_PATCH = D / "aim_gap_master_patch_proposal_20260918.csv"

PLACEHOLDER = {"", "Unknown", "Unknown Review", "nan", "None", "NaN", "Not on AIM spine"}

# Old suggestion / workbook L1 → AIM spine L1 (Jerome taxonomy 2026-09-17)
OLD_TO_SPINE = {
    "Body Exterior": "Accident & Body",
    "Accident parts": "Accident & Body",
    "Hardware & consumables": "Chassis Frame",
    "Repair parts": None,  # too broad — do not map alone
    "Competitive parts": None,
    "High value repair": None,
    "Comfort parts": "Cabin Interior",
    "Other / review": None,
}

# Description-root → (L1, L2, L3) high-confidence rules
# Order matters: first match wins inside rule_desc.
DESC_RULES: list[tuple[re.Pattern, str, str, str, str]] = [
    # Engines / complete assemblies
    (re.compile(r"^ENGINE\s*ASM", re.I), "Engine", "Complete Assembly", "Engine Assembly", "rule_desc"),
    (re.compile(r"^ENGINE\s*ASSEMBLY", re.I), "Engine", "Complete Assembly", "Engine Assembly", "rule_desc"),
    (re.compile(r"^SHORT\s*BLOCK|^LONG\s*BLOCK|^BLOCK\s*ASM;\s*CYL", re.I), "Engine", "Block & Structure", "Cylinder Block", "rule_desc"),
    # Cabs / body shells
    (re.compile(r"^CAB\s*ASM", re.I), "Accident & Body", "Panels", "Cab", "rule_desc"),
    (re.compile(r"^CABIN\s*ASM|^CAB\s*ASSEMBLY", re.I), "Accident & Body", "Panels", "Cab", "rule_desc"),
    (re.compile(r"^BODY\s*ASM", re.I), "Accident & Body", "Panels", "Panel", "rule_desc"),
    (re.compile(r"^FRAME\s*ASM", re.I), "Chassis Frame", "Side Rail & Crossmember", "Frame", "rule_desc"),
    # EV / high-voltage
    (re.compile(r"HIGH\s*VOLTAGE|HV\s*BATTERY|BATTERY\s*ASM;\s*HIGH", re.I), "Electrical", "Charging", "HV Battery", "rule_desc"),
    (re.compile(r"^INVERTER|^CONVERTER;\s*DC|^DC.?DC\s*CONVERTER|^TRACTION\s*MOTOR|^MOTOR\s*ASM;\s*TRAC", re.I), "Electrical", "Motors & Actuators", "EV Drive", "rule_desc"),
    (re.compile(r"ON.?BOARD\s*CHARGER|^CHARGER\s*ASM;\s*EV|^EV\s*CHARGER", re.I), "Electrical", "Charging", "EV Charger", "rule_desc"),
    # Special tools (description)
    (re.compile(
        r"(SPECIAL\s*TOOL|ACTIVATION\s*TOOL|DRIVER\s*TOOL|INSTALLER|REMOVER|"
        r"COMPRESSION\s*GAUGE|DIAL\s*GAUGE|GAUGE\s*PLATE|^TESTER$|^TESTER;|"
        r"PULLER|WRENCH|TOOL\s*SET|^ARBOR$|^PILOT$|AIMING\s*TARGET|"
        r"CAMERA\s*AIMING|SLINGER\s*PULLER)",
        re.I,
    ), "Tools Equipment", "Workshop Tools", "Tool", "rule_desc"),
    # Clear family nouns
    (re.compile(r"^CLUTCH\s*ASM|^CLUTCH\s*KIT", re.I), "Clutch", "Clutch Kit", "Clutch Kit", "rule_desc"),
    (re.compile(r"^TRANSMISSION\s*ASM", re.I), "Transmission", "Geartrain", "Transmission Assembly", "rule_desc"),
    (re.compile(r"^TRANSFER\s*ASM", re.I), "Driveline Axle", "Final Drive", "Transfer Case", "rule_desc"),
    (re.compile(r"^SHAFT\s*ASM;\s*FRT\s*DRIVE|^SHAFT\s*ASM;\s*PROP", re.I), "Driveline Axle", "Axle Shaft", "Drive Shaft", "rule_desc"),
    (re.compile(r"^AXLE;\s*FRT|^AXLE;\s*RR|^CASE;\s*FRT\s*AXLE", re.I), "Driveline Axle", "Final Drive", "Final Drive Asm", "rule_desc"),
    (re.compile(r"^SENSOR;\s*(SPEED|MAP|O2|NOX|TIRE|DEF|SPD)", re.I), "Electrical", "Instruments", "Sensor", "rule_desc"),
    (re.compile(r"^HARNESS;", re.I), "Electrical", "Harness & Connectors", "Harness", "rule_desc"),
    (re.compile(r"^RADIO\s*CONTROL|^CONTROL\s*ASM;\s*STEREO|^STEREO", re.I), "Cabin Interior", "Dashboard & Controls", "Audio", "rule_desc"),
    (re.compile(r"^BLADE;\s*WIPER|^WIPER\s*BLADE", re.I), "Maintenance Service", "Wiper", "Wiper Blade", "rule_desc"),
    (re.compile(r"^LINK;\s*DRAG|^ROD\s*END|^JOINT\s*ASM;\s*BALL", re.I), "Steering", "Linkage", "Drag Link", "rule_desc"),
    (re.compile(r"^CHAMBER;\s*POWER|^EXPANDER$|^BRAKE\s*UNIT;\s*EXH", re.I), "Brakes", "Actuation", "Air Chamber", "rule_desc"),
    (re.compile(r"^PAD\s*KIT|^SHOE\s*KIT|^DISC;\s*BRK|^DRUM;\s*BRK|^CALIPER", re.I), "Brakes", "Pads & Shoes", "Brake Friction", "rule_desc"),
    (re.compile(r"^COOLER;\s*CHARGE\s*AIR|^INTERCOOLER", re.I), "Intake Exhaust Emission", "Turbo", "Charge Air Cooler", "rule_desc"),
    (re.compile(r"^THROTTLE\s*ASM|^RAIL;?\s*COMMON|^RAIL\s*ASM;\s*COMMON|^LIMITER;\s*FUEL|^NOZZLE\s*ASM;\s*INJ|^PUMP\s*ASM;\s*INJ", re.I), "Fuel System", "Injection", "Injector / Rail", "rule_desc"),
    (re.compile(r"^PAN\s*ASM;\s*OIL|^OIL\s*PAN", re.I), "Engine", "Block & Structure", "Oil Pan", "rule_desc"),
    (re.compile(r"^SEAT|^CUSHION\s*ASM;\s*PASSENGER|^CUSHION;\s*SEAT|^BACK\s*ASM;\s*PASSENGER", re.I), "Cabin Interior", "Seat", "Seat Cushion", "rule_desc"),
    (re.compile(r"^MIRROR", re.I), "Accident & Body", "Mirrors", "Mirror", "rule_desc"),
    (re.compile(r"^LAMP\s*ASM|^LAMP;", re.I), "Lighting", "Lighting", "Lamp", "rule_desc"),
    (re.compile(r"^GLASS;", re.I), "Accident & Body", "Glass", "Glass", "rule_desc"),
    (re.compile(r"^FILTER|^ELEMENT;\s*(OIL|FUEL|AIR)|^CARTRIDGE\s*KIT;\s*FUEL|^ELEMENT\s*KIT;\s*FUEL", re.I), "Maintenance Service", "Filters", "Filter", "rule_desc"),
    (re.compile(r"^REBATE|^TRANSPORT|^FREIGHT|^HANDLING|0TRANSPORT|0000REBATE", re.I), "Logistics Packaging", "Packaging", "Non-part", "rule_desc"),
    (re.compile(r"\b15W40\b|\bATF\b|GREASE|CLEANER|BESCO|LUBRICANT|T/AXLEOIL|GEAROIL|RIM\s*R4|CK4_|CJ4_", re.I), "Fluids Chemicals", "Lubricants", "Fluid", "rule_desc"),
    (re.compile(r"^SPRING\s*ASM;\s*LEAF|^LEAF\s*SPRING", re.I), "Suspension", "Springs", "Leaf Spring", "rule_desc"),
    (re.compile(r"^KEY;\s*BLANK", re.I), "Accident & Body", "Locks & Handles", "Key", "rule_desc"),
    (re.compile(r"^BATTERY$", re.I), "Electrical", "Charging", "Battery", "rule_desc"),
    (re.compile(r"^COVER;\s*BATTERY|^TRAY;\s*BATTERY|^CABLE;\s*BATTERY", re.I), "Electrical", "Charging", "Battery Accessory", "rule_desc"),
    (re.compile(r"^REPAIR\s*KIT;\s*AIR\s*DRYER|^DRYER;\s*AIR|^AIR\s*DRYER", re.I), "Brakes", "Air System", "Air Dryer", "rule_desc"),
    (re.compile(r"^ADJUSTER;\s*VLV\s*LASH|^VALVE;\s*EVRV", re.I), "Engine", "Valve Train", "Valve", "rule_desc"),
    (re.compile(r"^COVER;\s*RADAR", re.I), "Accident & Body", "Panels", "ADAS Cover", "rule_desc"),
    (re.compile(r"^BOLSTER;|^EMBLEM;", re.I), "Accident & Body", "Trim", "Trim", "rule_desc"),
    (re.compile(r"^INTERFACE\s*MX|^TELEMATIC|^TACHograph|^DIGITAL\s*TACHO", re.I), "Electrical", "Control Units", "Telematics", "rule_desc"),
    # Residual top nouns (second pass)
    (re.compile(r"^SENSOR;", re.I), "Electrical", "Instruments", "Sensor", "rule_desc"),
    (re.compile(r"^CAMERA\s*ASM|^CAMERA;", re.I), "Electrical", "Control Units", "Camera / ADAS", "rule_desc"),
    (re.compile(r"^CONDENSER\s*ASM;\s*A/C|^COMPRESSOR\s*ASM;\s*A/C|^CORE;\s*HTR|^HEATER;\s*COOLING|^EVAPORATOR", re.I), "Cabin Interior", "HVAC Filters", "HVAC", "rule_desc"),
    (re.compile(r"^HEAD\s*ASM;\s*CYL|^CYLINDER\s*HEAD", re.I), "Engine", "Cylinder Head", "Cylinder Head", "rule_desc"),
    (re.compile(r"^BEARING;\s*CLU|^RELEASE\s*BEARING|BLOCK;\s*SHIFT,?\s*CLU", re.I), "Clutch", "Release System", "Release Bearing", "rule_desc"),
    (re.compile(r"^KNUCKLE;|^ARM;\s*UPR\s*CONT|^ARM;\s*LWR\s*CONT|^CONTROL\s*ARM", re.I), "Suspension", "Arms & Links", "Control Arm", "rule_desc"),
    (re.compile(r"^RING;\s*BLOCK|^GEAR\s*SET;|^SYNCHRONIZER|^HUB;\s*SYNCHRO", re.I), "Transmission", "Geartrain", "Gear", "rule_desc"),
    (re.compile(r"^RUBBER;\s*CUSHION,?\s*ENG|^FOOT;\s*ENG|^MOUNT;\s*ENG|^MOUNTING;\s*ENG", re.I), "Engine", "Mounting", "Engine Mount", "rule_desc"),
    (re.compile(r"^GUIDE\s*ASM;\s*AIR|^DUCT;\s*AIR|^PIPE;\s*AIR\s*INT", re.I), "Intake Exhaust Emission", "Air Intake", "Air Guide", "rule_desc"),
    (re.compile(r"^MANIFOLD;\s*INL|^MANIFOLD;\s*EXH", re.I), "Intake Exhaust Emission", "Manifold", "Manifold", "rule_desc"),
    (re.compile(r"^HOSE;|^PIPE;\s*(WATER|FUEL|INJ|VAC)", re.I), "Chassis Frame", "Mounting Hardware", "Hose / Pipe", "rule_desc"),
    (re.compile(r"^BOLT;|^NUT;|^WASHER;|^SCREW;|^CLIP;|^CLAMP;|^RIVET;", re.I), "Chassis Frame", "Mounting Hardware", "Fastener", "rule_desc"),
    (re.compile(r"^GASKET;|^SEAL;|^O-RING|^O\s*RING|^OIL\s*SEAL", re.I), "Engine", "Gasket & Sealing", "Gasket", "rule_desc"),
    (re.compile(r"^BRACKET;|^SUPPORT;|^HANGER;(?!.*HIGH\s*VOLTAGE)", re.I), "Chassis Frame", "Crossmember & Brackets", "Bracket", "rule_desc"),
    (re.compile(r"^PANEL\s*ASM|^PANEL;|^FENDER|^DOOR\s*ASM|^BUMPER|^GRILLE|^STEP;", re.I), "Accident & Body", "Panels", "Panel", "rule_desc"),
    (re.compile(r"^SWITCH;|^RELAY;|^FUSE;", re.I), "Electrical", "Switch Relay Fuse", "Switch", "rule_desc"),
    (re.compile(r"^PUMP\s*ASM;\s*FUEL|^PUMP;\s*FUEL|^PUMP\s*ASM;\s*WATER|^PUMP;\s*WATER", re.I), "Fuel System", "Pumps", "Pump", "rule_desc"),
    (re.compile(r"^TURBO|^TURBOCHARGER", re.I), "Intake Exhaust Emission", "Turbo", "Turbocharger", "rule_desc"),
    (re.compile(r"^RADIATOR|^COOLER;\s*(?!CHARGE)", re.I), "Cooling", "Radiator", "Radiator", "rule_desc"),
    (re.compile(r"^GUSSET;|^CROSSMEMBER|^C/MBR", re.I), "Chassis Frame", "Crossmember & Brackets", "Crossmember", "rule_desc"),
    (re.compile(r"^CLUTCH;\s*COOLING\s*FAN|^FAN\s*CLUTCH", re.I), "Cooling", "Fan", "Fan Clutch", "rule_desc"),
    (re.compile(r"^PIPE\s*ASM;\s*INJ|^PIPE;\s*INJ", re.I), "Fuel System", "Injection", "Injection Pipe", "rule_desc"),
    (re.compile(r"^HEATER\s*UNIT|^HEATER\s*ASM", re.I), "Cabin Interior", "HVAC Filters", "HVAC", "rule_desc"),
    (re.compile(r"^JOINT\s*ASM;\s*OUTSIDE|^JOINT\s*ASM;\s*INSIDE|^CV\s*JOINT", re.I), "Driveline Axle", "Axle Shaft", "Drive Shaft", "rule_desc"),
    (re.compile(r"^PLUG;\s*DRAIN|^DRAIN\s*PLUG", re.I), "Engine", "Block & Structure", "Drain Plug", "rule_desc"),
    (re.compile(r"^HYDRAULIC\s*UNIT;\s*ANTI\s*LOCK|^BOOSTER;\s*HYDRAULIC\s*BRK|^ABS\s*UNIT", re.I), "Brakes", "Actuation", "ABS / Booster", "rule_desc"),
    (re.compile(r"^RETAINER;\s*RR\s*AXLE|^RETAINER;\s*AXLE", re.I), "Driveline Axle", "Final Drive Bearings & Seals", "Axle Seal", "rule_desc"),
    (re.compile(r"^JOURNAL\s*ASM;\s*PROP|^YOKE;\s*PROP", re.I), "Driveline Axle", "Axle Shaft", "Prop Shaft", "rule_desc"),
    (re.compile(r"^REPAIR\s*KIT;\s*STRG|^STEERING\s*GEAR|^GEAR\s*ASM;\s*STRG", re.I), "Steering", "Gear", "Steering Gear", "rule_desc"),
    (re.compile(r"^RESISTOR$|^RESISTOR;", re.I), "Electrical", "Switch Relay Fuse", "Resistor", "rule_desc"),
    (re.compile(r"^ROD;\s*TIE|^TIE\s*ROD", re.I), "Steering", "Linkage", "Tie Rod", "rule_desc"),
    (re.compile(r"^BOOSTER\s*ASM;\s*CLU|^BOOSTER;\s*CLU", re.I), "Clutch", "Release System", "Clutch Booster", "rule_desc"),
    (re.compile(r"^BACK\s*ASM;\s*SEAT|^BACK;\s*SEAT", re.I), "Cabin Interior", "Seat", "Seat Back", "rule_desc"),
    (re.compile(r"^JOINT\s*ASM$", re.I), "Driveline Axle", "Axle Shaft", "Joint", "rule_desc"),
    (re.compile(r"^CAGE\s*ASM;\s*DIFF|^CASE;\s*RR\s*AXLE|^BEARING;\s*RR\s*AXLE", re.I), "Driveline Axle", "Differential", "Differential", "rule_desc"),
    (re.compile(r"^BEARING\s*ASM;\s*CTR|^BEARING;\s*CTR", re.I), "Driveline Axle", "Axle Shaft", "Prop Shaft", "rule_desc"),
    (re.compile(r"^GUIDE\s*ASM\s*[:;]\s*AIR", re.I), "Intake Exhaust Emission", "Air Intake", "Air Guide", "rule_desc"),
    (re.compile(r"^CHAMBER\s*ASM;\s*SPRING|^BRAKE\s*ASM;\s*PARKING", re.I), "Brakes", "Actuation", "Brake Assembly", "rule_desc"),
    (re.compile(r"^RUBBER;\s*(SUB\s*SPRING|MTG,?\s*CAB|CUSHION)", re.I), "Suspension", "Bushings", "Rubber Mount", "rule_desc"),
    (re.compile(r"^LINER;\s*C/BL|^LINER\s*SET;\s*ENG|^LINER;\s*CYL", re.I), "Engine", "Block & Structure", "Cylinder Liner", "rule_desc"),
    (re.compile(r"^RING;\s*FUEL\s*INJ|^METAL;\s*CM|^COVER;\s*CYL\s*HD|^PULLEY;\s*IDLE", re.I), "Engine", "Internal Rotating", "Engine Internal", "rule_desc"),
    (re.compile(r"^SHAFT;\s*STRG|^SHAFT\s*ASM;\s*STRG", re.I), "Steering", "Column", "Steering Shaft", "rule_desc"),
    (re.compile(r"^RING;\s*INSIDE|^RING;\s*OUTSIDE|^SLEEVE$", re.I), "Transmission", "Geartrain", "Synchronizer", "rule_desc"),
    (re.compile(r"^PIN;\s*LOCK|^CAP;\s*KNUCKLE", re.I), "Suspension", "Arms & Links", "Knuckle Hardware", "rule_desc"),
]

# 5884* is the dedicated workshop-tool band in AIM master (plus desc keywords above)
TOOL_PN_PREFIXES = {"5884"}

# Price floors for expensive complete assemblies when desc is weak but pattern matches
PRICE_ENGINE_EUR = 3000.0
PRICE_CAB_EUR = 2000.0


def _norm_pn(s: object) -> str:
    t = "" if s is None or (isinstance(s, float) and np.isnan(s)) else str(s).strip()
    t = re.sub(r"\.0$", "", t)
    if t.isdigit():
        return t.zfill(10)
    return t


def _desc_root(desc: str) -> str:
    return desc.split(";")[0].strip().upper()


def _is_placeholder(val: object) -> bool:
    s = "" if val is None or (isinstance(val, float) and np.isnan(val)) else str(val).strip()
    return s in PLACEHOLDER


def load_gap() -> pd.DataFrame:
    lines = pd.read_parquet(D / "pricing_aim_source_lines.parquet")
    gap = lines[lines["aim_l1"].astype(str).str.contains("Not on AIM", case=False, na=False)].copy()
    gap["part_number"] = gap["part_number"].map(_norm_pn)
    agg = gap.groupby("part_number", as_index=False).agg(
        description=("description", "first"),
        billed_eur=("billed_eur", "sum"),
        prior_eur=("prior_eur", "max"),
        new_eur=("new_eur", "max"),
        qty=("qty", "sum"),
        n_lines=("db", "count"),
    )
    agg["price"] = agg["new_eur"].fillna(agg["prior_eur"])
    # Prefer list price from audit when cube has no price
    aud = pd.read_csv(D / "_audit_cls_spine.csv", dtype=str, low_memory=False)
    aud["pn"] = aud["pn"].map(_norm_pn)
    aud["list_eur"] = pd.to_numeric(aud["list_eur"], errors="coerce")
    aud = aud.drop_duplicates("pn")
    agg = agg.merge(
        aud[["pn", "hs", "hs4", "hs6", "list_eur", "l1", "l2", "l3", "wb_l1", "wb_l2", "wb_l3", "noun"]],
        left_on="part_number",
        right_on="pn",
        how="left",
    )
    agg["price"] = agg["price"].fillna(agg["list_eur"])
    agg["description"] = agg["description"].fillna("").astype(str)
    agg["desc_u"] = agg["description"].str.upper().str.strip()
    agg["desc_root"] = agg["desc_u"].map(_desc_root)
    return agg.drop(columns=["pn"], errors="ignore")


def build_desc_precedent() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Majority AIM class by exact description and description-root from known master."""
    aim = pd.read_csv(D / "aim_master_v2.csv", dtype=str, low_memory=False)
    aim["part_number"] = aim["part_number"].map(_norm_pn)
    aim["desc_u"] = aim["description"].fillna("").astype(str).str.upper().str.strip()
    aim["desc_root"] = aim["desc_u"].map(_desc_root)
    aim["eur"] = pd.to_numeric(aim.get("l12m_billed_eur", aim.get("eur")), errors="coerce").fillna(0.0)
    known = aim[~aim["aim_l1_fixed"].map(_is_placeholder)].copy()
    known = known[known["aim_l1_fixed"].notna()]

    def maj(df: pd.DataFrame, key: str, min_share: float = 0.70, min_n: int = 2) -> pd.DataFrame:
        g = (
            df.groupby([key, "aim_l1_fixed", "aim_l2_fixed", "aim_l3"], dropna=False)
            .agg(n=("part_number", "count"), eur=("eur", "sum"))
            .reset_index()
        )
        tot = g.groupby(key)["n"].transform("sum")
        g["share"] = g["n"] / tot
        top = g.sort_values(["n", "eur"], ascending=False).drop_duplicates(key)
        top = top[(top["share"] >= min_share) & (top["n"] >= min_n)]
        return top.set_index(key)[["aim_l1_fixed", "aim_l2_fixed", "aim_l3", "share", "n"]]

    return maj(known, "desc_u"), maj(known, "desc_root", min_share=0.75, min_n=3)


def build_hs_majority() -> pd.DataFrame:
    aim = pd.read_csv(D / "aim_master_v2.csv", dtype=str, low_memory=False)
    aim["part_number"] = aim["part_number"].map(_norm_pn)
    aud = pd.read_csv(D / "_audit_cls_spine.csv", dtype=str, low_memory=False)
    aud["pn"] = aud["pn"].map(_norm_pn)
    m = aim.merge(aud[["pn", "hs6"]], left_on="part_number", right_on="pn", how="inner")
    known = m[~m["aim_l1_fixed"].map(_is_placeholder) & m["hs6"].notna() & (m["hs6"] != "")]
    # L1 majority by HS6
    l1g = known.groupby(["hs6", "aim_l1_fixed"]).size().reset_index(name="n")
    tot = l1g.groupby("hs6")["n"].transform("sum")
    l1g["share"] = l1g["n"] / tot
    l1 = l1g.sort_values("n", ascending=False).drop_duplicates("hs6")
    l1 = l1[l1["share"] >= 0.70].copy()
    # Modal L2 for winning L1
    l2g = known.groupby(["hs6", "aim_l1_fixed", "aim_l2_fixed"]).size().reset_index(name="n2")
    l2top = l2g.sort_values("n2", ascending=False).drop_duplicates(["hs6", "aim_l1_fixed"])
    out = l1.merge(l2top, on=["hs6", "aim_l1_fixed"], how="left")
    # Modal L3
    l3g = known.groupby(["hs6", "aim_l1_fixed", "aim_l2_fixed", "aim_l3"]).size().reset_index(name="n3")
    l3top = l3g.sort_values("n3", ascending=False).drop_duplicates(["hs6", "aim_l1_fixed", "aim_l2_fixed"])
    out = out.merge(l3top, on=["hs6", "aim_l1_fixed", "aim_l2_fixed"], how="left")
    return out.set_index("hs6")[["aim_l1_fixed", "aim_l2_fixed", "aim_l3", "share", "n"]]


def load_suggestions() -> pd.DataFrame:
    p = D / "aim_gap_suggestions_20260702.csv"
    if not p.exists():
        return pd.DataFrame()
    sug = pd.read_csv(p, dtype=str, low_memory=False)
    sug["pn"] = sug["pn"].map(_norm_pn)
    sug["confidence"] = pd.to_numeric(sug["confidence"], errors="coerce")
    sug["eq_hit"] = sug.get("eq_hit", pd.Series(dtype=str)).fillna("").astype(str).str.strip()
    return sug.drop_duplicates("pn")


def tool_l3_from_desc(desc: str) -> str:
    u = desc.upper()
    if "PULLER" in u:
        return "Puller"
    if "TESTER" in u or "ACTIVATION" in u:
        return "Tester"
    if "GAUGE" in u:
        return "Gauge"
    return "Tool"


def classify(gap: pd.DataFrame) -> pd.DataFrame:
    prec_exact, prec_root = build_desc_precedent()
    hs_maj = build_hs_majority()
    sug = load_suggestions()
    sug_map = sug.set_index("pn") if len(sug) else None

    rows = []
    for r in gap.itertuples(index=False):
        pn = r.part_number
        desc = r.description or ""
        desc_u = r.desc_u or ""
        price = float(r.price) if pd.notna(r.price) else np.nan
        billed = float(r.billed_eur) if pd.notna(r.billed_eur) else 0.0
        hs = getattr(r, "hs", "") or ""
        hs6 = getattr(r, "hs6", "") or ""
        wb_l1 = getattr(r, "wb_l1", "") or ""
        wb_l2 = getattr(r, "wb_l2", "") or ""
        wb_l3 = getattr(r, "wb_l3", "") or ""

        assigned = None  # (l1, l2, l3, method, conf, notes)

        # --- 1) High-confidence description rules ---
        for pat, l1, l2, l3, method in DESC_RULES:
            if pat.search(desc_u):
                if l1 == "Tools Equipment":
                    l3 = tool_l3_from_desc(desc)
                # Price reinforce for engines/cabs
                note = f"desc match: {pat.pattern[:48]}"
                conf = "high"
                if l1 == "Engine" and l2 == "Complete Assembly" and pd.notna(price) and price < 500:
                    conf = "med"
                    note += "; price low for complete engine"
                assigned = (l1, l2, l3, method, conf, note)
                break

        # --- 2) Tool PN prefix 5884* (workshop band) ---
        if assigned is None and str(pn)[:4] in TOOL_PN_PREFIXES:
            # Skip if clearly a non-tool noun already in master patterns
            if re.search(r"SENSOR|TARGET;AEBS|INSTALLER|REMOVER|GAUGE|WRENCH|TOOL|ARBOR|PILOT|TESTER|PULLER", desc_u):
                assigned = (
                    "Tools Equipment",
                    "Workshop Tools",
                    tool_l3_from_desc(desc),
                    "rule_pn",
                    "high",
                    "PN prefix 5884 + tool-like description",
                )
            else:
                assigned = (
                    "Tools Equipment",
                    "Workshop Tools",
                    "Tool",
                    "rule_pn",
                    "med",
                    "PN prefix 5884 (workshop tool band); desc weak",
                )

        # --- 3) Price + weak assembly cues ---
        if assigned is None and pd.notna(price):
            if re.search(r"\bENGINE\b", desc_u) and price >= PRICE_ENGINE_EUR:
                assigned = (
                    "Engine",
                    "Complete Assembly",
                    "Engine Assembly",
                    "rule_price",
                    "med",
                    f"ENGINE keyword + list €{price:,.0f}",
                )
            elif re.search(r"\bCAB\b", desc_u) and price >= PRICE_CAB_EUR and "CABLE" not in desc_u:
                assigned = (
                    "Accident & Body",
                    "Panels",
                    "Cab",
                    "rule_price",
                    "med",
                    f"CAB keyword + list €{price:,.0f}",
                )

        # --- 4) Description precedent from AIM master ---
        if assigned is None and desc_u in prec_exact.index:
            hit = prec_exact.loc[desc_u]
            if isinstance(hit, pd.DataFrame):
                hit = hit.iloc[0]
            assigned = (
                str(hit["aim_l1_fixed"]),
                str(hit["aim_l2_fixed"]),
                str(hit["aim_l3"]),
                "rule_desc",
                "high" if float(hit["share"]) >= 0.85 else "med",
                f"exact-desc precedent share={float(hit['share']):.2f} n={int(hit['n'])}",
            )
        if assigned is None and r.desc_root in prec_root.index:
            hit = prec_root.loc[r.desc_root]
            if isinstance(hit, pd.DataFrame):
                hit = hit.iloc[0]
            assigned = (
                str(hit["aim_l1_fixed"]),
                str(hit["aim_l2_fixed"]),
                str(hit["aim_l3"]),
                "rule_desc",
                "med",
                f"desc-root precedent share={float(hit['share']):.2f} n={int(hit['n'])}",
            )

        # --- 5) HS6 majority ---
        if assigned is None and hs6 and hs6 in hs_maj.index:
            hit = hs_maj.loc[hs6]
            if isinstance(hit, pd.DataFrame):
                hit = hit.iloc[0]
            assigned = (
                str(hit["aim_l1_fixed"]),
                str(hit["aim_l2_fixed"]) if pd.notna(hit["aim_l2_fixed"]) else "",
                str(hit["aim_l3"]) if pd.notna(hit["aim_l3"]) else "",
                "hs",
                "med" if float(hit["share"]) >= 0.85 else "low",
                f"HS6 {hs6} majority L1 share={float(hit['share']):.2f} n={int(hit['n'])}",
            )

        # --- 6) Workbook AIM-spine labels already present ---
        if assigned is None and wb_l1 and not _is_placeholder(wb_l1) and wb_l1 not in OLD_TO_SPINE:
            # Real spine label already on workbook axis
            spine_l1s = {
                "Engine", "Accident & Body", "Chassis Frame", "Electrical", "Transmission",
                "Wheels Hub", "Lighting", "Cabin Interior", "Intake Exhaust Emission",
                "Fuel System", "Brakes", "Maintenance Service", "Suspension", "Cooling",
                "Steering", "Driveline Axle", "Lubrication", "Fluids Chemicals",
                "Tools Equipment", "Clutch", "Literature Marketing", "Logistics Packaging",
            }
            if wb_l1 in spine_l1s:
                assigned = (
                    wb_l1,
                    wb_l2 if wb_l2 and not _is_placeholder(wb_l2) else "",
                    wb_l3 if wb_l3 and not _is_placeholder(wb_l3) else "",
                    "eq_hit",
                    "med",
                    "workbook already holds AIM-spine L1",
                )

        # --- 7) Prior suggestions (high confidence) remapped ---
        if assigned is None and sug_map is not None and pn in sug_map.index:
            s = sug_map.loc[pn]
            if isinstance(s, pd.DataFrame):
                s = s.iloc[0]
            conf_n = float(s["confidence"]) if pd.notna(s["confidence"]) else 0.0
            sug_l1 = str(s.get("sug1_l1") or "")
            sug_l2 = str(s.get("sug1_l2") or "")
            mapped = OLD_TO_SPINE.get(sug_l1, sug_l1 if sug_l1 in {
                "Engine", "Accident & Body", "Chassis Frame", "Electrical", "Transmission",
                "Wheels Hub", "Lighting", "Cabin Interior", "Intake Exhaust Emission",
                "Fuel System", "Brakes", "Maintenance Service", "Suspension", "Cooling",
                "Steering", "Driveline Axle", "Lubrication", "Fluids Chemicals",
                "Tools Equipment", "Clutch", "Literature Marketing", "Logistics Packaging",
            } else None)
            eq = str(s.get("eq_hit") or "").strip()
            if mapped and conf_n >= 3.0:
                assigned = (
                    mapped,
                    sug_l2,
                    "",
                    "eq_hit" if eq else "rule_desc",
                    "med" if conf_n >= 3.5 else "low",
                    f"prior suggestion sug1={sug_l1}/{sug_l2} conf={conf_n:.2f} eq_hit={eq or 'none'}",
                )
            elif eq and eq.lower() not in ("", "0", "false", "nan"):
                assigned = (
                    mapped or "",
                    sug_l2,
                    "",
                    "eq_hit",
                    "low",
                    f"eq_hit flag only; sug1={sug_l1}; needs manual confirm",
                )

        if assigned is None:
            assigned = ("", "", "", "unassigned", "low", "no rule/HS/precedent/suggestion hit — needs EQ-Hit")

        l1, l2, l3, method, conf, notes = assigned
        # Family tags for summary
        tag = ""
        if l1 == "Engine" and l2 == "Complete Assembly":
            tag = "engine"
        elif l3 == "Cab" or re.search(r"^CAB\s*ASM", desc_u):
            tag = "cab"
        elif l1 == "Tools Equipment":
            tag = "tool"
        elif "HV Battery" in (l3 or "") or "EV " in (l3 or "") or re.search(
            r"HIGH\s*VOLTAGE|INVERTER|TRACTION\s*MOTOR|EV\s*CHARGER|CONVERTER;\s*DC", desc_u
        ):
            tag = "ev"
        elif l1 == "Engine":
            tag = "engine_part"

        rows.append(
            {
                "pn": pn,
                "description": desc,
                "price": round(price, 2) if pd.notna(price) else "",
                "billed_eur": round(billed, 2),
                "hs": hs,
                "assigned_l1": l1,
                "assigned_l2": l2,
                "assigned_l3": l3,
                "method": method,
                "confidence": conf,
                "notes": notes,
                "family_tag": tag,
            }
        )

    return pd.DataFrame(rows)


def write_summary(df: pd.DataFrame) -> None:
    tot_n = len(df)
    tot_eur = df["billed_eur"].sum()
    assigned = df[df["method"] != "unassigned"]
    un = df[df["method"] == "unassigned"]

    def band(conf: str) -> pd.DataFrame:
        return assigned[assigned["confidence"] == conf]

    lines = []
    lines.append("# AIM gap auto-assign — 18 Sep 2026")
    lines.append("")
    lines.append(
        f"The pricing-revision gap (parts not on the AIM spine) is **{tot_n:,} part numbers** "
        f"and **€{tot_eur:,.0f}** billed in the revision window. This file proposes families "
        f"for review. It does **not** change the live AIM master."
    )
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    for conf in ("high", "med", "low"):
        b = band(conf)
        lines.append(
            f"- {conf}: {len(b):,} PNs / €{b['billed_eur'].sum():,.0f} "
            f"({100 * b['billed_eur'].sum() / tot_eur:.1f}% of gap €)"
        )
    lines.append(
        f"- still unassigned: {len(un):,} PNs / €{un['billed_eur'].sum():,.0f} "
        f"({100 * un['billed_eur'].sum() / tot_eur:.1f}% of gap €) — these need a manual EQ-Hit look"
    )
    lines.append("")
    lines.append("## How the euro was assigned")
    lines.append("")
    by_m = (
        assigned.groupby("method")
        .agg(pns=("pn", "count"), eur=("billed_eur", "sum"))
        .sort_values("eur", ascending=False)
    )
    for method, row in by_m.iterrows():
        lines.append(f"- {method}: {int(row['pns']):,} PNs / €{row['eur']:,.0f}")
    lines.append("")
    lines.append("## Top families proposed")
    lines.append("")
    by_l1 = (
        assigned[assigned["assigned_l1"] != ""]
        .groupby("assigned_l1")
        .agg(pns=("pn", "count"), eur=("billed_eur", "sum"))
        .sort_values("eur", ascending=False)
        .head(15)
    )
    for l1, row in by_l1.iterrows():
        lines.append(f"- {l1}: {int(row['pns']):,} PNs / €{row['eur']:,.0f}")
    lines.append("")
    lines.append("## Engines, cabs, special tools, EV")
    lines.append("")

    def tag_block(tag: str, label: str) -> None:
        t = df[df["family_tag"] == tag]
        lines.append(
            f"- {label}: {len(t):,} PNs / €{t['billed_eur'].sum():,.0f}"
        )
        if len(t):
            top = t.nlargest(5, "billed_eur")
            for _, x in top.iterrows():
                lines.append(
                    f"  - `{x['pn']}` {x['description'][:50]} — €{x['billed_eur']:,.0f} "
                    f"→ {x['assigned_l1']} / {x['assigned_l2']} / {x['assigned_l3']} ({x['confidence']})"
                )

    tag_block("engine", "Engines (complete assembly)")
    tag_block("engine_part", "Other engine-family parts (still in the gap)")
    tag_block("cab", "Cabs")
    tag_block("tool", "Special / workshop tools")
    tag_block("ev", "EV / high-voltage")
    lines.append("")
    lines.append(
        "Note on engines: complete ENGINE ASM rows in the revision cube are already on the "
        "AIM spine under Engine → Complete Assembly, so they do not appear in this gap list. "
        "Cab ASMs, workshop tools, and high-voltage parts that were still Unknown are classified above."
    )
    lines.append("")
    lines.append("## Residual still unassigned — top 20 by billed €")
    lines.append("")
    topu = un.nlargest(20, "billed_eur")
    for _, x in topu.iterrows():
        lines.append(
            f"- `{x['pn']}` {x['description'][:55]} — €{x['billed_eur']:,.0f}"
            + (f" (list €{x['price']})" if x["price"] != "" else "")
        )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append(f"- Full assign: `{OUT_ASSIGN}`")
    lines.append(f"- High-confidence patch proposal (not applied): `{OUT_PATCH}`")
    lines.append("")
    lines.append(
        "Next step when you are ready: review the high-confidence patch file, then say "
        "rebuild/ship if you want it applied into the AIM master."
    )
    OUT_SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    existing = OUT_ASSIGN if OUT_ASSIGN.exists() else None
    gap = load_gap()
    print(f"gap PNs={len(gap):,} billed€={gap['billed_eur'].sum():,.0f}")

    df = classify(gap)

    if existing is not None:
        # Resume/merge: keep prior high-conf rows if new method is weaker
        old = pd.read_csv(existing, dtype=str, low_memory=False)
        if "pn" in old.columns and "confidence" in old.columns:
            rank = {"high": 3, "med": 2, "low": 1}
            old["pn"] = old["pn"].map(_norm_pn)
            old_r = old.set_index("pn")
            for i, row in df.iterrows():
                pn = row["pn"]
                if pn in old_r.index:
                    oc = str(old_r.loc[pn].get("confidence", "low"))
                    om = str(old_r.loc[pn].get("method", "unassigned"))
                    if rank.get(oc, 0) > rank.get(row["confidence"], 0) and om != "unassigned":
                        for c in (
                            "assigned_l1",
                            "assigned_l2",
                            "assigned_l3",
                            "method",
                            "confidence",
                            "notes",
                            "family_tag",
                        ):
                            if c in old_r.columns:
                                df.at[i, c] = old_r.loc[pn].get(c, df.at[i, c])
            print(f"merged prior {existing.name}")

    df = df.sort_values(["billed_eur"], ascending=False)
    df.to_csv(OUT_ASSIGN, index=False)

    patch = df[(df["confidence"] == "high") & (df["method"] != "unassigned") & (df["assigned_l1"] != "")]
    patch_out = patch[
        ["pn", "description", "assigned_l1", "assigned_l2", "assigned_l3", "method", "confidence", "notes", "billed_eur"]
    ].copy()
    patch_out.to_csv(OUT_PATCH, index=False)

    write_summary(df)

    # Console return for parent
    assigned = df[df["method"] != "unassigned"]
    un = df[df["method"] == "unassigned"]
    print("--- RETURN ---")
    print(f"OUT_ASSIGN={OUT_ASSIGN}")
    print(f"OUT_SUMMARY={OUT_SUMMARY}")
    print(f"OUT_PATCH={OUT_PATCH}")
    print(f"total_pns={len(df)} total_eur={df['billed_eur'].sum():.2f}")
    for c in ("high", "med", "low"):
        b = assigned[assigned["confidence"] == c]
        print(f"assigned_{c}_pns={len(b)} eur={b['billed_eur'].sum():.2f}")
    print(f"unassigned_pns={len(un)} eur={un['billed_eur'].sum():.2f}")
    for tag in ("engine", "cab", "tool", "ev"):
        t = df[df["family_tag"] == tag]
        print(f"{tag}_pns={len(t)} eur={t['billed_eur'].sum():.2f}")
    print("residual_top20:")
    for _, x in un.nlargest(20, "billed_eur").iterrows():
        print(f"  {x['pn']}|{x['description'][:40]}|{x['billed_eur']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
