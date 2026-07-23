# -*- coding: utf-8 -*-
"""One-off IDS checklist inspection."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import xlrd
from openpyxl import load_workbook

BASE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\Data\90_INBOX\IDS_2026")
OUT = Path(__file__).with_name("_checklist_inspect_out.txt")


def p(*args):
    line = " ".join(str(a) for a in args)
    print(line)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wipe():
    OUT.write_text("", encoding="utf-8")


def hungary():
    p("=== 1) HUNGARY ===")
    hu = BASE / "reports" / "evaluation_result" / "2026 IDS Evaluation Result Report_Hungary.xls"
    wb = xlrd.open_workbook(str(hu), formatting_info=False)
    sh = wb.sheet_by_index(0)
    p("file", hu)
    p("sheet", sh.name, "nrows", sh.nrows, "ncols", sh.ncols)
    # row1 (0) title; row2 (1) dealer numbers; row3 (2) dealer names typically
    names = []
    for c in range(3, sh.ncols):
        v = sh.cell_value(2, c)
        if v not in (None, ""):
            names.append((c, str(v).strip()))
    p("dealer name cells on row3:", len(names))
    for c, n in names[:5]:
        p("  sample", c, repr(n)[:60])
    blank_names = sum(1 for _, n in names if not n)
    # Also check if some dealer cols have empty names but scores
    # Find total row
    total_row = None
    for r in range(sh.nrows):
        for c in (1, 2):
            if str(sh.cell_value(r, c) or "").strip().lower() == "total":
                # prefer Score (Original) row ~12
                label = str(sh.cell_value(r, 2) or sh.cell_value(r, 1) or "")
                if "score" in label.lower() or label.strip().lower() == "total":
                    total_row = r
    # better: scan col C for 'Score (Original)'
    for r in range(sh.nrows):
        lab = str(sh.cell_value(r, 2) or "")
        if "score (original)" in lab.lower() or lab.strip().lower() == "total":
            # row 13 in DK is Score Original / Total points
            if "original" in lab.lower() or (lab.strip().lower() == "total" and r > 200):
                total_row = r
                break
    # DK: row 13 (index 12) is Score (Original)
    for r in range(10, 20):
        p(f"  meta/score row {r+1}: C={sh.cell_value(r,2)!r} D={sh.cell_value(r,3)!r}")

    # Use row index 12 (Excel 13) as Score Original
    score_row = 12
    totals = []
    dealer_cols = [c for c, _ in names] if names else list(range(3, min(3 + 25, sh.ncols)))
    if not names:
        # fallback: use numeric headers on row2
        dealer_cols = [c for c in range(3, sh.ncols) if sh.cell_value(1, c) not in (None, "")]
        names = [(c, str(sh.cell_value(2, c) or "").strip()) for c in dealer_cols]

    for c, n in names:
        t = sh.cell_value(score_row, c)
        totals.append((n, t))
    numeric = [float(t) for _, t in totals if isinstance(t, (int, float))]
    p("score_row Excel", score_row + 1, "n_dealers", len(totals), "n_numeric", len(numeric))
    if numeric:
        p("unique totals", len(set(round(x, 4) for x in numeric)))
        p("min", min(numeric), "max", max(numeric), "mean", round(sum(numeric) / len(numeric), 2))
        ctr = Counter(round(x, 2) for x in numeric)
        p("top value frequencies:", ctr.most_common(5))
        identical = len(set(round(x, 4) for x in numeric)) == 1
        p("ALL IDENTICAL?", identical)
    blank_name_cols = [(c, t) for (c, n), (_, t) in zip(names, totals) if not n]
    p("blank dealer names on row3:", len([n for _, n in names if not n]))

    # Source file count
    src = BASE / "Hungary" / "IDS self evaluation reports Hungary 2026"
    files = list(src.rglob("*.xlsx")) + list(src.rglob("*.xls"))
    files = [f for f in files if not f.name.startswith("~$")]
    p("HU source workbooks:", len(files), "under", src)


def iuk():
    p("\n=== 3) IUK blank names ===")
    path = BASE / "reports" / "evaluation_result" / "2026 IDS Evaluation Result Report_IUK.xls"
    wb = xlrd.open_workbook(str(path), formatting_info=False)
    sh = wb.sheet_by_index(0)
    names = []
    for c in range(3, sh.ncols):
        v = sh.cell_value(2, c)
        names.append((c, str(v).strip() if v not in (None, "") else ""))
    # trim trailing empties
    while names and not names[-1][1] and sh.cell_value(12, names[-1][0]) in (None, ""):
        names.pop()
    blank = [(c, n) for c, n in names if not n]
    filled = [(c, n) for c, n in names if n]
    p("IUK report dealers (cols with name or score):", len(names))
    p("blank names:", len(blank), "filled:", len(filled))
    # check scores on blank name cols
    for c, _ in blank[:15]:
        score = sh.cell_value(12, c)
        num = sh.cell_value(1, c)
        p(f"  blank col {c} dealer#={num} score={score}")
    # Source: filename vs cover
    iuk_dir = BASE / "IUK"
    src_files = sorted(
        [
            f
            for f in iuk_dir.iterdir()
            if f.is_file() and f.suffix.lower() in {".xlsx", ".xls"} and not f.name.startswith("~$")
        ]
    )
    p("IUK source files:", len(src_files))
    # Try reading cover dealer names for a few .xls that often lack cover parse
    from build_ids_result_report import parse_dealer_workbook, collect_dealer_files

    files = collect_dealer_files(iuk_dir)
    blank_parsed = []
    for f in files:
        d = parse_dealer_workbook(f)
        nm = (d.meta.get("dealer_name") if d.meta else None) or ""
        display = d.name
        if not str(nm).strip():
            blank_parsed.append((f.name, display, d.error))
    p("dealers with blank cover meta dealer_name:", len(blank_parsed), "/", len(files))
    for item in blank_parsed[:20]:
        p("  ", item)


def be_nl_lu():
    p("\n=== 2) BE / NL / LU ===")
    be_dir = BASE / "BE" / "BE"
    be_files = [
        f
        for f in be_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".xlsx", ".xls"} and not f.name.startswith("~$")
    ]
    nl_dir = BASE / "NL"
    nl_files = [
        f
        for f in nl_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".xlsx", ".xls"} and not f.name.startswith("~$")
    ]
    p("BE dealer xlsx:", len(be_files))
    p("NL dealer xlsx:", len(nl_files))
    # Huberty = Luxembourg typically
    for f in be_files:
        if any(k in f.name.lower() for k in ("huberty", "lux", "luxembourg", " lx")):
            p("  BE LU candidate:", f.name)
    # report dealer counts
    for country in ("BE", "NL"):
        path = BASE / "reports" / "evaluation_result" / f"2026 IDS Evaluation Result Report_{country}.xls"
        wb = xlrd.open_workbook(str(path), formatting_info=False)
        sh = wb.sheet_by_index(0)
        names = [str(sh.cell_value(2, c)).strip() for c in range(3, sh.ncols) if sh.cell_value(2, c) not in (None, "")]
        p(f"{country} report dealer names:", len(names))
    # LU folder?
    for cand in ("LU", "LX", "Luxembourg", "Luxemburg"):
        p(f"folder {cand} exists?", (BASE / cand).is_dir())


def romania():
    p("\n=== 5) ROMANIA ===")
    path = BASE / "reports" / "evaluation_result" / "2026 IDS Evaluation Result Report_Romania.xls"
    wb = xlrd.open_workbook(str(path), formatting_info=False)
    sh = wb.sheet_by_index(0)
    names = []
    totals = []
    for c in range(3, sh.ncols):
        n = sh.cell_value(2, c)
        if n in (None, ""):
            continue
        names.append(str(n).strip())
        totals.append(sh.cell_value(12, c))
    p("Romania report dealers:", len(names))
    numeric = [float(t) for t in totals if isinstance(t, (int, float))]
    if numeric:
        p("totals min/max/mean", min(numeric), max(numeric), round(sum(numeric) / len(numeric), 2))
    # ranking
    rank = BASE / "rankings" / "Romania_dealer_ranking.xlsx"
    if rank.is_file():
        rwb = load_workbook(rank, data_only=True, read_only=True)
        ws = rwb.active
        rows = list(ws.iter_rows(values_only=True))
        p("ranking sheet", ws.title, "rows", len(rows) - 1)
        # find total/pct cols
        hdr = [str(x or "") for x in rows[0]]
        p("ranking headers:", hdr[:12])
        rwb.close()
    # search tb
    roots = [
        Path(r"C:\Users\jerom\Downloads"),
        Path(r"C:\Users\jerom\Desktop\claude"),
        BASE,
    ]
    found = []
    for root in roots:
        if not root.exists():
            continue
        try:
            for pat in ("*_tb.xls", "*_tb.xlsx", "*Romania*tb*", "*romania*compare*", "*Romania*Comparison*"):
                found.extend(root.rglob(pat))
        except OSError:
            pass
    found = [f for f in found if f.is_file()][:40]
    p("tb/comparison matches:", len(found))
    for f in found[:20]:
        p(" ", f)


def midi():
    p("\n=== 4) MIDI ===")
    midi_file = BASE / "MIDI" / "MIDI_FR.xlsx"
    p("MIDI_FR.xlsx exists?", midi_file.is_file(), midi_file)
    # no result report
    reports = list((BASE / "reports" / "evaluation_result").glob("*MIDI*"))
    p("MIDI result reports:", reports)
    ranks = list((BASE / "rankings").glob("MIDI_*dealer_ranking.xlsx"))
    p("MIDI ranking files:", len(ranks))
    for r in ranks:
        p(" ", r.name)
    if midi_file.is_file():
        wb = load_workbook(midi_file, read_only=True, data_only=True)
        p("sheets:", wb.sheetnames[:15])
        if "DLR SELF EVALUATION" in wb.sheetnames:
            ws = wb["DLR SELF EVALUATION"]
            codes = Counter()
            dealers = Counter()
            for row in ws.iter_rows(min_row=2, values_only=True):
                code = str(row[2] or "").strip().upper() if len(row) > 2 else ""
                dlr = str(row[1] or "").strip() if len(row) > 1 else ""
                if len(code) == 2 and code.isalpha() and code != "CO":
                    codes[code] += 1
                    if dlr:
                        dealers[(code, dlr)] += 1
            p("CodDiv row counts:", dict(codes))
            by_c = Counter(c for c, _ in dealers)
            p("unique dealers by CodDiv:", dict(by_c))
        wb.close()


def score_cap():
    p("\n=== 6) SCORE CAP ===")
    # already documented in code; confirm _avg_pct_formula
    from build_ids_result_report import _avg_pct_formula, _standard_eval_score, _coerce_score

    p("_coerce_score(4,1)=", _coerce_score(4, 1))
    p("_standard_eval_score with over-max simulated via row stub")
    # check formula text
    import inspect
    import build_ids_result_report as m

    p("_avg_pct_formula:", m._avg_pct_formula(18, 22))
    src = Path(m.__file__).read_text(encoding="utf-8")
    p("has MIN in avg pct?", "MIN(" in src)
    p("write path caps with min(val, max_points)?", "min(float(val), float(trow.max_points))" in src)


def db_owner():
    p("\n=== 7) DB OWNER ===")
    # search for responsibility files
    hits = []
    for root in [
        BASE,
        Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\ids_dealer_ranking"),
        Path(r"C:\Users\jerom\Desktop\claude\ISZE\05_memory"),
        Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs"),
    ]:
        if not root.exists():
            continue
        for pat in ("*owner*", "*responsib*", "*allocation*", "*DB*owner*", "*country*owner*"):
            try:
                hits.extend(root.rglob(pat))
            except OSError:
                pass
    hits = [h for h in hits if h.is_file() and "node_modules" not in str(h)][:30]
    p("owner/responsib file hits:", len(hits))
    for h in hits:
        p(" ", h)
    awards = BASE / "rankings" / "DB Evaluation for Awards 26.xlsx"
    p("Awards workbook:", awards.is_file(), awards)
    if awards.is_file():
        wb = load_workbook(awards, read_only=True, data_only=True)
        p("awards sheets:", wb.sheetnames)
        ws = wb[wb.sheetnames[0]]
        rows = list(ws.iter_rows(max_row=45, max_col=8, values_only=True))
        for i, row in enumerate(rows[:40], 1):
            if any(row):
                p(f"  r{i}:", [str(x)[:40] if x is not None else "" for x in row])
        wb.close()


if __name__ == "__main__":
    wipe()
    hungary()
    be_nl_lu()
    iuk()
    midi()
    romania()
    score_cap()
    db_owner()
    p("\nDONE ->", OUT)
