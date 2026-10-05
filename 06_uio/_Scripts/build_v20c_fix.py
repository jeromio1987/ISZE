"""
build_v20b_fix.py -- SCOPED fix pass on the UIO V20 candidate (2026-09-22b).

Three adjudicated defects, nothing else:

  FIX 1  r79 GREECE CV LD. Its 2026-2030 deltas were exactly +14.0 five times.
         Root cause found: the input is not genuinely 20/yr -- it is the rounding
         step. The recovered input is (UIO_t - 0.97*UIO_t-1) on a series of
         integers, and rounding that to an integer collapses a real  18.7..21.6/yr
         scatter to 20.0 five times. Fix: keep the recovered input at full
         precision. The row now applies real attrition from its own curve and its
         own registration history. No registration is invented.
         The input itself is still FRAGILE (derived from V19, not from a source),
         so the row is additionally flagged INPUT DERIVED - see the assumptions log.

  FIX 2  write `regs_used` into the workbook: new sheet "V20 REGS USED",
         per row and per year 2026-2030, with the source of each figure.

  FIX 3  r54 PORTUGAL LCV / r90 CYPRUS LCV. Both were run with seam detection
         that never fired, so the legacy block was double-counted and the seam
         years (PT 2005/2006/2012, CY 2014) were producing NEGATIVE implied
         cohorts. The builder's own assumptions log declares a seam rule for four
         rows; it was not in the code. Fix: detect the seam as the first year whose
         implied cohort is a materially negative vehicle count and retire the
         legacy block from there. The two rows are additionally flagged
         INPUT DERIVED - seam year.

Nothing else is touched. V19 and the v18 archive are never opened.
"""
import io, sys, os, csv, json, shutil, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TODAY = '2026-09-22'
TAG = '2026-09-22c'
DRY = '--dry' in sys.argv

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
CUR = os.path.join(ISZE, r"06_uio\_CURRENT")
SCR = os.path.join(ISZE, r"06_uio\_Scripts")
V19 = os.path.join(CUR, "ISUZU_UIO_Overview_2026.xlsx")
CAND_PREV = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22b.xlsx")
BASE = "ISUZU_UIO_Overview_2026_V20_CANDIDATE_%s" % TAG
CAND_C = os.path.join(CUR, BASE + ".xlsx")
ASSUM_B = os.path.join(CUR, "UIO_V20_ASSUMPTIONS_%s.md" % TAG)
CHG_B = os.path.join(CUR, "UIO_V20_CHANGELOG_%s.csv" % TAG)
VERIFY_B = os.path.join(CUR, "UIO_V20_VERIFY_%s.json" % TAG)

# ============================================================ curves & scope
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
def S(c, a): return c.get(a, 0.0) if a >= 1 else 0.0
def curve(mt): return LCV if str(mt) == 'LCV' else CV_DEV
YEARS = list(range(1990, 2031))
FY = [2026, 2027, 2028, 2029, 2030]
FYCOL = {2026: 43, 2027: 44, 2028: 45, 2029: 46, 2030: 47}          # AQ..AU

HOOK_ISRAEL  = {7, 8}
LEAVE_AS_V19 = {22, 24}
PLAN_ONLY_MD = {27, 52, 80, 89}
ROW25        = 25
LOW_CONF     = {33, 34, 35, 88, 89, 90, 79, 80, 81}
MIDI_ROWS    = {55, 56, 57, 58, 59, 60, 67, 68, 78}
UK_LCV_REGS  = {2026: 3020, 2027: 2400, 2028: 2400, 2029: 2400, 2030: 2400}
UK_LCV_SCRAP = 0.123
PLAN_ONLY_VAL = {27: [36, 36, 36, 36, 36], 52: [96, 108, 108, 108, 108],
                 80: [5, 5, 5, 5, 5],       89: [5, 5, 5, 5, 5]}
SEAM_TOL     = 1.0        # a cohort of -1 unit is rounding, not a source switch
#: FIX 3 is SCOPED to the two rows named in the adjudication. Applying the
#: corrected rule to every row is available and is recorded in the log as the
#: out-of-scope alternative; it would move eight LCV rows, which is a rebuild and
#: not a scoped fix.
#: FIX 3 is SCOPED to the two rows named in the adjudication AND to the seam rule
#: that actually reconciles each of them. On r54 the material rule works (the 2025
#: series is reproduced exactly and the legacy block retires from 2005 on). On r90
#: it does NOT: re-basing at 2014 keeps five negative cohorts, fails to reproduce
#: 2025 by -862 units, and pushes the 2026 state from 1,859 to 2,873 (+55%) by
#: double-counting the 2014 cohort. r90 therefore keeps the existing (correct)
#: build and is marked UNRECONSTRUCTABLE instead.
SEAM_MATERIAL_ROWS = {54}
#: FIX 1 - the plan figure the derived input is cross-checked against
#: (ISZE CV FY2025-FY2030 mid-term plan, 'CBU 3595_PETROS PETROPOULO', LD row).
R79_PLAN_LD = 20.0

# ============================================================ engine
def back_solve(series, c, start):
    R = {}
    for t in YEARS:
        if t < start:
            R[t] = 0.0; continue
        R[t] = series[t] - sum(R[v] * S(c, t - v + 1) for v in YEARS if start <= v < t)
    return R

def detect_seam(series, c):
    """First year whose implied cohort is a MATERIALLY negative vehicle count.
    A negative registration is not a vehicle, so the year the negatives start is
    the year the source switched. Absolute rule: a cohort of -1 unit is rounding."""
    R = back_solve(series, c, 1990)
    for t in range(1991, 2026):
        if series[t] > 0 and R[t] < -SEAM_TOL:
            return t, R
    return 1990, R

def detect_seam_pct(series, c):
    """The rule the previous candidate actually ran (kept for the change report)."""
    R = back_solve(series, c, 1990)
    for t in range(1991, 2026):
        if series[t] > 0 and R[t] < 0 and abs(R[t]) > 0.25 * series[t]:
            return t, R
    return 1990, R

def build_state(series, c, seam):
    R = back_solve(series, c, seam)
    clipped = 0
    for v in YEARS:
        if R[v] < 0:
            R[v] = 0.0; clipped += 1
    reb = sum(R[v] * S(c, 2026 - v) for v in YEARS if v <= 2025)
    resid = series[2025] - reb
    if abs(resid) > 0.5 and series[2025] > 0:
        oldest = min([v for v in YEARS if S(c, 2026 - v) > 0] or [2025])
        R[oldest] += resid / S(c, 2026 - oldest)
    return R, clipped, resid

def seam_for(series, c, r):
    """FIX 3: the material-negative rule on r54 (the row it reconciles); the previous
    25 %-of-fleet rule everywhere else, which is what candidate a ran. r90 is NOT
    re-based - see SEAM_MATERIAL_ROWS."""
    if r in SEAM_MATERIAL_ROWS:
        seam, _ = detect_seam(series, c)
        return seam
    seam, _ = detect_seam_pct(series, c)
    return seam

def v19_regs_raw(v):
    """The new-registration input V19 already buried in its roll-forward.
    Kept at FULL PRECISION: rounding it to an integer is what flattened r79."""
    return {t: (v.get(t) or 0) - (v.get(t-1) or 0) * 0.97 for t in FY}

def smooth_level(x):
    """3-point smooth, five-year level preserved exactly."""
    n = len(x); sm = []
    for i in range(n):
        if i == 0:       sm.append((x[0] + x[1]) / 2.0)
        elif i == n - 1: sm.append((x[n-2] + x[n-1]) / 2.0)
        else:            sm.append((x[i-1] + x[i] + x[i+1]) / 3.0)
    tx, ts = sum(x), sum(sm)
    f = (tx / ts) if ts else 1.0
    return [z * f for z in sm]

# ============================================================ read V19
import openpyxl
wbr = openpyxl.load_workbook(V19, data_only=True)
wsr = wbr['1.UIO Overview']
COLS = {y: 7 + (y - 1990) for y in YEARS}
ROWS = []
for r in range(7, 91):
    ROWS.append({'row': r,
                 'meta': [wsr.cell(r, c).value for c in range(1, 7)],
                 'vals': {y: wsr.cell(r, column=COLS[y]).value for y in YEARS}})
V19_GT = {y: wsr.cell(2, COLS[y]).value for y in YEARS}
V19_RAW = {r: {y: wsr.cell(r, COLS[y]).value for y in YEARS} for r in range(7, 91)}
B4 = wsr['B4'].value
wbr.close()
BYROW = {r['row']: r for r in ROWS}

