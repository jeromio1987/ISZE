# UIO V20 — what needs to change and why

**Status:** draft, nothing built yet — IUK LCV (row 25) CY2026F **locked** 30 July 2026
**Written:** 27 July 2026 (Jérôme Van der Pluym / Claude); **amended** 30 July 2026 (IUK LCV decision);
**revised 9 August 2026** (internal-consistency pass — see *What changed in this revision* below)
**File it applies to:** `C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx` (V19, dated 18 June 2026)

> **This is a review draft.** It sits beside the live spec as `V20_SPEC_v2_DRAFT.md` and is not
> committed. Nothing in the locked IUK LCV arithmetic has been changed — 44,926 stands, and is now
> better supported than it was.

### What changed in this revision

| # | Change | Why |
|---|---|---|
| R1 | Truck survival row: life corrected **9.9 → 9.8 years** | 1 ÷ 10.2 % = 9.80, not 9.9. The table was self-contradictory. |
| R2 | Timeline corrected: the defect was in the workbook **by 12 June**, not introduced at V19 (18 June) | The v18 dashboard, built 2026-06-12 17:03, already carries the signature. |
| R3 | Added **Check 4** — the published v18 dashboard independently reproduces the 7.8 % → 37.7 % overstatement | Second artefact, derived without opening the workbook. |
| R4 | The 44,926 lock now records that **two independent methods agree to 3 units** | Was buried as a weaker "alternative". It is corroboration, not a fallback. |
| R5 | Appendix: the **"All rows" totals do not equal the sum of the rows** — short by ~2,500/yr | New finding. Larger than the 90-unit row-25 issue. |
| R6 | *Still open* expanded: owner of the June change, and the appendix perimeter question | Both were unrecorded. |
| R7 | New **Problem 8 — the dashboard is publishing the defect right now** | Share-ready, staged in two deploy folders, and its headline KPI is arithmetically impossible. |

---

## The short version

The car park model works like this: take last year's fleet, remove the trucks that were scrapped, add
the trucks that were newly registered. That gives this year's fleet. Repeat.

In June we changed how the "remove the scrapped trucks" step works, and we got it wrong. The model now
assumes a truck lasts 33 years. Everywhere else in the same file we assume roughly 10 to 12 years, and
the real-world data says the same. Because we only remove 3 % of the fleet each year instead of about
10 %, the fleet grows every year no matter what we feed in. That is the growth spike everyone is
looking at.

**When, exactly (corrected 9 Aug 2026).** This spec is written against V19, dated 18 June 2026, and
earlier wording implied the change arrived with V19. It did not.

The published dashboard `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` carries a self-declared
provenance stamp naming a **v18 workbook, 2026-06-12 17:03**, and the forecast series embedded in that
dashboard already fits the broken formula (Check 4 below). So the defect was in the model **by 12 June
at the latest — six days before V19**. Anyone hunting for the change should look at the v17 → v18 step,
not v18 → v19.

> **Source discipline:** the archived v18 workbook was **not opened**, and must not be. The only valid
> workbook remains `06_uio/_CURRENT/ISUZU_UIO_Overview_2026.xlsx` (V19 internally). The 12 June date is
> read from the dashboard's own metadata string and from the forecast numbers baked into its HTML —
> both artefacts, not the archived file.

Two separate things caused the numbers to move in June, and they are being confused with each other:

- **The Ireland and Portugal data updates were good work.** We replaced our own estimates with real
  government and dealer registration data. That made the fleet numbers go *down*, which is correct.
- **The forecast method change, made the same week, is the problem.** It has nothing to do with Ireland
  or Portugal. It affects every market and every future year.

On top of that, the Israel numbers are about a quarter too low in every single year — a separate issue
we only found because UTI shared their government registration data in July.

**Bottom line:** the historical part of the file (1990–2025) is in decent shape. The forecast part
(2026–2030) should not be quoted to anyone until this is fixed.

---

## Problem 1 — The model assumes trucks live three times longer than they do

### What's happening

For the years 1990 to 2025, the file builds the fleet properly: it takes the trucks registered in each
year and works out how many of them are still on the road today, using a survival curve. A survival
curve is just a table saying "after 5 years, 96 % are still running; after 10 years, 55 %; after 15
years, none".

For 2026 onward, the file throws that away and uses a single flat number instead: remove 3 % of the
fleet per year, add the new trucks.

Those two methods do not agree with each other:

| Method | Average truck life it implies | Scrapped per year |
|---|---:|---:|
| The survival curve we use for trucks 1990–2025 | 9.8 years | **10.2 %** |
| The survival curve we use for pickups 1990–2025 | 8.1 years | **12.3 %** |
| The flat number used for 2026–2030 | 33.3 years | **3.0 %** |

*Life = 1 ÷ scrap rate, so the two columns check each other: 1 ÷ 0.102 = 9.8, 1 ÷ 0.123 = 8.1,
1 ÷ 0.030 = 33.3. The scrap rate is the primary figure — it is what the arithmetic uses everywhere
else in this spec. **Corrected 9 Aug 2026:** the truck row previously read 9.9 years, which does not
reconcile with 10.2 % (1 ÷ 9.9 = 10.1 %). This is the table that carries the whole argument; a reviewer
will divide.*

So on 1 January 2026 the trucks in our model suddenly start living three times longer than they did on
31 December 2025. Nothing in the real world changed — only our arithmetic.

### How we know this is wrong, not just different

Four independent checks all say the same thing. The fourth was added 9 August 2026 and is the only one
that needs no access to the workbook at all.

