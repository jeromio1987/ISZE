# -*- coding: utf-8 -*-
"""Re-apply the fleet-brand gate to the tender feed already on disk.

The gate lives in `isze_core_v3.apply_fleet_brand_gate` and runs on every new scrape.
This script applies it to the existing `tender_data.json` so the change is visible
without waiting for the next scheduled run. It is idempotent: running it twice
changes nothing the second time.

    python 04_tools/ISZE_Tender_Monitor_Install/apply_fleet_brand_gate_to_feed.py
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import isze_core_v3 as core                                     # noqa: E402

FEED = HERE.parents[1] / "01_data" / "14_dashboards" / "tender_data.json"


def main() -> int:
    data = json.loads(FEED.read_text(encoding="utf-8"))
    bak = FEED.with_suffix(".json.bak_before_fleet_brand_gate")
    if not bak.exists():
        shutil.copy2(FEED, bak)

    before = Counter(o.get("decision") for o in data.get("opportunities", []))
    for n in data.get("notices", []):
        core.apply_fleet_brand_gate(n, str(n.get("description") or ""))
    for o in data.get("opportunities", []):
        # Re-classify with the corrected pickup pattern (2026-10-01: "Bond-Max" read as D-Max).
        core.attach_product_segment(o)
        text = " ".join(str(x.get("title") or "") for x in (o.get("notices") or []))
        core.apply_fleet_brand_gate(o, text)
    data["opportunities"].sort(key=lambda o: (
        core.DECISION_ORDER.get(o.get("decision"), 9),
        core.URGENCY_ORDER.get(o.get("urgency"), 9),
        -(o.get("opportunity_score") or 0),
    ))
    after = Counter(o.get("decision") for o in data.get("opportunities", []))
    brand = Counter(o.get("fleet_brand") for o in data.get("opportunities", []))
    demoted = [o for o in data["opportunities"] if o.get("decision_before_brand_gate")]

    FEED.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"opportunities: {len(data['opportunities'])}")
    print(f"decision before: {dict(before)}")
    print(f"decision after : {dict(after)}")
    print(f"fleet brand    : {dict(brand)}")
    print(f"demoted to Watch by the gate: {len(demoted)}")
    for o in demoted[:40]:
        print(f"   {o['decision_before_brand_gate']:<9} {o.get('country',''):<12} {str(o.get('title'))[:90]}")
    print(f"backup: {bak}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
