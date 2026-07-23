#!/usr/bin/env python3
"""Logic checks for IDS 2026 Evaluation Result Reports (scores, %, sections).

See IDS_2026_LOGIC_CHECK.md for full checklist and error register.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean

import xlrd

from build_ids_result_report import load_matrix_rows_from_sheet
from ids_paths import IDS_RESULT_REPORTS_DIR, resolve_dk_template, result_report_path
from ids_report_extract import discover_result_reports
from ids_report_qa import compare_to_dk

COL_LABEL = 0
COL_MAX = 2
COL_FIRST_DEALER = 3
ROW_SCORE_ORIG = 12
ROW_SCORE_PCT = 13
QUESTION_RE = re.compile(r"^[A-H][.\-]\d+[-.]\d+", re.I)
SECTION_RE = re.compile(r"^[A-H]\.\s")


@dataclass
class Issue:
    country: str
    check: str
    detail: str


@dataclass
class CountryResult:
    country: str
    path: str
    dealers: int = 0
    layout_ok: bool = True
    issues: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.layout_ok and not self.issues


def _country_from_path(path: Path) -> str:
    stem = path.stem
    prefix = "2026 IDS Evaluation Result Report_"
    return stem[len(prefix) :] if stem.startswith(prefix) else stem


def _dealer_cols(sh) -> list[int]:
    cols: list[int] = []
    for c in range(COL_FIRST_DEALER, sh.ncols):
        idx = sh.cell_value(1, c)
        name = sh.cell_value(2, c)
        if (idx == "" or idx is None) and not name:
            break
        if name:
            cols.append(c)
    return cols


def _num(val) -> float | None:
    if val in ("", None):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    return None


def _check_scores_and_pct(country: str, sh, dealer_cols: list[int]) -> list[Issue]:
    issues: list[Issue] = []
    matrix = load_matrix_rows_from_sheet(sh)

    for trow in matrix:
        r = trow.sheet_row
        if r is None:
            continue
        mx = _num(sh.cell_value(r, COL_MAX))
        if mx is None or mx <= 0:
            continue

        col_scores = [_num(sh.cell_value(r, c)) for c in dealer_cols]
        ok_scores = [v for v in col_scores if v is not None]

        for c, val in zip(dealer_cols, col_scores):
            if val is None:
                continue
            if val > mx + 1e-6:
                dealer = sh.cell_value(2, c)
                issues.append(
                    Issue(
                        country,
                        "score_above_max",
                        f"row {r + 1} {trow.ref!r} dealer {dealer!r}: {val} > max {mx}",
                    )
                )

        if ok_scores:
            avg_score = mean(ok_scores)
            avg_pct = min(avg_score / mx, 1.0)
            if avg_pct > 1.001:
                issues.append(
                    Issue(
                        country,
                        "pct_above_100",
                        f"row {r + 1} {trow.ref!r}: computed avg % {avg_pct:.4f} > 1",
                    )
                )

    # Row 13 total <= 280, row 14 dealer % <= 1
    for c in dealer_cols:
        total = _num(sh.cell_value(ROW_SCORE_ORIG, c))
        if total is not None and total > 280 + 1e-6:
            issues.append(
                Issue(
                    country,
                    "total_above_280",
                    f"dealer {sh.cell_value(2, c)!r}: total {total} > 280",
                )
            )
        pct = _num(sh.cell_value(ROW_SCORE_PCT, c))
        if pct is not None and pct > 1.001:
            issues.append(
                Issue(
                    country,
                    "dealer_pct_above_100",
                    f"dealer {sh.cell_value(2, c)!r}: row 14 pct {pct} > 1",
                )
            )

    return issues


def _check_section_sums(country: str, sh, dealer_cols: list[int]) -> list[Issue]:
    issues: list[Issue] = []
    matrix = load_matrix_rows_from_sheet(sh)

    subs = [t for t in matrix if t.kind == "subcategory"]
    cats = [t for t in matrix if t.kind == "category"]

    for s in subs:
        r = s.sheet_row
        if r is None:
            continue
        qrows = []
        for qr in matrix:
            if qr.sheet_row is None or qr.sheet_row <= r:
                continue
            if qr.kind in ("subcategory", "category"):
                break
            if qr.kind == "question":
                qrows.append(qr.sheet_row)
        for c in dealer_cols:
            subv = _num(sh.cell_value(r, c))
            if subv is None:
                continue
            qsum = sum(
                _num(sh.cell_value(qr, c)) or 0
                for qr in qrows
                if _num(sh.cell_value(qr, c)) is not None
            )
            if abs(subv - qsum) > 0.02:
                issues.append(
                    Issue(
                        country,
                        "subsection_mismatch",
                        f"{s.ref} dealer {sh.cell_value(2, c)!r}: row {r + 1}={subv} vs sum questions={qsum}",
                    )
                )

    for cat in cats:
        r = cat.sheet_row
        if r is None:
            continue
        subrows = []
        for sr in matrix:
            if sr.sheet_row is None or sr.sheet_row <= r:
                continue
            if sr.kind == "category":
                break
            if sr.kind == "subcategory":
                subrows.append(sr.sheet_row)
        if not subrows:
            continue
        for c in dealer_cols:
            catv = _num(sh.cell_value(r, c))
            if catv is None:
                continue
            ssum = sum(
                _num(sh.cell_value(sr, c)) or 0
                for sr in subrows
                if _num(sh.cell_value(sr, c)) is not None
            )
            if abs(catv - ssum) > 0.02:
                issues.append(
                    Issue(
                        country,
                        "section_mismatch",
                        f"{cat.ref} dealer {sh.cell_value(2, c)!r}: row {r + 1}={catv} vs sum subsections={ssum}",
                    )
                )

    if cats:
        cat_rows = [c.sheet_row for c in cats if c.sheet_row is not None]
        for c in dealer_cols:
            total = _num(sh.cell_value(ROW_SCORE_ORIG, c))
            if total is None:
                continue
            has_detail = any(
                _num(sh.cell_value(qr.sheet_row, c)) is not None
                for qr in matrix
                if qr.kind == "question" and qr.sheet_row is not None
            )
            if not has_detail:
                continue
            sec_sum = sum(
                _num(sh.cell_value(sr, c)) or 0
                for sr in cat_rows
                if _num(sh.cell_value(sr, c)) is not None
            )
            if abs(total - sec_sum) > 0.5:
                issues.append(
                    Issue(
                        country,
                        "total_vs_sections",
                        f"dealer {sh.cell_value(2, c)!r}: total {total} vs sections {sec_sum}",
                    )
                )

    return issues


def _check_excel_pct_column(country: str, path: Path, dealer_cols: list[int]) -> list[Issue]:
    """Read calculated Ave. % via Excel COM when available (catches formula errors)."""
    try:
        import win32com.client  # type: ignore
    except ImportError:
        return []

    issues: list[Issue] = []
    xl = win32com.client.Dispatch("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    wb = None
    try:
        wb = xl.Workbooks.Open(str(path.resolve()))
        ws = wb.Worksheets(1)
        # dealer_cols uses 0-based indices (xlrd). Excel COM is 1-based.
        # If last dealer col is K (11), avg col is L (12) and Ave. % is M (13).
        avg_pct_col = dealer_cols[-1] + 3 if dealer_cols else None
        if avg_pct_col is None:
            return []
        for row in range(15, ws.UsedRange.Rows.Count + 1):
            ref = ws.Cells(row, 1).Value
            if not ref:
                continue
            mx = ws.Cells(row, 3).Value
            if mx in ("", None):
                continue
            pct = ws.Cells(row, avg_pct_col).Value
            if pct in ("", None):
                continue
            if float(pct) > 1.001:
                issues.append(
                    Issue(
                        country,
                        "excel_pct_above_100",
                        f"row {row} {ref!r}: Ave. % = {pct}",
                    )
                )
    except Exception as exc:
        issues.append(Issue(country, "excel_com_error", str(exc)))
    finally:
        if wb is not None:
            wb.Close(False)
        xl.Quit()
    return issues


def check_report(path: Path, *, use_excel: bool = False, layout: bool = True) -> CountryResult:
    country = _country_from_path(path)
    result = CountryResult(country=country, path=str(path))

    if layout:
        qa = compare_to_dk(path, resolve_dk_template())
        result.layout_ok = qa["ok"]
        result.dealers = qa.get("dealers", 0)
        for msg in qa.get("issues", []):
            result.issues.append(Issue(country, "layout", msg))

    rb = xlrd.open_workbook(str(path))
    sh = rb.sheet_by_index(0)
    dealer_cols = _dealer_cols(sh)
    if not result.dealers:
        result.dealers = len(dealer_cols)

    result.issues.extend(_check_scores_and_pct(country, sh, dealer_cols))
    result.issues.extend(_check_section_sums(country, sh, dealer_cols))

    if use_excel:
        result.issues.extend(_check_excel_pct_column(country, path, dealer_cols))

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=IDS_RESULT_REPORTS_DIR,
        help="Folder with 2026 IDS Evaluation Result Report_*.xls",
    )
    parser.add_argument("--country", help="Check one country code only (e.g. BE)")
    parser.add_argument(
        "--excel",
        action="store_true",
        help="Also evaluate Ave. %% via Excel COM (Windows + Excel installed)",
    )
    parser.add_argument(
        "--no-layout",
        action="store_true",
        help="Skip DK layout QA (scores/sections only)",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.country:
        paths = [result_report_path(args.country)]
        paths = [p for p in paths if p.is_file()]
    else:
        paths = discover_result_reports(args.reports_dir)

    if not paths:
        print("No report files found.", file=sys.stderr)
        return 2

    results = [
        check_report(p, use_excel=args.excel, layout=not args.no_layout) for p in paths
    ]
    failed = [r for r in results if not r.ok]

    if args.json:
        payload = {
            "ok": not failed,
            "countries": len(results),
            "failed": len(failed),
            "results": [
                {
                    "country": r.country,
                    "ok": r.ok,
                    "dealers": r.dealers,
                    "layout_ok": r.layout_ok,
                    "issues": [{"check": i.check, "detail": i.detail} for i in r.issues],
                }
                for r in results
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        for r in results:
            status = "OK" if r.ok else "FAIL"
            print(f"{r.country:12} {status:4}  dealers={r.dealers}  issues={len(r.issues)}")
            for i in r.issues:
                print(f"  [{i.check}] {i.detail}")
        print()
        print(f"Summary: {len(results) - len(failed)}/{len(results)} passed")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
