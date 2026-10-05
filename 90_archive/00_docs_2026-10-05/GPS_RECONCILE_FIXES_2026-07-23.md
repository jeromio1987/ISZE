# GPS Reconcile — Remaining Fixes for Cursor

**Date:** 2026-07-23 · **Supersedes status section of** `00_docs\GPS_RECONCILE_MEMO_2026-07-16.md` (root-cause analysis there still stands — this doc is the current punch list).

## Live state as of today (`python 04_tools\gps_reconcile.py`, full run)

**5 of the original 8 hard failures are already resolved** — someone applied Fix 3 (echarts vendoring) and Fix 4 (ghost dashboard removal) after the 07-16 memo was written; `gps_snapshot.json` has also since been re-copied from `gps_v9_snapshot.json`. Do not re-do any of this:

| # (07-16 memo) | Check | Status today |
|---|---|---|
| 1 `snapshot_copy` | PASS — byte-identical | already fixed, don't touch |
| 2, 5 `dashboard_*:gps/...` | gone from harness | ghost file archived to `02_dashboards\_archive\gps_orphan_2026-07-16\`, removed from `DASHBOARDS` list | already fixed |
| 3, 4 `dashboard_selfcontained:fleet/...` | PASS — no CDN dependency | `build_gps_dashboards.py:19` already reads vendored `_ui\echarts.min.js` | already fixed |

**Ran `gps_reconcile.py --rebuild` today** to regenerate the two stale billing-FY CSVs from the already-verified-fresh raw recompute (`billing_json_vs_raw` etc. all PASS — the raw spine itself was never wrong, only these two derived exports hadn't been re-run since 07-03). This is a data regen, not a code change — see the pipeline re-run result appended at the bottom of this doc once it lands.

**What's actually still broken — 2 real code bugs, both below.** Everything else left failing traces back to these two.

---

## Fix 1 — `04_tools\build_gps_kosha_v4.py`, line 36 (blocks failure `kosha_chain`)

```python
# line 36 — current:
PLAN  = DATA / "ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx"  # uploaded plan

# fix — file lives in the 11_planning subfolder (confirmed present on disk today):
PLAN  = DATA / "11_planning" / "ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx"
```

`load_bp()` runs at **module import time** (line 54: `BP, BP_LABEL = load_bp()`), so this isn't just wrong when called — **importing this module at all currently raises `FileNotFoundError`.** That's the direct cause of harness failure `kosha_chain` (`_audit_gps_integrity.py` → "Toggle gross == rebuilt billing JSON": 11 mismatches) — the Toggle workbook (v4a/v4b output) can't be rebuilt from the now-refreshed raw billing because the builder can't run at all. One line unblocks it.

**After the path fix, regenerate the Kosha workbooks** (`GPS_MODE=net python build_gps_kosha_v4.py` then `GPS_MODE=gross python build_gps_kosha_v4.py`) and re-run the harness — `kosha_chain` should flip to PASS.

---

## Fix 2 — `04_tools\build_gps_v5.py`, line 56 (the €2.91M phantom BP)

```python
# line 56 — current:
BP   = {2027:35_284_400, 2028:37_530_000, 2029:42_560_000, 2030:48_270_000}
```

This is a **pre-revision** BP snapshot. Live `PL Plan row 186` (IX study, cols G–J) today:

| FY | Hardcoded (line 56) | Live PL Plan row 186 | Delta |
|----|---:|---:|---:|
| 2027 | 35,284,400 | 35,284,444 | −44 (rounding; also gets overwritten at runtime anyway, see below) |
| 2028 | 37,530,000 | 37,530,115 | −115 (rounding) |
| **2029** | **42,560,000** | **41,530,410** | **+1,029,590** |
| **2030** | **48,270,000** | **46,385,705** | **+1,884,295** |

**Combined FY29+FY30 phantom uplift the network is silently asked for: €2,913,885.** `ISZE_GPS_v5.xlsx` → `Kosha Gap` row 11 solves `Gap = 0` by construction (Option A back-solves uplift X to force revenue = BP), so this never shows up as a visible gap — it's baked straight into the demanded distributor uplift for FY29/FY30. FY2027 already gets overwritten correctly at runtime by `_load_reviewed_bp_fy27()` (line 1077-1079), which is why only FY29/FY30 are live money.

**One thing to check before patching:** `09_meetings\Preparation Meetings\UTI\_build\build_uti_gps_incentive_proposals.py:17` does `from build_gps_v5 import CLASS_RATE, read_uio_classes, read_warranty` — that importer has nothing to do with the BP/Kosha Gap logic, so **don't make the PL-Plan read a bare module-level side effect of importing `build_gps_v5`** or you give an unrelated UTI script a new hard dependency on the planning workbook's location/existence every time it runs. Load it lazily, inside `main()`, instead:

```python
# near the top, replacing line 56 entirely:
PLAN = BASE / "11_planning" / "ISZE PL Plan FY2026 2027 2028 20260205_2 -.xlsx"

