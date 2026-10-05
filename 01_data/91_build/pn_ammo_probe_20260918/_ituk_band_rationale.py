"""ITUK: how should N35 and N75 be priced when their intervals differ?

Two candidate rationales, and they point in OPPOSITE directions.

  A. Interval ratio only        visits = interval ratio, so N35 = 2 x N75
                               (this is what the fix assumed: cv = 0.5 x (1 + share))

  B. Interval AND mileage       visits = km a year / km interval
                               N35: 12,891 / 20,000 ; N75: 35,478 / 40,000
                               The mileage gap (2.75x) is WIDER than the interval gap (2x),
                               so N35 needs FEWER visits than N75, not more.

Correct expected demand is always the SUM over bands, never one blended rate:
    expected = fleet_N35 x visits_N35 x factor + fleet_N75 x visits_N75 x factor
"""

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
PD = ROOT + r"\03_analytics\Isuzu\prism\data"
DER = ROOT + r"\01_data\00_derived"

R_UK = pd.read_csv(DER + r"\warranty_cv_km_age_by_market.csv").set_index("market")
km_n35 = float(R_UK.loc["UK", "km_yr_N35"])
km_n75 = float(R_UK.loc["UK", "km_yr_N75"])
INT_N35, INT_N75 = 20_000, 40_000

# The ITUK fleet, from the workbook section 2.B and the pipeline's bucket.
N35_UIO = 10_900.0
N75_UIO = 10_684.0        # 9,359 + 651 + 257 + 417 (N75 group incl. N50/N62/UNSPEC)
CV_TOTAL = 22_190.9       # pipeline cv_std bucket
SHARE = 0.5051

# IML lane: filters 1.25 visits/yr at 40,000 km and 50,000 km/yr.
IML_N75 = 50_000 / 40_000

print("=" * 100)
print("THE TWO RATIONALES FOR ITUK (oil filter, factor 1.0)")
print("=" * 100)
print(f"  measured UK mileage : N35 {km_n35:,.0f} km/yr | N75 {km_n75:,.0f} km/yr "
      f"(ratio {km_n75/km_n35:.2f}x)")
print(f"  factory intervals   : N35 {INT_N35:,} km    | N75 {INT_N75:,} km "
      f"(ratio {INT_N75/INT_N35:.2f}x)")
print()

v_a_n35 = IML_N75 * (INT_N75 / INT_N35)
v_a_n75 = IML_N75
exp_a = N35_UIO * v_a_n35 + N75_UIO * v_a_n75

v_b_n35 = km_n35 / INT_N35
v_b_n75 = km_n75 / INT_N75
exp_b = N35_UIO * v_b_n35 + N75_UIO * v_b_n75

print(f"{'':34s} {'N35 visits':>11s} {'N75 visits':>11s} {'expected':>12s}")
print(f"  A. interval ratio only        {v_a_n35:11.3f} {v_a_n75:11.3f} {exp_a:12,.0f}")
print(f"  B. interval AND measured km   {v_b_n35:11.3f} {v_b_n75:11.3f} {exp_b:12,.0f}")
print(f"  {'':32s} -> B is {100*(exp_b/exp_a-1):+.1f}% vs A")
print()
print("  Reading: on the interval alone N35 needs DOUBLE. But a Grafter drives")
print(f"  {km_n75/km_n35:.2f}x less far than an N75, which more than cancels it. So under B,")
print("  N35 needs FEWER visits than N75 — the opposite of what the fix assumed.")
print()

print("=" * 100)
print("WHAT WE ACTUALLY SHIPPED, AND WHERE IT LANDS")
print("=" * 100)
applied_rate = 0.5 * (1 + SHARE)
exp_shipped = CV_TOTAL * applied_rate
print(f"  shipped PRISM-lane cv_std rate : 0.5 x (1 + {SHARE}) = {applied_rate:.4f}")
print(f"  ITUK cv fleet                  : {CV_TOTAL:,.1f}")
print(f"  -> expected oil filter         : {exp_shipped:,.0f}")
print(f"  ratio B (measured km) on same fleet: {CV_TOTAL * SHARE * v_b_n35 + CV_TOTAL*(1-SHARE)*v_b_n75:,.0f}")
print(f"    difference: {100*((CV_TOTAL*SHARE*v_b_n35 + CV_TOTAL*(1-SHARE)*v_b_n75)/exp_shipped-1):+.1f}%")
print()
print("  So the shipped number happens to land close to rationale B on this fleet,")
print("  from the WRONG reasoning: 0.5x(1+share) assumes equal mileage, B does not.")
print("  Two errors partly cancelling is not a method.")
print()

print("=" * 100)
print("AND THE IML LANE, WHICH GOVERNS THE PUBLISHED DECK, WAS NEVER TOUCHED")
print("=" * 100)
print(f"  IML v7: UIO 22,389, filters {IML_N75} visits/yr for the WHOLE N-series,")
print(f"  expected oil filter 27,986, cover 35.1%.")
print(f"  It charges N35 the same 1.25 as N75 — exactly the defect being asked about.")
print(f"  Corrected on rationale A: {exp_a:,.0f} expected -> cover "
      f"{9_818/exp_a*100:.1f}% (from 35.1%)")
print(f"  Corrected on rationale B: {exp_b:,.0f} expected -> cover "
      f"{9_818/exp_b*100:.1f}%")
print()
print("  Both are large moves and they disagree with each other. The choice between them")
print("  is the mileage basis, which is a business answer, not a data-cleaning one.")
