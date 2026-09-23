# Project 2 — Parts family / catalogue / Japanese codes (multi-hour brief)

Outward: **catalogue product tree** vs **parts family**. Never “AIM v2” to management.
Block-2 checklist is in `00_ASK.md`. CSV tables: `jp_codes`, `classification`, `benchmark_*`.

---

## Part I — Switch classification files now?

# GPT review brief — should we switch classification files now?

**Prepared:** 2026-09-20 · **Internal** · for GPT / peer challenge  
**Ask from Jerome:** Would you recommend switching now to the separated classification file? He does **not** want “V2” mentioned to management. Check hard — recent agent work has had errors.  
**This file is not a management pack.** Plain language for management is in §8.

---

## 0. Verdict (agent — challenge this)

**Do not switch management-facing or live pack consumers to the current separated classification file today.**

Reasons (measured on this machine 2026-09-20):

1. The separated file on disk is **stale** (mtime **2026-09-18**) while `aim_master_v2.csv` was patched through **2026-09-20** (EQ overnight, residual top-N, fig-key AIM fixes). Examples below show the master is right and the classification file is still wrong.
2. Live builders still read the **old fused** `aim_pn_classification.csv` and/or `aim_master_v2.csv` (pricing simulation, OS hub, billing windows, leakage, etc.). A silent “switch” without a consumer audit would split the house.
3. The structural idea (two trees, separate columns) is **genuinely better** than one mixed Level-1 column — but structure ≠ current content fitness.
4. Management should never hear “V2”. Say **catalogue product tree** vs **AIM parts family** (each still L1→L2→L3).

**Safer near-term:** quote AIM families from **`aim_master_v2.csv`** (where patches live). Keep catalogue residual / Other/review from the classification file only with the caveat that it is **not** rebuilt since 18 Sep.

---

## 1. What the two files are (no “V2” needed)

| File | Role | Last mtime on this PC |
|---|---|---|
| `01_data/00_derived/aim_pn_classification.csv` | Older file. Has both `aim_l1/l2/l3` and `catalog_l1/l2/l3`, but many packs still treat `aim_l1` as one mixed axis. | 2026-09-18 08:02 |
| `01_data/00_derived/aim_pn_classification_v2.csv` | Same catalogue tree in `catalog_*`, workbook/AIM vocabulary moved to `workbook_*`, plus flags (`catalog_residual`, `axis_conflict`, `desc_ambiguous`). | 2026-09-18 08:02 |
| `01_data/00_derived/aim_master_v2.csv` | Working AIM spine used for EQ apply / residual / fig-key fixes. | **2026-09-20 08:17** |

Still **three layers on each tree**. Nothing was collapsed to fewer levels.

| Tree | What it answers | Example |
|---|---|---|
| **Catalogue product tree** | Where the part sits in the Isuzu / PR00 catalogue | Competitive parts → Clutch parts → … · or Other / review → Miscellaneous → Review needed |
| **AIM parts family** | Aftersales / mix / capture language | Clutch → Clutch Kit → Clutch Kit · Maintenance Service → Air Filter → Air Cleaner Filter |

The 17 Sep audit found the old fused `aim_l1` mixed catalogue-style labels (“Repair parts”) with system families (“Engine”, “Brakes”) in one column — unsafe for management charts. Separating columns fixes that **wiring** problem. It does not by itself fix wrong leaves, EQ “no safe leaf”, or stale rebuilds.

Sources: `03_analytics/Isuzu/prism/docs/AIM_CLASSIFICATION_AUDIT_2026-09-17.md`, `AIM_BASIS_ANNEX_2026-09-17.md`, `DECISIONS.md` 2026-09-17 two-trees lock, `01_data/91_build/build_aim_classification_v2.py`.

---

## 2. Checks run for this brief (2026-09-20)

### 2.1 Safety gate on the separated classification file

Command: `python 01_data/91_build/verify_aim_classification.py`  
Result: **PASS 18/18** (gate JSON rewritten 2026-09-20 08:17 during fig-key AIM apply — gate reads the classification file, not the master patches).

Notable measured values from `aim_classification_gate.json`:

| Check | Measured | Floor/ceiling |
|---|---:|---|
| Rows | 164,667 | >100k |
| Duplicate keys | 0 | 0 |
| Catalogue L2 / L3 counts | 27 / 176 | approved baseline |
| PR00 copy integrity (catalogue cols) | 99.36% | ≥99% |
| Figure purity (majority L2 of own figure) | 71.9% | ≥65% |
| Residual share (catalogue Other/review) | **5.74%** | ≤8% |
| Euro coverage | 93.82% | ≥90% |

**Caveat:** gate PASS means the **classification file’s own contract** holds. It does **not** prove the file matches the latest `aim_master_v2` patches.

### 2.2 Stale content — master patched, classification not

Spot-check of PNs fixed on master 2026-09-20 vs classification file (still 18 Sep content):

| PN | Master AIM now | Classification `workbook_*` still says | Catalogue tree |
|---|---|---|---|
| `8982831940` pressure plate | Clutch / Clutch Kit / Clutch Kit | Chassis Frame / Mounting Hardware / Plate | Competitive → Clutch parts |
| `8975435900` clutch disc | Clutch / Clutch Kit / Clutch Kit | Brakes / Disc & Drum / Brake Disc | Competitive → Clutch parts |
| `5874123812` INTERFACE MX2-T | Tools Equipment / Workshop Tools / Tester | Unknown / Unknown / Unknown | **Other / review** |
| `5876100201` air cleaner | Maintenance Service / Air Filter / … | Competitive parts / Filters / Air filter (different vocabulary) | Competitive → Filters |

**Conclusion:** switching consumers to the separated file **today** would re-surface wrong AIM labels that were already fixed on the master.

### 2.3 Catalogue “Other / review” vs true AIM open

On live master after patches (definition: `cat_l1 == Other / review` AND AIM blank/Unknown/Other):

| Metric | Value |
|---|---:|
| True open PNs | **9,164** |
| True open L12M | **€114,516** |
| Of which L12M > 0 | 398 PNs (all the euro) |
| Zero L12M | 8,766 PNs |
| Already have figure key | 7,607 |
| No figure key | 1,557 |

Export: `01_data/90_INBOX/AIM_residual_Other_review_TRUE_OPEN_by_L12M_20260920.xlsx`

On the **stale** classification file, `catalog_residual=1` still shows **9,459** rows — the familiar ~5.74% residual. That residual % is a **catalogue-tree** label, not “AIM unknown”.

L12M join of classification file to sales (approx last 12 months from `sales_fact`): catalogue Other/review ~**€421k** on that join (method differs from master L12M column — do not mix with €114k true-open figure without reconciling bases).

### 2.4 EQ Hit creates its own large leftover (more important than catalogue Other)

Overnight EQ session 2026-09-19 (`_EQ_HIT_SESSION_20260919_RESULTS.csv`):

| Outcome | PNs | Queue euro |
|---|---:|---:|
| FOUND | **744 / 744** | — |
| Mapped → AIM patch | 384 | ~€172k |
| **FOUND but no safe AIM leaf (NEEDS_HUMAN)** | **360 (48%)** | **~€82k (32%)** |

So EQ is not “missing parts”. Almost half of hits land in a human/Other pile because the **AIM spine has no legal leaf** (engine mounting, transmission case/gear, radio, wiper, head cover, pedal, …). Scraping more catalogue-Other PNs does not clear that constraint.

### 2.5 Fig-key vs AIM family (Excel / master)

Verified on `AIM_Master_PN_Categories_Figkey_20260920.xlsx` / master:

- Figure key vs figure no + key no: **0 mismatches**
- Brake PMS figures → AIM Brakes: **0 conflicts**
- Oil/fuel/air filter figures under Maintenance Service: **intentional**, not errors
- Patched 2026-09-20 (high euro first): **126** PNs · **€789k** (clutch family + air cleaners)
- Skipped on purpose: cabin blower on fig `873-042` (AIM Cabin/HVAC already correct; urea map on that figure is blunt)

### 2.6 Who still reads the old fused file

Examples (not exhaustive):

- `02_dashboards/pricing/_build/build_pricing_simulation_spec_basis.py` → `aim_pn_classification.csv`
- `02_dashboards/Data/91_build/build_aim_billing_windows.py` → `aim_pn_classification.csv`
- `02_dashboards/_build/build_isze_os_hub.py` links the old path
- GPT pack builder already ships a copy named `09_aim_pn_classification_v2.csv` (content = separated file as of last pack build — may also be stale vs master)

**Unknown / not fully swept in this brief:** every HTML/deck that groups by `aim_l1` without naming which tree. Treat as open risk.

---

## 3. Is the separated file “genuinely better”?

| Claim | Assessment |
|---|---|
| Stops mixing “Repair parts” and “Engine” as peer Level-1s on one chart | **Yes** — that is the real upgrade |
| Still three layers each | **Yes** |
| Safety gate exists | **Yes** (18/18 on current file) |
| Commercial “score beside the catalogue” layer fully built | **No** — builder explicitly does not invent those scores yet |
| Content current with EQ / residual / fig-key AIM fixes | **No** — frozen at 18 Sep |
| Safe default for all live packs today | **No** |

So: **architecture yes, cutover no** (until rebuild + consumer migration).

---

## 4. Recommended path (if Jerome agrees)

1. **Now:** Do not tell management about a file version. Do not flip live pack inputs to the separated file as-is.
2. **When asked to rebuild:** refresh the classification file from PR00 catalogue + **current** `aim_master_v2` AIM families; re-run gate; re-export residual.
3. **Then:** migrate consumers one by one — catalogue charts use `catalog_*`; AIM family charts use workbook/AIM columns (or master). Never fuse them on one axis.
4. **In parallel (higher ROI than cutover):** add AIM leaves that unblock the EQ NEEDS_HUMAN pile (mounts, case covers, audio, etc.), then re-apply high-euro EQ leftovers.

---

## 5. What GPT should challenge / re-measure

Please mark each as CONFIRM / REJECT / UNKNOWN with evidence:

1. Is the 18 Sep vs 20 Sep mtime gap still true on the reviewer’s machine?
2. Do the four spot-check PNs still disagree between master and classification `workbook_*`?
3. Is 360/744 NEEDS_HUMAN still the right read of the EQ results file (not double-counting later residual applies)?
4. Which live packs would break or silently change if `aim_pn_classification.csv` were replaced by the separated file without code changes?
5. Is residual 5.74% still the right management residual to quote, or must it be recomputed after master sync?
6. Are there management decks already using language that implies one fused Level 1?

---

## 6. Absolute paths (this PC)

- Master (patched): `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv`
- Separated classification: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_pn_classification_v2.csv`
- Older fused classification: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_pn_classification.csv`
- Gate: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_classification_gate.json`
- True-open list: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\AIM_residual_Other_review_TRUE_OPEN_by_L12M_20260920.xlsx`
- EQ results: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_EQ_HIT_SESSION_20260919_RESULTS.csv`
- Fig-key fix note: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_AIM_figkey_aim_fix_20260920_NOTE.md`
- Audit: `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\docs\AIM_CLASSIFICATION_AUDIT_2026-09-17.md`

---

## 7. Honesty about agent error risk

Recent session mistakes / limits to weight when reviewing:

- Early “taxonomy conflicts” treated Maintenance Service filters as errors (they are intentional AIM service-basket placement).
- Catalogue Other/review euro (~€717k narrative vs later master cuts) mixed bases — always re-derive.
- Classification residual % quoted after AIM patches without rebuild → overstates “still open”.
- EQ NEEDS_HUMAN pile was under-emphasised relative to catalogue Other until Jerome pushed.

Treat §0–§2 numbers as **claims with paths**, not gospel, until GPT re-runs the spot checks.

---

## 8. How to talk to management (no version names)

Use:

- **Catalogue product tree** — Competitive / Repair / Accident / … / Other needing review  
- **AIM parts family** — Engine, Brakes, Clutch, Maintenance filters, …  

Avoid: V2, Axis A/B, Mode A/B, “we switched files”, agent stamps.

One honest sentence if needed:  
“We keep the catalogue tree and the aftersales parts family as two separate three-level trees so a chart never mixes ‘Repair parts’ with ‘Engine’ as if they were the same kind of label.”


---

## Part II — Settled position (ZKK / ZUK / HKK / EPLE)

# Settled position — the Japanese classification codes (ZKK / ZUK / HKK / EPLE)

**Date:** 2026-09-20 · **Internal / private** · read-only measurement, no rebuild, no mail
**What this is:** the one document to read instead of reconciling four others. Every number names the
file it came from. Where something was not measured, it says UNKNOWN.

**A word on one term.** The **price class** is the band that sets the margin we apply to a part,
assigned by Japan. It is a separate thing from the base price. Throughout this note "class" means
that band, and the reported values come from the Japanese `New Part Class` / `Current Part Class`
columns or from our spine's `price_class_iml`.

---

## Verdict in one paragraph

ZKK and ZUK are real, complete on the one file generation we hold, and worth carrying as catalogue
attributes — but they are catalogue and price labels, not part families, and nothing today changed
that. The design in the thesis (functional family from AIM, catalogue label from Japan, side by side,
never in one chart) holds and is now backed by re-measured numbers. Four claims made earlier today did
not reproduce and are corrected here; two held. The corrections all push one way: every claim that
ZKK does *more* than name a catalogue block and a price class has now failed a re-measurement. The two
things you should do next: approve the **column** request to Japan (ZKK, ZUK and EPLE on the file we
distribute), and do **not** chart on ZKK or ZUK and do **not** publish any figure from the benchmark's
purity column. Two things are genuinely unknown and worth one question to Japan: what ZUK means, and
who defines these codes.

**Added later on 2026-09-20 — the code-level verdict is in, and it closes the question.**
`01_data\90_INBOX\ZKK_CODE_DICTIONARY_2026-09-20.md` measured all 142 ZKK codes one by one, and the
answer is decisive: **ZKK is not a coherent axis and never can be.** Of the 51 ZKK codes large enough
to judge, **one** holds essentially a single kind of part and **46 are fragmented**, holding
**97.86%** of the €46.18M covered base. ZKK `275` alone is **46.77%** of that base across **415**
distinct part types. Widened to every billed ZKK code, 89 codes fall below 40% concentration and hold
**99.67%** of the money. HKK is a cleaner code than ZKK outside its one dominant value — **71.67%**
purity on the 23.2% of base euro that is not `1110` — but `1110` itself holds **83.7% of rows and
76.8% of the euro** with a top part type of 5.5%. And ZKK is **unrelated to HKK as either parent or
child**: 0 of 142 ZKK values equals any full HKK value, and only 5 of 142 match even a three-character
HKK prefix. Read with the corrections above, the position is unchanged in direction and much firmer in
evidence: carry ZKK as a catalogue attribute, never chart on it, and do not describe it as the HKK
prefix. The dictionary is now the authority for the code-level facts; the benchmark JSON is not (see
the reading order below).

---

## Every claim made today, and where it ended

| # | Claim | Originally said | Now correct | Status | Source |
|---|---|---|---|---|---|
| 1 | ZKK's code list equals the HKK prefix list | "The ZKK code *is* the HKK prefix" | **5 of 142** ZKK codes are also 3-character prefixes in the live HKK column (`110, 113, 213, 331, 332`); **7 of 142** are prefixes on the 2022 HKK workbook (`113, 114, 115, 211, 330, 331, 332`); **0 of 142** equal any full HKK value | **Corrected** | `REPRODUCIBILITY_AUDIT_JP_CODES_2026-09-20.md` claim 1; `HKK_SYSTEM_REVIEW_2026-09-20.md` §10.1 |
| 2 | ZKK `114` maps to class `XC` on every row | "dominant class `XC`, share 100%" | **112,095 / 144,830 = 77.40%** on `New Part Class`; **77.39%** on `Current Part Class`; **77.82%** excluding 789 blank class rows | **Corrected** | audit claim 2; `HKK_SYSTEM_REVIEW_2026-09-20.md` §10.3 |
| 3 | ZKK `070` is `XM` on 100% of rows | 100% | **68.9%** | **Corrected** | audit claim 2; `HKK_SYSTEM_REVIEW_2026-09-20.md` §10.3 |
| 4 | ZUK `11G00` is `XC` on 100% of rows | 100% | **78.4%** | **Corrected** | `GPT_REVIEW_ZKK_ZUK_and_AIM_v2_20260920.md` §2.3 |
| 5 | ZUK `13G00` is dominant `EV` at 95% | `EV`, 95% | dominant class is **`XM` at 80.6%** | **Corrected** | `HKK_SYSTEM_REVIEW_2026-09-20.md` §10.3 |
| 6 | ZUK `11F91` is dominant `RY` at 100% | `RY`, 100% | dominant class is **`XC` at 73.1%** | **Corrected** | `HKK_SYSTEM_REVIEW_2026-09-20.md` §10.3 |
| 7 | HKK `1110` row count | 491,294 (91.5%) | **458,368 (85.38%)** on `PRICE CD 250912` | **Corrected** | audit claim 3; `HKK_SYSTEM_REVIEW_2026-09-20.md` §9 |
| 8 | HKK `1114` row count | 21,834, "status 4 = surcharge" | **0 — the value does not occur.** The whole digit-4 group is **2,100** rows (`3114` 2,094, `1124` 4, `1914` 2) | **Corrected** | audit claim 3; `HKK_SYSTEM_REVIEW_2026-09-20.md` §9 |
| 9 | Where 491,294 and 21,834 came from | presented as measured | no file on this machine carries them | **UNKNOWN** | audit claim 3 |
| 10 | HKK is five characters: prefix + letter + trailing status digit | five characters | **four characters.** All **125** distinct HKK values are exactly 4 characters on all 536,854 rows | **Corrected** | audit claim 1/3; verified twice |
| 11 | The benchmark's `leading_noun_purity_pct` measures classification quality | published as a purity metric | it is the **blank-description share**: 82.59% for ZKK, ZUK and HKK alike, and the same on the benchmark's own base (115,228 / 139,524 = 82.59%) | **Settled — column not usable** | audit claim 4 |
| 12 | ZKK falls to 12.32% purity on the Japanese description | 12.32% | **confirmed** (ZUK 12.85%, HKK 16.28%) | **Settled** | audit claim 4 |
| 13 | ZKK has "only 1 of 142" description-pure codes; purity 17.5% | 1 of 142; 17.5% | **8 of 142** have a single leading noun; row-weighted purity **17.74%**. The "1" came from our own mostly-blank description field | **Corrected** | `HKK_SYSTEM_REVIEW_2026-09-20.md` §10.1; `GPT_REVIEW…` §2.1 |
| 14 | ZUK overlaps HKK heavily | argued from leading characters | **0 of 359** ZUK values equals any HKK value, and 0 equals any ZKK value. Shared leading two characters on **96.89%** of rows against **93.92%** expected by chance (both re-measured here on the price-file columns) | **Corrected** | audit claim 5 |
| 15 | AIM L1>L2 benchmark purity is 88.83% | 88.83% | **88.77%** | **Corrected** | audit claim 4; `GPT_REVIEW…` §2.5 |
| 16 | The 2022 HKK workbook lists 24 prefixes | 24 | **27** (`Parts` 13, `Accessories` 3, `Lubricant` 11) | **Corrected** | audit claim 1; re-measured |
| 17 | `PRICE CD 260910.xlsx` has 14 columns | 14 | **13**, and **no** HKK, ZKK, ZUK or EPLE column at all; 533,400 data rows on `Sheet1` | **Corrected** | audit claim 3 |
| 18 | ZKK `114` holds 1,901 distinct leading nouns | 1,901 | **confirmed** (top four `HARNESS` 15,895, `PIPE` 11,432, `CONTROL UNIT` 7,982, `BRACKET` 7,670) | **Settled** | audit claim 1 note; `HKK_SYSTEM_REVIEW…` §10.1 |
| 19 | ZKK = 142 codes of exactly 3 characters, 0 blank; ZUK = 359 codes of 5 characters, shape `DDCDD` | as stated | **code counts and blank counts confirmed** on all 536,854 rows (142 ZKK codes, 359 ZUK codes, 125 HKK codes, zero blanks in any of the three). The `DDCDD` shape and the `A`–`G` middle letter are **carried from the audit's own pass**, not re-measured again here | **Settled** | audit; code counts re-measured |
| 20 | ZKK carries 88.11% of our billed euro | 88.11% | **88.11%** — €46,183,083.72 of €52,414,407.82 | **Settled** | `aim_master_v2.csv`, re-measured at 09:24 |
| 21 | ZKK correlates with price class rather than determining it | "drives price class directly" | **correlates.** A table built from `New Part Class` directly is more accurate than one inferred from ZKK or ZUK | **Corrected / Settled** | audit claims 2–3 |
| 22 | The price-class concentration note is consistent with the spine | pending | **consistent** — class `C` **45.96%** of billed euro (€24,090,144), blank 8.21% (€4,301,869) | **Settled — re-measured here** | `aim_master_v2.csv` at 09:24, own measurement; note: `CLASS_PRICE_CLASS_CONCENTRATION_2026-09-20.md` |
| 23 | What ZUK categorises | "accessory / option categorisation" (a guess) | no dictionary held; structure proven, meaning not | **UNKNOWN** | `GPT_REVIEW…` §1.2, §3.6 |
| 24 | Who defines ZKK, ZUK, HKK and EPLE | not stated | Japan's file is all we hold — no code table, no documentation | **UNKNOWN** | `GPT_REVIEW…` §3.3 |
| 25 | Whether a published ZKK/ZUK description list exists | not found | nobody has found one | **UNKNOWN** | `GPT_REVIEW…` §3.4 |
| 26 | Whether the 12 single-class ZKK codes are single-class by design | claimed "100%" | all 12 cover **139 rows of 536,854**; the largest is `530` at 62 rows. At that size it may be chance | **UNKNOWN** | audit, "still UNKNOWN" |
| 27 | Whether a live pack breaks after the Japan columns were appended | not run | no pack has been run since the columns were loaded | **UNKNOWN** | `GPT_REVIEW…` §5.2, §8 |
| 28 | ZKK is a coherent part-family axis | implied by every proposal to chart on it | **No.** Of the **51** ZKK codes with ≥200 part numbers, **1** is coherent (`113`, 262 part numbers, 83.2% `FRAME ASM`, €5,416) and **46 are fragmented** (largest part type under 40%), holding **€45,197,049 = 97.86%** of the €46.18M base. Widened to all 132 billed codes: 15 reach 80%, 89 fall below 40% and those hold **99.67%** of the money | **Settled — ZKK cannot be an axis** | `ZKK_CODE_DICTIONARY_2026-09-20.md` §3; independently re-measured |
| 29 | ZKK `275` is a manageable bucket | "the biggest code" | **46.77%** of the €46.18M base — and **41.21%** of the whole €52.41M billed book — across **415** distinct leading part nouns. Its largest single part type is `HARNESS` at 13.7% | **Settled** | `ZKK_CODE_DICTIONARY_2026-09-20.md` §3, §4; independently re-measured |
| 30 | HKK is cleaner than ZKK as a system | "HKK wins on every cut" | **Confirmed, and it is not a small edge.** Outside its one dominant value, HKK scores **71.67%** purity on the 23.2% of base euro that is not `1110`, against ZKK's **12.10%** on the 53.2% that is not `275`. But `1110` itself holds **116,816 part numbers = 83.7% of base rows, €35,450,059 = 76.8% of base euro**, top part type 5.5%. So HKK is the cleaner code and says nothing about three quarters of the money | **Settled — both halves** | `ZKK_CODE_DICTIONARY_2026-09-20.md` §5; independently re-measured |
| 31 | ZKK is related to HKK as parent or child | the earlier claim that ZKK *is* the HKK prefix | **Unrelated.** 0 of 142 ZKK values equals any full HKK value; 5 of 142 equal a three-character HKK prefix (`110, 113, 213, 331, 332`); 20 of HKK's own 25 prefixes match no ZKK value at all. A parent would contain its children's codes; neither pattern holds | **Settled** | `ZKK_CODE_DICTIONARY_2026-09-20.md` §1; independently re-measured |
| 32 | How many HKK codes carry the part type the 2022 workbook names | "**28 of 39** carry the named part type — 72%" | denominator **39 of 39** reproduces; numerator does not. Between **12 and 16 of 39 (31% to 41%)** depending on the match rule | **DISPUTED — both numbers kept, 72% not to be quoted** | independent re-measurement, `01_data\91_build\zkk_independent_verify_20260920.py` |
| 33 | "ZKK `275` is 46.77% of the billed book" | as written in the dictionary's verdict | **Correct on its own definition and misleading in the short form.** 46.77% is of the €46.18M covered base. On the €52,414,407.82 billed book it is **41.21%**. Quote it with the base named | **Wording corrected** | independent re-measurement |
| 34 | "ZKK `275` touches 25 AIM families at ≥1%" | 25 | **25** on `aim_l1_fixed` falling back to `aim_l1`, which is the column the dictionary names; **24** on `aim_l1` alone, because `Lighting` falls from 69.1% to 0.0%. Two of the 25 hold under €5,000 of base euro | **Confirmed on the stated column; label the column** | independent re-measurement |

Nothing is marked **DISPUTED**: the three measurements that were asked for were re-run independently
and every audit number reproduced to the row. There is no open disagreement between documents.

**That sentence is now out of date, and is left standing so the change is visible.** The code-level
measurement that followed (`ZKK_CODE_DICTIONARY_2026-09-20.md`) reproduced everything in the audit, so
the audit itself remains clean. It added rows 28–34 above, of which **one is disputed**: the HKK
named-slot count (row 32, claimed 28 of 39, measured 12 to 16 of 39). Nothing else in the 34 rows is
in conflict. Rows 33 and 34 are wording corrections rather than disputed numbers, and row 28 settles
the axis question that every earlier document had left open.

---

## What the spine carries now

`01_data\00_derived\aim_master_v2.csv` — **32 columns, 165,213 rows**, 27.8 MB
(28,508,322 bytes), last written **2026-09-20 09:24:12** by the concurrent AIM leaf-unlock and EQ remap
work. The row count and column count are unchanged from before that rewrite, and the `jp_zkk` coverage
is unchanged.

