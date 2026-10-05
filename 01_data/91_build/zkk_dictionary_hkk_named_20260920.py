# -*- coding: utf-8 -*-
"""
ZKK dictionary -- does HKK's fourth character carry a named meaning?

The 2022 workbook `01_data/HKK Code 20221028.xlsx` lays out, per sheet, a block per
three-digit prefix and, under it, a single slot character with a name written beside it.
This pass extracts those (prefix, slot, name) triples and tests each against the dominant
Japanese leading noun measured on the billed book for the matching four-character HKK code.

Read-only. Nothing written to disk.

Run: python 01_data/91_build/zkk_dictionary_hkk_named_20260920.py
"""
from __future__ import annotations

import collections
import csv
import re
import sys
import unicodedata
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "01_data" / "00_derived" / "jp_codes_cache_20260920.csv"
SPINE = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
HKK2022 = ROOT / "01_data" / "HKK Code 20221028.xlsx"
BLANKISH = {"", "-", "--", "N/A", "NA", "NONE", "UNKNOWN", "(BLANK)"}

# first four letters of the workbook name, mapped to the vocabulary the Japanese description uses
BRIDGE = {
    "CAB": "CAB",
    "LINER": "LINER",
    "DOOR": "DOOR",
    "DPF": "DPD",
    "MIRROR": "MIRROR",
    "GLASS": "GLASS",
    "GASKET": "GASKET",
    "BEARING": "BEARING",
    "BULB": "BULB",
    "BELT": "BELT",
    "HOSE": "HOSE",
    "SEAL": "SEAL",
    "OILSEAL": "SEAL",
    "PAD": "PAD",
    "DISC": "DISC",
    "PLATE": "PLATE",
    "PRESSURE": "PLATE",
    "DRIVEN": "DISC",
    "FILTER": "FILTER",
    "ELEMENT": "ELEMENT",
    "AIR": "AIR",
    "FUEL": "FILTER",
    "HEATER": "HEATER",
    "PISTON": "PISTON",
    "REPAIR": "REPAIR",
    "NOZZLE": "NOZZLE",
    "PANEL": "PANEL",
    "SILENCER": "SILENCER",
    "SPRING": "SPRING",
    "DIAPHRAGM": "DIAPHRAGM",
    "PIN": "PIN",
    "WHEEL": "WHEEL",
    "BLADE": "BLADE",
    "WIPER": "BLADE",
    "SHOE": "SHOE",
    "BUSH": "BUSHING",
    "TORQUE": "BUSHING",
    "CUP": "CUP",
    "LINING": "LINING",
    "CHAMBER": "CHAMBER",
    "RADIATOR": "RADIATOR",
    "DOOR": "DOOR",
    "INJECTOR": "INJECTOR",
    "INJ": "INJECTOR",
    "TACHO": "TACHO",
    "BATTERY": "BATTERY",
    "JACK": "JACK",
    "TYRE": "TYRE",
    "LAMP": "LAMP",
    "REAR": "LAMP",
    "COMBILAMP": "LAMP",
    "PLUG": "PLUG",
    "THERMOSTAT": "THERMOSTAT",
    "RIM": "RIM",
    "FRAME": "FRAME",
}

# words that appear in the workbook names but carry no part-type meaning
STOP = {"REBUILT", "REMAN", "COMPONENT", "COMPONENTS", "PARTS", "ASSEMBLY", "INCL",
        "OTHER", "GENERAL", "SMALL", "SNOW", "LIGHT", "BULBS", "SEAT", "BED", "WEDGE",
        "PIGGY", "BACK", "MASTER", "WHEEL", "ROD", "NUT", "FLUID"}


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    if t.endswith(".0") and t[:-2].replace("-", "").isdigit():
        t = t[:-2]
    return t


def noun(desc: str) -> str:
    d = re.sub(r"\s+", " ", (desc or "").upper()).strip()
    head = re.sub(r"\s+", " ", re.split(r"[;,]", d)[0]).strip(" .-*/")
    return head if head and head not in BLANKISH else "(blank)"


