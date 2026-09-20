#!/usr/bin/env python3
"""Audit step 9: does the part text agree with the family it was put in?

High-precision rules only. Each rule is a phrase that names the part's system
beyond reasonable doubt, plus explicit exceptions for the cases where that
phrase legitimately belongs elsewhere (a brake lamp switch is electrical, an
air-cleaner bracket is hardware, and so on). A violation is therefore a
candidate error a parts person would recognise, not a token collision.

Every violation is reported with billed euro, the part family, and the fleet
context is added in the summary tables downstream.
"""
from __future__ import annotations
import collections, csv, re
from pathlib import Path

csv.field_size_limit(10_000_000)
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
OUT = D / "_audit_cls_description_violations.csv"

rows = list(csv.DictReader((D / "_audit_cls_spine.csv").open(encoding="utf-8", newline="")))
for r in rows:
    r["eur"] = float(r["eur"] or 0)
live = [r for r in rows if r["node_present"] == "1" and r["description"]]
tot_eur = sum(r["eur"] for r in rows)

def has(r, *pats):
    d = r["description"]
    return any(re.search(p, d) for p in pats)

# (rule id, what the text proves, match patterns, allowed Level 2 set, exception patterns)
RULES = [
    ("air_filtration", "an engine air filter / air-cleaner element",
     [r"\bFILTER; ?ACL\b", r"\bELEMENT; ?A[CI]L\b", r"ELEMENT; ?AIR CLEANER",
      r"FILTER; ?AIR CLEANER", r"ELEMENT ASM; ?AIR", r"\bAIR CLEANER ELEMENT\b"],
     {"Filters"},
     [r"\bCASE\b", r"\bCOVER\b", r"\bBRACKET\b", r"\bBRKT\b", r"\bBOLT\b", r"\bSEAL\b",
      r"\bGASKET\b", r"\bCLAMP\b", r"\bDUCT\b", r"\bHOSE\b", r"\bBODY\b", r"\bIND\b"]),

    ("oil_filter", "an oil filter / oil filter element",
     [r"\bOIL FILTER\b", r"FILTER; ?OIL", r"ELEMENT; ?OIL"],
     {"Filters"},
     [r"\bBRACKET\b", r"\bBRKT\b", r"\bCASE\b", r"\bCOVER\b", r"\bBOLT\b", r"\bGASKET\b",
      r"\bSEAL\b", r"\bPIPE\b", r"\bHOSE\b", r"\bSWITCH\b", r"\bSENSOR\b", r"\bBODY\b"]),

    ("fuel_filter", "a fuel filter / fuel filter element",
     [r"\bFUEL FILTER\b", r"FILTER; ?FUEL", r"ELEMENT; ?FUEL"],
     {"Filters"},
     [r"\bBRACKET\b", r"\bBRKT\b", r"\bCASE\b", r"\bCOVER\b", r"\bBOLT\b", r"\bGASKET\b",
      r"\bSEAL\b", r"\bPIPE\b", r"\bHOSE\b", r"\bSWITCH\b", r"\bSENSOR\b", r"\bBODY\b",
      r"\bPUMP\b"]),

    ("brake_friction", "brake friction material (pad / shoe / lining / disc / drum)",
     [r"PAD KIT; ?DISC BRK", r"\bSHOE\b.*\bBRK\b", r"LINING.*\bBRK\b",
      r"\bROTOR; ?DISC BRK", r"\bDRUM; ?BRK", r"DISC BRK\b"],
     {"Brake parts"},
     [r"\bSWITCH\b", r"\bSENSOR\b", r"\bLAMP\b", r"\bBOLT\b", r"\bNUT\b", r"\bCLIP\b",
      r"\bSHIM\b", r"\bSPRING\b", r"\bPIN\b"]),

    ("clutch_core", "a clutch disc / cover / pressure plate / release bearing",
     [r"\bDISC; ?CLU", r"\bCOVER ASM; ?CLU", r"PRESSURE PLATE", r"\bCLUTCH DISC\b",
      r"BEARING; ?RELEASE", r"RELEASE BEARING"],
     {"Clutch parts"},
     [r"\bBOLT\b", r"\bNUT\b", r"\bCOOLING FAN\b", r"\bFAN\b"]),

    ("turbo", "a turbocharger",
     [r"\bTURBOCHARGER\b", r"TURBO CHARGER"],
     {"Turbo"},
     [r"\bGASKET\b", r"\bBOLT\b", r"\bPIPE\b", r"\bHOSE\b", r"\bBRACKET\b", r"\bBRKT\b"]),

    ("injector", "a fuel injector / injection nozzle / injection pump",
     [r"NOZZLE ASM; ?INJ", r"INJECTOR ASM(?!.*DEF)", r"PUMP ASM; ?INJ", r"\bINJECTION PUMP\b"],
     {"Injectors"},
     [r"\bPIPE\b", r"\bGASKET\b", r"\bSEAL\b", r"\bBOLT\b", r"\bHOLDER\b", r"\bDEF\b"]),

    ("radiator_water_pump", "a radiator / water pump / thermostat",
     [r"^RADIATOR", r"\bRADIATOR ASM\b", r"PUMP ASM; ?WATER", r"PUMP; ?WATER",
      r"^THERMOSTAT"],
     {"Cooling"},
     [r"\bHOSE\b", r"\bPIPE\b", r"\bBRACKET\b", r"\bBRKT\b", r"\bBOLT\b", r"\bGASKET\b",
      r"\bCAP\b", r"\bGRILLE\b", r"\bSUPPORT\b", r"\bMOUNT\b"]),

    ("shock_leaf", "a shock absorber / leaf spring",
     [r"ABSORBER ASM", r"SHOCK ABSORBER", r"SPRING ASM; ?(LEAF|FRT|RR)", r"\bLEAF SPR\b"],
     {"Suspension"},
     [r"\bBUSHING\b", r"\bBOLT\b", r"\bNUT\b", r"\bBRACKET\b", r"\bBRKT\b", r"\bPIN\b",
      r"\bSHACKLE\b", r"\bCLIP\b", r"\bSEAT\b"]),

    ("bumper", "a bumper",
     [r"\bBUMPER\b"],
     {"Body parts"},
     [r"\bSENSOR\b", r"\bLAMP\b", r"\bHARNESS\b", r"\bBOLT\b", r"\bNUT\b", r"\bRUBBER\b",
      r"\bSTOPPER\b", r"\bCLIP\b"]),

    ("mirror", "a mirror",
     [r"\bMIRROR\b"],
     {"Mirrors"},
     [r"\bSWITCH\b", r"\bHARNESS\b", r"\bMOTOR\b", r"\bBOLT\b", r"\bDOOR ASM\b"]),

    ("lamp", "a lamp / headlamp / lighting unit",
     [r"\bHEADLAMP\b", r"\bLAMP ASM\b", r"COMB LAMP", r"\bFOG LAMP\b"],
     {"Lighting"},
     [r"\bSWITCH\b", r"\bHARNESS\b", r"\bRELAY\b", r"\bBRACKET\b", r"\bBRKT\b",
      r"\bBOLT\b", r"\bCOVER\b", r"\bSUPPORT\b", r"\bPANEL\b", r"\bBEZEL\b"]),

    ("starter_alt", "a starter motor / alternator",
     [r"STARTER ASM", r"\bALTERNATOR\b", r"GENERATOR ASM"],
     {"Starter / alternator"},
     [r"\bSWITCH\b", r"\bRELAY\b", r"\bBOLT\b", r"\bBRACKET\b", r"\bBRKT\b", r"\bPULLEY\b",
      r"\bBELT\b", r"\bHARNESS\b"]),

    ("steering_core", "a steering box / drag link / tie rod / knuckle arm",
     [r"STEERING (UNIT|GEAR|BOX)", r"\bLINK; ?DRAG\b", r"\bDRAG LINK\b",
      r"\bTIE ROD\b", r"ROD ASM; ?TIE"],
     {"Steering"},
     [r"\bBOOT\b", r"\bBOLT\b", r"\bNUT\b", r"\bGASKET\b", r"\bSEAL\b", r"\bHOSE\b",
      r"\bBRACKET\b", r"\bBRKT\b", r"\bCLAMP\b"]),

    ("driveline", "a propeller shaft / differential carrier",
     [r"PROPELLER SHAFT", r"SHAFT ASM; ?PROP", r"\bDIFF(ERENTIAL)? (ASM|CARRIER|CASE)\b",
      r"CARRIER ASM; ?DIFF"],
     {"Transmission parts"},
     [r"\bBOLT\b", r"\bNUT\b", r"\bGASKET\b", r"\bSEAL\b", r"\bBEARING\b", r"\bBRACKET\b"]),

    ("ac_core", "an A/C compressor / condenser / evaporator",
     [r"COMPRESSOR ASM; ?A/?C", r"\bCONDENSER\b", r"\bEVAPORATOR\b",
      r"CMPR ASM; ?A/?C"],
     {"Air conditioning"},
     [r"\bBELT\b", r"\bBOLT\b", r"\bBRACKET\b", r"\bBRKT\b", r"\bHOSE\b", r"\bPIPE\b",
      r"\bSWITCH\b", r"\bRELAY\b", r"\bFAN\b"]),

    ("harness", "a wiring harness",
     [r"^HARNESS", r"\bWIRING HARNESS\b"],
     {"Electrical sensors"},
     [r"\bBOLT\b", r"\bCLIP\b", r"\bGROMMET\b", r"\bBRACKET\b", r"\bBRKT\b",
      r"\bSPEED SENSOR\b", r"\bPROTECTOR\b", r"\bCOVER\b"]),

    ("silencer", "a silencer / muffler / exhaust pipe",
     [r"\bSILENCER\b", r"\bMUFFLER\b", r"PIPE; ?EXH", r"\bEXHAUST PIPE\b"],
     {"Exhaust"},
     [r"\bGASKET\b", r"\bBOLT\b", r"\bNUT\b", r"\bCLAMP\b", r"\bBRACKET\b", r"\bBRKT\b",
      r"\bHANGER\b", r"\bRUBBER\b", r"\bSENSOR\b"]),

    ("gasket", "a gasket / oil seal",
     [r"^GASKET\b", r"^GASKET SET\b", r"^SEAL; ?OIL\b", r"^OIL SEAL\b"],
     {"Gaskets / seals"},
     [r"\bKIT\b.*\bOVERHAUL\b.*\bENG\b"]),

    ("window_regulator", "a door window regulator (a body part, not a voltage regulator)",
     [r"REGULATOR ASM; ?DOOR", r"REGULATOR; ?DOOR", r"REGULATOR ASM; ?WINDOW",
      r"WINDOW REGULATOR"],
     {"Body parts"},
     []),

    ("king_pin", "a king pin (steering / axle geometry, not loose hardware)",
     [r"\bKING PIN\b"],
     {"Steering", "Transmission parts", "Suspension"},
     []),

    ("ball_joint_arm", "a control-arm ball joint (suspension geometry)",
     [r"JOINT ASM; ?BALL.*CONT ARM", r"BALL JOINT.*CONT ARM", r"ARM ASM; ?(LWR|UPR) CONT"],
     {"Suspension", "Steering"},
     []),
]

