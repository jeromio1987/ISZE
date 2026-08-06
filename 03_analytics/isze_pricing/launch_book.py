"""Launch price book — new-model PNs (P700, D-Max 2.2L).

Why this is a separate engine from allocation:

  New PNs have q0 = 0, so they carry ZERO weight in the Laspeyres weighted
  increase. The 3% target does not bind on them. There is also no old price for
  a distributor to compare against. So launch pricing is unconstrained by the
  price round -- and it is the only decision here that cannot be revisited: you
  can raise an existing part 3%/yr forever and never recover a launch price set
  too low.

The trade-off it models:

  For roughly the first 3-4 years no aftermarket alternative exists -- nobody
  tools for a parc that does not exist. But that is also the warranty period,
  when paid volume is low. Paid money arrives years 4-7, which is exactly when
  IAM arrives. Pricing high in the empty window mainly buys an earlier and
  steeper IAM entry.

  So the objective is not year-1 margin. It is discounted gross profit over the
  model's parts life, where launch price feeds back into retained share.

Every behavioural parameter is an [ASSUMPTION] in config.yaml. This model has no
observed elasticity behind it and must not be presented as if it does. Its value
is in ranking tactics against each other, not in forecasting a number.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------- demand
def replacement_km(raw, oil_interval_km: float) -> float:
    """Resolve a replacement interval to kilometres.

    Accepts a number, or 'svc' / 'svc2' / 'svc3' meaning 1x / 2x / 3x the
    model's oil-service interval. The token form keeps scheduled items tied to
    the interval in config, so changing 20,000 -> 15,000 km propagates instead
    of silently leaving a stale hardcoded figure in the parts file.
    """
    s = str(raw).strip().lower()
    if s.startswith("svc"):
        mult = float(s[3:]) if len(s) > 3 else 1.0
        return oil_interval_km * mult
    return float(raw)


def demand_per_vehicle_year(row, fork: str, model_cfg: dict) -> float:
    """units/vehicle/year = annual km / replacement km.

    Mileage is the honest unit here. A units-per-year figure hides both the
    duty cycle and the service interval; kilometres expose both, and both are
    things that can actually be argued about with IML or a distributor.
    """
    km = replacement_km(getattr(row, f"repl_km_{fork}"), model_cfg["oil_interval_km"])
    return model_cfg["annual_km"] / km if km > 0 else 0.0


# ---------------------------------------------------------------- price build
def fob_eur(bp_jpy: float, fx: float, source_discount: float) -> float:
    return bp_jpy / fx * source_discount


def build_price_book(parts: pd.DataFrame, cfg: dict, scenario: str) -> pd.DataFrame:
    f = cfg["formula"]
    sc = cfg["launch"]["scenarios"][scenario]
    out = parts.copy()

    out["fob_eur"] = [
        fob_eur(r.bp_jpy, f["fx_rate"], f["source_discount"][r.source])
        for r in out.itertuples()
    ]
    out["class_factor"] = out["part_class"].map(f["class_factor"])
    out["sp_class_implied"] = out["fob_eur"] / out["class_factor"]

    L = cfg["launch"]
    out["multiplier"] = out["role"].map(
        {k: v for k, v in sc.items() if k != "label"}).fillna(1.0).clip(
        L["min_multiplier"], L["max_multiplier"])
    out["sp_launch"] = out["sp_class_implied"] * out["multiplier"]

    # GP% moves with the multiplier: cost is FOB, so GP = 1 - class_factor/m
    out["gp_pct_class"] = 1 - out["class_factor"]
    out["gp_pct_launch"] = 1 - out["class_factor"] / out["multiplier"]

    out["street_eur"] = out["sp_launch"] * f["street_factor"]
    # index vs IAM street where a benchmark exists; else fall back to the
    # multiplier, i.e. treat the class-implied price as parity. [ASSUMPTION]
    out["price_index"] = np.where(
        out["iam_street_eur"] > 0,
        out["street_eur"] / out["iam_street_eur"].replace(0, np.nan),
        out["multiplier"])
    out["index_basis"] = np.where(out["iam_street_eur"] > 0, "iam_benchmark",
                                  "class_relative_fallback")
    return out


# ---------------------------------------------------------------- lifecycle
def parc_curve(model_cfg: dict, years: int,
               warranty_years: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Return (total surviving parc, parc still inside warranty) by year.

    Warranty runs per VEHICLE from its own registration, not from model launch.
    A truck registered in year 5 is still covered in year 7. In steady state a
    rolling slice of the parc is therefore always under warranty -- so the
    warranty channel is a permanent feature, not a launch-phase one.
    """
    reg = model_cfg["annual_registrations"]
    ramp = list(model_cfg["ramp"])
    ramp += [ramp[-1]] * max(0, years - len(ramp))
    surv = model_cfg["survival_rate"]

    parc = np.zeros(years)
    parc_warr = np.zeros(years)
    for t in range(years):
        for s in range(t + 1):
            alive = reg * ramp[s] * (surv ** (t - s))
            parc[t] += alive
            if (t - s) < warranty_years:
                parc_warr[t] += alive
    return parc, parc_warr