def nfkc(v) -> str:
    return unicodedata.normalize("NFKC", str(v or "")).strip()


def main() -> int:
    P = print

    # ---- extract (prefix, slot, name) from the 2022 workbook ----
    # Layout per row is: [3-digit prefix][single slot char][name] repeated across the row.
    # The header rows use full-width digits and a different spacing, so scan every row for
    # the triple rather than anchoring on the header.
    triples: dict[str, list[str]] = collections.defaultdict(list)
    wb = openpyxl.load_workbook(HKK2022, read_only=True, data_only=True)
    for sh in wb.sheetnames:
        ws = wb[sh]
        for row in ws.iter_rows(values_only=True):
            cells = [nfkc(c) for c in row]
            i = 0
            while i < len(cells) - 2:
                if re.fullmatch(r"\d{3}", cells[i]) and re.fullmatch(r"[A-Za-z0-9]", cells[i + 1]):
                    name = cells[i + 2]
                    if len(name) > 1 and not name.startswith("(") and name != "Others":
                        triples[cells[i] + cells[i + 1]].append(name)
                        i += 3
                        continue
                i += 1
    wb.close()
    P(f"  (prefix, slot, name) triples extracted from the 2022 workbook: {len(triples)}")

    # ---- billed book ----
    cache = {}
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("pn"))
            if pn:
                cache[pn] = r
    base = {}
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("part_number"))
            if not pn:
                continue
            c = cache.get(pn)
            if not c:
                continue
            z = s(c.get("zkk"))
            if not z:
                continue
            base[pn] = {"eur": float(r.get("l12m_billed_eur") or 0),
                        "desc": s(c.get("jp_description")), "hkk": s(c.get("hkk"))}

    agg = collections.defaultdict(lambda: {"pns": 0, "eur": 0.0, "nouns": collections.Counter()})
    for pn, v in base.items():
        a = agg[v["hkk"]]
        a["pns"] += 1
        a["eur"] += v["eur"]
        a["nouns"][noun(v["desc"])] += 1
    base_eur = sum(v["eur"] for v in base.values())

    P("")
    P("=" * 100)
    P("L. DOES THE 2022 WORKBOOK NAME MATCH WHAT WE MEASURE ON THE BILLED BOOK?")
    P("=" * 100)
    P(f"  {'HKK':<7} {'PNs':>7} {'EUR':>13} {'2022 name':<38} {'measured dom noun':<18} {'share':>6}  verdict")
    hit = miss = 0
    tested = 0
    for code in sorted(agg):
        if code not in triples or agg[code]["pns"] < 2:
            continue
        names = triples[code]
        name = sorted(names, key=len)[-1]
        a = agg[code]
        dom, cnt = a["nouns"].most_common(1)[0]
        share = 100 * cnt / a["pns"]
        # is the workbook name reflected in the dominant measured noun?
        # token test both ways: a meaningful word from the workbook name appearing in the
        # measured noun (Air Filter Element -> FILTER) or the measured noun appearing in the name
        ntoks = {t for t in re.findall(r"[A-Z]{4,}", name.upper()) if t not in STOP}
        dtoks = {t for t in re.findall(r"[A-Z]{4,}", dom.upper()) if t not in STOP}
        ok = any(a in b or b in a for a in ntoks for b in dtoks)
        if a["pns"] >= 20:
            tested += 1
            if ok:
                hit += 1
            else:
                miss += 1
        P(f"  `{code}` {a['pns']:>7,} {a['eur']:>13,.0f} {name[:37]:<38} {dom:<18} {share:>5.1f}%  "
          f"{'MATCH' if ok else 'no match'}")
    P("")
    P(f"  codes with >=20 PNs tested against the 2022 workbook name: {tested}; "
      f"match {hit}; no match {miss}")
    P(f"  -> of the tested codes, {100*hit/max(tested,1):.0f}% carry the part type the workbook names")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
