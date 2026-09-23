# -*- coding: utf-8 -*-
"""
Self-check for verify_uio_v20.py — proves the harness DISCRIMINATES.

Builds a synthetic "correctly rebuilt" candidate in a temp file and asserts that
the checks which FAIL on V19 can PASS. If the harness failed this, it would only
be a machine for printing FAIL, not a verification harness.
"""
import os, sys, subprocess, json, tempfile
import openpyxl

HARNESS = r"C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\scripts\verify_uio_v20.py"
DEV = {1: 1.00, 2: 0.99, 3: 0.98, 4: 0.97, 5: 0.96, 6: 0.95, 7: 0.90, 8: 0.80,
       9: 0.70, 10: 0.55, 11: 0.40, 12: 0.30, 13: 0.20, 14: 0.10, 15: 0.05, 16: 0.00}
LCV = {1: 1.00, 2: 0.98, 3: 0.95, 4: 0.92, 5: 0.89, 6: 0.84, 7: 0.80, 8: 0.65,
       9: 0.50, 10: 0.40, 11: 0.20, 12: 0.00}
YEARS = list(range(1990, 2031))
FIRST, C0 = 1990, 7


def conv(regs, t, curve):
    return sum(regs.get(v, 0) * curve.get(t - v + 1, 0.0) for v in range(FIRST, t + 1))


def build_row(regs_hist, plan, curve, anchor_2025):
    """Rebuild a row: convolve history to 2025, then extend the convolution with plan regs."""
    r = dict(regs_hist)
    # scale so 2025 lands exactly on the declared anchor
    raw25 = conv(r, 2025, curve)
    k = anchor_2025 / raw25 if raw25 else 1.0
    r = {y: v * k for y, v in r.items()}
    out = {}
    for t in YEARS:
        if t <= 2025:
            out[t] = round(conv(r, t, curve))
        else:
            r[t] = plan.get(t, 0.0)
            out[t] = round(conv(r, t, curve))
    return out


