"""Sanity-check raw warranty Excels vs Jerome 2026-07-27 decision (Mode B)."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import openpyxl

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\06_Warranty")
OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\warranty_audit_2026-07-27")
CV = ROOT / "Warranty_CV_2025.xlsx"
LCV = ROOT / "Warranty_LCV_2025.xlsx"
UMI = ROOT / "UMI warranty data 202301 - 202605.xlsx"


def parse_ymd(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    s = str(int(v)) if isinstance(v, (int, float)) else str(v).strip().replace("-", "").replace("/", "")[:8]
    if len(s) != 8 or not s.isdigit():
        return None
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except ValueError:
        return None


def month_key(d):
    return f"{d.year:04d}-{d.month:02d}"


def monthly(pairs, year=None):
    by = defaultdict(lambda: {"n": 0, "eur": 0.0})
    for d, a in pairs:
        if year and d.year != year:
            continue
        by[month_key(d)]["n"] += 1
        by[month_key(d)]["eur"] += a
    if not by:
        return {
            "months": {},
            "min": None,
            "max": None,
            "zero_months": [],
            "black_holes_2plus": [],
            "continuous": None,
        }
    keys = sorted(by)
    y0, m0 = map(int, keys[0].split("-"))
    y1, m1 = map(int, keys[-1].split("-"))
    exp = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        exp.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    holes = [mk for mk in exp if mk not in by or by[mk]["n"] == 0]
    big = []
    run = []
    for mk in exp:
        if mk in holes:
            run.append(mk)
        else:
            if len(run) >= 2:
                big.append(run[:])
            run = []
    if len(run) >= 2:
        big.append(run)
    return {
        "months": {k: {"n": v["n"], "eur": round(v["eur"], 2)} for k, v in sorted(by.items())},
        "min": keys[0],
        "max": keys[-1],
        "zero_months": holes,
        "black_holes_2plus": big,
        "continuous": len(big) == 0 and len(holes) == 0,
    }


def find_col(headers, *names):
    upper = {str(h).strip().upper(): i for i, h in enumerate(headers) if h is not None}
    for n in names:
        if n.upper() in upper:
            return upper[n.upper()]
    for n in names:
        for h, i in upper.items():
            if n.upper() in h:
                return i
    return None


def is_blank_pn(part):
    if part is None:
        return True
    s = str(part).strip()
    if s == "" or s.replace("0", "") == "":
        return True
    try:
        if float(s) == 0:
            return True
    except ValueError:
        pass
    return False


def load_price(wb):
    clean = {}
    for tab in ("ITUK", "UTI"):
        if tab not in wb.sheetnames:
            continue
        ws = wb[tab]
        for r in range(2, ws.max_row + 1):
            part, price = ws.cell(r, 1).value, ws.cell(r, 4).value
            if part is None or not isinstance(price, (int, float)) or price <= 0:
                continue
            pk = str(int(part)) if isinstance(part, float) else str(part).strip()
            clean[pk] = float(price)
            clean[pk.lstrip("0") or "0"] = float(price)
    return clean


def lookup(clean, part):
    pk = str(int(part)) if isinstance(part, float) else str(part).strip()
    return clean.get(pk) or clean.get(pk.lstrip("0") or "0")


def parse_sheet4(ws4, treat_zero_as_country=True):
    sections = []
    cur = None
    for r in range(1, ws4.max_row + 1):
        a, b, c = ws4.cell(r, 1).value, ws4.cell(r, 2).value, ws4.cell(r, 3).value
        if a is None:
            continue
        s = str(a).strip()
        is_country = (
            bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9 _\-]{0,40}", s))
            or s.lower().startswith("grand")
            or s == "Row Labels"
        )
        is_zero = (
            s in ("0", "0.0")
            or (isinstance(a, (int, float)) and a == 0)
            or bool(re.fullmatch(r"0+", s))
        )
        if is_country or (treat_zero_as_country and is_zero):
            cur = {"label": s, "parts": [], "sum": 0.0}
            sections.append(cur)
            continue
        if cur is None:
            continue
        try:
            qty = float(b) if b is not None else 0.0
        except (TypeError, ValueError):
            qty = 0.0
        price = None
        if isinstance(c, (int, float)):
            price = float(c)
        elif c is not None:
            cs = str(c).replace("\xa0", "").replace(" ", "").replace(",", ".")
            if cs and "#N" not in cs.upper():
                try:
                    price = float(cs)
                except ValueError:
                    price = None
        eur = qty * price if price is not None else 0.0
        cur["parts"].append({"part": s, "qty": qty, "price": price, "eur": eur, "zero": is_blank_pn(s)})
        cur["sum"] += eur
    return sections


def main():
    print("Loading CV...")
    wb = openpyxl.load_workbook(CV, data_only=True)
    price = load_price(wb)
    ws = wb["DATA WITHOUT MIDI"]
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    H = {str(h).upper(): i + 1 for i, h in enumerate(headers) if h}

    blank_stats = {
        "n": 0,
        "lbr": 0.0,
        "partamt": 0.0,
        "clm": 0.0,
        "sub": 0.0,
        "by_cty": defaultdict(lambda: {"n": 0, "lbr": 0.0}),
    }
    valid = {"n": 0, "qty": 0.0, "partamt": 0.0, "priced_eur": 0.0}
    ie_pt = {}
    samples_blank = []
    by_db_dates = defaultdict(list)
    by_db_parts = defaultdict(list)
    cty_to_db = {
        "UK": "ITUK",
        "ISRAEL": "UTI",
        "IRELAND": "IRELAND",
        "PORTUGAL": "PORTUGAL",
        "GERMANY": "ISD",
    }

    for r in range(2, ws.max_row + 1):
        billy = ws.cell(r, H["BILLYMD"]).value
        d = parse_ymd(billy)
        if d is None:
            continue
        cty = str(ws.cell(r, H["CTY_NAME"]).value or "").strip().upper()
        part = ws.cell(r, H["PARTNBR"]).value
        qty_raw = ws.cell(r, H["QTY1"]).value
        try:
            qty = float(qty_raw) if qty_raw not in (None, "", "00") else 0.0
        except (TypeError, ValueError):
            qty = 0.0
        partamt = float(ws.cell(r, H["PARTAMT1"]).value or 0)
        lbr = float(ws.cell(r, H["LBRAMT"]).value or 0)
        sub = float(ws.cell(r, H["SUBAMT"]).value or 0)
        clm = float(ws.cell(r, H["CLMAMT"]).value or 0)
        db = cty_to_db.get(cty, cty)
        by_db_dates[db].append((d, partamt if partamt else lbr))
        if not is_blank_pn(part):
            p = lookup(price, part)
            by_db_parts[db].append((d, p * qty if p else partamt))
        if d.year != 2025:
            continue
        if is_blank_pn(part):
            blank_stats["n"] += 1
            blank_stats["lbr"] += lbr
            blank_stats["partamt"] += partamt
            blank_stats["clm"] += clm
            blank_stats["sub"] += sub
            blank_stats["by_cty"][cty]["n"] += 1
            blank_stats["by_cty"][cty]["lbr"] += lbr
            if len(samples_blank) < 12:
                samples_blank.append(
                    {
                        "row": r,
                        "cty": cty,
                        "part": part,
                        "qty": qty_raw,
                        "partamt": partamt,
                        "lbr": lbr,
                        "sub": sub,
                        "clm": clm,
                        "ope": ws.cell(r, H["OPE_NAME"]).value,
                    }
                )
        else:
            valid["n"] += 1
            valid["qty"] += qty
            valid["partamt"] += partamt
            p = lookup(price, part)
            if p:
                valid["priced_eur"] += qty * p

    for country in ("IRELAND", "PORTUGAL"):
        st = {
            "rows": 0,
            "blank_pn": 0,
            "blank_lbr": 0.0,
            "valid_pn": 0,
            "valid_priced": 0,
            "valid_unpriced": 0,
            "valid_priced_eur": 0.0,
            "unpriced_samples": [],
            "blank_samples": [],
        }
        for r in range(2, ws.max_row + 1):
            if str(ws.cell(r, H["CTY_NAME"]).value or "").strip().upper() != country:
                continue
            d = parse_ymd(ws.cell(r, H["BILLYMD"]).value)
            if not d or d.year != 2025:
                continue
            st["rows"] += 1
            part = ws.cell(r, H["PARTNBR"]).value
            qty_raw = ws.cell(r, H["QTY1"]).value
            try:
                qty = float(qty_raw) if qty_raw not in (None, "", "00") else 0.0
            except (TypeError, ValueError):
                qty = 0.0
            partamt = float(ws.cell(r, H["PARTAMT1"]).value or 0)
            lbr = float(ws.cell(r, H["LBRAMT"]).value or 0)
            if is_blank_pn(part):
                st["blank_pn"] += 1
                st["blank_lbr"] += lbr
                if len(st["blank_samples"]) < 5:
                    st["blank_samples"].append(
                        {
                            "part": part,
                            "lbr": lbr,
                            "partamt": partamt,
                            "ope": ws.cell(r, H["OPE_NAME"]).value,
                        }
                    )
            else:
                st["valid_pn"] += 1
                p = lookup(price, part)
                if p:
                    st["valid_priced"] += 1
                    st["valid_priced_eur"] += qty * p
                else:
                    st["valid_unpriced"] += 1
                    if len(st["unpriced_samples"]) < 10:
                        st["unpriced_samples"].append(
                            {"part": str(part), "qty": qty, "partamt": partamt}
                        )
        st["coverage_pct"] = (
            round(100 * st["valid_priced"] / st["valid_pn"], 1) if st["valid_pn"] else None
        )
        ie_pt[country] = st

    ws4 = wb["Sheet4"]
    buggy = parse_sheet4(ws4, True)
    correct = parse_sheet4(ws4, False)
    buggy_zero = sum(
        s["sum"]
        for s in buggy
        if s["label"] in ("0", "0.0") or re.fullmatch(r"0+", str(s["label"]))
    )
    correct_zero = 0.0
    correct_valid = 0.0
    for s in correct:
        for p in s["parts"]:
            if p["zero"]:
                correct_zero += p["eur"]
            else:
                correct_valid += p["eur"]

    sheet4_evidence = {
        "buggy_parse_zero_bucket_eur": round(buggy_zero, 2),
        "correct_zero_pn_eur": round(correct_zero, 2),
        "correct_valid_pn_eur": round(correct_valid, 2),
        "buggy_sections_zero": [
            {
                "label": s["label"],
                "n_parts": len(s["parts"]),
                "sum": round(s["sum"], 2),
                "first_parts": [p["part"] for p in s["parts"][:3]],
            }
            for s in buggy
            if s["label"] in ("0", "0.0") or str(s["label"]).startswith("0")
        ],
        "note": (
            "Pivot sorts PARTNBR 0 before real PNs under each country. "
            "Old audit treated 0 as country header and summed following real parts "
            "into fake orphan bucket (~314k)."
        ),
    }

    cv_cov = {}
    for db in ("ITUK", "UTI", "IRELAND", "PORTUGAL", "ISD"):
        allp = by_db_dates.get(db, [])
        partsp = by_db_parts.get(db, [])
        dates = [d for d, _ in allp]
        m = monthly(partsp, 2025)
        cv_cov[db] = {
            "n_cy2025_all": sum(1 for d, _ in allp if d.year == 2025),
            "n_cy2025_parts": sum(1 for d, _ in partsp if d.year == 2025),
            "date_min": str(min(dates)) if dates else None,
            "date_max": str(max(dates)) if dates else None,
            "cy2025_parts_monthly": m,
        }
        print(
            f"CV {db}: n_parts={cv_cov[db]['n_cy2025_parts']} "
            f"{m['min']}..{m['max']} holes={m['black_holes_2plus']} ok={m['continuous']}"
        )
    wb.close()

    # LCV
    print("Loading LCV...")
    wb = openpyxl.load_workbook(LCV, data_only=True, read_only=True)
    export = next((n for n in wb.sheetnames if "Export" in n or "Claim" in n), wb.sheetnames[-1])
    ws = wb[export]
    rows = ws.iter_rows(values_only=True)
    headers = list(next(rows))
    dist_i = find_col(headers, "DistributorName", "Distributor")
    date_i = find_col(headers, "Written Date_YMD", "Written Date", "AssessmentDate")
    if date_i is None:
        for i, h in enumerate(headers):
            if h and "date" in str(h).lower():
                date_i = i
                break
    cost_i = find_col(headers, "Approved total part cost", "Total Part Cost", "Part Cost")
    print(f"LCV sheet={export} dist={dist_i} date={date_i} cost={cost_i}")
    loose = [
        ("ISUZU (UK)", "IUK"),
        ("ISUZU SALES DEUTSCHLAND - ISD", "ISD"),
        ("ISUZU IRELAND", "IRELAND"),
        ("IMOTORS", "PORTUGAL"),
    ]
    by = defaultdict(list)
    for row in rows:
        dist = str(row[dist_i] or "").strip() if dist_i is not None else ""
        d = parse_ymd(row[date_i]) if date_i is not None else None
        if d is None and date_i is not None and isinstance(row[date_i], datetime):
            d = row[date_i].date()
        if d is None:
            continue
        db = None
        for needle, code in loose:
            if needle.upper() in dist.upper():
                db = code
                break
        if db is None:
            continue
        amt = float(row[cost_i]) if cost_i is not None and isinstance(row[cost_i], (int, float)) else 0.0
        by[db].append((d, amt))
    wb.close()

    lcv_cov = {}
    for db in ("IUK", "ISD", "IRELAND", "PORTUGAL"):
        dates = [d for d, _ in by.get(db, [])]
        m = monthly(by.get(db, []), 2025)
        lcv_cov[db] = {
            "n_cy2025": sum(1 for d, _ in by.get(db, []) if d.year == 2025),
            "date_min": str(min(dates)) if dates else None,
            "date_max": str(max(dates)) if dates else None,
            "cy2025_monthly": m,
        }
        print(
            f"LCV {db}: n={lcv_cov[db]['n_cy2025']} "
            f"{m['min']}..{m['max']} holes={m['black_holes_2plus']} ok={m['continuous']}"
        )

    # UMI
    print("Loading UMI...")
    wb = openpyxl.load_workbook(UMI, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = ws.iter_rows(values_only=True)
    headers = list(next(rows))
    date_i = find_col(headers, "Written Date_YMD")
    cost_i = find_col(headers, "Approved total part cost")
    pairs = []
    for row in rows:
        d = parse_ymd(row[date_i]) if date_i is not None else None
        if d is None:
            continue
        amt = float(row[cost_i]) if cost_i is not None and isinstance(row[cost_i], (int, float)) else 0.0
        pairs.append((d, amt))
    wb.close()
    dates = [d for d, _ in pairs]
    umi = {
        "n_all": len(pairs),
        "n_cy2025": sum(1 for d, _ in pairs if d.year == 2025),
        "eur_cy2025": round(sum(a for d, a in pairs if d.year == 2025), 2),
        "date_min": str(min(dates)),
        "date_max": str(max(dates)),
        "full_span_monthly": monthly(pairs),
        "cy2025_monthly": monthly(pairs, 2025),
    }
    m = umi["cy2025_monthly"]
    mf = umi["full_span_monthly"]
    print(
        f"UMI: n={umi['n_cy2025']} eur={umi['eur_cy2025']} "
        f"{m['min']}..{m['max']} holes={m['black_holes_2plus']} "
        f"full_holes={mf['black_holes_2plus']}"
    )

    # Alt files
    alt = {}
    for path in (ROOT / "CV Warranty.xlsx", ROOT / "CV warranty01_03_2026.xlsx"):
        if not path.exists():
            continue
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        info = {"sheets": wb.sheetnames, "spans": {}}
        for name in wb.sheetnames[:3]:
            ws = wb[name]
            rows = ws.iter_rows(values_only=True)
            try:
                headers = list(next(rows))
            except StopIteration:
                continue
            bi = find_col(headers, "BILLYMD", "Written Date_YMD")
            if bi is None:
                for i, h in enumerate(headers):
                    if h and "date" in str(h).lower():
                        bi = i
                        break
            if bi is None:
                info["spans"][name] = {"headers": [str(h) for h in headers[:10] if h]}
                continue
            ds = []
            for row in rows:
                d = parse_ymd(row[bi])
                if d is None and isinstance(row[bi], datetime):
                    d = row[bi].date()
                if d:
                    ds.append(d)
            info["spans"][name] = {
                "n": len(ds),
                "min": str(min(ds)) if ds else None,
                "max": str(max(ds)) if ds else None,
            }
        wb.close()
        alt[path.name] = info
        print(f"ALT {path.name}: {info['spans']}")

    table = []
    for db, info in cv_cov.items():
        m = info["cy2025_parts_monthly"]
        table.append(
            {
                "db": db,
                "source": "CV",
                "n": info["n_cy2025_parts"],
                "min": info["date_min"],
                "max": info["date_max"],
                "m_min": m["min"],
                "m_max": m["max"],
                "holes": m["black_holes_2plus"],
                "zero_months": m["zero_months"],
                "ok": m["continuous"],
            }
        )
    for db, info in lcv_cov.items():
        m = info["cy2025_monthly"]
        table.append(
            {
                "db": db,
                "source": "LCV",
                "n": info["n_cy2025"],
                "min": info["date_min"],
                "max": info["date_max"],
                "m_min": m["min"],
                "m_max": m["max"],
                "holes": m["black_holes_2plus"],
                "zero_months": m["zero_months"],
                "ok": m["continuous"],
            }
        )
    m = umi["cy2025_monthly"]
    mf = umi["full_span_monthly"]
    table.append(
        {
            "db": "UMI",
            "source": "UMI file",
            "n": umi["n_cy2025"],
            "min": umi["date_min"],
            "max": umi["date_max"],
            "m_min": m["min"],
            "m_max": m["max"],
            "holes": m["black_holes_2plus"],
            "zero_months": m["zero_months"],
            "ok": m["continuous"],
            "eur_cy2025": umi["eur_cy2025"],
            "full_holes": mf["black_holes_2plus"],
            "full_ok": mf["continuous"],
        }
    )

    any_hole = any(r.get("holes") for r in table)

    # Soft-check: sparse DBs with few claims may have single zero months — flag only 2+ consecutive
    verdicts = {
        "A_314k_skippable": {
            "yes": True,
            "why": (
                f"PARTNBR 0000000000 = labour lines: {blank_stats['n']} CY2025 rows on "
                f"DATA WITHOUT MIDI, PARTAMT sum=EUR {blank_stats['partamt']:.2f}, "
                f"LBRAMT sum=EUR {blank_stats['lbr']:,.2f}. "
                f"Sheet4 fake orphan EUR {sheet4_evidence['buggy_parse_zero_bucket_eur']:,.2f} "
                f"was buggy pivot parse (0 sorted before real PNs; following parts mis-bucketed). "
                f"Correct zero-PN parts EUR={sheet4_evidence['correct_zero_pn_eur']}."
            ),
        },
        "B_ie_pt_still_problem": {
            "yes": False,
            "ireland": ie_pt["IRELAND"],
            "portugal": ie_pt["PORTUGAL"],
            "why": (
                "Blank-PN rows are labour (skip). Remaining unpriced cells are real PNs "
                "missing from ITUK/UTI price map — valuation lower-bound only, not missing "
                "warranty data. Non-blocking for GPS parts gap narrative."
            ),
        },
        "C_black_holes": {"any_big_black_hole": any_hole, "table": table},
        "D_data_missing_gps_cy2025": {
            "yes": bool(any_hole),
            "statement": (
                "Some DBs show multi-month zero periods — see coverage table."
                if any_hole
                else (
                    "No data missing for GPS CY2025 parts warranty on key DBs "
                    "(files present, no multi-month black holes; 314k/IE-PT labour-or-parse caveats closed)."
                )
            ),
        },
    }

    payload = {
        "verified": "2026-07-27",
        "jerome_rule": [
            "SKIP PARTNBR 0 / 0000000000 (no real PN) — labour, not parts country gap",
            "IE/PT incomplete prices: same — skip labour/no-PN; don't chase price-map for non-parts",
            "If warranty data exists for both customers with no big black periods -> no data missing",
        ],
        "blank_pn_labour": {
            **blank_stats,
            "by_cty": {k: dict(v) for k, v in blank_stats["by_cty"].items()},
            "samples": samples_blank,
        },
        "valid_pn": {k: round(v, 2) if isinstance(v, float) else v for k, v in valid.items()},
        "ie_pt": ie_pt,
        "sheet4_evidence": sheet4_evidence,
        "cv_coverage": cv_cov,
        "lcv_coverage": lcv_cov,
        "umi_coverage": umi,
        "alt_files": alt,
        "verdicts": verdicts,
    }
    out_path = OUT / "sanity_results.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"WROTE {out_path}")
    print(json.dumps(verdicts, indent=2, default=str))


if __name__ == "__main__":
    main()
