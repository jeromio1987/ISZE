# King-pin service category: before and after (2 Oct 2026)

**Status: not applied.** You agreed to point the king-pin rule at Steering > Knuckle / arm but asked to see the before and after first. Nothing has been edited. The rule file, the parts catalogue dimension and every page are as they were.

Euro = parts billed, last 12 months Sep 2025 to Aug 2026, all customers, from the billing table (total EUR 35,212,240). Catalogue = `pr00_classification.csv` as settled today from the approved release 2026-10-02-chassis-frame.

## In short

- **Today the rule tags 0 parts.** It looks for king pins inside the catalogue group "Suspension". No part there has "king" in its type (the Suspension types are leaf spring, shock absorber, hanger, stabilizer, bushing, rod, air spring, other). The king-pin parts are in Steering > Knuckle / arm.
- **Pointed at Steering > Knuckle / arm as agreed, it tags 1,014 parts, EUR 249,223.** Only about half of that is king pins. **533 parts / EUR 147,302 have "KING PIN" in the description. The other 481 parts / EUR 101,921 do not.** They are front-axle knuckles (KNUCKLE; FRT AXLE, the biggest share), knuckle arms, pitman arms, knuckle caps, and 383 parts with no description on file. All of them would be labelled "king pin kit".
- **No PMS or GPS figure changes.** King pin is not one of the 14 service families that the PMS figures use. It has no modelled demand, so the PMS cover and the PMS capture figures do not move.
- **One model does move: the lost-sales family split.** Those parts move out of their current family into "Other": EUR 244,675 from Suspension & chassis, plus EUR 4,548 from smaller families. That only happens when the catalogue dimension and the lost-sales model are next rebuilt.
- **Recommendation:** do not point the rule at the whole Knuckle / arm type. Point it at the king-pin figure keys instead. Figure key 410-004 alone holds 128 of the 129 parts on it and EUR 136,037; the other keys are listed below. The rule engine already supports rules by figure key. The decision is yours.

## What the rule is

- File: `03_analytics\Isuzu\prism\data\fig_key_taxonomy.yaml`, rule list `pr00_pms_category_rules`.
- Today: `match_group: "Suspension"` with `king: king_pin` (among shock, spring, bushing, bearing, seal).
- How it works: if the part's catalogue group contains "suspension" and its type contains "king", the part gets the service category `king_pin`. The rule writes into `pms_category` in `parts_catalog_dimension.csv` when that file is rebuilt (`03_analytics\Isuzu\prism\scripts\build_fig_key_dimension.py`).
- "After" was simulated as one added rule: group "Steering", type "Knuckle / arm" -> `king_pin`. Both runs used the real dimension builder on today's files, so BVP and registry precedence is the pipeline's own.

## Before and after

| | Before (today) | After (Knuckle / arm) |
|---|---:|---:|
| Parts tagged king pin | 0 | 1,014 |
| of which "KING PIN" in description | 0 | 533 |
| of which another description or none | 0 | 481 |
| Parts billed, last 12 months | EUR 0 | EUR 249,223 (91 parts, 11,536 units) |
| of which king-pin parts | EUR 0 | EUR 147,302 (37 parts, 6,194 units) |
| of which knuckles, arms, caps etc. | EUR 0 | EUR 101,921 (54 parts) |
| Parts billed, calendar 2025 | EUR 0 | EUR 275,105 (107 parts, 12,362 units) |

Largest parts that would be tagged (last 12 months): 5878324001 KING PIN KIT EUR 65,430; 5878323991 KING PIN KIT EUR 46,760; 8972615494 KNUCKLE; FRT AXLE EUR 15,444; 7552338520 KNUCKLE; FRT AXLE EUR 14,228; 8972615504 KNUCKLE; FRT AXLE EUR 13,238; 7552338510 KNUCKLE; FRT AXLE EUR 12,655; 5878324011 KING PIN KIT EUR 10,976.

## Per market (last 12 months)

