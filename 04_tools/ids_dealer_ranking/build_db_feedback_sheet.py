#!/usr/bin/env python3
"""IDS 2026 — DB feedback sheet builder (v0.4).

Builds a distributor-facing feedback sheet that a DB can use with its dealers.
Four layers, all from the IDS 2026 evaluation result reports:

  A  Executive summary  — one printable page per dealer (score, band, vs country
     average, top 3 strengths, top 3 gaps, plus 2–3 suggested next steps seeded
     from the same checklist gaps; owner / target date / proof blank for the
     meeting).
  B  Dealer workshop pack — exec summary + section scorecard A-E + Kaizen actions
     built from the largest individual checklist gaps, with owner / target date /
     proof blank.
  C  DB rollup cover — primary artefact for the DB: network KPIs, visit hit list,
     incomplete / not-completed lane, suggested DB-level next steps, Pull
     scorecard scaffold, then the ranked dealer list. Dealer one-pagers are annexes.
  D  Capture / follow-up — a Commitments block the dealer returns; `consolidate`
     merges returned workbooks into one table. No server, Excel only.

Sections A-E are reported as conversation structure only. In the 2026 results the
five sections move closely together, so a section score carries little that the
total does not already carry. Actions are therefore derived from individual
checklist items, never from "section X is weak", and no output claims a section
predicts commercial performance.

Averages: each market states its own basis. Where a market has dealers whose
evaluation was not completed (France and Spain in 2026), those are excluded from
the average calculation only and keep their own sheet. All other markets include
every evaluated dealer.

Reads only. Writes only under the target output folder.

Usage
  python build_db_feedback_sheet.py build --country "UK LCV" --all-dealers --rollup
  python build_db_feedback_sheet.py build --country Poland --country Greece --all-dealers --rollup
  python build_db_feedback_sheet.py build --country France --dealer "I.B.R. CONCEPT SARL"
  python build_db_feedback_sheet.py template
  python build_db_feedback_sheet.py consolidate --in-dir <folder of returned .xlsx>
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties

import xlrd

from build_ids_result_report import COL_FIRST_DEALER, ROW_COUNTRY, ROW_META_START
from ids_paths import REPO, country_display_name, result_report_path
from ids_report_extract import extract_result_report

VERSION = "v0.4"
OUT_ROOT = REPO / "09_meetings" / f"IDS_2026_DB_Feedback_Sheet_{VERSION}"

# Exec summary: seed this many suggested actions from top checklist gaps.
# Keep at 2–3 so the one-pager still prints on a single A4 page.
EXEC_SUGGESTED_ACTIONS_N = 3
EXEC_ACTION_TEXT_LIMIT = 100

# Layer C — visit triage and DB planning blocks on the rollup.
HIT_LIST_MAX = 12
HIT_LIST_MIN_TARGET = 8
DB_ACTIONS_N = 5
# Zero / near-zero totals treated as incomplete evaluation (Teams / Baumann context).
INCOMPLETE_TOTAL_PCT_MAX = 0.001

RED_MARKED_JSON = (
    REPO
    / "01_data"
    / "90_INBOX"
    / "tomoe_ids_mail_pull"
    / "20260731_0858_red_marked_dealers.json"
)

SECTIONS = ("A", "B", "C", "D", "E")
SECTION_SHORT = {
    "A": "Premises, facility and clothing",
    "B": "Organisation, management, personnel",
    "C": "Service",
    "D": "Parts and accessories",
    "E": "Vehicle sales",
}

# Absolute bands, printed on every sheet so a DB can reproduce them.
BAND_GOOD_MIN = 0.80
BAND_MEDIUM_MIN = 0.60
BAND_LABELS = ("Good", "Medium", "Needs improvement")

# Locked rule — 2026-07-31. Averages only; excluded dealers remain dealers.
AVG_EXCLUDE_RED = {"France", "Spain"}
AVG_ALL_IN = {"Italy", "Switzerland"}

#: Callers add their own "Average basis" heading or prefix.
AVERAGE_RULE_NOTE = (
    "The market average is calculated on the dealers evaluated in "
    "that market. Where a market contains dealers whose evaluation was not "
    "completed, those are excluded from the average calculation only — they remain "
    "part of the network, stay in the dealer list and keep their own sheet. Every "
    "sheet states the number of dealers behind its own average."
)

# The 2026 section scores are close to a single underlying factor: the five
# sections move together, so a section score adds little to the total. Every
# client-facing file says this out loud, and actions come from checklist items.
SECTION_NOTE = (
    "How to read sections A–E: in the 2026 results the five sections move closely "
    "together — a dealer who scores well on one section usually scores well on the "
    "others. Use the section table as structure for the conversation, not as five "
    "independent capabilities, and do not read a single section as a verdict on "
    "that part of the business. The actions are therefore built from the "
    "individual checklist items where points were actually lost."
)

NA = "N.A."

# House palette — navy / terracotta, same as the other IDS sheets.
NAVY = "1A2744"
TERRACOTTA = "C45C3E"
GOOD = "2D8A5E"
AMBER = "C48A1A"
GREY = "6B7A90"
LIGHT = "F4F6F9"

COMMITMENT_HEADERS = (
    "Country",
    "Dealer",
    "Action ref",
    "Section",
    "Action agreed with the dealer",
    "Owner (role)",
    "Target date",
    "Proof / evidence",
    "Status",
)
STATUS_OPTIONS = "Not started,In progress,Done,Dropped"


# --------------------------------------------------------------------------- #
# formatting helpers
# --------------------------------------------------------------------------- #


def pct(v: float | None, blank: str = NA) -> str:
    return blank if v is None else f"{v * 100:.1f}%"


def pp(v: float | None, blank: str = NA) -> str:
    return blank if v is None else f"{v * 100:+.1f} pp"


def points(score: float | None, maximum: float | None, blank: str = NA) -> str:
    if score is None or not maximum:
        return blank
    return f"{score:g} / {maximum:g}"


def clean_text(text: str | None, limit: int = 160) -> str:
    s = re.sub(r"\s+", " ", (text or "")).strip()
    if len(s) <= limit:
        return s
    return s[: limit - 1].rstrip(" ,.;:") + "…"


def band_of(p: float | None) -> str | None:
    if p is None:
        return None
    if p >= BAND_GOOD_MIN:
        return "Good"
    if p >= BAND_MEDIUM_MIN:
        return "Medium"
    return "Needs improvement"


def band_css(band: str | None) -> str:
    return {
        "Good": "good",
        "Medium": "medium",
        "Needs improvement": "weak",
    }.get(band or "", "")


def band_pill(band: str | None, *, blank: bool = False) -> str:
    if blank or not band:
        return ""
    return f'<span class="pill {band_css(band)}">{escape(band)}</span>'


#: Characters with no canonical decomposition, so NFKD alone will not fold them.
_FOLD_EXTRA = {
    "Ł": "L", "ł": "l", "Ø": "O", "ø": "o", "Æ": "AE", "æ": "ae",
    "Œ": "OE", "œ": "oe", "Đ": "D", "đ": "d", "Þ": "TH", "þ": "th",
    "ß": "ss", "Å": "A", "å": "a",
}


def ascii_fold(text: str) -> str:
    """Plain-ASCII form for filenames. Document contents keep the original name."""
    s = "".join(_FOLD_EXTRA.get(ch, ch) for ch in (text or ""))
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def safe_name(name: str) -> str:
    """ASCII, filesystem-safe stem. Non-ASCII markets must still produce openable
    filenames when a pack is zipped and forwarded."""
    s = re.sub(r"[^A-Za-z0-9\-]+", "_", ascii_fold(name).strip())
    return s.strip("_")[:60] or "dealer"


# --------------------------------------------------------------------------- #
# average basis — locked 2026-07-31 rule
# --------------------------------------------------------------------------- #


def load_red_marked() -> dict[str, set[str]]:
    """Country -> casefolded names excluded from average calculation."""
    if not RED_MARKED_JSON.is_file():
        return {}
    try:
        raw = json.loads(RED_MARKED_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, set[str]] = {}
    for country, rows in raw.items():
        label = country_display_name(country)
        out[label] = {
            str(r.get("name") or "").strip().casefold()
            for r in rows
            if str(r.get("name") or "").strip()
        }
    return out


def average_basis(country: str, dealers: list[dict]) -> dict[str, Any]:
    """Split dealers into the average population and the excluded ones."""
    red = load_red_marked()
    excluded_names: set[str] = set()
    if country in AVG_EXCLUDE_RED:
        excluded_names = red.get(country, set())
        if not excluded_names:
            raise SystemExit(
                f"{country} needs the red-marked exclusion list but none was found "
                f"in {RED_MARKED_JSON}. Refusing to publish an average on the wrong basis."
            )
        rule = (
            f"In {country}, dealers marked red in the 2026 ranking (evaluation not "
            f"completed) are excluded from the average calculation only."
        )
    else:
        # Italy and Switzerland are explicitly all-in; every other market has no
        # incomplete-evaluation list, so there is nothing to exclude. Never imply
        # an exclusion that does not exist in this market.
        rule = "No dealer is excluded: every evaluated dealer counts towards this average."

    included = [d for d in dealers if d["name"].casefold() not in excluded_names]
    excluded = [d for d in dealers if d["name"].casefold() in excluded_names]
    return {
        "rule": rule,
        "included": included,
        "excluded": excluded,
        "n_all": len(dealers),
        "n_included": len(included),
        "n_excluded": len(excluded),
    }


# --------------------------------------------------------------------------- #
# country model
# --------------------------------------------------------------------------- #


def _avg(vals: list[float | None]) -> float | None:
    ok = [v for v in vals if v is not None]
    return mean(ok) if ok else None


def _ranked(dealers: list[dict]) -> None:
    """Stamp competition rank (1, 2, 2, 4) over every dealer in the country."""
    order = sorted(
        dealers, key=lambda d: (d["total_pct"] is None, -(d["total_pct"] or 0.0))
    )
    last_pct: float | None = None
    last_rank = 0
    for i, d in enumerate(order, 1):
        if d["total_pct"] is not None and d["total_pct"] == last_pct:
            d["rank"] = last_rank
        else:
            d["rank"] = i
            last_rank = i
            last_pct = d["total_pct"]


def read_evaluation_dates(path: Path) -> list[str | None]:
    """Evaluation Date per dealer column, in the same order as the extracted records.

    The shared extractor exposes name and address but not the date, and a DB does
    want to see when its dealer was evaluated. Returns None where the cell is
    empty — several markets left it blank.
    """
    try:
        book = xlrd.open_workbook(str(path))
        sh = book.sheet_by_index(0)
    except Exception:  # noqa: BLE001 - date is optional context, never fatal
        return []

    row_date = ROW_META_START + 1
    out: list[str | None] = []
    for c in range(COL_FIRST_DEALER, sh.ncols):
        idx = sh.cell_value(ROW_COUNTRY, c)
        name = str(sh.cell_value(ROW_META_START, c) or "").strip()
        if idx in ("", None) and not name:
            break
        if not name:
            continue
        value = sh.cell_value(row_date, c)
        ctype = sh.cell_type(row_date, c)
        if value in ("", None):
            out.append(None)
        elif ctype == xlrd.XL_CELL_DATE:
            try:
                out.append(xlrd.xldate_as_datetime(value, book.datemode).date().isoformat())
            except Exception:  # noqa: BLE001
                out.append(None)
        elif isinstance(value, (int, float)):
            try:
                out.append(xlrd.xldate_as_datetime(value, book.datemode).date().isoformat())
            except Exception:  # noqa: BLE001
                out.append(str(value))
        else:
            out.append(str(value).strip() or None)
    return out


def build_country_model(country_input: str) -> dict[str, Any]:
    """Everything the renderers need for one DB, on the correct average basis."""
    country = country_display_name(country_input)
    path = result_report_path(country)
    if not path.is_file():
        raise SystemExit(f"No IDS result report for {country}: {path}")

    label, records, sections_meta, questions_meta = extract_result_report(path)
    if not records:
        raise SystemExit(f"No dealers found in {path}")

    q_by_id = {q["id"]: q for q in questions_meta}
    section_max = {
        sid: (records[0].sections.get(sid) or {}).get("max") for sid in SECTIONS
    }
    total_max = sum(v for v in section_max.values() if v) or None

    dates = read_evaluation_dates(path)
    if len(dates) != len(records):
        dates = [None] * len(records)

    name_counts: dict[str, int] = {}
    for rec in records:
        name_counts[rec.name] = name_counts.get(rec.name, 0) + 1
    seen: dict[str, int] = {}

    dealers: list[dict[str, Any]] = []
    for seq, rec in enumerate(records, 1):
        # Several markets list the same company on more than one column (separate
        # sites evaluated individually). Keep them apart in filenames and links.
        stem = safe_name(rec.name)
        if name_counts[rec.name] > 1:
            seen[rec.name] = seen.get(rec.name, 0) + 1
            stem = f"{stem}_site{seen[rec.name]}"
        dealers.append(
            {
                "seq": seq,
                "file_key": stem,
                "multi_site": name_counts[rec.name] > 1,
                "evaluation_date": dates[seq - 1] if seq - 1 < len(dates) else None,
                "name": rec.name,
                "address": rec.address,
                "total": rec.total,
                "total_pct": rec.total_pct,
                "sections": {
                    sid: {
                        "score": (rec.sections.get(sid) or {}).get("score"),
                        "max": (rec.sections.get(sid) or {}).get("max"),
                        "pct": (rec.sections.get(sid) or {}).get("pct"),
                    }
                    for sid in SECTIONS
                },
                "questions": {
                    qid: {
                        "score": vals.get("score"),
                        "max": vals.get("max") or (q_by_id.get(qid) or {}).get("max"),
                    }
                    for qid, vals in (rec.questions or {}).items()
                },
            }
        )

    _ranked(dealers)
    basis = average_basis(country, dealers)
    included = basis["included"]

    country_avg_pct = _avg([d["total_pct"] for d in included])
    country_avg_points = _avg([d["total"] for d in included])
    section_avg_pct = {
        sid: _avg([d["sections"][sid]["pct"] for d in included]) for sid in SECTIONS
    }
    # A section can be scored by fewer dealers than the total (UK LCV left
    # section E blank for three dealers), so its denominator is stated separately.
    section_scored_n = {
        sid: sum(1 for d in included if d["sections"][sid]["pct"] is not None)
        for sid in SECTIONS
    }
    question_avg_pct: dict[str, float | None] = {}
    for qid, meta in q_by_id.items():
        qmax = meta.get("max")
        if not qmax:
            question_avg_pct[qid] = None
            continue
        vals = [
            d["questions"][qid]["score"] / qmax
            for d in included
            if d["questions"].get(qid, {}).get("score") is not None
        ]
        question_avg_pct[qid] = mean(vals) if vals else None

    band_counts = {b: 0 for b in BAND_LABELS}
    for d in included:
        b = band_of(d["total_pct"])
        if b:
            band_counts[b] += 1

    for d in dealers:
        d["in_average"] = d in included
        d["band"] = band_of(d["total_pct"])
        d["vs_country_pp"] = (
            d["total_pct"] - country_avg_pct
            if d["total_pct"] is not None and country_avg_pct is not None
            else None
        )

    return {
        "country": country,
        "report_label": label,
        "source_report": path,
        "sections_meta": {
            s["id"]: s["label"] for s in sections_meta if s["id"] in SECTIONS
        },
        "section_max": section_max,
        "total_max": total_max,
        "questions": q_by_id,
        "question_avg_pct": question_avg_pct,
        "dealers": dealers,
        "basis": basis,
        "country_avg_pct": country_avg_pct,
        "country_avg_points": country_avg_points,
        "section_avg_pct": section_avg_pct,
        "section_scored_n": section_scored_n,
        "band_counts": band_counts,
        "built_on": date.today().isoformat(),
    }


def find_dealer(model: dict, name: str) -> dict:
    needle = name.strip().casefold()
    exact = [d for d in model["dealers"] if d["name"].casefold() == needle]
    if exact:
        return exact[0]
    loose = [d for d in model["dealers"] if needle in d["name"].casefold()]
    if len(loose) == 1:
        return loose[0]
    if len(loose) > 1:
        raise SystemExit(
            f"'{name}' matches {len(loose)} dealers: "
            + ", ".join(d["name"] for d in loose[:6])
        )
    raise SystemExit(f"Dealer '{name}' not found in {model['country']}")


# --------------------------------------------------------------------------- #
# strengths / gaps
# --------------------------------------------------------------------------- #


def scored_items(model: dict, dealer: dict) -> list[dict]:
    out: list[dict] = []
    for qid, vals in dealer["questions"].items():
        meta = model["questions"].get(qid) or {}
        qmax = vals.get("max") or meta.get("max")
        score = vals.get("score")
        if not qmax or score is None:
            continue
        out.append(
            {
                "ref": qid,
                "section": meta.get("section") or qid[:1].upper(),
                "text": meta.get("text") or "",
                "score": float(score),
                "max": float(qmax),
                "pct": float(score) / float(qmax),
                "lost": float(qmax) - float(score),
                "country_avg_pct": model["question_avg_pct"].get(qid),
            }
        )
    return out


def top_strengths(model: dict, dealer: dict, n: int = 3) -> list[dict]:
    """Heaviest checklist items scored in full."""
    items = [i for i in scored_items(model, dealer) if i["lost"] < 0.001]
    items.sort(key=lambda i: (-i["max"], i["ref"]))
    return items[:n]


def top_gaps(model: dict, dealer: dict, n: int = 3) -> list[dict]:
    """Checklist items losing the most points."""
    items = [i for i in scored_items(model, dealer) if i["lost"] > 0.001]
    items.sort(key=lambda i: (-i["lost"], -i["max"], i["ref"]))
    return items[:n]


def suggested_action_text(item: dict, *, limit: int = EXEC_ACTION_TEXT_LIMIT) -> str:
    """Plain action line for the exec summary: ref + short checklist wording."""
    return f"{item['ref']} — {clean_text(item['text'], limit)}"


def incomplete_dealers(model: dict) -> list[dict]:
    """Dealers that must not burn visit time as 'bad scores'.

    France / Spain: red-marked (evaluation not completed) — already outside the
    average. Other markets: any evaluated dealer with a zero / blank total. If
    none, the rollup states that explicitly.
    """
    country = model["country"]
    if country in AVG_EXCLUDE_RED:
        return list(model["basis"]["excluded"])

    out: list[dict] = []
    for d in model["dealers"]:
        tp = d.get("total_pct")
        if tp is None or tp <= INCOMPLETE_TOTAL_PCT_MAX:
            out.append(d)
    return out


def hit_list_dealers(model: dict, *, limit: int = HIT_LIST_MAX) -> list[dict]:
    """Priority visit candidates for the DB — below average and/or Needs improvement.

    Excludes the incomplete lane. Sorted: Needs improvement first, then furthest
    below the market average, then lowest score. Cap ~8–12.
    """
    incomplete_keys = {d["file_key"] for d in incomplete_dealers(model)}
    candidates: list[dict] = []
    for d in model["dealers"]:
        if d["file_key"] in incomplete_keys:
            continue
        if not d.get("in_average", True):
            continue
        below = d.get("vs_country_pp") is not None and d["vs_country_pp"] < 0
        needs = d.get("band") == "Needs improvement"
        if below or needs:
            candidates.append(d)

    def _sort_key(d: dict) -> tuple:
        needs = 0 if d.get("band") == "Needs improvement" else 1
        vs = d.get("vs_country_pp")
        vs_key = vs if vs is not None else 0.0
        tot = d.get("total_pct")
        tot_key = tot if tot is not None else 1.0
        return (needs, vs_key, tot_key)

    candidates.sort(key=_sort_key)
    return candidates[:limit]


def hit_list_why(d: dict) -> str:
    """Short shared reason line for a hit-list row."""
    bits: list[str] = []
    if d.get("band"):
        bits.append(f"Band: {d['band']}")
    if d.get("vs_country_pp") is not None:
        bits.append(f"{pp(d['vs_country_pp'])} vs market average")
    return " · ".join(bits) if bits else NA


def common_gap_refs(model: dict, *, n: int = 5) -> list[dict]:
    """Most frequent checklist gaps across dealers in the average (by lost points)."""
    counts: Counter[str] = Counter()
    lost_sum: dict[str, float] = {}
    sample: dict[str, dict] = {}
    for d in model["basis"]["included"]:
        for item in top_gaps(model, d, n=5):
            ref = item["ref"]
            counts[ref] += 1
            lost_sum[ref] = lost_sum.get(ref, 0.0) + float(item["lost"])
            sample.setdefault(ref, item)
    ranked = sorted(
        counts.keys(),
        key=lambda r: (-counts[r], -lost_sum.get(r, 0.0), r),
    )
    out: list[dict] = []
    for ref in ranked[:n]:
        item = sample[ref]
        out.append(
            {
                "ref": ref,
                "section": item["section"],
                "text": item["text"],
                "dealer_count": counts[ref],
                "lost_sum": lost_sum[ref],
            }
        )
    return out


def suggested_db_actions(model: dict, *, n: int = DB_ACTIONS_N) -> list[str]:
    """3–5 network-level starters from hit-list / gap / incomplete patterns."""
    actions: list[str] = []
    hits = hit_list_dealers(model)
    incomplete = incomplete_dealers(model)
    included = model["basis"]["included"]
    n_inc = len(included) or 1
    below = sum(
        1
        for d in included
        if d.get("vs_country_pp") is not None and d["vs_country_pp"] < 0
    )
    below_pct = below / n_inc
    needs_n = sum(1 for d in included if d.get("band") == "Needs improvement")

    if hits:
        actions.append(
            f"Schedule reviews with the {len(hits)} dealers on the hit list "
            f"(below market average and/or Needs improvement). Use each dealer "
            f"workshop pack as the annex for the visit."
        )
    if below:
        actions.append(
            f"Agree visit cadence for the {below} of {len(included)} dealers "
            f"({below_pct * 100:.0f}%) currently below the market average "
            f"({pct(model['country_avg_pct'])})."
        )
    if needs_n:
        actions.append(
            f"Prioritise coaching for the {needs_n} dealer(s) in the "
            f"Needs improvement band — start from checklist gaps on their sheet, "
            f"not from a single section label."
        )
    for gap in common_gap_refs(model, n=2):
        actions.append(
            f"Network pattern: checklist item {gap['ref']} "
            f"({clean_text(gap['text'], 72)}) appears as a top gap for "
            f"{gap['dealer_count']} dealers — review whether the DB can remove "
            f"a shared blocker (tooling, training, stock, process)."
        )
    if incomplete:
        actions.append(
            f"Clear the incomplete / not-completed lane: {len(incomplete)} dealer(s) "
            f"need a finished evaluation or a conscious exit — do not treat these "
            f"rows as coaching targets for a low score."
        )
    else:
        actions.append(
            "Confirm monthly Pull ownership: who updates visited %, actions closed, "
            "and escalations open after each review cycle."
        )

    # De-dupe while preserving order; cap at n.
    seen: set[str] = set()
    out: list[str] = []
    for a in actions:
        if a in seen:
            continue
        seen.add(a)
        out.append(a)
        if len(out) >= n:
            break
    return out


PULL_SCORECARD_ROWS = (
    (
        "% dealers visited YTD",
        "Share of hit-list (or agreed priority) dealers that had a feedback "
        "review in the calendar year.",
    ),
    (
        "% suggested actions closed",
        "Commitments returned with proof and a done date, divided by actions "
        "still open from agreed reviews.",
    ),
    (
        "# incomplete cleared",
        "Not-completed / red-marked / zero-shell dealers moved to a finished "
        "evaluation or a conscious exit this month.",
    ),
    (
        "# escalations open",
        "Actions overdue more than 30 days, or blocked by a DB/ISZE issue "
        "(price, stock, tooling) without an owner.",
    ),
)


def section_rows(model: dict, dealer: dict | None) -> list[dict]:
    rows = []
    for sid in SECTIONS:
        sec = (dealer or {}).get("sections", {}).get(sid, {}) if dealer else {}
        p = sec.get("pct")
        avg = model["section_avg_pct"].get(sid) if model else None
        rows.append(
            {
                "id": sid,
                "label": SECTION_SHORT[sid],
                "score": sec.get("score"),
                "max": sec.get("max") or (model or {}).get("section_max", {}).get(sid),
                "pct": p,
                "country_avg_pct": avg,
                "gap": (p - avg) if p is not None and avg is not None else None,
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #

CSS = f"""
:root {{
  --navy:#{NAVY}; --terracotta:#{TERRACOTTA}; --good:#{GOOD}; --amber:#{AMBER};
  --grey:#{GREY}; --light:#{LIGHT}; --line:#d4dae3;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:#eef1f5; color:var(--navy);
  font-family:"Segoe UI",system-ui,-apple-system,sans-serif;
  font-size:10.2pt; line-height:1.35;
}}
.page {{
  background:#fff; width:210mm; min-height:296mm; margin:8mm auto; padding:11mm 12mm;
  box-shadow:0 2px 10px rgba(26,39,68,.12);
}}
.head {{ border-bottom:2.5px solid var(--navy); padding-bottom:6px; margin-bottom:9px;
        display:flex; justify-content:space-between; align-items:flex-end; gap:12px; }}
