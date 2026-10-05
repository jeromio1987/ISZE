"""Build brake_corner_data.json: every number the page shows, read from source.

Three files are read, read-only:
  01_data/00_derived/parts_catalog_dimension.csv
      part_number, fig_key, fig_key_label, pms_category
  01_data/00_derived/sales_by_db_fig_key_year.csv
      year, distributor_code, fig_key, fig_key_label, billed_qty, net_sales_eur,
      distinct_pns
  01_data/00_derived/price_bp_weighted_compare_pn.csv
      part_number, billed_description, billed_qty, net_sales_value,
      distributor_code, class_mapped

Method
------
The supplier's billed description names the part in words.  Each callout is
therefore anchored on a billed description, not on a figure key: the part numbers
billed under that description are collected from the price file, each one is
joined through the catalogue bridge to whatever figure key it sits under, and the
billed euro and quantity for those figure keys are read out of the sales file.
That is what makes "411-025, EUR 2.81M" a traceable statement rather than a guess.

A callout whose part has no figure key is marked fig_key = null and says so; a
callout whose part is never billed at all is marked billed_eur = null.  Neither is
dropped, and neither is invented.
"""
from __future__ import annotations

import collections
import csv
import json
import os
import re

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
D = os.path.join(ISZE, "01_data", "00_derived")
CAT = os.path.join(D, "parts_catalog_dimension.csv")
SALES = os.path.join(D, "sales_by_db_fig_key_year.csv")
PRICE = os.path.join(D, "price_bp_weighted_compare_pn.csv")
HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------- #
# the callouts.  `desc_re` names the part in the supplier's own billed wording.
# --------------------------------------------------------------------------- #
CALLOUTS = [
    {
        "id": "A",
        "part": "Brake disc (front)",
        "kind": "disc",
        "desc_re": r"^ROTOR;\s*DISC BRK,FRT\s*$",
        "desc_used": "ROTOR; DISC BRK,FRT",
    },
    {
        "id": "B",
        "part": "Brake pads (front)",
        "kind": "pads",
        "desc_re": r"^PAD KIT;\s*CALIPER,DISC BRK,FRT\s*$",
        "desc_used": "PAD KIT; CALIPER,DISC BRK,FRT",
    },
    {
        "id": "C",
        "part": "Brake pads, without shim and clip",
        "kind": "pads",
        "desc_re": r"^PAD KIT;\s*DISC BRK,W/O SHIM\s*&\s*CLIP\s*$",
        "desc_used": "PAD KIT; DISC BRK,W/O SHIM & CLIP",
    },
    {
        "id": "D",
        "part": "Brake caliper (front)",
        "kind": "caliper",
        "desc_re": r"^CALIPER;\s*FRT DISC BRK\s*$",
        "desc_used": "CALIPER; FRT DISC BRK",
    },
    {
        "id": "E",
        "part": "Road wheel",
        "kind": "wheel",
        "desc_re": r"^WHEEL;\s*DISC(,AL)?\s*$",
        "desc_used": "WHEEL; DISC,AL and WHEEL; DISC (not split by axle)",
    },
    {
        "id": "F",
        "part": "Tyre",
        "kind": "tyre",
        "desc_re": r"^TYRE",
        "desc_used": None,
    },
]

print("=== reading the price file ===")
fam_pns = collections.defaultdict(collections.Counter)
fam_qty = collections.defaultdict(float)
fam_eur = collections.defaultdict(float)
fam_db = collections.defaultdict(collections.Counter)
n_price = 0
for r in csv.DictReader(open(PRICE, newline="", encoding="utf-8-sig")):
    n_price += 1
    d = (r["billed_description"] or "").strip()
    for c in CALLOUTS:
        if not re.match(c["desc_re"], d, re.I):
            continue
        e = float(r["net_sales_value"] or 0)
        fam_pns[c["id"]][(r["part_number"] or "").strip()] += e
        fam_qty[c["id"]] += float(r["billed_qty"] or 0)
        fam_eur[c["id"]] += e
        fam_db[c["id"]][r["distributor_code"] or r["gps_db_label"] or "-"] += e
