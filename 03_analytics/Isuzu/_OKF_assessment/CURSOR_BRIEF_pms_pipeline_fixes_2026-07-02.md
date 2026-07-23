# Cursor brief — PMS pipeline fixes (2026-07-02)

Context: Claude (Cowork) built a UTI vs. ITUK/Imotors/Ireland PMS comparison and found several issues while doing it. Some are already fixed in the deliverable by working around them from outside the pipeline; the ones below need to be fixed *in the pipeline itself* since they affect every downstream dashboard, not just this one workbook. Written for whoever (Cursor or a human) has real write access to `ISZE/03_analytics/Isuzu/prism/`.

---

## Task 1 — Verify these two files aren't actually corrupted (do this first, 2 min)

Claude's shell tool read these two files as truncated mid-statement; Claude's file-editor tool read them as complete. Almost certainly a sandbox-mount artifact on Claude's side, not a real problem — but verify before touching anything else, since if it's real it blocks everything downstream.

- `03_analytics/Isuzu/prism/scripts/build_bvp_p0_p1.py` — should end with:
  ```python
      return 0

  if __name__ == "__main__":
      raise SystemExit(main())
  ```
  Claude's shell tool saw it cut off after `if __name__ == ` (280 lines, missing the last 3).

- `03_analytics/Isuzu/prism/modules/pms_capture_config.py` — should end with:
  ```python
      raw = yaml.safe_load(_ASSUMPTIONS_PATH.read_text(encoding="utf-8")) or {}
      cons = {**_DEFAULT_CONSUMABLE, **(raw.get("consumable_factor") or {})}
      wear = {**_DEFAULT_WEAR, **(raw.get("wear_factor") or {})}
      return cons, wear
  ```
  Claude's shell tool saw it cut off mid-string at `encoding="u` (49 lines).

Run `python -m py_compile` on both, or just open them and confirm line counts (283 and ~55 lines respectively). If they're genuinely fine — expected — no action needed, just confirms this was a Claude-side tooling issue worth reporting as feedback, not a codebase issue.

---

## Task 2 — Re-run the PMS capture pipeline (stale since 2026-06-15)

`pms_capture_by_db_year.csv` and `pms_opportunity_matrix.csv` are dated 2026-06-15 07:02–07:18, but two of their real inputs have moved since:

- `01_data/00_derived/sales_fact.csv` — refreshed 2026-07-01 11:13 (new/corrected transactions not reflected in current PMS numbers)
- `03_analytics/Isuzu/prism/data/pms_capture_assumptions.yaml` — `air_filter` consumable_factor changed from `1.0` to `0.5` on 2026-07-02 (comment: "PROVISIONAL ... flag C"), also not reflected

Minimal command sequence (from `03_analytics/Isuzu/prism/`):

```
python scripts/build_bvp_p0_p1.py          # writes pms_capture_by_db_year.csv, bvp_pn_dimension.csv, genuine_bvp_crossref.csv
python scripts/build_pms_opportunity_matrix.py
python scripts/build_pms_db_summary.py
python scripts/verify_derived_pipeline.py  # confirm still 103/0 or investigate any new fails
```

If you want to be thorough and run the full documented chain instead of just these three, use `scripts/run_pipeline_and_verify.ps1` as-is — but note it also touches `FACTS.md`, the live dashboards, and other documents outside this scope, so a full run should be a deliberate call, not a side effect of this fix.

**Expected effect:** air-filter capture % roughly doubles and its TAM/gap roughly halves for every distributor (confirmed by hand for UTI/ITUK/Portugal/Ireland — e.g. ITUK air filter moves from ~49% to ~98% capture). Everything else should be close to unchanged unless the sales_fact.csv refresh added materially different CY2025 volume.

