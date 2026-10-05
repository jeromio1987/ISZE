# What the AIM classification actually covers

**Measured 2026-09-24. Read-only: nothing on the board, its builder, the safety gate or any
classification file was changed.**

Jerome is right that the pillar board scores the wrong thing. It gives AIM 60% because three of five
files exist, and a review scored it 30% because the release is not approved. Neither number looks at
the classification itself. So I measured it.

One thing first, because it is the question he actually asked. The dock is **not** about fifty
unclassified part numbers. Over the last twelve months of billing the unclassified set is **1,679
part numbers carrying EUR 329,446** — under one per cent of the money. Of those, **49 part numbers
with EUR 14,097** have no row on the master at all, and **4,129 part numbers carry the `Unknown`
marker**, worth EUR 238,668. Whichever of those numbers the earlier note meant, the classification is
not being marked down for fifty parts.

---

## The window I used

The workspace does not have one twelve-month window; it has several. I used the one the AIM packs
and the master itself use.

**Window: 1 September 2025 to 31 August 2026**, inclusive. Derived, not chosen: the maximum
`billing_date` in `sales_fact.parquet` after the parts-base filters is 2026-08-31, then twelve
calendar months back to 1 September 2025. I used the same filters the parts base uses — GPS-facing
distributors only, lines whose `line_kind` is `part`, and credit notes and returns removed. The
window carries **EUR 33,399,344** of billed parts and **1,219,773 units**.

Two other windows are in use elsewhere in the workspace, and coverage holds on all three:

| Window | Where it is used | Billed EUR | With a family |
|---|---|---|---|
| 2025-09-01 → 2026-08-31 | this measure; the AIM packs and the master | 33,399,344 | **99.01%** |
| 2025-07-01 → 2026-06-30 | the price-revision pack | 34,057,281 | **99.36%** |
| 2025-01-01 → 2026-06-30 | the safety gate's own euro check (18 months) | 52,414,408 | **98.98%** |

---

## 1. The share of billed EUR with a family assigned

| | EUR | Units | Share of EUR | Share of units |
|---|---|---|---|---|
| With a family | **33,069,898** | 1,209,285 | **99.01%** | 99.14% |
| No family (the residual) | 329,446 | 10,488 | 0.99% | 0.86% |
| Total | 33,399,344 | 1,219,773 | 100% | 100% |

By count of part numbers the picture is different and worth stating: **15,925 part numbers were
billed in the window, 14,246 carry a family (89.46%) and 1,679 do not.** So coverage is 99.01% of the
money and 89.46% of the part numbers. The ten-point gap is the tail — many part numbers billed for a
few hundred euros each.

**The share of the catalogue is a different question, and the master answers it honestly.** Of its
165,290 rows, **21,023 (12.72%) carry an AIM family** and **164,795 (99.70%) sit on a catalogue
node**. A part can have a place in the parts catalogue without yet having a commercial family
attached, and that is the normal state for a part nobody has billed. All but 61 rows (99.96%) have one
or the other. Quote the 12.72% as the catalogue share and the 99.01% as the billed-euro share; they
measure different things and both are true.

## 2. Where the residual sits — the fifteen biggest part numbers

The residual is 1,679 part numbers. The fifteen below carry EUR 97,260 of the EUR 329,446, and the
fifty biggest carry EUR 154,715.

| Part number | Billed EUR (L12M) | Part description as billed |
|---|---|---|
| 8982263230 | 19,525.08 | REPAIR KIT; AIR DRYER |
| 7552498500 | 8,999.92 | FRAME ASM |
| 7552498490 | 8,999.92 | FRAME ASM |
| 7553068050 | 7,414.20 | CASE; RR AXLE |
| 8979461460 | 6,992.62 | HOSE; FLEX,P/S CONT VLV |
| 8982034990 | 6,850.25 | TRANSMISSION ASM; MANUAL |
| 8984818641 | 6,410.29 | CASE; RR AXLE |
| 7552623640 | 6,214.67 | BOX ASM; SHIFT CONT |
| 5876102381 | 5,109.39 | PAD KIT; CALIPER, DISC BRK, FR |
| 8976641840 | 4,154.41 | FRAME; CUSHION,FRT SEAT |
| 8975372320 | 3,642.57 | TRANSMISSION ASM; AUTO |
| 7552029253 | 3,331.20 | MOTOR ASM; REAR DRIVE |
| 7552357310 | 3,251.26 | HYDRAULIC UNIT; ANTI LOCK BRK |
| 8984818581 | 3,190.63 | CASE; RR AXLE |
| 8983996200 | 3,173.80 | RAIL ASM; COMMON |

