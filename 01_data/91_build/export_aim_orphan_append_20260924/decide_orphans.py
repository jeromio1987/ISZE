# -*- coding: utf-8 -*-
"""Decision file for the 43 orphan part numbers.

Route ladder, exactly as briefed:
  (a) the EPC figure name from classified.csv, read through aim_rules.py  -> stamp export_aim_eq_20260924
  (b) the exact description already meaning ONE full AIM path on the master with >= 3
      supporting parts (master + classification overlay), figure key used only as a veto
                                                                        -> stamp export_pr00_20260924
  (c) unplaced, reported

Writes decision_orphans.csv into this folder. Read-only against the master.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
EQ = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
OUT = ROOT / "01_data" / "91_build" / "export_aim_orphan_append_20260924"

sys.path.insert(0, str(EQ))
from aim_rules import RULES  # noqa: E402

RULES = sorted(RULES, key=lambda r: -len(r[0]))

PH = {"", "Unknown", "Unknown Review", "Not on AIM spine", "nan", "None", "To Review",
      "Unclassified"}

STAMP_EPC = "export_aim_eq_20260924"
STAMP_DESC = "export_pr00_20260924"


def aim_from_fig_name(fig_name: str):
    """The same reading classify.py uses: strip the leading figure code, longest rule wins."""
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", (fig_name or "").upper())
    hits = [(p, l1, l2, l3) for p, l1, l2, l3 in RULES if p in up]
    if not hits:
        return None, "", []
    p, l1, l2, l3 = hits[0]
    return (l1, l2, l3), p, hits


def master_path(r: dict):
    l1 = (r.get("aim_l1") or "").strip()
    l2 = (r.get("aim_l2") or "").strip()
    l3 = (r.get("aim_l3") or "").strip()
    f1 = (r.get("aim_l1_fixed") or "").strip()
    f2 = (r.get("aim_l2_fixed") or "").strip()
    if f1 not in PH:
        l1 = f1
    if f2 not in PH:
        l2 = f2
    return l1, l2, l3


def main() -> None:
    orphans = []
    with (EQ / "orphans_43.csv").open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            orphans.append(r)
    pns = [r["part_number"].strip().upper() for r in orphans]
    assert len(set(pns)) == 43, len(set(pns))
    print(f"orphans: {len(orphans)}")

    master_leaves = set()
    M_desc = defaultdict(list)
    M_fig = defaultdict(list)
    with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            p = master_path(r)
            if all(x and x not in PH for x in p):
                master_leaves.add(p)
                M_desc[(r.get("description") or "").strip()].append(p)
            fk = (r.get("fig_key") or "").strip()
            if fk and all(x and x not in PH for x in p):
                M_fig[fk].append(p)

    C_desc = defaultdict(list)
    C_fig = defaultdict(list)
    with (DER / "aim_pn_classification_20260920.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pa = ((r.get("aim_l1_fixed") or "").strip(), (r.get("aim_l2_fixed") or "").strip(),
                  (r.get("aim_l3_fixed") or "").strip())
            if all(x and x not in PH for x in pa):
                C_desc[(r.get("description_norm") or "").strip()].append(pa)
                fk = (r.get("fig_key") or "").strip()
                if fk:
                    C_fig[fk].append(pa)

    cls = {}
    with (EQ / "classified.csv").open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            k = (r.get("pn") or "").strip().upper()
            if k in pns and k not in cls:
                cls[k] = r

    decisions = []
    for o in orphans:
        pn = o["part_number"].strip().upper()
        desc = (o["Description"] or "").strip()
        fig_key = (o["fig_key"] or "").strip()
        c = cls[pn]
        d = {
            "pn": pn,
            "description": desc,
            "fig_key": fig_key,
            "list_eur": (o.get("list_eur") or "").strip(),
            "abc": (o.get("ABC Code") or "").strip(),
            "route": "c",
            "stamp": "",
            "chosen_l1": "", "chosen_l2": "", "chosen_l3": "",
            "evidence": "",
            "epc_fig_name": "",
            "rule_phrase": "",
            "route_a_triple": "",
            "route_b_triple": "",
            "route_b_support_total": 0,
            "route_b_support_master": 0,
            "route_b_support_overlay": 0,
            "route_b_figkey_top": "",
            "route_b_figkey_n": 0,
            "route_b_figkey_disagrees": False,
            "classified_source": (c.get("aim_source_this_pass") or "").strip(),
            "classified_note": (c.get("aim_note") or "").strip(),
            "fig_name_rule_contested": False,
            "a_vs_b_conflict": False,
            "place": False,
        }

        # ---- route (a): the EPC figure name through the authored rules
        fig_name = ""
        if d["classified_source"] == "EPC figure name":
            fig_name = d["classified_note"]
        d["epc_fig_name"] = fig_name
        trip_a, phrase, hits = aim_from_fig_name(fig_name)
        d["rule_phrase"] = phrase
        distinct_a = {h[1:] for h in hits}
        d["fig_name_rule_contested"] = len(distinct_a) > 1
        if trip_a:
            d["route_a_triple"] = " > ".join(trip_a)
        # ---- route (b): exact description -> one full AIM path, >=3, fig key as veto
        pool = Counter(M_desc.get(desc, [])) + Counter(C_desc.get(desc, []))
        strong = {k: v for k, v in pool.items() if v >= 3}
        if len(strong) == 1:
            (path, support), = strong.items()
            d["route_b_triple"] = " > ".join(path)
            d["route_b_support_total"] = support
            d["route_b_support_master"] = Counter(M_desc.get(desc, []))[path]
            d["route_b_support_overlay"] = Counter(C_desc.get(desc, []))[path]
            fk_paths = Counter(M_fig.get(fig_key, [])) + Counter(C_fig.get(fig_key, []))
            top = fk_paths.most_common(1)[0] if fk_paths else None
            if top:
                d["route_b_figkey_top"] = " > ".join(top[0])
                d["route_b_figkey_n"] = top[1]
                d["route_b_figkey_disagrees"] = top[0] != path

        if trip_a:
            d["route"] = "a"
            d["stamp"] = STAMP_EPC
            d["chosen_l1"], d["chosen_l2"], d["chosen_l3"] = trip_a
            d["evidence"] = (f"EPC figure name {fig_name!r} -> rule {phrase!r} "
                             f"-> {' > '.join(trip_a)}")
            d["place"] = True
        elif d["route_b_triple"] and not d["route_b_figkey_disagrees"]:
            path = tuple(d["route_b_triple"].split(" > "))
            if path in master_leaves:
                d["route"] = "b"
                d["stamp"] = STAMP_DESC
                d["chosen_l1"], d["chosen_l2"], d["chosen_l3"] = path
                d["evidence"] = (f"description {desc!r} -> one full master path, support "
                                 f"{d['route_b_support_total']} "
                                 f"(master {d['route_b_support_master']}, overlay "
                                 f"{d['route_b_support_overlay']})")
                d["place"] = True
        if not d["place"]:
            d["route"] = "c"
            if not fig_name and d["classified_source"] == "figure key, unanimous on the master":
                d["evidence"] = ("no EPC figure name; the earlier run placed it by a unanimous "
                                 f"figure key ({fig_key}) which is not a route in this brief; "
                                 f"description evidence below the 3-part bar")
            elif d["classified_note"] == "not in the EPC":
                d["evidence"] = ("not in the EPC and the exact description carries fewer than 3 "
                                 "supporting parts on the master")
            else:
                d["evidence"] = ("no EPC figure name, and the exact description does not settle "
                                 "on one full master path with >= 3 supporting parts")

        assert not (d["place"] and not all((d["chosen_l1"], d["chosen_l2"], d["chosen_l3"])))
        if d["place"]:
            assert (d["chosen_l1"], d["chosen_l2"], d["chosen_l3"]) in master_leaves, pn
        decisions.append(d)

    OUT.mkdir(parents=True, exist_ok=True)
    cols = list(decisions[0].keys())
    with (OUT / "decision_orphans.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(decisions)

    placed = [d for d in decisions if d["place"]]
    print(f"\nplaced: {len(placed)}   unplaced: {len(decisions) - len(placed)}")
    print("  route a:", sum(1 for d in decisions if d["route"] == "a"))
    print("  route b:", sum(1 for d in decisions if d["route"] == "b"))
    print("  route c:", sum(1 for d in decisions if d["route"] == "c"))
    print("\nfigure names where more than one rule matched (contested, first rule still wins):")
    for d in decisions:
        if d["route"] == "a" and d["fig_name_rule_contested"]:
            note = "" if not d["route_b_triple"] else f"   route(b) would say {d['route_b_triple']}"
            print(f"   {d['pn']}  {d['epc_fig_name']!r} -> {d['route_a_triple']}{note}")
    print("\nroute (a) vs route (b) disagreements where (b) has support:")
    for d in decisions:
        if d["route"] == "a" and d["route_b_triple"] and d["route_b_triple"] != d["route_a_triple"]:
            print(f"   {d['pn']:12} {d['description'][:30]:30} a={d['route_a_triple']:56} "
                  f"b={d['route_b_triple']} (sup {d['route_b_support_total']})")
    print("\nunplaced:")
    for d in decisions:
        if not d["place"]:
            print(f"   {d['pn']:12} {d['description'][:34]:34} fig {d['fig_key']:8} "
                  f"src {d['classified_source']!r:42} note {d['classified_note']!r}")


if __name__ == "__main__":
    main()