**Check 1 — rebuild Ireland from scratch.** We took the Irish registration history that's already
written into the file, applied the survival curve, and got 731 trucks for 2025. The file says 731. Exact
match, so we know we understand the engine correctly. Then we ran that same engine forward with the same
sales plan:

| Ireland, year 2030 | What V19 says | What the proper method gives | V19 is too high by |
|---|---:|---:|---:|
| Trucks (light) | 1,645 | 1,382 | **19 %** |
| Pickups | 3,174 | 2,527 | **26 %** |

**Check 2 — where does it end up?** If Ireland registers 216 trucks a year forever, the fleet eventually
settles at 216 × 9.9 = about **2,100 trucks**. Under the 3 % rule it settles at **7,200**. The 2030
figure is only the beginning of the error; it keeps growing after that.

**Check 3 — measure the real scrappage from shipment data.** Using the new VIN file (see the last
section), we can count actual trucks sent to each market and compare against how the fleet moved:

| Market | Fleet 2019 | Shipped 2020–24 | Fleet 2024 | Real scrappage per year |
|---|---:|---:|---:|---:|
| Ireland | 820 | 451 | 749 | **13.3 %** |
| Portugal | 1,502 | 1,427 | 2,239 | **7.4 %** |

Ireland and Portugal are the only two markets where the fleet history is built on real registration
data, so they are the only two where this measurement is meaningful. They average about 10 %, which is
what the survival curve says. The model uses 3 %.

*(The same calculation on Belgium, Cyprus, Malta and Greece returns 0.3 %–3 %. That is not evidence
those markets scrap less — it is evidence their fleet history is not built on real data. See Problem 5.)*

**Check 4 — the published dashboard convicts itself** *(added 9 August 2026)*. The forecast series is
hard-coded into `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` as plain JSON, so it can be tested
without opening any workbook. Fit it to `UIO × 0.97 + regs` and read off the implied annual additions:

| Step | Implied new registrations |
|---|---:|
| 2025 → 2026 | 17,358 |
| 2026 → 2027 | 17,378 |
| 2027 → 2028 | 17,449 |
| 2028 → 2029 | 17,666 |
| 2029 → 2030 | 17,735 |
| | *spread: 2.2 % of mean* |

Near-constant additions at a 0.97 survival factor. That is the 3 % rule, fitted to its own output. Hold
those same additions and swap in the 10.2 % truck curve:

| Grand Total | Dashboard says | At 10.2 % scrap | Overstated by |
|---|---:|---:|---:|
| 2026 | 268,194 | 249,717 | **7.4 %** |
| 2030 | 304,580 | 222,388 | **37.0 %** |

Compare against *The size of it* immediately below, which was derived from the workbook months earlier
and independently: **7.8 % rising to 37.7 %**. Two routes, two artefacts, agreement inside half a point
across five years. This is now the easiest version of the argument to show someone who does not have
the file open.

### The size of it

| Grand Total | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---:|---:|---:|---:|---:|
| Too high by | 7.8 % | 15.6 % | 23.2 % | 30.6 % | **37.7 %** |

### The fix

Delete the 3 % rule. Use the same survival-curve method for 2026–2030 that we already use for
1990–2025. One method for the whole row, no join in the middle.

Applies to columns AQ to AU (the years 2026–2030) on sheet `1.UIO Overview`, every row except:

- **UK CV rows 22 and 24** — already correct (Sheet 4 survival model). Leave those alone.
- **Israel rows 7 and 8** — rebuilt entirely (Problem 4).

**UK LCV row 25 is in scope** for this scrap fix (see Decision — IUK LCV below). Ireland, Portugal,
and all other non-Israel markets follow this Problem 1 fix as written.

---

## Problem 2 — The pickup fleet is forecast to grow when it should be shrinking

### What's happening

This is the same 3 % bug as Problem 1, but for pickups it doesn't just make the number too big — it
makes the direction wrong.

The pickup registration forecast comes from IMIT's November 2025 study. We checked every number in the
model against that file and they all match exactly (Ireland 430, Portugal 900, Germany 1,000, Greece
630, Italy 4,540, and so on). The inputs are fine.

The problem is what IMIT actually forecasts:

| ISZE pickup registrations, per IMIT | 2024 | 2025 | 2026 | 2027 |
|---|---:|---:|---:|---:|
| units | 16,977 | 15,312 | **10,845** | 10,595 |

Registrations drop **29 %**. Meanwhile our model has the pickup fleet growing **22.8 %** between 2025
and 2030. Both cannot be true.

Here's the clean way to see it. At 10,845 registrations a year, the fleet can only sustain
10,845 × 8.1 years = about **88,000 pickups**. We already have **125,000** on the road. The fleet is
42 % bigger than the current registration rate can hold up. It has to come down.

### The fix

Same as Problem 1. Once the real survival curve is applied, the pickup rows turn downward on their own.
No separate override is needed.

**Warning:** this will be the biggest single movement in the file, and it flows into every number that
divides by fleet size — parts spend per truck, capture rates, GPS target wallet. Expect questions.

---

## Decision — IUK LCV row 25 (Jerome, 30 July 2026) — LOCKED

**Row:** `U KING / LCV / IUK` = sheet `1.UIO Overview` **row 25**. Hardcoded values. **Not** linked to
sheet `4. ITUK UIO Projection` (that sheet drives **ITUK CV** rows 22/24 only).

### Problem

V19’s 2025E→2026F+ rise is **wrong**. It uses the same broken `UIO × 0.97 + regs` (3 % scrap). Real
pickup scrap is ~10–12 % (spec: **12.3 %** / 8.1 yr life). With collapsing UK D-Max registrations the
parc must **fall**, not grow. Decline is acceptable and better for GPS target honesty.