viol_rows = []
print("DESCRIPTION-vs-FAMILY TEST  (high-precision rules)")
print(f"scope: {len(live):,} classified part numbers that carry a description")
print(f"{'rule':<20} {'matched':>8} {'wrong':>7} {'wrong %':>8} {'billed EUR wrong':>18}")
summary = []
for rid, claim, pats, allowed, excs in RULES:
    matched = [r for r in live if has(r, *pats) and not (excs and has(r, *excs))]
    wrong = [r for r in matched if r["l2"] not in allowed]
    ew = sum(r["eur"] for r in wrong)
    em = sum(r["eur"] for r in matched)
    summary.append((rid, claim, len(matched), len(wrong), em, ew, allowed))
    print(f"{rid:<20} {len(matched):>8,} {len(wrong):>7,} "
          f"{(100*len(wrong)/len(matched) if matched else 0):>7.1f}% {ew:>18,.0f}")
    for r in wrong:
        viol_rows.append({
            "rule": rid, "text_proves": claim, "part_number": r["pn"],
            "description": r["description"], "assigned_l1": r["l1"],
            "assigned_l2": r["l2"], "assigned_l3": r["l3"],
            "should_be_l2_one_of": " | ".join(sorted(allowed)),
            "hs_code": r["hs"], "fig_no": r["fig_no"],
            "list_price_eur": r["list_eur"], "l12m_eur": f"{r['eur']:.2f}",
            "l12m_qty": r["qty"],
        })