print("price rows %d" % n_price)
for c in CALLOUTS:
    print("  %s %-38s pns %-4d qty %-9s EUR %12s"
          % (c["id"], c["part"], len(fam_pns[c["id"]]), format(fam_qty[c["id"]], ",.0f"),
             format(fam_eur[c["id"]], ",.0f")))

print()
print("=== reading the catalogue bridge ===")
pn_to_keys = collections.defaultdict(list)
n_cat = 0
for r in csv.DictReader(open(CAT, newline="", encoding="utf-8-sig")):
    n_cat += 1
    pn = (r["part_number"] or "").strip()
    if pn:
        pn_to_keys[pn].append((r["fig_key"] or "", r["fig_key_label"] or "",
                               r["pms_category"] or ""))
print("catalogue rows %d  distinct part numbers %d" % (n_cat, len(pn_to_keys)))

print()
print("=== reading the sales file ===")
key_eur = collections.defaultdict(float)
key_qty = collections.defaultdict(float)
key_pns = collections.defaultdict(int)
key_label = collections.defaultdict(collections.Counter)
key_db = collections.defaultdict(collections.Counter)
key_year = collections.defaultdict(lambda: collections.defaultdict(float))
n_sales = 0
for r in csv.DictReader(open(SALES, newline="", encoding="utf-8-sig")):
    n_sales += 1
    k = (r["fig_key"] or "").strip()
    if not k or k == "unmapped":
        continue
    key_eur[k] += float(r["net_sales_eur"] or 0)
    key_qty[k] += float(r["billed_qty"] or 0)
    key_pns[k] = max(key_pns[k], int(r["distinct_pns"] or 0))
    key_label[k][r["fig_key_label"]] += float(r["net_sales_eur"] or 0)
    key_db[k][r["distributor_code"]] += float(r["net_sales_eur"] or 0)
    key_year[k][r["year"]] += float(r["net_sales_eur"] or 0)
print("sales rows %d   figure keys with billing %d   total EUR %s"
      % (n_sales, len(key_eur), format(sum(key_eur.values()), ",.0f")))

# --------------------------------------------------------------------------- #
# assemble
# --------------------------------------------------------------------------- #
out = {
    "sources": {
        "parts_catalog_dimension.csv":
            "part_number, fig_key, fig_key_label, pms_category, "
            "classification_source, pr00_family, pr00_group, pr00_level3_type, "
            "pms_registry, in_bvp_catalog",
        "sales_by_db_fig_key_year.csv":
            "year, distributor_code, fig_key, fig_key_label, billed_qty, "
            "net_sales_eur, distinct_pns",
        "price_bp_weighted_compare_pn.csv":
            "customer_code, sold_to_names, distributor_code, gps_db_label, country, "
            "region, scope, network_role, in_scope, is_non_parts, is_direct_account, "
            "part_number, billed_description, billed_qty, net_sales_value, "
            "class_new_raw, bp_new_class, class_mapped, unpriced_reason, bp_new_jpy, "
            "bp_prior_revised, bp_prior_billed, delta_jpy, delta_pct, value_jpy, "
            "value_eur_step",
    },
    "period": "all years present in the sales file (2023 to 2026 to date)",
    "unit_note": ("billed_eur is net sales value in euro as recorded in the billing "
                  "file; billed_qty is the number of pieces billed. Both cover every "
                  "distributor in the file."),
    "callouts": [],
}

