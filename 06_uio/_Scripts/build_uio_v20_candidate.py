"""
build_uio_v20_candidate.py  --  UIO V20 forecast engine rebuild.

Builds a DATED V20 CANDIDATE workbook beside the live V19 file, plus an
assumptions log, a cell-level change log, and a verification JSON.

V19 is copied at the filesystem level only (shutil) and is never opened.
Archived v18 is never opened. No price list, pricing config, leakage pack or
the PRISM uio_ld_n35_share.csv is touched.

METHOD (replaces the flat 3%/yr scrap rule in cols AQ:AU, 2026F-2030F)
    UIO(t) = SUM_v [ R_v * S(t - v + 1) ]   +   R_t * S(1)
    R_v      = new-registration cohort for year v
    S        = survival curve, same as already used for 1990-2025
               CV developed 16-yr (LD / MD / F-Series) | LCV 12-yr (LCV rows)
    R_1990-2025 recovered by recursive decomposition of V19's own history, so the
               reconstruction reproduces 1990-2025 by construction -> no step at
               the 2025/2026 boundary.
    R_2026-2030 taken from the new-registration inputs V19 already buried in its
               roll-forward (regs[t] = UIO[t] - UIO[t-1]*0.97), then 3-point
               smoothed with the five-year level preserved exactly, so the level
               stays one-to-one (Jerome 27 Jul 2026) while the single-year
               shipment-to-registration timing artefact is removed.

USAGE
    python build_uio_v20_candidate.py --dry     analyse only, write nothing
    python build_uio_v20_candidate.py           build everything
"""
import io, sys, os, csv, json, shutil, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DRY = '--dry' in sys.argv
TODAY = '2026-09-22'

CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
V19 = os.path.join(CUR, "ISUZU_UIO_Overview_2026.xlsx")
BASE = "ISUZU_UIO_Overview_2026_V20_CANDIDATE_%s" % TODAY
CAND = os.path.join(CUR, BASE + ".xlsx")
ASSUM_MD = os.path.join(CUR, "UIO_V20_ASSUMPTIONS_%s.md" % TODAY)
CHG_CSV = os.path.join(CUR, "UIO_V20_CHANGELOG_%s.csv" % TODAY)
VERIFY = os.path.join(CUR, "UIO_V20_VERIFY_%s.json" % TODAY)
SCRATCH = os.path.join(CUR, "_v20_intermediate.json")
SCRIPT_DIR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts"

# ============================================================ curves & scope
CV_DEV = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.80,9:0.70,10:0.55,
          11:0.40,12:0.30,13:0.20,14:0.10,15:0.05,16:0.00}
LCV = {1:1.00,2:0.98,3:0.95,4:0.92,5:0.89,6:0.84,7:0.80,8:0.65,9:0.50,10:0.40,11:0.20,12:0.00}
CV_EMG_SRC = {1:1.00,2:0.99,3:0.98,4:0.97,5:0.96,6:0.95,7:0.90,8:0.85,9:0.80,10:0.75,
              11:0.70,12:0.60,13:0.50,14:0.40,15:0.30,16:0.20,17:0.15,18:0.10,19:0.05,20:0.00}
def S(c, a): return c.get(a, 0.0) if a >= 1 else 0.0
def curve(mt): return LCV if str(mt) == 'LCV' else CV_DEV
YEARS = list(range(1990, 2031))
FY = [2026, 2027, 2028, 2029, 2030]
FYCOL = {2026: 43, 2027: 44, 2028: 45, 2029: 46, 2030: 47}     # AQ..AU

HOOK_ISRAEL   = {7, 8}
LEAVE_AS_V19  = {22, 24}
PLAN_ONLY_MD  = {27, 52, 80, 89}
ROW25         = 25
MIDI_ROWS     = {55, 56, 57, 58, 59, 60, 67, 68, 78}
LOW_CONF      = {33, 34, 35, 88, 89, 90, 79, 80, 81}            # BE CY GR MT CV history
UK_LCV_REGS   = {2026: 3020, 2027: 2400, 2028: 2400, 2029: 2400, 2030: 2400}
UK_LCV_SCRAP  = 0.123
PLAN_ONLY_VAL = {27: [36, 36, 36, 36, 36], 52: [96, 108, 108, 108, 108],
                 80: [5, 5, 5, 5, 5],       89: [5, 5, 5, 5, 5]}

# ============================================================ engine
def back_solve(series, c, start):
    R = {}
    for t in YEARS:
        if t < start:
            R[t] = 0.0; continue
        R[t] = series[t] - sum(R[v] * S(c, t - v + 1) for v in YEARS if start <= v < t)
    return R

def detect_seam(series, c):
    R = back_solve(series, c, 1990)
    for t in range(1991, 2026):
        if series[t] > 0 and R[t] < 0 and abs(R[t]) > 0.25 * series[t]:
            return t
    return 1990

def build_state(series, c):
    seam = detect_seam(series, c)
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
    return seam, R, clipped, resid

def v19_regs(v):
    return {t: round((v.get(t) or 0) - (v.get(t-1) or 0) * 0.97) for t in FY}

def smooth_level(x):
    n = len(x); sm = []
    for i in range(n):
        if i == 0:       sm.append((x[0] + x[1]) / 2.0)
        elif i == n - 1: sm.append((x[n-2] + x[n-1]) / 2.0)
        else:            sm.append((x[i-1] + x[i] + x[i+1]) / 3.0)
    tx, ts = sum(x), sum(sm)
    f = (tx / ts) if ts else 1.0
    return [int(round(z * f)) for z in sm]

# ============================================================ read V19
import openpyxl
wbr = openpyxl.load_workbook(V19, data_only=True)
wsr = wbr['1.UIO Overview']
COLS = {y: 7 + (y - 1990) for y in YEARS}
ROWS = []
for r in range(7, 91):
    ROWS.append({'row': r,
                 'meta': [wsr.cell(row=r, column=i).value for i in range(1, 7)],
                 'vals': {y: wsr.cell(row=r, column=COLS[y]).value for y in YEARS}})
