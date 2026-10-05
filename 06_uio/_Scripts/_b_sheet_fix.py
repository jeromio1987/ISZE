"""_b_sheet_fix.py -- rewrite the V20 ASSUMPTIONS tail once, with the correct check7 numbers."""
import io, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import openpyxl, win32com.client as win32

CUR = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT"
TAG = '2026-09-22b'
CAND_B = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_%s.xlsx" % TAG)
HAR = os.path.join(CUR, "_uio_v20_B_verification_report.json")
FY = [2026, 2027, 2028, 2029, 2030]; COLS = {y: 7 + (y - 1990) for y in FY}

har = json.load(open(HAR, encoding='utf-8'))
m = har['checks']['check7_overstatement_curve']['metrics']
me, sp = m['measured_pct'], m['spec_pct']
maxd = max(abs(me[k] - sp[k]) for k in sp)
n_in = sum(1 for k in sp if abs(me[k] - sp[k]) <= 1.5)
V19S, AS, BS = 1446918, 1190448, 1197489

wb = openpyxl.load_workbook(CAND_B, data_only=True)
ws = wb["1.UIO Overview"]
gt = {y: float(ws.cell(2, COLS[y]).value) for y in FY}
wb.close()

TAIL = []
TAIL.append(("h", "Fix pass b (%s)" % TAG))
TAIL.append(("t", "FIX 1 r79 GREECE CV LD: the +14.0 x 5 straight line was a ROUNDING artefact, not a flat input. "
                  "The recovered input UIO(t)-0.97*UIO(t-1) was rounded to a whole number BEFORE the level-preserving "
                  "3-point smooth, which collapsed its ~+/-1 unit scatter. It is now smoothed at full precision, so the "
                  "row applies its own curve-driven attrition; 2030 cell 107 -> 108. Because the defect is in the engine, "
                  "the repair is applied engine-wide (23 rows move 1-2 units) - see assumptions log s.4.7."))
TAIL.append(("t", "FIX 1 - still open: no Greek CV LD registration series exists on disk (IML 6.CV Vol ctry 230 = zero "
                  "1990-2026). The row's level and its 20/yr input are both V19-derived. Flagged INPUT DERIVED in col AV."))
TAIL.append(("t", "FIX 2 new sheet 'V20 REGS USED': per row and per year 2026-2030, the registration input actually used, "
                  "the raw pre-smoothing input, the source of each, and an explicit UNRECONSTRUCTABLE block. 6 rows recover "
                  "a NEGATIVE input (r28, r43, r53, r58, r59, r69) - listed in log s.4.11, disclosed not fixed."))
TAIL.append(("t", "FIX 3 r54 PORTUGAL LCV (seam 2005) and r90 CYPRUS LCV (seam 2014): the seam detector required a negative "
                  "cohort > 25% of that year's fleet; PT 2005 was 0.25% and CY 2014 was 3.1%, so it never fired and the legacy "
                  "block was double-counted, producing negative registrations (PT 2005 -14.6 / 2006 -132.7 / 2012 -34.0; "
                  "CY 2014 -137.6). The detector is now the log's own rule (first materially negative implied cohort, < -1 unit), "
                  "SCOPED TO THESE TWO ROWS. Both flagged INPUT DERIVED - seam year."))
TAIL.append(("t", "FIX 3 - still open: the seam years are UNRECONSTRUCTABLE from the sources on disk; no positive-number guess "
                  "was made. Out-of-scope alternative measured and NOT done: applying the corrected rule to all rows moves 22 rows "
                  "and shifts the 2030 Grand Total about +1.5% (log s.4.8)."))
TAIL.append(("t", "r33 BELGIUM and r90's forecast behaviour were adjudicated CURVE and are not re-litigated. r33's own cells are "
                  "untouched; it moved only because the engine-wide rounding step was removed."))
TAIL.append(("t", "Unchanged and out of scope: V19, the v18 archive, live price lists, uio_ld_n35_share.csv, the ceiling chain, "
                  "every harness threshold, and the locked IUK row-25 value 44,926."))
TAIL.append(("b", ""))
TAIL.append(("h", "Independent verification of THIS candidate (%s)" % TAG))
TAIL.append(("t", "Harness: 03_analytics/Isuzu/prism/scripts/verify_uio_v20.py - written separately; reads only workbook values, "
                  "the curve table and the VIN register."))
