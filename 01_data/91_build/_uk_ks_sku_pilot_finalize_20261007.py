# -*- coding: utf-8 -*-
"""Write empty staging + rebuild wider UK exact metrics (no ledger append — 0 accepts)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_sku_pilot_20261007"

# Staging header (same shape as Isuzu-PN pilot) — 0 data rows
hdr = (
    "obs_id,part_no,match_method,competitor_brand,competitor_pn,description,source,"
    "source_url,country,observed_at,vintage,price,price_avg,currency,price_eur,fx_note,"
    "vat,price_type,stock,n_obs,loader,delivery_note,delivery_included,"
    "delivery_cost_amount,delivery_cost_currency,family,pilot_verdict,sku_searched,bridge_tier\n"
)
staging = OUT / "staging_exact_oem_accepted_sku_pilot_20261007.csv"
staging.write_text(hdr, encoding="utf-8")
print("wrote", staging)

# Before metrics (baseline already on disk)
before_paths = [
    WT / "01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json",
    ROOT / "01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json",
]
before = None
before_path = None
for p in before_paths:
    if p.exists():
        before = json.loads(p.read_text(encoding="utf-8"))
        before_path = p
        break
print(
    "BEFORE eligible_rows",
    before.get("eligible_rows") if before else None,
    "eligible_pns",
    before.get("eligible_pns") if before else None,
    "from",
    before_path,
)

# Rebuild from worktree (ledger lives there)
builder = WT / "01_data/91_build/build_market_data_gap_coverage_20261007.py"
rc = subprocess.call([sys.executable, str(builder), "--also-uk-exact"], cwd=str(WT))
print("rebuild rc", rc)

after_path = WT / "01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
after = json.loads(after_path.read_text(encoding="utf-8")) if after_path.exists() else {}
print(
    "AFTER eligible_rows",
    after.get("eligible_rows"),
    "eligible_pns",
    after.get("eligible_pns"),
)

# Mirror metrics into main clone derived (same as prior pilot path convention)
main_metrics = ROOT / "01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
if after_path.exists():
    main_metrics.write_text(after_path.read_text(encoding="utf-8"), encoding="utf-8")
    print("mirrored metrics ->", main_metrics)

rollup = {
    "before": {
        "eligible_rows": before.get("eligible_rows") if before else None,
        "eligible_pns": before.get("eligible_pns") if before else None,
        "path": str(before_path),
    },
    "after": {
        "eligible_rows": after.get("eligible_rows"),
        "eligible_pns": after.get("eligible_pns"),
        "path": str(after_path),
    },
    "ledger_appended": False,
    "accepted_exact_oem": 0,
    "staging": str(staging),
}
(OUT / "sku_pilot_eligible_before_after_20261007.json").write_text(
    json.dumps(rollup, indent=2), encoding="utf-8"
)
print("wrote", OUT / "sku_pilot_eligible_before_after_20261007.json")
raise SystemExit(rc)
