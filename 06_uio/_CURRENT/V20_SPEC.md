# UIO V20 — what needs to change and why

**Status:** draft, nothing built yet — IUK LCV (row 25) CY2026F **locked** 30 July 2026
**Written:** 27 July 2026 (Jérôme Van der Pluym / Claude); **amended** 30 July 2026 (IUK LCV decision)
**File it applies to:** `C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\ISUZU_UIO_Overview_2026.xlsx` (V19, dated 18 June 2026)

---

## The short version

The car park model works like this: take last year's fleet, remove the trucks that were scrapped, add
the trucks that were newly registered. That gives this year's fleet. Repeat.

In June we changed how the "remove the scrapped trucks" step works, and we got it wrong. The model now
assumes a truck lasts 33 years. Everywhere else in the same file we assume roughly 10 to 12 years, and
the real-world data says the same. Because we only remove 3 % of the fleet each year instead of about
10 %, the fleet grows every year no matter what we feed in. That is the growth spike everyone is
looking at.

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
| The survival curve we use for trucks 1990–2025 | 9.9 years | **10.2 %** |
| The survival curve we use for pickups 1990–2025 | 8.1 years | **12.3 %** |
| The flat number used for 2026–2030 | 33.3 years | **3.0 %** |

So on 1 January 2026 the trucks in our model suddenly start living three times longer than they did on
31 December 2025. Nothing in the real world changed — only our arithmetic.

### How we know this is wrong, not just different

Three independent checks all say the same thing.

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
in line with IMIT direction. Alternative if needed for a labeled bridge: scale IML level by IMIT YoY —
same direction; prefer the scrap+regs arithmetic above for consistency with Problem 1/2.

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

### Correction — 2026-09-18: the "LD" label is not a weight class

The table above reads Israel's `LD` row as light (3.5 t) trucks. **It is not.** Two independent
sources agree that UTI's Israeli fleet contains no 3.5 t Isuzu truck at all:

- The **CV warranty VIN register** for UTI, 2,360 distinct VINs / 3,394 claims, Dec 2023 → Mar 2026:
  `NPR75` 895, `FRR90` 817, `FSR90` 627, `NPR85` 13, `NPR88` 8 — and **zero** `NLR` / `NKR` / `NMR`.
- The **Ministry of Transport table** in this section, whose smallest band is 6.5–7.5 t.

So the Israel `LD` row is the whole N-series fleet at 6.5/7.5 t and it is **already priced at the
7.5 t parts-wallet rate (€739)**, which is correct. The rate was deliberately left unchanged.
What was wrong is the label: `LD` means 6.5/7.5 t in Israel and 3.5 t in most of Europe, and the
same token drives the wallet rate per market. The workbook now says so — see cell **B92** of
`1.UIO Overview`, and Changelog rows V19-5 to V19-7.

**Consequence for the GPS / parts-wallet layer in §Problem 6:** the per-market 3.5 t shares below
were measured on shipments 2020–2026. The generator was since rebuilt to use each market's own
best available basis, and the numbers that matter are:

| Market | Share of the `LD` row that is 3.5 t | Basis used |
|---|---:|---|
| ISRAEL | **0 %** | CV claim VINs + ministry table — nothing to split |
| ITUK (UK) | 50.5 % | workbook sheet `2. Vehicle Volume` §B, read live |
| PORTUGAL | 62.0 % | JP VIN register, 2,111 shipments |
| MALTA | 36.9 % | JP VIN register, 130 shipments |
| GERMANY | **22.0 %** | Helwig parc bands (153 at or under 3.5 t of 697) |
| BELGIUM | 91.8 % | JP VIN register, 49 shipments |
| IRELAND | 6.3 % | SIMI weight bands |
| CYPRUS | 5.3 % | JP VIN register, 114 shipments |
| GREECE | 0 % | 4 shipments only — left unchanged rather than measure with four vehicles |

**Germany and Malta above contradict the table in §Problem 6**, which lists them as "0 % — no
change". Germany's wallet is €3.8 m, so that is not a rounding item. The Germany basis here is a
parc breakdown, not a shipment mix, so it is the better number.

Measured 2025E wallet impact: Portugal €3.05 m → €2.45 m (its GPS % rises by about a quarter),
Malta −10.5 %, Ireland −2.1 %, Belgium −1.9 %, Germany −1.8 %, Cyprus −0.7 %. Israel and the UK are
unchanged. Split table: `03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv`.

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

