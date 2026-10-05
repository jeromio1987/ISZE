# AIM gap × BEV RG30 APL (IBX/ISA/IUK) — 2026-09-18

Join only. No HTML/Excel rebuild.

## Where the files were

Not in Downloads or a fresh save. They were already on disk under `01_data/` (and Outlook INetCache), dated ~215 days old. Copied into `90_INBOX` this pass.

| File | Path | Size |
|---|---|---|
| IBX | `01_data/90_INBOX/RG30_APL and Recommended list for IBX.xlsx` | 1,479,020 |
| ISA | `01_data/90_INBOX/RG30_APL and Recommended list for ISA.xlsx` | 1,567,491 |
| IUK | `01_data/90_INBOX/RG30_APL and Recommended list for IUK.xlsx` | 1,568,525 |

Also still at `01_data/RG30_APL and Recommended list for {IBX,ISA,IUK}.xlsx` (same bytes).

Sheet on all three: `RL`. Header has `EV Unique RG20` (label on sheet; files are RG30 APL).

## PN extract

| Metric | Value |
|---|---|
| Unique Isuzu PNs (union of 3) | **2325** |
| Rows in `ev_parts_pns_20260918.csv` (pn×db_tag) | **6972** |
| EV-unique flagged | **540** |
| Training-snippet PNs kept if missing | 7552347140 / 7552360101 / 7552598420 |

## Gap overlap

| Metric | Value |
|---|---|
| Gap PNs also on RG30 APL | **412** |
| Of which leftover (Unknown/empty prior) | **81** |
| High-conf Electrical/EV assign | **109** |
| Medium (on list, not clearly electrical) | **303** |
| Master patches this pass (`gap_auto_20260918_rg30`) | **12** |

EV triple used from master vocab (no dedicated HV leaf): **Electrical → Charging → Alternator/Generator**, with Sensors / Motors / Control Units / Lighting / Harness when the part name clearly matches.

## Outputs

- `01_data/00_derived/ev_parts_pns_20260918.csv`
- `01_data/00_derived/aim_gap_bev_assign_20260918.csv` (overwrites prior RG20-only assign)
- `01_data/00_derived/aim_gap_bev_assign_SUMMARY_20260918.md`
- Master backup: `01_data/00_derived/aim_master_v2.csv.bak_pre_rg30_20260918`

## Browser note

Agent Outlook tab was not available (only EQ-Hit open; new tab navigate failed). Disk find was enough — no mailbox download needed this pass.
