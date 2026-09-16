"""ITUK=2194; join Duncan PNs to audit + peek + sales_fact."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PACK = ROOT / r"01_data\90_INBOX\IML_ITUK_Meeting_20260813"
PREV = json.loads((PACK / "_pms_anomaly_check.json").read_text(encoding="utf-8"))
AUDIT = ROOT / r"01_data\00_derived\ituk_pms_pn_audit.csv"
SALES = ROOT / r"01_data\00_derived\sales_fact.csv"
PEEK = ROOT / r"09_meetings\Preparation Meetings\IML_ITUK_PMS\peek_ISZE___ITUK__PN_Level_.json"
OUT = PACK / "_pms_join.json"

ITUK = "2194"


def load_peek() -> dict:
    data = json.loads(PEEK.read_text(encoding="utf-8"))
    out = {}
    last_cat = None
    for _, row in data["rows"]:
        if not row:
            continue
        if row[0] in ("OIL FILTER", "FUEL FILTER", "AIR FILTER", "CLUTCH", "BRAKE"):
            last_cat = row[0]
        pn = row[1]
        if pn is None:
            continue
        pn_s = str(pn).strip()
        if not pn_s or not pn_s[0].isdigit():
            continue
        try:
            ws = float(str(row[8]).replace(",", "")) if row[8] not in (None, "") else None
        except Exception:
            ws = None
        try:
            cover = float(row[9]) if row[9] not in (None, "") else None
        except Exception:
            cover = None
        out[pn_s] = {
            "category": last_cat,
            "desc": row[2],
            "model_ituk": row[3],
            "model_iml": row[4],
            "uio": row[5],
            "freq": row[6],
            "expected": row[7],
            "ws2025": ws,
            "cover": cover,
            "pr00": row[10],
        }
    return out


def main() -> None:
    peek = load_peek()
    print("peek pns", len(peek), flush=True)
    audit = pd.read_csv(AUDIT, dtype={"part_number": str})
    audit["part_number"] = audit["part_number"].astype(str).str.replace(r"\.0$", "", regex=True)

    pns = [r["pn"] for r in PREV["pn_rows"]]
    usecols = ["sold_to", "part_number", "billed_qty", "net_sales_value", "year"]
    sf = pd.read_csv(SALES, usecols=usecols, dtype={"sold_to": str, "part_number": str})
    sf["sold_to"] = sf["sold_to"].astype(str).str.replace(r"\.0$", "", regex=True)
    sf["part_number"] = sf["part_number"].astype(str).str.replace(r"\.0$", "", regex=True)
    ituk = sf[sf["sold_to"] == ITUK]
    print("ITUK 2194 rows", len(ituk), flush=True)

    def year_map(year: int) -> dict:
        g = (
            ituk[ituk["year"] == year]
            .groupby("part_number", as_index=False)
            .agg(qty=("billed_qty", "sum"), eur=("net_sales_value", "sum"))
        )
        return {r.part_number: {"qty": float(r.qty), "eur": float(r.eur)} for r in g.itertuples(index=False)}

    ymap = {y: year_map(y) for y in (2023, 2024, 2025, 2026)}

    joined = []
    for r in PREV["pn_rows"]:
        pn = r["pn"]
        pk = peek.get(pn, {})
        au = audit[audit["part_number"] == pn]
        au_by_year = {
            int(x.year): {"qty": float(x.actual_qty), "eur": float(x.actual_rev_eur), "cat": x.pms_category, "type": x.pms_type, "model": x.pms_model}
            for x in au.itertuples(index=False)
        }
        rec = {
            **{k: r[k] for k in ("pn", "category", "priority", "n_model_slides", "models", "duncan_monthly", "duncan_ytd", "duncan_annualised_monthly", "comments", "zero_ytd")},
            "peek": pk,
            "isze": {str(y): ymap[y].get(pn) for y in (2023, 2024, 2025, 2026)},
            "audit": au_by_year,
        }
        isze25 = (ymap[2025].get(pn) or {}).get("qty")
        ws = pk.get("ws2025")
        ytd = r["duncan_ytd"] or 0
        monthly_ann = r["duncan_annualised_monthly"]
        rec["ratios"] = {
            "ytd_vs_ws": (ytd / ws) if ws else None,
            "ann_vs_ws": (monthly_ann / ws) if ws and monthly_ann else None,
            "ytd_vs_isze25": (ytd / isze25) if isze25 else None,
            "ann_vs_isze25": (monthly_ann / isze25) if isze25 and monthly_ann else None,
            "ws_vs_isze25": (ws / isze25) if ws and isze25 else None,
        }
        joined.append(rec)

    duncan_set = set(pns)
    missing = []
    for pn, info in peek.items():
        ws = info.get("ws2025") or 0
        if pn not in duncan_set and ws >= 150:
            missing.append({"pn": pn, **info})
    missing.sort(key=lambda x: -(x.get("ws2025") or 0))

    # high ISZE 2025 PMS PNs not in Duncan
    a25 = audit[audit["year"] == 2025]
    missing_audit = []
    for x in a25.itertuples(index=False):
        if x.part_number not in duncan_set and float(x.actual_qty) >= 200:
            missing_audit.append(
                {
                    "pn": x.part_number,
                    "cat": x.pms_category,
                    "qty": float(x.actual_qty),
                    "eur": float(x.actual_rev_eur),
                    "type": x.pms_type,
                    "model": x.pms_model,
                }
            )
    missing_audit.sort(key=lambda x: -x["qty"])

    # N75 vs N35 oil from peek
    def model_bucket(m):
        m = (m or "").upper()
        if m == "N75":
            return "N75"
        if m == "N35":
            return "N35"
        if "N35/N75" in m or "N35" in m and "N75" in m:
            return "shared"
        if "F-SERIES" in m:
            return "F"
        return m or "unk"

    cat_split = {}
    for pn, info in peek.items():
        cat = info.get("category") or "?"
        b = model_bucket(info.get("model_ituk"))
        cat_split.setdefault(cat, {}).setdefault(b, {"ws": 0.0, "pns": []})
        ws = info.get("ws2025") or 0
        cat_split[cat][b]["ws"] += ws
        cat_split[cat][b]["pns"].append({"pn": pn, "ws": ws, "cover": info.get("cover"), "iml": info.get("model_iml")})

    OUT.write_text(
        json.dumps(
            {
                "joined": joined,
                "missing_from_duncan_peek_ws_ge_150": missing,
                "missing_from_duncan_audit2025_qty_ge_200": missing_audit,
                "peek_count": len(peek),
                "cat_split_ws2025": cat_split,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print("missing peek", missing[:8], flush=True)
    print("missing audit", missing_audit[:12], flush=True)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
