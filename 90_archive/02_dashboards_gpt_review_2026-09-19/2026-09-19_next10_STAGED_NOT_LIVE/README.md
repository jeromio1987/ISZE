# STAGED — corrected copies, NOT approved, NOT live

**Created:** 2026-09-19 (staging pass)
**Status:** these are **corrected copies that have not been approved** by Jerome.
They are **not shipped**. Do not treat them as the live deliverable.

Jerome's instruction for this pass: *"for now put them somewhere separate we will see if we
overwrite them."* The overwrite decision is **open**.

---

## What is in this folder

Ten corrected HTML files produced by the automated review pass of 2026-09-19, copied here
byte-for-byte from `..\2026-09-19_next10_fixed\` (that folder was **not** modified):

| # | Staged file | Bytes |
|---|---|---|
| 01 | `01_ISZE_Exec_Aftersales_Paper.html` | 279,733 |
| 02 | `02_ISZE_Leakage_Cockpit.html` | 2,057,215 |
| 03 | `03_Warranty_Commercial_Review.html` | 359,577 |
| 04 | `04_ISZE_AIM_Classification_Paper.html` | 286,352 |
| 05 | `05_ISZE_AIM_vs_Price_Class_Case.html` | 34,475 |
| 06 | `06_ISZE_Pricing_Policy_Paper_REV3.html` | 296,666 |
| 07 | `07_ISZE_Pricing_Revision_AIM_Source.html` | 6,605,745 |
| 08 | `08_ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html` | 228,031 |
| 09 | `09_ISZE_Competitiveness_Dashboard.html` | 145,499 |
| 10 | `10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | 60,478 |

Plus:

- `Data\` — 1 file (`Data\dashboards\isze_data.preload.js`, 44,046 bytes)
- `_ui\` — 5 files (230,423 bytes)
- Ten `0N_OPEN_*.cmd` launchers (CRLF, copied unchanged)
- `_qa_staging_verify\` — 10 viewport screenshots + `staging_verify.json` from this staging pass
- `_PRE_PATCH_CANDIDATES_2026-09-19_1254\` — see below
- `_STAGING_MANIFEST.json` — SHA-256 of every staged file

**Total: 56 files, 32,128,492 bytes (30.6 MB).**

Dependencies were copied because the pages load sibling assets. Note that in practice only
file **09** needs them: it references `_ui\chart.umd.min.js`, `_ui\editorial.css`,
`_ui\editorial-full.css`, `_ui\editorial-charts.js`, `_ui\isze-shell.js` and
`Data\dashboards\isze_data.preload.js`. The other nine are self-contained (no `src`/`href`
to a local file). All ten render headless with real content (see `_qa_staging_verify\`).

---

## Dependency path check — one real problem found (file 09)

Checked every local `src`/`href` in all ten pages against its position in this folder.

- **Files 01–08 and 10 are self-contained.** They contain no `src`/`href` pointing at a
  local file. In this folder there are no internal links at all, so nothing can break.
  The `data/...` strings that appear in some of them are prose in tables (source notes),
  not asset loads.
- **File 09 references six local assets.** All six resolve correctly in this folder:

  | Reference | Resolves here |
  |---|---|
  | `_ui/chart.umd.min.js` | yes |
  | `_ui/editorial.css` | yes |
  | `_ui/editorial-full.css` | yes |
  | `_ui/editorial-charts.js` | yes |
  | `_ui/isze-shell.js` | yes |
  | `Data/dashboards/isze_data.preload.js` | yes |

**The problem is with the live copy, not this one.** The corrected file 09 changed five
asset paths from `../_ui/...` to `_ui/...` (a deploy-layout path) and one data path from
`../Data/...` to `Data/...`. At the live location `02_dashboards\sales\`, those five `_ui`
assets do **not** exist — `02_dashboards\sales\_ui\` contains only `plotly.min.js`, while
the five files it asks for sit in `02_dashboards\_ui\`. So the live file loads without
`chart.umd.min.js`, `editorial.css`, `editorial-full.css`, `editorial-charts.js` and
`isze-shell.js`. The pre-overwrite version referenced `../_ui/...`, which did resolve.

Headless render of the live file is visibly thinner than the same file opened from this
folder (58.4% of pixels inked vs 67.9% at the same window size), consistent with the
missing stylesheet and chart library. This is reported, **not fixed** — no content was
edited in this pass.

The nine cross-navigation links in file 09 (`../hub/index.html`, `../fleet/...`, `../ops/...`,
and siblings such as `AIM_Dashboard_CY2026.html`) point to pages that exist in the live
`02_dashboards\` tree but not inside this folder. That is expected for a flat staging folder
and does not affect the page's own data.

---

## State of the live originals

The automated pass **copied each corrected file over its live original** on 2026-09-19 at
17:11–17:16. So **the live originals currently contain these same corrected files** —
verified byte-identical (same size, same blob hash) for all ten:

| Live original | = staged copy? |
|---|---|
| `02_dashboards\sales\ISZE_Exec_Aftersales_Paper.html` | identical |
| `02_dashboards\sales\ISZE_Leakage_Cockpit.html` | identical |
| `02_dashboards\sales\Warranty_Commercial_Review.html` | identical |
| `02_dashboards\sales\ISZE_AIM_Classification_Paper.html` | identical |
| `02_dashboards\sales\ISZE_AIM_vs_Price_Class_Case.html` | identical |
| `02_dashboards\pricing\ISZE_Pricing_Policy_Paper_REV3.html` | identical |
| `02_dashboards\pricing\ISZE_Pricing_Revision_AIM_Source.html` | identical |
| `02_dashboards\pricing\ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html` | identical |
| `02_dashboards\sales\ISZE_Competitiveness_Dashboard.html` | identical |
| `02_dashboards\sales\Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | identical |

