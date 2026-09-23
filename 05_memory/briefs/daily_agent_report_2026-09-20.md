# ISZE daily agent — 2026-09-20

**Ran for real.**

Started 2026-09-20 18:49Z. Allowlisted actions run unattended; everything else is proposed with evidence.

## Done by the agent

- A2 rebuilt isze_dashboard_v2.html
- A2 rebuilt isze_dashboard_v4_opportunity.html

## Proposed — needs Jerome

- A1 filter audit not refreshed: it requires the portal scraper, which is excluded from unattended runs (D5). Run manually if a fresh audit is wanted.
- Risk cockpit data is 82 days old (threshold 21d) at `02_dashboards\sales\risk_cockpit.data.js`. Refreshing it writes to a protected output root, so it needs Jerome's go-ahead.
- Dashboard Data tender copy is 32 days old (threshold 14d) at `02_dashboards\Data\dashboards\tender_data.json`. Refreshing it writes to a protected output root, so it needs Jerome's go-ahead.

## Refused by the guard

- (nothing)

---

## Detail

### Guard check — is the published feed still the last good one?

- sha256[:16] `8fcafeb4ef0ce9c7` · 5.6 days old

### A2 — rebuild local tender dashboards from the existing workbook

Workbook: `isuzu_tenders_v3.xlsx` (1.0h old)
- rebuilt `isze_dashboard_v2.html` (exit 0)
- rebuilt `isze_dashboard_v4_opportunity.html` (exit 0)

### A1 — refresh the tender filter audit

- not run: needs the external scraper (denylist D5)

### Checks the agent cannot fix alone — proposed with evidence