| Market | After, all 1,014 parts: EUR | units | share of market's parts billed | of which king-pin parts only: EUR |
|---|---:|---:|---:|---:|
| ITUK | 115,284 | 7,962 | 1.63% | 81,616 |
| IRELAND | 23,367 | 1,034 | 2.19% | 21,726 |
| UTI | 18,731 | 533 | 0.61% | 17,316 |
| BELGIUM | 12,340 | 383 | 0.49% | 1,904 |
| PORTUGAL | 11,093 | 153 | 0.60% | 2,314 |
| IUK | 10,359 | 363 | 0.17% | 0 |
| UMI | 9,558 | 70 | 0.33% | 0 |
| UKRAINE | 9,524 | 187 | 0.91% | 4,613 |
| ARMENIA | 7,837 | 53 | 2.47% | 4,005 |
| GERMANY | 7,540 | 303 | 0.27% | 1,236 |
| other customers | 4,993 | 72 | 0.58% | 2,857 |
| KAZAKHSTAN | 4,648 | 87 | 3.40% | 4,625 |
| MALTA | 4,498 | 23 | 2.06% | 3,654 |
| CYPRUS | 2,772 | 57 | 0.64% | 979 |
| NORWAY | 2,375 | 113 | 0.15% | 0 |
| GREECE | 1,308 | 16 | 0.27% | 84 |
| FINLAND | 739 | 11 | 0.22% | 0 |
| ICELAND | 559 | 46 | 0.68% | 0 |
| ROMANIA | 548 | 7 | 0.30% | 319 |
| HUNGARY | 539 | 8 | 0.16% | 7 |
| SWEDEN | 336 | 50 | 0.02% | 0 |
| DENMARK | 229 | 4 | 0.12% | 0 |
| PALESTINE | 47 | 1 | 0.21% | 47 |

Market = billing customer mapped to its distributor through `distributor_dimension.csv`. Before = EUR 0 in every market. A "0" in the last column means the market's euro here is knuckles, arms and caps only. IUK and UMI (D-Max markets) bought no king-pin parts in the window.

## Which figures this feeds

| Where the service category is used | Effect of the change |
|---|---|
| AIM pages: PMS cover on billing and on sales to dealer | **None.** The pages count 14 service families (filters, brakes, clutch). `king_pin` is not one of them and is dropped. |
| PMS capture / gap (`pms_capture_by_db_year.csv`, the expected-versus-actual demand figures) | **None.** That file has the same 14 categories and no demand rate for king pins. |
| GPS | **None found.** The GPS figures I checked do not read this field. About 75 scripts read the catalogue dimension and I did not open each one, so this is not proven for all of them. |
| Lost-sales model (`lost_sales_build.py`: family split in `lost_sales_model.csv` / `lost_sales_market.csv`) | **Moves.** A part that has a service category is put in a family by that category, and `king_pin` goes to "Other". EUR 244,675 moves from Suspension & chassis to Other (101 parts), EUR 1,373 from Belts & cooling, EUR 1,171 from Clutch & driveline, and EUR 2,004 that is unclassified today. The share of parts billed with a service category goes from 19.54% to 20.24%. |
| GPS part explorer label (`category_hint`) | Mostly none: when a part has a figure key, the label shows the figure key, and almost all of these parts have one. |

## The alternative: king-pin figure keys

The figure keys that hold the 533 king-pin parts are almost entirely king-pin parts:

| Figure key | Parts | with "KING PIN" text | EUR last 12 months |
|---|---:|---:|---:|
| 410-004 | 129 | 128 (the other is 5878305371 REPAIR KIT, refiled to Knuckle / arm today) | 136,037 |
| 410-026 | 20 | 20 | 6,460 |
| 410-014 | 13 | 11 | 1,219 |
| 410-029 | 3 | 3 | 861 |
| 410-025 | 19 | 19 | 792 |
| 410-003 | 144 | 144 | 722 |
| 410-032 | 22 | 22 | 509 |
| 410-364, 410-007, 410-045, 410-044 | 31 | 31 | 703 |
| 410-024, 410-006, 410-008, 410-021, 410-028, 410-030, 410-047 | 154 | 154 | 0 |

A rule on these keys would tag the king pins (about EUR 147k) and leave the front-axle knuckles and pitman arms alone. The rule file already uses rules by figure key for filters (e.g. `match_fig_key: "130-006"`). It needs one line per key. I have not computed that variant's per-market figures separately: they equal the "king-pin parts only" column above, apart from 410-014's 2 other parts.

## Seen in passing, not acted on

The dimension on disk is not what a rebuild with today's rule file gives on 156 parts. 151 parts the rule would tag `leaf_spring` are blank on disk, and 5 parts differ the other way (1 fan belt; 1 brake pad, 1 bushing, 1 fuel filter, 1 oil filter). None of them are king-pin or Knuckle / arm parts, so this comparison is not affected. A rebuild of the dimension for any reason would bring these changes too.

Source: `01_data\91_build\kingpin_rule_before_after_20261002.py` -> `kingpin_rule_before_after_20261002.json` (read-only run; the simulated rule file was a temporary copy, deleted after the run).
