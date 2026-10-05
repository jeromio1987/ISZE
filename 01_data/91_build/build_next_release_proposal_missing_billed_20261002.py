#!/usr/bin/env python3
"""Proposal (not a release): classification for part numbers billed in the last 12 months
that are not in the classification release at all. Jerome's go of 2 Oct 2026.

READ-ONLY on every release file, RELEASES.json, pr00 and the gate. Writes only:
  01_data/00_derived/_releases/next_release_proposal_missing_billed_2026-10-02.csv

Window: billing_date 2025-09-01..2026-08-31 (same as APPROVAL_SUMMARY_2026-10-02-candidate).
Part numbers are compared after left-padding all-digit part numbers to 10 digits (sales_fact
drops leading zeros: 583306120 = 0583306120 in the release).
Compared against release 2026-10-02-candidate (pending). Against approved 2026-10-02 the same
method gives 63 parts / EUR 108,165, which reconciles to the approval summary: the candidate
added 7475447681, 7551939337 and 7552895450.

Evidence per part: sales_fact description, figure key from _audit_cls_pr00_flat.csv
(fig_no-key_no), siblings in the candidate release on the same figure key and with the same
description, supersession (newest_pn), jp_codes_cache_20260920.csv, epc_catalogue_heavy,
the AIM master (AIM_Master_PN_Categories_Figkey_release_2026-10-02-candidate.csv).
parts_catalog_dimension has none of the 56 parts.

Every proposed triple is asserted to exist already in the candidate release (no new labels).
"""
from pathlib import Path
import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ISZE / "01_data" / "00_derived"
REL = DER / "_releases"
OUT = REL / "next_release_proposal_missing_billed_2026-10-02.csv"
EXCLUDED = {  # non-part billing lines, reported in the review
    "SERVICE FEE OUTSIDE EUROPE": "service fee",
    "SERVICE FEE WITHIN EUROPE": "service fee",
    "COST DEMURRAGE": "transport / freight cost",
    "COMPENSATIONS SALE E-CREDIT": "credit / compensation line",
}