V19_GT = {y: wsr.cell(row=2, column=COLS[y]).value for y in YEARS}
V19_MIDI = {y: wsr.cell(row=5, column=COLS[y]).value for y in YEARS}
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
           'dist': meta[5], 'v19': [v[t] for t in FY], 'v20': None, 'regs_v19': None,
           'regs_used': None, 'status': '', 'rule': '', 'seam': None,
           'life': round(sum(c.values()), 2), 'scrap_pct': round(100.0/sum(c.values()), 2),
           'low_conf': r in LOW_CONF}
    if r in HOOK_ISRAEL:
        rec['status'] = 'HOOK - Israel rebuilt by a separate agent'
        rec['rule'] = 'Task item 3: leave a hook, do not compute'
        plan[r] = rec; continue
    if r in LEAVE_AS_V19:
        rec['status'] = 'LEFT AS V19 - UK CV sheet-4 survival model already correct'
        rec['rule'] = 'Task item 3: out of scope'
        plan[r] = rec; continue

    regs = v19_regs(v)
    rec['regs_v19'] = [regs[t] for t in FY]

    if r == ROW25:
        u = {2025: v[2025]}
        for t in FY:
            u[t] = int(round(u[t-1] * (1 - UK_LCV_SCRAP) + UK_LCV_REGS[t]))
        rec['v20'] = [u[t] for t in FY]
        rec['regs_used'] = [UK_LCV_REGS[t] for t in FY]
        rec['status'] = 'REBUILT - locked CY2026F = 44,926'
        rec['rule'] = ('Locked value (Jerome 30 Jul 2026): 2025E 47,783 x (1-0.123) + IMIT 3,020 = 44,926; '
                       'then pickup scrap 12.3% + IMIT regs each year')
        plan[r] = rec; continue

    if r in PLAN_ONLY_MD:
        rec['v20'] = [0, 0, 0, 0, 0]
        rec['regs_used'] = PLAN_ONLY_VAL[r]
        rec['status'] = 'PLAN ONLY - removed from Grand Total'
        rec['rule'] = ('Task item 6: plan-only block. VIN evidence - 0 medium-duty units of 3,238 '
                       'trucks shipped to Europe since 2020 (VIN_register.parquet, series NLR/NPR/NMR/NNR/FRR/FSR only)')
        plan[r] = rec; continue

    if all(x == 0 for x in regs.values()) and v[2025] == 0:
        rec['status'] = 'no forecast in V19 - no action'
        plan[r] = rec; continue

    seam, Rs, clipped, resid = build_state(v, c)
    rec['seam'] = seam if seam != 1990 else None
    used = smooth_level([regs[t] for t in FY])
    rec['regs_used'] = used
    u = {}
    for t in FY:
        stock = sum(Rs[vg] * S(c, t - vg + 1) for vg in range(1990, t))
        Rs[t] = used[FY.index(t)]
        u[t] = int(round(stock + Rs[t] * S(c, 1)))
    rec['v20'] = [u[t] for t in FY]
    rec['status'] = 'REBUILT on survival curve (%.2f yr avg life, %.2f%%/yr scrap)' % (
        sum(c.values()), 100.0/sum(c.values()))
    rec['rule'] = ('Survival curve same method as 1990-2025 (task item 2) + level-preserving 3-pt '
                   'smoothing of the new-registration input (task item 5)')
    if r == 42:
        rec['status'] += ' | INDICATIVE - Germany history fabricated'
        rec['rule'] += (' | INDICATIVE: no German registration/parc series on disk with history; '
                        'Helwig parc is a 31/12/2025 snapshot of 787 Nfz only')
    plan[r] = rec

# ---- change log: one row per changed cell
for r in sorted(plan):
    p = plan[r]
    if p['v20'] is None:
        continue
    for i, y in enumerate(FY):
        old, new = p['v19'][i], p['v20'][i]
        if abs(old - new) < 0.5:
            continue
        import openpyxl.utils as _u
        changelog.append({
            'row': r, 'country': p['country'], 'cv_lcv': p['cv'], 'model_type': p['model'],
            'distributor': p['dist'], 'year': y,
            'cell': '%s%d' % (_u.get_column_letter(FYCOL[y]), r),
            'column': _u.get_column_letter(FYCOL[y]),
            'old_value_v19': round(old, 1), 'new_value_v20': round(new, 1),
            'delta': round(new - old, 1),
            'pct_change': round((new/old - 1)*100, 1) if old else '',
            'rule_applied': p['rule'], 'source': '',
            'scope_status': p['status'], 'date': TODAY})

# ---- source note per row family
def src_for(p):
    r = p['row']
    if r == ROW25:
        return 'IMIT LCV UIO Nov-2025 (IUK UK) + locked arithmetic 30-Jul-2026'
    if r in PLAN_ONLY_MD:
        return 'VIN_register.parquet (01_data/07_UIO/vin) - zero MD units 2020-2026'
    if r in LOW_CONF and p['model'] != 'LCV':
        return 'V19 series (low-confidence history) + survival curve'
    if p['model'] == 'LCV':
        return 'V19 series + LCV 12-yr survival curve (workbook sheet 3 / IMIT Nov-2025)'
    return 'V19 series + CV developed 16-yr survival curve (workbook sheet 3 Section A)'
for ch in changelog:
    ch['source'] = src_for(plan[ch['row']])

print("changed cells: %d" % len(changelog))

# ============================================================ totals
def total(getter, include_midi, drop_plan_only):
    t = 0.0
    for r in range(7, 91):
        if r in MIDI_ROWS and not include_midi: continue
        if r in PLAN_ONLY_MD and drop_plan_only: continue
        t += getter(r)
    return t

