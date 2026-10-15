"""Brake pad SPA exercise numbers — ITUK CY2025."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data/00_derived"
OUT = ROOT / "02_dashboards/pricing/_build/_tmp_brake_pad_spa_exercise_20261015.json"

df = pd.read_parquet(DER / "sales_fact.parquet")
ituk = df[df["sold_to_sap"].astype(str).str.replace(".0", "", regex=False) == "2575"].copy()
ituk["billing_date"] = pd.to_datetime(ituk.billing_date, errors="coerce")
ituk["pn"] = ituk.part_number.astype(str).str.replace(r"\.0$", "", regex=True)

kit_pn = "8982447940"
kit = ituk[(ituk.pn == kit_pn) & (ituk.billing_date >= "2025-01-01") & (ituk.billing_date < "2026-01-01")]
k_qty = float(kit.billed_qty.sum())
k_eur = float(kit.net_sales_value.sum())
k_asp = k_eur / k_qty if k_qty else 0.0

cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
ituk_pad = cap[(cap.distributor_code == "ITUK") & (cap.pms_category == "brake_pad") & (cap.line_type == "total") & (cap.year == 2025)].iloc[0]
base_qty = float(ituk_pad.actual_qty)
base_eur = float(ituk_pad.actual_rev_eur)
base_asp = float(ituk_pad.avg_sp_eur)
expected = float(ituk_pad.expected_qty)
capture = float(ituk_pad.capture_rate)
uio = float(ituk_pad.uio_units)
gap_eur = float(ituk_pad.revenue_gap_eur)

ela = pd.read_csv(DER / "price_volume_elasticity.csv")
pad_beta = float(ela.loc[ela.category == "brake_pad", "beta_elasticity"].iloc[0])
pad_se = float(ela.loc[ela.category == "brake_pad", "se_beta"].iloc[0])
brakes_beta = float(ela.loc[ela.category == "AIM: Brakes", "beta_elasticity"].iloc[0])

def scen(label, qty0, eur0, asp0, gm0, d_price, beta, mode="ce"):
    new_asp = asp0 * (1 + d_price)
    d_qty = ((1 + d_price) ** beta - 1) if mode == "ce" else (beta * d_price)
    new_qty = qty0 * (1 + d_qty)
    new_eur = new_qty * new_asp
    cost_u = asp0 * (1 - gm0)
    profit0 = eur0 - qty0 * cost_u
    profit1 = new_eur - new_qty * cost_u
    gm1 = 1 - cost_u / new_asp if new_asp else None
    return {
        "label": label, "d_price_pct": round(d_price * 100, 1), "beta": beta, "mode": mode,
        "qty0": round(qty0, 1), "qty1": round(new_qty, 1), "d_qty_pct": round(d_qty * 100, 1),
        "eur0": round(eur0, 0), "eur1": round(new_eur, 0),
        "d_eur_pct": round((new_eur / eur0 - 1) * 100, 1) if eur0 else None,
        "profit0": round(profit0, 0), "profit1": round(profit1, 0),
        "d_profit_pct": round((profit1 / profit0 - 1) * 100, 1) if profit0 else None,
        "gm0_pct": round(gm0 * 100, 1), "gm1_pct": round(gm1 * 100, 1) if gm1 is not None else None,
        "capture1": round(new_qty / expected, 3) if expected else None,
    }

GM0 = 0.53
scenarios = []
for beta, name in [(pad_beta, "brake_pad reading"), (brakes_beta, "AIM Brakes reading"), (-4.0, "claimed -4"), (-0.81, "dealer stress"), (-0.1584, "dealer central")]:
    scenarios.append(scen(f"{name} / linear", base_qty, base_eur, base_asp, GM0, -0.20, beta, "linear"))
    scenarios.append(scen(f"{name} / CE", base_qty, base_eur, base_asp, GM0, -0.20, beta, "ce"))
scenarios.append(scen("kit / pad CE", k_qty, k_eur, k_asp, GM0, -0.20, pad_beta, "ce"))
scenarios.append(scen("kit / claimed linear", k_qty, k_eur, k_asp, GM0, -0.20, -4.0, "linear"))

payload = {
    "as_of": "2026-10-15", "window": "CY2025", "distributor": "ITUK", "sold_to": 2575,
    "family": {"pms_category": "brake_pad", "uio_units": uio, "expected_qty": expected,
               "actual_qty": base_qty, "actual_rev_eur": base_eur, "avg_sp_eur": base_asp,
               "capture_rate": capture, "revenue_gap_eur": gap_eur},
    "kit_8982447940": {"qty": k_qty, "eur": round(k_eur, 2), "asp_eur": round(k_asp, 2),
                       "share_of_family_eur": round(k_eur / base_eur, 3) if base_eur else None},
    "elasticity": {"brake_pad_beta": pad_beta, "brake_pad_se": pad_se,
                   "brake_pad_ci95": [round(pad_beta - 1.96 * pad_se, 2), round(pad_beta + 1.96 * pad_se, 2)],
                   "aim_brakes_beta": brakes_beta},
    "gm0_assumption_pct": 53.0,
    "break_even_at_minus_20pct_price": {"qty_for_same_eur_pct": 25.0, "qty_for_same_profit_pct": round((0.53/0.33-1)*100, 1)},
    "scenarios_minus_20pct_price": scenarios,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(OUT)
for s in scenarios:
    print(f"{s['label']:40} qty {s['d_qty_pct']:+6.1f}%  eur {s['d_eur_pct']:+6.1f}%  profit {s['d_profit_pct']:+6.1f}%  gm {s['gm0_pct']}->{s['gm1_pct']}")
