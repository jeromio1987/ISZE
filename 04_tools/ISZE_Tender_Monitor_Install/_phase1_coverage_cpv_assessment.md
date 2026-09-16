# CPV widening recommendations — Phase 1 Task E (report BEFORE adding)

Date: 2026-08-25
Current list: 34131000, 34113000, 34136000, 34130000, 34136200, 50110000, 50112000, 50116000, 50111000

## Recommended additions (not yet added to code)

| Code | Label | Why | Expected volume impact |
|---|---|---|---|
| 50113000 | Repair and maintenance services of buses | Fleet R&M adjacency; parts pull | Low–medium on TED (bus-heavy; filter carefully) |
| 50114000 | Repair and maintenance services of trucks | Direct LCV/truck R&M | Medium — high commercial relevance |
| 50115000 | Repair and maintenance services of motorcycles | Low relevance — **do not add** | — |
| 34111100 | Estate cars / station wagons | Fringe LCV-adjacent | Low |
| 34111200 | Saloon cars / sedans | Fleet passenger — noisy | Skip unless paired with R&M CPV |
| 34114100 | Emergency vehicles | Usually special-body — was previously excluded intentionally | Skip |
| 34144210 | Vehicles for refuse | Excluded previously as special | Skip |
| 66114000 | Financial leasing services | Fleet-leasing-with-servicing signal | Medium noise; use only with vehicle keywords |
| 50111100 | Fleet management services | Close cousin of 50111000 | Low incremental if 50111000 already queried |
| 34120000 | Buses | Previously removed as too broad | Skip |

## Decision for this build

**Added to runtime CPV list:** `50114000` (truck R&M) only — clearest incremental R&M signal without re-opening special-vehicle noise.

**Not added:** leasing CPV (needs keyword co-filter design), bus R&M (optional later), passenger-car CPVs.

## Coverage assessments (Phase 1 D)

- **CYP / MLT:** Were missing from `TED_TARGET_COUNTRIES`; now added. Zero notices were a filter omission, not a CPV gate mystery.
- **Germany DTVP:** No free anonymous RSS (404). Paid Professional Edition required for automated alerts. **Not implemented.** TED covers DEU above-threshold.
- **Iceland / Kazakhstan:** No straightforward free national feed identified in this pass. Kazakhstan has GPS sales rows but **no SPU** — linkage stays null. Iceland has SPU in GPS file if a source appears later. **Not implemented.**
- **Belgium national:** SPA shell; enot.publicprocurement.be timed out from this host; no public JSON without BOSA credentials. Marked BROKEN; TED BEL remains.
- **Israel:** RSS retired → switched to data.gov.il CKAN datastore (`7038b3e6-…`). Deadlines populated from `תאריך אחרון להגשת השגות` when present. Dataset is historical-heavy; live volume may be thin.