# pn: (cat triple, aim triple, conf_cat, conf_aim, evidence, open question)
C = {
 'body_other': ('Accident parts', 'Body parts', 'Other body'),
 'bumper': ('Accident parts', 'Body parts', 'Bumper'),
 'panel': ('Accident parts', 'Body parts', 'Panel'),
 'grille': ('Accident parts', 'Body parts', 'Grille'),
 'lock': ('Accident parts', 'Body parts', 'Handle / lock'),
 'interior': ('Accident parts', 'Body parts', 'Interior trim'),
 'pad': ('Competitive parts', 'Brake parts', 'Brake pad'),
 'meter': ('Repair parts', 'Electrical sensors', 'Meter / gauge'),
 'alt': ('Repair parts', 'Starter / alternator', 'Alternator / generator'),
 'vreg': ('Repair parts', 'Starter / alternator', 'Voltage regulator'),
 'inj': ('High value repair', 'Injectors', 'Injector'),
 'head': ('Repair parts', 'Engine parts', 'Cylinder head'),
 'pump': ('Repair parts', 'Hydraulic / mechanical', 'Pump'),
 'sealant': ('Hardware & consumables', 'Consumables', 'Sealant / adhesive'),
 'oth_engine': ('Repair parts', 'Engine parts', 'Other engine'),
 'ecu': ('Repair parts', 'Electrical sensors', 'Control unit'),
 'harness': ('Repair parts', 'Electrical sensors', 'Harness / cable'),
 'relay': ('Repair parts', 'Electrical sensors', 'Relay / solenoid / fuse'),
 'aftert': ('Competitive parts', 'Exhaust', 'Aftertreatment'),
 'valve_eng': ('Repair parts', 'Engine parts', 'Valve / valvetrain'),
 'gasketset': ('Repair parts', 'Gaskets / seals', 'Gasket set'),
 'bolt': ('Hardware & consumables', 'Hardware', 'Bolt'),
 'strg_gear': ('Competitive parts', 'Steering', 'Steering gear / unit'),
 'strg_oth': ('Competitive parts', 'Steering', 'Other steering'),
 'switch': ('Repair parts', 'Electrical sensors', 'Switch'),
 'fueltank': ('Competitive parts', 'Fuel system', 'Fuel tank / cap'),
 'bracket': ('Hardware & consumables', 'Hardware', 'Bracket / stay'),
 'sensor': ('Repair parts', 'Electrical sensors', 'Sensor'),
 'airhose': ('Competitive parts', 'Air system', 'Air hose / pipe'),
 'washer': ('Hardware & consumables', 'Hardware', 'Washer'),
 'oth_elec': ('Repair parts', 'Electrical sensors', 'Other electrical'),
 'spacer': ('Hardware & consumables', 'Hardware', 'Spacer / retainer'),
 'oth_trans': ('High value repair', 'Transmission parts', 'Other transmission'),
}
A = {
 'cab': ('Accident & Body', 'Complete Assembly', 'Cab Assembly'),
 'bumper': ('Accident & Body', 'Panels', 'Bumper'),
 'panel': ('Accident & Body', 'Panels', 'Panel'),
 'grille': ('Accident & Body', 'Panels', 'Grille'),
 'door': ('Accident & Body', 'Panels', 'Door'),
 'seatback': ('Cabin Interior', 'Seat', 'Seat Back'),
 'padkit': ('Brakes', 'Pads & Shoes', 'Brake Pad Kit'),
 'cluster': ('Electrical', 'Instruments', 'Instrument Cluster'),
 'alt': ('Electrical', 'Charging', 'Alternator/Generator'),
 'reg': ('Electrical', 'Charging', 'Regulator'),
 'batt': ('Electrical', 'Charging', 'Battery Accessory'),
 'inj': ('Fuel System', 'Fuel Control', 'Injector'),
 'headcover': ('Engine', 'Cylinder Head', 'Head Cover'),
 'fuelpump': ('Fuel System', 'Injection Pump', 'Fuel Pump'),
 'defpump': ('Intake Exhaust Emission', 'DEF System', 'DEF Pump'),
 'oilseal': ('Engine', 'Gasket & Sealing', 'Oil Seal'),
 'ecu': ('Electrical', 'Control Units', 'Control Unit'),
 'conn': ('Electrical', 'Harness & Connectors', 'Connector'),
 'fuse': ('Electrical', 'Switch Relay Fuse', 'Fuse'),
 'strgvalve': ('Steering', 'Control & Sensors', 'Valve'),
 'gasket_tr': ('Transmission', 'Bearings & Seals', 'Gasket'),
 'bolt': ('Chassis Frame', 'Mounting Hardware', 'Bolt'),
 'plate': ('Chassis Frame', 'Mounting Hardware', 'Plate'),
 'strggear': ('Steering', 'Gear', 'Steering Gear'),
 'damper': ('Suspension', 'Shock Absorber', 'Damper'),
 'switch': ('Electrical', 'Switch Relay Fuse', 'Switch'),
 'fueltank': ('Fuel System', 'Tank & Supply', 'Fuel Tank'),
 'cable': ('Cabin Interior', 'Pedals & Controls', 'Cable'),
 'isensor': ('Electrical', 'Instruments', 'Sensor'),
 'egr': ('Intake Exhaust Emission', 'EGR', 'EGR Component'),
 'gear': ('Transmission', 'Geartrain', 'Gear'),
 'engint': ('Engine', 'Internal Rotating', 'Engine Internal'),
 'casecover': ('Transmission', 'Case', 'Case Cover'),
}
H, M, L = 'high', 'medium', 'low'
P = {
 '7553266960': ('body_other', 'cab', H, H, "fig key 604-002: 57/57 parts in release on Body parts > Other body; same description 3/3 and noun CAB ASM 13/13 on AIM Cab Assembly", ""),
 '5876102381': ('pad', 'padkit', H, H, "fig key 302-017: 113/115 on Brake pad; AIM Brake Pad Kit on all 33 labelled siblings and 39 PAD KIT parts", ""),
 '7552319201': ('meter', 'cluster', H, M, "fig key 890-299: 73/73 on Meter / gauge; same description 15 labelled parts on AIM Instrument Cluster", "AIM master puts this part on Electrical > Audio > Radio; release convention for DISPLAY; MULTI is Instrument Cluster (15 parts)"),
 '7552319211': ('meter', 'cluster', H, M, "fig key 890-299: 73/73 on Meter / gauge; same description 15 labelled parts on AIM Instrument Cluster", "AIM master puts this part on Electrical > Audio > Radio; release convention for DISPLAY; MULTI is Instrument Cluster (15 parts)"),
 '1812004173': ('alt', 'alt', H, H, "fig key 060-002: 397/397 on Alternator / generator; EPC (FRR) path 0-60 engine electrical; 35/35 GENERATOR ASM on AIM Alternator/Generator", ""),
 '7552961740': ('grille', 'grille', H, H, "fig key 701-004: 57/59 on Grille; same description 10/10 on Grille and AIM Panels > Grille", "Alternative AIM label Accident & Body > Trim > Emblem exists (45 parts on figure 701); same-description convention is Grille"),
 '7552973320': ('inj', 'inj', H, M, "fig key 146-020: 5/6 on Injector; same description 3/3 (EUR 267k billed) on Injector and AIM Fuel Control > Injector", "Class question, not this part: DEF dosing injectors sit under fuel injectors on both axes; AIM DEF System labels exist. AIM master puts this part on DEF System > DEF Tank"),
 '7552005220': ('head', 'headcover', H, M, "fig key 011-001: 400/405 on Cylinder head; same description 12 labelled on AIM Cylinder Head > Head Cover (only leaf under Cylinder Head)", ""),
 '7552710010': ('pump', 'fuelpump', H, M, "fig key 146-190: both siblings (PUMP KIT, EUR 20.6k) on Pump and AIM Injection Pump > Fuel Pump", "Figure 146 is the DEF / aftertreatment figure; AIM master puts this part on DEF System > DEF Pump. Followed the 2 siblings"),
 '7552647041': ('sealant', 'oilseal', L, L, "fig key 061-298: no sibling in release; only 2 other SEALER parts (figure 620-633) on Oil seal / seal and AIM Oil Seal; HS 8708299099 (body parts); price list EUR 354", "What is this SEALER (EUR 354 each)? Catalogue label Sealant / adhesive is a guess from the word; 2 other SEALER parts use Oil seal / seal"),
 '7552325061': ('oth_engine', 'cluster', M, M, "fig key 826-580: 7/7 on Other engine; same description 4/4 on AIM Instrument Cluster", "Class question: rear cameras on Other engine looks wrong (Other electrical exists); AIM master says Control Units > Control Unit"),
 '7552647031': ('sealant', 'oilseal', L, L, "fig key 061-298: no sibling in release; only 2 other SEALER parts (figure 620-633) on Oil seal / seal and AIM Oil Seal; HS 8708299099 (body parts); price list EUR 253", "Same as 7552647041"),
 '8976547872': ('alt', 'alt', H, H, "superseded by 8976547870, which is in the release on Alternator / generator and AIM Alternator/Generator; fig key 060-002 397/397", ""),
 '7552481570': ('ecu', 'ecu', H, H, "fig key 826-776: 63/63 on Control unit; same description 29/29 on AIM Control Unit", ""),
 '7551993781': ('harness', 'conn', H, H, "fig key 810-009: 228/228 on Harness / cable; same description: all 11 labelled on AIM Harness & Connectors > Connector (12 Unknown)", ""),
 '8972718920': ('relay', 'fuse', L, L, "fig key 810-042 (harness figure): only 2 siblings, no description, on Handle / lock; HS 8708299099; nothing else on file", "Reading BLOCK; JUNCTION as an electrical junction / fuse block is an interpretation, not confirmed in the EPC"),
 '8975437940': ('vreg', 'reg', H, H, "fig key 066-075: 10/10 on Voltage regulator; AIM Electrical > Charging > Regulator used for the 2 other generator voltage regulators", ""),
 '7552319721': ('aftert', 'conn', H, H, "fig key 810-729: 26/26 on Aftertreatment; same description: all 10 labelled on AIM Connector", ""),
 '8977946020': ('valve_eng', 'strgvalve', H, M, "fig key 057-752: 10/10 on Valve / valvetrain; same description 7/7 (EUR 44k billed) on AIM Steering > Control & Sensors > Valve", "Class question: EVRV is an engine vacuum valve on the EGR figure, the 7 siblings carry a Steering AIM label; Intake Exhaust Emission > EGR > EGR Component exists. Followed siblings"),
 '8975830430': ('bumper', 'bumper', H, H, "fig key 601-002: 123/123 on Bumper; same description 20/20 on AIM Panels > Bumper", ""),
 '5878191810': ('gasketset', 'gasket_tr', H, M, "fig key 005-002: 1,730/1,743 on Gasket set; same description 91/91 on AIM Transmission > Bearings & Seals > Gasket", "Class question: engine gasket sets carry a Transmission AIM label (226 GASKET SET parts); Engine > Gasket & Sealing > Gasket exists. Followed siblings"),
 '5878168422': ('gasketset', 'gasket_tr', H, M, "supersedes 5878168421 (in release: Gasket set, AIM Transmission Gasket); fig key 005-001 4,861/5,224 on Gasket set; same description 112/112 on AIM Transmission Gasket", "Same class question as 5878191810"),
 '8974923851': ('harness', 'conn', H, H, "fig key 810-038: 356/356 on Harness / cable; same description: all 24 labelled on AIM Connector; newest_pn 8974923852 is not in the release either", "8974923852 (newest number) is also missing from the release; add it with the same values"),
 '1812220920': ('alt', 'alt', M, M, "EPC (FRR) path 0-66 GENERATOR; jp class XC; fig key 066-023 has 5 siblings without description on Oil / lubricant (looks like an error)", "Not following the 5 fig-key siblings (Oil / lubricant, no description); they may need the same fix"),
 '8976765330': ('lock', 'door', H, H, "fig key 730-001: 434/434 on Handle / lock; same description: all 27 labelled on AIM Panels > Door (20 Unknown)", ""),
 '7475007370': ('interior', 'seatback', H, H, "fig key 750-001: 385/385 on Interior trim; same description 31 on AIM Seat > Seat Back (7 Seat Cushion, 33 Unknown)", "AIM master puts this part on Seat Cushion; BACK ASM = seat back"),
 '7552750070': ('bolt', 'bolt', H, H, "BOLT noun: 428 on Hardware > Bolt, 578 on AIM Mounting Hardware > Bolt; fig key 061-174 has no sibling", ""),
 '7552061582': ('strg_gear', 'strggear', H, M, "fig key 435-046: 115/115 on Steering gear / unit; same description: all 7 labelled on AIM Steering > Gear > Steering Gear (19 Unknown)", ""),
 '8977945650': ('strg_oth', 'damper', M, M, "no fig-key sibling (431-094); DAMPER; STEERING parts (433-125, 9 parts) are on Steering > Other steering and AIM Suspension > Shock Absorber > Damper", "Steering dampers carry a Suspension AIM label in the release; followed that convention"),
 '7552927230': ('switch', 'switch', H, H, "fig key 825-077: 14/14 on Switch; same description 5/5 on AIM Switch", ""),
 '8978343810': ('fueltank', 'fueltank', H, H, "fig key 140-003: 71/71 on Fuel tank / cap; same description 24/24 on AIM Tank & Supply > Fuel Tank", ""),
 '8983456700': ('harness', 'cable', H, H, "fig key 285-024: 68/68 on Harness / cable; same description 2/2 on AIM Pedals & Controls > Cable", ""),
 '7552056260': ('bracket', 'plate', L, M, "fig key 815-597: no sibling; figure 815 is a harness figure; same description PLATE 2/2 on AIM Mounting Hardware > Plate but catalogue Review needed", "Catalogue Bracket / stay is a guess; the 2 other PLATE parts are still Review needed"),
 '7475056720': ('bumper', 'bumper', H, H, "fig key 601-003: 59/59 on Bumper; same description 9/9 on AIM Panels > Bumper", ""),
 '8942720796': ('panel', 'panel', H, H, "fig key 605-016 (AIM master); same description 30/31 on Panel and 31/31 on AIM Panels > Panel; no pr00 row on file", "No price-list row found for this part"),
 '8983938064': ('bumper', 'bumper', H, H, "fig key 690-001: 177/177 on Bumper; same description 37/37 on AIM Panels > Bumper", ""),
 '8983938054': ('bumper', 'bumper', H, H, "fig key 690-001: 177/177 on Bumper; same description 37/37 on AIM Panels > Bumper", ""),
 '7475392910': ('sensor', 'isensor', H, H, "fig key 826-748: 26/26 on Sensor; same description 15/18 labelled on AIM Instruments > Sensor", ""),
 '7552923220': ('bumper', 'bumper', H, H, "fig key 601-046: 23/23 on Bumper; same description 4/4 on AIM Panels > Bumper", ""),
 '7552710020': ('aftert', 'defpump', M, L, "fig key 146-191: 1 sibling (no description) on Aftertreatment, AIM blank; part sits next to PUMP KIT 146-190 on the DEF figure", "AIM DEF Pump is a guess; the 146-190 pump kits carry Injection Pump > Fuel Pump"),
 '8978342570': ('fueltank', 'fueltank', H, H, "fig key 140-003: 71/71 on Fuel tank / cap; same description 24/24 on AIM Tank & Supply > Fuel Tank", ""),
 '7552061521': ('strg_gear', 'strggear', H, M, "fig key 435-048: 101/104 on Steering gear / unit; same description: 7 on AIM Steering Gear, 29 on Unknown Review > To Review", ""),
 '8982108731': ('body_other', 'cluster', H, M, "fig key 890-080: 96/96 on Other body; same description 14 on AIM Instrument Cluster, 1 Audio > Radio, 12 Unknown", "Class question: antennas on Instrument Cluster vs Audio > Radio"),
 '7552614230': ('sensor', 'egr', H, L, "fig key 057-808: 4/4 on Sensor; AIM: the only same-description part is Unknown; figure 057 is the EGR figure (143 parts on AIM EGR Component)", "AIM EGR Component is taken from the figure, not from siblings"),
 '7552614250': ('airhose', 'egr', H, L, "fig key 057-047: 2/2 on Air hose / pipe, AIM blank; figure 057 is the EGR figure", "AIM EGR Component is taken from the figure, not from siblings"),
 '8973269420': ('washer', 'gear', M, L, "fig key 265-355: no sibling; WASHER noun 140 on Hardware > Washer; figure 265 (transmission) AIM mostly Geartrain > Gear", "AIM Geartrain > Gear is taken from the figure"),
 '7552125540': ('oth_elec', 'batt', L, L, "fig key 061-269: no sibling; figure 061 holds harness / relay / battery-cover parts (7552750070 BOLT; COVER,BATTERY on 061-174); EUR 2.79 list", "Reading this VALVE as a battery accessory is an interpretation"),
 '7552614241': ('harness', 'conn', H, M, "fig key 057-358: 3/3 on Harness / cable; same description 14/14 on AIM Connector", "HS code 7307991090 is a steel pipe fitting, not an electrical connector; may be a pipe connector on the EGR figure"),
 '8980528100': ('oth_engine', 'engint', L, L, "fig key 012-090: the 1 sibling (PIPE; OIL,JET 8982473200) is on Consumables > Oil / lubricant and AIM Unknown; figure 012 is the cylinder block / liner figure", "Not following the sibling: an oil jet is an engine part, not a lubricant; filing it under Oil / lubricant would count it with lubricants. Sibling 8982473200 needs the same fix"),
 '1331560190': ('spacer', 'gear', H, L, "fig key 265-042: 6/6 on Spacer / retainer (AIM blank on all 6); figure 265 (transmission) AIM mostly Geartrain > Gear", "AIM Geartrain > Gear is taken from the figure"),
 '1331560200': ('spacer', 'gear', H, L, "fig key 265-042: 6/6 on Spacer / retainer (AIM blank on all 6); figure 265 AIM mostly Geartrain > Gear", "AIM taken from the figure"),
 '1331560210': ('spacer', 'gear', H, L, "fig key 265-042: 6/6 on Spacer / retainer (AIM blank on all 6); figure 265 AIM mostly Geartrain > Gear", "AIM taken from the figure"),
 '1331560220': ('spacer', 'gear', M, L, "fig key 294-023: no sibling (figure 294 has 1 part, Other clutch); 5 same-series shims 1331560180-230 sit on 265-042 Spacer / retainer", "AIM taken from figure 265"),
 '1331560180': ('spacer', 'gear', H, L, "fig key 265-042: 6/6 on Spacer / retainer (AIM blank on all 6); figure 265 AIM mostly Geartrain > Gear", "AIM taken from the figure"),
 '1331560230': ('spacer', 'gear', H, L, "fig key 265-042: 6/6 on Spacer / retainer (AIM blank on all 6); figure 265 AIM mostly Geartrain > Gear", "AIM taken from the figure"),
 '8980376041': ('oth_trans', 'casecover', L, M, "fig key 220-676 (transmission case figure): no sibling; AIM master has this part on Transmission > Case > Case Cover; HS 8708999790 (not a lubricant / additive)", "What is INHIBITOR on the transmission case figure? Catalogue Other transmission is a guess"),
}
RANK = {L: 0, M: 1, H: 2}


