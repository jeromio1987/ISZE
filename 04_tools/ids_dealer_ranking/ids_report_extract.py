"""Extract dealer / section scores from DK-layout IDS result .xls reports."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

import xlrd

from build_ids_result_report import (
    COL_FIRST_DEALER,
    COL_LABEL,
    COL_MAX,
    COL_TEXT,
    ROW_COUNTRY,
    ROW_META_START,
    ROW_SCORE_ORIG,
    ROW_SCORE_PCT,
    ROW_DATA_START,
    load_matrix_rows_from_sheet,
)

SECTION_RE = re.compile(r"^([A-H])\.\s", re.IGNORECASE)

REPORT_PREFIX = "2026 IDS Evaluation Result Report_"
REPORT_SUFFIX = ".xls"


@dataclass
class DealerRecord:
    country: str
    name: str
    total: float | None
    total_pct: float | None
    country_avg_total: float | None
    country_avg_pct: float | None
    sections: dict[str, dict[str, float | None]] = field(default_factory=dict)
    totals_only: bool = False

    @property
    def id(self) -> str:
        return f"{self.country}::{self.name}"


def _num(val: Any) -> float | None:
    if val in ("", None):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    return None


def _country_from_sheet(sh) -> str:
    line = str(sh.cell_value(ROW_COUNTRY, COL_LABEL)).strip()
    if line.lower().startswith("country"):
        return line.split(None, 1)[-1].strip()
    return line


def _country_from_filename(path: Path) -> str:
    stem = path.stem
    if stem.startswith(REPORT_PREFIX):
        return stem[len(REPORT_PREFIX) :]
    return stem


def _read_dealers(sh) -> list[tuple[int, str]]:
    dealers: list[tuple[int, str]] = []
    for c in range(COL_FIRST_DEALER, sh.ncols):
        idx = sh.cell_value(ROW_COUNTRY, c)
        name = str(sh.cell_value(ROW_META_START, c) or "").strip()
        if idx in ("", None) and not name:
            break
        if not name:
            continue
        dealers.append((c, name))
    return dealers


def _avg(vals: list[float | None]) -> float | None:
    ok = [v for v in vals if v is not None]
    return mean(ok) if ok else None


def _question_rows_under_category(matrix: list, category) -> list:
    """All question rows belonging to a top-level A–E category (incl. under subcats).

    Category / total cells in result .xls are Excel formulas without cached values,
    so xlrd reads blanks — dashboard extract must sum question scores instead.
    """
    rows: list = []
    started = False
    for row in matrix:
        if row.sheet_row == category.sheet_row:
            started = True
            continue
        if not started:
            continue
        if row.kind == "category":
            break
        if row.kind == "question" and row.sheet_row is not None:
            rows.append(row)
    return rows


def _sum_question_scores(sh, question_rows: list, col: int) -> float | None:
    vals = [_num(sh.cell_value(q.sheet_row, col)) for q in question_rows]
    ok = [v for v in vals if v is not None]
    return sum(ok) if ok else None


def extract_result_report(path: Path) -> tuple[str, list[DealerRecord], list[dict[str, str]]]:
    """Return country label, dealer records, and section definitions."""
    rb = xlrd.open_workbook(str(path))
    sh = rb.sheet_by_index(0)
    country = _country_from_sheet(sh) or _country_from_filename(path)
    dealers = _read_dealers(sh)
    if not dealers:
        return country, [], []

    matrix = load_matrix_rows_from_sheet(sh)
    section_rows = [r for r in matrix if r.kind == "category" and r.ref]
    sections_meta: list[dict[str, str]] = []
    seen: set[str] = set()
    section_questions: dict[str, list] = {}

    for row in section_rows:
        m = SECTION_RE.match(row.ref)
        if not m:
            continue
        sec = m.group(1).upper()
        if sec in seen:
            continue
        seen.add(sec)
        sections_meta.append(
            {
                "id": sec,
                "label": row.text.strip() or row.ref.strip(),
                "ref": row.ref.strip(),
            }
        )
        section_questions[sec] = _question_rows_under_category(matrix, row)

    dealer_cols = [d[0] for d in dealers]
    # Precompute per-section scores for every dealer (cell value or question sum).
    section_scores: dict[str, dict[int, float | None]] = {}
    section_max: dict[str, float | None] = {}
    for row in section_rows:
        m = SECTION_RE.match(row.ref)
        if not m:
            continue
        sec = m.group(1).upper()
        if sec not in section_questions:
            continue
        r = row.sheet_row
        max_pts = (_num(sh.cell_value(r, COL_MAX)) if r is not None else None) or row.max_points
        section_max[sec] = max_pts
        qrows = section_questions[sec]
        by_col: dict[int, float | None] = {}
        for col in dealer_cols:
            score = _num(sh.cell_value(r, col)) if r is not None else None
            if score is None:
                score = _sum_question_scores(sh, qrows, col)
            by_col[col] = score
        section_scores[sec] = by_col

    records: list[DealerRecord] = []
    resolved_totals: dict[int, float | None] = {}
    resolved_pcts: dict[int, float | None] = {}

    for col, name in dealers:
        total = _num(sh.cell_value(ROW_SCORE_ORIG, col))
        total_pct = _num(sh.cell_value(ROW_SCORE_PCT, col))
        sec_data: dict[str, dict[str, float | None]] = {}

        for sec, by_col in section_scores.items():
            max_pts = section_max.get(sec)
            score = by_col.get(col)
            col_scores = [by_col.get(dc) for dc in dealer_cols]
            avg_score = _avg(col_scores)
            avg_pct = (avg_score / max_pts) if avg_score is not None and max_pts else None
            pct = (score / max_pts) if score is not None and max_pts else None
            sec_data[sec] = {
                "score": score,
                "max": max_pts,
                "pct": pct,
                "country_avg_score": avg_score,
                "country_avg_pct": avg_pct,
            }

        if total is None:
            sec_vals = [v.get("score") for v in sec_data.values() if v.get("score") is not None]
            if sec_vals:
                total = sum(sec_vals)
                total_pct = total / 280.0

        resolved_totals[col] = total
        resolved_pcts[col] = total_pct

        totals_only = total is not None and not any(
            v.get("score") is not None for v in sec_data.values()
        )

        records.append(
            DealerRecord(
                country=country,
                name=name,
                total=total,
                total_pct=total_pct,
                country_avg_total=None,
                country_avg_pct=None,
                sections=sec_data,
                totals_only=totals_only,
            )
        )

    # Second pass: country averages need all resolved totals (already filled above
    # only if we iterate once — fix averages now that dict is complete).
    country_avg_total = _avg([resolved_totals[dc] for dc in dealer_cols])
    country_avg_pct = _avg([resolved_pcts[dc] for dc in dealer_cols])
    for rec in records:
        rec.country_avg_total = country_avg_total
        rec.country_avg_pct = country_avg_pct

    return country, records, sections_meta


def discover_result_reports(reports_dir: Path) -> list[Path]:
    if not reports_dir.is_dir():
        return []
    return sorted(
        p
        for p in reports_dir.glob(f"{REPORT_PREFIX}*{REPORT_SUFFIX}")
        if p.is_file() and "_Delta" not in p.name and " - Copy" not in p.name
    )


def build_dashboard_payload(reports_dir: Path) -> dict[str, Any]:
    paths = discover_result_reports(reports_dir)
    all_dealers: list[dict[str, Any]] = []
    countries: list[str] = []
    section_map: dict[str, str] = {}

    for path in paths:
        country, records, sections = extract_result_report(path)
        if country not in countries:
            countries.append(country)
        for s in sections:
            section_map.setdefault(s["id"], s["label"])
        for rec in records:
            all_dealers.append(
                {
                    "id": rec.id,
                    "country": rec.country,
                    "name": rec.name,
                    "total": rec.total,
                    "total_pct": rec.total_pct,
                    "country_avg_total": rec.country_avg_total,
                    "country_avg_pct": rec.country_avg_pct,
                    "totals_only": rec.totals_only,
                    "sections": rec.sections,
                }
            )

    section_order = sorted(section_map.keys())
    sections = [{"id": sid, "label": section_map[sid]} for sid in section_order]

    def profile_for(dealer_list: list[dict[str, Any]]) -> dict[str, Any]:
        sec_pct: dict[str, float | None] = {}
        for sid in section_order:
            vals = [
                d["sections"][sid]["pct"]
                for d in dealer_list
                if sid in d.get("sections", {})
                and d["sections"][sid].get("pct") is not None
            ]
            sec_pct[sid] = mean(vals) if vals else None
        tvals = [d["total_pct"] for d in dealer_list if d.get("total_pct") is not None]
        return {
            "total_pct": mean(tvals) if tvals else None,
            "sections_pct": sec_pct,
        }

    country_profiles: dict[str, Any] = {}
    for c in countries:
        subset = [d for d in all_dealers if d["country"] == c]
        country_profiles[c] = {
            "dealer_count": len(subset),
            **profile_for(subset),
        }

    network = {"dealer_count": len(all_dealers), **profile_for(all_dealers)}

    return {
        "countries": countries,
        "sections": sections,
        "dealers": all_dealers,
        "dealer_count": len(all_dealers),
        "country_count": len(countries),
        "country_profiles": country_profiles,
        "network": network,
    }
