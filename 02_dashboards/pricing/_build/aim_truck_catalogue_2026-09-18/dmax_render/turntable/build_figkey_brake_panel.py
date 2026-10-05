"""Build the fig-key brake panel data for the D-Max turntable page.

This is the single builder. It reads four files and writes _figkey_panel.json.
Nothing is written back to 01_data. No number is typed in by hand.

Sources and the columns actually used
-------------------------------------
01_data/00_derived/sales_by_db_fig_key_year.csv
    year, distributor_code, fig_key, fig_key_label, billed_qty,
    net_sales_eur, distinct_pns
        what we billed, per figure key, per market, per year
01_data/00_derived/parts_catalog_dimension.csv
    part_number, fig_key, fig_key_label, pms_category, pr00_family,
    pr00_group, pr00_level3_type
        the part number to figure key bridge
01_data/00_derived/aim_pn_classification_v2.csv
    part_number, catalog_l1, catalog_l2, catalog_l3
        the catalogue category name for each part number
03_analytics/Isuzu/prism/data/gps_model_targets.csv
    model_group, target_eur_per_vehicle, notes
        the official spend target

Four tests are run and printed, because the answer to "does the figure key work"
depends on all four:

  1. Is the three-digit prefix consistent, judged on the labels inside it?
  2. How much euro can be placed on a zone, and how much cannot?
  3. Does the figure key's label place a part better or worse than its
     catalogue category name?
  4. The brake family split by what the figure key can and cannot say.

Run:  python build_figkey_brake_panel.py
"""
from __future__ import annotations

import collections
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"

SALES = D / "sales_by_db_fig_key_year.csv"
DIM = D / "parts_catalog_dimension.csv"
CLASS = D / "aim_pn_classification_v2.csv"
UIO = D / "gps_spu_by_distributor.csv"
TARGETS = ISZE / "03_analytics" / "Isuzu" / "prism" / "data" / "gps_model_targets.csv"
OUT = HERE / "_figkey_panel.json"

WINDOW = "2023 to 2026 to date"

# ===========================================================================
# The zone rule, applied to a label. STRICT is only words that say where on
# the vehicle the part physically sits. LOOSE adds the functional fallback.
# ===========================================================================
STRICT = {
    "front": ["headlamp", "fog lamp", "marker lamp", "marker / signal lamp",
              "tail lamp", "tail / combination lamp", "bumper", "grille", "lens",
              "bulb", "wiper", "front", "frt"],
    "rear": ["rear", "rr ", "tailgate", "loadbox", "cargo", "step / guard"],
    "cab": ["door", "glass / window", "mirror", "interior trim", "cab", "seat",
            "windscreen", "windshield", "fender", "panel", "trim / molding",
            "roof", "carpet", "handle / lock", "steering column"],
    "engine": ["engine", "turbocharger", "injector", "injection pump", "fuel pump",
               "radiator", "coolant", "thermostat", "water pump", "cylinder head",
               "liner", "piston", "pulley", "egr", "valvetrain", "air filter",
               "oil filter", "fuel filter", "urea (adblue) filter", "intercooler",
               "starter motor", "alternator", "master cylinder", "brake booster",
               "a/c compressor", "condenser", "heater core", "blower",
               "engine bearing", "engine shaft", "engine ring", "engine gear",
               "air compressor", "air duct", "fuel tank"],
    "chassis": ["brake disc", "brake drum", "brake shoe", "brake pad", "brake hose",
                "brake pipe", "wheel cylinder", "pad kit", "shoe kit", "lining",
                "abs component", "clutch", "transmission", "gearbox", "differential",
                "propeller", "axle", "leaf / suspension spring", "shock absorber",
                "stabilizer", "air spring", "suspension", "steering", "knuckle",
                "tie rod", "exhaust", "silencer", "muffler", "catalyst",
                "aftertreatment", "parking brake", "shift linkage", "gear set",
                "hanger / shackle", "drive shaft", "air tank", "air dryer",
                "air hose", "air valve"],
    "elec": ["sensor", "harness", "control unit", "switch", "relay", "actuator",
             "voltage regulator", "meter / gauge"],
}
LOOSE = {k: list(v) for k, v in STRICT.items()}
LOOSE["engine"] += ["filter", "gasket set", "oil seal / seal", "other gasket / seal",
                    "packing", "cap / plug", "fuel hose / pipe", "fuel sender",
                    "fuel system", "tensioner / idler", "valve / valvetrain",
                    "oil / lubricant", "grease", "cylinder"]
