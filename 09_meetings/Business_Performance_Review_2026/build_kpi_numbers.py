"""KPI Master File — fill rate, days of stock, back orders, coverage. Writes _kpi_numbers.json."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
KPI = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\planning\KPI Master File august 2026.xlsx")

out: dict = {"source": str(KPI)}

# ---- Days of Parts in Stock
stock = pd.read_excel(KPI, sheet_name="Parts Handling", header=None, skiprows=2, nrows=22)
hdr = pd.read_excel(KPI, sheet_name="Parts Handling", header=None, nrows=3).iloc[2].tolist()
months = [str(m) for m in hdr[1:] if str(m) != "nan"]
stock.columns = ["Distributor"] + [f"c{i}" for i in range(len(stock.columns) - 1)]
stock_rows = {}
for _, r in stock.iterrows():
    if pd.isna(r["Distributor"]):
        continue
    vals = [r[c] for c in stock.columns[1:]]
    stock_rows[str(r["Distributor"]).strip()] = vals

# ---- First Fill Rate
fill = pd.read_excel(KPI, sheet_name="Parts Handling", header=None, skiprows=29, nrows=22)
fill.columns = ["Distributor"] + [f"c{i}" for i in range(len(fill.columns) - 1)]
fill_rows = {}
for _, r in fill.iterrows():
    if pd.isna(r["Distributor"]):
        continue
    fill_rows[str(r["Distributor"]).strip()] = [r[c] for c in fill.columns[1:]]

# ---- Back Order Lines
bo = pd.read_excel(KPI, sheet_name="Parts Handling", header=None, skiprows=56, nrows=22)
bo.columns = ["Distributor"] + [f"c{i}" for i in range(len(bo.columns) - 1)]
bo_rows = {}
for _, r in bo.iterrows():
    if pd.isna(r["Distributor"]):
        continue
    bo_rows[str(r["Distributor"]).strip()] = [r[c] for c in bo.columns[1:]]


def latest(vals, asof_str=True):
    """Return the last month that has a real number, with its label."""
    for i in range(len(vals) - 1, -1, -1):
        v = vals[i]
        if v is None or (isinstance(v, float) and pd.isna(v)):
            continue
        if isinstance(v, str):
            s = v.strip()
            if s in ("", "N/D", "N/A", "nan"):
                continue
            try:
                return float(s), i
            except ValueError:
                continue
        return float(v), i
    return None, None


def summarise(rows, label, scale=1.0):
    res = {}
    for db, vals in rows.items():
        v, idx = latest(vals)
        if v is None:
            res[db] = {"latest": None, "month_idx": None}
            continue
        res[db] = {
            "latest": round(v * scale, 2),
            "month_idx": idx,
            "month_label": months[idx] if idx is not None and idx < len(months) else None,
            "history_last6": [None if (x is None or (isinstance(x, float) and pd.isna(x))
                                      or str(x).strip() in ("", "N/D", "N/A", "nan"))
                              else (round(float(x) * scale, 2) if _isnum(x) else None)
                              for x in vals[-6:]],
        }
    reported = sum(1 for r in res.values() if r["latest"] is not None)
    out[label] = {
        "months": months,
        "by_db": res,
        "reported": reported,
        "total_rows": len(res),
    }
    return res


def _isnum(x):
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def _maxnum(rows):
    best = None
    for vals in rows.values():
        for x in vals:
            if _isnum(x):
                f = float(x)
                best = f if best is None else max(best, f)
    return best


_mx = _maxnum(fill_rows)
fill_scale = 100.0 if (_mx is not None and _mx < 1.5) else 1.0
print("fill scale", fill_scale, "max raw", _mx)
summarise(fill_rows, "first_fill_rate", scale=fill_scale)
summarise(stock_rows, "days_of_parts_in_stock", scale=1.0)
summarise(bo_rows, "back_order_lines", scale=1.0)

(HERE / "_kpi_numbers.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
ff = out["first_fill_rate"]
print("months span", ff["months"][0], "->", ff["months"][-1])
print(f"fill rate reported by {ff['reported']} of {ff['total_rows']} rows")
for db in ["ITUK", "IUK", "ISD", "UMI", "RSA", "Isuzu Sverige", "IBX (BENELUX)", "Imotors"]:
    r = ff["by_db"].get(db)
    print(f"  {db:18s} {r['latest'] if r else None}  ({r['month_label'] if r else ''})")
st = out["days_of_parts_in_stock"]
print(f"stock reported by {st['reported']} of {st['total_rows']}")
for db in ["ITUK", "IUK", "ISD", "UMI", "RSA", "Isuzu Sverige"]:
    r = st["by_db"].get(db)
    print(f"  {db:18s} {r['latest'] if r else None}  ({r['month_label'] if r else ''})")
