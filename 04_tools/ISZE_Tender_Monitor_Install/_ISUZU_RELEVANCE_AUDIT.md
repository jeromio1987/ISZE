# Selective audit — is the tender net actually Isuzu-relevant?

**Date:** 2026-08-25 · **Before tighten:** 679 opportunities / 773 notices  
**After Isuzu gate (same xlsx rebuild):** **172 opportunities / 193 notices**  
**Question:** Are we selecting tenders that matter for Isuzu (D-Max / N-Series / LCV + fleet R&M parts), or mostly generic vans and noise?

---

## Verdict (post-tighten)

**Net is now Isuzu-shaped.** Transport-services CPV (`600…`), SEND/passenger/towing noise titles, and generic car R&M without an LCV signal are dropped at the gate (scraper + dashboard rebuild). Scoring weights were **not** retuned.

| Signal | Before | After | Read |
|---|---:|---:|---|
| Notices | 773 | 193 | −580 dropped by gate |
| Opportunities | 679 | 172 | Commercial shortlist |
| CPV `60000000` | 54 | 0 | Excluded |
| Title `passenger` | 16 | 0 | Dropped |
| Spot-check (15 random) | mostly vans/noise | pickups, tippers, chassis cabs, truck R&M | Pass |

---

## What the filter does now

1. **TED / national:** surgical CPV list × keyword match (unchanged fetch).
2. **Hard exclusions:** buses, fire/refuse/ambulance, **transport services `600…`**, tyre repair CPV, etc.
3. **Isuzu commercial gate** (`passes_isuzu_selection_gate` in `isze_core_v3.py`):
   - Keep if core CPV (`34131` pickups, `34113` 4WD, `34130` goods, `34136` vans, `50114` truck R&M), **or**
   - Keep if LCV/goods/fleet text signal (no bare `\bvan\b` — Dutch false positive).
   - Drop noise titles (SEND, passenger, 4-seat, towing, cemetery, …).
   - Demote parent motor vehicles / car R&M (`34100000` / `50112`) unless LCV signal.
4. **Scoring** ranks what remains (Attack / Selective / Watch / Ignore).

---

## GPS figures (not a CSS bug)

1. Fleet size extracted — thin after tighten (6 GPS-sized opportunities in this rebuild).
2. Country needs a GPS SPU row — FR/PL/ES/IT/NL/CZ often null even with fleet.
3. **Addressable** = fleet × (max_spend / uio). **Capture at current** = fleet × actual SPU.

---

## Still open (not selection)

- Nordics national APIs need keys in `nordics_api_keys.env` (see `NORDICS_API_KEYS.md`).
- Belgium national feed still BROKEN; TED BEL OK.
- UK Contracts Finder volume collapsed under the gate (mostly passenger/route noise) — intentional.

---

## Decision (resolved)

Tighten **applied** 2026-08-25 as part of the god-tier loop. No further Jerome call needed for the noise cut described above.
