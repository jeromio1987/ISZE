# UK next harvest — exact-OEM pages only — 2026-10-07

## Verdict

Wider UK shop eligible stays at **17 offers / 12 PNs** (baseline; this note does not claim growth). Getting toward the 50-row bar needs **new pages that already print the Isuzu OE on the product card** (`exact_oem`), not another pass of KS category search. First host: **KS International** (`www.ks-international.com`).

## What the evidence already proves

| Fact | Source |
|---|---|
| Wider eligible = **17** offers / **12** PNs | `market_data_gap_coverage_uk_wider_exact_20261007.metrics.json` |
| Focus walls: **54** `category_only` (Isuzu PN not on card), **22** pack-unknown | OE crosswalk + pack hunt notes |
| TMC: OE often on page, **no inventable flat £** under £150 | Delivery fill note |
| Every eligible row today is **KS** `exact_oem` + VAT excl + £10 mainland cost | Wider scan |

### UK `exact_oem` yield by host (U29b ledger, 2026-10-07)

| Host | exact_oem rows | PNs | Already delivery+tax+cost ready |
|---|---:|---:|---:|
| **www.ks-international.com** | 84 | 65 | **17** |
| (Eucon UK survey — no shop URL) | 68 | 34 | 0 |
| www.tmcgroup.co.uk | 55 | 55 | 0 |
| omegaspareparts.com | 10 | 2 | 0 |
| tranzparts.co.uk | 6 | 5 | 0 (loader retired for evidence) |

KS is the only host that currently produces eligible shop offers after delivery/tax/cost wiring. TMC already shows OE on many PDPs but dies on under-£150 carriage (checkout silent / timeout). Do not invent TMC £. Do not re-harvest Tranzparts for eligibility while its loader is retired.

### Proven walls (do not re-plough)

1. **KS `category_only` (54 focus rows)** — descriptions already say the Isuzu number is not on the card. Crosswalk hunt found **0** honest KS-SKU→Isuzu upgrades. Re-running the same search query without an OE-on-card gate only grows relevance noise.
2. **Pack-unknown (22)** — still sit on those same `category_only` cards; pack text alone would not unlock them.
3. **TMC flat carriage** — not published; basket/checkout timed out. Secondary host only if a live £ amount appears.
4. **KS body / rotor `exact_oem` without £10** — ~67 rows / 53 PNs left without cost because the live KS delivery page names filter / clutch / exhaust (and focus pads were wired earlier), not body panels. Those are a **policy wire** question, not a new harvest.

## Target hosts (priority)

| Priority | Host | Why | Gate |
|---|---|---|---|
| **1 — first** | **KS International** | Sole host with eligible rows today; £10 + VAT excl path proven for filter/clutch (and wired focus pads) | Accept row only if Isuzu PN is printed on title / SKU / OE field |
| 2 | T&M Commercials | 55 `exact_oem` already; high OE hit rate | Only if a published under-£150 £ (or free ≥£150 on that SKU) + VAT rate appear — do not invent |
| 3 | Omega | Thin (2 PNs); no delivery wire | Skip until delivery/tax stated |
| — | Tranzparts | Retired for evidence | Skip |
| — | Eucon survey | No shop URL / delivery | Not a shop harvest |

## PN shortlist

