"""Extract dealer / section scores from DK-layout IDS result .xls reports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Any

import xlrd

from ids_paths import ISZE_ROOT, country_display_name
from build_ids_result_report import (
    COL_FIRST_DEALER,
    COL_LABEL,
    COL_MAX,
    COL_TEXT,
    QUESTION_RE,
    ROW_COUNTRY,
    ROW_META_START,
    ROW_SCORE_ORIG,
    ROW_SCORE_PCT,
    ROW_DATA_START,
    _norm_ref,
    load_matrix_rows_from_sheet,
)

SECTION_RE = re.compile(r"^([A-H])\.\s", re.IGNORECASE)

REPORT_PREFIX = "2026 IDS Evaluation Result Report_"
REPORT_SUFFIX = ".xls"

# Tomoe Baumann MIDI rule (2026-07-31):
# - FR/ES red-marked → out of averages only (list/map keep them)
# - IT/CH → ALL dealers in averages (including zero-score shells)
RED_MARKED_JSON = (
    ISZE_ROOT
    / "01_data"
    / "90_INBOX"
    / "tomoe_ids_mail_pull"
    / "20260731_0858_red_marked_dealers.json"
)
AVG_ALL_IN = frozenset({"Italy", "Switzerland"})
AVG_EXCLUDE_RED = frozenset({"France", "Spain"})

# Section E not assessed (2026-08-15):
# Israel LCV (UMI) filled 0/18 questions, 0/27 points at all 29 dealers.
# That is not_scored — not a vehicle-sales fail. Leave E out of scoring;
# record the 0/27; exclude those zeros from country / network averages.
SECTION_E_NOT_SCORED_COUNTRIES = frozenset({"Israel LCV"})
SECTION_E_MAX = 27.0
TOTAL_MAX_AE = 280.0


# META_ROWS offset: Dealer Name (0), Evaluation Date (1), Address (2)
ROW_EVAL_DATE = ROW_META_START + 1
ROW_ADDRESS = ROW_META_START + 2

# Plausible calendar-year bounds for a 2026-cycle IDS assessment date. Anything
# outside this window is treated as unparseable rather than guessed at.
_EVAL_DATE_YEAR_MIN = 2015
_EVAL_DATE_YEAR_MAX = 2035

# Evaluation-Date cells are hand-typed free text across ~20 country workbooks.
# Month names seen in this dataset (EN/NL/FR/DE/NO/DA/IT/ES) mapped to 1-12.
_MONTH_NAMES = {
    "jan": 1, "january": 1, "januari": 1, "janvier": 1, "januar": 1, "gennaio": 1, "enero": 1,
    "feb": 2, "february": 2, "februari": 2, "fevrier": 2, "février": 2, "februar": 2, "febbraio": 2, "febrero": 2,
    "mar": 3, "march": 3, "maart": 3, "mars": 3, "märz": 3, "marz": 3, "marzo": 3,
    "apr": 4, "april": 4, "avril": 4, "aprile": 4, "abril": 4,
    "may": 5, "mei": 5, "mai": 5, "maggio": 5, "mayo": 5,
    "jun": 6, "june": 6, "juni": 6, "juin": 6, "giugno": 6, "junio": 6,
    "jul": 7, "july": 7, "juli": 7, "juillet": 7, "luglio": 7, "julio": 7,
    "aug": 8, "august": 8, "augustus": 8, "aout": 8, "août": 8, "agosto": 8,
    "sep": 9, "sept": 9, "september": 9, "septembre": 9, "settembre": 9, "septiembre": 9,
    "oct": 10, "october": 10, "oktober": 10, "octobre": 10, "ottobre": 10, "octubre": 10,
    "nov": 11, "november": 11, "novembre": 11, "noviembre": 11,
    "dec": 12, "december": 12, "decembre": 12, "décembre": 12, "dezember": 12,
    "desember": 12, "dicembre": 12, "diciembre": 12,
}


def _valid_ymd(y: int, m: int, d: int) -> bool:
    if not (_EVAL_DATE_YEAR_MIN <= y <= _EVAL_DATE_YEAR_MAX):
        return False
    if not (1 <= m <= 12):
        return False
    if not (1 <= d <= 31):
        return False
    try:
        date(y, m, d)
    except ValueError:
        return False
    return True


def _parse_assessment_date(raw: Any, datemode: int) -> str | None:
    """Best-effort, non-guessing parse of an Evaluation-Date cell to ISO 'YYYY-MM-DD'.

    Returns None (never a fabricated value) when the cell is empty or the text
    is genuinely ambiguous/malformed (e.g. a year with a missing digit) rather
    than attempting a guess. Only unambiguous re-formatting of digits already
    present in the cell is performed.
    """
    if raw in ("", None):
        return None

    if isinstance(raw, (int, float)):
        val = float(raw)
        # A real Excel date serial for a 2015-2035 date (1900 date system).
        if 42000.0 <= val <= 50000.0:
            try:
                d = xlrd.xldate_as_datetime(val, datemode)
                return d.date().isoformat()
            except Exception:
                pass
        # Hand-typed 8-digit ddmmyyyy with no separators (e.g. 22012026 for
        # 22 Jan 2026) — deterministic re-read of the same digits, not a guess.
        ival = int(val) if val == int(val) else None
        if ival is not None and 1_010_000 <= ival <= 31_129_999:
            s = str(ival)
            if len(s) == 8:
                day, month, year = int(s[0:2]), int(s[2:4]), int(s[4:8])
                if _valid_ymd(year, month, day):
                    return f"{year:04d}-{month:02d}-{day:02d}"
        return None

    text = str(raw).strip()
    if not text:
        return None
    low = text.lower()

    m = re.match(r"^(\d{4})[-./](\d{1,2})[-./](\d{1,2})$", text)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_ymd(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"
        return None

    m = re.match(r"^(\d{1,2})\s*[-./,]\s*(\d{1,2})\s*[-./,]\s*(\d{2,4})$", text)
    if m:
        day, month, year_raw = int(m.group(1)), int(m.group(2)), m.group(3)
        if len(year_raw) == 2:
            year = 2000 + int(year_raw)
        elif len(year_raw) == 4:
            year = int(year_raw)
        else:
            return None  # 3-digit year: a digit is missing — ambiguous, do not guess
        if _valid_ymd(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"
        return None

    m = re.match(r"^(\d{1,2})[.\s]+([a-zA-Zà-ÿ]+)[.\s]+(\d{4})$", low)
    if m:
        day = int(m.group(1))
        month = _MONTH_NAMES.get(m.group(2).strip("."))
        year = int(m.group(3))
        if month and _valid_ymd(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"
        return None

    return None


@dataclass
class DealerRecord:
    country: str
    name: str
    total: float | None
    total_pct: float | None
    country_avg_total: float | None
    country_avg_pct: float | None
    sections: dict[str, dict[str, float | None]] = field(default_factory=dict)
    # qid -> {score, max, pct} for scored checklist items
    questions: dict[str, dict[str, float | None]] = field(default_factory=dict)
    totals_only: bool = False
    address: str | None = None
    # ISO 'YYYY-MM-DD' when the source Evaluation-Date cell parsed unambiguously.
    # None when the cell is blank or the hand-typed text is ambiguous/malformed
    # (never guessed — see _parse_assessment_date).
    assessment_date: str | None = None
    # Disambiguate same company name / multi-site columns in one country report
    site_key: str | None = None
    # True when dealer is listed but excluded from country / section averages
    excluded_from_average: bool = False
    # "A-E" (280), "A-D" (253 when Section E is not_scored), or "totals_only"
    score_basis: str = "A-E"
    raw_total: float | None = None
    raw_total_pct: float | None = None
    total_max: float | None = None

    @property
    def id(self) -> str:
        if self.site_key:
            return f"{self.country}::{self.name}::{self.site_key}"
        return f"{self.country}::{self.name}"


def _norm_dealer_name(name: str) -> str:
    return " ".join((name or "").casefold().split())


@lru_cache(maxsize=1)
def load_red_marked_names() -> dict[str, set[str]]:
    """Country → normalised dealer names excluded from averages (Baumann)."""
    if not RED_MARKED_JSON.is_file():
        return {}
    raw = json.loads(RED_MARKED_JSON.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = {}
    for country, rows in raw.items():
        out[str(country)] = {
            _norm_dealer_name(r["name"])
            for r in rows
            if isinstance(r, dict) and r.get("name")
        }
    return out


def _num(val: Any) -> float | None:
    if val in ("", None):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    return None


def _country_from_sheet(sh) -> str:
    line = str(sh.cell_value(ROW_COUNTRY, COL_LABEL)).strip()
    if line.lower().startswith("country"):
        raw = line.split(None, 1)[-1].strip()
        return country_display_name(raw)
    return country_display_name(line)


def _country_from_filename(path: Path) -> str:
    stem = path.stem
    if stem.startswith(REPORT_PREFIX):
        return country_display_name(stem[len(REPORT_PREFIX) :])
    return country_display_name(stem)


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


def _ad_score_max(rec: DealerRecord) -> tuple[float, float]:
    """Sum scored A–D points and their max (Section E left out)."""
    score = 0.0
    mx = 0.0
    for sid in ("A", "B", "C", "D"):
        block = rec.sections.get(sid) or {}
        if block.get("score") is not None:
            score += float(block["score"])
        if block.get("max"):
            mx += float(block["max"])
    return score, mx


def _detect_section_e_fill(rec: DealerRecord) -> str:
    """scored | not_scored | blank | totals_only.

    Israel LCV is an explicit not_scored customer (all 29 dealers 0/18, 0/27).
    Blank = E questions empty (UK LCV three dealers; UK CV totals-only).
    Genuine zeros in FR/IT/ES/CH stay scored (Tomoe rule handles red-marks).
    """
    if rec.totals_only:
        return "totals_only"
    if rec.country in SECTION_E_NOT_SCORED_COUNTRIES:
        return "not_scored"
    q_e = [
        block
        for qid, block in (rec.questions or {}).items()
        if str(qid).upper().startswith("E")
    ]
    scores = [b.get("score") for b in q_e]
    e = rec.sections.get("E") or {}
    if not q_e or all(s is None for s in scores):
        if e.get("score") is None and e.get("pct") is None:
            return "blank"
        if not q_e:
            return "blank"
    return "scored"


def _apply_section_e_policy(
    records: list[DealerRecord],
    dealers: list[tuple[int, str]],
    resolved_totals: dict[int, float | None],
    resolved_pcts: dict[int, float | None],
) -> set[int]:
    """Mark Section E fill, restate A–D totals, return cols left out of E averages."""
    e_out_of_avg: set[int] = set()
    for rec, (col, _) in zip(records, dealers):
        fill = _detect_section_e_fill(rec)
        if rec.totals_only:
            rec.score_basis = "totals_only"
            continue
        eblock = rec.sections.setdefault(
            "E",
            {"score": None, "max": SECTION_E_MAX, "pct": None},
        )
        eblock["fill"] = fill
        if fill in ("not_scored", "blank"):
            e_out_of_avg.add(col)
            eblock["pct"] = None
            for qid, qblock in rec.questions.items():
                if str(qid).upper().startswith("E"):
                    qblock["pct"] = None
                    qblock["fill"] = fill
        if fill == "not_scored":
            rec.raw_total = rec.total
            rec.raw_total_pct = rec.total_pct
            ad_score, ad_max = _ad_score_max(rec)
            rec.total = ad_score
            rec.total_pct = (ad_score / ad_max) if ad_max else None
            rec.total_max = ad_max or (TOTAL_MAX_AE - SECTION_E_MAX)
            rec.score_basis = "A-D"
            if eblock.get("score") is None:
                eblock["score"] = 0.0
            eblock.setdefault("max", SECTION_E_MAX)
            resolved_totals[col] = rec.total
            resolved_pcts[col] = rec.total_pct
        else:
            rec.score_basis = "A-E"
            rec.total_max = TOTAL_MAX_AE
    return e_out_of_avg


def _is_scored_pct(pct: float | None) -> bool:
    """True when total % is usable for averages (> 0).

    Zero-score shells stay in dealer lists. For most markets they stay out of
    averages (hygiene). Exception — Tomoe Baumann: Italy / Switzerland keep
    every dealer in averages, including zero shells.
    """
    if pct is None:
        return False
    try:
        return float(pct) > 0.0
    except (TypeError, ValueError):
        return False


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


def _question_section(matrix: list, sheet_row: int | None) -> str | None:
    """Nearest preceding A–E category for a question sheet row."""
    if sheet_row is None:
        return None
    current: str | None = None
    for row in matrix:
        if row.kind == "category" and row.ref:
            m = SECTION_RE.match(row.ref)
            if m:
                current = m.group(1).upper()
        if row.sheet_row == sheet_row:
            return current
    return current


def extract_result_report(
    path: Path,
) -> tuple[str, list[DealerRecord], list[dict[str, str]], list[dict[str, Any]]]:
    """Return country, dealers, section defs, and question catalogue for this report."""
    rb = xlrd.open_workbook(str(path))
    sh = rb.sheet_by_index(0)
    country = _country_from_sheet(sh) or _country_from_filename(path)
    dealers = _read_dealers(sh)
    if not dealers:
        return country, [], [], []

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

    # Question catalogue + per-dealer scores
    question_meta: list[dict[str, Any]] = []
    question_rows: list[tuple[str, Any]] = []  # (qid, matrix row)
    seen_q: set[str] = set()
    for row in matrix:
        if row.kind != "question" or not row.ref:
            continue
        if not QUESTION_RE.match(row.ref) and not re.match(
            r"^[A-H][-.]\d+[-.]\d+", row.ref, re.I
        ):
            continue
        qid = _norm_ref(row.ref)
        if qid in seen_q:
            continue
        seen_q.add(qid)
        sec = _question_section(matrix, row.sheet_row) or (
            qid[0].upper() if qid else None
        )
        max_pts = row.max_points
        if max_pts is None and row.sheet_row is not None:
            max_pts = _num(sh.cell_value(row.sheet_row, COL_MAX))
        text = (row.text or "").strip()
        if not text and row.sheet_row is not None:
            text = str(sh.cell_value(row.sheet_row, COL_TEXT) or "").strip()
        question_meta.append(
            {
                "id": qid,
                "section": sec,
                "text": text,
                "max": max_pts,
            }
        )
        question_rows.append((qid, row))

    records: list[DealerRecord] = []
    resolved_totals: dict[int, float | None] = {}
    resolved_pcts: dict[int, float | None] = {}
    name_by_col: dict[int, str] = {col: name for col, name in dealers}
    name_counts: dict[str, int] = {}
    for _, name in dealers:
        name_counts[name] = name_counts.get(name, 0) + 1
    name_seen: dict[str, int] = {}

    for col, name in dealers:
        total = _num(sh.cell_value(ROW_SCORE_ORIG, col))
        total_pct = _num(sh.cell_value(ROW_SCORE_PCT, col))
        address = str(sh.cell_value(ROW_ADDRESS, col) or "").strip() or None
        assessment_date = _parse_assessment_date(
            sh.cell_value(ROW_EVAL_DATE, col), rb.datemode
        )
        sec_data: dict[str, dict[str, float | None]] = {}

        for sec, by_col in section_scores.items():
            max_pts = section_max.get(sec)
            score = by_col.get(col)
            pct = (score / max_pts) if score is not None and max_pts else None
            sec_data[sec] = {
                "score": score,
                "max": max_pts,
                "pct": pct,
                "country_avg_score": None,
                "country_avg_pct": None,
            }

        q_data: dict[str, dict[str, float | None]] = {}
        for qid, row in question_rows:
            max_pts = next((q["max"] for q in question_meta if q["id"] == qid), None)
            score = (
                _num(sh.cell_value(row.sheet_row, col))
                if row.sheet_row is not None
                else None
            )
            pct = (score / max_pts) if score is not None and max_pts else None
            q_data[qid] = {
                "score": score,
                "max": max_pts,
                "pct": pct,
                "country_avg_pct": None,
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

        site_key: str | None = None
        if name_counts.get(name, 0) > 1:
            name_seen[name] = name_seen.get(name, 0) + 1
            # Prefer a short address token so multi-site companies stay distinct
            addr_bit = (address or "").replace("\n", " ").strip()
            if addr_bit:
                site_key = f"{name_seen[name]}|{addr_bit[:48]}"
            else:
                site_key = f"col{col}"

        records.append(
            DealerRecord(
                country=country,
                name=name,
                total=total,
                total_pct=total_pct,
                country_avg_total=None,
                country_avg_pct=None,
                sections=sec_data,
                questions=q_data,
                totals_only=totals_only,
                address=address,
                assessment_date=assessment_date,
                site_key=site_key,
            )
        )

    e_out_of_avg_cols = _apply_section_e_policy(
        records, dealers, resolved_totals, resolved_pcts
    )

    # Average basis (Tomoe Baumann MIDI rule):
    # IT/CH = all dealers in (incl. zero shells); FR/ES = drop red-marked only;
    # other markets = drop zero-score shells (hygiene).
    red = load_red_marked_names().get(country, set())
    included_cols: list[int] = []
    excluded_cols: set[int] = set()
    for col in dealer_cols:
        name = name_by_col[col]
        pct = resolved_pcts.get(col)
        if country in AVG_ALL_IN:
            included_cols.append(col)
            continue
        if country in AVG_EXCLUDE_RED:
            if _norm_dealer_name(name) in red:
                excluded_cols.add(col)
            else:
                included_cols.append(col)
            continue
        if not _is_scored_pct(pct):
            excluded_cols.add(col)
        else:
            included_cols.append(col)

    country_avg_total = _avg([resolved_totals[dc] for dc in included_cols])
    country_avg_pct = _avg([resolved_pcts[dc] for dc in included_cols])

    # Section averages on the same included set
    sec_avg_score: dict[str, float | None] = {}
    sec_avg_pct: dict[str, float | None] = {}
    for sec, by_col in section_scores.items():
        max_pts = section_max.get(sec)
        scores = [
            by_col.get(dc)
            for dc in included_cols
            if not (sec == "E" and dc in e_out_of_avg_cols)
        ]
        avg_score = _avg(scores)
        sec_avg_score[sec] = avg_score
        sec_avg_pct[sec] = (
            (avg_score / max_pts) if avg_score is not None and max_pts else None
        )

    # Question averages on the same included set
    q_country_avg: dict[str, float | None] = {}
    for qid, row in question_rows:
        max_pts = next((q["max"] for q in question_meta if q["id"] == qid), None)
        pcts: list[float] = []
        is_e = str(qid).upper().startswith("E")
        for col in included_cols:
            if is_e and col in e_out_of_avg_cols:
                continue
            score = (
                _num(sh.cell_value(row.sheet_row, col))
                if row.sheet_row is not None
                else None
            )
            if score is None or not max_pts:
                continue
            pcts.append(score / max_pts)
        q_country_avg[qid] = mean(pcts) if pcts else None

    for rec, (col, _) in zip(records, dealers):
        rec.country_avg_total = country_avg_total
        rec.country_avg_pct = country_avg_pct
        rec.excluded_from_average = col in excluded_cols
        for sec, block in rec.sections.items():
            block["country_avg_score"] = sec_avg_score.get(sec)
            block["country_avg_pct"] = sec_avg_pct.get(sec)
        for qid, block in rec.questions.items():
            block["country_avg_pct"] = q_country_avg.get(qid)

    return country, records, sections_meta, question_meta


def discover_result_reports(reports_dir: Path) -> list[Path]:
    """List country result .xls files, preferring English-named files over legacy codes."""
    if not reports_dir.is_dir():
        return []
    candidates = [
        p
        for p in reports_dir.glob(f"{REPORT_PREFIX}*{REPORT_SUFFIX}")
        if p.is_file() and "_Delta" not in p.name and " - Copy" not in p.name
    ]
    best: dict[str, Path] = {}
    for path in candidates:
        label = country_display_name(path.stem[len(REPORT_PREFIX) :])
        stem_label = path.stem[len(REPORT_PREFIX) :]
        prev = best.get(label)
        if prev is None:
            best[label] = path
            continue
        prev_stem = prev.stem[len(REPORT_PREFIX) :]
        if stem_label == label and prev_stem != label:
            best[label] = path
        elif stem_label != label and prev_stem != label and path.name < prev.name:
            best[label] = path
    return sorted(best.values(), key=lambda p: p.name.casefold())


def _section_e_network_meta(all_dealers: list[dict[str, Any]]) -> dict[str, Any]:
    """Hover copy + excluded-customer record for network averages."""
    by_c: dict[str, dict[str, int]] = {}
    for d in all_dealers:
        c = d.get("country") or "?"
        fill = ((d.get("sections") or {}).get("E") or {}).get("fill")
        row = by_c.setdefault(c, {"n": 0, "not_scored": 0, "blank": 0, "scored": 0})
        row["n"] += 1
        if fill == "not_scored":
            row["not_scored"] += 1
        elif fill == "blank":
            row["blank"] += 1
        elif fill == "scored":
            row["scored"] += 1

    excluded: list[dict[str, Any]] = []
    il = by_c.get("Israel LCV") or {}
    if il.get("not_scored"):
        excluded.append(
            {
                "country": "Israel LCV",
                "customer": "UMI",
                "fill": "not_scored",
                "dealers": il["not_scored"],
                "questions": 18,
                "points": 27,
                "reason": (
                    "Section E was not assessed. 0/18 questions, 0/27 points. "
                    "Not a vehicle-sales fail."
                ),
            }
        )
    uk = by_c.get("UK LCV") or {}
    if uk.get("blank"):
        excluded.append(
            {
                "country": "UK LCV",
                "customer": "IUK",
                "fill": "blank",
                "dealers": uk["blank"],
                "reason": (
                    "Dealers left Section E empty (blank, not zero) and are "
                    "omitted from the Section E average only."
                ),
            }
        )

    hover = (
        "Anonymous full-network average after the France/Spain red-mark rule "
        "(20 + 5 dealers out of the average; Italy and Switzerland keep everyone in). "
        "Section E for Israel LCV (UMI) is not scored — 29 dealers, 18 questions / "
        "27 points, fill not_scored — and is excluded from this average. "
        "0/27 is not a vehicle-sales fail. Israel LCV totals are A–D only (max 253). "
        "UK LCV: 3 dealers blank on E (omitted from Section E only)."
    )
    return {
        "excluded_customers": excluded,
        "by_country": by_c,
        "hover": hover,
    }


def build_dashboard_payload(reports_dir: Path) -> dict[str, Any]:
    paths = discover_result_reports(reports_dir)
    all_dealers: list[dict[str, Any]] = []
    countries: list[str] = []
    section_map: dict[str, str] = {}
    # qid -> meta (first seen wins for text/max)
    question_map: dict[str, dict[str, Any]] = {}
    # temporary: dealer id -> {qid: pct}
    dealer_q_pct: dict[str, dict[str, float | None]] = {}

    for path in paths:
        country, records, sections, questions = extract_result_report(path)
        if country not in countries:
            countries.append(country)
        for s in sections:
            section_map.setdefault(s["id"], s["label"])
        for q in questions:
            question_map.setdefault(
                q["id"],
                {
                    "id": q["id"],
                    "section": q.get("section"),
                    "text": q.get("text") or "",
                    "max": q.get("max"),
                },
            )
        for rec in records:
            all_dealers.append(
                {
                    "id": rec.id,
                    "country": rec.country,
                    "name": rec.name,
                    "address": rec.address,
                    "assessment_date": rec.assessment_date,
                    "total": rec.total,
                    "total_pct": rec.total_pct,
                    "total_max": rec.total_max,
                    "score_basis": rec.score_basis,
                    "raw_total": rec.raw_total,
                    "raw_total_pct": rec.raw_total_pct,
                    "country_avg_total": rec.country_avg_total,
                    "country_avg_pct": rec.country_avg_pct,
                    "totals_only": rec.totals_only,
                    "excluded_from_average": rec.excluded_from_average,
                    "sections": rec.sections,
                }
            )
            dealer_q_pct[rec.id] = {
                qid: (vals.get("pct") if isinstance(vals, dict) else None)
                for qid, vals in (rec.questions or {}).items()
            }

    section_order = sorted(section_map.keys())
    sections = [{"id": sid, "label": section_map[sid]} for sid in section_order]

    # Stable question order: by section then ref
    def _q_sort_key(qid: str) -> tuple:
        meta = question_map[qid]
        sec = meta.get("section") or qid[:1]
        return (sec, qid)

    question_ids = sorted(question_map.keys(), key=_q_sort_key)
    questions = [question_map[qid] for qid in question_ids]

    # Attach compact parallel pct arrays (null if missing)
    for d in all_dealers:
        qmap = dealer_q_pct.get(d["id"], {})
        if d.get("totals_only") or not qmap:
            d["q"] = None
        else:
            # Round to 4 dp to keep HTML smaller
            arr: list[float | None] = []
            for qid in question_ids:
                v = qmap.get(qid)
                arr.append(round(v, 4) if isinstance(v, (int, float)) else None)
            d["q"] = arr

        # Section network avg filled after network profile is known
        for sid, sec in (d.get("sections") or {}).items():
            if isinstance(sec, dict):
                sec.setdefault("network_avg_pct", None)

    def _in_average(d: dict[str, Any]) -> bool:
        """Trust extract flags (IT/CH all-in may include zero-score shells)."""
        return not d.get("excluded_from_average")

    def profile_for(dealer_list: list[dict[str, Any]]) -> dict[str, Any]:
        basis = [d for d in dealer_list if _in_average(d)]
        sec_pct: dict[str, float | None] = {}
        for sid in section_order:
            vals = [
                d["sections"][sid]["pct"]
                for d in basis
                if sid in d.get("sections", {})
                and d["sections"][sid].get("pct") is not None
            ]
            sec_pct[sid] = mean(vals) if vals else None
        tvals = [d["total_pct"] for d in basis if d.get("total_pct") is not None]
        return {
            "total_pct": mean(tvals) if tvals else None,
            "sections_pct": sec_pct,
            "avg_basis_count": len(basis),
        }

    def question_profile(dealer_list: list[dict[str, Any]]) -> list[float | None]:
        basis = [d for d in dealer_list if _in_average(d)]
        out: list[float | None] = []
        for i in range(len(question_ids)):
            vals = [
                d["q"][i]
                for d in basis
                if isinstance(d.get("q"), list)
                and i < len(d["q"])
                and d["q"][i] is not None
            ]
            out.append(round(mean(vals), 4) if vals else None)
        return out

    country_profiles: dict[str, Any] = {}
    for c in countries:
        subset = [d for d in all_dealers if d["country"] == c]
        country_profiles[c] = {
            "dealer_count": len(subset),
            "excluded_from_average_count": sum(
                1 for d in subset if d.get("excluded_from_average")
            ),
            **profile_for(subset),
            "q_pct": question_profile(subset),
        }

    scored_for_network = [d for d in all_dealers if _in_average(d)]
    section_e_meta = _section_e_network_meta(all_dealers)
    for c, prof in country_profiles.items():
        if c == "Israel LCV":
            prof["score_basis"] = "A-D"
            prof["section_e_fill"] = "not_scored"
            prof["avg_hover"] = (
                "Israel LCV national average is A–D only (max 253). "
                "Section E is recorded as not scored (29 dealers, 0/18 questions, "
                "0/27 points, fill not_scored) and is excluded from this average. "
                "0/27 is not a vehicle-sales fail. The operating gap is Section D "
                "(Parts), not vehicle sales."
            )
    network = {
        "dealer_count": len(all_dealers),
        **profile_for(all_dealers),
        "q_pct": question_profile(scored_for_network or all_dealers),
        "section_e": section_e_meta,
        "avg_hover": section_e_meta["hover"],
    }

    # Stamp network section avg onto each dealer section block
    for d in all_dealers:
        for sid, sec in (d.get("sections") or {}).items():
            if isinstance(sec, dict):
                sec["network_avg_pct"] = network["sections_pct"].get(sid)

    return {
        "countries": countries,
        "sections": sections,
        "questions": questions,
        "dealers": all_dealers,
        "dealer_count": len(all_dealers),
        "country_count": len(countries),
        "country_profiles": country_profiles,
        "network": network,
        "bands": {
            "good_min_pct": 0.80,
            "medium_min_pct": 0.60,
            "near_country_pp": 0.05,
            "weak_gap_pp": -0.10,
        },
    }
