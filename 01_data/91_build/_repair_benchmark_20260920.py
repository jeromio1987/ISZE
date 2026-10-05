# -*- coding: utf-8 -*-
"""
PART B - repair the benchmark artefacts.

1. Recompute the '15-level functional (ISZE, Apr 2026)' row from the real `L1 Category` column of
   sheet 'PARTS FUNCTIONAL', on the same common base as every other system.
2. Record that its coverage is limited to the workbook's own 15,353 April-2026 part numbers.
3. Make the JSON and the CSV agree on that row.
4. Add the Part A price-class concentration results under a clearly named key.

Writes: 01_data/90_INBOX/_classification_benchmark_20260920.json
        01_data/90_INBOX/_classification_benchmark_tables_20260920.csv
Backups already taken as *.bak_pre_classrepair.
"""
from __future__ import annotations

import collections
import csv
import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
SPINE = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
FUNCT = ROOT / "01_data" / "01_Pricing" / "ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx"
JSON_PATH = ROOT / "01_data" / "90_INBOX" / "_classification_benchmark_20260920.json"
CSV_PATH = ROOT / "01_data" / "90_INBOX" / "_classification_benchmark_tables_20260920.csv"
FINAL = ROOT / "01_data" / "90_INBOX" / "_tmp_final_20260920.json"
SERVICE_L1 = "Maintenance Service"
ROW = "15-level functional (ISZE, Apr 2026)"


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    return t[:-2] if t.endswith(".0") else t


def leading_noun(desc: str) -> str:
    d = (desc or "").upper().strip()
    return re.split(r"[;,(]", d)[0].strip()


