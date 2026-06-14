#!/usr/bin/env python3
"""Build IDS dealer country ranking from evaluation workbooks (Box folder export).

Reads each *.xlsx in --input-dir, sheet 'scorecard' (case-insensitive), cells F22 and K22.
Dealer name is parsed from the filename. Output matches the Denmark rank-list layout.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.series import SeriesLabel
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

PREFIXES = (
    r"ISUZU\s+IDS\s+Evaluation\s+Sheet_RO\s+2026\s*",
    r"IDS\s+Evaluation\s+Sheet_rev11\s+no\s+red_",
    r"IDS\s+Evaluation\s+Sheet_rev11\s+",
    r"IDS[\-\s]+evaluation[\-\s]+sheet[\-\s]+2026[\-\s]*",
    r"IDS\s+Evaluation\s+Sheet\s+2026[\-\s]*",
    r"IDS\s+Evaluation\s+Sheet_\s*",
    r"IDS\s+Evaluation\s+Sheet\s*[–\-]?\s*",
    r"IDS\s+Evaluation\s+sheet\s*",
    r"IDS\s+evaluation[\-\s]+sheet[\-\s]+2026[\-\s]*",
    r"KTGreen\s+Ltd[\-\s]*Evaluation\s+Sheet\s*",
    r"NUNNS\s+IDS\s+Evaluation\s+Sheet\s+2026\s*",
    r"Pentraeth\s+IDS\s+Evaluation\s+Sheet\s+2026\s*\(\d+\)\s*",
    r"UNITY\s+TREDINGTON\s*[\-\s]*IDS\s+Evaluation\s+Sheet\s+2026\s*",
    r"Isuzu\.\s*Proveeda\.\s*IDS\s+Evaluation\s+Sheet\s+2026\s*",
    r"Isuzu\s+IDS\s+Evaluation\s+Sheet\s*[–\-]?\s*",
    r"Isuzu\s+Evaluation\s+Sheet\s*[–\-]?\s*",
    r"Isuzu\s+Evaluation\s*[–\-]?\s*",
    r"ISUZU\s+AUDIT\s+",
    r"IDS Evaluation 2026 - PORT - FINAL - Envio Rede - ",
    r"\s*-\s*OK\s*$",
    r"\s+Isuzu Márkszerviz Szabványok 2026(?:\s+magyar)?\s*$",
    r"\s+Isuzu M.rkszerviz Szabv.nyok 2026(?:\s+magyar)?\s*$",
)


def dealer_name_from_filename(path: Path) -> str:
    stem = path.stem.strip()
    for pat in PREFIXES:
        stem = re.sub(pat, "", stem, flags=re.IGNORECASE).strip()
    stem = re.sub(r"\s+", " ", stem).strip(" -–—")
    return stem or path.stem


def read_dealer_name_from_cover(path: Path) -> str | None:
    """Read dealer name from Cover Page / Fedlap (single-dealer audits)."""
    try:
        wb = load_workbook(path, read_only=True, data_only=True)
    except Exception:
        return None
    for sheet_name in ("Cover Page", "Fedlap"):
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        for row in ws.iter_rows(min_row=1, max_row=40, values_only=True):
            label = row[1] if len(row) > 1 else None
            if not isinstance(label, str):
                continue
            if label.strip().lower() != "dealer name":
                continue
            val = row[4] if len(row) > 4 else None
            if val:
                wb.close()
                return str(val).strip()
    wb.close()
    return None


def dealer_display_name(path: Path) -> str:
    return read_dealer_name_from_cover(path) or dealer_name_from_filename(path)


def _coerce_percent(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        if 0 <= v <= 1:
            return round(v * 100, 2)
        return round(v, 2)
    s = str(value).strip().replace(",", ".")
    if not s or s in {"#N/A", "N/A", "-"}:
        return None
    if s.endswith("%"):
        s = s[:-1].strip()
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def _find_score_sheet(wb) -> str | None:
    for name in wb.sheetnames:
        low = name.strip().lower()
        if low == "scorecard":
            return name
    for name in wb.sheetnames:
        low = name.strip().lower()
        if any(
            k in low
            for k in (
                "scorekaart",
                "score card",
                "scorecard",
                "fiche de r",
                "results",
                "eredmény",
                "eredmeny",
                "eredmeny",
            )
        ):
            return name
    return None


def read_scorecard_metrics(path: Path) -> tuple[float | None, float | None]:
    from israel_evaluation import find_israel_eval_sheet, read_israel_total

    wb = load_workbook(path, read_only=True, data_only=True)
    israel_sheet = find_israel_eval_sheet(wb.sheetnames)
    if israel_sheet:
        wb.close()
        return read_israel_total(path)

    sheet_name = _find_score_sheet(wb)
    if sheet_name is None:
        wb.close()
        raise ValueError(f"no score sheet in {path.name}")

    ws = wb[sheet_name]
    f22 = ws["F22"].value
    k22 = ws["K22"].value
    l22 = ws["L22"].value

    # English layout: F22 / K22 are %. BE/NL/FR templates: F22=max points, K22/L22 are %.
    if isinstance(f22, (int, float)) and f22 > 100 and isinstance(k22, (int, float)):
        points = _coerce_percent(k22)
        items = _coerce_percent(l22)
    else:
        points = _coerce_percent(f22)
        items = _coerce_percent(k22)

    wb.close()
    return points, items


def _is_dealer_eval_workbook(path: Path) -> bool:
    if path.name.startswith("~$"):
        return False
    upper = path.name.upper()
    if "DEALERS" in upper and "EVALUATION" not in upper:
        return False
    return True


def collect_dealers(input_dir: Path, limit: int | None) -> list[dict]:
    files = sorted(p for p in input_dir.glob("*.xlsx") if _is_dealer_eval_workbook(p))
    if limit:
        files = files[:limit]
    rows: list[dict] = []
    for path in files:
        try:
            points, items = read_scorecard_metrics(path)
        except Exception as exc:  # noqa: BLE001 — collect per-file errors for report
            rows.append(
                {
                    "name": dealer_display_name(path),
                    "points": None,
                    "items": None,
                    "file": path.name,
                    "error": str(exc),
                }
            )
            continue
        rows.append(
            {
                "name": dealer_display_name(path),
                "points": points,
                "items": items,
                "file": path.name,
                "error": None,
            }
        )
    rows.sort(
        key=lambda r: (r["points"] is None, -(r["points"] or -1), r["name"].lower()),
    )
    return rows


def write_ranking_workbook(
    country: str,
    rows: list[dict],
    output: Path,
    *,
    points_header: str = "Points achieved %",
    items_header: str = "Items scored %",
    chart_second_series: bool = True,
) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = country[:31]

    headers = ["Rank", "Name", points_header, items_header]
    ws.append(headers)
    for col in range(1, 5):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    rank = 0
    for row in rows:
        if row.get("error"):
            continue
        if row["points"] is None and row["items"] is None:
            continue
        rank += 1
        ws.append([rank, row["name"], row["points"], row["items"]])

    n = rank
    if n == 0:
        ws.append(["", "(no valid dealer files)", "", ""])
    else:
        chart = BarChart()
        chart.type = "col"
        chart.grouping = "clustered"
        chart.title = country
        chart.y_axis.title = "%"
        chart.y_axis.scaling.min = 0
        chart.y_axis.scaling.max = 100
        chart.x_axis.title = "Dealer"

        cats = Reference(ws, min_col=2, min_row=2, max_row=1 + n)
        points_ref = Reference(ws, min_col=3, min_row=1, max_row=1 + n)
        items_ref = Reference(ws, min_col=4, min_row=1, max_row=1 + n)

        chart.add_data(points_ref, titles_from_data=True)
        if chart_second_series:
            chart.add_data(items_ref, titles_from_data=True)
        chart.set_categories(cats)
        if chart_second_series and len(chart.series) >= 2:
            chart.series[1].graphicalProperties.solidFill = "C00000"
        chart.width = 18
        chart.height = 10
        ws.add_chart(chart, "F2")

    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 36
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 16

    err_rows = [r for r in rows if r.get("error")]
    if err_rows:
        es = wb.create_sheet("_errors")
        es.append(["File", "Dealer", "Error"])
        for r in err_rows:
            es.append([r["file"], r["name"], r["error"]])

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="Folder of dealer .xlsx files")
    parser.add_argument("--country", required=True, help="Country label (sheet title), e.g. BE")
    parser.add_argument("--output", type=Path, help="Output .xlsx (default: input-dir/../rankings/{country}.xlsx)")
    parser.add_argument("--limit", type=int, default=0, help="Process only first N files (0 = all)")
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 1

    limit = args.limit or None
    rows = collect_dealers(input_dir, limit)
    if not rows:
        print(f"No .xlsx files in {input_dir}", file=sys.stderr)
        return 1

    output = args.output
    if output is None:
        output = input_dir.parent / "rankings" / f"{args.country}_dealer_ranking.xlsx"
    output = output.resolve()

    write_ranking_workbook(args.country, rows, output)

    ok = sum(1 for r in rows if not r.get("error"))
    bad = len(rows) - ok
    print(f"Wrote {output}")
    print(f"  dealers ranked: {ok}")
    if bad:
        print(f"  errors: {bad} (see _errors sheet)")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
