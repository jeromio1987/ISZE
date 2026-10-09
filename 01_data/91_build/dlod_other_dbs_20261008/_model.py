# -*- coding: utf-8 -*-
"""Scenario model for the Don't Lose the Deal other-distributors study. Reads payload.json, writes model.json.

Per distributor d:
  P      hard-part pool, FY2026 billed, warranty removed (payload: profile_low)
  R      = u * P          ISZE billing that sits on supported cases
  S      = rho * R        support given at the distributor price (rho measured on ITUK register: 0.323)
  cost   = phi * S        what ISZE credits
  gain   = p * g * (1+b) * R   ISZE margin on jobs that really would have walked
  p*     = phi * rho / (g * (1+b))   break-even share of supported jobs that must truly be saved
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
pl = json.loads((HERE / "payload.json").read_text(encoding="utf-8"))
RHO = pl["register"]["support_over_isze_bill"]          # support euros per euro of ISZE billing on supported lines
U_REF = pl["intensity"]["u_fy26_visible"]
PHI_C, U_C, P_C = 0.5, 0.03, 0.5
AVG_BILL_RATIO = pl["rate"]["avg_isze_bill_per_line"] / next(x for x in pl["dists"] if x["code"] == "ITUK")["profile_avg_price"]


def scen(P, g, u, phi, p, rho=RHO, b=0.0):
    R = u * P
    cost = phi * rho * R
    gain = p * g * (1 + b) * R
    return dict(R=R, support=rho * R, cost=cost, gain=gain, net=gain - cost)


rows = []
for d in pl["dists"]:
    P, g = d["profile_low"], d["gm"]
    r = dict(code=d["code"], scope=d["scope"], P=P, P_high=d["profile"], g=g, uio=d["uio"], dealers=d["dealers"])
    r["p_star_phi50"] = 0.5 * RHO / g
    r["p_star_phi100"] = 1.0 * RHO / g
    r["p_star_phi25"] = 0.25 * RHO / g
    r["ceiling_u3"] = g * 0.03 * P                       # gain with p=100%, cost 0
    for u in (0.01, 0.03, 0.06, 0.10):
        for p in (0.25, 0.5, 0.75):
            s = scen(P, g, u, PHI_C, p)
            r[f"net_u{int(u*100)}_p{int(p*100)}"] = s["net"]
    c = scen(P, g, U_C, PHI_C, P_C)
    r.update(R_central=c["R"], support_central=c["support"], cost_central=c["cost"], gain_central=c["gain"], net_central=c["net"])
    r["cases_central"] = c["R"] / (AVG_BILL_RATIO * d["profile_avg_price"])
    r["cases_per_dealer"] = r["cases_central"] / d["dealers"] if d["dealers"] else None
    mpv = d["margin_per_vehicle"]
    r["margin_per_vehicle"] = mpv
    # retention break-even: vehicle-years of average spend that must be kept to repay the central cost
    r["vehicle_years_to_repay"] = c["cost"] / mpv if mpv else None
    r["vehicle_years_pct_fleet"] = r["vehicle_years_to_repay"] / d["uio"] if mpv and d["uio"] else None
    r["touched_vehicles_at_itu_rate"] = d["uio"] * pl["rate"]["vehicles_per_1000_uio_fy26_visible"] / 1000 if d["uio"] else None
    r["share_of_touched_needed_1yr"] = (r["vehicle_years_to_repay"] / r["touched_vehicles_at_itu_rate"]) if mpv and r["touched_vehicles_at_itu_rate"] else None
    r["share_of_touched_needed_3yr"] = r["share_of_touched_needed_1yr"] / 3 if r["share_of_touched_needed_1yr"] else None
    rows.append(r)


# ---- per-case economics (one supported case = one supported line at the average ticket)
for r, d in zip(rows, pl["dists"]):
    bill = AVG_BILL_RATIO * d["profile_avg_price"]
    r["bill_per_case"] = bill
    r["direct_margin_per_saved_case"] = r["g"] * bill
    r["cost_per_case_phi50"] = PHI_C * RHO * bill
    mpv = d["margin_per_vehicle"] or 0.0
    r["indirect_3y_per_saved_vehicle"] = 3 * mpv
    for delta in (0.0, 0.25, 0.5):
        r[f"p_star_delta{int(delta*100)}"] = r["cost_per_case_phi50"] / (r["direct_margin_per_saved_case"] + delta * 3 * mpv)

# ---- can the distributor fund the offer itself? support = depth * normal price; keep at least r_min margin on the offer
DEPTH = pl["register"]["support_over_dn"]
R_MIN = 0.20
selffund = []
for m in (1.3, 1.4, 1.6, pl["register"]["dn_price_over_cost"]):
    cost = 1.0
    support = DEPTH * m * cost
    room = max(0.0, m * cost - cost / (1 - R_MIN))
    isze_share = max(0.0, 1 - room / support)
    retained = 1 - cost / (m * (1 - DEPTH) * cost)
    selffund.append(dict(price_ratio=m, support_per_cost=support, room_per_cost=room, isze_share_needed=isze_share, retained_margin_on_offer=retained))
out_extra = dict(selffund=selffund, depth=DEPTH, r_min=R_MIN)

others = [x for x in rows if x["code"] != "ITUK"]
tot = {}
for u in (0.01, 0.03, 0.06, 0.10):
    for p in (0.25, 0.5, 0.75):
        tot[f"u{int(u*100)}_p{int(p*100)}"] = sum(x[f"net_u{int(u*100)}_p{int(p*100)}"] for x in others)
pool_others = sum(x["P"] for x in others)
gm_w = sum(x["P"] * x["g"] for x in others) / pool_others

# ITUK own check: does the 30k credit pay back?
it_bill_vis = pl["windows"]["fy26_visible"]["isze_bill_eur"]
g_it = next(x for x in rows if x["code"] == "ITUK")["g"]
itcheck = dict(credit=30000.0, bill_visible=it_bill_vis, p_star_if_visible_only=30000.0 / (g_it * it_bill_vis),
               p_star_if_bill_doubles=30000.0 / (g_it * it_bill_vis * 2),
               phi_if_visible_only=30000.0 / (pl["windows"]["fy26_visible"]["support_eur"] + pl["fleet_total_gbp"] * 1.17))

# blanket price cut alternative: elasticity needed to hold margin euros
def eps_star(g, x):
    return (g / (g - x) - 1) / x

blanket = {str(int(x * 100)): eps_star(pl["network_gm"], x) for x in (0.03, 0.05, 0.10)}

# size-of-prize arithmetic for context
ctx = dict(pool_others=pool_others, margin_on_pool_others=pool_others * gm_w, one_pp_price_on_pool_others=pool_others * 0.01,
           gm_weighted_others=gm_w,
           total_billed_others=sum(x["billed"] for x in pl["dists"] if x["code"] != "ITUK"),
           )
out = dict(params=dict(rho=RHO, phi=PHI_C, u=U_C, p=P_C, u_ref=U_REF, avg_bill_ratio=AVG_BILL_RATIO),
           rows=rows, totals=tot, itcheck=itcheck, blanket_eps=blanket, ctx=ctx, **out_extra)
(HERE / "model.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
print("ok", "rho", round(RHO, 3), "avg_bill_ratio", round(AVG_BILL_RATIO, 2))
