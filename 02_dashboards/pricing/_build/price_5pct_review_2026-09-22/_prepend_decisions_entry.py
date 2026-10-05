"""Prepend the 2026-09-22 price-ambition closure entry to ISZE/DECISIONS.md.

Append-only log, newest at top. Takes a backup first and verifies the result, because an earlier
write probe on this file truncated it (restored from git HEAD before this ran).
"""
import shutil
from pathlib import Path

P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\DECISIONS.md")
BAK = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build"
           r"\price_5pct_review_2026-09-22\_qa\DECISIONS.md.bak_pre_20260922")

ENTRY = """## 2026-09-22 - The price adjustment ambition is closed, permanently

**Status:** Accepted - Jerome, chat, 2026-09-22, verbatim: *"delete price ambition I will come when it's done for now do a simulation on 5% increase and than never ask again."*

**Decision:** The price-ambition question (+4% / +5% / launch-only, and every form of it) is **closed permanently**. It is not deferred and not parked. No agent asks it again in any form. He returns to it himself when it is done.

**Executed:** The +5% flat simulation was produced the same day and is its last output. New, dated files only; the 17 September pack was not overwritten:

- `01_data/01_Pricing/Price_Increase_5pct_Flat_SIMULATION_2026-09-22.xlsx`
- `02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.html`
- `02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_SIMULATION_2026-09-22.SHIP_RECEIPT.json`
- `02_dashboards/pricing/_build/price_5pct_review_2026-09-22/price_increase_5pct_sim_summary_2026-09-22.json`

**Not executed, deliberately:** no price list, no price file and no pricing configuration was touched, and nothing was mailed. The simulation is arithmetic on paper only. `03_analytics/isze_pricing/config.yaml` was not opened for editing.

**Number, for the record:** a flat +5% is **EUR 1,749,680.47** on the whole in-scope base and **EUR 1,629,792.63** collectable on the 47,617 lines that can take a new price, against the filed revision measured at **+5.9616%** / EUR 1,652,140.71 on the same lines. The two are separate readings of one base and are **never added**. On this base the refresh reproduced the 17 September figures to the cent, because the base file has not moved.

**Docs updated:** `00_docs/PRICE_AMBITION_CLOSED_2026-09-22.md` (new, the superseding record) - `00_docs/ISZE_ROADMAP.md` section 2 ref B1 and section 5 - `00_docs/roadmaps/pricing.md` section 5 - `00_docs/DECISION_RECONCILE_20260916.md` B1 and B8 - and the "blocked on ambition" headers in `01_data/01_Pricing/PLAN_FORECAST_WEIGHTED_AMBITION.md`, `01_data/01_Pricing/BOOK_B_CONCLUSIONS_20260819.md`, `01_data/01_Pricing/DB_DLR_COMMERCIAL_STACK.md` and `00_docs/AFTERMARKET_BI_BUILD_MENU_20260819.md`. No pricing file was rewritten.

**Scope limit:** this closes the **ambition** question only. The filed +5.9616% revision and the other pricing items (`roadmaps/pricing.md` sections 2.2 to 2.8) are untouched.

---

"""

ANCHOR = b"## 2026-09-20 "

raw = P.read_bytes()
orig_len = len(raw)

if b"price adjustment ambition is closed" in raw:
    print("already present - nothing written")
    raise SystemExit(0)

idx = raw.find(ANCHOR)
assert idx > 0, "anchor entry (2026-09-20) not found - refusing to write"
assert raw.startswith(b"# ISZE decision log"), "unexpected head - refusing to write"

BAK.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(P, BAK)
print(f"backup -> {BAK.name} ({BAK.stat().st_size} bytes)")

payload = ENTRY.encode("utf-8")
new = raw[:idx] + payload + raw[idx:]

with open(P, "wb") as f:
    f.write(new)

after = P.read_bytes()
assert len(after) == orig_len + len(payload), f"length mismatch {len(after)}"
assert after == new, "content mismatch after write"
assert after.startswith(b"# ISZE decision log")
assert b"price adjustment ambition is closed" in after
assert b"## 2026-09-20 " in after, "anchor entry lost"
assert after[idx + len(payload):] == raw[idx:], "original bytes after anchor changed"

print(f"OK: {orig_len} -> {len(after)} bytes (+{len(payload)}), original tail preserved")
print("--- new head ---")
print(after[:400].decode("utf-8", errors="replace"))