def v19of(r, i): return plan[r]['v19'][i]
def v20of(r, i):
    p = plan[r]
    return p['v20'][i] if p['v20'] is not None else p['v19'][i]

cmp_tbl = {}
for i, y in enumerate(FY):
    cmp_tbl[y] = {k: round(val, 1) for k, val in {
        'v19_incl_midi': total(lambda r: v19of(r, i), True, False),
        'v20_incl_midi': total(lambda r: v20of(r, i), True, True),
        'v19_ex_midi':   total(lambda r: v19of(r, i), False, False),
        'v20_ex_midi':   total(lambda r: v20of(r, i), False, True),
    }.items()}
    c = cmp_tbl[y]
    c['overstatement_incl_pct'] = round((c['v19_incl_midi']/c['v20_incl_midi']-1)*100, 1)
    c['overstatement_incl_units'] = round(c['v19_incl_midi']-c['v20_incl_midi'], 0)
    c['overstatement_ex_pct'] = round((c['v19_ex_midi']/c['v20_ex_midi']-1)*100, 1)
    c['overstatement_ex_units'] = round(c['v19_ex_midi']-c['v20_ex_midi'], 0)

print("\n%-6s %13s %13s %9s | %13s %13s %9s" % ("Year","V19 incl","V20 incl","over","V19 ex","V20 ex","over"))
for y in FY:
    c = cmp_tbl[y]
    print("%-6d %13.0f %13.0f %8.1f%% | %13.0f %13.0f %8.1f%%" % (
        y, c['v19_incl_midi'], c['v20_incl_midi'], c['overstatement_incl_pct'],
        c['v19_ex_midi'], c['v20_ex_midi'], c['overstatement_ex_pct']))

# ---- boundary + rebuild checks
def boundary_check(r, mt):
    p = plan[r]
    if p['v20'] is None: return None
    v = {y: float(BYROW[r]['vals'].get(y) or 0) for y in YEARS}
    c = curve(mt)
    seam, Rs, _, _ = build_state(v, c)
    t = 2026
    stock = sum(Rs[vg] * S(c, t - vg + 1) for vg in range(1990, t))
    implied = stock / S(c, 1) if S(c, 1) else None
    return {'row': r, 'country': p['country'], 'model': mt,
            'v19_2025': v[2025], 'v20_2025': round(v[2025], 1),
            'implied_2026_pre_plan_stock': round(stock, 1),
            'gap_units': round(v[2025] - stock, 1),
            'gap_pct': round((v[2025]/stock - 1)*100, 2) if stock else None}

checks = [boundary_check(r, plan[r]['model']) for r in (26, 29, 51, 54, 9)]
checks = [x for x in checks if x]

# ============================================================ write outputs
if DRY:
    print("\nDRY RUN - nothing written.")
    raise SystemExit(0)

# --- assumptions log (.md)
def md_table(headers, rows_):
    out = ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---']*len(headers)) + '|']
    for r_ in rows_:
        out.append('| ' + ' | '.join(str(x) for x in r_) + ' |')
    return '\n'.join(out)

reb = [p for p in plan.values() if p['v20'] is not None]
A = []
A.append("# UIO V20 — assumptions log\n")
A.append("**Candidate:** `%s`  \n**Generated:** %s  \n**Applies to:** `ISUZU_UIO_Overview_2026.xlsx` (V19, 18 Jun 2026) — read-only reference, not modified\n" % (CAND, TODAY))
A.append("## 1. Purpose and authority\n")
A.append("The live V19 file carries a split method: 1990–2025 is built with a survival curve, "
         "2026–2030 with a flat 3 %/yr scrap rule (`UIO × 0.97 + new registrations`). "
         "The flat rule implies a 33.3-year vehicle life; the curve used everywhere else implies "
         "9.85 years (CV) and 8.13 years (LCV). This candidate removes the flat rule and applies "
         "the same survival curve to 2026–2030.\n")
A.append("This is a **dated candidate**, not a promotion of the live file. V19 remains canonical "
         "until someone promotes this candidate.\n")
A.append("## 2. The method\n")
A.append("For every in-scope row:\n")
A.append("```\nUIO(t) = SUM_v [ R_v × S(t − v + 1) ]  +  R_t × S(1)\n```\n")
A.append("- `R_v` = new-registration cohort for year *v*.\n"
         "- `S` = survival curve by vehicle age.\n"
         "- `R_1990–2025` is recovered by recursive decomposition of V19's **own** historical series "
         "(`R_t = UIO(t) − Σ_{v<t} R_v × S(t−v+1)`). The reconstruction therefore reproduces "
         "1990–2025 exactly by construction, so there is **no step at the 2025/2026 boundary**.\n"
         "- `R_2026–2030` is taken from the new-registration inputs V19 already buried in its "
         "roll-forward (`regs(t) = UIO(t) − UIO(t−1) × 0.97`), then 3-point smoothed with the "
         "five-year level preserved exactly.\n")
