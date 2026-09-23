# Plan — Forecast-weighted ambition (not past-sales only)

> **2026-09-22 — the ambition question is CLOSED, permanently.** Jerome, verbatim: *"delete price
> ambition I will come when it's done for now do a simulation on 5% increase and than never ask
> again."* Everything below is a build plan kept for reference. **Do not ask him to choose an
> ambition value, a band, or a launch-family scope.** No agent re-asks it in any form. Last output:
> the +5% flat simulation of 2026-09-22. Record:
> [`00_docs/PRICE_AMBITION_CLOSED_2026-09-22.md`](../../00_docs/PRICE_AMBITION_CLOSED_2026-09-22.md).

**internal · 2026-08-12 · Jerome**  
**Language:** plain English.

---

## What you asked (capiche)

Today’s **+3% weighted** index is weighted on **past sales** (L12M).  
You want **more ambition on forecasted sales** — especially where **P700** and **D-Max 2.2L** will create **new / rising demand** (services, first failures ~50–70k km), **not** only where we already sold a lot last year.

Shell = side business → **out of scope**.

---

## Two books (do not mix silently)

| Book | Weight basis | Target | Purpose |
|------|--------------|--------|---------|
| **A — Base** | Past L12M € | **+3%** exact | Normal list story to IML/IMIT |
| **B — Ambition** | **Forecast €** (see below) | You choose (e.g. **+4% / +5%**) **or** open overshoot on launch families only | Price where demand is going |

Book B is honest: it is **not** “still +3% on past sales.”

---

## Forecast weight (simple recipe)

For each part (or family):

```
forecast_weight = past_L12M_€ × growth_factor
```

| Bucket | growth_factor (starting point — edit with you) | Why |
|--------|-----------------------------------------------|-----|
| D-Max 2.2 **oil-interval** (oil/air/fuel/blower/urea filters) | **1.15–1.33** | 15k SCR vs 20k legacy (schedules) |
| D-Max 2.2 / P700 **first-failure wave** (~50–70k: pads, some clutch, sensors…) | **1.10–1.40** by year of ramp | New parc entering wear band |
| P700 **new-only** (ISIM/DCT, ADAS, LED, new cab — no history) | **seed €** from launch plan (not L12M) | Past sales = 0 |
| P700 **carryover** (same engine/SCR as old N) | **~1.0–1.1** | Config: no SCR windfall on P700 |
| Everything else | **1.0** | No fake ambition |
| Shell / lube | **0** (exclude) | Side business |

Then Book B solves:

`sum(forecast_weight × Δ) / sum(forecast_weight) = ambition_target`

So rising-demand lines **pull more of the increase** — because the weight is forward-looking.

---

## P700 + 2.2L parts — what mail gave us

Outlook scan (Inbox + Sent, keywords P700 / 2.2 / RZ4F / RG21):  
`01_data/01_Pricing/_raw/outlook_p700_dmax22_mail_scan_20260812.json`  
Summary: `01_data/01_Pricing/OUTLOOK_P700_DMAX22_MAIL_SCAN.md`

**Finding:** mail is mostly **P700 order / tender** traffic. **No clean parts BOM / PN price list** in those threads (no useful Excel BOM attached in the scan).

**Working list until IML/IMIT send real PNs** — from the existing launch basket (placeholder codes):

### D-Max 2.2L (wear + captive families)
Oil / fuel / air / blower / urea filters · brake pads/rotors · clutch disc · drive belt · DPD/SCR · NOx sensors · DEF pump/injector · EGR · turbo · injectors · ECU  
(see launch run `…__launch__dmax_22_base` — still **TBD-*-22** until real PNs)

### P700 (from config + public launch notes — not a PN list)
- **Carryover:** filters, injectors, turbo, EGR, AdBlue/SCR (same engines)  
- **Genuinely new:** ISIM dual-clutch 9-speed (fluid/filter, clutch packs, mechatronics) · ADAS (BSIS, DWS, TSR, TPMS) · LED lighting · new cabs · **13.5t** class with no ISZE history  

**To lock real PNs we still need from IML/IMIT:** first-stock / catalogue / supersession for P700 + RG21 filter&SCR map.

---

## Real PN lists from APL packs (2026-08-12) — Book B seed map

**Built (internal, no inventing).** Builder: `01_data/01_Pricing/_build_apl_pn_lists.py`  
Hunt notes: `01_data/01_Pricing/OUTLOOK_APL_MAIL_SCAN.md`

### Outputs (canonical)

| File | Role |
|------|------|
| `01_data/00_derived/apl_pn_list_long_20260812.csv` | All harvested rows (~188.7k) |
| `01_data/00_derived/apl_pn_list_unique_20260812.csv` | Deduped PNs (**15,917** unique) |
| `01_data/00_derived/apl_pn_list_book_b_seeds_20260812.csv` | Same unique set for Book B join (Shell/lube out — none found in these APL packs as oil SKUs) |
| `01_data/00_derived/apl_pn_list_ITUK_20260812.csv` | ITUK APL long |
| `01_data/00_derived/apl_pn_list_RG21_2.2L_20260812.csv` | RG21 (= D-Max 2.2L) RL long |
| `01_data/00_derived/apl_pn_list_P700_20260812.csv` | P700 long |
| `01_data/00_derived/apl_pn_list_20260812.meta.json` | Counts + caveats |

