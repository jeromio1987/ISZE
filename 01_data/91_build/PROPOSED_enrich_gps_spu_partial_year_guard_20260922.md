# Proposed guard — `enrich_gps_spu_v9.py` partial-year capture

**Status:** PROPOSED, NOT APPLIED. `03_analytics/Isuzu/prism/scripts/enrich_gps_spu_v9.py` was not edited.
**Written:** 2026-09-22
**Relates to:** `01_data/00_derived/_data_integrity_open_issues.md` § SPU-PARTIAL

## Why a file-level containment will not hold

`enrich_gps_spu_v9.py` is the writer. Every time it runs it recomputes
`gps_capture_vs_max = total_sales_eur / max_spend_eur` for every row that has a
target, and then sets `traffic_light_v9` from that number. It has no notion of
whether `total_sales_eur` covers twelve months. The 2026 rows carry eight months
of billing against a full-year target, so the next pipeline run puts the false
percentage and the red light straight back — which is exactly what happened on
2026-09-21, after the 2026-09-15 file-level containment had blanked them.

The guard therefore belongs in the writer, not in the file.

## What the guard has to do

1. Decide, per row, whether it is a part-period numerator over a full-period
   denominator. Take that from the row's own `period_basis` when the column is
   present — whoever wrote it knew the extract date — and fall back to the
   existing `modules.year_coverage.is_partial(year)` helper when it is not.
2. On those rows, leave `gps_capture_vs_max` and
   `gps_capture_ex_warranty_vs_max` **blank** and set `traffic_light_v9` and
   `traffic_light_v9_ex_warranty` to **`unknown`**.
3. Guard **every** place that writes those four columns, not just the first loop.
   The script recomputes them in three separate places (the main loop, the 2025
   UIO alignment loop, and a final pass over all rows for the ex-warranty
   figures). A guard in one place and not the others silently reinstates the
   defect.
4. Leave `max_spend_eur`, `total_sales_eur`, `uio_units` and `spend_per_unit_eur`
   alone. The target is a legitimately published full-year figure; the sales
   figure and the fleet are facts; the per-truck rate is correctly computed for
   the part year it covers.
5. Re-emit `period_basis` and `coverage_note` so the annotation cannot be lost
   again — the 2026-09-21 regeneration dropped both columns, and that is what let
   the false percentages sit next to a note telling the reader not to use them.
6. Refuse to write if any partial-year row still carries a capture percentage or
   a colour. A silent guard is a guard that gets removed by the next person.

## Unified diff