## Problem 9 — The car park has no tonnage dimension at all *(added 19 September 2026)*

This is the root defect behind `LD-LABEL`. The workbook's own mapping sheet states it plainly, so it
does not need to be inferred:

| Where | What it says |
|---|---|
| `Assumptions & Mapping` **A8** | `N-Series (NLR, NMR, NNR, NPR, N35, N50/55, N62/65, N75)` |
| `Assumptions & Mapping` **B8** | `LD (N-series label — weight differs by market)` |
| `Assumptions & Mapping` **C8** | *"Key assumption: all N-prefix = LD"* |
| `Cover` **C8** | `LD (N-series; 3.5 t or 6.5/7.5 t depending on market), MD, F-Series (N-series excl.), LCV` |
| `1.UIO Overview` **B92** | *"LD — label only; NOT a weight class…"* (the 2026-09-18 relabel) |

The 2026-09-18 relabel corrected the **label**. The **dimension** is still missing: `1.UIO Overview` has
one row per market × vehicle class × model type × year, and `model type` stops at `LD` / `MD` /
`F-Series` / `LCV` (columns D7 and below). There is no tonnage column anywhere in the workbook. Every
per-tonnage fleet denominator in the workspace therefore inherits the collapse, and the 3.5 t share that
the parts-wallet model applies (`uio_ld_n35_share.csv`) is a **downstream patch on a collapsed row**,
not a measurement in the fleet model itself.

**This problem is a spec change plus evidence. It is not authorised as a model rebuild** — see
*Scope of this change* below.

### The dimension to add

```
market × vehicle class × tonnage band × year
```

**Band set — take the sources' own bands, do not invent a finer one:**

| Band | Source bands that map to it | Note |
|---|---|---|
| **3.5 t** | JP register `gvw_t` 3.5 (NLR); SIMI `N Series 3.5T`; I-Motors `3.5 Ton`; Helwig `<=3.40` + `3.41–3.50`; ITUK list `N35` | bands the two 3.5 t sources split at 3.40/3.50 will be recombined |
| **5.5 t** | JP register `gvw_t` 5.5 (NMR); I-Motors `5 ton`; ITUK list `N50`/`N55` | |
| **6.5 t** | JP register `gvw_t` 6.5 (NNR); ITUK list `N62`/`N65`; UTI `6.5 TON` | |
| **7.5 t** | JP register `gvw_t` 7.5 (NPR); SIMI `N series 7.5T`; I-Motors `7,5 ton`; ITUK list `N75` (incl. `N75.190`); UTI `7.5 TON` | |
| **11 t** | JP register `gvw_t` 11.0 (FRR); I-Motors `11 Ton`; UTI `10TON` + `11 TON` | UTI's two 10 t classes are merged to this band |
| **13.5 t** | JP register `gvw_t` 13.5 (FSR); I-Motors `14 Ton`; UTI `12 TON`; ITUK list `F135`/`F150`/`F180` | band boundaries differ; see caveat |

**Grouping decision (justified, not arbitrary):** six bands, to be **reported as three groups** —
`3.5 t` alone (it is the one that changes the parts wallet), `5.5–7.5 t` (the N-series middle), and
`11–13.5 t` (F-series) — because no market has a source fine enough to defend the six as separate
denominators, and the 3.5 t cut is the only one with a different wallet rate (€296 vs €739) behind it.

**Boundary caveat that must be printed, not buried:** the band edges are not the same across sources.
Helwig's Nfz table **stops at 7.51–12.00 t** (`2026-06-11_ISD_Fahrzeugbestand_-_Basis_-_Übersicht_D_.xlsx`
sheet `Table`, D30 = 35) and carries **no 12 t+ row at all** — so on the German parc a `13.5 t` band
would silently mean "nothing", not zero. Band 6 is therefore **unestablished for Germany** and must be
emitted as null, never as 0.

### Where each market's tonnage comes from — measured

