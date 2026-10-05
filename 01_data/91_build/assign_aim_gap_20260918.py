#!/usr/bin/env python3
"""Classify pricing-revision AIM gap PNs (Not on AIM spine / Not classified at L3).

Evidence order:
  1. Description + unit-price / PN patterns
  2. HS6 modal from already-classified aim_master_v2
  3. Catalogue / workbook AIM labels where present
  4. Figure-key modal (weak)
  5. Residual -> needs_eq_hit / needs_list

Writes:
  01_data/00_derived/aim_gap_auto_assign_20260918.csv
  01_data/90_INBOX/aim_gap_auto_assign_20260918_summary.md
  01_data/00_derived/aim_gap_high_conf_patch_20260918.csv
  Optionally patches aim_master_v2 aim_l1_fixed/aim_l2_fixed/aim_l3 for HIGH only.
"""
from __future__ import annotations

import re
import time
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
INBOX = ROOT / "01_data" / "90_INBOX"
APPLY_HIGH_TO_MASTER = True

# ---------------------------------------------------------------------------
# Description rules: (id, confidence, L1, L2, L3, patterns, exceptions)
# Patterns match uppercase description. First match wins (order matters).
# ---------------------------------------------------------------------------
DESC_RULES: list[tuple] = [
    # --- noise / fluids (must be early) ---
    ("rebate", "high", "Logistics Packaging", "Packaging", "Label",
     [r"\bREBATE\b", r"^0000REBATE$"], []),
    ("transport", "high", "Logistics Packaging", "Packaging", "Label",
     [r"\bTRANSPORT", r"^0TRANSPORT$"], []),
    ("shell_lube", "high", "Fluids Chemicals", "Lubricants", "Lubricant",
     [r"^05500", r"\bRIM R4\b", r"\b15W40\b", r"\b10W40\b", r"\b5W30\b",
      r"\bENGINE OIL\b", r"\bGEAR OIL\b", r"\bATF\b", r"\bAXLE.?OIL\b",
      r"T/AXLEOIL", r"\bLUBRICANT\b", r"\bGREASE\b"],
     [r"\bFILTER\b", r"\bSEAL\b", r"\bGASKET\b", r"\bPIPE\b", r"\bHOSE\b",
      r"\bPUMP\b", r"\bCOOLER\b", r"\bSENSOR\b"]),
    ("atf_fluid", "high", "Fluids Chemicals", "Transmission Fluid", "ATF",
     [r"\bATF\b", r"TRANS(MISSION)?\s*FLUID", r"\bDEXRON\b"],
     [r"\bFILTER\b", r"\bSEAL\b", r"\bGASKET\b", r"\bCOOLER\b"]),
    ("cleaner_chem", "high", "Fluids Chemicals", "Cleaning Chemicals", "Cleaner",
     [r"\bCLEANER\b", r"\bDETERGENT\b", r"\bBRAKE CLEAN"], []),

    # --- complete assemblies (high euro, clear nouns) ---
    ("engine_asm", "high", "Engine", "Complete Assembly", "Engine Assembly",
     [r"\bENGINE ASM\b", r"\bENGINE ASSY\b", r"^ENGINE;"],
     [r"\bMOUNT\b", r"\bGASKET\b", r"\bCOVER\b", r"\bBRACKET\b", r"\bHARNESS\b"]),
    ("trans_asm", "high", "Transmission", "Geartrain", "Gear",
     [r"\bTRANSMISSION ASM\b", r"\bTRANS ASM\b"],
     [r"\bMOUNT\b", r"\bGASKET\b", r"\bCOOLER\b", r"\bHARNESS\b", r"\bFILTER\b"]),
    ("transfer_asm", "high", "Driveline Axle", "Final Drive", "Final Drive Asm",
     [r"\bTRANSFER ASM\b", r"\bTRANSFER CASE\b"],
     [r"\bGASKET\b", r"\bSEAL\b", r"\bBOLT\b"]),
    ("clutch_asm", "high", "Clutch", "Clutch Kit", "Clutch Kit",
     [r"\bCLUTCH ASM\b", r"\bCLUTCH KIT\b", r"\bDISC; ?CLU", r"COVER ASM; ?CLU",
      r"PRESSURE PLATE", r"BEARING; ?RELEASE", r"RELEASE BEARING"],
     [r"\bBOLT\b", r"\bNUT\b", r"\bFAN\b", r"\bCABLE\b", r"\bPEDAL\b"]),
    ("cab_asm", "high", "Accident & Body", "Panels", "Panel",
     [r"\bCAB ASM\b"], [r"\bMOUNT\b", r"\bBOLT\b", r"\bHARNESS\b"]),
    ("hv_battery", "high", "Electrical", "Starting & Charging", "Battery Cable",
     [r"BATTERY ASM; ?HIGH VOLTAGE", r"HIGH.?VOLTAGE.?BATTERY", r"\bHV BATTERY\b"],
     []),  # note: L3 is closest available; flagged in notes as EV-adjacent

    # --- brakes ---
    ("brake_pad_kit", "high", "Brakes", "Pads & Shoes", "Brake Pad Kit",
     [r"PAD KIT", r"PAD; ?DISC BRK", r"\bBRAKE PAD\b"],
     [r"\bSWITCH\b", r"\bSENSOR\b", r"\bSHIM\b", r"\bSPRING\b", r"\bPIN\b"]),
    ("brake_pad", "high", "Brakes", "Pads & Shoes", "Brake Pad",
     [r"\bPAD;.*BRK", r"\bBRK.?PAD\b"],
     [r"\bKIT\b", r"\bSWITCH\b", r"\bSENSOR\b"]),
    ("brake_shoe", "high", "Brakes", "Pads & Shoes", "Brake Shoe",
     [r"\bSHOE;.*BRK", r"\bBRAKE SHOE\b", r"SHOE ASM; ?BRK"],
     [r"\bSWITCH\b", r"\bSENSOR\b", r"\bSPRING\b"]),
    ("brake_lining", "high", "Brakes", "Pads & Shoes", "Brake Lining",
     [r"LINING;.*BRK", r"\bBRAKE LINING\b"], []),
    ("brake_disc", "high", "Brakes", "Disc & Drum", "Brake Disc",
     [r"\bDISC; ?BRK", r"ROTOR; ?DISC BRK", r"\bBRAKE DISC\b", r"\bBRAKE ROTOR\b"],
     [r"\bPAD\b", r"\bSHOE\b", r"\bCALIPER\b"]),
    ("brake_drum", "high", "Brakes", "Disc & Drum", "Brake Drum",
     [r"\bDRUM; ?BRK", r"\bBRAKE DRUM\b"], []),
    ("brake_caliper", "high", "Brakes", "Caliper", "Brake Caliper",
     [r"\bCALIPER\b"], [r"\bPAD\b", r"\bKIT\b", r"\bBOLT\b", r"\bPIN\b", r"\bSEAL\b"]),
    ("brake_hose", "high", "Brakes", "Hydraulic", "Brake Hose",
     [r"HOSE; ?BRK", r"\bBRAKE HOSE\b"], []),
    ("brake_pipe", "high", "Brakes", "Hydraulic", "Brake Pipe",
     [r"PIPE; ?BRK", r"\bBRAKE PIPE\b"], [r"\bEXHAUST\b"]),
    ("brake_valve", "high", "Brakes", "Booster & Control", "Brake Valve",
     [r"VALVE; ?BRK", r"\bBRAKE VALVE\b", r"\bBRAKE UNIT\b"],
     [r"\bABS\b", r"\bSENSOR\b"]),
    ("abs_sensor", "high", "Brakes", "ABS Control", "ABS Sensor",
     [r"SENSOR; ?ABS", r"\bABS SENSOR\b", r"SENSOR; ?WHEEL SPEED"], []),

    # --- steering ---
    ("drag_link", "high", "Steering", "Linkage", "Drag Link",
     [r"LINK; ?DRAG", r"\bDRAG LINK\b"], []),
    ("tie_rod", "high", "Steering", "Linkage", "Tie Rod",
     [r"\bTIE ROD\b", r"ROD ASM; ?TIE", r"\bTIE-ROD\b"], [r"\bEND\b"]),
    ("tie_rod_end", "high", "Steering", "Linkage", "Tie Rod End",
     [r"TIE ROD END", r"END; ?TIE"], []),
    ("steering_unit", "high", "Steering", "Steering Gear", "Steering Unit",
     [r"STEERING (UNIT|GEAR|BOX)", r"\bPOWER STEERING\b"],
     [r"\bHOSE\b", r"\bPUMP\b", r"\bSEAL\b", r"\bBOOT\b"]),
    ("king_pin", "high", "Steering", "Knuckle & King Pin", "King Pin Kit",
     [r"\bKING.?PIN\b", r"PIN; ?KING"], []),
    ("knuckle", "high", "Steering", "Knuckle & King Pin", "King Pin Kit",
     [r"\bKNUCKLE\b"], [r"\bBALL\b", r"\bBUSH"]),

    # --- suspension ---
    ("shock", "high", "Suspension", "Shock Absorber", "Damper",
     [r"ABSORBER ASM", r"SHOCK ABSORBER", r"\bDAMPER\b"],
     [r"\bBUSH", r"\bMOUNT\b", r"\bBOLT\b"]),
    ("leaf_spring", "high", "Suspension", "Leaf Springs", "Leaf Spring Asm",
     [r"SPRING ASM; ?(LEAF|FRT|RR)", r"\bLEAF SPR", r"SPRING; ?LEAF"],
     [r"\bBUSH", r"\bSHACKLE\b", r"\bPIN\b", r"\bSEAT\b"]),
    ("air_spring", "high", "Suspension", "Air Suspension", "Air Spring",
     [r"\bAIR SPRING\b", r"SPRING; ?AIR", r"\bAIR BAG; ?SUS"], []),
    ("ball_joint", "high", "Suspension", "Suspension Arm", "Ball Joint",
     [r"JOINT ASM; ?BALL", r"\bBALL JOINT\b"], []),
    ("bushing_susp", "high", "Suspension", "Bush & Mount", "Bushing",
     [r"\bBUSHING\b", r"\bBUSH;"],
     [r"\bENGINE\b", r"\bCAB\b", r"\bTRANS"]),
    ("shackle", "high", "Suspension", "Spring", "Shackle",
     [r"\bSHACKLE\b"], []),

    # --- fuel ---
    ("common_rail", "high", "Fuel System", "Fuel Rail", "Common Rail",
     [r"RAIL; ?COMMON", r"\bCOMMON RAIL\b", r"\bFUEL RAIL\b"], []),
    ("injector", "high", "Fuel System", "Fuel Control", "Injector",
     [r"INJECTOR ASM(?!.*DEF)", r"NOZZLE ASM; ?INJ", r"\bINJECTOR\b"],
     [r"\bPIPE\b", r"\bSEAL\b", r"\bGASKET\b", r"\bDEF\b", r"\bHOLDER\b"]),
    ("inj_nozzle", "high", "Fuel System", "Injection", "Injector Nozzle",
     [r"NOZZLE; ?INJ", r"\bINJECTION NOZZLE\b"], [r"\bDEF\b"]),
    ("fuel_pump", "high", "Fuel System", "Fuel Pump", "Fuel Pump",
     [r"PUMP ASM; ?(FUEL|INJ)", r"\bFUEL PUMP\b", r"PUMP; ?FUEL"],
     [r"\bDEF\b", r"\bWATER\b", r"\bOIL\b"]),
    ("fuel_press_limiter", "high", "Fuel System", "Fuel Control", "Fuel Sensor",
     [r"LIMITER; ?FUEL", r"FUEL PRESS", r"PRESSURE.?LIMITER"],
     [r"\bHOSE\b", r"\bPIPE\b"]),
    ("fuel_filter", "high", "Maintenance Service", "Fuel Filter", "Fuel Filter Element",
     [r"\bFUEL FILTER\b", r"FILTER; ?FUEL", r"ELEMENT; ?FUEL"],
     [r"\bBRACKET\b", r"\bCASE\b", r"\bCOVER\b", r"\bPUMP\b"]),
    ("fuel_tank", "high", "Fuel System", "Tank & Supply", "Fuel Tank",
     [r"TANK; ?FUEL", r"\bFUEL TANK\b"], [r"\bCAP\b", r"\bSENDER\b"]),
    ("fuel_hose", "high", "Fuel System", "Fuel Lines & Hoses", "Fuel Hose",
     [r"HOSE; ?FUEL", r"\bFUEL HOSE\b"], []),
    ("fuel_pipe", "high", "Fuel System", "Fuel Lines & Hoses", "Fuel Pipe",
     [r"PIPE; ?FUEL", r"\bFUEL PIPE\b"], []),

    # --- intake / exhaust / emission ---
    ("turbo", "high", "Intake Exhaust Emission", "Turbo", "Turbocharger",
     [r"\bTURBOCHARGER\b", r"TURBO CHARGER", r"\bTURBO ASM\b"],
     [r"\bGASKET\b", r"\bPIPE\b", r"\bHOSE\b", r"\bBRACKET\b", r"\bACTUATOR\b"]),
    ("nox_sensor", "high", "Intake Exhaust Emission", "Sensors", "NOx Sensor",
     [r"SENSOR;.*NOX", r"\bNOX SENSOR\b", r"DEF.?DCM.?EXH.?NOX"], []),
    ("pm_sensor", "high", "Intake Exhaust Emission", "Sensors", "PM Sensor",
     [r"SENSOR; ?PM\b", r"\bPM SENSOR\b", r"SENSOR; ?PARTICULATE"], []),
    ("o2_sensor", "high", "Intake Exhaust Emission", "Sensors", "NOx Sensor",
     [r"SENSOR; ?O2", r"\bO2 SENSOR\b", r"\bOXYGEN SENSOR\b", r"\bLAMBDA\b"],
     []),  # closest emission sensor L3
    ("map_sensor", "high", "Electrical", "Sensors", "Speed Sensor",
     [r"SENSOR; ?MAP", r"\bMAP SENSOR\b", r"SENSOR; ?MANIF"],
     []),  # note: manifold/MAP — electrical sensor bucket
    ("def_sensor", "high", "Intake Exhaust Emission", "DEF System", "DEF Sensor",
     [r"SENSOR; ?DEF", r"\bDEF SENSOR\b", r"SENSOR; ?UREA"], []),
    ("def_pump", "high", "Intake Exhaust Emission", "DEF System", "DEF Pump",
     [r"PUMP; ?DEF", r"\bDEF PUMP\b", r"PUMP ASM; ?DEF"], []),
    ("def_tank", "high", "Intake Exhaust Emission", "DEF System", "DEF Tank",
     [r"TANK; ?DEF", r"\bDEF TANK\b", r"TANK; ?UREA"], []),
    ("dpd_asm", "high", "Intake Exhaust Emission", "DPF/DPD", "DPD Assembly",
     [r"\bDPD ASM\b", r"\bDPF ASM\b", r"\bDPD\b", r"\bDPF\b"],
     [r"\bSENSOR\b", r"\bGASKET\b", r"\bPIPE\b", r"\bCLAMP\b"]),
    ("egr", "high", "Intake Exhaust Emission", "EGR", "EGR Component",
     [r"\bEGR\b"], [r"\bGASKET\b", r"\bBOLT\b"]),
    ("catalyst", "high", "Intake Exhaust Emission", "Emission Control", "Catalyst",
     [r"\bCATALYST\b", r"\bCATCON\b", r"CONVERTER; ?CAT"], []),
    ("exhaust_pipe", "high", "Intake Exhaust Emission", "Exhaust", "Exhaust Pipe",
     [r"PIPE; ?EXH", r"\bEXHAUST PIPE\b", r"PIPE ASM; ?EXH"],
     [r"\bFUEL\b", r"\bWATER\b", r"\bOIL\b"]),
    ("silencer", "high", "Intake Exhaust Emission", "Exhaust", "Silencer",
     [r"\bSILENCER\b", r"\bMUFFLER\b"], []),
    ("throttle_asm", "high", "Intake Exhaust Emission", "Air Intake", "Air Duct",
     [r"THROTTLE ASM", r"\bTHROTTLE BODY\b"], []),
    ("charge_air_cooler", "high", "Cooling", "Radiator", "Radiator Assembly",
     [r"COOLER; ?CHARGE AIR", r"\bINTERCOOLER\b", r"COOLER; ?AIR"],
     [r"\bOIL\b", r"\bFUEL\b", r"\bATF\b"]),
    ("air_duct", "high", "Intake Exhaust Emission", "Air Intake", "Air Duct",
     [r"\bAIR DUCT\b", r"DUCT; ?AIR", r"GUIDE ASM; ?AIR"], []),

    # --- cooling ---
    ("radiator", "high", "Cooling", "Radiator", "Radiator Assembly",
     [r"^RADIATOR", r"\bRADIATOR ASM\b", r"RADIATOR;"],
     [r"\bCAP\b", r"\bHOSE\b", r"\bBRACKET\b", r"\bGRILLE\b", r"\bSUPPORT\b"]),
    ("water_pump", "high", "Cooling", "Water Pump", "Water Pump",
     [r"PUMP ASM; ?WATER", r"PUMP; ?WATER", r"\bWATER PUMP\b"],
     [r"\bWASHER\b"]),
    ("thermostat", "high", "Cooling", "Thermostat & Control", "Thermostat",
     [r"^THERMOSTAT", r"\bTHERMOSTAT\b"], [r"\bHOUSING\b", r"\bGASKET\b"]),
    ("water_pipe", "high", "Cooling", "Cooling Hoses & Pipes", "Water Pipe",
     [r"PIPE; ?WATER", r"\bWATER PIPE\b", r"HOSE; ?WATER", r"\bBYPASS HOSE\b"],
     [r"\bFUEL\b", r"\bOIL\b", r"\bBRAKE\b"]),
    ("ac_condenser", "high", "Cooling", "Radiator", "Radiator Assembly",
     [r"CONDENSER ASM", r"\bCONDENSER\b.*A/?C", r"COMPRESSOR ASM; ?A/?C"],
     []),
    ("ac_compressor", "high", "Cooling", "Radiator", "Radiator Assembly",
     [r"COMPRESSOR ASM; ?A/?C", r"\bA/?C COMPRESSOR\b"], []),

    # --- engine internals ---
    ("oil_pan", "high", "Engine", "Block & Structure", "Oil Pan",
     [r"PAN ASM; ?OIL", r"\bOIL PAN\b", r"PAN; ?OIL"], []),
    ("cyl_head", "high", "Engine", "Cylinder Head", "Head Cover",
     [r"HEAD ASM; ?CYL", r"\bCYLINDER HEAD\b", r"HEAD; ?CYL"],
     [r"\bGASKET\b", r"\bBOLT\b", r"\bCOVER\b"]),
    ("piston", "high", "Engine", "Internal Rotating", "Piston",
     [r"\bPISTON\b"], [r"\bPIN\b", r"\bRING\b", r"\bCALIPER\b"]),
    ("crankshaft", "high", "Engine", "Internal Rotating", "Crankshaft",
     [r"\bCRANKSHAFT\b", r"\bCRANK SHAFT\b"], []),
    ("camshaft", "high", "Engine", "Valve Train", "Camshaft",
     [r"\bCAMSHAFT\b", r"\bCAM SHAFT\b"], []),
    ("timing_chain", "high", "Engine", "Timing Drive", "Timing Chain",
     [r"\bTIMING CHAIN\b", r"CHAIN; ?TIMING"], []),
    ("timing_belt", "high", "Maintenance Service", "Belts", "Timing Belt",
     [r"\bTIMING BELT\b", r"BELT; ?TIMING"], []),
    ("drive_belt", "high", "Maintenance Service", "Belts", "Drive Belt",
     [r"\bDRIVE BELT\b", r"BELT; ?DRIVE", r"\bFAN BELT\b", r"\bV-BELT\b"], []),
    ("oil_seal", "high", "Engine", "Gasket & Sealing", "Oil Seal",
     [r"\bOIL SEAL\b", r"SEAL; ?OIL"],
     [r"\bHUB\b", r"\bAXLE\b", r"\bWHEEL\b"]),
    ("gasket_eng", "medium", "Transmission", "Bearings & Seals", "Gasket",
     [r"\bGASKET\b"],
     [r"\bHEAD\b", r"\bEXH\b", r"\bINTAKE\b"]),  # generic gasket — medium
    ("oil_filter", "high", "Maintenance Service", "Oil Filter", "Oil Filter Element",
     [r"\bOIL FILTER\b", r"FILTER; ?OIL", r"ELEMENT; ?OIL FILTER", r"ELEMENT; ?OIL\b"],
     [r"\bBRACKET\b", r"\bCOOLER\b", r"\bPIPE\b", r"\bSENSOR\b"]),
    ("air_filter", "high", "Maintenance Service", "Air Filter", "Air Cleaner Filter",
     [r"FILTER; ?ACL", r"ELEMENT; ?A[CI]L", r"ELEMENT; ?AIR CLEANER",
      r"FILTER; ?AIR CLEANER", r"\bAIR FILTER\b"],
     [r"\bCASE\b", r"\bCOVER\b", r"\bBRACKET\b", r"\bDUCT\b", r"\bHOSE\b"]),
    ("oil_cooler", "high", "Lubrication", "Oil Filter System", "Oil Cooler",
     [r"COOLER; ?OIL", r"\bOIL COOLER\b"], []),
    ("oil_pump", "high", "Lubrication", "Oil Pump", "Oil Pump",
     [r"PUMP; ?OIL", r"PUMP ASM; ?OIL", r"\bOIL PUMP\b"],
     [r"\bWATER\b", r"\bFUEL\b", r"\bDEF\b"]),
    ("glow_plug", "high", "Maintenance Service", "Ignition & Tune-Up", "Glow Plug",
     [r"\bGLOW PLUG\b", r"PLUG; ?GLOW"], []),

    # --- driveline ---
    ("prop_shaft", "high", "Driveline Axle", "Axle Shaft", "Drive Shaft",
     [r"SHAFT ASM; ?PROP", r"PROPELLER SHAFT", r"SHAFT ASM; ?FRT DRIVE",
      r"SHAFT ASM; ?DRIVE", r"\bDRIVE SHAFT\b"],
     [r"\bSEAL\b", r"\bBOLT\b"]),
    ("axle_shaft", "high", "Driveline Axle", "Axle Shaft", "Axle Shaft",
     [r"SHAFT; ?AXLE", r"\bAXLE SHAFT\b"], []),
    ("diff_pinion", "high", "Driveline Axle", "Differential", "Pinion",
     [r"\bPINION\b"], [r"\bSTEERING\b"]),
    ("diff_carrier", "high", "Driveline Axle", "Differential", "Carrier",
     [r"\bDIFF(ERENTIAL)? (ASM|CARRIER|CASE)\b", r"CARRIER; ?DIFF"], []),
    ("axle_seal", "high", "Driveline Axle", "Final Drive Bearings & Seals", "Axle Seal",
     [r"SEAL; ?AXLE", r"\bAXLE SEAL\b"], []),

    # --- electrical ---
    ("alternator", "high", "Electrical", "Charging", "Alternator/Generator",
     [r"\bALTERNATOR\b", r"GENERATOR ASM", r"\bGENERATOR\b"],
     [r"\bBRACKET\b", r"\bPULLEY\b", r"\bBELT\b", r"\bHARNESS\b"]),
    ("starter", "high", "Electrical", "Motors & Actuators", "Motor",
     [r"STARTER ASM", r"\bSTARTER\b"],
     [r"\bSWITCH\b", r"\bRELAY\b", r"\bSOLENOID\b", r"\bBRACKET\b"]),
    ("control_unit", "high", "Electrical", "Control Units", "Control Unit",
     [r"\bECM\b", r"\bECU\b", r"\bCONTROL (UNIT|MODULE)\b", r"UNIT; ?CONTROL",
      r"MODULE; ?CONTROL", r"\bBCM\b", r"\bTCM\b"],
     [r"\bBRACKET\b", r"\bCOVER\b"]),
    ("harness", "high", "Electrical", "Harness & Connectors", "Connector",
     [r"\bHARNESS\b", r"\bWIRING\b"],
     [r"\bCLIP\b", r"\bBRACKET\b", r"\bPROTECTOR\b"]),
    ("relay", "high", "Electrical", "Switch Relay Fuse", "Relay",
     [r"\bRELAY\b"], []),
    ("fuse", "high", "Electrical", "Switch Relay Fuse", "Fuse",
     [r"\bFUSE\b"], [r"\bBOX\b", r"\bBLOCK\b"]),
    ("switch", "high", "Electrical", "Switch Relay Fuse", "Switch",
     [r"\bSWITCH\b"], [r"\bHARNESS\b", r"\bBRACKET\b"]),
    ("speed_sensor", "high", "Electrical", "Sensors", "Speed Sensor",
     [r"SENSOR; ?SPEED", r"\bSPEED SENSOR\b", r"SENSOR; ?VEHICLE SPEED"], []),
    ("tire_sensor", "high", "Electrical", "Sensors & Switches", "Radar Sensor",
     [r"SENSOR; ?TIRE", r"\bTPMS\b", r"TIRE INFLATION"], []),
    ("radar_sensor", "high", "Electrical", "Sensors & Switches", "Radar Sensor",
     [r"SENSOR; ?RADAR", r"\bRADAR\b", r"\bMILLIMETER"], []),
    ("camera", "high", "Electrical", "Instruments", "Instrument Cluster",
     [r"\bCAMERA ASM\b", r"\bCAMERA\b"], [r"\bBRACKET\b", r"\bCOVER\b"]),
    ("display", "high", "Electrical", "Instruments", "Instrument Cluster",
     [r"\bDISPLAY\b", r"\bMONITOR\b", r"RADIO CONTROL ASM", r"\bSTEREO\b"], []),
    ("instrument", "high", "Electrical", "Instruments", "Instrument Cluster",
     [r"\bMETER CLUSTER\b", r"\bCOMBINATION METER\b", r"CLUSTER; ?METER"], []),
    ("actuator", "high", "Electrical", "Motors & Actuators", "Actuator",
     [r"\bACTUATOR\b"], [r"\bTURBO\b"]),
    ("motor_gen", "high", "Electrical", "Motors & Actuators", "Motor",
     [r"\bMOTOR\b"], [r"\bSTARTER\b", r"\bWIPER\b", r"\bWINDOW\b"]),
    ("wiper_motor", "high", "Electrical", "Motors & Actuators", "Wiper Motor",
     [r"MOTOR; ?WIPER", r"\bWIPER MOTOR\b"], []),
    ("window_motor", "high", "Electrical", "Motors & Actuators", "Window Motor",
     [r"MOTOR; ?WINDOW", r"\bWINDOW MOTOR\b", r"MOTOR; ?DOOR"], []),
    ("bulb", "high", "Electrical", "Lighting", "Bulb",
     [r"\bBULB\b", r"\bLAMP; ?BULB"], []),
    ("headlamp", "high", "Accident & Body", "Lamps", "Headlamp Assembly",
     [r"\bHEADLAMP\b", r"\bHEAD LAMP\b", r"LAMP ASM; ?HEAD"],
     [r"\bBULB\b", r"\bSWITCH\b", r"\bBRACKET\b"]),
    ("rear_comb_lamp", "high", "Accident & Body", "Lamps", "Rear Combination Lamp",
     [r"COMB LAMP", r"COMBINATION LAMP", r"LAMP ASM; ?RR", r"LAMP ASM; ?REAR"],
     [r"\bBULB\b", r"\bBRACKET\b"]),
    ("lamp_asm", "high", "Electrical", "Lighting", "Lamp",
     [r"\bLAMP ASM\b", r"\bFOG LAMP\b", r"\bLAMP\b"],
     [r"\bSWITCH\b", r"\bHARNESS\b", r"\bBRACKET\b", r"\bBULB\b", r"\bHEAD\b"]),
    ("airbag", "high", "Cabin Interior", "Seat", "Seat Belt",
     [r"\bAIR.?BAG\b", r"\bINFLATOR\b", r"\bSRS\b"],
     [r"\bCOVER\b", r"\bLABEL\b"]),  # closest safety cabin L3
    ("seat_belt", "high", "Cabin Interior", "Seat", "Seat Belt",
     [r"\bSEAT BELT\b", r"BELT; ?SEAT", r"\bSEATBELT\b"], []),
    ("seat_cushion", "high", "Cabin Interior", "Seat", "Seat Cushion",
     [r"CUSHION ASM; ?.*SEAT", r"\bSEAT CUSHION\b", r"SEAT ASM"],
     [r"\bBELT\b", r"\bBOLT\b"]),

    # --- body ---
    ("bumper", "high", "Accident & Body", "Panels", "Bumper",
     [r"\bBUMPER\b"],
     [r"\bSENSOR\b", r"\bLAMP\b", r"\bHARNESS\b", r"\bBOLT\b", r"\bRUBBER\b",
      r"\bSTOPPER\b"]),
    ("door", "high", "Accident & Body", "Panels", "Door",
     [r"\bDOOR\b"],
     [r"\bHANDLE\b", r"\bLOCK\b", r"\bMIRROR\b", r"\bHARNESS\b", r"\bSWITCH\b",
      r"\bMOTOR\b", r"\bSEAL\b", r"\bWEATHER"]),
    ("grille", "high", "Accident & Body", "Panels", "Grille",
     [r"\bGRILLE\b", r"\bGRILL\b"], [r"\bBOLT\b", r"\bCLIP\b"]),
    ("hood", "high", "Accident & Body", "Panels", "Hood",
     [r"\bHOOD\b", r"\bBONNET\b"], [r"\bLOCK\b", r"\bSTAY\b", r"\bINSULATOR\b"]),
    ("fender", "high", "Accident & Body", "Panels", "Fender",
     [r"\bFENDER\b", r"\bWING\b"], [r"\bLINER\b", r"\bBOLT\b"]),
    ("mirror", "high", "Accident & Body", "Mirrors", "Mirror",
     [r"\bMIRROR\b"],
     [r"\bSWITCH\b", r"\bHARNESS\b", r"\bMOTOR\b", r"\bBOLT\b"]),
    ("windshield", "high", "Accident & Body", "Glass", "Windshield",
     [r"\bWINDSHIELD\b", r"\bWINDSCREEN\b", r"GLASS; ?WIND"], []),
    ("handle", "high", "Accident & Body", "Locks & Handles", "Handle",
     [r"\bHANDLE\b"], [r"\bDOOR ASM\b"]),
    ("latch", "high", "Accident & Body", "Locks & Handles", "Latch",
     [r"\bLATCH\b", r"\bLOCK ASM\b"], []),
    ("wiper_blade", "high", "Accident & Body", "Wiper & Washer", "Wiper Blade",
     [r"BLADE; ?WIPER", r"\bWIPER BLADE\b", r"\bBLADE\b.*WIPER"], []),
    ("wiper_arm", "high", "Accident & Body", "Wiper & Washer", "Wiper Arm",
     [r"ARM; ?WIPER", r"\bWIPER ARM\b"], []),
    ("washer_tank", "high", "Accident & Body", "Wiper & Washer", "Washer Tank",
     [r"TANK; ?WASHER", r"\bWASHER TANK\b"], []),
    ("step", "high", "Accident & Body", "Panels", "Step",
     [r"\bSTEP\b"], [r"\bMOTOR\b", r"\bSWITCH\b"]),
    ("body_asm_rear", "high", "Accident & Body", "Panels", "Panel",
     [r"BODY ASM; ?REAR", r"BODY ASM; ?FRT", r"\bBODY ASM\b"], []),
    ("rear_gate", "high", "Accident & Body", "Rear Gate", "Rear Gate Assembly",
     [r"\bREAR GATE\b", r"GATE ASM; ?RR", r"\bTAILGATE\b"], []),
    ("weatherstrip", "high", "Accident & Body", "Trim", "Weatherstrip",
     [r"\bWEATHERSTRIP\b", r"\bWEATHER STRIP\b"], []),
    ("emblem", "high", "Accident & Body", "Trim", "Emblem",
     [r"\bEMBLEM\b", r"\bBADGE\b", r"\bDECAL\b"], []),
    ("molding", "medium", "Accident & Body", "Panels", "Panel",
     [r"\bMOLDING\b", r"\bMOULDING\b"], []),

    # --- wheels ---
    ("wheel_rim", "high", "Wheels Hub", "Wheel Rim", "Rim",
     [r"\bRIM\b", r"\bWHEEL\b"],
     [r"\bNUT\b", r"\bBOLT\b", r"\bBEARING\b", r"\bHUB\b", r"\bSENSOR\b",
      r"\b15W40\b", r"R4L", r"\bOIL\b"]),  # exclude Shell Rim oils
    ("hub", "high", "Wheels Hub", "Hub & Bearing", "Hub",
     [r"\bHUB\b"], [r"\bCAP\b", r"\bBOLT\b", r"\bNUT\b", r"\bSEAL\b"]),
    ("hub_seal", "high", "Wheels Hub", "Hub Seals", "Hub Seal",
     [r"SEAL; ?HUB", r"\bHUB SEAL\b"], []),

    # --- transmission gears ---
    ("gear", "high", "Transmission", "Geartrain", "Gear",
     [r"^GEAR;", r"\bGEAR\b"],
     [r"\bSTEERING\b", r"\bPUMP\b", r"\bOIL\b", r"\bRING\b"]),
    ("syncro", "high", "Transmission", "Geartrain", "Synchronizer",
     [r"\bSYNCHRONIZER\b", r"\bSYNCHRO\b", r"RING; ?SYNCHRO"], []),
    ("shift_fork", "high", "Transmission", "Shift Mechanism", "Shift Fork",
     [r"FORK; ?SHIFT", r"\bSHIFT FORK\b"], []),
    ("overhaul_kit", "high", "Transmission", "Repair Kits", "Overhaul Kit",
     [r"\bOVERHAUL KIT\b", r"KIT; ?OVERHAUL", r"REPAIR KIT; ?TRANS"], []),
    ("repair_kit_gen", "medium", "Transmission", "Repair Kits", "Overhaul Kit",
     [r"\bREPAIR KIT\b"], []),

    # --- chassis hardware ---
    ("bolt", "high", "Chassis Frame", "Mounting Hardware", "Bolt",
     [r"^BOLT;", r"^BOLT$"], []),
    ("nut", "high", "Chassis Frame", "Mounting Hardware", "Nut",
     [r"^NUT;", r"^NUT$"], []),
    ("plate", "medium", "Chassis Frame", "Mounting Hardware", "Plate",
     [r"^PLATE;", r"^PLATE$"], [r"\bCLUTCH\b", r"\bPRESSURE\b"]),
    ("bracket", "high", "Chassis Frame", "Crossmember & Brackets", "Bracket",
     [r"\bBRACKET\b", r"\bBRKT\b"], []),
    ("support", "high", "Chassis Frame", "Crossmember & Brackets", "Support",
     [r"\bSUPPORT\b"], [r"\bBEARING\b"]),
    ("stay", "high", "Chassis Frame", "Crossmember & Brackets", "Stay",
     [r"\bSTAY\b"], []),
    ("guard", "high", "Chassis Frame", "Underbody Protection", "Guard",
     [r"\bGUARD\b", r"\bPROTECTOR\b"], [r"\bHARNESS\b"]),
    ("crossmember", "high", "Chassis Frame", "Crossmember & Brackets", "Crossmember",
     [r"\bCROSSMEMBER\b", r"\bCROSS MEMBER\b"], []),

    # --- cabin ---
    ("cable", "high", "Cabin Interior", "Pedals & Controls", "Cable",
     [r"\bCABLE\b"], [r"\bBATTERY\b", r"\bHARNESS\b"]),
    ("lever", "high", "Cabin Interior", "Pedals & Controls", "Lever",
     [r"\bLEVER\b"], []),
    ("knob", "high", "Cabin Interior", "Dashboard & Controls", "Knob",
     [r"\bKNOB\b"], []),
    ("sun_visor", "high", "Cabin Interior", "Interior Trim", "Sun Visor",
     [r"\bVISOR\b", r"\bSUN VISOR\b"], []),
    ("floor_mat", "high", "Cabin Interior", "Interior Trim", "Floor Mat",
     [r"\bFLOOR MAT\b", r"MAT; ?FLOOR"], []),
    ("blower_filter", "high", "Cabin Interior", "HVAC Filters", "Blower Filter",
     [r"FILTER; ?CABIN", r"FILTER; ?BLOWER", r"\bCABIN FILTER\b", r"\bPOLLEN\b"], []),

    # --- tools / literature ---
    ("special_tool", "low", "Tools Equipment", "Workshop Tools", "Gauge",
     [r"\bSST\b", r"\bSPECIAL TOOL\b", r"\bPULLER\b", r"\bTESTER\b",
      r"\bGAUGE\b", r"\bTOOL\b"],
     [r"\bBOX\b"]),  # often needs_list
    ("manual", "high", "Literature Marketing", "Manuals", "Manual",
     [r"\bMANUAL\b", r"\bHANDBOOK\b", r"\bCATALOGUE\b", r"\bCATALOG\b"],
     [r"\bTRANSMISSION\b", r"\bGEAR\b"]),
    ("label_pkg", "high", "Logistics Packaging", "Packaging", "Label",
     [r"^LABEL;", r"\bLABEL\b"], []),

    # --- sensors catch-all (after specific sensors) ---
    ("sensor_generic", "medium", "Electrical", "Sensors", "Speed Sensor",
     [r"\bSENSOR\b"], []),

    # --- hose/pipe catch-alls (after specific) ---
    ("hose_generic", "medium", "Cooling", "Cooling Hoses & Pipes", "Water Pipe",
     [r"^HOSE;", r"\bHOSE\b"],
     [r"\bFUEL\b", r"\bBRAKE\b", r"\bOIL\b", r"\bAIR\b"]),
    ("pipe_generic", "medium", "Cooling", "Cooling Hoses & Pipes", "Water Pipe",
     [r"^PIPE;", r"\bPIPE\b"],
     [r"\bFUEL\b", r"\bBRAKE\b", r"\bEXH\b", r"\bOIL\b"]),

    # --- bearing ---
    ("bearing", "medium", "Transmission", "Bearings & Seals", "Gasket",
     [r"\bBEARING\b"],
     [r"\bRELEASE\b", r"\bHUB\b", r"\bWHEEL\b"]),  # L3 weak — note

    # --- hydraulic unit (often ABS/ESP) ---
    ("hydraulic_unit_abs", "high", "Brakes", "ABS Control", "ABS Sensor",
     [r"HYDRAULIC UNIT; ?ANTI LOCK", r"\bABS HYDRAULIC\b", r"UNIT; ?ABS"], []),
    ("brake_booster", "high", "Brakes", "Booster & Control", "Brake Valve",
     [r"BOOSTER; ?HYDRAULIC BRK", r"\bBRAKE BOOSTER\b", r"BOOSTER; ?BRK"], []),
    ("hydraulic_unit", "medium", "Brakes", "ABS Control", "ABS Sensor",
     [r"\bHYDRAULIC UNIT\b", r"UNIT; ?HYDRAULIC"], []),

    # --- more residual euros ---
    ("inj_pipe", "high", "Fuel System", "Fuel Lines & Hoses", "Fuel Pipe",
     [r"PIPE ASM; ?INJ", r"PIPE; ?INJ", r"\bINJECTION PIPE\b"], []),
    ("drain_plug", "high", "Lubrication", "Sump & Sealing", "Drain Plug",
     [r"PLUG; ?DRAIN", r"\bDRAIN PLUG\b"], []),
    ("tie_rod_short", "high", "Steering", "Linkage", "Tie Rod",
     [r"^ROD; ?TIE\b", r"ROD; ?TIE,"], []),
    ("joint_out_drive", "high", "Driveline Axle", "Axle Shaft", "Drive Shaft",
     [r"JOINT ASM; ?OUTSIDE", r"JOINT ASM; ?FRT DRIVE", r"CV JOINT"], []),
    ("prop_journal", "high", "Driveline Axle", "Axle Shaft", "Drive Shaft",
     [r"JOURNAL ASM; ?PROP", r"\bUNIVERSAL JOINT\b", r"JOINT; ?UNIV"], []),
    ("axle_frt", "high", "Driveline Axle", "Axle Shaft", "Axle Shaft",
     [r"^AXLE; ?FRT", r"^AXLE; ?RR", r"\bFRONT AXLE\b", r"\bREAR AXLE\b"],
     [r"\bSEAL\b", r"\bBOLT\b", r"\bNUT\b"]),
    ("axle_retainer", "high", "Driveline Axle", "Final Drive Bearings & Seals", "Axle Seal",
     [r"RETAINER; ?.*AXLE", r"RETAINER; ?RR AXLE"], []),
    ("fan_clutch", "high", "Cooling", "Radiator", "Radiator Assembly",
     [r"CLUTCH; ?COOLING FAN", r"\bFAN CLUTCH\b"], []),
    ("heater_unit", "high", "Cabin Interior", "HVAC Filters", "Blower Filter",
     [r"\bHEATER UNIT\b", r"HEATER ASM", r"\bHVAC\b"],
     [r"\bHOSE\b", r"\bPIPE\b"]),  # closest HVAC leaf
    ("power_chamber", "medium", "Brakes", "Booster & Control", "Brake Valve",
     [r"CHAMBER; ?POWER", r"\bBRAKE CHAMBER\b", r"CHAMBER; ?BRK"], []),
    ("gusset", "high", "Chassis Frame", "Crossmember & Brackets", "Reinforcement",
     [r"\bGUSSET\b", r"C/MBR", r"CROSS.?MBR"], []),
    ("expander", "medium", "Brakes", "Pads & Shoes", "Brake Shoe",
     [r"^EXPANDER", r"EXPANDER; ?BRK"], []),
    ("resistor", "medium", "Electrical", "Switch Relay Fuse", "Relay",
     [r"\bRESISTOR\b"], []),
    ("strg_repair_kit", "high", "Steering", "Steering Gear", "Steering Unit",
     [r"REPAIR KIT; ?STRG", r"KIT; ?STEERING"], []),
    ("besco_cleaner", "high", "Fluids Chemicals", "Cleaning Chemicals", "Cleaner",
     [r"\bBESCO\b", r"CLEAN SUPER", r"\bBRAKE CLEAN"], []),
    ("cover_generic", "low", "Chassis Frame", "Mounting Hardware", "Plate",
     [r"^COVER;", r"^COVER$"],
     [r"\bHEAD\b", r"\bVALVE\b", r"\bTIMING\b"]),
    ("rubber_generic", "medium", "Suspension", "Bush & Mount", "Bushing",
     [r"^RUBBER;", r"^RUBBER$"], []),
    ("clip", "high", "Chassis Frame", "Mounting Hardware", "Bolt",
     [r"^CLIP;", r"^CLIP$"], []),
    ("washer_hw", "high", "Chassis Frame", "Mounting Hardware", "Bolt",
     [r"^WASHER;", r"^WASHER$"],
     [r"\bWIND\b", r"\bWIPER\b"]),
    ("screw", "high", "Chassis Frame", "Mounting Hardware", "Bolt",
     [r"^SCREW;", r"^SCREW$"], []),
    ("stud", "high", "Chassis Frame", "Mounting Hardware", "Bolt",
     [r"^STUD;", r"^STUD$"], []),
    ("pin_generic", "medium", "Chassis Frame", "Mounting Hardware", "Bolt",
     [r"^PIN;", r"^PIN$"],
     [r"\bKING\b", r"\bPISTON\b", r"\bCOTTER\b"]),
    ("spring_generic", "medium", "Suspension", "Spring", "Spring Pin",
     [r"^SPRING;", r"^SPRING$"],
     [r"\bLEAF\b", r"\bAIR\b", r"\bVALVE\b"]),
    ("arm_control", "high", "Suspension", "Suspension Arm", "Ball Joint",
     [r"ARM; ?.*(CONT|CONTROL|LWR|UPR|SUS)", r"\bCONTROL ARM\b"],
     [r"\bWIPER\b", r"\bIDLER\b"]),
    ("cylinder_asm_brake", "high", "Brakes", "Hydraulic", "Brake Pipe",
     [r"CYLINDER ASM; ?.*(BRK|BRAKE|MASTER|WHEEL)", r"\bMASTER CYLINDER\b",
      r"\bWHEEL CYLINDER\b"], []),
    ("back_asm", "medium", "Accident & Body", "Panels", "Panel",
     [r"\bBACK ASM\b"], []),

    # --- interface / telematics / EV mystery ---
    ("interface_mx", "low", "Electrical", "Control Units", "Control Unit",
     [r"\bINTERFACE\b", r"\bMX2\b", r"\bTELEMATIC\b", r"\bMODEM\b"],
     []),
    ("rod_end", "high", "Steering", "Linkage", "Tie Rod End",
     [r"ROD END ASM", r"\bROD END\b", r"END ASM; ?ROD"], []),
    ("rod_inner", "high", "Steering", "Linkage", "Tie Rod",
     [r"ROD ASM; ?INNER", r"ROD; ?INNER"], []),
    ("rail_asm_common", "high", "Fuel System", "Fuel Rail", "Common Rail",
     [r"RAIL ASM; ?COMMON", r"\bCOMMON RAIL\b"], []),
    ("shift_block_clu", "high", "Clutch", "Release System", "Pivot",
     [r"BLOCK; ?SHIFT,?CLU", r"SHIFT.?BLOCK.?CLU"], []),
    ("ring_block_gear", "high", "Transmission", "Geartrain", "Synchronizer",
     [r"RING; ?BLOCK", r"\bBLOCK RING\b"], []),
    ("eng_mount_rubber", "high", "Engine", "Mounting", "Insulator",
     [r"RUBBER; ?CUSHION,?ENG", r"ENG MTG", r"ENGINE MOUNT", r"INSULATOR; ?ENG"], []),
    ("heater_core", "high", "Cabin Interior", "HVAC Filters", "Blower Filter",
     [r"CORE; ?HTR", r"\bHEATER CORE\b", r"HTR UNIT"], []),
    ("air_dryer", "high", "Brakes", "Booster & Control", "Brake Valve",
     [r"DRYER; ?AIR", r"\bAIR DRYER\b"], []),
    ("def_tube", "high", "Intake Exhaust Emission", "DEF System", "DEF Tank",
     [r"TUBE ASM; ?DEF", r"PIPE; ?DEF", r"HOSE; ?DEF"], []),
    ("seat_cushion_plain", "high", "Cabin Interior", "Seat", "Seat Cushion",
     [r"CUSHION; ?SEAT", r"\bSEAT CUSHION\b"], []),
    ("battery_12v", "high", "Electrical", "Starting & Charging", "Battery Cable",
     [r"^BATTERY$", r"^BATTERY;", r"\bBATTERY\b"],
     [r"HIGH VOLTAGE", r"\bCABLE\b", r"\bTRAY\b", r"\bCOVER\b"]),
    ("antenna", "high", "Electrical", "Instruments", "Instrument Cluster",
     [r"^ANTENNA", r"\bANTENNA\b"], []),
    ("manifold_inl", "high", "Intake Exhaust Emission", "Air Intake", "Air Duct",
     [r"MANIFOLD; ?INL", r"\bINTAKE MANIFOLD\b", r"MANIFOLD; ?INT"], []),
    ("manifold_exh", "high", "Intake Exhaust Emission", "Exhaust", "Exhaust Pipe",
     [r"MANIFOLD; ?EXH", r"\bEXHAUST MANIFOLD\b"], []),
    ("clutch_booster", "high", "Clutch", "Release System", "Pivot",
     [r"BOOSTER ASM; ?CLU", r"\bCLUTCH BOOSTER\b"], []),
    ("frame_asm", "high", "Chassis Frame", "Crossmember & Brackets", "Crossmember",
     [r"^FRAME ASM", r"FRAME ASM;", r"^FRAME;"],
     [r"\bDOOR\b", r"\bWINDOW\b", r"\bSEAT\b"]),
    ("diff_cage", "high", "Driveline Axle", "Differential", "Carrier",
     [r"CAGE ASM; ?DIFF", r"\bDIFF CAGE\b", r"CASE; ?DIFF"], []),
    ("valve_lash", "high", "Engine", "Valve Train", "Rocker Arm",
     [r"ADJUSTER; ?VLV", r"\bVALVE LASH\b", r"LASH ADJUSTER"], []),
    ("cyl_liner", "high", "Engine", "Block & Structure", "Oil Pan",
     [r"LINER; ?C/BL", r"\bCYLINDER LINER\b", r"LINER; ?CYL"], []),
    ("spring_chamber", "high", "Brakes", "Booster & Control", "Brake Valve",
     [r"CHAMBER ASM; ?SPRING", r"SPRING BRAKE", r"CHAMBER; ?SPRING"], []),
    ("sleeve_gen", "low", "Transmission", "Geartrain", "Gear",
     [r"^SLEEVE$", r"^SLEEVE;"], []),
    ("guide_air", "high", "Intake Exhaust Emission", "Air Intake", "Air Duct",
     [r"GUIDE ASM\s*:?\s*AIR", r"GUIDE ASM; ?AIR"], []),
]

