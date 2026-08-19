# UTI PartSales — source notes

**DB:** UTI (SAP sold-to **1799**). Never blend with UMI **1797**.
**Grain:** network PN (no dealer). Each xlsx = one report month + YTD cols.

## Outlook job

Subject: `UTIPartSales was executed at 01/MM/YYYY 08:05:0x`  
Attachment always named `UTIPartSales.xlsx`.  
Sheet row 3: report month / year = **previous calendar month** vs the 1st-of-month job.

## Filed 2026-08-13 from Jerome Inbox/Sent

| File | Report | Mail received |
|------|--------|----------------|
| `UTIPartSales_2025-08.xlsx` | 2025-08 | 2025-09-01 |
| `UTIPartSales_2025-09.xlsx` | 2025-09 | 2025-10-01 |
| `UTIPartSales_2025-10.xlsx` | 2025-10 | 2025-11-01 |
| `UTIPartSales_2025-11.xlsx` | 2025-11 | 2025-12-01 |
| `UTIPartSales_2026-01.xlsx` … `2026-06.xlsx` | 2026-01 … 06 | 1st of following month (Jun = 2026-07-21 FW) |

Pre-existing: `UTIPartSales_2025-01.xlsx`, `UTIPartSales_2025-12_YTD.xlsx` (keep the larger Dec file; 2026-01-01 mail copy is smaller).

## Still missing

CY2025 **Feb–Jul** — not in Inbox, Sent, Archive, Deleted, Sales store, or Parts store (2026-08-13 broader hunt).  
CY2026 **Jul+** — Aug-1 job not in mailbox as of 2026-08-13.  
Archive customer folders (`Archive\Inbox\archive\customers\UMI%2FUTI\…`) show **0 items** locally (online stubs) — COM cannot see files that live only there.

## sap4* hunt 2026-08-13 (old job senders)

Jerome screenshot: `sap4@uti.co.il` (19 items, 1/11/2020–1/05/2022), `sap4u@uti.co.il` (1), `sap4uti@uti.co.il` (5+), subject UTIPartSales.

**Result: 0 attachments filed.** Senders are **not** in the cached classic-Outlook mailbox COM can read.

| Probe | Result |
|-------|--------|
| COM Restrict / Jet From + subject UTIPartSales, all 3 stores (260 folders) | 0 sap4 hits |
| Brute Archive (primary 429 / Sales 130 / Parts 3481) | 0 |
| Instant Search `from:sap4@uti.co.il` (TableView.GetTable) | 0 rows |
| Windows Search `FromAddress LIKE '%sap4%'` | 0. Indexed UTIPartSales = **noreply2@** 2025–2026 only |
| `Archive\…\UMI%2FUTI\UTI` | Items.Count=0 and PR_CONTENT_COUNT=0 |
| Stores | primary + Sales + Parts only — **no Online Archive store** |

Indexed `@uti.co.il` From in this OST: `noreply2@`, `eran@`, `yossiu@`, `Shahafr@` — no `sap4*`.

### Pass 6 (2026-08-13, try-harder)

Not a second Restrict. Different methods:

| Probe | Result |
|-------|--------|
| Outlook profiles | **one** profile `jer` (default). No second PST/OST profile. |
| Stores / files | primary OST `C:\Users\jerom\AppData\Local\Microsoft\Outlook\jerome.van.der.pluym@isuzu-e.com - jer.ost` (~32 GB) + Sales + Parts. **0 PST** under AppData/OneDrive/claude. **No Online Archive store** (GetStore by name fails). |
| Live COM window | classic `OUTLOOK.EXE` on work Inbox; 1 selection — **not** the 19-item sap4 view. |
| New Outlook (`Olk`) | installed; toggle **off**. Identity = personal IMAP `info@vdpj-ventures.be`, not isuzu-e.com. |
| Recipient Cache | 3 ContactItems (class 40): `sap4@`, `sap4u@`, `sap4uti@uti.co.il` in `Contacts\Recipient Cache` (643 nicknames). Windows Search `sap4@uti.co.il` hits **this path only**, not mail. |
| CreateRecipient | resolves as SMTP nickname, not an Exchange user. |
| Instant Search TableView `from:sap4@uti.co.il` (All Outlook Items, Single view, 40s poll) | **0 rows** (Compact GetTable cannot enumerate Exchange UI hits). Pass6’s “19 rows” was a **stale** prior UTIPartSales table, not sap4. |
| Subject-only GetTable Inbox/Sent/Deleted | 2025–26 `noreply2@` / FW only. |
| Brute folders with real counts (Archive 429 / Sales 130 / Parts 3481) | 0 sap4, 0 UTIPartSales 2020–22. |
| Graph / REST | no workspace token; tenant admin consent already closed. |

**Why the UI shows 19 and COM saves 0:** People/Instant Search paints **server-side** hits for a Recipient Cache nickname. Those 2020–22 items are **not in the OST**. COM can only save what is cached.

Those 2020–22 jobs would be **historical sell-out**, not the CY2025 Feb–Jul gap. To file them: in the Outlook window that *shows* the 19 items, select → Save Attachments into `01_data\90_INBOX\`, or drag the mails into Inbox and re-hunt. Never Send.

Scan logs: `01_data/90_INBOX/outlook_uti_sap4_scan_20260813.json` (+ pass2–6e, Windows Search JSON).

Mail dumps: `01_data/90_INBOX/UTI_PartSales_mail_20260813/` · `01_data/90_INBOX/dealer_sales_mail_20260813/`
