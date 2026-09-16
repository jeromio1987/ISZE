# Data asks — Georg (LCV warranty), then IMIT, then IML

**Date:** 2026-08-18  
**Status:** drafts only — **not sent**.  
**Question:** set up mails to relevant parties with data still needed; start with warranty (Georg for LCV); IMIT & IML next; skip ISZE-internal (Jerome checks later).

Sources: `ISZE_OS_DATA_MAP.yaml` (18 Aug 2026), `_data_integrity_open_issues.md` (LCV-DEC), files in `01_data\06_Warranty\`, Outlook scan `outlook_scan_masumi_hadi_2026\hits.json` (warranty thread 16–17 Jun 2026).

---

## Cover (read before sending)

| Party | Still needed (one line) |
|---|---|
| **Georg / LCV warranty** | Next LCV **claim-assessment** export from **May 2026 onward** (same grain as last file). Do **not** re-ask Dec 2025. |
| **IMIT** | **No open warranty need.** Map ask is LCV **chassis / registration-year cutoffs** (SCR vs non-SCR) so 15k vs 20k can be weighted. |
| **IML** | **No open warranty need.** Map ask #1 is confirm **air-to-oil replacement ratio** (provisional 0.5). |
| **ISZE** | Skipped (list_to_pocket, P4, IAM vintage rebuild, GPS artefact wiring). |

**Do not send IMIT/IML if you only wanted warranty.** Those two drafts exist because the OS map has non-warranty asks for them — not because they own LCV claims.

### LCV-DEC vs what Georg already sent

The named GPS artefact `Warranty_LCV_2025.xlsx` (mtime 28 May 2026) still **ends AssessMonth 202511 / RO dates to 17 Nov 2025**. That is LCV-DEC on **that workbook**.

Georg already filled December 2025 (and more) on later extracts — **do not ask again**:

| File | Sent | What’s in it |
|---|---|---|
| `ExportClaimAssessment202510-202512 with EV.xlsx` | Georg, 17 Jun 2026, Re: missing warranty data | AssessMonth **202510–202512**; operation dates into **16–17 Dec 2025** |
| `ExportClaimAssessment202601-202605 with EV.xls.xlsx` | Georg, 16 Jun 2026, Re: warranty data | Filename says Jan–May 2026; **AssessMonth only 202601–202604**; operation dates to **17 Apr 2026**. No 202605. |
| `ExportClaimAssessment202401-202412.xlsx` | same 17 Jun mail | CY2024 LCV |

Wiring `Warranty_LCV_2025.xlsx` vs the Oct–Dec sister file is **ISZE-internal** — not this mail.

CV stays with **René Paul** (`rene.paul@isuzu.de`). Not in this batch.

### Ranked map items **not** in these three mails

- ITUK brake 0.4 vs 0.8 (ITUK, not this batch)
- IML/ISZJ EPC billed-on-old (map #6) — leave until after air:oil / Jerome’s ISZE pass
- N35 registry (map #8, IML **and** ISZE) — skip until Jerome checks ISZE
- Dealer sell-out / Pull / VIN / fill — not Georg / IMIT / IML warranty

Closed doors not asked: SAP gross, AIM 0–100, IDS→sales, CIS into GPS-base, quoting elasticity, inventing CY GPS%.

---

## 1. Georg — LCV warranty (send first)

**Identity check:** This is **Georg Fischer**, Aftersales Service Specialist, Aftersales Department, **ISUZU MOTORS Germany GmbH** (`georg.fischer@isuzu.de` / `Georg.Fischer@isuzu.de`). He is the person who sent the LCV `ExportClaimAssessment*` files. Not “Georgia dealer”, not Karoutas Georgios.

**Reply on existing thread:** Subject `Re: warranty data` / `Re: missing warranty data` (Jun 2026). Same To/Cc as that thread.

```
To:  Georg Fischer <georg.fischer@isuzu.de>
Cc:  Hadewijch Tibos <hadewijch.tibos@isuzu-e.com>; René Paul <rene.paul@isuzu.de>
Subject: Re: warranty data
```

```
Hello Georg,

Could I ask you for the next LCV claim-assessment export?

The last file we have is ExportClaimAssessment202601-202605 with EV.xls.xlsx (16 June).
In that file AssessMonth stops at 202604 (April 2026), with operation dates through 17 April.

Please send the same ExportClaimAssessment extract from May 2026 onwards (May to the latest month you can pull).

We already have ExportClaimAssessment202510-202512 with EV.xlsx for Oct–Dec 2025 — no need to resend 2025.

Many thanks and kind regards,

Jérôme Van der Pluym
Assistant Manager // Pricing analyst
Sales – Vehicle Parts | Isuzu Motors Europe NV
+32 475 851 089
jerome.van.der.pluym@isuzu-e.com
Bist 12, 2630 Aartselaar, Belgium
```

---

## 2. IMIT — SCR / chassis cutoffs (not warranty)

**Entity:** **Isuzu Motors International Operations (Thailand) Co., Ltd.** (IMIT). Source T / LCV factory side. Not IML, not IUK, not ITUK, not ISD, not IMG.

**No IMIT warranty file in the map.** LCV claims come from Georg (IMG aftersales), not IMIT.

**Map item:** `lcv_scr_cutoffs` (ranked #3). We already have the service PDFs (RG21 RZ4F-TC with SCR = 15k km; without SCR / older = 20k). Missing slice is **which chassis / registration years** are SCR vs not, so the LCV parc can be split.

**To:** IMIT SVC Europe group (used on ISZE service threads) + Yamai (IMIT, already on those threads). **Not** Peeraya — she is Parts Sales Group (`s_peeraya@imit.isuzu.com`).

```
To:  IMIT SVC Group 1 (Europe & Turkey & Russia) <imit_svcg1@imit.isuzu.com>; Toshiki Yamai <t_yamai@imit.isuzu.com>
Cc:  Kawin Thirakhupt <t_kawin@imit.isuzu.com>; Sales <sales@isuzu-e.com>
Subject: D-Max / LCV — chassis or registration year for SCR vs non-SCR service interval
```

```
Dear Yamai san, dear IMIT SVC team,