```diff
--- a/03_analytics/Isuzu/prism/scripts/enrich_gps_spu_v9.py
+++ b/03_analytics/Isuzu/prism/scripts/enrich_gps_spu_v9.py
@@ -19,6 +19,7 @@
 from config import DATA_BUILD_DIR, DERIVED_DIR, GPS_SPU_BY_DB_CSV  # noqa: E402
 from modules.bvp_analytics import UIO_OVERRIDES  # noqa: E402
+from modules.year_coverage import is_partial  # noqa: E402
 
 V9_JSON = DATA_BUILD_DIR / "uio_v19_gps.json"
 if not V9_JSON.is_file():
@@ -27,6 +28,60 @@ def _traffic_light_v9(capture: float) -> str:
     return "red"
 
 
+PARTIAL_BASIS = "partial_year"
+FULL_BASIS = "full_year"
+
+PARTIAL_COVERAGE_NOTE = (
+    "PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. "
+    "Do not compare against a full-year row, and do not read a capture % or traffic "
+    "light off this row: the max-spend target is a full-year figure."
+)
+
+
+def _is_partial_row(row) -> bool:
+    """Is this a part-period numerator sitting over a full-period denominator?
+
+    The row's own ``period_basis`` wins: it was written by whoever knew the
+    extract date. Only when the column is absent do we fall back to the
+    billing-date coverage of the year in ``sales_fact``.
+    """
+    basis = str(row.get("period_basis") or "").strip().lower()
+    if basis:
+        return basis == PARTIAL_BASIS
+    try:
+        return bool(is_partial(int(row["year"])))
+    except (TypeError, ValueError):
+        return False
+
+
+def _ensure_basis_columns(df: pd.DataFrame) -> pd.DataFrame:
+    """Keep ``period_basis`` / ``coverage_note`` present so the warning survives.
+
+    The 2026-09-21 regeneration dropped both columns. Nothing noticed for a day.
+    """
+    if "period_basis" not in df.columns:
+        df["period_basis"] = [
+            PARTIAL_BASIS if is_partial(int(y)) else FULL_BASIS for y in df["year"]
+        ]
+    if "coverage_note" not in df.columns:
+        df["coverage_note"] = ""
+    partial = df["period_basis"].astype(str).str.strip().str.lower().eq(PARTIAL_BASIS)
+    blank = df["coverage_note"].fillna("").astype(str).str.strip().eq("")
+    df.loc[partial & blank, "coverage_note"] = PARTIAL_COVERAGE_NOTE
+    return df
+
+
+def _assert_no_capture_on_partial_rows(df: pd.DataFrame) -> None:
+    """A row that says 'do not read a capture % off this row' must not carry one."""
+    if "period_basis" not in df.columns:
+        return
+    bad = df[df["period_basis"].astype(str).str.strip().str.lower().eq(PARTIAL_BASIS)]
+    if bad.empty:
+        return
+    for col in ("gps_capture_vs_max", "gps_capture_ex_warranty_vs_max"):
+        if col in bad.columns:
+            n = int(bad[col].notna().sum())
+            if n:
+                raise SystemExit(
+                    f"refusing to write: {n} partial-year rows carry {col}"
+                )
+    for col in ("traffic_light_v9", "traffic_light_v9_ex_warranty"):
+        if col in bad.columns:
+            coloured = ~bad[col].fillna("").astype(str).str.strip().isin(["", "unknown"])
+            n = int(coloured.sum())
+            if n:
+                raise SystemExit(
+                    f"refusing to write: {n} partial-year rows carry a {col} colour"
+                )
+
+
 def main() -> None:
     if not GPS_SPU_BY_DB_CSV.exists():
         print("SKIP: gps_spu_by_distributor.csv missing", flush=True)
@@ -48,6 +103,7 @@ def main() -> None:
 
     df = pd.read_csv(GPS_SPU_BY_DB_CSV)
+    df = _ensure_basis_columns(df)
     max_spend: list[float | None] = []
     capture_pct: list[float | None] = []
     lights: list[str] = []
@@ -56,17 +112,29 @@ def main() -> None:
     for _, row in df.iterrows():
         db = row["distributor_code"]
         year = int(row["year"])
+        partial = _is_partial_row(row)
         d = dists.get(db, {})
         ms = (d.get("max_spend") or {}).get(str(year))
-        if ms is None and year == 2025:
-            ms = (d.get("max_spend") or {}).get("2025")
         sales = float(row.get("total_sales_eur") or 0)
         max_spend.append(round(float(ms), 2) if ms else None)
-        cap = sales / float(ms) if ms and float(ms) > 0 else None
+        # A part-period numerator over a full-year denominator is not a capture %.
+        # ``max_spend_eur`` itself stays: the target is a real, published figure.
+        if partial:
+            cap = None
+        else:
+            cap = sales / float(ms) if ms and float(ms) > 0 else None
         capture_pct.append(round(cap, 4) if cap is not None else None)
-        lights.append(_traffic_light_v9(cap) if cap is not None else row.get("traffic_light", "unknown"))
+        if partial:
+            lights.append("unknown")
+        elif cap is not None:
+            lights.append(_traffic_light_v9(cap))
+        else:
+            lights.append(row.get("traffic_light", "unknown"))
 
     df["max_spend_eur"] = max_spend
     df["gps_capture_vs_max"] = capture_pct
@@ -100,16 +168,19 @@ def main() -> None:
         sales = float(df.at[idx, "total_sales_eur"] or 0)
         ms = df.at[idx, "max_spend_eur"]
-        if ms and float(ms) > 0:
+        if ms and float(ms) > 0 and not _is_partial_row(row):
             cap = sales / float(ms)
             df.at[idx, "gps_capture_vs_max"] = round(cap, 4)
             df.at[idx, "traffic_light_v9"] = _traffic_light_v9(cap)
         sales_ex = df.at[idx, "sales_ex_warranty_eur"]
-        if ms and pd.notna(sales_ex) and float(ms) > 0:
+        if ms and pd.notna(sales_ex) and float(ms) > 0 and not _is_partial_row(row):
             cap_ex = float(sales_ex) / float(ms)
             df.at[idx, "gps_capture_ex_warranty_vs_max"] = round(cap_ex, 4)
             df.at[idx, "traffic_light_v9_ex_warranty"] = _traffic_light_v9(cap_ex)
@@ -117,16 +188,20 @@ def main() -> None:
     for idx, row in df.iterrows():
         ms = row.get("max_spend_eur")
         sales_ex = row.get("sales_ex_warranty_eur")
-        if ms and pd.notna(sales_ex) and float(ms) > 0:
+        if ms and pd.notna(sales_ex) and float(ms) > 0 and not _is_partial_row(row):
             cap_ex = float(sales_ex) / float(ms)
             df.at[idx, "gps_capture_ex_warranty_vs_max"] = round(cap_ex, 4)
             df.at[idx, "traffic_light_v9_ex_warranty"] = _traffic_light_v9(cap_ex)
 
+    _assert_no_capture_on_partial_rows(df)
     df.to_csv(GPS_SPU_BY_DB_CSV, index=False)
     n_ms = df["max_spend_eur"].notna().sum()
-    print(f"enrich_gps_spu_v9: {len(df)} rows, max_spend on {n_ms} -> {GPS_SPU_BY_DB_CSV}", flush=True)
+    n_partial = int(
+        df["period_basis"].astype(str).str.strip().str.lower().eq(PARTIAL_BASIS).sum()
+    )
+    print(
+        f"enrich_gps_spu_v9: {len(df)} rows, max_spend on {n_ms}, "
+        f"{n_partial} partial-year rows held at unknown -> {GPS_SPU_BY_DB_CSV}",
+        flush=True,
+    )
```

