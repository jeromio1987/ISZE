# ISZE daily brief — 2026-09-20

**Something is failing. See section 1.**

Generated 2026-09-20 18:50Z by `isze_daily_check.py`. Read-only digest of reports that already exist; it computes nothing new and changes nothing.

Checklist for you:

1. Pipeline FAIL: lost_sales.billed_ties_to_parts_base — billed EUR 112,089,306.89 vs parts base EUR 117,600,501.42 (delta 5,511,194.53)
2. Risk cockpit data is 82 days old (threshold 21d): 02_dashboards/sales/risk_cockpit.data.js
3. Dashboard Data tender copy is 32 days old (threshold 14d): 02_dashboards/Data/dashboards/tender_data.json
4. Task ISZE_EQ_Hit_Session_20260919 last result 1 (not success).

## 1. Pipeline health

Report generated **2026-09-20T14:31:48Z** · 152 pass · 1 warn · 1 fail

- **FAIL** `lost_sales.billed_ties_to_parts_base` — billed EUR 112,089,306.89 vs parts base EUR 117,600,501.42 (delta 5,511,194.53)
- WARN `uio_year.historical_gaps` — Named hole(s) in the workbook's older years, left unfilled: ['DENMARK 2012', 'DENMARK 2013']

## 2. Needs your attention

Latest automation drift: **automation_drift_2026-09-19.md** (1d ago)
- [MEDIUM] (language) 510 banned label(s) in shared pages changed in the last 7 days
- [MEDIUM] (open-item) ISZE_FY2027_ActionPlan_v1.xlsx: `90_archive/root_files/` only
- [MEDIUM] (open-item) ITUK_PMS_Analysis_Apr2026_v2.xlsx: `03_analytics/Isuzu/pms-pilot/_archive/` only
- [MEDIUM] (open-item) ISUZU_UIO_Dashboard_2026_v17.html: `02_dashboards/_archive/`
- [MEDIUM] (open-item) isze-weekly-intelligence-brief: Confirm target for `latest_weekly_brief.txt`
- [MEDIUM] (open-item) isze-dashboard-freshness-check: Post-reorg paths for three XLSX + UIO HTML

Data integrity open issues: 1d ago (`01_data/00_derived/_data_integrity_open_issues.md`)

FACTS drift report: 3d ago
  - *Checked:** 2026-09-17T13:55:17Z
  - *Snapshot as-of:** 2026-09-17T13:47:43Z
  - *Result: ALIGNED** — 0 drifted, 0 missing, 13 aligned.

## 3. Freshness — is anything stale?

| Thing | Last touched | Age | Threshold |
|---|---|---|---|
| Tender feed | 6d ago | ok | 10d |
| Sales fact | 4h ago | ok | 10d |
| Metrics snapshot | 3d ago | ok | 10d |
| Exec aftersales paper | 1d ago | ok | 21d |
| Risk cockpit data | 82d ago | **stale >21d** | 21d |
| Dashboard Data tender copy | 32d ago | **stale >14d** | 14d |

## 4. Tender watch

Feed generated **2026-09-15T04:20Z** · 376 opportunities · 1 attack · 15 selective

- No opportunity in the feed names Isuzu or D-Max.

**9 deadline(s) inside 7 days:**
- 2026-09-21 (1d) · Watch · Austria · Austria – Motor vehicles for the transport of goods – Rahmenvereinbarung Lieferung LKW (Kl
- 2026-09-21 (1d) · Ignore · Germany · Germany – Panel vans – Leichte Lkw bis 3,5 t
- 2026-09-22 (2d) · Ignore · Romania · Contract de furnizare autoturisme de teren  hibrid prin Programul privind reducerea emisii
- 2026-09-23 (3d) · Watch · Norway · Liten lastebil - ca 5 tonn totalvekt
- 2026-09-23 (3d) · Ignore · Norway · Rammeavtale operasjonell leasing av biler, og administrasjon av fylkeskommunens bilpark
- 2026-09-24 (4d) · Watch · Norway · Anskaffelse av elektrisk truck
- 2026-09-25 (5d) · Ignore · United Kingdom · Procurement of backhoe loader and flatbed cargo truck
- 2026-09-25 (5d) · Ignore · United Kingdom · Procurement of specialized vehicle
- 2026-09-25 (5d) · Ignore · Germany · Germany – Light vans – Lieferung von fünf Kleintransportern 3,49t zGG, Doppelkabine mit ti


## 5. Scheduled tasks

| Task | Next run | Last run | Last result |
|---|---|---|---|
| ISZE Tender Monitor | 21/09/2026 7:30:00 | 15/09/2026 6:16:04 | 0 |
| ISZE_CursorWeekDigest_Weekly | 27/09/2026 20:00:00 | 20/09/2026 20:00:00 | 0 |
| ISZE_DelegatorWatch_20min | N/A | 18/09/2026 19:40:00 | 0 |
| ISZE_DiscountScanner_Weekly | 24/09/2026 7:00:00 | 17/09/2026 7:00:00 | 0 |
| ISZE_EQ_Hit_Session_20260919 | N/A | 19/09/2026 23:00:00 | 1 |
| ISZE_LiveStateAudit_Weekly | 21/09/2026 8:00:00 | 15/09/2026 6:16:04 | 0 |
| ISZE_PMS_IAM_Refresh | 21/09/2026 7:00:00 | 15/09/2026 6:16:04 | 0 |

_A weekly task cannot run while the machine is asleep, and this laptop has no wake timer. Missed Mondays are the usual symptom._

