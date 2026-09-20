"""Three-way split of a billing move, and the fleet term that turns it into a per-vehicle answer.

Reused from the method already in this workspace (``prism/modules/lost_sales_build.py``,
``build_price_layer``), which exists because the published ``revenue_waterfall.csv`` carries a mix
term that is identically zero and therefore says nothing.

The rule that makes the split real rather than an identity
---------------------------------------------------------
If price is measured at the same grain as the mix axis, ``volume + price`` equals the total by
construction and mix is always zero. Mix only exists when price is taken one level ABOVE the mix
axis. So for any node:

    P0    = sum_c (q0_c / Q0) * p0_c     the node's own weighted price in the base period
    vol   = (Q1 - Q0) * P0               more or fewer units, at the base-period price
    mix   = sum_c q1_c * p0_c - Q1 * P0  a different basket, valued at base-period prices
    price = sum_c q1_c * (p1_c - p0_c)   a different price, on the units actually sold

The three sum to ``R1 - R0`` exactly. A category with no observed price in the base period falls
back to its own later price, so the shift lands in mix rather than being invented as price.

Then, because a raw euro move still folds in the fleet:

    d_pervehicle = vol/F1 + price/F1 + mix/F1 + R0*(F0-F1)/(F0*F1)

Four terms: volume, price, mix, fleet. The last one is what you would have needed to sell just to
stand still on a bigger fleet. The four add up to the change in billed euro per vehicle.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Below this, a residual is rounding rather than a real unexplained term.
RESIDUAL_TOLERANCE_EUR = 0.51


def split_move(base: pd.DataFrame, end: pd.DataFrame) -> dict:
    """Split one period pair for one node.

    ``base`` and ``end`` carry one row per mix-axis member with ``member``, ``qty`` and ``eur``.
    """
    b = base.set_index("member") if len(base) else pd.DataFrame(columns=["qty", "eur"])
    e = end.set_index("member") if len(end) else pd.DataFrame(columns=["qty", "eur"])
    members = b.index.union(e.index)
    q0 = (b["qty"].reindex(members).fillna(0.0) if "qty" in b else pd.Series(0.0, index=members))
    q1 = (e["qty"].reindex(members).fillna(0.0) if "qty" in e else pd.Series(0.0, index=members))
    r0 = float(b["eur"].sum()) if "eur" in b else 0.0
    r1 = float(e["eur"].sum()) if "eur" in e else 0.0
    p0 = np.where(q0 > 0, (b["eur"].reindex(members).fillna(0.0) if "eur" in b else 0.0) / q0, np.nan)
    p1 = np.where(q1 > 0, (e["eur"].reindex(members).fillna(0.0) if "eur" in e else 0.0) / q1, np.nan)
    p0 = pd.Series(p0, index=members)
    p1 = pd.Series(p1, index=members)
    p0f = p0.fillna(p1).fillna(0.0)
    p1f = p1.fillna(p0).fillna(0.0)
    q_total0 = float(q0.sum())
    q_total1 = float(q1.sum())
    p_bar0 = float((q0 / q_total0 * p0f).sum()) if q_total0 > 0 else 0.0
    d_vol = (q_total1 - q_total0) * p_bar0
    d_mix = float((q1 * p0f).sum()) - q_total1 * p_bar0
    d_price = float((q1 * (p1f - p0f)).sum())
    d_tot = r1 - r0
    return {
        "r0": round(r0, 2), "r1": round(r1, 2), "delta_total": round(d_tot, 2),
        "vol": round(d_vol, 2), "price": round(d_price, 2), "mix": round(d_mix, 2),
        "q0": round(q_total0, 2), "q1": round(q_total1, 2), "p_bar0": round(p_bar0, 4),
        "residual": round(d_tot - d_vol - d_price - d_mix, 4),
        "members": [str(m) for m in members],
        "p0": {str(m): None if pd.isna(v) else round(float(v), 4) for m, v in p0.items()},
        "p1": {str(m): None if pd.isna(v) else round(float(v), 4) for m, v in p1.items()},
    }


def per_vehicle_terms(split: dict, fleet0: float | None, fleet1: float | None) -> dict:
    """Turn the euro split into the change in billed euro per vehicle, with the fleet term named.

    Returns ``None`` for every term when either fleet is missing, so the caller shows
    "not comparable" rather than a number divided by an invented denominator.
    """
    if not fleet0 or not fleet1 or fleet0 <= 0 or fleet1 <= 0:
        return {"available": False,
                "why": "the fleet for one of the two periods is not on the page"}
    f0, f1 = float(fleet0), float(fleet1)
    vol = split["vol"] / f1
    price = split["price"] / f1
    mix = split["mix"] / f1
    fleet_term = split["r0"] * (f0 - f1) / (f0 * f1)
    return {
        "available": True,
        "vol": round(vol, 2), "price": round(price, 2), "mix": round(mix, 2),
        "fleet": round(fleet_term, 2),
        "total": round(vol + price + mix + fleet_term, 2),
        "rate0": round(split["r0"] / f0, 2), "rate1": round(split["r1"] / f1, 2),
        "fleet0": round(f0), "fleet1": round(f1),
        "check": round((split["r1"] / f1) - (split["r0"] / f0)
                       - (vol + price + mix + fleet_term), 4),
    }


def thin_base(part_numbers: int, dealers: int, euro: float) -> tuple[bool, str]:
    """Is this base thick enough for a percentage to be read as a signal?"""
    if part_numbers < 5 or dealers < 2 or euro < 25_000:
        bits = []
        if part_numbers < 5:
            bits.append(f"{part_numbers} part number{'s' if part_numbers != 1 else ''}")
        if dealers < 2:
            bits.append(f"{dealers} customer{'s' if dealers != 1 else ''}")
        if euro < 25_000:
            bits.append(f"EUR {euro:,.0f}")
        return True, "a small base: " + ", ".join(bits)
    return False, ""