The eight Japanese columns, appended in one load and not touched since:

| Column | What it holds |
|---|---|
| `jp_zkk` | Japan's catalogue category, three characters; 142 codes in the source file, 132 seen in our book |
| `jp_zuk` | Japan's second code, five characters in a fixed pattern; 359 codes; **meaning UNKNOWN** |
| `jp_hkk` | Japan's route and commercial-code field; four characters |
| `jp_eple` | Japan's engineering grouping, four digits; `9999` is the blank/general value |
| `jp_fig_key` | the figure key exactly as Japan sends it |
| `jp_class_new` | the two-letter price class as Japan assigns it |
| `jp_class_current` | the same, on the current price list |
| `jp_code_source` | `jp_price_cd_250912`, or blank — provenance on every row |

**Blank rows: 25,689 of 165,213.** Those part numbers are not in the file Japan sends us at all, so no
Japanese field can be filled from it. They carry **€6,231,324 = 11.89%** of twelve-month billed euro.
Read plainly: **88.11% of billed euro is labelled, 11.89% cannot be labelled from this source.** It is
a data request to Japan — those parts need to appear in the price file — not a classification gap on
our side.

---

## Safe to act on

- **Ask Japan for the columns.** ZKK, ZUK and EPLE already sit on every row of the file they send us
  and are simply missing from the file we distribute. This is a column request, not a
  re-categorisation project. It closes the February 2023 customer ask with data that already exists.
- **Carry ZKK, ZUK, HKK and EPLE beside the family tree as attributes.** They are complete on the one
  generation we hold and cost nothing to maintain.
- **Use ZKK as a completeness check** against our own family tree — a part with a ZKK code and no
  family is a countable gap.
- **Use the class concentration as context.** Class `C` holds 45.96% of billed euro; that is a
  measured fact on the 09:24 spine.
- **Tell the customer what exists and what is missing**, without a date, and without offering HKK as a
  category system. 54% of its description slots are empty and several families the business sells have
  no home in it.

## Not yet safe

- **Do not chart on ZKK or ZUK.** They are catalogue and price labels. A chart by them will not answer
  "how is our filter and brake business doing" and a distributor will not recognise the codes. This is
  no longer a judgement call: **1 of 51 judgeable ZKK codes is coherent, and the 46 fragmented ones
  hold 97.86% of the covered base** (`ZKK_CODE_DICTIONARY_2026-09-20.md` §3). A ZKK chart is a chart of
  `275`, and `275` is 415 different part types under one label.
- **Do not publish any figure from the benchmark's `leading_noun_purity_pct` column.** It measures
  missing descriptions, and it prints the same 82.59% for three systems that classify completely
  differently.
- **Do not say ZKK "is" the HKK prefix**, and do not say ZKK determines the price class. It shares 5
  of 142 values with the live HKK column and reaches 77.4% on its largest code.
- **Do not describe ZKK and HKK as a pair, a hierarchy, or two levels of one thing.** They are
  unrelated code lists that occupy overlapping numeric ranges: 0 of 142 ZKK values equals any full HKK
  value, and 20 of HKK's own 25 prefixes match no ZKK code. Carry both as separate attributes or
  neither, but never as parent and child (`ZKK_CODE_DICTIONARY_2026-09-20.md` §1).
- **Do not quote the "28 of 39 / 72%" HKK named-slot figure.** The denominator holds and the numerator
  does not reproduce; the measured range is 31% to 41% (row 32 above). The named examples are sound and
  may be used one by one.
- **Do not write "ZKK `275` is 46.77% of the billed book" without saying which base.** It is 46.77% of
  the €46.18M covered base and 41.21% of the €52.41M billed book.
- **Do not repeat the HKK row counts** 491,294 and 21,834 anywhere. They reproduce on no file we hold.
- **Do not claim to know what ZUK means**, and do not present the four Japanese codes as documented by
  Japan. They are not.
- **Do not change how the spine is read** until at least one live pack has been run. No pack has been
  tested since the columns were appended.

---

## Remaining open questions

**Ours to answer.**

1. **Which taxonomy is the outward one** — the 15-level functional tree or the family tree. They
   overlap and neither is a superset. (Jerome)
2. **Is ZKK the middle layer under the family tree, or does it go out on its own?** The data supports
   the middle-layer shape. (Jerome)
3. **Load the April 2026 workbook's part-by-part functional mapping onto the full book?** It covers
   15,353 part numbers worth €46,578,498 = 88.87% of billed book, and it was never loaded. This is a
   load job, and it changes the spine, so it needs an explicit go-ahead. (Jerome, then a build)
4. **Which country list goes out**, and does the customer get HKK at all as a middle layer. (Jerome)
5. **A fair score for our own family tree on the whole book**, including the 25,689 rows the Japanese
   file cannot label. Today every comparison sits on the 88.11% slice, which flatters it. (us)

**Japan's to answer. No amount of work on our side resolves these.**

6. **What does ZUK mean?** 359 complete, well-formed codes with no dictionary. One question closes it.
7. **Who defines ZKK, ZUK, HKK and EPLE** — Japan, or ISZJ, or we do. And is there a code table.
8. **Why does the 2026 price file carry none of these columns?** Deliberate narrowing or a lost export.
9. **Why did prefix `114` disappear from the live HKK column** while the 2022 workbook still lists it.
10. **Will the codes be stable across file generations?** We hold one generation. That is a single
    observation, not a guarantee, and it is the one thing that would weaken the case for carrying them.

---

## Reading order

Read in this order. Anything not listed is not part of this question.

| Order | Document | Status |
|---|---|---|
| 1 | `01_data\90_INBOX\SETTLED_POSITION_JP_CODES_2026-09-20.md` | **This file. Current. Start here.** |
| 2 | `01_data\90_INBOX\ZKK_CODE_DICTIONARY_2026-09-20.md` | **Current. The authority for ZKK/HKK code-level facts.** The code-by-code table, the coherence counts, the AIM cross-view, and the ZKK-versus-HKK structure. Where it disagrees with the benchmark JSON, **this document wins**; the benchmark is not the reference for any code-level number |
| 3 | `01_data\90_INBOX\REPRODUCIBILITY_AUDIT_JP_CODES_2026-09-20.md` | **Current.** The independent measurement. Authoritative for every corrected number |
| 4 | `01_data\90_INBOX\THESIS_AIM_and_ZKK_coexist_2026-09-20.md` | **Current.** The design argument. Its four PROVISIONAL items are settled and marked so, and its Part 3 granularity section is re-pointed at the dictionary's recomputed purity |
| 5 | `01_data\90_INBOX\CLASS_PRICE_CLASS_CONCENTRATION_2026-09-20.md` | **Current.** The price-class concentration. Consistent with the spine |
| 6 | `01_data\90_INBOX\HKK_SYSTEM_REVIEW_2026-09-20.md` | **Current, corrected.** Read its corrections notice first. Its §9 table and §10.3 class table carried superseded numbers and now show both the old and the corrected value |
| 7 | `01_data\90_INBOX\GPT_REVIEW_ZKK_ZUK_and_AIM_v2_20260920.md` | **Current, corrected.** Written for outside review. Its corrections are marked in place so the challenge list and the body agree |
| 8 | `01_data\90_INBOX\CLASSIFICATION_BENCHMARK_2026-09-20.md` | **Superseded for numbers.** Read the JSON or CSV instead. The prose argues from un-repaired figures, and the `leading_noun_purity_pct` column in both is not usable. **For any code-level figure, neither the prose nor the JSON is the reference — use the dictionary (order 2)** |
| 9 | `01_data\00_derived\aim_master_v2.csv` | The spine. 32 columns, 165,213 rows, written 09:24 today. Re-verified 2026-09-20: 165,213 distinct part numbers, no repeat rows, book total €52,414,407.82 |
| 10 | `01_data\【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912` | The source. 536,854 rows, the only file carrying ZKK, ZUK, HKK and EPLE |
| 11 | `01_data\90_INBOX\_hkk_zkk_transcript_extract_20260920.md` | Historical, July 2026. Left for context on the ZUK error only — its verdict on ZUK is wrong |

**Scripts behind the code-level facts.** The dictionary's own seven scripts are listed in that file.
The independent re-measurement written later is
`01_data\91_build\zkk_independent_verify_20260920.py` — it reproduces the base, the join, the
coherence counts, the `275` figures and the HKK comparison, and it is the source of the one disputed
number (row 32).

**No email was sent or drafted, no dashboard or workbook was rebuilt, and no data file was modified in
producing this note. The files written for it were this one and the two corrected documents named in
it, plus the status updates in `THESIS_AIM_and_ZKK_coexist_2026-09-20.md`.**

**Later the same day, this file was updated again as the single entry point.** Added: the code-level
verdict from `ZKK_CODE_DICTIONARY_2026-09-20.md`, claims rows **28–34**, the dictionary's precedence in
the reading order, and the wording corrections found by an independent re-measurement. The earlier
wrong claims were left standing and marked, not deleted. No data file was touched.

### Other files that moved today, and were not changed by this work

Reported, not touched, because they changed while this settlement was being written:

- `01_data\00_derived\aim_master_v2.csv` — rewritten 09:24:12 by the AIM leaf-unlock work (27.8 MB).
- `01_data\90_INBOX\_classification_benchmark_20260920.json` and
  `_classification_benchmark_tables_20260920.csv` — rewritten 09:26:44. The purity values in them are
  unchanged by that rewrite, so the finding stands.
- `01_data\90_INBOX\ISZE_Pricing_Policy_Management_v1.4.pptx` — written 09:18:21. **Not opened and not
  looked at** by this work.


---

## Part III — Full ZKK/ZUK measurement brief

# GPT review brief — ZKK / ZUK and how they sit next to AIM v2

**Prepared:** 2026-09-20 · **Internal / private** · read-only work
**For:** GPT / peer challenge. This is not a management pack and not a distributor pack.

**Ask from Jerome:** what do we actually know about ZKK and ZUK, and how can they live next to AIM v2
without breaking the aftersales view? Recent agent work has had errors — check the numbers hard.

**Language note before anything else:** `AIM v2` is an internal working name. It must not appear in
material that goes to management or to a distributor. Outward, say **"our parts family tree"** and
**"the catalogue category"**. Inside this file the working name is used freely.

> **Corrections applied 2026-09-20, after this brief was written.** An independent full pass
> (`01_data\90_INBOX\REPRODUCIBILITY_AUDIT_JP_CODES_2026-09-20.md`) re-measured the claims below and
> confirmed them, with three corrections to this brief itself: the 2022 HKK workbook carries **27**
> three-digit prefixes, not 24 (§1.1, §2.6, §6 item 2); the current master price file has **13**
> columns, not 14 (§3.5); and **AIM L1>L2's benchmark purity is 88.77%**, not 88.83% (§2.5). The
> "fifth character" framing in §2.2 and §6 item 8 is withdrawn — HKK values are four characters. The
> original wording is kept beside each correction. Settled position:
> `01_data\90_INBOX\SETTLED_POSITION_JP_CODES_2026-09-20.md`.

---

## 0. Verdict (agent — challenge this)

1. **ZKK is real, complete and free, and it is a catalogue and price-class bucket — not a functional
   family.** It is filled on 100% of the 536,854 rows of the September 2025 Japanese price file,
   with 142 distinct codes of exactly three characters. It is not a description of what the part is
   for. That is the whole finding, and both halves of it matter.

2. **ZUK is a separate, real axis and it is not lossy.** 100% filled, always exactly five characters,
   always the shape digits-digits-letter-digits-digits, 359 stable values. A July 2026 agent session
   dismissed ZUK together with `Example Model`. That verdict is correct for `Example Model` only, and
   wrong for ZUK. §4 states the error plainly.
   *(Added 2026-09-20: measured at code level, **0 of 359** ZUK values equals any HKK value and 0
   equals any ZKK value. Its separation from the other two codes is now proven, not inferred from
   leading characters. See §1.2 and §2.6 item 3.)*

3. **Do not replace AIM v2 with ZKK, and do not fuse them into one column.** ZKK and ZUK answer a
   catalogue and price-class question; AIM answers what the part is for. Neither is a superset of the
   other. Fusing two different kinds of label onto one axis is the defect the 17 September audit
   already found once.

4. **I could not reproduce several facts that this brief was asked to state, and I am reporting the
   measured values instead.** Specifically: ZKK's code list does **not** equal the HKK prefix list —
   **5 of 142** ZKK codes are also three-character prefixes in the live HKK column (`110`, `113`,
   `213`, `331`, `332`), and **0 of 142** equal any full HKK value; ZKK and ZUK do **not** determine
   the price class, they only correlate with it (the dominant class of ZKK `114` is `XC` at 77.4%,
   not 100%); the HKK row counts in the earlier ZKK note do not reproduce on the same file; the
   benchmark's description-purity column is measuring blank descriptions rather than classification
   quality; and the HKK glossary's description does not hold for every prefix. Details in §2.5–§2.7
   and §3.2.
   **This is the most important thing for GPT to re-measure.**
   **Checked and settled 2026-09-20** by an independent full pass
   (`01_data\90_INBOX\REPRODUCIBILITY_AUDIT_JP_CODES_2026-09-20.md`); every corrected figure above was
   confirmed by a second measurement. See §8 for what that audit did and did not settle.

5. **The design that does hold is a two-axis spine, not a replacement.** AIM v2 stays the functional
   family. ZKK and ZUK are carried beside it as catalogue and price-class labels. Each chart states on
   its face which axis it is on. §5 gives the concrete design and names what is still missing — 9,164
   parts with no AIM family, and a part-by-part functional map for 15,353 part numbers that exists in
   an April 2026 workbook and was never loaded onto the spine.

---

## 1. What ZKK is, and what ZUK is

Source for every number in this section, unless stated:
`01_data\【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912`, from ISZJ, September 2025 —
536,854 rows, columns `Pno, Parts name, New B/P, New Part Class, Current B/P, Current Part Class,
EPLE, FIGKEY, Example Model, ZUK, HKK, ZKK`. It is the only sheet in the workbook.

The extracted per-part map sits in
`01_data\00_derived\jp_codes_cache_20260920.csv` — 536,854 rows, one row per part number, columns
`pn, jp_description, jp_fig_key, eple, example_model, zuk, hkk, zkk, class_new, class_current`.
Its coverage against our billed book is measured in
`01_data\90_INBOX\_jp_codes_match_report_20260920.json`.

### 1.1 ZKK

| Fact | Measured value | Source |
|---|---|---|
| Characters | exactly 3, all rows | `_zkk_code_counts_20260920.json` (142 rows), re-measured on the workbook |
| Distinct codes | **142** | same |
| Blank rows | **0** of 536,854 | re-measured on the workbook |
| Biggest code by row count | `114` — 144,830 rows (27.0% of the file) | `_zkk_code_counts_20260920.json` |
| Biggest code by ISZE euro | `275` — EUR 21,597,704 of the covered base (46.77%) | `_classification_benchmark_20260920.json` |
| Codes holding at least 1% of the covered euro | 12 | same |
| Top ten codes' share of the covered euro | 92.03% | same |

Its shape includes numbers we already recognise — but see §2.6, this is not the HKK prefix list.
Against the 27 prefix values listed on the three sheets of the 2022 HKK workbook, ZKK shares
**seven**: `113`, `114`, `115`, `211`, `330`, `331`, `332`. Against the 25 three-character prefixes
that actually appear in the live HKK column, ZKK shares **five**: `110`, `113`, `213`, `331`, `332`.
**Zero** ZKK values equal any full HKK value. The two prefix lists do not agree with each other, so a
claim that ZKK "is" the HKK prefix cannot be rescued by picking either one.
The rest of ZKK runs in numeric blocks (`200`–`299`, `530`–`560`, `600`–`700`, `800`, `900`) that
appear nowhere in the HKK prefixes.

### 1.2 ZUK

| Fact | Measured value | Source |
|---|---|---|
| Characters | exactly 5, all rows | re-measured on the workbook |
| Shape | digits, digits, letter, digits, digits — held on **536,854 of 536,854 rows** | same |
| Distinct codes | **359** | same |
| Blank rows | **0** | same |
| Leading two characters | `11` on 520,189 rows, `13` on 15,445; the remaining 8 leading pairs are tiny | same |
| Letter seen in position 3 | only `A B C D E F G` — seven values, all rows | same |
| Biggest code by row count | `11G00` — 265,999 rows (49.5%) | same |

ZUK's leading numbers `11` and `13` are not HKK or ZKK values, so it is a separate axis. Measured at
code level, **0 of 359** ZUK values equals any HKK value and **0 of 359** equals any ZKK value; the
two columns `ZUK` and `HKK` share their leading two characters on 96.89% of rows against 93.92%
expected by chance, which is a shared dominant code family rather than shared meaning (settled
2026-09-20). Nothing in the files we hold states what ZUK is *for*. The earlier note guessed
"accessory / option categorisation". **What ZUK actually classifies is UNKNOWN.** It is a defined code
with no dictionary.

### 1.3 EPLE, for completeness

`EPLE` is four digits, **662** distinct values, every row filled. `9999` is the blank/general value at
**228,463 rows = 42.56%** of the file. On our billed book a non-`9999` EPLE is present on 44.98% of
parts but only **5.60% of euro** (EUR 2,936,069 of EUR 52,414,408). It cannot carry a spine column as
things stand. Source: `_jp_codes_match_report_20260920.json`.

### 1.4 Coverage of our own billed book

Joining the Japanese map to the spine `01_data\00_derived\aim_master_v2.csv` on `Pno`:

| Field | Codes seen | Parts hit | Euro hit | % of euro | % of parts |
|---|---:|---:|---:|---:|---:|
| `zkk` | 132 | 139,524 | EUR 46,183,084 | **88.11%** | 84.45% |
| `zuk` | 284 | 139,524 | EUR 46,183,084 | 88.11% | 84.45% |
| `hkk` | 72 | 139,524 | EUR 46,183,084 | 88.11% | 84.45% |
| `jp_fig_key` | 12,830 | 139,207 | EUR 46,110,512 | 87.97% | 84.26% |
| `class_new` | 26 | 139,334 | EUR 46,127,261 | 88.00% | 84.34% |
| `eple` | 658 | 74,315 | EUR 2,936,069 | 5.60% | 44.98% |

Spine totals: 165,213 rows, EUR 52,414,408 last twelve months billed.
Note the difference between the two columns of "codes": 142 ZKK codes exist in the file, but only
**132** of them appear on our billed book. The other ten never sell here.

*(Re-pointed 2026-09-20 at the 09:24 spine: 32 columns, 165,213 rows, 27.8 MB. The `jp_zkk` coverage
re-measures at **88.1114%** of billed euro — €46,183,083.72 of €52,414,407.82 — and **25,689** rows
are blank, carrying €6,231,324. Essentially unchanged. The "codes seen" figures above sit on the
pre-09:24 spine and are not re-measured here.)*

---

## 2. Checks run for this brief

I read the files, then re-ran the load myself rather than trusting them. Section 2.6 lists where my
measurement and the existing files disagree.

### 2.1 The ZKK codes do not describe parts — measured

Grouping all 536,854 rows by the leading noun of the Japanese part description (`jp_description` in
the cache, cut at the first `;`, `,` or `(`):

- Row-weighted "purity" — how often the most common noun in a code's rows accounts for all of them —
  is **17.74%** over 142 codes.
- Only **8 of 142** codes are description-pure at all. The earlier note said one. The difference is
  which description is used: on the Japanese description field it is eight. On our own spine's
  description field it is at most one, because that field is blank on 84% of rows and the blanks form
  a single blob that swallows every code at once (§2.5).
- `ZKK 114`, the largest code at 144,830 rows, holds **1,901 distinct leading nouns**. Its top four
  are `HARNESS` 15,895 rows, `PIPE` 11,432, `CONTROL UNIT` 7,982, `BRACKET` 7,670 — together 30% of
  the code.
- `ZKK 070` at 14,612 rows is the opposite case: `SPRING` 8,037 rows (55.0%) and `SPRING ASM` 2,235
  (15.3%), i.e. a code that happens to be spring-ish but is still not a family — it holds 358 nouns.

So ZKK is a catalogue and price bucket. A chart by ZKK will not answer "how is our filter business
doing" and a chart by ZKK will not be recognised by a distributor.

### 2.2 HKK — the 2022 glossary still describes the letter, and the fourth character is not uniform

On `01_data\HKK Code 20221028.xlsx` (dumped to `01_data\90_INBOX\_hkk_dump_20260920.txt`), the letter
under prefix `111` or `113` maps to a real part family. Tested against the live 2026 descriptions:

| HKK | rows | top descriptions | 2022 sheet said |
|---|---:|---|---|
| `1110` | 458,368 | CONTROL UNIT; E, HARNESS; CAB, HARNESS; FRAME | prefix 111, letter 0, "General Parts" |
| `113G` | 26,855 | GASKET SET; ENG (16,663) | `113 G` = "Gasket" |
| `313A` | 11,726 | SPRING; LEAF (9,036) | `313 A` = "Spring" |
| `111D` | 6,120 | CAB ASM; SERVICE (5,770) | `111 D` = "Cab" |
| `111K` | 3,626 | LINER SET; ENG (3,058) | `111 K` = "Liner, Liner Kit" |
| `1131` | 2,517 | BEARING; NEEDLE, COUNTER, THRUST | `113 1` = "Bearing" |
| `111J` | 1,522 | PUMP ASM; INJ, NOZZLE ASM; INJ | `111 J` = "Nozzle" |
| `1128` | 1,082 | DISC; CLUTCH (961) | `112 8` = "Driven Plate ASM" |

That is a real finding in HKK's favour and it corrects the earlier note, which said the family
content only appears once the trailing digit is separated. The slot character carries the family —
the fourth character under these prefixes, which is a letter.

**But the fourth character is not a uniform sales-status flag.** *(Corrected 2026-09-20. This section
was first written about a "fifth character"; there is no fifth character. Every one of the 125
distinct HKK values on `PRICE CD 250912` is exactly **four** characters, on all 536,854 rows. The
argument is unchanged in substance, restated against four characters.)* The earlier note read the
trailing digit as status (`4` = surcharge, `8` = VOR, and so on). On the live file:

- HKK is a three-digit prefix plus one **fourth** character, which may be a letter or a digit.
- The digit `4` appears as that fourth character on **2,100 rows in total**, almost all of them `3114`
  (2,094 rows); the rest is `1124` at 4 rows and `1914` at 2. There is no code `1114` at all.
- `3114`'s top descriptions are GOVERNOR ASM; INJ, SHIM; PLUNGER, PLUG; CLOSING — injector pump
  components. The 2022 sheet agrees: `311 | 4 | Inj Pump`, i.e. the fourth character is a part slot
  under prefix `311`, not a status.
- The status reading holds where the 2022 sheet supports it — `111 4` is "Surcharge for VOR handling",
  `111 8` is "VOR Order". It does not hold under prefix `311`.

So that fourth character is a **slot label that means different things under different prefixes**. A
status reading is safe under prefix `111`; it is unsafe everywhere else. **Which prefixes the status
reading is valid for is NOT fully decoded.**

Distribution of HKK on the live file: 125 distinct codes; `1110` alone is 458,368 rows and all
`111*` codes together are **89.08%** of the file.

### 2.3 Do ZKK and ZUK determine the price class? No — they correlate with it

Measured over all 536,854 rows, the share of rows carrying each code that show each dominant
`New Part Class`:

| Code | rows | dominant class | share of rows | second class |
|---|---:|---|---:|---|
| ZKK `114` | 144,830 | `XC` | **77.4%** | `DD` 4.7% |
| ZKK `070` | 14,612 | `XM` | **68.9%** | `XC` 14.8% |
| ZKK `200` | 66,042 | `XC` | **59.0%** | `EV` 20.0% |
| ZKK `283` | 33,357 | `XC` | **81.0%** | `C` 2.9% |
| ZUK `11G00` | 265,999 | `XC` | **78.4%** | `EV` 5.0% |
| ZUK `13G00` | 13,150 | `XM` | **80.6%** | `XC` 9.2% |
| ZUK `11F91` | 6,977 | `XC` | **73.1%** | `XF` 8.1% |

The pattern is real — ZKK `070` and ZUK `13G00` pick out the `XM` class, everything else lands mostly
in `XC`. But "100% on every row" is not what the file shows. **A price-class table built by reading
`New Part Class` alone is more accurate than one inferred from ZKK or ZUK.** The codes are a useful
cross-check on the class, not a substitute for the column.

`New Part Class` has **40** distinct values on the file, of which `XC` is 382,000 rows and 4,095 rows
are blank. The spine uses a different, one-letter vocabulary, so the two do not join directly.

### 2.4 The benchmark table

Source: `01_data\90_INBOX\_classification_benchmark_20260920.json` and
`_classification_benchmark_tables_20260920.csv`, from
`01_data\91_build\benchmark_classification_systems_20260920.py`.

**Common base: 139,524 part numbers, EUR 46,183,084 — the 88.11% of the billed book that carries a
ZKK code.** Every system below is measured on that same slice. Read §3.1 before using any row.

| System | Codes used | Codes ≥1% of euro | Biggest single code | Top-10 share | Leading-noun purity | Service basket in system's top-3 codes | Euro coverage of base |
|---|---:|---:|---:|---:|---:|---:|---:|
| ZKK (Japan) | 132 | 12 | 46.77% | 92.03% | 82.59% | 73.44% | 100% |
| ZUK (Japan) | 284 | 5 | 69.38% | 87.91% | 82.60% | 82.57% | 100% |
| HKK (Japan) | 72 | 7 | 76.76% | 92.89% | 82.59% | 63.92% | 100% |
| ZKK + EPLE (Japan) | 12,268 | 12 | 44.60% | 86.29% | 82.85% | 71.96% | 100% |
| Figure key prefix (Japan) | 287 | 33 | 7.95% | 38.72% | 82.55% | 64.38% | 99.84% |
| AIM L1 (ours, live) | 25 | 18 | 17.06% | 81.71% | 86.18% | 100.00% | 100% |
| AIM L2 (ours, live) | 110 | 30 | 9.36% | 44.09% | 88.77% | 77.68% | 100% |
| AIM L1>L2>L3 (ours, live) | 518 | 32 | 4.66% | 28.79% | 90.49% | 65.21% | 100% |
| 15-level functional (ours, Apr 2026) | 16 | 15 | 17.82% | 88.45% | **20.09%** | 91.61% | 95.40% |
| 15-level functional L1>L2 (ours, Apr 2026) | 94 | 29 | 8.51% | 47.02% | **37.78%** | 71.43% | 95.40% |

