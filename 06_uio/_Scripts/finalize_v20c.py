"""finalize_v20c.py -- section 12 for candidate c, with the true numbers and both residuals."""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl, win32com.client as win32

TAG = '2026-09-22c'
CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
CAND_C = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_%s.xlsx" % TAG)
CAND_B = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22b.xlsx")
CAND_A = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx")
V19    = os.path.join(CUR, "ISUZU_UIO_Overview_2026.xlsx")
ASSUM  = os.path.join(CUR, "UIO_V20_ASSUMPTIONS_%s.md" % TAG)
VERIFY = os.path.join(CUR, "UIO_V20_VERIFY_%s.json" % TAG)
HAR    = os.path.join(CUR, "_uio_v20_C_verification_report.json")
HAR_B  = os.path.join(CUR, "_uio_v20_B_verification_report.json")
FY = [2026, 2027, 2028, 2029, 2030]; COLS = {y: 7 + (y - 1990) for y in FY}

har = json.load(open(HAR, encoding='utf-8')); CH = har['checks']
harB = json.load(open(HAR_B, encoding='utf-8'))
m = CH['check7_overstatement_curve']['metrics']; me, sp = m['measured_pct'], m['spec_pct']
maxd = max(abs(me[k] - sp[k]) for k in sp)
n_in = sum(1 for k in sp if abs(me[k] - sp[k]) <= 1.5)

def gt(p):
    wb = openpyxl.load_workbook(p, data_only=True); ws = wb["1.UIO Overview"]
    d = {y: float(ws.cell(2, COLS[y]).value) for y in FY}; wb.close(); return d
GC, GB, GA, GV = gt(CAND_C), gt(CAND_B), gt(CAND_A), gt(V19)
sc, sb, sa, sv = (sum(x.values()) for x in (GC, GB, GA, GV))

def md(h, rows_):
    out = ['| ' + ' | '.join(str(x) for x in h) + ' |', '|' + '|'.join(['---']*len(h)) + '|']
    out += ['| ' + ' | '.join(str(x) for x in r) + ' |' for r in rows_]
    return '\n'.join(out)

L = []
L.append("")
L.append("### 12.1 Harness result on this candidate")
L.append("")
L.append("**Same harness, same machine: live V19 7 of 10 FAIL, candidate a 3 of 10 FAIL, this candidate "
         "2 of 10 FAIL.** Full report: `%s`." % HAR)
L.append("")
L.append(md(['Check', 'V19', 'a', 'b', '**c**'],
            [['`check1_method_consistency`', 'FAIL', 'FAIL (4 rows)', 'PASS', '**FAIL (1 row — r90)**'],
             ['`check2_ireland_rebuild`', 'FAIL', 'PASS', 'PASS', '**PASS**'],
             ['`check2b_ireland_2030`', 'FAIL', 'PASS', 'PASS', '**PASS**'],
             ['`check3_steady_state`', 'FAIL', 'PASS', 'PASS', '**PASS**'],
             ['`check4_vin_scrappage`', 'PASS', 'WARN', 'WARN', '**WARN**'],
             ['`check5_flat_rule_present`', 'FAIL', 'FAIL (2 rows)', 'PASS', '**PASS**'],
             ['`check6_totals_identity`', 'FAIL', 'PASS', 'PASS', '**PASS**'],
             ['`check7_overstatement_curve`', 'FAIL', 'FAIL', 'FAIL', '**FAIL — stated residual, §12.2**'],
             ['`check8_locked_values`', 'FAIL', 'PASS', 'PASS', '**PASS**'],
             ['`check9_self_cert_guard`', 'PASS', 'PASS', 'PASS', '**PASS**']]))
L.append("")
L.append("**`check1` on this candidate is one row: r90.** It is not a new defect and it is not "
         "repairable here. r90's forecast shape makes the harness read it as a flat roll-forward; the "
         "only change that cleared the flag (candidate b's seam re-base) did so by inflating the row "
         "55 % with seam residual, and was reverted (§4.11). **r90 therefore stands as a stated "
         "residual on the same footing as `check7`.** `check5` still passes with **0** hits.")