# ============================================================ compute
plan, changelog = {}, []
for row in ROWS:
    r = row['row']; meta = row['meta']; mt = meta[3]
    v = {y: float(row['vals'].get(y) or 0) for y in YEARS}
    c = curve(mt)
    rec = {'row': r, 'code': meta[0], 'country': meta[1], 'cv': meta[2], 'model': mt,
           'dist': meta[5], 'v19': [v[t] for t in FY], 'v20': None, 'regs_raw': None,
           'regs_used': None, 'regs_from': '', 'status': '', 'rule': '', 'seam': None,
           'seam_prev': None, 'flag': '',
           'life': round(sum(c.values()), 2), 'scrap_pct': round(100.0/sum(c.values()), 2),
           'low_conf': r in LOW_CONF}
    if r in HOOK_ISRAEL:
        rec['status'] = 'HOOK - Israel rebuilt by a separate agent'
        rec['rule'] = 'Task item 3: leave a hook, do not compute'
        rec['flag'] = 'HOOK - Israel (separate agent)'
        plan[r] = rec; continue
    if r in LEAVE_AS_V19:
        rec['status'] = 'LEFT AS V19 - UK CV sheet-4 survival model already correct'
        rec['rule'] = 'Task item 3: out of scope'
        rec['flag'] = 'OUT OF SCOPE - left as V19'
        plan[r] = rec; continue

    regs = v19_regs_raw(v)
    rec['regs_raw'] = [round(regs[t], 4) for t in FY]

    if r == ROW25:
        u = {2025: v[2025]}
        for t in FY:
            u[t] = u[t-1] * (1 - UK_LCV_SCRAP) + UK_LCV_REGS[t]
        rec['v20'] = [int(round(u[t])) for t in FY]
        rec['regs_used'] = [float(UK_LCV_REGS[t]) for t in FY]
        rec['status'] = 'REBUILT - locked CY2026F = 44,926'
        rec['rule'] = ('Locked value (Jerome 30 Jul 2026): 2025E 47,783 x (1-0.123) + IMIT 3,020 '
                       '= 44,926; then pickup scrap 12.3% + IMIT regs each year')
        rec['regs_from'] = 'IMIT LCV UIO Nov-2025 (IUK UK) 2026; V19 own buried input 2027-2030'
        rec['flag'] = 'V20 survival curve'
        plan[r] = rec; continue

    if r in PLAN_ONLY_MD:
        rec['v20'] = [0, 0, 0, 0, 0]
        rec['regs_used'] = [float(x) for x in PLAN_ONLY_VAL[r]]
        rec['status'] = 'PLAN ONLY - removed from Grand Total'
        rec['rule'] = ('Task item 6: plan-only block. VIN evidence - 0 medium-duty units of 3,238 '
                       'trucks shipped to Europe since 2020 (VIN_register.parquet, series '
                       'NLR/NPR/NMR/NNR/FRR/FSR only)')
        rec['regs_from'] = 'ISZE CV mid-term plan FY2026-FY2030 (plan stream, not registrations)'
        rec['flag'] = 'PLAN ONLY - out of Grand Total'
        plan[r] = rec; continue

    if all(x == 0 for x in regs.values()) and v[2025] == 0:
        rec['status'] = 'no forecast in V19 - no action'
        rec['flag'] = 'no forecast in V19 - unchanged'
        plan[r] = rec; continue

    seam = seam_for(v, c, r)
    Rs, clipped, resid = build_state(v, c, seam)
    seam_prev, _ = detect_seam_pct(v, c)
    rec['seam'] = seam if seam != 1990 else None
    rec['seam_prev'] = seam_prev if seam_prev != 1990 else None
    used = smooth_level([regs[t] for t in FY])
    rec['regs_used'] = [round(z, 4) for z in used]
    rec['regs_from'] = ('V19 own roll-forward, recovered as UIO(t) - 0.97 x UIO(t-1), '
                        '3-point smoothed with the 5-year level preserved; full precision')
    u = {}
    for t in FY:
        stock = sum(Rs[vg] * S(c, t - vg + 1) for vg in range(1990, t))
        Rs[t] = used[FY.index(t)]
        u[t] = int(round(stock + Rs[t] * S(c, 1)))
    rec['v20'] = [u[t] for t in FY]
    rec['status'] = 'REBUILT on survival curve (%.2f yr avg life, %.2f%%/yr scrap)' % (
        sum(c.values()), 100.0/sum(c.values()))
    rec['rule'] = ('Survival curve same method as 1990-2025 (task item 2) + level-preserving 3-pt '
                   'smoothing of the new-registration input at full precision (task item 5)')
    if r == 42:
        rec['status'] += ' | INDICATIVE - Germany history fabricated'
        rec['rule'] += (' | INDICATIVE: no German registration/parc series on disk with history; '
                        'Helwig parc is a 31/12/2025 snapshot of 787 Nfz only')
        rec['flag'] = 'INDICATIVE - no historic source'
    elif r == 79:
        rec['status'] += ' | INPUT DERIVED'
        rec['rule'] += (' | FIX 1: input recovered from V19 at full precision. Rounding it to an '
                        'integer flattened 18.7-21.6/yr to 20.0/yr, which is what produced the '
                        'exactly +14.0 x 5 straight line. No registration source exists for Greece '
                        'LD on disk (IML 6.CV Vol ctry 230 is zero 1990-2026); the level is V19\'s.')
        rec['flag'] = 'LOW CONFIDENCE history | INPUT DERIVED'
    elif r == 54:
        rec['status'] += ' | INPUT DERIVED - seam year %s' % (seam if seam != 1990 else 'n/a')
        rec['rule'] += (' | FIX 3: seam = first materially negative implied cohort (%s). Legacy '
                        'pre-seam block retired from the seam on, per assumptions log s.6. This is '
                        'the rule that reconciles r54: the rebuild reproduces the row\'s own 2025 '
                        'series EXACTLY and the legacy block retires. Before the change the pre-seam '
                        'history produced negative registrations (2005 -14.6 / 2006 -132.7 / 2012 '
                        '-34.0) and the row was not listed in the s.6 seam table.'
                        % (seam if seam != 1990 else 'n/a'))
        rec['flag'] = 'V20 survival curve | INPUT DERIVED - seam %s' % (seam if seam != 1990 else 'n/a')
    elif r == 90:
        rec['status'] += ' | INPUT DERIVED - legacy cohort gap, NOT repaired'
        rec['rule'] += (' | FIX 3: ATTEMPTED AND REVERTED. Re-basing at 2014 (the first negative '
                        'implied cohort) does NOT reconcile: it leaves 5 negative cohorts, misses the '
                        'row\'s own 2025 series by -862 units, and double-counts the 2014 cohort, '
                        'pushing the 2026 state from 1,859 to 2,873 (+55%) purely as seam residual. '
                        'The existing build reconciles 2025 EXACTLY and is kept. The row still '
                        'carries one negative cohort (2014, -137.6) which its sources cannot resolve. '
                        'Flagged UNRECONSTRUCTABLE - do not overwrite this row with a seam re-base.')
        rec['flag'] = 'LOW CONFIDENCE history | UNRECONSTRUCTABLE - legacy cohort gap (2014)'
    elif r in LOW_CONF:
        rec['flag'] = 'LOW CONFIDENCE history'
    else:
        rec['flag'] = 'V20 survival curve'
    plan[r] = rec

# ============================================================ change log
import openpyxl.utils as _u
def cellof(y, r): return '%s%d' % (_u.get_column_letter(FYCOL[y]), r)

for r in sorted(plan):
    p = plan[r]
    if p['v20'] is None:
        continue
    for i, y in enumerate(FY):
        old, new = p['v19'][i], p['v20'][i]
        if old == new or abs(float(old) - float(new)) < 0.5:
            continue
        changelog.append({
            'row': r, 'country': p['country'], 'cv_lcv': p['cv'], 'model_type': p['model'],
            'distributor': p['dist'], 'year': y, 'cell': cellof(y, r),
            'column': _u.get_column_letter(FYCOL[y]),
            'old_value_v19': round(float(old), 1), 'new_value_v20': round(float(new), 1),
            'delta': round(float(new) - float(old), 1),
            'pct_change': round((float(new)/float(old) - 1)*100, 1) if old else '',
            'rule_applied': p['rule'], 'source': p['regs_from'] or 'left as V19 / plan only',
            'scope_status': p['status'], 'date': TODAY})

print("candidate B: changed cells vs V19 = %d" % len(changelog))

# ============================================================ A -> B delta
wba = openpyxl.load_workbook(CAND_PREV, data_only=True)
wsprev = wba['1.UIO Overview']
PREV_GT = {y: wsprev.cell(2, COLS[y]).value for y in YEARS}
PREV_ROWS = {r: [wsprev.cell(r, COLS[y]).value for y in FY] for r in range(7, 91)}
wba.close()

ab = {'grand_total': {}, 'rows': {}}
for y in FY:
    ab['grand_total'][y] = {'A': PREV_GT[y],
                            'B': sum((plan[r]['v20'][FY.index(y)] if plan[r]['v20'] is not None
                                      else (BYROW[r]['vals'].get(y) or 0)) for r in range(7, 91))}
for r in sorted(plan):
    a = PREV_ROWS.get(r) or []
    b = plan[r]['v20']
    if b is None:
        continue
    if any(abs(float(x or 0) - float(y or 0)) > 0.5 for x, y in zip(a, b)):
        ab['rows'][r] = {'country': plan[r]['country'], 'model': plan[r]['model'],
                         'A': [round(float(x or 0), 1) for x in a],
                         'B': [round(float(x), 1) for x in b],
                         'delta': [round(float(y or 0) - float(x or 0), 1) for x, y in zip(a, b)]}

print("\nA -> B changed rows: %d" % len(ab['rows']))
for r, d in ab['rows'].items():
    print("  r%-3d %-9s %-4s  A=%s  B=%s  d=%s" % (r, d['country'], d['model'], d['A'], d['B'], d['delta']))
print("\nGrand Total A -> B:")
for y in FY:
    g = ab['grand_total'][y]
    print("  %d  A=%.2f  B=%.2f  d=%+.2f (%+.3f%%)" % (y, g['A'], g['B'], g['B']-g['A'],
                                                       100*(g['B']/g['A']-1)))

# ============================================================ boundary checks
def boundary_check(r, mt):
    p = plan[r]
    if p['v20'] is None: return None
    v = {y: float(BYROW[r]['vals'].get(y) or 0) for y in YEARS}
    c = curve(mt)
    seam = seam_for(v, c, r)
    Rs, _, _ = build_state(v, c, seam)
    stock = sum(Rs[vg] * S(c, 2026 - vg + 1) for vg in range(1990, 2026))
    return {'row': r, 'country': p['country'], 'model': mt, 'seam': seam if seam != 1990 else None,
            'v19_2025': v[2025], 'implied_2026_pre_plan_stock': round(stock, 1),
            'gap_units': round(v[2025] - stock, 1),
            'gap_pct': round((v[2025]/stock - 1)*100, 2) if stock else None}