tot_wrong_pn = len({v["part_number"] for v in viol_rows})
tot_wrong_eur = sum(float(v["l12m_eur"]) for v in viol_rows)
print(f"\nTOTAL   {tot_wrong_pn:,} distinct part numbers misfiled by these rules, "
      f"EUR {tot_wrong_eur:,.0f} billed ({100*tot_wrong_eur/tot_eur:.2f}% of the 18-month book)")

with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(viol_rows[0].keys()))
    w.writeheader()
    w.writerows(sorted(viol_rows, key=lambda v: -float(v["l12m_eur"])))
print(f"-> {OUT}")

print("\n" + "=" * 78)
print("the 45 costliest single misfiles")
for v in sorted(viol_rows, key=lambda v: -float(v["l12m_eur"]))[:45]:
    print(f"  EUR {float(v['l12m_eur']):>10,.0f}  {v['part_number']}  "
          f"{v['description'][:38]:<38}")
    print(f"      sits in {v['assigned_l1']} > {v['assigned_l2']} > {v['assigned_l3']}"
          f"   | text proves {v['text_proves']}")

print("\n" + "=" * 78)
print("where the misfiled parts are actually sitting")
c = collections.Counter()
ce = collections.Counter()
for v in viol_rows:
    k = f"{v['assigned_l1']} > {v['assigned_l2']} > {v['assigned_l3']}"
    c[k] += 1
    ce[k] += float(v["l12m_eur"])
for k, e in ce.most_common(25):
    print(f"  EUR {e:>10,.0f}  {c[k]:>4} PNs   {k}")
