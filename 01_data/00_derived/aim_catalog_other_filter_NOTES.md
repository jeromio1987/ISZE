# `Other filter` decomposed - what is actually in the bucket

Internal working note, blunt, not a shareable deck. Built 2026-09-17 by
`01_data/91_build/build_other_filter_split.py`.

Question: Jerome asked why a part family he classified sits in `Other filter`, and to treat that
part separately. This note answers what `Other filter` really contains and whether it can be
analysed as a product story.

Basis: `catalog_full` - the catalogue columns (`catalog_l1` / `catalog_l2` / `catalog_l3`) on **all**
rows, not restricted to `aim_source == 'pr00_catalog'`. That restriction keeps only 13.5% of the euro
and would drop the largest part numbers; see `aim_catalog_breakdown_NOTES.md` section 4.

---

## 1. Exact size and reconciliation

`Competitive parts > Filters > Other filter`, in-scope billed rows, L12M to 2026-06-30:

| Measure | Recomputed here | `aim_catalog_focus_filters.csv` network line | Delta |
|---|---|---|---|
| Part numbers billed | 48 | 48 | 0 |
| L12M quantity | 6,655 | 6,655 | 0 |
| L12M billed euro | 668,819.46 | 668,819.46 | 0.00 |
| Step euro | 27,774.10 | 27,774.10 | 0.00 |
| Weighted increase | 4.6841% | 4.6841% | 0.00 pp |
| Quantity priced on both sides | 6,652 | 6,652 | 0 |

**Ties out exactly.** The per-distributor lines in the same file also sum to 668,819.46 on 6,655
units, so the network line is a true sum of the parts, not a separately computed figure.

Two scope notes, so the numbers cannot be misread later:

* The taxonomy holds **237** part numbers under this node. Only **48** billed in the window. The
  other 189 are catalogue entries with no billing. Of those 189, only **14 carry any description at
  all** but **182 carry a figure key**, so the group table projects them onto the groups using the
  catalogue's own figure grouping. That projection raises the aftertreatment group from 8 billed part
  numbers to **37 in the taxonomy** and the strainers from 16 to **20**; it does not change a single
  euro figure, because none of them billed. The `n_pn_in_taxonomy` column is therefore a projection
  and is labelled as such. 147 of the 189 remain genuinely unresolvable.
* Rows billed but **excluded from the network**: 9 rows, 56 units, **6,232.08 EUR** - 4 rows on the
  IMG direct account (3,675.73 EUR, including 3 units of the big part) and 5 on non-customer
  accounts (2,556.35 EUR). They are outside the distributor network and outside every figure below.

---

## 2. What is actually in it

Grouping used `description_norm` and billed description first, then the catalogue figure key, then
the other vocabulary (`aim_l2` / `aim_l3`, `pms_category`, `filter_part_role`, `bp_new_class`). The
rules are in the builder and are reproducible; each part number carries the rule that fired.

| Group | PN billed | L12M qty | L12M billed EUR | Share of bucket | EUR per unit | Step EUR | Weighted increase | EUR per truck |
|---|---|---|---|---|---|---|---|---|
| Aftertreatment filter assemblies (exhaust particulate) | 8 | 537 | 494,115.49 | 73.88% | 920.14 | 18,183.45 | 4.05% | 7.04 |
| Urea / DEF (AdBlue) filter elements and kits | 4 | 1,200 | 74,896.20 | 11.20% | 62.41 | 3,860.74 | 6.54% | 1.65 |
| Crankcase ventilation (VCV) filter assemblies | 1 | 1,438 | 65,593.32 | 9.81% | 45.61 | 3,873.90 | 7.00% | see note |
| Hydraulic / transmission strainers and screens | 16 | 1,298 | 26,629.19 | 3.98% | 20.52 | 1,580.42 | 7.02% | 0.16 |
| Gaskets and seals sold with filters | 9 | 2,127 | 6,778.13 | 1.01% | 3.19 | 229.81 | 3.77% | too small to show |
| Filter covers, pipes and fitting hardware | 2 | 13 | 360.35 | 0.05% | 27.72 | 23.99 | 7.01% | too small to show |
| Oil-filter elements filed under Other filter | 1 | 22 | 155.50 | 0.02% | 7.07 | 8.20 | 5.02% | too small to show |
| Non-filter parts (exhaust, tools, other) | 2 | 10 | 104.29 | 0.02% | 10.43 | 6.26 | 7.04% | too small to show |
| Unresolved filter parts (no product evidence) | 5 | 10 | 186.99 | 0.03% | 18.70 | 7.34 | 7.03% | too small to show |
| **TOTAL** | **48** | **6,655** | **668,819.46** | **100.00%** | **100.50** | **27,774.10** | **4.68%** | **4.08** |

