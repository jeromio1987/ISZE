#!/usr/bin/env python3
"""Cheap content gate for ISZE_Exec_Aftersales_Paper.html (2026-09-15 retro).

Exit 0 = required strings / absences look OK for a commercialisation re-cut.
Does not replace paint/screenshot QA or verify-before-done receipt.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_Exec_Aftersales_Paper.html"
TENDER = ROOT / "01_data" / "14_dashboards" / "tender_data.json"
CMD = ROOT / "02_dashboards" / "sales" / "OPEN_ISZE_Exec_Aftersales_Paper.cmd"

FORBIDDEN = [
    (r"\bwallet\b", "forbidden word: wallet"),
    (r"\bstreet\b", "forbidden word: street"),
    (r"IML v7", "shared nickname: IML v7"),
    (r"Model B", "shared nickname: Model B"),
    (r"PRISM lane", "shared nickname: PRISM lane"),
]


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")


def _ok(msg: str) -> None:
    print(f"OK: {msg}")


def main() -> int:
    fails: list[str] = []

    if not HTML.is_file():
        _fail(f"missing HTML: {HTML}")
        return 1
    text = HTML.read_text(encoding="utf-8", errors="replace")
    low = text.lower()

    if not CMD.is_file():
        fails.append(f"missing launcher: {CMD}")
    else:
        _ok("OPEN_*.cmd present")

    if "cdn.jsdelivr" in low or "cdnjs.cloudflare" in low:
        fails.append("CDN chart library reference found")
    else:
        _ok("no CDN chart CDN hosts")

    bar_rows = len(re.findall(r'class="[^"]*bar-row', text))
    canvases = len(re.findall(r"<canvas\b", text, flags=re.I))
    if bar_rows < 1 and canvases < 1:
        fails.append("no bar-row or canvas charts")
    else:
        _ok(f"charts present (bar-row~{bar_rows}, canvas~{canvases})")

    # Commercialisation markers (post-review). Soft on exact wording; require themes.
    need_any = [
        (
            "ceiling_placeholder",
            [
                r"placeholder",
                r"flat\s*(?:EUR|euro|€)?\s*250",
                r"250\s*/\s*uio",
                r"flat\s*250",
            ],
            "ceiling / flat 250/UIO placeholder disclose",
        ),
        (
            "category_gap",
            [r"clutch\s*disc", r"brake\s*pad", r"brake\s*shoe"],
            "category gap (clutch/brake) on page",
        ),
        (
            "gap_types",
            [r"substitution", r"under[\s-]?service", r"catalogue\s*gap"],
            "gap-type split language",
        ),
        (
            "warranty",
            [r"warranty"],
            "warranty mentioned",
        ),
        (
            "telematics_or_gap",
            [r"telematic", r"subscription", r"connected[\s-]vehicle", r"vin\s+feed"],
            "telematics/subscriptions sized or named",
        ),
        (
            "book_b",
            [r"book\s*b\s*\(the price list we might change\)", r"alloc(?:ation)?\s*ambition"],
            "Book B glossed + alloc ambition",
        ),
    ]

    for _key, pats, label in need_any:
        if any(re.search(p, text, flags=re.I) for p in pats):
            _ok(label)
        else:
            fails.append(f"missing required theme: {label}")

    # Margin: business GP language — not CSS "margin:"
    if re.search(
        r"(?:gross\s*(?:profit|margin)|GP\s+at\s+risk|parts\s+GP|dealer\s+GP|\b(?:margin|GP)\s+UNKNOWN|UNKNOWN.{0,40}(?:margin|gross\s*profit))",
        text,
        flags=re.I,
    ):
        _ok("margin layer or margin UNKNOWN")
    else:
        fails.append("no margin / GP layer and no margin UNKNOWN")

    # Sell-out share of GPS billed book (not CSS width:NN% next to a sell-out bar label)
    bodyish = re.sub(r'style\s*=\s*"[^"]*"', " ", text, flags=re.I)
    bodyish = re.sub(r"style\s*=\s*'[^']*'", " ", bodyish, flags=re.I)
    if re.search(
        r"sell[\s-]?out.{0,160}(?:\d+(?:[.,]\d+)?\s*%\s*of\s*(?:GPS\s+)?billed|percent of (?:the )?(?:GPS\s+)?billed|share of (?:the )?(?:GPS\s+)?billed)",
        bodyish,
        flags=re.I,
    ) or re.search(
        r"(?:\d+(?:[.,]\d+)?\s*%|percent).{0,40}of\s+(?:GPS\s+)?billed.{0,80}sell[\s-]?out",
        bodyish,
        flags=re.I,
    ) or re.search(
        r"sell[\s-]?out.{0,80}(?:covers?|coverage).{0,40}\d+(?:[.,]\d+)?\s*%",
        bodyish,
        flags=re.I,
    ):
        _ok("sell-out framed with share/percent of billed book")
    else:
        fails.append("sell-out coverage not framed as % of billed / share of book")

    for pat, label in FORBIDDEN:
        if re.search(pat, text, flags=re.I):
            # Allow Book B gloss and footnote filenames — "street"/"wallet" never OK
            fails.append(label)

    # Live tender as-of: require opportunity count near tender language (not a PN substring)
    if TENDER.is_file():
        try:
            td = json.loads(TENDER.read_text(encoding="utf-8"))
            live_n = None
            if isinstance(td, dict):
                stats = td.get("meta", {}).get("stats") if isinstance(td.get("meta"), dict) else None
                if isinstance(stats, dict) and "opportunities" in stats:
                    live_n = int(stats["opportunities"])
                elif isinstance(td.get("opportunities"), list):
                    live_n = len(td["opportunities"])
                elif isinstance(td.get("summary"), dict) and "opportunities" in td["summary"]:
                    live_n = int(td["summary"]["opportunities"])
                elif "opportunity_count" in td:
                    live_n = int(td["opportunity_count"])
            if live_n is not None:
                # Word-ish context: "376 opportunities" or "opportunities … 376"
                pat_a = re.compile(
                    rf"(?<!\d){live_n}(?!\d)\s+opportunit",
                    flags=re.I,
                )
                pat_b = re.compile(
                    rf"opportunit\w*.{{0,40}}(?<!\d){live_n}(?!\d)",
                    flags=re.I,
                )
                if pat_a.search(text) or pat_b.search(text):
                    _ok(f"tender opportunity count matches live ({live_n})")
                else:
                    fails.append(
                        f"tender opportunity count {live_n} from live feed not found next to "
                        "'opportunities' in HTML (stale page 10 risk)"
                    )
            else:
                _ok("tender_data.json present (count shape not parsed; skip exact match)")
        except Exception as e:  # noqa: BLE001
            fails.append(f"could not parse tender_data.json: {e}")
    else:
        fails.append(f"missing tender feed: {TENDER}")

    # Account-health calibration honesty when the paper cites RED/AMBER distributors
    if re.search(r"\bRED\b", text) and re.search(r"\bAMBER\b", text):
        if re.search(r"thresholds?[_\s-]?calibrat", text, flags=re.I) or re.search(
            r"not\s+calibrat|uncalibrat|draft\s+thresholds", text, flags=re.I
        ):
            _ok("account-health calibration qualifier present")
        else:
            fails.append("RED/AMBER cited without thresholds_calibrated / uncalibrated qualifier")

    if fails:
        for f in fails:
            _fail(f)
        print("VERIFY_EXEC_AFTERSALES=FAIL")
        return 1

    print("VERIFY_EXEC_AFTERSALES=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