def iam_entry(price_index: float, role: str, cfg: dict) -> float:
    """Year IAM arrives, pulled forward by how far above parity you price.

    A high genuine price is precisely the signal that tells an aftermarket
    supplier a part is worth tooling for. Without this feedback the model has no
    counterforce on captive parts and drives price to infinity.
    """
    L = cfg["launch"]
    base = L["iam_entry_year"].get(role, 99)
    excess = max(0.0, float(price_index) - 1.0)
    return max(L["entry_year_min"], base - L["entry_price_sensitivity"] * excess)


def _frozen(sc: dict, role: str) -> bool:
    """freeze_after_warranty may be false, true (all roles), or a role list.

    Jerome's tactic targets parts whose early demand sits in warranty -- the
    failure-driven ones. Freezing wear parts as well is a different decision and
    should be made explicitly, not inherited.
    """
    f = sc.get("freeze_after_warranty", False)
    if isinstance(f, (list, tuple)):
        return role in f
    return bool(f)


def price_path(sp_launch: float, cfg: dict, sc: dict, role: str,
               years: int) -> np.ndarray:
    """Price by year. Optionally frozen once the warranty period ends."""
    inc = cfg["launch"]["price_path"]["annual_increase"]
    t = np.arange(years)
    eff = np.minimum(t, cfg["launch"]["warranty"]["years"]) \
        if _frozen(sc, role) else t
    return sp_launch * (1 + inc) ** eff


def index_path(prices: np.ndarray, iam_street: float, multiplier: float,
               cfg: dict, sc: dict, role: str, years: int) -> np.ndarray:
    """Competitive position by year.

    Freezing a line while the rest of the book rises makes it progressively
    cheaper in relative terms -- and that arrives at roughly the same time IAM
    does, which is the point of the tactic.
    """
    pp = cfg["launch"]["price_path"]
    t = np.arange(years)
    if iam_street and iam_street > 0:
        street = prices * cfg["formula"]["street_factor"]
        return street / (iam_street * (1 + pp["iam_annual_drift"]) ** t)
    # no benchmark: measure against a class-implied line that inflates normally
    eff = np.minimum(t, cfg["launch"]["warranty"]["years"]) \
        if _frozen(sc, role) else t
    return multiplier * (1 + pp["annual_increase"]) ** (eff - t)


def capture_curve(idx: np.ndarray, role: str, cfg: dict, years: int) -> np.ndarray:
    """Retained share of the PAID channel, year by year.

    Discrete decay toward a floor, where both the floor and the decay rate are
    recomputed each year from that year's competitive position. This is what
    lets a price freeze slow the bleed rather than only setting it at launch.
    """
    e = cfg["launch"]["erosion"]
    entry = iam_entry(float(idx[0]), role, cfg)   # tooling decision is made at launch

    cap = np.ones(years)
    for t in range(1, years):
        if t < entry:
            cap[t] = cap[t - 1]
            continue
        excess = max(0.0, float(idx[t]) - 1.0)
        floor = float(np.clip(e["floor_base"] - e["floor_sensitivity"] * excess,
                              e["floor_min"], 1.0))
        # k is the fraction of the remaining gap closed each year, so it must
        # stay inside (0, 1). Unclamped it exceeds 1 whenever the index is far
        # above parity -- which overshoots the floor and drives capture negative.
        k = float(np.clip(e["k_base"] * (1 + e["k_sensitivity"] * excess),
                          0.0, 0.95))
        cap[t] = cap[t - 1] - k * (cap[t - 1] - floor)
    return cap