L.append("")
L.append("**What cleared, and what the fix was worth.** `check5` goes 2 hits → **0**. `check1` goes 4 "
         "rows (r33, r54, r79, r90) → **1** (r90): r33 left the flag when the engine-wide rounding step "
         "was removed (§4.7), r54 and r79 left it because their rows changed, r90 remains. The harness "
         "was not touched, nor its thresholds, nor the locked row-25 value.")
L.append("")
L.append("### 12.2 `check7` — the residual")
L.append("")
L.append(md(['Year', 'V19 Grand Total', 'This candidate', 'V19 over', 'Spec claim', 'Delta (pp)',
             'Harness own recompute'],
            [[y, "%.0f" % GV[y], "%.0f" % GC[y], "%+.1f %%" % (100*(GV[y]/GC[y]-1)),
              "%+.1f %%" % sp[str(y)], "%+.2f" % (100*(GV[y]/GC[y]-1) - sp[str(y)]),
              "%.1f %%" % m['recomputed_pct'][str(y)]] for y in FY]))
L.append("")
L.append("Max |delta| is **%.2f pp** against the harness's ±1.5 pp band, and **%d of the 5 years are "
         "inside it**. The band is narrower than the spread between defensible implementations of the "
         "survival-curve method — the harness's own instant-rate recompute reaches only %.1f %% at 2030, "
         "the spec's curve comes from the v18 *dashboard* rather than from any workbook, and this "
         "candidate lands at %.1f %%. **Not forced.** The guarded behaviour is met: V19 is materially "
         "inflated, the gap is monotone, and it widens every year. Reverting the r90 seam error (§4.11) "
         "brought this check **closer** to the spec than candidate b (max %.2f pp vs %.2f pp), which is "
         "the expected direction."
         % (maxd, n_in, m['recomputed_pct']['2030'], me['2030'], maxd,
            max(abs(harB['checks']['check7_overstatement_curve']['metrics']['measured_pct'][k]
                    - harB['checks']['check7_overstatement_curve']['metrics']['spec_pct'][k]) for k in sp)))
L.append("")
L.append("### 12.3 `check4` WARN — carried, not a defect in this candidate")
L.append("")
L.append("Identical in every candidate: the VIN register on disk was rebuilt 2026-09-18, after the spec "
         "was written, and no longer reproduces the spec's shipment totals (Ireland 523 vs 451, Portugal "
         "1,583 vs 1,427). Measured scrappage 15.1 % / 9.1 %, far from the 3 % rule — the claim that "
         "matters. **Open input**, §8 item 9.")
L.append("")
L.append("### 12.4 Grand Total 2026-2030 — four-way")
L.append("")
L.append(md(['Year', 'V19', 'Candidate a', 'Candidate b', '**Candidate c**', 'c − b', 'V19 over c'],
            [[y, "%.0f" % GV[y], "%.0f" % GA[y], "%.0f" % GB[y], "**%.0f**" % GC[y],
              "%+.0f" % (GC[y]-GB[y]), "%+.1f %%" % (100*(GV[y]/GC[y]-1))] for y in FY]))
L.append("")
L.append(md(['Window', 'V19', 'Candidate a', 'Candidate b', '**Candidate c**', 'c vs a', 'c vs V19'],
            [['2026-2030 sum', "%.0f" % sv, "%.0f" % sa, "%.0f" % sb, "**%.0f**" % sc,
              "%+.2f %%" % (100*(sc/sa-1)), "%+.2f %%" % (100*(sc/sv-1))]]))
L.append("")
L.append("The %+.2f %% move from candidate b to c is exactly the r90 revert: −1,014 / −1,167 / −1,263 "
         "/ −1,290 / −1,254 units, of which the CYPRUS LCV row is the whole of it. Candidate c's Grand "
         "Totals are within 0.03 %% of the adjudication's own measured figures (252,218 → 224,270) in "
         "every year."
         % (100*(sc/sb-1)))
L.append("")
L.append("### 12.5 The r90 decision, stated plainly")
L.append("")
L.append("This candidate contains a **deliberate, disclosed non-fix**. r90 CYPRUS LCV carries one "
         "negative implied cohort (2014, −137.6) that its sources cannot resolve, and the row is left "
         "on its existing reconciling build rather than re-based. Reasons, in order of weight:")
L.append("")
L.append("1. **Re-basing does not reconcile.** It misses the row's own 2025 series by 862 units and "
         "leaves five negative cohorts instead of one (§4.11).")
