# Handoff: air filter and the Focus cut (`Competitive parts > Filters`)

> **Correction added 2026-09-20 — read this box before the rest.**
>
> This body is a **17 September** note and its numbers are on that day's state. Three things have
> moved. The long section *"Which tree you are reading, because there are two"* **explains the air
> cleaners correctly and its central judgement still holds** — the pricing work did not need the
> misplacement corrected, and the two-tree reading of the 40 part numbers is still right. What is
> now stale:
>
> 1. **The master-side misfile was fixed in the wrong direction, then properly.** The
>    `Cleaning Chemicals` branch holds **0 part numbers** today. A 20 Sep pass
>    (`figkey_aim_fix_20260920`) moved the set to `Air conditioning > Other A/C` (124 PNs /
>    EUR 998,360) and `Air system > Other air system` (8 PNs / EUR 162,252) instead of to
>    Filters — **132 PNs / EUR 1,160,612** in total, against the "12 elements / EUR 124,952" the
>    state packet carried.
> 2. **The cause was a stale copy, not a misclassification.** `build_aim_master.py` copied
>    `pr00_classification.csv`'s tree into the master's `cat_l1/l2/l3` on **17 Sep 22:06** and was
>    never re-copied after `pr00` was corrected at 19:50 and again at 22:22. The master is
>    **98.34%** consistent with its own declared upstream; the older classification file is
>    **99.36%**.
> 3. **The numbers below are still correct for what they measure.** They are on the 12-month
>    pricing basis and on the catalogue tree, and that tree has the air filter in the right place.
>    Note the distinction the body already makes: **€1,203,146.04 on 256 PNs** is the whole leaf
>    on the 18-month audit window; **€796,783.16 on 40 PNs** is the element-only subset on the
>    12-month window. Both stand.
>
> **New dated file for any rebuild:** `01_data/00_derived/aim_pn_classification_20260920.csv`,
> built from the declared upstream — 164,907 rows, air filter at **254 PNs / EUR 1.2M**. Builder
> `01_data/91_build/build_aim_classification_20260920.py`, gate 17/18.
>
> **Before re-deriving anything below, say which tree and which window.** Only the master-side
> misfile description and the state packet's element count were wrong. Full evidence:
> `01_data/90_INBOX/AIM_V2_READINESS_2026-09-20.md`.



**Written 2026-09-17.** Internal working material. Blunt is fine. This file changes nothing; it points at what already exists on disk.

---

## Instructions

### 1. Use `01_data/00_derived/aim_catalog_focus_filters.csv` on the `catalog_full` basis. Do not use `pr00_catalog_only`.

Every table in that file is emitted twice, once per basis. Take `catalog_full` for any network or per-market answer.

The reason is mechanical, not stylistic. `aim_source` is a **precedence label for which vocabulary won `aim_l1`** in the source file. It is **not a completeness flag for `catalog_l1`**, `catalog_l2` or `catalog_l3`. The catalogue columns are populated on 164,610 rows of the classification file, not on the 139,410 that carry `aim_source == 'pr00_catalog'`, and they match the true PR00 source on 100% of joined rows on every `aim_source` value, including `aim_workbook`, `gap_suggestion` and `rule_patch_eq_20260917`.

What the literal restriction costs you, measured on this 12-month base:

| | `catalog_full` | `pr00_catalog_only` |
|---|---|---|
| In-scope billed euro | €34,993,609.39 (100%) | €4,527,386.17 (12.94%) |
| Filters total | €3,118,954.54 on 257 part numbers | €1,931.98 on 19 part numbers |
| Air filter | €796,783.16 on 40 part numbers | **no row at all** |

Concretely: `8982705240 ELEMENT; OIL FILTER` is a €256,036 line and carries `aim_source == 'aim_workbook'`. The literal restriction drops it out of the oil-filter answer. The whole `Air filter` leaf disappears. `catalog_full` is the basis that ties out exactly to the shipped pricing comparison, so the split is a partition of the shipped number rather than a second number.

### 2. Join the classification on part number, 10-character zero-padded strings on both sides.

File: `01_data/00_derived/aim_pn_classification_v2.csv` (governed columns `catalog_l1` / `catalog_l2` / `catalog_l3`). The older `aim_pn_classification.csv` carries the same tree plus the `aim_source` flag and is the one the Focus cut joins to. The classification file is clean on 10-character keys; three rows in the weight base carry a non-part key (two service-fee lines, one demurrage line) and are not parts.

The air-filter correction is **one token rule**: `ACL` in an Isuzu description means air cleaner, plus the literal string `ELEMENT; AIR CLEANER`. Nothing else was added, and no exclusion list was invented. The rule is expressed in the audit test as:

