# -*- coding: utf-8 -*-
"""Read-only evidence probe for the 43 orphan part numbers on the IE40 price list.

For each part number work out which of the three routes settles it:

  (a) the EPC figure name from classified.csv, read through aim_rules.py
  (b) the exact description already meaning ONE full AIM path on the master
      (>= 3 supporting parts), figure key used only as a veto  -- the method the
      earlier 44-row append used (see finalise_decisions.py there)
  (c) leave unplaced

Writes evidence_43_probe.json / .csv into this folder. Touches nothing else.
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


def aim_from_fig_name(fig_name: str):
    """Exactly the reading classify.py uses: strip the leading figure code, longest rule wins."""
    up = re.sub(r"^\s*[\dA-Z]+\s*-\s*[\dA-Z]+\s*-\s*", "", (fig_name or "").upper())
    for phrase, l1, l2, l3 in RULES:
        if phrase in up:
            return (l1, l2, l3), phrase
    return None, ""


def master_path(r: dict) -> tuple[str, str, str]:
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
    print(f"orphans: {len(orphans)}")

    # ---- master: live leaves, description -> paths, fig_key -> paths
    master_leaves: set[tuple[str, str, str]] = set()
    master_leaf_rows: Counter = Counter()
    M_desc = defaultdict(list)
    M_fig = defaultdict(list)
    master_rows = 0
    master_pns = set()
    with (DER / "aim_master_v2.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            master_rows += 1
            master_pns.add((r.get("part_number") or "").strip().upper())
            p = master_path(r)
            if all(x and x not in PH for x in p):
                master_leaves.add(p)
                master_leaf_rows[p] += 1
                M_desc[(r.get("description") or "").strip()].append(p)
            fk = (r.get("fig_key") or "").strip()
            if fk and all(x and x not in PH for x in p):
                M_fig[fk].append(p)
    print(f"master rows: {master_rows}")
    print(f"orphans with a master row: {len(set(pns) & master_pns)}")

    # ---- overlay
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

    # ---- classified.csv rows for the orphans
    cls = {}
    with (EQ / "classified.csv").open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            k = (r.get("pn") or "").strip().upper()
            if k in pns and k not in cls:
                cls[k] = r

    out = []
    for o in orphans:
        pn = o["part_number"].strip().upper()
        desc = (o["Description"] or "").strip()
        fig_key = (o["fig_key"] or "").strip()
        c = cls[pn]
        fig_name = ""
        if c["aim_source_this_pass"] == "EPC figure name":
            fig_name = (c["aim_note"] or "").strip()

        rec = {
            "pn": pn,
            "description": desc,
            "fig_key": fig_key,
            "abc": (o.get("ABC Code") or "").strip(),
            "list_eur": (o.get("list_eur") or "").strip(),
            "epc_fig_name": fig_name,
            "classified_note": (c["aim_note"] or "").strip(),
            "classified_l1": (c["aim_level_1"] or "").strip(),
            "classified_l2": (c["aim_level_2"] or "").strip(),
            "classified_l3": (c["aim_level_3"] or "").strip(),
            "classified_source": (c["aim_source_this_pass"] or "").strip(),
        }

        # route (a)
        trip, phrase = aim_from_fig_name(fig_name)
        rec["rule_phrase"] = phrase
        if trip:
            rec["route_a_triple"] = list(trip)
            rec["route_a_leaf_on_master"] = trip in master_leaves
            rec["route_a_matches_classified"] = list(trip) == [
                rec["classified_l1"], rec["classified_l2"], rec["classified_l3"]]
        else:
            rec["route_a_triple"] = None
            rec["route_a_leaf_on_master"] = False
            rec["route_a_matches_classified"] = False

        # route (b) -- description agreement, master + overlay, >=3, single
        pool = Counter(M_desc.get(desc, [])) + Counter(C_desc.get(desc, []))
        strong = {k: v for k, v in pool.items() if v >= 3}
        rec["desc_pool"] = [[list(k), v] for k, v in pool.most_common(4)]
        rec["desc_strong_count"] = len(strong)
        if len(strong) == 1:
            (path, support), = strong.items()
            rec["route_b_triple"] = list(path)
            rec["route_b_support_total"] = support
            rec["route_b_support_master"] = Counter(M_desc.get(desc, []))[path]
            rec["route_b_support_overlay"] = Counter(C_desc.get(desc, []))[path]
            rec["route_b_leaf_on_master"] = path in master_leaves
            rec["route_b_master_leaf_rows"] = master_leaf_rows[path]
            fk_paths = Counter(M_fig.get(fig_key, [])) + Counter(C_fig.get(fig_key, []))
            top = fk_paths.most_common(1)[0] if fk_paths else None
            rec["route_b_figkey_top"] = list(top[0]) if top else None
            rec["route_b_figkey_n"] = top[1] if top else 0
            rec["route_b_figkey_disagrees"] = bool(top) and top[0] != path
        else:
            rec["route_b_triple"] = None
            rec["route_b_support_total"] = 0
            rec["route_b_support_master"] = 0
            rec["route_b_support_overlay"] = 0
            rec["route_b_leaf_on_master"] = False
            rec["route_b_master_leaf_rows"] = 0
            rec["route_b_figkey_top"] = None
            rec["route_b_figkey_n"] = 0
            rec["route_b_figkey_disagrees"] = False

        out.append(rec)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "evidence_43_probe.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    with (OUT / "evidence_43_probe.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pn", "description", "fig_key", "abc", "list_eur", "epc_fig_name",
                    "rule_phrase", "route_a", "a_on_master", "a_matches_classified",
                    "route_b", "b_support_total", "b_support_master", "b_support_overlay",
                    "b_leaf_rows", "b_figkey_top", "b_figkey_n", "b_figkey_disagrees",
                    "classified_source", "classified_note"])
        for r in out:
            w.writerow([
                r["pn"], r["description"], r["fig_key"], r["abc"], r["list_eur"],
                r["epc_fig_name"], r["rule_phrase"],
                " > ".join(r["route_a_triple"]) if r["route_a_triple"] else "",
                r["route_a_leaf_on_master"], r["route_a_matches_classified"],
                " > ".join(r["route_b_triple"]) if r["route_b_triple"] else "",
                r["route_b_support_total"], r["route_b_support_master"],
                r["route_b_support_overlay"], r["route_b_master_leaf_rows"],
                " > ".join(r["route_b_figkey_top"]) if r["route_b_figkey_top"] else "",
                r["route_b_figkey_n"], r["route_b_figkey_disagrees"],
                r["classified_source"], r["classified_note"],
            ])

    print()
    print("route (a) available (rule fired):", sum(1 for r in out if r["route_a_triple"]))
    print("   of which the leaf exists on the master:",
          sum(1 for r in out if r["route_a_leaf_on_master"]))
    print("   rule triple differs from classified.csv:",
          [r["pn"] for r in out if r["route_a_triple"] and not r["route_a_matches_classified"]])
    print("route (b) single strong description:",
          sum(1 for r in out if r["route_b_triple"]))
    print("   of which the leaf exists on the master:",
          sum(1 for r in out if r["route_b_leaf_on_master"]))
    print("neither:", [r["pn"] for r in out if not r["route_a_triple"] and not r["route_b_triple"]])
    print()
    print("figure-key vetoes fired:",
          [(r["pn"], r["route_b_figkey_top"]) for r in out if r["route_b_figkey_disagrees"]])
    print()
    for r in out:
        a = " > ".join(r["route_a_triple"]) if r["route_a_triple"] else "-"
        b = " > ".join(r["route_b_triple"]) if r["route_b_triple"] else "-"
        print(f"{r['pn']:12} {r['description'][:30]:30} a[{a[:44]:44}] b[{b[:44]:44}] "
              f"b_sup={r['route_b_support_total']:>3} fk={r['route_b_figkey_top']} "
              f"veto={r['route_b_figkey_disagrees']}")


if __name__ == "__main__":
    main()