Nine part numbers sit above EUR 5,000 and they carry EUR 76,516 between them. The shape of the rest
is a long thin tail: **1,622 of the 1,679 are billed under EUR 1,000 each, and together they are
EUR 167,334.** None of the fifteen above is a blank: they are real parts (an air-dryer repair kit,
two rear-axle cases, a manual transmission assembly, a front pad kit) that the classification rules
have not reached. So the gap is decidable work, not noise.

The residual splits three ways by how it got there:

| Why it has no family | Part numbers | EUR | Share of the window |
|---|---|---|---|
| Carries the `Unknown` marker | 1,263 | 238,668 | 0.71% |
| A blank family with no marker — a repair path never run | 367 | 76,681 | 0.23% |
| No row on the AIM master at all | 49 | 14,097 | 0.04% |

## 3. The `Unknown` marker

**4,129 part numbers carry it** — 3,598 as plain `Unknown` and 531 as `Unknown Review` — in the
governed `aim_l1_fixed` column. Those part numbers bill **EUR 238,668 over the twelve months
(0.71% of the window) and 9,025 units.**

The 49 with no row on the master are worth naming separately, because they are a different kind of
gap. The largest is one ITUK brake pad kit at EUR 5,109; the rest run down from EUR 1,222 to EUR 9.
Six of them (`1812004173`, `1812220920`, `1331560180`, `1331560190`, `1331560200`, `1331560220` and
their siblings) carry numbers in a supplier's own range rather than Isuzu's ten-digit form, so they
may not be Isuzu part numbers at all. I did not take that further.

## 4. By distributor — the residual is not concentrated anywhere

Twenty-two distributors billed in the window. The residual as a share of each one's own billing runs
from **0.15% to 2.32%**, and the three largest residuals together are half of it (ITUK 17.8%, IUK
16.5%, UTI 14.8%). That is the same shape as the billing, not a problem in one market.

| Distributor | With a family | Residual EUR | Billed EUR | Residual as % |
|---|---|---|---|---|
| ITUK | 99.15% | 58,716 | 6,892,054 | 0.85% |
| IUK | 99.09% | 54,453 | 5,974,922 | 0.91% |
| UTI | 98.39% | 48,811 | 3,030,586 | 1.61% |
| UMI | 99.02% | 27,897 | 2,838,136 | 0.98% |
| PORTUGAL | 98.65% | 24,752 | 1,830,406 | 1.35% |
| UKRAINE | 97.80% | 22,970 | 1,041,719 | 2.20% |
| GERMANY | 99.28% | 19,793 | 2,757,933 | 0.72% |
| BELGIUM | 99.40% | 14,805 | 2,473,699 | 0.60% |
| IRELAND | 98.96% | 10,673 | 1,029,455 | 1.04% |
| NORWAY | 99.31% | 9,902 | 1,439,927 | 0.69% |

The remaining twelve range from SWEDEN (EUR 8,921 / 0.62%) to ICELAND (EUR 123 / 0.15%). No market is
a case on its own.

## 5. Accuracy — 50 part numbers, weighted to the biggest euros

I drew 50 classified part numbers with probability proportional to their billed EUR (fixed seed
20260924, so the draw repeats), then checked each part's own billed description against the family it
carries. I read the family level, the group level and the leaf level separately, because they fail in
different places. The part's figure key — the truck drawing it appears on — and the families its
figure-key siblings carry were used as an independent second read. **Nothing was adjusted.**

| Level | Agree | Bar |
|---|---|---|
| Family (L1) | **47 of 50 = 94%** | 90% |
| Group (L2) | 43 of 50 = 86% | — |
| Leaf (L3) | 41 of 50 = 82% | — |

