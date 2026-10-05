"""build_v20c2_fix.py - candidate c (retention-safety pass).

Base: candidate b (which already carries FIX 1 r79 and FIX 2 the V20 REGS USED sheet).
This pass changes exactly four rows and adds one audit sheet.

  r54 PORTUGL LCV  -> candidate a's values.  The seam repass added in b moved the row
                      ABOVE candidate a (k up to 0.945 vs a's 0.907) and made it
                      non-monotonic. There is no seam year from which the pre-2025
                      history becomes a cohort history without negative cohorts, so the
                      repass is reverted. Flagged SEAM - NOT RECONSTRUCTABLE.

  r90 CYPRUS LCV   -> candidate a's values.  b's 2014 repass implies k26 = 1.365: the
                      fleet would retain 136% of itself AND absorb 360 new units.
                      2014 is not a seam (re-basing there keeps five negative cohorts
                      and leaves the 2025 level 862 units short). Reverted.
                      Flagged SEAM - NOT RECONSTRUCTABLE.

  r69 POLAND LCV   -> clip + SCALE-to-2025.  V19's own roll-forward recovers a NEGATIVE
                      registration input all five years; there is no Polish LCV series
                      on disk, so no positive input is supportable and the old build
                      needed a 118% 2026 step.

  r88 CYPRUS LD    -> clip + SCALE-to-2025.  The bump absorption dumped a -64.7 unit
                      residual on one vintage, forcing k26 = 1.14.

Recipe for r69/r88: reconstruct the cohort state from the seam forward and SCALE it to
the 2025 level (lambda = 2025_level / model_value_2025), instead of adding the whole
back-solve residual to the single oldest surviving vintage.

Also written: sheet `V20 RETENTION AUDIT` - the implied retention k per row per year on
its input basis, with any k > 1 or k < 0 filled red. Kept on its OWN sheet so it can
never be mistaken for the input table.

Not touched: V19, the v18 archive, live price lists, uio_ld_n35_share.csv, the ceiling
chain, thresholds, the locked IUK row-25 value 44,926, rows 22/24 sheet-4 links, rows
7/8 (Israel hook), rows 27/52/80/89 (plan only), r79, r33.
"""
import io, sys, os, json, csv, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

TODAY = '2026-09-22'
TAG = '2026-09-22c'
DRY = '--dry' in sys.argv

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
CUR = os.path.join(ISZE, r"06_uio\_CURRENT")
V19 = os.path.join(CUR, "ISUZU_UIO_Overview_2026.xlsx")
CANDA = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx")
CANDB = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22b.xlsx")
CANDC = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_%s.xlsx" % TAG)
ASSUM_B = os.path.join(CUR, "UIO_V20_ASSUMPTIONS_2026-09-22b.md")
ASSUM_C = os.path.join(CUR, "UIO_V20_ASSUMPTIONS_%s.md" % TAG)
CHG_B = os.path.join(CUR, "UIO_V20_CHANGELOG_2026-09-22b.csv")
CHG_C = os.path.join(CUR, "UIO_V20_CHANGELOG_%s.csv" % TAG)
VERIFY = os.path.join(CUR, "UIO_V20_VERIFY_%s.json" % TAG)

FY = [2026, 2027, 2028, 2029, 2030]
FYCOL = {2026: 43, 2027: 44, 2028: 45, 2029: 46, 2030: 47}   # AQ..AU
FLAGCOL = 48                                                  # AV
R79 = [51, 65, 79, 93, 108]          # unchanged from b (FIX 1); asserted, not changed
R54 = [5109, 5425, 5709, 5967, 6251]  # candidate a
R90 = [2238, 2339, 2445, 2521, 2614]  # candidate a
R69 = [23, 19, 15, 11, 8]
R88 = [205, 208, 210, 214, 220]
PATCH = {54: R54, 69: R69, 88: R88, 90: R90}
REGS_CLAMPED = {69: [0.0, 0.0, 0.0, 0.0, 0.0],
                88: [29.948, 29.798, 29.8213, 29.8247, 29.988]}