def norm(p: str) -> str:
    p = str(p).strip()
    return p.zfill(10) if p.isdigit() and len(p) < 10 else p


def main() -> None:
    s = pd.read_parquet(DER / "sales_fact.parquet")
    w = s[(s.billing_date >= "2025-09-01") & (s.billing_date <= "2026-08-31")].copy()
    w["pn"] = w.part_number.map(norm)
    rel = pd.read_csv(REL / "aim_pn_classification_release_2026-10-02-candidate.csv", dtype=str, keep_default_na=False)
    base = pd.read_csv(REL / "aim_pn_classification_release_2026-10-02.csv", dtype=str, keep_default_na=False, usecols=["part_number"])
    for name, r in (("approved 2026-10-02", base), ("candidate", rel)):
        m = w[~w.pn.isin(set(r.part_number))]
        print(f"vs {name}: {m.pn.nunique()} parts, EUR {m.net_sales_value.sum():,.2f}")
    m = w[~w.pn.isin(set(rel.part_number))]
    excl = m[m.pn.isin(EXCLUDED)]
    print("excluded:", excl.groupby("pn").net_sales_value.sum().round(2).to_dict())
    m = m[~m.pn.isin(EXCLUDED)]
    g = m.groupby("pn").agg(description=("description", "first"), l12m_billed_eur=("net_sales_value", "sum"),
                            billed_qty=("billed_qty", "sum"), billing_lines=("pn", "size"),
                            sold_to_count=("sold_to", "nunique")).reset_index()
    assert set(g.pn) == set(P), (set(g.pn) ^ set(P))
    fl = pd.read_csv(DER / "_audit_cls_pr00_flat.csv", dtype=str, keep_default_na=False).set_index("pn")
    cat_set = set(map(tuple, rel[["catalog_l1", "catalog_l2", "catalog_l3"]].values))
    aim_set = set(map(tuple, rel[["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]].values))
    rows = []
    for _, r in g.iterrows():
        ck, ak, cc, ca, ev, q = P[r.pn]
        cat, aim = C[ck], A[ak]
        assert cat in cat_set, cat
        assert aim in aim_set, aim
        if r.pn in fl.index and fl.loc[r.pn, "fig_no"]:
            fk, src = f"{fl.loc[r.pn, 'fig_no']}-{fl.loc[r.pn, 'key_no']}", "pr00 flat (fig_no-key_no)"
        elif r.pn == "8942720796":
            fk, src = "605-016", "AIM master"
        else:
            fk, src = "", ""
        conf = min((cc, ca), key=RANK.get)
        rows.append({"part_number": r.pn, "description": r.description, "fig_key": fk, "fig_key_source": src,
                     "l12m_billed_eur": round(r.l12m_billed_eur, 2), "billed_qty": r.billed_qty,
                     "billing_lines": r.billing_lines, "sold_to_count": r.sold_to_count,
                     "in_release": False,
                     "proposed_catalog_l1": cat[0], "proposed_catalog_l2": cat[1], "proposed_catalog_l3": cat[2],
                     "proposed_aim_l1": aim[0], "proposed_aim_l2": aim[1], "proposed_aim_l3": aim[2],
                     "confidence_catalog": cc, "confidence_aim": ca, "confidence": conf,
                     "evidence": ev, "open_question": q,
                     "status": "PROPOSED - not applied to any release; Jerome approves"})
    out = pd.DataFrame(rows)
    out["_r"] = out.confidence.map(RANK)
    out = out.sort_values(["_r", "l12m_billed_eur"], ascending=[True, False]).drop(columns="_r")
    out.to_csv(OUT, index=False, encoding="utf-8")
    print(f"wrote {OUT} ({len(out)} rows, EUR {out.l12m_billed_eur.sum():,.2f})")
    print(out.groupby("confidence").l12m_billed_eur.agg(["size", "sum"]).round(2))


if __name__ == "__main__":
    main()
