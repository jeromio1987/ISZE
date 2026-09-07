# Deep Sales-to-Dealer Analytics Framework (GPS + PMS + AIM)

**Status:** accepted plan · implemented in `build_next_analyses_std.py`  
**Audience:** Mode B (internal) · Mode A labels on the Six-DB dashboard use **sales-to-dealer** language  
**Does not:** invent new dashboards · touch warranty logic · rebuild `sales_fact` unless broken

---

## Goal

Stop gasket/bolt qty from inflating country rankings and “capture” reads by layering:

1. AIM relevance gates (core vs consumables)
2. GPS spend-per-UIO (overall / core / consumables)
3. PMS expected-vs-actual (PRISM denominators)
4. One dashboard with toggles (not more HTML packs)

---

## Layer 0 — Push vs Pull (value-first)

| Layer | Source | What we measure |
|-------|--------|-----------------|
| **Billing (push)** | `01_data/00_derived/sales_fact.parquet` | Invoice EUR + billed qty (parts lines) |
| **Sales-to-dealer (pull)** | `dealer_sellout_long_*_CY*.csv` | Dealer qty → **ISZE-denominated value proxy** = qty × distributor×PN median ASP from billing |

Warranty: leave alone (no new warranty filters in this pack).

---

## Layer 1 — Consumables gate (AIM taxonomy)

**SSOT:** `01_data/00_derived/aim_pn_classification.csv`  
**Classifier:** `03_analytics/Isuzu/prism/modules/aim_pn_classifier.py`  
**Attach path:** `dealer_sellout_analytics.attach_pn_master` → `enrich_unified_taxonomy` (joins AIM L1/L2/L3 onto PN)

A PN is **consumables** when **any** of:

- `aim_l1 == "Hardware & consumables"`, **or**
- `aim_l2` / `aim_l3` matches gasket / seal / bolt / fastener (case-insensitive substring)

Flags:

| Flag | Meaning |
|------|---------|
| `consumables_flag` | True if gate above hits |
| `core_flag` | True if not consumables |

**Default ranking / AIM capture charts use `core_flag` only.** Consumables remain visible under the Consumables focus toggle; their share of total proxy € is always shown for transparency.

---

## Layer 2 — AIM buckets (inside the gate)

Unchanged AIM split (from BVP xref):

- `bvp`
- `genuine_contested`
- `genuine_only` (implicit remainder)

Country BVP capture / mix ranking for the **Core** focus applies this split **only on core PNs**. Overall focus keeps the prior all-PN behaviour for context.

---

## Layer 3 — GPS gated metrics (€ / UIO)

**Engine / formula anchor:** `03_analytics/Isuzu/prism/modules/gps_engine.py`  
**Dictionary:** `metric_dictionary.md` § GPS — `spend_per_unit_eur = total_sales_eur ÷ uio_units`  
**UIO denom:** `gps_spu_by_distributor.csv` / AIM payload `uio_units`

For each DB and gate ∈ {overall, core, consumables}:

| Metric | Numerator | Denominator |
|--------|-----------|-------------|
| **Dealer GPS-style proxy** | Sales-to-dealer value proxy (€) for gated PNs | UIO park for DB |
| **Billing GPS** | Billing net EUR for gated PNs | Same UIO |

### Channel labels (hard)

| DB | Park channel | Never say |
|----|--------------|-----------|
| **IUK** | **LCV** (D-Max / pickup) | “trucks” / CV for IUK |
| **ITUK** | **CV** | — |
| UTI | CV | — |
| IRELAND / PORTUGAL / GREECE | CV+LCV | — |

IUK ≠ ITUK; IRELAND ≠ IUK.

---

## Layer 4 — PMS expected vs actual

**Engine:** `03_analytics/Isuzu/prism/modules/pms_engine.py`  
**Assumptions:** `prism/data/pms_capture_assumptions.yaml`  
**Dictionary:** `metric_dictionary.md` § PMS capture

Expected demand (per DB × year × `pms_category`):

```
base = UIO × services_per_year × addressable_pct
consumables (filters): expected = base × consumable_factor
wear (brake / clutch): expected = base × wear_factor
```

Defaults (see dictionary + yaml): N75 **0.5** svc/yr; LCV (IUK) **1.0**; addressable typically **100%** in current PRISM lane; air_filter factor **0.5**.

**Primary line_type = total** (sales is sales — not genuine-only as headline).

Actuals in this pack:

| Actual channel | Source |
|----------------|--------|
| **Billing actual €** | `pms_capture_by_db_year.csv` `actual_rev_eur` (line_type=total) |
| **Billing actual qty** | same file `actual_qty` (PRISM expected is unit-based) |
| **Sales-to-dealer actual €** | Dealer qty × median ISZE ASP on PNs with `pms_category` |
| **Expected €** | `expected_qty × avg_sp_eur` (unit denom converted when SP exists) |

Capture qty = `actual_qty ÷ expected_qty`. Capture € = `actual_rev ÷ expected_eur` when priced. Uncapped display OK; >100% is a finding.

**Headline PMS cats (always on the Six-DB page):** oil / fuel / air filters, brake pad / shoe / rotor, clutch kit / disc / pressure plate. Blower and other cats are not the landing layer.

---

## Dashboard controls (one HTML)

**Builder:** `03_analytics/Isuzu/prism/scripts/build_next_analyses_std.py`  
**Outputs:**

- `02_dashboards/sales/Next_Analyses_Sales_to_Dealer_SixDB.html`
- `01_data/14_dashboards/next_analyses_sales_to_dealer.json`
- `01_data/00_derived/next_analyses_findings.md`
- Sibling `OPEN_Next_Analyses_Sales_to_Dealer_SixDB.cmd`

### Metric focus

| Focus | Default? | Behaviour |
|-------|----------|-----------|
| Overall | no | All PNs in **€** (context) |
| **Core** | **yes** | Excludes consumables from ranking / gated GPS / gap headline |
| Consumables | no | Diagnostic only — still **€ gap first**, never qty landing |
| PMS | no | Filters / brakes / clutch expected vs actual (visible on landing anyway) |

### View

| View | Role |
|------|------|
| Gap | Billing invoice **€** vs sales-to-dealer proxy **€** (qty = checkbox diagnostic) |
| GPS | Gated spend per UIO (**landing**) |
| PMS | Headline service items in €; qty expected kept as the PRISM unit denom |

Landing paints: hero KPIs in € · Core · GPS €/UIO · € gap (not Consumables+Qty) · PMS filters/brakes/clutch · AIM L1 proxy €.

Language: **sales-to-dealer** (not dealer sell / sell-out as primary label). No new Mode A dashboard files.

---

## QA checklist

1. IUK axis / tables show **LCV**, never trucks.
2. Consumables share of proxy € visible when Core is selected.
3. PMS expected denominators match PRISM (0.5 svc/yr N75-class; factors from yaml).
4. Core ranking not bolt/gasket-inflated vs Overall (spot-check direction).
5. `file://` paint: Chart.js inlined; OPEN cmd present; no CDN required.
6. Gap chart default Y-axis is **Euros**, never Consumables+Qty on landing.
7. PMS section lists oil/fuel/air filters and brakes/clutch, not consumables-only.

---

## References

- `modules/gps_engine.py` — GPS = net EUR / UIO  
- `modules/pms_engine.py` — expected = UIO × freq × addressable × category factor  
- `docs/metric_dictionary.md` — GPS / PMS / BVP definitions  
- `01_data/00_derived/aim_pn_classification.csv` — AIM L1/L2/L3 gate  