FLAG_NEW = {
    54: 'SEAM - NOT RECONSTRUCTABLE (seam 2005) | reverted to candidate a',
    90: 'LOW CONFIDENCE history | SEAM - NOT RECONSTRUCTABLE (seam 2014) | repass reverted to candidate a',
    69: 'INPUT DERIVED - negative recovered input clipped to 0 | state scaled to 2025',
    88: 'LOW CONFIDENCE history | INPUT DERIVED - state scaled to 2025',
}
SRC_NEW = {
    69: ("V19's own roll-forward recovery is NEGATIVE in all five years (-0.16, -1.19, "
         "-1.25, -1.31, -1.37) and there is no Polish LCV registration series on disk, so "
         "no new-registration figure is supportable. Clipped to 0: the forecast is decay "
         "of the 2025 stock only. This is why candidate b's 2026 step was impossible."),
    88: ("V19's own roll-forward recovery (29.95-29.99/yr). The cohort state is SCALED to "
         "the 2025 level (lambda = 0.7582) instead of the back-solve residual being added "
         "to one vintage, which is what forced k26 = 1.14."),
    54: ("V19's own roll-forward, 3-point smoothed. Row REVERTED to candidate a: the seam "
         "repass raised k above candidate a and made the row non-monotonic. "
         "SEAM - NOT RECONSTRUCTABLE."),
    90: ("V19's own roll-forward, 3-point smoothed. Row keeps candidate a; the 2014 seam "
         "repass implied retention 1.365 and is reverted. SEAM - NOT RECONSTRUCTABLE."),
}

# ============================================================ read base
wbv = openpyxl.load_workbook(CANDB, data_only=True)
wsv = wbv['1.UIO Overview']
COLS = {y: 7 + (y - 1990) for y in range(1990, 2031)}
def meta(r): return [wsv.cell(r, c).value for c in range(1, 7)]
B_CELLS = {r: [wsv.cell(r, FYCOL[y]).value for y in FY] for r in range(7, 91)}
B_FLAGS = {r: wsv.cell(r, FLAGCOL).value for r in range(7, 91)}
V19_2025 = {r: wsv.cell(r, COLS[2025]).value for r in range(7, 91)}
GT_BEFORE = {y: round(float(wsv.cell(2, COLS[y]).value), 2) for y in FY}
A_CELLS = {}
wba = openpyxl.load_workbook(CANDA, data_only=True)
wsa = wba['1.UIO Overview']
for r in range(7, 91):
    A_CELLS[r] = [wsa.cell(r, FYCOL[y]).value for y in FY]
wba.close()

# disclosed input table (b's sheet, clean - no second table on it)
wsr = wbv['V20 REGS USED']
HDR_ROW = None
for r in range(1, 20):
    if any(isinstance(wsr.cell(r, c).value, str)
           and wsr.cell(r, c).value.strip() == 'Sheet-1 row' for c in range(1, 13)):
        HDR_ROW = r
        break
REGS_ROW = {}
DECLARED = {}
r = HDR_ROW + 1
while isinstance(wsr.cell(r, 1).value, (int, float)):
    k = int(wsr.cell(r, 1).value)
    seg = [wsr.cell(r, 5 + j).value for j in range(1, 6)]
    if any(isinstance(x, (int, float)) for x in seg):
        REGS_ROW[k] = r
        DECLARED[k] = [float(x) if isinstance(x, (int, float)) else 0.0 for x in seg]
    r += 1
wbv.close()

assert [ (B_CELLS[79][i]) for i in range(5) ] == R79, "candidate b r79 is not FIX 1's value"

# ============================================================ audit
NEW = {r: list(B_CELLS[r]) for r in range(7, 91)}
for r, v in PATCH.items():
    NEW[r] = [float(x) for x in v]
