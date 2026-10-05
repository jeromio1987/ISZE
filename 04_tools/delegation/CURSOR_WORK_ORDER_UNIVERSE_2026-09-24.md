# Cursor work order — Isuzu Universe follow-ups (24 September 2026)

Four tasks. Each block is self-contained: paste one block per Cursor chat, in order A → D.
A and B can run in parallel. C is small. D waits for Jerome's signal.

**Rules for every task (repeat of workspace rules):**
- Read `CLAUDE.md`, `INDEX.md`, and the last 10 rows of `00_docs\agent\DELEGATOR_BOARD.md` first. When done, append one row.
- Never load `01_data\raw\sales\*.XLSX` or line-level billing.
- No emails, no publishing, no new scheduled tasks, no change to an existing scheduled task.
- Labels: "sales to dealer", "parts billed", "the price list", "reference dealer price". Lubricants stay out of parts figures; say "fuel filter", never "fuel".
- Never invent a number. If data is missing, show it as missing.
- Write files as UTF-8 **without BOM** (Python `open(..., "w", encoding="utf-8")`; not PowerShell `Set-Content`).
- Report back in under 150 words: files changed, checks run with results, anything left open.

---

## A · PRISM tender page reads the live tender feed (small)

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in 04_tools\delegation\CURSOR_WORK_ORDER_UNIVERSE_2026-09-24.md.

Problem: the PRISM tender page 03_analytics\Isuzu\prism\pages\14_Tender_Pipeline.py reads
01_data\00_derived\tender_pipeline.csv, last built 29 May 2026 (708 rows). The live feed is
01_data\14_dashboards\tender_data.json (written weekly by the "ISZE Tender Monitor" task; last
generated 2026-09-22, 619 opportunities, 689 notices).

Do:
1. Make the page load tender_data.json -> "opportunities" directly (fields include rm_contract,
   parts_signal, decision, deadline_date, value_amount, fleet_size, country, distributor_code,
   owner_suggested, opportunity_score, url, product_segment_label, outcome). Show meta.generated_at
   on the page as "Feed date". Keep a clear error if the file is missing.
2. Replace the hard-coded warning ("value on only 12 of 520 ... deadlines on 55") with counts
   computed from the file (value present, deadline present, outcomes recorded). Today these
   should read 31, 128 and 0 of 619; verify, do not copy.
3. Check that the chart helpers in modules\advanced_visuals.py (fig_tender_funnel, _country,
   _owner, _scatter) still read tender_pipeline.csv. If so, point them at the same loader. Do not
   delete tender_pipeline.csv or scripts\build_tender_pipeline.py.
4. Add an R&M filter: a checkbox "R&M contracts only" (rm_contract == True) and a
   "deadline on or after today" toggle.
5. Run the PRISM tests (pytest in 03_analytics\Isuzu\prism) and start the app once
   (run_prism_internal.ps1). Load the tender page and take a screenshot. Confirm the feed date
   and counts render.
```

---

## B · Weekly R&M tender digest per distributor (medium)

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in 04_tools\delegation\CURSOR_WORK_ORDER_UNIVERSE_2026-09-24.md.

Goal: the "coordinated tenders" tool from the Isuzu Universe paper. Once a week, every
distributor gets a one-page list of the open public tenders for fleet repair and maintenance (R&M)
in its market that it could bid on, or pass to a dealer.

Input: 01_data\14_dashboards\tender_data.json -> "opportunities" (619 rows; 279 have
rm_contract = true; 236 are product_segment_label "R&M only — no vehicle buy"). Useful fields:
distributor_code, ids_dealer_name / ids_dealer_city / ids_match_confidence, deadline_date,
days_to_deadline, decision (Attack/Selective/Watch/Ignore), opportunity_score, buyer, title,
country, value_amount, fleet_size, aftersales_summary, url, data_gaps, outcome.

Build 04_tools\ISZE_Tender_Monitor_Install\build_rm_digest.py:
1. Select rm_contract == true AND decision in (Attack, Selective, Watch) AND (deadline_date >=
   run date OR deadline missing). List deadline-missing rows in a separate "deadline not
   published, check the notice" section, never mixed with dated ones.
2. Group by distributor_code. Rows with no distributor_code go to an internal
   "unassigned" page. Count them in the report.
3. Per distributor, output one self-contained HTML (charcoal + Isuzu red, no CDN, A4
   printable), sorted by deadline:
   - buyer, title, deadline and days left, value if published (else "not published"), fleet size
     if published, a one-line aftersales summary, the nearest Isuzu dealer if the match
     confidence is high (otherwise leave it blank), and a link to the notice;
   - a closing box: "Tell us which of these you will pursue: pursue / pass / already known".
4. Per distributor, also write a CSV with an empty "outcome" column: pursue / pass / won / lost /
   no decision. This is the outcome record. It is the missing piece: 0 of 619 opportunities have
   an outcome today. Check how 04_tools\ISZE_Tender_Monitor_Install\tender_outcomes.py stores
   outcomes (meta.outcomes_store in tender_data.json) and make the CSV importable by it. Do not
   write into the outcome store.
5. Pages that could go to a distributor must not contain internal terms. Scan them for: AIM,
   PRISM, DLOD, IDS as an acronym, GPS, BVP, IML, ITUK, IUK, UMI, UTI, "campaign", .csv, .json,
   .py. The count must be 0. Each page shows only its own distributor's name.
6. Output: 04_tools\ISZE_Tender_Monitor_Install\rm_digest\<run date>\, plus index.html
   (internal) and an OPEN_RM_DIGEST.cmd (open only).
7. Do NOT add it to run_tender_monitor.bat and do NOT create a scheduled task. Jerome decides
   that. In your report, give the exact line you would add to the .bat.
8. Run it on today's feed. Report the count of R&M opportunities per distributor (dated and
   undated), the unassigned count, and the banned-term result. Render 2 pages with headless
   Chrome and look at them.
```