Copies also under `01_data/01_Pricing/`.

### Pack breakdown (unique PN touching pack)

| Pack | Long rows | Unique PN | What it is |
|------|-----------|-----------|------------|
| **ITUK_APL** | 172,200 | 10,249 | Suzuki `20260714_1037` ×10 `.xls` + VK05 UK D-Gr ×39 `.xls` (ITUK recommended APL) |
| **RG21_2.2L** | 8,876 | 3,994 | Norway + Greece RL sheets (`P/NO.` / `P/NAME`) |
| **P700** | 7,588 | 4,804 | Accessories+EUR list, VL27 Belgium all/recommended, body FOB sample, ITUK P700 initial PRD |

Overlap (unique): ITUK∩RG21 ≈ 355 · P700∩ITUK ≈ 2,741 · P700∩RG21 ≈ 301 · all three ≈ 267.  
P700-only ≈ 2,029 · RG21-only ≈ 3,605 · ITUK-only ≈ 7,420.

### Which PNs feed which Book B buckets

| Book B bucket | Feed from these lists | How to use |
|---------------|----------------------|------------|
| **RG21 / 2.2L interval-linked** (filters, SCR/urea, service) | `source_pack=RG21_2.2L` (+ filter/scr_dpd `family_hint` on those PNs) | Prefer growth_factor on oil-interval / service lines; join to L12M € |
| **RG21 / 2.2L first-failure** | Same RG21 list where `family_hint` ∈ brake / clutch / sensor / turbo / injector | Wear-band growth_factor |
| **P700 new-only (seed €)** | P700 accessories (FCA/EXW EUR) + body P700 column + PRD lines with **no** L12M history | Seed € from list/PRD qty — not past sales |
| **P700 carryover / launch basket** | VL27 Belgium All Parts + Recommended (IBX new project) ∩ ITUK APL where shared | growth ~1.0–1.1 until config says otherwise |
| **ITUK background APL** | ITUK_APL | Context / coverage — not automatic ambition unless also in RG21 or P700 seed |
| **Shell / lube** | Out | No `5500*` oil SKUs in these packs; heuristic flags only |

### Inventory — used vs skipped

**Used**
- ITUK Suzuki APL unpack: `01_data/90_INBOX/suzuki_pms_mail_pull/zip_20260714_1037/20260714_1037/`
- ITUK VK05 UK D-Gr zip (parsed once)
- RG21 Norway + Greece RL xlsx
- UTI P700: accessories (+ ITUK feedback), VL27 Belgium, body parts compare, ITUK P700 initial PRD

**Skipped (on purpose)**
- `…_UTI_P700_20260714_1037.zip` — **MD5 = ITUK Suzuki APL** (not a UTI-only list)
- UTI copies of VK05 B/D-Gr and VL27 — **byte-identical** to ITUK copies
- N-series / F-series xlsx — **FIGKEY + Name only, no PN column**
- PDFs, VIN list, awards survey, lubricants PDF, production volume / UK model sheets (not PN catalogues)

### Caveats (shared care)

- Suzuki/RG21 **BP / B/P** kept as `price_raw` with flag `BP_raw_currency_unclear` — do not treat as EUR list.
- Accessory prices labelled `accessory_list_fca_exw_eur` (as printed).
- Body file = small OLD vs P700 FOB sample, not a full body catalogue.
- **No dedicated UTI-only APL** found beyond the P700 materials above.
- Family hints are description heuristics — not official PMS categories.

**Ready for forecast-weight join:** yes on PN universe (unique + pack tags). Still missing for a clean Book B run: ambition % choice, growth_factor sign-off, and L12M € join + seed € rules for P700-new-only.

---

## UTI P700 volume + recommended list (2026-08-12)

**Units (Jerome — no mix breakdown):** **800** CY2025 → **1000** CY2026 (**×1.25**).  
Use **1.25** only as a **network seed / demand-index scale** on UTI P700 Book B seed € when ambition % is set. **Do not invent per-PN qty.**

**Recommended list (prefer recommended sheets over catalogue dump):**

| File | Role |
|------|------|
| `01_data/01_Pricing/UTI_P700_Recommended_Parts_List_20260812.xlsx` | Advise · Recommended · Volume_context · Family_priority · Catalogue_all_VL27 |
| `01_data/01_Pricing/UTI_P700_Recommended_Parts_List_20260812.csv` | Recommended sheet only |
| `01_data/00_derived/uti_p700_recommended_parts_list_20260812.csv` | Same CSV (derived) |
| `01_data/01_Pricing/UTI_P700_Recommended_Parts_List_20260812_ADVISE.md` | Continue vs still-need brief |
| Builder | `01_data/01_Pricing/_build_uti_p700_recommended_list.py` |