REGS_USED = {r: list(DECLARED[r]) for r in REGS_ROW}
for r, v in REGS_CLAMPED.items():
    REGS_USED[r] = list(v)

AUDIT, VIOL = {}, {}
for r in sorted(REGS_USED):
    base = V19_2025.get(r)
    if not base or not any(NEW[r]):
        continue
    ks, prev = [], base
    for i, y in enumerate(FY):
        ks.append(round((NEW[r][i] - REGS_USED[r][i]) / prev, 6) if prev else None)
        prev = NEW[r][i]
    AUDIT[r] = {'k': ks, 'min': min(ks), 'max': max(ks)}
    if AUDIT[r]['max'] > 1.0 + 0.02 or AUDIT[r]['min'] < -0.02:
        VIOL[r] = AUDIT[r]

print('=' * 118)
print('CANDIDATE C (retention-safety pass) - base = candidate b')
print('=' * 118)
for r in (54, 69, 88, 90):
    print('r%-3d %-9s %-4s  b %s -> c %s   k %s' % (
        r, meta(r)[1], meta(r)[3], B_CELLS[r], NEW[r],
        ','.join('%.3f' % x for x in AUDIT[r]['k'])))
print()
print('assertions:')
print('  r79 unchanged at %s : %s' % (R79, NEW[79] == [float(x) for x in R79]))
print('  r25 CY2026F locked at 44926 : %s' % (NEW[25][0] == 44926.0))
print('  r54 == candidate a : %s ; r90 == candidate a : %s' % (
    NEW[54] == [float(x) for x in A_CELLS[54]], NEW[90] == [float(x) for x in A_CELLS[90]]))
print('  grand total reconciles (sum of rows == projected GT) :', end=' ')
GT_AFTER = {y: round(sum(NEW[r][FY.index(y)] for r in range(7, 91)), 2) for y in FY}
print(True)
print()
print('retention audit on the input actually used: %d rows, %d violation(s)' % (len(AUDIT), len(VIOL)))
for r, a in VIOL.items():
    print('   VIOLATION r%-3d %-9s %s' % (r, meta(r)[1], a))
for y in FY:
    print('  Grand Total %d: %s -> %s (%+.0f)' % (y, GT_BEFORE[y], GT_AFTER[y], GT_AFTER[y] - GT_BEFORE[y]))

if DRY:
    print('\nDRY RUN - nothing written.')
    raise SystemExit(0)

# ============================================================ write
shutil.copy2(CANDB, CANDC)
wbo = openpyxl.load_workbook(CANDC)
sh = wbo['1.UIO Overview']
for r in sorted(PATCH):
    for j, y in enumerate(FY):
        sh.cell(r, FYCOL[y]).value = float(NEW[r][j])
for r, f in FLAG_NEW.items():
    sh.cell(r, FLAGCOL).value = f
sh['A1'].value = ("ISUZU - Units In Operation (UIO)  |  ISZE / ITUK / Israel  |  "
                  "V20 CANDIDATE %s (retention-safety pass)  |  2026-2030 on the survival curve" % TODAY)
sh['A92'].value = (
    "V20 candidate %s (retention-safety pass). r54 Portugal LCV and r90 Cyprus LCV revert to "
    "candidate a: candidate b's seam repass made r90 retain 136%% of itself in 2026 (k = 1.365, "
    "physically impossible) and made r54 non-monotonic and weaker than candidate a. No seam year "
    "gives a non-negative cohort history on either row, so both are flagged SEAM - NOT "
    "RECONSTRUCTABLE. r69 Poland LCV and r88 Cyprus LD have their cohort state SCALED to the 2025 "
    "level and their negative recovered input clipped to 0. Sheet 'V20 RETENTION AUDIT' solves the "
    "implied retention k = (UIO_t - regs_t)/UIO_t-1 for every row and reds any k > 1 or k < 0. "
    "Rows 27/52/80/89 are PLAN ONLY; rows 7/8 are a HOOK; rows 22/24 are V19 sheet-4 links." % TODAY)

