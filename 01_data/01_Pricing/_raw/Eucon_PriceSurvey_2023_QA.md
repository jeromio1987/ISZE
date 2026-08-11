# Eucon 2023 Price Survey — hard QA (Mode B)

**Date:** 2026-08-10  
**Verdict (first):** **Crossrefs (OEM Isuzu PN ↔ peer OE PN) are safe to use for mapping. Survey prices are NOT usable as street / retail as-is** — Isuzu “ISZE price” tracks **IE40/PR00 list EUR** (2023 vintage ≈ 2026 PR00), and OEM competitor prices are **GBP list**. IAM has explicit list vs workshop columns. **No ×1.785 (or any street restatement) appears in the workbooks.** Do not feed survey Isuzu or OEM GBP into `peer_street_eur` or action-map street deltas without restating.

Repro scratch: `_qa_eucon_2023_run.py` → `_qa_eucon_2023_scratch.json` (same folder).

---

## Filed paths (canonical)

| File | Bytes |
|------|------:|
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\Eucon_PriceSurvey_UK_2023_OEM_rawdata_20240109.xlsx` | 57,698 |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\Eucon_PriceSurvey_ITUK_2023_OEM_rawdata.xlsx` | 22,215 |
| `C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\_raw\Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx` | 25,402 |

---

## 1) Schema

### UK OEM (`Isuzu UK` + helper `Sheet1`)
- **Market:** Country=`UK` on every data row.
- **Key columns:** `CustomerPartNumber` (Isuzu PN, col F; duplicated col N) · `CompetitorBrand` · `CompetitorPartNumber` (peer OE) · `CompetitorVehicle` · `ISZE price` · `CompetitorPrice` · `Currency` · `Comparability`.
- **Rows:** 212 data (+ header). Brands: DAF 138 · Ford 37 · Toyota 37.
- **Helper Sheet1:** `part`, `ISZE price`, `Price in EUR` (competitor), `difference` formula `=D/C`, `Price in pond` (competitor GBP). `EXCHG rate` header present — **value cell empty**.

### ITUK OEM (`Sheet1`)
- Same OEM map columns (no Country/vehicle-on-Isuzu headers). **All** `CompetitorBrand=DAF`. Currency **GBP**. 138 data rows.

### UK IAM (`LCV`, `HCV`)
- `Isuzu Part Number` · `Manufacturer Brand` · `Competitor Part Number` · **`Competitor List Price`** · **`Workshop Purchase Price`** · Comment / Comparability Quality.
- LCV 66 + HCV 170 = **236** data rows. Country=`UK`.

---

## 2) Pricing-point detection

| Column | What it is | Usable as street? |
|--------|------------|-------------------|
| OEM `CompetitorPrice` + `Currency=GBP` | Peer **OEM list GBP** | **No** — list, wrong FX/point for EU street |
| OEM helper `Price in EUR` | Competitor GBP×~**1.163** (implied median EUR/GBP from D÷F) | Still **list**, not street |
| OEM / helper `ISZE price` | Tracks **PR00/IE40 list EUR** (see §4) | **No** for street; OK only as vintage list check |
| Main sheet `ISZE price` | Mostly blank; 13 rows are broken `VLOOKUP`/`#REF!` into Sheet1 | **Do not trust** main-sheet ISZE col — use Sheet1 helper |
| IAM `Competitor List Price` | IAM **list** | No (list) |
| IAM `Workshop Purchase Price` | IAM **trade/workshop** (median workshop÷list ≈ **0.65**) | Closer to trade; still **not** ISZE genuine street (PR00×1.785) |
| ×1.785 / PR00×1.40×1.275 | **Absent** from all three files | Must apply outside if needed |

**Exact in-sheet formula found:** `Sheet1!E2 = D2/C2` → competitor EUR ÷ ISZE price (ratio), **not** an FX definition. EXCHG rate column unused.

**Hold:** any headline “ISZE vs competitor %” built from these sheets without restating both sides to the same point (genuine street vs IAM workshop, etc.).

---

## 3) Integrity

| Check | UK OEM | ITUK OEM | UK IAM |
|-------|--------|----------|--------|
| Data rows | 212 | 138 | 236 |
| Isuzu PN null | 0 | 0 | 0 |
| Peer/IAM PN null | 0 | 0 | 105 (all “not available…” comments) |
| Isuzu PN 10-digit numeric | **all** | **all** | (normalize zfill-10 OK) |
| Price nulls | ISZE main 211/212 blank; Comp GBP 21 null | ISZE 138/138 blank; Comp GBP 18 null | list 110 · workshop 105 null |
| Comparability | 179 COMPARABLE / 22 NOT / 11 N/A | 109 / 19 / 10 | n/a (comment-driven) |
| Dup Isuzu×peer×brand | 13 keys, +46 extra rows (kit/vehicle repeats; same peer OE) | similar kit repeats | 33 dup keys |

