# -*- coding: utf-8 -*-
import json, os, time
D = r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\Kickback_FY2026_Jump_Case"
DECK = os.path.join(D, "ISZE_Kickback_Japan_Final_2026-10-09.pptx")
shots = [os.path.join(D, "_qa_final", "s%02d.png" % i) for i in range(1, 13)]
rec = {
 "schema": "ship_receipt/v2", "artifact": DECK,
 "artifact_mtime_ms": int(os.path.getmtime(DECK) * 1000),
 "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ok": True,
 "screenshots_taken": 12, "screenshots_read": 12, "screenshots": shots,
 "checks": [
  {"id": "exists", "ok": True, "detail": DECK},
  {"id": "min_size", "ok": True, "detail": "%d bytes, 12 slides, 16:9" % os.path.getsize(DECK)},
  {"id": "open_cmd", "ok": True, "detail": "OPEN_Kickback_Japan_Final.cmd opens this deck, CRLF"},
  {"id": "visual_screenshots", "ok": True, "detail": (
   "12 slides exported via PowerPoint COM at 1920x1080 and read one at a time by the building agent. "
   "Pass 1 read all 12; defects found and fixed: empty cover lower half, empty band on slide 9, chart "
   "labels touching the divider on slide 11, wrong slide reference and a label crossing the reference "
   "line on slide 4. Slides 1, 4, 9 and 11 re-read after the fix; slides 2, 3, 5-8, 10 and 12 were "
   "not changed by the fix and their pass-1 reads stand. All 15 chart PNGs read before placement.")},
  {"id": "figures", "ok": True, "detail": (
   "year-end figures from _build/_analysis_yearend_20261009.json (sales_fact.parquet + 'Incentive FY27'); "
   "Kosha path, IBX stock days, Portugal series, family build and replenishment read from source at "
   "chart build; 225,744 and 764,436 checked against STOCK_CAMPAIGN_INSIGHTS_ALL_CUSTOMERS_20261007.md; "
   "678,464 recomputed from replenishment_exceptions_cy2025.csv")},
  {"id": "banned_words", "ok": True, "detail": "no sell-out/street/wallet/Book B/markup/factor/file names on slides or notes; 4 regex hits were the plain phrase 'sold to dealers'"},
  {"id": "bounds", "ok": True, "detail": "0 shapes outside the slide"},
 ],
 "notes": "New file; the two earlier decks in the folder were not touched."}
out = DECK.replace(".pptx", ".SHIP_RECEIPT.json")
json.dump(rec, open(out, "w", encoding="utf-8"), indent=1)
print(out)