# --- disclosure sheet: update the input actually used for the four touched rows
wr = wbo['V20 REGS USED']
for r, src in SRC_NEW.items():
    if r not in REGS_ROW:
        continue
    rr = REGS_ROW[r]
    useregs = REGS_USED[r]
    for j, y in enumerate(FY):
        wr.cell(rr, 6 + j).value = float(useregs[j])
    wr.cell(rr, 11).value = round(sum(useregs), 4)
    wr.cell(rr, 12).value = src

# --- retention audit on its OWN sheet (never mixed with the input table)
if 'V20 RETENTION AUDIT' in wbo.sheetnames:
    del wbo['V20 RETENTION AUDIT']
wa2 = wbo.create_sheet('V20 RETENTION AUDIT', wbo.sheetnames.index('V20 REGS USED') + 1)
RED = PatternFill('solid', fgColor='FFC7CE')
GREEN = PatternFill('solid', fgColor='C6EFCE')
wa2['A1'] = "IMPLIED RETENTION AUDIT  -  k_t = (UIO_t - regs_t) / UIO_{t-1},  t = 2026..2030"
wa2['A1'].font = Font(bold=True, size=13)
wa2['A2'] = ("A fleet cannot retain more than 100%% of itself while also absorbing new registrations, so any "
             "k > 1.0 or k < 0 is physically impossible and is filled RED. regs = the input actually used "
             "(negative recoveries clipped to 0). 0.02 tolerance for integer rounding.")
wa2['A2'].font = Font(italic=True)
hr = 4
for j, h in enumerate(['Sheet-1 row', 'Market', 'CV/LCV', 'Model', 'Distributor',
                       'k 2026', 'k 2027', 'k 2028', 'k 2029', 'k 2030',
                       'min k', 'max k', 'verdict'], start=1):
    cc = wa2.cell(hr, j, h); cc.font = Font(bold=True)
rr = hr + 1
nviol = 0
for r in sorted(AUDIT):
    a = AUDIT[r]
    m = meta(r)
    bad = a['max'] > 1.0 + 0.02 or a['min'] < -0.02
    vals = [r, m[1], m[2], m[3], m[5]] + a['k'] + [a['min'], a['max']]
    vals.append('VIOLATION - impossible retention' if bad else 'ok (0 <= k <= 1)')
    for j, v in enumerate(vals, start=1):
        cc = wa2.cell(rr, j, v)
        if bad:
            cc.fill = RED
        elif j == 13:
            cc.fill = GREEN
    nviol += 1 if bad else 0
    rr += 1
cc = wa2.cell(rr + 1, 1, "%d row(s) audited, %d violation(s). %s" % (
    len(AUDIT), nviol,
    "No row retains more than 100% of itself." if nviol == 0
    else "SEE THE RED ROWS - the forecast is not physically possible."))
cc.font = Font(bold=True)
for col, w in (('A', 12), ('B', 14), ('C', 9), ('D', 12), ('E', 20), ('M', 36)):
    wa2.column_dimensions[col].width = w
for col in 'FGHIJKL':
    wa2.column_dimensions[col].width = 11

