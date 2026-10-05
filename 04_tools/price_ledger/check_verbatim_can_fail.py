# -*- coding: utf-8 -*-
"""Prove the verbatim check can FAIL — third attempt, and why the first two didn't.

Attempt 1: planted rows in OFFERED_ROWS.csv but never rebuilt the ledger, so the
verifier (which reads the parquet) never saw them.
Attempt 2: planted them and rebuilt, but the rows collided on `obs_id` with the real
row and the ledger REFUSED the build ("duplicate obs_id"), so the verifier again ran
against the old parquet. That refusal is the ledger's own guard working correctly — it
is worth knowing it exists.

This attempt plants rows whose id cannot collide: the id is recomputed the same way the
bridge computes it, so each planted row keeps its link to the real source page and
reaches the parquet. Then the verifier must reject them.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ISZE = Path(__file__).resolve().parents[2]
LD = ISZE / "04_tools" / "price_ledger"
OFFERED = LD / "OFFERED_ROWS.csv"
LEDGER = ISZE / "01_data" / "00_derived" / "price_observations.parquet"
bak_off, bak_led = LD / "_bak_offered.csv", LD / "_bak_ledger.parquet"

KEY_COLS = ["part_no", "competitor_brand", "competitor_pn", "source", "country",
            "observed_at", "price_type", "loader", "description", "source_url"]


def obs_id_for(row: dict) -> str:
    """Exactly the bridge's formula, so a planted row keeps its page link."""
    key = "|".join(str(row.get(c)) for c in KEY_COLS)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def run(script):
    return subprocess.run([sys.executable, str(script)], capture_output=True, text=True, cwd=str(ISZE))


shutil.copy2(OFFERED, bak_off)
shutil.copy2(LEDGER, bak_led)
exit_code = 1
try:
    d = pd.read_csv(OFFERED, dtype={"part_no": str})
    base = d[(d["loader"] == "geparden") & (d["price"].notna())].iloc[0].to_dict()
    page = base["page_file"]
    print(f"base row source page: {page}")

    # 1. a price that is nowhere on that page (real part number, false price)
    fp = dict(base)
    fp["price"] = 987654.32
    fp["price_eur"] = None
    fp["description"] = "PLANTED false price for the verifier self-test"
    fp["obs_id"] = obs_id_for(fp)

    # 2. a part number that is nowhere on that page
    fn = dict(base)
    fn["part_no"] = "1111111111"
    fn["description"] = "PLANTED false part number for the verifier self-test"
    fn["obs_id"] = obs_id_for(fn)

    pd.concat([d, pd.DataFrame([fp, fn])], ignore_index=True).to_csv(OFFERED, index=False)
    print(f"planted 2 rows with non-colliding ids: {fp['obs_id']}, {fn['obs_id']}")

    b = run(LD / "build_price_ledger.py")
    print(f"ledger build exit {b.returncode}" + ("  <- REFUSED" if b.returncode else ""))

    v = run(LD / "verify_scraped_observations.py")
    print(f"verifier exit {v.returncode}  (non-zero expected)\n")
    for line in v.stdout.splitlines():
        s = line.strip()
        if s.startswith("FAIL") or "987654" in s or "1111111111" in s:
            print(f"   {s[:160]}")

    caught_price = "987654" in v.stdout
    caught_pn = "1111111111" in v.stdout
    failed = "failed:" in v.stdout and "failed: 0" not in v.stdout
    ok = v.returncode != 0 and caught_price and caught_pn and failed
    print()
    print(f"   caught the false price      : {caught_price}")
    print(f"   caught the false part number: {caught_pn}")
    print()
    print("PASS — the verbatim check rejects fabricated rows" if ok
          else "FAIL — the check did not catch a planted row")
    exit_code = 0 if ok else 1
finally:
    shutil.copy2(bak_off, OFFERED)
    shutil.copy2(bak_led, LEDGER)
    bak_off.unlink(); bak_led.unlink()
    r = run(LD / "verify_scraped_observations.py")
    print(f"\nrestored both files; verifier on the restored state: exit {r.returncode}")

raise SystemExit(exit_code)
