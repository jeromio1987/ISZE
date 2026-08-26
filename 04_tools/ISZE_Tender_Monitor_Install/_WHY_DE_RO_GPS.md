# Why DE & RO dominate the GPS € total

**Question:** Why focus on Germany & Romania?  
**Snapshot:** `isze_dashboard_v4_data.json` · generated **2026-08-25T16:15:49Z** · **186** opportunities · **211** notices.

---

## One-sentence verdict

**We are not focusing on DE/RO; they are the only markets where notice fleet × pickup/truck × GPS pack currently intersects.**

---

## The €1,488 he saw

| Country | Sized opps | Fleet × segment | GPS € / yr |
|---|---:|---|---:|
| Germany | 2 | 3 truck + 2 truck | **€1,238.22** |
| Romania | 1 | 1 truck | **€250.00** |
| **Total** | **3** | | **€1,488.22** |

Detail:

| Country | Fleet | Seg | GPS € | Title (short) |
|---|---:|---|---:|---|
| DE | 3 | truck | €742.93 | 3 Stück Elektro-Transporter DoKa-Pritsche… |
| DE | 2 | truck | €495.29 | 2 LKW mit Kran und Abrollk… |
| RO | 1 | truck | €250.00 | Furnizare utilaj special… (1 buc) |

Formula: `fleet × (max_spend_eur ÷ uio_units)` from `gps_spu_by_distributor.csv` via `country_distributor_map.yaml`. DE addr SPU ≈ **€247.64**; RO = **€250.00**.

---

## Countries with a GPS SPU map (16)

Non-null in `country_distributor_map.yaml` (latest year with usable SPU):

Belgium, Cyprus, Denmark, Finland, **Germany**, Greece, Hungary, Iceland, Ireland, Israel (→ UTI), Malta, Norway, Portugal, **Romania**, Sweden, United Kingdom (→ ITUK).

**Null map (examples with live notices):** France, Poland, Italy, Spain, Netherlands, Czechia, Austria, Slovakia, … — notices stay in the pipeline; GPS € stays **null**.

---

## The three-way intersection (why only DE/RO get €)

GPS € is emitted only when **all three** are true:

1. **Fleet** extracted from the notice (count published in title/text)  
2. **GPS map** for that country (real SPU row)  
3. **Product segment** = pickup or truck (van/LCV / weak / R&M-only → GPS null by design)

On this snapshot, **exactly 3** opportunities clear all three — and they are the DE/RO rows above.

| Country | Opps | With fleet | GPS map? | Pickup/truck | Full intersect | GPS-sized | GPS € |
|---|---:|---:|:---:|---:|---:|---:|---:|
| Germany | 34 | 4 | Y | 22 | **2** | **2** | **1,238** |
| Poland | 25 | 5 | **N** | 14 | 0 | 0 | 0 |
| Belgium | 20 | **0** | Y | 7 | 0 | 0 | 0 |
| France | 13 | 1 | **N** | 8 | 0 | 0 | 0 |
| Czechia | 13 | 0 | N | 13 | 0 | 0 | 0 |
| Romania | 10 | 2 | Y | 8 | **1** | **1** | **250** |
| Italy | 9 | 1 | **N** | 6 | 0 | 0 | 0 |
| Spain | 9 | 0 | N | 5 | 0 | 0 | 0 |
| Netherlands | 6 | 0 | N | 0 | 0 | 0 | 0 |
| Israel | 5 | **0** | Y | 2 | 0 | 0 | 0 |
| Ireland | 5 | 0 | Y | 3 | 0 | 0 | 0 |
| … | … | mostly 0 fleet | mixed | … | 0 | 0 | 0 |

---

## PL / BE / FR / IT — notices exist; € blank for honest reasons

| Country | Notices | Why GPS € is blank |
|---|---:|---|
| **Poland** | 25 | Has fleet (e.g. 6 / 3 / 2) and even pickup rows — **no GPS map** (`Poland: null`). Also some weak/van. |
| **France** | 13 | 1 truck with fleet=3 — **no GPS map** (`France: null`). |
| **Italy** | 9 | fleet=4 but **no map** + weak segment. |
| **Belgium** | 20 | **Map exists** — but **0** notices with an extracted fleet count. |
| **Israel** | 5 | **Map exists** (UTI) — but **0** with fleet → GPS null. |

Pipeline still shows these as leads (buyer, title, Fit, link). Empty GPS ≠ ignored market.

---

## Van fleets that look “big” but are *not* in the €1,488

Product-fit gate blocks pure van/LCV from the pickup GPS wallet (no N-Series SPU in the pack — null, not €0):

| Country | Fleet | Seg | Hypo if wrongly applied | Status |
|---|---:|---|---:|---|
| Romania | 83 | lcv_van | ~€20,750 | **Blocked** — not in €1,488 |
| Germany | 20 | lcv_van | ~€4,953 | **Blocked** |
| Germany | 13 | lcv_van | ~€3,219 | **Blocked** |

That is why the GPS floor looks “small” and DE/RO-heavy: the large van counts never enter the sum.

---

## Bottom line for Jerome

- **186** opportunities across **25** countries in the country table.  
- **13** state a fleet; **3** of those also have map + pickup/truck → **€1,488**.  
- DE €1,238 + RO €250 is an **intersection artefact**, not a strategy preference.