def main() -> int:
    # ---------------- spine + base ----------------
    spine = {}
    total_eur = 0.0
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("part_number"))
            e = float(r.get("l12m_billed_eur") or 0)
            total_eur += e
            spine[pn] = {"eur": e, "desc": s(r.get("description")),
                         "l1": s(r.get("aim_l1_fixed")) or s(r.get("aim_l1")),
                         "zkk": s(r.get("jp_zkk"))}
    base = [p for p, v in spine.items() if v["zkk"]]
    base_eur = sum(spine[p]["eur"] for p in base)

    # ---------------- the workbook ----------------
    funct, funct2 = {}, {}
    wb = openpyxl.load_workbook(FUNCT, read_only=True, data_only=True)
    ws = wb["PARTS FUNCTIONAL"]
    it = ws.iter_rows(values_only=True)
    next(it)
    hdr = [s(h) for h in next(it)]
    ipn, il1, il2 = hdr.index("PN"), hdr.index("L1 Category"), hdr.index("L2 Sub-Category")
    n_rows = 0
    seen = set()
    for r in it:
        if r[ipn] is None:
            continue
        pn = s(r[ipn])
        if not pn:
            continue
        n_rows += 1
        seen.add(pn)
        funct[pn] = s(r[il1]) or "(blank)"
        funct2[pn] = f"{s(r[il1])} > {s(r[il2])}"
    wb.close()

    # ---------------- measure the row exactly as the benchmark does ----------------
    def measure(label, fn):
        rows_by_code = collections.defaultdict(list)
        eur_by_code = collections.defaultdict(float)
        labelled_eur = 0.0
        labelled_pns = 0
        svc_eur = collections.defaultdict(float)
        for pn in base:
            code = fn(pn)
            if not code:
                continue
            e = spine[pn]["eur"]
            labelled_pns += 1
            labelled_eur += e
            rows_by_code[code].append(pn)
            eur_by_code[code] += e
            if spine[pn]["l1"] == SERVICE_L1 and e:
                svc_eur[code] += e
        ranked = sorted(eur_by_code.items(), key=lambda kv: -kv[1])
        shares = [v / labelled_eur for _, v in ranked]
        tot_rows = sum(len(v) for v in rows_by_code.values())
        pure = 0
        for code, pns in rows_by_code.items():
            nouns = collections.Counter(leading_noun(spine[p]["desc"]) for p in pns)
            pure += nouns.most_common(1)[0][1]
        svc = sorted(svc_eur.values(), reverse=True)
        svc_total = sum(svc) or 1.0
        return {
            "system": label,
            "codes_used": len(rows_by_code),
            "labelled_pns": labelled_pns,
            "pn_coverage_pct": round(100 * labelled_pns / len(base), 2),
            "labelled_eur": round(labelled_eur, 2),
            "eur_coverage_pct": round(100 * labelled_eur / base_eur, 2),
            "codes_ge_0p5pct": sum(1 for x in shares if x >= 0.005),
            "codes_ge_1pct": sum(1 for x in shares if x >= 0.01),
            "max_code_share_pct": round(100 * shares[0], 2),
            "top10_share_pct": round(100 * sum(shares[:10]), 2),
            "leading_noun_purity_pct": round(100 * pure / tot_rows, 2) if tot_rows else 0.0,
            "service_top_code_share_pct": round(100 * (svc[0] / svc_total), 2) if svc else 0.0,
            "service_top3_share_pct": round(100 * (sum(svc[:3]) / svc_total), 2) if svc else 0.0,
            "top_codes": [
                {"code": k, "pns": len(rows_by_code[k]), "eur": round(v, 2),
                 "pct": round(100 * v / labelled_eur, 2)}
                for k, v in ranked
            ],
        }

    row = measure(ROW, lambda pn: funct.get(pn, ""))
    print(f"recomputed {ROW}")
    for k in ("codes_used", "labelled_pns", "pn_coverage_pct", "labelled_eur", "eur_coverage_pct",
              "codes_ge_0p5pct", "codes_ge_1pct", "max_code_share_pct", "top10_share_pct",
              "leading_noun_purity_pct", "service_top_code_share_pct", "service_top3_share_pct"):
        print(f"   {k:<34} {row[k]}")

    # ---------------- load existing JSON, patch only what is required ----------------
    doc = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    prev = doc["results"].get(ROW, {})
    print(f"\nprevious row: codes_used {prev.get('codes_used')} purity "
          f"{prev.get('leading_noun_purity_pct')} eur_cov {prev.get('eur_coverage_pct')}")

    wb_eur_on_spine = sum(spine[p]["eur"] for p in seen if p in spine)
    row["source_sheet"] = "PARTS FUNCTIONAL"
    row["source_column"] = "L1 Category"
    row["coverage_note"] = (
        f"Coverage is limited to the workbook's own {n_rows:,} part numbers from April 2026 "
        f"(01_data/01_Pricing/ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx, sheet "
        f"'PARTS FUNCTIONAL'). This is NOT a full-spine classification: {row['labelled_pns']:,} of "
        f"those part numbers sit on the {len(base):,}-PN common base and carry EUR "
        f"{row['labelled_eur']:,.2f} of the EUR {base_eur:,.2f} base ({row['eur_coverage_pct']}%), "
        f"but the workbook classifies nothing outside its own {n_rows:,} part numbers. The other "
        f"{len(base) - row['labelled_pns']:,} base part numbers are simply absent from the workbook."
    )
    row["coverage_basis"] = {
        "workbook_file": str(FUNCT),
        "workbook_sheet": "PARTS FUNCTIONAL",
        "workbook_data_rows": n_rows,
        "workbook_distinct_pns": len(seen),
        "workbook_eur_on_spine": round(wb_eur_on_spine, 2),
        "common_base_pns": len(base),
        "common_base_eur": round(base_eur, 2),
        "classified_on_base_pns": row["labelled_pns"],
        "classified_on_base_eur": row["labelled_eur"],
    }
    row["repair_note"] = (
        "Values on this row are computed from the workbook's real 'L1 Category' column (collapsed "
        "to the 16 L1 families) on the same common base as every other system in this file. An "
        "earlier run of this benchmark read the 'Segment' column (A-X, B-Y revenue tiers) instead "
        "and reported a purity of 6.7%; that number was wrong and is not reproduced here."
    )
    doc["results"][ROW] = row

    # L1>L2 companion row: recompute too so the pair stays consistent
    row2 = measure("15-level functional L1>L2 (ISZE, Apr 2026)", lambda pn: funct2.get(pn, ""))
    row2["source_sheet"] = "PARTS FUNCTIONAL"
    row2["source_column"] = "L1 Category > L2 Sub-Category"
    row2["coverage_note"] = row["coverage_note"]
    row2["coverage_basis"] = row["coverage_basis"]
    row2["repair_note"] = row["repair_note"]
    doc["results"]["15-level functional L1>L2 (ISZE, Apr 2026)"] = row2

    # ---------------- Part A results into the same file ----------------
    partA = json.loads(FINAL.read_text(encoding="utf-8"))
    doc["price_class_concentration"] = {
        "question": ("Is the claim '79% has price class C' correct, and is price class the right "
                     "analysis axis?"),
        "measured": "2026-09-20",
        "definition": ("Price class is the band that sets the margin we apply, assigned by Japan "
                       "and carried on the price file separately from the base price."),
        "basis_1_japan_cd_unweighted": partA["A1_japan_cd_rows"],
        "basis_2_isze_billed_book_eur": partA["A2_spine_iml_eur"],
        "basis_3_parts_with_a_japan_code_eur": partA["A3_spine_jpclass_new_eur"],
        "zkk_versus_class": {
            "from_japan_price_cd": partA["zkk_from_cd"],
            "from_isze_billed_spine": partA["zkk_from_spine"],
            "zkk_leading_nouns_from_japan_parts_name": partA["zkk_leading_noun_all_top"],
        },
        "verdict": {
            "claim_79pct_class_C": "Not reproduced on any basis measured here.",
            "closest_basis_to_the_claim": (
                "The Japan price CD collapsed to a single letter, on all rows, is 72.3% class C "
                "(72.8% of rows that carry a class). That is the highest C share measured."
            ),
            "right_basis_to_quote": (
                "The billed book weighted by euro, from aim_master_v2.csv column price_class_iml: "
                "46.0% of priced euro is class C, or 50.1% of the whole book. Class is a margin "
                "band, so the money-weighted share is the one that matters commercially."
            ),
            "codes_large_enough_to_chart": {
                "japan_cd_unweighted_ge_1pct": partA["A1_japan_cd_rows"]["codes_ge_1pct_measured"],
                "japan_cd_ge_0p5pct": 6,
                "isze_billed_book_eur_ge_1pct": partA["A2_spine_iml_eur"]["codes_ge_1pct_priced"],
                "parts_with_japan_code_eur_ge_1pct": partA["A3_spine_jpclass_new_eur"]["codes_ge_1pct"],
                "parts_with_japan_code_eur_ge_0p5pct": partA["A3_spine_jpclass_new_eur"]["codes_ge_0p5pct"],
            },
        },
        "sources": {
            "japan_price_cd": partA["A1_japan_cd_rows"]["source"],
            "spine": str(SPINE),
            "jp_code_cache": str(ROOT / "01_data" / "00_derived" / "jp_codes_cache_20260920.csv"),
        },
    }
    doc.setdefault("artifact_notes", {})["price_class_and_functional_repair"] = (
        "2026-09-20. The 'price_class_concentration' key was added and the 15-level functional rows "
        "were recomputed from the workbook's 'L1 Category' column. The readable report "
        "CLASSIFICATION_BENCHMARK_2026-09-20.md was NOT modified."
    )
    doc["csv_layout_note"] = (
        "The CSV mirrors each system's top_codes exactly, then repeats every row's scalar metrics as "
        "rows whose system is prefixed 'METRICS — ' with the metric name in the code column and the "
        "value in the pns column."
    )
    JSON_PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n-> {JSON_PATH}")

    # ---------------- CSV: same top codes, plus a METRICS block ----------------
    metric_names = ["codes_used", "codes_ge_0p5pct", "codes_ge_1pct", "max_code_share_pct",
                    "top10_share_pct", "leading_noun_purity_pct", "service_top_code_share_pct",
                    "service_top3_share_pct", "eur_coverage_pct"]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["system", "code", "pns", "eur", "pct_of_system"])
        for label, r in doc["results"].items():
            for c in r["top_codes"][:15]:
                w.writerow([label, c["code"], c["pns"], c["eur"], c["pct"]])
        for label, r in doc["results"].items():
            for m in metric_names:
                w.writerow([f"METRICS — {label}", m, r.get(m), "", ""])
    print(f"-> {CSV_PATH}")

    # ---------------- verify agreement ----------------
    csv_tops = collections.defaultdict(list)
    csv_metrics = collections.defaultdict(dict)
    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["system"].startswith("METRICS — "):
                csv_metrics[r["system"][len("METRICS — "):]][r["code"]] = r["pns"]
            else:
                csv_tops[r["system"]].append((r["code"], r["pns"], r["eur"], r["pct_of_system"]))
    ok = True
    for label, r in doc["results"].items():
        j = [(c["code"], str(c["pns"]), str(c["eur"]), str(c["pct"])) for c in r["top_codes"][:15]]
        c = [tuple(x) for x in csv_tops.get(label, [])]
        if j != c:
            ok = False
            print(f"MISMATCH top codes: {label}")
        for m in metric_names:
            if str(csv_metrics.get(label, {}).get(m)) != str(r.get(m)):
                ok = False
                print(f"MISMATCH metric {label} {m}: json={r.get(m)} csv="
                      f"{csv_metrics.get(label, {}).get(m)}")
    print(f"\nJSON/CSV agreement across {len(doc['results'])} systems: "
          f"{'OK' if ok else 'FAILED'}")
    print(f"functional row now: codes {row['codes_used']} purity {row['leading_noun_purity_pct']} "
          f"eur_cov {row['eur_coverage_pct']} max {row['max_code_share_pct']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