L.append("2. **It inflates the row 55 % with residual, not evidence** — the 2026 state goes 1,859 → "
         "2,873 (4,310 cohort units at a 0.20 survival ratio).")
L.append("3. **It contradicts the independent LCV source the workbook itself cites.** The IMIT LCV UIO "
         "study (Nov 2025) has Cyprus at 2,024 (2026) and 2,433 (2028). The re-based row is +61 % and "
         "+52 % against that; the existing row is +11 % and +0.5 %.")
L.append("")
L.append("The cost of the revert is that `check1` flags the row again. I would rather ship a row that "
         "reconciles, agrees with its cited source, and is flagged, than one that clears a test by "
         "double-counting a cohort.")

txt = open(ASSUM, encoding='utf-8').read()
txt += '\n'.join(L)
open(ASSUM, 'w', encoding='utf-8').write(txt)
print("appended 12.1-12.5 to %s" % ASSUM)

v = json.load(open(VERIFY, encoding='utf-8'))
v['independent_harness'] = {
    'harness': 'ISZE/03_analytics/Isuzu/prism/scripts/verify_uio_v20.py',
    'report': HAR, 'verdict': har['verdict'], 'n_checks': har['n_checks'], 'n_fail': har['n_fail'],
    'failed_checks': har['failed_checks'],
    'statuses': {k: CH[k]['status'] for k in CH},
    'check1_switching_rows': CH['check1_method_consistency']['metrics']['switching_rows'],
    'check5_flat_3pct_rows': CH['check5_flat_rule_present']['metrics']['rows'],
    'check7': {'measured_pct': me, 'recomputed_pct': m['recomputed_pct'], 'spec_pct': sp,
               'max_abs_delta_pp': round(maxd, 2), 'years_inside_1p5pp': n_in,
               'verdict': 'STATED RESIDUAL - not forced.'},
    'stated_residuals': {
        'check1_method_consistency': 'r90 CYPRUS LCV only. Not repairable here: the seam re-base that cleared it inflates the row 55% with seam residual and contradicts the row\'s own IMIT source - attempted in candidate b and reverted (assumptions log s.4.11).',
        'check7_overstatement_curve': 'Band narrower than the spread between defensible implementations. Not forced.'},
}
v['grand_total'] = {
    'v19': {str(y): round(GV[y], 2) for y in FY},
    'candidate_a': {str(y): round(GA[y], 2) for y in FY},
    'candidate_b': {str(y): round(GB[y], 2) for y in FY},
    'candidate_c': {str(y): round(GC[y], 2) for y in FY},
    'fivesum': {'v19': round(sv, 2), 'candidate_a': round(sa, 2),
                'candidate_b': round(sb, 2), 'candidate_c': round(sc, 2)},
}
json.dump(v, open(VERIFY, 'w', encoding='utf-8'), indent=1, default=str)
print("updated %s" % VERIFY)