CSV worklist (40 PNs):

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UNIVERSE_UK_NEXT_HARVEST_PNS_20261007.csv`

Built from `epc_decode_worklist.csv` euros (all-market size) × target families adjacent to what already unlocked (brake pad / oil / air / fuel / blower filter / clutch / brake shoe), **excluding** the 12 already-eligible PNs. Sorted to put **`no_uk_ledger_row` first** (never scraped into UK ledger yet), then high billed euro.

| Mix on the 40 | Count |
|---|---:|
| `no_uk_ledger_row` | 40 |
| Already eligible (excluded) | 12 (baseline) |

Top billed examples (not prices — size only): brake pad `8975056801` (~€995k all-market billed), fuel filters `5876150170` / `1876100934`, brake pad `8978279610`, brake shoe `8978348260`, air `1876101132`, blower `8975488420`.

Probe script (re-runnable, read-only):

`C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_next_harvest_probe_20261007.py`

## Query method (OE-in-title / SKU preferred)

1. Search KS for the Isuzu part number: `https://www.ks-international.com/catalogsearch/result/?q=<PN>`.
2. Open each hit’s **product card / PDP**.
3. **Accept as `exact_oem` only if** the Isuzu PN appears in title, SKU, or an OE/cross-ref field on that card (same bar as the 17 eligible KS rows).
4. **Reject** relevance-only kits/filters that do not print the searched Isuzu number — keep them out of the ledger, or tag `category_only` with an explicit “not on card” note (do not upgrade later by hope).
5. Capture VAT basis from the listing (`Excl. VAT` / structured data) and delivery from the live KS delivery page when the family matches the published £10 mainland minimum (filter / clutch / exhaust; pads only if the same policy path used for the focus fill still applies — do not invent £10 on body/rotor).
6. Prefer **filter + clutch** PNs on the worklist first (policy text matches). Brake pad/shoe next only when OE-on-card is proven; carriage must still be stated, not assumed.

Do **not** bulk re-query the 15 blocked focus PNs from `blocked_focus.csv` with the same search-only method. If those PNs are tried again, the accept gate above is mandatory.

## Success criteria (per new row)

A harvested row counts toward the 50-row bar only when all of these hold:

1. `match_method = exact_oem` (Isuzu PN on the card).
2. Delivery basis stated (`delivery_included` yes/no) with **cost amount** when `no`.
3. Tax basis stated (excl/incl); rate if the evidence layer requires it.
4. Coverage rebuild marks the row eligible (same builder as the wider report).

**Not success:** more `category_only` hits, TMC rows without £, Eucon survey rows, pack invent, OE invent.

## Estimated effort

| Slice | Effort | What you get |
|---|---|---|
| **Safe pilot — 8 PNs** (top filter/clutch + 2 pads from the CSV, KS only, OE-on-card gate) | ~30–60 min human or scripted fetch + parse | Validates hit rate before a long run; expect many empty/no-OE results |
| Full 40-PN KS pass with OE gate | ~2–4 h depending on throttle / manual review | Upper bound if hit rate is like today’s KS exact_oem density — still may land well short of +33 offers |
| TMC re-hunt for published £ | Only if policy/basket shows a number | Unblocks existing 55 exact_oem without new OE harvest |

**Do not start a multi-hour scrape** until the 8-PN pilot shows OE-on-card hits. If the pilot returns only relevance cards, stop and change host or query (competitor-number search with graded OE print), do not widen the same KS search.

## Small safe pilot (obvious, optional)

Eight PNs from the worklist head, **filters/clutch first**:

1. `5876150170` fuel_filter  
2. `1876100934` fuel_filter  
3. `1876101132` air_filter  
4. `8975488420` blower_filter  
5. `8975425390` fuel_filter  
6. `8982120690` clutch_disc  
7. `8975056801` brake_pad (OE-on-card only; carriage must be stated)  
8. `8978279610` brake_pad  

Stop after these eight. Count `exact_oem` accepted vs rejected. Only then decide whether to run the remaining 32.

## Not done / not claimed

- No scrape run in this pass (pilot listed, not executed).  
- No prices invented.  
- Eligible counts **unchanged** at wider **17 / 12** and focus **4**.  
- Portugal untouched.  
- Board / INTERNAL wire not rebuilt.

## Paths

| Artefact | Path |
|---|---|
| This note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_NEXT_HARVEST_2026-10-07.md` |
| PN worklist CSV | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UNIVERSE_UK_NEXT_HARVEST_PNS_20261007.csv` |
| Wider metrics (baseline) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json` |
| Blocked focus walls | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\_uk_oe_crosswalk_probe_20261007\blocked_focus.csv` |
| Wider scan note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_WIDER_ELIGIBLE_SCAN_2026-10-07.md` |
| U26 harvest report | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\91_build\_u26_E_REPORT.md` |