| Market | Tonnage source | File · sheet/column | Explicit band labels? | Period |
|---|---|---|---|---|
| **ITUK (UK)** | Duncan's VIN list + workbook ITUK parc | `01_data/90_INBOX/Duncan_VIN_20260723/2026-07-23_VIN_List_23_07_2026.xlsx` sheet `VIN List 23_07_2026` col `model` (`N35`, `N75`, `N50`, `N62`…); workbook `2. Vehicle Volume` §B rows 26–33 (cols C–U) | yes (`N35`–`N75`) | list 2008→2026; workbook parc 2024 |
| **ISZE 7 markets** (BE, CY, DE, GR, IE, MT, PT) | JP VIN register | `01_data/07_UIO/vin/VIN_register.parquet` cols `series`, `gvw_t`, `gvw_t_source`, `db_label`, `invoice_year` | yes (`gvw_t` 3.5/5.5/6.5/7.5/11.0/13.5) | **2020 → 2026 only** |
| **Germany** | Helwig Schmitt external parc | `…/_isd_std_mail_20260818/attachments/2026-06-11_ISD_Fahrzeugbestand_-_Basis_-_Übersicht_D_.xlsx` sheet `Table` C24:C30 / D24:D30 | yes | snapshot 31/12/2025 (**parc, not flow**) |
| **Ireland** | SIMI national registrations | `01_data/07_UIO/isuzuregdata.xlsx` sheet `Sheet2` A5/A6 | yes (`N Series 3.5T`, `N series 7.5T`) | 2010 → 2025 |
| **Portugal** | **NEW — I-Motors registration register, per VIN** | `01_data/07_UIO/Matriculas Isuzu SAP.xlsx` sheets `2005-2019` (bands J–N, chassis B, date P) **and** `2019-2026` (bands I–M, chassis B, date O); `SUM` sheet rows 11–15 | yes (`3.5 Ton`, `5 ton`, `7,5 ton`, `11 Ton`, `14 Ton`) | **2005 → 2026-06** |
| **Israel (UTI)** | UTI registration data by GVW band | `01_data/90_INBOX/_imie_mail_20260730/UIO ISUZU 2025.xlsx` sheet `גיליון1` — header row 1: `6.5 TON` / `7.5 TON` / `10TON` / `11 TON` / `12 TON`, rows 2–33 years 1994–2025 | yes | **1994 → 2025** |

**Fleet-path detail, stated because two per-VIN registers exist:** ITUK already has a **per-VIN**
model-label list (`N35` 11,739 / `N75` 11,554 distinct VINs). The JP register (`VIN_register.parquet`)
excludes ITUK and UTI by construction (`scope_cv_ex_ituk_uti` = True on all 3,238 rows;
`SCOPE_EXCLUDE_DB = {"ITUK","UK","UTI","UMI"}` in `01_data/07_UIO/vin/build_vin_register.py`). So the
ITUK tonnage layer needs no new pack — it needs the existing list **aggregated by `model` ×
registration year**, which is exactly the shape the new dimension requires.

### Where the tonnage is *not* measured

Two of the JP register's seven markets are flow-inferred rather than parc-measured, and this must be
labelled rather than silently published as a measurement:

| Market | Why | Evidence |
|---|---|---|
| **Malta** | **No 3.5 t truck in the register at all.** Destination MT = 130 shipments: NPR 73, NMR 48, FRR 9, **NLR 0**. `uio_ld_n35_share.csv` keeps a 36.9 % N35 share for Malta labelled `unmeasured`. An NMR is a 5.5 t truck — reading it as 3.5 t is the same misread that was already caught once. | register `db_label=Malta` × `series`: NMR 48, NPR 73, FRR 9 |
| **Cyprus** | **No 3.5 t truck in the register at all.** Destination CY = 114 shipments: NPR 60, NNR 48, NMR 6, **NLR 0**. The `uio_ld_n35_share.csv` row carries share 0.053 tagged `unmeasured`. | register `db_label=Cyprus` × `series` |

For both, the honest reading is **zero measured 3.5 t**, not "share unknown": the register covers the
whole 2020→2026 window and finds none. The fallback for a market with **no tonnage source at all** is a
row-level `tonnage_basis = "not measured"` and a **null** band split — never a silent default and never
a share borrowed from another market.

### The `LD` collapse — what replaces it, and the meaning problem

Replacing the token is the easy half. The hard half is that **`LD` does not decode to one band, and the
meaning differs by market**, so it cannot simply be renamed:

| Market | What `LD` actually holds | Basis |
|---|---|---|
| **Israel (UTI)** | the whole N-series at **6.5/7.5 t** — no 3.5 t exists | **verified:** CV claim VINs hold zero NLR/NMR/NNR across 2,143 distinct VINs; **reported, not verified:** the Ministry of Transport band table starting at 6.5–7.5 t (the source is a PDF slide picture, not a data file — see the note below) |
| **Portugal** | **60.6 % 3.5 t** | I-Motors register N-series 2005–2026: `3.5 Ton` 2,209 of (`3.5` + `5` + `7,5`) 3,646 = 60.6 % |
| **Ireland** | **30.9 % 3.5 t** (parc basis) | SIMI bands; `uio_ld_n35_share.csv` row (was 0.063 on a wrongly-attributed shipment number) |
| **Germany** | **22.0 % 3.5 t** | Helwig `3.41–3.50 t` 153 of `3.41–7.50 t` 697 |
| **ITUK (UK)** | **50.5 %** (workbook §B: N35 10,900 of 21,584 N-series) | workbook `2. Vehicle Volume` §B |
| **Belgium** | **85.7 %** (register NLR 42 of 49) | JP register |
| **Malta / Cyprus / Greece** | **0 % measured** | register holds no NLR |

So the replacement is not "split `LD` into bands by a fixed ratio". It is: **each market carries its own
measured band split, from its own source, with its own basis and period — and the split must be stated
in the row, not applied from a global assumption.** Greece is the case that shows why: its `LD` row is
**37 units** (2025E) on 4 shipments, so it gets `tonnage_basis = "not measured"` and stays unsplit
rather than being given a ratio derived from four vehicles.

### Additive to the year dimension

This is **additive**: the existing 1990–2030 year axis stays exactly as it is, and tonnage becomes an
extra key on `1.UIO Overview`. A per-year, per-band fleet therefore becomes possible for the first time
— `market × LD_band × year` — and `03_analytics/Isuzu/prism/scripts/build_uio_by_market_type_year.py`,
which already publishes the year axis (`01_data/00_derived/uio_by_market_type_year.csv`), is the natural
place to carry it, with a `band` column and a `tonnage_basis` column beside the existing `band_note`.

### Honest coverage of any future per-band denominator

| Market | Tonnage basis | Period a band split can be defended for |
|---|---|---|
| ITUK (UK) | per-VIN model label, 29,935 VINs | 2008 → 2026 |
| Portugal | per-VIN registration register, banded | **2005 → 2026** |
| Israel (UTI) | registration data by GVW band | **1994 → 2025** |
| Germany | Helwig parc snapshot | 31/12/2025 only (no history) |
| Ireland | SIMI banded registrations | 2010 → 2025 |
| Belgium, Cyprus, Malta, Greece | JP register shipments | **2020 → 2026 only** |
| Every other row in the workbook (Iceland, Norway, Sweden, Denmark, Netherlands, Luxembourg, France, Switzerland, Spain, Italy, Poland, Austria, Hungary, Serbia, Romania, Bulgaria, Azores) | **none** — `LD` rows are blank in most of these and carry no band source | not defensible |

That is the coverage: **six markets with a usable tonnage basis and a long enough period to build a
per-band fleet, and everything else unmeasured.** A per-band denominator can be quoted for those six
and for no others.

### Scope of this change — and what is separately broken

**This section records a spec change and the evidence for it. It does not authorise a V20 rebuild.**
The model rebuild is a separate decision and the 2026–2030 forecast columns must not be re-based on this
work. Separately and independently, **the 2026–2030 rows are known-broken** (`UIO-FCAST`: ~3 %/yr scrap
from 2026 against a ~10.2 % CV / ~12.3 % LCV curve, +9 % in 2026 rising to +59 % by 2030;
`01_data/00_derived/_data_integrity_open_issues.md`). A tonnage dimension built on top of a broken
forecast would simply give the error more keys.

### Open items this section does **not** close

- **The band edges differ by source** (Helwig stops at 12.00 t; I-Motors says `14 Ton`; UTI says
  `12 TON`). The six-band set is a reconciliation, not a measurement, and the reconciliation rule is
  written above rather than verified against a truck.