for c in CALLOUTS:
    pns = fam_pns[c["id"]]
    hits = collections.Counter()
    matched_pns = 0
    for pn, e in pns.items():
        for fk, fl, cat in pn_to_keys.get(pn, []):
            hits[(fk, fl, cat)] += e
            matched_pns += 1
    keys = []
    for (fk, fl, cat), e in hits.most_common(4):
        keys.append({
            "fig_key": fk,
            "fig_key_label": fl,
            "pms_category": cat or None,
            "billed_eur": round(key_eur.get(fk, 0.0), 2) if fk in key_eur else None,
            "billed_qty": round(key_qty.get(fk, 0.0), 1) if fk in key_qty else None,
            "distinct_pns": key_pns.get(fk) or None,
            "by_year": ({y: round(v, 2) for y, v in sorted(key_year[fk].items())}
                        if fk in key_year else None),
            "top_distributors": ([list(x) for x in key_db[fk].most_common(4)]
                                 if fk in key_db else None),
            "part_number_eur_share": round(e, 2),
        })
    entry = {
        "id": c["id"],
        "part": c["part"],
        "kind": c["kind"],
        "described_in_billing_as": c["desc_used"],
        "part_numbers_billed": len(pns),
        "billed_qty_own_lines": round(fam_qty[c["id"]], 1),
        "billed_eur_own_lines": round(fam_eur[c["id"]], 2),
        "top_part_numbers": [[pn, round(e, 2)] for pn, e in pns.most_common(5)],
        "distributors": [list(x) for x in fam_db[c["id"]].most_common(5)],
        "part_numbers_matched_in_catalogue": matched_pns,
        "fig_keys": keys,
        "fig_key": keys[0]["fig_key"] if keys else None,
        "fig_key_label": keys[0]["fig_key_label"] if keys else None,
        "pms_category": keys[0]["pms_category"] if keys else None,
        "billed_eur": keys[0]["billed_eur"] if keys else None,
        "billed_qty": keys[0]["billed_qty"] if keys else None,
        "distinct_pns": keys[0]["distinct_pns"] if keys else None,
    }
    if not keys:
        entry["fig_key_note"] = ("No figure key in the parts catalogue covers this part, "
                                 "so the figure key is not shown. The billed figures "
                                 "beside it come from the billing file only.")
    if not pns:
        entry["billing_note"] = ("No part of this kind is billed anywhere in the "
                                 "billing file, so this part has no billed figure at all.")
    out["callouts"].append(entry)
    print()
    print("%s  %-38s" % (c["id"], c["part"]))
    print("   billed as       : %s" % (c["desc_used"] or "nothing - never billed"))
    print("   part numbers    : %d billed, %d matched into the catalogue"
          % (len(pns), matched_pns))
    print("   figure key      : %s %s" % (entry["fig_key"], entry["fig_key_label"] or ""))
    if entry["billed_eur"] is not None:
        print("   what we billed  : EUR %s over %s pieces"
              % (format(entry["billed_eur"], ",.0f"),
                 format(entry["billed_qty"], ",.0f")))
    if entry["top_part_numbers"]:
        print("   largest parts   : %s"
              % ", ".join("%s EUR %s" % (p, format(e, ",.0f"))
                          for p, e in entry["top_part_numbers"][:3]))

# A figure key whose label does not describe the part is a real condition in this
# catalogue (the front caliper bills under a key labelled "Brake disc", and the road
# wheel under "Other mechanical").  Test it on the DISTINCTIVE noun of the part, not
# on any shared word: "Brake caliper" and "Brake disc" both contain "brake", so
# matching on any shared word would wrongly call that a fit.
EXPECT_KEYWORDS = {
    "A": ["disc", "rotor"],
    "B": ["pad"],
    "C": ["pad"],
    "D": ["caliper"],
    "E": ["wheel", "rim"],
    "F": ["tyre", "tire"],
}


def label_describes_part(label, cid):
    if not label:
        return False
    low = label.lower()
    return any(k in low for k in EXPECT_KEYWORDS.get(cid, []))


for entry in out["callouts"]:
    entry["fig_key_label_describes_part"] = label_describes_part(
        entry.get("fig_key_label"), entry["id"])
    if entry.get("fig_key") and not entry["fig_key_label_describes_part"]:
        entry["fig_key_note"] = (
            "Catalogue label mismatch: this part bills under the figure key %s, which "
            "the parts catalogue labels '%s' - a label that does not describe it. The "
            "key and its billed euro are stated as the catalogue has them."
            % (entry["fig_key"], entry["fig_key_label"]))
    # the two figures that must never be confused: the whole figure key, and the
    # lines that are actually the part drawn here
    if entry.get("billed_eur") and entry.get("billed_eur_own_lines") is not None:
        entry["fig_key_eur"] = entry["billed_eur"]
        entry["fig_key_qty"] = entry["billed_qty"]
        entry["own_lines_share_of_fig_key_pct"] = round(
            100.0 * entry["billed_eur_own_lines"] / max(1e-9, entry["billed_eur"]), 1)

with open(os.path.join(HERE, "brake_corner_data.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1)
print()
print("wrote", os.path.join(HERE, "brake_corner_data.json"))
print("=== DONE ===")