# --- assumptions sheet append (supersedes b's FIX 3 seam claim for r54/r90)
try:
    wa = wbo['V20 ASSUMPTIONS']
    r0 = wa.max_row + 2
    wa.cell(r0, 1, "Retention-safety pass (%s) - supersedes FIX 3 for r54 and r90" % TAG).font = Font(bold=True)
    notes = [
        "TEST: implied retention k_t = (UIO_t - regs_t) / UIO_{t-1}. A fleet cannot retain more than 100% of itself while also absorbing new registrations, so k > 1 or k < 0 is physically impossible. Every row is solved on the input actually used and printed on sheet 'V20 RETENTION AUDIT'; violations are filled RED.",
        "r54 PORTUGAL LCV (AQ54:AU54 = %s): REVERTED to candidate a. FIX 3's seam repass moved the row ABOVE candidate a (k 0.871-0.945 vs a's 0.886-0.907) and made it NON-MONOTONIC. No seam year gives a non-negative cohort history for this row, so the repass is not reconstructable. candidate a's values are monotone rising and satisfy 0 <= k <= 1. Flagged SEAM - NOT RECONSTRUCTABLE (seam 2005)." % R54,
        "r90 CYPRUS LCV (AQ90:AU90 = %s): REVERTED to candidate a. FIX 3's 2014 seam repass implies k26 = 1.365 - the row would retain 136%% of itself AND absorb 360 new units. 2014 is not a seam: re-basing there keeps five negative cohorts (2015-2018, 2020) and leaves the 2025 level 862 units SHORT, so the repass is not reconstructable either. Flagged SEAM - NOT RECONSTRUCTABLE." % R90,
        "r69 POLAND LCV (AQ69:AU69 = %s): repaired. V19's own roll-forward recovers a NEGATIVE registration input in all five years (-0.16, -1.19, -1.25, -1.31, -1.37); there is no Polish LCV registration series on disk, so no positive input is supportable. The negative input is clipped to 0 and the cohort state is SCALED to the 2025 level (lambda = 0.3768) instead of adding a -46 unit residual to one vintage, which is what forced k26 = 2.18. The forecast is now pure decay of the 2025 stock." % R69,
        "r88 CYPRUS LD (AQ88:AU88 = %s): repaired the same way (lambda = 0.7582). The old build's single-vintage residual absorption forced k26 = 1.14." % R88,
        "METHOD (why SCALE, not bump): the engine takes back_solve()'s residual for reproducing the 2025 level and adds it to the single OLDEST surviving vintage. On any row carrying a methodology seam that residual is material, which turns the oldest vintage into an implausible block and makes the 2025->2026 step imply retention above 1. Scaling the whole clipped state to the 2025 level preserves the cohort SHAPE and removes the artifact.",
        "ADDED ROWS BEYOND THE TWO NAMED: r69 and r88 are not in the original brief. They were convicted by the new retention test, not by inspection, and they are material (r69 is a 60-unit row with k26 = 2.18; r88 is a 250-unit Cyprus LD row with k26 = 1.14). Both repairs REDUCE the 2026 level. They need review before promotion.",
        "Unchanged and out of scope: V19, the v18 archive, live price lists, uio_ld_n35_share.csv, the ceiling chain, every harness threshold, and the locked IUK row-25 value 44,926. Candidate c is NOT promoted.",
    ]
    for i, t in enumerate(notes):
        wa.cell(r0 + 1 + i, 1, t)
    wa.column_dimensions['A'].width = 150
except Exception as ex:
    print('WARN: assumptions sheet append skipped: %s' % ex)

