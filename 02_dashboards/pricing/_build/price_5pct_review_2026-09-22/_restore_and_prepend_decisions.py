"""Restore the lost 2026-09-20 DECISIONS.md entry and prepend the 2026-09-22 closure entry.

WHY THIS EXISTS
---------------
An earlier write probe on ISZE/DECISIONS.md ran `open(path, "wb")` and closed the handle without
writing, which truncated the file. It was restored from git HEAD, but the 2026-09-20 entry had
never been committed, so it was lost from disk. No copy survives: Cursor local history for that
file stops 2026-08-11, the worktree/backup copies predate it, and a scan of every git blob in the
120-200 KB range found no copy.

WHAT IS RESTORED, AND HOW CONFIDENTLY
-------------------------------------
Sections 1-3 of the 2026-09-20 entry are reproduced from the version read on disk before the
truncation - the title, status line and all three sections were read in full.
The "Also answered in the same pass" block is assembled from the decision-register entries of the
same date in `00_docs/ISZE_ROADMAP.md`, which the 2026-09-21 drift audit confirms this entry
referenced. It is marked as reconstructed in the entry itself so nobody mistakes it for verbatim.

Both writes are byte-level inserts above the existing 2026-09-19 anchor. A backup is taken and the
result is asserted before the script reports success.
"""
import shutil
from pathlib import Path

P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\DECISIONS.md")
BAK = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\_build"
           r"\price_5pct_review_2026-09-22\_qa\DECISIONS.md.bak_pre_20260922")

ENTRY_2209 = """## 2026-09-22 - The price adjustment ambition is closed, permanently

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

ENTRY_2009 = """## 2026-09-20 - GPT review forcing decisions executed (8% cap / classification / Portugal)

**Status:** Accepted - Jerome, chat, 2026-09-20, answering the recovered GPT review's three forcing decisions.

### 1. Per-line +8% ceiling - not binding; deleted

**What he said:** *"1) no binding delete it everywhere"*

**Executed:**
- `03_analytics/isze_pricing/config.yaml` - `allocation.cap` and `allocation.cap_top50` set to `null`
- `03_analytics/isze_pricing/engine.py` - null caps mean no upper clip; floor still applies
- Pricing roadmap and policy-paper REV3 builder / HTML rewritten so the +8% line is no longer presented as a live engine rule
- Historical run folders under `isze_pricing/runs/` left as archives (not rewritten)

### 2. Classification - make the export match the master

**What he said:** *"2+3) just let it be correct"* (classification half)

**Executed:**
- Rebuilt `aim_pn_classification_20260920.csv` from live `aim_master_v2` + live `pr00_classification`
- Synced `aim_pn_classification_v2.csv` workbook columns from that join (backup `*.bak_pre_master_sync_*`)
- Synced fused `aim_pn_classification.csv` `aim_l1/l2/l3` from master (backup taken)
- Spot-check: clutch pressure plate / clutch disc / tool interface now match master on the exports

### 3. Portugal light share - accept 0.6364 on 2,206 base

**What he said:** same line as (2)

**Executed / recorded:**
- `uio_ld_n35_share.csv` already holds Portugal **0.6364** / `imotors_parc_bands` / units **2206** - left as-is
- Register **D24** closed as **decided** (2026-09-20): share accepted; **ceiling rebuild still not authorised**

### Also recorded in the same pass - RECONSTRUCTED

The three sections above are as written on 2026-09-20. This block was rebuilt from the
decision-register entries of the same date (`00_docs/ISZE_ROADMAP.md`), which the 2026-09-21 drift
audit confirms this entry referenced. Each line is one factual clause from the register. Treat the
register as the authority, not this block.

- **D01 / D02** - swap the two action labels in the revision exception builder, and widen the raise / no-raise band to **0.80 / 1.10** with brakes named first. Decided; **not executed.**
- **D03** - the **margins reading** (37%, then 25-27.5%; combined multiple about 2.15-2.19). The multiplier chain is **not adopted**. Decided and informed; **not executed.**
- **D08** - rebuild the five live dashboards, the AIM truck catalogue and the BPR deck so the fleet reads **163,198** and the per-truck slide becomes a matched rate (**EUR 188.16** on 163,459, **EUR 188.46** on 163,198). Caveat given at the time: re-running the engine yields **EUR 54,323,455** against the published **EUR 55,253,312**, so a rebuild re-bases the ceiling. **Approved, not run.**
- **D13** - a bare `.bak` ignore rule added to `.gitignore`, and the nine files under `JEROME_ONLY/` untracked with `git rm --cached`; all nine verified still on disk. Nothing committed, nothing pushed.
- **D15** - `class_factor.T` in `03_analytics/isze_pricing/config.yaml` changed from `0.80` to `0.60`, the 40% margin the price file charges; nothing else in that file touched. The live price list is still not touched.
- **D24** - the Portugal share accepted at 0.6364 on the 2,206 base; the ceiling rebuild is **not** authorised.
- **D25** - no pricing value, band, threshold, label or price file changes through the decision register. Pricing changes are Jerome's to start directly.
- **D26** - the retired Aftermarket BI Command Center stays retired; the tier-A ship-gate update is outstanding and was deliberately not made.

**Provenance for this whole entry:** it was truncated by an agent write probe on 2026-09-22 and
restored the same day. No verbatim copy survived, so sections 1-3 were rewritten from the version
read on disk before the truncation and the block above was reconstructed from the register. Nothing
decided on 2026-09-20 was changed by the restoration.

---

"""

ANCHOR = b"## 2026-09-19 "

raw = P.read_bytes()
orig_len = len(raw)

assert raw.startswith(b"# ISZE decision log"), "unexpected head - refusing to write"
idx = raw.find(ANCHOR)
assert idx > 0, "2026-09-19 anchor not found - refusing to write"

BAK.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(P, BAK)
print(f"backup -> {BAK.name} ({BAK.stat().st_size} bytes)")

parts = []
if b"price adjustment ambition is closed" not in raw:
    parts.append(ENTRY_2209.encode("utf-8"))
    print("will add: 2026-09-22 closure entry")
else:
    print("skip: 2026-09-22 closure entry already present")
if b"GPT review forcing decisions executed" not in raw:
    parts.append(ENTRY_2009.encode("utf-8"))
    print("will add: 2026-09-20 restored entry")
else:
    print("skip: 2026-09-20 entry already present")

if not parts:
    print("nothing to write")
    raise SystemExit(0)

payload = b"".join(parts)
new = raw[:idx] + payload + raw[idx:]

with open(P, "wb") as f:
    f.write(new)

after = P.read_bytes()
assert len(after) == orig_len + len(payload), f"length mismatch {len(after)}"
assert after == new, "content mismatch"
assert after.startswith(b"# ISZE decision log")
assert after[idx + len(payload):] == raw[idx:], "original bytes after anchor changed"
assert b"price adjustment ambition is closed" in after
assert b"GPT review forcing decisions executed" in after
assert b"## 2026-09-19 " in after

print(f"OK: {orig_len} -> {len(after)} bytes (+{len(payload)})")
print("--- new head ---")
print(after[:300].decode("utf-8", errors="replace"))