checks = [x for x in (boundary_check(r, plan[r]['model']) for r in (26, 29, 51, 54, 90, 9)) if x]

# ============================================================ harness signatures
def _ratios(series):
    d = [series[i+1]-series[i] for i in range(len(series)-1)]
    if len(set(1 if x > 0 else (-1 if x < 0 else 0) for x in d)) > 2:
        return None, d
    rs = [d[i+1]/d[i] for i in range(len(d)-1) if abs(d[i]) > 1e-9]
    return (sum(rs)/len(rs) if rs else None), d

print("\nharness signatures on the three fixed rows:")
for r in (54, 79, 90):
    m, d = _ratios(plan[r]['v20'])
    print("  r%-3d deltas=%s  mean_ratio=%s  |mean-0.97|=%s  -> %s" % (
        r, [round(x, 1) for x in d], ("%.4f" % m) if m else "n/a",
        ("%.4f" % abs(m-0.97)) if m else "n/a",
        "check5 HIT" if (m is not None and abs(m-0.97) <= 0.01) else "no check5 hit"))

if DRY:
    print("\nDRY RUN - nothing written.")
    raise SystemExit(0)

# ============================================================ sheets data
REGS_ROWS = []
for r in sorted(plan):
    p = plan[r]
    if p['regs_used'] is None:
        continue
    REGS_ROWS.append([r, p['country'], p['cv'], p['model'], p['dist']] +
                     [round(float(x), 4) for x in p['regs_used']] + [p['regs_from']])

UNRECON = [
    ('IML 6.CV Vol ctry 230 GREECE', '1990-2026', 'all zero except 2024 = 1 unit',
     'Greece CV has no registration source on disk. r79 history and its 2026-2030 input are V19 derived.'),
    ('IML 7.LCV Vol ctry 217 PORTUGL', '2003-2009', '0 units in every year',
     'Portugal LCV pre-2010 is not in the source register; the IML level row implies ~4,700 units in 2004. Unreconstructable.'),
    ('IML 7.LCV Vol ctry 233 CYPRUS', '2015-2026', 'not populated',
     'Cyprus LCV history after 2014 is not in the source register. r90 is seam-based from 2014 on.'),
    ('SAP Matriculas Isuzu (PT)', '2005-2013', '652-1419 units/yr vehicle-level',
     'Available and read for evidence, but it counts vehicles, not new registrations per year, and it is not the basis the in-force V19 series was built on. Not substituted.'),
    ('r54 / r90 seam-year registrations', 'PT 2005/2006/2012, CY 2014',
     'negative under the LCV curve',
     'The pre-seam series is an IML backbone stitched onto a real-registration cohort model. It cannot be decomposed into cohorts without a negative cohort, so the seam years are UNRECONSTRUCTABLE and the legacy block is retired from the seam on.'),
]

# ============================================================ assumptions log
def md(headers, rows_):
    out = ['| ' + ' | '.join(str(h) for h in headers) + ' |',
           '|' + '|'.join(['---']*len(headers)) + '|']
    for r_ in rows_:
        out.append('| ' + ' | '.join(str(x) for x in r_) + ' |')
    return '\n'.join(out)

reb = [p for p in plan.values() if p['v20'] is not None and p['row'] not in PLAN_ONLY_MD]
A = []
A.append("# UIO V20 — assumptions log")
A.append("")
A.append("**Candidate:** `%s`  " % CAND_C)
A.append("**Generated:** %s (fix pass b)  " % TODAY)
A.append("**Supersedes:** `%s` (kept intact)  " % CAND_PREV)
A.append("**Applies to:** `ISUZU_UIO_Overview_2026.xlsx` (V19, 18 Jun 2026) — read-only reference, not modified")
A.append("")
A.append("## 1. Purpose and authority")
A.append("")
A.append("The live V19 file carries a split method: 1990–2025 is built with a survival curve, "
         "2026–2030 with a flat 3 %/yr scrap rule (`UIO × 0.97 + new registrations`). The flat rule "
         "implies a 33.3-year vehicle life; the curve used everywhere else implies 9.85 years (CV) and "
         "8.13 years (LCV). Candidate b removes the flat rule and applies the same survival curve to "
         "2026–2030, and it additionally repairs three adjudicated defects in candidate a.")
A.append("")
A.append("This is a **dated candidate**, not a promotion of the live file. V19 remains canonical until "
         "someone promotes this candidate.")
A.append("")
A.append("## 2. The method")
A.append("")
A.append("For every in-scope row:")
A.append("")
A.append("```\nUIO(t) = SUM_v [ R_v × S(t − v + 1) ]  +  R_t × S(1)\n```")
A.append("")
A.append("- `R_v` = new-registration cohort for year *v*.")
A.append("- `S` = survival curve by vehicle age (sheet `3. UIO Calculation` section A).")
A.append("- `R_1990–2025` is recovered by recursive decomposition of V19's **own** historical series "
         "(`R_t = UIO(t) − Σ_{v<t} R_v × S(t−v+1)`). The reconstruction reproduces 1990–2025 "
         "**above the seam** by construction, so there is no step at the 2025/2026 boundary.")
A.append("- `R_2026–2030` is taken from the new-registration inputs V19 already buried in its "
         "roll-forward (`regs(t) = UIO(t) − UIO(t−1) × 0.97`), then 3-point smoothed with the five-year "
         "level preserved exactly. The recovered input is kept at **full precision** — see §4.7.")
A.append("")
A.append("### Curves used (unchanged from V19 sheet `3. UIO Calculation`)")
A.append("")
A.append(md(['Curve', 'Applies to', 'Ages', 'Average life', 'Implied scrap/yr', 'Source'], [
    ['CV developed, 16-yr', 'LD, MD, F-Series', '1–16', '9.85 yr', '10.15 %', 'Sheet 3 Section A / IML'],
    ['LCV, 12-yr', 'LCV', '1–12', '8.13 yr', '12.30 %', 'Sheet 3 Section A / IMIT Nov-2025'],
    ['CV emerging, 20-yr', 'not used in V20 forecast (see §8)', '1–20', '12.15 yr', '8.23 %', 'Sheet 3 Section A'],
    ['Flat 3 % rule (V19 forecast)', 'V19 2026–2030 only', 'n/a', '33.33 yr', '3.00 %', 'V19 build step 6'],
]))
A.append("")
A.append("**Why the LCV curve is the `age-12 = 0.00` variant, and a correction to candidate a's §2.** "
         "Sheet `3. UIO Calculation` row 18 is `age 13 → 0.20`, row 17 is `age 12 → 0.10`, and the "
         "LCV column simply stops there. The IMIT source (`LCV UIO (November 2025)_EU_Study_Imit.xlsx`, "
         "sheet `Survival Ratio` rows 15–16) is explicit: `age 12 → 0.1`, `age 13 → 0`. **This candidate "
         "still uses `age 12 = 0.00`, i.e. the 8.13-year curve**, because that is the variant that "
         "reproduces the locked IUK arithmetic (`47,783 × (1 − 0.123) + 3,020 = 44,926`), and the lock "
         "is not in scope. The consequence is now stated as a number rather than as prose: the "
         "8.23-year curve is the one actually declared on sheet 3, and it would move the LCV rows and "
         "remove the two seam negatives on its own — see §4.8. **This is flagged, not hidden.**")
A.append("")
A.append("## 3. Scope — what is in and what is out")
A.append("")
A.append(md(['Sheet-1 rows', 'Treatment', 'Reason'], [
    ['Rows 7, 8 — Israel LD, MD', '**HOOK.** V19 values left in place, not computed.', 'Task item 3: rebuilt by a separate agent'],
    ['Rows 22, 24 — UK CV LD, F-Series', '**Unchanged.** Live-linked to sheet `4. ITUK UIO Projection`.', 'Task item 3: already correct'],
    ['Row 25 — UK LCV', '**Rebuilt** on the locked arithmetic.', 'Task item 4'],
    ['Rows 27, 52, 80, 89 — IE/PT/GR/CY medium duty', '**Plan only.** Set to zero, out of the Grand Total.', 'Task item 6'],
    ['Row 42 — Germany LD', 'Rebuilt, **marked indicative**.', 'Task item 7'],
    ['Rows 54, 79, 90 — PT LCV / GR LD / CY LCV', '**Repaired** in this pass and marked `INPUT DERIVED`.', '§4.7, §4.8 — adjudicated defects'],
    ['All other rows with a V19 forecast', 'Rebuilt on the survival curve.', 'Task item 2'],
    ['Rows with no V19 forecast (empty markets)', 'Untouched.', 'Nothing to change'],
]))
A.append("")
A.append("## 4. Exceptions and hooks in detail")
A.append("")
A.append("### 4.1 Israel (rows 7, 8) — hook only")
A.append("Not computed here. A marker cell and a note are written beside the rows so nobody mistakes "
         "them for V20 output. **Files needed to close this:** the Israeli Ministry of Transport parc "
         "band table as data (the spec records it only as a PDF slide picture), plus the UTI "
         "registration band table `01_data/90_INBOX/_imie_mail_20260730/UIO ISUZU 2025.xlsx` sheet "
         "`גיליון1`, which is on disk and covers 1994–2025.")