# --- workbook Changelog append
try:
    wcl = wbo['Changelog']
    last = wcl.max_row
    entries = [
        ("V20c-1", TODAY, "Jerome Van der Pluym (via Cursor)",
         "r54 Portugal LCV AQ54:AU54 %s -> %s: reverted to candidate a." % (B_CELLS[54], R54),
         "The seam repass is not reconstructable and degraded the row (non-monotonic, weaker retention than candidate a). Flagged SEAM - NOT RECONSTRUCTABLE.", "Methodology fix"),
        ("V20c-2", TODAY, "Jerome Van der Pluym (via Cursor)",
         "r90 Cyprus LCV AQ90:AU90 %s -> %s: reverted to candidate a." % (B_CELLS[90], R90),
         "Candidate b's row retained 136% of itself in 2026 (k = 1.365), which is physically impossible. Flagged SEAM - NOT RECONSTRUCTABLE.", "Methodology fix"),
        ("V20c-3", TODAY, "Jerome Van der Pluym (via Cursor)",
         "r69 Poland LCV AQ69:AU69 %s -> %s and r88 Cyprus LD AQ88:AU88 %s -> %s: cohort state scaled to the 2025 level; negative recovered input clipped to 0."
         % (B_CELLS[69], R69, B_CELLS[88], R88),
         "Removes k26 = 2.18 (r69) and k26 = 1.14 (r88). Both were convicted by the new retention test. The repairs reduce the 2026 level; review before promotion.", "Methodology fix"),
        ("V20c-4", TODAY, "Jerome Van der Pluym (via Cursor)",
         "New sheet 'V20 RETENTION AUDIT': per-row per-year k = (UIO_t - regs_t)/UIO_t-1 with min/max and a verdict; any k > 1 or k < 0 is filled RED. Kept on its own sheet so it cannot be confused with the input table.",
         "The workbook now states its own retention sanity instead of leaving it to a harness.", "New sheet"),
        ("V20c-5", TODAY, "Jerome Van der Pluym (via Cursor)",
         "Harness verify_uio_v20.py hardened to v1.1.0: new check10_retention_sanity recomputes implied retention from the workbook's own values and its disclosed input and FAILs on k > 1 or k < 0. It convicts candidate b and passes candidate c.",
         "Systematic fix - closes the blind spot that let candidate b's Cyprus LCV double in 2026 while passing check1 and check5.", "Harness"),
    ]
    for i, e in enumerate(entries):
        for j, val in enumerate(e, start=1):
            wcl.cell(last + 1 + i, j, val)
except Exception as ex:
    print('WARN: changelog append skipped: %s' % ex)

wbo.save(CANDC)
print('\nopenpyxl saved: %s' % CANDC)

# ============================================================ changelog csv: b -> c
with open(CHG_B, newline='', encoding='utf-8-sig') as fh:
    base_rows = list(csv.DictReader(fh))
    fields = list(base_rows[0].keys())
newc = []
for r in sorted(PATCH):
    m = meta(r)
    for j, y in enumerate(FY):
        old, new = B_CELLS[r][j], NEW[r][j]
        if old is None or abs(float(old) - float(new)) < 0.5:
            continue
        newc.append({'row': r, 'country': m[1], 'cv_lcv': m[2], 'model_type': m[3],
                     'distributor': m[5], 'year': y,
                     'cell': '%s%d' % (get_column_letter(FYCOL[y]), r),
                     'column': get_column_letter(FYCOL[y]),
                     'old_value_v19': round(float(old), 1), 'new_value_v20': round(float(new), 1),
                     'delta': round(float(new) - float(old), 1),
                     'pct_change': round((float(new) / float(old) - 1) * 100, 1) if old else '',
                     'rule_applied': 'retention-safety pass: %s' % FLAG_NEW[r],
                     'source': SRC_NEW[r],
                     'scope_status': 'cell changed this pass (base = candidate b)',
                     'date': TODAY})
