"""Two-level pricing: ISZE -> DB and DB -> DLR.

Everything in this engine currently runs on one plane: what ISZE invoices to
distributors. That plane measures DISTRIBUTOR STOCKING BEHAVIOUR, not end-market
demand. It is the reason elasticity was ruled unmeasurable - ISZE sits too far
from the market to see a demand curve.

Dealer sell-out from Jan 2025 adds the second plane and changes three things.

1. THE INDEX WEIGHTS ARE CURRENTLY SELF-BIASING.
   The weighted increase is a Laspeyres index on L12M ISZE->DB volume. Announce
   an increase with notice and distributors buy ahead of it. That pre-buy
   inflates L12M volume on exactly the parts that went up, which OVERWEIGHTS
   those same parts in next year's index. The measurement instrument is bent by
   the action it measures. Weighting on DB->DLR removes the loop, because a
   dealer does not pre-buy on an ISZE price letter.

2. PASS-THROUGH BECOMES OBSERVABLE.
   Today a 3% list increase is assumed to reach the market as 3%. It may reach
   it as 0% on competed lines the distributor absorbs, and as 6% on captive
   lines where they take the opportunity. Until now that was unknowable.

3. THE 1.785 STREET FACTOR STOPS BEING AN ASSUMPTION.
   1.40 distributor x 1.275 dealer is a flat guess applied to 18 distributors
   with GP% ranging 40.8 to 47.1. Plane B measures it per distributor per
   category instead.

Design rule: OPTIMISE ON PLANE B, CONSTRAIN ON PLANE A. Demand evidence and
competitive position come from sell-out; the negotiated weighted increase is
still declared and measured on ISZE->DB, because that is what a distributor
audits. The bridge between them is itself a measurable object with diagnostics.

Until sell-out data lands, every function here degrades to plane A and records
basis MISSING rather than silently substituting.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PLANE_A = "isze_to_db"
PLANE_B = "db_to_dlr"

# Minimum columns a sell-out extract must carry to be usable.
SELLOUT_CONTRACT = ["period", "distributor_code", "dealer_code",
                    "part_number", "units", "net_value_eur"]


def load_sellout(path: Path | None) -> tuple[pd.DataFrame | None, dict]:
    """Load DB->DLR sell-out. Returns (frame, report)."""
    rep = {"basis": "MISSING", "path": str(path) if path else None,
           "rows": 0, "missing_columns": [], "periods": None,
           "distributors": 0, "dealers": 0}
    if not path or not Path(path).exists():
        rep["note"] = ("sell-out not available; all weighting and evidence "
                       "falls back to plane A")
        return None, rep
    df = pd.read_csv(path, dtype={"part_number": str})
    miss = [c for c in SELLOUT_CONTRACT if c not in df.columns]
    if miss:
        rep["missing_columns"] = miss
        rep["note"] = "contract not met; refusing to use a partial extract"
        return None, rep
    rep.update(basis="db_to_dlr", rows=len(df),
               periods=[str(df.period.min()), str(df.period.max())],
               distributors=int(df.distributor_code.nunique()),
               dealers=int(df.dealer_code.nunique()))
    return df, rep


def weights(plane_a: pd.DataFrame, sellout: pd.DataFrame | None,
            key: list[str], plane: str = PLANE_A) -> tuple[pd.Series, str]:
    """Index weights from the requested plane, with the basis used.

    Plane A weights carry the pre-buy loop described above. Prefer plane B for
    weighting as soon as a full twelve months of sell-out exists - a partial
    year would bias toward whatever is seasonal in the months held.
    """
    if plane == PLANE_B and sellout is not None:
        g = sellout.groupby(key).net_value_eur.sum()
        return g, "db_to_dlr"
    return plane_a.groupby(key).rev_prior.sum(), "isze_to_db"


def passthrough(plane_a: pd.DataFrame, sellout: pd.DataFrame,
                key: list[str]) -> pd.DataFrame:
    """How much of an ISZE price movement reached the dealer.

    ratio = 1.0  full pass-through
          < 1.0  distributor absorbing - typically competed lines, and a signal
                 the increase is landing where the market will not carry it
          > 1.0  distributor amplifying - typically captive lines; margin the
                 increase created but that ISZE did not capture
    """
    a = plane_a.groupby(key).agg(
        isze_price_prior=("sp_actual_prior", "mean"),
        isze_price_new=("sp_actual_new", "mean"))
    b = (sellout.assign(unit_price=lambda d: d.net_value_eur / d.units.replace(0, np.nan))
         .groupby(key + ["period"]).unit_price.mean().unstack("period"))
    if b.shape[1] < 2:
        return pd.DataFrame()
    first, last = b.columns[0], b.columns[-1]
    out = a.join(pd.DataFrame({"dlr_price_prior": b[first],
                               "dlr_price_new": b[last]}))
    out["isze_change"] = out.isze_price_new / out.isze_price_prior - 1
    out["dlr_change"] = out.dlr_price_new / out.dlr_price_prior - 1
    out["passthrough"] = np.where(np.abs(out.isze_change) > 1e-6,
                                  out.dlr_change / out.isze_change, np.nan)
    out["verdict"] = np.select(
        [out.passthrough < 0.7, out.passthrough > 1.3],
        ["distributor absorbing", "distributor amplifying"], "broadly passed on")
    return out.reset_index()


def stocking_delta(plane_a: pd.DataFrame, sellout: pd.DataFrame,
                   key: list[str]) -> pd.DataFrame:
    """Units bought from ISZE minus units sold to dealers.

    Persistently positive = channel building stock, so ISZE->DB flatters real
    demand and a correction is coming. Persistently negative = destocking, so
    ISZE->DB understates demand. Either way, pricing off plane A alone reads
    the wrong signal for as long as the swing lasts.
    """
    a = plane_a.groupby(key).units_prior.sum().rename("units_in")
    b = sellout.groupby(key).units.sum().rename("units_out")
    out = pd.concat([a, b], axis=1).fillna(0)
    out["delta_units"] = out.units_in - out.units_out
    out["stock_swing_pct"] = np.where(
        out.units_out > 0, out.delta_units / out.units_out, np.nan)
    out["flag"] = np.select(
        [out.stock_swing_pct > 0.15, out.stock_swing_pct < -0.15],
        ["building stock", "destocking"], "balanced")
    return out.reset_index()


def channel_margin(plane_a: pd.DataFrame, sellout: pd.DataFrame,
                   key: list[str]) -> pd.DataFrame:
    """Measured distributor margin, replacing the assumed 1.40 factor."""
    a = plane_a.groupby(key).sp_actual_new.mean().rename("isze_price")
    b = (sellout.assign(up=lambda d: d.net_value_eur / d.units.replace(0, np.nan))
         .groupby(key).up.mean().rename("dlr_price"))
    out = pd.concat([a, b], axis=1).dropna()
    out["measured_db_factor"] = out.dlr_price / out.isze_price
    out["assumed_db_factor"] = 1.40
    out["variance_pp"] = (out.measured_db_factor - 1.40) * 100
    return out.reset_index()


def report(plane_a: pd.DataFrame, sellout: pd.DataFrame | None,
           key: list[str]) -> dict:
    """Everything the second plane can currently tell us."""
    if sellout is None:
        return {"basis": "MISSING",
                "note": "no sell-out extract; single-plane operation"}
    pt = passthrough(plane_a, sellout, key)
    sd = stocking_delta(plane_a, sellout, key)
    cm = channel_margin(plane_a, sellout, key)
    return {
        "basis": "db_to_dlr",
        "median_passthrough": None if pt.empty else round(
            float(pt.passthrough.median()), 3),
        "cells_absorbing": None if pt.empty else int(
            (pt.verdict == "distributor absorbing").sum()),
        "cells_amplifying": None if pt.empty else int(
            (pt.verdict == "distributor amplifying").sum()),
        "cells_building_stock": int((sd.flag == "building stock").sum()),
        "cells_destocking": int((sd.flag == "destocking").sum()),
        "median_measured_db_factor": None if cm.empty else round(
            float(cm.measured_db_factor.median()), 3),
    }
