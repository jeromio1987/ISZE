# ISZE Master Dashboard — map + desk

One product, two rooms — not one mashed HTML file.

| Mode | File | Question |
|------|------|----------|
| **Map** | `dist/prism_map.html` | How is the network wired? What is live vs concept? |
| **Desk** | `dist/isze_cockpit.internal.html` | Wallet → Spend → Capture → Mix → Warranty |

Click a map node → desk focused on that module (`?module=gps_pure_sales&db=ITUK`). Customer builds stay desk-only (no map, no warranty, no concept nodes). Map chips are injected from the same derived files the desk modules read.

Status: **working skeleton, 5 desk modules** (wallet, GPS euros, PMS capture, mix, warranty) plus the PRISM map as front door.

```powershell
cd ISZE\02_dashboards\_composable
node build.mjs                                   # desk internal + prism_map.html
node build.mjs --audience=customer --focus=ITUK  # desk customer only (map still refreshed)
```

Map authoring copy: `ISZE/03_analytics/Isuzu/prism/docs/PRISM_SHOWCASE_v2.html` (edit there; build copies + wires desk links).

---

One dashboard with composable modules instead of ~60 standalone HTML files.

## Why no framework

Tested and rejected: Evidence.dev. Build = **86 MB / 130 files**, and the output
**does not work over `file://`** (DuckDB-WASM fetches its data, and browsers block
`fetch()` on file URLs). That breaks the one property the existing ISZE dashboards
have: double-click and it works, anywhere, offline, no server.

This build: **68 KB internal / 35 KB customer**, zero dependencies, zero network calls.
Data is inlined in a `<script>` tag — the same approach as the existing
`risk_cockpit.data.js` / `window.__RISK_COCKPIT_DATA__` pattern.

## The three mechanisms

### 1. Modules are composable

One file per module in `modules/`. The build picks them up automatically — adding a
module means adding one file, with nothing to register. (Verified: the GPS module was
dropped in by a separate workstream and appeared in the build with no wiring.)

```js
export default {
  id, title,
  audience: ["internal", "customer"],   // module-level visibility
  grain: "month" | "year" | "fy",       // the granularity the SOURCE actually has
  source: "01_data/00_derived/....csv", // path relative to ISZE root
  internalOnlyFields: [...],            // field-level redaction
  parse(csvText),                       // runs at BUILD time (node)
  clientRender(rows, ctx),              // runs in the BROWSER
  clientRenderCustomer(rows, ctx),      // optional, separate customer view
  initialState, onEvent(ev, state),     // optional per-module interactivity
}
```

### 2. Period is one control across all modules

`month` · `quarter` (fiscal, Q1 = Apr–Jun) · `fy` (Apr–Mar) · `cy`.
Monthly data is rolled up client-side; the total is invariant across every rollup
(verified: $7,338,739 in all four modes).

**Granularity mismatch is reported, never fabricated.** Ask for quarters from a
year-grain source and the module says so and shows the year.

**Gaps in the source are reported.** `warranty_fy26_monthly.csv` is missing Dec-2025
(11 of 12 months); the dashboard states this above the chart instead of presenting
11 months as a full year.

### 3. Internal vs customer is a BUILD choice, not a client-side toggle

With `--audience=customer`:

- modules whose `audience` excludes `customer` are **dropped entirely** (warranty is
  not in the customer file);
- fields in `internalOnlyFields` are **deleted from the data** before writing;
- if a `clientRenderCustomer` exists, **only that function source** is compiled in —
  the internal renderer never reaches the customer file.

That third rule exists because of a failed leak test: in the first version the
*values* were stripped but the *field names* (`revenue_gap_eur`, `top_gap_categories`)
still leaked via the compiled render source. A shared renderer with an
`if (isCustomer)` branch is not safe enough.

Verified on the customer file — none of these strings appear: `revenue_gap` ·
`top_gap_categories` · `brake_pad` · `clutch_disc` · `warranty` · `Total_USD` ·
the amounts `6925978` / `2050245` / `1610699` / `1837682`.

**Why build-time and not a login:** a static file has no server, no sessions, no auth
surface. What is not in the file cannot leak.

## No anonymised placeholders

Customer views show the distributor's own figures against **group aggregates**
(peer-group averages, network median, share, rank position). They never render a list
of "Distributor B…R" placeholder rows — that adds no information and reads as filler.

## Peer groups

CV / LCV / mixed membership comes from the `scope` field of the live GPS dashboard's
embedded `DUAL` dataset — the authoritative CV/LCV classification, not a guess.

Groups are derived from the dimension's `scope` and `region` columns, so adding a DB
updates every group automatically.

| Group | n | Members |
|---|---|---|
| Network average | 22 | all network DBs |
| CV customers | 2 | ITUK, UTI |
| Mixed (CV + LCV) | 7 | GERMANY, BELGIUM, IRELAND, CYPRUS, GREECE, MALTA, PORTUGAL |
| LCV customers | 9 | IUK, UMI, NORWAY, SWEDEN, DENMARK, FINLAND, ICELAND, ROMANIA, HUNGARY |
| Nordics | 5 | NORWAY, SWEDEN, DENMARK, FINLAND, ICELAND |
| CIS countries | 3 | UKRAINE, ARMENIA, KAZAKHSTAN |

When a selected DB is itself a member of the benchmark group, the module says so:
with a 2-member group the delta is mechanically symmetric and must be read as
position within the group, not as a gap to an independent benchmark.

## Shared distributor dimension — RESOLVED

`01_data/00_derived/distributor_dimension.csv` is the single source of truth for
"which DB is this row about" (docs: `distributor_dimension.md`, producer:
`01_data/91_build/build_distributor_dimension.py`). The build loads it, and every
module resolves its raw label to a canonical `distributor_code` through it.
**One picker drives all modules.**