| | 2024 | 2025E | 2026F | later |
|---|---:|---:|---:|---:|
| **V19 (wrong direction from 2026F)** | 48,876 | 47,783 (−2.24 %) | **49,280** (+3.1 %) | climbs to ~52,804 by 2030 |
| **IMIT Nov 2025 UK fleet (12 yr)** | 41,012 | 40,095 | 37,695 | 35,517… (falling) |

- 2024→2025E **−2.2 % is correct** (IMIT-aligned ratio on the IML absolute level). Keep 2025E = **47,783**.
- IMIT UK D-Max regs: 2024 = 7,013 · 2025 ≈ 4,280 (−39 %) · **2026E ≈ 3,020**.
- V19 appendix buried ~2,930 for 2026 regs on row 25; prefer **IMIT ≈ 3,020** for the rebuild.

**Clarify prior “leave the UK alone” wording:** that meant **rows 22 and 24 only**. **Row 25 is in
scope** for the scrap / survival fix.

### Correct method (preferred)

Keep the **IML absolute level** (do not silently drop 48k→40k to IMIT absolute without labeling). Apply
the same pickup survival / scrap as the rest of the file, plus IMIT new regs:

**CY2026F** = `2025E × (1 − 0.123) + IMIT_2026_regs`

Using the locked inputs (2025E = 47,783, scrap = **12.3 %** pickup curve, regs = **3,020**):

```
47,783 × (1 − 0.123) + 3,020 = 41,905.691 + 3,020 = 44,925.691 → 44,926
```

| Locked for FY27 GPS / Extended Target | Value |
|---|---:|
| **IUK LCV CY2026F (use this, not V19)** | **44,926** |
| vs 2025E 47,783 | **−6.0 %** |
| V19 was | 49,280 (+3.13 %) — **do not use** |

Roll 2027–2030 the same way (pickup scrap 12.3 % + IMIT regs each year) so the series keeps declining
in line with IMIT direction.

### Why 44,926 is safe to defend *(promoted 9 August 2026)*

A second, completely independent route lands on the same number. Instead of building it from scrap and
registrations, scale the IML absolute level by IMIT's own UK fleet year-on-year:

| Route | Working | CY2026F |
|---|---|---:|
| **A — scrap + regs** *(primary)* | 47,783 × (1 − 0.123) + 3,020 | **44,926** |
| **B — IMIT YoY on IML level** | 47,783 × (37,695 ÷ 40,095), i.e. −5.986 % | **44,923** |
| | **gap** | **3 units — 0.007 %** |

Route A is bottom-up arithmetic on a survival curve. Route B is a top-down ratio from an outside study.
They share only the 2025E starting level. Landing 3 units apart is not a rounding coincidence — it is
two methods agreeing.

**Use this when the number is challenged.** The earlier draft filed Route B as a weaker "alternative
for a labeled bridge"; that undersold it. Route A remains primary for consistency with Problems 1 and 2,
but B is the corroboration, not the fallback. Against V19's 49,280 there is no comparable second route —
nothing outside the workbook reproduces it.

### Downstream

GPS Extended Target Dashboard (IUK cols R/U): replace the **+3.13 %** UIO growth assumption with the
corrected **−6.0 %** (2025E→2026F). FY27 GPS still needs a CY2026F number — that number is **44,926**,
not 49,280.

*(Ireland / Portugal / other markets: still the Problem 1 survival-curve fix — unchanged by this
decision.)*

### Related commercial context (pointer only — lock unchanged)

IMIE 3-party decks indexed 30 Jul 2026 (Nikola Broecker / Jerome self-mail dump) show UK D-Max under
**ZEV mandate + BIK** pressure, YTD market volume called an **all-time low**, and IUK still on an **ICE**
order strip with **BEV ≈ 0**. That supports the *direction* of this IUK LCV decline (and IMIT’s weak
2026 regs), but it does **not** replace the locked **44,926** arithmetic. Detail:
`05_memory/projects/imie_3party_2025_2026.md`.

---

## Problem 3 — The sales plan is treated as if every planned truck reaches the road

### What's happening

The truck numbers for 2026–2030 come from the mid-term sales plan
(`ISZE_CV_FY2025-FY2030_mid-term_plan___12RS.xlsx`, November 2025):

| Trucks per year in the plan | FY2025 | FY2026 | FY2030 |
|---|---:|---:|---:|
| Ireland (light) | 26 | **216** | 216 |
| Ireland (medium) | 1 | **36** | 36 |
| Portugal (light) | 141 | **456** | 456 |
| Portugal (medium) | 1 | **96** | 108 |
| Germany (light) | — | 390 | **1,000** |
| Greece (light, both dealers) | 4 | 50 | 50 |
| Belgium (light) | — | 35 | 35 |
| Malta (light) | 1 | 24 | 24 |
| Cyprus (light) | 2 | 30 | 30 |
| **Europe total** | **630** | **1,325** | **1,935** |

The plan counts trucks ISZE ships to the distributor. The car park counts trucks registered with the
government and driving around. The model treats them as the same thing.

### Jerome's decision (27 July 2026) — and the evidence behind it

**Decision: use the plan one-to-one, assuming stock levels stay roughly stable.**

The VIN file lets us test that assumption for the first time, for Ireland, where we have both shipment
records and government registration records:

| Year | Shipped to Ireland | Registered in Ireland | Difference |
|---|---:|---:|---:|
| 2020 | 79 | 63 | +16 |
| 2021 | 108 | 98 | +10 |
| 2022 | 88 | 96 | −8 |
| 2023 | 122 | 71 | **+51** |
| 2024 | 54 | 117 | **−63** |
| **2020–2024** | **451** | **445** | **+6** |