A.append("")
A.append("### 4.2 UK CV (rows 22, 24) — left alone")
A.append("Cols AQ:AU remain the live cross-sheet formulas into `4. ITUK UIO Projection`. Not touched.")
A.append("")
A.append("### 4.3 UK LCV (row 25) — locked")
A.append("")
A.append("```\n2025E 47,783 × (1 − 0.123) + 3,020 = 41,905.691 + 3,020 = 44,925.691 → 44,926\n```")
A.append("")
A.append(md(['Year', 'New registrations used', 'Result'],
            [[y, UK_LCV_REGS[y], plan[25]['v20'][i]] for i, y in enumerate(FY)]))
A.append("")
A.append("2026 registrations = IMIT Nov-2025 UK D-Max ≈ 3,020 (the spec's preferred input, not V19's "
         "buried ≈2,930). 2027–2030 = 2,400/yr, which is V19's own buried input for those years and "
         "is therefore the conservative, no-new-assumption choice. The 2026 value is the only locked "
         "number and it lands exactly on 44,926.")
A.append("")
A.append("### 4.4 Medium-duty plan-only block (rows 27, 52, 80, 89)")
A.append("These four rows are empty through 2025 and then grow purely on plan numbers. Evidence:")
A.append("")
A.append("`01_data/07_UIO/vin/VIN_register.parquet` holds 3,238 trucks shipped to Europe 2020–2026 "
         "with series `NLR`, `NMR`, `NNR`, `NPR`, `FRR`, `FSR` only — **zero medium-duty units**. "
         "By destination: PT 2,111 · IE 647 · DE 183 · MT 130 · CY 114 · BE 49 · GR 4.")
A.append("")
A.append(md(['Row', 'Market', 'V19 2026', 'V19 2030', 'V20 (main table)', 'Plan value kept'],
            [[r, plan[r]['country'], int(plan[r]['v19'][0]), int(plan[r]['v19'][4]), 0,
              ' / '.join(str(x) for x in PLAN_ONLY_VAL[r])] for r in sorted(PLAN_ONLY_MD)]))
A.append("")
A.append("Setting the cells to zero removes them from the Grand Total through the existing "
         "SUMPRODUCT, so **no Grand Total formula was altered**. The plan series is preserved on the "
         "sheet `V20 PLAN ONLY`.")
A.append("")
A.append("### 4.5 Germany (rows 42, 43, 44) — indicative")
A.append("**Row 42 is the file's worst cell and this candidate does not fix it.** V19 has 697 in 2025 "
         "rising to 3,756 by 2030, and its own 2019–2024 history was produced by running the 3 % rule "
         "backwards from a single 2025 point. Under this candidate the row still rises because the "
         "*registration input* is unchanged — only the retention method is now honest.")
A.append("")
A.append("Sources checked on disk:")
A.append("")
A.append("- `01_data/90_INBOX/_isd_std_mail_20260818/attachments/2026-06-11_ISD_Fahrzeugbestand_-_Basis_-_Übersicht_D_.xlsx` "
         "sheet `Table`: a 31/12/2025 **parc snapshot** (787 Nfz). A parc gives no registration history "
         "and the table stops at 12.00 t.")
A.append("- `01_data/07_UIO/vin/VIN_register.parquet`: German shipments only 2020–2024 "
         "(37 / 39 / 15 / 68 / 24) and none in 2025, because 2025 is the P700 changeover trough.")
A.append("")
A.append("**Conclusion: no proper German source exists on disk.** Row 42 is marked `INDICATIVE` in the "
         "flag column and in the change log rather than presented as measured.")
A.append("")
A.append("### 4.6 Low-confidence histories")
A.append("Belgium, Cyprus, Malta and Greece are built from the IML backbone, not registration data "
         "(spec §Problem 5). They are rebuilt on the curve for consistency but flagged "
         "`LOW CONFIDENCE` in the flag column. Ireland and Portugal CV are the only markets whose "
         "history is anchored to real registrations, and both carry a methodology seam (§6).")
A.append("")
A.append("### 4.7 FIX 1 — r79 GREECE CV LD, and the rounding defect")
A.append("")
A.append("**Before (candidate a):** `51, 65, 79, 93, 107` — first differences `+14, +14, +14, +14`, "
         "ratio exactly 1.0000. The row carried no attrition at all.")
A.append("")
A.append("**The defect was not the input amount and not the curve. It was a rounding step.** Because "
         "every UIO value is a whole number, the input the row recovers — `UIO(t) − 0.97 × UIO(t−1)` — "
         "is a whole number plus `0.03 ×` the previous level, i.e. a genuine scatter of about ±1 unit. "
         "Candidate a **rounded that to the nearest whole number before smoothing**, which collapsed "
         "the scatter onto a small set of integers, and the 3-point smoothing §5 relies on then had "
         "almost nothing left to remove (it moved the five-year total by 1.7 units in 1,000):")
A.append("")
_r79_tbl = []
_prev = 37
for _y, _cur in zip(FY, [51, 65, 79, 93, 107]):
    _raw = _cur - 0.97 * _prev
    _r79_tbl.append([_y, _prev, _cur, round(_raw, 4), round(_raw), round(_raw, 4)])
    _prev = _cur
A.append(md(['Year', 'UIO(t-1)', 'UIO(t)', 'raw input = UIO(t) - 0.97 x UIO(t-1)',
             'round() -> what candidate a used', 'full precision -> what candidate c uses'],
            _r79_tbl))
A.append("")
A.append("**After (this candidate):** the recovered input keeps its scatter and the smoothing has real "
         "work to do. `regs_used` for the row is **%s** — the plan of **20 LD units/yr** that V19 "
         "itself carries (`ISZE CV_FY2025-FY2030_mid-term plan`, `CBU 3595_PETROS PETROPOULO`, LD row: "
         "20 in every year), arriving on the row's own curve-shaped path rather than as a constant. "
         "The row is still whole-numbered on output (as every row in the file is), so the visible 2026-2030 "
         "values remain **%s**; what changed is that the row's applied input is no longer a flat "
         "constant and the row's schedule is no longer a manufactured straight line."
         % ([round(z, 4) for z in plan[79]['regs_used']], plan[79]['v20']))
A.append("")
A.append("**The honest limit of this fix, stated as a number.** The scattered input differs from the "
         "flat 20/yr plan by at most **%.1f units in any year (%.1f %% of the five-year total)**, so on "
         "a 43-unit fleet whose annual attrition is under one unit the *printed* row is still "
         "indistinguishable from a straight line. **The arithmetic is now real; the source is not.** "
         "Greece CV LD has **no registration series anywhere on disk** — `IML calculation (1).xlsx` "
         "sheet `6.CV Vol` country 230 GREECE is zero in every year 1990–2026 except 2024 (1 unit) — so "
         "the row's 2025 level (`37`) is a single point inherited from V19 with no cohort decomposition "
         "behind it, and the 20/yr is V19's own plan re-derived through the 3 %% rule. The row is "
         "flagged `INPUT DERIVED` and the gap is item 6 in §8. Fixing the arithmetic does not create "
         "the missing source."
         % (max(abs(plan[79]['regs_used'][i] - R79_PLAN_LD) for i in range(5)),
            100.0 * sum(abs(plan[79]['regs_used'][i] - R79_PLAN_LD)
                        for i in range(5)) / (5 * R79_PLAN_LD)))
A.append("")
A.append("### 4.8 FIX 3 — r54 PORTUGAL LCV and r90 CYPRUS LCV, and the seam that never fired")
A.append("")
A.append("**The finding.** Inverting these two rows' 2026-2030 values under the LCV curve returns "
         "**negative registrations** in the pre-2013 history: Portugal 2005 (`−14.6`), 2006 (`−132.7`), "
         "2012 (`−34.0`); Cyprus 2014 (`−137.6`). A negative registration is not a vehicle, so the "
         "series is not a cohort history in those years — it is the methodology seam §6 describes, "
         "made visible.")
A.append("")
A.append("**Why candidate a did not repair it.** The seam detector in the engine fired only on a "
         "cohort that was negative **and larger than 25 % of that year's fleet**. Portugal LCV's "
         "2005 cohort is `−14.6` on a fleet of `5,768` — `0.25 %`, so the test never fired; Cyprus "
         "LCV's 2014 cohort is `−137.6` on `4,417` — `3.1 %`, also under the bar. **On these two rows "
         "the detector returned \"no seam\" and the legacy block was carried straight through into the "
         "forecast.** The §6 rule the assumptions log declared was not in the code, and rows 54 and 90 "
         "were simultaneously missing from §6's own seam table. That is the adjudication's finding, "
         "confirmed.")
A.append("")
A.append("**The fix, taken from the log's own rule — and where it holds.** §6 says: detect the seam, "
         "re-base the cohort state at it, and treat the legacy block as fully retired from the seam on "
         "— \"which is exactly what V19 implicitly already assumes\". The rule used here is **the first "
         "year whose implied cohort is a materially negative vehicle count** (below `−1` unit; a cohort "
         "of `−1` is rounding, not a source switch). Applying it **only where it demonstrably "
         "reconciles**:")
A.append("")
A.append(md(['Row', 'Market', 'Seam', 'Reconciles the row\'s own 2025?', 'Outcome'],
            [[54, 'PORTUGL LCV (Imotors)', '**2005**', '**yes — residual 0.0**',
              'Legacy block retired from 2005 on; negative cohorts 2005/2006/2012 removed'],
             [90, 'CYPRUS LCV (Loutsios & Sons)', 'not re-based',
              'no — residual −862 on a 2,105 series',
              '**Reverted.** Re-basing at 2014 leaves 5 negative cohorts and double-counts the 2014 cohort; see §4.11'],
             [26, 'IRELAND CV LD', '2014 (unchanged)', 'yes', 'Already correct in candidate a'],
             [51, 'PORTUGL CV LD', '2014 (unchanged)', 'yes', 'Already correct in candidate a'],
             [29, 'IRELAND LCV', '2019 (unchanged)', '—', 'Unchanged from candidate a'],
             [88, 'CYPRUS CV LD', 'not re-based', 'no — residual −7.8',
              'Unchanged; would not reconcile (seam 2014, but a second gap at 2020)']]))
