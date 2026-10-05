# Parts classification — full audit

**Prepared:** 2026-09-17 · internal · read-only (nothing in the classifier, the pipeline or any pack was changed)
**Subject:** the 3-level parts classification — its source, its method, its accuracy, and how it compares to the standards the rest of the industry uses
**Sales window for every euro figure:** 2025-01-01 → 2026-06-30 (18 months, gross billed, €50.71M on classified part numbers). This is **not** the 12-month in-scope base used in `aim_catalog_breakdown_NOTES.md` — do not mix the two.

This audit is independent of, and goes further than, `03_analytics/Isuzu/prism/docs/AIM_CLASSIFICATION_AUDIT_2026-09-17.md`. That one audited the **file** (keys, hierarchy, the two-vocabulary problem, coverage). This one audits the **classification itself** — whether the parts are in the right boxes, tested against three sources the classifier never saw.

---

## Verdict

The tree is well-built and consistently applied. What it is not is *verified*, and in one category it is materially wrong.

The classification was produced by pattern-matching the part description text. That is a legitimate way to start, and it was executed cleanly: there is not a single case in 16,210 distinct descriptions where the same text was given two different answers. But a text rule can only ever be as good as the words, and nobody has ever checked its output against an independent source. When I did — against customs commodity codes, against Isuzu's own catalogue figures, and against the part text read by a human rule — the tree agrees about **63–71%** of the time, and one whole service category is in the wrong family.

The single worst case: **engine air filtration is €1.20M of billed parts over 18 months, and only €42,534 of it — 3.5% — sits in `Filters > Air filter`.** The rest is filed under air conditioning and "other air system". A shipped note concluded air filters were "a network number in name only" at €28,469 and that the zeros in eleven markets were "real zeros, not missing data". That conclusion is an artefact of the classification, not a fact about the business.

The encouraging half of that finding: **two other taxonomies in this workspace already have those air filters in the right place** — the figure-key layer that feeds PMS, and a functional workbook built in March 2026. So the service-capture numbers are safe, and the correction is available without new research. What is missing is a written rule about which taxonomy wins.

Separately, two defects in the build chain mean roughly one key in five is not classified from its own description at all, and the safety gate's strongest-looking check cannot detect any of it.

| # | Finding | Severity |
|---|---|---|
| 1 | Engine air filtration 96.5% outside the Filters family — €1.16M | **P0** |
| 2 | The gate's "catalogue ties to PR00 on 100%" check is circular and proves nothing | **P0** |
| 3 | 19.5% of keys inherit their node from a superseding part number, not their own row | **P1** |
| 4 | Level 1 is a commercial judgement derived from a part noun — structurally unsound | **P1** |
| 5 | Five more wrong-system classes: king pins, ball joints, drag links, bumper bars, window regulators — €683k | **P1** |
| 6 | 18.2% of billed euro sits in a bucket named "Other" or "Review needed" | **P1** |
| 7 | `king_pin` is a configured service category with zero rows in data — €219,775 invisible | **P1** |
| 8 | Four parallel taxonomies exist; they disagree, and no precedence is written down | **P1** |
| 9 | Leaf level too coarse to act on across 65% of the book | **P2** |
| 10 | No attribute layer — the real gap against every external standard | **P2 · ON HOLD (roadmap)** |
| 11 | Determinism: same text always gives the same node | **PASS** |
| 12 | Hierarchy, keys, vocabulary control | **PASS** |
| 13 | PMS service categories survive the misfile via the figure-key layer | **PASS** |

---

## 1. What the system actually is

The chain, end to end:

```
IE40 PR00 price list (SAP), 13-Mar-2026
  └─ "IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx"   164,380 rows
       Level 1 Family / Level 2 Group / Level 3 Type added here
  └─ build_pr00_classification.py  →  pr00_classification.csv             164,795 keys
  └─ build_aim_pn_classification.py →  aim_pn_classification.csv          164,667 rows
  └─ build_aim_classification_v2.py →  aim_pn_classification_v2.csv       164,667 rows
  └─ verify_aim_classification.py   →  aim_classification_gate.json        PASS 13/13
```

The method is stated by the source workbook itself, on its `3-Level Summary` sheet:

> "3-level classification summary. **Generated from Description field using rule-based mapping.** Rows without a clear pattern are assigned to Other / review."

So this is a keyword classifier over the part text. Three consequences follow, and they are the spine of this audit:

1. **It knows only what the description says.** `FILTER; ACL` does not contain the word "air", so nothing in the text tells a rule that ACL means air cleaner.
2. **Nothing in the chain validates it.** Every downstream check compares a copy against the same workbook.
3. **The commercial layer is derived from the noun.** Level 1 is *Competitive parts / Repair parts / Accident parts / High value repair / Comfort parts / Hardware & consumables*. Those are market positions, inferred from what the part is called.

A detail worth knowing: **the classification file itself carries a description on only 15.3% of its rows** (25,191 of 164,667), and on the 139,410 `pr00_catalog` rows that form the backbone, only 6.0%. The text the classifier used is in the price workbook, not in the classification file. Anyone auditing the file alone cannot see what the decision was based on. I had to reload the price master to do this audit at all.

### Shape of the tree