**Over five years the two match within 1.3 %.** The decision is sound.

But look at 2023 and 2024. Individual years swing by 50 to 70 units in both directions, because trucks
shipped in one year get registered in the next. So:

- **Use the plan one-to-one for the level.** Confirmed by evidence.
- **Do not use it one-to-one year by year.** Smooth it, or apply a shipment-to-registration lag. Without
  this, single forecast years will be visibly wrong even though the five-year total is right.

### Two things that still need fixing regardless

**Medium-duty rows built from nothing.** Rows 27 (Ireland), 52 (Portugal), 80 (Greece) and 89 (Cyprus)
are empty through 2025 and then grow purely on plan numbers. Portugal reaches 498 medium trucks by 2030
starting from zero. The VIN file confirms this is not real: across all 3,238 trucks shipped to Europe
since 2020, **not one is a medium-duty unit**. Move these rows into a clearly marked "plan only" block,
kept out of the Grand Total until a first real registration shows up.

**Germany is the worst cell in the file.** 697 trucks in 2025 growing to 3,756 by 2030 — up 439 %. Worse,
its own *history* for 2019–2024 was invented by running the 3 % rule backwards from a single 2025 data
point. So both directions rest on the wrong number, in a market with no real registration data at all.
Either find a proper source or mark the whole row as indicative.

---

## Problem 4 — Israel's fleet is about a quarter too low, in every year

### What's happening

UTI's July 2026 parts presentation
(`C:\Users\jerom\Downloads\מצגת לחלפים בלגיה - אפריל 2026.pdf`, slides 14, 15 and 17) contains the
Israeli Ministry of Transport's registered fleet figures. That is government registration data — the
same quality of source as SIMI in Ireland, and better than the UTI shipment file we currently use.

| Year | Our model | UTI / government actual | Gap |
|---|---:|---:|---:|
| 2020 | 7,793 | 11,514 | −32.3 % |
| 2022 | 9,011 | 12,557 | −28.2 % |
| 2024 | 10,049 | 13,323 | −24.6 % |
| 2025 | 10,336 | 13,881 | −25.5 % |
| 2026 | 10,760 | **14,019** (at 30 June) | −23.2 % |

The gap is roughly 3,300–3,700 trucks and it barely moves across seven years. A steady gap like that
means we are missing a *block* of vehicles, not that our scrappage rate is slightly off.

By weight class, at 30 June 2026 (the four classes add up to exactly 14,019, so the slide is internally
consistent):

| Weight class | Isuzu trucks | Average age | Market average age |
|---|---:|---:|---:|
| 6.5 – 7.5 t | 8,610 | 9.4 yrs | 9.8 yrs |
| 7.6 – 10 t | 2,485 | 6.2 yrs | 10.7 yrs |
| 10.1 – 12 t | 2,697 | 5.9 yrs | 7.3 yrs |
| 12.1 – 16 t | 227 | 5.6 yrs | 9.1 yrs |

Our light-truck row shows 6,101 against 8,610 actual (**29 % low**). Our medium row shows 4,659 against
5,409 (**14 % low**).

### Three possible reasons — we can't yet tell which

1. **Weight classes we never mapped.** Our Israel setup only covers nominal classes 6.5t, 7.5t, 10t, 11t
   and 12t. The 7.6–10 t class (2,485 trucks) has no home in our model, and 12.1–16 t (227) sits above
   everything we map. This alone could explain most of a steady gap.
2. **We scrap old trucks that are still working.** Slide 14 shows **1,680 trucks first registered
   between 1999 and 2010 that are still on the road — 12 % of the whole fleet**, aged 16 to 27 years.
   Our Israel survival curve is down to 5 % at age 19 and zero at 20. We are killing trucks the
   government says are registered. This is exactly the problem we already fixed for the UK in V15 with
   the owner-operator floor; Israel never got one.
3. **Different populations.** The government counts every registered Isuzu truck regardless of who
   imported it. We build our number from UTI's own file. Parallel imports, or stock from a previous
   importer, would produce precisely this kind of fixed gap.

### The fix

Rebuild Israel on the government data as the primary source, exactly as we did for Ireland in June. Add
a class for 7.6–10 t and one for 12.1–16 t. Then add an age floor for trucks over 15 years once we can
see how big the old tail really is.

**Do not simply multiply the Israel rows by 1.25.** Anchor to the real data and rebuild, or the same bug
returns next year.

---

## Problem 5 — Four markets have no real fleet history at all

Belgium, Cyprus, Malta and Greece are built from the IML backbone and the old scrap-adjusted car park,
not from registration data. The VIN cross-check exposes this: measured against actual shipments, these
markets appear to scrap **0.3 % to 3 %** of their fleet per year, which is not physically plausible for
trucks. Ireland and Portugal, which do use real data, come out at 7 %–13 %.

This was not visible before we had the shipment file. These four markets should be flagged as low
confidence and put in the queue for a registration-based rebuild.

---

## Problem 6 — Every 3.5-tonne truck is charged the parts wallet of a 7.5-tonne truck

This one is about GPS, not the car park, but it comes from the same root: we don't distinguish truck
sizes properly.

### The Isuzu weight ladder

The number in a model code is a **chassis generation code, not a weight**. The proof is in our own data:
the NLR appears as NLR85, NLR87 and NLR88; the NPR appears as NPR75 and NPR85. One truck class cannot
have three different weights. The real ladder for Europe is:

| Code | European name | Actual GVW | What the VIN script currently says |
|---|---|---:|---:|
| NLR | N35 | **3.5 t** | 8.5 / 8.7 / 8.8 t — **150 % too heavy** |
| NMR | N50 / N55 | 5.5 t | 8.5 / 8.8 t — 55 % too heavy |
| NNR | N62 / N65 | 6.5 t | 8.5 / 8.8 t — 31 % too heavy |
| NPR | N75 | 7.5 t | 7.5 t (correct) / 8.5 t |
| FRR | F110 / F120 | 11–12 t | 9.0 t — **22 % too light** |
| FSR | F135 | 13.5 t | 9.0 t — **33 % too light** |

Confirmed against Isuzu Ireland's own published range (3.5 t, 7.5 t, 11 t) and the P700 launch classes
(3.5, 6.5, 7.5, 13.5 t). Across the 3,238 trucks in the VIN file this makes the fleet look like 26,689
tonnes when it is really 19,687 — an average of 8.24 t per truck instead of 6.08 t.

**Fix in `build_vin_register.py`:** replace the `GVW_FROM_CODE` lookup, which reads the chassis code as
tonnage, with a series-to-GVW map (NLR 3.5, NMR 5.5, NNR 6.5, NPR 7.5, FRR 11–12, FSR 13.5). The current
map is right for NPR75 by coincidence and wrong for everything else.

### Why this hits GPS

GPS % = actual parts sales ÷ target wallet, and the target wallet uses a maximum spend per vehicle that
depends on model group (`prism/data/gps_model_targets.csv`):

| Group | € per vehicle per year |
|---|---:|
| N35 Grafter | **296** |
| N75 / N50 / N62 | **739** |
| F-Series / MD | 887 |
| LCV / D-Max | 250 |

The car park file has no model split for these markets — the model column just says "LD" for every
N-series truck. The mapper (`prism/modules/gps_model_targets.py`) sees "LD" and returns
N75 / N50 / N62. **So a 3.5-tonne Grafter is charged €739 of parts wallet a year instead of €296.**

Two things follow. First, the N35 Grafter row in the targets file is **dead configuration** — no code
path can ever return it, and even the branch that looks for "NLR" or "N35" routes to LCV / D-Max at
€250, not to the €296 Grafter rate. Second, the size of the distortion depends entirely on how many
3.5-tonne trucks a market runs, and that varies enormously:

| Market | Share of N-series that is 3.5 t | Effect on the whole distributor's target wallet | Multiply current GPS % by |
|---|---:|---:|---:|
| **Portugal** | **68.5 %** | **−21.9 %** | **1.28** |
| Belgium | 85.7 % | −1.8 % | 1.02 |
| Ireland | 6.3 % | −2.1 % | 1.02 |
| Germany, Malta, Cyprus, Greece | 0 % | no change | 1.00 |
| **Seven markets together** | 42.5 % | **−6.0 %** | **1.06** |

Belgium has the highest Grafter share but almost no trucks, so it barely moves; its wallet is nearly all
D-Max. **Portugal is the real one.** Its target wallet drops from €3.05 m to €2.38 m, which means
Portugal's GPS % is currently understated by about a quarter.

**Caveat, and it matters:** the 3.5-tonne share above comes from what was *shipped* 2020–2026, applied
to the *whole* 2025 fleet. Older vehicles may carry a different mix. Treat these as an indication of
size, not as a restatement of Portugal's GPS.

### The fix

1. Correct the weight decode in the VIN build script.
2. Split the "LD" car park row into N35 and N50/N62/N75 for the markets that need it, so the GPS mapper
   can tell them apart. The VIN register gives the split for recent years; older years need a source.
3. Make the mapper actually able to return N35 Grafter, and decide whether a 3.5-tonne Grafter belongs
   at €296 (its own line) or €250 (with the pickups). Right now the CSV says one thing and the code does
   another.
4. Re-run GPS and check whether any distributor breaks 100 % — Portugal moves most.

---

## Problem 7 — The written documentation no longer matches the numbers

The June change overwrote the calculations but nobody updated the sheets that describe them:

| What the file says | What it actually does (2030) | What the description would give |
|---|---:|---:|
| Ireland pickups: "IMIT growth rates … 2030 = 2,648" | **3,174** | 2,648 |
| Portugal trucks: "3 % decay, no sales plan available" | **4,042** | ~1,895 (the plan was applied anyway) |
| Portugal pickups: "8 % growth per year" | **8,128** | 6,954 |

The `Data Sources` sheet also still describes Germany and Portugal as based on the old scrap-adjusted
car park and quotes numbers we stopped using in June. That old method no longer drives the data for
Ireland and Portugal — but it still drives the documentation, which is why the file reads as if two
people wrote it. **Germany is the one place where the old scrap logic genuinely still fabricates the
history.**

Fix: rewrite the method sections and the source list to describe what the rebuilt file actually does.

---

## Problem 8 — The dashboard is publishing the defect right now *(added 9 August 2026)*

Problems 1–7 are about a workbook nobody outside the team opens. This one is about the artefact people
actually look at, and it is worse than the workbook because it is share-ready and staged for deploy.

**File:** `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` (24,475 bytes).
`ISUZU_UIO_Dashboard_2026_v18.html` beside it is only a `<meta refresh>` redirect stub, not a second
dashboard.

### It contains two incompatible models of the same fleet

| Year | **Set 1** — the plotted data + KPI values | **Set 2** — chart annotations, warn-box, CV/LCV | Delta |
|---|---:|---:|---:|
| 2024 | 252,710 | 254,117 | −1,407 |
| 2025 | 258,594 | 260,449 | −1,855 |
| 2026 | 268,194 | 250,718 | **+17,476** |
| 2030 | 304,580 | 262,559 | **+42,021 (+16.0 %)** |

Set 1 rises every year. Set 2 dips in 2026. Both are printed on the same screen.

### The headline KPI is arithmetically impossible