- **`9.5 t` has no home.** The NMR88 is described as a 9.5 t truck in
  `uio_ld_n35_share.csv`'s Malta note while `SERIES_GVW_T` maps NMR to 5.5 t. Malta carries 48 NMR and
  Cyprus 6. Until that is resolved, those units cannot be placed in a band honestly.
- **The 3.5 t Norway / Sweden question is unverified.** The JP register does not cover those markets.
  Measured distance (under-built by about 17 % vs the manufacturer 20,000 km, which would fit a 3.5 t)
  is **not** model identification and is not used here.

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
7. **Add the tonnage dimension** (Problem 9) — **spec only for now, and it is a model change.** Do not
   start this until Jerome authorises a rebuild. It sits after the survival-curve fix because a band
   split applied to an overstated fleet is a more precise wrong number, not a better one.

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
**Tonnage:** each row carries a measured `gvw_t` from the ISZJ series (`gvw_t_source = series` on all
3,238 rows), so this file is also the tonnage source for those seven markets — see §Problem 9.
Production dates run from **2019-08** and it includes **34 re-export rows**.
It is **not** the only per-VIN register in the workspace: ITUK has one too (29,935 VINs, 2008→2026,
`90_INBOX/Duncan_VIN_20260723/`) and Portugal has a banded one back to 2005 (`07_UIO/Matriculas Isuzu SAP.xlsx`).

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

## The ITUK (Duncan) VIN packs — what each one actually contains *(added 19 September 2026)*

Every file below was opened and read. `01_data/90_INBOX/Duncan_VIN_20260723/`.

| File | What it actually is | Per-VIN? | Model label? | Reg date? | Odometer? |
|---|---|---|---|---|---|
| `2026-07-23_VIN_List_23_07_2026.xlsx` (1.74 MB, sheet `VIN List 23_07_2026`, 103,515 rows) | **A real per-VIN register.** 103,515 rows → **29,935 unique VINs**, model label + registration date. Registration dates span **2008-01-02 → 2026-05-01**. The three named columns (`Complete Engine `, `CAB ASM…`) are **100 % empty** — headers only. | **yes** | **yes** (`N35`, `N75`, `N50`, `N55`, `N62`, `N65`, `F110`, `F120`, `F135`, `F180`, `N75.190`, plus `NQR(7)`, `NPR(3)`, `NKR(T)`, `DEMO`, `REF`, `unknown`) | **yes** | **no** |
| `2026-01-15_Fleet_VIN_list_2014_-_2024_study.xlsx` (3.32 MB) | Cohort study. Sheet `N35_N75` = **8,199 unique VINs, no duplicates**, reg dates **2014-01-01 → 2024-02-05**, with a **production date** column. Sheet `Sheet1` = **8,589 unique VINs** (a **superset** — it adds 390 F110/F120/F135 units). Sheet `pivot` is a Japanese-labelled summary (`個数 / vin`) by model × year. | **yes** | **yes** (`N35`, `N75`, `N50`, `N55`, `N62`, `N65`, `F110`, `F120`, `F135`) | **yes** | **no** |
| `2025-12-01_Fleet_VIN_list_2014_-_2024_study.xlsx` (3.43 MB) | Same layout as the January file, **older revision**: `N35_N75` sheet has **no production-date column** (4 cols vs 5), and Sheet1 still holds the same 8,589 VINs. Superseded by the January file. | **yes** | **yes** | **yes** | **no** |
| `2026-03-17_CBU_Master_Data_-_Appended.xlsx` (3.12 MB, sheet `Master`, 12,011 rows) | **Build-to-registration lifecycle tracker.** **12,011 unique VINs, one row each.** 49 columns: order month, shipping date, completion date, model code, model name, engine no, key no, UK arrival, DCU fit, order dealer, into bodybuilder, bodybuild complete, invoice date, invoice-to name, **registration date**, registration mark, non-RAV, customer (CRM). Registration dates **2021-09-24 → 2025-12-08**, **1,787 rows with no registration date** (built but not registered). VINs are distinct from the JP register (overlap **0**). | **yes** | **yes** (model *name*, e.g. `NLR87AU-ED5LAYE`, `NPR75U-…`) | **yes** | **no** |
| `2026-07-17_P700_ITUK_TRUCK_ARRIVALS.xlsx` (10 KB, sheet `Table 1`) | **A monthly arrivals plan, not a register.** 6 rows: `TOTAL`, `N35`, `N55`, `N65`, `N75`, `F110`, `F135`; 18 monthly columns **Oct-26 → Mar-28**. No VIN, no vehicle. | **no** | row label only | no | **no** |
| `2026-07-27_VIN_engine_cab_enquiries_2020_2026.xlsx` (18 KB) | **41 deduplicated VIN enquiry references** extracted from mailbox snippets. Sheets `VIN Enquiries` (41 rows), `Summary`, `Source Index`. Its own limitation note (B9): *"based on returned search snippets, not opened full email bodies."* Workbook split: 20 rows tagged Cab, 21 tagged Engine (both `B5`+`B6` = 41 ✓). | **yes** | no | no | **no** |