**Three family-level disagreements, named:**

**8981455011 — OVERHAUL KIT; SUPPLY PUMP (EUR 45,341), carried on Transmission > Repair Kits.**
Its figure key 040-424 is labelled "Pump" and holds 22 such parts. An overhaul kit for the supply
pump belongs to the engine or the fuel system, not to the transmission. The leaf "Overhaul Kit" is
defensible; the family is not.

**8973665260 — SLEEVE & HUB ASM; TOP-4TH,OD (EUR 2,029), carried on Wheels Hub > Hub & Bearing >
Hub.** It is a fourth-gear mainshaft hub sleeve. Its figure key 226-524 is labelled "Review needed"
and holds only two parts, so nothing corroborates the wheel-hub reading. This looks like a misread
of a shared key.

**8980432054 — PUMP ASM; OIL,P/S (EUR 401), carried on Fuel System > Injection Pump > Fuel Pump.**
It is a power-steering pump. Its figure key 436-001 is labelled "Steering pump" and holds 238 parts,
and the other parts already classified under that key sit on Steering. This is a steering part filed
under the fuel system.

**Where they agree but a level below is coarse:** 8978279610 (a front pad kit filed as a brake disc;
its figure key's six siblings are pad kits), 8981028241 (an air-conditioning compressor filed on
Radiator; its key is labelled "A/C compressor" and holds 78), 8980317403 (a heater unit filed on
Blower Filter), 8983039020 (a front-axle knuckle filed on King Pin Kit), 8982473952 (a throttle
assembly filed on Air Duct), 8978420540 (an engine harness filed on Connector), 8980080340 (a shoe
hold-down pin filed on Brake Shoe). Each of those is a family that is right and a leaf that is too
coarse or off by one shelf.

**What the sample does not say.** It is one reader's judgement on 50 rows chosen by size, not a random
sample of the 14,246 classified part numbers that were billed. It measures the money you can see. It
says nothing about the roughly 144,000 master rows with no family, which have no billing to test
against.

---

## What is fair to score

The board's AIM condition 1 tests whether a file exists; condition 2 tests whether 18 stored checks
all passed. Neither can tell you whether the classification is any good, which is what Jerome was
pointing at. Below is a set of five conditions that test the thing. Each one names the exact test and
the file it reads, so it can be built.

**Condition 1 — Coverage on billed euro.**
*Test:* over the twelve months ending at the maximum `billing_date`, the share of billed parts euro
sitting on a part number with a governed family (`aim_l1_fixed` where filled, otherwise `aim_l1`) is
at least **98.0%**; and every unclassified part number above **EUR 5,000** in that window is printed
by part number, euro and description.
*Files:* `01_data/00_derived/sales_fact.parquet`, `01_data/00_derived/aim_master_v2.csv`.
*Today:* **99.01%, and nine parts above EUR 5,000, all named in section 2.** Met.

**Condition 2 — Accuracy on a sample.**
*Test:* 50 classified part numbers drawn with probability proportional to billed euro on a fixed seed;
a named reviewer reads each part's billed description against its family; at least **90%** agree at
family level, and every disagreement is listed by part number.
*Files:* `sales_fact.parquet` and `aim_master_v2.csv` for the draw; the answers are a human judgement
and must be signed.
*Today:* **94% (47 of 50), three disagreements named in section 5.** Met.

**Condition 3 — One named, approved, frozen release.**
*Test:* `_releases/RELEASES.json` holds exactly one candidate with status `APPROVED`, and
`check_classification_release.py` exits 0 against the file the AIM pages are built from.
*Files:* `01_data/00_derived/_releases/RELEASES.json`,
`01_data/00_derived/_releases/check_classification_release.py`.
*Today:* **two candidates, one PENDING_APPROVAL and one NOT_RELEASED, and zero approved.** Not met.
This is a decision, not a measurement, and it is the only one of the five that needs a person.

