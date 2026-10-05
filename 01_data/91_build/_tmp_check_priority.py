import pandas as pd

from pathlib import Path

P = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing\AIM_PRIORITY_LIST.csv")
g = pd.read_csv(P, dtype={"part_number": str})
print("rows", len(g), "| cols", len(g.columns))
print("billed EUR", round(g["l12m_billed_eur"].sum(), 2))
print("step EUR  ", round(g["step_eur"].sum(), 2))
print()
print("=== TOP 25 BY STEP (the pricing priority head) ===")
t = g.head(25)
for _, r in t.iterrows():
    print("%3d %-12s %10s %9s %7s | %-34s | %s > %s" % (
        r["priority_rank"], r["part_number"], round(r["l12m_billed_eur"]),
        round(r["step_eur"]), (f"{r['delta_pct']:.2f}" if pd.notna(r["delta_pct"]) else "n/a"),
        str(r["billed_description"])[:34], str(r["aim_l1"])[:18], str(r["aim_l2"])[:18]))
print()
print("=== STEP BY CORRECTED AIM L1 ===")
s = (g.groupby("aim_l1").agg(pn=("part_number", "size"), billed=("l12m_billed_eur", "sum"),
                             step=("step_eur", "sum")).sort_values("step", ascending=False))
s["billed_%"] = (100 * s["billed"] / g["l12m_billed_eur"].sum()).round(2)
s["step_%"] = (100 * s["step"] / g["step_eur"].sum()).round(2)
print(s.round(0).to_string())
print()
print("=== PMS FLAG SPLIT ===")
print(g.groupby("pms_flag").agg(pn=("part_number", "size"), billed=("l12m_billed_eur", "sum"),
                                step=("step_eur", "sum")).round(0).to_string())
print()
print("=== how much of the step is in the top N ===")
for n in (10, 25, 50, 100, 250, 500, 1000):
    print(f"  top {n:>5}: {g.iloc[n-1]['cum_step_share_pct']:.1f}%")
