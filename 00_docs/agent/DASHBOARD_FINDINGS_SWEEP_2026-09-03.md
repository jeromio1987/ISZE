# Dashboard findings sweep — 2026-09-03

Read-only pass: local `02_dashboards/` (sales / ids / hub / aftermarket) vs GitHub. No rebuild, no sync, no Six-DB EUR fix.

**Question answered:** we had not done a local + GitHub findings pass; this note is that pass.

Sources: HTML SSR/tables (not 07_deploy), `01_data/00_derived/next_analyses_*.md/csv`, green `_verification_report.md` (116/0/0, generated 2026-08-26), `metrics_snapshot.json` (as_of 2026-08-25), `gh` + HTTP.

---

## 1. Local vs GitHub (what is shareable)

| Surface | Status |
|---|---|
| Documented live URL `https://jeromio1987.github.io/isze-dashboard/` | **404** (HEAD). `gh api` on `jeromio1987/isze-dashboard` also **404**. Same for `github.io/ISZE/`. Pages is **not** a working public copy. |
| Repo `jeromio1987/ISZE` | Private. Default `main` has the Aug pack of sales HTML. **No GitHub Pages** on this repo (`/pages` 404). |
| `Next_Analyses_Sales_to_Dealer_SixDB.html` | **Local only** (untracked). Not on `origin/main`, not in GitHub `02_dashboards/sales/`. |
| `Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | On GitHub `main` (blob SHA `46dec8dc…`). **Working tree is newer** (local hash `35129c1e…`) — Portugal + six-network numbers not committed. |
| Aftermarket BI Command Center | Local SHA matches last commit (`fb5fd190…`) — GitHub file = this disk copy. |
| Hub `MASTER_DASHBOARD.html` | On GitHub; still **IML v7 / Mode-B jargon** (see §4). |
| Hub index `BI_PACKS.html` | Does **not** link Six-DB next-analyses. Mode A column still labels AIM-GPS as “ITUK / UTI” only. |

**Verdict:** almost nothing “on GitHub” is a live Pages site. Colleagues with repo access see **main as of last push (2026-08-27)**. The 3 Sep Six-DB pack and the dirty AIM-GPS HTML exist **only on this machine** until commit + (optional) Pages.

---

## 2. Good findings already in the dashboards (sales)

### BVP capture (sales-to-dealer, CY2025) — Six-DB Core gate

Order is the story. Consumables are **not** what ranks the markets (same order overall vs core).

| Rank | DB | Channel | BVP capture | BVP mix | StD proxy €/veh |
|---|---|---|---|---|---|
| 1 | UTI | CV | **92.5%** | 13.7% | €204 |
| 2 | PORTUGAL | CV+LCV | **74.4%** | 6.4% | €172 |
| 3 | GREECE | CV+LCV | **48.7%** | 9.5% | €114 |
| 4 | IRELAND | CV+LCV | **26.8%** | 5.4% | €329 |
| 5 | ITUK | CV | **19.0%** | 2.7% | €241 |
| 6 | IUK | **LCV** | **8.5%** | 0.8% | €119 |

AIM-GPS pack (overall, not core-gated) matches the shape: UTI StD BVP **13.5%** / capture **92.3%**; IUK StD BVP **0.8%** / capture **8.5%**; ITUK StD BVP **2.6%** / capture **19.0%**. Portugal StD capture **74.2%** on proxy €1.44M.

**Read it:** UTI already sells BVP through the dealer network. ITUK/IUK do not — ITUK is a large genuine machine (86% genuine-only of proxy) with thin BVP. IUK is the floor.

### GPS (billing vs StD proxy, Core) — Six-DB

- **ITUK CV** UIO 22,389: StD **€241**/veh vs billing **€244**/veh (qty up, € almost flat).
- **UTI CV** UIO 10,336: StD **€204** vs billing **€316** — StD qty 78,472 vs billing 102,353 (**−23.3% qty, −35.7% €**). Dealers are not moving the same volume ISZE billed. (EUR definition owned elsewhere — do not “fix” here.)
- **IRELAND** UIO 3,056: StD **€329** vs billing **€381** (highest €/veh of the six).
- **IUK LCV** UIO **47,783**: StD **€119** vs billing **€126**. Same park as PRISM GPS CSV 2025 IUK **€128**/veh (amber). **Not trucks.**
- **PORTUGAL** UIO 8,176: StD **€172** vs billing **€204**. 2026 StD run-rate ~**€1.89M** through 2026-08 (pack finding).
- **GREECE** UIO 3,742: StD **€114** vs billing **€135**.

Network PRISM GPS 2025 (invoice, `gps_spu_by_distributor.csv`, not StD): Ireland **€389**, UTI **€322**, ITUK **€249**, Portugal **€209**, Greece **€139**, IUK **€128**. Parts base in snapshot: **€112.09M** GPS-facing parts.

### PMS (total capture, billing ÷ expected) — do not swap to genuine-only

Oil filter 2025 (Six-DB / PRISM ITUK 116.4% matches verification band):

- ITUK **116%** bill / **122%** StD (saturated on this denominator).
- UTI **91%** bill / **76%** StD.
- Ireland **191%** bill — treat as **UIO/expected mismatch until proven** (PMS table UIO 2,161 vs GPS UIO 3,056).
- IUK **37.7%** bill / **39.7%** StD — large LCV park, weak filter capture.
- Portugal oil **52%** bill; fuel filter StD BVP share in AIM-GPS: Portugal **81.9%**, Greece **89.7%**, UTI **48.7%**, ITUK **15.3%**, **IUK 0.9%**.

Brake pads: UTI billing **455** vs expected **6,460** (~7%) — wear is not following filter strength.

ITUK oil-filter 2025 total capture **116.4%** is in `_verification_report.md`; 2024 was **83.5%**.

### Leakage (Aftermarket BI Command Center — five DBs, **no Portugal**)

Hero: network leakage **€11.9M** (qty gap × reference sell-out PR00×1.785); overstock **€4M** headline / mix bar overstock **€2.76M**; balanced **€10.0M**.

DB leakage waterfall: **IUK €9.4M (79%)** · Ireland **€1.3M** · ITUK **€0.94M** · UTI **€0.24M** · Greece leakage **€0 / “—”** with overstock still **€727k**.

Top PN cards are **all IUK** (e.g. 8983767550 ~**€573k**). AIM treemap: **€10.5M Unmapped AIM** (88% of at-risk €) — family story is mostly unmapped, not “Maintenance Service €759k”.

Greece: blank leakage is **honest** (no validated sell-out for that lens), not a quiet zero.

### Dealer grain (ITUK)

Six-DB: Andy Powell **73.0%** BVP capture vs Waldron **0.4%** (≥€20k proxy). Network 19% is an average of extremes.

### Why a Core gate exists

IUK top-25 StD **qty** consumables share **50.9%**. Qty-first ranking without the gate is bolt/fastener theatre.

---

## 3. Misleading / jargon / local-only traps

| Issue | Where | Why it lies |
|---|---|---|
| **Qty-first charts** | Six-DB gap canvas (`cGap` = qty); AIM-GPS KPIs lead IUK **248,638 qty**; PMS BVP **qty** chart | Bolts inflate IUK/ITUK. Core gate + € columns are the fix already in Six-DB tables — chart still qty. |
| **“Per truck” / “€ per truck”** | AIM-GPS column header **Per truck** on IUK/Ireland/Portugal/Greece rows; `02_dashboards/bi/Dealer_Sellout.html` heading **Sell-out spend-per-unit (€ per truck)** with **IUK €243** | IUK is **LCV** (UIO 47,783). Six-DB pack labels this correctly; BI twin and AIM-GPS header do not. BI IUK **€243/truck** also **disagrees** with AIM-GPS **€122 proxy** and PRISM **€128**. Snapshot **2026-08-20**, five DBs, qty hero **970k**. |
| **Mode B on Mode A paths** | Aftermarket BI: brand **“Mode B”** + footer “Internal Mode B”; UTI replenishment badge Mode B; `MASTER_DASHBOARD.html` KPI **“PMS gap ITUK (IML v7)”** repeated | Fine for Jerome; **not** for a GitHub/Pages share. BI_PACKS still lists Aftermarket under Internal (correct) and AIM-GPS under Mode A (title still ITUK/UTI). |
| **PROJECT_HUB.html** | `lang="nl"`, tab **Overzicht** | Dutch chrome on a hub page. |
| **Leakage exec HTML** | `01_data/01_Pricing/LEAKAGE_EXEC_SUMMARY_20260819.html` | Same €11.9M story; **not** under `02_dashboards/`. Easy to miss in a “dashboards only” glob. |
| **Portugal missing** | Aftermarket BI / leakage five-DB cut | Six-DB + AIM-GPS **include** Portugal; leakage hero does not. Do not compare €11.9M to six-DB GPS as the same footprint. |
| **Tender fleet** | Ops Tender Monitor | Do not quote stated fleet as market potential (coverage rule). Skipped as a “good finding”. |
| **ITUK UIO dual** | PMS expected uses **23,068** in Six-DB PMS CSV; GPS/StD **22,389** | Known FACTS split. Quote which park. |
| **Ireland 190% oil** | Six-DB PMS | Good as a **red flag**, bad as “Ireland oversells filters 2×” until UIO is aligned. |

Empty shells skipped: GREECE leakage column (banner/zero by design); tender (c) fleet extracts; Action Ledger / ops Mode B pages (not sales analysis).

---

## 4. What to open locally (not GitHub)

- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\Next_Analyses_Sales_to_Dealer_SixDB.html` (launcher sibling `.cmd` — not run this pass).
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` (disk newer than GitHub).
- `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_Aftermarket_BI_Command_Center.html` (same as GitHub file; leakage €).
- IDS: `02_dashboards\ids\IDS_2026_dealer_compare.html` + country files — map/tiles QA is a ship-gate topic, not a sales KPI source.

IDS was opened in the inventory only: useful for dealer scores vs country average, not for GPS/PMS/BVP league tables.

---

## 5. Not done this pass

- No commit, sync, Pages publish, or Six-DB EUR methodology change.
- No pixel paint of every IDS country map.
- No claim that GitHub Pages is “up to date” — it is **down / unpublished** at the documented URL.
