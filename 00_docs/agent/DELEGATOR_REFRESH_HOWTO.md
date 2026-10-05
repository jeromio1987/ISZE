# What to do when the delegator board says AIM moved

**Companion to:** `00_docs/agent/DELEGATOR_BOARD.md` · **Written:** 2026-09-17

The watch is **detect-only**. It tells you that an AIM input moved and that the packs built on
that input are now stale. It does not rebuild anything by itself. This page says what to do next.

---

## 1. First, read the protected list — it is not optional

Jerome locked these as **read-only on 2026-09-17**. Do not overwrite, edit, or regenerate any of
them. The watcher refuses to write them even when `-RefreshDerived` is on, and this page does not
authorise anyone else to either.

| Locked file | Why it is locked |
|---|---|
| `01_data/01_Pricing/Pricing_Revision_AIM_Source_Analysis.xlsx` | The shipped revision pack |
| `01_data/Pricing/Pricing_Revision_AIM_Source_Analysis.xlsx` | Its duplicate copy |
| `02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html` | The shipped revision page |
| `02_dashboards/pricing/_build/pricing_dashboard_data.json` | Its data pack |
| `02_dashboards/pricing/AIM_PRIORITY_LIST.csv` / `.xlsx` | The AIM priority list |
| `01_data/00_derived/aim_master_v2.csv` | The corrected AIM master |
| Anything else already under `01_data/00_derived/` | Derived spine — existing files stay as they are |
| `03_analytics/isze_pricing/config.yaml` | The engine config; the exchange-rate fork is open and deliberately unsettled |

Plus the receipts and `OPEN_*.cmd` launchers beside each of those.

**If a locked file genuinely needs rebuilding, that is Jerome's call, not the watcher's.** Record
the request on the board and stop. Authority rule: `.cursor/rules/isze-no-ship-without-ok.mdc`.

---

## 2. The refresh this workstream does own

The +5% flat review is **new work on new files** (created 2026-09-17). Only this set may be rebuilt
by the watcher or by anyone acting on a board row:

| Artifact | Path |
|---|---|
| Builder | `02_dashboards/pricing/_build/price_5pct_review_2026-09-17/build_price_increase_5pct_review.py` |
| Workbook | `01_data/01_Pricing/Price_Increase_5pct_Flat_REVIEW_2026-09-17.xlsx` |
| HTML page | `02_dashboards/pricing/ISZE_Price_Increase_5pct_Flat_REVIEW_2026-09-17.html` |
| Launcher | `02_dashboards/pricing/OPEN_ISZE_Price_Increase_5pct_Flat_REVIEW.cmd` |

Rebuild it with:

```
python 02_dashboards/pricing/_build/price_5pct_review_2026-09-17/build_price_increase_5pct_review.py
```

Then verify before claiming anything is done — builder exit 0 is not done
(`.cursor/rules/isze-ship-gate.mdc`):

```
python 02_dashboards/pricing/_build/verify_pricing_analysis_xlsx.ps1
```

---

## 3. When an AIM file moves and a rebuild is actually wanted

The AIM-derived packs are locked, so the honest sequence is:

1. **Say so plainly.** Write on the board which locked pack is now stale and why.
2. **Ask Jerome.** A rebuild of a shipped pricing deliverable needs his explicit word in the
   current message. Not a board row, not this page.
3. **If he authorises new work, build new dated files** — never overwrite the locked ones. Follow
   the naming already used here: a `_REVIEW_<date>` suffix on the artifact, and a dated folder
   under `_build/`.
4. **Verify, then receipt.** Paint-check the HTML in a real browser, run the workbook checks, and
   write a `SHIP_RECEIPT.json` beside each output (`verify-before-done`).

The commands that would have been used for the AIM-derived packs, kept here for reference only —
**do not run these against the locked files without Jerome's instruction**:

```
python 01_data/91_build/build_aim_master_v2_and_priority.py
python 01_data/91_build/build_pricing_aim_source_cube.py
python 02_dashboards/pricing/_build/build_pricing_revision_analysis_xlsx.py
python 02_dashboards/pricing/_build/build_pricing_revision_dashboard.py
```

---

## 4. Three things that are never delegated

Straight from `00_docs/RUNBOOK_ROUTINE_HANDOVER.md` §5, and they apply to this watch as much as to
a second person:

- **Anything that sends mail.** Draft only, and Jerome sends.
- **Anything that changes a price.** A price move is a signed decision by a named person.
- **Anything that publishes to the shared mirror.** One-way and cannot be walked back.

The watcher writes to exactly one place: the board, and the state file. Nothing else.