Two rows of that table do not reconcile, and one column of it is broken. See §2.5 and §3.2.

### 2.5 The purity column is measuring missing descriptions, not classification quality

The benchmark asks our spine for a description to derive the leading noun, then measures purity on the
common base. Our spine's `description` column is **blank on 139,310 of 165,213 rows — 84.32%**. Blanks
group as identical, so they inflate purity for whichever system lumps them together.

Re-measured on the same base with the Japanese description (`jp_description`, which is complete on
every row):

| System | Benchmark purity (our spine description) | Re-measured (Japanese description) | blank share of the base |
|---|---:|---:|---:|
| ZKK | 82.59% | **12.32%** | 82.59% |
| HKK | 82.59% | **16.28%** | 82.59% |
| AIM L1 | 86.18% | **8.21%** | 82.59% |
| AIM L1>L2 | 88.77% | **10.94%** | 82.59% |

The benchmark's purity column is therefore **not a usable measure of classification quality**, on any
row. The published numbers are the blank share plus a small residue. The re-measured column reverses
the story: the systems that looked purest were the ones with the most blanks inside each code. Note
also that purity favours coarse systems by construction — a system with one code scores 100%. Any
corrected metric must therefore state the code count beside the purity, or normalise it; and the
row-weighted and euro-weighted versions should both be shown, because they rank the systems
differently. Reference values on the Japanese description from the independent pass: ZKK **12.32%**
at 132 codes, ZUK **12.85%**, HKK **16.28%** at 72 codes; euro-weighted on the non-blank spine
description, ZKK 17.25%, ZUK 20.03%, HKK 30.20%, AIM L1 33.25%, AIM L1>L2 66.42%. *(The 88.83% above
was corrected to 88.77% on 2026-09-20; the 10.94% was right.)*

The Japanese description is available on our spine only for the 139,524 parts that matched the price
file, so a fair purity measure for AIM L1/L2 needs a description we do not have for 25,689 spine rows.

### 2.6 Where the source files disagree with each other

Three disagreements, all checkable by re-running the joins:

1. **HKK row counts.** `HKK_SYSTEM_REVIEW_2026-09-20.md` §9 stated 536,854 rows with `1110` at
   491,294 (91.5%) and `1114` at 21,834. On the same workbook I measure `1110` at **458,368** (85.38%)
   and no `1114` at all. The gap is 32,926 rows and applies only to the HKK field — ZKK (142 codes),
   ZUK (359 codes) and the row count (536,854) all agree exactly. **Settled 2026-09-20 by an
   independent full pass: 458,368 and 0 are correct on `PRICE CD 250912`.** `PRICE CD 260910.xlsx` has
   no HKK column and cannot be the source of any HKK count. The origin of 491,294 and 21,834 is
   **UNKNOWN** — they match no file on this machine.
2. **ZUK versus HKK overlap.** *(Added 2026-09-20.)* Measured at code level, **0 of 359** ZUK values
   equals any HKK value, and 0 of 359 equals any ZKK value; no ZUK value shares even a three-character
   prefix with a ZKK code. The two columns `ZUK` and `HKK` share their leading two characters on
   96.89% of rows against 93.92% expected if they were independent. That is a property of both columns
   being dominated by one code family, not evidence that they carry the same information. Settled.
3. **ZKK versus the HKK prefix list.** §1.1 above. Of the **27** prefix values on the 2022 HKK
   workbook, **7** appear in ZKK and **20 do not** — `111`, `112`, `118`, `123`, `133`, `191`, `310`,
   `311`, `312`, `313`, `319`, `320`, `333`, `334`, `335`, `336`, `337`, `338`, `339`, `391`. Against
   the 25 three-character prefixes in the live HKK column, ZKK shares 5 and 20 do not.
   *Corrected 2026-09-20:* this item first said "24 prefix values … 19 do not". Both are now measured:
   **27** prefixes, **7** shared, **20** not shared.
4. **The service-basket column is circular.** The benchmark defines the service basket as spine rows
   whose AIM L1 is `Maintenance Service`, then measures how well each system concentrates that basket.
   AIM L1 therefore scores 100.00% by construction. ZKK, ZUK and HKK are asked to reproduce a
   definition that belongs to AIM, and are penalised for not doing so. Read that column as
   "agrees with AIM's own basket", never as "sees the aftersales business".

### 2.7 Three more limits inside the benchmark script

- The script's own docstring lists a `stability` metric — code churn between the September 2025 file
  and the current master price file. **It is not implemented.** There is no stability row in the JSON.
  Do not quote one.
- The HKK row measures 5-character codes. §2.2 shows HKK is actually **four** characters and the
  family lives in the letter inside the fourth slot, so the HKK row is measured at the wrong
  granularity: `1110` is "prefix 111, General Parts, slot 0" — and codes beginning `111` are 89.08% of
  the file.
  *Corrected 2026-09-20:* the sentence read "§2.2 shows the family lives in characters 1 to 4". There
  are only four characters, so "characters 1 to 4" is the whole value. The point stands: the HKK row
  should be re-run at four characters, and the fifth-character framing is withdrawn.
- The ZUK row is measured at five characters across 284 codes, of which 308 of the 359 values are
  `11xxx`. ZUK's own shape puts the letter third, so the first four characters may be the meaningful
  unit and the fifth a variant. **Not tested.** The 69.38% top-code share in §2.4 may be a
  granularity effect rather than a real concentration.

---

## 3. The honest limits, stated as limits

### 3.1 The common base flatters AIM

The benchmark only measures the 88.11% of euro that carries a ZKK code. AIM was classified on that
same slice, so AIM's coverage and granularity numbers are computed where AIM had something to work
with. The **11.89% of the billed book that carries no ZKK code — EUR 6,231,324 across 25,689 spine
part numbers — is absent from the table entirely**.

A fair AIM score has to be computed on **all 165,213 spine rows**, including the ones ZKK cannot
label. **That is NOT YET DONE.** Until it is, do not quote "AIM covers X% of the book" from this
benchmark.

### 3.2 The 15-level functional rows do not reconcile, and must be recomputed

The April 2026 workbook has a real functional mapping on the `PARTS FUNCTIONAL` sheet — `PN`,
`L1 Category`, `L2 Sub-Category`, 15,353 rows, 16 distinct L1 values. The benchmark's two 15-level
rows show 16 codes and 94 codes, which is the right code count for that sheet. **The euro is what does
not fit, and I could not reconcile it.**

- The benchmark's L1 row labels **EUR 44,057,046** across its 16 codes, covering 14,948 individual
  part numbers — only **10.71%** of the common base's parts.
- On the spine, all 15,353 mapped part numbers together are worth EUR 46,578,498. Restricted to the
  88.11% ZKK slice that this benchmark uses as its base, they can be worth at most roughly EUR 41M.
- So the benchmark's euro share sits **above** what the April 2026 mapping can carry on this base, by
  more than a rounding margin. I do not know why.

I also have to correct something I concluded in an earlier pass of this same brief: I thought the
script had read the `Segment` column of `PARTS MASTER` (nine revenue tiers, `A-X` to `C-Z`) instead of
a function. That is wrong. The code values in the JSON — `EXHAUST & EMISSION`, `ELECTRICAL & SENSORS`,
`BRAKES`, `UNCLASSIFIED` — are `L1 Category` values, and the code count matches `PARTS FUNCTIONAL`,
not `Segment`'s nine. The script's comment about a previous run reading the wrong column appears to
have been addressed. What I cannot explain is the euro.

**Do not use either 15-level row until it is recomputed from `PARTS FUNCTIONAL` with the euro printed
per level-1 category beside the row count.** If the two reconcile, the 15-level design is a serious
contender; on the benchmark's own numbers it beats everything except the figure key prefix on
granularity, while touching a tenth of the parts.

### 3.3 Nothing here is verified against Japan

Whether Japan defines ZKK and ZUK, or whether these are codes ISZE or ISZJ applies on our side, is
**UNKNOWN**. We hold Japan's file, and that is all we hold. No confirmation, no code table, no
documentation.

### 3.4 There may be no published description list for these codes

Whether a ZKK or ZUK code table with published descriptions exists is **UNKNOWN**. The 2022 HKK
workbook is the only naming evidence we hold, and it names the prefix, the letter and the slot digit —
**it does not name ZKK or ZUK at all**. So we can decode HKK's letters from a document a customer sent
us in 2022; we cannot decode ZKK or ZUK from anything.

### 3.5 Version and currency

All codes in this brief come from the September 2025 price file. The current master price file on disk,
`01_data\PRICE CD 260910.xlsx`, has **13 columns** and carries **none** of `ZKK`, `ZUK`, `HKK`,
`EPLE` or `Example Model`. The 13 columns are `Country of origin, Inventry code, GM Pno, Pno, New Pno,
Parts name, Base price, Model, QTY, Net weight, H/S code, FIGKEY, Class`, and the file holds
**533,400** data rows on `Sheet1`. (The earlier "14 columns" was corrected to 13 on 2026-09-20.) So the
complete codes are one file-generation behind the price file we are actually working from, and the
column set is not guaranteed to be stable.

Careful with the row counts: **533,400** belongs to `PRICE CD 260910.xlsx` and **536,854** belongs to
`【CY2026Price Revison】PRICE CD.xlsx`. Any sentence that puts 533,400 beside the ZKK or ZUK figures is
mixing the two files.

### 3.6 ZUK's meaning

Restated because it matters for the design: ZUK is complete, well-shaped and undocumented.
**What it categorises is UNKNOWN.**

---

## 4. One correction to state plainly: the July 2026 verdict on ZUK

A July 2026 agent session reviewed this same file and concluded that `Example Model`, `ZUK`, `HKK` and
`ZKK` were "a lossy sample, not a PN-to-model bridge". The reasoning was that values such as `WFJTUB`
are two-letter model prefixes concatenated and capped at about three examples. Its own extract is on
disk at `01_data\90_INBOX\_hkk_zkk_transcript_extract_20260920.md`.

That reasoning is **correct for `Example Model` only**. Measured on the file:

- `Example Model` is free-form, 1.8% blank (9,823 rows), lossy, and its parse is ambiguous on odd
  lengths. The July finding stands for this column and this column alone.
- `ZUK` is **0% blank, exactly five characters on 536,854 of 536,854 rows, always the shape
  digits-digits-letter-digits-digits, 359 stable values**. That is a defined code, the opposite of a
  sample.
- `ZKK` is likewise 0% blank with 142 values of exactly three characters.

The session took one column's defect and wrote it across four columns. `ZUK` and `ZKK` were
characterised from `Example Model`'s problems. That is the error, and its cost is visible: nobody
followed up on the two columns that were actually complete, and the same four columns were
re-dismissed months later on the same reasoning.

GPT: this is the claim I would most like independently checked, because it is a statement about the
behaviour of an earlier agent, and because "the sample is lossy" is exactly the kind of verdict that
sounds safe. Check `ZUK` and `Example Model` separately and see whether you reach two different
answers.

---

## 5. The design: how ZKK and ZUK sit next to AIM v2

### 5.1 The two axes, and why neither replaces the other

| | AIM v2 | ZKK and ZUK |
|---|---|---|
| Answers | what the part is for | where the part sits in Japan's catalogue, and which price class family it belongs to |
| Owner | ours; we maintain it | Japan's; it arrives with the price file |
| Complete? | no — 9,164 parts are still catalogue Other/review with no family | yes — 0 blank rows on 536,854 |
| Upkeep | manual work per part | free, one join |
| Stable over time? | changes when we work on it | fixed by the file generation; nothing here needs upkeep |
| Moves to match our view? | it *is* our view | it never moves to match our view |
| Good for | aftersales mix, capture, the service basket, anything a distributor or a manager reads | budget and price-class work, catalogue position, completeness checks |
| Bad for | cross-checking catalogue completeness | answering "how is our filter business doing" |

Neither is a superset of the other. ZKK cannot name the filter family; AIM cannot tell you a part's
catalogue block or which class family it sits in. Fusing them onto one axis is the same defect the
17 September audit found when the old single `aim_l1` column held "Repair parts" and "Engine" as
equals. One chart cannot carry both, because a reader cannot tell whether two adjacent bars are two
kinds of part or two catalogue blocks.

### 5.2 What to put on the spine

The spine would carry both, side by side, and each chart declares its axis on its face:

- `aim_l1`, `aim_l2`, `aim_l3` — functional. Ours. The axis for the aftersales, capture and service
  story.
- `jp_zkk`, `jp_zuk`, `jp_hkk`, `jp_fig_key` — Japan's catalogue labels, carried as attributes.

**That is already done.** `01_data\00_derived\aim_master_v2.csv` now has 32 columns; the eight Japan
columns were appended and the gate that recorded the change is
`01_data\90_INBOX\_jp_codes_spine_gate_20260920.json`. It records 165,213 rows, 24 columns before and
32 after, `pn_matched` 139,524, euro matched 88.11%, and all three structural checks passing: row
count unchanged, header is the old columns plus the new ones, and existing columns unchanged. Fill on
the new columns is 139,524 of 165,213 rows.

So the spine side of this design is **done and verified**, not proposed.

### 5.3 Division of labour to propose

| Question | Axis | Why |
|---|---|---|
| What is our budget or price position in this class? | ZKK / ZUK, with the `New Part Class` column as the primary source | catalogue and price-class question |
| What is our aftersales mix, capture, or service basket? | AIM | functional family question |
| Which specific part is this, on which figure? | figure key | part identification and drill-down |
| Is our catalogue covered? | ZKK against AIM, side by side | a part with ZKK and no AIM family is a known gap, countable |

### 5.4 What still needs work in AIM v2 for this to hold

1. **9,164 parts sit in catalogue Other/review with no AIM family** — EUR 114,516 of last-twelve-month
   billing, of which 398 part numbers carry all the euro and 8,766 carry none. Source:
   `01_data\90_INBOX\AIM_residual_Other_review_TRUE_OPEN_by_L12M_20260920.xlsx`. Adding a legal AIM
   leaf for each of these is manual work.
2. **The taxonomy already exists and is applied to a slice.** `01_data\01_Pricing\ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx`,
   sheet `PARTS FUNCTIONAL`, holds a part-by-part functional mapping for **15,353 part numbers**
   across 16 level-1 categories, produced April 2026. All 15,353 of those part numbers are on the
   current spine, and they carry **EUR 46,578,498 = 88.87% of the billed book**. The spine's remaining
   149,860 part numbers, worth EUR 5,835,910, carry no mapping from that workbook.

   I checked that arithmetic because it contradicts an earlier plan. The workbook's own title row
   says "15,353 PNs — 92.6% revenue classified". That 92.6% is measured against
   `PARTS MASTER`'s own 15,353-row base, which totals **EUR 26.7M** per its title row — under half
   of our billed book, and a different base from the one this brief uses. Against our book it is **88.87%**, which is
   remarkably close to ZKK's 88.11% by coincidence rather than by construction — the two cover
   different parts.

   The point stands and it is the important one: **the taxonomy exists, in English, with level 1 and
   level 2 codes, and it was simply never put on the full spine.** That is a load job against a file
   we already have, not a design job. Its 3,374 `UNCLASSIFIED` rows are the same open problem as
   item 1, seen from the other side.

3. **A fair AIM score must be recomputed on all 165,213 rows** before any coverage claim goes
   outward. See §3.1.

---

## 6. What GPT should challenge / re-measure

Please mark each CONFIRM / REJECT / UNKNOWN with evidence and a command.

1. **The 88.11% coverage figure.** Does joining `01_data\00_derived\jp_codes_cache_20260920.csv` to
   `01_data\00_derived\aim_master_v2.csv` on `pn` still give 139,524 parts and EUR 46,183,084 of
   EUR 52,414,408? Watch the join key: the price file's `Pno` and our `part_number` are both strings
   and both have leading zeros somewhere.
   *(Re-measured 2026-09-20 on the 09:24 spine: **139,524** parts and **€46,183,083.72 of
   €52,414,407.82 = 88.11%**, with **25,689** blank rows. Confirmed.)*
2. **ZKK's code list equals the HKK prefix list — I could not reproduce this.** The answer depends on
   which HKK prefix list is meant. The 2022 HKK workbook lists **27** prefixes across its three
   sheets; ZKK shares **7** with it (`113`, `114`, `115`, `211`, `330`, `331`, `332`) and not the
   other 20. The 25 three-character prefixes that actually appear in the live HKK column share **5**
   with ZKK (`110`, `113`, `213`, `331`, `332`). **0 of 142** ZKK values equals any full HKK value.
   The two candidate lists do not agree with each other. Meanwhile 118 ZKK values — the whole
   `200`–`299`, `530`–`560` and `600`–`700` blocks among them — appear in no HKK list at all. Under
   what definition is the claim true?
   *(Numbers corrected 2026-09-20: this item first said 24 prefixes and 5 matches on the 2022 workbook.
   Confirmed by a second independent measurement.)*
3. **That ZKK and ZUK determine the price class.** I measure the dominant class of ZKK `114` at
   `XC` on 77.4% of its rows, ZUK `11G00` at `XC` on 78.4%, ZUK `13G00` at `XM` on 80.6%. Rows exist
   for several codes with no single class. Does any code reach 100%?
4. **The purity result.** I cannot reproduce 17.5%, 82.59% or 20.09%. On the Japanese description I get
   17.74% for ZKK and 12.32% on the common base; the benchmark's spine description is blank on 84.32%
   of rows, which is what produces its 82.59%. Recompute purity only on rows with a real description
   and see which systems survive.
5. **The ZUK shape claim.** Verify 536,854 of 536,854 rows are exactly five characters with the letter
   in position 3 and all other positions numeric, and that there are 359 distinct values with only
   `A B C D E F G` ever appearing as the letter.
   *(Confirmed 2026-09-20 by an independent pass, together with the added point that 0 of 359 ZUK
   values equals any HKK or ZKK value. See §2.6 item 3.)*
6. **Would any live pack break if the columns were added?** The eight `jp_*` columns were appended, so
   every existing column kept its position and only 16 Python files read the spine by name. I did
   **not** run any pack. Rebuild or dry-run at least the pricing system
   (`01_data\90_INBOX\build_pricing_system_20260919.py`), the UTI lighting measurement
   (`01_data\90_INBOX\measure_uti_lighting_collision_20260919.py`) and the lamps review
   (`01_data\90_INBOX\build_lamps_insurance_review_20260919.py`) and say whether output is unchanged.
7. **The HKK row counts.** 458,368 versus 491,294 for `1110`, and 0 versus 21,834 for `1114`, on the
   same file. **Settled 2026-09-20:** 458,368 and 0 are correct on `PRICE CD 250912`; `PRICE CD
   260910.xlsx` has no HKK column and cannot source an HKK count; the origin of 491,294 and 21,834 is
   UNKNOWN. ZKK, ZUK and the row count agree exactly because they were read correctly; only the HKK
   per-value counts were wrong.
8. **The HKK fourth character.** Is that character a sales-status flag under every prefix, only under
   `111`, or never? `3114` looks like "Inj Pump" from both the 2022 sheet and the live descriptions,
   not a surcharge. *(Heading corrected 2026-09-20: it asked about a "fifth character". HKK values are
   four characters; there is no fifth. The status question itself is still open.)*
9. **The HKK granularity.** The benchmark measures HKK codes as if they were five characters. Re-run
   HKK at four characters and see whether its top-10 share collapses from 92.89% and its service-basket
   share rises from 63.92%.
10. **The 15-level functional euro.** Both 15-level rows show shapes consistent with reading the
    `PARTS FUNCTIONAL` sheet, but their euro coverage of the common base — 95.40% — is above what the
    15,353 mapped part numbers can carry on that base. Recompute from `PARTS FUNCTIONAL`, print the
    euro per level-1 category next to the row count, and reconcile to the spine. Then say whether the
    15-level design beats AIM L1>L2>L3 on granularity, or does not.
11. **AIM on the full book, not on the ZKK slice.** Compute AIM L1, L2 and L1>L2>L3 on all 165,213
    spine rows, including the 25,689 with no ZKK code, and report what is left blank. This is the
    number that would actually go outward, and it does not exist yet.
12. **The 15,353-part functional map.** Confirm that every one of those part numbers is on the current
    spine, that the mapping is one row per part with no duplicates, and that loading it lifts AIM
    coverage on the full book. My measurement says 15,353 of 15,353 rows are on the spine, no
    duplicates, worth EUR 46,578,498 or 88.87% of the billed book.
13. **What ZUK means.** If GPT can find any published Isuzu description of ZUK, that settles §3.6. If
    not, say UNKNOWN and do not guess.
14. **Anything in the July 2026 extract that I have mis-stated.** §4 accuses that session of writing
    one column's defect across four. Check the extract directly.

---

## 7. Absolute paths (this PC)

Files used for this brief:

- Precedent for this brief's shape: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_REVIEW_classification_switch_20260920.md`
- Earlier ZKK / ZUK note, with its own corrections notice: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\HKK_SYSTEM_REVIEW_2026-09-20.md`
- Coverage of each Japanese field against our book: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_jp_codes_match_report_20260920.json`
- System-versus-system benchmark: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_classification_benchmark_20260920.json`
- Benchmark, flat tables: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_classification_benchmark_tables_20260920.csv`
- The 142 ZKK code counts: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_zkk_code_counts_20260920.json`
- Full dump of the 2022 HKK workbook sheets: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_hkk_dump_20260920.txt`
- July 2026 session extract that dismissed ZUK: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_hkk_zkk_transcript_extract_20260920.md`
- Extracted part-number to code map, 536,854 rows: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\jp_codes_cache_20260920.csv`
- Extractor that built the map: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\extract_jp_classification_codes_20260920.py`
- Benchmark script: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\benchmark_classification_systems_20260920.py`
- Script that appended the Japan columns to the spine: `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\apply_jp_codes_to_spine_20260920.py`
- Gate recording that spine change: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_jp_codes_spine_gate_20260920.json`
- Live spine, now 32 columns: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv`
- Pre-change backup of the spine: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\aim_master_v2.csv.bak_pre_jpcodes_20260920_070544`

Source data:

- September 2025 Japanese price file, one sheet `PRICE CD 250912`, 536,854 rows: `C:\Users\jerom\Desktop\claude\ISZE\01_data\【CY2026Price Revison】PRICE CD.xlsx`
  (the file name contains two full-width bracket pairs, so quote the path or resolve it with a glob)
- Current master price file — carries none of these codes: `C:\Users\jerom\Desktop\claude\ISZE\01_data\PRICE CD 260910.xlsx`
- 2022 HKK workbook supplied by the customer: `C:\Users\jerom\Desktop\claude\ISZE\01_data\HKK Code 20221028.xlsx`
- April 2026 classification workbook, sheets `FUNCTIONAL TAXONOMY` and `PARTS FUNCTIONAL`: `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx`
- True-open part list: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\AIM_residual_Other_review_TRUE_OPEN_by_L12M_20260920.xlsx`
- Earlier spine audit: `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\docs\AIM_CLASSIFICATION_AUDIT_2026-09-17.md`

---

## 8. Honesty about agent error risk

What this brief has **not** verified:

- Nothing is confirmed with Japan. Who defines ZKK and ZUK, and whether a published code table exists,
  are both UNKNOWN.
- What ZUK categorises is UNKNOWN. It is complete and well-shaped and we cannot say what it means.
- No live pack was rebuilt after the Japan columns were appended. I checked the file-level gate and
  counted the readers; I did not run one.
- A fair AIM score on all 165,213 spine rows does not exist. The only AIM numbers in this brief sit on
  the 88.11% ZKK slice.
- The disagreement with the earlier ZKK note over the HKK row counts was **settled on 2026-09-20** by an
  independent full pass: 458,368 and 0 are correct on `PRICE CD 250912`, and the origin of 491,294 and
  21,834 remains UNKNOWN. The cause of the earlier reading is not proven, though its shape — too high
  for one value and non-zero for a value that does not exist — is the shape of a mis-scoped read.
- I did not open the current master price file's columns myself; the "carries none of ZKK, ZUK, HKK,
  EPLE" statement is carried from the earlier note.
- The stale column count for the current master price file is **resolved** (2026-09-20).
  `PRICE CD 260910.xlsx`, sheet `Sheet1`, is **533,400 data rows and 13 columns**; the columns are
  `Country of origin, Inventry code, GM Pno, Pno, New Pno, Parts name, Base price, Model, QTY, Net
  weight, H/S code, FIGKEY, Class`. The 533,400 in `HKK_SYSTEM_REVIEW_2026-09-20.md` §4 and the 13 in
  its §10 both refer to this same file and are both correct; the "14" in this brief's §3.5 was wrong.
  The **536,854** belongs to `【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912`, which is
  the September 2025 file carrying the Japanese codes.

Where this work has been wrong before, so GPT can weight it:

1. **The July 2026 ZUK verdict.** Four columns dismissed on one column's defect. §4. This is the error
   this brief exists to correct.
2. **Three figures in the earlier ZKK note had to be corrected the same day it was written** — the
   fill rates, the claim that the letter is the only family signal, and the error class in its §8.
   Their own corrections notice is at the top of `HKK_SYSTEM_REVIEW_2026-09-20.md`. The correction
   was made honestly and quickly; the fact that it was needed is the point.
   **A further seven corrections were applied to that note on 2026-09-20** on the independent audit's
   findings: its §9 HKK row counts and §10.3 class table were wrong, its §10.1 prefix-equality claim
   was wrong, its "five characters" framing was wrong, its purity sentence was wrong, and its 91.5%
   share appears in two places. Items 4–7 of its corrections notice list them.