EUR per truck is struck on **unique markets**, not on customer rows: a market that bills the same
group on several customer codes would otherwise be counted several times (Denmark and Portugal do
exactly that on the VCV part). Group rates use the fleet of the markets that actually bill that group,
which is why the aftertreatment rate is over 70,148 trucks and not the full network. The bucket rate
is 668,819 EUR over **163,459 trucks in the 18 markets that have a 2025 count**. Armenia, Kazakhstan,
Palestine and Ukraine have no count by design and are excluded from every rate, never divided into.

Which market bills what, for the three groups worth a line:

| Group | Top market | EUR | Share of group | Markets billing it | Fleet of those markets | EUR per truck |
|---|---|---|---|---|---|---|
| Aftertreatment assemblies | ITUK | 249,994 | 50.6% | 7 | 70,148 | 7.04 |
| - of which second | UTI | 215,813 | 43.7% | | | 20.88 on 10,336 UTI trucks |
| Urea / DEF kits | ITUK | 72,267 | 96.5% | 5 | 45,523 | 1.65 |
| Strainers and screens | NORWAY | 7,510 | 28.2% | 21 | 163,459 | 0.16 |

### Group notes, including the ones that do not behave like a portfolio

**Aftertreatment filter assemblies - 494,115 EUR, 73.9% of the bucket, 21.0% of the whole Filters
node.** Eight part numbers, all `FILTER ASM`, all figure `150-558`, all price class D, all on the
same +4.0% base-price step. List prices run 111,280 to 219,208 JPY, i.e. 680 to 1,340 EUR per unit,
against 45.61 EUR per unit for a VCV filter and 3.19 EUR for a filter gasket. **920.14 EUR a
unit average** against 100.50 EUR for the bucket as a whole and 3.19 EUR for the gaskets. These are
not consumables. Two hands take 94.3%: ITUK 249,994 EUR and UTI 215,813 EUR. The rest is 10,990 EUR
in Portugal, 7,374 in Germany, 5,313 in Belgium, 3,709 in Ireland, 923 in Greece.

**Urea / DEF (AdBlue) filter elements and kits - 74,896 EUR, 11.2%.** Four `FILTER KIT; PUMP ASM,DEF
DCM S` numbers on figure `146-152`, two of them a supersession pair (8983507160 superseded by
8983507161). This is the one group that genuinely belongs to a maintenance schedule - it is the
filter in the DEF dosing module. But it is an **ITUK line**: 72,267 of the 74,896 EUR, 96.5%. The
concentration is the story, not the rate: 1.65 EUR per truck across the five markets that bill it is
a thin number resting on one distributor. There is no network pattern to draw from it.

**Crankcase ventilation (VCV) filter assembly - 65,593 EUR, 9.8%.** One part number, `7552026060
FILTER ASM; VCV`, 1,438 units, figure `057-018`. It spreads over 14 markets but is **not** a
consumption rate: against the 127,419 trucks in service in those 14 markets it is 0.0113 units per
truck per year, an implied **88.6 years** between replacements. That is not a service interval, it is
stocking. **UMI alone is 947 of the 1,438 units (65.9%) and 41,805 of the 65,593 EUR (63.7%)**, with
IUK 250 units, Norway 69, Portugal 42, Sweden 38, Belgium 33 and everything else in single or double
digits. Read the two Israel rows separately - UMI (1797) bills this part, UTI (1799) bills none of it.
So the group is a stock movement in one market in one year plus a real but small replacement flow
elsewhere. Two caveats hold: it is the only member of its group, so the 7.00% weighted increase is one
part number's price move; and the 0.51 EUR per truck is dominated by that stock movement, so the
builder deliberately returns no per-truck figure for it at all.

**Hydraulic / transmission strainers and screens - 26,629 EUR, 4.0%.** Sixteen part numbers:
automatic-transmission oil strainers, a power-steering tank strainer, oil-pump strainers, strainer
covers, strainer pipes and one eye bolt. It bills in **21 markets** - broader than anything else in
the bucket - at 0.16 EUR per truck, and it is the only group here whose rate is not concentrated:
Norway is 28.2% and ITUK 13.7%, the top two together only 41.9%. These are workshop parts with a
long replacement life, not a price-recovery lever.