```powershell
python 01_data\91_build\build_distributor_dimension.py   # rebuild the dimension
cd 02_dashboards\_composable ; node build.mjs            # then the dashboard
```

Only `network_db` rows reach the dashboard. Standing non-customers (Turkey / MIDI)
are classified **before** any other rule, so a future crossref row cannot promote
them back into the network.

Built from data, not guesswork:

| Fact | Source |
|---|---|
| payer → distributor_code | `sales_with_crossref.parquet` (`sold_to` + `distributor_code`) |
| sold-to level split | `sales_fact.parquet` (`sold_to_sap`, 477k rows) |
| entity names | `pricing_zpr1_customers.parquet` |
| CV / LCV / mixed scope | `ISZE_GPS_Dashboard.html` embedded `DUAL` |

**`payer_code` is not unique** — `1797` is both UMI and UTI. The join key is
`sold_to_sap`: **1797 = Universal Motors Israel (UMI)**, **1799 = Universal Trucks
Israel (UTI)**, confirmed by SAP customer name. The Israel merge is resolved.

Modules declare `dbField: "<column>"`; the shell adds `_db` (canonical code) to every
row, drops rows whose DB is not `network_db`, and warns at build time about any label
missing from the dimension.

Automatically excluded by this mechanism:

- **sold_to 373** — one line, FY2026, SaTy `DR`, material `SERVICE`, €160,493.
  A service fee, which `gps_pure_sales_2026-08-13.csv` counts as `pure_sales_eur` with
  `other_excl_eur = 0`. The pipeline excludes `SERVICE FEE WITHIN EUROPE` (it caught
  IMG's €10,000) but not the bare `SERVICE` code. **Pipeline fix still needed at source.**
- **MIDI (88)** and **IMG (105)** — real direct accounts, not network DBs.
  The GPS file already flags MIDI as `midi_non_gps_channel`.
- **Sverige2 (2929)** — excluded per business instruction.

### Population differs per module — surfaced, not hidden

`pms_summary_by_db.csv` covers 18 of the 22 network DBs; Ukraine, Armenia, Kazakhstan
and Palestine have no PMS capture data. Select the CIS group and the GPS module shows
three distributors while the PMS module says so explicitly instead of rendering empty.

Germany, Portugal and Denmark each bill through two sold-tos — any per-DB total must
sum them. The four CIS / Middle-East DBs have no CV/LCV scope, because the GPS
dashboard's classification only covers the original 18.

## Historic note — the blocker this replaced

The two sources use **different names for largely the same distributors**, and there
is no mapping table anywhere in `01_data/` (only parts dimensions exist).

- `pms_summary_by_db.csv` — 18 DBs, country/entity names: `BELGIUM`, `DENMARK`, `SWEDEN`…
- `gps_pure_sales_2026-08-13.csv` — 27 DBs, SAP legal-entity names: `Danmark`,
  `Sverige` / `Sverige2`, `Nordic FI`, `BL Iceland`, `AutoWallis`, `GasanZammit`,
  `Loutsios`, `ROM Auto`, `CIS-KTK`, plus `CBC`, `GA`, `IBX`, `IMG`, `IMIO`, `ISD`,
  `KIMA`, `MIDI`, `RSA`, `TR`

Only `ITUK`, `IUK`, `UMI`, `UTI`, `Ireland`, `Norway` overlap directly.

**Consequence:** "network" means 18 DBs in one module and 27 in another, in the same
dashboard. The DB picker therefore drives only its own module. A shared DB selector
across all modules needs a canonical distributor dimension first
(SAP payer code → DB name → country → CV/LCV scope → peer groups).

**`CIS-KTK` does exist** (payer 2294; FY2026 €1,009,971) — so a CIS peer group is
possible once the dimension exists. It is empty only in the PMS source.

The mapping is not guessed here: some pairs are obvious (`Danmark`→Denmark), but
`CBC`, `GA`, `IBX`, `IMG`, `IMIO`, `ISD`, `KIMA`, `MIDI`, `RSA`, `TR` and the
`Sverige` / `Sverige2` split need confirmation from the business.

## Known limitations

- **A customer link is a file, not a session.** Access cannot be revoked; you simply
  stop sending new links.
- **`verification_ok` is `null`.** The build does not yet read
  `_verification_report.json`, so the output carries no green-check guarantee.
- **Charts are inline SVG/CSS bars**, no chart library — keeps the file small and
  dependency-free. Richer visuals need a decision later
  (`_ui/chart.umd.min.js` is 196 KB and can be inlined).
- Peer averages are **unweighted** across DBs; a UIO-weighted figure is shown
  alongside. Neither is spend-weighted — the source has no addressable-spend column.

## GPS module — euros only, no GPS%

Source: `01_data/00_derived/gps_pure_sales_2026-08-13_v2.csv` (FY grain).
Canonical numerator: `pure_sales_eur` (GPS-eligible parts, Shell excluded).
Warranty is a client-side filter. Shell is an internal lubricants line, not parts.

**No GPS%.** UIO is not signed off and v20 is not approved, so the module computes no
denominator and shows no capture %. Check 4 (FY2026 other-exclusions €0 vs FY2025
€247k ITUK) is a banner in the internal view; FY-on-FY is not a clean trend. UMI
FY2024 ex-warranty is negative in the file and is shown, not hidden.

## Not built yet

UIO module (v20 not approved, v19 is current) · SaTy · SPA run-rate · fill rate
(note: `oem_peer_street_fill_*.csv` is a pricing survey, not supply fill rate).
The live `ISZE_GPS_Dashboard.html` has not been recalculated.
