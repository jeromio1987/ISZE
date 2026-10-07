"""Connect the first two real feeds to the INTERNAL build (U29 task C).

Writes `payload/real_feeds.local.json`, a small block that records the two real feeds in
the shape the product already reads:

  tender_data.notices   the live weekly tender feed (`01_data/14_dashboards/tender_data.json`),
                        reduced to the fields `src/data/tender_investigation.js` snapshots.
  prism_measures        accepted PRISM-shaped measures at the level each was measured
                        (national ITUK and Portugal, CY2025), built only from
                        `01_data/00_derived/`. No national total is split to a dealer.

It never invents a value, never infers a delivery basis, and never writes the feed itself.
Nothing here goes into the SYNTHETIC artifact: the synthetic build keeps its own fixtures.

Run from anywhere.  Read-only on both sources.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
ISZE = COMPONENT.parents[1]  # ...\ISZE
# Worktrees often omit gitignored IDS/xlsx; fall back to the main clone.
_MAIN_ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DATA_ROOT = ISZE if (ISZE / "01_data" / "08_Distributor" / "IDS_2026" / "ITUK" / "IDS ITUK self evaluations.xlsx").exists() else _MAIN_ISZE
DERIVED = DATA_ROOT / "01_data" / "00_derived"
TENDER = DATA_ROOT / "01_data" / "14_dashboards" / "tender_data.json"
if not TENDER.exists():
    TENDER = _MAIN_ISZE / "01_data" / "14_dashboards" / "tender_data.json"
OUT = COMPONENT / "payload" / "real_feeds.local.json"

# The two markets this pilot prices. Never another distributor.
MARKETS = {"ITUK": "Isuzu Truck UK", "PORTUGAL": "Portugal (I-Motors)"}
YEAR = 2025


def _name(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _date(v):
    """The feed writes ISO dates or nothing. Never guess a date."""
    s = _name(v)
    if not s:
        return None
    return s[:10] if len(s) >= 10 and s[4] == "-" else s


def build_notices() -> dict:
    if not TENDER.exists():
        return {"present": False, "reason": "the weekly tender feed file is not on disk",
                "notices": []}
    doc = json.loads(TENDER.read_text(encoding="utf-8"))
    raw = doc.get("notices") or []
    out = []
    seen = set()
    for n in raw:
        code = _name(n.get("distributor_code"))
        if code not in MARKETS:
            continue
        oid = _name(n.get("opportunity_id"))
        if not oid or oid in seen:
            continue
        seen.add(oid)
        out.append({
            "opportunity_id": oid,
            "title": _name(n.get("Title")),
            "buyer": _name(n.get("Buyer")),
            "country": _name(n.get("Country")),
            "deadline_date": _date(n.get("Deadline Date")),
            "published_latest": _date(n.get("Published Date")),
            "lifecycle": _name(n.get("Lifecycle")),
            "notice_type": _name(n.get("Notice Type")),
            "value_amount": (None if n.get("value_amount") in (None, "")
                             else float(n["value_amount"])),
            "currency": _name(n.get("Currency")),
            "source": _name(n.get("Source")) or "tender_feed",
            "url": _name(n.get("URL")),
            "distributor_code": code,
            "aftersales_tags": n.get("aftersales_tags") or [],
            "parts_signal": bool(n.get("parts_signal")),
            "decision": _name(n.get("decision")),
        })
    return {
        "present": True,
        "generated_at": (doc.get("meta") or {}).get("generated_at"),
        "source_file": str(TENDER),
        "source_stats": (doc.get("meta") or {}).get("stats"),
        "rule": ("notices whose distributor_code is ITUK or PORTUGAL only; the deadline is "
                 "the notice's own; an expired or cancelled notice is never a current "
                 "deadline; a notice value is never Isuzu parts revenue"),
        "notices": out,
    }


def build_prism_measures() -> dict:
    """Accepted measures at the LEVEL each was measured. National stays national."""
    src = DERIVED / "gps_spu_by_distributor.csv"
    pms = DERIVED / "gps_spu_pms.csv"
    measures = []
    if src.exists():
        g = pd.read_csv(src)
        g = g[(g["year"] == YEAR) & (g["distributor_code"].isin(MARKETS))]
        for _, r in g.iterrows():
            code = r["distributor_code"]
            uio_src = _name(r.get("uio_source")) or "01_data/00_derived/gps_spu_by_distributor.csv"
            measures.append({
                "id": f"PRISM-UIO-{code}-{YEAR}",
                "kind": "trucks_in_service",
                "value": (None if pd.isna(r["uio_units"]) else float(r["uio_units"])),
                "unit": "vehicles",
                "source": uio_src,
                "period": f"CY{YEAR}",
                "year": YEAR,
                "population": "national",
                "accepted_basis": "ituk_dvla_2026" if code == "ITUK" else "v18_actual",
                "denominator_version": "uio_v1",
                "market": code,
                "note": "national fleet; never divided to a dealer",
            })
            measures.append({
                "id": f"PRISM-SPEND-{code}-{YEAR}",
                "kind": "measured_spend",
                "value": (None if pd.isna(r["total_sales_eur"]) else float(r["total_sales_eur"])),
                "unit": "EUR",
                "source": "01_data/00_derived/gps_spu_by_distributor.csv",
                "period": f"CY{YEAR}",
                "year": YEAR,
                "population": "national",
                "accepted_basis": "billed_eur_v2",
                "denominator_version": "spend_v2",
                "market": code,
                "note": "billed parts value on the GPS basis; national",
            })
            if not pd.isna(r.get("spend_per_unit_eur")):
                measures.append({
                    "id": f"PRISM-SPU-{code}-{YEAR}",
                    "kind": "spend_per_truck",
                    "value": float(r["spend_per_unit_eur"]),
                    "unit": "EUR/vehicle",
                    "source": "01_data/00_derived/gps_spu_by_distributor.csv",
                    "period": f"CY{YEAR}",
                    "year": YEAR,
                    "population": "national",
                    "accepted_basis": "billed_eur_v2 / uio_v1",
                    "denominator_version": "spu_v2",
                    "market": code,
                    "note": "national average; not a dealer rate",
                })
    families = []
    if pms.exists():
        p = pd.read_csv(pms)
        p = p[(p["year"] == YEAR) & (p["distributor_code"].isin(MARKETS))
              & (p["line_type"] == "all")]
        for _, r in p.iterrows():
            families.append({
                "distributor_code": r["distributor_code"],
                "pms_category": r["pms_category"],
                "net_sales_eur": float(r["net_sales_eur"]),
                "uio_units": None if pd.isna(r["uio_units"]) else float(r["uio_units"]),
                "spu_eur": None if pd.isna(r["spu_eur"]) else float(r["spu_eur"]),
            })
    return {
        "present": bool(measures),
        "year": YEAR,
        "source_files": ["01_data/00_derived/gps_spu_by_distributor.csv",
                         "01_data/00_derived/gps_spu_pms.csv"],
        "rule": ("each measure stays at the level it was measured at; a national total is "
                 "never allocated to a dealer; the fleet forecast beyond 2025 is excluded"),
        "measures": measures,
        "family_detail_national": families,
    }



# --- IDS sheet (ITUK + Portugal / I-Motors) appended for U29 IDS wire ---
import re as _re

IDS_ITUK_SELF = (
    DATA_ROOT / "01_data" / "08_Distributor" / "IDS_2026" / "ITUK"
    / "IDS ITUK self evaluations.xlsx"
)
IDS_PT_RESULT = (
    DATA_ROOT / "01_data" / "08_Distributor" / "IDS_2026" / "reports"
    / "evaluation_result" / "2026 IDS Evaluation Result Report_Portugal.xls"
)

CASE_DEALERS = {
    "ITUK": {
        "dealer_id": "ITUK-FERNDOWN",
        "display_name": "Ferndown Commercials Ltd",
        "match_names": ["Ferndown Commercials Ltd"],
    },
    "PORTUGAL": {
        "dealer_id": "PT-ASTARA-LISBOA",
        "display_name": "ASTARA RETAIL LISBOA",
        "match_names": ["ASTARA RETAIL LISBOA", "ASTARA RETAIL LISBON"],
    },
}

QUESTION_CODE_RE = _re.compile(r"^[A-H]\.\d+-\d+[A-Z]?$", _re.IGNORECASE)


def _slug_dealer(name: str) -> str:
    s = "".join(ch if ch.isalnum() else "-" for ch in (name or "").upper())
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-") or "UNKNOWN"


def _find_dealer_col(header_row, match_names):
    wanted = {str(n).strip().upper() for n in match_names}
    for i, cell in enumerate(header_row):
        if cell is None or (isinstance(cell, float) and pd.isna(cell)):
            continue
        if str(cell).strip().upper() in wanted:
            return i
    return None


def _rows_from_ituk_self():
    if not IDS_ITUK_SELF.exists():
        return [], {"present": False, "reason": "ITUK self-evaluation workbook missing",
                    "path": str(IDS_ITUK_SELF)}
    xl = pd.ExcelFile(IDS_ITUK_SELF)
    sheet_name = "Sales, Parts & Service"
    if sheet_name not in xl.sheet_names:
        sheet_name = xl.sheet_names[0]
    m = pd.read_excel(IDS_ITUK_SELF, sheet_name=sheet_name, header=None)
    meta = CASE_DEALERS["ITUK"]
    col = _find_dealer_col(list(m.iloc[2].values), meta["match_names"])
    if col is None:
        return [], {"present": False, "reason": "Ferndown column not found in ITUK self-eval",
                    "path": str(IDS_ITUK_SELF)}
    rows = []
    for i in range(4, len(m)):
        code = m.iloc[i, 0]
        text = m.iloc[i, 1]
        val = m.iloc[i, col]
        if pd.isna(code):
            continue
        code_s = str(code).strip()
        if not QUESTION_CODE_RE.match(code_s):
            continue
        if pd.isna(val):
            continue
        ans = str(val).strip()
        if ans.lower() in {"result", "nan", ""}:
            continue
        low = ans.lower()
        if low in {"yes", "y", "compliant"}:
            state, answer = "answered", "meets"
        elif low in {"no", "n", "non compliant", "non-compliant"}:
            state, answer = "answered", "does_not_meet"
        else:
            state, answer = "answered", ans
        qtext = "" if pd.isna(text) else str(text).strip()
        rows.append({
            "dealer_id": meta["dealer_id"],
            "distributor": "ITUK",
            "questionnaire_version": "IDS-2026-ITUK",
            "local_question_code": code_s,
            "question_text": (qtext or code_s)[:240],
            "answer_state": state,
            "answer": answer,
            "date_or_round": "2026",
        })
    return rows, {
        "present": True,
        "path": str(IDS_ITUK_SELF),
        "sheet": sheet_name,
        "dealer": meta["display_name"],
        "dealer_id": meta["dealer_id"],
        "rows": len(rows),
    }


def _rows_from_portugal_result():
    if not IDS_PT_RESULT.exists():
        return [], {"present": False, "reason": "Portugal IDS result report missing",
                    "path": str(IDS_PT_RESULT)}
    m = pd.read_excel(IDS_PT_RESULT, sheet_name="Portugal26", header=None)
    meta = dict(CASE_DEALERS["PORTUGAL"])
    col = _find_dealer_col(list(m.iloc[2].values), meta["match_names"])
    if col is None:
        for i in range(3, m.shape[1]):
            name = m.iloc[2, i]
            if pd.isna(name):
                continue
            if "ASTARA" in str(name).upper():
                col = i
                meta = {
                    "dealer_id": "PT-" + _slug_dealer(str(name)),
                    "display_name": str(name).strip(),
                    "match_names": [str(name).strip()],
                }
                break
    if col is None:
        return [], {"present": False, "reason": "no Portugal dealer column found",
                    "path": str(IDS_PT_RESULT)}
    rows = []
    for i in range(16, len(m)):
        code = m.iloc[i, 0]
        if pd.isna(code):
            continue
        code_s = str(code).strip()
        if not QUESTION_CODE_RE.match(code_s):
            continue
        text = m.iloc[i, 1]
        mx = m.iloc[i, 2]
        val = m.iloc[i, col]
        if pd.isna(val):
            state, answer = "missing", None
        else:
            try:
                v = float(val)
                mxx = float(mx) if not pd.isna(mx) else None
            except (TypeError, ValueError):
                state, answer = "answered", str(val)
            else:
                if mxx is not None and v >= mxx:
                    state, answer = "answered", "meets"
                elif v == 0:
                    state, answer = "answered", "does_not_meet"
                else:
                    state, answer = "answered", (
                        f"partial:{v:g}/{mxx:g}" if mxx is not None else f"score:{v:g}"
                    )
        rows.append({
            "dealer_id": meta["dealer_id"],
            "distributor": "PORTUGAL",
            "questionnaire_version": "IDS-2026-PORTUGAL",
            "local_question_code": code_s,
            "question_text": (str(text).strip()[:240] if not pd.isna(text) else code_s),
            "answer_state": state,
            "answer": answer,
            "date_or_round": "2026",
        })
    return rows, {
        "present": True,
        "path": str(IDS_PT_RESULT),
        "sheet": "Portugal26",
        "dealer": meta["display_name"],
        "dealer_id": meta["dealer_id"],
        "rows": len(rows),
    }


def build_ids_sheet():
    ituk_rows, ituk_meta = _rows_from_ituk_self()
    pt_rows, pt_meta = _rows_from_portugal_result()
    rows = ituk_rows + pt_rows
    return {
        "present": bool(rows),
        "rows": rows,
        "identities": {
            "ITUK": {
                "dealer_id": CASE_DEALERS["ITUK"]["dealer_id"],
                "distributor": "ITUK",
                "display_name": CASE_DEALERS["ITUK"]["display_name"],
                "validated": True,
            },
            "PORTUGAL": {
                "dealer_id": pt_meta.get("dealer_id") or CASE_DEALERS["PORTUGAL"]["dealer_id"],
                "distributor": "PORTUGAL",
                "display_name": pt_meta.get("dealer") or CASE_DEALERS["PORTUGAL"]["display_name"],
                "validated": True,
            },
        },
        "provenance": {"ITUK": ituk_meta, "PORTUGAL": pt_meta},
    }

def main() -> int:
    notices = build_notices()
    prism = build_prism_measures()
    ids = build_ids_sheet()
    block = {
        "_note": ("Real feeds for the INTERNAL build only (U29 task C + IDS for ITUK and "
                  "Portugal/I-Motors). Tender from the weekly feed; PRISM from derived files; "
                  "IDS answers from the 2026 evaluation files. SYNTHETIC never carries this."),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "markets": MARKETS,
        "tender_data": {"notices": notices["notices"]},
        "prism_measures": prism["measures"],
        "ids_sheet": {"rows": ids["rows"]},
        "ids_identities": ids["identities"],
        "provenance": {
            "tender": {k: v for k, v in notices.items() if k != "notices"},
            "prism": {k: v for k, v in prism.items() if k != "measures"},
            "ids": ids["provenance"],
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(block, indent=2, ensure_ascii=False), encoding="utf-8")
    by = {}
    for n in notices["notices"]:
        by[n["distributor_code"]] = by.get(n["distributor_code"], 0) + 1
    print(f"wrote {OUT}")
    print(f"  tender notices (ITUK/PORTUGAL): {len(notices['notices'])}  by market: {by}")
    print(f"  prism measures: {len(prism['measures'])}")
    print(f"  ids sheet rows: {len(ids['rows'])}  "
          f"ITUK={ids['provenance']['ITUK'].get('rows')}  "
          f"PORTUGAL={ids['provenance']['PORTUGAL'].get('rows')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