LOOSE["chassis"] += ["other mechanical", "shaft", "gear", "linkage / lever",
                     "case / housing / coupling", "bearing", "bushing / mount",
                     "other air system", "release bearing", "pressure plate / cover",
                     "hub bearing", "hub oil seal", "king pin", "wheel pin",
                     "rod / link", "spring", "pin", "other transmission",
                     "other clutch", "other steering", "other suspension",
                     "other exhaust", "other brake", "fuel hose / pipe"]
LOOSE["elec"] += ["other electrical", "a/c electrical"]
LOOSE["rear"] += ["body structure", "other body", "bracket / stay", "bolt", "nut",
                  "washer", "clip", "spacer / retainer", "fastener", "other hardware",
                  "rubber / grommet", "step / guard"]
LOOSE["cab"] += ["panel", "trim / molding", "interior / exterior cover", "glass"]

# Labels that name a part every vehicle carries but that is not in one place,
# or that carry no information at all. These are never placed.
NEVER_PLACED = {
    "review needed", "unmapped", "(blank)", "", "not classified at this level",
    "bolt", "nut", "washer", "clip", "pin", "spacer / retainer", "fastener",
    "other hardware", "rubber / grommet", "other gasket / seal", "oil seal / seal",
    "oil / lubricant", "grease", "cap / plug", "packing", "bracket / stay",
}

# ===========================================================================
# The chapter map. A three-digit prefix is a chapter in the parts catalogue;
# a chapter is an assembly on the vehicle. Written from the label content
# printed by the probe scripts, then checked for disjointness below.
# ===========================================================================
CHAPTER_ZONE = {
    "front": {"301", "302", "601", "603", "690", "801", "808", "803", "310",
              "805", "670", "701", "682"},
    "engine": {"001", "005", "010", "011", "012", "013", "014", "015", "020", "022",
               "025", "030", "031", "032", "033", "035", "036", "037", "038", "039",
               "040", "041", "042", "050", "051", "052", "055", "056", "057", "060",
               "061", "065", "066", "070", "071", "080", "081", "082", "084", "085",
               "086", "087", "090", "110", "111", "115", "120", "121", "122", "130",
               "131", "135", "140", "141", "145", "330", "331", "436", "850", "871",
               "875", "873"},
    "cab": {"605", "607", "610", "614", "630", "631", "632", "635", "641", "643",
            "645", "647", "650", "651", "652", "655", "665", "675", "678", "680",
            "681", "683", "684", "688", "720", "740", "742", "743", "745", "750",
            "755", "760", "430", "821", "840", "841", "845", "860", "865", "880",
            "890"},
    "chassis": {"150", "155", "156", "160", "201", "203", "205", "206", "207", "208",
                "210", "220", "221", "225", "226", "228", "229", "230", "231", "235",
                "236", "237", "239", "240", "241", "242", "244", "245", "246", "247",
                "248", "249", "253", "255", "256", "260", "261", "262", "265", "266",
                "275", "280", "281", "282", "285", "290", "320", "321", "322", "325",
                "326", "334", "340", "341", "345", "346", "352", "355", "358", "360",
                "370", "375", "377", "378", "383", "401", "410", "411", "412", "415",
                "416", "420", "425", "433", "435", "440", "441", "442", "450", "455",
                "460", "461", "465", "466", "470", "471", "480", "666", "996"},
    "rear": {"501", "510", "515", "520", "530", "540", "604", "620", "640", "660",
             "686", "687", "705", "710", "730", "741", "915", "930", "931", "932",
             "933", "995", "999", "305", "306", "308", "311", "997"},
    "elec": {"810", "815", "816", "820", "825", "826", "827", "828", "870", "146",
             "315", "350"},
}
_owner = {}
for _z, _ps in CHAPTER_ZONE.items():
    for _p in _ps:
        if _p in _owner:
            raise SystemExit("prefix %s is in two zones: %s and %s" % (_p, _owner[_p], _z))
        _owner[_p] = _z