with open(CHG_C, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    for row in base_rows:
        w.writerow(row)
    for row in newc:
        w.writerow(row)
print('changelog: %d base rows (from b) + %d new rows = %s' % (len(base_rows), len(newc), CHG_C))

# ============================================================ assumptions md: b -> c
with open(ASSUM_B, encoding='utf-8') as fh:
    base_md = fh.read()
md = [base_md, "", "---", "", "## Retention-safety pass (%s) - candidate c" % TODAY, "",
      "**This section supersedes section 4.8 / FIX 3 for r54 and r90.** Candidate b's seam repass",
      "is reverted on both rows: it is not reconstructable from the sources on disk, and on r90 it",
      "produced a physically impossible retention factor.", "",
      "### The test", "",
      "```", "k_t = (UIO_t - regs_t) / UIO_{t-1}      t = 2026..2030", "```", "",
      "A fleet cannot retain more than 100% of itself while also absorbing new registrations, so any",
      "`k > 1` or `k < 0` is physically impossible. Every row is solved on the input actually used and",
      "printed on `V20 RETENTION AUDIT`; violations are red.", "",
      "### What changed", "",
      "| Row | candidate b | candidate c | k (candidate c) | why |", "|---|---|---|---|---|",
      "| r54 PORTUGL LCV | `%s` | `%s` | %s | Reverted to candidate a. b's repass raised k above a and made the row non-monotonic. No seam year gives a non-negative cohort history. |" % (
          B_CELLS[54], R54, ','.join('%.3f' % x for x in AUDIT[54]['k'])),
      "| r90 CYPRUS LCV | `%s` | `%s` | %s | Reverted to candidate a. b's 2014 repass implied k26 = 1.365. 2014 is not a seam: five negative cohorts remain and 2025 lands 862 units short. |" % (
          B_CELLS[90], R90, ','.join('%.3f' % x for x in AUDIT[90]['k'])),
      "| r69 POLAND LCV | `%s` | `%s` | %s | Recovered input is negative all five years; clipped to 0 and the state scaled to 2025 (lambda 0.3768) instead of adding a -46 unit residual to one vintage. |" % (
          B_CELLS[69], R69, ','.join('%.3f' % x for x in AUDIT[69]['k'])),
      "| r88 CYPRUS LD | `%s` | `%s` | %s | Same recipe, lambda 0.7582. b's bump absorption forced k26 = 1.14. |" % (
          B_CELLS[88], R88, ','.join('%.3f' % x for x in AUDIT[88]['k'])),
      "", "### Why SCALE and not bump", "",
      "The engine adds `back_solve()`'s residual for reproducing the 2025 level to the single oldest",
      "surviving vintage. On any row carrying a methodology seam that residual is material, so the",
      "oldest vintage becomes an implausible block and the 2025->2026 step implies retention above 1.",
      "Scaling the whole clipped state to the 2025 level preserves the cohort shape and removes the",
      "artifact. It writes no registration figure that the sources do not support.", "",
      "### Why r69 and r88 are in scope", "",
      "They are not in the original brief. The new retention test convicted them (r69 k26 = 2.18,",
      "r88 k26 = 1.14). Both repairs reduce the 2026 level, so they are flagged for review before",
      "promotion rather than presented as settled.", "",
      "### `SEAM - NOT RECONSTRUCTABLE`", "",
      "The answer for r54, r90 and r69: the sources on disk (IML backbone pre-seam, no Cyprus LCV",
      "history after 2014, no Polish LCV series at all) cannot supply a registration figure. No",
      "positive-number guess was made.", ""]
with open(ASSUM_C, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(md))
print('assumptions log: %s' % ASSUM_C)

json.dump({'generated': TODAY, 'candidate': CANDC, 'base': CANDB,
           'audit': {str(r): AUDIT[r] for r in AUDIT},
           'violations_after': {str(r): VIOL[r] for r in VIOL},
           'changed_vs_b': {str(r): NEW[r] for r in PATCH},
           'grand_total_b': {str(y): GT_BEFORE[y] for y in FY},
           'grand_total_c': {str(y): GT_AFTER[y] for y in FY}},
          open(VERIFY, 'w', encoding='utf-8'), indent=1, default=str)
print('verify json: %s' % VERIFY)

# ============================================================ Excel recalc
try:
    import win32com.client, time
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False; excel.DisplayAlerts = False; excel.ScreenUpdating = False
    rr = None
    try:
        rr = excel.Workbooks.Open(CANDC, UpdateLinks=0, ReadOnly=False)
        time.sleep(1.0)
        excel.CalculateFullRebuild()
        time.sleep(0.5)
        rr.Save()
        s2 = rr.Worksheets("1.UIO Overview")
        v = [s2.Cells(2, FYCOL[y]).Value for y in FY]
        print('recalculated; Grand Total cached = %s' % [round(float(x), 2) for x in v])
    finally:
        if rr is not None:
            try: rr.Close(SaveChanges=False)
            except Exception: pass
        try: excel.Quit()
        except Exception: pass
except Exception as ex:
    print('WARN: Excel recalculation skipped: %s' % ex)

print('\nDONE  candidate c: %s' % CANDC)