```
FILTER; ACL   ELEMENT; AIL / ACIL   ELEMENT; AIR CLEANER
FILTER; AIR CLEANER   AIR CLEANER ELEMENT   ELEMENT ASM; AIR
minus any description that is a housing or fastener rather than an element
(CASE / COVER / BRACKET / BOLT / SEAL / GASKET / CLAMP / DUCT / HOSE / BODY / IND)
```

### 3. Do not quote an air-filter figure dated before 2026-09-17, and do not repeat the "network number in name only" line.

Engine air filtration was misfiled under air conditioning and "other air system" until the 2026-09-17 refile. Any air-filter euro read from a pre-patch table is wrong.

Two claims that circulated before the patch are **side effects of the misfile, not facts about the business**. Delete them:

- that the `Air filter` leaf was "a network number in name only at €28,469";
- that certain markets showed "real zeros, not missing data".

Both came from reading a leaf that was holding 3.6% of its own category. After the refile the leaf holds the whole category on the 12-month base, and **every one of the 22 in-scope markets bills engine air filtration**. The smallest is Palestine at €574. There are no zeros.

---

## Verified figures

Window is attached to every number. The two windows are different and must not be blended: the pricing revision uses the 12 months 2025-07-01 to 2026-06-30; the classification audit used the 18 months 2025-01-01 to 2026-06-30 (gross billed).

**The `Filters > Air filter` leaf, `catalog_full`, 12 months to 2026-06-30:**

| Metric | Value |
|---|---|
| Billed euro | **€796,783.16** |
| Part numbers with billed euro | 40 |
| Units | 40,700 |
| Step euro | €16,436.60 |
| Weighted base-price increase | 2.1566% |
| Share of Filters (€3,118,954.54) | 25.5% |

**The engine-air-filtration category, wherever it sits in the tree.** On the 12-month base and after the patch, this is the **same €796,783.16 across the same 40 part numbers**. The misfile is gone and nothing that reads as an engine air-cleaner element is left outside the leaf. Traced on the billed description text rather than on the tree, the category and the leaf are the identical part-number set (40 = 40, no difference either way). Descriptions in the set:

| Billed description | Part numbers | 12M billed EUR |
|---|---|---|
| `FILTER; ACL` | 22 | €640,513.45 |
| `ELEMENT; AIR CLEANER` | 2 | €99,143.71 |
| `FILTER; ACL,INNER` | 4 | €31,232.92 |
| `FILTER; AIR CLEANER` | 9 | €25,723.73 |
| `FILTER; ACL,OUTER` | 2 | €85.23 |
| `ELEMENT ASM; AIR CLEANER` | 1 | €84.12 |
| **Total** | **40** | **€796,783.16** |

**Same category on the 18-month window of the audit, for reconciliation only:** €1,203,146.04 across 256 part numbers (gross billed, 2025-01-01 to 2026-06-30). Do not compare that to the €796,783.16 above as a growth rate; the windows differ.

**What the refile actually moved.** The pre-patch state, 12-month base, `catalog_full`:

| Pre-patch location | Part numbers | 12M billed EUR |
|---|---|---|
| `Comfort parts > Air conditioning > Other A/C` | 27 | €669,122.59 |
| `Competitive parts > Air system > Other air system` | 2 | €99,143.71 |
| `Competitive parts > Filters > Air filter` | 10 | €28,469.00 |
| **Total** | **39** | **€796,735.30** |

The refile moved **128 part numbers** on 2026-09-17. On the audit's 18-month window those carried €1,160,611.71; on the 12-month window the leaf itself went from €28,469.00 on 10 part numbers to €796,783.16 on 40. The same event, two windows, and the reason the two figures differ is the window rather than anything else.

**Engine air filtration by market, `catalog_full`, 12 months to 2026-06-30:**

| Market | Part numbers | Units | Billed EUR | EUR per truck in service |
|---|---|---|---|---|
| UTI | 7 | 8,623 | 159,027.98 | 15.4 |
| ITUK | 14 | 4,753 | 133,147.44 | 5.9 |
| IUK | 8 | 6,594 | 114,287.29 | 2.4 |
| BELGIUM | 21 | 2,514 | 47,382.44 | 4.9 |
| PORTUGAL | 20 | 1,956 | 40,481.54 | 5.0 |
| NORWAY | 4 | 1,952 | 37,448.82 | 4.7 |
| GERMANY | 13 | 1,822 | 37,322.74 | 2.9 |
| SWEDEN | 5 | 1,882 | 36,458.48 | 4.3 |
| IRELAND | 25 | 1,530 | 34,863.60 | 11.4 |
| GREECE | 14 | 1,636 | 26,125.35 | 7.0 |
| UMI | 5 | 1,914 | 21,844.04 | 1.2 |
| CYPRUS | 15 | 1,279 | 19,199.17 | 8.3 |
| HUNGARY | 7 | 930 | 18,663.52 | 5.0 |
| ARMENIA | 4 | 545 | 13,810.71 | no fleet count |
| UKRAINE | 3 | 784 | 13,506.98 | no fleet count |
| ROMANIA | 7 | 625 | 12,776.68 | 11.9 |
| KAZAKHSTAN | 6 | 336 | 7,950.06 | no fleet count |
| FINLAND | 7 | 368 | 7,673.10 | 6.4 |
| DENMARK | 5 | 274 | 7,377.48 | 8.7 |
| MALTA | 8 | 192 | 4,137.35 | 4.0 |
| ICELAND | 3 | 134 | 2,724.38 | 6.7 |
| PALESTINE | 3 | 57 | 574.01 | no fleet count |
| **Network** | **40** | **40,700** | **€796,783.16** | n/a |

