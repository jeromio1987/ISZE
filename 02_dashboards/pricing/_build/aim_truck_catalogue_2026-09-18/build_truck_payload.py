#!/usr/bin/env python3
"""Truck catalogue payload builder.

Reads the payload the drill page and the spider already use:

  02_dashboards/pricing/_build/aim_repertoire_map_2026-09-17/payload.json

and adds the two things this page needs:

  1. a physical ZONE for every part type (front, cab, engine bay, chassis,
     rear, electrical), so a click on a vehicle can open real families; and
  2. the official ISZE maximum spend per vehicle per year per model group,
     read from prism/data/gps_model_targets.csv - never typed in by hand.

Read-only over 01_data. Writes truck_payload.json in this folder.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SRC = ISZE / "02_dashboards" / "pricing" / "_build" / "aim_repertoire_map_2026-09-17" / "payload.json"
TARGETS = ISZE / "03_analytics" / "Isuzu" / "prism" / "data" / "gps_model_targets.csv"
FLEET = ISZE / "01_data" / "00_derived" / "gps_spu_by_distributor.csv"
HERE = Path(__file__).resolve().parent
OUT = HERE / "truck_payload.json"

# ---------------------------------------------------------------------------
# Zones. Five are positional - the family really does live there on a truck.
# The sixth is functional: a sensor or a harness runs the length of the
# vehicle, so it is grouped by what it does, not by where it sits.
# ---------------------------------------------------------------------------
ZONES = [
    {"k": "front", "name": "Front and lamps",
     "where": "Nose of the vehicle",
     "how": "Positional",
     "blurb": "Everything at the very front: the bumper and its brackets, the grille, "
              "the head and fog lamps, the lenses and the front marker lamps."},
    {"k": "cab", "name": "Cab, doors and glass",
     "where": "Cab side",
     "how": "Positional",
     "blurb": "The driver's box: doors, side panels, fenders, windscreen and side glass, "
              "mirrors, handles and locks, and the interior trim."},
    {"k": "engine", "name": "Engine bay and intake",
     "where": "Under the cab and hood",
     "how": "Positional",
     "blurb": "The engine itself and everything bolted around it: filtration, cooling, "
              "belts, turbo, injectors, fuel delivery, air intake and the A/C compressor."},
    {"k": "chassis", "name": "Chassis, brakes and driveline",
     "where": "Under the body, along the frame",
     "how": "Positional",
     "blurb": "What carries and stops the truck: brakes, suspension, steering, clutch, "
              "transmission, the rear axle and the exhaust run."},
    {"k": "rear", "name": "Rear, body and hardware",
     "where": "Rear of the body",
     "how": "Positional",
     "blurb": "Behind the cab: the cargo body and its structure, steps and guards, tail "
              "lamps, and the fasteners and consumables that go everywhere."},
    {"k": "elec", "name": "Electrical and electronics",
     "where": "Runs the whole length",
     "how": "Functional, not positional",
     "blurb": "Sensors, harnesses, control units, switches, relays, meters and actuators. "
              "These are grouped by function because a sensor or a loom is not in one place "
              "on a truck. Read as a layer, not as a location."},
]
Z_IX = {z["k"]: i for i, z in enumerate(ZONES)}

# Every part type, assigned by name. Prefix rules are used where the L2 already
# tells the whole story; explicit names settle the rest.
Z_PREFIX = {
    "Brake": "chassis", "ABS": "chassis", "Wheel cylinder": "chassis",
    "Parking brake": "chassis", "Master cylinder": "chassis",
    "Aftertreatment": "chassis", "EGR": "chassis", "Exhaust": "chassis",
    "Silencer": "chassis", "Catalyst": "chassis",
    "Steering": "chassis", "Knuckle": "chassis", "Tie rod": "chassis",
    "Leaf / suspension": "chassis", "Shock": "chassis", "Suspension": "chassis",
    "Stabilizer": "chassis", "Air spring": "chassis", "Hanger /": "chassis",
    "Bushing": "chassis", "Rod / link": "chassis",
    "Clutch": "chassis", "Release bearing": "chassis", "Pressure plate": "chassis",
    "Transmission": "chassis", "Differential": "chassis", "Gear": "chassis",
    "Propeller": "chassis", "Shift linkage": "chassis", "Gearbox": "chassis",
    "Other transmission": "chassis", "Linkage /": "chassis", "Pump": "chassis",
    "Shaft": "chassis", "Case / housing": "chassis", "Bearing": "chassis",
    "Cylinder": "chassis", "Other mechanical": "chassis",
    "Other brake": "chassis", "Other steering": "chassis",
    "Other suspension": "chassis", "Other clutch": "chassis",
    "Other exhaust": "chassis",
    "Other cooling": "engine",
    "Filter": "engine", "Air filter": "engine", "Oil filter": "engine",
    "Fuel filter": "engine", "Other filter": "engine",
    "Pulley": "engine", "Tensioner": "engine", "Timing belt": "engine",
    "Drive belt": "engine",
    "Radiator": "engine", "Cooling": "engine", "Cooler": "engine",
    "Thermostat": "engine", "Coolant hose": "engine", "Reservoir": "engine",
    "Water pump": "engine",
    "Fuel pump": "engine", "Fuel tank": "engine", "Fuel hose": "engine",
    "Fuel sender": "engine", "Other fuel": "engine",
    "Injector": "engine", "Injection pump": "engine", "Common rail": "engine",
    "Turbocharger": "engine", "Turbo hose": "engine", "Turbo gasket": "engine",
    "Engine": "engine", "Valve": "engine", "Piston": "engine", "Liner": "engine",
    "Other engine": "engine",
    "Gasket": "engine", "Oil seal": "engine", "Packing": "engine",
    "O-ring": "engine", "Other gasket": "engine",
    "Alternator": "engine", "Starter motor": "engine",
    "Air dryer": "engine", "Air duct": "engine", "Air hose": "engine",
    "Air compressor": "engine", "Air valve": "engine", "Air tank": "engine",
    "Other air system": "engine",
    "Blower": "engine", "A/C": "engine", "Other A/C": "engine",
    "Heater core": "engine", "Condenser": "engine", "Evaporator": "engine",
    "Voltage regulator": "elec",
    "Sensor": "elec", "Control unit": "elec", "Harness": "elec",
    "Meter": "elec", "Switch": "elec", "Relay": "elec", "Actuator": "elec",
    "Other electrical": "elec",
    "Headlamp": "front", "Fog lamp": "front", "Bulb": "front",
    "Lens": "front", "Marker": "front", "Other lighting": "front",
    "Bumper": "front", "Grille": "front", "Wiper": "front",
    "Panel": "cab", "Door": "cab", "Glass": "cab", "Interior trim": "cab",
    "Fender": "cab", "Handle": "cab", "Trim / molding": "cab",
    "Interior / exterior cover": "cab", "Mirror": "cab",
    "Other body": "rear", "Step / guard": "rear", "Body structure": "rear",
    "Tail / combination": "rear",
    "Bolt": "rear", "Nut": "rear", "Washer": "rear", "Clip": "rear",
    "Pin": "rear", "Spring": "rear", "Spacer": "rear", "Fastener": "rear",
    "Other hardware": "rear", "Rubber / grommet": "rear", "Cap / plug": "rear",
    "Bracket": "rear", "Oil / lubricant": "rear", "Grease": "rear",
}
# Residual buckets are not physical: they get no zone and are named separately.
NO_ZONE = {"Review needed", "Not classified at this level"}


def zone_for(name: str) -> str | None:
    if name in NO_ZONE:
        return None
    if name in Z_PREFIX:
        return Z_PREFIX[name]
    # longest prefix wins, so "Other transmission" is not caught by "Other"
    for p in sorted(Z_PREFIX, key=len, reverse=True):
        if name.startswith(p):
            return Z_PREFIX[p]
    raise SystemExit(f"UNMAPPED part type: {name!r} - add it to Z_PREFIX")


def main() -> int:
    p = json.loads(SRC.read_text(encoding="utf-8"))
    m, rows = p["meta"], p["rows"]
    l1, l2, l3 = m["l1"], m["l2"], m["l3"]

    zone_of = []
    for t in l3:
        zone_of.append(Z_IX[zone_for(t[2])] if zone_for(t[2]) else -1)

    # ---- official targets, read not typed
    targets = []
    for r in csv.DictReader(open(TARGETS, newline="", encoding="utf-8-sig")):
        targets.append({"group": r["model_group"],
                        "label": r["model_label"].split(" \u2014 ")[0],
                        "eur": int(float(r["target_eur_per_vehicle"])),
                        "note": r["notes"]})
    main_targets = [t for t in targets if not t["group"].startswith("Other_")]

    # ---- fleet in service, 2025, markets that carry a count
    fleet_total, fleet_markets = 0.0, 0
    for r in csv.DictReader(open(FLEET, newline="", encoding="utf-8-sig")):
        if r["year"] != "2025":
            continue
        try:
            u = float(r["uio_units"] or 0)
        except ValueError:
            u = 0.0
        if u > 0:
            fleet_total += u
            fleet_markets += 1

    # ---- the four vehicles, with the series each one stands for
    vehicles = [
        {"k": "dmax", "name": "D-Max", "kind": "Pickup / LCV",
         "series": ["D-Max"], "target": "LCV_D_Max"},
        {"k": "nlr", "name": "N-Series light", "kind": "Light truck",
         "series": ["NLR", "NPR"], "target": "N35_Grafter"},
        {"k": "nmr", "name": "N-Series heavy", "kind": "Medium truck",
         "series": ["NMR", "NNR"], "target": "N75_N50_N62"},
        {"k": "frr", "name": "F-Series", "kind": "Heavy truck",
         "series": ["FRR", "FSR"], "target": "F_Series_MD"},
    ]
    tgt = {t["group"]: t for t in targets}
    for v in vehicles:
        t = tgt.get(v["target"])
        v["target_eur"] = t["eur"]
        v["target_label"] = t["label"]
        v["target_note"] = t["note"]

    # ---- per-zone summary so the page and the receipt can both check it
    zone_eur = {z["k"]: 0.0 for z in ZONES}
    zone_pn = {z["k"]: set() for z in ZONES}
    outside = 0.0
    for r in rows:
        z = zone_of[r[3]]
        if z < 0:
            outside += r[6]
            continue
        k = ZONES[z]["k"]
        zone_eur[k] += r[6]
        zone_pn[k].add(r[0])

    total = sum(r[6] for r in rows)
    covered = sum(zone_eur.values())

    out = {
        "meta": {
            "built": datetime.now(timezone.utc).isoformat(),
            "source": "aim_repertoire_map_2026-09-17/payload.json",
            "window": m["window"],
            "window_label": m["window_label"],
            "l1": l1, "l2": l2, "l3": l3,
            "db": m["db"], "db_country": m["db_country"], "db_uio": m["db_uio"],
            "pn": m["pn"], "desc": m["desc"],
            "zones": ZONES,
            "zone_of_l3": zone_of,
            "residual_l1": m["residual_l1"],
            "repertoire": m["repertoire"],
            "checks": m["checks"],
            "targets": main_targets,
            "vehicles": vehicles,
            "fleet_2025": {"units": round(fleet_total), "markets": fleet_markets},
            "zone_summary": {k: {"eur": round(zone_eur[k], 2), "pn": len(zone_pn[k])}
                             for k in zone_eur},
            "outside_zones_eur": round(outside, 2),
            "coverage": {"zones_eur": round(covered, 2), "total_eur": round(total, 2),
                         "pct": round(100 * covered / total, 4)},
        },
        "rows": rows,
    }

    blob = json.dumps(out, separators=(",", ":"), ensure_ascii=False)
    OUT.write_text(blob, encoding="utf-8")

    print("=" * 78)
    print("TRUCK CATALOGUE PAYLOAD")
    print("=" * 78)
    print(f"part types   : {len(l3)}  mapped to a zone: {sum(1 for z in zone_of if z>=0)}")
    print(f"zone coverage: EUR {covered:,.2f} of {total:,.2f} "
          f"({100*covered/total:.2f}%)")
    print(f"outside zones: EUR {outside:,.2f}  (residual buckets, named separately)")
    print()
    for z in ZONES:
        k = z["k"]
        print(f"  {z['name']:<32} {zone_eur[k]:>15,.2f}  {len(zone_pn[k]):>4} pn")
    print()
    print("official targets (max spend per vehicle per year, from the CSV):")
    for t in main_targets:
        note = t["note"].replace("\u2212", "-").replace("\u00d7", "x")
        print(f"  {t['label']:<24} EUR {t['eur']:>5,}   {note}")
    print()
    print(f"fleet in service 2025: {fleet_total:,.0f} vehicles across "
          f"{fleet_markets} markets that carry a count")
    print()
    print(f"checks: {m['checks']}")
    print(f"payload: {len(blob)/1e6:.2f} MB -> {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