The KPI deltas were computed from Set 2 and printed beside Set 1 values:

| Card | Printed | Recomputed from the value shown | |
|---|---|---:|---|
| Total UIO 2024 | ▲ +4.3 % vs 2023 | +4.28 % | ok |
| 2025E — 258,594 | ▲ +2.5 % vs 2024 | +2.33 % | wrong (+2.49 % is Set 2) |
| **2030F — 304,580** | **+0.8 % vs 2025E** | **+17.78 %** | **wrong by a factor of 22** |

258,594 → 304,580 is +17.8 %. The card says +0.8 %, which is Set 2's 262,559 ÷ 260,449. A reader takes
away "the fleet is flat to 2030" from a chart whose own data grows by a sixth.

### The warning box defends a decline that is not in the chart

> *"The −3.7 % dip in 2026F … is a genuine model output, not an error. … When sharing this dashboard
> externally, explain the dip proactively."*

The plotted series does **258,594 → 268,194 = +3.71 %**. It rises. Same magnitude, opposite sign. The
instruction sends someone into an external meeting to explain a fall the screen does not show. The dip
annotation is anchored 17,476 units below the curve; the 2030 label floats 42,021 units below it.

### Everything else found in the same pass

| | Finding |
|---|---|
| D1 | Freshness banner reads **2026-05-12**; footer and provenance string both say **2026-06-12**. The staleness warning is itself a month stale. |
| D2 | ITUK detail table titled *"v17 cohort model"*, but only the **total row** is v17 — model rows are v11 and sum to 32,587 in 2030 against a 28,209 total. Gap widens 0 → 4,378. Disclosed only in a 10-px note. |
| D3 | CV/LCV chart implies a 2024 total of **254,117** (Set 2) while the KPI two rows above says 252,710. Its 37.8 / 62.2 % split is computed on 254,117. |
| D4 | Country bars are **ex-MIDI** (they sum to 160,125, reconciling exactly to 252,710 − 92,585 ✓) but carry no label, while the trend chart is MIDI-inclusive and does. Reading UK against the wrong base gives **28.2 %** instead of **44.5 %**. |
| D5 | MIDI's 92,585 — **36.6 % of the Grand Total** — is annotated *"not re-verified after v17"*. |
| D6 | Assets load from `../_ui/`. Correct inside `02_dashboards/`; any copy placed elsewhere renders five blank charts. |

### Where else this payload lives

The same defective series and the same +0.8 % KPI are present in:

- `02_dashboards/fleet/ISUZU_UIO_Dashboard_2026.html` — the working copy
- `07_deploy/Master Dashboard/ISUZU_UIO_Dashboard_2026.html` — **deploy**
- `07_deploy/publish-site/ISUZU_UIO_Dashboard_2026.html` — **deploy**

Two of the three are in deploy folders. Whatever else is decided, the dashboard should not be shared
externally in this state, and the warn-box instruction to "explain the dip proactively" should be
withdrawn before anyone follows it.

**Fix:** rebuild the dashboard from the corrected workbook once Problems 1–4 land, and until then mark
the 2026–2030 columns as under revision. Do not patch the KPI deltas alone — that would leave a
consistent-looking page still built on the 3 % rule.

---

## Deliberately not touching

- **UK CV only — sheet `4. ITUK UIO Projection` and Overview rows 22 and 24.** Those already use real
  registration data, proper survival curves, and an age floor. Leave **22/24** alone. **Do not read
  this as “all UK rows”** — **row 25 (IUK LCV)** is in scope (Decision — IUK LCV, locked 30 July 2026).
- **The summary tables further down sheet 1 (rows ~93–200).** These have been stale and misaligned
  across every country since about V12. Already flagged. They need their own rebuild, not a patch.

---

## Build order

1. **Israel first.** Self-contained, doesn't depend on anything else, biggest single correction.
2. **The survival curve fix** (Problems 1 and 2 together — they are one change), **including IUK LCV
   row 25** per the locked CY2026F = **44,926** arithmetic (not V19’s 49,280).
3. **The sales plan handling** (Problem 3): one-to-one on the level, smoothing on the annual profile,
   plan-only rows split out.
4. **Flag the four low-confidence markets** (Problem 5).
5. **Fix the weight decode and the GPS N35 target** (Problem 6). Independent of the rest — can run in
   parallel. Nothing is corrupted today because the VIN file isn't wired into anything, but the GPS
   half is live and affecting Portugal now.
6. **Rewrite the documentation** (Problem 7).
7. **Rebuild the dashboard** (Problem 8) — last, because it reads the corrected file. But do step 0
   first: pull `ISUZU_UIO_Dashboard_2026.html` out of both `07_deploy/` folders, or mark its 2026–2030
   columns as under revision, so nothing ships while the rebuild is in flight.

Before touching the live file, save a dated copy into the `_Archive` folder. Right now the only copy of
V19 that exists is the working file itself.

## How we'll know it's right

- Run the forecast engine backwards to 2025 for Ireland, Portugal and Israel. It should land on the
  historical number within one unit. No jump at the 2025/2026 boundary.
- The pickup fleet in 2030 must be smaller than in 2025. Falling registrations cannot grow a fleet.
- **IUK LCV (row 25) CY2026F = 44,926** (declining vs 47,783); must not quote V19’s 49,280.
- Israel 2026 must reconcile to 14,019, class by class, with any exclusions written down.
- No row may grow faster than its registration input divided by its survival-curve length.
- Every forecast number must trace to a named file that actually exists on disk.
- Cell B4 on sheet 1 set to "Exclude MIDI" before any Kosha or action-plan figure is quoted.

---

## The new VIN file — what it is and what it's worth