Israel is two rows throughout, never blended: **1797 UMI** (LCV) and **1799 UTI** (CV) are different fleets with different parts mixes, and the customer name column cannot split them.

**Residual, checked so you do not have to.** 64 part numbers still sit under `Comfort parts > Air conditioning` with `ACL` or `AIR CLEANER` in their own description, worth €7,282 billed. They are not elements: 56 of them (€7,253) are brackets, covers, bolts, hoses, ducts and body assemblies, which are physically air-cleaner housings and mountings, not filter elements. The remaining 8 carry €28.83 of billed euro between them and are washers, rubbers and collars. The element count is complete at 40 part numbers. If a later pass wants housings in the family too, that is a different decision and it needs a different rule.

---

## Which tree you are reading, because there are two

The figures in this brief are on the **catalogue tree** (`catalog_l1` / `catalog_l2` / `catalog_l3`, the governed columns of `aim_pn_classification_v2.csv`). The pricing-revision pack Jerome received today is on the **AIM spine** (`aim_l1_fixed` / `aim_l2_fixed` / `aim_l3` in `aim_master_v2.csv`, carried into `pricing_aim_source_lines.parquet` and the workbook and pages built from it). Both trees are on disk, both are internally consistent, and the same part numbers land in different families on each. A reader comparing the two will see two different air-filter numbers for the same 40 part numbers.

**The same 40 air-filter part numbers, both trees, 12 months to 2026-06-30, in-scope:**

| Tree | Placement | Part numbers | Billed EUR | Step EUR |
|---|---|---|---|---|
| Catalogue | `Competitive parts > Filters > Air filter` | 40 | €796,783.16 | €16,436.60 |
| AIM spine | `Maintenance Service > Air Filter > Air Cleaner Filter` | 28 | €671,831.60 | €15,762.18 |
| AIM spine | `Fluids Chemicals > Cleaning Chemicals > Cleaner` | 12 | €124,951.56 | €674.42 |

Same 40 part numbers, same €796,783.16 in total on both trees. **The difference is family placement, not missing data.** Neither figure is wrong, and neither file needs correcting in this work.

**Which tree to use depends on the question.**

- For a **filter family or price-step question** (what the whole filter block bills, how hard each filter type moves, which markets over- or under-index), use the **catalogue tree**. It holds all four filter types in one family and the whole leaf present and complete.
- For **AIM-level analysis** and for anything that has to reconcile with today's pricing workbook, use the **AIM spine**. That is the spine the pack was built on, and a figure that has to tie to it must come from it.
- Do not put a catalogue-tree filter total beside an AIM-spine filter total in the same table without saying which is which. "Filters" means a different set of parts on each.

**A second AIM misfile, recorded not fixed.** Those 12 part numbers sitting under `Cleaning Chemicals > Cleaner` each carry a description that literally reads air cleaner. Air-cleaner elements filed as cleaning chemicals is the same class of error the ACL refile just fixed on the catalogue tree, and it is still live on the AIM spine:

| Part number | Description | 12M billed EUR |
|---|---|---|
| 5876100201 | `ELEMENT; AIR CLEANER` | €72,502.83 |
| 5876102500 | `ELEMENT; AIR CLEANER` | €26,640.88 |
| 8970622940 | `FILTER; AIR CLEANER` | €22,491.57 |
| 8971786092 | `FILTER; AIR CLEANER` | €1,386.99 |
| 5876102330 | `FILTER; AIR CLEANER` | €776.29 |
| 8941560520 | `FILTER; AIR CLEANER` | €505.72 |
| 8943820632 | `FILTER; AIR CLEANER` | €303.56 |
| 8971730260 | `FILTER; AIR CLEANER` | €135.22 |
| 8982290480 | `ELEMENT ASM; AIR CLEANER` | €84.12 |
| 5876101480 | `FILTER; AIR CLEANER` | €74.56 |
| 8970442262 | `FILTER; AIR CLEANER` | €40.46 |
| 8971732100 | `FILTER; AIR CLEANER` | €9.36 |
| **Total** | | **€124,951.56** |