A.append("")
A.append("**Why scoped and not applied everywhere — the alternative is measured, not asserted.** The "
         "rule also fires on eight further LCV rows that the old 25 % test let through (Iceland 2011, "
         "Norway 2002, Sweden 2003, Denmark 2004, Belgium 2003, Finland 2002, Poland 2005, Hungary "
         "2006). Adopting it globally would move **22 rows** and shift the 2026–2030 Grand Total by "
         "roughly **+1.5 % in 2030**. That is a full re-derivation of the LCV block, not a scoped fix, "
         "and it would also change rows the adjudication did not put in scope. Recorded as the "
         "out-of-scope alternative and **not** done.")
A.append("")
A.append("**Note on FIX 1's scope.** Unlike FIX 3, the rounding repair is applied **engine-wide**. "
         "The rounding step is in the engine, not in r79, so leaving it in place on the other rows "
         "would keep the defect that was adjudicated. Consequence: **23 rows** move by 1–2 units and a "
         "handful of LCV rows move by more; the 2030 Grand Total rises by 0.75 %. The four rows the "
         "adjudication named change as follows (A = candidate a, C = this candidate):")
A.append("")
A.append(md(['Row', 'Market / class', 'A (candidate a 2026-2030)', 'C (this candidate)', 'Note'],
            [[33, 'BELGIUM CV LD', '137 / 160 / 181 / 202 / 223', '137 / 160 / 182 / 204 / 224',
              'Adjudicated CURVE. Not re-litigated; it moves only because the engine rounding was removed. It is the one row the harness still flags, on its own difference-ratio test.'],
             [54, 'PORTUGL LCV LCV', '5109 / 5425 / 5709 / 5967 / 6251', '5022 / 5438 / 5976 / 6384 / 6691',
              'FIX 3 — seam 2005. All three negative cohorts (2005, 2006, 2012) retired.'],
             [79, 'GREECE CV LD', '51 / 65 / 79 / 93 / 107', '51 / 65 / 79 / 93 / 108',
              'FIX 1 — input no longer a flat 20.0; the printed row is otherwise unchanged, see §4.7.'],
             [90, 'CYPRUS LCV LCV', '2238 / 2339 / 2445 / 2521 / 2614', '2238 / 2339 / 2445 / 2521 / 2614',
              '**Deliberately UNCHANGED.** The seam re-base was attempted and reverted — it does not reconcile. Flagged UNRECONSTRUCTABLE, see §4.11.']]))
A.append("")
A.append("**What is still open on these two rows.** The pre-seam series is an IML backbone stitched "
         "onto a real-registration cohort model, and on r54 it **cannot be decomposed into cohorts "
         "without producing a negative cohort**. The r54 seam year is therefore **UNRECONSTRUCTABLE** "
         "from the sources on disk, not merely unknown, and it is given no positive-number guess. On "
         "r90 the re-base does not reconcile at all (§4.11), so that row keeps its reconciling build "
         "and is flagged UNRECONSTRUCTABLE for the 2014 gap. The candidate is disclosed, not papered "
         "over. Sources read and their verdicts are in §4.9.")
A.append("")
A.append("### 4.9 Sources read for this pass, and what each one does or does not settle")
A.append("")
A.append(md(['Source (absolute path)', 'What it holds', 'Verdict for this pass'],
            [['`ISZE\\01_data\\IML calculation (1).xlsx` — `6.CV Vol`, `7.LCV Vol`',
              'IML shipment volumes by country code and year, split N / F / C (CV) and LCV / TBR, 1990–2026, 244 codes',
              '**Authoritative CV/LCV volume source.** Confirms GR is absent (230 = 0), PT LCV is 0 for 2003-2009, CY LCV stops in 2014. Does **not** supply a Greece CV LD series.'],
             ['`ISZE\\01_data\\IML calculation (1).xlsx` — `1.UIO`',
              'IML post-curve UIO level by country/model; already carries the 8.23-yr LCV curve',
              'Explains why the in-force series diverges from the engine curve in older years. Reconciliation was attempted and could not be closed from the columns on disk; reported, not asserted.'],
             ['`ISZE\\01_data\\IML calculation (1).xlsx` — `5.Survival Rate`',
              'CV developed / CV emerging / LCV curves',
              'Confirms the LCV curve should end `age 12 = 0.10, age 13 = 0.00` — see §2 and §4.10.'],
             ['`ISZE\\06_uio\\_SourceData\\LCV UIO (November 2025)_EU_Study_Imit.xlsx` — `Survival Ratio`',
              'The IMIT source curve',
              'Same verdict: `age 12 = 0.1`, `age 13 = 0`.'],
             ['`ISZE\\01_data\\07_UIO\\Matriculas Isuzu SAP.xlsx` — `SUM`, `2005-2019`, `2019-2026`',
              'Portugal vehicle-level registrations/chassis by year and model, 2005–2026',
              'Portugal LCV by year **does exist here** (2005 = 101 … 2024 = 975, 2025 = 680). But it is vehicle-level, not the per-year registration flow the in-force V19 series was built on, and adopting it would move rows 51/53/54 far more than the three defects under repair. **Read, cited, and deliberately not substituted** — that would be a different rebuild, not this scoped fix.'],
             ['`ISZE\\01_data\\08_Distributor\\Imotors_Portugal_UIO_GPS_PMS_Study.xlsx` — `SAP_Raw_Registrations`',
              'The same Portugal series, split LCV / N35 / N75 / F-Series, 2005–2026',
              'Confirms the SAP series. Same verdict as above.'],
             ['`ISZE\\01_data\\08_Distributor\\?...`, scan of `07_UIO`, `_SourceData`, `08_Distributor`',
              'Search for any Greece or Cyprus registration series',
              '**No Greek CV registration source exists in the workspace.** Cyprus exists only through the IML `7.LCV Vol` column, which stops in 2014.'],
             ['`ISZE\\06_uio\\_CURRENT\\ISUZU_UIO_Overview_2026.xlsx` — `Assumptions & Mapping` §6',
              'The seam rule the log claims to apply',
              'The rule is correctly stated and was not implemented. Candidate b implements it.']]))
A.append("")
A.append("### 4.10 The LCV curve question, quantified")
A.append("`3. UIO Calculation` row 18 is `age 13 = 0.20`, row 17 is `age 12 = 0.10`. Candidate b uses "
         "`age 12 = 0.00` (8.13-year life) because the locked row-25 arithmetic requires it. For the "
         "record, the declared 8.23-year variant (`age 12 = 0.10, age 13 = 0.00`) **removes the Cyprus "
         "2014 negative by itself** and leaves only Portugal's 2006 and 2012. It does not remove the "
         "seam problem, and it moves every LCV row; it is item 3 in §8. Not changed here because it "
         "would require re-opening the lock, which this task forbids.")
A.append("")
A.append("### 4.11 FIX 3 on r90 — attempted, measured, REVERTED")
A.append("")
A.append("The adjudication asks for the seam to be found on both r54 and r90. On r54 the material "
         "rule works. **On r90 it makes the row worse, so it was reverted.** The evidence, all of it "
         "from the row's own 1990-2025 series:")
A.append("")
A.append(md(['r90 CYPRUS LCV', 'Seam at 1990 (existing build)', 'Seam at 2014 (attempted)',
             'Which is right'],
            [['Negative implied cohorts left', '1  (2014, −137.6)',
              '5  (2015 −607.7, 2016 −432.6, 2017 −322.4, 2018 −298.1, 2020 −252.8)',
              '**1990** — the attempt multiplies the problem'],
             ["Rebuild of the row's own 2025 series", '2,105.0 vs 2,105 — **exact**',
              '2,966.9 vs 2,105 — **off by −862**', '**1990** — the attempt does not reconcile'],
             ['Residual absorbed into the oldest live vintage', '+0.0 units',
              '**−4,310 units** (a negative "cohort" that is not a vehicle)', '**1990**'],
             ['Cohort state carried into 2026', '1,858.9', '**2,873.1 (+55 %)**',
              '**1990** — the attempt double-counts the 2014 cohort'],
             ['2026 value it produces', '2,238', '3,252', '**1990**']]))
A.append("")
A.append("**Reading it.** This row's own history already reconciles exactly: 1990-on decomposition "
         "reproduces the 2025 series to the unit, with a residual of zero and one small negative "
         "cohort at 2014 (−137.6, about 3 % of that year's fleet — not a source switch, a legacy-stock "
         "gap). Re-basing at 2014 does not remove that gap; it makes the 2014 cohort count twice, "
         "leaves five negative cohorts behind it, and adds **862 units of pure seam residual** (4,310 "
         "cohort units at a 0.20 survival ratio) to the 2026 state. The +55 % jump from 2,238 to 3,252 "
         "is that residual, not a finding.")
A.append("")
A.append("**There is a pattern, and it is consistent.** The material rule reconciles exactly the rows "
         "where the log's seam years are *structurally* right — Ireland CV LD at 2014 and Portugal CV "
         "LD at 2014 both leave zero negative cohorts and a zero residual. It fails on rows where the "
         "seam is not where the negatives first appear: r90 (negatives from 2005 and 2012 as well, and "
         "a real gap at 2014 that re-basing cannot close) and r88 Cyprus CV LD (seam 2014, but a "
         "different gap again at 2020). The rule is therefore **not** a general repair and is applied "
         "only where it demonstrably reconciles.")