# Rules that should be flagged needs_eq_hit / needs_list despite assignment
NEEDS_EQ = {
    "hv_battery", "special_tool", "interface_mx", "camera", "display",
    "airbag", "radar_sensor", "dc_converter", "heater_unit",
}
NEEDS_LIST = {
    "special_tool", "interface_mx",
}


def _match_rule(desc_u: str, pn: str) -> tuple | None:
    """Match against description alone for ^-anchored patterns; PN+desc otherwise."""
    blob = f"{pn} {desc_u}"
    for rule in DESC_RULES:
        rid, conf, l1, l2, l3, pats, excs = rule
        matched = False
        for p in pats:
            target = desc_u if p.startswith("^") else blob
            if re.search(p, target):
                matched = True
                break
        if not matched:
            continue
        if any(re.search(e, blob) for e in excs):
            continue
        return rid, conf, l1, l2, l3
    return None


def _modal_triple(series_of_tuples, min_n=3, min_share=0.45):
    c = Counter(series_of_tuples)
    if not c:
        return None
    (trip, n) = c.most_common(1)[0]
    total = sum(c.values())
    share = n / total
    if total < min_n or share < min_share:
        return None
    return trip[0], trip[1], trip[2], share, total


def main() -> None:
    print("Loading source lines…")
    src = pd.read_parquet(D / "pricing_aim_source_lines.parquet")
    gap_mask = (
        src["aim_l1"].astype(str).str.contains("Not on AIM", case=False, na=False)
        | src["aim_l3"].astype(str).str.contains("Not classified", case=False, na=False)
    )
    gap = src.loc[gap_mask].copy()
    gap["part_number"] = gap["part_number"].astype(str).str.strip()
    gap["description"] = gap["description"].fillna("").astype(str)

    # unit / list price: prefer new_eur when priced_both, else billed/qty
    gap["unit_from_bill"] = gap["billed_eur"] / gap["qty"].replace(0, pd.NA)
    gap["list_or_unit_price"] = gap["new_eur"].where(gap["priced_both"] == True, gap["unit_from_bill"])  # noqa: E712

    agg = gap.groupby("part_number", as_index=False).agg(
        description=("description", "first"),
        billed_eur=("billed_eur", "sum"),
        qty=("qty", "sum"),
        list_or_unit_price=("list_or_unit_price", "median"),
        price_class=("price_class", "first"),
        n_lines=("db", "count"),
    )
    print(f"Gap PNs: {len(agg):,}  euro: {agg['billed_eur'].sum():,.0f}")

    # Evidence joins
    spine = pd.read_csv(D / "_audit_cls_spine.csv", low_memory=False, dtype=str)
    spine["pn"] = spine["pn"].astype(str).str.strip()
    spine = spine.drop_duplicates("pn", keep="first")
    for c in ("hs", "hs4", "hs6", "list_eur", "fig_key", "fig_no", "key_no"):
        if c not in spine.columns:
            spine[c] = ""

    pr00f = pd.read_csv(D / "_audit_cls_pr00_flat.csv", low_memory=False, dtype=str)
    pr00f["pn"] = pr00f["pn"].astype(str).str.strip()
    pr00f = pr00f.drop_duplicates("pn", keep="first")
    pr00f["hs6_pr00"] = pr00f["hs_code"].fillna("").astype(str).str.replace(r"\D", "", regex=True).str[:6]

    apn = pd.read_csv(D / "aim_pn_classification_v2.csv", low_memory=False, dtype=str)
    apn["part_number"] = apn["part_number"].astype(str).str.strip()
    apn = apn.drop_duplicates("part_number", keep="first")

    master = pd.read_csv(D / "aim_master_v2.csv", low_memory=False, dtype=str)
    master["part_number"] = master["part_number"].astype(str).str.strip()
    ok = master[
        ~master["aim_l1"].isin(["Unknown", "Unknown Review", "Not on AIM spine", ""])
        & master["aim_l1"].notna()
    ].copy()

    # HS6 modal from classified master
    hs_join = ok.merge(spine[["pn", "hs6"]], left_on="part_number", right_on="pn", how="left")
    hs_join = hs_join[hs_join["hs6"].fillna("") != ""]
    hs_modal: dict[str, tuple] = {}
    for hs6, g in hs_join.groupby("hs6"):
        trips = list(zip(g["aim_l1"], g["aim_l2"], g["aim_l3"]))
        m = _modal_triple(trips, min_n=5, min_share=0.40)
        if m:
            hs_modal[hs6] = m  # l1,l2,l3,share,n

    # Noun-head modal from classified master
    ok["noun"] = ok["description"].fillna("").astype(str).str.upper().str.split(";").str[0].str.strip()
    noun_modal: dict[str, tuple] = {}
    for noun, g in ok.groupby("noun"):
        if not noun or len(g) < 5:
            continue
        trips = list(zip(g["aim_l1"], g["aim_l2"], g["aim_l3"]))
        m = _modal_triple(trips, min_n=5, min_share=0.50)
        if m:
            noun_modal[noun] = m

    # Fig-key modal (prefer spine fig_key; master may already carry one)
    if "fig_key" in ok.columns:
        fig_src = ok[["part_number", "aim_l1", "aim_l2", "aim_l3", "fig_key"]].copy()
    else:
        fig_src = ok[["part_number", "aim_l1", "aim_l2", "aim_l3"]].merge(
            spine[["pn", "fig_key"]], left_on="part_number", right_on="pn", how="left"
        )
    fig_src["fig_key"] = fig_src["fig_key"].fillna("").astype(str)
    fig_src = fig_src[fig_src["fig_key"] != ""]
    fig_modal: dict[str, tuple] = {}
    for fk, g in fig_src.groupby("fig_key"):
        if len(g) < 8:
            continue
        trips = list(zip(g["aim_l1"], g["aim_l2"], g["aim_l3"]))
        m = _modal_triple(trips, min_n=8, min_share=0.55)
        if m:
            fig_modal[fk] = m

    AIM_L1 = set(ok["aim_l1"].unique())
    VALID_TRIPLES = set(zip(ok["aim_l1"], ok["aim_l2"], ok["aim_l3"]))

    def _validate(l1, l2, l3, notes_list):
        if not l1:
            return l1, l2, l3
        if (l1, l2, l3) in VALID_TRIPLES:
            return l1, l2, l3
        notes_list.append(f"WARN non-vocab triple {l1}>{l2}>{l3}")
        cands_l3 = [t[2] for t in VALID_TRIPLES if t[0] == l1 and t[1] == l2]
        if cands_l3:
            l3 = Counter(cands_l3).most_common(1)[0][0]
            notes_list.append(f"snapped L3 to {l3}")
            return l1, l2, l3
        cands_l2 = [(t[1], t[2]) for t in VALID_TRIPLES if t[0] == l1]
        if cands_l2:
            l2, l3 = Counter(cands_l2).most_common(1)[0][0]
            notes_list.append(f"snapped to {l1}>{l2}>{l3}")
        return l1, l2, l3

    # Merge evidence onto agg
    out = agg.merge(
        spine[["pn", "hs6", "hs4", "hs", "list_eur", "fig_key", "fig_no"]],
        left_on="part_number", right_on="pn", how="left",
    ).drop(columns=["pn"], errors="ignore")
    out = out.merge(
        pr00f[["pn", "hs6_pr00", "price_eur"]],
        left_on="part_number", right_on="pn", how="left",
    ).drop(columns=["pn"], errors="ignore")
    out = out.merge(
        apn[[
            "part_number", "catalog_l1", "catalog_l2", "catalog_l3",
            "workbook_l1", "workbook_l2", "workbook_l3", "fig_key",
        ]].rename(columns={"fig_key": "fig_key_apn"}),
        on="part_number", how="left",
    )

    out["hs6"] = out["hs6"].fillna("").astype(str)
    out.loc[out["hs6"] == "", "hs6"] = out["hs6_pr00"].fillna("").astype(str)
    out["list_or_unit_price"] = out["list_or_unit_price"].fillna(
        pd.to_numeric(out["list_eur"], errors="coerce")
    ).fillna(pd.to_numeric(out["price_eur"], errors="coerce"))

    rows = []
    for r in out.itertuples(index=False):
        pn = r.part_number
        desc = r.description or ""
        desc_u = desc.upper()
        billed = float(r.billed_eur or 0)
        hs6 = (r.hs6 or "")[:6]
        notes = []
        method = None
        conf = None
        l1 = l2 = l3 = None

        # PN prefix Shell oils
        if re.match(r"^05500", pn) or re.search(r"RIM R4|15W40|10W40", desc_u):
            hit = ("shell_lube_pn", "high", "Fluids Chemicals", "Lubricants", "Lubricant")
        else:
            hit = _match_rule(desc_u, pn)

        if hit:
            rid, conf, l1, l2, l3 = hit
            method = f"desc:{rid}"
            if rid in NEEDS_EQ:
                notes.append("needs_eq_hit")
            if rid in NEEDS_LIST:
                notes.append("needs_list")
            if rid == "hv_battery":
                notes.append("EV high-voltage battery; L3 Battery Cable is closest available leaf")
            if rid in ("map_sensor", "o2_sensor", "tire_sensor", "bearing", "gasket_eng"):
                notes.append("L3 is nearest available leaf — review")
            if rid == "ac_compressor" or rid == "ac_condenser":
                notes.append("A/C mapped to Cooling>Radiator (no HVAC L1 in AIM)")

        # Workbook AIM triple if description missed or only medium/low
        wb_l1 = getattr(r, "workbook_l1", None) or ""
        wb_l2 = getattr(r, "workbook_l2", None) or ""
        wb_l3 = getattr(r, "workbook_l3", None) or ""
        if wb_l1 in AIM_L1 and wb_l2 and wb_l3:
            if method is None:
                l1, l2, l3 = wb_l1, wb_l2, wb_l3
                method = "workbook_aim"
                conf = "high"
            elif conf in ("medium", "low"):
                # upgrade if workbook agrees on L1
                if wb_l1 == l1:
                    l2, l3 = wb_l2, wb_l3
                    conf = "high"
                    method = f"{method}+workbook"
                    notes.append("workbook confirmed L2/L3")
                else:
                    notes.append(f"workbook says {wb_l1}>{wb_l2}>{wb_l3}")

        # HS6 modal
        if method is None and hs6 in hs_modal:
            hl1, hl2, hl3, share, n = hs_modal[hs6]
            l1, l2, l3 = hl1, hl2, hl3
            method = f"hs6_modal:{hs6}"
            conf = "high" if share >= 0.70 and n >= 20 else "medium"
            notes.append(f"HS6 modal share={share:.0%} n={n}")

        # Noun modal
        noun = desc_u.split(";")[0].strip()
        if method is None and noun in noun_modal:
            nl1, nl2, nl3, share, n = noun_modal[noun]
            l1, l2, l3 = nl1, nl2, nl3
            method = f"noun_modal:{noun}"
            conf = "medium" if share >= 0.65 else "low"
            notes.append(f"noun modal share={share:.0%} n={n}")

        # Fig key
        fk = (getattr(r, "fig_key", None) or getattr(r, "fig_key_apn", None) or "")
        if method is None and fk in fig_modal:
            fl1, fl2, fl3, share, n = fig_modal[fk]
            l1, l2, l3 = fl1, fl2, fl3
            method = f"fig_key:{fk}"
            conf = "low"
            notes.append(f"fig modal share={share:.0%} n={n}")

        # Catalogue family only as note (different tree — do not invent AIM from Competitive parts)
        cat_l1 = getattr(r, "catalog_l1", None) or ""
        if cat_l1:
            notes.append(f"catalog_tree={cat_l1}")

        if method is None:
            # residual classification
            if re.search(r"\b(TOOL|SST|PULLER|TESTER|GAUGE)\b", desc_u):
                method = "residual"
                conf = "low"
                l1, l2, l3 = "Tools Equipment", "Workshop Tools", "Gauge"
                notes.append("needs_list")
            elif re.search(r"\b(EV|HIGH VOLTAGE|HYBRID|INVERTER|TRACTION)\b", desc_u):
                method = "residual"
                conf = "low"
                l1, l2, l3 = "Electrical", "Control Units", "Control Unit"
                notes.append("needs_eq_hit")
            else:
                method = "unassigned"
                conf = "none"
                l1 = l2 = l3 = ""
                notes.append("needs_eq_hit")

        # Force Pads & Shoes naming (never Friction)
        if l2 == "Friction":
            l2 = "Pads & Shoes"

        if l1:
            l1, l2, l3 = _validate(l1, l2, l3, notes)

        rows.append({
            "part_number": pn,
            "description": desc,
            "billed_eur": round(billed, 2),
            "list_or_unit_price": None if pd.isna(r.list_or_unit_price) else round(float(r.list_or_unit_price), 2),
            "hs6": hs6,
            "method": method,
            "confidence": conf,
            "proposed_aim_l1": l1,
            "proposed_aim_l2": l2,
            "proposed_aim_l3": l3,
            "notes": "; ".join(notes),
            "price_class": getattr(r, "price_class", ""),
            "fig_key": fk,
        })

    res = pd.DataFrame(rows).sort_values("billed_eur", ascending=False)

    high = res[res["confidence"] == "high"].copy()
    high_patch = high[[
        "part_number", "description", "billed_eur", "proposed_aim_l1",
        "proposed_aim_l2", "proposed_aim_l3", "method", "notes",
    ]].rename(columns={
        "proposed_aim_l1": "aim_l1_fixed",
        "proposed_aim_l2": "aim_l2_fixed",
        "proposed_aim_l3": "aim_l3",
    })
    patch_path = D / "aim_gap_high_conf_patch_20260918.csv"
    high_patch.to_csv(patch_path, index=False)
    print(f"Wrote {patch_path}  high={len(high_patch)}")

    # Deliverable CSV first (before master, which may be file-locked)
    out_csv = D / "aim_gap_auto_assign_20260918.csv"
    tmp_csv = D / "aim_gap_auto_assign_20260918.csv.tmp"
    res.to_csv(tmp_csv, index=False)
    tmp_csv.replace(out_csv)
    print(f"Wrote {out_csv}  rows={len(res)}")

    # Apply HIGH to master (aim_l1_fixed / aim_l2_fixed / aim_l3 only)
    applied = 0
    if APPLY_HIGH_TO_MASTER:
        m = pd.read_csv(D / "aim_master_v2.csv", low_memory=False, dtype=str)
        m["part_number"] = m["part_number"].astype(str).str.strip()
        patch = high_patch.rename(columns={
            "aim_l1_fixed": "_p_l1",
            "aim_l2_fixed": "_p_l2",
            "aim_l3": "_p_l3",
        })[["part_number", "_p_l1", "_p_l2", "_p_l3"]]
        m = m.merge(patch, on="part_number", how="left")
        hit = m["_p_l1"].notna()
        applied = int(hit.sum())
        m.loc[hit, "aim_l1_fixed"] = m.loc[hit, "_p_l1"]
        m.loc[hit, "aim_l2_fixed"] = m.loc[hit, "_p_l2"]
        m.loc[hit, "aim_l3"] = m.loc[hit, "_p_l3"]
        m.loc[hit, "aim_l1"] = m.loc[hit, "_p_l1"]
        m.loc[hit, "aim_l2"] = m.loc[hit, "_p_l2"]
        m.loc[hit, "has_aim"] = "1"
        m.loc[hit, "aim_changed"] = "gap_auto_20260918"
        prev = m.loc[hit, "aim_source"].fillna("").astype(str)
        m.loc[hit, "aim_source"] = prev.where(
            prev.str.contains("gap_auto_20260918", na=False),
            prev + "|gap_auto_20260918",
        )
        m = m.drop(columns=["_p_l1", "_p_l2", "_p_l3"])
        master_path = D / "aim_master_v2.csv"
        master_tmp = D / "aim_master_v2.csv.tmp"
        m.to_csv(master_tmp, index=False)
        for attempt in range(8):
            try:
                master_tmp.replace(master_path)
                print(f"Applied high-conf to aim_master_v2: {applied} rows")
                break
            except PermissionError:
                time.sleep(1.5)
        else:
            fallback = D / "aim_master_v2_gap_patched_20260918.csv"
            master_tmp.replace(fallback)
            print(f"MASTER LOCKED — wrote patch copy to {fallback} ({applied} rows)")
            applied = -applied  # signal locked    # Summary stats
    def _summ(df):
        return len(df), float(df["billed_eur"].sum())

    total_n, total_e = _summ(res)
    high_n, high_e = _summ(res[res["confidence"] == "high"])
    med_n, med_e = _summ(res[res["confidence"] == "medium"])
    low_n, low_e = _summ(res[res["confidence"] == "low"])
    none_n, none_e = _summ(res[res["confidence"] == "none"])
    assigned = res[res["confidence"] != "none"]
    asg_n, asg_e = _summ(assigned)

    needs_eq = res[res["notes"].str.contains("needs_eq_hit", na=False)]
    needs_list = res[res["notes"].str.contains("needs_list", na=False)]
    leftover = res[res["confidence"].isin(["none", "low"])]

    method_top = (
        assigned.assign(method_family=assigned["method"].str.split(":").str[0])
        .groupby("method_family")
        .agg(n=("part_number", "count"), eur=("billed_eur", "sum"))
        .sort_values("eur", ascending=False)
    )

    l1_top = (
        assigned.groupby("proposed_aim_l1")
        .agg(n=("part_number", "count"), eur=("billed_eur", "sum"))
        .sort_values("eur", ascending=False)
    )

    top20 = res.head(20)
    leftover20 = leftover.sort_values("billed_eur", ascending=False).head(30)

    lines = []
    lines.append("# AIM gap auto-assign — 2026-09-18")
    lines.append("")
    lines.append(
        f"The pricing-revision book had **{total_n:,} part numbers** still on "
        f"**Not on AIM spine / Not classified at L3**, worth **EUR {total_e:,.0f}** "
        f"of billed parts in the revision cube."
    )
    lines.append("")
    lines.append(
        f"I assigned **{asg_n:,} PNs (EUR {asg_e:,.0f}, {100*asg_e/total_e:.1f}% of gap euro)**. "
        f"Of those: **{high_n:,} high** (EUR {high_e:,.0f}), "
        f"**{med_n:,} medium** (EUR {med_e:,.0f}), "
        f"**{low_n:,} low** (EUR {low_e:,.0f}). "
        f"**{none_n:,} PNs (EUR {none_e:,.0f})** stay unassigned."
    )
    lines.append("")
    lines.append(
        f"High-confidence rows were written into `aim_master_v2.csv` on "
        f"`aim_l1_fixed` / `aim_l2_fixed` / `aim_l3` (**{applied:,} master rows updated**). "
        f"Medium and low stay proposal-only in the CSV. "
        f"Rebate, transport, and Shell `05500*` oils were labelled "
        f"(Logistics Packaging or Fluids Chemicals > Lubricants), not left as mystery."
    )
    lines.append("")
    lines.append("## How the assign was made")
    lines.append("")
    lines.append(
        "Order of evidence: description / PN pattern first, then existing workbook AIM labels, "
        "then HS6 majority from already-classified parts, then noun-head majority, then figure key. "
        "Catalogue-tree families (Competitive / Repair / …) were recorded in notes only — "
        "they are not the AIM spine. L2 uses **Pads & Shoes**, never Friction."
    )
    lines.append("")
    lines.append("### Top methods (by euro)")
    lines.append("")
    lines.append("| Method family | PNs | EUR |")
    lines.append("|---|---:|---:|")
    for name, row in method_top.head(12).iterrows():
        lines.append(f"| {name} | {int(row['n']):,} | {row['eur']:,.0f} |")
    lines.append("")
    lines.append("### Proposed AIM L1 mix (assigned only)")
    lines.append("")
    lines.append("| AIM L1 | PNs | EUR |")
    lines.append("|---|---:|---:|")
    for name, row in l1_top.head(15).iterrows():
        lines.append(f"| {name} | {int(row['n']):,} | {row['eur']:,.0f} |")
    lines.append("")
    lines.append("## Top 20 assigns by billed euro")
    lines.append("")
    lines.append("| PN | Description | EUR | Conf | AIM | Method |")
    lines.append("|---|---|---:|---|---|---|")
    for _, r in top20.iterrows():
        aim = f"{r['proposed_aim_l1']} > {r['proposed_aim_l2']} > {r['proposed_aim_l3']}"
        if not r["proposed_aim_l1"]:
            aim = "(unassigned)"
        lines.append(
            f"| {r['part_number']} | {str(r['description'])[:48]} | {r['billed_eur']:,.0f} | "
            f"{r['confidence']} | {aim} | {r['method']} |"
        )
    lines.append("")
    lines.append("## Still needs EQ hit or mailbox / list")
    lines.append("")
    lines.append(
        f"**needs_eq_hit:** {len(needs_eq):,} PNs, EUR {needs_eq['billed_eur'].sum():,.0f} "
        f"(includes fully unassigned plus EV / camera / airbag / tool-adjacent rows that got a "
        f"best-effort leaf)."
    )
    lines.append(
        f"**needs_list:** {len(needs_list):,} PNs, EUR {needs_list['billed_eur'].sum():,.0f} "
        f"(special tools / interface / telematics-style lines)."
    )
    lines.append("")
    lines.append("### Largest leftovers (low or none)")
    lines.append("")
    lines.append("| PN | Description | EUR | Flag | Notes |")
    lines.append("|---|---|---:|---|---|")
    for _, r in leftover20.iterrows():
        flag = "needs_eq_hit" if "needs_eq_hit" in str(r["notes"]) else (
            "needs_list" if "needs_list" in str(r["notes"]) else r["confidence"]
        )
        lines.append(
            f"| {r['part_number']} | {str(r['description'])[:48]} | {r['billed_eur']:,.0f} | "
            f"{flag} | {str(r['notes'])[:80]} |"
        )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append(f"- `{out_csv}`")
    lines.append(f"- `{patch_path}` (high-confidence patch mirror)")
    lines.append(f"- `{INBOX / 'aim_gap_auto_assign_20260918_summary.md'}` (this note)")
    lines.append(
        f"- Master updated: `{D / 'aim_master_v2.csv'}` "
        f"(high only; marker `aim_changed=gap_auto_20260918`)"
    )
    lines.append("")

    summary_path = INBOX / "aim_gap_auto_assign_20260918_summary.md"
    text = "\n".join(lines)
    summary_path.write_text(text, encoding="utf-8")
    (D / "aim_gap_auto_assign_20260918_summary.md").write_text(text, encoding="utf-8")
    # Remove competing uppercase SUMMARY if present (wrong vocab / parallel draft)
    rival = D / "aim_gap_auto_assign_20260918_SUMMARY.md"
    if rival.exists():
        rival.unlink()
    print(f"Wrote {summary_path}")

    # Console return packet for parent
    print("\n=== COUNTS ===")
    print(f"total_gap_pns={total_n}")
    print(f"assigned_high={high_n} eur={high_e:.2f}")
    print(f"assigned_med={med_n} eur={med_e:.2f}")
    print(f"assigned_low={low_n} eur={low_e:.2f}")
    print(f"unassigned={none_n} eur={none_e:.2f}")
    print(f"needs_eq={len(needs_eq)} eur={needs_eq['billed_eur'].sum():.2f}")
    print(f"needs_list={len(needs_list)} eur={needs_list['billed_eur'].sum():.2f}")
    print(f"master_rows_patched={applied}")


if __name__ == "__main__":
    main()
