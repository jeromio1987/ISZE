# GPS & PMS V2 — Mode B concept (LCV-first sparring lock)

**Status spine (fixed / not fixed / Monday):** [`GPS_PMS_V2_SPEC.md`](GPS_PMS_V2_SPEC.md)

**Status:** LCV-first locked · Opt1 live shadow · Opt2/Opt3 skeleton · **Not** Mode A cutover  
**Updated:** 2026-09-05  
**Builder:** `03_analytics/Isuzu/prism/scripts/build_gps_pms_v2_shadow.py`  
**UI shell:** Aftermarket BI Command Center only (no new HTML family)

## Verdict

**Start LCV.** EU Mileage is an LCV warranty sample; RG/RT service PDFs are on disk; CV still lacks network km. One demand engine, **three optional denominators** — not three dashboards.

```text
Opt1  Flat LCV          = LCV bucket + mileage-aware svc/yr     [default · live]
Opt2  Generation split  = Trooper | D-Max RT | D-Max RG         [optional · skeleton]
Opt3  10y car park      = age ≤ 10y in expected only            [optional · skeleton]
```

V1 + IML Model B stay the published lanes until explicit rebuild/ship OK.

```text
expected = Σ (
  registered UIO (option-scoped)
  × annual_km ÷ service_interval_km
  × parts_per_event × addressable
  × fitment_weight × cohort_intensity
)
```

## Dual-lane rule (hard)

| Lane | Use | Do not |
|------|-----|--------|
| **V1** | Network KPI / verify | Overwrite with V2 |
| **IML Model B** ITUK | External IML | Merge with PRISM / V2 |
| **V2 shadow** | Mode B + Aftermarket BI V2 tab | Quote as “the” capture |

## EQ-HIT (locked — full catalogue, no compromise)

EQ-HIT answers **which PN fits which chassis / engine**. It is **not** required to turn on Opt1 (mileage) or Opt3 (age), but it **is** the long-run fitment SSOT for Opt2 PN-level demand.

| Need | Without EQ-HIT | With EQ-HIT |
|------|----------------|-------------|
| Parc size / age | UIO + gov regs / VIN | None |
| km → svc/yr | EU Mileage | None |
| Interval by generation | Schedule PDFs | Confirms / fills gaps |
| **All parts** PN → Trooper / RT / RG (and engines) | BVP partial only | **Full extract — accepted even if multi-day** |

**Jerome 2026-09-05:** do **not** truncate to “top 20 PMS only” or skip engine-type coverage. When an EQ-HIT session is available, pull **complete** applicability (PMS + wear + related service parts / engines as EQ-HIT exposes them). Days of work OK; half-maps not OK. Offline BVP still carries Opt1 until that extract exists.

## UIO accuracy ranking (hover)

| Rank | Meaning |
|------|---------|
| **A** | Gov/authority regs + subtype counts (Trooper / RT / RG) |
| **B** | Gov total LCV, no subtype |
| **C** | IML/IMIT shipment×survival (UIO v19 Sheet 1) |
| **D** | Proxy / prior-year / missing |

Never invent subtypes. Opt2 stays **disabled** until rank A (or explicit subtype file) exists for that DB.

## Ultimate dashboard

Plug into [`ISZE_Aftermarket_BI_Command_Center.html`](../../02_dashboards/sales/ISZE_Aftermarket_BI_Command_Center.html) — tab **GPS/PMS V2 LCV**. Slide path = print/export from that panel. No 101st HTML.

## Sparring locks (companion notes)

| Topic | Note |
|-------|------|
| Subtype SSOT per DB | [`GPS_PMS_V2_LCV_SUBTYPE_SSOT.md`](GPS_PMS_V2_LCV_SUBTYPE_SSOT.md) |
| Trooper schedule | [`GPS_PMS_V2_TROOPER_SCHEDULE.md`](GPS_PMS_V2_TROOPER_SCHEDULE.md) |
| 10y age definition | [`GPS_PMS_V2_10Y_DEFINITION.md`](GPS_PMS_V2_10Y_DEFINITION.md) |

## Artefacts

| File | Role |
|------|------|
| `eu_mileage_by_db_lcv.csv` | LCV km/yr |
| `lcv_uio_accuracy_by_db.csv` | Rank A–D + hover text |
| `pms_v2_lcv_opt_skeleton.csv` | Opt1/2/3 expected + enable flags |
| `pms_capture_by_db_year_v2_mileage.csv` | Opt1 capture vs V1 |
| `gps_wallet_v2_by_distributor.csv` | Wallet index |
| `gps_pms_v2_findings.md` | Read-out |

## Deferred

CV/N75 V2 league · full EQ-HIT scrape · overwrite V1 · new Mode A HTML outside Aftermarket BI.
