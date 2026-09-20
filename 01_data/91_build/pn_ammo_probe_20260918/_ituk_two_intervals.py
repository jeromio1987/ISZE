"""ITUK: what the 1.25 visits/yr IML rate does when it is applied to both N35 and N75.

The IML v7 rate is filters 1.25/yr = 40,000 km service interval / 50,000 km a year.
That is the N75 rate. N35 runs a 20,000 km interval, so its visits/yr is a different number.
"""

import pandas as pd

ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"
PD = ROOT + r"\03_analytics\Isuzu\prism\data"

# Fleet, from the workbook 2.B ratio applied to the pipeline's cv_std bucket.
UIO_TOTAL = 22389.0
N35_SHARE = 10_900 / 21_584           # workbook section 2.B: N35 10,900 of 21,584 N-series
N35 = 11_209.0                        # cv_std 22,190.9 x 0.5051
N75 = 10_982.0
F = 877.0

# Interval and mileage per band.
# N75: IML v7 - 40,000 km interval, 50,000 km/yr assumed  -> 1.25 visits
# N35: 20,000 km interval (deck slide 14 + Rene GIDSS NLR87/RZ4E), measured 14,494 km/yr
N75_KM_YR, N75_INTERVAL = 50_000, 40_000
N35_KM_YR, N35_INTERVAL = 14_494, 20_000

v_n75 = N75_KM_YR / N75_INTERVAL
v_n35 = N35_KM_YR / N35_INTERVAL
v_n35_if_iml = 1.25

FACTORS = {"oil_filter": 1.0, "fuel_filter": 1.0, "air_filter": 0.5, "urea_filter": 1.0,
           "blower_filter": 1.0}

print("=" * 92)
print("VISITS PER YEAR")
print("=" * 92)
print(f"  N75  40,000 km at {N75_KM_YR:,} km/yr  ->  {v_n75:.4f} visits/yr")
print(f"  N35  20,000 km at {N35_KM_YR:,} km/yr  ->  {v_n35:.4f} visits/yr")
print(f"  N35 at the IML 1.25 rate (what runs today) -> {v_n35_if_iml:.4f}")
print(f"  N35 is therefore overstated by {100*(v_n35_if_iml/v_n35 - 1):.1f}% on filters")
print()

print("=" * 92)
print("ITUK FILTER EXPECTED DEMAND: IML v7 flat 1.25 vs band intervals")
print("=" * 92)
rows = []
tot_now = tot_fix = 0.0
for cat, f in FACTORS.items():
    now = N35 * v_n35_if_iml * f + N75 * v_n75 * f
    fix = N35 * v_n35 * f + N75 * v_n75 * f
    tot_now += now
    tot_fix += fix
    rows.append({"category": cat, "expected_now": round(now), "expected_banded": round(fix),
                 "delta": round(fix - now), "delta_pct": round(100 * (fix / now - 1), 1)})
print(pd.DataFrame(rows).to_string(index=False))
print()
print(f"  five filter categories: {tot_now:,.0f} -> {tot_fix:,.0f} "
      f"({100*(tot_fix/tot_now-1):.1f}%)")

print()
print("=" * 92)
print("WHAT IT DOES TO ITUK CAPTURE (oil filter, on the IML deck's own actuals)")
print("=" * 92)
actual_oil = 9818.0      # from iml_v7_ituk_cy2025.yaml
deck_expected = 27986.0  # the deck's flat-1.25 denominator
cover_now = actual_oil / deck_expected
# Scale the deck denominator by the same ratio the banded model moves it.
ratio = (N35 * v_n35 + N75 * v_n75) / (N35 * v_n35_if_iml + N75 * v_n75)
banded_expected = deck_expected * ratio
print(f"  today      : {actual_oil:,.0f} / {deck_expected:,.0f} = {cover_now:.1%}")
print(f"  banded     : {actual_oil:,.0f} / {banded_expected:,.0f} = {actual_oil/banded_expected:.1%}")
print(f"  the cover figure moves {100*((actual_oil/banded_expected)-cover_now):+.1f} points")
print()
print("  The same correction applies to every filter category, because they all carry one flat "
      "1.25 in the IML lane. Wear parts (clutch, brake 0.5) carry their own overrides and are "
      "less affected, but ITUK brake already has its own 0.4 factor for a related reason.")
print()
print("=" * 92)
print("AND IT IS NOT ONLY ITUK — the PRISM lane has the same shape")
print("=" * 92)
print("  PRISM lane gives cv_std one rate, 0.5 visits/yr, to both truck bands:")
print("    N35 and N75 are both priced at 0.5, even though N35's interval is half as long.")
print("  A measured 14,494 km/yr N35 at a 20,000 km interval = 0.7247 visits/yr, not 0.5.")
print(f"    N35 understated on the PRISM lane by {100*(v_n35/0.5 - 1):.1f}%")