## Before / after, in words

**Before** — the main loop computes a percentage for every row that has a target,
whether or not the sales column behind it covers the year:

```python
ms = (d.get("max_spend") or {}).get(str(year))
sales = float(row.get("total_sales_eur") or 0)
cap = sales / float(ms) if ms and float(ms) > 0 else None
capture_pct.append(round(cap, 4) if cap is not None else None)
lights.append(_traffic_light_v9(cap) if cap is not None else row.get("traffic_light", "unknown"))
```

**After** — the same rows keep their target but get no percentage and no colour:

```python
partial = _is_partial_row(row)
ms = (d.get("max_spend") or {}).get(str(year))
sales = float(row.get("total_sales_eur") or 0)
max_spend.append(round(float(ms), 2) if ms else None)
if partial:
    cap = None
else:
    cap = sales / float(ms) if ms and float(ms) > 0 else None
capture_pct.append(round(cap, 4) if cap is not None else None)
lights.append("unknown" if partial else (_traffic_light_v9(cap) if cap is not None else row.get("traffic_light", "unknown")))
```

The mechanism is one sentence: a row whose own `period_basis` says `partial_year`
is a part-year numerator over a full-year denominator, so the division is
refused and the reader is told so instead of being handed a colour.

## What the output would look like after the guard

- **2023 and 2024** — unchanged. No target on those rows, so no percentage either
  way; the green/amber colours there come from the sales-band column and are not
  affected.
- **2025** — unchanged. Twelve months of billing against a twelve-month target,
  so the 18 percentages (0.3535 to 0.9233) and their colours stand.
- **2026** — `max_spend_eur` still present on all 18 rows that have a target;
  `gps_capture_vs_max` and `gps_capture_ex_warranty_vs_max` blank;
  `traffic_light_v9` and `traffic_light_v9_ex_warranty` set to `unknown`;
  `spend_per_unit_eur` and `uio_units` untouched; `period_basis` and
  `coverage_note` re-emitted on every 2026 row. The 4 markets with no target
  (UKRAINE, ARMENIA, KAZAKHSTAN, PALESTINE) are already `unknown` and stay so.
