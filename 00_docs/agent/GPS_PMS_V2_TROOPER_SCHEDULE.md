# GPS/PMS V2 — Trooper service interval (sparring lock)

**Updated:** 2026-09-05 · Mode B

## Lock (Jerome)

**Trooper uses the same service interval as D-Max RT** (`20,000` km oil visit → same `svc/yr` arithmetic as RT once mileage is applied).

| Generation | Interval km | Status |
|------------|------------:|--------|
| Trooper | **20,000** (= RT) | Locked by Jerome |
| D-Max RT | 20,000 | RT56 / RT88 PDFs |
| D-Max RG | 20,000 | RG / RG21 PDFs (SCR 15k still needs cutoffs) |

Config: `03_analytics/Isuzu/prism/data/gps_pms_v2_config.yaml` → `generation_interval_km.trooper: 20000`.

## Still missing (not interval)

- Trooper **parc counts** per DB (subtype SSOT) — Ireland SIMI can name Trooper; most DBs cannot.
- Optional: file a Trooper/UBS PDF later for documentation; **not required** for interval math anymore.