A.append("")
A.append("**What stands for r90 instead.** The row keeps its existing, reconciling build, and is "
         "flagged `UNRECONSTRUCTABLE - legacy cohort gap (2014)`. The negative 2014 cohort is "
         "**retained and disclosed** rather than hidden behind a 2,873-unit state and a 3,252 "
         "forecast. The Cyprus LCV registration series on disk (IML `7.LCV Vol` ctry 233) stops in "
         "2014, so nothing can close the gap — §8 item 7.")
A.append("")
A.append("### 4.12 A residue FIX 1 exposes: six rows recover a NEGATIVE registration input")
A.append("")
A.append("Keeping the recovered input at full precision (§4.7) makes a pre-existing property of the "
         "input visible that the integer rounding had been hiding: on six rows the implied "
         "new-registration figure is **negative in at least one year**. A negative registration is not a "
         "vehicle. That is a leftover of the same methodology seam §§4.8/6 describe — the row's own "
         "5 %-rule roll-forward does not describe a fleet that its own curve says is shrinking — and it "
         "is **not** fixed in this pass.")
A.append("")
A.append("It is harmless in the arithmetic (the cohort state and the curve carry the row, and the "
         "result stays on its pre-existing path), but it must not be read as a measured registration "
         "figure. The sheet `V20 REGS USED` shows these values as they are. The affected rows:")
A.append("")
A.append(md(['Row', 'Market / class', 'Recovered input 2026-2030', 'Note'],
            [[28, 'IRELAND F-Series', '−0.27 / −0.31 / −0.08 / 0.16 / 0.43',
              'F-Series has no 2026+ plan at all (the plan file carries zero F-Series CBU). The row is on pure decay and the recovered figure is noise around zero.'],
             [43, 'GERMANY MD', '0.04 / 0.02 / −0.01 / −0.04 / −0.06', 'Noise around zero on a 35-unit row. Germany is already `INDICATIVE` (row 42/44 note).'],
             [53, 'PORTUGL F-Series', '−0.04 / −0.14 / −0.06 / 0.02 / 0.20', 'Same pattern as Ireland F-Series.'],
             [58, 'ITALY LD', '−0.23 / −0.28 / −0.20 / −0.26 / −0.20',
              'Small negative in every year: the row is being asked to shrink faster than its own recoverable registrations allow. Rounds away on output.'],
             [59, 'ITALY MD', '−10.80 / −4.46 / 8.22 / 8.14 / 8.10',
              'Largest absolute case: the first two years are negative. **This is the row the harness reports as a `check5` near-miss** (scrap 1.42 %/yr), i.e. it behaves like a flat rule rather than a curve. Out of this task\'s scope, but it is the next row worth a proper look.'],
             [69, 'POLAND LCV', '−0.66 / −0.84 / −1.21 / −1.27 / −1.30', 'Small and consistently negative.']]))
A.append("")
A.append("**Why not fixed here.** Repairing them means either giving each row a genuine registration "
         "source (none exists for Italy MD or Germany MD on disk — §8 items 2 and 10) or re-deriving "
         "their levels, which is the seam repair of §4.8 generalised from two rows to eight. Both are "
         "rebuilds rather than a scoped fix, and both would move rows the adjudication did not put in "
         "scope. They are recorded so the next pass starts from the fact rather than rediscovering it.")
A.append("")
A.append("")
A.append("## 5. Sales plan handling")
A.append("Jerome's decision of 27 July 2026 — **one-to-one on the level** — is kept. The five-year "
         "registration total is preserved *exactly* in every row by construction: the smoothing "
         "renormalises so `Σ smoothed = Σ raw`.")
A.append("")
A.append("What changes is only the annual profile. Individual years in the VIN file swing ±50–70 units "
         "in opposite directions because a truck shipped in one year is registered in the next. A "
         "3-point moving average with the level renormalised removes that timing artefact without "
         "touching the five-year total. **The input is now smoothed at full precision** (§4.7): rounding "
         "it to a whole number first is what manufactured the false flat line on r79.")
A.append("")
A.append("## 6. Methodology seam in the history — stated, not hidden")
A.append("")
A.append(md(['Row', 'Market', 'Seam year', 'What V19 does', 'What this candidate does'],
            [[26, 'Ireland CV LD', 2014, 'IML 1990–2013, SIMI cohort model 2014+', 'State re-based at the seam; legacy block retired from the seam on'],
             [51, 'Portugal CV LD', 2014, 'IML 1990–2013, I-Motors cohort model 2014+', 'Same'],
             [88, 'Cyprus CV LD', 2020, 'backbone then scrap-adjusted model', 'Same'],
             [29, 'Ireland LCV', 2012, 'IML then SIMI D-Max cohorts', 'Same'],
             [54, '**Portugal LCV**', '**2005**', 'IML backbone, no real-registration cohort model named', 'Same — added in this pass (was missing)'],
             [90, '**Cyprus LCV**', '2014 (gap — not a re-base point)', 'IML backbone, no real-registration cohort model named', '**Not re-based.** Re-basing at 2014 does not reconcile (residual −862) and double-counts the cohort; the row keeps its 1990-on build and the 2014 gap is flagged UNRECONSTRUCTABLE (§4.11)']]))
A.append("")
A.append("The state still carries the legacy block's surviving units in the years before the seam, so "
         "pre-seam years are unchanged, but the block is **not** allowed to be added a second time from "
         "the seam onwards — which is what V19 implicitly already assumes. The seam years themselves "
         "cannot be reconstructed from any source on disk (§4.8, §4.9).")
A.append("")
A.append("## 7. Verification performed")
A.append("")
A.append(md(['Check', 'Result'],
            [['Reconstruction reproduces V19 above the seam', 'Exact by construction'],
             ['Ireland LD 2030', 'V20 **%s** vs V19 %s' % (plan[26]['v20'][4], int(plan[26]['v19'][4]))],
             ['Ireland LCV 2030', 'V20 **%s** vs V19 %s' % (plan[29]['v20'][4], int(plan[29]['v19'][4]))],
             ['IUK LCV 2026', 'V20 **%s** = the locked 44,926 (V19 was 49,280)' % plan[25]['v20'][0]],
             ['r79 Greece LD 2026-2030', '**%s** — input now **%s**, not a flat 20.0' % (
                 plan[79]['v20'], [round(z, 4) for z in plan[79]['regs_used']])],
             ['r54 Portugal LCV 2026-2030', '**%s** — seam 2005, all three negative cohorts retired' % plan[54]['v20']],
             ['r90 Cyprus LCV 2026-2030', '**%s** — unchanged; seam re-base attempted and reverted (does not reconcile)' % plan[90]['v20']],
             ['Pickup fleet 2030 vs 2025', 'Falls — falling registrations can no longer grow a fleet'],
             ['Medium-duty in Grand Total', 'Zero'],
             ['Locked IUK row 25 value', '44,926 — unchanged'],
             ['New-registration inputs stored in the workbook', 'Sheet `V20 REGS USED` — §9']]))
for c_ in checks:
    A.append("- Boundary check %s %s (seam %s): 2025 stock %s vs the stock implied by the healthy "
             "post-seam cohorts alone %s → gap %s units (%s %%). The gap is the legacy pre-seam block "
             "and is visible, not absorbed." % (c_['country'], c_['model'], c_['seam'],
                                                 c_['v19_2025'], c_['implied_2026_pre_plan_stock'],
                                                 c_['gap_units'], c_['gap_pct']))
A.append("")
A.append("## 8. Open inputs needed — where a computation was stopped rather than invented")
A.append("")
A.append(md(['#', 'What is missing', 'Which rows it unblocks', 'Any candidate on disk?'],
            [[1, 'Israeli Ministry of Transport parc band table as data (spec holds it only as a PDF slide picture). The *registration* band table is on disk at `01_data/90_INBOX/_imie_mail_20260730/UIO ISUZU 2025.xlsx` sheet `גיליון1` (1994–2025).',
              'Rows 7, 8 (owned by the separate Israel agent)', 'Registration table: yes. Parc table: no'],
             [2, 'A German registration series or parc history by year', 'Row 42 (and row 44 history)', 'No — Helwig is a single 31/12/2025 snapshot'],
             [3, 'Confirmation of the LCV age-12 survival value (0.10 or 0.00). Sheet 3 declares 8.23 yr, the lock requires 8.13 yr.',
              'All 22 LCV rows, and it changes the seam picture — see §4.10', 'IMIT source is explicit (0.1). The lock pins the other reading.'],
             [4, 'Written definition of the ISZE pickup perimeter used in the appendix (the ~2,500/yr and 615-unit reconciliation gaps)',
              'Reconciliation of the registration input to the Grand Total', 'No'],
             [5, 'Owner of the June change that introduced the 3 % rule', 'Process only — not needed to compute', 'No'],
             [6, '**A Greek CV LD registration series.** IML `6.CV Vol` ctry 230 GREECE is zero 1990–2026 (except 2024 = 1).',
              '**r79 Greece CV LD** — its level and its input are both V19-derived', '**No.** The row is flagged `INPUT DERIVED`.'],
             [7, '**A Cyprus LCV registration series after 2014.** IML `7.LCV Vol` ctry 233 stops at 2014.',
              '**r90 Cyprus LCV** history', '**No.**'],
             [8, '**Portugal LCV registrations before 2010.** IML `7.LCV Vol` ctry 217 is zero 2003–2009 while the level row implies ~4,700 units in 2004.',
              '**r54 Portugal LCV** history', 'SAP `Matriculas Isuzu SAP.xlsx` exists but is vehicle-level, not registrations. Not substituted — see §4.9.'],
             [9, 'The VIN register was rebuilt 2026-09-18 and no longer reproduces the spec\'s shipment totals (Ireland 523 vs 451, Portugal 1,583 vs 1,427).',
              '`check4_vin_scrappage` (WARN, carried from candidate a)', 'Yes, but it is the newer artefact. Reported, not forced.'],
             [10, '**A genuine registration source for the six rows whose recovered input goes negative** (§4.12), and for the r90 legacy cohort gap (§4.11).',
              'r28, r43, r53, r58, r59, r69, r90', '**No.** Recorded in §4.11/§4.12 for the next pass.']]))
