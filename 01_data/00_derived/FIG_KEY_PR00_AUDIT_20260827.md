# Fig-key dimension vs current SAP IE40 PR00 — audit 2026-08-27

**Mode B · internal.** Read-only measurement, no rebuild performed.
**Reproduce:** `python 01_data/91_build/audit_fig_key_vs_pr00.py`
**Evidence:** `fig_key_pr00_audit.json` · `fig_key_pr00_disagreements.csv` (1,618 rows)
**Roadmap:** closes the sizing question on `00_docs/ISZE_ROADMAP.md` §1 item 8 (fig-key V2 remainder).

---

## Why this ran

The roadmap carried "bulk PN → fig key from SAP IE40 PR00 column" as an open item without a size, dating from the V2 spec. `pricing_pr00_ie40.parquet` does carry `fig_no` + `key_no` (99.7% of rows), so the question is answerable from files already on disk.

## Inputs

| File | Vintage |
|---|---|
| `parts_catalog_dimension.parquet` (164,969 PNs) | CSV last committed 2026-07-23, parquet 2026-08-11 |
| `pricing_pr00_ie40.parquet` (164,824 PNs with a figure) | `Price_file_PR00_IE40_20260810.xlsx` + `SAP_Pull_PN_Validity_List_PR00_return_20260812.xlsx` |

`fig_key` is the composite `<fig_no>-<key_no>` (e.g. `130-006`).

## Finding 1 — 1,841 blanks are fillable today

| | PNs |
|---|---:|
| Catalogue `fig_key` blank | 3,778 |
| **Fillable from the SAP figure on disk** | **1,841** |
| Not fillable (no SAP fig/key row for that PN) | 1,937 |

Coverage would move **97.71% → 98.83%** on a rebuild. No new data needed.

## Finding 2 — 1,618 PNs disagree with the current SAP figure

Where both sides carry a figure (160,560 PNs), they agree on **98.99%**.

| | PNs |
|---|---:|
| Disagree | 1,619 |
| Explained by supersession (catalogue used the `newest_pn` figure) | 1 |
| **Unexplained** | **1,618** |
| …of which the PN is *not* superseded | 1,609 |

By the catalogue's own `classification_source`: `pr00` 1,565 · `bvp_dimension` 33 · `pms_registry` 19 · `epc_n75_4hk1` 1.

**Read it as vintage, not corruption.** 1,565 of the 1,618 are rows the catalogue says it took *from* PR00, on parts that are not superseded — so the dimension was built against an IE40 pull older than the 2026-08-10 file now on disk, and SAP has revised those figures since. `gps_v2_fig_key.md` already states the contract: `build_pr00_classification.py  # needs IE40 PR00 xlsx when refreshed`. A new IE40 landed; the builder has not been re-run against it.

## Why it matters beyond the catalogue

`sales_fact.fig_key` is joined from this dimension (`fig_key_source = catalog`) because CY exports still lack the SAP `FIG KEY CLASSIFICATION` column — `gps_v2_fig_key.md` §71. So a stale dimension propagates into every fig-key rollup downstream. At ~1.0% of compared PNs the effect is small, but it is a silent wrong-figure, not a visible gap.

## What was deliberately not done

- **No rebuild.** That is `build_pr00_classification.py` → `build_fig_key_dimension.py` → `run_pipeline_and_verify.ps1`, on Jerome's workspace, and it changes derived numbers.
- **No CSV editing.** The disagreements file is evidence, not a patch.
- **No claim about €.** This audit touches the catalogue dimension only — no billing, no GPS, no capture rate was recomputed.

## Next step (one command, on the workspace)

```
python 03_analytics/Isuzu/prism/scripts/build_pr00_classification.py
python 03_analytics/Isuzu/prism/scripts/build_fig_key_dimension.py
powershell 03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1
```

Then re-run this audit: fillable should go to 0 and unexplained drift should collapse. Anything left after that is a genuine taxonomy question, not vintage.
