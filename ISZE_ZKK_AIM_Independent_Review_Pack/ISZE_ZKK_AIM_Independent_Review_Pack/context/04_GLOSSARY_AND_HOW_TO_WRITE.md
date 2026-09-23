# 04 - Vocabulary, and how to write about this business

**As of:** 2026-09-19.

---

## 1. Words to use and words to avoid

Several internal words are banned because they mean nothing to the people who read the output, or because
they are actively misleading. Use the right-hand column.

| Do not write or say | Write instead |
|---|---|
| wallet, parts wallet, wallet euro | **parts billed** (what we sold) or **target spend per truck** (what the fleet could spend). Two different things - never one word for both |
| street, street price, street fills | **OEM peer retail**, or **reference dealer price**. "Filling the street" becomes "getting peer retail prices" or "completing price coverage" |
| street index | **price index** - the shop price divided by our reference dealer price |
| sell-out, sell-out data | **sales to dealer** (what moved at dealer level). Not the same as what ISZE invoiced |
| class factor 0.47 | **53% margin**. Give the margin; if the factor must appear, footnote it |
| factor band 0.70-1.35 | a **margin band**: 30% down to minus 35% against the class |
| "1 minus the class factor" | just give the margin |
| capture rate, capture | spell it out: **share of expected service demand sold**. The word "capture" is fine once glossed, but never in a headline |
| DB, DLR (in shared output) | **distributor**, **dealer** |
| parc | **trucks in service** or the **fleet** |
| leakage | say what actually happened - "service spend not reaching us", "billed on superseded part numbers" |
| ship-gate, harness, receipt, roll-up, payload, lane, surface, drift | do not use any of these. They are internal agent shorthand with no business meaning |
| Mode A / Mode B | **shared / external** for anything leaving ISZE; **internal / private** for internal work |

Also banned in shared output: internal project nicknames for the maintenance schedule model and the
classification model. Point to the business source instead (the April 2026 service analysis, the trip report,
the European parts analysis) and describe the thing in plain words.

Do not use terms like "capture rate", "leakage", "realisation" or "mix bucket" as headline labels in shared
output either. Gloss them once in plain words, or avoid them. "Share of expected service demand sold" and
"service spend not reaching us" are the plain forms. If a term needs a glossary to land, the sentence has
failed and should be rewritten.

A note on the ceiling measure, because a reader will ask: the ceiling is built from a target spend per truck
in service, which used to be called the parts wallet. **Use "target spend per truck" in anything that leaves
ISZE.** The engine and the data files may still carry the word "wallet" in file and column names; that is a
pipeline name, not a label for readers.

---

## 2. Acronym decoder

| Term | What it means |
|---|---|
| ISZE | Isuzu Motors Europe - the parts hub. Jerome's company, SAP branch IE40 |
| IML / ISZJ | Isuzu Motors Limited - the Japan parent and the Japan parts source |
| IMIE | Isuzu Motors International Europe - vehicle sales, separate from ISZE |
| IMIT | Isuzu Motors International Thailand - the Thailand parts source |
| IIF | Isuzu training entity, based in Dubai |
| IAS | Isuzu Accessories Supplier, Thailand |
| MIDI | A regional Isuzu entity. Not an ISZE customer - excluded from ISZE's own totals by convention |
| DB | Distributor |
| DLR / ASC | Dealer / authorised service centre |
| VP | Vehicle parts |
| ACC | Accessories |
| PMS | Periodic maintenance service - the scheduled service parts: filters, brake, clutch |
| UIO | Units in operation - trucks registered and in service. In this pack: "trucks in service" |
| GPS | In this workspace this is **not** satellite positioning. It is a parts-sales KPI: spend per truck in service, in euro per year |
| IAM | Independent aftermarket - non-original parts sold by outside suppliers |
| OEM-equivalent | A branded non-Isuzu part (Bosch, Valeo, etc.) |
| BVP | Best Value Parts - ISZE's own value tier of parts |
| PR00 | The standard European price list |
| ZPR1 | The Israel-specific price list |
| CIS | The price list for Armenia and Kazakhstan |
| SPA | Special price agreement - a discounted price for a specific customer or model |
| DLOD | "Don't lose the deal" - an ITUK programme for competitive quotes |
| R&M | Repair and maintenance contracts |
| GP | Gross profit |
| FX | Foreign exchange. Here specifically JPY per EUR |
| FOB | Free on board - the price ISZE pays, in euro, before margin |
| BP | Base price in JPY, set by IML |
| FY | Fiscal year, April to March |
| IDS | Isuzu Dealer Standards - a dealer self-assessment round, A to E |
| AIM | The part classification and commercial analytics model |
| EGR | Exhaust gas recirculation valve |
| DPD | Diesel particulate diffuser |
| N35 / N50 / N55 / N62 / N65 / N75 | N-Series truck classes by gross vehicle weight. N35 is 3.5 tonnes (the UK "Grafter"), N75 is 7.5 tonnes |
| 4JJ3, 4HK1, 6HK1, 6UZ1 | Diesel engine codes - D-Max, N-Series, and two F-Series engines |
| Kosha | The Isuzu commercial plan with the FY2031 revenue target |
| TED | The European Union tender portal |
| DVLA | The UK driver and vehicle licensing agency - source of the UK fleet count |
| SIMI | The Irish motor industry body - source of the Irish fleet count |
| VIN | Vehicle identification number - used to count shipments and measure scrappage |