**Do NOT re-add the classification-leakage fix** (`pms_missing_pns_figkey.csv`, €978,233, 230 PNs) as if it's still open — it's already live via `03_analytics/Isuzu/prism/data/pms_capture_supplement.csv` (339 PNs = the 230 in-scope leakage PNs + 109 brake_rotor PNs, built 2026-06-15 06:46, consumed by `build_bvp_p0_p1.py`'s `main()`). Claude made exactly this mistake in an earlier draft and had to walk it back — the fix-list markdown docs (`PMS_classification_leakage.md`, `PMS_figkey_completeness.md`) are now historical/superseded, not open items. Worth adding a note to those two files pointing at the supplement so nobody re-opens this again.

---

## Task 3 — Fix `distributor_master_mapping.csv` (real data bug, not a Claude artifact)

File: `03_analytics/Isuzu/prism/data/distributor_master_mapping.csv`

Two rows near the bottom:
```
UTI,UNIVERSAL MOTORS ISRAEL LTD,Israel,MENA,Yes,No,ISRAEL,LCV only
UTI_CV,UNIVERSAL TRUCKS ISRAEL LTD,Israel,MENA,No,Yes,ISRAEL,CV only - separate legal entity
```
`UNIVERSAL MOTORS ISRAEL LTD` is UMI's legal entity, not UTI's — the two rows are swapped/mislabeled. `sap_sold_to_mapping.csv`, the UIO overview (`06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx`), and every PMS brief agree UTI = CV/trucks (sap code 1799), UMI = LCV/D-Max (sap code 1797). Fix: rename the `distributor_code` values so `UTI` row maps to Universal Trucks (segment_cv=Yes) and `UMI` (currently missing as its own row, or needs adding) maps to Universal Motors (segment_cv=No, LCV only).

Also check the `ITUK` / `IUK` rows in the same file:
```
IUK,I.M. PARTS & SERVICE Limited,United Kingdom,UK/IE,Yes,No,U KING,LCV only - separate from ITUK
ITUK,ISUZU TRUCK (UK) LIMITED,United Kingdom,UK/IE,Yes,No,U KING,UK LCV - main entity
```
Both show `segment_cv=No`, and ITUK's own note calls it "UK LCV" — contradicted by ITUK's own DVLA CV registration (22,389 units) and every PMS brief's "N75 CV" framing for ITUK. ITUK should be `segment_cv=Yes, segment_lcv=No`; IUK should stay `segment_cv=No, segment_lcv=Yes` (that one row is correct).

Anything downstream that filters "which distributors sell CV" using this file's `segment_cv` column instead of the UIO CV/LCV split will currently get UTI and ITUK backwards.

---

## Task 4 — Needs a business decision before implementing (don't just code this)

Five more BVP categories now have usable PN-level classification sitting unused in `01_data/00_derived/parts_catalog_dimension.csv` (`leaf_spring`, `shock_absorber`, `water_pump`, `fan_belt`, `bushing`), but none has a `consumable_factor` / `wear_factor` entry in `pms_capture_assumptions.yaml`, so they can't get a real capture % or TAM yet. If Jerome/IML supply a service-interval assumption for these, add them to `P1_CATEGORIES` (via the yaml, same pattern as `brake_rotor`) and re-run Task 2. Until then, leave them out of the official capture numbers — don't invent factors.

Separately, 9 BVP categories (generator, starter, engine foot rubber, center bearing, hub bearing, hub oil seal, king pin kit, wheel pin set, wiper blade) have **zero** PN classification anywhere in the data — this needs the Snap-on EPC bulk-file ask or manual click-through described in `03_analytics/Isuzu/pms-pilot/BVP_FINDING.md`. Not a code task.

---

## Task 5 — Check `build_isze_dashboard_json.py` / `isze_data.json` timestamp

`01_data/14_dashboards/isze_data.json` contains `"pms_refreshed": "2026-07-02T12:00:41Z"`, but the file's own mtime is 2026-06-29 and the PMS source CSVs it should reflect are from 2026-06-15. Either something regenerated just the timestamp field without regenerating the underlying PMS numbers, or the field is a static placeholder rather than a real "last built" stamp. Worth a quick look at how `build_isze_dashboard_json.py` sets that field — if it's supposed to be trustworthy, right now it isn't.
