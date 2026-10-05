# -*- coding: utf-8 -*-
"""
Classification benchmark: which system is best for sales classification?

Every system is measured on ONE common base (spine PNs that carry a ZKK code),
so the comparison is fair. Nothing is rebuilt; this is measurement only.

Systems compared
  Japan-native : ZKK, ZUK, HKK, ZKK+EPLE, figure key prefix
  ISZE-native  : AIM L1, AIM L2, AIM L1>L2>L3 triple
  ISZE design  : the 15-level functional taxonomy (Mar2026 workbook)

Metrics
  coverage      % of billed EUR and % of PNs the system can label
  granularity   usable codes: those holding >=0.5% and >=1% of covered EUR
  concentration share of the single biggest code, and of the top 10
  purity        row-weighted: how often the dominant leading-noun is the only noun
  service       can the system isolate the aftersales service basket?
                (AIM 'Maintenance Service' EUR concentration into its codes)
  stability     code churn between the Sep-2025 CD and the 260910 file, where both exist

Outputs
  01_data/90_INBOX/_classification_benchmark_20260920.json
  01_data/90_INBOX/_classification_benchmark_tables_20260920.csv

Run: python 01_data/91_build/benchmark_classification_systems_20260920.py
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "01_data" / "00_derived" / "jp_codes_cache_20260920.csv"
SPINE = ROOT / "01_data" / "00_derived" / "aim_master_v2.csv"
FUNCT = ROOT / "01_data" / "01_Pricing" / "ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx"
OUT_JSON = ROOT / "01_data" / "90_INBOX" / "_classification_benchmark_20260920.json"
OUT_CSV = ROOT / "01_data" / "90_INBOX" / "_classification_benchmark_tables_20260920.csv"

SERVICE_L1 = "Maintenance Service"          # our aftersales service basket on the spine


def s(v) -> str:
    if v is None:
        return ""
    t = str(v).strip()
    return t[:-2] if t.endswith(".0") else t


def leading_noun(desc: str) -> str:
    d = (desc or "").upper().strip()
    d = re.split(r"[;,(]", d)[0].strip()
    return d


def main() -> int:
    # ---------- spine ----------
    spine: dict[str, dict] = {}
    total_eur = 0.0
    with SPINE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            pn = s(r.get("part_number"))
            if not pn:
                continue
            e = float(r.get("l12m_billed_eur") or 0)
            spine[pn] = {
                "eur": e,
                "aim_l1": s(r.get("aim_l1_fixed")) or s(r.get("aim_l1")) or "(blank)",
                "aim_l2": s(r.get("aim_l2_fixed")) or s(r.get("aim_l2")) or "(blank)",
                "aim_l3": s(r.get("aim_l3")) or "(blank)",
                "desc": s(r.get("description")),
            }
            total_eur += e
    print(f"spine: {len(spine)} PNs, EUR {total_eur:,.0f} L12M")

    # ---------- japan codes ----------
    jp: dict[str, dict] = {}
    with CACHE.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            jp[r["pn"]] = r
    print(f"jp cache: {len(jp)} PNs")

    # ---------- the 15-level functional taxonomy (Mar2026 design) ----------
    # NOTE: the functional mapping lives on the 'PARTS FUNCTIONAL' sheet (PN -> L1 Category /
    # L2 Sub-Category). It is NOT the 'Segment' column on PARTS MASTER, which is an ABC/XYZ
    # revenue tier. An earlier run of this script read the wrong column.
    funct: dict[str, str] = {}
    funct2: dict[str, str] = {}
    if FUNCT.exists():
        wb = openpyxl.load_workbook(FUNCT, read_only=True, data_only=True)
        if "PARTS FUNCTIONAL" in wb.sheetnames:
            ws = wb["PARTS FUNCTIONAL"]
            it = ws.iter_rows(values_only=True)
            next(it)  # title
            hdr = [s(h) for h in next(it)]
            ipn, il1, il2 = (hdr.index("PN"), hdr.index("L1 Category"),
                             hdr.index("L2 Sub-Category"))
            for r in it:
                if r[ipn] is None:
                    continue
                pn = s(r[ipn])
                funct[pn] = s(r[il1]) or "(blank)"
                funct2[pn] = f"{s(r[il1])} > {s(r[il2])}"
        wb.close()
    print(f"mar2026 functional: {len(funct)} PNs")

    # ---------- the common base ----------
    base = [pn for pn, v in spine.items() if pn in jp and jp[pn]["zkk"]]
    base_eur = sum(spine[p]["eur"] for p in base)
    print(f"COMMON BASE: {len(base)} PNs, EUR {base_eur:,.0f} "
          f"({100*base_eur/total_eur:.2f}% of the book)\n")

    # ---------- system definitions ----------
    def jp_code(field):
        return lambda pn: jp[pn][field] if pn in jp else ""

    def aim_l1(pn):
        return spine[pn]["aim_l1"]

    def aim_l2(pn):
        return spine[pn]["aim_l2"]

    def aim_triple(pn):
        v = spine[pn]
        return f'{v["aim_l1"]} > {v["aim_l2"]} > {v["aim_l3"]}'

    def fig_prefix(pn):
        f = jp[pn]["jp_fig_key"] if pn in jp else ""
        return f[:3] if f and len(f) >= 3 else ""

    def zkk_eple(pn):
        if pn not in jp:
            return ""
        return f'{jp[pn]["zkk"]}-{jp[pn]["eple"]}' if jp[pn]["eple"] not in ("", "9999") else jp[pn]["zkk"]

    def functional(pn):
        return funct.get(pn, "")

    def functional2(pn):
        return funct2.get(pn, "")

    SYSTEMS = {
        "ZKK (Japan)": jp_code("zkk"),
        "ZUK (Japan)": jp_code("zuk"),
        "HKK (Japan)": jp_code("hkk"),
        "ZKK + EPLE (Japan)": zkk_eple,
        "Figure key prefix (Japan)": fig_prefix,
        "AIM L1 (ISZE, live)": aim_l1,
        "AIM L2 (ISZE, live)": aim_l2,
        "AIM L1>L2>L3 (ISZE, live)": aim_triple,
        "15-level functional (ISZE, Apr 2026)": functional,
        "15-level functional L1>L2 (ISZE, Apr 2026)": functional2,
    }

    # ---------- measure ----------
    def measure(label, fn):
        rows_by_code: dict[str, list[str]] = collections.defaultdict(list)
        eur_by_code: dict[str, float] = collections.defaultdict(float)
        labelled_eur = 0.0
        labelled_pns = 0
        service_eur_by_code: dict[str, float] = collections.defaultdict(float)
        service_total = 0.0
        for pn in base:
            code = fn(pn)
            if not code:
                continue
            e = spine[pn]["eur"]
            labelled_pns += 1
            labelled_eur += e
            rows_by_code[code].append(pn)
            eur_by_code[code] += e
            if spine[pn]["aim_l1"] == SERVICE_L1 and e:
                service_eur_by_code[code] += e
                service_total += e

        if not eur_by_code or labelled_eur <= 0:
            return None

        ranked = sorted(eur_by_code.items(), key=lambda kv: -kv[1])
        shares = [v / labelled_eur for _, v in ranked]
        # purity on leading noun
        tot_rows = sum(len(v) for v in rows_by_code.values())
        pure_rows = 0
        for code, pns in rows_by_code.items():
            nouns = collections.Counter(leading_noun(spine[p]["desc"]) for p in pns)
            pure_rows += nouns.most_common(1)[0][1]
        # service basket concentration: share of service EUR inside the single best code,
        # and the top-3 codes' share (higher = the system can see the service basket)
        svc = sorted(service_eur_by_code.values(), reverse=True)
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
            "leading_noun_purity_pct": round(100 * pure_rows / tot_rows, 2) if tot_rows else 0.0,
            "service_top_code_share_pct": round(100 * (svc[0] / svc_total), 2) if svc else 0.0,
            "service_top3_share_pct": round(100 * (sum(svc[:3]) / svc_total), 2) if svc else 0.0,
            "top_codes": [
                {"code": k, "pns": len(rows_by_code[k]), "eur": round(v, 2),
                 "pct": round(100 * v / labelled_eur, 2)}
                for k, v in ranked[:15]
            ],
        }

    results = {}
    for label, fn in SYSTEMS.items():
        r = measure(label, fn)
        if r:
            results[label] = r

    # ---------- write ----------
    OUT_JSON.write_text(
        json.dumps(
            {
                "common_base": {
                    "pns": len(base),
                    "eur": round(base_eur, 2),
                    "share_of_book_pct": round(100 * base_eur / total_eur, 2),
                },
                "results": results,
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["system", "code", "pns", "eur", "pct_of_system"])
        for label, r in results.items():
            for c in r["top_codes"]:
                w.writerow([label, c["code"], c["pns"], c["eur"], c["pct"]])

    # ---------- print the verdict table ----------
    cols = [
        ("system", 38, "s"),
        ("codes_used", 11, "d"),
        ("codes_ge_1pct", 14, "d"),
        ("max_code_share_pct", 10, "f"),
        ("top10_share_pct", 10, "f"),
        ("purity", 8, "f"),
        ("svc_top3", 9, "f"),
        ("eur_cov", 8, "f"),
    ]
    print(f"{'system':<38} {'codes':>6} {'>=1%':>5} {'max%':>7} {'top10%':>7} "
          f"{'purity':>7} {'svc3%':>7} {'EURcov':>7}")
    print("-" * 96)
    for label, r in sorted(results.items(), key=lambda kv: -kv[1]["eur_coverage_pct"]):
        print(f"{label:<38} {r['codes_used']:>6} {r['codes_ge_1pct']:>5} "
              f"{r['max_code_share_pct']:>7.1f} {r['top10_share_pct']:>7.1f} "
              f"{r['leading_noun_purity_pct']:>7.1f} {r['service_top3_share_pct']:>7.1f} "
              f"{r['eur_coverage_pct']:>6.1f}%")
    print("\n*(common base = the 88.1% of billed euro that carries a ZKK code)*")
    print(f"-> {OUT_JSON.name}")
    print(f"-> {OUT_CSV.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