---

## 3. How to write numbers

**A quantity is never a finding.** Every quantified gap, shortfall or leakage carries three things or it is
not finished:

1. **Euro** - what the quantity is worth, on an observed average selling price. Euro is the decision currency.
2. **Part family or service category** - which parts. "258,824 units" is meaningless; "258,824 oil filters" is
   a finding.
3. **Fleet base** - the trucks in service, so the quantity reads as a rate per vehicle rather than an absolute.

**Wrong:**

> IUK has a gap of 258,824 units.

**Right:**

> IUK's service-parts gap is EUR 5.8M across four filter and wear families, on 47,783 light commercial
> vehicles. That is 82.7% of its expected service demand unbought, and it is measured against a flat 20,000 km
> annual distance assumption while IUK's own light truck fleet averages less than that in the one place we have
> measured it.

Lead with euro or with a rate per vehicle. Never lead with a unit count.

**Mileage is measured, not assumed.** Where a measured annual distance exists for a market or a class, it
replaces the flat assumption for that segment. Known measured figures: the UK N35 light truck fleet averages
about 14,494 km per year (from 18,277 odometer intervals across 5,421 vehicles); UTI's N75 fleet averages
about 51,680 km per year; and all-market figures for the N35, N75 and F-series are about 12,165, 35,217 and
45,630 km per year respectively, still provisional. **Do not use the "annual mileage" column in the N35
mileage workbook** - it divides the odometer reading by a shrinking vehicle age, so the newest reading equals
the odometer itself and one vehicle appears to do 63,273 miles a year on a 63,273-mile clock. Derive mileage
from odometer deltas over elapsed time.

**Units need a denominator to be judged.** The same absolute gap means opposite things in a large and a small
market. This is why every gap table in file 02 carries the fleet count and the gap per truck.

---

## 4. How to talk about margin

Prices are built with a divisor. The factor and the margin are two names for one thing:

```
selling price = FOB / class factor       so    margin = 1 - class factor
```

| Never write | Write instead |
|---|---|
| class factor 0.47 | **53% margin** |
| class factor 0.70-1.35 | a **margin band** of 30% to minus 35% against the class |
| 45% margin coded as a factor | **45% margin on the parts a Chinese equivalent exists for** |
| 0.60 coded as a factor | **60% margin where the part cannot be followed by a competitor** |
| 0.40 flat | **60% margin, flat across the catalogue** |
| source discount 0.62 / 0.611 | state the **margin it implies**, once, then the code if needed |

The reason is not style. The factor is the divisor; the margin is the decision. A document that says "factor
0.47" makes the reader do the arithmetic and hides the fact that a factor is a margin somebody chose.

The same applies to the class letters. Class C is not information on its own. "Class C, 53% margin" is.

---

## 5. Two audiences

**Internal / private** - this file set, internal sparring, private notes, the numbers in file 02 with their
caveats. Full detail is fine, including the parts that make ISZE look bad.

**Shared / external** - anything a distributor, a dealer, IML Japan or a colleague outside the immediate team
might read: meeting packs, shared dashboards, Excel studies, mail. In that register:

- No internal project nicknames, no pipeline vocabulary, no file names, no field names.
- No personal names where a role will do.
- Every figure carries its as-of date and its basis.
- Every acronym is spelled out the first time and glossed in one short sentence.
- Write for the distributor in the room, not for an analyst. Words like "stock versus urgent", "official
  sales", "dealer score against the country average" land; words like "capture", "realisation" and "mix
  bucket" do not.

---

## 6. The three mistakes that most often produce a wrong answer

**1. Blending two entities that share a name.** Israel: UMI and UTI are separate distributors with separate
fleets and separate sold-to codes (1797 and 1799). United Kingdom: ITUK (trucks) and IUK (light commercial)
are separate. Any "UK" or "Israel" total that silently adds them is wrong. Averaging UTI into UMI for anything
linked to the dealer standards round is specifically forbidden, because UTI did not take part in it.

**2. Reading a distributor's purchases as end-customer demand.** ISZE invoices the distributor. What the
distributor ordered reflects their stocking decision as much as the market. Only five markets have shared
dealer-level sales, so for the rest, customer demand is inferred, not measured. Say so.

**3. Comparing a partial year with a full year.** 2026 in the data is January to June only. Every 2026 figure
in this pack is a partial year, and the source file says so in a column. Never set a half year beside a full
year and describe the difference as growth or decline.
