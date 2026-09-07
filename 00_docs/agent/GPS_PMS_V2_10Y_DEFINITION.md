# GPS/PMS V2 — Opt3 10y car park definition (sparring lock)

**Locked 2026-09-05 · Mode B**

## Plain English

**Opt3 = “only count vehicles that are 10 years old or younger when we size expected filters.”**

Ideal age source = **first registration** (gov).  
If we do not have that, we may use **VIN `cohort_date`** as a proxy (already on disk for a few DBs).  
If we have neither → Opt3 stays **off** for that DB.

So: Opt3 does **not** always mean “we have VIN.” It means “we have *some* age clock.” VIN is the fallback we actually have today for ~7 DBs; most of the network still has Opt3 off.

```text
in_10y_carpark ⇔ (asof_year - registration_year) ≤ 10
```

Opt3 expected demand uses **only** vehicles in the 10y car park (LCV scope for V2 start).

## Fallback order (when first registration is missing)

| Priority | Source | Use |
|----------|--------|-----|
| 1 | Government / national registration year | Preferred |
| 2 | VIN `cohort_date` (JP VIN register) | Proxy for first-on-road / shipment cohort |
| 3 | Neither | **Opt3 disabled** for that DB (`opt3_enabled=false`) |

**Not used for Opt3 age:** first ISZE invoice date, SAP billing first-seen — those measure commercial relationship, not vehicle age.

## Why this lock

- Matches how DVLA/SIMI/Matriculas think about car park.
- VIN cohort is already on disk for a few DBs and is closer to reg age than invoice.
- Mixing invoice age would silently shrink high-loyalty old fleets and inflate capture.

## Shadow behaviour

- Where VIN ages exist: compute `share_age_le_10` and scale LCV Opt1 expected → Opt3 skeleton.
- **Portugal:** Matriculas SUM year columns preferred over VIN (`share_age_le_10` ≈ 0.62 at 2025-12-31; VIN proxy was inflated ≈1.0).
- Elsewhere without gov/VIN age: Opt3 columns null, flag disabled, accuracy note points here.

## Open

Full network Opt3 needs reg-year extracts (Ireland SIMI years, IUK SMMT, etc.) wired into a cohort table — Portugal Matriculas done; VIN proxy remains for a few DBs.