---

## C · Spot-check follow-up: independent witnesses for 11 rows (small)

```text
Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in 04_tools\delegation\CURSOR_WORK_ORDER_UNIVERSE_2026-09-24.md.

Context: 01_data\90_INBOX\_aftermarket_spotcheck_20260924\SPOTCHECK_20_CHECKED_AI_2026-09-24.csv
holds an AI-run check of 20 competitor cross-references. Result: 0 wrong, 2 unverifiable, 18
confirmed; verdict "carry on". Caveat: 13 of the 18 confirmations rest only on spareto.com, which
does not state its data source. It may share catalogue data with our Eucon source, so those rows
may only prove the data agrees with itself. Rows 16 and 19 were re-confirmed independently (the
bilstein partsfinder official catalogue, Autodoc, and other shops).

Do: for rows 2, 3, 4, 7, 9, 10, 12, 14, 15, 18 and 20, find ONE source that is not Spareto: the
brand's own catalogue (partsfinder.bilsteingroup.com for febi/SWAG/Blue Print, the Bosch, Hella,
Denso, Ajusa or Metelli catalogues), or a shop that shows the Isuzu OE number. Record the URL, a
quote of at most 15 words, and the pack quantity. Do not log in, accept terms or buy anything.
Leave a row blank if nothing independent is found.
Write SPOTCHECK_20_INDEPENDENT_2026-09-24.csv in the same folder. Do not edit the other files.
Report: how many of the 11 now have an independent witness, and any row where the independent
source contradicts Spareto (fitment or pack quantity).
```

---

## D · New classification release: register and re-test (waits for Jerome)

```text
START ONLY when Jerome confirms the new classification release is finished.

Work in C:\Users\jerom\Desktop\claude\ISZE. Follow the rules in 04_tools\delegation\CURSOR_WORK_ORDER_UNIVERSE_2026-09-24.md.

Context: Isuzu Universe\01_Strategy\CLASSIFICATION_RELEASE_DECISION_2026-09.md (read it all,
including "Update 24 September 2026"). Frozen candidate:
01_data\00_derived\_releases\aim_pn_classification_release_2026-09-20.csv (SHA-256 60111c10…).
Release register: 01_data\00_derived\_releases\RELEASES.json. Checker:
01_data\00_derived\_releases\check_classification_release.py.

Do:
1. Hash the new release file. Add it to RELEASES.json as a candidate with status
   PENDING_APPROVAL (never APPROVED). Record path, SHA-256, rows, build date, upstream.
2. Compare it with the 2026-09-20 frozen copy on billed 2025 parts (from
   01_data\00_derived\sales_fact.parquet; freight, rebates and interest excluded): rows changed,
   and euro changed by family/group. List the top 10 by euro.
3. Re-test the three white-paper checks from the memo:
   (a) Isuzu Truck UK brake pads, 2024 → 2025, measured on the brake-pad group;
   (b) the Portugal clutch examples, components against true kits;
   (c) share of air-filter euro sitting under "Air conditioning" (should be 0), and the 17-of-18
       check (the "Filters > Filter element" leaf).
   Also check the known faults: 4 Shell lubricant PNs under Wheel Rim; guide pin 8980475290 in
   brake pads; bumper bars in leaf spring.
4. Write "Isuzu Universe\01_Strategy\CLASSIFICATION_RELEASE_RETEST_<date>.md": what improved,
   what regressed, and a recommendation (freeze it or not). Do not approve. Do not edit
   build.py. Do not modify any classification file.
```