**Location:** `C:\Users\jerom\Desktop\claude\ISZE\01_data\07_UIO\vin\`
**Contents:** 3,238 trucks, every one with a unique VIN, no duplicates, all 17 characters valid.
**Covers:** Portugal 2,111 · Ireland 647 · Germany 183 · Malta 130 · Cyprus 114 · Belgium 49 · Greece 4.
**Period:** 2020 to mid-2026.

### First thing to be clear about

These are **not registrations**. They are trucks built and shipped from Japan, dated by invoice,
shipment or assembly. The gap between "shipped from Japan" and "registered in Ireland" is exactly the
gap Problem 3 is about. The README in that folder already says this and says not to substitute these
counts for the car park. That instruction is correct and should stay.

### Where it genuinely helps

**1. It settles the plan-versus-reality question.** Already used above: Ireland shipments and Irish
registrations match within 1.3 % over five years. That is the evidence base for the one-to-one decision,
and it is the first time we've been able to check it at all.

**2. It gives us a real measured scrappage rate.** Also used above: Ireland 13.3 %/yr, Portugal 7.4 %/yr.
Independent of any survival curve, straight from shipments and fleet movement. Both land near the 10 %
the curve predicts and nowhere near the 3 % the model uses. This is the strongest single piece of
evidence for Problem 1.

**3. It covers exactly the right seven markets.** Belgium, Cyprus, Germany, Greece, Ireland, Malta,
Portugal — precisely the seven markets where the sales plan drives the truck forecast. Not a coincidence,
but very convenient.

**4. It proves the medium-duty rows are fiction.** Every truck in the file is a light N-series (NLR, NMR,
NNR, NPR) or an F-series (FRR, FSR). Zero medium-duty units in six years. The plan says Portugal will
have 498 of them by 2030.

**5. It probably closes an open question from June.** We flagged that Ireland registered 32 F-series
trucks in 2025 against a plan of 1, and wondered about grey imports. The VIN file shows Ireland was
genuinely shipped 30 F-series in 2023 and 18 in 2024. Those almost certainly registered late — this is
our own supply, not grey market. Worth confirming with Isuzu Ireland, but the suspicion is largely
answered.

**6. It exposes markets we can't trust.** Problem 5 above only became visible because of this file.

### The 2025 gap is real — it's the P700 changeover

Ireland, Germany, Belgium, Cyprus, Malta and Greece all show zero shipments in 2025; only Portugal has
records. **This is not a data problem.** It is the model changeover to the new P700 range — the biggest
product overhaul Isuzu has done in Europe in thirty years. The P700 covers 3.5, 6.5, 7.5 and 13.5 tonne
chassis, was shown publicly at RTX at the end of June 2026, order books opened in July, production
starts at Fujisawa in August 2026 and first chassis reach bodybuilders from October.

So the shape of the data is exactly what a changeover looks like: outgoing range winds down through
2024, a trough in 2025, and the new range starting to flow in 2026 (Ireland 119 units in the first half).

**What this means for the forecast:** the 2025 registration trough is temporary and must not be used as
the baseline. It also softens one earlier concern — the jump from 61 Irish registrations in 2025 to a
plan of 216 looks less extreme once you compare against the pre-changeover average of about 89 a year
rather than against the trough. It's still a 2.4× step and still needs justifying, but the 2025 number
is not the right comparison.

Portugal keeps shipping through 2025 because it runs on a different build/supply pattern from the
others — 1,991 of its 2,111 units come through as semi-knocked-down kits. Portugal is **no longer** an
assembly plant, so those kits should not be read as local manufacturing.

**Re-exports are handled correctly.** 34 trucks move between markets — "Portugal to Belgium", "Malta to
Cyprus". The build script credits them to the destination, which is right.

### Recommendation

**Yes, use it — but as a validation tool, not as a replacement for the car park.**

It cannot rebuild the fleet history: it only goes back to 2020, and a truck fleet has 15 to 20 years of
history in it. What it does brilliantly is check whether our assumptions match reality, and so far it
says two of them badly don't.

Concretely, for V20:

- Use it to **set the scrappage rate per market** instead of assuming one, wherever the fleet history is
  real (Ireland, Portugal today; Israel and the other four once rebuilt).
- Use it to **calibrate the shipment-to-registration lag** for Problem 3.
- Use it as an **annual sanity check**: shipments over five years should roughly equal registrations
  over five years. Where they don't, something is wrong with one of the two sources.
- Do **not** overwrite any car park figure with a VIN count.
- Chase the **UK and Israel VIN packs**. Israel especially — combined with the government fleet data
  from the presentation, that would let us decompose the Problem 4 gap properly instead of guessing
  between three explanations.

---

## Still open

- **Where is the Israeli government extract?** The presentation is a picture of the data, not the data.
  Slide 14's chart can't be read reliably — it has 14 bars for 13 years, a duplicated 2022 label and one
  bar with no number on it. We need the file: registration year by weight class, plus their class
  definitions. Without it, the 3,259-truck gap can't be split across the three explanations.
- **Is €296 or €250 the right wallet for a 3.5-tonne Grafter?** The targets file says €296 on its own
  line; the code routes N35 to the €250 pickup rate. Someone has to decide which is intended.
- **Where does the N35 split come from for years before 2020?** The VIN register only covers 2020
  onward, and the Portugal correction needs the mix across the whole fleet.
- **Two source files cited in the workbook do not exist on disk.** `IMIT_forecast.xlsx` and
  `UIO_ISUZU_2025.xlsx` are named in the `Data Sources` sheet but are not in the ISZE folders, Downloads,
  Desktop, Documents or OneDrive. The pickup numbers do reconcile to the November 2025 IMIT study, so
  that one is just a wrong filename. The Israel file can't be checked at all.
- **Ireland F-series** — worth a one-line confirmation from Isuzu Ireland now that the VIN data mostly
  explains it.

*Added 9 August 2026:*

- **Who made the June change, and against what request?** This is the largest gap in the document. The
  spec says "**we** changed how the scrap step works, and **we** got it wrong", and Problem 7 says
  "**nobody** updated the sheets that describe them". No person, team, session or ticket is recorded
  anywhere — not in this spec, not in `05_memory/projects/uio.md`, not in any commit message. Git
  attribution shows only who committed the spec, which says nothing about who edited the workbook.
  Until this is answered, the same change can be made again by the same route. **Whoever owns the
  answer, it is not derivable from anything currently on disk — it has to be supplied.**
- **What is the appendix missing?** ~2,500 registrations a year enter the Grand Total from rows that
  are not in the appendix table (see *The appendix does not add up*). Recover them or relabel the total.
- **Which market perimeter does "ISZE pickup registrations" mean?** The appendix and Problem 2 differ by
  615 units for 2026 after removing MIDI Italy. Fix the definition, not the number.
- **The €296 / €250 Grafter wallet is not a background question.** It is live in Portugal now and it
  moves a GPS denominator. It has been open since the first draft; it should be closed before, not
  during, the rebuild.

---

## Appendix — the registration numbers currently buried in the file

The forecast cells contain values only, no formulas, so these inputs aren't visible to anyone opening
the workbook. Recovered by working backwards from the numbers.

| Row | Market | Type | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---:|---:|---:|---:|---:|
| 25 | UK | pickup | 2,930† | 2,400 | 2,400 | 2,400 | 2,400 |
| 60 | Italy | pickup | 4,500 | 4,600 | 4,690 | 4,690 | 4,690 |
| 44 | Germany | pickup | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| 42 | Germany | truck | 390 | 388 | 624 | 898 | 1,000 |
| 35 | Belgium | pickup | 840 | 840 | 840 | 840 | 840 |
| 54 | Portugal | pickup | 900 | 900 | 840 | 840 | 840 |
| 51 | Portugal | truck | 456 | 456 | 456 | 456 | 456 |
| 52 | Portugal | truck (medium) | 96 | 108 | 108 | 108 | 108 |
| 29 | Ireland | pickup | 430 | 430 | 430 | 430 | 430 |
| 26 | Ireland | truck | 216 | 216 | 216 | 216 | 216 |
| 27 | Ireland | truck (medium) | 36 | 36 | 36 | 36 | 36 |
| 81 | Greece | pickup | 630 | 630 | 630 | 630 | 630 |
| 90 | Cyprus | pickup | 360 | 400 | 360 | 360 | 360 |
| 18 | Sweden | pickup | 900 | 920 | 875 | 875 | 875 |
| 15 | Norway | pickup | 420 | 350 | 455 | 455 | 455 |
| 9 | Israel | pickup | 900 | 1,000 | 930 | 930 | 930 |
| 75 | Hungary | pickup | 370 | 370 | 275 | 275 | 275 |
| 84 | Romania | pickup | 170 | 170 | 172 | 172 | 172 |
| 66 | Finland | pickup | 140 | 140 | 155 | 155 | 155 |
| 21 | Denmark | pickup | 120 | 120 | 135 | 135 | 135 |
| 63 | Malta | pickup | 75 | 125 | 105 | 105 | 105 |
| 12 | Iceland | pickup | 45 | 45 | 92 | 92 | 92 |
| **Sum of the rows above** | | | 15,924 | 15,644 | 15,824 | 16,098 | 16,200 |
| **"All rows" as previously stated** | | | **18,478** | **18,267** | **18,412** | **18,605** | **18,660** |
| **Unexplained** | | | **−2,554** | **−2,623** | **−2,588** | **−2,507** | **−2,460** |

† V19 buried ~2,930 for UK pickup 2026 regs. For the IUK LCV rebuild use **IMIT 2026E ≈ 3,020**
(Decision — IUK LCV). Swapping that single cell moves the row sum to 16,014 (+90).

### The appendix does not add up *(found 9 August 2026)*

The "All rows" line was presented as the total of this table. **It is not.** Every year is short by
roughly 2,500 units — about **14 % of the registration input** — and the gap is stable across all five
years, which means a *block* of rows is missing from the recovery rather than a few cells being off.

This matters more than the 90-unit row-25 correction above, because the appendix is the only visible
record of what is driving the forecast. Every one of these cells is a hardcoded value with no formula
behind it; if 2,500 units a year are entering the Grand Total from rows nobody has written down, the
build cannot be verified.

Some absences are explainable and should be confirmed rather than assumed:

- **UK trucks** (ITUK CV rows 22/24) come from sheet 4, not from a buried constant — correctly absent.
- **Israel rows 7/8** are rebuilt entirely under Problem 4 — correctly absent.
- **Poland and Netherlands** carry 27 and 1 units of parc; far too small to matter.

That does not account for ~2,500/yr. Before the rebuild starts, either recover the missing rows into
this table or relabel the line honestly as a partial recovery. **Do not carry a total that is 14 %
larger than the numbers printed beneath it.**

**A second reconciliation to settle at the same time.** The pickup rows above sum to **14,730** for
2026. Problem 2 quotes IMIT's 2026 ISZE pickup registrations as **10,845**. Removing Italy (4,500 —
MIDI, outside the ISZE perimeter) gives 10,230, still **615 short**. No obvious perimeter reproduces
10,845 exactly. One of the two figures is on a different market basis, and the basis is written down
nowhere. State it explicitly before either number is quoted.
