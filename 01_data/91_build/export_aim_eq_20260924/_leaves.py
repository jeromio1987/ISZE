"""Print the live Level-3 leaves for the pairs the classifier needs."""
import pandas as pd

m = pd.read_csv(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv",
                dtype=str, low_memory=False)
m["l1"] = m["aim_l1"].fillna("").str.strip()
m["l2"] = m["aim_l2"].fillna("").str.strip()
m["l3"] = m["aim_l3"].fillna("").str.strip()
live: dict[tuple[str, str], set[str]] = {}
for a, b, c in zip(m["l1"], m["l2"], m["l3"]):
    if a and b and c and not a.lower().startswith("unknown"):
        live.setdefault((a, b), set()).add(c)

want = [
    ("Accident & Body", "Panels"), ("Accident & Body", "Wiper & Washer"),
    ("Accident & Body", "Trim"), ("Accident & Body", "Rear Gate"),
    ("Accident & Body", "Glass"), ("Accident & Body", "Lamps"),
    ("Accident & Body", "Mirrors"), ("Accident & Body", "Bumpers"),
    ("Accident & Body", "Locks & Handles"), ("Accident & Body", "Roof"),
    ("Cabin Interior", "HVAC Filters"), ("Cabin Interior", "Interior Trim"),
    ("Cabin Interior", "Dashboard & Controls"), ("Cabin Interior", "Seat"),
    ("Cooling", "Cooling Hoses & Pipes"), ("Cooling", "Radiator"),
    ("Cooling", "Thermostat & Control"), ("Cooling", "Water Pump"),
    ("Driveline Axle", "Axle Shaft"), ("Driveline Axle", "Final Drive"),
    ("Driveline Axle", "Differential"), ("Brakes", "Disc & Drum"),
    ("Brakes", "Discs & Drums"), ("Brakes", "Hydraulic"), ("Brakes", "Actuation"),
    ("Brakes", "Booster & Control"), ("Brakes", "ABS Control"),
    ("Brakes", "Pads & Shoes"), ("Brakes", "Caliper"), ("Brakes", "Repair Kits"),
    ("Electrical", "Harness & Connectors"), ("Electrical", "Lighting"),
    ("Electrical", "Sensors"), ("Electrical", "Switch Relay Fuse"),
    ("Electrical", "Control Units"), ("Electrical", "Charging"),
    ("Electrical", "Starting & Charging"), ("Electrical", "Instruments"),
    ("Electrical", "Motors & Actuators"), ("Electrical", "Audio"),
    ("Engine", "Block & Structure"), ("Engine", "Cylinder Head"),
    ("Engine", "Internal Rotating"), ("Engine", "Valve Train"),
    ("Engine", "Timing Drive"), ("Engine", "Mounting"), ("Engine", "Gasket & Sealing"),
    ("Fuel System", "Injection"), ("Fuel System", "Fuel Lines & Hoses"),
    ("Fuel System", "Tank & Supply"), ("Fuel System", "Filtration"),
    ("Fuel System", "Fuel Pump"), ("Fuel System", "Fuel Rail"),
    ("Fuel System", "Fuel Control"), ("Fuel System", "Injection Pump"),
    ("Transmission", "Case"), ("Transmission", "Geartrain"),
    ("Transmission", "Shift Mechanism"), ("Transmission", "Repair Kits"),
    ("Transmission", "Bearings & Seals"),
    ("Intake Exhaust Emission", "Air Intake"), ("Intake Exhaust Emission", "Turbo"),
    ("Intake Exhaust Emission", "Exhaust"), ("Intake Exhaust Emission", "EGR"),
    ("Intake Exhaust Emission", "Emission Control"), ("Intake Exhaust Emission", "DEF System"),
    ("Intake Exhaust Emission", "DPF/DPD"), ("Intake Exhaust Emission", "Sensors"),
    ("Suspension", "Leaf Springs"), ("Suspension", "Shock Absorber"),
    ("Suspension", "Suspension Arm"), ("Suspension", "Bush & Mount"),
    ("Suspension", "Bushings"), ("Suspension", "Spring"), ("Suspension", "Stabilizer"),
    ("Suspension", "Air Suspension"),
    ("Steering", "Gear"), ("Steering", "Column"), ("Steering", "Linkage"),
    ("Steering", "Knuckle & King Pin"), ("Steering", "Control & Sensors"),
    ("Chassis Frame", "Crossmember & Brackets"), ("Chassis Frame", "Side Rail & Crossmember"),
    ("Chassis Frame", "Mounting Hardware"), ("Chassis Frame", "Underbody Protection"),
    ("Wheels Hub", "Hub & Bearing"), ("Wheels Hub", "Wheel Rim"), ("Wheels Hub", "Hub Seals"),
    ("Maintenance Service", "Filters"), ("Maintenance Service", "Air Filter"),
    ("Maintenance Service", "Oil Filter"), ("Maintenance Service", "Fuel Filter"),
    ("Maintenance Service", "Belts"), ("Maintenance Service", "Ignition & Tune-Up"),
    ("Clutch", "Clutch Kit"), ("Clutch", "Disc"), ("Clutch", "Pressure Plate"),
    ("Clutch", "Release System"),
    ("Lubrication", "Oil Filter System"), ("Lubrication", "Oil Pump"),
    ("Lubrication", "Sump & Sealing"), ("Lubrication", "Lubrication Lines"),
    ("Lubrication", "Breather & Vent"),
    ("Fluids Chemicals", "Coolant"), ("Fluids Chemicals", "Lubricants"),
    ("Fluids Chemicals", "Grease"), ("Fluids Chemicals", "Cleaning Chemicals"),
    ("Fluids Chemicals", "Transmission Fluid"),
    ("Tools Equipment", "Workshop Tools"), ("Literature Marketing", "Manuals"),
    ("Logistics Packaging", "Packaging"),
]
for pair in want:
    print(f"{pair[0]:26s} | {pair[1]:26s} | {sorted(live.get(pair, []))}")