Step euro on the same 12 part numbers is €674.42. Verified on `pricing_aim_source_lines.parquet` joined to `pr00_classification.csv` on the 40-part air-filter set: the AIM spine splits them 28 / 12 exactly as above, and the 12 match the list here part number for part number.

**Recorded, not fixed.** The AIM workbook and the AIM spine are PRISM-owned. Moving 12 part numbers inside a pricing revision would change the pack's own families underneath the reader, so it is deliberately left alone here. The catalogue tree is already correct on these parts, which means a filter question asked on the catalogue tree is unaffected by this. It should be raised as its own item against the AIM workbook.

---

## Background: what the Focus cut is and is not

**It is** a diagnosis of **product mix and of the price step by family**: which competitive families carry the euro, how many units move through each, and how hard the base price moves in each. It is a partition of the shipped pricing-revision number, so it adds up rather than competing with it. Under `catalog_full` it reads: Brake parts €3,551,589.15 (step €242,912.82, +7.79%), Filters €3,118,954.54 (step €101,719.62, +3.37%), Exhaust €2,481,740.57 (+7.07%), Steering €1,906,409.45 (+2.63%), and the smaller families below those. Inside Filters, the clearest single signal is that oil filters move roughly twice as hard as fuel filters (+5.05% against +2.26%) while billing about 72% of fuel-filter euro.

**It is not** a price proposal, an elasticity estimate, an allocation run, or a recommendation to change any list price. No revenue or margin outcome is modelled. The weighted increase is a move in the base price we compare against, nothing more. Anything that turns it into a proposal is a separate piece of work with a separate brief.

**Weight base.** `01_data/00_derived/price_bp_weighted_compare_pn.csv`: one row per customer × part number on the last 12 months of billed parts, in-scope customers only. The step euro ties out on that file with `in_scope == True`; the weighted increase ties out on the subset of those rows that carry a price on both sides:

| | Value |
|---|---|
| Window | 2025-07-01 to 2026-06-30 |
| Weighted increase | **5.9616%** |
| Step euro | **€1,652,140.71** |
| In-scope rows | 48,653 |
| In-scope billed euro | €34,993,609.39 |
| Rows matched to the classification | 48,574 (99.8376%), €797,239.74 unmatched (2.28% of euro) |

Method, so the numbers can be reproduced: `SUM(qty × bp_new_jpy) / SUM(qty × bp_prior_revised) − 1` over rows priced on both sides; step euro is the sum of `value_eur_step`. Per-distributor tie-out passes at a maximum increase delta of 0.0000 pp and a maximum euro delta of €0.00.

**Patch state: read this before trusting the leaf.** The `ACL` to air-cleaner correction **is applied**, not pending. `aim_pn_classification.csv` and `pr00_classification.csv` both carry the corrected nodes, `aim_pn_classification_v2.csv` was rebuilt after the patch, and the classification gate reports PASS 14/14. The pre-patch file is preserved as `aim_pn_classification.csv.bak_pre_eq_20260917` if you need to compare. The script that applied it is `01_data/90_INBOX/_patch_cls_eq_confirmed_20260917.py`, with its machine record in `_patch_cls_eq_confirmed_20260917_report.json` (128 air-filtration part numbers moved, zero residual wrongs on re-test).

One trap: `04_tools/autodoc_scraper/_HANDOFF_BUNDLE/scripts/fix_v3_aim_air_filters.py` is **not** this fix and has nothing to do with the catalogue tree. It edits a separate workbook's `AIM_Category` column (moving air-intake rows out of `Fluids Chemicals`) and it does not appear to have been run. Ignore it for this work.

**Where the mechanism is written down.** `01_data/00_derived/aim_catalog_breakdown_NOTES.md` §4 (why the `pr00_catalog_only` restriction does not mean what it looks like) and `00_docs/CLASSIFICATION_FULL_AUDIT_20260917.md` §3 (the air-filtration misfile in full). Note that the audit works the 18-month window and the catalogue note works the 12-month window; both say so, and the figures above keep them apart.

**Cells still open on this tree, so they do not surprise you.** `Other filter` (€668,819.46 on 48 part numbers) is a residual bucket, not one family: it mixes DEF and aftertreatment assemblies, hydraulic and transmission strainers, and one gasket, and a single part number (`8982878080 FILTER ASM`, €298,160) is 44.6% of it. Establish what that part is before it enters any commercial reading. Filters as a whole moves softly (+3.37%) relative to most competitive families, which is worth a second look rather than an explanation.