.head h1 {{ margin:0; font-size:15.5pt; letter-spacing:-.2px; }}
.head .sub {{ margin:2px 0 0; font-size:9pt; color:var(--grey); }}
.head .right {{ text-align:right; font-size:8.6pt; color:var(--grey); white-space:nowrap; }}
.head .right strong {{ display:block; color:var(--navy); font-size:10pt; }}
h2 {{ font-size:10.6pt; margin:0 0 6px; text-transform:uppercase; letter-spacing:.5px;
     color:var(--navy); border-bottom:1px solid var(--line); padding-bottom:3px; }}
.block {{ margin-bottom:9px; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:7px; }}
.kpi {{ background:var(--light); border-left:3.5px solid var(--terracotta);
       border-radius:5px; padding:7px 9px; }}
.kpi .v {{ font-size:16pt; font-weight:700; line-height:1.05; }}
.kpi .v.fill {{ display:block; width:100%; min-width:0; height:21px;
               border-bottom:1px dotted #8f9db0; margin-bottom:2px; }}
.kpi .l {{ font-size:7.8pt; color:var(--grey); text-transform:uppercase; letter-spacing:.4px; }}
.kpi .n {{ font-size:8.2pt; color:var(--grey); }}
.bandstrip {{ display:flex; align-items:center; gap:10px; background:var(--light);
             border-radius:5px; padding:8px 11px; margin-top:7px; font-size:9pt; }}
.pill {{ display:inline-block; font-size:9pt; font-weight:700; border-radius:4px;
        padding:2px 9px; white-space:nowrap; }}
.pill.good {{ background:#e5f4ec; color:var(--good); }}
.pill.medium {{ background:#f9f0d8; color:var(--amber); }}
.pill.weak {{ background:#f8e6e1; color:var(--terracotta); }}
.pill.blank {{ background:#fff; color:var(--grey); border:1px dashed var(--line); padding:2px 26px; }}
.scale {{ color:var(--grey); font-size:8.4pt; }}
table {{ width:100%; border-collapse:collapse; font-size:9.1pt; }}
th {{ text-align:left; font-size:7.8pt; text-transform:uppercase; letter-spacing:.4px;
     color:#fff; background:var(--navy); padding:5px 6px; font-weight:600; }}
td {{ padding:4.5px 6px; border-bottom:1px solid var(--line); vertical-align:top; }}
tr:nth-child(even) td {{ background:#fafbfd; }}
td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
td.sec {{ font-weight:700; white-space:nowrap; }}
td.q {{ color:#33415c; }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:11px; }}
.panel {{ border:1px solid var(--line); border-radius:6px; padding:9px 11px; }}
.panel h3 {{ margin:0 0 6px; font-size:9.4pt; text-transform:uppercase; letter-spacing:.4px; }}
.panel.pos h3 {{ color:var(--good); }}
.panel.neg h3 {{ color:var(--terracotta); }}
.panel ol {{ margin:0; padding-left:16px; }}
.panel li {{ margin-bottom:4px; }}
.panel li .ref {{ font-weight:700; }}
.panel li .meta {{ color:var(--grey); font-size:8.4pt; }}
.fill {{ border-bottom:1px dotted #9aa7b8; display:inline-block; min-width:60px; }}
.ident {{ display:flex; gap:18px; font-size:8.6pt; color:var(--grey);
         background:var(--light); border-radius:5px; padding:5px 10px; margin-bottom:8px; }}
.ident span.fill {{ min-width:110px; }}
.fillrow td {{ height:22px; }}
.hint {{ font-size:8.2pt; color:var(--grey); margin:-2px 0 5px; }}
.suggest td {{ padding:3.5px 6px; font-size:8.7pt; }}
.suggest td.action {{ color:#33415c; }}
.note {{ font-size:8.0pt; color:var(--grey); border-top:1px solid var(--line);
        padding-top:6px; margin-top:8px; }}
.note strong {{ color:var(--navy); }}
.reading {{ font-size:8.4pt; color:var(--grey); background:var(--light);
           border-left:3px solid var(--mid, #d4dae3); border-radius:4px;
           padding:6px 9px; margin:7px 0 0; }}
.dist {{ display:grid; grid-template-columns:repeat(3,1fr); gap:7px; }}
@media print {{
  @page {{ size:A4 portrait; margin:10mm; }}
  body {{ background:#fff; font-size:9.6pt; }}
  .page {{ width:auto; min-height:0; margin:0; padding:0; box-shadow:none;
          page-break-after:always; }}
  .page:last-child {{ page-break-after:auto; }}
  .block, .panel, table {{ page-break-inside:avoid; }}
}}
"""


def _doc(title: str, body: str) -> str:
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        f"<title>{escape(title)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n"
        f"{body}\n</body>\n</html>\n"
    )


def _head(title: str, sub: str, right_top: str, right_bot: str) -> str:
    return (
        '<div class="head"><div>'
        f"<h1>{title}</h1><p class=\"sub\">{sub}</p></div>"
        f'<div class="right"><strong>{right_top}</strong>{right_bot}</div></div>'
    )


def _scale_text() -> str:
    return (
        f"Bands: Good {BAND_GOOD_MIN * 100:.0f}% and above · "
        f"Medium {BAND_MEDIUM_MIN * 100:.0f}% to under {BAND_GOOD_MIN * 100:.0f}% · "
        f"Needs improvement below {BAND_MEDIUM_MIN * 100:.0f}%"
    )


def _basis_note(model: dict | None) -> str:
    if model is None:
        return (
            '<div class="note"><strong>Average basis.</strong> '
            + escape(AVERAGE_RULE_NOTE)
            + "</div>"
        )
    b = model["basis"]
    if b["n_excluded"]:
        basis = (
            f"The {escape(model['country'])} average shown here is calculated on "
            f"<strong>{b['n_included']} of {b['n_all']}</strong> evaluated dealers. "
            f"{escape(b['rule'])} Excluded dealers keep their own feedback sheet and "
            "stay in the network list."
        )
    else:
        basis = (
            f"The {escape(model['country'])} average shown here is calculated on "
            f"<strong>all {b['n_all']}</strong> evaluated dealers. "
            f"{escape(b['rule'])}"
        )
    return (
        '<div class="note"><strong>Average basis.</strong> '
        f"{basis} "
        f"Source: 2026 IDS evaluation result report, {escape(model['country'])}. "
        f"Maximum score {model['total_max']:g} points."
        "</div>"
    )


def _item_li(item: dict | None, *, blank: bool) -> str:
    if blank or item is None:
        return (
            '<li><span class="ref">____</span> '
            '<span class="fill" style="min-width:250px">&nbsp;</span>'
            '<div class="meta">Points <span class="fill" style="min-width:60px">&nbsp;</span></div></li>'
        )
    return (
        f'<li><span class="ref">{escape(item["ref"])}</span> '
        f"{escape(clean_text(item['text'], 132))}"
        f'<div class="meta">Section {escape(item["section"])} · '
        f"{points(item['score'], item['max'])} points · "
        f"country average {pct(item['country_avg_pct'])}</div></li>"
    )


def exec_block(model: dict | None, dealer: dict | None, *, blank: bool = False) -> str:
    """Layer A — the executive summary page."""
    country = model["country"] if model else "____________"
    total_max = (model or {}).get("total_max")

    if blank or dealer is None:
        head = _head(
            "Dealer feedback — executive summary",
            "Isuzu Dealer Standards 2026 · dealer: "
            '<span class="fill" style="min-width:210px">&nbsp;</span>',
            "Distributor: ______________",
            'Evaluation date: __________',
        )
        band_html = '<span class="pill blank">&nbsp;</span>'
        kpis = [
            ("&nbsp;", "Total score", "of 280 points"),
            ("&nbsp;", f"{escape(country)} average", "dealers in average: ____"),
            ("&nbsp;", "Difference vs average", "percentage points"),
            ("&nbsp;", f"Rank in {escape(country)}", "of ____ dealers"),
        ]
        kpi_html = "".join(
            f'<div class="kpi"><div class="v fill">{v}</div>'
            f'<div class="l">{l}</div><div class="n">{n}</div></div>'
            for v, l, n in kpis
        )
        strengths = [None, None, None]
        gaps = [None, None, None]
    else:
        head = _head(
            escape(dealer["name"]),
            f"Isuzu Dealer Standards 2026 · executive summary · {escape(country)}",
            f"Rank {dealer['rank']} of {len(model['dealers'])}",
            f"Built {escape(model['built_on'])} · {VERSION}",
        )
        band_html = band_pill(dealer["band"]) or f'<span class="pill">{NA}</span>'
        kpi_html = "".join(
            [
                '<div class="kpi"><div class="v">'
                f'{pct(dealer["total_pct"])}</div><div class="l">Total score</div>'
                f'<div class="n">{points(dealer["total"], total_max)} points</div></div>',
                '<div class="kpi"><div class="v">'
                f'{pct(model["country_avg_pct"])}</div>'
                f'<div class="l">{escape(country)} average</div>'
                f'<div class="n">{model["basis"]["n_included"]} of '
                f'{model["basis"]["n_all"]} dealers in average</div></div>',
                '<div class="kpi"><div class="v">'
                f'{pp(dealer["vs_country_pp"])}</div>'
                '<div class="l">Difference vs average</div>'
                '<div class="n">percentage points</div></div>',
                '<div class="kpi"><div class="v">'
                # Named explicitly: UK LCV and UK CV are separate networks, so
                # "rank in country" would invite the wrong comparison.
                f'{dealer["rank"]}</div>'
                f'<div class="l">Rank in {escape(country)}</div>'
                f'<div class="n">of {len(model["dealers"])} dealers</div></div>',
            ]
        )
        strengths = top_strengths(model, dealer) or [None]
        gaps = top_gaps(model, dealer) or [None]
        while len(strengths) < 3:
            strengths.append(None)
        while len(gaps) < 3:
            gaps.append(None)

    strengths_li = "".join(
        _item_li(i, blank=blank or i is None) for i in strengths[:3]
    )
    gaps_li = "".join(_item_li(i, blank=blank or i is None) for i in gaps[:3])

    # Suggested next steps on the one-pager — same gap source as Kaizen, starters only.
    if blank or dealer is None:
        seeded_actions: list[dict | None] = [None] * EXEC_SUGGESTED_ACTIONS_N
    else:
        seeded_actions = list(top_gaps(model, dealer, n=EXEC_SUGGESTED_ACTIONS_N))
        while len(seeded_actions) < EXEC_SUGGESTED_ACTIONS_N:
            seeded_actions.append(None)

    action_trs = []
    for item in seeded_actions:
        if item is None:
            action_trs.append(
                '<tr class="fillrow"><td></td><td></td><td></td><td></td></tr>'
            )
        else:
            action_trs.append(
                '<tr class="suggest"><td class="action">'
                f"<strong>{escape(item['ref'])}</strong> — "
                f"{escape(clean_text(item['text'], EXEC_ACTION_TEXT_LIMIT))}"
                "</td><td></td><td></td><td></td></tr>"
            )

    # Evaluation date and address come from the report where the market filled them
    # in, otherwise they stay fill-in fields rather than being invented. The
    # evaluator column holds individual people's names and is deliberately not
    # printed on a shared sheet.
    addr = (dealer or {}).get("address") if not blank else None
    edate = (dealer or {}).get("evaluation_date") if not blank else None
    blank_field = '<span class="fill">&nbsp;</span>'
    ident = (
        '<div class="ident">'
        f"<div>Evaluation date {escape(str(edate)) if edate else blank_field}</div>"
        f"<div>Address {escape(clean_text(addr, 72)) if addr else blank_field}</div>"
        "</div>"
    )

    return f"""<section class="page">
{head}
{ident}
<div class="block">
  <h2>Result</h2>
  <div class="kpis">{kpi_html}</div>
  <div class="bandstrip"><span>Band</span>{band_html}
    <span class="scale">{_scale_text()}</span></div>
</div>
<div class="block two">
  <div class="panel pos"><h3>Top 3 strengths</h3><ol>{strengths_li}</ol></div>
  <div class="panel neg"><h3>Top 3 gaps</h3><ol>{gaps_li}</ol></div>
</div>
<div class="block">
  <h2>Suggested next steps — edit in the meeting</h2>
  <p class="hint">Starters from the largest checklist gaps above. Change, drop or add
    actions in the meeting. Owner, target date and proof stay blank until agreed.</p>
  <table>
    <thead><tr><th style="width:52%">Action</th><th style="width:18%">Owner (role)</th>
    <th style="width:15%">Target date</th><th style="width:15%">Proof</th></tr></thead>
    <tbody>
      {"".join(action_trs)}
    </tbody>
  </table>
</div>
{_basis_note(model if not blank else None)}
</section>"""


def workshop_pack_html(model: dict | None, dealer: dict | None, *, blank: bool = False) -> str:
    """Layer B — executive summary page plus scorecard and Kaizen actions."""
    rows = section_rows(model, dealer if not blank else None)
    sec_html = "".join(
        f'<tr><td class="sec">{r["id"]}</td><td>{escape(r["label"])}</td>'
        f'<td class="num">{points(r["score"], r["max"], "" if blank else NA)}</td>'
        f'<td class="num">{pct(r["pct"], "" if blank else NA)}</td>'
        f'<td class="num">{pct(r["country_avg_pct"], "" if blank else NA)}</td>'
        f'<td class="num">{pp(r["gap"], "" if blank else NA)}</td></tr>'
        for r in rows
    )

    seeded = [] if blank or dealer is None else top_gaps(model, dealer, n=5)
    action_rows = []
    for i in range(5):
        item = seeded[i] if i < len(seeded) else None
        if item is None:
            action_rows.append(
                f'<tr class="fillrow"><td class="num">{i + 1}</td><td></td><td></td>'
                "<td></td><td></td><td></td></tr>"
            )
        else:
            action_rows.append(
                f'<tr><td class="num">{i + 1}</td><td class="sec">{escape(item["section"])}</td>'
                f'<td><strong>{escape(item["ref"])}</strong> {escape(clean_text(item["text"], 150))}'
                f'<br><span class="meta" style="color:#6b7a90;font-size:8.4pt">'
                f'Now {points(item["score"], item["max"])} points · '
                f'{item["lost"]:g} point(s) available</span></td>'
                "<td></td><td></td><td></td></tr>"
            )

    country = model["country"] if model and not blank else "____________"
    name = dealer["name"] if dealer and not blank else "____________________"
    head = _head(
        "Dealer workshop pack",
        f"Isuzu Dealer Standards 2026 · {escape(name)} · {escape(country)}",
        "Section scorecard and actions",
        f"{'' if blank else escape((model or {}).get('built_on', ''))} {VERSION}",
    )

    second = f"""<section class="page">
{head}
<div class="block">
  <h2>Section scorecard A–E</h2>
  <table>
    <thead><tr><th style="width:4%">&nbsp;</th><th>Section</th>
    <th class="num" style="width:13%">Points</th><th class="num" style="width:10%">Score</th>
    <th class="num" style="width:15%">Country average</th>
    <th class="num" style="width:12%">Difference</th></tr></thead>
    <tbody>{sec_html}</tbody>
  </table>
  <p class="reading">{SECTION_NOTE}</p>
</div>
<div class="block">
  <h2>Kaizen actions — agree 3 to 5 with the dealer</h2>
  <table>
    <thead><tr><th style="width:4%">#</th><th style="width:6%">Sec.</th>
    <th>Action (largest scored gaps are pre-filled)</th>
    <th style="width:14%">Owner (role)</th><th style="width:12%">Target date</th>
    <th style="width:14%">Proof / evidence</th></tr></thead>
    <tbody>{"".join(action_rows)}</tbody>
  </table>
</div>
<div class="block">
  <h2>Dealer confirmation</h2>
  <table>
    <thead><tr><th>Dealer representative (role)</th><th>Distributor representative (role)</th>
    <th style="width:18%">Date</th><th style="width:18%">Next review</th></tr></thead>
    <tbody><tr class="fillrow"><td></td><td></td><td></td><td></td></tr></tbody>
  </table>
</div>
{_basis_note(model if not blank else None)}
</section>"""

    return _doc(
        f"IDS 2026 dealer workshop pack — {name}",
        exec_block(model, dealer, blank=blank) + "\n" + second,
    )


def exec_summary_html(model: dict | None, dealer: dict | None, *, blank: bool = False) -> str:
    name = dealer["name"] if dealer and not blank else "template"
    return _doc(
        f"IDS 2026 dealer feedback — {name}",
        exec_block(model, dealer, blank=blank),
    )


def _dealer_name_cell(d: dict, annex: dict | None) -> str:
    name_cell = escape(d["name"])
    if d.get("multi_site") and d.get("address"):
        name_cell += (
            f'<br><span style="color:#6b7a90;font-size:8pt">'
            f'{escape(clean_text(d["address"], 70))}</span>'
        )
    if annex:
        name_cell = f'<a href="{escape(annex["href"])}">{name_cell}</a>'
    return name_cell


def rollup_html(model: dict, annexes: list[dict]) -> str:
    """Layer C — DB rollup: diagnose / contract / pull overview for one distributor."""
    b = model["basis"]
    total = b["n_all"]
    counts = model["band_counts"]
    dist = "".join(
        f'<div class="kpi"><div class="v">{counts[bl]}</div>'
        f'<div class="l">{bl}</div>'
        f'<div class="n">{counts[bl] / b["n_included"] * 100:.0f}% of dealers in average</div></div>'
        if b["n_included"]
        else f'<div class="kpi"><div class="v">{NA}</div><div class="l">{bl}</div><div class="n"></div></div>'
        for bl in BAND_LABELS
    )

    scored_sections = sorted(
        ((sid, v) for sid in SECTIONS if (v := model["section_avg_pct"].get(sid)) is not None),
        key=lambda x: x[1],
    )
    unscored_sections = [
        (sid, None) for sid in SECTIONS if model["section_avg_pct"].get(sid) is None
    ]
    weakest = scored_sections[0] if scored_sections else (None, None)
    strongest = scored_sections[-1] if scored_sections else (None, None)

    def _sec_row(sid: str, v: float | None) -> str:
        smax = model["section_max"].get(sid)
        return (
            f'<tr><td class="sec">{sid}</td><td>{escape(SECTION_SHORT[sid])}</td>'
            f'<td class="num">{f"{smax:g}" if smax else NA}</td>'
            f'<td class="num">{pct(v)}</td>'
            f'<td class="num">{model["section_scored_n"].get(sid, 0)}</td></tr>'
        )

    sec_html = "".join(
        _sec_row(sid, v) for sid, v in [*scored_sections, *unscored_sections]
    )

    def _sec_caption(pair: tuple[str | None, float | None]) -> str:
        sid = pair[0]
        if sid is None:
            return NA
        return f"Section {sid} — {escape(SECTION_SHORT[sid])}"

    annex_by_key = {a["file_key"]: a for a in annexes}
    hits = hit_list_dealers(model)
    incomplete = incomplete_dealers(model)
    db_actions = suggested_db_actions(model)

    hit_rows = []
    for i, d in enumerate(hits, 1):
        annex = annex_by_key.get(d["file_key"])
        hit_rows.append(
            f'<tr><td class="num">{i}</td>'
            f'<td>{_dealer_name_cell(d, annex)}</td>'
            f'<td class="num">{pct(d["total_pct"])}</td>'
            f'<td class="num">{pp(d["vs_country_pp"])}</td>'
            f'<td>{band_pill(d["band"]) or NA}</td>'
            f'<td>{escape(hit_list_why(d))}</td></tr>'
        )
    if not hit_rows:
        hit_rows.append(
            '<tr><td colspan="6">No dealers below the market average or in the '
            "Needs improvement band. Use the dealer list to plan maintenance visits."
            "</td></tr>"
        )

    if model["country"] in AVG_EXCLUDE_RED:
        incomplete_note = (
            f"Dealers marked red in the 2026 ranking for {escape(model['country'])} "
            "(evaluation not completed). They stay in the network and keep a sheet, "
            "but are outside the average and should not burn visit time as low scores."
        )
    else:
        incomplete_note = (
            "Dealers with a zero or blank total score in this market's evaluation "
            "(incomplete / not completed). If none are listed, there is no incomplete "
            "lane for this market."
        )

    incomplete_rows = []
    for d in incomplete:
        annex = annex_by_key.get(d["file_key"])
        reason = (
            "Red-marked — evaluation not completed"
            if model["country"] in AVG_EXCLUDE_RED
            else "Zero / blank total — treat as incomplete, not as a coaching score"
        )
        incomplete_rows.append(
            f'<tr><td>{_dealer_name_cell(d, annex)}</td>'
            f'<td class="num">{pct(d["total_pct"])}</td>'
            f'<td>{band_pill(d["band"]) or NA}</td>'
            f'<td>{escape(reason)}</td></tr>'
        )
    if not incomplete_rows:
        incomplete_rows.append(
            "<tr><td colspan=\"4\"><strong>None.</strong> No incomplete / "
            "not-completed dealers identified for this market.</td></tr>"
        )

    action_trs = []
    for i, text in enumerate(db_actions, 1):
        action_trs.append(
            f'<tr class="suggest"><td class="num">{i}</td>'
            f'<td class="action">{escape(text)}</td>'
            "<td></td><td></td><td></td></tr>"
        )
    while len(action_trs) < 3:
        n = len(action_trs) + 1
        action_trs.append(
            f'<tr class="fillrow"><td class="num">{n}</td><td></td>'
            "<td></td><td></td><td></td></tr>"
        )

    pull_trs = "".join(
        f"<tr><td>{escape(metric)}</td>"
        f'<td class="num fill" style="min-width:48px">&nbsp;</td>'
        f"<td>{escape(defn)}</td>"
        "<td></td><td></td></tr>"
        for metric, defn in PULL_SCORECARD_ROWS
    )

    dealer_rows = []
    for d in sorted(
        model["dealers"], key=lambda x: (x["total_pct"] is None, -(x["total_pct"] or 0))
    ):
        annex = annex_by_key.get(d["file_key"])
        dealer_rows.append(
            f'<tr><td class="num">{d["rank"]}</td>'
            f'<td>{_dealer_name_cell(d, annex)}</td>'
            f'<td class="num">{points(d["total"], model["total_max"])}</td>'
            f'<td class="num">{pct(d["total_pct"])}</td>'
            f'<td class="num">{pp(d["vs_country_pp"])}</td>'
            f'<td>{band_pill(d["band"]) or NA}</td>'
            f'<td>{"Yes" if d["in_average"] else "No"}</td></tr>'
        )

    head = _head(
        f"{escape(model['country'])} — dealer network feedback",
        "Isuzu Dealer Standards 2026 · distributor rollup · primary DB overview",
        f"{total} dealers evaluated",
        f"Built {escape(model['built_on'])} · {VERSION}",
    )

    return _doc(
        f"IDS 2026 network rollup — {model['country']}",
        f"""<section class="page">
{head}
<div class="block">
  <h2>Network result</h2>
  <div class="kpis">
    <div class="kpi"><div class="v">{pct(model["country_avg_pct"])}</div>
      <div class="l">Network average</div>
      <div class="n">{b["n_included"]} of {b["n_all"]} dealers in average</div></div>
    <div class="kpi"><div class="v">{total}</div><div class="l">Dealers evaluated</div>
      <div class="n">{b["n_excluded"]} outside the average</div></div>
    <div class="kpi"><div class="v">{pct(strongest[1])}</div>
      <div class="l">Highest section average</div>
      <div class="n">{_sec_caption(strongest)}</div></div>
    <div class="kpi"><div class="v">{pct(weakest[1])}</div>
      <div class="l">Lowest section average</div>
      <div class="n">{_sec_caption(weakest)}</div></div>
  </div>
  <div class="bandstrip"><span class="scale">{_scale_text()}</span></div>
</div>
<div class="block">
  <h2>Hit list — priority dealers to visit</h2>
  <p class="hint">Below the market average and/or Needs improvement. Cap {HIT_LIST_MAX}.
    Incomplete / not-completed dealers are listed separately and are not visit
    targets for a “low score”. Open the dealer workshop pack for the visit.</p>
  <table>
    <thead><tr><th class="num" style="width:5%">#</th><th>Dealer</th>
    <th class="num" style="width:9%">Score</th>
    <th class="num" style="width:11%">vs average</th>
    <th style="width:14%">Band</th><th>Why on the list</th></tr></thead>
    <tbody>{"".join(hit_rows)}</tbody>
  </table>
</div>
<div class="block">
  <h2>Incomplete / not-completed lane</h2>
  <p class="hint">{incomplete_note}</p>
  <table>
    <thead><tr><th>Dealer</th><th class="num" style="width:10%">Score</th>
    <th style="width:14%">Band</th><th>Reason</th></tr></thead>
    <tbody>{"".join(incomplete_rows)}</tbody>
  </table>
</div>
{_basis_note(model)}
</section>
<section class="page">
{_head(f"{escape(model['country'])} — DB next steps &amp; Pull", "Isuzu Dealer Standards 2026 · distributor rollup", f"{total} dealers", f"{VERSION}")}
<div class="block">
  <h2>Suggested DB-level next steps — edit in the DB planning meeting</h2>
  <p class="hint">Network actions derived from the hit list, common checklist gaps,
    and the incomplete lane. Owner, target date and proof stay blank until the
    distributor planning meeting.</p>
  <table>
    <thead><tr><th class="num" style="width:5%">#</th>
    <th style="width:52%">Suggested action</th>
    <th style="width:15%">Owner (role)</th>
    <th style="width:14%">Target date</th>
    <th style="width:14%">Proof</th></tr></thead>
    <tbody>{"".join(action_trs)}</tbody>
  </table>
</div>
<div class="block">
  <h2>Pull scorecard — monthly return (fill in)</h2>
  <p class="hint">Blank on purpose. Measure the distributor’s process, not a fake
    monthly IDS score. Definitions stay fixed; values are entered after reviews.</p>
  <table>
    <thead><tr><th style="width:22%">Metric</th>
    <th class="num" style="width:10%">This month</th>
    <th>Definition</th>
    <th style="width:14%">Owner</th>
    <th style="width:12%">As of</th></tr></thead>
    <tbody>{pull_trs}</tbody>
  </table>
</div>
<div class="block">
  <h2>Band distribution</h2>
  <div class="dist">{dist}</div>
</div>
<div class="block">
  <h2>Sections across the network — lowest average first</h2>
  <table>
    <thead><tr><th style="width:5%">&nbsp;</th><th>Section</th>
    <th class="num" style="width:12%">Max points</th>
    <th class="num" style="width:16%">Network average</th>
    <th class="num" style="width:14%">Dealers scored</th></tr></thead>
    <tbody>{sec_html}</tbody>
  </table>
  <p class="reading">{SECTION_NOTE}</p>
</div>
{_basis_note(model)}
</section>
<section class="page">
{_head(f"{escape(model['country'])} — dealer list", "Isuzu Dealer Standards 2026 · distributor rollup", f"{total} dealers", f"{VERSION}")}
<div class="block">
  <h2>All dealers, highest score first</h2>
  <p class="hint">Dealer workshop packs are annexes for the visit — this rollup is
    the overview the distributor runs from.</p>
  <table>
    <thead><tr><th class="num" style="width:6%">Rank</th><th>Dealer</th>
    <th class="num" style="width:12%">Points</th><th class="num" style="width:9%">Score</th>
    <th class="num" style="width:11%">vs average</th><th style="width:15%">Band</th>
    <th style="width:10%">In average</th></tr></thead>
    <tbody>{"".join(dealer_rows)}</tbody>
  </table>
</div>
{_basis_note(model)}
</section>""",
    )


# --------------------------------------------------------------------------- #
# Excel
# --------------------------------------------------------------------------- #

THIN = Side(style="thin", color="D4DAE3")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
F_TITLE = Font(name="Segoe UI", size=15, bold=True, color=NAVY)
F_SUB = Font(name="Segoe UI", size=9, color=GREY)
F_H2 = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
F_LABEL = Font(name="Segoe UI", size=9, color=GREY)
F_BIG = Font(name="Segoe UI", size=14, bold=True, color=NAVY)
F_BODY = Font(name="Segoe UI", size=9.5, color=NAVY)
F_BOLD = Font(name="Segoe UI", size=9.5, bold=True, color=NAVY)
F_NOTE = Font(name="Segoe UI", size=8, italic=True, color=GREY)
FILL_NAVY = PatternFill("solid", fgColor=NAVY)
FILL_LIGHT = PatternFill("solid", fgColor=LIGHT)
FILL_INPUT = PatternFill("solid", fgColor="FFFDF2")
WRAP = Alignment(wrap_text=True, vertical="top")
RIGHT = Alignment(horizontal="right")


def _section_header(ws, row: int, text: str, last_col: int) -> None:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    c = ws.cell(row, 1, text.upper())
    c.font = F_H2
    c.fill = FILL_NAVY
    c.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[row].height = 19


def _table_header(ws, row: int, headers: list[str], widths: list[int]) -> None:
    for i, (h, w) in enumerate(zip(headers, widths), 1):
        c = ws.cell(row, i, h)
        c.font = F_H2
        c.fill = FILL_NAVY
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BOX
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[row].height = 26


def _fit_page(ws, print_area: str, *, landscape: bool = False) -> None:
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.print_area = print_area
    ws.sheet_view.showGridLines = False


def _readme_sheet(wb: Workbook, model: dict | None, *, blank: bool) -> None:
    ws = wb.create_sheet("Read me")
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 108
    ws.sheet_view.showGridLines = False
    ws["B2"] = "Isuzu Dealer Standards 2026 — dealer feedback sheet"
    ws["B2"].font = F_TITLE
    ws["B3"] = f"Distributor working document {VERSION}"
    ws["B3"].font = F_SUB
    lines = [
        ("How to use this file", None),
        ("1.", "Dealer fiche — one printable page per dealer. Print or save as PDF and use it to open the review. Suggested next steps are pre-filled from the largest checklist gaps; edit them in the meeting and add owner, target date and proof."),
        ("2.", "Sections A-E — where the dealer stands per section against the country average."),
        ("3.", "Kaizen actions — agree 3 to 5 actions. The largest individual checklist gaps are pre-filled; add owner, target date and proof."),
        ("4.", "Commitments — the block the dealer keeps. Return this file and the commitments of every dealer can be consolidated into one list."),
        ("5.", "Master data — the full country table, ready for your own pivots and filters."),
        ("Scoring", None),
        ("", f"Maximum score {'280' if blank else format(model['total_max'], 'g')} points across sections A to E."),
        ("", f"Bands: {_scale_text_plain()}."),
        ("Reading sections A–E", None),
        ("", SECTION_NOTE),
        ("Average basis", None),
        ("", AVERAGE_RULE_NOTE),
    ]
    if model and not blank:
        lines.append(("", _basis_note_plain(model).replace("Average basis. ", "This file: ")))
    lines.append(("Blank fields", None))
    lines.append(
        (
            "",
            f"Fields shown as {NA} are not available in the 2026 evaluation data. "
            "They are left empty on purpose rather than estimated.",
        )
    )

    row = 5
    for tag, text in lines:
        if text is None:
            ws.cell(row, 2, tag).font = Font(
                name="Segoe UI", size=10.5, bold=True, color=TERRACOTTA
            )
            row += 1
            continue
        ws.cell(row, 1, tag).font = F_BOLD
        c = ws.cell(row, 2, text)
        c.font = F_BODY
        c.alignment = WRAP
        ws.row_dimensions[row].height = 15 + 14 * (len(text) // 105)
        row += 1
    _fit_page(ws, f"A1:B{row}")


def _fiche_sheet(wb: Workbook, model: dict | None, dealer: dict | None, *, blank: bool) -> None:
    """Printable dealer fiche — the Excel twin of layer A."""
    ws = wb.create_sheet("Dealer fiche")
    ws.sheet_view.showGridLines = False
    widths = [12, 30, 13, 13, 13, 15]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.merge_cells("A1:F1")
    ws["A1"] = "" if blank else dealer["name"]
    ws["A1"].font = F_TITLE
    ws.row_dimensions[1].height = 22
    ws.merge_cells("A2:F2")
    ws["A2"] = (
        "Isuzu Dealer Standards 2026 · executive summary"
        if blank
        else f"Isuzu Dealer Standards 2026 · executive summary · {model['country']}"
    )
    ws["A2"].font = F_SUB

    # From the report where the market filled it in, otherwise a fill-in field.
    # The evaluator column holds people's names and is not printed here.
    ws.merge_cells("A3:F3")
    ident = ws["A3"]
    addr = (dealer or {}).get("address") if not blank else None
    edate = (dealer or {}).get("evaluation_date") if not blank else None
    ident.value = (
        f"Evaluation date: {edate or '____________'}"
        f"     Address: {clean_text(addr, 70) if addr else '____________________'}"
    )
    ident.font = F_LABEL
    ident.fill = FILL_INPUT
    ws.row_dimensions[3].height = 16

    row = 5
    _section_header(ws, row, "Result", 6)
    row += 1
    kpi = [
        (
            "Total score",
            None if blank else dealer["total_pct"],
            "pct",
            "" if blank else f"{points(dealer['total'], model['total_max'])} points",
        ),
        (
            f"{'Country' if blank else model['country']} average",
            None if blank else model["country_avg_pct"],
            "pct",
            ""
            if blank
            else f"{model['basis']['n_included']} of {model['basis']['n_all']} dealers in average",
        ),
        (
            "Difference vs average",
            None if blank else dealer["vs_country_pp"],
            "pp",
            "percentage points",
        ),
        (
            f"Rank in {'market' if blank else model['country']}",
            None if blank else dealer["rank"],
            "int",
            "" if blank else f"of {len(model['dealers'])} dealers",
        ),
        ("Band", None if blank else dealer["band"], "text", _scale_text_plain()),
    ]
    for label, value, kind, note in kpi:
        ws.cell(row, 1, label).font = F_LABEL
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        c = ws.cell(row, 3, _xl_value(value, kind))
        c.font = F_BIG
        c.alignment = RIGHT
        if kind == "pct":
            c.number_format = "0.0%"
        elif kind == "pp":
            c.number_format = "+0.0;-0.0"
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=6)
        n = ws.cell(row, 4, note)
        n.font = F_LABEL
        n.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[row].height = 20
        row += 1

    row += 1
    _section_header(ws, row, "Top 3 strengths", 6)
    row += 1
    strengths = [] if blank or dealer is None else top_strengths(model, dealer)
    row = _items_block(ws, row, strengths, blank=blank)

    row += 1
    _section_header(ws, row, "Top 3 gaps", 6)
    row += 1
    gaps = [] if blank or dealer is None else top_gaps(model, dealer)
    row = _items_block(ws, row, gaps, blank=blank)

    row += 1
    _section_header(ws, row, "Suggested next steps — edit in the meeting", 6)
    row += 1
    hint = ws.cell(
        row,
        1,
        "Starters from the largest checklist gaps above. Change, drop or add in "
        "the meeting. Owner, target date and proof stay blank until agreed.",
    )
    hint.font = F_NOTE
    hint.alignment = WRAP
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    ws.row_dimensions[row].height = 28
    row += 1
    _table_header(ws, row, ["Action", "", "", "Owner (role)", "Target date", "Proof"], widths)
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    row += 1
    seeded = (
        []
        if blank or dealer is None
        else top_gaps(model, dealer, n=EXEC_SUGGESTED_ACTIONS_N)
    )
    for i in range(EXEC_SUGGESTED_ACTIONS_N):
        item = seeded[i] if i < len(seeded) else None
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
        action = ws.cell(
            row,
            1,
            "" if item is None else suggested_action_text(item),
        )
        action.font = F_BODY
        action.alignment = WRAP
        for col in range(1, 7):
            c = ws.cell(row, col)
            c.border = BOX
            if item is None or col >= 4:
                c.fill = FILL_INPUT
        ws.row_dimensions[row].height = 26 if item is None else 32
        row += 1

    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row + 2, end_column=6)
    note = ws.cell(row, 1, _basis_note_plain(model if not blank else None))
    note.font = F_NOTE
    note.alignment = WRAP
    _fit_page(ws, f"A1:F{row + 2}")


def _items_block(ws, row: int, items: list[dict], *, blank: bool) -> int:
    _table_header(
        ws,
        row,
        ["Ref", "Checklist item", "", "", "Points", "Country average"],
        [12, 30, 13, 13, 13, 15],
    )
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
    row += 1
    for i in range(3):
        item = items[i] if i < len(items) else None
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
        ws.cell(row, 1, "" if item is None else item["ref"]).font = F_BOLD
        c = ws.cell(row, 2, "" if item is None else clean_text(item["text"], 150))
        c.font = F_BODY
        c.alignment = WRAP
        p = ws.cell(row, 5, "" if item is None else points(item["score"], item["max"]))
        p.font = F_BODY
        p.alignment = RIGHT
        a = ws.cell(
            row, 6, "" if item is None else _xl_value(item["country_avg_pct"], "pct")
        )
        a.font = F_BODY
        a.alignment = RIGHT
        if item is not None and item["country_avg_pct"] is not None:
            a.number_format = "0.0%"
        for col in range(1, 7):
            ws.cell(row, col).border = BOX
            if item is None:
                ws.cell(row, col).fill = FILL_INPUT
        ws.row_dimensions[row].height = 28
        row += 1
    return row


def _xl_value(value: Any, kind: str) -> Any:
    if value is None:
        return ""
    if kind == "pp":
        return round(value * 100, 1)
    return value


def _scale_text_plain() -> str:
    return (
        f"Good {BAND_GOOD_MIN * 100:.0f}% and above, Medium "
        f"{BAND_MEDIUM_MIN * 100:.0f}% to under {BAND_GOOD_MIN * 100:.0f}%, "
        f"Needs improvement below {BAND_MEDIUM_MIN * 100:.0f}%"
    )


def _basis_note_plain(model: dict | None) -> str:
    if model is None:
        return f"Average basis. {AVERAGE_RULE_NOTE}"
    b = model["basis"]
    if b["n_excluded"]:
        basis = (
            f"The {model['country']} average is calculated on {b['n_included']} of "
            f"{b['n_all']} evaluated dealers. {b['rule']} Excluded dealers keep their "
            "own feedback sheet and stay in the network list."
        )
    else:
        basis = (
            f"The {model['country']} average is calculated on all {b['n_all']} "
            f"evaluated dealers. {b['rule']}"
        )
    return (
        f"Average basis. {basis} "
        f"Source: 2026 IDS evaluation result report, {model['country']}. "
        f"Maximum score {model['total_max']:g} points."
    )


def _sections_sheet(wb: Workbook, model: dict | None, dealer: dict | None, *, blank: bool) -> None:
    ws = wb.create_sheet("Sections A-E")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:G1")
    ws["A1"] = "Section scorecard A to E"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:G2")
    ws["A2"] = (
        "Isuzu Dealer Standards 2026"
        if blank
        else f"{dealer['name']} · {model['country']}"
    )
    ws["A2"].font = F_SUB

    headers = ["", "Section", "Points", "Max", "Score", "Country average", "Difference"]
    widths = [5, 42, 10, 8, 10, 16, 12]
    _table_header(ws, 4, headers, widths)
    row = 5
    for r in section_rows(model, dealer if not blank else None):
        ws.cell(row, 1, r["id"]).font = F_BOLD
        ws.cell(row, 2, r["label"]).font = F_BODY
        for col, (val, fmt) in enumerate(
            [
                (r["score"] if not blank else "", None),
                (r["max"] if r["max"] else "", None),
                (_xl_value(r["pct"], "pct") if not blank else "", "0.0%"),
                (_xl_value(r["country_avg_pct"], "pct") if not blank else "", "0.0%"),
                (_xl_value(r["gap"], "pp") if not blank else "", "+0.0;-0.0"),
            ],
            start=3,
        ):
            c = ws.cell(row, col, val)
            c.font = F_BODY
            c.alignment = RIGHT
            if fmt and val != "":
                c.number_format = fmt
        for col in range(1, 8):
            ws.cell(row, col).border = BOX
        row += 1

    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row + 3, end_column=7)
    c = ws.cell(row, 1, SECTION_NOTE)
    c.font = F_NOTE
    c.alignment = WRAP
    row += 5
    ws.merge_cells(start_row=row, start_column=1, end_row=row + 2, end_column=7)
    c = ws.cell(row, 1, _basis_note_plain(model if not blank else None))
    c.font = F_NOTE
    c.alignment = WRAP
    _fit_page(ws, f"A1:G{row + 2}")


def _kaizen_sheet(wb: Workbook, model: dict | None, dealer: dict | None, *, blank: bool) -> None:
    ws = wb.create_sheet("Kaizen actions")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:G1")
    ws["A1"] = "Kaizen actions — agree 3 to 5 with the dealer"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:G2")
    ws["A2"] = (
        "Add owner, target date and proof for each action."
        if blank
        else f"{dealer['name']} · {model['country']} · largest scored gaps are pre-filled"
    )
    ws["A2"].font = F_SUB

    headers = [
        "#",
        "Sec.",
        "Ref",
        "Action / checklist item",
        "Owner (role)",
        "Target date",
        "Proof / evidence",
    ]
    widths = [5, 6, 10, 58, 18, 14, 24]
    _table_header(ws, 4, headers, widths)
    seeded = [] if blank or dealer is None else top_gaps(model, dealer, n=5)
    row = 5
    for i in range(5):
        item = seeded[i] if i < len(seeded) else None
        ws.cell(row, 1, i + 1).font = F_BOLD
        ws.cell(row, 2, "" if item is None else item["section"]).font = F_BODY
        ws.cell(row, 3, "" if item is None else item["ref"]).font = F_BODY
        text = (
            ""
            if item is None
            else f"{clean_text(item['text'], 220)} "
            f"(now {points(item['score'], item['max'])} points)"
        )
        c = ws.cell(row, 4, text)
        c.font = F_BODY
        c.alignment = WRAP
        for col in range(1, 8):
            ws.cell(row, col).border = BOX
            if col >= 5:
                ws.cell(row, col).fill = FILL_INPUT
        ws.cell(row, 6).number_format = "yyyy-mm-dd"
        ws.row_dimensions[row].height = 34
        row += 1

    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row + 1, end_column=7)
    c = ws.cell(
        row,
        1,
        "Pre-filled actions restate the 2026 checklist item where points were lost. "
        "Replace or reword them freely — the dealer must recognise the action as its own.",
    )
    c.font = F_NOTE
    c.alignment = WRAP
    _fit_page(ws, f"A1:G{row + 1}", landscape=True)


def _commitments_sheet(wb: Workbook, model: dict | None, dealer: dict | None, *, blank: bool) -> None:
    """Layer D — the block the dealer returns; consolidate() reads exactly this."""
    ws = wb.create_sheet("Commitments")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:I1")
    ws["A1"] = "Commitments — return this sheet after the review"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:I2")
    ws["A2"] = (
        "One row per commitment. Keep the column order so all dealers can be "
        "consolidated into one list."
    )
    ws["A2"].font = F_SUB

    widths = [16, 30, 10, 8, 54, 18, 14, 26, 15]
    _table_header(ws, 4, list(COMMITMENT_HEADERS), widths)

    seeded = [] if blank or dealer is None else top_gaps(model, dealer, n=5)
    row = 5
    for i in range(12):
        item = seeded[i] if i < len(seeded) else None
        vals = [
            "" if blank else model["country"],
            "" if blank else dealer["name"],
            "" if item is None else item["ref"],
            "" if item is None else item["section"],
            "" if item is None else clean_text(item["text"], 220),
            "",
            "",
            "",
            "Not started" if item is not None else "",
        ]
        for col, v in enumerate(vals, 1):
            c = ws.cell(row, col, v)
            c.font = F_BODY
            c.alignment = WRAP
            c.border = BOX
            if col >= 6:
                c.fill = FILL_INPUT
        ws.cell(row, 7).number_format = "yyyy-mm-dd"
        ws.row_dimensions[row].height = 30
        row += 1

    dv_sec = DataValidation(type="list", formula1='"A,B,C,D,E"', allow_blank=True)
    dv_sec.error = "Use a section letter A to E."
    ws.add_data_validation(dv_sec)
    dv_sec.add(f"D5:D{row - 1}")

    dv_status = DataValidation(
        type="list", formula1=f'"{STATUS_OPTIONS}"', allow_blank=True
    )
    dv_status.error = "Use one of: " + STATUS_OPTIONS.replace(",", ", ")
    ws.add_data_validation(dv_status)
    dv_status.add(f"I5:I{row - 1}")

    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:I{row - 1}"
    _fit_page(ws, f"A1:I{row - 1}", landscape=True)


def _master_data_sheet(wb: Workbook, model: dict | None, *, blank: bool) -> None:
    ws = wb.create_sheet("Master data")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:N1")
    ws["A1"] = "Master data — one row per dealer"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:N2")
    ws["A2"] = (
        "Source: 2026 IDS evaluation result report."
        if blank
        else f"Source: 2026 IDS evaluation result report, {model['country']}. "
        f"Average basis: {model['basis']['n_included']} of {model['basis']['n_all']} dealers."
    )
    ws["A2"].font = F_SUB

    headers = [
        "Country",
        "Rank",
        "Dealer",
        "Evaluation date",
        "Address",
        "Total points",
        "Max points",
        "Total score",
        "Band",
        "Country average",
        "Difference (pp)",
        "In average",
        *[f"Section {sid}" for sid in SECTIONS],
    ]
    widths = [14, 6, 44, 14, 40, 12, 11, 11, 18, 15, 14, 11, 11, 11, 11, 11, 11]
    _table_header(ws, 4, headers, widths)
    row = 5
    if not blank:
        for d in sorted(
            model["dealers"],
            key=lambda x: (x["total_pct"] is None, -(x["total_pct"] or 0)),
        ):
            vals = [
                model["country"],
                d["rank"],
                d["name"],
                d.get("evaluation_date"),
                d.get("address"),
                d["total"],
                model["total_max"],
                d["total_pct"],
                d["band"] or NA,
                model["country_avg_pct"],
                _xl_value(d["vs_country_pp"], "pp"),
                "Yes" if d["in_average"] else "No",
                *[d["sections"][sid]["pct"] for sid in SECTIONS],
            ]
            for col, v in enumerate(vals, 1):
                c = ws.cell(row, col, "" if v is None else v)
                c.font = F_BODY
                if col in (8, 10) or col >= 13:
                    c.number_format = "0.0%"
                if col == 11:
                    c.number_format = "+0.0;-0.0"
            row += 1
    ws.freeze_panes = "D5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(headers))}{max(row - 1, 5)}"
    _fit_page(ws, f"A1:{get_column_letter(len(headers))}{max(row - 1, 5)}", landscape=True)


def write_dealer_workbook(
    path: Path, model: dict | None, dealer: dict | None, *, blank: bool = False
) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    _readme_sheet(wb, model, blank=blank)
    _fiche_sheet(wb, model, dealer, blank=blank)
    _sections_sheet(wb, model, dealer, blank=blank)
    _kaizen_sheet(wb, model, dealer, blank=blank)
    _commitments_sheet(wb, model, dealer, blank=blank)
    _master_data_sheet(wb, model, blank=blank)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def write_rollup_workbook(path: Path, model: dict) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    _readme_sheet(wb, model, blank=False)

    ws = wb.create_sheet("Network overview")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:E1")
    ws["A1"] = f"{model['country']} — dealer network feedback"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:E2")
    ws["A2"] = "Isuzu Dealer Standards 2026 · distributor rollup · primary DB overview"
    ws["A2"].font = F_SUB
    for i, w in enumerate([34, 14, 14, 14, 30], 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    row = 4
    _section_header(ws, row, "Network result", 5)
    row += 1
    b = model["basis"]
    facts = [
        ("Dealers evaluated", b["n_all"], None),
        ("Dealers in the average", b["n_included"], None),
        ("Dealers outside the average", b["n_excluded"], None),
        ("Network average", model["country_avg_pct"], "0.0%"),
        ("Average points", model["country_avg_points"], "0.0"),
        ("Maximum points", model["total_max"], None),
    ]
    for label, value, fmt in facts:
        ws.cell(row, 1, label).font = F_LABEL
        c = ws.cell(row, 2, value)
        c.font = F_BOLD
        c.alignment = RIGHT
        if fmt:
            c.number_format = fmt
        row += 1

    row += 1
    _section_header(ws, row, "Band distribution (dealers in the average)", 5)
    row += 1
    for bl in BAND_LABELS:
        n = model["band_counts"][bl]
        ws.cell(row, 1, bl).font = F_LABEL
        ws.cell(row, 2, n).font = F_BOLD
        c = ws.cell(row, 3, n / b["n_included"] if b["n_included"] else "")
        c.number_format = "0%"
        c.font = F_BODY
        row += 1

    row += 1
    _section_header(ws, row, "Sections across the network — lowest average first", 5)
    row += 1
    _table_header(
        ws,
        row,
        ["Section", "Max points", "Network average", "Dealers scored", ""],
        [34, 14, 16, 14, 30],
    )
    row += 1
    for sid, v in sorted(
        ((s, model["section_avg_pct"].get(s)) for s in SECTIONS),
        key=lambda x: (x[1] is None, x[1] if x[1] is not None else 0.0),
    ):
        ws.cell(row, 1, f"{sid} — {SECTION_SHORT[sid]}").font = F_BODY
        ws.cell(row, 2, model["section_max"].get(sid)).alignment = RIGHT
        c = ws.cell(row, 3, v)
        c.number_format = "0.0%"
        c.alignment = RIGHT
        n = ws.cell(row, 4, model["section_scored_n"].get(sid, 0))
        n.font = F_BODY
        n.alignment = RIGHT
        for col in range(1, 6):
            ws.cell(row, col).border = BOX
        row += 1

    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row + 3, end_column=5)
    c = ws.cell(row, 1, SECTION_NOTE)
    c.font = F_NOTE
    c.alignment = WRAP
    row += 5
    ws.merge_cells(start_row=row, start_column=1, end_row=row + 3, end_column=5)
    c = ws.cell(row, 1, _basis_note_plain(model))
    c.font = F_NOTE
    c.alignment = WRAP
    _fit_page(ws, f"A1:E{row + 3}")

    # Hit list
    ws = wb.create_sheet("Hit list")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:F1")
    ws["A1"] = f"{model['country']} — hit list (priority dealers to visit)"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:F2")
    ws["A2"] = (
        "Below market average and/or Needs improvement. Incomplete lane is separate."
    )
    ws["A2"].font = F_SUB
    _table_header(
        ws,
        4,
        ["#", "Dealer", "Score", "vs average (pp)", "Band", "Why on the list"],
        [5, 42, 10, 14, 18, 44],
    )
    hits = hit_list_dealers(model)
    row = 5
    if not hits:
        ws.merge_cells("A5:F5")
        ws["A5"] = (
            "No dealers below the market average or in the Needs improvement band."
        )
        ws["A5"].font = F_BODY
        row = 6
    else:
        for i, d in enumerate(hits, 1):
            ws.cell(row, 1, i).font = F_BOLD
            ws.cell(row, 2, d["name"]).font = F_BODY
            c = ws.cell(row, 3, d["total_pct"])
            c.number_format = "0.0%"
            c.alignment = RIGHT
            c = ws.cell(row, 4, _xl_value(d["vs_country_pp"], "pp"))
            c.number_format = "+0.0;-0.0"
            c.alignment = RIGHT
            ws.cell(row, 5, d["band"] or NA).font = F_BODY
            ws.cell(row, 6, hit_list_why(d)).font = F_BODY
            for col in range(1, 7):
                ws.cell(row, col).border = BOX
            row += 1
    _fit_page(ws, f"A1:F{max(row, 5)}", landscape=True)

    # Incomplete lane
    ws = wb.create_sheet("Incomplete lane")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:D1")
    ws["A1"] = f"{model['country']} — incomplete / not-completed lane"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:D2")
    if model["country"] in AVG_EXCLUDE_RED:
        ws["A2"] = (
            "Red-marked dealers (evaluation not completed). Outside the average; "
            "do not treat as coaching targets for a low score."
        )
    else:
        ws["A2"] = (
            "Zero / blank totals only. If empty: none for this market."
        )
    ws["A2"].font = F_SUB
    _table_header(ws, 4, ["Dealer", "Score", "Band", "Reason"], [44, 10, 18, 48])
    incomplete = incomplete_dealers(model)
    row = 5
    if not incomplete:
        ws.merge_cells("A5:D5")
        ws["A5"] = "None. No incomplete / not-completed dealers identified."
        ws["A5"].font = F_BODY
        row = 6
    else:
        for d in incomplete:
            reason = (
                "Red-marked — evaluation not completed"
                if model["country"] in AVG_EXCLUDE_RED
                else "Zero / blank total — treat as incomplete, not as a coaching score"
            )
            ws.cell(row, 1, d["name"]).font = F_BODY
            c = ws.cell(row, 2, d["total_pct"])
            c.number_format = "0.0%"
            c.alignment = RIGHT
            ws.cell(row, 3, d["band"] or NA).font = F_BODY
            ws.cell(row, 4, reason).font = F_BODY
            for col in range(1, 5):
                ws.cell(row, col).border = BOX
            row += 1
    _fit_page(ws, f"A1:D{max(row, 5)}", landscape=True)

    # DB next steps
    ws = wb.create_sheet("DB next steps")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:E1")
    ws["A1"] = "Suggested DB-level next steps — edit in the DB planning meeting"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:E2")
    ws["A2"] = (
        f"{model['country']} · starters from hit list, common checklist gaps, "
        "incomplete lane. Owner / date / proof blank."
    )
    ws["A2"].font = F_SUB
    _table_header(
        ws,
        4,
        ["#", "Suggested action", "Owner (role)", "Target date", "Proof"],
        [5, 70, 16, 14, 18],
    )
    row = 5
    for i, text in enumerate(suggested_db_actions(model), 1):
        ws.cell(row, 1, i).font = F_BOLD
        c = ws.cell(row, 2, text)
        c.font = F_BODY
        c.alignment = WRAP
        for col in range(1, 6):
            ws.cell(row, col).border = BOX
            if col >= 3:
                ws.cell(row, col).fill = FILL_INPUT
        ws.row_dimensions[row].height = 42
        row += 1
    _fit_page(ws, f"A1:E{max(row - 1, 5)}", landscape=True)

    # Pull scorecard
    ws = wb.create_sheet("Pull scorecard")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:E1")
    ws["A1"] = f"{model['country']} — Pull scorecard (monthly return)"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:E2")
    ws["A2"] = (
        "Blank on purpose. Fill after reviews. Measures the distributor process, "
        "not a monthly IDS re-score."
    )
    ws["A2"].font = F_SUB
    _table_header(
        ws,
        4,
        ["Metric", "This month", "Definition", "Owner", "As of"],
        [24, 12, 58, 16, 12],
    )
    row = 5
    for metric, defn in PULL_SCORECARD_ROWS:
        ws.cell(row, 1, metric).font = F_BOLD
        ws.cell(row, 2).fill = FILL_INPUT
        ws.cell(row, 2).border = BOX
        c = ws.cell(row, 3, defn)
        c.font = F_BODY
        c.alignment = WRAP
        for col in (1, 3, 4, 5):
            ws.cell(row, col).border = BOX
        ws.cell(row, 4).fill = FILL_INPUT
        ws.cell(row, 5).fill = FILL_INPUT
        ws.row_dimensions[row].height = 36
        row += 1
    _fit_page(ws, f"A1:E{max(row - 1, 5)}", landscape=True)

    _master_data_sheet(wb, model, blank=False)

    ws = wb.create_sheet("Consolidated commitments")
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:I1")
    ws["A1"] = f"{model['country']} — consolidated dealer commitments"
    ws["A1"].font = F_TITLE
    ws.merge_cells("A2:I2")
    ws["A2"] = (
        "Paste the Commitments rows returned by each dealer here, or let the "
        "generator consolidate the returned files."
    )
    ws["A2"].font = F_SUB
    _table_header(ws, 4, list(COMMITMENT_HEADERS), [16, 30, 10, 8, 54, 18, 14, 26, 15])
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = "A4:I4"
    _fit_page(ws, "A1:I4", landscape=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


# --------------------------------------------------------------------------- #
# layer D — consolidate returned workbooks
# --------------------------------------------------------------------------- #


def consolidate(in_dir: Path, out_xlsx: Path, out_csv: Path) -> int:
    """Merge the Commitments sheet of every returned workbook into one table."""
    files = sorted(
        p
        for p in in_dir.glob("*.xlsx")
        if p.is_file() and not p.name.startswith("~$")
    )
    rows: list[list[Any]] = []
    for path in files:
        try:
            wb = load_workbook(path, data_only=True, read_only=True)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"  skip {path.name}: {exc}", file=sys.stderr)
            continue
        if "Commitments" not in wb.sheetnames:
            wb.close()
            continue
        ws = wb["Commitments"]
        for r in ws.iter_rows(min_row=5, max_col=len(COMMITMENT_HEADERS), values_only=True):
            action = r[4]
            if action is None or not str(action).strip():
                continue
            vals = [
                "" if v is None else (v.date().isoformat() if isinstance(v, datetime) else v)
                for v in r
            ]
            rows.append([*vals, path.name])
        wb.close()

    headers = [*COMMITMENT_HEADERS, "Source file"]
    wb_out = Workbook()
    ws_out = wb_out.active
    ws_out.title = "Consolidated"
    ws_out.sheet_view.showGridLines = False
    _table_header(ws_out, 1, headers, [16, 30, 10, 8, 54, 18, 14, 26, 15, 34])
    for i, row in enumerate(rows, 2):
        for col, v in enumerate(row, 1):
            c = ws_out.cell(i, col, v)
            c.font = F_BODY
            c.alignment = WRAP
    ws_out.freeze_panes = "A2"
    ws_out.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{max(len(rows) + 1, 1)}"
    out_xlsx.parent.mkdir(parents=True, exist_ok=True)
    wb_out.save(out_xlsx)

    with out_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(headers)
        w.writerows(rows)

    print(f"Consolidated {len(rows)} commitment(s) from {len(files)} file(s)")
    print(f"  {out_xlsx}")
    print(f"  {out_csv}")
    return 0


# --------------------------------------------------------------------------- #
# build orchestration
# --------------------------------------------------------------------------- #


def build_country(
    country: str,
    *,
    out_root: Path,
    dealers: list[str] | None,
    all_dealers: bool,
    rollup: bool,
) -> dict[str, Any]:
    model = build_country_model(country)
    out_dir = out_root / safe_name(model["country"])
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    annexes: list[dict] = []

    if all_dealers:
        targets = [d for d in model["dealers"]]
    else:
        targets = [find_dealer(model, n) for n in (dealers or [])]

    dealer_dir = out_dir / "dealers"
    dealer_dir.mkdir(parents=True, exist_ok=True)
    for d in targets:
        stem = (
            f"IDS_2026_Dealer_Feedback_{safe_name(model['country'])}"
            f"_{d['file_key']}_{VERSION}"
        )
        html_a = dealer_dir / f"{stem}_exec_summary.html"
        html_a.write_text(exec_summary_html(model, d), encoding="utf-8")
        html_b = dealer_dir / f"{stem}_workshop_pack.html"
        html_b.write_text(workshop_pack_html(model, d), encoding="utf-8")
        xlsx = write_dealer_workbook(dealer_dir / f"{stem}.xlsx", model, d)
        written += [html_a, html_b, xlsx]
        annexes.append(
            {"file_key": d["file_key"], "href": f"dealers/{html_b.name}"}
        )

    if rollup:
        r_html = out_dir / f"IDS_2026_DB_Rollup_{safe_name(model['country'])}_{VERSION}.html"
        r_html.write_text(rollup_html(model, annexes), encoding="utf-8")
        r_xlsx = write_rollup_workbook(
            out_dir / f"IDS_2026_DB_Rollup_{safe_name(model['country'])}_{VERSION}.xlsx",
            model,
        )
        written += [r_html, r_xlsx]

    return {
        "country": model["country"],
        "folder": str(out_dir),
        "source_report": str(model["source_report"]),
        "source_report_file": model["source_report"].name,
        "dealers_evaluated": model["basis"]["n_all"],
        "dealers_with_a_sheet": len(targets),
        "dealers_in_average": model["basis"]["n_included"],
        "dealers_excluded_from_average": model["basis"]["n_excluded"],
        "average_rule": model["basis"]["rule"],
        "country_average_pct": model["country_avg_pct"],
        "band_counts": model["band_counts"],
        "section_average_pct": model["section_avg_pct"],
        "section_scored_dealers": model["section_scored_n"],
        "file_count": len(written),
        "files": [str(p) for p in written],
        "model": model,
    }


def write_blank_template(out_root: Path) -> list[Path]:
    out_dir = out_root / "_template"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"IDS_2026_Dealer_Feedback_BLANK_TEMPLATE_{VERSION}"
    html_a = out_dir / f"{stem}_exec_summary.html"
    html_a.write_text(exec_summary_html(None, None, blank=True), encoding="utf-8")
    html_b = out_dir / f"{stem}_workshop_pack.html"
    html_b.write_text(workshop_pack_html(None, None, blank=True), encoding="utf-8")
    xlsx = write_dealer_workbook(out_dir / f"{stem}.xlsx", None, None, blank=True)
    return [html_a, html_b, xlsx]


def main() -> int:
    # Dealer names in several markets are outside cp1252; never let a console
    # encoding abort a build.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build feedback sheets for one or more markets")
    p_build.add_argument(
        "--country",
        action="append",
        required=True,
        help="English market label, repeatable (e.g. --country Poland --country Greece)",
    )
    p_build.add_argument("--dealer", action="append", default=[], help="Dealer name (repeatable)")
    p_build.add_argument("--all-dealers", action="store_true", help="Every dealer in the country")
    p_build.add_argument("--rollup", action="store_true", help="Also build the DB rollup (layer C)")
    p_build.add_argument("--out-dir", type=Path, default=OUT_ROOT)

    p_tpl = sub.add_parser("template", help="Build the blank template")
    p_tpl.add_argument("--out-dir", type=Path, default=OUT_ROOT)

    p_con = sub.add_parser("consolidate", help="Merge returned Commitments sheets")
    p_con.add_argument("--in-dir", type=Path, required=True)
    p_con.add_argument("--out-dir", type=Path, default=OUT_ROOT / "_returns")

    args = parser.parse_args()

    if args.cmd == "template":
        paths = write_blank_template(args.out_dir)
        for p in paths:
            print(p)
        return 0

    if args.cmd == "consolidate":
        out = args.out_dir
        return consolidate(
            args.in_dir,
            out / f"IDS_2026_Consolidated_Commitments_{VERSION}.xlsx",
            out / f"IDS_2026_Consolidated_Commitments_{VERSION}.csv",
        )

    if not args.dealer and not args.all_dealers:
        parser.error("give --dealer NAME (repeatable) or --all-dealers")

    manifest_path = args.out_dir / "_build_manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    manifest["version"] = VERSION
    manifest["built_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    manifest["average_rule_note"] = AVERAGE_RULE_NOTE
    manifest["section_reading_note"] = SECTION_NOTE
    manifest["bands"] = {
        "good_min_pct": BAND_GOOD_MIN,
        "medium_min_pct": BAND_MEDIUM_MIN,
    }

    total_files = 0
    for country in args.country:
        result = build_country(
            country,
            out_root=args.out_dir,
            dealers=args.dealer,
            all_dealers=args.all_dealers,
            rollup=args.rollup,
        )
        result.pop("model")
        total_files += result["file_count"]
        print(
            f"{result['country']:14} {result['dealers_with_a_sheet']:>3} dealer sheet(s) · "
            f"average {pct(result['country_average_pct'])} on "
            f"{result['dealers_in_average']} of {result['dealers_evaluated']} dealers · "
            f"{result['file_count']:>4} files -> {result['folder']}"
        )
        manifest.setdefault("markets", {})[result["country"]] = {
            k: v for k, v in result.items() if k != "files"
        }

    print(f"\n{total_files} files written under {args.out_dir}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