3. **I contradicted this brief's own instructions in four places**, and I have written what I measured
   rather than what I was asked to state: the ZKK/HKK prefix equality, the price-class claim, the
   purity figures, and the HKK row counts. All four were **independently confirmed on 2026-09-20**, and
   one further correction to my own work was needed: the 2022 workbook carries 27 prefixes, not 24. I
   also corrected one of my own conclusions mid-draft — I first read the 15-level benchmark rows as
   measuring the wrong column, then established that they are not, and rewrote §3.2. Corrections are
   in the file rather than tidied away.
4. **The benchmark's purity column and its 15-level euro reached a file on disk looking authoritative**
   while being, on my reading, a measure of blank descriptions and an unreconciled number. A figure in
   a JSON file is not evidence that the figure means what its name says.

Treat §1 and §2 as **claims with paths**, not as settled. Re-run the joins.

---

*Nothing was rebuilt, renamed, moved, mailed or published in producing this brief. No existing file
was modified. The only file written is this one.*


---

## Part IV — Reproducibility audit (independent re-measure)

# Reproducibility audit — Japanese classification codes (ZKK / ZUK / HKK / EPLE)

**Date:** 2026-09-20 · **Internal / private** · read-only measurement, no rebuild, no mail
**Scope:** the four disputed claims in `HKK_SYSTEM_REVIEW_2026-09-20.md` §9–§13 and
`GPT_REVIEW_ZKK_ZUK_and_AIM_v2_20260920.md` §6, plus the ZUK overlap question and a consistency
check against the concurrent class-concentration note.

**Workbook pass method.** The Japanese price workbook was read once, fully, with `openpyxl` in
`read_only` mode, and every counter was collected in that single pass. It took 54 seconds. One
further pass was made over one sheet of `PRICE CD 260910.xlsx` (46 seconds). Nothing else was read
twice. All other numbers come from the derived CSVs.

---

## Verdict

Counted plainly: of the six items, **four needed correcting and two held**. Claim 4's rebuttal (the
purity column is measuring blanks) is correct and reproduces to the decimal, and claim 6 (the
concurrent class note) reconciles to the row. Claims 1, 2, 3 and 5 are all wrong as written. One
thing was measuring a different quantity from the one it named: the benchmark's `leading_noun_purity_pct`
column, which is a blank-description count wearing a classification-quality label.

Claim 1 (ZKK equals the HKK prefix list) is wrong under every definition of "prefix list" I could
construct, and wrong by a wide margin — the true intersection is 5 codes against the live HKK file,
not 142. Claim 2 (ZKK `114` maps to class `XC` on 100% of rows) is wrong on both class columns; the
correct figure is 77.4%. Claim 3 (HKK `1110` = 491,294 rows, `1114` = 21,834) is wrong on both
counts: the correct values on the named sheet are 458,368 and 0, and the published pair matches no
file I can find, so its origin is UNKNOWN. Claim 5 (ZUK overlaps HKK heavily) is false at code
level: no ZUK value equals any HKK value, though 96.89% of rows share the first two characters
against 93.92% expected by chance, so the "overlap" is a marginal-distribution artefact rather than
a shared meaning.

The one-sentence version: the earlier ZKK note's §9 numbers cannot be reproduced and its §10.3 table
cannot be reproduced, but its central conclusion — ZKK is a catalogue-and-price bucket and not a
functional family — is **strengthened**, not weakened, by every correction below.

---

## Results table

| # | Claim | Published value (source, as written) | Measured value (my source) | Verdict |
|---|---|---|---|---|
| 1 | ZKK's code list equals the HKK prefix list | "the ZKK code *is* the HKK prefix" — §10.1; rebuttal: 5 of 142 | ZKK ∩ live HKK 3-char prefixes = **5 of 142** (`110, 113, 213, 331, 332`); ZKK ∩ 2022 workbook prefixes = **7 of 142** (`113, 114, 115, 211, 330, 331, 332`); ZKK ∩ live HKK 4-character codes = **0** | **Corrected — claim false** |
| 2 | ZKK `114` maps to class `XC` on 100% of its 144,830 rows | §10.3, "dominant class `XC`, share 100%" | On `New Part Class`: **112,095 / 144,830 = 77.40%**. On `Current Part Class`: **112,087 / 144,830 = 77.39%**. Excluding the 789 blank class rows: **77.82%** (`New Part Class`) | **Corrected — claim false** |
| 3 | HKK `1110` = 491,294 rows; `1114` = 21,834 rows | §9 table | On `【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912`, column `HKK`: `1110` = **458,368**; `1114` = **0**. No `1114` row exists | **Corrected — claim false**; origin of 491,294 UNKNOWN |
| 4 | The purity column measures blanks, not classification quality | rebuttal: spine description blank on 84.32%; ZKK 82.59% → 12.32% | Spine description blank on **139,310 / 165,213 = 84.32%**; on the benchmark's own base **115,228 / 139,524 = 82.59%**. Benchmark-style purity **82.59%**; Japanese-description purity **12.32%** | **Rebuttal confirmed; metric not usable** |
| 5 | ZUK overlaps HKK heavily | no value given, argued from leading characters | ZUK ∩ HKK at value level = **0 of 359 vs 125**. Shared first two characters on **520,152 / 536,854 = 96.89%** of rows; **93.92%** expected if independent | **Corrected — claim false at code level** |
| 6 | (consistency check) — class-concentration note vs benchmark | `CLASS_PRICE_CLASS_CONCENTRATION_2026-09-20.md` | Every class figure in it reconciles to the row against my independent pass, including the 40-distinct-code count and the full 13-bucket fits-rule breakdown. Two small wording points only | **Consistent — no material disagreement** |

---

## Claim 1 — ZKK's code list equals the HKK prefix list

**Method.** Two sources for "the HKK prefix list", because the claim does not say which one is
meant, and one format test.

- Live HKK prefixes: the first three characters of the `HKK` column in
  `01_data\【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912`, all 536,854 rows. A full
  pass, no filter. 125 distinct HKK values collapse to **25** distinct three-character prefixes.
- 2022 HKK workbook prefixes: `01_data\HKK Code 20221028.xlsx`, sheets `Parts`, `Accessories`,
  `Lubricant`, read with full-width digits normalised. A code counts as a prefix only when a
  three-digit number sits immediately left of a single part-slot character in the same row, which is
  the sheet's own layout pattern. That yields **27** prefixes.
- ZKK: the `ZKK` column of the same sheet. **142** distinct values, every one exactly three
  characters, with no leading zeros lost — the cells are stored as text, not numbers.

**The format normalisation was tested first, as instructed.** ZKK `114` is three characters; HKK
`1110` is four. I tested the candidate normalisations and only one is even close:

| Normalisation tried | Intersection with ZKK | Result |
|---|---:|---|
| ZKK (3 char) vs HKK full cell (4 char) | **0 of 142** | fails — no ZKK value ever equals a full HKK value |
| ZKK vs the first 3 characters of HKK (live file) | **5 of 142** | the rebuttal's number, confirmed |
| ZKK vs the 2022 workbook's 3-digit prefixes | **7 of 142** | `113, 114, 115, 211, 330, 331, 332` |

Truncating HKK to its first four characters is a no-op, because the live HKK values are already four
characters — there is no five-character HKK code in the price file, contrary to the earlier note's
claim that HKK is five characters wide with a trailing sales-status digit. All 125 distinct HKK
values on the file are exactly four characters.

**The numbers.** Under the live-file definition, 137 of 142 ZKK codes are not HKK prefixes. The 137
include the whole `200`–`299` block — 91 codes — plus `530`–`560`, `600`–`700`, `800`, `900` and the
`001`/`070`/`071`/`073`/`075`/`083`/`116`/`120`/`181` block. Conversely 20 live HKK prefixes
(`111, 112, 129, 130, 191, 310, 311, 312, 313, 320, 321, 322, 325, 326, 327, 328, 329, 333, 334,
338`) are not ZKK codes.

Under the 2022-workbook definition, 135 of 142 do not match. The seven that do are worth reporting
precisely because they are so few, and because the two lists do not even agree with each other: the
2022 workbook lists `114` and `330`, and the live HKK column never emits a code beginning `114` or
`330`; the live column emits `110` and `213`, which the 2022 workbook does not list. A claim that
ZKK "is" the HKK prefix therefore cannot be rescued by picking either list — the two candidate lists
disagree with each other, and ZKK matches neither of them beyond a handful of values.

**A related fact that matters for the HKK argument.** All 125 distinct HKK values on the price file
are exactly **four** characters, on all 536,854 rows — not five. There is no fifth character in this
file. So the earlier note's §9 framing of HKK as "prefix (three) + letter + a trailing digit meaning
sales status" is not a reading of the file at all: it is a reading of the 2022 workbook's layout
imposed on a file that does not have that layout. What the file actually holds is 125 four-character
codes, which is why the rebuttal's HKK row measures four characters and why `1114` cannot exist as a
five-character status code — `1114` would be the four-character code `111` + `4`, and the file has
no such value.

**One correction to the rebuttal's own arithmetic.** The rebuttal's `GPT_REVIEW` §6 item 2 says
5 of 24 prefixes match, and lists the five as `113, 114, 211, 331, 332`. The count is right for the
live file; the list is not, and it mixes the two definitions. `114` and `211` are 2022-workbook
prefixes that never appear in the live HKK column, and the live-only matches `110` and `213` are
missing from the list. The 2022 workbook also has 27 clean three-digit prefixes, not 24. Correct
composition: **5 against the live column** (`110, 113, 213, 331, 332`), **7 against the 2022
workbook** (`113, 114, 115, 211, 330, 331, 332`).

**Verdict: corrected, and the claim is false.** The ZKK code is not the HKK prefix. It shares five
values with the live HKK file out of 142, which is a coincidence of numeric ranges, not an identity.
The earlier note's own supporting examples — it listed `123`, `133`, `310`, `311`, `312`, `313`,
`319`, `320`, `330`, `331`–`339` as "matching" — are mostly wrong: `310`–`313`, `319`, `320`, `333`,
`334`, `338` appear as HKK prefixes but not as ZKK codes, and `123`, `133`, `330`, `335`–`337`,
`339` appear in the 2022 workbook but not in the live file.

---

## Claim 2 — ZKK determines the price class

**Method.** Full pass over `【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912` (the only
sheet in the workbook), filtering `ZKK == "114"`, counting both class columns independently. The
denominator is the count of rows with `ZKK == "114"` — **144,830**. Blank class cells are counted as
a bucket and reported, not dropped. I also recomputed the same thing from
`01_data\00_derived\jp_codes_cache_20260920.csv` as a second path, and the two agree to the row.

**The numbers.**

| Column | `XC` rows | Denominator | Match rate |
|---|---:|---:|---:|
| `New Part Class` | 112,095 | 144,830 | **77.40%** |
| `Current Part Class` | 112,087 | 144,830 | **77.39%** |
| `New Part Class`, blank class rows excluded | 112,095 | 144,041 | **77.82%** |

The blanks are 789 rows in `New Part Class` and 797 in `Current Part Class`. Even removing them
entirely leaves 77.82%, nowhere near 100%. The distribution tail is long: 26 distinct class values
appear on ZKK `114` rows, including `DD` (6,811), `XD` (6,678), `XF` (6,041), `EV` (2,959) and
`BP` (2,628).

**Where the "100%" likely came from.** `ZKK 114`'s single biggest class is `XC`, and `XC`'s biggest
band is class `C`. It is easy to read the dominant value off a top-N listing and write 100%. Also,
just **12 of the 142 ZKK codes genuinely sit in one class only**, and they total 139 rows out of
536,854 — the largest is `530` at 62 rows. So a claim of "100%" is true for 12 codes covering 0.03%
of the file, and false for `114`, which is the biggest code in the file.

**Verdict: corrected, and the claim is false.** "Dominant class `XC` at 77.4%" is the correct
statement. The earlier note had the dominant class right and the share wrong; the rebuttal's 77.4%
is exactly right on `New Part Class`.

---

## Claim 3 — HKK row counts

**Method.** Full pass over both candidate workbooks, counting the `HKK` column directly, no filter.

| File | Sheet | Rows | `1110` | Share | `1114` | Distinct HKK values |
|---|---|---:|---:|---:|---:|---:|
| `01_data\【CY2026Price Revison】PRICE CD.xlsx` | `PRICE CD 250912` | 536,854 | **458,368** | 85.38% | **0** | 125 |
| `01_data\PRICE CD 260910.xlsx` | `Sheet1` | 533,400 | — | — | — | — (no HKK column) |

`PRICE CD 260910.xlsx` has 13 columns — `Country of origin, Inventry code, GM Pno, Pno, New Pno,
Parts name, Base price, Model, QTY, Net weight, H/S code, FIGKEY, Class` — and carries **no HKK, ZKK,
ZUK or EPLE column at all**. So it cannot be the source of any HKK row count. Both published HKK
numbers must therefore come from the 2025 Japanese file, or from somewhere that is not in this
workspace.

**Neither published number reproduces on the named file.** `1110` is 458,368, not 491,294 — a gap of
32,926 rows. `1114` does not exist; the nearest thing is the trailing-digit-4 group, which is 2,100
rows across three codes (`3114` 2,094, `1124` 4, `1114` 0), and the earlier note's own §9 prose
describes `1114` as "Surcharge for VOR handling" while its own table gives 21,834 rows — the 2,100
is what the file actually holds, and 21,834 is 10.4× that.

**Where 491,294 and 21,834 come from: UNKNOWN.** I checked every plausible arithmetic route and none
reproduces them: not `111`-prefixed rows (478,244), not `1110` plus the trailing-4 rows (460,468),
not the whole of `01_data\HKK.xlsx` (its `HKK data` sheet has `1110` on 710,160 rows of 904,721, and
its `HKK2` sheet 819,945 of 893,773). The values exist in no file I opened. The earlier note's
corrections notice already documents one `read_only` handle that was never closed and produced
partial counts. I could not prove that is what happened here, but the failure mode is the same in
shape: a count that is too high for a value and non-zero for a value that does not exist looks like
a mis-scoped read, not a real measurement.

**Verdict: corrected, and the claim is false.** Correct per file: on
`【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912`, `1110` is **458,368** (85.38%) and
`1114` is **0**. `PRICE CD 260910.xlsx` cannot be cited for HKK at all. The rebuttal's 458,368 and
its "no `1114`" are both correct.

---

## Claim 4 — the purity metric does not measure what it claims

**Method.** I reproduced the benchmark's own computation from its script
(`01_data\91_build\benchmark_classification_systems_20260920.py`, `leading_noun` on
`spine["desc"]`, blanks included as a bucket) and then re-measured the same systems four other ways,
on the same common base (139,524 PNs, €46,183,084, 88.11% of the book).

**The numbers, all on the same base.**

| System | Benchmark column (spine description, blanks as a bucket) | Japanese description, blanks as a bucket | Spine description, blanks excluded, denominator = all rows | Spine description, blanks excluded, denominator = non-blank rows |
|---|---:|---:|---:|---:|
| ZKK | 82.59% | **12.32%** | 1.48% | 8.50% |
| ZUK | 82.60% | 12.85% | 1.51% | 8.68% |
| HKK | 82.59% | 16.28% | 2.55% | 14.62% |
| AIM L1 | 86.18% | 8.21% | 3.84% | 22.04% |
| AIM L1>L2 | 88.83% | 10.94% | 6.49% | 37.27% |

The mechanism is exactly as the rebuttal describes. The spine's `description` is blank on 139,310
of 165,213 rows (84.32% of the spine) and on 115,228 of the 139,524 rows in the common base —
**82.59%**, the identical number the benchmark prints as "purity". Blanks are identical strings, so
they coalesce into one giant "noun" per code and the purity score becomes, to the first decimal
place, the blank share.

The rebuttal's 82.59% and 12.32% both reproduce exactly. Two smaller numbers in the rebuttal's
§2.5 do not: it gives AIM L1>L2 as 88.83%, and the benchmark file and my recompute both give
**88.77%**. And its claim that "82.59%" is the blank share is right for ZKK, ZUK and HKK — all
three land on the same blank share, which is itself the tell: three different systems scoring an
identical 82.59% cannot be measuring how well they classify.

**Is the metric meaningful as built? No.** It is a measure of how much of the description field is
missing, and because the missing part is common to the whole base it moves all systems toward the
same number. The two rows that escape it are the AIM rows, and they escape only because AIM's own
labels were partly derived from the description in the first place — which makes the comparison
circular in AIM's favour.

**What a corrected metric needs.**

1. **A description field that is complete on the rows measured.** The Japanese `Parts name` is
   100% filled on all 536,854 rows and 0% blank on the common base. It is the only field on disk
   that can carry this metric.
2. **The denominator named.** "Blanks excluded, over all labelled rows" is the honest form, because
   it does not let a system with many blanks hide behind them. On that definition the ranking is
   ZKK 12.32%, ZUK 12.85%, HKK 16.28% — and it reverses the benchmark: the Japanese codes look worse
   than the 82.59% suggested, and the systems with more blank rows inside each code looked "pure"
   precisely because of the blanks.
3. **A floor against chance.** Purity favours coarse systems by construction — a system with one
   code scores 100%. Any corrected metric needs the code count beside it, or a normalised score such
   as (observed purity − 1/n_codes) ÷ (1 − 1/n_codes). On the Japanese description, ZKK at 12.32%
   with 132 codes and HKK at 16.28% with 72 codes are not comparable as raw percentages.
4. **Row-weighted and euro-weighted both shown.** They differ a lot. Euro-weighted purity on the
   non-blank spine description is ZKK 17.25%, ZUK 20.03%, HKK 30.20%, AIM L1 33.25%, AIM L1>L2
   66.42% — i.e. on money the AIM L1>L2 pair looks genuinely better, which the row-counted benchmark
   column could not show.

**Verdict: the rebuttal is right and the published column is not usable.** No number in the
benchmark's `leading_noun_purity_pct` column should be quoted. The note
`CLASS_PRICE_CLASS_CONCENTRATION_2026-09-20.md` §7 already flags this in its own limits section,
which is the right handling.

---

## Claim 5 — ZUK versus HKK overlap

**Method.** Row-level comparison of the `ZUK` and `HKK` columns on all 536,854 rows, both at code
level and at the first two characters, plus a chance-agreement baseline computed from each column's
own marginal distribution. Source: `01_data\00_derived\jp_codes_cache_20260920.csv`, which I verified
against the workbook pass — its ZKK and HKK distributions match the workbook to the row.

**The numbers.**

| Comparison | Result |
|---|---|
| ZUK values (359) that equal an HKK value (125) | **0** |
| ZUK values that equal a ZKK value | **0** |
| ZUK first three characters that equal a ZKK code | **0** |
| Rows where ZUK and HKK share the first two characters | **520,152 of 536,854 = 96.89%** |
| Same, expected if the two columns were independent | **504,225 = 93.92%** |
| Rows where the two are equal at any prefix length | 0 |

**Reading it.** The "heavy overlap" argument is built on the leading pair, and the leading pair is
where it falls apart. ZUK leads with `11` on 520,189 rows and `13` on 15,445; HKK leads with `11` on
520,372 rows and `31` on 15,557. The joint table is almost entirely the diagonal cell
(`11`,`11`) = 520,149 rows. That is not agreement — it is two columns that each put ~97% of the file
in one bucket. The chance baseline is 93.92%, so the observed 96.89% is about three points above
what independence predicts. And wherever the columns actually separate, they separate
systematically: ZUK's second-largest group is `13` and HKK's is `31`, and those two never coincide
(joint `13`,`31` = 15,399; joint `13`,`13` = 0). Against the 2022 HKK workbook there is also no
contact: no ZUK first-three value matches any of the 27 prefixes there.

**Verdict: measured, and the overlap argument is not supported.** ZUK and HKK touch at no code
value at all. The 96.89% leading-pair agreement is a property of both columns being dominated by
one family of codes, not evidence that they carry the same information. If anything the measurement
supports the opposite of the argument: it shows ZUK has no code-level relationship to HKK or ZKK,
which is what the original note claimed when it called ZUK "a separate axis". What that note got
wrong is a different thing — it then asserted flatly that **nothing** in the files says what ZUK is
for. The structure I measured (fixed `DDCDD` shape, only `A`–`G` ever in the middle position, 359
values) is compatible with an option/applicability code, and `11`/`13` leading pairs against 520,189
and 15,445 rows is a model-family split. But that is a structural inference, not a dictionary, and
the meaning of ZUK remains **UNKNOWN**.

---

## Claim 6 — consistency with the concurrent class note

The other worker's note exists: `01_data\90_INBOX\CLASS_PRICE_CLASS_CONCENTRATION_2026-09-20.md`,
written 09:29:50 today. I did not duplicate its work. I checked its class figures and its fits-rule
buckets against my own independent measurements.

**Reproduced exactly.** Its Japan-file `New Part Class` distribution — `XC` 382,000, `XD` 26,633,
`EV` 24,682, `DD` 24,557, `XF` 20,071, `XM` 14,818, `BP` 9,379, `VV` 6,124, `XV` 4,212, blank 4,095,
`C` 3,145 — matches my independent pass row for row. Its "40 distinct codes" is correct: 39 non-blank
plus one blank bucket. Its entire fits-rule breakdown reconciles exactly, and I checked every part of
it:

| Bucket in its §2 | Codes | Rows | My count |
|---|---:|---:|---:|
| 19 two-letter codes that fit the second-character rule | 19 | 527,743 | 527,743 |
| 2 single-letter codes already equal to their class (`C`, `J`) | 2 | 3,973 | 3,973 |
| 4 two-letter codes with no class in our billed book (`RY`, `ST`, `EC`, `DZ`) | 4 | 952 | 952 |
| 1 single letter that is not a class (`X`) | 1 | 35 | 35 |
| 13 codes absent from our billed book | 13 | 56 | 56 |
| blank | — | 4,095 | 4,095 |
| **total** | | **536,854** | **536,854** |

Its `price_class_iml` distribution for the billed book (C €24,090,144 · V €7,243,684 · D €6,244,376 ·
F €5,665,598 · P €3,265,777 · M €1,247,376 · J €296,411 · T €59,173; blank €4,301,869) matches mine
to the euro, and its headline "class C is 45.96% of the whole book and 50.07% of priced euro" is
correct. Its 100-ZKK-codes-in-C figure reproduces (I measure 100). Its "107 of the 142 ZKK codes have
class C as their dominant class" reproduces (I measure 107). Its "12 sit in exactly one class"
reproduces (I measure 12). Its 13-codes-absent list is consistent with mine: those 13 carry no
`jp_class_new` row on the billed spine at all, which is exactly what "absent" should mean.

**Where I was wrong, and I am saying so because it was my error.** My first draft of this audit
listed two disagreements. Both were misreadings on my part and both are withdrawn.

1. I claimed the note put `EC` in the wrong bucket, and that its 56-row absent total was therefore
   wrong. That was my error. The note lists `EC` in the "4 two-letter codes that carry no class in
   our billed book" group, at 50 rows, alongside `RY` 796, `ST` 101 and `DZ` 5 — 952 rows — and its
   separate 13-code/56-row group is `CM, JJ, CP, E, F, QC, B, G, W, DB, CD, D, GD`, which contains no
   `EC` at all. Both groups are correct as written. I had read `EC` into the wrong list.
2. I claimed its "18 of the 40 do not fit the rule" contradicted its own breakdown. It does not:
   19 + 2 + 4 + 1 + 13 = 39 non-blank codes, of which 19 + 2 = 21 fit, leaving 18 that do not, plus
   the blank bucket. The arithmetic is right and my reconciliation of it was wrong.

**Two wordings worth tightening, neither an error.** Its §2 says the distribution has "40 distinct
codes"; strictly it has 39 non-blank values plus a blank bucket, which is 40 slots. The note's own
fits-rule paragraph then counts the 39 non-blank codes correctly, so this is a labelling point, not a
number. And its §4 sentence "of 142 ZKK codes on `PRICE CD 250912`, only 12 sit in exactly one class;
the other 130 span several" is true on the Japan file, but 7 of those 12 single-class codes do not
appear on our billed book at all, so only 5 of them are visible in its own Basis 3. Worth one clause,
not a correction.

**A file that moved under this audit.** Both the JSON and the CSV the benchmark note "repaired"
(`_classification_benchmark_20260920.json`, mtime 09:26:44) were rewritten while I was measuring.
The `leading_noun_purity_pct` values are unchanged in the new version — ZKK 82.59, AIM L1>L2 88.77 —
so claim 4 stands either way, and I re-read the file after the change to confirm it. Its §6 claim
that "recomputing the 15-level row from `L1 Category` reproduces 20.09 exactly" is consistent with
what the file now holds (20.09, 37.78), and that 20.09 also matches the untouched readable report
`CLASSIFICATION_BENCHMARK_2026-09-20.md`.

---

## What is still UNKNOWN, and why

- **The origin of 491,294 and 21,834.** They appear in no file on this machine that carries HKK data.
  I could not reconstruct them from any prefix, suffix or sheet combination. UNKNOWN.
- **The origin of "no `114`" in the live HKK column.** The 2022 workbook lists prefix `114` and the
  live file never emits a code starting `114`. Why the code was dropped between the glossary and the
  price file is UNKNOWN; no document in the workspace explains it.
- **What ZUK means.** Structure is proven (359 values, `DDCDD`, middle letter only `A`–`G`). Meaning
  is not. No published Isuzu description of ZUK exists in this workspace. UNKNOWN.
- **What ZKK means, in business words.** We know it is 3 characters, filled on every row, and
  correlates with price class. We do not hold a naming sheet for it. UNKNOWN.
- **Whether the 12 single-class ZKK codes are single-class by design or by low volume.** All 12
  total 139 rows; the largest is 62 rows. At that size, "single class" may be chance. UNKNOWN.
