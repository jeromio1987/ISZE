# AIM gap tools / EV overlay — 2026-09-18

Join only. No HTML/Excel rebuild. `aim_master_v2.csv` left untouched.

## Input caveat

`01_data/00_derived/special_tools_pns_20260918.csv` on disk is **no longer** the AIM Workshop Tools 84. Another pass replaced it with **353 PNs from `Specialtools.pdf` (ISB25-SST-08 bulletin)**. Overlap with the AIM 84 is only **5**.

The counts below for “84 tools” are from `aim_pn_classification_v2.csv` where `workbook_l2=Workshop Tools` and `workbook_source=aim_workbook` (the set the Outlook notes describe).

## Overlap counts

### AIM Workshop Tools (84)

| Check | Count |
|---|---|
| In pricing gap CSV | **0** |
| Gap assigned | 0 |
| Gap unassigned | **0** |
| In `aim_master_v2` | **84 / 84** |
| Master already `Tools Equipment` | **84 / 84** |

Nothing left to overlay for tools against the gap: they are out of the gap and already classified on master.

### EV snippet PNs (3)

| Check | Count |
|---|---|
| In pricing gap CSV | **0** |
| Gap assigned / unassigned | 0 / 0 |
| In `aim_master_v2` | **0 / 3** |

PNs: `7552347140`, `7552360101`, `7552598420`.

### Disk SST file (353) — residual only

Not the brief’s 84. Of 353: **14** in gap (**7** assigned, **7** still `unassigned`), **282** in master, **28** with an AIM L1 (only **5** already `Tools Equipment`). The 7 gap-unassigned SST PNs were **not** written into the overlay (wrong list for this pass).

## Overlay written

`01_data/00_derived/aim_gap_tools_ev_overlay_20260918.csv`

- **3 rows** (EV only): `proposed_aim_l1=Electrical (HV)`, `method=outlook_or_aim_tools_list`, `confidence=high`
- `overlay_action=propose_not_in_gap_not_in_master` — they are not gap rows; this is a proposal file only
- Tools overlay rows: **0** (master already done; none in gap)

## Mail subjects Jerome should save into `01_data/90_INBOX`

Agent browser cannot land attachments on disk. He must download in Outlook on Windows and drop the files:

1. **N Series Special Service Tool Information** (Saida — N-Series SST PDF / ISB25-SST-08)
2. **2026MY – TF Series Special Service Tool Information** (Saida — TF Series SST)
3. **RE: BEV RG30 All Parts list & Recommended list by DBs** / **FW: All parts list BEV RG30** / Natalie’s nested `.msg` **BEV RG30 All Parts list**
4. **EV unique parts pricing** (nested `RE: BEV price file`)

## Plain residual

1. Tools AIM-84: closed on master; no gap work.
2. EV-3: not billed in the gap set and missing from master — overlay proposes HV until the full BEV list lands.
3. Disk tools CSV is the wrong list (SST 353); restore or re-extract the AIM-84 if that path must stay the workbook list.
4. SST bulletin still has **7** unassigned gap PNs if someone wants a separate SST overlay later.
