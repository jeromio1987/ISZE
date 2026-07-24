# Data request — ITUK brake IAM (aftermarket) pricing evidence

**Requested by:** Jerome Van der Pluym (VP Sales ISZE) · **Drafted:** 2026-07-03
**Purpose:** Turn the Apr 2026 ITUK trip's brake-pricing finding from anecdote into a sized €
decision. Feeds the phase-one brake offensive (`05_memory/projects/pms-coverage.md`).

**Do not build anything from this file yet** — it specifies what to collect, not code to write.
Hand it to whoever is doing the pricing legwork (manual desk research, a dealer call round, or a
scraper build).

---

## 1. Why this is needed

The current evidence for "ITUK is losing the brake category to IAM (independent aftermarket)" is
two data points from one April 2026 site visit, both recalled from memory, neither sourced to a
document:

- **KS International brake parts ~60–75% below ITUK wholesale** (no PN-level backup)
- **JDS 9% avg retail discount vs RRP** (no PN-level backup)

These numbers cannot be quoted with confidence in a business case or IML brief — there is no
underlying price list, no PN mapping, no date stamp. This request collects the PN-level pricing
that would let someone recompute "60-75%" (or correct it) and turn it into a €/unit gap that lines
up with the PMS capture-gap numbers already in `pms_capture_by_db_year.csv`.

## 2. Exact part numbers to price (phase-one scope only)

Phase-one is **N75 brake + air filter** (`05_memory/projects/pms-coverage.md` — brake offensive,
air filter defensive). This request covers **brake only**; air filter is already the more
competitive category per the trip report and lower priority for this exercise.

**Genuine ISZE brake PNs in the PMS pilot registry** (`prism/modules/pms_engine.py`,
`PMS_PN_REGISTRY`) — price these exactly, they are the ones capture is measured against:

| PN | Model | Category |
|----|-------|----------|
| 8982447940 | N75_4HK1 / N75_4JZ1 | Brake pad (front) |
| 8982169220 | N75_4JZ1 | Brake pad (front) |
| 8982169210 | N35_RZ4E / N35_4JZ1 | Brake pad (front, reference only — N35 not phase-one) |

**Brake rotor and caliper PNs are NOT in the 55-PN pilot registry** (rotor is priced in the model
only as a wear-factor assumption, `brake_rotor: 0.25` in `pms_capture_assumptions.yaml` — there is
no PN list yet). Before pricing rotors/calipers, pull the genuine PN list from
`01_data/derived/parts_catalog_dimension.csv` filtered to `fig_key` = the brake-rotor/caliper EPC
group for NPR75 (4HK1) and NPR88 (4JZ1) — ask Claude or Cursor to extract that list first if it
isn't already in hand; do not guess PNs.

**BVP (Best Value Parts) equivalents** for the same PNs — pull from
`01_data/derived/genuine_bvp_crossref.csv` (`genuine_pn` = the PNs above → `bvp_pn`). Price these
too — the comparison that actually matters commercially is genuine vs. IAM *and* BVP vs. IAM, not
just genuine vs. IAM.

## 3. Competitors to price

| Source | Why | What's already known |
|--------|-----|----------------------|
| **KS International** | Named in trip report as the ~60-75%-below benchmark | Wholesale-side comparison — need their trade/wholesale price list, not retail |
| **JDS (dealer)** | 9% avg retail discount vs RRP observed at their counter | This is ITUK's own dealer discounting off RRP, not a competitor price — collect separately from IAM pricing, don't conflate the two numbers |
| **Any general IAM brake supplier active in the ITUK trading area** (e.g. via TVS Chorley / Warrington VC / CV Components — the dealers visited) | Broadens beyond a single anecdote | None yet — ask the dealers directly which IAM brands they see undercutting on brake |

If KS International doesn't publish a wholesale list, the fallback is a same-fitment cross-reference
lookup (TecDoc / part-finder sites) using the genuine PN → find 2-3 IAM-brand equivalents by
fitment (NPR75/NPR88, 4HK1/4JZ1) and price those instead. Record which method was used per row.

## 4. Data format to return

One row per (PN, competitor, source) — CSV or Excel, whichever is easier to produce:

| Column | Example | Notes |
|--------|---------|-------|
| `genuine_pn` | 8982447940 | ISZE PN this row is benchmarked against |
| `pn_type` | genuine / bvp | which side of the crossref this competitor price compares to |
| `competitor` | KS International | supplier name |
| `competitor_pn` | (their part number, if known) | blank if cross-referenced by fitment only |
| `price_level` | wholesale / trade / retail | **critical** — do not mix levels in one comparison |
| `price_value` | 45.30 | |
| `currency` | GBP | |
| `price_date` | 2026-07-15 | when this price was observed/quoted |
| `source` | phone quote / website URL / printed catalogue | |
| `notes` | fitment confirmed by TecDoc | anything relevant |

Save the completed file to `01_data/12_raw/reference/` (or hand it to Claude/Cursor to place it
there) — do not compute the "% below ITUK wholesale" figure by hand; that comparison should be
built against the ISZE wholesale price already in PRISM (`prism/data/pms_capture_assumptions.yaml`
adjacent) so both sides use the same as-of date and currency conversion.

## 5. What this is NOT

- Not a request to fix the stale discount scraper (`04_tools/discount-scanner/` — separate,
  already-tracked roadmap item, different purpose: online retail promo monitoring, not wholesale
  IAM brake pricing).
- Not a request to build a recurring pipeline yet. One clean snapshot first; decide whether it's
  worth automating after seeing whether the 60-75% figure holds up.

## 6. What happens after collection

Once the CSV lands in `01_data/12_raw/reference/`, ask Claude to: (1) join it to the genuine/BVP
wholesale prices already in PRISM, (2) compute an actual €-per-unit and %-below figure per PN and
per competitor, (3) compare that to the existing `pms_opportunity_matrix.csv` brake gap so the
"IAM is undercutting us" story and the "here's the capture gap" story use the same numbers.