A.append("### Curves used (unchanged from V19 sheet `3. UIO Calculation`)\n")
A.append(md_table(['Curve', 'Applies to', 'Ages', 'Average life', 'Implied scrap/yr', 'Source'], [
    ['CV developed, 16-yr', 'LD, MD, F-Series', '1–16', '9.85 yr', '10.15 %', 'Sheet 3 Section A / IML'],
    ['LCV, 12-yr', 'LCV', '1–12', '8.13 yr', '12.30 %', 'Sheet 3 Section A / IMIT Nov-2025'],
    ['CV emerging, 20-yr', 'not used in V20 forecast (see §8)', '1–20', '12.15 yr', '8.23 %', 'Sheet 3 Section A'],
    ['Flat 3 % rule (V19 forecast)', 'V19 2026–2030 only', 'n/a', '33.33 yr', '3.00 %', 'V19 build step 6'],
]))
A.append("\n**Why the LCV curve is the `age-12 = 0.00` variant.** Sheet `3. UIO Calculation` row 18 "
         "shows age 12 = 0.10 while the IMIT source (`LCV UIO (November 2025)_EU_Study_Imit.xlsx`, "
         "sheet `ISZE` row 53) stops at age 11 = 0.20 with no age-12 column. The live sheet therefore "
         "appears to hold a year-13 value in the year-12 slot. The maximum-life-12 reading is used "
         "here because it is the variant that reproduces the locked IUK arithmetic "
         "(`47,783 × (1 − 0.123) + 3,020 = 44,926`), and because it matches the 8.1-year life quoted "
         "in the V20 spec. If Jerome confirms 0.10 at age 12, the LCV rows move by about +5.6 % at "
         "2030 and the lock would need re-opening. **This is flagged, not hidden.**\n")
A.append("### CV emerging curve — checked, not used\n")
A.append("Israel's rows sit on the emerging curve in V19. In this candidate rows 7 and 8 are parked "
         "as a hook (§9) and Israel LCV (row 9) runs on the LCV curve, so the emerging curve is not "
         "used anywhere in the V20 forecast. It is recorded here only so the omission is deliberate.\n")
A.append("## 3. Scope — what is in and what is out\n")
A.append(md_table(['Sheet-1 rows', 'Treatment', 'Reason'], [
    ['Rows 7, 8 — Israel LD, MD', '**HOOK.** V19 values left in place, not computed.', 'Task item 3: rebuilt by a separate agent'],
    ['Rows 22, 24 — UK CV LD, F-Series', '**Unchanged.** Live-linked to sheet `4. ITUK UIO Projection`.', 'Task item 3: already correct'],
    ['Row 25 — UK LCV', '**Rebuilt** on the locked arithmetic.', 'Task item 4'],
    ['Rows 27, 52, 80, 89 — IE/PT/GR/CY medium duty', '**Plan only.** Set to zero, out of the Grand Total.', 'Task item 6'],
    ['Row 42 — Germany LD', 'Rebuilt, **marked indicative**.', 'Task item 7'],
    ['All other rows with a V19 forecast', 'Rebuilt on the survival curve.', 'Task item 2'],
    ['Rows with no V19 forecast (empty markets)', 'Untouched.', 'Nothing to change'],
]))
A.append("\n## 4. Exceptions and hooks in detail\n")
A.append("### 4.1 Israel (rows 7, 8) — hook only\n"
         "Not computed here. A marker cell and a note are written beside the rows so nobody mistakes "
         "them for V20 output. **Files needed to close this:** the Israeli Ministry of Transport parc "
         "band table as data (the spec records it only as a PDF slide picture), plus the UTI "
         "registration band table `01_data/90_INBOX/_imie_mail_20260730/UIO ISUZU 2025.xlsx` sheet "
         "`גיליון1`, which is on disk and covers 1994–2025.\n")
A.append("### 4.2 UK CV (rows 22, 24) — left alone\n"
         "Cols AQ:AU remain the live cross-sheet formulas into `4. ITUK UIO Projection`. Not touched.\n")
A.append("### 4.3 UK LCV (row 25) — locked\n")
A.append("```\n2025E 47,783 × (1 − 0.123) + 3,020 = 41,905.691 + 3,020 = 44,925.691 → 44,926\n```\n")
A.append(md_table(['Year', 'New registrations used', 'Result'], [
    [y, UK_LCV_REGS[y], plan[25]['v20'][i]] for i, y in enumerate(FY)]))
A.append("\n2026 registrations = IMIT Nov-2025 UK D-Max ≈ 3,020 (the spec's preferred input, not "
         "V19's buried ≈2,930). 2027–2030 = 2,400/yr, which is V19's own buried input for those "
         "years and is therefore the conservative, no-new-assumption choice. The 2026 value is the "
         "only locked number and it lands exactly on 44,926.\n")
A.append("### 4.4 Medium-duty plan-only block (rows 27, 52, 80, 89)\n")
A.append("These four rows are empty through 2025 and then grow purely on plan numbers. Evidence:\n")
A.append("`01_data/07_UIO/vin/VIN_register.parquet` holds 3,238 trucks shipped to Europe 2020–2026 "
         "with series `NLR`, `NMR`, `NNR`, `NPR`, `FRR`, `FSR` only — **zero medium-duty units**. "
         "By destination: PT 2,111 · IE 647 · DE 183 · MT 130 · CY 114 · BE 49 · GR 4.\n")
A.append(md_table(['Row', 'Market', 'V19 2026', 'V19 2030', 'V20 (main table)', 'Plan value kept in plan-only block'], [
    [r, plan[r]['country'], int(plan[r]['v19'][0]), int(plan[r]['v19'][4]), 0,
     ' / '.join(str(x) for x in PLAN_ONLY_VAL[r])] for r in sorted(PLAN_ONLY_MD)]))
A.append("\nSetting the cells to zero removes them from the Grand Total through the existing "
         "SUMPRODUCT, so **no Grand Total formula was altered**. The plan series is preserved on the "
         "new sheet `V20 PLAN ONLY` so it can be reinstated the moment a first real medium-duty "
         "registration appears.\n")
A.append("### 4.5 Germany (rows 42, 43, 44) — indicative\n")
A.append("**Row 42 is the file's worst cell and this candidate does not fix it.** V19 has 697 in "
         "2025 rising to 3,756 by 2030, and its own 2019–2024 history was produced by running the "
         "3 % rule backwards from a single 2025 point. Under V20 the row still rises to 3,493 "
         "because the *registration input* is unchanged — only the retention method is now honest.\n")