**UK vs ITUK:** **92** shared Isuzu PNs. On shared Isuzu×DAF COMPARABLE keys: **68 agree** on peer OE set, **0 conflicts**. Safe to treat ITUK as DAF-enrichment of the same OE map.

---

## 4) Sanity vs workspace (list, not street)

Join: survey helper `ISZE price` ↔ `pricing_pr00_ie40.sp_eur` / `pricing_list_pn.sp_eur` / `eucon_price_gap.ISZE_IE40_Price_EUR` (2026 lists).

Among **111** UK unique PNs with both survey ISZE + current PR00 (>0):

| Class (±15%) | Count |
|--------------|------:|
| Near **PR00 list EUR** | **104** |
| Near street ×1.785 | **0** |
| Near trade ×1.40 | **0** |
| Far | 7 |

Ratio survey÷PR00: p10≈**0.92** · p90≈**1.00** (2023 survey slightly below / ≈ 2026 list on most).

Spot examples (survey ISZE vs PR00; street Δ would be ~−43% if misread as street):

| PN | Survey ISZE | PR00 2026 | vs list | Looks like |
|----|------------:|----------:|--------:|------------|
| 8974995480 | 21.47 | 21.18 | +1.4% | list |
| 8975546610 | 83.35 | 82.25 | +1.3% | list |
| 8983767550 | (in scratch) | 79.26 | ~list | list |
| 8982705240 | 4.99 | 6.80 | −27% | far (revision/mix) |
| 8981919560 | 142.12 | 162.02 | −12% | still within 15% list band |

IAM spot: workshop averages sit nearer gap IAM online averages than PR00×1.785 — consistent with **trade/IAM**, not genuine street.

---

## 5) Crossref usability → `oem_peer_basket`

**Yes — OEM files can fill `peer_oe_pn` where COMPARABLE and 1:1 Isuzu×Brand.**

| Metric | Count |
|--------|------:|
| Survey clear 1:1 Isuzu×Brand (Ford/Toyota/DAF, COMPARABLE) | **138** |
| Multi peer OE same brand (ambiguous) | **0** |
| Basket rows filled pass 1 (market-aligned only) | **21** |
| Basket expand + fill pass 2 (2026-08-10) | rows **540**; **`peer_oe_pn` = 39** (`needs_scrape`); +9 Isuzu PNs |
| Status after pass 2 | OE mapped; **`peer_street_eur` still blank** (scrape blocked) |
| Explicitly **not** filled | IUK **Ford Transit** ← survey Ford is **Ranger/LCV** context |

**Fill rule used:** LCV×Toyota, LCV×Ford, IUK|GERMANY×DAF only; COMPARABLE; unique peer OE; confidence note in `notes`; source tag `eucon_pricesurvey_2023_oem`. No invented PNs. No street EUR from OEM GBP list.

**Street pass 2:** Autodoc Cloudflare; KS empty on peer OEs → see `Eucon_PriceSurvey_2023_street_scrape_note.md`. Interim IAM workshop proxy only in `01_data/00_derived/oem_peer_street_fill_20260810.csv` (`source=eucon_iam_workshop`); Isuzu compare = PR00×1.785.

Basket file: `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\oem_peer_basket.csv`
Script: `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\isze_pricing\fill_oem_peer_basket_from_eucon.py`

---

## Safe vs hold

| Use | Safe? |
|-----|-------|
| OEM **Isuzu PN ↔ peer OE PN** (COMPARABLE) for basket / TecDoc / scrape keys | **SAFE** (with market/model alignment) |
| IAM Isuzu ↔ IAM competitor PN (where PN filled) | **SAFE** as IAM xref (not `peer_oe_pn`) |
| Survey Isuzu price as **vintage list EUR check** vs PR00 | **SAFE with caveat** (2023 vs 2026; some far PNs) |
| Survey prices / OEM GBP / IAM list as **street** or action-map % | **HOLD** |
| OEM GBP→EUR via implied 1.163 as “official FX” | **HOLD** (header empty; inferred only) |
| Main-sheet `ISZE price` VLOOKUPs | **HOLD** (broken `#REF!`) |
| Filling `peer_street_eur` from these files | **HOLD** until local street scrape on mapped OE PNs |
| Dashboards / ship | **Not done** (per instruction) |

---

## Next (when Jerome asks)

1. Unblock peer OE retail scrape (or TecDoc/manual) on the **39** `needs_scrape` rows → then `oem_benchmark` (≥3 priced peers/cat).  
2. Remaining clear survey pairs outside WANT / market-align still held.  
3. Never promote survey list GBP/EUR into street KPIs without ×1.785 (genuine) or IAM workshop lens labelled as such.
