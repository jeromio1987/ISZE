#!/usr/bin/env python3
"""Proposal only: billed parts whose AIM label does not fit their description.

Brief R2 (2026-10-15). Does NOT cut a release, does not touch release / master /
overlay / RELEASES.json. Pad kits stay in the R1 proposal; this file excludes them.

    python 01_data/91_build/build_next_release_proposal_wrong_labels_20261015.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
BASE_ID = "2026-10-11"
BASE = REL / f"aim_pn_classification_release_{BASE_ID}.csv"
SALES = DER / "sales_fact.parquet"
PAD = REL / "next_release_proposal_pad_kits_2026-10-15.csv"
OUT_ID = "2026-10-15"
OUT = REL / f"next_release_proposal_wrong_labels_{OUT_ID}.csv"
OUT_PAIRS = REL / f"next_release_proposal_wrong_labels_{OUT_ID}.pairs.csv"
OUT_SUM = OUT.with_suffix(".summary.json")
OUT_NOTE = OUT.with_suffix(".note.md")

sys.path.insert(0, str(ISZE / "02_dashboards" / "pricing" / "_build" / "price_5pct_proposal_2026-09-29"))
from evidence_lib import load_base  # noqa: E402

AIM = ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]
FY26 = ("2025-04-01", "2026-03-31")
DROP_KEYS = {"0000REBATE", "000SERVICE"}
STATUS = "PROPOSED"
EUR_REVIEW = 1000.0

# Existing leaves used as move targets (must exist in the release).
LEAF_OIL_PUMP = ("Lubrication", "Oil Pump", "Oil Pump")
LEAF_WATER_PUMP = ("Cooling", "Water Pump", "Water Pump")
LEAF_BRAKE_SHOE = ("Brakes", "Pads & Shoes", "Brake Shoe")
LEAF_SPEED_SENSOR = ("Electrical", "Sensors", "Speed Sensor")
LEAF_SPEED_SENSOR_ALT = ("Electrical", "Sensors & Switches", "Speed Sensor")
LEAF_FUEL_FILTER = ("Maintenance Service", "Filters (unspecified)", "Fuel Filter")
LEAF_FUEL_FILTER_EL = ("Maintenance Service", "Fuel Filter", "Fuel Filter Element")
LEAF_FLYWHEEL = ("Engine", "Internal Rotating", "Engine Internal")
LEAF_ABS_SENSOR = ("Brakes", "ABS Control", "ABS Sensor")
LEAF_CHARGE_AIR = ("Cooling", "Radiator", "Radiator Assembly")  # no intercooler leaf; decide instead
LEAF_WINDOW_REG = ("Accident & Body", "Panels", "Door")  # no regulator leaf → decide
LEAF_STARTER = ("Electrical", "Motors & Actuators", "Motor")  # no starter leaf → decide
LEAF_CLUTCH_MASTER = ("Clutch", "Release System", "Slave Cylinder")  # nearest existing; decide if weak
LEAF_BRK_MASTER = ("Brakes", "Hydraulic", "Brake Pipe")  # no master cylinder leaf → decide

STOP = {
    "ASM", "ASSY", "KIT", "RR", "FRT", "FR", "LH", "RH", "NO", "WITH", "AND", "FOR",
    "THE", "A", "OF", "IN", "TO", "UP", "DN", "UPR", "LWR", "CTR", "SIDE", "W", "SET",
    "TYPE", "COMPL", "COMP", "UNIT", "PART", "NEW", "OLD",
}

# Synonyms: description token -> label tokens that count as a match.
SYN = {
    "HEAD": {"HEADLAMP", "HEADLIGHT", "LAMP"},
    "HEADLAMP": {"HEAD", "LAMP", "LIGHTING"},
    "LAMP": {"LIGHTING", "HEADLAMP", "LIGHT"},
    "SPD": {"SPEED"},
    "SPEED": {"SPD"},
    "BRK": {"BRAKE", "BRAKES"},
    "BRAKE": {"BRK", "BRAKES"},
    "BRAKES": {"BRAKE", "BRK"},
    "HTR": {"HEATER", "HVAC"},
    "HEATER": {"HTR", "HVAC"},
    "A/C": {"HVAC", "COOLING", "AIR"},
    "AC": {"HVAC", "COOLING"},
    "CLU": {"CLUTCH"},
    "CLUTCH": {"CLU"},
    "TRANS": {"TRANSMISSION"},
    "TRANSMISSION": {"TRANS"},
    "ENG": {"ENGINE"},
    "ENGINE": {"ENG"},
    "MTG": {"MOUNT", "MOUNTING"},
    "MOUNT": {"MTG", "MOUNTING"},
    "FILTER": {"FILTRATION", "ELEMENT", "CARTRIDGE"},
    "CARTRIDGE": {"FILTER", "ELEMENT"},
    "ELEMENT": {"FILTER", "CARTRIDGE"},
    "SHOE": {"SHOES", "BRAKE"},
    "PAD": {"PADS", "BRAKE"},
    "DISC": {"ROTOR", "BRAKE"},
    "ROTOR": {"DISC", "BRAKE"},
    "ALT": {"ALTERNATOR", "GENERATOR"},
    "ALTERNATOR": {"GENERATOR", "CHARGING"},
    "GENERATOR": {"ALTERNATOR", "CHARGING"},
    "INJ": {"INJECTOR", "INJECTION"},
    "INJECTOR": {"INJ", "INJECTION"},
    "PUMP": {"PUMP"},
    "OIL": {"LUBRICATION", "LUBRICANT"},
    "WATER": {"COOLING"},
    "FUEL": {"FUEL"},
    "SENSOR": {"SENSORS"},
    "SENSORS": {"SENSOR"},
    "WHEEL": {"WHEELS", "HUB"},
    "FLYWHEEL": {"ENGINE", "INTERNAL", "ROTATING"},
    "STARTER": {"STARTING", "MOTOR"},
    "BATTERY": {"CHARGING", "BATTERY"},
    "WINDOW": {"DOOR", "BODY"},
    "REGULATOR": {"DOOR", "WINDOW"},
    "COMPRESSOR": {"HVAC", "COOLING"},
    "CONDENSER": {"HVAC", "COOLING"},
    "EVAPORATOR": {"HVAC", "HEATER"},
    "RADIO": {"AUDIO"},
    "STEREO": {"AUDIO", "RADIO"},
    "CAMERA": {"INSTRUMENTS", "ELECTRICAL"},
    "DISPLAY": {"INSTRUMENTS"},
    "ANTENNA": {"AUDIO", "RADIO"},
    "THROTTLE": {"INTAKE", "AIR"},
    "TRANSFER": {"DRIVELINE", "AXLE"},
    "HYDRAULIC": {"BRAKE", "ABS"},
    "ANTI": {"ABS", "BRAKE"},
    "LOCK": {"ABS", "BRAKE"},
    "MASTER": {"HYDRAULIC", "BRAKE", "CLUTCH"},
    "CYLINDER": {"HYDRAULIC", "BRAKE", "CLUTCH"},
    "AIRBAG": {"SEAT", "BELT", "CABIN"},
    "BAG": {"SEAT", "BELT"},
    "HOSE": {"HYDRAULIC", "PIPE", "FUEL", "COOLING"},
    "PIPE": {"HOSE", "LINE"},
    "GASKET": {"SEALING", "SEAL"},
    "SEAL": {"GASKET", "SEALING"},
    "BEARING": {"HUB", "AXLE", "PROP"},
    "JOINT": {"AXLE", "DRIVE", "SHAFT"},
    "SHAFT": {"AXLE", "DRIVE", "PROP"},
    "GEAR": {"TRANSMISSION", "STEERING"},
    "SPRING": {"SUSPENSION"},
    "BUSH": {"SUSPENSION", "BUSHING"},
    "BUSHING": {"SUSPENSION", "BUSH"},
    "FILTER": {"MAINTENANCE", "SERVICE"},
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def desc_key(d: str) -> str:
    d = re.sub(r"\s+", " ", (d or "").upper().strip())
    if ";" in d:
        head, rest = d.split(";", 1)
        qual = rest.split(",", 1)[0].strip()
        return f"{head.strip()};{qual}"
    return d.split(",", 1)[0].strip()


def tokens(s: str) -> set[str]:
    return {t for t in re.split(r"[^A-Z0-9/]+", (s or "").upper()) if t and t not in STOP and len(t) > 1}


def expand(toks: set[str]) -> set[str]:
    out = set(toks)
    for t in list(toks):
        out |= SYN.get(t, set())
    return out


def not_real_label(l1: str, l3: str) -> bool:
    if l1 == "" or l1 in ("Unknown", "Unknown Review"):
        return True
    if "Review" in (l3 or ""):
        return True
    return False


def fit_score(dkey: str, leaf: tuple[str, str, str]) -> float:
    """How well description words fit an AIM leaf. Higher = better."""
    dt = expand(tokens(dkey.replace(";", " ")))
    lt = expand(tokens(" ".join(leaf)))
    if not dt:
        return 0.0
    inter = dt & lt
    # weight L3 hits higher
    l3t = expand(tokens(leaf[2]))
    l3_hit = len(dt & l3t)
    return len(inter) + 1.5 * l3_hit


def best_leaf(dkey: str, leaves: set[tuple[str, str, str]], exclude: set[tuple[str, str, str]] | None = None) -> tuple[tuple[str, str, str] | None, float]:
    exclude = exclude or set()
    best = None
    best_s = 0.0
    for leaf in leaves:
        if leaf in exclude:
            continue
        if not_real_label(leaf[0], leaf[2]):
            continue
        if leaf[0] in ("", "Unknown", "Unknown Review"):
            continue
        s = fit_score(dkey, leaf)
        if s > best_s:
            best_s = s
            best = leaf
    return best, best_s


# Explicit description-driven moves / decides. Checked before the scorer.
# Each rule: (dkey_regex or exact dkey, current filter, verdict, target or None, reason)
def explicit_verdict(dkey: str, cur: tuple[str, str, str], leaves: set[tuple[str, str, str]]) -> tuple[str, tuple[str, str, str] | None, str] | None:
    dk = dkey
    head = dk.split(";", 1)[0]
    qual = dk.split(";", 1)[1] if ";" in dk else ""

    # --- known brief cases ---
    if dk == "SHOE KIT;BRAKE":
        if cur[2] == "Caliper Repair Kit":
            assert LEAF_BRAKE_SHOE in leaves
            return "move", LEAF_BRAKE_SHOE, "description says SHOE / BRAKE, not a caliper repair kit"
        if cur == LEAF_BRAKE_SHOE:
            return "keep", None, "label already Brake Shoe"
    if dk.startswith("CARTRIDGE;FUEL FILTER") or (head == "CARTRIDGE" and "FUEL FILTER" in qual):
        if "Fuel Filter" in cur[2]:
            return "keep", None, "L3 already names Fuel Filter; description is a fuel filter cartridge"
    if dk == "BATTERY ASM;HIGH VOLTAGE":
        if cur[2] == "Alternator/Generator":
            return "decide", None, "high-voltage battery, not an alternator; no HV battery leaf exists"
    if dk == "SENSOR;MAP":
        # never move to Speed Sensor (false pointer from the common label)
        if cur in (LEAF_SPEED_SENSOR, LEAF_SPEED_SENSOR_ALT):
            return "decide", None, "MAP sensor is not a speed sensor; no MAP sensor leaf exists"
        if cur[2] == "DPD Pressure Sensor":
            return "decide", None, "MAP sensor is not a DPD pressure sensor; no MAP sensor leaf exists"

    # --- clear family moves (description word decides) ---
    if head == "FLYWHEEL" and cur[2] == "Wheel":
        if LEAF_FLYWHEEL in leaves:
            return "move", LEAF_FLYWHEEL, "description says FLYWHEEL, not a road wheel"
        return "decide", None, "flywheel, not a road wheel; no dedicated flywheel leaf"
    if head == "SENSOR" and qual.startswith("SPD") and cur[2] == "Wheel":
        tgt = LEAF_SPEED_SENSOR if LEAF_SPEED_SENSOR in leaves else LEAF_SPEED_SENSOR_ALT
        if tgt in leaves:
            return "move", tgt, "description says SENSOR SPD (speed), not a wheel"
    if head == "HYDRAULIC UNIT" and "ANTI LOCK" in qual:
        # ABS hydraulic unit — no dedicated leaf; ABS Sensor is wrong
        return "decide", None, "ABS hydraulic unit; no ABS modulator / hydraulic unit leaf exists"
    if head == "COOLER" and "CHARGE AIR" in qual:
        return "decide", None, "charge-air cooler (intercooler); no intercooler leaf (radiator is the nearest wrong home)"
    if head == "REGULATOR" and "WINDOW" in qual:
        return "decide", None, "window regulator; no window-regulator leaf (door panel is the nearest wrong home)"
    if head == "COMPRESSOR ASM" and "A/C" in qual:
        return "decide", None, "A/C compressor; no compressor leaf"
    if head == "CONDENSER ASM" and "A/C" in qual:
        return "decide", None, "A/C condenser; no condenser leaf"
    if head == "STARTER ASM":
        return "decide", None, "starter motor; no starter leaf (Motor is the nearest wrong home)"
    if head == "CAMERA ASM" or head == "CAMERA":
        return "decide", None, "camera; no camera leaf"
    if head == "AIR BAG UNIT" or head.startswith("AIR BAG"):
        return "decide", None, "airbag; no airbag leaf"
    if head == "CYLINDER ASM" and "CLUTCH MASTER" in qual:
        return "decide", None, "clutch master cylinder; no clutch master leaf (slave cylinder is not the same)"
    if head == "CYLINDER ASM" and "BRK MASTER" in qual:
        return "decide", None, "brake master cylinder; no master-cylinder leaf"
    if head == "TRANSFER ASM":
        return "decide", None, "transfer case; no transfer-case leaf"
    if head == "THROTTLE ASM":
        return "decide", None, "throttle body; no throttle leaf"
    if head == "DISPLAY" or head.startswith("DISPLAY;"):
        return "decide", None, "multi display; no display leaf"
    if head == "RADIO CONTROL ASM" or (head == "RADIO" and "CONTROL" in qual):
        if cur[0] == "Electrical" and cur[1] == "Audio":
            return "keep", None, "radio control sits under Audio"
        tgt = ("Electrical", "Audio", "Radio")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says RADIO CONTROL; Audio > Radio is the existing leaf"
    if head == "HEATER UNIT":
        return "decide", None, "heater unit; HVAC blower-filter leaf is not the heater"
    if head == "CORE" and "HTR" in qual:
        tgt = ("Cabin Interior", "HVAC Filters", "Heater Core")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says HTR UNIT core; leaf is Heater Core"
    if head == "EVAPORATOR ASM":
        return "decide", None, "A/C evaporator; no evaporator leaf"
    if head == "ANTENNA":
        tgt = ("Electrical", "Audio", "Radio")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "antenna belongs with Audio > Radio (nearest existing leaf)"
    if head == "MOTOR" and "POWER WINDOW" in qual:
        tgt = ("Electrical", "Motors & Actuators", "Window Motor")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says POWER WINDOW REG motor; leaf is Window Motor"
    if head == "EXPANDER" and cur[0] == "Brakes":
        return "decide", None, "brake expander; no expander leaf"
    if head == "BLOCK" and "SHIFT" in qual and "CLU" in (qual + dk):
        return "decide", None, "clutch shift block; Pivot is not a fit and no shift-block leaf exists"
    if head == "DECAL":
        tgt = ("Accident & Body", "Trim", "Emblem")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says DECAL; Emblem is the existing trim leaf"
    if head == "BARREL ASM" and "KEY" in qual:
        return "decide", None, "lock barrel / steering lock; no lock-barrel leaf"
    if head == "GUSSET":
        tgt = ("Chassis Frame", "Crossmember & Brackets", "Reinforcement")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says GUSSET on crossmember; Reinforcement is the chassis leaf"
    if head == "COVER" and "TRIM" in qual and "SEAT" in dk:
        tgt = ("Cabin Interior", "Trim", "Trim")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "seat trim cover, not a wheel rim"
    if head == "COVER" and "SEAL" in qual and "NOZZLE" in dk:
        return "decide", None, "nozzle seal cover; Injector Nozzle is not a cover leaf"
    if head == "JOINT ASM" and "DRIVE SHAFT" in dk:
        tgt = ("Driveline Axle", "Axle Shaft", "Drive Shaft")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description names drive shaft joint"
    if head == "BEARING ASM" and "PROP SHAFT" in dk:
        return "decide", None, "prop-shaft centre bearing; Prop Shaft leaf is the shaft, not the bearing"
    if head == "RUBBER" and "CUSHION" in qual and "ENG MTG" in dk:
        tgt = ("Engine", "Mounting", "Engine Mount")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says ENG MTG cushion; Engine Mount is the leaf"
    if head == "RING" and "BLOCK" in qual:
        return "keep", None, "syncro / gear ring on transmission; Synchronizer fits the family"
    if head in ("T/AXLEOIL", "AXLEOIL") or "AXLEOIL" in head:
        # lubricant track excluded — but if already on Lubricant, keep; else keep on Fluids
        if cur[0] == "Fluids Chemicals":
            return "keep", None, "axle oil is a fluid; lubricants stay on the fluids track"
        return "keep", None, "axle oil already treated as lubricant/fluid; lubricants are out of this brief's move set"
    if head == "BESCO CLEAN SUPER (200L)" or head.startswith("BESCO CLEAN"):
        if cur[2] == "Cleaner":
            return "keep", None, "cleaner chemical already on Cleaner"
    if head == "LAMP ASM" and qual.startswith("HEAD"):
        tgt = ("Lighting", "Lamps", "Headlamp Assembly")
        if cur == tgt or cur[2] in ("Headlamp Assembly", "Front Lamp Asm"):
            return "keep", None, "head lamp assembly already on a headlamp leaf"
    if head == "HEADLAMP UNIT":
        tgt = ("Lighting", "Lamps", "Headlamp Assembly")
        if tgt in leaves and cur != tgt and "Headlamp" not in cur[2]:
            return "move", tgt, "description says HEADLAMP UNIT"
        if "Headlamp" in cur[2] or cur[2] == "Lamp":
            return "keep", None, "already under lighting / headlamp"

    # --- hard keeps / decides that the scorer gets wrong ---
    if head == "CYLINDER" and "WHEEL" in qual:
        # wheel brake cylinder — no leaf; never Slave Cylinder
        if cur[2] == "Wheel":
            return "decide", None, "wheel brake cylinder, not a road wheel; no wheel-cylinder leaf"
        return "decide", None, "wheel brake cylinder; no wheel-cylinder leaf"
    if head == "BRACKET":
        if "Bracket" in cur[2] or cur[2] in ("Support", "Stay", "Reinforcement"):
            return "keep", None, "description is a bracket; current chassis/bracket leaf fits"
        return "decide", None, "description is a bracket; sensor/other leaves are not brackets"
    if head == "PANEL" and "WHEEL HOUSE" in qual:
        if cur[2] == "Panel":
            return "keep", None, "wheel-house panel is a body panel"
        tgt = ("Accident & Body", "Panels", "Panel")
        if tgt in leaves:
            return "move", tgt, "wheel-house panel is a body panel, not a wheel"
    if head == "PAD" and "STEP" in qual:
        if cur[2] == "Step":
            return "keep", None, "step pad is a body step, not a brake pad"
        return "decide", None, "step pad; Step leaf fits better than Brake Pad but needs a human call if current differs"
    if head == "BEARING" and "HUB" in qual:
        if cur[2] in ("Hub", "Hub Seal") or "Hub" in cur[1]:
            return "keep", None, "hub bearing sits with the hub family"
        return "decide", None, "hub bearing; Release Bearing (clutch) is the wrong home and no hub-bearing leaf exists"
    if head == "SWITCH":
        if cur[2] == "Switch":
            return "keep", None, "description is a switch; Switch leaf fits"
        tgt = ("Electrical", "Switch Relay Fuse", "Switch")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says SWITCH; Switch is the existing leaf"
    if head == "SEAL" and "OIL" in qual and ("HUB" in dk or cur[2] == "Hub Seal"):
        if cur[2] == "Hub Seal":
            return "keep", None, "hub oil seal already on Hub Seal"
    if head == "GASKET" and "OIL FILLER" in qual:
        if cur[2] == "Gasket":
            return "keep", None, "oil-filler gasket is a gasket, not an oil seal"
    if head == "PUMP" and "WATER" in qual and cur[2] in ("Fuel Pump", "Gasket"):
        if LEAF_WATER_PUMP in leaves:
            return "move", LEAF_WATER_PUMP, "description says WATER pump, not a fuel pump or gasket"
    if head == "PUMP" and "OIL" in qual and cur[2] in ("Fuel Pump", "Gasket"):
        if LEAF_OIL_PUMP in leaves:
            return "move", LEAF_OIL_PUMP, "description says OIL pump, not a fuel pump or gasket"
    if head == "BELT" and "SEAT" in qual:
        tgt = ("Cabin Interior", "Seat", "Seat Belt")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says SEAT BELT, not a drive belt"
    if head == "METER COMPL" and "CLUSTER" in qual:
        tgt = ("Cabin Interior", "Dashboard & Controls", "Meter Cluster")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says METER CLUSTER; Meter Cluster is the existing leaf"
        if cur[2] in ("Meter Cluster", "Instrument Cluster"):
            return "keep", None, "already on a meter/instrument cluster leaf"
    if head in ("ELEMENT", "ELEMENT KIT", "CARTRIDGE KIT") and "FUEL FILTER" in qual:
        # prefer Fuel Filter Element when current is the coarse Fuel Filter leaf
        tgt = LEAF_FUEL_FILTER_EL
        if cur[2] == "Fuel Filter" and tgt in leaves:
            return "move", tgt, "description is a fuel-filter element; Fuel Filter Element is the finer existing leaf"
        if "Fuel Filter" in cur[2]:
            return "keep", None, "already on a fuel-filter leaf"
    if head == "FILTER ASM" and "FUEL" in qual:
        if "Fuel Filter" in cur[2]:
            return "keep", None, "fuel filter assembly already on a fuel-filter leaf"
        tgt = LEAF_FUEL_FILTER
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says FUEL filter assembly"
    if head == "ROD END" and "TIE ROD" in qual:
        tgt = ("Steering", "Linkage", "Tie Rod End")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says TIE ROD END"
    if head == "SENSOR" and "TEMPERATURE" in qual:
        tgt = ("Electrical", "Sensors", "Temperature Sensor")
        if tgt in leaves and cur != tgt and cur[2] == "Sensor":
            return "move", tgt, "description says TEMPERATURE sensor"
    if head == "GEAR" and "PINION" in qual:
        if cur[2] == "Pinion":
            return "keep", None, "pinion gear already on Pinion"
        return "decide", None, "pinion gear; Side Gear is the wrong differential leaf"
    if head == "SUPPORT" and "BRK" in qual:
        if cur[2] in ("Support", "Bracket", "Stay"):
            return "keep", None, "brake disc support is a bracket/support, not the disc itself"
        return "decide", None, "brake support/bracket; Brake Disc leaf is the disc, not the support"
    if head == "STRAINER ASM" or head == "STRAINER":
        if "Strainer" in cur[2] or cur[2] == "Filter":
            return "keep", None, "strainer already on a strainer/filter leaf"
        return "decide", None, "oil strainer; Oil Jet is not a strainer"
    if head == "CLUTCH" and "COOLING FAN" in qual:
        return "decide", None, "cooling-fan clutch; Clutch Disc (driveline) is the wrong home and no fan-clutch leaf exists"
    if head == "CABLE" and "BATTERY" in qual:
        tgt = ("Electrical", "Charging", "Battery Cable")
        alt = ("Electrical", "Starting & Charging", "Battery Cable")
        if cur[2] == "Battery Cable":
            return "keep", None, "already on Battery Cable"
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says BATTERY cable"
        if alt in leaves and cur != alt:
            return "move", alt, "description says BATTERY cable"
    if head == "BEARING ASM" and "CTR" in qual:
        return "decide", None, "prop-shaft centre bearing; Release Bearing is clutch and Prop Shaft is the shaft"
    if head == "BEARING" and ("AXLE" in qual or "DIFF" in qual):
        return "decide", None, "axle/diff bearing; Release Bearing (clutch) is the wrong home"
    if (
        head.startswith("BESCO")
        or "ATF" in head
        or "AXLE OIL" in head
        or "AXLEOIL" in head
        or cur[2] == "Lubricant"
        or (cur[0] == "Fluids Chemicals" and any(x in head for x in ("OIL", "ATF", "GREASE")))
    ):
        if cur[0] == "Fluids Chemicals" or cur[2] == "Lubricant":
            return "keep", None, "fluid/lubricant already on Fluids Chemicals; lubricants are out of this move set"
        return "keep", None, "looks like a fluid/lubricant line; lubricants are out of this brief's move set"
        return "keep", None, "looks like a fluid/lubricant line; lubricants are out of this brief's move set"
    if head == "GASKET" and "OIL PAN" in qual:
        tgt = ("Engine", "Gasket & Sealing", "Gasket")
        if cur[2] == "Gasket":
            return "keep", None, "oil-pan gasket already on Gasket"
        if cur[2] == "Oil Pan" and tgt in leaves:
            return "move", tgt, "description says GASKET for the oil pan, not the pan itself"
        return "keep", None, "oil-pan gasket; Oil Seal is the wrong sealing leaf"
    if head == "REGULATOR ASM" and "DOOR" in qual:
        return "decide", None, "door window regulator; Electrical Regulator is a voltage regulator"
    if head == "ELEMENT KIT" and "OIL FILTER" in qual:
        tgt = ("Maintenance Service", "Oil Filter", "Oil Filter Element")
        if cur[2] in ("Oil Filter", "Oil Filter Element"):
            if cur[2] == "Oil Filter" and tgt in leaves:
                return "move", tgt, "oil-filter element kit; Oil Filter Element is the finer leaf"
            return "keep", None, "already on an oil-filter leaf"
    if head == "CARTRIDGE" and "OIL FILTER" in qual:
        tgt = ("Maintenance Service", "Oil Filter", "Oil Filter Element")
        if cur[2] == "Oil Filter" and tgt in leaves:
            return "move", tgt, "oil-filter cartridge; Oil Filter Element is the finer leaf"
        if "Oil Filter" in cur[2]:
            return "keep", None, "already on an oil-filter leaf"
    if head == "SENSOR" and qual.startswith("SPEED"):
        tgt = LEAF_SPEED_SENSOR if LEAF_SPEED_SENSOR in leaves else LEAF_SPEED_SENSOR_ALT
        if cur[2] == "Speed Sensor":
            return "keep", None, "already Speed Sensor"
        if cur[2] == "ABS Sensor" and tgt in leaves:
            return "move", tgt, "description says SPEED sensor, not ABS"
    if head == "COOLER ASM" and "OIL" in qual:
        tgt = ("Lubrication", "Oil Filter System", "Oil Cooler")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says OIL cooler"
    if head == "SENSOR" and "NOX" in qual:
        tgt = ("Intake Exhaust Emission", "Sensors", "NOx Sensor")
        if tgt in leaves and cur != tgt and cur[2] != "NOx Sensor":
            return "move", tgt, "description says NOX sensor"
    if head == "BEARING" and ("PINION" in qual or "FINAL" in qual):
        if cur[2] == "Pinion":
            return "keep", None, "final-pinion bearing sits with the pinion family"
        return "decide", None, "final-pinion bearing; Release Bearing is clutch"
    if head == "BEARING" and "KNUCKLE" in qual:
        return "decide", None, "knuckle bearing; Release Bearing is clutch"
    if head == "HOSE":
        # generic hose — do not send to Brake Hose without BRK in the text
        if "BRK" in dk or "BRAKE" in dk:
            tgt = ("Brakes", "Hydraulic", "Brake Hose")
            if tgt in leaves and cur != tgt:
                return "move", tgt, "description names a brake hose"
        if cur[2] in ("Brake Hose", "Fuel Hose", "Bypass Hose", "Air Duct"):
            return "keep", None, "hose already on a hose/duct leaf; description too thin to force a move"
        return "decide", None, "hose; description too thin to pick Brake/Fuel/Bypass hose safely"
    if head == "VALVE" and "EXH BRAKE" in qual:
        tgt = ("Brakes", "Booster & Control", "Brake Valve")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says EXH BRAKE valve"
    if head == "HEAD ASM" and "CYL" in qual:
        return "decide", None, "cylinder head assembly; Head Cover is the cover, not the head"
    if head == "PIPE" and "CLU" in qual:
        return "decide", None, "clutch pipe; Brake Pipe is the wrong hydraulic leaf"
    if head == "TANK ASM" and "OIL" in qual:
        return "decide", None, "oil tank; Oil Pan is the engine sump, not this tank"
    if head == "SHAFT ASM" and "PROP" in qual:
        tgt = ("Driveline Axle", "Axle Shaft", "Prop Shaft")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says PROP shaft"
    if head == "PIPE" and "OIL" in qual:
        tgt = ("Lubrication", "Lubrication Lines", "Oil Pipe")
        if tgt in leaves and cur != tgt:
            return "move", tgt, "description says OIL pipe"

    # blank description keys are not reviewable by words
    if dk == "":
        return "keep", None, "no description words to judge the label against"

    return None


def score_verdict(
    dkey: str,
    cur: tuple[str, str, str],
    leaves: set[tuple[str, str, str]],
    mode: str,
) -> tuple[str, tuple[str, str, str] | None, str]:
    """mode = 'real' (group B) or 'not_real' (group C)."""
    ex = explicit_verdict(dkey, cur, leaves)
    if ex is not None:
        return ex

    cur_s = fit_score(dkey, cur)
    exclude: set[tuple[str, str, str]] = set()
    if dkey == "SENSOR;MAP":
        exclude |= {LEAF_SPEED_SENSOR, LEAF_SPEED_SENSOR_ALT}

    best, best_s = best_leaf(dkey, leaves, exclude=exclude)
    raw = tokens(dkey.replace(";", " "))
    head_toks = tokens(dkey.split(";", 1)[0]) - {"ASM", "COMPL", "KIT", "UNIT"}
    conflict_heads = {
        "BRACKET", "PANEL", "SWITCH", "COVER", "BOLT", "NUT", "SCREW", "CLIP",
        "PAD", "STEP", "PLATE", "PIPE", "HOSE", "WIRE", "HARNESS", "SUPPORT",
        "STRAINER", "GASKET", "SEAL", "GEAR", "BEARING", "HOUSING", "COIL",
        "STEM", "HEAD", "TRANSMISSION", "MASTER", "CLUTCH", "CABLE",
    }

    def head_contradicts(leaf: tuple[str, str, str]) -> bool:
        if not head_toks:
            return False
        leaf_toks = tokens(leaf[1] + " " + leaf[2])
        if head_toks & leaf_toks:
            return False
        return bool(head_toks & conflict_heads)

    def safe_move(leaf: tuple[str, str, str]) -> bool:
        l3_raw = tokens(leaf[2])
        return bool(raw & l3_raw) and not head_contradicts(leaf)

    # Group C: no scorer moves — only explicit_verdict above may move.
    # Blank/Unknown/Review rows are too thin for automatic leaf picking.
    if mode == "not_real":
        return "keep", None, "no existing leaf fits the description closely enough (or description too thin)"

    # Group B
    if best is not None and best != cur and best_s >= 5.5 and best_s >= cur_s + 3.5:
        if safe_move(best):
            return "move", best, f"description words fit {' > '.join(best)} better than {' > '.join(cur)}"
        if cur_s <= 1.0:
            return "decide", None, (
                f"current label {' > '.join(cur)} does not fit; "
                f"nearest leaf {' > '.join(best)} is not a safe match — needs a human call"
            )
        return "keep", None, "current label shares enough meaning with the description"

    if cur_s >= 2.0:
        return "keep", None, "description words fit the current label"
    if cur_s <= 0.5 and (best is None or best_s < 4.0):
        return "decide", None, (
            f"current label {' > '.join(cur)} does not fit the description; "
            "no existing leaf fits closely enough"
        )
    return "keep", None, "description is compatible with the current label (no clearer existing leaf)"


def main() -> None:
    # ---- start hashes ----
    expect = {
        BASE: "d9b26b0124bacadcece437f665fc673e32b70d2087d78aa0884ea6615369f605",
        SALES: "66db408990e20396dedc2ce9ce840b43d7c3dbb8c0263bff94ea8db77f0aedd2",
        PAD: "41402fb51101b0881e28826ed0d86771ad45e1dc46de035431ef9fc1dffbd677",
    }
    for p, exp in expect.items():
        got = sha256(p)
        if got != exp:
            raise SystemExit(f"START HASH MISMATCH {p}: got {got}")

    reg = json.loads((REL / "RELEASES.json").read_text(encoding="utf-8"))
    base_entry = next(c for c in reg["candidates"] if c["release_id"] == BASE_ID)
    assert base_entry["status"] == "APPROVED", base_entry["status"]
    base_sha = sha256(BASE)
    assert base_sha == base_entry["sha256"]

    rel = pd.read_csv(BASE, dtype=str, keep_default_na=False)
    for c in rel.columns:
        rel[c] = rel[c].str.strip()
    rel["pn"] = rel.part_number.str.zfill(10)
    # report-only: rebate/service duplicate keys
    rebate_note = {
        "keys": sorted(DROP_KEYS),
        "rows_in_release": int(rel.pn.isin(DROP_KEYS).sum()),
        "line_kinds": (
            rel[rel.pn.isin(DROP_KEYS)]
            .groupby(["pn", "line_kind"])
            .size()
            .reset_index(name="n")
            .to_dict("records")
        ),
    }
    rel = rel.drop_duplicates("pn", keep="first")
    rel = rel[~rel.pn.isin(DROP_KEYS)].copy()

    leaves = set(zip(*(rel[c] for c in AIM)))
    assert LEAF_OIL_PUMP in leaves and LEAF_WATER_PUMP in leaves and LEAF_BRAKE_SHOE in leaves

    sf = pd.read_parquet(SALES, columns=["billing_date", "part_number", "net_sales_value"])
    sf["pn"] = sf.part_number.astype(str).str.strip().str.zfill(10)
    sf["billing_date"] = pd.to_datetime(sf.billing_date)
    fy = (
        sf[(sf.billing_date >= FY26[0]) & (sf.billing_date <= FY26[1])]
        .groupby("pn")
        .net_sales_value.sum()
    )
    fy = fy[fy != 0]

    parts = rel[rel.line_kind.eq("part")].copy()
    u = parts[parts.pn.isin(fy.index)].copy()
    u["eur_fy2026"] = u.pn.map(fy)
    u_n, u_eur = int(len(u)), round(float(u.eur_fy2026.sum()), 2)
    assert u_n == 16705 and abs(u_eur - 33468155.07) < 1.0, (u_n, u_eur)

    u["not_real"] = [
        not_real_label(a, b) for a, b in zip(u.aim_l1_fixed, u.aim_l3_fixed)
    ]
    nr = u[u.not_real]
    blank = u[u.aim_l1_fixed.eq("")]
    assert len(nr) == 1951 and abs(round(float(nr.eur_fy2026.sum()), 2) - 427322.00) < 1.0
    assert len(blank) == 91 and abs(round(float(blank.eur_fy2026.sum()), 2) - 4468.84) < 1.0

    pad_pns = set(pd.read_csv(PAD, dtype=str).part_number.str.strip().str.zfill(10))
    u["dkey"] = u.description_norm.map(desc_key)
    u["label"] = list(zip(u.aim_l1_fixed, u.aim_l2_fixed, u.aim_l3_fixed))

    # ---- Group A pumps ----
    desc = u.description_norm.str.upper()
    ga_mask = (
        desc.str.startswith("PUMP ASM")
        & u.aim_l3_fixed.isin(["Fuel Pump", "Gasket"])
        & ~desc.str.contains(r"FUEL|INJ|DEF", regex=True)
    )
    ga = u[ga_mask].copy()
    assert len(ga) == 81 and abs(round(float(ga.eur_fy2026.sum()), 2) - 220342.23) < 1.0

    def pump_kind(d: str) -> str:
        d = d.upper()
        if "VAC" in d:
            return "vacuum"
        if "WATER" in d:
            return "water"
        if "OIL" in d:
            return "oil"
        return "other"

    ga["pump_kind"] = ga.description_norm.map(pump_kind)
    oil = ga[ga.pump_kind.eq("oil")]
    water = ga[ga.pump_kind.eq("water")]
    vac = ga[ga.pump_kind.eq("vacuum")]
    assert len(oil) == 50 and abs(round(float(oil.eur_fy2026.sum()), 2) - 151920.30) < 1.0
    assert len(water) == 25 and abs(round(float(water.eur_fy2026.sum()), 2) - 60725.72) < 1.0
    assert len(vac) == 6 and abs(round(float(vac.eur_fy2026.sum()), 2) - 7696.21) < 1.0

    # price tool euros
    L = load_base()
    tool_all = L[L.movable].groupby("pn").net_sales_value.sum()

    pair_rows: list[dict] = []
    part_rows: list[dict] = []

    def add_pair_and_parts(
        group: str,
        sub: pd.DataFrame,
        verdict: str,
        target: tuple[str, str, str] | None,
        reason: str,
        reviewed: bool,
    ) -> None:
        eur = float(sub.eur_fy2026.sum())
        cur = (
            sub.aim_l1_fixed.iloc[0],
            sub.aim_l2_fixed.iloc[0],
            sub.aim_l3_fixed.iloc[0],
        )
        dkey = sub.dkey.iloc[0]
        v = verdict if reviewed else "not_reviewed"
        rsn = reason if reviewed else "pair below EUR 1,000 FY2026; not reviewed"
        tgt = target if (v == "move" and target) else (None if v != "move" else target)
        pair_rows.append(
            {
                "description_key": dkey,
                "group": group,
                "verdict": v,
                "current_aim_l1": cur[0],
                "current_aim_l2": cur[1],
                "current_aim_l3": cur[2],
                "proposed_aim_l1": "" if tgt is None else tgt[0],
                "proposed_aim_l2": "" if tgt is None else tgt[1],
                "proposed_aim_l3": "" if tgt is None else tgt[2],
                "parts": int(len(sub)),
                "eur_fy2026": round(eur, 2),
                "reason": rsn,
            }
        )
        for r in sub.itertuples():
            tgt_p = tgt
            part_rows.append(
                {
                    "part_number": r.pn,
                    "description": r.description_norm,
                    "fig_key": r.fig_key,
                    "group": group,
                    "verdict": v,
                    "current_aim_l1": r.aim_l1_fixed,
                    "current_aim_l2": r.aim_l2_fixed,
                    "current_aim_l3": r.aim_l3_fixed,
                    "proposed_aim_l1": "" if tgt_p is None else tgt_p[0],
                    "proposed_aim_l2": "" if tgt_p is None else tgt_p[1],
                    "proposed_aim_l3": "" if tgt_p is None else tgt_p[2],
                    "eur_fy2026": round(float(r.eur_fy2026), 2),
                    "eur_price_tool": round(float(tool_all.reindex([r.pn]).fillna(0.0).iloc[0]), 2),
                    "reason": rsn,
                    "status": STATUS,
                }
            )

    # Group A per-part (not pair-aggregated the same way — brief gives pump counts)
    for r in ga.itertuples():
        kind = r.pump_kind
        if kind == "oil":
            v, tgt, reason = "move", LEAF_OIL_PUMP, "description is an oil pump ASM, not a fuel pump or gasket"
        elif kind == "water":
            v, tgt, reason = "move", LEAF_WATER_PUMP, "description is a water pump ASM, not a fuel pump or gasket"
        elif kind == "vacuum":
            v, tgt, reason = "decide", None, "vacuum pump; no vacuum-pump leaf exists in the release"
        else:
            v, tgt, reason = "decide", None, "pump ASM that is not oil/water/fuel; no matching leaf"
        # also emit as pairs by (dkey, label)
        pass

    # Aggregate group A as pairs for the pairs file, and parts for the part file
    for (dkey, l1, l2, l3), sub in ga.groupby(["dkey"] + AIM):
        kinds = sub.pump_kind.value_counts()
        # one kind per pair expected
        kind = kinds.index[0]
        if kind == "oil":
            v, tgt, reason = "move", LEAF_OIL_PUMP, "description is an oil pump ASM, not a fuel pump or gasket"
        elif kind == "water":
            v, tgt, reason = "move", LEAF_WATER_PUMP, "description is a water pump ASM, not a fuel pump or gasket"
        else:
            v, tgt, reason = "decide", None, "vacuum pump; no vacuum-pump leaf exists in the release"
        add_pair_and_parts("A_pumps", sub, v, tgt, reason, reviewed=True)

    # ---- Group B ----
    b = u[~u.pn.isin(pad_pns) & ~u.pn.isin(set(ga.pn)) & ~u.not_real].copy()
    b_pairs = (
        b.groupby(["dkey"] + AIM, dropna=False)
        .agg(eur=("eur_fy2026", "sum"), n=("pn", "size"))
        .reset_index()
    )
    rev_b = b_pairs[b_pairs.eur >= EUR_REVIEW]
    assert len(rev_b) == 1006, len(rev_b)
    assert abs(round(float(rev_b.eur.sum()), 2) - 32170538.93) < 1.0, round(float(rev_b.eur.sum()), 2)

    for r in b_pairs.itertuples():
        sub = b[
            (b.dkey == r.dkey)
            & (b.aim_l1_fixed == r.aim_l1_fixed)
            & (b.aim_l2_fixed == r.aim_l2_fixed)
            & (b.aim_l3_fixed == r.aim_l3_fixed)
        ]
        reviewed = float(r.eur) >= EUR_REVIEW
        cur = (r.aim_l1_fixed, r.aim_l2_fixed, r.aim_l3_fixed)
        if reviewed:
            v, tgt, reason = score_verdict(r.dkey, cur, leaves, mode="real")
            if v == "move":
                assert tgt is not None and tgt in leaves and tgt != cur
                assert reason.strip()
            if v == "decide":
                assert reason.strip()
        else:
            v, tgt, reason = "not_reviewed", None, ""
        add_pair_and_parts("B_real_labels", sub, v, tgt, reason, reviewed=reviewed)

    # known-case checks on emitted pairs
    pb = pd.DataFrame(pair_rows)
    pb_b = pb[pb.group.eq("B_real_labels")]

    shoe = pb_b[pb_b.description_key.eq("SHOE KIT;BRAKE") & pb_b.current_aim_l3.eq("Caliper Repair Kit")]
    assert len(shoe) == 1 and shoe.iloc[0].verdict == "move" and shoe.iloc[0].proposed_aim_l3 == "Brake Shoe"

    cart = pb_b[pb_b.description_key.eq("CARTRIDGE;FUEL FILTER")]
    assert len(cart) >= 1 and all(
        (row.verdict == "keep") or ("Fuel Filter" in row.current_aim_l3)
        for row in cart.itertuples()
    )
    assert all(row.verdict != "move" or "Fuel Filter" in row.proposed_aim_l3 for row in cart.itertuples())

    bat = pb_b[pb_b.description_key.eq("BATTERY ASM;HIGH VOLTAGE")]
    assert len(bat) == 1 and bat.iloc[0].verdict == "decide"

    smap = pb_b[pb_b.description_key.eq("SENSOR;MAP")]
    assert not any(
        (row.verdict == "move") and (row.proposed_aim_l3 == "Speed Sensor")
        for row in smap.itertuples()
    )

    # ---- Group C ----
    c = u[u.not_real].copy()
    c_pairs = (
        c.groupby(["dkey"] + AIM, dropna=False)
        .agg(eur=("eur_fy2026", "sum"), n=("pn", "size"))
        .reset_index()
    )
    rev_c = c_pairs[c_pairs.eur >= EUR_REVIEW]
    assert len(rev_c) == 82, len(rev_c)
    assert abs(round(float(rev_c.eur.sum()), 2) - 333245.10) < 1.0, round(float(rev_c.eur.sum()), 2)

    for r in c_pairs.itertuples():
        sub = c[
            (c.dkey == r.dkey)
            & (c.aim_l1_fixed == r.aim_l1_fixed)
            & (c.aim_l2_fixed == r.aim_l2_fixed)
            & (c.aim_l3_fixed == r.aim_l3_fixed)
        ]
        reviewed = float(r.eur) >= EUR_REVIEW
        cur = (r.aim_l1_fixed, r.aim_l2_fixed, r.aim_l3_fixed)
        if reviewed:
            v, tgt, reason = score_verdict(r.dkey, cur, leaves, mode="not_real")
            if v == "move":
                assert tgt is not None and tgt in leaves
                assert reason.strip()
            else:
                # keep with reason when no leaf fits
                if v != "keep":
                    v = "keep"
                if not reason:
                    reason = "no existing leaf fits the description closely enough (or description too thin)"
        else:
            v, tgt, reason = "not_reviewed", None, ""
        add_pair_and_parts("C_not_real_labels", sub, v, tgt, reason, reviewed=reviewed)

    parts_df = pd.DataFrame(part_rows)
    pairs_df = pd.DataFrame(pair_rows)

    # every move/decide reviewed must have reason
    bad_reason = pairs_df[
        pairs_df.verdict.isin(["move", "decide"]) & (pairs_df.reason.str.strip() == "")
    ]
    assert bad_reason.empty, bad_reason.head()

    # every move target exists and differs
    moves = pairs_df[pairs_df.verdict.eq("move")]
    for row in moves.itertuples():
        tgt = (row.proposed_aim_l1, row.proposed_aim_l2, row.proposed_aim_l3)
        cur = (row.current_aim_l1, row.current_aim_l2, row.current_aim_l3)
        assert tgt in leaves and tgt != cur, (row.description_key, tgt, cur)

    # ---- dry run on a full copy of the release file ----
    full = pd.read_csv(BASE, dtype=str, keep_default_na=False)
    for c in full.columns:
        full[c] = full[c].str.strip()
    assert len(full) == 165055
    dry = full.copy()
    dry["pn"] = dry.part_number.str.zfill(10)
    move_pns = set(parts_df.loc[parts_df.verdict.eq("move"), "part_number"])
    for r in parts_df[parts_df.verdict.eq("move")].itertuples():
        m = dry.pn.eq(r.part_number)
        dry.loc[m, "aim_l1_fixed"] = r.proposed_aim_l1
        dry.loc[m, "aim_l2_fixed"] = r.proposed_aim_l2
        dry.loc[m, "aim_l3_fixed"] = r.proposed_aim_l3
    # only AIM cols may differ, and only on move parts
    for c in dry.columns:
        if c in AIM or c == "pn":
            continue
        if not dry[c].equals(full[c]):
            raise SystemExit(f"dry run changed non-AIM column {c}")
    changed = (dry[AIM] != full[AIM]).any(axis=1)
    assert set(dry.loc[changed, "pn"]) <= move_pns | DROP_KEYS
    assert move_pns <= set(dry.loc[changed, "pn"])
    # no new labels
    new_leaves = set(zip(*(dry[c] for c in AIM))) - set(zip(*(full[c] for c in AIM)))
    assert not new_leaves, new_leaves
    # pad kits unchanged
    pad_before = full[full.part_number.str.zfill(10).isin(pad_pns)][AIM].reset_index(drop=True)
    pad_after = dry[dry.pn.isin(pad_pns)][AIM].reset_index(drop=True)
    assert pad_before.equals(pad_after)

    # ---- write outputs ----
    parts_df = parts_df.sort_values(
        ["group", "verdict", "eur_fy2026", "part_number"],
        ascending=[True, True, False, True],
    )
    pairs_df = pairs_df.sort_values(
        ["group", "verdict", "eur_fy2026", "description_key"],
        ascending=[True, True, False, True],
    )
    parts_df.to_csv(OUT, index=False, encoding="utf-8")
    pairs_df.to_csv(OUT_PAIRS, index=False, encoding="utf-8")

    def bucket(df: pd.DataFrame) -> dict:
        g = df.groupby(["group", "verdict"]).agg(
            parts=("part_number", "size"), eur_fy2026=("eur_fy2026", "sum")
        )
        out = {}
        for (grp, verd), row in g.iterrows():
            out.setdefault(grp, {})[verd] = {
                "parts": int(row.parts),
                "eur_fy2026": round(float(row.eur_fy2026), 2),
            }
        return out

    # Proposals for Claude extras
    alt_never = rel[
        rel.aim_l3_fixed.eq("Alternator/Generator")
        & ~rel.pn.isin(fy.index)
        & ~rel.description_norm.str.upper().str.contains(
            r"ALTERNATOR|GENERATOR|ALT\b", regex=True, na=False
        )
    ]
    alt_by_src = (
        alt_never.aim_source.value_counts().head(20).to_dict()
        if "aim_source" in alt_never.columns
        else {}
    )

    missing_leaf_notes = (
        pairs_df[pairs_df.verdict.eq("decide")]
        .groupby("reason", as_index=False)
        .agg(pairs=("description_key", "size"), parts=("parts", "sum"), eur_fy2026=("eur_fy2026", "sum"))
        .sort_values("eur_fy2026", ascending=False)
    )

    summary = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "built_by": "01_data/91_build/build_next_release_proposal_wrong_labels_20261015.py",
        "status": STATUS,
        "base_release": BASE_ID,
        "base_sha256": base_sha,
        "rule": (
            "Universe U = line_kind part with FY2026 billed != 0. "
            "Group A = PUMP ASM on Fuel Pump/Gasket without FUEL/INJ/DEF. "
            "Group B = real labels, review pairs >= EUR 1,000. "
            "Group C = not-real labels, review pairs >= EUR 1,000. "
            "Description words decide; move only to an existing leaf."
        ),
        "universe": {
            "parts": u_n,
            "eur_fy2026": u_eur,
            "not_real_parts": int(len(nr)),
            "not_real_eur_fy2026": round(float(nr.eur_fy2026.sum()), 2),
            "blank_parts": int(len(blank)),
            "blank_eur_fy2026": round(float(blank.eur_fy2026.sum()), 2),
        },
        "by_group_verdict": bucket(parts_df),
        "pair_counts": {
            "B_reviewed": 1006,
            "B_reviewed_eur_fy2026": 32170538.93,
            "C_reviewed": 82,
            "C_reviewed_eur_fy2026": 333245.10,
            "A_parts": 81,
            "A_eur_fy2026": 220342.23,
        },
        "dry_run": {
            "move_parts": int(len(move_pns)),
            "new_labels": 0,
            "release_rows": 165055,
            "pad_kits_unchanged": 30,
            "non_aim_cells_changed": 0,
        },
        "rebate_service_duplicate_keys": rebate_note,
        "alternator_never_billed_no_alt_word": {
            "parts": int(len(alt_never)),
            "by_aim_source_top": {str(k): int(v) for k, v in alt_by_src.items()},
        },
        "decide_reasons": missing_leaf_notes.to_dict("records"),
        "not_touched": [
            "release files",
            "aim_master_v2.csv",
            "aim_pn_classification_20260920.csv",
            "RELEASES.json",
            "pad kit proposal parts",
        ],
    }
    OUT_SUM.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # ---- note for Jerome ----
    moves_parts = parts_df[parts_df.verdict.eq("move")].copy()
    top10 = moves_parts.nlargest(10, "eur_fy2026")
    decide_parts = parts_df[parts_df.verdict.eq("decide")].copy()
    decide_by_reason = (
        decide_parts.groupby("reason", as_index=False)
        .agg(parts=("part_number", "size"), eur_fy2026=("eur_fy2026", "sum"))
        .sort_values("eur_fy2026", ascending=False)
    )

    a_move_eur = float(parts_df[parts_df.group.eq("A_pumps") & parts_df.verdict.eq("move")].eur_fy2026.sum())
    a_decide_eur = float(parts_df[parts_df.group.eq("A_pumps") & parts_df.verdict.eq("decide")].eur_fy2026.sum())
    b_move = parts_df[parts_df.group.eq("B_real_labels") & parts_df.verdict.eq("move")]
    c_move = parts_df[parts_df.group.eq("C_not_real_labels") & parts_df.verdict.eq("move")]

    lines = []
    lines.append("# Wrong AIM labels on billed parts - proposal for the next release")
    lines.append("")
    lines.append(
        f"In the AIM release of 11 October, {len(moves_parts)} billed parts look misfiled against their own "
        f"description (EUR {moves_parts.eur_fy2026.sum():,.0f} in FY2026). I propose moving them to an existing "
        f"AIM leaf. Another {len(decide_parts)} parts (EUR {decide_parts.eur_fy2026.sum():,.0f}) are wrong or "
        f"unclear but have no existing leaf that fits, so they need a name or a no from you before any release. "
        f"The 30 pad kits stay in the separate pad-kit proposal and are not in this file. Nothing has been applied."
    )
    lines.append("")
    lines.append(
        f"Oil and water pumps are the largest clean block: 50 oil pumps (EUR {float(oil.eur_fy2026.sum()):,.0f}) "
        f"and 25 water pumps (EUR {float(water.eur_fy2026.sum()):,.0f}) sit under Fuel Pump or Gasket; they move to "
        f"Lubrication > Oil Pump > Oil Pump and Cooling > Water Pump > Water Pump. Six vacuum pumps "
        f"(EUR {float(vac.eur_fy2026.sum()):,.0f}) stay on decide - there is no vacuum-pump leaf."
    )
    lines.append("")
    lines.append("The ten largest proposed moves by part:")
    for r in top10.itertuples():
        lines.append(
            f"* {r.part_number} — {r.description or '(no description)'} — EUR {r.eur_fy2026:,.0f} FY2026 — "
            f"from {r.current_aim_l1} > {r.current_aim_l2} > {r.current_aim_l3} "
            f"to {r.proposed_aim_l1} > {r.proposed_aim_l2} > {r.proposed_aim_l3}"
        )
    lines.append("")
    lines.append("Decide list (wrong or unclear, no existing leaf fits), by reason:")
    for r in decide_by_reason.itertuples():
        lines.append(f"* EUR {r.eur_fy2026:,.0f} across {r.parts} parts — {r.reason}")
    lines.append("")
    lines.append(
        f"Also reviewed: {len(b_move)} further real-label moves outside the pump block "
        f"(EUR {b_move.eur_fy2026.sum():,.0f}) and {len(c_move)} moves from blank/Unknown/Review labels "
        f"(EUR {c_move.eur_fy2026.sum():,.0f}). Pairs under EUR 1,000 FY2026 are in the file as not reviewed."
    )
    lines.append("")
    lines.append("Nothing has been applied to the release, the master or the live overlay.")
    lines.append("")
    lines.append("Proposal file, one row per part:")
    lines.append(str(OUT))
    lines.append("")
    lines.append("Pairs file, one row per description key and label:")
    lines.append(str(OUT_PAIRS))
    lines.append("")
    lines.append("Builder (proposal only; dry-run checks that only AIM labels on move parts would change):")
    lines.append(str(ISZE / "01_data" / "91_build" / "build_next_release_proposal_wrong_labels_20261015.py"))
    lines.append("")
    lines.append(
        "Sources: AIM release of 11 Oct 2026, sales_fact.parquet for FY2026, "
        "price tool billed base via load_base, pad-kit proposal excluded by part number."
    )
    note_txt = "\n".join(lines) + "\n"
    note_txt = note_txt.replace("\u2014", "-").replace("\u2013", "-")
    OUT_NOTE.write_text(note_txt, encoding="utf-8")

    print(json.dumps({
        "parts": int(len(parts_df)),
        "pairs": int(len(pairs_df)),
        "move_parts": int(len(move_pns)),
        "decide_parts": int(len(decide_parts)),
        "by_group_verdict": summary["by_group_verdict"],
        "out": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