7 Level-1 families · 25 Level-2 groups · 172 distinct Level-3 names, forming **171 populated leaf paths** in the current file. (The gate's `governed_l3_count = 172` counts names, not paths — a small difference, but the two are quoted interchangeably elsewhere.)

Leaf sizes run from **1 part number to 9,022**, median 556. Nine leaves hold ten parts or fewer, and they read like rule-ordering leftovers rather than categories: `Filters > Hydraulic / transmission filter` (1 part), `Mirrors > Mirror glass` (1), `Turbo > Turbo actuator` (1), `Body parts > Wiper` (2), `Consumables > Sealant / adhesive` (2), `Exhaust > Exhaust sensor` (3), `Brake parts > Brake booster` (7).

`Filters > Filter element` holding exactly **1** part number is the tell. Filter elements are one of the highest-volume things we sell; a leaf with that name and one member means the earlier rules consumed almost everything before that rule ran.

---

## 2. Quality of the classification

### 2.1 Determinism — PASS

If the method is a rule over a string, identical strings must give identical answers. Tested on the source workbook's own Description column, 16,210 distinct non-empty descriptions:

| Test | Result |
|---|---|
| same description, different Level 1 | **0** |
| same description, different Level 2 | **0** |
| same description, different Level 3 | **0** |

This is a genuine pass and it corrects an earlier reading. The `aim_pn_classification.csv` audit found 71 descriptions mapping to more than one `aim_l1`; that is the *workbook* vocabulary layer joined by description, not the catalogue columns. The catalogue tree is a clean function of the text.

It also means every error found below is **systematic, not random** — which is good news. A systematic error is fixable with one rule; a random one is not fixable at all.

### 2.2 Text drift — not a problem

I expected the classification to be stale against the live price master (13-Mar vs 10-Aug 2026). It is not:

| | |
|---|---|
| present in both files | 162,904 |
| description identical | 162,881 (**99.99%**) |
| description changed | 23 (€12,347) |
| in the live master but never classified | 2,454 (€21,781) |
| in the classified list, gone from the live master | 1,476 |

Worth a separate note: the live price master contains a handful of **corrupted description strings** — `k0109AMP UNIT` (was `HEADLAMP UNIT`), `c0268dLATOR; HYDRO BOOSTER`, `nOSE; RUBBER,VSV`, `8980103310SHION,ENG MTG,RR`, `3 VER; RECLINING`. Around ten rows, low value, but it is the source of truth for part text and it has been overwritten in place somewhere upstream.

### 2.3 Independent check 1: customs commodity codes

The PR00 price master carries an **HS commodity code** on 98.9% of parts — the customs tariff code, filled by Isuzu/SAP, never seen by the classifier. 195 distinct 6-digit subheadings across 86 headings.

Method: for each HS6 subheading with 30+ parts, take the majority Level-2 group of its members, then ask how often a part agrees with its own HS peers.

| | parts | euro |
|---|---|---|
| in scope (HS6 groups ≥30 parts) | 152,794 | €46.88M |
| agrees with its HS6 majority | 95,871 (**62.7%**) | €32.21M (**68.7%**) |

**Read this carefully — it is not a 37% error rate.** HS is a *customs* taxonomy and its biggest bucket, `870899` "other parts of motor vehicles", holds 15,780 of our parts and means nothing functionally. HS is also wrong itself in places: our largest single brake line, `8983767550 ROTOR; DISC BRK,FRT` at €998,989, is coded `870850` (drive axles) in the price master. Our classification has that one right and the customs code wrong.

What the test is good for is **coherence per group**, and there it is very informative:

| Level 2 group | parts | billed € | share in its top HS6 | distinct HS6 |
|---|---|---|---|---|
| Air system | 5,480 | 592,045 | **14.6%** | 78 |
| Air conditioning | 3,172 | 2,158,884 | **17.3%** | 66 |
| Cooling | 4,481 | 1,193,633 | 19.4% | 47 |
| Exhaust | 5,361 | 3,758,395 | 19.4% | 60 |
| Hydraulic / mechanical | 8,312 | 1,896,547 | 21.1% | 65 |
| Hardware | 16,919 | 830,749 | 21.2% | 83 |
| Electrical sensors | 19,232 | 6,293,859 | 35.7% | **103** |
| … | | | | |
| Brake parts | 7,482 | 5,299,429 | 58.4% | 57 |
| Mirrors | 2,136 | 476,246 | 66.9% | 21 |
| Belts | 480 | 43,844 | **75.8%** | 16 |

The tight groups (Belts, Mirrors, Brake parts, Clutch parts, Lighting) are real families. The loose ones are not families at all — they are **residual bins with a family name on them**. `Hydraulic / mechanical` spread across 65 customs subheadings, `Hardware` across 83, `Electrical sensors` across 103. Those three hold 44,463 part numbers, 27% of the catalogue.

### 2.4 Independent check 2: Isuzu's own catalogue figures

Every part carries a **Fig No.** — Isuzu's own parts-catalogue illustration group, the manufacturer's real assembly structure. 297 figures, 244 with 20+ parts.

| | parts | euro |
|---|---|---|
| agrees with its figure's majority group | 109,050 / 152,773 (**71.4%**) | €34.15M / €47.43M (**72.0%**) |

Same caution applies: an Isuzu figure legitimately contains the bolts and gaskets of the assembly it illustrates, so perfect purity would be wrong. And figures `999` / `997` are themselves catch-alls (761 and 488 parts, 21 groups each).

The useful signal is figures that scatter where they should not. `fig 450` — 1,923 parts, €634,960 — splits across 13 groups: Suspension 648, Hardware 469, Hydraulic/mechanical 381, Brake parts 233, Body parts 117. That is one Isuzu assembly area being shredded into five of our families, and it is the same three bins doing it.

### 2.5 Independent check 3: reading the part text like a parts person

This is the test you asked for directly. I wrote 22 high-precision rules — each a phrase that names the part's system beyond argument, each with explicit exceptions so a brake *lamp switch* is not counted as a brake and an air-cleaner *bracket* is not counted as a filter. A violation is something a parts person would recognise on sight, not a token collision.

Scope: 153,578 classified parts that carry a description.

**Result: 3,546 part numbers misfiled, €2,091,184 billed — 4.12% of the 18-month book.**

That splits into two very different things, and they must not be added into one headline:

**(a) Wrong system — the part is in a family it has no physical relation to. 1,274 parts, €1,844,034.**

| class | parts | billed € | what happened |
|---|---|---|---|
| engine air filtration | 128 | **1,160,612** | `FILTER; ACL` and `ELEMENT; AIR CLEANER` → Air conditioning / Other air system |
| king pin kits | 536 | 219,775 | `KING PIN KIT` → `Hardware & consumables > Hardware > Pin` |
| steering links | 235 | 171,854 | `LINK; DRAG` → `Hydraulic / mechanical > Linkage / lever` |
| bumper bars | 201 | 148,994 | `BAR; FRT BUMPER` → `Suspension > Leaf / suspension spring` |
| control-arm ball joints | 67 | 126,243 | `JOINT ASM; BALL,LWR CONT ARM` → `Hydraulic / mechanical > Linkage / lever` |
| window regulators | 107 | 16,556 | `REGULATOR ASM; DOOR` → `Starter / alternator > Voltage regulator` |

The window regulator is the clearest illustration of the method's limit: a door window winder and a voltage regulator share one word, and a text rule cannot tell them apart. 107 part numbers.

The king pin case matters commercially beyond the reporting. A king pin kit is a steering-geometry wear item with real money on it; it is sitting in "Hardware & consumables", which everything downstream treats as low-value consumables.

**(b) Object type vs system of use — defensible either way, but applied inconsistently. 2,272 parts, €247,150.**

The tree cannot decide whether to file a part by *what it is* or by *what it serves*. 9,637 gasket-ish parts go to `Gaskets / seals`; 1,423 go to the system instead (`GASKET; DPD` → Exhaust > Aftertreatment, €21,498; `GASKET; INJ NOZZLE` → Injectors, €12,912). Same with harnesses: 6,607 to `Electrical sensors`, 673 to their system (`HARNESS; DIFF LOCK` → Transmission). Neither choice is wrong. Having both in one tree is.

Full line-by-line list, sortable, with HS code, figure, list price and billed euro on every row:
`01_data/00_derived/_audit_cls_description_violations.csv`

---

## 3. Finding 1 in full: engine air filtration

Every part whose text reads as an engine air-cleaner element, 18-month window:

| where it actually sits | parts | billed € | share |
|---|---|---|---|
| `Comfort parts > Air conditioning > Other A/C` | 122 | **998,360** | 83.0% |
| `Competitive parts > Air system > Other air system` | 6 | **162,252** | 13.5% |
| `Competitive parts > Filters > Air filter` | 128 | 42,534 | **3.5%** |
| **total engine air filtration** | **256** | **1,203,146** | 100% |

€1,160,612 — 96.5% — is outside the Filters family. Cabin and blower filtration is a *separate* €1,622,097 across 147 parts, and that one genuinely does belong under air conditioning; I have not mixed it in.

Euro, family and fleet together, so the number can be judged:

| market | fleet 2025 | billed € | units | €/truck | units/truck | misfiled |
|---|---|---|---|---|---|---|
| UTI | 10,336 | 228,545 | 12,257 | 22.1 | 1.186 | 99% |
| ITUK | 22,389 | 217,383 | 7,734 | 9.7 | 0.345 | 88% |
| IUK | 47,783 | 177,863 | 10,187 | 3.7 | 0.213 | 100% |
| IBX | UNKNOWN | 71,028 | 3,799 | — | — | 95% |
| Norway | UNKNOWN | 59,170 | 3,102 | — | — | 100% |
| Ireland | UNKNOWN | 52,605 | 2,267 | — | — | 86% |
| Sverige | UNKNOWN | 45,807 | 2,447 | — | — | 100% |
| UMI | 18,542 | 32,545 | 2,838 | 1.8 | 0.153 | 99% |
| **network** | 163,459 | **1,203,146** | **61,243** | 7.3 | 0.370 | **96.5%** |

Three things this changes:

1. **The published air-filter figure understates the category by about 28x.** To be exact about bases: on my own 18-month window the `Air filter` leaf holds €42,534 while the category holds €1,203,146 — a ratio of **28.3x**. `aim_catalog_breakdown_NOTES.md` §7 reports €28,469 on a 12-month in-scope base, which is consistent with the same leaf; it is the leaf that is small, not the category. That note concludes: *"Air filter is a network number in name only… it is genuinely absent in Norway, Sweden, Finland, Iceland, Denmark, Hungary, Malta, Palestine, Armenia, Kazakhstan and Romania. Those are real zeros, not missing data."* Norway bills €59,170 of engine air filtration in this window and Sweden €45,807. They are not zeros. The parts were filed as air conditioning.

2. **The service-capture view is NOT affected — I checked, and it holds.** I expected this to break PMS and it does not, because the PMS layer does not read the catalogue tree. `fig_key_taxonomy.yaml` derives `pms_category` from the PR00 node *or* from the EPC figure key, and the figure rule rescues the misfile:

| route | parts | billed € |
|---|---|---|
| could match `match_group: "Filters"` | 128 | 42,534 |
| rescued by `match_fig_key: "130-006"` and siblings (130-026, 130-027) | 66 | 1,123,009 |
| no category by either route | 62 | 37,603 |

In the shipped `parts_catalog_dimension.csv`, **207 of the 256 parts are correctly tagged `pms_category = air_filter`, covering €1,202,903 of the €1,203,146 — 99.98% of the euro.** So PMS capture for air filters is sound. My earlier reading that capture was "measuring 3.5% of the category" was wrong; the figure-key layer is doing the work the text rule could not.

That is worth understanding rather than just correcting. **The right answer already exists inside the workspace, in a different taxonomy.** Fixing the catalogue tree is not new research — it is adopting what the figure-key layer already knows.

3. **Air conditioning is overstated.** `Air conditioning > Other A/C` bills €1,113,634 in the window; €998,360 of that is engine air filters. That leaf is mostly not air conditioning.

The fix is one rule: **`ACL` in an Isuzu description means air cleaner.** That single token, plus `ELEMENT; AIR CLEANER`, moves €1.16M into the right family — and the figure keys to do it with are already mapped.

### 3.1 King pins: a configured service category that is empty

The same test on king pins fails the other way, and nothing rescues it. `fig_key_taxonomy.yaml` contains:

```yaml
  - match_group: "Suspension"
    level3_contains:
      king: king_pin
```

All 536 king-pin parts sit in `Hardware`, so `match_group: "Suspension"` can never fire, and there is no figure-key fallback for king pins:

| | |
|---|---|
| parts reading `KING PIN` | 536 (€219,775) |
| able to match the Suspension rule | **0** |
| `king_pin` rows in the shipped `parts_catalog_dimension.csv` | **0** |
| where they actually sit | Hardware > Pin 366 · Hardware > Washer 136 · Hardware > Bolt 22 · Other gasket / seal 7 |

`king_pin` therefore exists as a service category in configuration and holds nothing in data. Anyone looking for king-pin service demand finds an empty set and would reasonably conclude we do not sell them. We sell €219,775 of them in 18 months.

---

## 4. Errors in the build chain

### 4.1 The gate's strongest check is circular — P0

`aim_classification_gate.json` reports 13/13 PASS, and its most reassuring line is:

```
catalogue_pr00_tie   measured=100.0   expected=>= 99.0%
note: "proves the governed columns were not silently rewritten"
```

It proves exactly that and nothing more. It compares `aim_pn_classification_v2.csv`'s catalogue columns against `pr00_classification.csv` — and both are copies of the same GPT-classified workbook. The check verifies that a copy is a faithful copy. It cannot detect a single error in this audit: the air-filter misfile ties to PR00 at 100%, because PR00 is where it came from.

The note's wording is the problem. "Proves the governed columns were not silently rewritten" is true. Anyone reading the gate output reasonably hears "the classification has been verified against the catalogue". There is no independent catalogue in the chain.

**And it skips rows.** `build_pr00_classification.py` stores keys zero-*stripped* (`s.lstrip("0")`); the v2 file and the gate use zero-*padded* 10-character keys:

| | |
|---|---|
| v2 rows | 164,667 |
| found verbatim in `pr00_classification.csv` | 163,014 |
| **never tested by the 100% check** | **1,653 (€870,378)** |
| of which keys with a leading zero | 1,616 — **none** joined |

So the gate reported "163,014 rows checked, 100.0%" and 1,653 rows were silently not checked. Every part number beginning with a zero is untested.

### 4.2 One key in five is classified from a different part — P1

`build_pr00_classification.py`, lines 130–143:

```python
for i_pn_idx in (i_pn, i_new):          # i_pn = "P/N", i_new = "Newest P/N"
    n = _norm(row[i_pn_idx])
    if not n or n in out:               # first writer wins
        continue
    out[n] = {...}                       # same node for both keys
```

It writes the classification under **both** the part number **and** its superseding "Newest P/N", first-come-first-served in workbook row order. I replayed the logic and reproduced the output exactly (164,794 keys against the file's 164,795 rows), so this is what runs.

| | |
|---|---|
| keys written | 164,794 |
| filled from a `Newest P/N` rather than the part's own row | **32,181 (19.5%)** |
| of those, the part's own row says something different | **1,083 (€181,775)** |

The 1,083 are the provable damage. Examples:

| part | own text | own node | inherited instead from |
|---|---|---|---|
| 8983167030 | `WRENCH;WHEEL PIN,41*21*445` | Hardware > Pin | `1851130150 WRENCH; WHEEL P` → Hydraulic / mechanical > Other mechanical |
| 8971846991 | `BUSHING; BRKT,RR SPRING` | Hardware > Spring | `8941185881 BUSHING; LEAF SPR,RR` → Suspension > Leaf spring |
| 8978339870 | `RELAY; MAIN` | Electrical > Relay | `8972385400 RELAY; CLUTCH FREE` → Clutch parts > Other clutch |
| 8980913940 | `FILTER; ACL` | Air conditioning > Other A/C | `8944302500 FILTER; AIR CLEANER` → **Filters > Air filter** |
| 8984849200 | `WEATHERSTRIP; FRONT DOOR` | Body parts > Door | `8980291993 SEAL; DOOR,MAIN` → Gaskets / seals |

The last-but-one row is a nice irony: one air filter got classified *correctly*, by accident, because it inherited from a part whose text happened to say "AIR CLEANER".

The other 31,098 successor keys have no own row, so inheritance is their only source. That may be right — a supersession usually replaces like with like — but it has never been checked, and the €181,775 proves it is not reliable.

### 4.3 A price-format trap

The PR00 `Price` column writes four-figure prices with a **space** thousands separator (`1 133.06`). A plain `float()` throws on all 7,001 of them — every part over €1,000. My own first pass hit this and reported a €1,000 ceiling on every price statistic in the audit; I found it, fixed it, and re-ran. Flagging it because anything else reading that column needs the same guard, and a silent drop of all four-figure parts would understate list value badly.

---

### 4.4 There are four parallel taxonomies, and nobody wrote down which one wins

This is the finding that reframes the rest. The catalogue tree is not the only classification in the workspace — it is one of four, all live, all built differently.

| # | Taxonomy | Shape | Built from | Coverage |
|---|---|---|---|---|
| 1 | **PR00 catalogue tree** (`catalog_l1/l2/l3`) | 7 / 25 / 171 | text rules on the description | 164,667 parts |
| 2 | **AIM workbook** (`workbook_l1/l2/l3`) | 21 system names + placeholders | joined by description to the AIM workbook | 16,499 parts, ~79% of euro |
| 3 | **Figure-key / PMS layer** (`pms_category`) | 22 figure keys + ~30 keyword rules | EPC figure number, with PR00 fallback | 8,266 of 164,969 rows tagged |
| 4 | **Mar-2026 functional workbook** | 15 numeric families + 99 UNCLASSIFIED, two levels | separate build, unwired | 15,353 billed parts |

Number 2 is the two-vocabulary problem the 17 Sep file audit covered. Numbers 3 and 4 are new to this audit and they matter for a specific reason: **they disagree with the catalogue tree, and where they disagree they are right.**

`C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx` (2.1 MB, seven sheets) carries a `FUNCTIONAL TAXONOMY` sheet with 15 numeric Level-1 families — `01 ENGINE`, `02 FUEL SYSTEM`, `03 EXHAUST & EMISSION`, `04 COOLING SYSTEM`, `05 FILTERS & MAINTENANCE`, `06 DRIVETRAIN & CLUTCH`, `07 BRAKES`, `08 STEERING & SUSPENSION`, `09 ELECTRICAL & SENSORS`, `10 BODY & EXTERIOR`, `11 GLASS & WIPERS`, `12 INTERIOR & CAB`, `13 CLIMATE CONTROL (HVAC)`, `14 WHEELS & TYRES`, `15 ACCESSORIES & MISC`, plus `99 UNCLASSIFIED` — and a Level 2 beneath (`05.02 Air Filter / Cleaner`, `01.01 Cylinder Block & Crankshaft`).

It also carries a full commercial segmentation the catalogue tree does not have: ABC revenue contribution × XYZ sales velocity × margin tier, resolving to nine named segments (FLAGSHIP, CORE, STRATEGIC HIGH, VOLUME DRIVER, STABLE, OPPORTUNITY, TAIL RUNNER, MANAGED, LONG TAIL) with A-X at 407 parts and 65.1% of revenue.

**Its air-filter node independently confirms finding 1.** `05.02 Air Filter / Cleaner` holds 54 parts and €726,020 of revenue on its own basis. Cross-checking those same 54 part numbers against the catalogue tree:

| where the catalogue tree puts them | parts | billed € (my window) |
|---|---|---|
| Air conditioning > Other A/C | 37 | 1,002,750 |
| Air system > Other air system | 3 | 162,260 |
| Air system > Air hose / pipe | 4 | 520 |
| Filters > Air filter | 10 | 42,460 |

Two classifications built independently, six months apart, disagree on €1.16M — and the unwired one is correct.

**But do not simply adopt it, because it has its own systematic defect.** The `PARTS FUNCTIONAL` sheet appears to have been sorted by description and filled downwards, so the first Level-2 node absorbed everything alphabetically near it. `01.01 Cylinder Block & Crankshaft` holds 312 parts, of which **145 are simply called "BEARING"**. Of the 233 parts whose description starts with BEARING, **147 land in the engine block node**, and at least **59 are provably gearbox or axle bearings**: `BEARING; BALL,MAINSHAFT`, `BEARING; BALL,INPUT SHAFT`, `BEARING; COUNTERSHAFT,FRT`, `BEARING; BALL,OUTPUT SHAFT`, `BEARING; AXLE SHAFT,FRT`. Those belong to `06 DRIVETRAIN & CLUTCH`, where 84 other bearings correctly sit.

So each taxonomy is right where the others are wrong. That is a reasonable position to be in — it is the argument for reconciling them rather than picking one. It is not a reasonable position to leave undocumented, which is where it is today: four trees, no precedence rule, and a gate that checks only one of them against a copy of itself.

---

## 5. Is Level 1 a valid axis at all?

This is the deepest problem, and it is a design question rather than a bug.

Level 1 is a **commercial posture**: *Competitive parts / Repair parts / Accident parts / High value repair / Comfort parts / Hardware & consumables*. It was assigned by a text rule reading the part noun.

Competitive exposure is not a property of a part's name. It is a property of a market: whether an independent brand offers that part, for that vehicle, in that country, at what price. The same brake disc is competitive in Germany with three aftermarket brands on the shelf and captive in Armenia with none. One label per part number, derived from a noun, cannot carry that.

The claim is falsifiable, so I tested it against the independent-brand price scrapes we hold (Autodoc, KS, Mekonomen):

| assigned Level 1 | scraped | independent brand found | hit rate |
|---|---|---|---|
| Competitive parts | 119 | 66 | **55.5%** |
| High value repair | 34 | 18 | 52.9% |
| Repair parts | 47 | 17 | 36.2% |
| Accident parts | 66 | 15 | 22.7% |
| Comfort parts | 18 | 14 | 77.8% |

Labelled Competitive: 55.5% have an independent-brand match. Labelled anything else: 38.8%. **Lift 1.43x**, where 1.00x would mean the label carries no information.

So the label is better than nothing and much weaker than its name implies. Turned round: of the 137 parts where an independent-brand alternative was actually confirmed, **only 48.2% sit in "Competitive parts"** — the label misses more than half of the competition we have already proven exists.

**Two honest caveats.** The sample is 302 parts, and it was not drawn at random — Competitive parts is 39.4% of the scrape list against 25.8% of the catalogue, so somebody already suspected these. Read the lift, not the absolute rate. This is a directional result on a small biased sample, not a measurement.

**This is exactly where EQ access would pay.** `aim_gap_suggestions_20260702.csv` already has an `eq_hit` column — and it is **empty on all 987 rows**. Somebody built the slot and never filled it. With EQ coverage the test above goes from n=302 to the whole competitive book, and the question "is this part actually contested" gets answered from evidence per market instead of inferred from its name. That is the one input that would let Level 1 be rebuilt as a measured attribute rather than a guessed one.

---

## 6. Is the leaf level fine enough to act on?

A leaf is usable if the parts in it are commercially alike. Two symptoms of a leaf that is too coarse: it mixes physically different goods, or one part number *is* the leaf.

**34 leaves carry €250k+ and fail on dispersion or concentration. Together they are €30,945,204 — 65.1% of the 18-month book.**

Worst of them:

| leaf | billed € | parts | distinct HS6 | distinct nouns | top part % |
|---|---|---|---|---|---|
| Electrical sensors > Sensor | 4,624,608 | 1,108 | 29 | 33 | 23.4% |
| Brake parts > Brake disc | 2,057,926 | 475 | 9 | 17 | **48.5%** |
| Exhaust > Aftertreatment | 2,038,790 | 2,241 | **45** | **71** | 20.0% |
| Steering > Steering gear / unit | 1,923,171 | 1,208 | 20 | 36 | **64.4%** |
| Body parts > Bumper | 1,563,028 | 1,479 | 16 | 42 | 14.8% |
| Air conditioning > Other A/C | 1,113,634 | 780 | 38 | 44 | 34.3% |
| Filters > Other filter | 992,218 | 237 | 22 | 38 | **46.4%** |
| Body parts > Door | 828,961 | 6,153 | 32 | **94** | 7.9% |

**Fifteen leaves are effectively one part number wearing a family name** (top part ≥40% of leaf euro, leaf over €100k): `Exhaust pipe` 71.9%, `Brake drum` 69.0%, `Clutch kit` 66.5%, `Steering gear / unit` 64.4%, `Injector` 62.2%, `Fuel pump` 52.7%, `Radiator` 51.4%, `Brake disc` 48.5%, `Blower / fan` 48.1%, `Silencer / muffler` 48.2%, `Other filter` 46.4%, `Control unit` 42.3%, `Other cooling` 41.0%, `Gear set / gear` 40.2%, `Other fuel system` 40.3%.

When somebody says "brake discs rose 7.8%", roughly half of that is one part number.

And the price spread inside single leaves shows how much is being lumped:

| leaf | min | median | max | max/median |
|---|---|---|---|---|
| Body parts > Other body | 0 | 12 | 16,615 | **1,435x** |
| Exhaust > Aftertreatment | 0 | 11 | 11,518 | **1,015x** |
| Body parts > Door | 0 | 28 | 9,163 | 333x |
| Gaskets / seals > Oil seal / seal | 0 | 7 | 1,980 | 280x |
| Transmission parts > Differential / axle | 0 | 14 | 3,503 | 246x |
| Filters > Oil filter | 1 | 14 | 1,473 | 103x |

A leaf holding both a €0 item and a €16,615 item is not a pricing unit.

### The residual

| bucket | parts | billed € | share of billed |
|---|---|---|---|
| `Other / review > Miscellaneous > Review needed` | 9,856 | 2,355,091 | 4.64% |
| no node at all | 57 | 819,772 | 1.62% |
| any Level 3 beginning "Other" | 16,574 | 6,045,405 | 11.92% |
| **combined** | **26,487** | **9,220,268** | **18.18%** |

Nearly one euro in five of billed parts sits in a box whose name admits it is not a category. Every family has its own overflow bin, and they are among the largest leaves in that family:

| overflow leaf | parts | billed € |
|---|---|---|
| Air system > Other air system | 1,877 | 394,485 |
| Gaskets / seals > Other gasket / seal | 1,801 | 330,741 |
| Body parts > Other body | 1,771 | 432,973 |
| Clutch parts > Other clutch | 1,651 | 219,485 |
| Brake parts > Other brake | 1,649 | 203,948 |
| Steering > Other steering | 1,618 | 145,960 |
| Lighting > Other lighting | 1,166 | 102,150 |
| Transmission parts > Other transmission | 983 | 875,971 |
| Air conditioning > Other A/C | 780 | 1,113,634 |
| Hydraulic / mechanical > Other mechanical | 776 | 581,187 |
| Cooling > Other cooling | 703 | 375,150 |

---

## 7. How this compares to the rest of the industry

Three reference points, all public.

**Volvo Trucks — the closest analogue, a commercial-vehicle OEM's own catalogue.** Volvo Impact uses **function groups 0–9**, then a 2-digit level (e.g. `51`), then a 3-digit level (e.g. `511`) which carries the chassis-specific detail. Ten top groups: 0 General · 1 Service and maintenance · 2 Engine, mounting and equipment · 3 Electrical system and instruments · 4 Power transmission · 5 Brakes · 6 Wheel suspension and steering · 7 Frame, springs, damping and wheels · 8 Body, cab and interior · 9 Miscellaneous. Three levels reaching roughly a thousand nodes.
Sources: [Volvo Impact function groups](https://servicepartmanuals.com/partmanual/volvo-impact-trucks-buses-2019-11-2018-spare-parts-catalog/), [function group levels](https://www.auto-epc.org/archive/index.php?thread-4694.html=)

Two things stand out against ours. Volvo's top level is **purely functional** — it says where the part is on the truck, never how it competes. And **"Service and maintenance" is its own group**, so scheduled-service parts are addressable as a set instead of scattered across Filters, Air conditioning and Air system the way our air filters are.

**Isuzu's own scheme — and it is publicly documented.** Every section and illustration carries a 3-digit Figure Number in the form `X-XX`. The catalogue's own "How to refer to Parts Catalog" page states that the first digit identifies the primary section and the second and third the subsection — `0-15` = Engine (0), Crankshaft/Piston/Flywheel (15) — with a letter suffix where a chapter has multiple sections (`0-15A`, `0-15B`). Ten top sections: 0 engine · 1 intake/cooling/fuel/exhaust · 2 clutch and transmission · 3 brakes · 4 propeller shaft, axles, steering, suspension, wheels · 5 frame and cab mounting · 6 cab and body panels · 7 trim, mirrors, instrument panel, seats · 8 electrical, heater and A/C · 9 tools. On the order of 150–250 figure numbers per model catalogue; the live price master carries **297** distinct figure numbers.
Sources: [NPS81/NQR81 parts catalogue](https://www.scribd.com/document/881607336/Catalog-NPS81-NQR81), [Giga CYZ figure list](https://www.autorepairmanuals.ws/arm/threads/isuzu-truck-giga-cyz-rhd-parts-catalog-1-8871-1022-0-2006.213300/)

**TecDoc / TecAlliance — the European aftermarket standard, and the most useful comparator we have.** Articles are classified to **generic articles** (5-digit `GenArtNo`) carrying a **standardised designation** held in its own table, an **assembly group**, a **purpose of use**, and typed **criteria** with mandatory / permitted / forbidden status.

The number that matters: TecAlliance rolls its **~9,900 generic articles** up into **32 main product groups and 160 sub-categories** for commercial sales reporting to the six international trading groups. That is a published, real-world commercial rollup sitting on top of the functional standard.
Sources: [TecAlliance myITG reporting structure, 9 May 2023](https://www.tecalliance.co.za/myitg-revolutionises-sales-reporting-to-itgs/), [TecDoc Data Format spec](https://dwnld.aws.tecalliance.com/TecDoc/Downloads/TecDoc-Data-Format.pdf) (tables 320 Generic Articles, 323 Standardised Article Description, 324 Assembly Groups, 331–333 Criteria)

A trap to avoid when quoting this: TecAlliance's current product pages advertise "360+ generic articles" and "35+ product groups", but that is the coverage of the *OE Parts Data* product only, not the size of the standard. I used that figure in my own first pass and it was wrong.

**ACES / PIES — the US standard.** The Product Classification database (PCdb) is a category → subcategory → part terminology hierarchy with **40,000+ part terminologies**. The attribute database (PAdb) adds **9,700+ part attributes** and 141,700+ attribute associations assigned per terminology, with one part type carrying up to 144 attributes. ACES 5.0 / PIES 8.0 became official 26 March 2026. Auto Care does not publish the category and subcategory counts.
Sources: [Auto Care PCdb](https://www.autocare.org/data-and-information/data-standards/databases/product-classification-database-pcdb), [PAdb](https://www.autocare.org/data-and-information/data-standards/databases/product-attribute-database-padb), [ACES 5.0 / PIES 8.0 release](https://www.autocare.org/news/latest-news/details/2026/04/02/auto-care-association-releases-aces--5.0-and-pies--8.0)

### What the comparison says

**Correcting my own first reading.** I initially wrote that our 172 leaves sat against "industry standards of 360 to 40,000" and that we were not in the same order of magnitude. That framing was wrong, because it compared our *commercial reporting grain* against TecDoc's *fitment-identification grain*. The right comparison is against TecDoc's commercial rollup:

| | our tree | Isuzu figures | Volvo | TecDoc | PCdb / PAdb |
|---|---|---|---|---|---|
| top level | 7 posture families | 10 sections | 10 function groups | 32 main product groups | categories (n/p) |
| second level | 25 groups | ~30 subsections | ~100 (2-digit) | **160 sub-categories** | subcategories (n/p) |
| leaf / identity grain | **171 leaves** | 297 figures in PR00 | ~1,000 (3-digit) | ~9,900 generic articles | 40,000+ terminologies |
| attributes per leaf | **none** | none | — | mandatory + proposed criteria | 9,700+ attributes |
| top level is | commercial | functional | functional | functional | functional |
| service parts | scattered | — | own group (1) | — | — |

Read that way, **7 / 25 / 171 is a credible commercial structure.** It is the same order as TecDoc's 32 / 160 reporting rollup, the same order as Isuzu's own 10 sections and 297 figures, and the same order as Volvo's 10 function groups. The leaf count is not the problem, and I should not have said it was.

The three real gaps are these:

**1. Nobody else puts a commercial judgement in the identity.** Isuzu's own figures, Volvo, TecDoc and PCdb all classify *what the part is*. TecDoc's commercial rollup is **derived from** the functional keys and allowed to change on its own schedule — TecAlliance's stated reason for building it that way rather than replacing the keys is that suppliers then need no new implementation. We instead fused the two into one Level 1, which is why a king pin kit lands in "Hardware & consumables" and stops being visible as a wear item, and why the "Competitive" label catches under half the competition we can prove.

**2. There is no attribute layer, and this is the actual gap.** TecDoc's criteria and PAdb's attributes are what make a category actionable — you can address every brake disc of a given diameter and thickness. Our leaves have no attributes at all, which is exactly why `Brake parts > Brake disc` is 475 parts with one of them at 48.5% of the euro, and why 34 leaves carrying 65% of the book fail on dispersion. That is a missing dimension, not a missing level.

**3. eCl@ss writes down the rule we broke.** In eCl@ss 16.0 (48,283 classes, published 28 Nov 2025), spare parts get a dedicated fourth-level "91" class which **deliberately drops all product-describing properties**, explicitly "to avoid that a certain product can be described as a distinct product class and as a parts-class for another parent product" ([eCl@ss classification class spec](https://eclass.eu/support/technical-specification/structure-and-elements/classification-class)). That is a standards body stating the one-thing-one-home rule — which is precisely the rule our gaskets, harnesses and pipes break in section 2.5(b).

### On the commercial axis specifically

There is no consultancy-published named segment list for parts posture, so our Level-1 vocabulary is not deviating from a standard — there is no standard to deviate from. What does exist:

- **captive / semi-captive / commercial** is the working vocabulary in service-parts pricing practice, scored from make-or-buy, competitor count, product group, volume, suppliers, market share and lifecycle stage ([Syncron, product segmentation](https://www.syncron.com/blog/optimizing-returns-with-smarter-product-segmentation-part-two)). That is a *scored* attribute built from several inputs — closer to what section 5 argues we need than to a label derived from a noun.
- **McKinsey's current position argues against what we do.** With catalogues of 100,000+ parts, pricing at "the product (sub-)category level or even the portfolio level" is the problem; the recommendation is learned "microsegments" of SKUs with similar pricing power, clustered on customer, manufacturer and geospatial parameters beyond the product itself, with 2–6% of sales as the reported uplift ([The future of aftermarket pricing](https://www.mckinsey.com/industries/automotive-and-assembly/our-insights/the-future-of-aftermarket-pricing-unlocking-value-with-ai)). Syncron makes the same point bluntly: "rather than simplistic groupings like product category, sales volume or region, segments should be based on a variety of market behavior characteristics."
- **The one legally fixed boundary** is EU Regulation 461/2010, which distinguishes "original spare parts" from "spare parts of matching quality". That is a property of the *competing* part, an input to exposure, not a label for our own SKU ([Case C-354/14, quoting the definitions](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A62014CJ0354)).
- **A warning on A/B/C.** In published literature ABC means consumption-value inventory classification, not competitive exposure. The Mar-2026 functional workbook already uses ABC in that correct inventory sense. If the word is ever used internally to mean price sensitivity, say so explicitly, because every external reader will hear consumption value.

**Negative finding worth recording:** there is no VDA or Odette standard for parts *grouping*. VDA 9004, 9007 and 9008 cover spare-part identification codes, Data Matrix logistics master data and packaging-information exchange — identification and packaging, not taxonomy. TecDoc is the European de facto standard for grouping, and "compliant" in practice means mapped to generic articles.

---

## 8. What I would do, in order

1. **Fix `ACL` → air cleaner.** ~~One token, €1.16M…~~ **DONE 2026-09-17.** 128 PNs / €1.16M moved to `Filters > Air filter`. Leaf after patch: €1.20M / 260 PNs (18-month spine). NOTES §7/§13 caveats withdrawn; Focus tables still need `build_aim_catalog_breakdown.py` rebuild to refresh the 12-month cut.
2. **Fix the five other wrong-system classes** — king pin, ball joint, drag link, bumper bar, window regulator. ~~1,146 parts, €683k…~~ **DONE 2026-09-17** with item 1 (1,146 PNs / €683k). All six rules: **0 residual wrongs** on re-run desctest. Patch: `01_data/90_INBOX/_patch_cls_eq_confirmed_20260917.py`; gate PASS.
3. **Stop the gate claiming verification it does not do.** ~~Either rename…~~ **DONE 2026-09-17.** Gate check renamed to `pr00_copy_integrity` (honest copy-only note). Independent floors added: HS6 coherence ≥55% (live 63%) and figure purity ≥65% (live 72%). `verify_aim_classification.py` PASS 17/17 after residual pass-2.
4. **Fix the key normalisation** so the 1,616 leading-zero parts are actually checked. ~~…~~ **DONE 2026-09-17.** PR00 build `_norm` → `zfill(10)`; gate `leading_zero_keys_present` = 1,615.
5. **Decide the successor rule.** ~~Either classify…~~ **DONE 2026-09-17 — own row wins.** `build_pr00_classification.py` overwrites on own P/N; Newest only fills absent keys. Live check: 4,859 divergent pairs keep own; 17 still inherit Newest at €0 (`01_data/90_INBOX/_verify_cls_supersession_live_20260917.json`).
5b. **Other / review residual (start).** Pass-1 six-class rules moved **0** (those misfiles were not in the residual bin). Pass-2 high-precision heads moved **333 PNs / €608k** (wiper blade, gate/transfer/throttle ASM, belt tensioner, pad kit, LLC, ELEMENT KIT). Leftover ~9.5k PNs / ~€1.75M need figure-key/EQ or new-leaf calls — see `_START_Other_Review_residual_20260917.md`.
6. **Split the axes.** ~~One functional tree…~~ **LOCKED 2026-09-17 — Jerome: proceed with two axes.** Axis A = identity only (`catalog_l1/l2/l3`, figure-anchored; existing three levels only). Axis B = commercial score beside that (contested per part per market) — **not** the hang-from parent. No fourth layer. See `DECISIONS.md` 2026-09-17.
7. **Get EQ in.** The `eq_hit` column is already there and empty. Rule-class probes confirmed the six corrections (14/40); systematic fill of the column is still open.
8. **Decide on object-vs-system for gaskets, harnesses and pipes** and apply it once. 2,272 parts, either way, but pick one. eCl@ss's "91" rule is the precedent for making that decision explicit. **Still needs your call.**
9. **Write down which of the four taxonomies wins, for what.** ~~cheapest item…~~ **DONE 2026-09-17** — table in `DECISIONS.md` 2026-09-17 (two-axes entry) and `aim_catalog_breakdown_NOTES.md` §0.
10. **Add an attribute layer before adding leaves.** Section 7 corrects my own first reading: 7/25/171 is a credible commercial grain, the same order as TecDoc's 32/160 reporting rollup and Isuzu's own 297 figures. The gap is that our leaves carry no attributes, which is why one part number can be half a family. More levels would not fix that; dimensions would. **ON HOLD 2026-09-17 — Jerome: deferred / later (doing too much right now).** Not “proceed,” not this week’s call. Attributes-before-levels stays the recommended order when work resumes; no new catalogue levels implied. See `DECISIONS.md` 2026-09-17 (attribute layer on hold).

Items 1–6 and 9 are closed. Item 10 is on hold (roadmap). Items 7–8 remain open.

---

## EQ-Hit validation (2026-09-17)

Live checks on `https://isuzu.snaponepc.com/epc/#/` against `_eq_hit_probe_pns.json`. Machine record: `01_data/00_derived/_eq_hit_validation_20260917.json`.

**14 of 40 probed so far. Every disputed rule class has at least one EQ hit that confirms the misfile.** Remaining rows are mostly more ACL / king-pin / drag-link duplicates of the same patterns.

| Rule | EQ says | Our tree had | Confirmed PNs (examples) |
|---|---|---|---|
| air_filtration (`FILTER; ACL`) | **1-30 - AIR CLEANER** | Comfort > A/C | 8974995480, 8981772710, 8983214130, 8976739570 |
| steering_core (`LINK; DRAG`) | **4-33 - STEERING LINKAGE** | Hydraulic linkage | 8980256421, 8980067942 |
| bumper (`BAR; FRT BUMPER`) | **6-01 - FRONT BUMPER** | Suspension leaf spring | 8983621213, 8975471071 |
| ball_joint_arm | **4-50 - FRONT SUSPENSION** | Hydraulic linkage | 8980058750 |
| king_pin | **4-10 - FRONT AXLE** | Hardware > Pin | 5878324001 |
| window_regulator (`REGULATOR ASM; DOOR`) | **6-31 - FRONT DOOR GLASS AND REGULATOR** | Voltage regulator | 8980098112 |

What this locks for the ACL fix and the rest of §8: the OEM catalogue figure names match the description-rule corrections. ACL is not cabin A/C. Door regulator is not an alternator voltage regulator. King pin is not a hardware pin. Drag link and ball joint are steering / suspension, not a generic hydraulic leaf.

Three probed numbers returned nothing in global search (`5876100201`, `1876101132`, `5876150521`) — typically older 5*/1* truck PNs. Description + sibling EQ hits still carry those rules.

Status on the JSON: `IN_PROGRESS` (26 probe rows left). Rule-class evidence was enough; **§8 items 1–2 applied 2026-09-17** (1,274 violation PNs patched in `aim_pn_classification.csv` + `pr00_classification.csv`, v2 rebuilt, `verify_aim_classification.py` PASS).

## Method and reproducibility

Every figure above was computed in this audit, not copied from another document. Scripts, in order, all under `01_data/91_build/`:

| script | what it does |
|---|---|
| `_audit_cls_00_inventory.py` | description coverage, leaf granularity, source inventory |
| `_audit_cls_01_descspine.py` | builds the part → description → euro spine from 13 sources + sales grain |
| `_audit_cls_02_pr00src.py` | opens the classified workbook and the live price master |
| `_audit_cls_03_loadprice.py` | reads the workbook's stated method + taxonomy, flattens the price master |
| `_audit_cls_04_join.py` | the audit spine; residual mass; noun-head consistency |
| `_audit_cls_05_independent.py` | HS commodity-code and figure cross-checks; description clashes |
| `_audit_cls_06_selfconsistency.py` | determinism test on the source workbook |
| `_audit_cls_07_drift.py` | 13-Mar vs 10-Aug description diff |
| `_audit_cls_08_supersession.py` | replays the builder; quantifies both build defects |
| `_audit_cls_09_desctest.py` | the 22 high-precision description rules |
| `_audit_cls_10_airfilter.py` | air filtration sizing and split |
| `_audit_cls_11_context.py` | fleet denominators; EQ evidence check |
| `_audit_cls_12_validity.py` | does "Competitive parts" predict competition |
| `_audit_cls_14_pms_impact.py` | traces the misfile into `pms_category` (air filter PASS, king pin FAIL) |
| `_audit_cls_15_functional.py` | opens the unwired Mar-2026 functional workbook |
| `_audit_cls_16_functional_qa.py` | QAs that workbook; cross-checks it against the catalogue tree |
| `_audit_cls_13_granularity.py` | leaf quality, concentration, price spread |

Outputs, all under `01_data/00_derived/`:

| file | contents |
|---|---|
| `_audit_cls_description_violations.csv` | every misfiled part, with rule, HS code, figure, list price, billed euro |
| `_audit_cls_successor_inheritance.csv` | the 1,083 parts whose node came from a different part |
| `_audit_cls_leaf_quality.csv` | all 171 leaves with dispersion, concentration and price-spread metrics |
| `_audit_cls_description_drift.csv` | the 23 changed descriptions |
| `_audit_cls_spine.csv` | the joined audit spine (164,667 rows) |
| `_audit_cls_desc_spine.csv` | part → best description → billed euro |
| `_audit_cls_pr00_flat.csv` | the price master flattened (165,358 rows) |
| `_audit_cls_05_out.txt` … `_13_out.txt` | full console output of each step |

Sources read:
`01_data/01_Pricing/IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx` ·
`01_data/01_Pricing/Price_file_PR00_IE40_20260810.xlsx` ·
`01_data/00_derived/aim_pn_classification_v2.csv` · `aim_pn_classification.csv` · `pr00_classification.csv` ·
`sales_fact.parquet` · `gps_spu_by_distributor.csv` · `price_bp_weighted_compare_pn.csv` ·
`competitiveness_autodoc_risk.csv` · `iam_ks_price_gap.csv` · `iam_mekonomen_price_gap.csv` ·
`aim_gap_suggestions_20260702.csv` ·
`03_analytics/Isuzu/prism/scripts/build_pr00_classification.py` ·
`01_data/91_build/build_aim_classification_v2.py` · `verify_aim_classification.py` ·
`01_data/00_derived/aim_catalog_breakdown_NOTES.md` ·
`03_analytics/Isuzu/prism/docs/AIM_CLASSIFICATION_AUDIT_2026-09-17.md`

Also read for the parallel-taxonomy section:
`03_analytics/Isuzu/prism/data/fig_key_taxonomy.yaml` ·
`01_data/00_derived/parts_catalog_dimension.csv` ·
`01_data/01_Pricing/ISZE_Parts_Sales_Classification_Mar2026_v2.xlsx`

**Not claimed / not checked:** whether the 31,098 successor keys with no own row are correctly inherited (unexamined, not proven wrong); whether any downstream pack other than the catalogue note has published the understated air-filter figure (consumer sweep not done); the two Level-1 vocabularies in `aim_l1`, already covered by the 17 Sep file audit and not re-litigated here; the remaining 13 service categories in `fig_key_taxonomy.yaml` beyond air filter and king pin (only those two were traced end to end); the BVP catalogue sheet map, which is a fifth mapping layer I did not audit.

**Corrections I made to my own earlier draft of this audit**, recorded so the reasoning is auditable: (a) I claimed PMS air-filter capture was corrupted — it is not, the figure-key layer tags 99.98% of the euro correctly; (b) I framed 172 leaves as an order-of-magnitude shortfall against industry standards — wrong comparison, the right comparator is TecDoc's 32/160 commercial rollup and we are in the same order; (c) I quoted TecDoc at "360+ generic articles", which is one product's coverage, not the standard's ~9,900; (d) my first price parse dropped all 7,001 parts over €1,000.