**The 7,585 EUR tail - 1.1% of the bucket, five groups.** 19 part numbers between them: filter
gaskets (1.01% - the largest single one is `8976282570 GASKET; FILTER,DEF` at 5,685 EUR), filter
covers and pipes, `FILTER; OIL,SUB` (155 EUR, which the other vocabulary already calls an oil-filter
element), an exhaust silencer, an oil-filter wrench, a brake-reservoir filter and a wheel-speed
sensor bushing. The largest member is 5,685 EUR. Nothing in here can carry a finding.

---

## 3. The single big part: `8982878080`

| | |
|---|---|
| Billed description | `FILTER ASM` |
| `description_norm` | `FILTER ASM` |
| `aim_l1` / `aim_l2` / `aim_l3` | Maintenance Service / Filters / **Filter Assembly** |
| `catalog_l1` / `l2` / `l3` | Competitive parts / Filters / **Other filter** |
| Figure key | `150-558`, label "Other filter" |
| `filter_part_role` | assembly |
| `aim_source` | `aim_workbook` (not PR00-sourced) |
| Price class | D |
| L12M quantity | 277 |
| L12M billed euro | 298,159.98 (44.58% of the bucket, 12.68% of the whole Filters node) |
| Base price new / prior | 148,897 / 143,170 JPY |
| Base-price step | +4.0001%, 9,690.77 EUR, **34.98 EUR per unit** |
| Net billed per unit | 1,076.39 EUR (bucket average 100.50 EUR) |

**What it actually is.** It is a **diesel particulate filter (DPF) assembly** for Isuzu 4HK1 engines -
NPR-HD / NPR-XD / NQR / NRR / FTR, roughly model years 2011-2023. External aftermarket catalogues
carry it as an exact replacement DPF, sold new or as a remanufactured / core-exchange unit, with
aftermarket equivalents C0309-SA, SG0803, GESI-0098 and DPFXFIT listings. The same catalogue entries
name its gasket kit (`8976110800`, `8976282570` - and `8976282570` is the 5,685 EUR `GASKET;
FILTER,DEF` sitting in this same bucket).

**Is it genuinely a filter?** Yes, physically - it is the exhaust soot filter. But it is not a
service-cartridge filter, and it is not an oil, fuel or air filter.

**By distributor - user ask is ITUK and UMI, but UMI does not buy it:**

| Distributor | Country | Qty | EUR | Step EUR | EUR per truck (2025) |
|---|---|---|---|---|---|
| UTI | Israel | 193 | 206,706.80 | 6,752.05 | 20.00 |
| ITUK | United Kingdom | 79 | 85,494.27 | 2,763.79 | 3.82 |
| Portugal | Portugal | 3 | 3,422.90 | 104.95 | 0.42 |
| Germany | Germany | 1 | 1,356.47 | 34.98 | 0.11 |
| Ireland | Ireland | 1 | 1,179.54 | 34.98 | 0.39 |

UTI bills 193 units on 10,336 trucks in service - **20.00 EUR per truck**, one part number, one
distributor, one country. ITUK is 79 units on 22,389 trucks - 3.82 EUR per truck. Israel is reported
as UTI (1799) and UMI (1797) as two rows always; **UMI did not bill this part number at all** in the
window. Each distributor row is a single customer code, so this is five purchases, not a distribution.

**The classification is internally inconsistent, and that is the real finding.** Three different
layers disagree about this same part:

| Layer | Says |
|---|---|
| PR00 catalogue columns (`catalog_l3`) | Filters -> **Other filter** |
| Workbook vocabulary (`aim_l1` / `aim_l2` / `aim_l3`) | **Maintenance Service** -> Filters -> Filter Assembly |
| Price-class cross in `aim_catalog_breakdown_NOTES.md` | The entire 516,387 EUR class-D block under Filters *is* the Other-filter block - i.e. class D behaves as an aftertreatment class, not a filter class |

The figure key does resolve it: `150-558` sits immediately beside `150-589` (DPD heat protector),
`150-617`, `150-633` (DEF front chamber), `150-638` (`CATALYST ASM; DEF`), `150-649` (filter
insulator), `150-651` (`INSULATOR ASM; SCR PIPE`), `150-655` (`COVER ASM; FILTER UPR`), `150-664`
and `150-666` (`BRACKET ASM; SCR ...`). That is the **exhaust aftertreatment figure group**. The
punchline: an `Exhaust > Aftertreatment` node already exists in the file with **2,241 part numbers**
in it, so the target node is not missing - it is being bypassed for these eight numbers. Two of the
39 members of figure `150-558` (8983064620, 8983064621) already sit under `Other / review > Review
needed` instead of this node. So the node assignment is not just arguable, it is already applied two
different ways inside one figure.

Report only - `aim_pn_classifier.py` is PRISM-owned and was not edited.