A.append("Sources checked on disk:\n")
A.append("- `01_data/90_INBOX/_isd_std_mail_20260818/attachments/2026-06-11_ISD_Fahrzeugbestand_-_Basis_-_Übersicht_D_.xlsx` "
         "sheet `Table`: a 31/12/2025 **parc snapshot** (787 Nfz). Bands: `<=3.40 t` 25, "
         "`3.41–3.50 t` 153, `3.51–5.50 t` 79, `5.51–6.50 t` 147, `6.51–7.50 t` 318, `3.41–7.50 t` 697, "
         "`7.51–12.00 t` 35. A parc gives no registration history and the table stops at 12.00 t.\n")
A.append("- `01_data/07_UIO/vin/VIN_register.parquet`: German shipments only 2020–2024 "
         "(37 / 39 / 15 / 68 / 24) and none in 2025, because 2025 is the P700 changeover trough.\n")
A.append("- A `V17 OVERRIDE` note on sheet `4. ITUK UIO Projection` row 17 shows the same "
         "single-point-backcast pattern was previously applied to the UK and had to be overridden.\n")
A.append("\n**Conclusion: no proper German source exists on disk.** Row 42 is therefore marked "
         "`INDICATIVE` in the flag column and in the change log rather than presented as measured. "
         "Row 44 (Germany LCV) also carries a flagged weakness: its registered stock falls to zero "
         "in 2025 while IMIT forecasts ≈10,000 D-Max, which is the same changeover artefact.\n")
A.append("### 4.6 Low-confidence histories\n")
A.append("Belgium, Cyprus, Malta and Greece are built from the IML backbone, not registration data "
         "(spec §Problem 5). They are rebuilt on the curve for consistency but flagged "
         "`LOW CONFIDENCE` in the flag column. Ireland and Portugal are the only markets whose LP "
         "history is anchored to real registrations, and both carry a methodology seam (§6).\n")
A.append("## 5. Sales plan handling\n")
A.append("Jerome's decision of 27 July 2026 — **one-to-one on the level** — is kept. The five-year "
         "registration total is preserved *exactly* in every row by construction: the smoothing "
         "renormalises so `Σ smoothed = Σ raw`.\n")
A.append("What changes is only the annual profile. Evidence from the VIN file, Ireland "
         "(*shipped vs registered*):\n")
A.append(md_table(['Year', 'Shipped', 'Registered', 'Difference'], [
    [2020, 79, 63, '+16'], [2021, 108, 98, '+10'], [2022, 88, 96, '−8'],
    [2023, 122, 71, '+51'], [2024, 54, 117, '−63'], ['**2020–2024**', '**451**', '**445**', '**+6 (1.3 %)**'],
]))
A.append("\nIndividual years swing ±50–70 units in opposite directions because a truck shipped in "
         "one year is registered in the next. A 3-point moving average with the level renormalised "
         "removes that timing artefact without touching the five-year total. Rows whose registration "
         "input is already constant (e.g. Ireland 216/yr) are unchanged.\n")
A.append("## 6. Methodology seam in the history — stated, not hidden\n")
A.append("Two rows cannot be decomposed into cohorts without producing a negative 'cohort', because "
         "V19 stitches an IML backbone onto a real-registration cohort model:\n")
A.append(md_table(['Row', 'Market', 'Seam year', 'What V19 does', 'What this candidate does'], [
    [26, 'Ireland LD', 2014, 'IML 1990–2013, SIMI cohort model 2014+', 'State re-based at the seam; legacy block retired from the seam on'],
    [51, 'Portugal LD', 2014, 'IML 1990–2013, I-Motors cohort model 2014+', 'Same'],
    [88, 'Cyprus LD', 2014, 'backbone then scrap-adjusted model', 'Same'],
    [29, 'Ireland LCV', 2019, 'IML then SIMI D-Max cohorts', 'Same'],
]))
A.append("\nThe state still carries the legacy block's surviving units in the years before the seam "
         "(it decays to zero within about ten years), so pre-seam years are unchanged, but the block "
         "is **not** allowed to be added a second time from the seam onwards — which is what V19 "
         "implicitly already assumes.\n")
A.append("## 7. Verification performed\n")
A.append(md_table(['Check', 'Result'], [
    ['Reconstruction reproduces V19 history', 'Exact by construction; 2025 output equals V19 2025 on every rebuilt row'],
    ['Ireland LD 2030', 'V20 **%s** vs V19 %s; spec independently predicted ≈1,382' % (plan[26]['v20'][4], int(plan[26]['v19'][4]))],
    ['Ireland LCV 2030', 'V20 **%s** vs V19 %s; spec independently predicted ≈2,527' % (plan[29]['v20'][4], int(plan[29]['v19'][4]))],
    ['IUK LCV 2026', 'V20 **%s** = the locked 44,926 (V19 was 49,280)' % plan[25]['v20'][0]],
    ['Pickup fleet 2030 vs 2025', 'Falls — falling registrations can no longer grow a fleet'],
    ['Medium-duty in Grand Total', 'Zero'],
]))
for c_ in checks:
    A.append("- Boundary check %s %s: 2025 stock %s vs the stock implied by the healthy 2014+ cohorts "
             "alone %s → gap %s units (%s %%). The gap is the legacy pre-seam block and is visible, "
             "not absorbed." % (c_['country'], c_['model'], c_['v20_2025'],
                                c_['implied_2026_pre_plan_stock'], c_['gap_units'], c_['gap_pct']))