### Correction to the existing note

The standing note said the list has *model and registration date, no odometer and no transmission*.
**Confirmed from the files** — there is no odometer/mileage column in any of the six (the two empty
columns in the VIN list are named for an engine and a cab, and are empty). The note is correct.

### The APL file is a summary, not a register — as suspected

`01_data/90_INBOX/APL_ITUK_202607/2026-07-27_VIN_List_23_07_2026_20260724.xlsx` has three sheets:
`Sheet2` = **`Count of vin` pivoted by registration year** (rows = model: `N35`, `N75`, `NLR85`,
`NLR87`, `NLR88`, `NNR85`, `NNR88`, `N123`, `T123M`); `Workfile` (29,936 rows) and
`VIN List 23_07_2026` (103,515 rows). So the workbook does carry the underlying list — but the
audit **opened the summary sheet only** and confirms it is a spreadsheet *about* VINs, not the register.
Use `2026-07-23_VIN_List_23_07_2026.xlsx` directly.

### Verdict — yes, ITUK can now produce a fleet by tonnage and by year

**It could not before, and the spec should record that it now can.** The per-VIN model label
(`N35` / `N75` / `N50` / `N62` / `F110` / `F135` …) plus the registration date is exactly a
**tonnage band × year** count, on a base of **29,935 VINs spanning 2008 → 2026**. Aggregating the
`model` column by `registration_date` year gives ITUK a measured band × year registration series with
no new source required. The two caveats are real but bounded: **no odometer** (so this cannot produce
km/year) and **no transmission** (so AT/MT splits remain out of reach) — neither is a tonnage question.

**Ceiling on what that gives you:** it is a **registration flow**, not a parc. The workbook's ITUK parc
of 22,389 is a survival-curve convolution of those registration cohorts, so a parc-by-band number
requires running the same survival curve per band — which is a model change, and is out of scope here.

### Israel — the tonnage question is already answered without a VIN pack

**Yes, Israel's tonnage is obtainable, and the file was already in the workspace.** The spec's *Still
open* list said *"Where is the Israeli government extract?"* — the **UTI registration data by GVW band**
is on disk:

`01_data/90_INBOX/_imie_mail_20260730/UIO ISUZU 2025.xlsx`, sheet `גיליון1` — the sheet name the
`Assumptions & Mapping` sheet has been citing as `UIO_ISUZU_2025.xlsx` sheet `גיליון1` all along.

| | 1994 | 2000 | 2010 | 2020 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| 6.5 t | 1 | 14 | 39 | 16 | 7 | 10 |
| 7.5 t | – | 13 | 327 | 325 | 393 | 369 |
| 10 t | – | – | 53 | 165 | 173 | 199 |
| 11 t | – | – | – | 36 | 73 | 59 |
| 12 t | – | – | 27 | 128 | 213 | 160 |
| **Total** | **1** | **27** | **446** | **670** | **859** | **797** |

*(rows 2–33, years 1994–2025; row 34 totals `755 / 8,150 / 2,293 / 564 / 1,924 / 13,686`.)*

So Israel has a **31-year (1994–2025) band × year** registration series. It is a **flow, not a parc** —
the parcel in the workbook (row 7 = 6,059; row 8 = 4,277) is the surviving convolution of these cohorts
on the 20-year emerging-market curve, which is why the two totals differ. Building an Israel
**parc-by-band** therefore means applying the existing Israel survival curve **per band**, and the bands
are UTI's coarse 6.5/7.5/10/11/12 rather than a true GVW ladder.