- **The two minor claim-6 points above.** Both are wording in the concurrent note — the "40 distinct
  codes" label and the "other 130" clause in §4 — and neither changes a number. I flag them so the
  note's author can tighten them, not as disagreements.
- **Whether `PRICE CD 260910.xlsx` should carry the Japanese codes.** It has 13 columns and none of
  them; the 2025 file has 12 columns and five of them. Whether that is a deliberate narrowing or a
  lost export is UNKNOWN. Note also that the earlier notes disagree with each other on this file's
  column count (13 vs 14) and on the 2025 file's row count (536,854 vs 533,400). I measured 13
  columns and 533,400 data rows on `Sheet1`; the 533,400 belongs to `PRICE CD 260910.xlsx`, and the
  536,854 belongs to `【CY2026Price Revison】PRICE CD.xlsx`. Any sentence that puts 533,400 rows
  beside the ZKK figures is mixing the two files.

---

## What this means for the ZKK decision

The corrections cut one way. Every claim that ZKK is *more* than a catalogue-and-price bucket has
now failed a re-measurement: it does not reproduce the HKK prefix list, it does not determine the
price class (77.4%, not 100%), and its two biggest codes span 26 and 25 different classes
respectively. The "dominant class 100%" table in §10.3 of the earlier note should not be shown to
anyone in its current form — three of its five rows are wrong.

What survives is the opposite conclusion, and it is now on much firmer ground than when it was
first written. ZKK `114` — 144,830 rows, 27% of the catalogue — holds 1,901 distinct leading part
nouns, its four largest being `HARNESS` 15,895, `PIPE` 11,432, `CONTROL UNIT` 7,982 and `BRACKET`
7,670, together 30% of the code. Only 12 of 142 ZKK codes sit in one class, and they cover 139 rows.
The purity column that made ZKK look description-pure at 82.59% was measuring blanks all along; on
the Japanese description the same code scores 12.32%.

So: **safe to act on.** ZKK is a catalogue-and-price label, filled on every row, that can be carried
beside the functional family as an attribute. It is not a replacement for a functional family axis,
and no chart should be cut on it. The column request to Japan is a column request, not a
re-categorisation, and that conclusion does not depend on any of the numbers above. ZUK is a
separate, well-formed code with no documented meaning — carry it, do not chart on it, and do not
claim to know what it means.

**Not safe to act on.** Anything that says ZKK *determines* the price class, or that its codes are
the HKK prefixes. Any use of the benchmark's purity column. Any HKK row count taken from
`HKK_SYSTEM_REVIEW_2026-09-20.md` §9 until it is corrected to 458,368 / 0 — and note that the 32,926
row gap the rebuttal could not explain is now explained to the extent it can be: the numbers in that
section do not come from the file the section names.

---

## Corrections to list (do not apply — listed only)

### `01_data\90_INBOX\HKK_SYSTEM_REVIEW_2026-09-20.md`

**1. §9, the HKK row table.**

> `| `1110` | 491,294 | prefix 111, letter 0, status 0 — the normal part |`
> `| `1114` | 21,834 | **status 4 = surcharge.** Descriptions are "Surcharge for VOR handling", "Freight charge", "Surcharge for Parts Return" |`
> `| `111D` | 2,545 | prefix 111, **letter D = "Cab"**, status 0 |`
> `| `111K` | 581 | prefix 111, letter K = "Liner, Liner Kit" |`

Replace with the values measured on the same file and sheet:

> `| `1110` | 458,368 | prefix 111, letter 0, status 0 — the normal part (85.38% of the file) |`
> `| `1114` | **0** | **does not occur on this sheet.** The trailing-digit-4 group is 2,100 rows in total, almost all `3114` (2,094 rows) |`
> `| `111D` | 6,120 | prefix 111, **letter D = "Cab"**, status 0 |`
> `| `111K` | 3,626 | prefix 111, letter K = "Liner, Liner Kit" |`

**2. §9, the sentence directly under that table.**

> "This is why HKK looked like a warehouse code in the first pass: at 91.5% of the catalogue it *is* one row, `1110`."

Replace with: "This is why HKK looked like a warehouse code in the first pass: at **85.4%** of the
catalogue it *is* one row, `1110`." (91.5% is 491,294/536,854; the measured share of the same file
is 458,368/536,854 = 85.38%.)

**3. §10.1, the prefix-equality claim.**

> "Its shape matches the HKK 2022 sheet's own opening blocks exactly: `113`, `114`, `118`, `211`, `310`, `311`, `312`, `313`, `319`, `133`, `331`–`339`, `123`, `320`. The ZKK code *is* the HKK prefix. HKK carries the prefix plus a route letter and a status flag; ZKK carries the category."

Replace with: "Its shape **resembles** the HKK 2022 sheet's blocks but is not the same list. Of the
142 ZKK codes, **5** are also three-character prefixes in the live HKK column (`110`, `113`, `213`,
`331`, `332`) and **7** are prefixes on the 2022 HKK workbook (`113`, `114`, `115`, `211`, `330`,
`331`, `332`); no ZKK value equals any full HKK value. ZKK and the HKK prefix are two different
code lists that share a few numeric blocks."

**4. §10.3, the table heading and its rows.**

> "Measured on all 536,854 rows, the dominant `New Part Class` of each code:" … "`ZKK 114` | 144,830 | `XC` | 100%" … "`ZKK 070` | 14,612 | `XM` | 100%" … "`ZUK 11G00` | 265,999 | `XC` | 100%" … "`ZUK 13G00` | 13,150 | `EV` | 95%" … "`ZUK 11F91` | 6,977 | `RY` | 100%"

Replace the heading with "the class the largest share of each code's rows falls in" and the rows
with the measured shares:

> `| ZKK 114 | 144,830 | XC | 77.4% |`
> `| ZKK 070 | 14,612 | XM | 68.9% |`
> `| ZUK 11G00 | 265,999 | XC | 78.4% |`
> `| ZUK 13G00 | 13,150 | XM | 80.6% |`
> `| ZUK 11F91 | 6,977 | XC | 73.1% |`

Three of the five codes have the wrong dominant class as well as the wrong share: `ZUK 13G00` is
dominantly `XM`, not `EV`, and `ZUK 11F91` is dominantly `XC`, not `RY`.

**5. §10.1, the purity sentences.**

> "Tested on 536,854 rows, grouping each ZKK code by the leading noun of the part description: only **1** of 142 codes is description-pure, and row-weighted purity is **17.5%**."

Replace with: "**8** of 142 codes have a single leading noun on the Japanese description, and
row-weighted purity is **17.74%** on the Japanese description — or **95.47%** if the leading noun is
taken from our own spine description, which is itself the defect: our description field is blank on
most rows, and the blanks inflate any noun-purity score. Use the Japanese description, and treat
17.74% as the honest figure."

**6. §10.1, the "1,901 leading nouns" sentence survives — no edit.** It is correct as written. I
re-measured it on the same file: ZKK `114` holds exactly 1,901 distinct leading nouns, top four
`HARNESS` 15,895, `PIPE` 11,432, `CONTROL UNIT` 7,982, `BRACKET` 7,670.

**7. §9 title and the corrections notice at the top of the file — "five characters".**

> "**§1 says "the letter is the only part-family signal". That is wrong.** HKK is five characters, not four: prefix (three) + letter + a **trailing digit meaning "sales status"**…"
> `# 9. HKK decoded properly — five characters, and the fifth is not a family`

Both should read **four** characters. All 125 distinct HKK values on `PRICE CD 250912` are exactly
four characters, on all 536,854 rows, stored as text. The longest HKK value in the file is four
characters and no five-character value exists. Suggested replacement for the notice: "HKK is four
characters: a three-digit prefix plus one letter-or-digit slot character that carries different
meanings under different prefixes. It is not uniformly a sales-status flag." And for the §9 title:
"# 9. HKK decoded properly — four characters, and the fourth means different things under different
prefixes". This also removes the need for the §2.2 argument in `GPT_REVIEW_ZKK_ZUK_and_AIM_v2_20260920.md`
to explain why the "fifth character" is not uniform — there is no fifth character to explain.

**8. §10.2, the ZUK leading-characters argument.**

> "Its leading characters are **not** any HKK or ZKK code (`11G00`, `11G22`, `13G00` — the two-digit numbers `11` and `13` are not in the HKK family list). It is a separate option/accessory axis."

The first sentence should be kept, but add the caveat so nobody later "discovers" an overlap that is
not there: "Add: measured at code level, **0 of 359** ZUK values equals any HKK value; the two
columns share their leading two characters on 96.89% of rows against 93.92% expected by chance,
which reflects both columns being dominated by one code family rather than any shared meaning."

**9. §12, item 3.**

> "**Drop `HKK` from the plan.** At 91.5% `1110` and with the family content living in 125 route codes, it adds nothing ZKK does not already carry."

Replace "91.5%" with "**85.4%**". The recommendation stands.

**10. §13 and §9 provenance.**

> "Live confirmation, `【CY2026Price Revison】PRICE CD.xlsx` (536,854 rows, sheet `PRICE CD 250912`, from ISZJ, September 2025), HKK column, 125 distinct values"

This is correct and needs no edit — the 125 distinct values and the 536,854 row count both
reproduce. Worth noting because it shows the HKK column was read correctly in every respect except
the per-value counts.

### `01_data\90_INBOX\GPT_REVIEW_ZKK_ZUK_and_AIM_v2_20260920.md`

**1. §0 item 4, first sub-claim.**

> "ZKK's code list does **not** equal the HKK prefix list (5 of 142 match, not all of them)"

Keep the count of 5, but state which list: "…does not equal the HKK prefix list: **5 of 142** ZKK
codes are also three-character prefixes in the live HKK column (`110`, `113`, `213`, `331`, `332`),
and 0 of 142 equal any full HKK value."

**2. §2.2, the "fifth character is not a uniform sales-status flag" argument.**

> "**But the fifth character is not a uniform sales-status flag.** The earlier note read the trailing digit as status…" … "So the fifth character is a **slot label that means different things under different prefixes**."

Correct in substance but built on a non-existent fifth character. All 125 distinct HKK values on
`PRICE CD 250912` are exactly **four** characters on all 536,854 rows; there is no fifth character
anywhere in the file. Rewrite the section against four characters: "HKK is a three-digit prefix plus
one **fourth** character (letter or digit). That fourth character means different things under
different prefixes. A status reading is safe under prefix `111`; it is unsafe everywhere else.
Which prefixes it is valid for is NOT fully decoded." Add the supporting count: the `3114` case is
2,094 rows, and the digit-4 group in total is 2,100 rows.

**3. §6 item 2, the composition of the five.**

> "The 2022 HKK workbook lists 24 prefixes across its three sheets; ZKK shares **5** with it (`113`, `114`, `211`, `331`, `332`) and not the other 19."

Two errors. Replace with: "The 2022 HKK workbook lists **27** three-digit prefixes across its three
sheets; ZKK shares **7** with it (`113`, `114`, `115`, `211`, `330`, `331`, `332`) and not the other
20. Against the 25 three-character prefixes that appear in the live HKK column, ZKK shares **5**
(`110`, `113`, `213`, `331`, `332`)."

**4. §6 item 7.**

> "7. **The HKK row counts.** 458,368 versus 491,294 for `1110`, and 0 versus 21,834 for `1114`, on the same file."

This is correct on both of its own numbers. Add the resolution: "Settled by an independent full
pass: 458,368 and 0 are correct on `PRICE CD 250912`. `PRICE CD 260910.xlsx` has no HKK column and
cannot be the source of any HKK count. The origin of 491,294 and 21,834 is **UNKNOWN** — they match
no file on this machine."

**5. §2.5, the AIM L1>L2 purity figure.**

> "| AIM L1>L2 | 88.83% | **10.94%** | 82.59% |"

Replace 88.83% with **88.77%** (the value in the benchmark file and in my recompute). The 10.94%
is correct.

**6. §2.5, the closing sentence.**

> "Note also that purity favours coarse systems by construction — a system with one code scores 100%."

Correct; add the consequence so the metric is not half-corrected: "…a system with one code scores
100%. Any corrected metric must therefore state the code count beside the purity, or normalise it;
and the row-weighted and euro-weighted versions should both be shown, because they rank the systems
differently."

**7. §3.5, the column-count sentence.**

> "so the complete codes are one file-generation behind the price file we are actually working from, and the column set is not guaranteed to be stable." … "`01_data\PRICE CD 260910.xlsx`, has 14 columns by our count"

Replace 14 with **13**, and list them: `Country of origin, Inventry code, GM Pno, Pno, New Pno,
Parts name, Base price, Model, QTY, Net weight, H/S code, FIGKEY, Class`. State that the file's
row count is **533,400** on `Sheet1`, so any sentence quoting 533,400 beside the ZKK/ZUK figures is
mixing this file with the 536,854-row 2025 file.

**8. §8, the "stale column count" bullet.**

> "The stale column count for the current master price file is unresolved. `HKK_SYSTEM_REVIEW_2026-09-20.md` §4 says 533,400 rows and §10 says 13 columns; the earlier GPT brief says 533,400."

Now resolved: `PRICE CD 260910.xlsx`, sheet `Sheet1`, is **533,400 data rows and 13 columns**.
`§4`'s 533,400 and `§10`'s 13 are both correct and refer to the same file; the 536,854 belongs to
`【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912`. Replace the bullet with that.

**9. §0 item 4, fifth sub-claim — no edit needed.** "the benchmark's description-purity column is
measuring blank descriptions rather than classification quality" is confirmed, with the mechanism
and the corrected figures. Its "see §2.5–§2.7 and §3.2" cross-reference is valid.

---

## Provenance

| Item | Path | Sheet / column |
|---|---|---|
| Japanese price CD, Sep 2025 | `01_data\【CY2026Price Revison】PRICE CD.xlsx` | `PRICE CD 250912`; `Pno, Parts name, New Part Class, Current Part Class, EPLE, FIGKEY, Example Model, ZUK, HKK, ZKK` — 536,854 rows, one sheet |
| Current master price file | `01_data\PRICE CD 260910.xlsx` | `Sheet1`; 13 columns, no HKK/ZKK/ZUK/EPLE — 533,400 rows |
| 2022 HKK workbook | `01_data\HKK Code 20221028.xlsx` | `Parts`, `Accessories`, `Lubricant` — 27 three-digit prefixes |
| Extracted code map | `01_data\00_derived\jp_codes_cache_20260920.csv` | 536,854 rows; verified equal to the workbook pass for ZKK and HKK |
| Live spine | `01_data\00_derived\aim_master_v2.csv` | 165,213 rows; `jp_zkk, jp_zuk, jp_hkk, jp_class_new, jp_class_current, price_class_iml, l12m_billed_eur, description` |
| Benchmark (repaired during this audit) | `01_data\90_INBOX\_classification_benchmark_20260920.json` | mtime 2026-09-20 09:26:44 |
| Benchmark script | `01_data\91_build\benchmark_classification_systems_20260920.py` | `leading_noun()`, `measure()` |
| Concurrent class note | `01_data\90_INBOX\CLASS_PRICE_CLASS_CONCENTRATION_2026-09-20.md` | written 09:29:50 |

No file was modified in producing this audit. The only file written is this one. No email was sent
or drafted, and nothing was rebuilt.


---

## Part V — ZKK code dictionary (code-level fragmentation)

# ZKK code dictionary — what the 142 Japanese catalogue codes actually hold

**Date:** 2026-09-20 · **Internal / private** · read-only measurement, no rebuild, no mail
**Question:** Jerome has to decide whether ZKK earns a permanent column on the spine beside AIM,
or whether it is too coarse to be worth carrying. Nobody had established what the 142 ZKK codes
actually mean. This document closes that gap.

---

## Status — 2026-09-20

**This document is the authority for the code-level facts on ZKK and HKK.** Where it disagrees with
`_classification_benchmark_20260920.json` or with `CLASSIFICATION_BENCHMARK_2026-09-20.md`, this
document wins. The benchmark's `leading_noun_purity_pct` column is a blank-description share and must
not be quoted anywhere.

**Independently re-measured on 2026-09-20** (script
`01_data\91_build\zkk_independent_verify_20260920.py`, written from scratch against
`01_data\00_derived\aim_master_v2.csv` and `01_data\00_derived\jp_codes_cache_20260920.csv`).
Everything below reproduced unless marked:

| Figure in this document | Independent result | Status |
|---|---|---|
| ZKK `275` = €21,597,705, 19,874 part numbers, **415** distinct leading nouns | identical to the euro and to the count | **Confirmed** |
| €46.18M base, 139,524 part numbers, 88.11% of the billed book | identical | **Confirmed** |
| join of spine `jp_zkk` to cache `zkk`: 139,524 compared, 0 disagreements | identical | **Confirmed** |
| 1 coherent code of 51 judgeable (`113`, 262 part numbers, 83.2% `FRAME ASM`) | identical | **Confirmed** |
| 46 fragmented codes holding €45,197,049 = **97.86%** of the base | identical | **Confirmed** |
| 15 codes at 80%, 89 below 40% holding **99.67%** of the base | 15 and 89, holding **99.67%** | **Confirmed** |
| 0 of 142 ZKK values equal a full HKK value; 5 of 142 equal a 3-character HKK prefix | identical (`110`, `113`, `213`, `331`, `332`) | **Confirmed** |
| HKK `1110` = 116,816 part numbers, 83.7% of base rows, 76.8% of base euro, top noun 5.5% | identical | **Confirmed** |
| HKK row purity 16.28% vs ZKK 12.32% on the billed base | **16.29%** vs **12.33%** | Confirmed; each differs by 0.01 point, which is rounding and the parenthesis rule, not a disagreement |
| HKK is cleaner than ZKK outside `1110` | confirmed — 71.67% purity on the whole non-`1110` slice | **Confirmed** |
| ZKK `275` holds ≥1% of **25** AIM families | 25 on `aim_l1_fixed`; **24** on `aim_l1` alone | **Confirmed on the column this document states;** the count moves with the column, see the note below |
| Japanese description blank on exactly 0 of the 139,524 base rows | 0 on the base; 2 rows of the 536,854-row file carry a blank leading noun | Confirmed in effect |
| **28 of the 39** HKK codes at ≥20 part numbers carry the part type the 2022 workbook names | denominator **39 of 39** matches; numerator **12 to 16 of 39 (31–41%)** depending on the match rule | **Disputed — see the note below** |

**Two labelling points that are not disputes but will mislead if the wording is copied elsewhere.**

1. **"46.77% of the billed book" is 46.77% of the €46.18M base, not of the €52.41M billed book.**
   On the total billed book, ZKK `275` is **41.21%** (€21,597,705 of €52,414,407.82). This document
   defines "the book" as the base inside its own header, and is consistent with itself; the shorter
   phrase should not be lifted out of this file without the definition.
2. **The "25 AIM families" count names the column it used.** It is `aim_l1_fixed` falling back to
   `aim_l1`, as section 4 states. On `aim_l1` alone the count is 24, because the `Lighting` family
   falls from 69.1% to 0.0% — `Lighting` has no rows in `aim_l1` at all on the billed base. Of the
   25, two families (`Logistics Packaging` at €69, `(blank)` at €4,971) hold under €5,000 of base
   euro, so the count of 25 includes cells that pass a 1% test without carrying commercial weight.

**The disputed figure, stated plainly.** Section 5 says "Of the 39 four-character HKK codes that hold
at least 20 part numbers on our billed book, **28 carry the part type the workbook names — 72%**".
I reproduce the denominator and not the numerator. Extracting the same 2022 workbook and joining it to
the same 139,524-part-number base gives **39** HKK codes at ≥20 part numbers with a workbook name —
the denominator is exact. On the numerator I get four different answers depending on the match rule,
and none reaches 28:

| Match rule | Codes matching |
|---|---:|
| Name appears in the code's most-common noun, euro-weighted | **12 of 39 (31%)** |
| Name appears in the code's most-common noun, row-weighted | **13 of 39 (33%)** |
| Name appears anywhere among the code's nouns, any frequency | **14 of 39 (36%)** |
| First word of the name equals the code's own top noun (strictest reading) | **16 of 39 (41%)** |

Every example this document quotes is real and reproduces: `111D` named `Cab` is 100% `CAB ASM`;
`111X` named `Door` is 100% `DOOR ASM`; `113A` named `Silencer` is 96.1% `SILENCER ASM`; `113F` named
`Rear Combi Lamp` is 100% `LAMP ASM`; `113B` named `Oil Seal` is 100% `SEAL`; `313A` named `Spring` is
86.7% `SPRING ASM`. Those are six of the roughly fifteen codes that do line up, which is why the
claim reads true. **The 72% is not reproducible; the honest range is 31% to 41%.** The direction of
the finding — that HKK's fourth character carries real part meaning — survives on either number.
Both are left in place here; do not quote the 72% until the two passes are reconciled.
Source: `01_data\91_build\zkk_independent_verify_20260920.py`.

**Two terms, explained once.**
The **price class** is the band that sets the margin we apply to a part. Japan assigns it and it
arrives on the price file next to the base price. It is a margin band, not a part family — class C
carries a 53% margin, class V a 45% margin. It says what we earn on a part, not what the part is.
The **leading noun** is the first word of the Japanese part description, taken before the first
semicolon or comma. It is the closest thing to a part type that the Japanese file gives us.

**Sources, and the exact column used for each number.**

| Number | File | Column |
|---|---|---|
| Per-row Japanese codes and part names | `01_data\00_derived\jp_codes_cache_20260920.csv` | `zkk`, `hkk`, `zuk`, `jp_description` |
| Billed euro, AIM family, price class | `01_data\00_derived\aim_master_v2.csv` | `l12m_billed_eur`, `aim_l1_fixed`, `aim_l2_fixed`, `jp_zkk` |
| 2022 code names | `01_data\HKK Code 20221028.xlsx` | sheets `Parts`, `Accessories`, `Lubricant` |
| The underlying source of both | `01_data\【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912` | `ZKK`, `HKK`, `ZUK`, `Parts name` |

**The base every figure below sits on.** `jp_codes_cache_20260920.csv` holds 536,854 rows and
536,854 distinct part numbers, so each part number carries exactly one ZKK value. Joined to
`aim_master_v2.csv`, **139,524 part numbers carry both a ZKK code and billed euro, worth
€46,183,083.72 = 88.11% of the €52,414,407.82 book.** Where a share of "the book" is quoted below
it is a share of that €46.18M base, and where a share of the catalogue is quoted it is from the
536,854-row file. The two are never mixed.

*A note on the join.* The spine carries eight `jp_*` columns — `jp_zkk`, `jp_zuk`, `jp_hkk`,
`jp_eple`, `jp_fig_key`, `jp_class_new`, `jp_class_current`, `jp_code_source`. **It does not carry
a `jp_description` column.** The Japanese description therefore comes from the cache's
`jp_description`, which the cache built from the file's `Parts name`. To prove the euro join is
sound rather than rebuilt, `jp_zkk` on the spine was compared with `zkk` in the cache for the same
part number: **139,524 of 139,524 agree, zero disagreements.** The cache's Japanese description is
100% filled on the base — exactly 0 blank rows.

---

## Verdict

**ZKK is a mixed bucket at the level that decides money, and it earns a place as a catalogue
attribute, not as an analysis axis.** Concretely: of the 51 ZKK codes large enough to judge (200 or
more part numbers), exactly **one** holds essentially a single kind of part (`113`, 262 part
numbers, 83.2% of them `FRAME ASM`). The other 50 are mixed. The 46 codes whose largest single
part type is under 40% of the code include **every ZKK code that carries real money** — they hold
**€45,197,049, or 97.86% of the €46.18M base.** ZKK `275` alone is €21,597,705, **46.77% of the
billed book**, and its largest part type is `HARNESS` at **13.7%**; it spans **415 distinct leading
nouns**. So ZKK is not a functional family and cannot be charted on. But it is filled on every row,
it is free to maintain, and the smaller codes do hold recognisable part types. Carry it beside AIM
as a Japan-assigned catalogue label — the same way `jp_class_new` and `jp_eple` are carried — and
keep the functional family as the axis. The decision does not depend on ZKK being coherent; it
depends on ZKK being **cheap and honest**, which it is.

---

## 1. The structural question, settled with numbers

**Is ZKK the parent of HKK, the child, a sibling, or unrelated?**

| Measurement | Result | Source |
|---|---:|---|
| Distinct HKK values in the file | **125** | `zkk`/`hkk` columns, all 536,854 rows |
| HKK value length | **exactly 4 characters on all 536,854 rows** — no fifth character anywhere | same |
| Distinct 3-character prefixes of HKK values | **25** | first 3 characters of `hkk` |
| HKK prefixes that are also a ZKK value | **5 of 142** → `110`, `113`, `213`, `331`, `332` | `zkk` vs `hkk[:3]` |
| **HKK full 4-character values that appear anywhere in ZKK** | **0** | `zkk` vs `hkk` |
| HKK prefixes that are **not** a ZKK value | **20** → `111`, `112`, `129`, `130`, `191`, `310`, `311`, `312`, `313`, `320`, `321`, `322`, `325`, `326`, `327`, `328`, `329`, `333`, `334`, `338` | same |
| ZKK value length | **exactly 3 characters on all 536,854 rows** | `zkk` |
| Distinct ZKK values | **142**, zero blanks | `zkk` |

Against the 2022 workbook `01_data\HKK Code 20221028.xlsx`, extracting every "three-digit number
followed by a single slot character" from its three sheets gives **26 prefixes** (Parts 13,
Accessories 2, Lubricant 11). **7 of the 142 ZKK values are among them — `113`, `114`, `115`,
`211`, `330`, `331`, `332`.** This is one fewer prefix than the earlier audit's 27; the difference
is a single code that sits on a summary line rather than in the block grid, and it does not touch
the overlap, which reproduces at 7 in both passes.