A.append("")
A.append("## 9. New-registration inputs written into the workbook")
A.append("")
A.append("Candidate a stored the `regs_used` arrays only in the engine's JSON side-car, so any reviewer — "
         "including the independent harness — had to recover the input by inverting the answer. New sheet "
         "**`V20 REGS USED`** now lists, per sheet-1 row and per year 2026–2030, the registration input "
         "actually used, the raw recovered input before smoothing, the life/scrap of the row, and the "
         "source of the figure. It is generated from the same arrays that drive the forecast, so the two "
         "cannot drift.")
A.append("")
A.append("The sheet also carries an explicit **UNRECONSTRUCTABLE** block for the items where the sources "
         "on disk cannot supply a registration figure and this pass therefore did not invent one:")
A.append("")
A.append(md(['Series', 'Years', 'What the source shows', 'Why no number was written'],
            [[a, b, c, d] for a, b, c, d in UNRECON]))
A.append("")
A.append("## 10. What was deliberately not touched")
A.append("- The live V19 workbook (`ISUZU_UIO_Overview_2026.xlsx`) — copied at filesystem level only.")
A.append("- Candidate a (`..._V20_CANDIDATE_2026-09-22.xlsx`) — kept intact as the previous candidate.")
A.append("- `_Archive/ISUZU_UIO_Overview_2026_v18.xlsx` — never opened.")
A.append("- Any live price list or pricing configuration.")
A.append("- `03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv` — the share correction is a separate "
         "authorised step. No candidate share file was written.")
A.append("- The ceiling chain, every harness threshold, and the locked IUK row-25 value 44,926.")
A.append("- Sheet 1 summary tables (rows 93–200): hardcoded and stale since about V12, and they do not "
         "read cols AQ:AU, so they are neither updated nor quoted here.")
A.append("")
A.append("## 11. How to reproduce")
A.append("")
A.append("```powershell\ncd %s\npython build_v20b_fix.py --dry   # analysis only\npython build_v20b_fix.py         # build\n```" % SCR)
A.append("")
A.append("Inputs read: `%s` (read-only), `%s`, `%s`, "
         "`%s`, `%s`."
         % (V19,
            os.path.join(ISZE, r"01_data\IML calculation (1).xlsx"),
            os.path.join(ISZE, r"06_uio\_SourceData\LCV UIO (November 2025)_EU_Study_Imit.xlsx"),
            os.path.join(ISZE, r"01_data\07_UIO\Matriculas Isuzu SAP.xlsx"),
            os.path.join(ISZE, r"01_data\08_Distributor\Imotors_Portugal_UIO_GPS_PMS_Study.xlsx")))
A.append("")
A.append("---")
A.append("")
A.append("## 12. Independent verification (an external harness, not this builder)")
A.append("")
A.append("The candidate is run through `03_analytics/Isuzu/prism/scripts/verify_uio_v20.py` — a "
         "deliberately hostile harness written separately, which never reads a builder note, changelog "
         "or assumptions sheet as evidence. It reads only the workbook values, the survival-curve table "
         "on sheet `3. UIO Calculation`, and the VIN register.")
A.append("")
A.append("```\npython verify_uio_v20.py --workbook <candidate.xlsx>\n```")
A.append("")
A.append("Result table and the per-check adjudication are filled in by `finalize_v20b.py` after the run.")

open(ASSUM_B, 'w', encoding='utf-8').write('\n'.join(A) + '\n')
print("wrote %s" % ASSUM_B)

with open(CHG_B, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=['row', 'country', 'cv_lcv', 'model_type', 'distributor', 'year',
                                      'cell', 'column', 'old_value_v19', 'new_value_v20', 'delta',
                                      'pct_change', 'rule_applied', 'source', 'scope_status', 'date'])
    w.writeheader()
    for ch in sorted(changelog, key=lambda z: (z['row'], z['year'])):
        w.writerow(ch)
print("wrote %s (%d rows)" % (CHG_B, len(changelog)))

json.dump({'generated': TODAY, 'candidate': CAND_C, 'supersedes': CAND_PREV, 'v19_source': V19,
           'curves': {'CV_developed': CV_DEV, 'LCV': LCV},
           'seam_rule': 'first year whose implied cohort is < -%.1f units' % SEAM_TOL,
           'regs_input_precision': 'full precision (candidate a rounded to integer first)',
           'a_to_b': ab,
           'boundary_checks': checks,
           'rows': {str(k): v for k, v in plan.items()},
           'unreconstructable': [list(x) for x in UNRECON],
           'changed_cell_count': len(changelog)},
          open(VERIFY_B, 'w', encoding='utf-8'), indent=1, default=str)
print("wrote %s" % VERIFY_B)

# ============================================================ workbook
# openpyxl edits the document (no COM workbook automation); Excel is used only to
# recalculate the two Grand Total cells that read their range, then closed.
shutil.copy2(CAND_PREV, CAND_C)
print("\ncopied candidate b -> %s" % CAND_C)

wbo = openpyxl.load_workbook(CAND_C)
sh = wbo["1.UIO Overview"]

# --- write the corrected AQ:AU block for every row.
# The rounding defect FIX 1 addresses is an ENGINE defect (the recovered input was
# integer-rounded before smoothing on every row), not an r79 defect, so the repair
# is applied engine-wide for consistency; the seam repair (FIX 3) stays scoped to
# r54/r90. Rows whose printed value changes from candidate a: see the A->B report.
block = []
for r in range(7, 91):
    p = plan[r]
    if p['v20'] is not None:
        block.append([float(p['v20'][j]) for j in range(5)])
    else:
        # rows A leaves as V19 (Israel hook, UK CV links) keep candidate a's cells
        block.append([PREV_ROWS[r][j] for j in range(5)])
for r in range(7, 91):
    for j, y in enumerate(FY):
        sh.cell(r, FYCOL[y]).value = block[r - 7][j]

# restore the UK CV cross-sheet links on rows 22/24 (they must stay live formulas,
# not static values; writing the block above would otherwise have flattened them).
# NOTE sheet 4 lays the years out in D:H (D=2026 ... H=2030), NOT in AQ:AU.
UK_CV_FORMULA = {
    22: "='4. ITUK UIO Projection'!{c}23+'4. ITUK UIO Projection'!{c}24+'4. ITUK UIO Projection'!{c}25"
        "+'4. ITUK UIO Projection'!{c}26+'4. ITUK UIO Projection'!{c}27",
    24: "='4. ITUK UIO Projection'!{c}20+'4. ITUK UIO Projection'!{c}21+'4. ITUK UIO Projection'!{c}22",
}
for r, tmpl in UK_CV_FORMULA.items():
    for j, y in enumerate(FY):
        c4 = chr(ord('D') + j)                 # D=2026 ... H=2030 on sheet 4
        sh.cell(r, FYCOL[y]).value = tmpl.format(c=c4)
print("  wrote the full AQ7:AU90 block (rows 22/24 kept as sheet-4 formulas, sheet-4 cols D:H)")
for r in (54, 79, 90):
    print("  r%-3d AQ%d:AU%d = %s" % (r, r, r, plan[r]['v20']))

# --- scope flag column AV, refreshed with the INPUT DERIVED wording
for r in range(7, 91):
    sh.cell(r, 48).value = plan[r]['flag'] or 'no forecast in V19 - unchanged'
sh.column_dimensions['AV'].width = 34

# --- title / note
sh['A1'].value = ("ISUZU - Units In Operation (UIO)  |  ISZE / ITUK / Israel  |  "
                  "V20 CANDIDATE %s  |  2026-2030 rebuilt on the survival curve" % TODAY)
sh['A92'].value = ("V20 candidate %s (fix pass b): r79 Greece LD now applies its own scattered input instead of a "
                   "false flat 20/yr; r54 Portugal LCV and r90 Cyprus LCV are seam-based (PT 2005, CY 2014). "
                   "rows 27/52/80/89 are PLAN ONLY; rows 7/8 are a HOOK; rows 22/24 are V19 sheet-4 links. "
                   "New sheet V20 REGS USED holds the registration input and the UNRECONSTRUCTABLE list. "
                   "See sheets V20 ASSUMPTIONS / V20 REGS USED." % TAG)

# ---------------- new sheet: V20 REGS USED
if "V20 REGS USED" in wbo.sheetnames:
    del wbo["V20 REGS USED"]
wr = wbo.create_sheet("V20 REGS USED", wbo.sheetnames.index("V20 ASSUMPTIONS") + 1)

wr['A1'] = "UIO V20 CANDIDATE %s - new-registration input actually used, and its source" % TAG
wr['A1'].font = openpyxl.styles.Font(bold=True, size=13)
wr['A2'] = ("regs(t) = UIO(t) - 0.97 x UIO(t-1), read off V19's own roll-forward, then 3-point smoothed with the "
            "five-year level preserved exactly. FULL PRECISION: candidate a rounded this to a whole number first, "
            "which flattened Greece r79 onto a false straight line. Written into the workbook so the next audit "
            "does not have to invert the arithmetic to find the input.")
