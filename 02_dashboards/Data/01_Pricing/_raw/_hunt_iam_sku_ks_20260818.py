"""One-shot: search KS by IAM SKU (do not zfill — Febi 16953 is not a 10-digit OE)."""
from __future__ import annotations

import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\autodoc_scraper")
from ks_scraper import HEADERS, BASE_URL, parse_ks_page  # noqa: E402

OUT_DIR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw")
CSV_PATH = OUT_DIR / "iam_sku_ks_hunt_20260818.csv"
JSON_PATH = OUT_DIR / "iam_sku_ks_hunt_20260818.json"

# Eucon UK 2023 IAM competitor PNs that fit billed Isuzu pads/rotors (HCV/LCV).
HUNTS = [
    {"isze_pn": "8982447940", "brand": "BLUE PRINT", "sku": "ADZ94218", "role": "ITUK volume pad"},
    {"isze_pn": "8982447940", "brand": "Febi", "sku": "16953", "role": "ITUK volume pad"},
    {"isze_pn": "8982447940", "brand": "Ferodo", "sku": "FCV1853", "role": "ITUK volume pad"},
    {"isze_pn": "8982447940", "brand": "Textar", "sku": "2945401", "role": "ITUK volume pad"},
    {"isze_pn": "8982169210", "brand": "BLUE PRINT", "sku": "ADZ94236", "role": "N35 pad"},
    {"isze_pn": "8982169210", "brand": "Febi", "sku": "16951", "role": "N35 pad"},
    {"isze_pn": "8982169210", "brand": "Textar", "sku": "2942001", "role": "N35 pad"},
    {"isze_pn": "8982169210", "brand": "Delphi", "sku": "LP2770", "role": "N35 pad"},
    {"isze_pn": "8982169210", "brand": "Winnard", "sku": "WP1572", "role": "N35 pad"},
    {"isze_pn": "8982488951", "brand": "BLUE PRINT", "sku": "ADZ94320", "role": "ITUK front rotor KS-404"},
    {"isze_pn": "8982488951", "brand": "Febi", "sku": "47468", "role": "ITUK front rotor KS-404"},
    {"isze_pn": "8976526220", "brand": "Brembo", "sku": "P34007", "role": "LCV pad KS-404"},
    {"isze_pn": "8976526220", "brand": "Brembo", "sku": "P 34 007", "role": "LCV pad KS-404"},
    {"isze_pn": "8976526220", "brand": "TRW", "sku": "GDB3545", "role": "LCV pad KS-404"},
]


def main() -> None:
    session = requests.Session()
    session.headers.update(HEADERS)
    rows = []
    for i, h in enumerate(HUNTS):
        url = BASE_URL.format(pn=requests.utils.quote(h["sku"]))
        rec = {
            **h,
            "url": url,
            "http_status": None,
            "result_count": None,
            "am_min_gbp": None,
            "am_n": 0,
            "am_titles": "",
            "gen_min_gbp": None,
            "gen_n": 0,
            "status": "error",
            "notes": "",
            "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        try:
            r = session.get(url, timeout=25)
            rec["http_status"] = r.status_code
            parsed = parse_ks_page(r.text, h["sku"])
            rec["result_count"] = parsed.get("result_count")
            am = parsed.get("aftermarket") or []
            ge = parsed.get("genuine") or []
            rec["am_n"] = len(am)
            rec["gen_n"] = len(ge)
            if am:
                rec["am_min_gbp"] = min(p["price_ex"] for p in am if p.get("price_ex") is not None)
                rec["am_titles"] = " | ".join(
                    f"{p.get('name')} £{p.get('price_ex')} sku={p.get('sku')}" for p in am[:6]
                )
            if ge:
                rec["gen_min_gbp"] = min(p["price_ex"] for p in ge if p.get("price_ex") is not None)
            rec["notes"] = parsed.get("notes") or ""
            rec["status"] = "ok" if (am or ge or (rec["result_count"] or 0) > 0) else "no_results"
            print(
                f"{h['sku']:12} {rec['status']:10} n={rec['result_count']} "
                f"am={rec['am_n']} gen={rec['gen_n']} min={rec['am_min_gbp']}",
                flush=True,
            )
        except Exception as e:
            rec["notes"] = str(e)
            rec["status"] = "error"
            print(f"{h['sku']:12} ERROR {e}", flush=True)
        rows.append(rec)
        if i < len(HUNTS) - 1:
            time.sleep(1.6)

    fields = list(rows[0].keys())
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote {CSV_PATH}", flush=True)


if __name__ == "__main__":
    main()