**Condition 4 — A distributor can open his own parts by family.**
*Test:* one page for at least one distributor that opens from Explorer with no server, carries that
distributor's own part numbers grouped by the families AIM assigns with the euro beside each family,
and states in its own text which distributor and which period it covers. A launcher must sit beside
it.
*Files:* candidate `02_dashboards/sales/ISZE_AIM_Comparison_PORTUGAL.html` with
`OPEN_ISZE_AIM_Comparison_PORTUGAL.cmd`.
*Today:* **met for Portugal, one distributor of twenty-two.** The page is self-contained — its data is
written into the page as one embedded block, 1.96 MB, no network call on first paint — and its data
covers Portugal only; the other distributor names in it appear in caveat text, not in figures.

**Condition 5 — The safety checks pass, and the drift rule means something.**
*Test:* all checks in `aim_classification_gate.json` pass, against **the file the AIM pages are built
from**, with the drift rule split in two: (a) no stored measure may move more than 1% between runs —
keep; (b) the leaf counts must **not** be equal to a frozen baseline, but any change must carry a
named review and a written new baseline **in the same run**.
*Files:* `01_data/00_derived/aim_classification_gate.json`,
`01_data/00_derived/aim_classification_leaf_baseline.json`,
`01_data/91_build/verify_aim_classification.py`.
*Today:* **17 of 18 pass. Not met.** The failing check is the one thing in the gate that is
bookkeeping, not data quality: it requires 177 bottom-level leaves against 176 present, so a
deliberate new class trips it. Rule (a) is doing real work and should stay. Rule (b) as written
punishes exactly the improvement Jerome is asking to be credited for.

**Scored today, these five give 3 of 5 = 60% — the same number the board shows.** That is a
coincidence worth saying out loud: the board's 60% comes from three "does the file exist" ticks, and
this 60% comes from coverage and accuracy passing while the release sits unapproved and the gate
still fails. The percentage lands in the same place; the reasons do not.

---

## What I could not measure

- **The price-revision base is a different twelve months** (July 2025 to June 2026). Coverage there
  is 99.36%, but a single number cannot be right for two windows at once, so the condition has to
  name its window.
- **The gate's own euro check says 93.82%.** I reproduced that figure exactly. It reads
  `sales_fact.parquet` with no filters at all — so its denominator includes freight, rebates, service
  fees and demurrage (EUR 1,807,550 in its window) — and it tests the catalogue axis, not the family
  axis. On the master's family axis the same 18 months are **98.98%**. Both numbers are correct; they
  answer different questions, and the board should not show the 93.82% next to a family-coverage
  claim.
- **Whether the Portugal page is what a distributor would actually use.** The page exists and is
  self-contained. Whether it satisfies the strategy paper's test — a participant completed a real
  task and can name a decision it changed — is not something I can measure from a file.
- **L2 and L3 coverage for the unclassified set.** They are blank together with the family, so there
  is nothing separate to measure there.

---

### Files this work wrote (all new; nothing existing was modified)

| File | What |
|---|---|
| `00_docs/AIM_COVERAGE_MEASURE_2026-09-24.md` | this memo |
| `01_data/91_build/_aim_coverage_measure_20260924.py` / `.json` | the five measures |
| `01_data/91_build/_aim_coverage_decomp_20260924.py` / `.json` | the residual split and the window sensitivity |
| `01_data/91_build/_aim_coverage_support_20260924.py` / `.json` | row-weighted coverage, billed-PN counts, figure-key corroboration, concentration |
| `01_data/91_build/_aim_gate_bridge_20260924.py` | reproduction of the gate's 93.82% and the same window on the family axis |
| `01_data/91_build/_aim_accuracy_sample_20260924.py` / `.csv` | the 50-part draw and the filled verdicts |
| `01_data/91_build/_aim_offmaster_20260924.py` | the 49 part numbers with no row on the master |
| `01_data/91_build/_aim_final_probe_20260924.py` | the L1 buckets on the billed window, and the Portugal page's scope |
| `01_data/91_build/_aim_figlabel_20260924.py`, `_aim_page_probe_20260924.py`, `_aim_page_ctx_20260924.py`, `_aim_sample_verdicts_20260924.py` | supporting probes |