A.append("\n## 8. Open inputs needed — where a computation was stopped rather than invented\n")
A.append(md_table(['#', 'What is missing', 'Which rows it unblocks', 'Any candidate on disk?'], [
    [1, 'Israeli Ministry of Transport parc band table as data (spec holds it only as a PDF slide picture). '
        'The *registration* band table is on disk at `01_data/90_INBOX/_imie_mail_20260730/UIO ISUZU 2025.xlsx` sheet `גיליון1` (1994–2025).',
     'Rows 7, 8 (owned by the separate Israel agent)', 'Registration table: yes. Parc table: no'],
    [2, 'A German registration series or parc history by year',
     'Row 42 (and row 44 history)', 'No — Helwig is a single 31/12/2025 snapshot'],
    [3, 'Confirmation of the LCV age-12 survival value (0.10 or 0.00)',
     'All 22 LCV rows, ±5.6 % at 2030', 'IMIT source stops at age 11; only the lock pins it'],
    [4, 'Written definition of the ISZE pickup perimeter used in the appendix (the ~2,500/yr and 615-unit reconciliation gaps)',
     'Reconciliation of the registration input to the Grand Total', 'No'],
    [5, 'Owner of the June change that introduced the 3 % rule',
     'Process only — not needed to compute', 'No'],
]))
A.append("\n## 9. What was deliberately not touched\n")
A.append("- The live V19 workbook (`ISUZU_UIO_Overview_2026.xlsx`) — copied at filesystem level only.\n"
         "- `_Archive/ISUZU_UIO_Overview_2026_v18.xlsx` — never opened.\n"
         "- Any live price list or pricing configuration.\n"
         "- `03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv` — the share correction is a separate "
         "authorised step. No candidate share file was written.\n"
         "- Leakage packs.\n"
         "- Sheet 1 summary tables (rows 93–200): **hardcoded and stale since about V12**, and they "
         "do not read cols AQ:AU, so they are neither updated nor quoted here. They need their own "
         "rebuild.\n")
A.append("## 10. How to reproduce\n")
A.append("```powershell\ncd %s\npython build_uio_v20_candidate.py --dry   # analysis only\npython build_uio_v20_candidate.py         # build\n```\n" % SCRIPT_DIR)
A.append("Inputs read: `%s` (read-only), `01_data/07_UIO/vin/VIN_register.parquet`, "
         "`01_data/90_INBOX/_isd_std_mail_20260818/attachments/2026-06-11_ISD_Fahrzeugbestand_-_Basis_-_Übersicht_D_.xlsx`, "
         "`06_uio/_SourceData/LCV UIO (November 2025)_EU_Study_Imit.xlsx`, "
         "`91_legacy/Isuzu/UIO/Script/ISZE CV_FY2025-FY2030_mid-term plan & 12RS.xlsx`.\n" % V19)

with open(ASSUM_MD, 'w', encoding='utf-8') as f:
    f.write('\n'.join(A))
print("wrote %s" % ASSUM_MD)

# --- change log CSV
with open(CHG_CSV, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=['row', 'country', 'cv_lcv', 'model_type', 'distributor', 'year',
                                      'cell', 'column', 'old_value_v19', 'new_value_v20', 'delta',
                                      'pct_change', 'rule_applied', 'source', 'scope_status', 'date'])
    w.writeheader()
    for ch in sorted(changelog, key=lambda z: (z['row'], z['year'])):
        w.writerow(ch)
print("wrote %s (%d rows)" % (CHG_CSV, len(changelog)))

# --- verification JSON
json.dump({'generated': TODAY, 'candidate': CAND, 'v19_source': V19, 'v19_B4_toggle': B4,
           'curves': {'CV_developed': CV_DEV, 'LCV': LCV, 'CV_emerging_source_only': CV_EMG_SRC},
           'life_and_scrap': {'CV': {'life_years': 9.85, 'scrap_pct': 10.15},
                              'LCV': {'life_years': 8.13, 'scrap_pct': 12.30},
                              'V19_flat_rule': {'life_years': 33.33, 'scrap_pct': 3.0}},
           'grand_total_comparison': cmp_tbl, 'boundary_checks': checks,
           'verification_checks': {
               'ireland_LD_2030_v20': plan[26]['v20'][4], 'ireland_LD_2030_v19': plan[26]['v19'][4],
               'ireland_LCV_2030_v20': plan[29]['v20'][4], 'ireland_LCV_2030_v19': plan[29]['v19'][4],
               'iuk_lcv_2026_v20': plan[25]['v20'][0], 'iuk_lcv_2026_v19': plan[25]['v19'][0],
               'iuk_lcv_2026_locked_target': 44926},
           'rows': {str(k): v for k, v in plan.items()},
           'changed_cell_count': len(changelog)},
          open(VERIFY, 'w', encoding='utf-8'), indent=1, default=str)
print("wrote %s" % VERIFY)

# ============================================================ workbook
shutil.copy2(V19, CAND)
print("copied V19 -> %s" % CAND)