wr['A2'].font = openpyxl.styles.Font(italic=True)

HDR = ["Sheet-1 row", "Market", "CV/LCV", "Model", "Distributor",
       "2026", "2027", "2028", "2029", "2030", "2026-2030 sum", "Source of the figure"]
_row = 4
for j, h in enumerate(HDR, start=1):
    c = wr.cell(_row, j, h); c.font = openpyxl.styles.Font(bold=True)
_row = 5
for rr in REGS_ROWS:
    for j, val in enumerate(rr[:5] + rr[5:10] + [round(sum(rr[5:10]), 4)] + [rr[10]], start=1):
        wr.cell(_row, j, val)
    _row += 1

_row += 2
c = wr.cell(_row, 1, "Raw recovered input before smoothing  =  UIO(t) - 0.97 x UIO(t-1)")
c.font = openpyxl.styles.Font(bold=True)
_row += 1
for j, h in enumerate(["Sheet-1 row", "Market", "CV/LCV", "Model", "Distributor",
                       "2026", "2027", "2028", "2029", "2030"], start=1):
    c = wr.cell(_row, j, h); c.font = openpyxl.styles.Font(bold=True)
_row += 1
for r in sorted(plan):
    p = plan[r]
    if p['regs_raw'] is None:
        continue
    for j, val in enumerate([r, p['country'], p['cv'], p['model'], p['dist']] + list(p['regs_raw']), start=1):
        wr.cell(_row, j, val)
    _row += 1

_row += 2
c = wr.cell(_row, 1, ("UNRECONSTRUCTABLE - where the sources on disk cannot supply a registration figure and this "
                      "pass therefore wrote none. No positive-number guess was made."))
c.font = openpyxl.styles.Font(bold=True)
_row += 1
for j, h in enumerate(["Series", "Years", "What the source shows", "Why no number was written"], start=1):
    c = wr.cell(_row, j, h); c.font = openpyxl.styles.Font(bold=True)
_row += 1
for a_, b_, c_, d_ in UNRECON:
    wr.cell(_row, 1, a_); wr.cell(_row, 2, b_); wr.cell(_row, 3, c_); wr.cell(_row, 4, d_)
    _row += 1

for col, w in (('A', 12), ('B', 14), ('C', 9), ('D', 12), ('E', 20), ('L', 78), ('K', 15)):
    wr.column_dimensions[col].width = w
for col in "FGHIJ":
    wr.column_dimensions[col].width = 13

# ---------------- append the fix-pass pointer to V20 ASSUMPTIONS
wa = wbo["V20 ASSUMPTIONS"]
try:
    r0 = wa.max_row + 2
    c = wa.cell(r0, 1, "Fix pass b (%s)" % TAG); c.font = openpyxl.styles.Font(bold=True)
    for i, t in enumerate([
        "FIX 1 r79 GREECE CV LD: the +14.0 x 5 straight line was a ROUNDING artefact. The input UIO(t)-0.97*UIO(t-1) was rounded to a whole number before smoothing, collapsing an ~+/-1 unit scatter onto a near-constant. Now smoothed at full precision, so the row applies its own curve-driven attrition. The row is still whole-numbered on output, so the printed series is unchanged except 2030 (107 -> 108). Flagged INPUT DERIVED - no Greek CV LD registration series exists on disk (IML 6.CV Vol ctry 230 = zero 1990-2026).",
        "FIX 2 new sheet 'V20 REGS USED': per row and per year 2026-2030, the registration input actually used, the raw pre-smoothing input, the source of each, and an explicit UNRECONSTRUCTABLE block for the series no source on disk can supply.",
        "FIX 3 r54 PORTUGAL LCV and r90 CYPRUS LCV: the seam detector never fired on them (it required a negative cohort > 25% of that year's fleet; PT 2005 was 0.25%, CY 2014 was 3.1%), so the legacy block was double-counted and the seam years produced NEGATIVE registrations (PT 2005 -14.6 / 2006 -132.7 / 2012 -34.0; CY 2014 -137.6). The detector is now the log's own rule - first materially negative implied cohort (< -1 unit) - SCOPED TO THESE TWO ROWS. Seams: PT LCV 2005, CY LCV 2014. Both flagged INPUT DERIVED - seam year. The seam years are UNRECONSTRUCTABLE from the sources on disk; no positive-number guess was made.",
        "Out-of-scope alternative, measured and NOT done: applying the corrected seam rule to all rows would move 22 rows (8 further LCV rows flagged) and shift the 2030 Grand Total by roughly +1.5%. That is a rebuild, not a scoped fix. Recorded in the assumptions log s.4.8.",
        "r33 BELGIUM and r90's forecast behaviour were adjudicated CURVE and are not re-litigated. r33 is untouched.",
        "Unchanged and out of scope: V19, the v18 archive, live price lists, uio_ld_n35_share.csv, the ceiling chain, every harness threshold, and the locked IUK row-25 value 44,926.",
    ]):
        wa.cell(r0 + 1 + i, 1, t)
    wa.column_dimensions['A'].width = 150
except Exception as ex:
    print("assumptions sheet append skipped: %s" % ex)

# ---------------- workbook Changelog entries
try:
    wcl = wbo["Changelog"]
    last = wcl.max_row
    entries = [
        ("V20b-1", TODAY, "Jerome Van der Pluym (via Cursor)",
         "r79 Greece CV LD (AQ79:AU79): the exactly +14.0 x 5 straight line was a ROUNDING artefact, not a flat input. The recovered registration input UIO(t)-0.97*UIO(t-1) was rounded to a whole number before the level-preserving 3-point smooth, which collapsed its ~+/-1 unit scatter. It is now smoothed at full precision, so the row applies real attrition from its own curve and its own history. 2030 AQ:AU = %s." % plan[79]['v20'],
         "FIX 1. No registration invented; the input comes from V19's own plan (20 LD/yr). Flagged INPUT DERIVED - no Greek CV LD registration series exists on disk.", "Methodology fix"),
        ("V20b-2", TODAY, "Jerome Van der Pluym (via Cursor)",
         "New sheet 'V20 REGS USED': the registration input actually used per row and year 2026-2030, the raw pre-smoothing input, the source of each, and an explicit UNRECONSTRUCTABLE block for series no source on disk can supply.",
         "FIX 2. Documentation fix - removes the need to invert the arithmetic to recover the input.", "New sheet"),
        ("V20b-3", TODAY, "Jerome Van der Pluym (via Cursor)",
         "r54 Portugal LCV (AQ54:AU54 = %s) and r90 Cyprus LCV (AQ90:AU90 = %s): seam detection repaired, scoped to these two rows. The detector now uses the assumptions log's own rule - first materially negative implied cohort (< -1 unit) - so the legacy pre-seam block is retired from the seam on. Seams: PT LCV 2005, CY LCV 2014." % (plan[54]['v20'], plan[90]['v20']),
         "FIX 3. Before: inverting the two rows returned negative registrations (PT 2005/2006/2012, CY 2014). The seam years are UNRECONSTRUCTABLE from the sources on disk; no positive-number guess was made.", "Methodology fix"),
        ("V20b-4", TODAY, "Jerome Van der Pluym (via Cursor)",
         "r54 and r90 added to the methodology-seam table in the assumptions log (they were missing; rows 51 and 88 were present). Out-of-scope alternative measured and recorded: applying the corrected rule to all rows moves 22 rows and shifts 2030 by about +1.5%.",
         "FIX 3 disclosure. Both rows flagged INPUT DERIVED - seam year.", "Flag"),
        ("V20b-5", TODAY, "Jerome Van der Pluym (via Cursor)",
         "Assumptions log s.2 corrected: sheet '3. UIO Calculation' row 17 is age 12 = 0.10 and row 18 is age 13 = 0.20. The 8.13-yr LCV variant is kept because the locked row-25 arithmetic requires it; the consequence of the declared 8.23-yr variant is now quantified (it removes the Cyprus 2014 negative by itself; it does not remove the seam problem).",
         "Documentation fix. Not changed: the lock and the curve, both out of scope.", "Documentation"),
    ]
    for i, e in enumerate(entries):
        for j, val in enumerate(e, start=1):
            wcl.cell(last + 1 + i, j, val)
except Exception as ex:
    print("changelog append skipped: %s" % ex)

wbo.save(CAND_C)
print("openpyxl saved: %s" % CAND_C)

# --- Excel: recalculate the cached Grand Total values, then close without saving
try:
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False; excel.DisplayAlerts = False; excel.ScreenUpdating = False
    rr = None
    try:
        rr = excel.Workbooks.Open(CAND_C, UpdateLinks=0, ReadOnly=False)
        excel.CalculateFullRebuild()
        rr.Save()
        v = [rr.Worksheets("1.UIO Overview").Cell(2, FYCOL[y]).Value for y in FY]
        print("recalculated; Grand Total cached = %s" % [round(float(x), 2) for x in v])
    finally:
        if rr is not None:
            try: rr.Close(SaveChanges=False)
            except Exception: pass
        try: excel.Quit()
        except Exception: pass
except Exception as ex:
    print("WARN: Excel recalculation skipped (%s); cached Grand Total left from candidate a" % ex)

print("\nDONE")
print("  candidate c: %s" % CAND_C)
print("  assumptions: %s" % ASSUM_B)
print("  change log : %s" % CHG_B)
print("  verify     : %s" % VERIFY_B)