- The script exits non-zero rather than writing if any partial-year row still
  carries a percentage or a colour.

## What would still be missing

- **The true 2026 capture cannot be computed from what is on disk.** The 2026 row
  covers billing to 31 August 2026 (`year_coverage_pct` = 0.6658 in
  `aim_gps_matrix.csv`), and the target is a full year. Nobody has a
  January–August target. The guard stops a false percentage; it does not produce
  a true one.
- **The stated 2026 period is still not reconciled.** `_data_integrity_open_issues.md`
  records Q1 EUR 9.99M and Q2 EUR 8.72M from `sales_fact` against a 2026 row sum of
  EUR 9.18M on the older basis. The guard does not resolve which window the row
  actually covers; it only refuses to divide it by a full-year target.
- **`spend_per_unit_eur` on 2026 is still a part-year rate.** Eight months of
  parts spend divided by a point-in-time fleet is arithmetically correct and
  plainly wrong to chart beside a full year. In tomorrow's pack it reads as a
  **−35.9% median collapse** (GREECE −50.0%, FINLAND −46.3%, UMI −45.9%),
  because `sales_fact` like-for-like January–August is **+6.5%** (EUR 24.50M
  against EUR 22.99M; parts-only +6.1%). The guard does not touch that column. It
  needs either an explicit annualisation flag or charts drawn on comparable
  months.
- **The readers are not fixed by this.** `build_network_percentile.py`,
  `build_aim_gps_matrix.py`, `build_isze_dashboard_json.py`, `build_bvp_p4_p5.py`
  and the three loose copies (`01_data/15_gpt_safe/`,
  `03_analytics/Isuzu/prism/evidence-app/data/derived/`, the 2026-09-23 meeting
  pack) each need a re-run and a refresh from source.

## Other places in this script with the same class of error

A part-period numerator over a full-period denominator, or a value used outside
the basis it was computed on:

1. **`gps_capture_ex_warranty_vs_max` / `traffic_light_v9_ex_warranty`.** The same
   eight-month numerator over the same full-year target, recomputed in a final
   pass over every row. Unguarded today; guarded in the diff above.
2. **`spend_per_unit_eur` on a part year.** Part-year spend over a full-fleet
   denominator. Correct arithmetic, incomparable basis, and the single largest
   visible error in tomorrow's pack. Not addressed by the guard — deliberately,
   because there is no obviously right replacement.
3. **The colour fallback.** `lights.append(... else row.get("traffic_light", "unknown"))`
   copies a **sales-band** colour into a **target-based** column whenever a
   market has no target. Two different meanings end up in one column, and a
   reader cannot tell which one they are looking at.
4. **A blank sale reads as zero.** `sales = float(row.get("total_sales_eur") or 0)`
   turns a missing euro into a 0% capture, i.e. reads as total failure rather
   than as unknown. For a market whose billing is genuinely absent, that is the
   worst possible default.
5. **A dead branch that looks deliberate.** `if ms is None and year == 2025:
   ms = (d.get("max_spend") or {}).get("2025")` looks up 2025 a second time and
   can never change the value. It reads as an intentional 2025 fallback and is
   not one.
6. **Only 2025 gets its fleet and per-truck rate reconciled** (the `df["year"] == 2025`
   loop). Every other year, including a part year, passes through with whatever
   fleet figure it arrived with.

## Verification of the guard, if it is applied

Run the script, then read back the file and confirm all four of these:

- every 2026 row has `period_basis = partial_year` and a non-empty `coverage_note`;
- `gps_capture_vs_max` is blank on all 18 target-bearing 2026 rows;
- `traffic_light_v9` is `unknown` on all 22 rows of 2026;
- the 2025 percentages and colours are byte-identical to the 2026-09-22 file.

Then re-run `build_network_percentile.py` and `build_aim_gps_matrix.py`, and
refresh the three copies from the corrected source.