PREFIX_TO_ZONE = _owner

ZONE_META = [
    ("front", "Front and lamps", "Nose of the vehicle", "Positional"),
    ("engine", "Engine bay", "Under the bonnet and the front of the chassis",
     "Positional"),
    ("cab", "Cab, doors and glass", "The driver's box", "Positional"),
    ("chassis", "Chassis, driveline and brakes", "Under the body, along the frame",
     "Positional"),
    ("rear", "Rear, body and hardware", "Behind the cab", "Positional"),
    ("elec", "Electrical and sensors", "Runs the whole length",
     "Functional, not positional"),
]

BRAKE_PREFIX = {"155", "156", "246", "301", "302", "305", "306", "308", "311", "315",
                "320", "326", "330", "331", "334", "340", "350", "352", "355", "358",
                "377", "411", "420", "666", "997"}
FRONT_AXLE_CH = {"301", "302"}
REAR_AXLE_CH = {"305", "306", "308", "311", "997"}
WHEEL_SENSOR_CH = {"315", "350", "820"}
ENGINE_BAY_CH = {"330", "331"}

BUCKET_ORDER = [
    ("front axle", "Positional - front axle",
     "The chapter is the front brake chapter, so the part lands on the front of the vehicle."),
    ("rear axle", "Positional - rear axle",
     "The chapter is the rear brake chapter, so the part lands on the rear of the vehicle."),
    ("engine bay (not axle-positional)", "Engine bay - not an axle position",
     "A master cylinder or a brake booster sits in the engine bay. It is a brake part with a real place, but that place is not an axle."),
    ("at a wheel (not one place)", "At a wheel - not one place",
     "An ABS sensor or a wheel-speed sensor is fitted at each wheel. It cannot be put on one zone without inventing which wheel."),
    ("runs between axles (not one place)", "Runs between axles - not one place",
     "A brake pipe or a brake hose runs the length of the vehicle between the axles."),
    ("chapter does not say which axle", "Chapter does not say which axle",
     "The part is a brake part but its chapter is a general chassis chapter, so the catalogue does not state a position."),
]


def pref(key: str):
    k = (key or "").strip()
    return k.split("-")[0] if re.fullmatch(r"\d{3}-\d{3}", k) else None


def zone_rule(rules):
    phrases = sorted([(p, z) for z, ps in rules.items() for p in ps],
                     key=lambda t: -len(t[0]))

    def f(label):
        l = (label or "").strip().lower()
        if l in NEVER_PLACED:
            return None
        for p, z in phrases:
            if p in l:
                return z
        return None
    return f


strict_zone = zone_rule(STRICT)
loose_zone = zone_rule(LOOSE)


def zone_of_key(label, key):
    """The page rule: the chapter map decides, because a chapter is an assembly.

    The label is used only to recognise a part that has no single place on the
    vehicle. This is the deliberate difference from the probe scripts, which
    asked whether the label alone could place a part and answered no.
    """
    if (label or "").strip().lower() in NEVER_PLACED:
        return None
    p = pref(key)
    return PREFIX_TO_ZONE.get(p) if p else None


def is_brake(label, key):
    l = (label or "").lower()
    if any(w in l for w in ("brake", "shoe", "pad kit", "lining", "caliper")):
        return True
    return pref(key) in BRAKE_PREFIX


def brake_bucket(label, key):
    l = (label or "").lower()
    p = pref(key)
    if p in FRONT_AXLE_CH:
        return "front axle"
    if p in REAR_AXLE_CH:
        return "rear axle"
    if p in ENGINE_BAY_CH:
        return "engine bay (not axle-positional)"
    if p in WHEEL_SENSOR_CH:
        return "at a wheel (not one place)"
    if "hose" in l or "pipe" in l:
        return "runs between axles (not one place)"
    return "chapter does not say which axle"


