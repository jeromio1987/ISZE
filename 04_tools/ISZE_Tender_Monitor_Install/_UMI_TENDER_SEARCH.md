# UMI government tender — search report

**Question:** Did we find the huge UMI government tender?  
**UMI =** Universal Motors Israel (sold-to **1797**, Israel LCV distributor — **≠ UTI 1799**).

**Verdict: STILL MISSING** as a scraped notice. The live commercial trail remains an **open Bart follow-up** about the **Electric Company of Israel (IEC / חברת החשמל)** tender — not a row in the tender monitor.

**Last IEC portal probe:** 2026-08-25 (focused scrape `--only iec`).

---

## Portal status (this pass)

| Portal | URL | Reachable from abroad? | Feed shape | Result |
|---|---|---|---|---|
| **Domestic supplier tenders** | `https://www.iec.co.il/content/suppliers/tenders-and-decisions/tenders/active-tenders` | **GEO_BLOCKED** — HTTP 200 “Access Denied” / חסום לגלישה מחו״ל; redirects abroad to denial page | No public RSS/API | **Cannot scrape** vehicle/leasing packs from this IP |
| **International active tenders** | `https://www.global-iec.com/activeTenders.html` | Yes | Server-rendered HTML (`.active-tenders-item`); **no RSS/API** (guessed `/rss`, `/api/tenders`, `.json` → 403) | Wired as `fetch_iec_israel` |
| mr.gov.il (existing) | autocomplete + HTML | Yes | Live IL gov tenders | Still **0** UMI / חברת החשמל buyers |

**Source health:**
- `IEC iec.co.il domestic` → **SKIPPED** (GEO_BLOCKED; not BROKEN)
- `IEC global-iec.com` → **OK** — **7** international cards parsed this run; **0** vehicle-keyword survivors after tight filter + Isuzu gate

---

## IEC international list — searched for UMI / רכב / צי / ליסינג

Live snapshot on `global-iec.com/activeTenders.html` (7 tenders). Titles are power / grid equipment only — **none** match vehicle, fleet, leasing, רכב, צי, משאית, טנדר:

| Tender # | Title (short) | Deadline | Vehicle hit? |
|---|---|---|---|
| HRSG Cleaning | Deep cleaning of HRSGs (RFI) | 2026-10-15 | No |
| 104075600 | Sale GE 9E gas turbine rotor | 2026-09-23 | No |
| 103926930 | VRLA power batteries framework | 2026-09-15 | No |
| 104068110 | Modular capacitors bank | 2026-10-05 | No |
| Rutenberg34 | High-voltage motor RFI | 2026-09-17 | No |
| 103999910 | BOPP spare parts (steam turbine) | 2026-08-31 | No |
| 104060600 | Lattice transmission towers | 2026-09-07 | No |

**No FOUND row** — no title / deadline / value / link for a UMI-shaped Electric Company vehicle tender. Do **not** invent one.

Press context (outside feed, unchanged): Calcalist IEC **employee leasing** (~1,221 cars by 2026) circulates to **domestic** IEC suppliers — passenger/leasing, not an Isuzu pickup GPS wallet row, and **not** on the international HTML list we can scrape.

---

## What we searched (prior + this pass)

| Source | Path / object | UMI / “Universal Motors” | Electric Company / חברת החשמל / vehicle |
|---|---|---|---|
| Live dashboard JSON | `isze_dashboard_v4_data.json` | **0** word-boundary hits | **0** (false “elec” was PL “napędem”) |
| Focused IEC scrape | `isuzu_tenders_v3_iec.xlsx` · sheet IEC Israel | — | **0** gated survivors |
| `tender_data.json` / xlsx Israel | mr.gov.il pipeline | **0** | **0** |
| Isuzu gate | meta drops | No UMI notice among drops | IEC vehicle survivors = 0 (nothing to gate-drop) |

---

## Israel notices that *are* in the feed (none are UMI / IEC)

5 opportunity families · source `🇮🇱 Israel` (mr.gov.il) · **all fleet_size = 0** → GPS € null even though Israel maps to UTI SPU.

| Decision | Buyer (short) | Title (short) | Link |
|---|---|---|---|
| Watch | משטרת ישראל / related | תחזוקה למשאית דואלית (+ family notices) | https://mr.gov.il/ilgstorefront/he/p/4000618987 |
| Ignore | מינהל הרכב הממשלתי | תיחור לדיגום משאית 42 טון | https://mr.gov.il/ilgstorefront/he/p/4000560558 |
| Ignore | מינהל הרכב הממשלתי | תיחור 16 לרכש רכבים מסחריים | https://mr.gov.il/ilgstorefront/he/p/4000573785 |
| Ignore | מינהל הרכב הממשלתי | תיחור 4 לרכש ואספקת רכבים מסחריים | https://mr.gov.il/ilgstorefront/he/p/4000564620 |
| Ignore | מינהל הרכב הממשלתי | תיחור מספר 21 לאספקת רכבים מסחריים | https://mr.gov.il/ilgstorefront/he/p/4000600026 |

---

## Known ISZE / UMI trail (not invented; not in the scraper)

**Path:** `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\UMI_Operating_Dashboard_2026\NUMBERS_LEDGER.json`

> R&M / fleet tenders: **UMI to review the Electric Company of Israel tender** and tell ISZE if special-pricing support is needed. … Source: **Outlook · Bart UMI notes 12 Aug 2026** · status **open** · owner UMI (Shelly / Nadav) · ISZE.

That is a **commercial open item with the distributor**, not a structured tender row with title / value / fleet / TED link.

---

## Most likely reason it is STILL MISSING

| Hypothesis | Evidence |
|---|---|
| **Lives on GEO_BLOCKED domestic IEC portal** (primary) | Domestic active-tenders Access Denied from abroad; international list has 0 vehicle/leasing notices |
| Never published on mr.gov.il | Prior search: 0 hits in live JSON / xlsx Israel |
| Filtered by Isuzu gate | **N/A** — no UMI/IEC vehicle notice entered the feed |
| Product-fit dropped a UMI notice | **No** — nothing UMI-shaped ingested |

---

## Engine change this pass

- Added `fetch_iec_israel` in `tender_scraper_v3.py` (domestic probe + global-iec HTML).
- Focused: `python tender_scraper_v3.py --only iec` → `isuzu_tenders_v3_iec.xlsx`.
- **Merge:** **0** vehicle survivors → nothing appended to main feed (honest no-op).
- Product-fit / market UX chips / Nordics **AWAITING_KEY** / IDS dealer linkage: **preserved** (not retuned).

---

## If FOUND were required — what would we show

**Not applicable.** No feed row with title, country value, fleet, or link to attribute to “UMI huge government tender.”

Closest actionable pointer: chase the **Bart 12 Aug Electric Company of Israel** open item with UMI (Shelly / Nadav), and/or pull the live IEC **domestic** supplier tender pack from someone **inside Israel** — the abroad monitor cannot invent it past the geo wall.
