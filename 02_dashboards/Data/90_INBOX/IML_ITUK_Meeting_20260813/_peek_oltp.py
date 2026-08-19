"""See if Duncan YTD matches OLTP warehouse sheet."""
from __future__ import annotations

import json
from pathlib import Path

import openpyxl
import pandas as pd

PACK = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IML_ITUK_Meeting_20260813")
XLSX = PACK / "N75_N35_Part_Numbers_-_PMS_Project.xlsx"
PREV = json.loads((PACK / "_pms_anomaly_check.json").read_text(encoding="utf-8"))
pns = [r["pn"] for r in PREV["pn_rows"]]

wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
for name in ["OLTP V_Item And Sundry - Wareho", "Sheet3"]:
    ws = wb[name]
    headers = None
    hits = []
    n = 0
    pn_idx = None
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        n += 1
        if i == 1:
            headers = [None if v is None else str(v) for v in row]
            print(name, "HEADERS", headers, flush=True)
            for j, h in enumerate(headers):
                if h and "part" in h.lower() or (h and h.lower() in ("item", "sku", "material", "pn")):
                    pn_idx = j
            continue
        if i == 2:
            print("row2", [None if v is None else str(v)[:40] for v in row[:12]], flush=True)
        if i > 8:
            break
    print("rows", n, "pn_idx", pn_idx, flush=True)
wb.close()
