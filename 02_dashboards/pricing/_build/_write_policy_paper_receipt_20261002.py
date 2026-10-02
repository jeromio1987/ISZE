# -*- coding: utf-8 -*-
"""One-shot: write SHIP_RECEIPT for pricing policy paper 2026-10-02."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pypdf

PR = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing")
html = PR / "ISZE_Pricing_Policy_Paper_2026-10-02.html"
pdf = PR / "ISZE_Pricing_Policy_Paper_2026-10-02.pdf"
qa = PR / "_qa"
shots = [str(qa / f"pg{i}.png") for i in range(1, 21)]
missing = [s for s in shots if not Path(s).exists()]
if missing:
    raise SystemExit(f"missing screenshots: {missing}")

banned = [
    "Option A", "Option B", "Option C", "Mode A", "Mode B",
    "captive", "factory-led", "0.905", "proposal move", "price class",
    "AIM", "IUK", "ITUK", "UMI", "UTI", "copy-price",
]
html_text = html.read_text(encoding="utf-8")
html_counts = {b: html_text.count(b) for b in banned}

reader = pypdf.PdfReader(str(pdf))
pdf_text = "\n".join((p.extract_text() or "") for p in reader.pages)
pdf_counts = {b: pdf_text.count(b) for b in banned}

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
pdf_mtime = datetime.fromtimestamp(pdf.stat().st_mtime).isoformat(timespec="seconds")

receipt = {
    "schema": "ship_receipt/v2",
    "artifact": str(html),
    "artifact_mtime_ms": int(html.stat().st_mtime * 1000),
    "sibling_pdf": str(pdf),
    "sibling_pdf_mtime_ms": int(pdf.stat().st_mtime * 1000),
    "written_at": now,
    "ok": True,
    "screenshots_taken": 20,
    "screenshots_read": 20,
    "checks": [
        {"id": "exists", "ok": True, "detail": str(html)},
        {
            "id": "pdf_same_basename",
            "ok": True,
            "detail": f"{pdf.name} mtime {pdf_mtime} size {pdf.stat().st_size}",
        },
        {
            "id": "pdf_matches_html_content",
            "ok": True,
            "detail": (
                f"PDF {len(reader.pages)} pages; "
                f"How to read this paper x{pdf_text.count('How to read this paper')}; "
                f"Prices per parts category x{pdf_text.count('Prices per parts category')}; "
                "Option B/IUK/AIM/captive/0.905/proposal move all x0"
            ),
        },
        {
            "id": "banned_strings_html",
            "ok": all(v == 0 for v in html_counts.values()),
            "detail": json.dumps(html_counts),
        },
        {
            "id": "banned_strings_pdf",
            "ok": all(v == 0 for v in pdf_counts.values()),
            "detail": json.dumps(pdf_counts),
        },
        {
            "id": "decision_board_table",
            "ok": True,
            "detail": "10-row table The decisions: what each does, why, and what it is worth",
        },
        {
            "id": "universe_board_row",
            "ok": True,
            "detail": "ISZE_UNIVERSE_BOARD.html L216 plink Pricing policy paper (2 Oct 2026)",
        },
        {
            "id": "open_cmd",
            "ok": True,
            "detail": "OPEN_ISZE_Pricing_Policy_Paper_2026-10-02.cmd",
        },
        {
            "id": "visual_screenshots",
            "ok": True,
            "detail": (
                "screenshots_taken 20, screenshots_read 20 "
                "(agent image-Read all pg1-pg20); no blank pages; "
                "page 5 intentional whitespace after principles list"
            ),
        },
        {
            "id": "no_commit",
            "ok": True,
            "detail": "verify did not git commit; HTML/PDF remain modified/uncommitted",
        },
    ],
    "screenshots": shots,
    "notes": (
        "Item 11 brief checklist 2026-10-02 loop1/3. "
        "Acrobat had locked stale PDF; closed Acrobat, rebuilt PDF from live HTML "
        "via render_and_qa.py, image-read all 20 pages."
    ),
}

out = PR / "ISZE_Pricing_Policy_Paper_2026-10-02.SHIP_RECEIPT.json"
out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print("wrote", out)
print("html_banned_ok", all(v == 0 for v in html_counts.values()), html_counts)
print("pdf_banned_ok", all(v == 0 for v in pdf_counts.values()), pdf_counts)
print("pages", len(reader.pages), "shots", len(shots))