import win32com.client as win32
excel = win32.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
excel.ScreenUpdating = False
xl_updatelinks_never = 0
wb = None
try:
    wb = excel.Workbooks.Open(CAND, UpdateLinks=xl_updatelinks_never, ReadOnly=False)
    sh = wb.Worksheets("1.UIO Overview")

    # block AQ7:AU90
    block = [[0]*5 for _ in range(84)]
    for idx, r in enumerate(range(7, 91)):
        p = plan[r]
        for j in range(5):
            block[idx][j] = p['v20'][j] if p['v20'] is not None else p['v19'][j]
    sh.Range("AQ7:AU90").Value = block

    # flag column AV
    flags = []
    for r in range(7, 91):
        p = plan[r]
        if r in HOOK_ISRAEL:                      f = 'HOOK - Israel (separate agent)'
        elif r in LEAVE_AS_V19:                   f = 'OUT OF SCOPE - left as V19'
        elif r in PLAN_ONLY_MD:                   f = 'PLAN ONLY - out of Grand Total'
        elif r == 42:                             f = 'INDICATIVE - no historic source'
        elif r in LOW_CONF:                       f = 'LOW CONFIDENCE history'
        elif p['v20'] is not None:                f = 'V20 survival curve'
        else:                                     f = 'no forecast in V19 - unchanged'
        flags.append([f])
    sh.Range("AV6").Value = "V20 scope flag"
    sh.Range("AV7:AV90").Value = flags
    sh.Range("AV6").Font.Bold = True
    sh.Columns("AV").ColumnWidth = 30

    # Israel hook note beside rows 7/8
    sh.Range("AW6").Value = "V20 hook"
    sh.Range("AW7").Value = "NOT REBUILT - separate Israel agent. Needs the MoT parc band table as data."
    sh.Range("AW8").Value = "NOT REBUILT - separate Israel agent. Needs the MoT parc band table as data."
    sh.Range("AW6").Font.Bold = True
    sh.Columns("AW").ColumnWidth = 60

    # title
    sh.Range("A1").Value = ("ISUZU - Units In Operation (UIO)  |  ISZE / ITUK / Israel  |  "
                            "V20 CANDIDATE %s  |  2026-2030 rebuilt on the survival curve" % TODAY)
    sh.Range("C4").Value = ('V20 candidate %s. B4 is left as "Include" exactly as V19; both the '
                            'incl-MIDI and ex-MIDI totals are reported in the V20 verification file. '
                            'See sheet "V20 ASSUMPTIONS".' % TODAY)
    sh.Range("A92").Value = ("V20 note: rows 27/52/80/89 are PLAN ONLY and set to zero so they leave the "
                             "Grand Total; rows 7/8 are a HOOK for the separate Israel rebuild; rows 22/24 "
                             "are unchanged UK CV sheet-4 links. See columns AV/AW and sheet V20 ASSUMPTIONS.")

    # ---- new sheet: V20 ASSUMPTIONS
    try: wb.Worksheets("V20 ASSUMPTIONS").Delete()
    except Exception: pass
    wa = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
    wa.Name = "V20 ASSUMPTIONS"
    wa.Range("A1").Value = "UIO V20 CANDIDATE - assumptions log"
    wa.Range("A1").Font.Bold = True; wa.Range("A1").Font.Size = 14
    wa.Range("A2").Value = "Full text: %s" % ASSUM_MD
    wa.Range("A3").Value = "Generated %s" % TODAY
    wa.Range("A5").Value = "Method"
    wa.Range("A5").Font.Bold = True
    wa.Range("A6").Value = ("UIO(t) = SUM_v [ R_v x S(t-v+1) ] + R_t x S(1).  1990-2025 R_v recovered by "
                            "recursive decomposition of V19's own history (exact reproduction, no step at "
                            "2025/2026). 2026-2030 R_v = the new-registration inputs V19 already buried in "
                            "its roll-forward, 3-point smoothed with the 5-year level preserved exactly.")
    wa.Range("A7").Value = "Curve / life / scrap"
    wa.Range("A7").Font.Bold = True
    for i, t in enumerate([
        "CV developed 16-yr (LD, MD, F-Series): 9.85 yr life, 10.15%/yr scrap",
        "LCV 12-yr (LCV rows): 8.13 yr life, 12.30%/yr scrap  <-- maximum-life-12 variant; see MD log s.2",
        "Flat 3% rule it replaces: 33.33 yr life, 3.00%/yr scrap",
    ]):
        wa.Range("A%d" % (8+i)).Value = t
    wa.Range("A12").Value = "Scope"
    wa.Range("A12").Font.Bold = True
    scope_rows = [
        ("Rows 7, 8 Israel LD/MD", "HOOK - not computed; separate Israel agent"),
        ("Rows 22, 24 UK CV", "Left as V19 - sheet-4 survival model already correct"),
        ("Row 25 UK LCV", "Rebuilt - locked CY2026F = 44,926"),
        ("Rows 27, 52, 80, 89 IE/PT/GR/CY MD", "PLAN ONLY - zeroed, out of Grand Total"),
        ("Row 42 Germany LD", "Rebuilt but INDICATIVE - no historic source on disk"),
        ("All other forecast rows", "Rebuilt on the survival curve"),
        ("Rows 93-200 summary tables", "NOT updated - hardcoded and stale since ~V12; do not quote"),
    ]
    for i, (k, val) in enumerate(scope_rows):
        wa.Range("A%d" % (13+i)).Value = k
        wa.Range("B%d" % (13+i)).Value = val
    wa.Range("A21").Value = "Open inputs needed"
    wa.Range("A21").Font.Bold = True
    opens = [
        "1. Israeli MoT parc band table as DATA (spec has it only as a PDF slide picture)",
        "2. A German registration series or parc history by year",
        "3. Confirmation of the LCV age-12 survival value (0.10 or 0.00)",
        "4. Written definition of the ISZE pickup perimeter (appendix reconciliation gaps)",
        "5. Owner of the June change that introduced the 3% rule",
    ]
    for i, t in enumerate(opens):
        wa.Range("A%d" % (22+i)).Value = t
    wa.Columns("A").ColumnWidth = 42
    wa.Columns("B").ColumnWidth = 92

    # ---- new sheet: V20 PLAN ONLY
    try: wb.Worksheets("V20 PLAN ONLY").Delete()
    except Exception: pass
    wp = wb.Worksheets.Add(After=wa)
    wp.Name = "V20 PLAN ONLY"
    wp.Range("A1").Value = "V20 PLAN ONLY block - medium duty, EXCLUDED from the Grand Total"
    wp.Range("A1").Font.Bold = True; wp.Range("A1").Font.Size = 13
    wp.Range("A2").Value = ("VIN evidence: 3,238 trucks shipped to Europe 2020-2026 (VIN_register.parquet), "
                            "series NLR/NMR/NNR/NPR/FRR/FSR only - ZERO medium-duty units. Reinstated into the "
                            "Grand Total the moment a first real medium-duty registration appears.")
    hdr = ["Sheet-1 row", "Market", "Model", "2026", "2027", "2028", "2029", "2030",
           "V19 2026", "V19 2030", "Status"]
    for j, h in enumerate(hdr, start=1):
        wp.Cells(4, j).Value = h
        wp.Cells(4, j).Font.Bold = True
    for i, r in enumerate(sorted(PLAN_ONLY_MD)):
        p = plan[r]
        rowv = [r, p['country'], p['model']] + PLAN_ONLY_VAL[r] + [int(p['v19'][0]), int(p['v19'][4]),
                                                                  'PLAN ONLY - not in Grand Total']
        for j, val in enumerate(rowv, start=1):
            wp.Cells(5+i, j).Value = val
    wp.Columns("A:J").ColumnWidth = 14

    # ---- new sheet: V20 CHANGE LOG
    try: wb.Worksheets("V20 CHANGE LOG").Delete()
    except Exception: pass
    wc = wb.Worksheets.Add(After=wp)
    wc.Name = "V20 CHANGE LOG"
    wc.Range("A1").Value = "V20 change log - every row/column touched. Full file: %s" % CHG_CSV
    wc.Range("A1").Font.Bold = True
    cols = ['row', 'country', 'cv_lcv', 'model_type', 'distributor', 'year', 'cell', 'column',
            'old_value_v19', 'new_value_v20', 'delta', 'pct_change', 'rule_applied', 'source',
            'scope_status', 'date']
    for j, h in enumerate(cols, start=1):
        wc.Cells(3, j).Value = h
        wc.Cells(3, j).Font.Bold = True
    for i, ch in enumerate(sorted(changelog, key=lambda z: (z['row'], z['year']))):
        for j, h in enumerate(cols, start=1):
            wc.Cells(4+i, j).Value = ch[h]
    wc.Columns("A:P").ColumnWidth = 18
    wc.Columns("M").ColumnWidth = 70
    wc.Columns("O").ColumnWidth = 55

    # ---- append V20 entries to the workbook Changelog sheet
    try:
        wcl = wb.Worksheets("Changelog")
        last = wcl.Cells(wcl.Rows.Count, 1).End(-4162).Row   # xlUp
        entries = [
            ("V20-1", "2026-09-22", "Jérôme Van der Pluym (via Cursor)",
             "1.UIO Overview cols AQ:AU (2026F-2030F): flat 3%/yr scrap rule REPLACED by the same survival-curve method already used for 1990-2025. CV LD/MD/F-Series on the 16-yr developed curve; LCV rows on the 12-yr curve.",
             "Task item 2. Removes the implied 33.3-yr vehicle life. Grand Total 2026 overstated by 6.3% (incl MIDI) rising to 27.5% by 2030.", "Methodology change"),
            ("V20-2", "2026-09-22", "Jérôme Van der Pluym (via Cursor)",
             "Row 25 UK LCV rebuilt on the locked arithmetic: 47,783 x (1-0.123) + 3,020 = 44,926 for CY2026F, rolled 2027-2030 with 12.3% pickup scrap + IMIT registrations.",
             "Task item 4. V19 had 49,280 (+3.13%); the locked value is 44,926 (-6.0%).", "Data change"),
            ("V20-3", "2026-09-22", "Jérôme Van der Pluym (via Cursor)",
             "Rows 27, 52, 80, 89 (IE/PT/GR/CY medium duty) zeroed and moved to the plan-only sheet 'V20 PLAN ONLY'. They leave the Grand Total through the existing SUMPRODUCT - no Grand Total formula was altered.",
             "Task item 6. VIN evidence: zero medium-duty units in 3,238 trucks shipped to Europe since 2020.", "Scope change"),
            ("V20-4", "2026-09-22", "Jérôme Van der Pluym (via Cursor)",
             "Rows 7, 8 (Israel LD/MD) parked as a HOOK for the separate Israel rebuild. Values left as V19, marked in column AW.",
             "Task item 3. Needs the MoT parc band table as data.", "Hook"),
            ("V20-5", "2026-09-22", "Jérôme Van der Pluym (via Cursor)",
             "Row 42 Germany LD rebuilt but marked INDICATIVE in column AV and in the change log. No German registration series or parc history exists on disk; the Helwig file is a single 31/12/2025 parc snapshot.",
             "Task item 7. The row still rises to 3,493 by 2030 because the registration input is unchanged - only retention is now honest.", "Flag"),
            ("V20-6", "2026-09-22", "Jérôme Van der Pluym (via Cursor)",
             "New-registration input for 2026-2030 taken from the values V19 already buried in its roll-forward, then 3-point smoothed with the five-year level preserved exactly.",
             "Task item 5. Keeps the one-to-one level decision (27 Jul 2026) while removing the shipment-to-registration timing artefact.", "Methodology change"),
            ("V20-7", "2026-09-22", "Jérôme Van der Pluym (via Cursor)",
             "Added sheets 'V20 ASSUMPTIONS', 'V20 PLAN ONLY', 'V20 CHANGE LOG' and columns AV (scope flag) / AW (hook).",
             "Auditability - task items 1, 8 and 9.", "New sheet"),
        ]
        for i, e in enumerate(entries):
            for j, val in enumerate(e, start=1):
                wcl.Cells(last+1+i, j).Value = val
    except Exception as ex:
        print("changelog append skipped: %s" % ex)

    excel.CalculateFullRebuild()
    wb.Save()
    print("workbook saved: %s" % CAND)
finally:
    if wb is not None:
        try: wb.Close(SaveChanges=False)
        except Exception: pass
    try: excel.Quit()
    except Exception: pass

print("\nDONE")
print("  candidate  : %s" % CAND)
print("  assumptions: %s" % ASSUM_MD)
print("  change log : %s" % CHG_CSV)
print("  verify     : %s" % VERIFY)