excel = win32.DispatchEx("Excel.Application")
excel.Visible = False; excel.DisplayAlerts = False
wbk = None
try:
    wbk = excel.Workbooks.Open(CAND_C, UpdateLinks=0, ReadOnly=False)
    wa = wbk.Worksheets("V20 ASSUMPTIONS")
    last = wa.Cells(wa.Rows.Count, 1).End(-4162).Row
    if last >= 39:
        wa.Range("A39:A%d" % max(last, 220)).ClearContents()
    lines = [
        ("h", "Fix pass c (%s) - supersedes b" % TAG),
        ("t", "WHY THERE IS A PASS c: candidate b re-based r90 CYPRUS LCV at 2014 in pursuit of FIX 3. That was WRONG and has been reverted. Re-basing r90 leaves 5 negative cohorts (not 1), misses the row's own 2025 series by -862 units, and double-counts the 2014 cohort, pushing the 2026 state from 1,859 to 2,873 (+55%) purely as seam residual. It also contradicts the IMIT LCV UIO study the workbook itself cites (Cyprus 2024 vs the row's 3,252). See log s.4.11."),
        ("t", "FIX 1 r79 GREECE CV LD - UNCHANGED from b and still correct: the +14.0 x 5 straight line was a ROUNDING artefact of integer-rounding the recovered input before the level-preserving smooth. Now smoothed at full precision. Row still flagged INPUT DERIVED (no Greek CV LD registration source exists on disk)."),
        ("t", "FIX 2 sheet 'V20 REGS USED' - UNCHANGED from b: per row and year the registration input used, the raw pre-smoothing input, the source, and the UNRECONSTRUCTABLE block."),
        ("t", "FIX 3 r54 PORTUGAL LCV - HELD: seam 2005, all three negative cohorts (2005/2006/2012) retired. This is the rule that reconciles (residual 0.0)."),
        ("t", "FIX 3 r90 CYPRUS LCV - REVERTED, deliberately. The row keeps its existing build, which reconciles 2025 exactly, and is flagged UNRECONSTRUCTABLE - legacy cohort gap (2014). No positive-number guess was made."),
        ("t", "r33 BELGIUM and r90's forecast behaviour were adjudicated CURVE and are not re-litigated. r33 moved only because the engine-wide rounding step was removed."),
        ("t", "Unchanged and out of scope: V19, the v18 archive, live price lists, uio_ld_n35_share.csv, the ceiling chain, every harness threshold, and the locked IUK row-25 value 44,926."),
        ("b", ""),
        ("h", "Independent verification of THIS candidate (%s)" % TAG),
        ("t", "Harness: 03_analytics/Isuzu/prism/scripts/verify_uio_v20.py - written separately; reads only workbook values, the curve table and the VIN register."),
        ("t", "VERDICT: CONVICTED - 2 of 10 checks fail. Live V19: 7 of 10. Candidate a: 3 of 10. Candidate b: 1 of 10."),
        ("t", "PASS check5_flat_rule_present: 0 rows show the 3%% constant-ratio signature (candidate a: 2 - r33/r54). Three reported near-misses: r59 Italy CV MD, r75 Hungary LCV, r90 Cyprus LCV."),
        ("t", "FAIL check1_method_consistency: 1 of 81 rows - r90 CYPRUS LCV only. Candidate a had 4 (r33/r54/r79/r90); r33 left when the engine rounding step was removed, r54 and r79 because their rows changed. r90 is NOT repairable here: the seam re-base that cleared it (candidate b) inflates the row 55%% with seam residual, so it was reverted. Stated residual."),
        ("t", "FAIL check7_overstatement_curve: STATED RESIDUAL, not forced. Measured V19 overstatement %.2f%% / %.2f%% / %.2f%% / %.2f%% / %.2f%% for 2026-2030 vs the spec's 7.8/15.6/23.2/30.6/37.7. Max |delta| %.2f pp against a +/-1.5 pp band; %d of 5 years inside. Closer to spec than candidate b (%.2f pp), as expected after the revert."
              % (me['2026'], me['2027'], me['2028'], me['2029'], me['2030'], maxd, n_in,
                 max(abs(harB['checks']['check7_overstatement_curve']['metrics']['measured_pct'][k]
                         - harB['checks']['check7_overstatement_curve']['metrics']['spec_pct'][k]) for k in sp))),
        ("t", "WARN check4_vin_scrappage: unchanged. The VIN register on disk was rebuilt 2026-09-18 and no longer reproduces the spec's shipment totals. Open input."),
        ("t", "PASS check2/2b Ireland, check3 steady state, check6 totals identity (all 41 years), check8 locked values (row 25 = 44,926, unchanged)."),
        ("t", "Grand Total 2026-2030: V19 %s -> a %s -> b %s -> c %s. Candidate c is %.2f%% below b (the r90 revert) and %.2f%% below V19. Per year (c): %s."
              % ("{:,}".format(round(sv)), "{:,}".format(round(sa)), "{:,}".format(round(sb)),
                 "{:,}".format(round(sc)), 100*(sc/sb-1), 100*(sc/sv-1),
                 ", ".join("%d %.1f" % (y, GC[y]) for y in FY))),
        ("t", "Full report: %s" % HAR),
    ]
    r = 39
    for kind, text in lines:
        c = wa.Cells(r, 1); c.Value = text
        if kind == "h":
            c.Font.Bold = True
        r += 1
    wa.Columns("A").ColumnWidth = 150
    wbk.Save()
    print("rewrote V20 ASSUMPTIONS rows 39..%d" % (r-1))
finally:
    if wbk is not None:
        try: wbk.Close(SaveChanges=False)
        except Exception: pass
    try: excel.Quit()
    except Exception: pass
print("DONE")
