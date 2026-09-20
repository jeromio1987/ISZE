#!/usr/bin/env python3
"""AIM repertoire map - payload builder.

Builds the embedded payload for ISZE_AIM_Repertoire_Map_2026-09-17.html.

Basis (single, locked, same as the shipped revision pack):
  price_bp_weighted_compare_pn.csv, in_scope == True, window 2025-07-01..2026-06-30
  AIM tree: aim_pn_classification_v2.csv -> catalog_l1 / catalog_l2 / catalog_l3
  Distributor: gps_db_label (the trading entity the pricing enquiry was run on)

Every in-scope row is kept. A part number with no catalogue node is labelled
UNCLASSIFIED and carried, never dropped, so the level-1 rows sum to the shipped
EUR 34,993,609.39 and the step to EUR 1,652,140.71.

Output: payload.json in this folder. Read-only over 01_data/00_derived.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
HERE = ISZE / "02_dashboards" / "pricing" / "_build" / "aim_repertoire_map_2026-09-17"

PN_FILE = D / "price_bp_weighted_compare_pn.csv"
TREE_FILE = D / "aim_pn_classification_v2.csv"
OUT = HERE / "payload.json"

FX = 163.7
UNCLASSIFIED_L1 = "UNCLASSIFIED"
NO_L3 = "Not classified at this level"

# Published revision on this base - the payload must reproduce both.
PUBLISHED_STEP = 1652140.71
PUBLISHED_BILLED = 34993609.39
PUBLISHED_PCT = 5.9616


def main() -> int:
    import csv

    # ---------------------------------------------------------------- tree
    tree: dict[str, tuple[str, str, str]] = {}
    tree_rows = 0
    for r in csv.DictReader(open(TREE_FILE, newline="", encoding="utf-8-sig")):
        tree_rows += 1
        pn = (r["part_number"] or "").strip()
        if not pn:
            continue
        l1 = (r["catalog_l1"] or "").strip() or UNCLASSIFIED_L1
        l2 = (r["catalog_l2"] or "").strip() or NO_L3
        l3 = (r["catalog_l3"] or "").strip() or NO_L3
        tree[pn] = (l1, l2, l3)

    # ---------------------------------------------------------------- rows
    # aggregate to one row per (distributor, part number)
    agg: dict[tuple[str, str], dict] = {}
    desc_count: dict[str, Counter] = defaultdict(Counter)
    country_of: dict[str, str] = {}
    in_scope_rows = 0
    billed_total = 0.0
    prior_total = 0.0
    new_total = 0.0
    step_total = 0.0
    unpriced_lines = 0
    unpriced_eur = 0.0

    for r in csv.DictReader(open(PN_FILE, newline="", encoding="utf-8-sig")):
        if str(r.get("in_scope", "")).strip().lower() != "true":
            continue
        in_scope_rows += 1
        pn = (r["part_number"] or "").strip().zfill(10)
        l1, l2, l3 = tree.get(pn, (UNCLASSIFIED_L1, NO_L3, NO_L3))
        db = (r["gps_db_label"] or "").strip() or "Unknown"
        country_of.setdefault(db, (r.get("country") or "").strip())

        qty = float(r["billed_qty"] or 0)
        eur = float(r["net_sales_value"] or 0)
        billed_total += eur

        priced = bool((r["bp_new_jpy"] or "").strip()) and bool(
            (r["bp_prior_revised"] or "").strip())
        prior = qty * float(r["bp_prior_revised"]) / FX if priced else 0.0
        new = qty * float(r["bp_new_jpy"]) / FX if priced else 0.0
        step = float(r["value_eur_step"] or 0)
        if priced:
            prior_total += prior
            new_total += new
            step_total += step
        else:
            unpriced_lines += 1
            unpriced_eur += eur

        k = (db, pn)
        a = agg.get(k)
        if a is None:
            a = agg[k] = {
                "l1": l1, "l2": l2, "l3": l3,
                "qty": 0.0, "qty_priced": 0.0, "eur": 0.0, "step": 0.0,
                "prior": 0.0, "new": 0.0, "priced": False,
            }
        a["qty"] += qty
        a["qty_priced"] += qty if priced else 0.0
        a["eur"] += eur
        a["step"] += step
        a["prior"] += prior
        a["new"] += new
        a["priced"] = a["priced"] or priced
        d = (r["billed_description"] or "").strip()
        if d:
            desc_count[pn][d] += 1

    network_pct = 100 * (new_total / prior_total - 1) if prior_total else 0.0

    # ---------------------------------------------------------------- vocab
    tree_pn = len(tree)
    tree_l1 = len({v[0] for v in tree.values()})
    tree_l3 = len({v[2] for v in tree.values()})
    billed_in_tree = sum(1 for p in {k[1] for k in agg} if p in tree)
    l1_names = sorted({v["l1"] for v in agg.values()})
    l2_names = sorted({(v["l1"], v["l2"]) for v in agg.values()})
    l3_names = sorted({(v["l1"], v["l2"], v["l3"]) for v in agg.values()})
    db_names = sorted({k[0] for k in agg})
    pn_names = sorted({k[1] for k in agg})

    l1_i = {n: i for i, n in enumerate(l1_names)}
    l2_i = {n: i for i, n in enumerate(l2_names)}
    l3_i = {n: i for i, n in enumerate(l3_names)}
    db_i = {n: i for i, n in enumerate(db_names)}
    pn_i = {n: i for i, n in enumerate(pn_names)}

    desc = []
    for pn in pn_names:
        c = desc_count.get(pn)
        d = c.most_common(1)[0][0] if c else ""
        desc.append(d[:46])

    # fleet denominator per distributor, from the catalogue matrix (2025 uio_units).
    # The pricing file names the trading entity (ISD / Imotors / UMI); the matrix
    # names the country. Map the two explicitly - never a silent join.
    db_uio_code = {
        "ITUK": "ITUK", "IUK": "IUK", "ISD": "GERMANY", "Imotors": "PORTUGAL",
        "IBX": "BELGIUM", "UTI": "UTI", "UMI": "UMI", "Ireland": "IRELAND",
        "Sverige": "SWEDEN", "Norway": "NORWAY", "RSA": "GREECE", "GA": "ARMENIA",
        "CBC": "KAZAKHSTAN", "KIMA": "PALESTINE", "Danmark": "DENMARK",
        "Nordic FI": "FINLAND", "AutoWallis": "HUNGARY", "ROM Auto": "ROMANIA",
        "GasanZammit": "MALTA", "BL Iceland": "ICELAND", "Loutsios": "CYPRUS",
        "CIS-KTK": "UKRAINE",
    }
    uio: dict[str, int | None] = {}
    for r in csv.DictReader(open(D / "aim_catalog_db_matrix.csv", newline="",
                                 encoding="utf-8-sig")):
        if r["scheme_basis"] != "catalog_full":
            continue
        code = (r["distributor_code"] or "").strip()
        if not code or code.startswith("Network"):
            continue
        ok = r["fleet_denominator_available"].strip().lower() in ("true", "1")
        uio.setdefault(code, int(float(r["uio_units_2025"] or 0)) if ok else None)
    db_uio = [uio.get(db_uio_code.get(n, ""), None) for n in db_names]

    rows = []
    for (db, pn), v in agg.items():
        rows.append([
            pn_i[pn], l1_i[v["l1"]], l2_i[(v["l1"], v["l2"])],
            l3_i[(v["l1"], v["l2"], v["l3"])], db_i[db],
            round(v["qty"], 1), round(v["eur"], 2),
            round(v["step"], 2), round(v["prior"], 2), round(v["new"], 2),
            round(v["qty_priced"], 1), 1 if v["priced"] else 0,
        ])
    rows.sort()

    # ---------------------------------------------------------------- checks
    sum_eur = sum(r[6] for r in rows)
    sum_step = sum(r[7] for r in rows)
    sum_prior = sum(r[8] for r in rows)
    sum_new = sum(r[9] for r in rows)
    recomputed_pct = 100 * (sum_new / sum_prior - 1) if sum_prior else 0.0

    checks = {
        "in_scope_rows": in_scope_rows,
        "aggregated_rows": len(rows),
        "part_numbers": len(pn_names),
        "distributors": len(db_names),
        "l1_nodes": len(l1_names),
        "l2_nodes": len(l2_names),
        "l3_nodes": len(l3_names),
        "billed_eur": round(sum_eur, 2),
        "step_eur": round(sum_step, 2),
        "weighted_pct": round(recomputed_pct, 4),
        "unpriced_lines": unpriced_lines,
        "unpriced_eur": round(unpriced_eur, 2),
    }
    checks["billed_matches_published"] = abs(sum_eur - PUBLISHED_BILLED) < 0.05
    checks["step_matches_published"] = abs(sum_step - PUBLISHED_STEP) < 0.6
    checks["pct_matches_published"] = abs(round(recomputed_pct, 4) - PUBLISHED_PCT) < 0.01
    checks["priced_rows"] = sum(1 for r in rows if r[11])
    checks["rows_unpriced_only"] = sum(1 for r in rows if not r[11])

    payload = {
        "meta": {
            "built": datetime.now(timezone.utc).isoformat(),
            "window": ["2025-07-01", "2026-06-30"],
            "window_label": "1 Jul 2025 to 30 Jun 2026",
            "fx_jpy_per_eur": FX,
            "source": "price_bp_weighted_compare_pn.csv (in_scope) x "
                      "aim_pn_classification_v2.csv",
            "l1": l1_names,
            "l2": [list(x) for x in l2_names],
            "l3": [list(x) for x in l3_names],
            "db": db_names,
            "db_country": [country_of.get(n, "") for n in db_names],
            "db_uio": db_uio,
            "pn": pn_names,
            "desc": desc,
            "unclassified_l1": UNCLASSIFIED_L1,
            "no_l3": NO_L3,
            "residual_l1": [UNCLASSIFIED_L1, "Other / review"],
            "repertoire": {
                "tree_rows": tree_rows,
                "tree_part_numbers": tree_pn,
                "tree_l1": tree_l1,
                "tree_l3": tree_l3,
                "billed_part_numbers": len(pn_names),
                "billed_in_tree": billed_in_tree,
                "classified_not_billed": tree_pn - billed_in_tree,
            },
            "checks": checks,
            "caveats": [
                "The percentage is a base-price move on the quantity-weighted prior "
                "base price. It is not a revenue, margin or elasticity outcome.",
                "Parts billed euro covers every in-scope line; the percentage covers "
                "only lines priced on both sides, which is stated on every panel.",
                "The AIM tree classifies 164,609 part numbers. Only "
                f"{len(pn_names):,} of them billed in this window, so the tree is not "
                "the whole catalogue and this page does not pretend it is.",
                "A part number with no catalogue node is labelled UNCLASSIFIED and "
                "carried, so nothing is dropped by the classification.",
                "Israel is UMI (1797) and UTI (1799), never blended.",
                "The commercial score (contested or captive, per part per market) is "
                "a separate axis and is not built as columns yet, so this page cannot "
                "colour a part as contested.",
            ],
        },
        "rows": rows,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    OUT.write_text(blob, encoding="utf-8")

    print("=" * 78)
    print("AIM REPERTOIRE MAP - PAYLOAD")
    print("=" * 78)
    print(f"in-scope lines           : {in_scope_rows:,}")
    print(f"rows (distributor x part): {len(rows):,}")
    print(f"part numbers             : {len(pn_names):,}")
    print(f"distributors             : {len(db_names):,}")
    print(f"tree nodes L1/L2/L3       : {len(l1_names)}/{len(l2_names)}/{len(l3_names)}")
    print()
    print(f"parts billed EUR         : {sum_eur:>16,.2f}  (published {PUBLISHED_BILLED:,.2f})")
    print(f"step EUR                 : {sum_step:>16,.2f}  (published {PUBLISHED_STEP:,.2f})")
    print(f"weighted                 : {recomputed_pct:>15.4f}%  (published {PUBLISHED_PCT}%)")
    print()
    print(f"cannot move (no price)   : {unpriced_lines:,} lines, EUR {unpriced_eur:,.2f}")
    print()
    print(f"repertoire               : {tree_rows:,} tree rows, {tree_pn:,} part numbers, "
          f"{tree_l1} L1, {tree_l3} L3 leaves")
    print(f"  billed in window       : {billed_in_tree:,} part numbers "
          f"({100*billed_in_tree/tree_pn:.2f}% of the tree)")
    print(f"  classified, no billing : {tree_pn-billed_in_tree:,} part numbers")
    print()
    print(f"checks : {checks}")
    print(f"payload: {len(blob)/1e6:.2f} MB -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