**The answer: neither parent nor child. They are unrelated code lists that occupy overlapping
numeric ranges.** The evidence is the two format tests. No ZKK value ever equals a full HKK value
— 0 of 142 — so ZKK is not a truncation of HKK. And truncating HKK to three characters matches only
5 of 142 ZKK values, while 20 of HKK's own 25 prefixes match nothing in ZKK at all. A parent would
contain its children's codes; a child would be built from its parent's codes; neither pattern holds.
What the two share is a numbering habit — both draw on the `110`–`339` range — not a hierarchy.
That the two candidate HKK lists disagree with each other (`114` and `330` appear in the 2022
workbook and never in the live column; `110` and `213` appear in the live column and not in the
workbook) is a second, independent reason not to read ZKK as derived from HKK.

One related structural fact, because it changes how HKK should be read: all 125 distinct HKK values
are **exactly four** characters on every row of the file. There is no trailing fifth status digit.

---

## 2. What each ZKK code holds — the full 142-row table

One row per ZKK code. **part numbers** and **EUR** are from the billed book (spine
`part_number` joined to `l12m_billed_eur`), so a code with no billed euro shows zero. **share** is
of the €46.18M base. The three noun columns are the three most common leading nouns of the
Japanese description inside that code, with each noun's share of the code's part numbers. A code
marked **\*** exists on the price file but never billed on our book, so its nouns are counted from
the 536,854-row file instead.

| ZKK | part numbers | EUR | share of book | top noun | share | 2nd noun | share | 3rd noun | share |
|---|---:|---:|---:|---|---:|---|---:|---|---:|
| `001` * | 0 | 0 | 0.00% | UOE&WEB P/C RIY | 60.0% | WEB P/C RIYOURY | 20.0% | HOROGRAM SEAL T | 20.0% |
| `070` | 1,862 | 509,959 | 1.10% | SPRING | 28.8% | GLASS | 17.2% | SPRING ASM | 15.9% |
| `071` | 40 | 17,258 | 0.04% | GLASS | 62.5% | SPRING | 25.0% | SPRING ASM | 12.5% |
| `073` * | 0 | 0 | 0.00% | BRACKET | 100.0% | — | — | — | — |
| `075` | 17 | 710 | 0.00% | FENDER | 94.1% | HOLDER | 5.9% | — | — |
| `083` * | 0 | 0 | 0.00% | HOSE | 50.0% | BRACKET ASM | 50.0% | — | — |
| `110` * | 0 | 0 | 0.00% | SPRING | 100.0% | — | — | — | — |
| `113` | 262 | 5,416 | 0.01% | FRAME ASM | 83.2% | PIPE | 5.0% | BODY ASM | 4.2% |
| `114` | 22,093 | 2,278,168 | 4.93% | GASKET SET | 4.5% | PIPE | 3.8% | HOSE | 3.2% |
| `115` | 60 | 64 | 0.00% | CABLE | 10.0% | SILENCER ASM | 8.3% | PIPE | 6.7% |
| `116` | 90 | 0 | 0.00% | PANEL | 31.1% | DOOR ASM | 17.8% | BRACKET | 16.7% |
| `120` | 5 | 6,043 | 0.01% | PUMP ASM | 100.0% | — | — | — | — |
| `181` | 29 | 979 | 0.00% | SUPPORT | 34.5% | PIN | 17.2% | BRACKET | 13.8% |
| `200` | 16,718 | 6,282,982 | 13.60% | GASKET SET | 18.3% | CONTROL UNIT | 7.4% | HARNESS | 2.6% |
| `201` | 401 | 1,317 | 0.00% | BOLT | 16.5% | GASKET | 9.0% | GEAR | 5.2% |
| `202` | 274 | 1,471 | 0.00% | BOLT | 44.9% | HEAD ASM | 4.7% | PIPE | 4.4% |
| `203` | 27 | 782 | 0.00% | BOLT | 40.7% | GASKET | 29.6% | BEARING | 11.1% |
| `206` | 3 | 322 | 0.00% | CAP | 33.3% | COUPLING | 33.3% | PIPE | 33.3% |
| `207` | 13 | 0 | 0.00% | PARTS KIT | 100.0% | — | — | — | — |
| `208` * | 0 | 0 | 0.00% | RETAINER | 100.0% | — | — | — | — |
| `209` | 14 | 653 | 0.00% | TANK | 42.9% | CLUTCH | 28.6% | VALVE KIT | 14.3% |
| `210` | 39 | 1,317 | 0.00% | LINER SET | 69.2% | COVER | 10.3% | BELT | 7.7% |
| `211` | 10 | 360 | 0.00% | GASKET | 50.0% | NUT | 50.0% | — | — |
| `212` | 36 | 280 | 0.00% | LINER SET | 22.2% | SEAL KIT | 19.4% | HOSE | 16.7% |
| `213` | 29 | 148 | 0.00% | PUMP ASM | 48.3% | BOLT | 10.3% | BULB ASM | 10.3% |
| `214` | 37 | 246 | 0.00% | CYLINDER ASM | 43.2% | SILENCER ASM | 43.2% | LEVER ASM | 8.1% |
| `215` | 32 | 0 | 0.00% | LINER SET | 59.4% | SWITCH | 12.5% | VALVE | 12.5% |
| `217` | 1 | 0 | 0.00% | REPAIR KIT | 100.0% | — | — | — | — |
| `220` | 120 | 6,643 | 0.01% | LINER SET | 20.8% | U-BOLT SET | 20.0% | ROD ASM | 7.5% |
| `221` | 14 | 87 | 0.00% | BUSHING | 28.6% | U-BOLT SET | 14.3% | BOLT | 14.3% |
| `222` | 320 | 75,068 | 0.16% | LINER SET | 19.4% | GEAR | 6.9% | BEARING | 5.3% |
| `223` | 45 | 514 | 0.00% | LINER | 22.2% | SILENCER ASM | 13.3% | ORNAMENT | 11.1% |
| `224` | 46 | 41 | 0.00% | RING | 52.2% | REPAIR KIT | 21.7% | PLUG | 4.3% |
| `225` | 668 | 6,442 | 0.01% | BOLT | 21.9% | GASKET SET | 13.6% | CLIP | 11.8% |
| `226` | 35 | 447 | 0.00% | GASKET SET | 42.9% | DRUM | 40.0% | JOINT ASM | 5.7% |
| `227` | 9 | 76 | 0.00% | SLEEVE | 55.6% | GASKET | 22.2% | SOLENOID | 22.2% |
| `228` | 18 | 8 | 0.00% | SHIM | 88.9% | CLIP | 5.6% | RETAINER | 5.6% |
| `229` | 18 | 91 | 0.00% | RING | 44.4% | CABLE | 16.7% | HOSE | 16.7% |
| `230` | 386 | 2,871 | 0.01% | SEAL | 7.3% | GASKET | 4.9% | NUT | 4.7% |
| `231` | 64 | 2,636 | 0.01% | NUT | 31.2% | CYLINDER | 20.3% | TANK | 7.8% |
| `232` | 37 | 0 | 0.00% | BLOCK ASM | 37.8% | LINER SET | 27.0% | NUT | 13.5% |
| `233` | 9 | 92 | 0.00% | REPAIR KIT | 44.4% | STUD | 33.3% | RING | 11.1% |
| `234` | 26 | 177 | 0.00% | HANDLE | 26.9% | CLIP | 19.2% | BOLT | 15.4% |
| `235` | 172 | 1,396 | 0.00% | GASKET SET | 91.3% | KING PIN SET | 5.2% | CLIP | 3.5% |
| `236` | 24 | 67 | 0.00% | BOLT | 25.0% | DOWEL | 16.7% | DISC | 12.5% |
| `238` | 8 | 0 | 0.00% | HUB | 50.0% | SHIM | 25.0% | BOLT | 25.0% |
| `239` | 383 | 8,792 | 0.02% | GASKET | 14.9% | CAP | 9.9% | UNIT | 8.4% |
| `240` | 221 | 1,783 | 0.00% | SHAFT | 29.9% | BRACKET | 10.9% | SWITCH | 7.7% |
| `241` | 18 | 0 | 0.00% | BLOCK ASM | 38.9% | PIPE ASM | 22.2% | RECTIFIER | 22.2% |
| `242` | 90 | 107 | 0.00% | RING | 13.3% | PLUG | 11.1% | CLIP | 10.0% |
| `243` | 918 | 3,563 | 0.01% | GASKET | 4.6% | TUBE | 3.8% | BRACKET | 3.5% |
| `244` | 47 | 30 | 0.00% | SCREW | 23.4% | CLIP | 17.0% | RING | 10.6% |
| `245` | 9 | 0 | 0.00% | BOLT | 22.2% | NIPPLE | 22.2% | RETAINER | 22.2% |
| `246` * | 0 | 0 | 0.00% | CYLINDER ASM | 42.9% | LINER SET | 28.6% | REPAIR KIT | 14.3% |
| `248` | 1 | 0 | 0.00% | SPACER | 100.0% | — | — | — | — |
| `249` | 1 | 0 | 0.00% | FLANGE | 100.0% | — | — | — | — |
| `250` | 216 | 830 | 0.00% | BOLT | 34.3% | BEARING | 12.5% | COVER | 5.6% |
| `251` | 186 | 12,579 | 0.03% | CLIP | 10.8% | BOLT | 10.2% | MOTOR | 6.5% |
| `252` | 13 | 12 | 0.00% | GASKET | 46.2% | BOLT | 15.4% | BRACKET | 15.4% |
| `253` | 86 | 7,052 | 0.02% | SWITCH | 10.5% | CABLE | 8.1% | WASHER | 7.0% |
| `254` | 175 | 9,936 | 0.02% | VALVE KIT | 14.3% | FAN | 11.4% | BELT | 8.6% |
| `255` | 39 | 8,847 | 0.02% | LINING SET | 48.7% | LINING | 33.3% | LINING KIT | 15.4% |
| `256` * | 0 | 0 | 0.00% | CABLE | 46.2% | SHIM | 30.8% | SEAL | 15.4% |
| `258` | 5 | 0 | 0.00% | LINER SET | 80.0% | CUP | 20.0% | — | — |
| `260` | 506 | 15,162 | 0.03% | BOLT | 35.0% | LINER SET | 28.5% | LINER | 13.2% |
| `261` | 23 | 750 | 0.00% | UNIT | 52.2% | CLIP | 26.1% | MOUNTING | 13.0% |
| `262` | 152 | 14,938 | 0.03% | MIRROR ASM | 38.2% | LAMP ASM | 20.4% | MIRROR | 7.9% |
| `263` | 435 | 41,795 | 0.09% | ELEMENT | 58.9% | FILTER | 17.2% | ELEMENT KIT | 11.0% |
| `264` | 812 | 18,066 | 0.04% | PUMP ASM | 11.0% | GASKET | 9.4% | BOOSTER ASM | 6.0% |
| `265` | 412 | 11,248 | 0.02% | WASHER | 12.4% | GASKET | 8.0% | BOLT | 7.3% |
| `266` | 128 | 37,181 | 0.08% | DISC | 15.6% | CAB ASM | 12.5% | BOLT | 11.7% |
| `267` | 64 | 76,782 | 0.17% | CAB ASM | 32.8% | SILENCER ASM | 31.2% | MANIFOLD | 10.9% |
| `268` | 59 | 1,744 | 0.00% | RING SET | 62.7% | LINER SET | 20.3% | GRILLE | 6.8% |
| `269` | 227 | 15,074 | 0.03% | BEARING | 55.5% | JOURNAL ASM | 8.8% | HANGER ASM | 8.8% |
| `270` | 4,652 | 328,307 | 0.71% | GASKET SET | 9.4% | PUMP ASM | 8.1% | CONTROL UNIT | 7.4% |
| `271` | 190 | 3,725 | 0.01% | GEAR | 12.1% | BOLT | 7.4% | GASKET | 7.4% |
| `272` | 3,381 | 371,190 | 0.80% | BRACKET | 5.1% | COVER | 4.0% | BOLT | 3.8% |
| `273` | 4,469 | 569,291 | 1.23% | BOLT | 5.3% | GASKET | 4.1% | BRACKET | 3.9% |
| `274` | 1,631 | 98,200 | 0.21% | GASKET SET | 3.6% | GASKET | 3.1% | VALVE | 3.1% |
| `275` | 19,874 | 21,597,705 | 46.77% | HARNESS | 13.7% | COVER | 5.1% | PANEL | 4.5% |
| `276` | 2,018 | 1,449,623 | 3.14% | BRACKET | 17.3% | PIPE | 7.2% | HOSE | 6.4% |
| `277` | 6,360 | 1,497,036 | 3.24% | HARNESS | 9.0% | BRACKET | 8.1% | CONTROL UNIT | 7.4% |
| `278` | 4,140 | 227,677 | 0.49% | BOLT | 5.9% | BRACKET | 5.4% | CASE | 3.8% |
| `279` | 746 | 49,462 | 0.11% | BOLT | 14.1% | GASKET | 7.2% | GASKET SET | 7.0% |
| `280` | 6,517 | 796,537 | 1.72% | GASKET SET | 4.4% | CYLINDER | 4.3% | BRACKET | 3.8% |
| `281` | 1,038 | 314,729 | 0.68% | BRACKET | 13.8% | PIPE | 7.3% | HOSE | 6.2% |
| `282` | 516 | 236,856 | 0.51% | SEAL | 6.0% | PANEL | 5.2% | GEAR | 3.9% |
| `283` | 12,993 | 4,926,347 | 10.67% | HARNESS | 12.3% | CONTROL UNIT | 8.0% | BRACKET | 7.8% |
| `284` | 81 | 10,062 | 0.02% | BOLT | 11.1% | CLIP | 9.9% | NUT | 9.9% |
| `285` | 346 | 20,670 | 0.04% | MOLDING | 9.0% | BOLT | 7.8% | CLIP | 7.2% |
| `286` | 505 | 54,329 | 0.12% | HOSE | 10.1% | SEAL | 6.3% | GASKET SET | 6.3% |
| `287` | 6,621 | 2,244,841 | 4.86% | BRACKET | 9.4% | PIPE | 5.0% | HOSE | 4.7% |
| `288` | 4,922 | 839,732 | 1.82% | BRACKET | 17.2% | COVER | 5.3% | HOSE | 4.3% |
| `289` | 77 | 4,053 | 0.01% | LEVER | 18.2% | PULLEY | 15.6% | HOSE | 11.7% |
| `290` | 36 | 0 | 0.00% | BOLT | 75.0% | TANK | 13.9% | STUD | 8.3% |
| `291` | 76 | 8,122 | 0.02% | STEERING UNIT | 19.7% | DUCT | 11.8% | HOSE | 9.2% |
| `292` | 38 | 232 | 0.00% | STEM ASM | 68.4% | GASKET SET | 26.3% | RING SET | 2.6% |
| `293` | 30 | 615 | 0.00% | VALVE | 16.7% | BELT | 13.3% | SWITCH | 13.3% |
| `294` | 73 | 10,565 | 0.02% | VALVE | 23.3% | DISC | 19.2% | REPAIR KIT | 12.3% |
| `295` | 20 | 41 | 0.00% | ROD | 30.0% | ELEMENT | 30.0% | SWITCH | 15.0% |
| `296` | 72 | 43,852 | 0.09% | THERMOSTAT | 41.7% | CYLINDER ASM | 15.3% | DISC | 6.9% |
| `297` | 13 | 209 | 0.00% | GASKET | 38.5% | FUSE | 23.1% | CLIP | 15.4% |
| `298` | 6 | 0 | 0.00% | VALVE | 83.3% | PAD KIT | 16.7% | — | — |
| `299` | 60 | 589,793 | 1.28% | PAD KIT | 15.0% | POWER UNIT | 11.7% | SWITCH | 11.7% |
| `330` | 631 | 31,406 | 0.07% | GASKET | 10.1% | BEARING | 9.5% | THERMOSTAT | 7.0% |
| `331` | 219 | 712 | 0.00% | WASHER | 24.7% | SEAL | 15.1% | HORN | 8.2% |
| `332` | 483 | 18,187 | 0.04% | CLIP | 9.1% | WASHER | 5.4% | BEARING | 5.4% |
| `356` | 411 | 0 | 0.00% | BOLT | 10.2% | GASKET | 8.0% | PLUG | 4.6% |
| `357` * | 0 | 0 | 0.00% | PLATE | 100.0% | — | — | — | — |
| `360` * | 0 | 0 | 0.00% | CASE-TRANS | 33.3% | PLUNGER | 33.3% | PLANE GASKET | 33.3% |
| `365` * | 0 | 0 | 0.00% | HOSE | 100.0% | — | — | — | — |
| `379` | 5 | 132 | 0.00% | GASKET | 100.0% | — | — | — | — |
| `400` | 4 | 0 | 0.00% | REPAIR KIT | 100.0% | — | — | — | — |
| `430` | 445 | 3,436 | 0.01% | BOLT | 21.8% | NUT | 13.0% | PIN | 9.9% |
| `431` | 191 | 1,150 | 0.00% | CLIP | 18.3% | U BOLT | 11.5% | PIPE | 11.0% |
| `432` | 311 | 5,479 | 0.01% | CLIP | 22.2% | PIPE | 12.2% | PLUG | 5.5% |
| `530` | 35 | 58 | 0.00% | HANDLE | 20.0% | SCREW | 20.0% | WASHER | 17.1% |
| `531` | 8 | 0 | 0.00% | PAD | 87.5% | FENDER | 12.5% | — | — |
| `532` | 8 | 0 | 0.00% | PUMP | 100.0% | — | — | — | — |
| `541` | 149 | 275 | 0.00% | HOSE | 20.1% | VALVE | 7.4% | STARTER ASM | 6.0% |
| `542` | 286 | 19,270 | 0.04% | BEARING | 22.7% | BOLT | 10.5% | WASHER | 8.0% |
| `543` | 309 | 2,926 | 0.01% | GASKET | 17.5% | WASHER | 12.6% | BOLT | 11.3% |
| `544` | 102 | 13,998 | 0.03% | RING | 17.6% | LAMP ASM | 12.7% | COVER | 12.7% |
| `545` | 69 | 233 | 0.00% | HOSE | 17.4% | BRACKET | 13.0% | VALVE | 11.6% |
| `546` | 316 | 4,952 | 0.01% | RUBBER | 13.6% | SHIM | 9.2% | PIN | 7.3% |
| `547` | 356 | 1,788 | 0.00% | BOLT | 14.9% | PUMP ASM | 7.6% | PLUG | 5.9% |
| `548` | 25 | 638 | 0.00% | RING | 36.0% | CAMSHAFT | 28.0% | GEAR | 20.0% |
| `549` | 126 | 5,779 | 0.01% | GEAR | 23.0% | SLEEVE | 13.5% | DRUM | 10.3% |
| `560` | 325 | 2,491 | 0.01% | PANEL | 69.5% | DOOR ASM | 7.4% | FRAME | 6.5% |
| `600` | 498 | 12,676 | 0.03% | WASHER | 12.7% | GASKET | 10.0% | NUT | 9.8% |
| `610` | 314 | 19,485 | 0.04% | CLIP | 15.9% | WASHER | 14.0% | GASKET | 10.8% |
| `620` | 798 | 158,658 | 0.34% | BOLT | 8.8% | NUT | 7.9% | GASKET | 5.0% |
| `630` | 99 | 267 | 0.00% | BOLT | 31.3% | GASKET | 14.1% | CLIP | 11.1% |
| `640` | 11 | 30 | 0.00% | CAP | 27.3% | INSERT | 27.3% | PIN | 18.2% |
| `650` | 1,335 | 50,034 | 0.11% | BOLT | 15.3% | GASKET | 8.8% | WASHER | 6.5% |
| `660` | 169 | 10,615 | 0.02% | CLIP | 18.9% | BOLT | 9.5% | HINGE | 6.5% |
| `670` | 33 | 1,110 | 0.00% | GASKET | 51.5% | WASHER | 12.1% | CLIP | 9.1% |
| `680` | 416 | 29,258 | 0.06% | BOLT | 11.8% | GASKET | 11.1% | RING | 10.1% |
| `690` | 136 | 2,828 | 0.01% | DISC | 8.8% | NUT | 8.1% | COVER | 7.4% |
| `700` | 44 | 7 | 0.00% | BOLT | 50.0% | SCREW | 18.2% | CAGE ASM | 11.4% |
| `800` | 2 | 0 | 0.00% | COVER | 50.0% | BODY ASM | 50.0% | — | — |
| `900` | 17 | 0 | 0.00% | RIM | 29.4% | BRACKET | 11.8% | MOLDING | 11.8% |

**What the table says at a glance.** The money and the meaning sit in different places. The six
largest codes by euro — `275`, `200`, `283`, `114`, `287`, `277` — hold **84.07%** of the billed book
between them, and every one of them is a mixture: their largest single part type runs from 4.5%
to 18.3%. The codes that read cleanly are small. `113` is 83.2% `FRAME ASM` on €5,416. `075` is
94.1% `FENDER` on €710. `235` is 91.3% `GASKET SET` on €1,396. Only `299` breaks the pattern in the
other direction: a narrow code (60 part numbers) that carries real money (€589,793) and is 90.3%
brake parts by euro.

Ten codes exist on the price file but never billed: `001`, `073`, `083`, `110`, `208`, `246`, `256`,
`357`, `360`, `365`. They are 56 rows of 536,854 in total.

---

## 3. Which codes are coherent and which are not

**The threshold, stated plainly.** A code counts as **coherent** when it holds **at least 200 part
numbers** and its **single most common leading noun covers 80% or more** of those part numbers. The
200-part-number floor keeps a three-row code from scoring 100% on one line item. The noun is taken
from the Japanese description, with blank descriptions excluded from the denominator — a correction
to the earlier benchmark, whose `leading_noun_purity_pct` column turned out to be measuring the
share of blank descriptions rather than classification quality. **The Japanese description is blank
on exactly 0 of the 139,524 rows in the base**, so the denominator exclusion changes nothing here;
it is stated because it is the honest form of the test.

| Group | Codes | Share of base euro |
|---|---:|---:|
| **Coherent** — ≥200 part numbers, dominant noun ≥80% | **1** | €5,416 (0.01%) |
| **Near** — ≥200 part numbers, dominant noun 60–80% | **1** | €2,491 (0.01%) |
| **Mixed** — ≥200 part numbers, dominant noun 40–60% | **3** | €58,340 (0.13%) |
| **Fragmented** — ≥200 part numbers, dominant noun under 40% | **46** | €45,197,049 (97.86%) |
| *of which:* codes with fewer than 200 part numbers (not judged) | 81 | €919,786 (1.99%) |

Rounding the wider set differently, because a single threshold hides the slope: **all 132 billed
codes**, the count whose dominant noun reaches 80% is **15**, reaching 40% is **43**, and falling
below 40% is **89** — and those 89 hold **99.67%** of the base euro.

**The codes named, in order of how cleanly they read.**

Coherent — `113` — 262 part numbers, 83.2% `FRAME ASM`, €5,416. The only code that passes the test.

Near-coherent — `560` — 325 part numbers, 69.5% `PANEL`, €2,491.

The cleanest of the mixed group — `263` is 435 part numbers at 58.9% `ELEMENT` (€41,795, filters and
elements, recognisably one trade); `269` is 227 part numbers at 55.5% `BEARING` (€15,074); `202` is
274 part numbers at 44.9% `BOLT` (€1,471).

**The fragmented codes — and these are the ones that carry the business.** They are not borderline;
they are genuinely heterogeneous.

- `275` — €21,597,705, **46.77% of the billed book**, 19,874 part numbers, **415 distinct leading
  nouns**, largest `HARNESS` at 13.7%.
- `200` — €6,282,982, 13.60% of the book, **470 distinct nouns**, largest `GASKET SET` at 18.3%.
- `283` — €4,926,347, 10.67%, 312 distinct nouns, largest `HARNESS` at 12.3%.
- `114` — €2,278,168, 4.93%, **640 distinct nouns**, largest `GASKET SET` at 4.5%. This is the
  largest code on the price file by row count (144,830 rows) and the most atomised by part type.
- `287` — €2,244,841, 4.86%, 312 distinct nouns, largest `BRACKET` at 9.4%.
- `277` — €1,497,036, 3.24%, 260 distinct nouns, largest `HARNESS` at 9.0%.
- `276` — €1,449,623, 3.14%, 189 distinct nouns, largest `BRACKET` at 17.3%.

**Why the number cannot be rescued by reading the digits.** ZKK's three characters look like they
might encode something. They do not. Grouped by position, the first digit puts the money in the `2`
block (106,380 part numbers, 93.04% of base euro) and that block is still 821 distinct nouns deep.
The second digit's biggest value, `7`, covers 49,418 part numbers whose largest noun is `HARNESS`
at 7.4%. The third digit's biggest value, `0`, covers 36,590 part numbers whose largest noun is
`GASKET SET` at 10.3%. No digit position separates part types; the digits are a serial number.

**This is the number that decides whether ZKK can be an axis: one code out of 51 judgeable is
coherent, and the 46 fragmented ones hold 97.86% of the money.** ZKK cannot be an axis.

---

## 4. ZKK against the AIM family

**Codes large enough to matter.** Sixteen ZKK codes hold at least 0.5% of the €46.18M base. For
each, the table shows the dominant AIM family and the share of that code's euro the family holds.
AIM family is from `aim_master_v2.csv`, column `aim_l1_fixed` (falling back to `aim_l1`).

