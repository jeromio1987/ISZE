# UK KS PDP OE upgrade — 2026-10-07

## Verdict

**The search card was lying by omission; the product page was not.** All **25** KS PDPs checked print the linked Isuzu part number under the Magento attribute **OE Equivalent Part Number** (also in JSON-LD `mpn` / product-info). That is enough for an honest `category_only` → `exact_oem` upgrade. **55** ledger rows patched on U29b. Wider UK `exact_oem` eligible moved **28 → 83** offers (**14 → 25** PNs). Focus usable (oil filter + brake pad cut) moved to **47** rows. Board / INTERNAL not rebuilt here.

Parent evening brief still said 18 / 13; the U29b wider metrics file at job start already read **28 / 14** before any PDP patch. Delta below uses that measured before.

## Method

New angle vs Isuzu-PN Magento search: take existing UK KS `category_only` rows (loader `ks`), open the **product page (PDP)** for the stored KS SKU (`competitor_pn`), and only upgrade when the Isuzu `part_no` is clearly printed on the PDP.

Cap **25** — selection filled with focus-blocked filter SKUs (highest £ among blocked oil-filter / filter-kit walls). High-£ clutch / exhaust `category_only` SKUs were crowded out of this 25 and remain a follow-on.

Ledger:  
`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet`

£10 delivery + VAT excl: all 25 were **filter** families, so they match the live KS mainland £10 classes (filter / clutch / muffler / tail pipe) in `UNIVERSE_UK_KS_POLICY_SCOPE_2026-10-07.md`. No body / rotor / spring wired.

Pass 2: for each accepted PDP, every other `category_only` row on the same KS SKU whose `part_no` also appears in that OE list was upgraded too (+8 rows).

## Tried / upgrades / rejects

| Metric | Count |
|---|---:|
| PDPs / SKUs checked | **25** |
| Upgrades (OE on PDP) | **25** (100%) |
| Rejects | **0** |
| Ledger rows patched (pass1 + pass2) | **55** |
| Distinct KS SKUs upgraded | **25** |
| Distinct Isuzu PNs touched | **13** |

### Candidates checked

| # | KS SKU | Candidate Isuzu PN | £ excl | Family | Blocked focus | Verdict |
|---:|---|---|---:|---|---|---|
| 1 | `0012884` | `8980188580` | 70.00 | filter | Y | upgrade — OE attr |
| 2 | `0012884K` | `8980188580` | 45.00 | filter | Y | upgrade — OE attr |
| 3 | `0012878` | `8971725491` | 45.00 | filter | Y | upgrade — OE attr |
| 4 | `0012879` | `8973299110` | 45.00 | filter | Y | upgrade — OE attr |
| 5 | `0012878K` | `8971725491` | 30.00 | filter | Y | upgrade — OE attr |
| 6 | `0013134K` | `8971725491` | 30.00 | filter | Y | upgrade — OE attr |
| 7 | `0012879K` | `8973299110` | 30.00 | filter | Y | upgrade — OE attr |
| 8 | `0013134` | `8971725491` | 20.00 | filter | Y | upgrade — OE attr |
| 9 | `0013721` | `8975439050` | 15.00 | filter | Y | upgrade — OE attr |
| 10 | `0013561G` | `8982705240` | 15.00 | filter | Y | upgrade — OE attr |
| 11 | `0011764` | `8980188580` | 13.00 | filter | Y | upgrade — OE attr |
| 12 | `0013721K` | `8975439050` | 12.00 | filter | Y | upgrade — OE attr |
| 13 | `0001004` | `8973299110` | 11.50 | filter | Y | upgrade — OE attr |
| 14 | `0011764K` | `8980188580` | 10.00 | filter | Y | upgrade — OE attr |
| 15 | `0013561` | `8982705240` | 10.00 | filter | Y | upgrade — OE attr |
| 16 | `0001022` | `8971482800` | 10.00 | filter | Y | upgrade — OE attr |
| 17 | `0001036` | `8973017520` | 9.00 | filter | Y | upgrade — OE attr |
| 18 | `0001004K` | `8973299110` | 8.50 | filter | Y | upgrade — OE attr |
| 19 | `0001011` | `8970497081` | 8.50 | filter | Y | upgrade — OE attr |
| 20 | `0001022K` | `8971482800` | 7.50 | filter | Y | upgrade — OE attr |
| 21 | `0011227K` | `8973099270` | 6.00 | filter | Y | upgrade — OE attr |
| 22 | `0078879` | `8971679720` | 5.00 | filter | Y | upgrade — OE attr |
| 23 | `0078955` | `8970497081` | 5.00 | filter | Y | upgrade — OE attr |
| 24 | `0703831` | `8981240801` | 5.00 | filter | Y | upgrade — OE attr |
| 25 | `0701999` | `8981650710` | 3.00 | filter | Y | upgrade — OE attr |

### Evidence examples (quoted from PDP)

| KS SKU | Where | Quote |
|---|---|---|
| `0013561G` | attr: OE Equivalent Part Number | `8982705240` |
| `0012884` | attr: OE Equivalent Part Number | `8980188580, 8970622940, 8980370110` |
| `0001011` | attr: OE Equivalent Part Number | `8-97049-708-1, 8970497081` |

`source_url` on patched rows points at the PDP (not the search grid). Description carries a short PDP OE upgrade note.

### Pass 2 extras (same SKU, other Isuzu PNs also on OE list)

| KS SKU | Extra Isuzu PN(s) upgraded | Extra rows |
|---|---|---:|
| `0012884` / `0012884K` | `8970622940` | 4 |
| `0012878` / `0012878K` | `8973299110` | 2 |
| `0013134` / `0013134K` | `8973017520` | 2 |
| **Total pass2** | | **8** |

## Rejects

None of the 25. No invent: only PNs literally present in the OE attribute / JSON-LD were upgraded.

## Eligible before / after

Coverage rebuild (U29b worktree script + node runner):

```text
python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact
```

| Cut | Before (job-start metrics) | After |
|---|---:|---:|
| Wider UK `exact_oem` eligible **offers** | **28** | **83** |
| Wider eligible **PNs** | **14** | **25** |
| Delta offers | | **+55** |
| Delta PNs | | **+11** |
| Of which in focus (oil filter + brake pad) | 4 (evening) / metrics later | **47** |
| Outside focus | | **36** |

Metrics after:  
`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`

## Backups

- `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet.bak_20261007T161122Z_before_ks_pdp_oe`
- `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet.bak_20261007T161320Z_before_ks_pdp_oe_pass2`

## Artefacts

| Object | Path |
|---|---|
| PDP HTML + search HTML + checks JSON | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_pdp_oe_upgrade_20261007\` |
| Runner | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_ks_pdp_oe_upgrade_20261007.py` |
| Pass2 | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_ks_pdp_oe_upgrade_pass2_20261007.py` |
| This note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_PDP_OE_UPGRADE_2026-10-07.md` |

## Follow-on (after parent refresh)

- INTERNAL + board rebuilt: **83** shop offers / **25** case hooks painted; banner focus **47** / wider **83** / **25** PNs. See `UNIVERSE_INTERNAL_ELIGIBLE_WIRE_2026-10-07.md`.
- No ACCEPT.
- High-£ clutch / exhaust `category_only` PDPs not in this 25 — same OE-attribute check is the obvious next pass.
- Remaining KS `category_only` after this job: **749** rows (many non-filter).