def lifecycle(book: pd.DataFrame, cfg: dict, model_key: str,
              scenario: str, fork: str = "base") -> pd.DataFrame:
    """Per-PN discounted GP over the horizon, split into paid and warranty."""
    L = cfg["launch"]
    years, w = L["horizon_years"], L["warranty"]
    sc = L["scenarios"][scenario]
    m = L["models"][model_key]

    parc, parc_warr = parc_curve(m, years, w["years"])
    warr_share = np.divide(parc_warr, parc, out=np.zeros(years), where=parc > 0)
    disc = 1 / (1 + L["discount_rate"]) ** np.arange(years)
    t = np.arange(years)

    rows = []
    for r in book.itertuples():
        upv = demand_per_vehicle_year(r, fork, m)
        prices = price_path(r.sp_launch, cfg, sc, r.role, years)
        idx = index_path(prices, r.iam_street_eur, r.multiplier, cfg, sc,
                         r.role, years)
        cap = capture_curve(idx, r.role, cfg, years)

        # share of demand billed to warranty = claim rate x the rolling share
        # of the parc still inside its own warranty window
        claim = w["claim_share"].get(r.role, 0.0) * warr_share
        demand = parc * upv

        u_warr = demand * claim * w["capture"]        # no IAM substitution here
        u_paid = demand * (1 - claim) * cap
        rev_w, rev_p = u_warr * prices, u_paid * prices

        # GP% varies with the price path: cost is FOB, so GP = 1 - FOB/price
        gp_pct = 1 - (r.fob_eur / prices)
        gp = (rev_w + rev_p) * gp_pct

        rows.append({
            "model": model_key, "pn": r.pn, "description": r.description,
            "role": r.role, "predecessor": r.predecessor,
            "part_class": r.part_class,
            "fork": fork,
            "repl_km": round(replacement_km(
                getattr(r, f"repl_km_{fork}"), m["oil_interval_km"])),
            "units_per_vehicle_year": round(upv, 4),
            "sp_class_implied": round(r.sp_class_implied, 2),
            "sp_launch": round(r.sp_launch, 2),
            "price_y10": round(float(prices[-1]), 2),
            "multiplier": r.multiplier,
            "gp_pct_launch": round(float(gp_pct[0]), 4),
            "index_launch": round(float(idx[0]), 3),
            "index_y10": round(float(idx[-1]), 3),
            "index_basis": r.index_basis,
            "revenue_warranty_10y": round(rev_w.sum()),
            "revenue_paid_10y": round(rev_p.sum()),
            "revenue_10y": round(rev_w.sum() + rev_p.sum()),
            "gp_10y": round(gp.sum()),
            "gp_npv": round(float((gp * disc).sum())),
            "capture_y10": round(float(cap[-1]), 3),
        })
    return pd.DataFrame(rows)


def run_scenarios(parts: pd.DataFrame, cfg: dict, model_key: str,
                  fork: str = "base") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (per-PN detail for every scenario, scenario comparison)."""
    sub = parts[parts["model"] == model_key].copy()
    details, summary = [], []

    for name in cfg["launch"]["scenarios"]:
        book = build_price_book(sub, cfg, name)
        life = lifecycle(book, cfg, model_key, name, fork)
        life.insert(0, "scenario", name)
        details.append(life)

        by_role = life.groupby("role")["gp_npv"].sum()
        by_pred = life.groupby("predecessor")["gp_npv"].sum()
        cap_rows = life[life.role == "captive"]
        summary.append({
            "scenario": name, "fork": fork,
            "label": cfg["launch"]["scenarios"][name]["label"],
            "revenue_10y": int(life.revenue_10y.sum()),
            "rev_warranty_10y": int(life.revenue_warranty_10y.sum()),
            "gp_npv": int(life.gp_npv.sum()),
            "gp_npv_wear": int(by_role.get("wear", 0)),
            "gp_npv_captive": int(by_role.get("captive", 0)),
            "gp_npv_new_parts": int(by_pred.get("none", 0)),
            "gp_npv_carryover": int(by_pred.get("carryover", 0)),
            "capture_y10_wear": round(
                float(life[life.role == "wear"].capture_y10.mean()), 3),
            "capture_y10_captive": round(float(cap_rows.capture_y10.mean()), 3),
            "captive_index_y10": round(float(cap_rows.index_y10.mean()), 3),
        })

    det = pd.concat(details, ignore_index=True)
    summ = pd.DataFrame(summary).sort_values("gp_npv", ascending=False)
    base = summ[summ.scenario == "class_only"]["gp_npv"]
    if len(base):
        summ["vs_class_only"] = summ["gp_npv"] - int(base.iloc[0])
        summ["vs_class_only_pct"] = (summ["vs_class_only"] /
                                     int(base.iloc[0]) * 100).round(1)
    return det, summ
