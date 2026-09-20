# Pricing programme — internal status brief (2026-08-12)

**Audience:** Jerome only (internal). No shared ship.  
**Alloc baseline:** `20260810T171626Z__alloc__t3pct` — **+3.0000% exact** (not re-run yet this pass).  
**Language:** do not say “street fills” — say **OEM peer retail** / **reference sell-out** (PR00×1.785).

---

## Done this pass

| Track | State |
|-------|--------|
| Spec C4 PR00 pull | **220** usable → IE40 + enquiry; **31** remain flagged |
| UMI Shell/lube | **Parked** (`UMI_SHELL_LUBE_PARKED`, ~€525k) — business off |
| Non-Shell remaining 24 | ZPR1 check CSV written — **14** have ZPR1 SP (~€13k); **10** no ZPR1 (~€54k, mostly cab/steering/tx) |
| Chassis → interval map | **Simple mode on** (assumed SCR share; does **not** move € until basis allowed). Extended = fill mix CSV. See `CHASSIS_INTERVAL_UNBLOCK.md` |
| OEM peer retail | Still **15/22**; **7** blanks — I cannot get genuine DAF online. Who needs them: **IUK** brakes/clutch/fuel + 1 Ford shoe. See `OEM_PEER_RETAIL_GAPS.md` |

---

## What still moves readiness (~62%)

1. **OEM peer retail** — one real **DAF/Paccar dealer quote** (pad / disc / clutch) unlocks near-gate brake/clutch cats. Ford shoe 1713904→2138025 needs your EPC confirm.  
2. **Fresh alloc** (when you say) — re-run +3% with current IE40 (incl. 220 fills) so NO_EVIDENCE / list coverage reflects reality.  
3. **θ_interval** — need LCV UIO by reg-year or SCR flag × market (map is ready; data isn’t).  
4. Non-Shell **10** with neither PR00 nor ZPR1 — keep flagged NO_EVIDENCE; don’t invent list.

---

## Key paths

- Gap remaining + flags: `01_data/00_derived/no_pr00_gap_cy2025_ranked.csv`  
- ZPR1 check: `01_data/00_derived/no_pr00_gap_remaining_zpr1_check_20260812.csv`  
- Chassis map: `03_analytics/isze_pricing/chassis_generation_interval_map.yaml`  
- Unblock note: `03_analytics/isze_pricing/CHASSIS_INTERVAL_UNBLOCK.md`  
- Engine: `03_analytics/isze_pricing/`  
- Dashboard: `02_dashboards/pricing/ISZE_Pricing_Engine_Readiness_Dashboard.html`
