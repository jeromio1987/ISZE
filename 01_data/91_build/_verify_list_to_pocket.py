import pandas as pd

d = "C:/Users/jerom/Desktop/claude/ISZE/01_data/00_derived/"
net = pd.read_csv(d + "pr00_realization_network_cy.csv")
print("=== year -> pr00_source (year-matching evidence) ===")
print(net[["year", "period", "pr00_source", "coverage_pct", "realization_pct"]].to_string(index=False))
print()
print("=== formula check: realization == matched_eur / list_value_eur ===")
ok = True
for _, r in net.iterrows():
    calc = r["matched_eur"] / r["list_value_eur"] * 100 if r["list_value_eur"] else None
    calc_cov = r["matched_eur"] / r["parts_eur"] * 100 if r["parts_eur"] else None
    stored = r["realization_pct"]
    stored_cov = r["coverage_pct"]
    r_ok = abs((stored or 0) - (calc or 0)) < 0.01
    c_ok = abs((stored_cov or 0) - (calc_cov or 0)) < 0.01
    ok = ok and r_ok and c_ok
    print(f"{int(r['year'])}: realization {stored} vs calc {calc:.2f} [{('OK' if r_ok else 'MISMATCH')}] | coverage {stored_cov} vs calc {calc_cov:.2f} [{('OK' if c_ok else 'MISMATCH')}]")
print()
print("ALL FORMULAS CONSISTENT:", ok)