def load_bp_row186() -> dict[int, float]:
    """Live BP (VP parts target), PL Plan 'IX study' row 186, cols G-J = FY2027-30.
    Mirrors build_gps_kosha_v4.py's load_bp() — not imported directly to avoid
    running that module's own top-level side effects (it does its own PLAN read
    at import time, plus loads the v3c/v4 source templates)."""
    wb = openpyxl.load_workbook(PLAN, data_only=True)
    ws = wb["IX study"]
    cols = {2027: 7, 2028: 8, 2029: 9, 2030: 10}
    bp = {yr: float(ws.cell(186, c).value) for yr, c in cols.items()}
    wb.close()
    return bp

CIS_P = {2027: 1700000, 2028: 1800000, 2029: 1900000, 2030: 2000000}  # unchanged, keep as-is
```

Then in `main()`, right before the `for yr in [2027,2028,2029,2030]:` loop (currently line 1064), add:

```python
global BP
BP = load_bp_row186()
```

(`BP` must exist as a module global for the rest of `main()`'s `BP[yr]` reads and the later `BP[2027] = reviewed_network` overwrite to keep working unchanged — no other line needs to change.)

**Verify:** re-run `build_gps_v5.py`, open `ISZE_GPS_v5.xlsx` → `Kosha Gap`, confirm FY29/FY30 `BP Target (€)` row now reads 41,530,410 / 46,385,705 (not 42,560,000 / 48,270,000) and the FY29/FY30 uplift X drops accordingly.

---

## Same defect, lower priority — optional, not required to clear the harness

Two sibling scripts carry the identical stale dict; neither feeds anything `gps_reconcile.py` checks, so they're not blocking today's backlog, but they'll produce the same wrong FY29/30 story if anyone runs them:

- `04_tools\build_gps_kosha_v3d.py:44` — same 42.56M/48.27M
- `04_tools\gps_full_run.py:54` — `BP = {2027:35.28e6, 2028:37.53e6, 2029:42.56e6, 2030:48.27e6}`

Same-class fix (swap for a `load_bp_row186()` call) if you're already in this area — Jerome's call whether it's worth the extra diff right now.

**Explicitly not authorised by this spec:** hoisting `load_bp_row186()` into a shared loader (e.g. `91_build\load_bp_fy27.py`-style) so v5/v3d/kosha_v4/gps_full_run all share one implementation. That's the right long-term shape but touches 4 files for a backlog that only needs 1 fixed today — a separate call if Jerome wants the consolidation.

---

## Verification checklist

1. Apply Fix 1, confirm `python build_gps_kosha_v4.py` (both `GPS_MODE=net` and `GPS_MODE=gross`) runs without `FileNotFoundError`.
2. Apply Fix 2, confirm `ISZE_GPS_v5.xlsx` FY29/30 BP cells match live PL Plan row 186 (41,530,410 / 46,385,705).
3. Re-run `python 04_tools\gps_reconcile.py` (full, no flags) — expect `kosha_chain` PASS, 0 hard failures.
4. Do **not** re-run with `--rebuild` again unless raw billing has changed since today — that step is already done as of this pass.
