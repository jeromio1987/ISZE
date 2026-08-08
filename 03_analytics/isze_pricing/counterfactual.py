"""Counterfactual pricing policies and the price bridge.

Two questions this answers, and the second matters more than the first.

1. WHAT WOULD THE OLD WAY HAVE GIVEN? Turnover and margin under each policy,
   so the differentiated engine can be judged against the alternative rather
   than presented on its own.

2. WHERE DID A PRICE CHANGE ACTUALLY COME FROM? Any movement in SP decomposes
   exactly into IML base price, FX, source mix, class factor, and an ISZE
   residual. That residual is the only part we chose.

The second is the one to take to a distributor. "Oldskool markup" turns out not
to be a single method:

    (a) STRICT cost-plus - re-derive SP = FOB/class_factor each year and accept
        whatever it gives. The increase is not chosen; cost and FX decide it.
    (b) TARGET markup - apply a chosen % to last year's price. This is what
        actually happens, and it is a margin decision wearing a cost-plus coat.

They currently point in opposite directions. FY2023 -> FY2026 FX moved
146.6 -> 163.7 JPY/EUR, so at constant BP_JPY strict cost-plus would have
CUT prices ~10.4%. ISZE applied +5.3%. Either BP_JPY rose ~17.6% to cover it,
or the difference is margin. The bridge below says which, per part.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------- primitives
def fob(bp_jpy, fx, disc):
    return bp_jpy / fx * disc


def sp_formula(bp_jpy, fx, disc, class_factor):
    """The IML formula. No ISZE judgement in here at all."""
    return fob(bp_jpy, fx, disc) / class_factor


# ---------------------------------------------------------------- price bridge
BRIDGE_TERMS = ["bp_effect", "fx_effect", "source_effect",
                "class_effect", "isze_decision"]


def bridge(df: pd.DataFrame, weight: str = "rev_prior") -> pd.DataFrame:
    """Decompose an actual price change into its drivers.

    Needs, per part: bp_jpy_prior/new, fx_prior/new, disc_prior/new,
    class_factor_prior/new, sp_actual_prior/new, and a weight.

    Exact by construction. SP = (BP/FX x d)/cf, so

        ln(SP1/SP0) = ln(BP1/BP0) - ln(FX1/FX0) + ln(d1/d0) - ln(cf1/cf0)

    and whatever the actual price did beyond that is the ISZE decision. Log
    contributions are rescaled to the arithmetic total so the terms sum to the
    headline percentage rather than to a log approximation of it.
    """
    d = df.copy()
    d["sp_formula_prior"] = sp_formula(d.bp_jpy_prior, d.fx_prior,
                                       d.disc_prior, d.class_factor_prior)
    d["sp_formula_new"] = sp_formula(d.bp_jpy_new, d.fx_new,
                                     d.disc_new, d.class_factor_new)

    ln = np.log
    d["l_bp"] = ln(d.bp_jpy_new / d.bp_jpy_prior)
    d["l_fx"] = -ln(d.fx_new / d.fx_prior)
    d["l_src"] = ln(d.disc_new / d.disc_prior)
    d["l_cls"] = -ln(d.class_factor_new / d.class_factor_prior)
    d["l_total"] = ln(d.sp_actual_new / d.sp_actual_prior)
    # everything the formula does not explain
    d["l_isze"] = d.l_total - (d.l_bp + d.l_fx + d.l_src + d.l_cls)

    # rescale log parts onto the arithmetic change so the walk reconciles
    arith = d.sp_actual_new / d.sp_actual_prior - 1
    scale = np.where(np.abs(d.l_total) > 1e-12, arith / d.l_total, 1.0)
    for src, dst in [("l_bp", "bp_effect"), ("l_fx", "fx_effect"),
                     ("l_src", "source_effect"), ("l_cls", "class_effect"),
                     ("l_isze", "isze_decision")]:
        d[dst] = d[src] * scale
    d["total_change"] = arith
    return d


def bridge_summary(d: pd.DataFrame, weight: str = "rev_prior") -> pd.Series:
    """Revenue-weighted bridge for the portfolio. Terms sum to the total."""
    w = d[weight] / d[weight].sum()
    out = {t: float((w * d[t]).sum()) for t in BRIDGE_TERMS}
    out["total_change"] = float((w * d.total_change).sum())
    out["reconciliation_error"] = out["total_change"] - sum(
        out[t] for t in BRIDGE_TERMS)
    return pd.Series(out)


# ---------------------------------------------------------------- policies
def policy_prices(d: pd.DataFrame, policy: str, cfg: dict,
                  engine_delta: pd.Series | None = None) -> pd.Series:
    """New SP under a named policy."""
    if policy == "cost_plus_strict":
        # re-derive from cost. The increase is whatever cost and FX give.
        return sp_formula(d.bp_jpy_new, d.fx_new, d.disc_new, d.class_factor_new)
    if policy == "frozen":
        return d.sp_actual_prior.copy()
    if policy == "uniform_target":
        return d.sp_actual_prior * (1 + cfg["allocation"]["target"])
    if policy == "engine":
        if engine_delta is None:
            raise ValueError("engine policy needs engine_delta")
        return d.sp_actual_prior * (1 + engine_delta.reindex(d.index).fillna(0))
    if policy == "market_based":
        # price every benchmarked line to its target position, ignore the index
        # constraint entirely. The unconstrained ideal, not a proposal.
        tgt = d.get("target_street_eur")
        if tgt is None:
            raise ValueError("market_based needs target_street_eur")
        sf = cfg["formula"]["street_factor"]
        return np.where(tgt > 0, tgt / sf, d.sp_actual_prior)
    raise ValueError(f"unknown policy {policy}")


def evaluate(d: pd.DataFrame, cfg: dict, policies: list[str],
             engine_delta: pd.Series | None = None,
             volume_model: str = "constant") -> pd.DataFrame:
    """Turnover and margin per policy.

    volume_model='constant' holds units at prior-year levels. That is a
    DELIBERATE limitation, not an oversight: with no measured elasticity a
    volume response would be invented, and differentiation would then look
    good or bad purely by assumption. Constant volume makes this pure price
    arithmetic and honest about it. Once DB->DLR history accumulates the same
    function becomes a backtest with a real volume term.
    """
    rows = []
    for p in policies:
        sp = pd.Series(policy_prices(d, p, cfg, engine_delta), index=d.index)
        units = d.units_prior
        rev = sp * units
        cost = fob(d.bp_jpy_new, d.fx_new, d.disc_new) * units
        gp = rev - cost
        w = d.rev_prior / d.rev_prior.sum()
        rows.append({
            "policy": p,
            "turnover": float(rev.sum()),
            "gp_eur": float(gp.sum()),
            "gp_pct": float(gp.sum() / rev.sum()) if rev.sum() else np.nan,
            "weighted_change": float((w * (sp / d.sp_actual_prior - 1)).sum()),
            "max_line_increase": float((sp / d.sp_actual_prior - 1).max()),
            "min_line_change": float((sp / d.sp_actual_prior - 1).min()),
            "lines_up": int((sp > d.sp_actual_prior).sum()),
            "lines_down": int((sp < d.sp_actual_prior).sum()),
            "volume_model": volume_model,
        })
    out = pd.DataFrame(rows)
    base = out[out.policy == "frozen"]
    if len(base):
        out["gp_vs_frozen"] = out.gp_eur - float(base.gp_eur.iloc[0])
    return out