| ZKK | EUR | share of book | dominant AIM family | share of code | 2nd AIM family | share |
|---|---:|---:|---|---:|---|---:|
| `275` | 21,597,705 | 46.77% | Accident & Body | 21.9% | Intake Exhaust Emission | 16.2% |
| `200` | 6,282,982 | 13.60% | Maintenance Service | 25.4% | Intake Exhaust Emission | 23.0% |
| `283` | 4,926,347 | 10.67% | Intake Exhaust Emission | 23.2% | Brakes | 14.3% |
| `114` | 2,278,168 | 4.93% | Intake Exhaust Emission | 34.6% | Brakes | 21.1% |
| `287` | 2,244,841 | 4.86% | Accident & Body | 20.5% | Steering | 14.0% |
| `277` | 1,497,036 | 3.24% | Electrical | 19.3% | Accident & Body | 16.8% |
| `276` | 1,449,623 | 3.14% | Maintenance Service | 42.4% | Intake Exhaust Emission | 25.1% |
| `288` | 839,732 | 1.82% | Driveline Axle | 18.4% | Brakes | 13.1% |
| `280` | 796,537 | 1.72% | Brakes | 14.7% | Steering | 14.4% |
| `299` | 589,793 | 1.28% | **Brakes** | **90.3%** | Maintenance Service | 9.7% |
| `273` | 569,291 | 1.23% | Intake Exhaust Emission | 51.5% | Brakes | 16.4% |
| `070` | 509,959 | 1.10% | Suspension | 54.3% | Accident & Body | 21.1% |
| `272` | 371,190 | 0.80% | Maintenance Service | 51.4% | Electrical | 12.8% |
| `270` | 328,307 | 0.71% | Maintenance Service | 26.9% | Electrical | 25.4% |
| `281` | 314,729 | 0.68% | Electrical | 35.6% | Transmission | 26.9% |
| `282` | 236,856 | 0.51% | Lighting | 44.9% | Electrical | 19.1% |

One of the sixteen — `299` — has a dominant family above 80%. Three more clear half — `070` at
54.3%, `273` at 51.5%, `272` at 51.4%. The other twelve have no family above half their euro, and
the two largest codes (`275`, `200`) have no family above a quarter. Looked at as concentration:
ZKK `275` gives 21.9% of its €21.6M to Accident & Body and 16.2% to Intake Exhaust Emission, so its
two biggest AIM families account for **38.1% of a code worth nearly half the book** — the remaining
61.9% is spread across the other twenty-plus families. So ZKK does not sit inside AIM, and AIM does
not sit inside ZKK. They are two grids over the same parts, and the cells do not line up.

**Read the other way round, every AIM family is itself split by ZKK.** The count below is the
number of ZKK codes holding at least 1% of that family's euro, and the share the single biggest ZKK
code takes of the family.

| AIM family | EUR | ZKK codes ≥1% of family | biggest ZKK | its share of family |
|---|---:|---:|---|---:|
| Intake Exhaust Emission | 7,878,944 | 7 | `275` | 44.5% |
| Accident & Body | 6,810,534 | 9 | `275` | 69.4% |
| Brakes | 4,825,888 | 10 | `275` | 42.2% |
| Maintenance Service | 4,682,409 | 10 | `200` | 34.1% |
| Electrical | 3,661,303 | 12 | `275` | 47.4% |
| Fuel System | 2,934,474 | 12 | `275` | 51.4% |
| Lighting | 2,551,170 | 6 | `275` | 69.1% |
| Wheels Hub | 1,767,297 | 13 | `275` | 41.8% |
| Driveline Axle | 1,373,222 | 7 | `275` | 45.9% |
| Cabin Interior | 1,262,293 | 7 | `275` | 66.2% |
| Suspension | 1,127,169 | 11 | `070` | 24.6% |
| Steering | 1,118,017 | 11 | `287` | 28.1% |
| Transmission | 1,100,953 | 13 | `275` | 26.9% |
| Unknown | 1,057,779 | 13 | `275` | 40.3% |
| Clutch | 1,031,162 | 9 | `200` | 37.0% |

**Does ZKK split inside an AIM family, or does it mostly repeat what AIM already says? Both, and
the split is real. The clearest single fact is that ZKK `275` — 46.77% of the billed book — holds
at least 1% of **twenty-five different AIM families**, from 72.1% of Lubrication down to 16.5%. No
family owns it and it owns no family.** Two worked examples, one each way.

**Example 1 — ZKK splits the family (Brakes).** The AIM family `Brakes` holds €4,825,888. Ten ZKK
codes each hold at least 1% of it, and they carry **eight different leading part nouns**:
`275` → `COVER`, `283` → `HYDRAULIC UNIT`, `299` → **`PAD KIT` at 100.0%**, `114` → `PAD KIT`,
`200` → `CYLINDER ASM`, `287` → `LINING`, `280` → `DRUM`, `288` → `SPRING`. AIM says "Brakes" once;
ZKK distinguishes the pad line from the drum line from the hydraulic line. Inside the finer AIM cell
`Brakes > Pads & Shoes` (€1,725,515), ZKK splits it into `275` (33.5%) and `299` (30.9%, 100%
`PAD KIT`). So on Brakes, ZKK genuinely adds a layer.

**Example 2 — ZKK repeats the family (Lighting).** The AIM family `Lighting` holds €2,551,170. Six
ZKK codes each hold at least 1% of it — and **all six have the same dominant noun, `LAMP ASM`**:
`275` 47.6%, `283` 48.8%, `287` 34.8%, `282` 50.0%, `280` 34.9%, `200` 21.1%. ZKK tells you nothing
about lighting that AIM has not already told you. It splits the euro into six piles that are the
same kind of part.

A third case is worth noting because it is the strongest evidence that ZKK's boundaries cross AIM's
rather than nesting inside them: inside `Intake Exhaust Emission > DPF/DPD` (€830,552), ZKK `114` is
100% `DPD ASM` on €407,474 while ZKK `275` is 45.5% `SENSOR` on €245,842. The emission-control
after-treatment part and the sensor that watches it sit in different ZKK codes and the same AIM cell.

---

## 5. ZKK against HKK as a level — is the extra character worth more?

Both columns are scored the same way, on the same 139,524-part-number base, with the same
leading-noun definition and the same exclusion of blank descriptions. Purities here are
**row-weighted**: for each code, the share of its part numbers taken by its single most common
leading noun, summed across codes. Note that this differs by 0.01 point from the earlier audit's
12.32% purely because that audit's split set includes the parenthesis — on `;` and `,` alone ZKK is
12.32%, on `; , (` it is 12.33%. The difference moves nothing.

| System | codes used | row purity | purity, euro-weighted | single-noun codes | codes ≥100 part numbers |
|---|---:|---:|---:|---:|---:|
| **ZKK** (3 characters) | 132 | **12.32%** | 17.25% | 8 | 64 of 132 |
| **HKK** (4 characters) | 72 | **16.28%** | 30.21% | 28 | 34 of 72 |
| HKK, first 3 characters only | 17 | 10.28% | — | 4 | — |
| Aim L1 | 25 | 8.21% | — | 1 | — |
| Aim L1>L2 | 120 | 10.97% | — | 12 | — |
| ZUK (5 characters) | 284 | 12.84% | — | 68 | — |

**Raw comparison: HKK is cleaner per code, and it is cleaner for a real reason.** On the codes that
hold at least 100 part numbers — which is 98.3% of the base for both, so the comparison is fair —
ZKK scores 11.95% and HKK 16.00%. Because purity favours coarse systems automatically, the
like-for-like version normalises for code count: **ZKK 11.66%, HKK 15.11%.** HKK wins on every cut.

**And there is independent evidence that HKK's fourth character carries the meaning.** The 2022
workbook `01_data\HKK Code 20221028.xlsx` names the slot character under each prefix. Of the 39
four-character HKK codes that hold at least 20 part numbers on our billed book, **28 carry the part
type the workbook names — 72%.** Examples: `111D` is named `Cab` and is 100% `CAB ASM`; `111X` is
named `Door` and is 100% `DOOR ASM`; `113A` is named `Silencer` and is 97.0% `SILENCER ASM`;
`113F` is named `Rear Combi Lamp` and is 99.2% `LAMP ASM`; `113B` is named `Oil Seal` and is 98.1%
`SEAL`; `313A` is named `Spring` and is 62.0% `SPRING`. The fourth character is not noise.

> **DISPUTED 2026-09-20 (independent re-measurement).** The **28 of 39 = 72%** above does not
> reproduce. The denominator does: extracting the same 2022 workbook and joining it to the same
> 139,524-part-number base gives exactly **39** HKK codes at ≥20 part numbers with a workbook name.
> The numerator depends on the match rule and stays between **12 and 16 of 39 (31% to 41%)** under the
> four rules tested (euro-weighted top noun 12, row-weighted top noun 13, name anywhere in the code
> 14, strict first-word 16). None reaches 28. **Every named example above is real and reproduces** —
> `111D` `CAB ASM` 100%, `111X` `DOOR ASM` 100%, `113A` `SILENCER ASM` 96.1%, `113F` `LAMP ASM` 100%,
> `113B` `SEAL` 100%, `313A` `SPRING ASM` 86.7% — which is why the claim reads true on inspection.
> The conclusion, that HKK's fourth character carries part meaning, holds on either number. Both
> values are kept here; **do not quote the 72% until the two passes are reconciled.** Source:
> `01_data\91_build\zkk_independent_verify_20260920.py`.

**But HKK's advantage lives entirely outside the code that carries the business.** HKK `1110` holds
**116,816 part numbers = 83.7% of the base rows and €35,450,059 = 76.8% of the base euro.** That one
code is a worse mixture than anything ZKK has: its largest part type is `HARNESS` at **5.5%**, and
it contains **130 distinct ZKK codes**. It is the "everything normal" bucket. Remove it and HKK's
purity jumps to 71.44% — but on only 21.5% of the base euro, against 51.5% of the base euro for ZKK
with `275` removed. So the honest statement is:

> **HKK is a cleaner code where it says anything at all, but it says nothing about 76.8% of the
> money. ZKK is a dirty code everywhere, but it spreads that dirt across 132 buckets instead of
> hiding three quarters of the book in one.** Neither is a functional family. HKK's extra character
> is doing real work on the 23% of the book outside `1110`; on the rest it is inert.

The two overlap but are not nested. ZKK `275` sits inside HKK `1110` for 19,145 of its 19,874 part
numbers (96.3%), worth €19,315,638 = 41.8% of the base euro. Across the book, a ZKK code holding
100+ part numbers spans a median of 8 HKK codes (maximum 48), and an HKK code holding 100+ part
numbers spans a median of 18 ZKK codes (maximum 130). Each is coarser than the other in a different
direction — which is what two unrelated code lists look like.

---

## 6. ZUK — one honest paragraph