**This does not close `UIO-FCAST`.** The same file's 2025 column totals 797 registrations against a
workbook row 7+8 parc of 10,336; the ~25 % understatement in the CV rows is a separate defect and the
band table does not resolve it.

### The Israel CV claim register — corrects the wording of the `V19-6` changelog entry

`1.UIO Overview` cell B92 and changelog `V19-6` say the CV warranty VIN register *"holds NPR75/FRR75
only"* / *"contains NPR75, FRR90 and FSR90 only, zero NLR"* — **the second half is verified; the "FRR75"
wording is not a series that exists.** Counted directly from the source claim files by decoding the
series out of each 17-character `VIN17`:

| File | Israel rows | Distinct VINs | NPR | FRR | FSR | NLR | NMR | NNR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `01_data/06_Warranty/Warranty_CV_2025.xlsx` sheet `Sheet1` | 1,082 | **898** | 326 | 319 | 253 | **0** | **0** | **0** |
| `01_data/CV_Warranty_01-08_2026.xlsx` sheet `Sheet1` | 1,506 | **1,245** | 287 | 539 | 419 | **0** | **0** | **0** |

**The substance holds: zero NLR, zero NMR, zero NNR across 2,143 distinct Israel claim VINs.** The
per-series counts the two decoded files give (NPR 326+287, FRR 319+539, FSR 253+419) do **not**
reproduce the `NPR75 895 / FRR90 817 / FSR90 627` cited in `uio_ld_n35_share.csv` and `_data_integrity_open_issues.md`;
the two files overlap in period (the 2025 file's claims run into 2026 dates), and the two claim
extracts may not be the same population. **The NPR/FRR/FSR figure is therefore *reported, not verified*
in this pass; the zero-NLR/NMR/NNR finding is verified here.**

---

## Still open

- **The Israeli government extract is a PDF picture, not a file.** The Ministry of Transport band table
  in §Problem 4 comes from the UTI presentation PDF, and the path quoted in this spec
  (`C:\Users\jerom\Downloads\מצגת לחלפים בלגיה - אפריל 2026.pdf`) **does not resolve on disk — not
  verified.** The *registration* band table **is** on disk and is what the tonnage section uses:
  `01_data/90_INBOX/_imie_mail_20260730/UIO ISUZU 2025.xlsx` sheet `גיליון1`. The **parc** band table
  (6.5–7.5 t = 8,610 etc., §Problem 4) still has no data file behind it.
- **The Israel CV band source has no 3.5 t column at all** — its smallest band is 6.5 t, so it
  corroborates "no 3.5 t in Israel" by omission and cannot independently measure a 3.5 t fleet.
  *The older phrasing of this item, and the second half of the N35-split item below, are superseded —
  the registration band table has been found.*
- **Is €296 or €250 the right wallet for a 3.5-tonne Grafter?** The targets file says €296 on its own
  line; the code routes N35 to the €250 pickup rate. Someone has to decide which is intended.
- **Where does the N35 split come from for years before 2020?** **Partly answered 19 September 2026** —
  Italy and Portugal are not covered by the JP register at all, so this question never applied to them:
  Portugal has a **per-VIN banded registration register back to 2005** (`Matriculas Isuzu SAP.xlsx`) and
  Israel has a band table back to **1994** (`UIO ISUZU 2025.xlsx`). What remains open is the **parc**
  mix before 2020 for the JP-register markets (BE, CY, DE, GR, IE, MT), where the register is a
  2020→2026 shipment flow and not a parc.
- **Two source files cited in the workbook do not exist on disk.** `IMIT_forecast.xlsx` and
  `UIO_ISUZU_2025.xlsx` are named in the `Data Sources` sheet but are not in the ISZE folders, Downloads,
  Desktop, Documents or OneDrive. The pickup numbers do reconcile to the November 2025 IMIT study, so
  that one is just a wrong filename. The Israel file can't be checked at all.
- **Ireland F-series** — worth a one-line confirmation from Isuzu Ireland now that the VIN data mostly
  explains it.

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
| **All rows** | | | **18,478** | **18,267** | **18,412** | **18,605** | **18,660** |

† V19 buried ~2,930 for UK pickup 2026 regs. For the IUK LCV rebuild use **IMIT 2026E ≈ 3,020**
(Decision — IUK LCV). The 18,478 all-rows total above is still the V19 recovery, not the locked rebuild.
