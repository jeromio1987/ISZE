# Distributor Leakage Cockpit + Sales Performance Review packs

One payload, two audiences. The internal cockpit answers **which partners are critical and
where they are leaking**. A customer pack answers **how is this market performing**, across
service families, fleet spend, brand mix and our own part-group classification, over time, with
the part numbers to act on.

## Build

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE

# 1. extract: reads the derived layer, writes payload.json. Refuses to build on a red pipeline.
python 02_dashboards\_build\leakage\extract.py

# 2. internal cockpit: all markets, named, includes the partner league
node 02_dashboards\_build\leakage\build.mjs

# 3. one customer pack per distributor
node 02_dashboards\_build\leakage\build.mjs --audience=customer --focus=ITUK
node 02_dashboards\_build\leakage\build.mjs --audience=customer --focus=SWEDEN
node 02_dashboards\_build\leakage\build.mjs --audience=customer --focus=BELGIUM

# 4. gate: static checks on the artifact, then rendered paint checks in real Chrome
python 02_dashboards\_build\leakage\verify.py
python 02_dashboards\_build\leakage\qa_leakage_tool.py

# 5. receipts (runs both gates again and records the result)
python 02_dashboards\_build\leakage\receipt_leakage_tool.py
```

To add a distributor, run step 3 with the new `--focus` code. To roll out all 22, loop over
`network_dbs` in `payload.json`.

## Outputs

| Audience | File | Panels |
|---|---|---|
| Internal | `02_dashboards/sales/ISZE_Leakage_Cockpit.html` | 11, including the partner league |
| Customer | `02_dashboards/sales/leakage_packs/ISZE_Sales_Performance_Review_<DB>.html` | 10 |

Each has a sibling `OPEN_*.cmd` (CRLF) for double-click.

## Like-for-like basis

The current year is part complete. Every comparison uses the **same months of each year**, and an
**average month** is shown so periods of different length can be compared without annualising
anything. Nothing is annualised, anywhere.

This matters more than it sounds, because the source has a part-year trap:

| Source | Problem | How it is handled |
|---|---|---|
| Service-demand denominator | The current-year expected demand is a **full 12 months** while the current-year actuals cover **6**, so the filed current-year capture rate reads about **half** its real value. | Both are carried as `capture_pct` and `capture_lfl_pct`. The window figure is the one labelled to read, and the panel says so in an amber banner. |
| Spend per vehicle | The current-year bar covers six months, so it sits low for a reason unrelated to performance. | The bar is labelled part year and the panel points the reader to the like-for-like figure instead. |
| Growth | Comparing a half year with a full year produced a headline of −58% where the real like-for-like movement was **+34.2%**. | Growth is computed on matched six-month windows only. |

Measured on the build date: billing runs to 2026-06-30, all 18 scored markets have exactly six
months of 2026, and the first half is ~49% of a full year.

## What to act on (part numbers)

The action ledger carries 22,738 part-level rows across all 22 markets with a recommended action.
The panel shows the largest lines per market with description, what is happening, the value and the
proposed action, grouped by cause first so the reader gets a short list rather than a data dump.

- Pricing-review signals are **excluded from customer packs**: that work is ours to conduct.
- A part with no description in any approved layer is shown by number and flagged, never given an
  invented name.
- A market with no worked-up list gets this market's own service-family value instead, never
  another market's part numbers.

## In-panel selectors

Panels that would otherwise show a wall of small multiples use a selector instead: the
service-family trajectory and the action-list filter are both dropdowns that redraw only their own
panel. The paint QA asserts that every selector actually changes its panel.

## How the customer strip works

This is the part that protects the relationship. It is not CSS hiding.

1. **Rows.** Only the focus market's rows are written into the file. The other markets are
   not filtered in the browser; they are absent from the data.
2. **Peers.** A benchmark is reduced to a number and a member **count**. The codes of the
   other markets never enter the payload, so they cannot leak out of it.
3. **Panels.** The partner league declares `audience: ["internal"]`, so its render source is
   never compiled into a customer file. Its field names are absent too.
4. **Labels.** The label entries for internal-only panels are dropped, so even the nav
   wording is gone.
5. **Enforcement.** `build.mjs` greps the finished customer file for the other 21 market
   codes and fails the build if any appears. `verify.py` repeats the check plus a scan for
   internal content (`risk_score`, `undercut`, `defection`, `threshold`, `early_warning`).

## Peer benchmarking

Benchmarks are always anonymous and always the same customer type: a CV market against CV
markets, an LCV market against LCV. Where the exact customer type is too thin to benchmark
(ITUK is CV, and there are only two CV markets), the default widens to the customer-type
pool and the pool is **named on the figure**, so the reader knows what they are compared
with. A group with fewer than three members never produces a median.

The benchmark always excludes the market being benchmarked, otherwise it is quietly
comparing a market with a median that contains it.

## Component intervals — the three-level rule

Expected demand for a service family is built from a component replacement interval. Each
category in each market takes the best level available:

| Level | Source | Applies to |
|---|---|---|
| 1 | **The market's own interval data** | ITUK only. Never extended to another market. |
| 2 | **The vehicle-family maintenance schedule** | The N-series schedule for trucks, the D-Max schedule for pickups, weighted by this market's measured vehicles-in-service split. |
| 3 | **Model placeholder** | Not scored. Carried as euro so the scale is visible, separated from the firm figure. |

### The family split is measured, not taken from the label

`distributor_dimension.csv` carries a `scope` label of CV / LCV / MIXED, but that label is not
reliable for deciding which schedule applies: **four markets are labelled MIXED while being 91%
or more one family** (Belgium 99% pickup, Greece 99%, Germany 95%, Cyprus 91%). Using the label
alone gave those markets no interval at all when the dominant family's schedule plainly applied.

`uio_by_model_bucket.csv` carries a real split, and that is what is used:

| Market | Trucks | Pickups | Applied |
|---|---:|---:|---|
| ITUK | 23,068 | 0 | N-series only |
| UTI | 10,336 | 0 | N-series only |
| IUK | 0 | 47,783 | D-Max only |
| Sweden | 0 | 8,443 | D-Max only |
| Belgium | 113 | 9,480 | D-Max, weighted 99% |
| Portugal | 2,475 | 4,733 | weighted 34% / 66% |

### A capture rate needs fleet coverage

A percentage is only interpretable when the expectation covers essentially the whole fleet.
Where it does not, the numerator counts the whole market while the denominator counts part of
it, which inverts the number: Belgium's AdBlue read **627%** because 69 units billed market-wide
were divided by an expectation built on its 113 trucks alone. Categories below **95% fleet
coverage are not scored**, and their euro is carried separately so the scale is not hidden.

### What the sources actually cover

| Category | CV (N-series) | Pickup (D-Max) | The market's own |
|---|---|---|---|
| Oil filter | 40,000 km | 20,000 km | - |
| Fuel filter | 40,000 km | 20,000 km | - |
| Urea (AdBlue) filter | 200,000 km | not in sources | 200,000 km |
| Brake pad | inspect only | front 50,000 / rear 75,000 km | 100,000 km |
| Brake shoe | inspect only | not in sources | 100,000 km |
| Brake rotor | not in schedule | paired with every 2nd front pad | - |
| Air filter | indicator-driven | not in sources | - |
| Clutch (5 parts) | **no replacement interval** | **no replacement interval** | - |
| Blower filter | clean as needed | not in sources | - |

Only 4 of the 14 scored categories have a replacement interval in the N-series schedule. The
schedule gives a clutch **fluid** interval at 40,000 km, which is a different part from the
clutch itself, so a clutch replacement rate cannot be read from it.

Sources: `01_data/03_PMS/PMS_Intervals_Authoritative_Sources.md` (N-series, Rene Paul GIDSS
schedules, 2026-07-16) and `03_analytics/Isuzu/prism/data/lcv_pms_genuine.yaml` (D-Max), plus
`01_data/03_PMS/ISZE_ITUK_Brake_Factor_IML_Ask_2026-07-23.md` for the market-supplied figures.

### Corrections this produced, ITUK

| | Before | After |
|---|---:|---:|
| Capture CY2025 | 65.9% | 83.0% on sourced intervals |
| Gap, firm | - | EUR 228,294 |
| Gap, on placeholders | - | EUR 657,481 |
| AdBlue gap | EUR 342,356 | EUR 20,022 |

- **AdBlue was modelled at an implied 39,499 km against an authoritative 200,000 km.**
- **Blower filter and pilot bearing were scored against CV markets** with zero units sold
  network-wide. Dropped for CV; worth 24,600 units of fictional demand at ITUK.
- **Brake rotor and pad are pickup parts** and were being given the truck schedule.

### Open, and printed on the face

Whether one paired front-and-rear brake job consumes **one part unit or two**. If two, the brake
expectation doubles and the capture percentage roughly halves. Stated per family on the panel.

## Mileage (annual distance)

One coherent figure per market, because using 50,000 km for a brake interval and 20,000 km for a
filter in the same market mixes a truck number with a car number. Measured odometer medians from
`01_data/00_derived/warranty_cv_km_age_by_market.csv` replace the flat 20,000 km default where a
market has one. Pickups use the 20,000 km D-Max figure, since the measured odometer sample
covers CV trucks.

## Data sources

All from `01_data/00_derived/`, plus `01_data/17_interactions/account_health_latest_flagged.csv`
for the league. The extractor refuses to run unless `_verification_report.json` is green.

Rate conventions are **not** uniform in the derived layer and are declared explicitly in
`extract.py`: `capture_rate` is a 0-1 fraction, `gps_pct` is 0-100, and `vs_network_risk_pp`
is already in percentage points. Guessing these silently corrupts every gap, so each column
goes through a named converter.

## Honesty rules built into the payload

- Every gap carries euro, the service family or part group, and the fleet base. A unit count
  is never a finding.
- Service-demand capture is modelled from assumed service intervals. The share of
  measurements reading above 100% is derived live and disclosed, because it means the
  assumed demand is too low, not that the market over-performs.
- The share of the spend ceiling set by the flat per-vehicle placeholder is derived live and
  disclosed, with the member markets named internally and suppressed in a customer pack.
- Gap typing (substitution / under-service / catalogue) is a CY2026 model with no history,
  and each panel using it prints that vintage on its face.
- The revenue bridge carries volume and price only: the source has no mix leg, and its
  coverage share is stated rather than left to look like a full reconciliation.
- Dealer-outlet detail exists for **one** market. Everywhere else the page shows the national
  number and an amber note, never an implied network view.

## Known limits

- Dealer-outlet grain is thin. Only the UK CY2025 sales-to-dealer file carries outlet names;
  every other market's detail stops at the national total. The honesty panel measures and
  states this rather than implying a network view.
- The part-group mix comes from a 6-market sales-to-dealer file, so a market without it shows
  an amber note in that panel while the revenue-at-risk figures still render from the
  22-market classification file.
- `revenue_waterfall.csv` does not decompose mix (`delta_mix_eur` is zero on every row), so
  no mix effect is reported.
