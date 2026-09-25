# -*- coding: utf-8 -*-
"""Build `04_tools/price_ledger/fx_rates.json` from the ECB's daily euro reference rates.

WHY THIS EXISTS
---------------
`build_price_ledger.py` validates with

    if df["currency"].map(FX).isna().any():
        errors.append("currency without FX rate")

against an inline `FX = {"EUR": 1.0, "GBP": 1.17, "SEK": 0.089}`. Every Phase 1
target except KS and Omega prices in a currency that is NOT in that table
(NOK, DKK, USD), so every row from those sites would be **refused** before it
reached the ledger. That is a blocker, not a rounding difference.

Rather than hand-typing a rate into a source file (which is how a wrong number
gets a clean audit trail — the same failure the OE RRP column caused), this script
writes a dated, cited JSON next to the ledger. One run, one citable source.

SOURCE
------
European Central Bank, euro foreign exchange reference rates, daily.
    https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
Public, no key, no scraping in the aggressive sense, and citable. The ECB quotes
**units of currency per euro**, so the euro value of one unit is `1 / rate`.

CONVENTION
----------
Output is `eur_per_unit` — the multiplier the ledger applies (`price * fx`), so it
matches the existing `FX` table's convention: `FX["GBP"] = 1.17` means 1 GBP is
worth 1.17 EUR. Verified: the ECB gives GBP 0.85986 per EUR, i.e. 1/0.85986 =
1.16298 EUR per GBP, which agrees with the working 1.17 already in the ledger.

This script writes a NEW file and changes nothing else. It does not edit
`build_price_ledger.py` — wiring the ledger to read this file is a proposed,
one-line change that belongs to the orchestrator.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ISZE = Path(__file__).resolve().parents[2]
OUT = ISZE / "04_tools" / "price_ledger" / "fx_rates.json"

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
UA = "ISZE-parts-research/1.0 (+aftersales analytics; contact via IML)"

# The ledger's PRICE_TYPES/CURRENCIES plus every currency the Phase 1 targets use.
WANTED = ["EUR", "GBP", "USD", "NOK", "SEK", "DKK", "PLN", "ILS",
          "JPY", "CHF", "HUF", "RON", "CZK"]


def main() -> int:
    r = requests.get(ECB_URL, timeout=30, headers={"User-Agent": UA})
    if r.status_code != 200:
        print(f"FAIL — ECB returned HTTP {r.status_code}")
        return 1

    text = r.text
    day = re.search(r'time=["\']([\d-]+)["\']', text)
    ref_date = day.group(1) if day else "unknown"

    # <Cube currency="USD" rate="1.1367"/>
    raw = dict(re.findall(r'currency=["\']([A-Z]{3})["\']\s+rate=["\']([\d.]+)["\']', text))
    if "USD" not in raw:
        print("FAIL — no rates parsed out of the ECB document; format may have changed")
        return 1

    eur_per_unit = {"EUR": 1.0}
    missing = []
    for cur in WANTED:
        if cur == "EUR":
            continue
        rate = raw.get(cur)
        if rate is None:
            missing.append(cur)
            continue
        units_per_eur = float(rate)
        eur_per_unit[cur] = round(1.0 / units_per_eur, 10)

    payload = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder": "04_tools/price_ledger/build_fx_rates.py",
        "reference_date": ref_date,
        "source": "European Central Bank euro foreign exchange reference rates (daily)",
        "source_url": ECB_URL,
        "convention": "eur_per_unit — multiply the native price by this to get EUR "
                      "(same convention as the existing inline FX table in build_price_ledger.py)",
        "quoted_as": "the ECB quotes units of currency per euro; eur_per_unit = 1 / quoted",
        "raw_ecb_units_per_eur": {k: raw[k] for k in WANTED if k in raw},
        "eur_per_unit": eur_per_unit,
        "missing_from_ecb": missing,
        "note": "ECB reference rates are published for information and are not a deal rate. "
                "They are used here so a Norwegian, Danish or US price can be recorded in euro "
                "at all; they replace no negotiated rate.",
        "supersedes": "the inline FX = {'EUR':1.0,'GBP':1.17,'SEK':0.089} working table "
                      "(as_of 2026-05-01, described in the ledger as 'not official')",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"reference date : {ref_date}")
    print(f"written        : {OUT}")
    print(f"currencies     : {len(eur_per_unit)}")
    for cur in sorted(eur_per_unit):
        print(f"  1 {cur} = {eur_per_unit[cur]:.6f} EUR")
    if missing:
        print(f"missing from ECB (left out on purpose): {missing}")

    # Drift against the 2026-05-01 working rates the ledger used before the rebase.
    # Reported for the record: it is the size of the change that was applied on
    # 2026-09-25, not a live disagreement - the ledger now uses the ECB rates above.
    print("\nrebase size against the 2026-05-01 working rates (applied 2026-09-25):")
    for cur, working in (("GBP", 1.17), ("SEK", 0.089)):
        ecb = eur_per_unit.get(cur)
        if ecb:
            drift = 100 * (ecb / working - 1)
            print(f"  {cur}: working {working} -> ECB {ecb:.6f}  ({drift:+.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
