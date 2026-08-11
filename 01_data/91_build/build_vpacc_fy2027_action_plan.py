"""Normalize FY2027 VPACC Action Plan (July) → 00_derived parquet + meta.

Source: 01_data/11_planning/Action plan FY2027 VPACC_July update.xlsx

Outputs:
  vpacc_fy2027_action_plan_july.parquet   — VP + ACC actions (PIC, progress, months)
  vpacc_fy2027_orders_sheet1.parquet      — ancillary Sheet1 order lines
  vpacc_fy2027_monthly_db_block.parquet   — sheet '2018' (misnamed) monthly EUR blocks
  vpacc_fy2027_action_plan_july.meta.json
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import pandas as pd

ISZE_ROOT = Path(__file__).resolve().parents[2]
SRC = ISZE_ROOT / "01_data" / "11_planning" / "Action plan FY2027 VPACC_July update.xlsx"
OUT_DIR = ISZE_ROOT / "01_data" / "00_derived"

MONTHS = [
    "apr", "may", "jun", "jul", "aug", "sep",
    "oct", "nov", "dec", "jan", "feb", "mar",
]
PROGRESS_MAP = {
    0: "not_started_or_blank",
    1: "plan_made",
    2: "started",
    3: "started_and_in_progress",
    4: "completed_and_eval",
}


def _cell_str(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    s = str(v).replace("\r\n", "\n").replace("\r", "\n").strip()
    return s if s else None


def _progress_filled(raw: str | None) -> tuple[int | None, str | None, str | None]:
    if not raw:
        return None, None, None
    filled = raw.count("■")
    empty = raw.count("□")
    if filled + empty >= 1:
        filled = min(filled, 4)
        return filled, PROGRESS_MAP.get(filled, "unknown"), raw
    low = raw.lower()
    if "completed" in low:
        return 4, PROGRESS_MAP[4], raw
    if "in progress" in low:
        return 3, PROGRESS_MAP[3], raw
    if "started" in low:
        return 2, PROGRESS_MAP[2], raw
    if "plan made" in low:
        return 1, PROGRESS_MAP[1], raw
    return None, None, raw


def _month_flag(v) -> str | None:
    s = _cell_str(v)
    return s.upper() if s else None


def _forward_fill(series: list[str | None]) -> list[str | None]:
    out: list[str | None] = []
    last = None
    for v in series:
        if v is not None:
            last = v
        out.append(last)
    return out


def parse_action_sheet(ws, stream: str, has_deadline: bool) -> list[dict]:
    rows = list(ws.iter_rows(values_only=True))

    def get(r, idx0):
        if r is None or idx0 >= len(r):
            return None
        return r[idx0]

    staging: list[dict] = []
    for i, r in enumerate(rows):
        excel_row = i + 1
        if excel_row < 6:
            continue
        if has_deadline:
            dm = _cell_str(get(r, 1))
            obj = _cell_str(get(r, 2))
            action = _cell_str(get(r, 3))
            deadline = _cell_str(get(r, 4))
            pic = _cell_str(get(r, 5))
            month_vals = [_month_flag(get(r, 6 + k)) for k in range(12)]
            progress_raw = _cell_str(get(r, 18))
            comments_legacy_dec = _cell_str(get(r, 19))
            status_vs_oct = _cell_str(get(r, 20))
            comments_legacy_nov = _cell_str(get(r, 21))
            comments_june = comments_may = comments = None
        else:
            dm = _cell_str(get(r, 1))
            obj = _cell_str(get(r, 2))
            action = _cell_str(get(r, 3))
            deadline = None
            pic = _cell_str(get(r, 4))
            month_vals = [_month_flag(get(r, 5 + k)) for k in range(12)]
            progress_raw = _cell_str(get(r, 17))
            comments_june = _cell_str(get(r, 18))
            comments_may = _cell_str(get(r, 19))
            comments = _cell_str(get(r, 20))
            comments_legacy_dec = status_vs_oct = comments_legacy_nov = None

        if not any(
            [dm, obj, action, pic, progress_raw, comments, comments_june, comments_may,
             comments_legacy_dec, status_vs_oct, comments_legacy_nov]
            + month_vals
        ):
            continue
        section_only = action is None and pic is None and progress_raw is None and not any(month_vals)
        if section_only and not (dm or obj):
            continue
        staging.append(
            {
                "_excel_row": excel_row,
                "dm_report": dm,
                "objective": obj,
                "action_point": action,
                "deadline": deadline,
                "pic": pic,
                "progress_raw": progress_raw,
                "comments_june": comments_june,
                "comments_may": comments_may,
                "comments": comments,
                "comments_legacy_dec": comments_legacy_dec,
                "status_vs_oct": status_vs_oct,
                "comments_legacy_nov": comments_legacy_nov,
                "months": month_vals,
                "_section_only": section_only,
            }
        )

    dm_ff = _forward_fill([x["dm_report"] for x in staging])
    obj_ff = _forward_fill([x["objective"] for x in staging])
    records = []
    for idx, x in enumerate(staging):
        if x["_section_only"]:
            continue
        filled, status, raw = _progress_filled(x["progress_raw"])
        rec = {
            "stream": stream,
            "fy": "FY2027",
            "update_month": "July",
            "excel_row": x["_excel_row"],
            "dm_report": dm_ff[idx],
            "objective": obj_ff[idx],
            "action_point": x["action_point"],
            "deadline": x["deadline"],
            "pic": x["pic"],
            "progress_raw": raw,
            "progress_filled": filled,
            "progress_status": status,
            "comments_june": x["comments_june"],
            "comments_may": x["comments_may"],
            "comments": x["comments"],
            "comments_legacy_dec": x["comments_legacy_dec"],
            "status_vs_oct": x["status_vs_oct"],
            "comments_legacy_nov": x["comments_legacy_nov"],
        }
        for m, mv in zip(MONTHS, x["months"]):
            rec[f"m_{m}"] = mv
        records.append(rec)
    return records


def parse_sheet1(ws) -> list[dict]:
    rows = list(ws.iter_rows(values_only=True))
    out = []
    for i, r in enumerate(rows):
        excel_row = i + 1
        if excel_row < 3:
            continue
        n = r[1] if len(r) > 1 else None
        if n is None:
            continue
        out.append(
            {
                "line_no": int(n) if isinstance(n, (int, float)) else n,
                "order_receipt": _cell_str(r[2] if len(r) > 2 else None),
                "qty": r[3] if len(r) > 3 else None,
                "invoiced_qty": r[4] if len(r) > 4 else None,
                "date_or_status": _cell_str(r[5] if len(r) > 5 else None),
                "excel_row": excel_row,
                "fy": "FY2027",
                "source_sheet": "Sheet1",
            }
        )
    return out


def parse_monthly_db_sheet(ws) -> list[dict]:
    """Sheet '2018' = calendar monthly EUR by DB; block 2 has no year label."""
    rows = list(ws.iter_rows(values_only=True))
    out: list[dict] = []
    month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                   "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

    def is_year(v) -> int | None:
        if isinstance(v, (int, float)) and 2000 <= int(v) <= 2100:
            return int(v)
        if isinstance(v, str) and re.fullmatch(r"20\d{2}", v.strip()):
            return int(v.strip())
        return None

    def is_month_header(r) -> bool:
        vals = [str(c).strip().upper()[:3] if c is not None else "" for c in (r[1:13] if len(r) > 1 else [])]
        return vals[:3] == ["JAN", "FEB", "MAR"]

    def emit_block(start_row_idx: int, year: int | None, block_index: int) -> int:
        j = start_row_idx
        while j < len(rows):
            rr = rows[j]
            if is_year(rr[1] if len(rr) > 1 else None) is not None:
                return j
            if is_month_header(rr):
                return j
            db = _cell_str(rr[0] if len(rr) > 0 else None)
            if not db:
                return j + 1
            for mi, mlabel in enumerate(month_names):
                col = mi + 1
                val = rr[col] if col < len(rr) else None
                if val is None or (isinstance(val, str) and not str(val).strip()):
                    continue
                try:
                    num = float(val)
                except (TypeError, ValueError):
                    continue
                out.append(
                    {
                        "calendar_year": year,
                        "block_index": block_index,
                        "db": db.strip(),
                        "month": mlabel,
                        "month_num": mi + 1,
                        "value_eur": num,
                        "source_sheet": "2018",
                        "note": "sheet_name_is_legacy_misnomer"
                        + ("" if year is not None else "; year_label_missing"),
                    }
                )
            j += 1
        return j

    i = 0
    block_index = 0
    while i < len(rows):
        r = rows[i]
        y = is_year(r[1] if len(r) > 1 else None)
        if y is not None:
            j = i + 1
            while j < len(rows) and not any(c is not None and str(c).strip() for c in rows[j]):
                j += 1
            if j < len(rows) and is_month_header(rows[j]):
                block_index += 1
                i = emit_block(j + 1, y, block_index)
                continue
            i += 1
            continue
        db0 = _cell_str(r[0] if len(r) > 0 else None)
        has_nums = any(isinstance(r[k], (int, float)) for k in range(1, min(13, len(r))))
        if db0 and has_nums and not is_month_header(r):
            block_index += 1
            i = emit_block(i, None, block_index)
            continue
        i += 1
    return out


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Missing source workbook: {SRC}")

    wb = openpyxl.load_workbook(SRC, data_only=True, read_only=True)
    sheet_map = {}

    vp = parse_action_sheet(wb["Action Plan VP"], stream="VP", has_deadline=False)
    sheet_map["Action Plan VP"] = {
        "role": "main_actions_vehicle_parts",
        "stream": "VP",
        "action_rows": len(vp),
        "join_keys": ["pic", "progress_status", "objective", "action_point"],
        "pic_col": "E",
        "progress_col": "R",
    }
    acc = parse_action_sheet(wb["Action Plan ACC"], stream="ACC", has_deadline=True)
    sheet_map["Action Plan ACC"] = {
        "role": "main_actions_accessories",
        "stream": "ACC",
        "action_rows": len(acc),
        "join_keys": ["pic", "progress_status", "deadline", "objective", "action_point"],
        "pic_col": "F",
        "progress_col": "S",
        "deadline_col": "E",
    }
    orders = parse_sheet1(wb["Sheet1"])
    sheet_map["Sheet1"] = {"role": "ancillary_order_lines", "rows": len(orders)}
    monthly = parse_monthly_db_sheet(wb["2018"])
    sheet_map["2018"] = {
        "role": "monthly_db_eur_blocks",
        "rows": len(monthly),
        "note": "Sheet name legacy misnomer; block_index=2 has no year label",
        "years": sorted({r["calendar_year"] for r in monthly if r["calendar_year"] is not None}),
    }
    wb.close()

    df_actions = pd.DataFrame(vp + acc)
    df_orders = pd.DataFrame(orders)
    df_monthly = pd.DataFrame(monthly)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p_actions = OUT_DIR / "vpacc_fy2027_action_plan_july.parquet"
    p_orders = OUT_DIR / "vpacc_fy2027_orders_sheet1.parquet"
    p_monthly = OUT_DIR / "vpacc_fy2027_monthly_db_block.parquet"
    p_meta = OUT_DIR / "vpacc_fy2027_action_plan_july.meta.json"

    df_actions.to_parquet(p_actions, index=False)
    df_orders.to_parquet(p_orders, index=False)
    df_monthly.to_parquet(p_monthly, index=False)

    pics = sorted({str(x) for x in df_actions["pic"].dropna().unique()}) if len(df_actions) else []
    meta = {
        "built_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": str(SRC.relative_to(ISZE_ROOT)).replace("\\", "/"),
        "source_filename": SRC.name,
        "update_label": "July",
        "fy": "FY2027",
        "builder": "01_data/91_build/build_vpacc_fy2027_action_plan.py",
        "sheet_map": sheet_map,
        "join_hints": {
            "owner_field": "pic",
            "status_fields": ["progress_status", "progress_filled", "progress_raw"],
            "stream_field": "stream",
            "streams": ["VP", "ACC"],
            "pics_seen": pics,
            "note": "Join later work on pic initials / stream; not dealer-keyed",
        },
        "outputs": {
            "actions": {
                "path": str(p_actions.relative_to(ISZE_ROOT)).replace("\\", "/"),
                "rows": int(len(df_actions)),
                "vp_rows": int((df_actions["stream"] == "VP").sum()) if len(df_actions) else 0,
                "acc_rows": int((df_actions["stream"] == "ACC").sum()) if len(df_actions) else 0,
            },
            "orders_sheet1": {
                "path": str(p_orders.relative_to(ISZE_ROOT)).replace("\\", "/"),
                "rows": int(len(df_orders)),
            },
            "monthly_db_block": {
                "path": str(p_monthly.relative_to(ISZE_ROOT)).replace("\\", "/"),
                "rows": int(len(df_monthly)),
            },
        },
        "progress_legend": {
            "■□□□": "plan_made",
            "■■□□": "started",
            "■■■□": "started_and_in_progress",
            "■■■■": "completed_and_eval",
            "□□□□": "not_started_or_blank",
        },
        "ambiguous_columns": [
            "ACC T–V are CY2023 DEC/NOV report residue (comments_legacy_* / status_vs_oct)",
            "Sheet tab '2018' misnamed; block_index=2 has no year label",
            "Month cells mixed flags x/X/G/Y stored as-is in m_*",
            "DM Report / Objective forward-filled from sparse section headers",
        ],
        "prior_workbook": "01_data/11_planning/Action plan FY2027 VPACC_April update.xlsx",
    }
    p_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(meta["outputs"], indent=2))


if __name__ == "__main__":
    main()