**How recommended was chosen:** VL27 Belgium **Recommended Class** + ITUK P700 **initial PRD** + accessories (FCA/EXW EUR) + **body P700** sample. VL27 **All Parts** kept as catalogue reference only. Shell/lube out. **UTI ≠ UMI.** RG21 2.2L not mixed in.

**Can continue without mix detail:** PN universe · qualitative P0/P1/P2 priority · Book B ×1.25 seed hook · ITUK overlap crosswalk.  
**Still need:** model mix % · gearbox (ISIM DCT vs manual) · market of 800/1000 · price basis (FCA vs PR00) · Book B ambition %.

---

## Continued without mix — provisional defaults (2026-08-12)

**Status:** Built scaffold + diagnostic sensitivity **without** waiting for model mix / gearbox / market / ambition %.  
**Book A** stays **+3% on past L12M** — not overwritten; **no new official alloc run id**.  
**Book B +4% / +5%** = **PROVISIONAL / diagnostic scenarios only** (not locked).

### Provisional growth_factor defaults (edit when you answer)

| Rule | Factor |
|------|--------|
| RG21 interval families (`filter`, `scr_dpd`) | **1.24** (mid 1.15–1.33) |
| RG21 first-failure (`brake` / `clutch` / `sensor` / `turbo` / `injector` / `belt`) | **1.25** (mid 1.10–1.40) |
| P700 carryover (history or ITUK overlap) | **1.05** (mid ~1.0–1.1) |
| P700 new-only / no L12M | `seed_eur_placeholder=NEED_SEED` (no invented €) |
| `on_uti_p700_recommended=1` | multiply by **1.25** (800→1000 network scale) |
| Else | **1.0** |
| Shell / lube | out (already excluded from seeds) |

L12M €: prefer `sales_fact` rolling L12M net sales; fill gaps from `pricing_sim_pr00_l12m` (`qty×sp_eur_2025`).

### Exact paths (canonical under `00_derived/`; copies in `01_Pricing/`)

| File | Role |
|------|------|
| `01_data/00_derived/forecast_weight_scaffold_20260812.csv` | Join: APL unique seeds + UTI recommended flag + L12M + growth_factor + FW |
| `01_data/00_derived/forecast_weight_scaffold_20260812.meta.json` | Counts + one-liners + caveats |
| `01_data/00_derived/forecast_weight_sensitivity_provisional_20260812.csv` | PROVISIONAL +4/+5 vs Book A +3 (diagnostic) |
| `01_data/00_derived/apl_overlap_ituk_p700_rg21_20260812.csv` | ITUK / P700 / RG21 overlap slice counts |
| `01_data/00_derived/apl_p700_only_20260812.csv` | P700-only PNs (scaffold cols) |
| `01_data/00_derived/apl_rg21_only_20260812.csv` | RG21-only PNs |
| Builder | `01_data/01_Pricing/_build_forecast_weight_scaffold.py` |

### Snapshot counts (this build)

- Scaffold rows: **15,917**  
- With L12M €: **6,326** (5,604 sales_fact + 722 sim fill)  
- NEED_SEED (P700-ish, no L12M): **2,219**  
- On UTI P700 recommended: **1,885**  
- Overlap: ITUK-only 7,420 · P700-only 2,029 · RG21-only 3,605 · all three 267  

### PROVISIONAL one-liners (not official alloc)

- **+4%:** on 6,326 PNs with L12M (€12.8M), mean g≈1.138; launch-tagged weight share L12M→FW ~74.8%→77.8%.  
- **+5%:** same weight table; UTI-rec FW share ~33.6% vs L12M ~28.8%.

### Still parked / do not invent

- Per-model-tonnage qty · fake locked ambition · Shell · gearbox / market mix of 800→1000 · seed € amounts for NEED_SEED rows.

---

## Execution steps

1. **Keep Book A** = +3% on past L12M (status quo). **Done — not touched.**  
2. **Build forecast weight table** (exclude Shell): **Done (provisional defaults)** — see scaffold CSV above.  
3. **Book B run** with your chosen ambition % (you name it) — **waiting**.  
4. **Diff A vs B:** which PNs/families get more € under forecast weights — after step 3.  
5. **Replace TBD-* with real PNs** — RG21/P700 lists now land real PNs; keep TBD only where still uncovered.  
6. Optional later: Israel P700 claim mix for **structure** only (not price level).  
7. Fill **NEED_SEED** € for P700-new-only (from launch plan / PRD — not invented).

---

## Decision needed from you

1. Ambition target for Book B: **+4%**, **+5%**, or **open on launch families only**?  
2. OK to **keep** these provisional growth factors, or edit the table above? (UTI P700 seed scale **1.25** from 800→1000 stays locked pending mix.)  
3. Who to chase for gaps (true UTI-only APL / ISIM-DCT / ADAS PN map) — IML / IMIT / both?  
4. UTI P700: model mix %, gearbox (ISIM DCT vs manual), market of 800/1000, preferred price basis (FCA accessory vs PR00)?
