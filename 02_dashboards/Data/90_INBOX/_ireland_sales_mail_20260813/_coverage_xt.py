"""Coverage stats for Ireland XT sales-to-dealer before normalize."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

import openpyxl

XT = Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_ireland_sales_mail_20260813"
    r"\attachments\2026-08-13_IE_XT_-_2026-08-13T114222.149.xlsx"
)


def parse_date(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    s = str(v).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            pass
    return None


def main() -> None:
    wb = openpyxl.load_workbook(XT, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    idx = {str(h).strip(): i for i, h in enumerate(header) if h is not None}
    inv_i = idx["InvoiceDate"]
    ord_i = idx["Item ordered"]
    sup_i = idx["Item supplied"]
    qty_i = idx["Qty suppld"]
    qty_ord_i = idx["Qty ordrd"]

    n = 0
    qty_sum = 0.0
    qty_ord_sum = 0.0
    months = Counter()
    years = Counter()
    mismatch_pn = 0
    zero_sup = 0
    dates = []
    for r in rows:
        n += 1
        d = parse_date(r[inv_i])
        if d:
            dates.append(d)
            months[d.strftime("%Y-%m")] += 1
            years[d.year] += 1
        qo = float(r[qty_ord_i] or 0)
        qs = float(r[qty_i] or 0)
        qty_ord_sum += qo
        qty_sum += qs
        if qs == 0:
            zero_sup += 1
        if str(r[ord_i]).strip() != str(r[sup_i]).strip():
            mismatch_pn += 1
    wb.close()
    dates.sort()
    print(f"lines={n}")
    print(f"invoice_min={dates[0]} max={dates[-1]}")
    print(f"qty_supld_sum={qty_sum}")
    print(f"qty_ordrd_sum={qty_ord_sum}")
    print(f"zero_supld_lines={zero_sup}")
    print(f"ordered_ne_supplied_lines={mismatch_pn}")
    print("years", dict(years))
    print("months:")
    for k in sorted(months):
        print(f"  {k}: {months[k]}")


if __name__ == "__main__":
    main()