def main():
    tmp = os.path.join(tempfile.gettempdir(), "_uio_v20_selfcheck.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "1.UIO Overview"

    # header
    for i, y in enumerate(YEARS):
        ws.cell(6, C0 + i, str(y))
    ws.cell(1, 1, "synthetic self-check candidate")

    # survival curve sheet
    cs = wb.create_sheet("3. UIO Calculation")
    cs.cell(5, 2, "Vehicle Age (Years)")
    cs.cell(5, 3, "CV - Developed")
    cs.cell(5, 5, "LCV - All")
    for a in range(1, 21):
        cs.cell(5 + a, 2, a)
        cs.cell(5 + a, 3, DEV.get(a))
        cs.cell(5 + a, 5, LCV.get(a))

    meta = {}          # row -> (ctry, country, cvlcv, model, asc, db)

    # --- Ireland CV LD, row 26: proper survival method, no flat rule ---
    ire = {1990: 860, 1991: 754, 1992: 890, 1993: 296, 1994: 203, 1995: 204,
           1996: 378, 1997: 409, 1998: 558, 1999: 582, 2000: 534, 2001: 372,
           2002: 516, 2003: 246, 2004: 618, 2005: 432, 2006: 570, 2007: 498,
           2008: 456, 2009: 0, 2010: 102, 2011: 77, 2012: 50, 2013: 69, 2014: 100,
           2015: 80, 2016: 95, 2017: 71, 2018: 89, 2019: 65, 2020: 63, 2021: 98,
           2022: 96, 2023: 71, 2024: 117, 2025: 61}
    v26 = build_row(ire, {y: 216 for y in range(2026, 2031)}, DEV, 731)
    for y, v in v26.items():
        ws.cell(26, C0 + y - FIRST, v)
    meta[26] = ("206", "IRELAND", "CV", "LD", "ISZE", "Isuzu Ireland")

    # --- Ireland LCV row 29 ---
    lreg = {y: 60 for y in range(2003, 2013)}
    lreg.update({2013: 74, 2014: 95, 2015: 154, 2016: 138, 2017: 96, 2018: 110,
                 2019: 124, 2020: 86, 2021: 113, 2022: 178, 2023: 111, 2024: 225,
                 2025: 317})
    v29 = build_row(lreg, {y: 430 for y in range(2026, 2031)}, LCV, 1338)
    for y, v in v29.items():
        ws.cell(29, C0 + y - FIRST, v)
    meta[29] = ("206", "IRELAND", "LCV", "LCV", "ISZE", "Isuzu Ireland")

    # --- UK LCV row 25: locked 44,926 and declining ---
    uk = {2019: 44904, 2020: 42742, 2021: 43482, 2022: 44968, 2023: 46592,
          2024: 48876, 2025: 47783}
    val = 47783
    for y in range(2026, 2031):
        val = val * (1 - 0.123) + 3020
        uk[y] = round(val)
    for y, v in uk.items():
        ws.cell(25, C0 + y - FIRST, v)
    meta[25] = ("205", "U KING", "LCV", "LCV", "ISZE", "IUK")

    # --- a filler row so Grand Total has something to sum ---
    for y in range(1990, 2031):
        ws.cell(40, C0 + y - FIRST, 10)
    meta[40] = ("210", "FRANCE", "CV", "LD", "ISZE", "IBX")

    # --- Israel rows (must not be silently zeroed) ---
    isr7 = {y: 4000 + (y - 1990) * 80 for y in range(1994, 2026)}
    for y in range(2026, 2031):
        isr7[y] = isr7[2025] - (y - 2025) * 60
    for y, v in isr7.items():
        ws.cell(7, C0 + y - FIRST, v)
    meta[7] = ("143", "ISRAEL", "CV", "LD", "ISZE", "UTI")

    isr8 = {y: 2500 + (y - 2018) * 120 for y in range(2018, 2026)}
    for y in range(2026, 2031):
        isr8[y] = isr8[2025] - (y - 2025) * 40
    for y, v in isr8.items():
        ws.cell(8, C0 + y - FIRST, v)
    meta[8] = ("143", "ISRAEL", "CV", "MD", "ISZE", "UTI")

    isr9 = {y: 18000 - (y - 2020) * 200 for y in range(2020, 2026)}
    for y in range(2026, 2031):
        isr9[y] = isr9[2025] - (y - 2025) * 150
    for y, v in isr9.items():
        ws.cell(9, C0 + y - FIRST, v)
    meta[9] = ("143", "ISRAEL", "LCV", "LCV", "ISZE", "UMI")

    for r, m in meta.items():
        for i, v in enumerate(m, start=1):
            ws.cell(r, i, v)

    # Grand Total row 2 = literal sum of the 7 rows the model declares.
    # The fixture writes the VALUES (no formula). That is what the harness tests, so the
    # identity check is a real comparison and not a tautology against a live SUMPRODUCT.
    total_rows = (7, 8, 9, 25, 26, 29, 40)
    for i, y in enumerate(YEARS):
        tot = sum(ws.cell(r, C0 + i).value or 0 for r in total_rows)
        ws.cell(2, C0 + i, tot)
    ws.cell(4, 2, "Exclude MIDI")

    # Sanity: the fixture must itself be internally consistent, or the tests below are
    # measuring the fixture rather than the harness.
    xs = sum(ws.cell(40, C0 + i).value or 0 for i in range(len(YEARS)))
    assert xs == 410, "filler row must not overlap rows 7:90 unexpectedly"

    wb.save(tmp)
    rep_path = os.path.join(tempfile.gettempdir(), "_uio_v20_selfcheck_report.json")

    proc = subprocess.run([sys.executable, HARNESS, "--workbook", tmp,
                           "--out", rep_path],
                          capture_output=True, text=True, encoding="utf-8")
    print(proc.stdout[-3000:])
    if proc.stderr.strip():
        print("STDERR:", proc.stderr[-2000:])

    with open(rep_path, encoding="utf-8") as fh:
        rep = json.load(fh)

    print("\n--- SELF-CHECK EXPECTATIONS ---")
    expectations = {
        "check1_method_consistency": "PASS",   # Ireland rows now one method
        "check2_ireland_rebuild": "PASS",      # 731 reproduced, no flat rule
        "check3_steady_state": "PASS",         # not settling at 7,200
        "check5_flat_rule_present": "PASS",    # no 3% signature in the output
        "check6_totals_identity": "PASS",      # Grand Total == sum of rows
        "check8_locked_values": "PASS",        # 44,926 set, Israel present, no plan-only MD
        # NOT expected to pass on a corrected candidate, and that is correct:
        # check7 compares against the V19 overstatement, which no longer applies.
        # check2b's spec anchors (1,382 / 2,527) are not reproducible from the inputs
        # on disk, so a rebuilt candidate lands elsewhere and the check reports that.
    }
    allowed_but_not_required = {"check7_overstatement_curve", "check2b_ireland_2030",
                                "check4_vin_scrappage"}
    bad = []
    for k, want in expectations.items():
        got = rep["checks"][k]["status"]
        ok = (got == want)
        if not ok:
            bad.append((k, want, got))
        print("  %-28s want=%-4s got=%-4s %s" % (k, want, got, "OK" if ok else "MISMATCH"))
    print("\n  not required to pass on a corrected candidate (reported for information):")
    for k in sorted(allowed_but_not_required):
        print("  %-28s status=%s" % (k, rep["checks"][k]["status"]))
    print("\nverdict:", rep["verdict"], "| failed:", rep["failed_checks"])
    if bad:
        print("\nSELF-CHECK FAILED:", bad)
        return 1
    print("\nSELF-CHECK PASSED — harness discriminates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