def main() -> int:
    rows = list(csv.DictReader(open(SALES, newline="", encoding="utf-8-sig")))
    total = sum(float(r["net_sales_eur"] or 0) for r in rows)

    eur_by_key = collections.Counter()
    lab_by_key = collections.defaultdict(collections.Counter)
    for r in rows:
        e = float(r["net_sales_eur"] or 0)
        eur_by_key[r["fig_key"]] += e
        lab_by_key[r["fig_key"]][r["fig_key_label"]] += e
    dom_lab = {k: c.most_common(1)[0][0] for k, c in lab_by_key.items()}
    dom_lab_share = {k: c.most_common(1)[0][1] / sum(c.values())
                     for k, c in lab_by_key.items()}

    key_pns = collections.defaultdict(set)
    for r in csv.DictReader(open(DIM, newline="", encoding="utf-8-sig")):
        pn, k = (r["part_number"] or "").strip(), (r["fig_key"] or "").strip()
        if pn and k:
            key_pns[k].add(pn)

    pn_cat = {}
    for r in csv.DictReader(open(CLASS, newline="", encoding="utf-8-sig")):
        pn_cat[r["part_number"].strip()] = (r["catalog_l1"] or "").strip(), \
                                           (r["catalog_l2"] or "").strip(), \
                                           (r["catalog_l3"] or "").strip()

    print("=" * 100)
    print("FIG KEY AS A POSITIONAL SPINE - D-Max brake panel")
    print("=" * 100)
    print(f"what we billed, all markets, {WINDOW}: EUR {total:,.2f}")
    print(f"rows {len(rows):,}   figure keys {len(eur_by_key):,}")
    print()

    # ---------------------------------------------------------------- test 1
    byp = collections.defaultdict(lambda: {"eur": 0.0, "zones": collections.Counter(),
                                           "noz": 0.0, "keys": set()})
    for r in rows:
        e = float(r["net_sales_eur"] or 0)
        p = pref(r["fig_key"]) or "not a figure key"
        z = strict_zone(r["fig_key_label"])
        d = byp[p]
        d["eur"] += e
        d["keys"].add(r["fig_key"])
        if z is None:
            d["noz"] += e
        else:
            d["zones"][z] += e

    clean, dirty, conflict = [], [], []
    for p, d in byp.items():
        if d["eur"] <= 0 or p == "not a figure key":
            continue
        pl = sum(d["zones"].values())
        d["n_zones"] = sum(1 for _, v in d["zones"].items() if pl and v / pl >= 0.20)
        d["purity"] = (d["zones"].most_common(1)[0][1] / pl) if pl else 0.0
        d["noz_share"] = d["noz"] / d["eur"]
        if d["n_zones"] >= 2:
            conflict.append(p)
        elif d["purity"] >= 0.85 and d["noz_share"] < 0.15:
            clean.append(p)
        else:
            dirty.append(p)

    def eur_of(lst):
        return sum(byp[p]["eur"] for p in lst)

    print("TEST 1  IS THE THREE-DIGIT PREFIX CONSISTENT?")
    print("        judged on the labels inside the prefix, using only positional words")
    print(f"          clean, one zone              : {len(clean):>4} prefixes  "
          f"EUR {eur_of(clean):>16,.0f}  {100*eur_of(clean)/total:>5.1f}%")
    print(f"          one zone plus noise          : {len(dirty):>4} prefixes  "
          f"EUR {eur_of(dirty):>16,.0f}  {100*eur_of(dirty)/total:>5.1f}%")
    print(f"          two or more zones            : {len(conflict):>4} prefixes  "
          f"EUR {eur_of(conflict):>16,.0f}  {100*eur_of(conflict)/total:>5.1f}%   <- the prefix rule breaks here")
    print()

    # ---------------------------------------------------------------- test 2
    placed = collections.Counter()
    unplaced = collections.Counter()
    for k, e in eur_by_key.items():
        z = zone_of_key(dom_lab.get(k, ""), k)
        if z is None:
            p = pref(k)
            if p is None:
                unplaced["not a figure key"] += e
            elif (dom_lab.get(k, "") or "").strip().lower() in ("review needed", "unmapped"):
                unplaced["Review needed or Unmapped"] += e
            elif (dom_lab.get(k, "") or "").strip().lower() in NEVER_PLACED:
                unplaced["a part every vehicle carries in no fixed place"] += e
            else:
                unplaced["chapter is not in the zone map"] += e
        else:
            placed[z] += e

    placed_eur, unplaced_eur = sum(placed.values()), sum(unplaced.values())
    if abs(placed_eur + unplaced_eur - total) > 0.05:
        raise SystemExit("ADDITIVITY BROKEN: %.2f + %.2f != %.2f"
                         % (placed_eur, unplaced_eur, total))

    print("TEST 2  HOW MUCH CAN BE PLACED ON A ZONE?")
    for z, _, _, _ in ZONE_META:
        print(f"          {z:<10} EUR {placed[z]:>16,.0f}  {100*placed[z]/total:>5.1f}%")
    print(f"          {'cannot place':<10} EUR {unplaced_eur:>16,.0f}  "
          f"{100*unplaced_eur/total:>5.1f}%")
    for k, v in unplaced.most_common():
        print(f"            {k:<52} EUR {v:>14,.0f}  {100*v/total:>5.1f}%")
    print(f"          total EUR {placed_eur+unplaced_eur:,.0f} "
          f"(billed EUR {total:,.0f})   additivity OK")
    print()

    # ---------------------------------------------------------------- test 3
    dom_cat = {}
    for k in eur_by_key:
        c = collections.Counter()
        for pn in key_pns.get(k, ()):
            if pn in pn_cat:
                c[pn_cat[pn][2]] += 1
        dom_cat[k] = c.most_common(1)[0][0] if c else ""

    def route(labelof, zonefn):
        return sum(e for k, e in eur_by_key.items() if zonefn(labelof(k)) is not None)

    a_txt = route(lambda k: dom_lab.get(k, ""), strict_zone)
    b_txt = route(lambda k: dom_cat.get(k, ""), strict_zone)
    a_all = route(lambda k: dom_lab.get(k, ""), loose_zone)
    b_all = route(lambda k: dom_cat.get(k, ""), loose_zone)
    dis = 0
    dis_eur = 0.0
    for k, e in eur_by_key.items():
        za, zb = loose_zone(dom_lab.get(k, "")), loose_zone(dom_cat.get(k, ""))
        if za is not None and zb is not None and za != zb:
            dis += 1
            dis_eur += e

    print("TEST 3  FIGURE KEY LABEL vs CATALOGUE CATEGORY NAME, same zone rule, same euro")
    print(f"          only words that state a position")
    print(f"            figure key label   EUR {a_txt:>16,.0f}  {100*a_txt/total:>5.1f}%")
    print(f"            category name      EUR {b_txt:>16,.0f}  {100*b_txt/total:>5.1f}%")
    print(f"          with the assembly fallback")
    print(f"            figure key label   EUR {a_all:>16,.0f}  {100*a_all/total:>5.1f}%")
    print(f"            category name      EUR {b_all:>16,.0f}  {100*b_all/total:>5.1f}%")
    print(f"          both place the key but disagree where: {dis} figure keys, "
          f"EUR {dis_eur:,.0f} ({100*dis_eur/total:.2f}%)")
    print()

    # ---------------------------------------------------------------- test 4
    # A figure key is classified ONCE, by its dominant label. Classifying row by
    # row let a key land in two buckets at the same time and made the bucket
    # totals disagree with the zone totals.
    brake = collections.defaultdict(lambda: {"eur": 0.0, "keys": set(),
                                             "labs": collections.Counter(),
                                             "pns": set()})
    for k, e in eur_by_key.items():
        label = dom_lab.get(k, "")
        if not is_brake(label, k):
            continue
        b = brake[brake_bucket(label, k)]
        b["eur"] += e
        b["keys"].add(k)
        b["labs"][label] += e
        b["pns"] |= key_pns.get(k, set())
    brake_total = sum(b["eur"] for b in brake.values())
    positional = brake["front axle"]["eur"] + brake["rear axle"]["eur"]

    print("TEST 4  THE BRAKE FAMILY, SPLIT BY WHAT THE FIGURE KEY CAN AND CANNOT SAY")
    print(f"          brake total EUR {brake_total:,.0f} "
          f"({100*brake_total/total:.2f}% of the catalogue)")
    for key, _, _ in BUCKET_ORDER:
        b = brake[key]
        print(f"            {key:<38} EUR {b['eur']:>11,.0f} "
              f"{100*b['eur']/brake_total:>5.1f}%  {len(b['keys']):>4} keys "
              f"{len(b['pns']):>5} part numbers")
    print(f"          positional front plus rear axle: EUR {positional:,.0f} "
          f"= {100*positional/brake_total:.1f}% of brake euro")
    print()

    # ---------------------------------------------------------------- targets
    tg = {r["model_group"]: r for r in csv.DictReader(
        open(TARGETS, newline="", encoding="utf-8-sig"))}
    lcv = float(tg["LCV_D_Max"]["target_eur_per_vehicle"])

    uio = collections.defaultdict(dict)
    for r in csv.DictReader(open(UIO, newline="", encoding="utf-8-sig")):
        try:
            uio[r["distributor_code"]][r["year"]] = float(r["uio_units"] or 0)
        except ValueError:
            pass
    ALIAS = {"GERMANY": "ISD", "SWEDEN": "Sverige", "FINLAND": "Nordic FI",
             "HUNGARY": "AutoWallis", "ROMANIA": "ROM Auto", "MALTA": "GasanZammit",
             "ICELAND": "BL Iceland", "CYPRUS": "Loutsios", "UKRAINE": "CIS-KTK",
             "PALESTINE": "KIMA"}
    dy = collections.Counter()
    for r in rows:
        dy[(r["distributor_code"], r["year"])] += float(r["net_sales_eur"] or 0)

    # Like for like: only the market-years that carry a vehicle count, and the
    # ceiling for each year is that year's vehicles in service at the official rate.
    # 2026 is left out: the billing file holds a part year, so it would compare a
    # whole-year ceiling with a part-year of billing.
    L4L_YEARS = ("2023", "2024", "2025")
    ceiling = 0.0
    matched = 0.0
    ceiling_by_year = collections.Counter()
    matched_by_year = collections.Counter()
    dbs = set()
    for (db, yr), e in dy.items():
        if yr not in L4L_YEARS:
            continue
        code = ALIAS.get(db, db)
        u = uio.get(code, {}).get(yr)
        if u is None or code is None:
            continue
        ceiling += u * lcv
        matched += e
        ceiling_by_year[yr] += u * lcv
        matched_by_year[yr] += e
        dbs.add(db)

    print("TARGET, like for like (%s, markets that carry a vehicle count)"
          % ", ".join(L4L_YEARS))
    print(f"          markets counted            : {len(dbs)}")
    for y in L4L_YEARS:
        print(f"          {y}  billed EUR {matched_by_year[y]:>14,.0f}   "
              f"ceiling EUR {ceiling_by_year[y]:>14,.0f}   "
              f"{100*matched_by_year[y]/ceiling_by_year[y]:>5.1f}%")
    print(f"          total billed               : EUR {matched:>16,.0f}")
    print(f"          ceiling at EUR {lcv:.0f}/vehicle : EUR {ceiling:>16,.0f}")
    print(f"          billed as a share of the ceiling: {100*matched/ceiling:.1f}%")
    print("          this covers all parts, not only brakes. The per-zone brake euro is")
    print("          shown against the whole-vehicle target, not against a brake target,")
    print("          because no separately published brake target exists.")
    print()

    # ---------------------------------------------------------------- write
    zone_target = {z: lcv * (placed[z] / placed_eur) for z, _, _, _ in ZONE_META}

    def pn_sample(names, n=14):
        return sorted(names)[:n]

    zones = []
    for z, name, where, basis in ZONE_META:
        # a brake part is counted once, under the brake bucket it belongs to
        zb = collections.Counter()
        zbpns = collections.defaultdict(set)
        for k, e in eur_by_key.items():
            if not is_brake(dom_lab.get(k, ""), k):
                continue
            bucket = brake_bucket(dom_lab.get(k, ""), k)
            home = {"front axle": "front", "rear axle": "rear",
                    "engine bay (not axle-positional)": "engine",
                    "at a wheel (not one place)": "chassis",
                    "runs between axles (not one place)": "chassis",
                    "chapter does not say which axle": "chassis"}[bucket]
            if home == z:
                zb[bucket] += e
                zbpns[bucket] |= key_pns.get(k, set())
        zones.append({
            "k": z, "name": name, "where": where, "basis": basis,
            "eur": round(placed[z], 2),
            "share_pct": round(100 * placed[z] / total, 2),
            "target_eur": round(zone_target[z], 2),
            "fig_keys": len({k for k in eur_by_key
                             if zone_of_key(dom_lab.get(k, ""), k) == z}),
            "part_numbers": len({pn for k in eur_by_key
                                 if zone_of_key(dom_lab.get(k, ""), k) == z
                                 for pn in key_pns.get(k, ())}),
            "brake_eur": round(sum(zb.values()), 2),
            "brake_share_pct": round(100 * sum(zb.values()) / total, 2),
            "brake_part_numbers": len({pn for s in zbpns.values() for pn in s}),
            "brake_buckets": [{"k": bk, "label": dict((a, b) for a, b, _ in BUCKET_ORDER)[bk],
                               "eur": round(v, 2),
                               "part_numbers": len(zbpns[bk])}
                              for bk, v in zb.most_common() if v > 0],
        })

    panel = {
        "built_for": "Isuzu D-Max turntable, zones on frame 1",
        "window": WINDOW,
        "sources": [
            "01_data/00_derived/sales_by_db_fig_key_year.csv "
            "(net_sales_eur, fig_key, fig_key_label, billed_qty, distinct_pns)",
            "01_data/00_derived/parts_catalog_dimension.csv "
            "(part_number, fig_key, fig_key_label, pms_category)",
            "01_data/00_derived/aim_pn_classification_v2.csv "
            "(part_number, catalog_l1, catalog_l2, catalog_l3)",
            "03_analytics/Isuzu/prism/data/gps_model_targets.csv "
            "(model_group, target_eur_per_vehicle, notes)",
        ],
        "total_eur": round(total, 2),
        "total_fig_keys": len(eur_by_key),
        "placed_eur": round(placed_eur, 2),
        "placed_pct": round(100 * placed_eur / total, 2),
        "unplaced_eur": round(unplaced_eur, 2),
        "unplaced_pct": round(100 * unplaced_eur / total, 2),
        "unplaced_reasons": [{"reason": k, "eur": round(v, 2),
                              "pct": round(100 * v / total, 2)}
                             for k, v in unplaced.most_common()],
        "zones": zones,
        "target": {
            "eur_per_vehicle_per_year": lcv,
            "note": tg["LCV_D_Max"]["notes"],
            "basis": ("EUR %d is the official target for one vehicle for one year. "
                      "A per-zone target is that figure split by each zone's share of "
                      "what we billed across the whole catalogue. It is an allocation, "
                      "not a separately published per-zone target. It is a target for "
                      "the whole vehicle, not for brakes only." % int(lcv)),
            "like_for_like": {
                "years": list(L4L_YEARS),
                "markets": len(dbs),
                "billed_eur": round(matched, 2),
                "ceiling_eur": round(ceiling, 2),
                "billed_share_pct": round(100 * matched / ceiling, 1),
                "by_year": [{"year": y,
                             "billed_eur": round(matched_by_year[y], 2),
                             "ceiling_eur": round(ceiling_by_year[y], 2),
                             "share_pct": round(100 * matched_by_year[y] / ceiling_by_year[y], 1)}
                            for y in L4L_YEARS],
                "note": ("Only the markets that carry a vehicle count are included, and "
                         "the ceiling is each year's vehicles in service at the official "
                         "rate. 2026 is left out because the billing file holds a part "
                         "year. This covers all parts, not only brakes."),
            },
        },
        "brake": {
            "total_eur": round(brake_total, 2),
            "share_of_catalogue_pct": round(100 * brake_total / total, 2),
            "positional_eur": round(positional, 2),
            "positional_pct": round(100 * positional / brake_total, 1),
            "buckets": [{
                "k": key, "label": label, "why": why,
                "eur": round(brake[key]["eur"], 2),
                "share_pct": round(100 * brake[key]["eur"] / brake_total, 1),
                "fig_keys": len(brake[key]["keys"]),
                "part_numbers": len(brake[key]["pns"]),
                "examples": [l for l, _ in brake[key]["labs"].most_common(5)],
                "home_zone": {"front axle": "front", "rear axle": "rear",
                              "engine bay (not axle-positional)": "engine",
                              "at a wheel (not one place)": "chassis",
                              "runs between axles (not one place)": "chassis",
                              "chapter does not say which axle": "chassis"}[key],
                "pn_sample": pn_sample(brake[key]["pns"]),
                "sample_keys": sorted(brake[key]["keys"])[:8],
            } for key, label, why in BUCKET_ORDER if brake[key]["eur"] > 0],
        },
        "tests": {
            "prefix_consistency": {
                "clean": {"prefixes": len(clean), "eur": round(eur_of(clean), 2),
                          "pct": round(100 * eur_of(clean) / total, 1)},
                "noise": {"prefixes": len(dirty), "eur": round(eur_of(dirty), 2),
                          "pct": round(100 * eur_of(dirty) / total, 1)},
                "conflict": {
                    "prefixes": len(conflict), "eur": round(eur_of(conflict), 2),
                    "pct": round(100 * eur_of(conflict) / total, 1),
                    "list": sorted(
                        [{"prefix": p, "eur": round(byp[p]["eur"], 2),
                          "zones": {z: round(v, 2) for z, v in byp[p]["zones"].most_common()},
                          "purity": round(byp[p]["purity"], 3)}
                         for p in conflict], key=lambda d: -d["eur"])[:30]},
            },
            "route_compare": {
                "strict": {"fig_key_label_eur": round(a_txt, 2),
                           "fig_key_label_pct": round(100 * a_txt / total, 1),
                           "category_name_eur": round(b_txt, 2),
                           "category_name_pct": round(100 * b_txt / total, 1)},
                "with_fallback": {"fig_key_label_eur": round(a_all, 2),
                                  "fig_key_label_pct": round(100 * a_all / total, 1),
                                  "category_name_eur": round(b_all, 2),
                                  "category_name_pct": round(100 * b_all / total, 1)},
                "disagree_keys": dis, "disagree_eur": round(dis_eur, 2),
                "disagree_pct": round(100 * dis_eur / total, 2),
            },
            "label_drift": {
                "keys_with_more_than_one_label":
                    sum(1 for c in lab_by_key.values() if len(c) > 1),
                "keys_total": len(lab_by_key),
                "weak_dominant":
                    sum(1 for k, s in dom_lab_share.items() if s < 0.95),
                "eur_in_drifted_keys": round(sum(
                    sum(c.values()) for c in lab_by_key.values() if len(c) > 1), 2),
            },
            "jerome_checks": {
                "positional_keyword_pct_measured": round(100 * a_txt / total, 1),
                "review_needed_pct": round(100 * sum(
                    float(r["net_sales_eur"] or 0) for r in rows
                    if r["fig_key_label"] == "Review needed") / total, 2),
                "unmapped_pct": round(100 * sum(
                    float(r["net_sales_eur"] or 0) for r in rows
                    if r["fig_key_label"] == "Unmapped") / total, 2),
                "not_a_fig_key_pct": round(100 * sum(
                    float(r["net_sales_eur"] or 0) for r in rows
                    if pref(r["fig_key"]) is None) / total, 2),
            },
        },
    }
    OUT.write_text(json.dumps(panel, indent=1), encoding="utf-8")
    print(f"panel -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