**The pre-today (pre-overwrite) content of those ten live originals was NOT restored in this
pass.** Doing so is safe for some files and unsafe for others. Detail:

### Recoverable from git (3 of 10)

These are tracked. `HEAD` (commit `9e34a6d`, 2026-09-16) holds a version whose content
**differs** from the current on-disk patched file — the difference is proven, not assumed:

| File | HEAD blob | HEAD bytes | live bytes | diff vs live |
|---|---|---|---|---|
| `ISZE_Exec_Aftersales_Paper.html` | `03f330ce` | 277,904 | 279,733 | +57 / −51 |
| `ISZE_Competitiveness_Dashboard.html` | `55c4fb1c` | 143,157 | 145,499 | +19 / −13 |
| `Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html` | `46dec8dc` | 67,090 | 60,478 | +48 / −67 |

**Caveat, important:** `git checkout HEAD -- <path>` would not give *today's* pre-patch file.
Between 2026-09-16 and 2026-09-19 the live files were rebuilt by their builders. For example
the exec paper's `€60.22M / 51.1%` figures were rebased to `€55.25M / 55.7%` **before** today's
patch, and the dealer page was re-skinned. Restoring HEAD would silently revert that work.
Only `ISZE_Competitiveness_Dashboard.html` is close — its only non-patch difference from HEAD
is the 2026-09-19 12:54 deploy-sync path normalisation (`../_ui/` → `_ui/`, `../hub/` → `hub/`).

### NOT recoverable (7 of 10)

Not tracked at all, and **none of these names appears in any commit in the repository's
history** (`git log --all` on `*/<name>` returns nothing):

- `ISZE_Leakage_Cockpit.html`
- `Warranty_Commercial_Review.html`
- `ISZE_AIM_Classification_Paper.html`
- `ISZE_AIM_vs_Price_Class_Case.html`
- `ISZE_Pricing_Policy_Paper_REV3.html`
- `ISZE_Pricing_Revision_AIM_Source.html`
- `ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html`

No backup of these exists anywhere on disk. Every other copy found is the **corrected** file
(the two sibling review folders and the `08_gpt` pack are all byte-identical to the live copy).
No copy of the pre-overwrite versions was made before the overwrite, and the live files were
then **de-indexed** as well (they now match no index entry), so the index cannot restore them.

`git stash list` is **empty**. Nothing was stashed.

### `_PRE_PATCH_CANDIDATES_2026-09-19_1254\`

Copy of the 10 relevant files from the deploy mirror `07_deploy\Master Dashboard\` and
`07_deploy\publish-site\`, whose mtimes are **2026-09-19 12:54** — roughly four hours
*before* the 17:11 overwrite.

Treat this as a **point-in-time snapshot, not a verified restore source.** The mirror is
produced by `02_dashboards\sync_to_deploys.ps1`, which re-writes relative paths for the
deploy layout, so no deploy copy is byte-faithful to what sat at `02_dashboards\...`.
The deltas between a 12:54 deploy copy and the current live file are small and consist of
today's patch (the added `basis-strip`, wording changes) **plus** that path normalisation.
Each copied file's SHA-256 is in `_STAGING_MANIFEST.json`.

**One of the ten is absent from the mirror entirely:** `ISZE_Pricing_Policy_Paper_REV3.html`
has no deploy-side counterpart (only an older, differently-named `ISZE_Pricing_Policy_Paper.html`).
There is no pre-patch copy of that file anywhere.

---

## Why this matters for the overwrite decision

1. **Seven of the ten live originals are untracked and have no other copy.** If the corrected
   versions are rejected later, the pre-overwrite originals cannot be brought back. The decision
   is effectively one-way for those seven.
2. **The three tracked ones can be recovered only to 2026-09-16, not to yesterday.** So even
   the "recoverable" three are not cleanly recoverable to their immediate pre-today state.
3. Nothing in this folder has been approved. Rebuild/ship permission was not given and was not
   assumed.

---

## Reproducing the checks

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE

# tracked?
git ls-files --error-unmatch -- 02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html

# is HEAD different from what is on disk?
git diff --numstat -- 02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html

# is this name in any commit at all?
git log --all --oneline -- "*/ISZE_Leakage_Cockpit.html"

# does the live file equal the corrected copy?
git hash-object -- 02_dashboards/sales/ISZE_Leakage_Cockpit.html
git hash-object -- 02_dashboards/sales/_gpt_review/2026-09-19_next10_fixed/02_ISZE_Leakage_Cockpit.html
```

No HTML content was edited in this pass. This folder is a copy plus a README.