---

## 4. Verdict - is `Other filter` analysable?

**Partly. It is analysable, but not as a filter type, and never as one line on a chart.**

* Two groups - aftertreatment assemblies (73.9%) and VCV (9.8%) - are **83.7% of the bucket** and
  are **not** consumable filters. They cannot sit beside oil and air filters.
* The one group that is a genuine scheduled filter is **DEF** (11.2%), and it is 96.5% one
  distributor, so it is a line item for ITUK, not a network family.
* The two most defensible findings are **price per unit and concentration**, not price move:
  aftertreatment assemblies bill at 920 EUR a unit (bucket average 100.50 EUR) against 3.19 EUR for
  the filter gaskets, and two distributors take 94.3% of that group. The VCV group looks like
  consumption but is not - 63.7% of it is UMI stocking, which is why it has to be read market by
  market.
* Excluding the aftertreatment block, the rest of the bucket holds exactly **one** finding at the
  scale that survives Jerome's rule (euro + family + fleet): the strainer group, 26,629 EUR on 21
  markets at 0.16 EUR per truck, with no distributor above 28.2%. Everything else is
  company-concentrated and should be flagged, not charted.
* The classification is internally inconsistent for the same part (catalogue says Other filter,
  workbook says Maintenance Service, figure group says aftertreatment).

**Blunt version:** `Other filter` is not a fourth filter type. It is two product families that were
never consumables (exhaust aftertreatment and engine ventilation parts) plus one small industrial
parts group, and only about a tenth of it behaves like a filter schedule. The big part is a DPF, not
a filter cartridge, and it is one part number in one market.

---

## 5. Recommended presentation

**Yes - present the clean filter portfolio as oil, fuel and air only.** That is 1,681,821 EUR of the
2,350,640 EUR Filters node (71.5%) on 188,226 units, with a weighted increase of 3.42%.

Then show the remainder **separately**, as two named blocks and a collapsed residual:

1. **Exhaust aftertreatment filter assemblies** - 494,115 EUR, 73.9% of the remainder, 21.0% of the
   whole Filters node, 8 part numbers, 2-part-number concentration 94.3% (ITUK + UTI).
2. **Urea / DEF filter kits** - 74,896 EUR, 11.2% of the remainder, 4 part numbers, 96.5% ITUK.
3. **Other filter parts and strainers** - the remaining 99,808 EUR: VCV 65,593, strainers 26,629,
   gaskets 6,778, and 807 EUR across four groups too small to show. Named, not charted.

### Wording that makes clear it is not one product story

> Filters covers two different businesses. The first is **filter cartridges - oil, fuel and air** -
> 1.68M EUR of the 2.35M EUR, on 188,226 cartridges. The second is **exhaust aftertreatment and
> engine ventilation parts**, which are not cartridges and do not follow a cartridge lifecycle:
> 668,819 EUR (28.5%), of which 494,115 EUR is exhaust particulate filter assemblies at 920 EUR a
> unit - five times the 100.50 EUR bucket average - and 65,593 EUR is crankcase ventilation filter
> assemblies, two thirds of which is a single market's stock. The single largest number in the group is
> `8982878080`, a diesel particulate filter assembly: 298,160 EUR, 44.6% of the group, 277 units, and
> it is bought by exactly two distributors - UTI (193 units, 206,707 EUR) and ITUK (79 units,
> 85,494 EUR).

For the classification fix, the plain ask is: **move the `FILTER ASM` aftertreatment parts
(figure `150-558`, eight billed part numbers) out of `Competitive parts > Filters` and into the
existing `Exhaust > Aftertreatment` node; keep the DEF kits under `Filters` as a named sub-type; and
leave the strainers and VCV parts as a labelled "other filter parts" line rather than a filter type.**
That is a taxonomy change to a PRISM-owned file, so it is a request, not something this analysis did.

### What is big enough to be a finding, and what is not

| Show it | Why |
|---|---|
| Aftertreatment filter assemblies, 494,115 EUR | Euro + family (exhaust aftertreatment) + fleet (7.04 EUR/truck on the 70,148 trucks in the markets that bill it) + unit price (920 EUR) + concentration (two hands, 94.3%) |
| Urea / DEF filter kits, 74,896 EUR | Euro + family + fleet (1.65 EUR/truck). Label it as one distributor's line - 96.5% ITUK |
| Hydraulic / transmission strainers, 26,629 EUR | Euro + family + fleet (0.16 EUR/truck) on 21 markets, no distributor above 28.2% - the widest-based group in the bucket |
| Crankcase ventilation assembly, 65,593 EUR | Euro + family + unit price (45.61 EUR). Do **not** quote it as a lifecycle or a per-truck rate - 63.7% is one market's stock movement |
| **Do not show** | Gaskets 6,778; covers and pipes 360; oil-filter element 156; non-filter parts 104; unresolved 187. Combined 7,585 EUR (1.1%). Largest single member 5,685 EUR. Name them in one residual line, do not give them a chart or a percentage |