**What ZUK is for: UNKNOWN.** What is measurable is its shape and its behaviour. ZUK is 5
characters on every row with no blanks (536,854 rows, 359 distinct values on the price file, 284 of
them appearing on our billed book). The pattern is fixed: position 1 is `1`, `2` or `3`; positions
4 and 5 are digits; and **only the letters `A` through `G` ever appear in position 3** — a
restriction tight enough that the middle character is almost certainly a category letter rather
than a serial. On the money it is extremely concentrated: **the top ten ZUK values hold 87.91% of
the base euro** and `11G00` alone holds **€32,042,425 = 69.38%**. It separates a few things nothing
else separates — ZUK `13G00` (13 part numbers, €354,725) is 93% ZKK `070` and 39.4% `SPRING`, a
suspension-spring grouping that cuts across ZKK codes; ZUK `11C95` (158 part numbers) is 16% ZKK
`280`; inside ZKK `283`, ZUK `11G09` is 76.1% `CONTROL UNIT`. But mostly it repeats: inside ZKK
`275`, ZUK `11G00` holds **85.7%**; inside ZKK `200`, **84.1%**; inside ZKK `114`, **90.3%**. Its
middle-character groups do not map onto part types in any readable way (the `C` group's top noun is
`BOLT` at 13.5%; the `G` group's is `HARNESS` at 6.0%). **Verdict: a well-formed, highly
concentrated second code with no dictionary — carry it, do not chart on it, and mark the meaning
UNKNOWN.**

---

## 7. What this means for the coexistence decision

The question was whether ZKK earns a permanent column beside AIM. **Yes — as an attribute. No — as
a grouping.** Those are different jobs and ZKK passes one and fails the other, cleanly.

It fails as a grouping, and the failure is not marginal. One ZKK code out of 51 judgeable holds
essentially one kind of part. The 46 fragmented codes hold 97.86% of the billed book. The biggest
code in the file, `275`, is 46.77% of our revenue across 415 different part types, and it is the
single largest slice of fourteen different AIM families at once. If someone builds a chart on ZKK,
they will be showing "everything" as a category and calling it one.

It passes as an attribute, for three reasons that survive every measurement above. It is complete:
filled on 100% of the 536,854 rows of `01_data\【CY2026Price Revison】PRICE CD.xlsx`, with zero
blanks. It is cheap: it already arrives on the file Japan sends us and therefore costs nothing to
maintain. And it is honest: unlike HKK, it does not hide three quarters of the book in one bucket,
so a part that is unclassified stays visibly unclassified. Those are the properties that make a
column worth carrying, and none of them depends on the code being coherent.

The practical consequence is the same as the settled position reached earlier, now backed by the
code-by-code table above: **carry `jp_zkk` on the spine beside the AIM family, exactly as
`jp_class_new` and `jp_eple` are carried; use it as a completeness check — a part with a ZKK code
and no AIM family is a countable gap — and do not cut any chart, score, ranking or registration on
it.** The same rule applies to ZUK and, for the 76.8% of the book inside `1110`, to HKK. If the
business wants a level finer than the AIM family, ZKK is not it; the AIM L1>L2 pair and the 15-level
functional taxonomy are the candidates, and ZKK sits sideways to both.

---

## 8. UNKNOWNs

Listed plainly. Nothing below is inferred into a number; each is a question the files on disk
cannot answer.

1. **What ZKK means in business words.** No naming sheet, no published Isuzu list, no dictionary of
   any kind exists in this workspace. We know its shape (three characters), its completeness (zero
   blanks), and its behaviour (weakly correlated with price class). We do not know what the numbers
   stand for.
2. **Whether the ZKK code list is stable across file generations.** We hold exactly one generation
   of Japan's file. A single observation is not a guarantee, and this is the one item that would
   weaken the case for carrying the column.
3. **Who defines ZKK, HKK, ZUK and EPLE** — Japan, ISZJ, or we do. And whether a code table exists
   at all.
4. **Why the 2026 price file carries none of these columns.** `01_data\PRICE CD 260910.xlsx`,
   sheet `Sheet1`, has 13 columns and no ZKK, ZUK, HKK or EPLE. Whether that is a deliberate
   narrowing or a lost export is UNKNOWN.
5. **What ZUK means.** See section 6. Shape proven, meaning not.
6. **Why prefix `114` appears in the 2022 HKK workbook but never in the live HKK column.**
7. **Whether any live pack breaks now that the Japan columns sit on the spine.** No pack has been
   run since the columns were appended. This is a test that has not been performed, not a known
   defect.
8. **A fair score for our own AIM family tree on the whole book.** Every comparison in this
   document sits on the 88.11% of euro that carries a ZKK code. The remaining 11.89% —
   25,689 spine rows, €6,231,324 — has no Japanese code at all and is invisible to every ZKK-based
   comparison, which flatters ZKK's apparent coverage of the business.
9. **The 2022 workbook's prefix count: 26 by my extract, 27 in the earlier audit.** The difference
   is one code sitting on a summary line rather than in the block grid, and it does not affect the
   ZKK overlap, which is 7 in both. Recorded rather than reconciled.

**One number elsewhere in the workspace that this document does not use.** The
`leading_noun_purity_pct` column in `01_data\90_INBOX\_classification_benchmark_20260920.json`
should not be quoted. It measures the share of blank descriptions, not classification quality — it
prints 82.59% for ZKK, ZUK and HKK alike, which is the blank-description share of the base. Every
purity figure in section 5 above was computed from the Japanese description with blanks excluded
from the denominator, and the two definitions are not interchangeable.

**Independent re-measurement, and where this document can be tightened.** On 2026-09-20 a second pass
wrote `01_data\91_build\zkk_independent_verify_20260920.py` from scratch against the same two files.
It reproduced the base, the join, the coherence counts, the `275` figures, the HKK `1110` figures and
the ZKK-versus-HKK structure. Three things it could not leave exactly as written:

1. **The HKK named-slot count in section 5 is disputed.** The denominator (39 codes) reproduces and the
   numerator does not; the measured range is 12 to 16 of 39, not 28. Marked in place in section 5.
2. **"ZKK `275` is 46.77% of the billed book"** is 46.77% of the €46.18M covered base and **41.21%**
   of the €52.41M billed book. The definition is in this document's header; the short phrase should
   not travel without it.
3. **The "25 AIM families" count** is on `aim_l1_fixed` falling back to `aim_l1`, the column section 4
   names. On `aim_l1` alone it is 24, because the `Lighting` family has no rows in `aim_l1` on the
   billed base. The count is right for the column stated; the column must travel with the number.

Everything else in this document, including every figure the verdict rests on, stands.

---

## Provenance

| Item | Path | Row / column detail |
|---|---|---|
| Japan price workbook (the source) | `01_data\【CY2026Price Revison】PRICE CD.xlsx`, sheet `PRICE CD 250912` | 536,854 rows; `Pno`, `Parts name`, `ZKK`, `ZUK`, `HKK`, `EPLE`; 142 ZKK values, 125 HKK values, 359 ZUK values, zero blanks in the three columns measured |
| Per-row code cache | `01_data\00_derived\jp_codes_cache_20260920.csv` | 536,854 rows, 536,854 distinct part numbers, one ZKK value each |
| The spine | `01_data\00_derived\aim_master_v2.csv` | 165,213 rows, 32 columns; `l12m_billed_eur` (book total €52,414,407.82), `aim_l1_fixed`, `aim_l2_fixed`, `jp_zkk` |
| 2022 HKK workbook | `01_data\HKK Code 20221028.xlsx` | sheets `Parts` (13 prefixes), `Accessories` (2), `Lubricant` (11) |
| Common base for every share | join of cache to spine on part number | 139,524 part numbers, €46,183,083.72, 88.11% of the billed book |

**Consistency check performed.** `jp_zkk` on the spine was compared row by row against `zkk` in the
cache for every shared part number: 139,524 compared, 139,524 equal, 0 disagreements.

**Measurement scripts written for this task** (all under `01_data\91_build\`, none modifying a
source file):

- `zkk_dictionary_measure_20260920.py` — structural test, per-code nouns, coherence groups, AIM comparison
- `zkk_dictionary_detail_20260920.py` — threshold variants, AIM split analysis, normalised purity
- `zkk_dictionary_closeout_20260920.py` — the full 142-row table, euro-weighted purity, spine consistency
- `zkk_dictionary_hkk_level_20260920.py` — HKK against ZKK on codes carrying volume
- `zkk_dictionary_hkk_named_20260920.py` — the 2022 workbook's names tested against measurement
- `zkk_dictionary_blocks_20260920.py` — ZKK numeric-block and digit-position structure
- `zkk_dictionary_reconcile_20260920.py` — purity definition variants and the 2022 prefix count
- `zkk_independent_verify_20260920.py` — **added 2026-09-20 by a later, independent pass.** Written
  from scratch against the spine and the cache; reproduces the base, the join, the coherence counts,
  the `275` figures and the HKK comparison, and is the source of the one disputed number in section 5

**No email was sent or drafted. No dashboard, workbook or data file was rebuilt or modified.**
`01_data\raw\sales\*` was not touched. This document and the eight scripts listed above are the only
files written for it. The document was then given a **Status** section at the top by the later pass;
no figure in the body was overwritten, and the one disputed figure was marked in place.


---

## Part VI — HKK system review

# HKK sales-category system — review

**Date:** 2026-09-20 · **Internal** · read-only work (one file read, one measurement pass; nothing rebuilt)

> **CORRECTIONS — 2026-09-20, same day, later.** Three things in the first issue of this note were
> wrong or incomplete. Read these before quoting anything below.
>
> 1. **§4 fill rates are wrong.** The price-file column fills were measured with a `read_only`
>    workbook handle that was never closed, so the number of rows seen depended on where the reading
>    stopped. Corrected, measured on the full 533,400 rows: `Class` **0.7% blank** (3,857 rows) and
>    `FIGKEY` **0.4% blank** (2,112 rows) are right; `Country of origin` is **84.4% blank**, not
>    15.6% filled as implied. The conclusion in §4 is unchanged.
> 2. **§1 says "the letter is the only part-family signal". That is wrong.** HKK is **four**
>    characters, not five: a three-digit prefix plus one letter-or-digit slot character that carries
>    different meanings under different prefixes. It is not uniformly a sales-status flag. There are
>    **125** HKK codes in the live file, not the 114 slots the 2022 sheet defines. §9 below is the
>    substance; §1 stands only as a description of the 2022 sheet.
>    *Correction added later on 2026-09-20.* This item as first written said: *"HKK is five characters,
>    not four: prefix (three) + letter + a trailing digit meaning 'sales status' — `0` normal sale, `4`
>    surcharge, `6` rebuilt, `7`, `8` VOR, `9` return."* That was wrong. Measured on all 536,854 rows
>    of `PRICE CD 250912`, every HKK value is exactly **four** characters; there is no fifth character
>    in the file. See items 4–7 below.
> 3. **§8 understates the error class.** The 142 fig-key errors it describes are *fig-key versus AIM*
>    inconsistencies. The larger defect is that **`aim_master_v2` holds no ZKK or ZUK column at all**,
>    so the newer and more complete Japanese codes were never loaded. §10.
>
> **Corrections added 2026-09-20 after the reproducibility audit**
> (`01_data\90_INBOX\REPRODUCIBILITY_AUDIT_JP_CODES_2026-09-20.md`). Items 4–7 below are added to this
> notice, not substituted for it. The original wording of every corrected passage is kept in the body
> with the right number beside it.
>
> 4. **§9's HKK row counts are wrong.** On `【CY2026Price Revison】PRICE CD.xlsx`, sheet
>    `PRICE CD 250912`, `1110` is **458,368** rows (85.38%), not 491,294 (91.5%), and **`1114` does
>    not occur on the sheet at all** — there is no 21,834-row `1114`. The trailing-digit-4 group is
>    2,100 rows in total, almost all `3114` (2,094). The origin of 491,294 and 21,834 is **UNKNOWN**;
>    neither value matches any file on this machine. Confirmed by two independent full passes.
> 5. **§10.1's prefix-equality claim is wrong.** ZKK's 142 codes are *not* the HKK prefix list.
>    **5 of 142** are also three-character prefixes in the live HKK column (`110`, `113`, `213`, `331`,
>    `332`); **7 of 142** are prefixes on the 2022 HKK workbook (`113`, `114`, `115`, `211`, `330`,
>    `331`, `332`); and **0 of 142** equal any full HKK value. The two candidate prefix lists do not
>    agree with each other either.
> 6. **§10.3's class table was wrong in three of its five rows.** No code reaches 100%. ZKK `114` is
>    `XC` on **77.4%**, ZKK `070` is `XM` on **68.9%**, ZUK `11G00` is `XC` on **78.4%**, ZUK `13G00`
>    is dominantly **`XM` on 80.6%** (not `EV`), and ZUK `11F91` is dominantly **`XC` on 73.1%**
>    (not `RY`). Only 12 of the 142 ZKK codes sit in a single class, and those 12 cover 139 rows of
>    536,854.
> 7. **§10.1's purity sentence is wrong.** **8** of 142 ZKK codes have a single leading noun on the
>    Japanese part description, and row-weighted purity is **17.74%** on that description. The
>    "only 1 of 142" reading came from our own spine `description` field, which is blank on most rows
>    and inflates any noun-purity score. Use the Japanese description and treat 17.74% as the honest
>    figure.
>
> Sections 9 and 10 are appended and supersede where they conflict. Where items 4–7 disagree with
> them, items 4–7 win.

**Source reviewed:** `01_data\HKK Code 20221028.xlsx` — sheets `Parts`, `Accessories`, `Lubricant`.
**Customer feedback:** Outlook thread *RE: preliminary price file for 2023.*, Sigurður Einar Jónsson
(BL ehf, Iceland), Dec 2023, in the bottom of the chain from Feb 2023.

---

## Verdict

HKK is not a classification system. It is a **sales-accounting bucket list** — where the line goes in
the P&L and which warehouse it ships from. It cannot answer "what part is this", which is exactly what
the customer, our own sales analysis and the price revision all need it to answer. As a functional
family system it is unusable: 55% of its code slots are empty and thirteen families the business
actually sells (clutch disc, brake pad, rotor, bumper, sensor, hose, bearing, bolt) have no home in it.

Do not present it to BL as the classification answer. It will confirm their complaint rather than
close it.

---

## 1. What HKK actually is — it is a route code, not a part family

The `Parts` sheet defines eleven prefixes:

| prefix | Japanese text | English on the sheet |
|---|---|---|
| 111 | 在庫品／部品／競合なし | stock / parts / non competitive |
| 112 | 在庫品／部品／アクティブ | stock / parts / active |
| 113 | 在庫品／部品／その他競合 | stock / parts / other competitive |
| 114 | 在庫品／部品／E-PARTS | stock / parts / E-PARTS |
| 115 | — | 9 = export temporary |
| 118 | 在庫品／部品／ＩＳＺ | stock / parts / ISZ |
| 191 | — | 0–6 = Part Catalogue, CSS-Net fees, UOE User ID fee, UOE subscription fee, CSS-Net single licence, Warehouse tool, Inventory CR |
| 211 | 直送品／部品／競合なし | direct / parts / non competitive |
| 310 | ICL／部品／BESTFIX（ISZ/generic） | (Isuzu-branded generic) |
| 311 | 直送品／部品／競合なし | direct / parts / non competitive |
| 312 | 直送品／部品／アクティブ | direct / parts / active |
| 313 | 直送品／部品／その他競合 | direct / parts / other competitive |
| 319 | ICL／BESTFIX（other OEM） | (other-OEM generic) |

The first digit is stock versus direct, the second is the sub-route, the third is the competitive
posture. The **letter** underneath is the part-family signal, and it is a 26-slot catch-all (plus 0–9)
repeated identically under all eleven prefixes. **Correction (2026-09-20):** this paragraph as first
written added that there is also a "**fifth character — a sales-status flag**". There is not. Every
HKK value in the live file is **four** characters — the three-digit prefix plus one fourth character.
What that fourth character means under each prefix is settled in §9.

Evidence that the prefix is the real content and the letter is not:

- `113 D` = "Rebuilt EGR Cooler", `313 C` = "Rebuilt Cab Tilt Cylinder", `310 F` = "Fan Belt",
  `111 H` = "AC Filter". Different families sharing letters across prefixes; the same family spread
  across letters.
- `110 8` = "VOR Order", `111 9` = "Surcharge for Parts Return", `111 4` = "Surcharge for VOR handling",
  `311 X` = "SLD Core Charge" — commercial charge codes sitting in the same slot space as "Cab" and "Door".
- `191 1` = "CSS-Net fees", `191 5` = "Warehouse tool" — services, not parts at all.
- `111 K` = "Liner, Liner Kit" and `113 K` = "Rebuilt AC Compressor" — the same letter, two unrelated
  part families, demonstrable in the offered file itself.

## 2. Measured size and fill

| Sheet | Prefixes | Code slots | Slots with a description | Empty |
|---|---:|---:|---:|---:|
| Parts | 13 | 393 | 172 | 221 (56%) |
| Accessories | 3 | 71 | 23 | 48 (68%) |
| Lubricant | 11 | 311 | 163 | 148 (48%) |
| **Total** | | **775** | **358** | **417 (54%)** |

Downstream of that: **23 labels appear under more than one code** inside `Parts` — "Fan Belt" on
`113/C`, `310/F`, `319/F`; "Wiper Blade" on `113/H`, `310/M`, `310/P`; "MOT Kit" on `112/E`, `310/X`,
`319/X`; "Disc Pad" on `310/1` and `319/1`. The same label in more than one bucket is fine in a route
system and fatal in a classification system: it makes aggregation wrong rather than merely coarse.

## 3. What is missing — the customer's complaint, reproduced

Keyword test against the 358 populated labels:

| the business sells this | HKK slots for it |
|---|---:|
| clutch disc (`DISC; CLUTCH`) | **0** |
| brake pad / `Disc Pad` | listed, but **31% of brake-pad euro has no price class** — see §5 |
| rotor (`ROTOR; DISC BRK`) | **0** |
| bumper | **0** |
| sensor | **0** (no sensor of any kind) |
| hose | 2 — "Radiator Hose", "Brake Hose" |
| bearing | 3 |
| bolt / nut | 1 ("Wheel Pin & Nut") |
| lamp | 1 ("Rear Combi Lamp") |
| mirror | 2 |
| injector | 2 — "Used Injector", "Rebuilt Injector" |

The customer wrote in Feb 2023: *"There are some item categories missing, like bumpers"*, and that
Isuzu has a category for each bolt while Nissan has one "Small parts". The file he eventually got
confirms both.

## 4. The price file does carry the field — but almost nothing in it

`PRICE CD 260910.xlsx` (533,400 rows) has both a `FIGKEY` and a `Class` column. Fill:

| column | blank rows | blank |
|---|---:|---:|
| `Class` | 3,857 | 0.7% |
| `FIGKEY` | 2,112 | 0.4% |
| `Country of origin` | 449,946 | **84.4%** |

So `Class` is the only classification field in the file that is effectively complete — and it is not
usable at face value either, because the column holds **39 distinct two-letter codes** where the
master price class is one letter:

- `XC` alone is 374,593 rows (70%), `XD` 26,010, `EV` 24,395, `DD` 22,403, `XF` 19,720.
- Of the 39 codes, **24 are letter-plus-`C`** (XC, DD, EV, XF, XM, ED, EF, CC, HD, …).
- The published price-class counts in the pipeline are only `C 11,542 · F 1,560 · D 1,380 · V 862 ·
  P 438 · M 301 · T 53 · J 37` — 46,613 rows are priced, out of 165,213 on the spine and 533,400 in
  the price file.

The `Class` column is therefore the right field delivered in a different vocabulary from the one the
Japanese price-class table uses (Japan: C "Gen.", D "Slow", F "Fast", V "V Fast", M "Med", P "Coll.").
Reconciling the 39 codes to the letters is a decode job, not a rename.

**Also measured:** the `FIGKEY` in the price file is not the figure key on our own spine. Our spine's
13,847 keys do not match the price file's 26,663 raw values at all; only after stripping separators do
13,281 of them overlap, and then **89.2% of price-file rows carry a figure key we already hold**. So
the price file is not adding classification information we lack — it is repeating it, in a different
format.

## 5. Why this is urgent on our side — it is already breaking the price revision

Both new fields were uploaded today. Both are thin:

- **Price class**: on the AIM spine, 33,748 rows are priced over €52.4M L12M billed, i.e. **66.8% of
  billed euro**. Of the €17.4M with no class, €4.30M (8.2%) is genuinely absent-classified (Fluids &
  Chemicals €612k, Engine €435k, Electrical €305k) and €1.65M is the "General Parts"/blank bucket.
- **Brake pads**: `Disc Pad` exists in HKK and appears in the list we sent the customer on 25 Jul 2023,
  and the price revision's own carve-out for pads used a 47% margin on 4,488 rows — yet **31% of
  brake-pad euro carries no price class at all**. Clutch disc is worse: in the revision, clutch disc
  and clutch kit are still one bucket, because the taxonomy has nowhere to split them.

So the customer's complaint and our own analysis failure have the same root cause. That is what makes
this the important one rather than a customer-service reply.

## 6. What the alternative looks like

The internal alternative already exists and is now the only live spine: **AIM**, one column, one
vocabulary.

| AIM L1 (`aim_l1_fixed`) | PNs | L12M € | share |
|---|---:|---:|---:|
| Intake Exhaust Emission | 970 | 8,020,703 | 15.30% |
| Accident & Body | 3,856 | 6,829,349 | 13.03% |
| Brakes | 712 | 4,964,353 | 9.47% |
| Maintenance Service | 568 | 4,921,913 | 9.39% |
| Electrical | 1,910 | 3,964,839 | 7.56% |
| Fuel System | 917 | 2,953,524 | 5.63% |
| Steering | 479 | 2,865,345 | 5.47% |
| Lighting | 965 | 2,590,249 | 4.94% |
| Wheels Hub | 1,004 | 1,894,907 | 3.62% |
| (blank) | 140,490 | 1,648,694 | 3.15% |
| Driveline Axle | 478 | 1,424,315 | 2.72% |
| Engine | 844 | 1,363,513 | 2.60% |
| Cabin Interior | 1,140 | 1,325,836 | 2.53% |
| Suspension | 677 | 1,229,048 | 2.34% |
| Unknown | 4,424 | 1,191,621 | 2.27% |
| Transmission | 1,342 | 1,107,235 | 2.11% |
| Clutch | 251 | 1,031,036 | 1.97% |
| Cooling | 558 | 941,267 | 1.80% |
| Fluids Chemicals | 135 | 860,847 | 1.64% |
| Chassis Frame | 2,420 | 623,123 | 1.19% |
| Literature Marketing | 40 | 274,541 | 0.52% |
| Tools Equipment | 102 | 176,019 | 0.34% |
| Unknown Review | 663 | 120,788 | 0.23% |
| Lubrication | 242 | 91,241 | 0.17% |

Two honest caveats on the table above, both already on file:

1. The €1.65M in the blank row is partly an artefact — 140,290 of those 140,490 rows carry a figure
   key and are reconstructable from it; they are unfilled on the spine, not unknown.
2. A **15-level** spine (Engine / Fuel / Exhaust / Cooling / Filters / Drivetrain & Clutch / Brakes /
   Steering & Suspension / Electrical / Body & Exterior / Glass & Wipers / Interior & Cab / HVAC /
   Wheels & Tyres / Accessories) already exists in
   `ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx`, sheet `FUNCTIONAL TAXONOMY` — built, in English,
   with L1/L2 codes (01.01 … 15.04) and euro per leaf. It is **not** upstreamed into the spine. That is
   the ready answer if a category structure has to go out; see the open decision below.

## 7. The 142 real errors found today, for context

A separate check this morning matched figure keys against class. €1.41M of L12M billed sits on four
figures mis-familied, and they are all the kind of error a family system is supposed to prevent:

| figure | n | L12M € | what is wrong |
|---|---:|---:|---|
| 873-042 | 16 | 620,163 | the fig is labelled urea in the PMS taxonomy, but the high-euro PNs are cabin blower filters |
| 201-001 | 53 | — | clutch discs tagged Brakes / Discs & Drums |
| 201-002 | 56 | 587,940 (both clutch figs) | clutch pressure plates tagged Chassis Frame / Mounting Hardware |
| 130-006 | 17 | 201,212 | air cleaners filed under Fluids Chemicals / Cleaning Chemicals |

126 of those 142 were corrected onto the spine this morning (€789,151), the blower rows deliberately
left because AIM already had them right.

## 8. Recommendation

1. **Do not ship HKK as the answer.** At 54% empty slots and no home for the top service families, it
   cannot be presented as a category system in January.
2. **Ship the field they actually asked for.** In Jan 2023 BL asked for three things: family codes /
   fig keys, **source country**, and **dimensions & weight**. The Jan 2023 price file did carry source
   country and weight; the 260910 file carries `Country of origin` at **15.6% fill** and a complete
   `Net weight`. Completing origin and weight is deliverable; a Japanese recategorisation is not.
3. **Give them the figure key plus the functional tree.** The figure key is already present on ~100%
   of the price file once normalised (2,112 blank rows, 0.4%), and the 15-level functional taxonomy is
   already built. Together they give BL the aggregation level they need. Any adoption by BL is a data
   commitment and needs the open country decision below first.
4. **Have Japan decode the `Class` column.** 39 two-letter codes to the letter vocabulary, once. That
   is a small ask with a large downstream return — it is the same column the price revision needs.
5. **Answer the customer honestly, without a date.** They have waited since Feb 2023. The honest reply
   is what exists, what is missing, and what we are doing about the field they need.

## Open decisions for Jerome

- **Country list.** The AIM spine carries 21 country-level values; BL trades in 18. Today's earlier
  session decided the country axis cannot be settled unilaterally, and the block is explicitly *not*
  auto-applied. What is the country list to be used if this goes out?
- **Attribute layer** (source country, dimensions, weight) is on hold on the roadmap — this
  recommendation re-orders it, because origin and weight are two of BL's three asks.
- **Which taxonomy is the outward one** — the 15-level functional tree, or AIM. They overlap and
  neither is a superset; putting both in front of a distributor would repeat the problem this review
  is about.
- **Does BL get HKK at all**, as the middle layer between figure key and their own reporting, or do we
  keep HKK internal and give them figure key + functional family only?

---

## Provenance

| item | path |
|---|---|
| HKK workbook (customer-supplied, 2022-10-28) | `01_data\HKK Code 20221028.xlsx` |
| Full sheet dump | `01_data\90_INBOX\_hkk_dump_20260920.txt` |
| Aim spine (live) | `01_data\00_derived\aim_master_v2.csv` — 165,213 rows |
| Fig key vs class verify | `01_data\90_INBOX\_AIM_figkey_vs_classes_verify_20260920.md` |
| Error rows | `01_data\90_INBOX\_AIM_figkey_vs_classes_REAL_errors_20260920.csv` |
| 15-level functional taxonomy | `01_data\01_Pricing\ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx` → `FUNCTIONAL TAXONOMY` |
| Master price file | `01_data\PRICE CD 260910.xlsx` — 533,400 rows |
| Earlier spine audit | `03_analytics\Isuzu\prism\docs\AIM_CLASSIFICATION_AUDIT_2026-09-17.md` |
| Mail thread | Outlook, *RE: preliminary price file for 2023.*, Sigurður Einar Jónsson (BL ehf) |

Nothing was rebuilt, renamed, mailed or published in producing this review. The only file written is
this one and the sheet dump beside it.

---

# 9. HKK decoded properly — four characters, and the fourth means different things under different prefixes

> **Corrected 2026-09-20.** This section was first titled *"HKK decoded properly — five characters, and
> the fifth is not a family"*. HKK is **four** characters. Every one of the 125 distinct HKK values on
> `PRICE CD 250912` is exactly four characters, on all 536,854 rows, stored as text; there is no
> five-character HKK value in the file. The original title and the table below are kept so the change
> is visible; the corrected figures are in the right-hand columns.

Re-read of the 2022 sheet against the live 2026 file. The 2022 sheet groups codes in blocks of ten
`0`–`9`, and the descriptions only ever named the digit-0 row. The digit is therefore not part of the
code; it is appended. What it means, read off the sheet itself:

> **Note (2026-09-20).** This paragraph describes the **2022 sheet's layout**, and that is all it
> describes. It does not carry over to the live file: the "appended digit" reading is what produced the
> withdrawn five-character claim. On the live file the code is four characters and there is no
> separate appended digit — the fourth character is a slot that may be a digit or a letter. The list
> below is evidence about the 2022 sheet, not about `PRICE CD 250912`.

| digit | rows that prove it |
|---|---|
| **0** | "General Parts" in every prefix (row 30) — the normal sale |
| **4** | `111 4` "Surcharge for VOR handling"; `112 4` "Rebuilt Shoe (small)" |
| **5** | `111 5` "Air Suspension Diaphragm" — plain part, no special meaning found |
| **6** | `112 6` "RU Active"; `113 6` "RU Semi Active" |
| **7** | `111 7` "Air Dryer Repair Kit"; `113 7` "Mirror" |
| **8** | `111 8` "VOR Order"; `112 8` "Driven Plate ASM" |
| **9** | `111 9` "Surcharge for Parts Return"; `113 9` "Service TM" |
| **1/2/3** | "DPF", "Heater Components", "Air Suspension ASM" — parts |

So the **four-character** form is prefix + one slot character. The 2022 sheet's own digit blocks
suggest that under prefix `111` the fourth character reads as a sales status (`0` normal, `4`
surcharge, `8` VOR, `9` return), but `311 4` is "Inj Pump" on that same sheet, so the status reading is
not uniform across prefixes.

Live confirmation, `【CY2026Price Revison】PRICE CD.xlsx` (536,854 rows, sheet `PRICE CD 250912`,
from ISZJ, September 2025), HKK column, 125 distinct values:

| HKK | rows | what it is |
|---|---:|---|
| `1110` | **458,368** | prefix 111, slot `0`, "General Parts" — the normal part. **Corrected from 491,294**, which does not reproduce on this file (see the notice at the top, item 4) |
| `1114` | **0** | **does not occur on this sheet.** The original 21,834 is withdrawn; the whole trailing-digit-4 group is 2,100 rows, of which `3114` is 2,094 (mostly injector-pump components, not a surcharge). Origin of 21,834 is UNKNOWN |
| `111D` | 6,120 | prefix 111, **slot D = "Cab"** (corrected from 2,545) |
| `111K` | 3,626 | prefix 111, slot K = "Liner, Liner Kit" (corrected from 581) |
| `111V`, `1116`, `1111`, … | the remainder | rebuilt / service / DPF slots, all four characters |

This is why HKK looked like a warehouse code in the first pass: at **85.4%** of the catalogue it *is*
one row, `1110`. (It was written as 91.5%; 91.5% is 491,294/536,854, and 491,294 does not reproduce.
The measured share is 458,368/536,854 = 85.38%.) The slot character is still not the family signal;
the letter inside it is.

# 10. The columns we were never given

The 2026 price file carries four columns ISZE has never loaded. The current master price file on disk,
`PRICE CD 260910.xlsx`, has 13 columns and **none of them are these**:

`EPLE` · `Example Model` · `ZUK` · `HKK` · `ZKK`

## 10.1 ZKK — the classification product, and it is the real one

**ZKK is the sales-category code, and it is the one the customer asked for by name.** Evidence:

- Three characters, `AAA`, **142 distinct codes**, every one of the 536,854 rows filled.
- ~~Its shape matches the HKK 2022 sheet's own opening blocks exactly: `113`, `114`, `118`, `211`,
  `310`, `311`, `312`, `313`, `319`, `133`, `331`–`339`, `123`, `320`. The ZKK code *is* the HKK
  prefix. HKK carries the prefix plus a route letter and a status flag; ZKK carries the category.~~
  **Corrected 2026-09-20 — this claim is false.** Its shape **resembles** the HKK 2022 sheet's blocks
  but is not the same list. Of the 142 ZKK codes, **5** are also three-character prefixes in the live
  HKK column (`110`, `113`, `213`, `331`, `332`) and **7** are prefixes on the 2022 HKK workbook
  (`113`, `114`, `115`, `211`, `330`, `331`, `332`); **no ZKK value equals any full HKK value**. The
  two candidate prefix lists disagree with each other — the 2022 workbook lists `114` and `330`, which
  the live column never emits, and the live column emits `110` and `213`, which the 2022 workbook does
  not list. ZKK and the HKK prefix are two different code lists that share a few numeric blocks.
- It drives price class ~~directly~~ — see the table in §10.3. **Partly.** It correlates strongly with
  class; it does not determine it.

**It is a catalogue-and-price category, not a functional family.** Tested on 536,854 rows, grouping
each ZKK code by the leading noun of the part description: ~~only **1** of 142 codes is
description-pure, and row-weighted purity is **17.5%**~~ → **corrected 2026-09-20: 8 of 142 codes have
a single leading noun on the Japanese part description, and row-weighted purity is **17.74%** on that
description.** The "only 1" reading came from our own spine `description` field, which is blank on most
rows and inflates any noun-purity score (blank rows group as one giant "noun"). Use the Japanese
description and treat 17.74% as the honest figure. ZKK `114`, the biggest code at 144,830 rows, is a
route/class bucket holding 1,901 different leading nouns. This is why it never felt like a clean
family axis — the commercial meaning is "what catalogue block and price class am I", not "what is
this part for".

## 10.2 The exact column BL asked for, and it is superior to ZUK

In February 2023 BL asked for "family codes / parts categorized group / FigKeys". The file has a
column called **`ZUK`**.

*Corrected 2026-09-20:* this sentence first read "likely 'Zuishō Kategorī', an accessory/option
categorisation". That was a guess, not a reading of any document. **What ZUK categorises is UNKNOWN.**
It is a complete, well-shaped code with no dictionary held anywhere in this workspace. Do not repeat
the guess.

`ZUK` is five characters in a fixed pattern **`DDCDD`** — digits, digits, letter, digits, digits —
with 359 distinct values. Its leading characters are **not** any HKK or ZKK code (`11G00`, `11G22`,
`13G00` — the two-digit numbers `11` and `13` are not in the HKK family list). It is a separate
option/accessory axis.

*Caveat added 2026-09-20 so nobody later "discovers" an overlap that is not there:* measured at code
level, **0 of 359** ZUK values equals any HKK value, and **0 of 359** equals any ZKK value. The two
columns `ZUK` and `HKK` share their leading two characters on **96.89%** of rows against **93.92%**
expected by chance, which reflects both columns being dominated by one code family rather than any
shared meaning. Wherever the columns separate they separate systematically: ZUK's second-largest
leading pair is `13` and HKK's is `31`, and those two never coincide.

**`ZKK` is the column that matches the ask, not `ZUK`.**

## 10.3 Both codes correlate with the price class

*(Heading corrected 2026-09-20. It first read "Both codes drive the price class cleanly". They do not
drive it — they correlate with it, and not cleanly.)*

Measured on all 536,854 rows — **the class the largest share of each code's rows falls in**
(heading corrected 2026-09-20; it previously read "the dominant `New Part Class` of each code", which
implied the code determined the class):

| code | rows | dominant class | share |
|---|---:|---|---:|
| `ZKK 114` | 144,830 | `XC` | **77.4%** (was written 100%) |
| `ZKK 070` | 14,612 | `XM` | **68.9%** (was written 100%) |
| `ZUK 11G00` | 265,999 | `XC` | **78.4%** (was written 100%) |
| `ZUK 13G00` | 13,150 | **`XM`** | **80.6%** (was written `EV`, 95%) |
| `ZUK 11F91` | 6,977 | **`XC`** | **73.1%** (was written `RY`, 100%) |

Three of the five rows had the wrong dominant class as well as the wrong share. No code reaches 100%.
On the 142 ZKK codes, only **12 sit in a single class**, and those 12 cover **139 rows of 536,854** —
the largest is `530` at 62 rows. So "100%" is true for 12 codes covering 0.03% of the file, and false
for `114`, which is the biggest code in the file. This table should not be shown in its original form.

The 39 two-letter class values my earlier note flagged as needing a decode **are the ZKK and ZUK
codes' own class output** — `XC`, `XD`, `EV`, `DD`, `XF`, `XM`, … They are not a mangled letter table.
They are what Japan intends. But the codes produce them as a **correlated** output, not a
deterministic one: a price-class table built by reading `New Part Class` directly is more accurate
than one inferred from ZKK or ZUK. The "decode the 39 codes" ask in §8 stands; the ask is also to keep
the ZKK/ZUK columns that sit behind them.

## 10.4 EPLE — the finest category in the file

`EPLE` is a four-digit code, **662 distinct values**, every row filled. `9999` (228,463 rows, 42.6%)
is the blank/general value; the interesting codes are the other 661. Purity is again
**14.9% row-weighted** — the same order as ZKK.

*(Note added 2026-09-20: this 14.9% is a row-weighted figure computed on the Japanese part
description, which is a legitimate form. Do not confuse it with the benchmark's
`leading_noun_purity_pct` column, which is not usable — it measures blank descriptions. See the
corrections notice at the top, item 7, and the audit claim 4.)*

What it looks like: `7012` "BOLT" 68% pure over 6,521 rows; `1901` "HARNESS" 66% over 1,906;
`2001` 29% "CAB ASM"; `604` (figure-key prefix) 100% "CAB ASM". It is an engineering/catalogue
grouping, finer-grained than ZKK.

**The hierarchy that suggests itself:** `ZKK` (142) → `EPLE` (662) → `FIGKEY` (26,663). Three levels,
all present on every row, all with real commercial meaning.

**Honest caveat.** Every one of these codes, including the best available one, is a *catalogue*
category. None of them is a functional family. The functional axis the business needs for PMS,
capture and the price revision — filters, brakes, clutch, service basket — is **not** in the Japanese
file at any level. That axis stays ours (AIM), and it is the reason AIM has to be reconciled *to*
ZKK rather than replaced by it.

# 11. The ZUK finding, and the limitation it was checked against

A July 2026 session concluded that `Example Model`, `ZUK`, `HKK` and `ZKK` in this file were
"a lossy sample, not a PN↔model bridge", because values like `WFJTUB` are two-letter model prefixes
concatenated and capped at three examples.

**That conclusion applies to `Example Model` only. It does not apply to ZUK.**

- `Example Model` is free-form, 1.8% blank, and lossy — the July finding is correct for it.
- `ZUK` is **100% filled, always exactly five characters, and always `DDCDD`** with the letter always
  in position 2. That is a defined code, not a sample. 359 values, stable, no variance in shape.

The July session bundled four different things under one verdict. `ZUK` was characterised from
`Example Model`'s defects. That is the error, and it is why nobody followed up on the column.

# 12. What this changes in the recommendation

Superseding §8's recommendation where the two differ:

1. **Ask Japan to add `ZKK` and `ZUK` to the ISZE price file — nothing else.** They already exist on
   every row of the file they send us; they are simply not in the file we distribute. This is a
   column request, not a re-categorisation project. It closes BL's February 2023 ask with data that
   already exists.
2. **Do not ask Japan to decode the 39 `Class` values.** The ZKK/ZUK codes generate them; ask for the
   code table, not the class table.
3. **Drop `HKK` from the plan.** At **85.4%** `1110` — ~~91.5%~~ — and with the family content living
   in the route codes' fourth character, it adds nothing ZKK does not already carry. (The share is
   458,368/536,854 = 85.38%. The 91.5% was 491,294/536,854 and 491,294 does not reproduce.) The
   recommendation stands.
4. **`EPLE` is the L2 layer** if a finer cut is wanted. 661 real values on every row.
5. **`FIGKEY` stays as the engineering level.** Note the standing issue: our spine's 13,847 figure
   keys do not match the file's 26,663 raw values until separators are stripped, and the country
   problem in §4 of the first issue still stands — `af`, `za`, `ru` at price-file level, 21 country
   values on our spine.

# 13. New open decisions for Jerome

- **Is ZKK the outward category**, in place of the 15-level functional tree? It is Japan's own code,
  it is on every row, and it needs no ISZE interpretation. But it is a catalogue/price bucket, not a
  functional family, so a chart by ZKK will not answer "how is our filter business doing".
- **Or is ZKK the middle layer**, with AIM as the outer family and ZKK as the catalogue detail? That
  is the shape the data supports, and it costs one join in `aim_master_v2` that does not exist today.
- **Which replaces what:** if ZKK goes out to BL, is the 15-level functional tree dropped, kept
  internal, or kept as the commercial overlay it currently is?
- **Loading the columns is not read-only.** Adding ZKK/ZUK/EPLE to `aim_master_v2` changes the spine
  every pack reads. That is a rebuild and needs an explicit go-ahead. *(Status 2026-09-20 later:
  the eight `jp_*` columns have since been appended to `01_data\00_derived\aim_master_v2.csv`, which is
  now 32 columns and 165,213 rows, rewritten at 09:24 today. No pack has been run against it since.
  The go-ahead is still needed before a pack or a shared deliverable depends on the new columns.)*

## Provenance for §9–§13

| item | path |
|---|---|
| Japanese price CD, Sep 2025, sheet `PRICE CD 250912`, 536,854 rows | `01_data\【CY2026Price Revison】PRICE CD.xlsx` |
| ZKK code counts (142 codes) | `01_data\90_INBOX\_zkk_code_counts_20260920.json` |
| Earlier session that dismissed ZUK | agent transcript `cdb22cc8`, 2026-07-26 |
| Current master price file (13 columns; no ZUK/HKK/ZKK/EPLE) | `01_data\PRICE CD 260910.xlsx` |
| Live spine (now carries the eight `jp_*` columns), 32 columns, 165,213 rows | `01_data\00_derived\aim_master_v2.csv` |
| Independent re-measurement of every corrected figure | `01_data\90_INBOX\REPRODUCIBILITY_AUDIT_JP_CODES_2026-09-20.md` |
| Consolidated settled position | `01_data\90_INBOX\SETTLED_POSITION_JP_CODES_2026-09-20.md` |