We have the D-Max / LCV service maintenance schedules (RG, RG21, RT56, RT88).
On RG21 RZ4F-TC the interval is 15,000 km with SCR and 20,000 km without SCR / older.

What we still miss is how to apply that to the European parc: from which chassis number and/or first-registration year is SCR standard on each generation (RG / RG21 / RT56 / RT88)?

A short table (generation × cutoff) is enough. We do not need a new warranty extract.

Many thanks and kind regards,

Jérôme Van der Pluym
Assistant Manager // Pricing analyst
Sales – Vehicle Parts | Isuzu Motors Europe NV
+32 475 851 089
jerome.van.der.pluym@isuzu-e.com
Bist 12, 2630 Aartselaar, Belgium
```

---

## 3. IML — air-to-oil ratio (not warranty)

**Entity:** **Isuzu Motors Limited** / ISZJ (Japan HQ). Not IMIT, not IMIE, not ITUK.

**No IML warranty need in the map.**

**Map item:** `iml_air_oil` (ranked #1) / Flag C. One IML number replaces the provisional air element ~every 2nd oil service (0.5).

**Contact:** **Takayoshi Suzuki**, ISZJ / IML International Parts — `Takayoshi_Suzuki@isuzu.com`. He is the IML PIC on PMS / parts threads with ISZE (not Georg Fischer). Cc Masumi + Hadi as on those threads. **Ryuusuke Tanaka** (`Ryuusuke_Tanaka@isuzu.com`) is on the lubricants thread — optional extra To if Jerome wants Product Marketing on the same ask; not required for a Suzuki-only send.

```
To:  Takayoshi Suzuki ISZJ <Takayoshi_Suzuki@isuzu.com>
Cc:  Masumi Hayakawa <masumi.hayakawa@isuzu-e.com>; Hadewijch Tibos <hadewijch.tibos@isuzu-e.com>; Sales <sales@isuzu-e.com>
Subject: PMS — air filter vs oil filter replacement ratio
```

```
Dear Suzuki san,

For the genuine service schedule, could you confirm the air-cleaner replacement ratio versus engine oil / oil filter?

We currently treat air as every second oil service. Please confirm if that is correct for N-series (and LCV if different), or send the official interval (km or months) for oil filter and air cleaner.

That one ratio is enough for now.

Many thanks and kind regards,

Jérôme Van der Pluym
Assistant Manager // Pricing analyst
Sales – Vehicle Parts | Isuzu Motors Europe NV
+32 475 851 089
jerome.van.der.pluym@isuzu-e.com
Bist 12, 2630 Aartselaar, Belgium
```

---

## Contacts — how verified

| Name | Email | Role | Verified from |
|---|---|---|---|
| Georg Fischer | `georg.fischer@isuzu.de` | Aftersales Service Specialist, IMG — **LCV WA extracts** | Signature + attachments on 16 Jun 2026 (`ExportClaimAssessment202601-202605 with EV.xls.xlsx`) and 17 Jun 2026 (`…202510-202512…` + CY2024). Thread To/Cc: Jerome → Georg + René, Cc Hadi. |
| René Paul | `rene.paul@isuzu.de` | IMG aftersales — **CV** (Cc only) | Same warranty thread; Georg wrote René would send CV. |
| Hadewijch Tibos | `hadewijch.tibos@isuzu-e.com` | ISZE Sales Manager | Same warranty thread Cc. |
| Toshiki Yamai | `t_yamai@imit.isuzu.com` | IMIT (SVC liaison on Europe service mails) | ISZE↔IMIT service threads (e.g. PN 7553149600 ISD). |
| IMIT SVC Group 1 | `imit_svcg1@imit.isuzu.com` | IMIT SVC Europe & Turkey & Russia | Display name on those threads. |
| Kawin Thirakhupt | `t_kawin@imit.isuzu.com` | IMIT Parts (usual Cc with Yamai) | Same IMIT threads. |
| Takayoshi Suzuki | `Takayoshi_Suzuki@isuzu.com` | ISZJ / IML International Parts | PMS / parts threads; IML_ITUK_PMS meeting extracts. |
| Masumi Hayakawa | `masumi.hayakawa@isuzu-e.com` | ISZE (usual IML Cc) | Suzuki / Ikeda / Koen IML threads. |

**Not used (wrong Georg / wrong dept):** Georg Fischer is **not** mixed with Georgia dealer mails. Peeraya Sawangsaensuk is IMIT **Parts Sales**, not the SCR cutoff owner. Koen is not required on Georg’s warranty thread (was not on Jun 2026 To/Cc).

---

## Confirm

**Not sent.** No Outlook Send. File is copy-paste only.

Path: `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\WARRANTY_DATA_ASKS_2026-08-18.md`