---

## 6. What could not be determined

* **No ISZE source states what `8982878080` is.** There is no description beyond `FILTER ASM` in the
  classification, the price file, or the catalogue dimension. The DPF identification comes from
  external aftermarket catalogue lookups by part number, not from an ISZE-owned document. Treat it as
  external evidence and re-check against the ISUZU parts catalogue before it goes into an external
  paper.
* **Same for the other aftertreatment numbers.** `8982050610` looks like a 4JJ1 DPF and `8982049420`
  is listed as a particulate filter for an N2R, but neither is confirmed from an ISZE document, and
  for `8975074440`, `8982336181`, `8980329082`, `8976080574` and `8978770040` no external lookup was
  run. The group is defended by the figure key and the price band, not by a resolved part name for
  every member.
* **`7552026060` VCV was not confirmed.** `VCV` is read as crankcase ventilation from the part name
  and figure. No lookup confirmed the application. The group is one part number, so a misread here
  moves 65,593 EUR. The group was also checked for a consumption rate and **has none** - 0.0113 units
  per truck per year across its 14 markets, an implied ~88 years between replacements. That is
  stocking behaviour, not a service interval, and 65.9% of the volume is UMI in one year. Do not
  quote a VCV replacement interval from this data.
* **The 189 unbilled part numbers are only partly classified.** 147 of them carry no description and
  no figure key that maps to a group, so they stay unresolved. The remaining ~42 are projected from
  their figure key (29 aftertreatment figures, 4 strainer figures, and a handful of covers and
  pipes). No euro is involved, because none of the 189 billed. If they ever start billing, the group
  table will need rebuilding rather than re-reading.
* **Denominators carry a documented defect.** The same 2025 fleet rows used here also feed
  `gps_spu_by_distributor.csv`. The `2026` row in `sales_by_db_fig_key_year.csv` is a partial year
  (the file covers 2026-01 to 2026-08), so any rate using 2026 GP spend is understated. That is a
  reason to rate on 2025, which is what this note does, not a defect in the euro figures here.
* **The strainer rate is thin.** 0.16 EUR per truck is a small number whose level is dominated by one
  part number (`8983417890`, 16,861 EUR of the 26,629 EUR). Treat the group's euro as solid and its
  rate as indicative only.
* **All rates here depend on the 2025 fleet row, and that file has a separate, documented defect.**
  The same `gps_spu_by_distributor.csv` also feeds `sales_by_db_fig_key_year.csv`, whose `2026` row is
  a partial year (2026-01 to 2026-08). That is a reason to rate on 2025, which is what this note does;
  it is not a defect in the euro figures here. If the 2025 fleet count is ever restated, every rate
  in this note moves with it.
* **Rates are struck on unique markets.** A first pass summed the fleet column per customer row and
  double-counted Denmark and Portugal on the VCV part (136,446 instead of 127,419 trucks). The outputs
  now carry the unique-market denominator and the group-by-distributor file, and the group-rate column
  returns nothing where the euro is concentrated in fewer than five markets.
* **No elasticity, no allocation, no price proposal, no new risk score.** Out of scope by instruction
  and not attempted. The weighted increase quoted throughout is a base-price move, not a revenue or
  margin outcome.

---

## 7. Files

* `01_data/00_derived/aim_catalog_other_filter_split.csv` - the group table, incl. a total row and
  the reconciliation columns.
* `01_data/00_derived/aim_catalog_other_filter_notable_pns.csv` - all 48 billed part numbers with
  group, quantity, euro, step, price, concentration and the rule that fired.
* `01_data/00_derived/aim_catalog_other_filter_by_distributor.csv` - the bucket by distributor.
* `01_data/00_derived/aim_catalog_other_filter_group_by_distributor.csv` - group x market, the only
  safe base for a rate or a concentration statement.
* `01_data/00_derived/aim_catalog_other_filter_meta.json` - reconciliation, big-part detail,
  out-of-scope rows, unbilled taxonomy tail, VCV consumption check, fleet caveats.
* Builder: `01_data/91_build/build_other_filter_split.py`.

Source taxonomy `03_analytics/Isuzu/prism/modules/aim_pn_classifier.py` was **not** modified.
