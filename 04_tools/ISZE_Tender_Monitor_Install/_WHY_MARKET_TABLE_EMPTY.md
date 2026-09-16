# Why the By-market table looked empty — and what changed

**Date:** 2026-08-25  
**Audience:** Jerome  
**Tool:** `ISZE_Tender_Monitor_Install` · dashboard v4

---

## What “empty” meant

The **By market** table showed Addressable GPS / yr = **—** and Capture rate = **—** for almost every country. That looked like a dead product. It was not missing pipeline — it was collapsing **three different honest nulls** into one silent dash.

| Real gap | What it means | Example |
|---|---|---|
| **No fleet in notice** | List feed never states vehicle count → cannot compute GPS € | Belgium 20 opps, 0 with fleet |
| **No GPS map in source pack** | Country has no SPU row in `gps_spu_by_distributor.csv` | France, Poland, Italy, Spain |
| **Van-only / product-fit** | Fleet exists but segment is van/LCV (or weak/R&M) → GPS € stays null | Germany Transporter vans; Poșta Română 83 utilitare |

Null ≠ €0. We never invent fleet, SPU, or “expected revenue.”

---

## P1 — GPS map audit (real data only)

**Question:** Do FR / PL / IT / ES exist in the GPS pack but get omitted from `country_distributor_map.yaml`?

**Answer: No.** `gps_spu_by_distributor.csv` SPU countries today:

Belgium, Cyprus, Denmark, Finland, Germany, Greece, Hungary, Iceland, Ireland, Israel, Malta, Norway, Portugal, Romania, Sweden, United Kingdom.

**Newly mapped this turn: none.** Yaml already wires every country that has a real SPU. FR / PL / IT / ES stay `null` with an explicit comment — inventing a distributor code would invent €.

Kazakhstan appears in the CSV without usable UIO/SPU → stays null.

---

## P2 — What we changed in the market view

Honest columns instead of a dash wall:

- Notices · With fleet (n) · GPS-sized (n) · Addressable GPS € (only if sized > 0)
- **Why blank** chips: `no fleet` / `no GPS map` / `van-only (no GPS)` / `awaiting Nordics key` / `no GPS map in source pack`
- Capture rate only when GPS-sized > 0 (else — + tooltip with reason)
- Segment mix (pickup / truck / van counts)

Sidebar **Coverage vs revenue** keeps opp share (and network revenue when BP is loaded) but replaces “no sized GPS” with the same reason counts.

KPI strip keeps **No fleet count in notice** + **Coverage vs dark**; adds **GPS € countries (map + pickup/truck)** so it is clear € only lands where map + product-fit allow.

Product-fit, Hebrew ISR gate, coverage chip, source-health (incl. AWAITING_KEY for Nordics) unchanged.

---

## Which countries can ever show GPS € with the current pack

Only when **all three** are true: published fleet count · country in the SPU list above · product segment pickup or truck.

On this snapshot that is Germany and Romania (sized). Belgium / IE / IL / PT / GR / HU / Nordics **can** size as soon as a pickup/truck fleet count appears in a notice — the map is already there. FR / PL / IT / ES **cannot** until a real SPU row is added to the source pack.

---

## Bottom line

The market table was full of real tenders and empty of GPS € for honest reasons. We did not fake €. We made the reasons visible.