TAIL.append(("t", "VERDICT: CONVICTED - 1 of 10 checks fails (candidate a: 3 of 10; live V19: 7 of 10)."))
TAIL.append(("t", "PASS check1_method_consistency: 0 of 81 rows switch method (candidate a: 4 - r33/r54/r79/r90). The fix is in "
                  "the workbook, not in the test."))
TAIL.append(("t", "PASS check5_flat_rule_present: 0 rows show the 3%% constant-ratio signature (candidate a: 2 - r33/r54). "
                  "Near-miss list fell from 5 rows to 2 (r59 Italy CV MD, r75 Hungary LCV), neither in dispute."))
TAIL.append(("t", "FAIL check7_overstatement_curve: STATED RESIDUAL, deliberately not forced. Measured V19 overstatement "
                  "%.2f%% / %.2f%% / %.2f%% / %.2f%% / %.2f%% for 2026-2030 vs the spec's 7.8/15.6/23.2/30.6/37.7. "
                  "Max |delta| %.2f pp against a +/-1.5 pp band; %d of 5 years inside. The band is narrower than the spread "
                  "between defensible implementations of the survival-curve method (the harness's own instant-rate recompute "
                  "lands at %.1f%% for 2030; this candidate at %.1f%%; the spec's curve is a different artefact again). "
                  "Repairing the two seam rows moved this candidate FURTHER below V19, which increases its distance from a spec "
                  "curve built on other arithmetic - the expected cost of FIX 3, not a regression."
                  % (me['2026'], me['2027'], me['2028'], me['2029'], me['2030'], maxd, n_in,
                     m['recomputed_pct']['2030'], me['2030'])))
TAIL.append(("t", "WARN check4_vin_scrappage: unchanged from candidate a. The VIN register on disk was rebuilt 2026-09-18 and no "
                  "longer reproduces the spec's shipment totals (Ireland 523 vs 451, Portugal 1,583 vs 1,427). Open input."))
TAIL.append(("t", "PASS check2/2b Ireland, check3 steady state, check6 totals identity (all 41 years), check8 locked values "
                  "(row 25 = 44,926, unchanged)."))
TAIL.append(("t", "Grand Total 2026-2030: V19 %s -> candidate a %s -> candidate b %s. Candidate b is +%.2f%% vs candidate a and "
                  "%.2f%% vs V19. Per year (b): %s."
                  % ("{:,}".format(V19S), "{:,}".format(AS), "{:,}".format(BS),
                     100*(BS/AS - 1), 100*(BS/V19S - 1),
                     ", ".join("%d %.1f" % (y, gt[y]) for y in FY))))
TAIL.append(("t", "Full report: %s" % HAR))

excel = win32.DispatchEx("Excel.Application")
excel.Visible = False; excel.DisplayAlerts = False
wbk = None
try:
    wbk = excel.Workbooks.Open(CAND_B, UpdateLinks=0, ReadOnly=False)
    wa = wbk.Worksheets("V20 ASSUMPTIONS")
    # clear everything from row 39 down, then rewrite the tail once
    last = wa.Cells(wa.Rows.Count, 1).End(-4162).Row
    if last >= 39:
        wa.Range("A39:A%d" % max(last, 200)).ClearContents()
    r = 39
    for kind, text in TAIL:
        c = wa.Cells(r, 1)
        c.Value = text
        if kind == "h":
            c.Font.Bold = True
        r += 1
    wa.Columns("A").ColumnWidth = 150
    print("rewrote V20 ASSUMPTIONS rows 39..%d" % (r - 1))
    wbk.Save()
finally:
    if wbk is not None:
        try: wbk.Close(SaveChanges=False)
        except Exception: pass
    try: excel.Quit()
    except Exception: pass

wb = openpyxl.load_workbook(CAND_B, data_only=True)
wa = wb["V20 ASSUMPTIONS"]
print("dims after:", wa.dimensions)
for i, row in enumerate(wa.iter_rows(min_row=38, max_row=wa.max_row, max_col=1, values_only=True), 38):
    if row[0]:
        print("%3d| %s" % (i, str(row[0])[:120]))
wb.close()
