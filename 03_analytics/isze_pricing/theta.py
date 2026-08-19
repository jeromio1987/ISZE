"""Momentum (theta) — spec section 6.

theta = expected forward volume / L12M volume. Under C6 the index is charged on
last year's volume while cash accrues on next year's, so euros returned per basis
point of index spent scale with theta. A cell with a shrinking parc should not be
asked to carry the same increase as one with a growing parc.

Spec section 6 factors theta into four components:

    theta = theta_parc x theta_interval x theta_cohort x theta_warranty

**Only theta_parc is implemented here.** It is the one the spec marks Available.
theta_interval stays blocked on the chassis-code -> model-year / SCR mapping,
which is the highest-value unblock in the spec and is not derivable from anything
on hand. theta_cohort and theta_warranty are Partial. Multiplying in a component
we cannot source would put an invented number inside a price change, so the other
three are left at 1.0 and the gap is reported rather than filled.

Source: 01_data/00_derived/UIO_carpark_for_GPS_recalc_2026-07-30.csv — the
corrected car park behind the GPS recalculation. Its own documentation is
emphatic about what it is and is not, and that carries through to here:

  - CY2025 is an actual anchor and does not move.
  - Exactly one CY2026 figure is exact (IUK LCV = 44,926, locked 30 Jul 2026).
  - Everything else corrected is a constant-hazard estimate (10.2% CV /
    12.3% LCV) that sizes the error. The full V20 cohort rebuild will differ by
    a few per cent.
  - Israel CV (UTI) is a known unfixed defect — missing weight classes, ~23% low.
  - UK CV (ITUK) is deliberately unchanged; it already runs a proper cohort
    survival model with an age floor.

So each theta carries a basis, and `theta.require_basis` in config.yaml decides
which bases may move a price — the same gate `allocation.require_basis` applies
to the premium. A parc estimate the car park itself flags as defective does not
get to move money just because it is a number.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Ranked weakest -> strongest. A group mixing statuses takes the weakest.
BASIS_RANK = [
    "no_parc",              # no car park rows, or zero wallet both years
    "uio_known_defect",     # car park flags this row as not fixed
    "uio_constant_hazard",  # corrected by constant-hazard estimate
    "uio_cohort_model",     # proper cohort survival model, not touched by the fix
    "uio_locked",           # exact, locked figure
]


def _weakest(bases) -> str:
    idx = [BASIS_RANK.index(b) if b in BASIS_RANK else 0 for b in bases]
    return BASIS_RANK[min(idx)] if idx else "no_parc"


def require_list(v, name: str) -> list:
    """A basis allowlist must be a list. Reject a bare string loudly.

    set('[a,b]') is a set of characters, which fails every membership test and
    holds the whole layer flat without raising. A config gate that silently
    stops gating is worse than one that breaks.
    """
    if isinstance(v, str):
        raise TypeError(
            f"{name} must be a list, got the string {v!r}. "
            f"A string here degrades to a set of characters and silently holds "
            f"every row flat. Quote it properly: --set {name}='[\"a\",\"b\"]', "
            f"or use the bare form --set {name}=[a,b]")
    return list(v or [])


def load_carpark(path: Path) -> pd.DataFrame:
    """Read the corrected car park, dropping MIDI.

    MIDI Europe is not an ISZE distributor and is excluded from every total.
    (The live UIO workbook's own MIDI filter is set to Include, so its Grand
    Total is contaminated — that trap does not reach here.)
    """
    cp = pd.read_csv(path)
    return cp[~cp["is_MIDI_exclude"].astype(bool)].copy()


def theta_table(carpark: pd.DataFrame, key: str, status_basis: dict) -> pd.DataFrame:
    """Wallet-weighted theta_parc per `key` (distributor_DB or country).

    Weighting by wallet rather than by units is deliberate. wallet = UIO x
    target rate, and the rate is constant per model_type across both years, so
    the wallet-weighted ratio is the rate-weighted UIO ratio: each model_type
    counts for what it is worth in euros, not how many units it has. An LCV unit
    at EUR 250/yr should not swing the answer as hard as an MD unit at EUR 887.
    """
    g = carpark.groupby(key).agg(
        w25=("wallet_CY2025_eur", "sum"),
        w26=("wallet_CY2026_corrected_eur", "sum"),
        statuses=("status", lambda s: sorted(set(s))),
    )
    g["theta_parc"] = g.w26 / g.w25.where(g.w25 > 0)
    g["basis"] = [
        "no_parc" if pd.isna(t)
        else _weakest([status_basis.get(s, "no_parc") for s in ss])
        for t, ss in zip(g.theta_parc, g.statuses)
    ]
    g["status"] = ["|".join(ss) for ss in g.statuses]
    return g.drop(columns=["statuses"])


def bucket(theta: float, bounds: dict) -> str:
    """Spec section 6 V1 simplification: bucket rather than compute."""
    if theta is None or (isinstance(theta, float) and np.isnan(theta)):
        return "stable"          # unknown parc is neutral, never a price move
    if theta < bounds["declining_below"]:
        return "declining"
    if theta > bounds["growing_above"]:
        return "growing"
    return "stable"


def attach(df: pd.DataFrame, cfg: dict, carpark_path: Path | None = None
           ) -> tuple[pd.DataFrame, dict]:
    """Attach theta_parc, its basis and its bucket to an engine frame.

    Joins on `db`. The action map mixes granularity — most cells carry a country
    (BELGIUM, GREECE) but the two markets with more than one distributor carry
    the distributor instead (ITUK/IUK in the UK, UMI/UTI in Israel). Matching
    distributor_DB first and falling back to country handles both, and it
    matters: those four are EUR 3.27M of EUR 5.77M captured, and they split.
    IUK's LCV parc is falling 6.0% while ITUK's CV parc rises 4.8% — a single
    U KING theta would net those two against each other and lose both signals.

    Returns (frame, report). Never raises on a missing car park: the package is
    meant to run, be tested and be modified without external data, so an absent
    file degrades to a flat theta and says so in the report.
    """
    t = cfg.get("theta", {})
    out = df.copy()
    out["theta_parc"] = np.nan
    out["theta_basis"] = "unwired"
    out["theta_join"] = "none"
    out["theta_bucket"] = "stable"

    report = {"theta_source": "DISABLED", "n_cells": len(out)}
    if not t.get("enabled", False):
        return out, report

    path = Path(carpark_path or t["carpark"])
    if not path.exists():
        report["theta_source"] = f"MISSING::{path}"
        return out, report

    cp = load_carpark(path)
    status_basis = t.get("status_basis", {})
    by_db = theta_table(cp, "distributor_DB", status_basis)
    by_country = theta_table(cp, "country", status_basis)
    alias = t.get("country_alias", {})

    def resolve(db):
        if db in by_db.index:
            r = by_db.loc[db]
            return r.theta_parc, r.basis, "distributor"
        c = alias.get(db, db)
        if c in by_country.index:
            r = by_country.loc[c]
            return r.theta_parc, r.basis, "country"
        return np.nan, "no_parc", "unmatched"

    res = [resolve(d) for d in out["db"]]
    out["theta_parc"] = [r[0] for r in res]
    out["theta_basis"] = [r[1] for r in res]
    out["theta_join"] = [r[2] for r in res]

    bounds = cfg["allocation"]["theta_bounds"]
    ungated = [bucket(x, bounds) for x in out["theta_parc"]]
    out["theta_bucket_ungated"] = ungated

    # The gate. A basis outside require_basis does not move a price.
    require = set(require_list(t.get("require_basis"), "theta.require_basis"))
    ok = out["theta_basis"].isin(require)
    out["theta_gated"] = ~ok
    out["theta_bucket"] = np.where(ok, ungated, "stable")

    w = out["weight"] / out["weight"].sum() if out["weight"].sum() else 0
    report.update({
        "theta_source": f"{path.name}",
        "n_unmatched": int((out.theta_join == "unmatched").sum()),
        "n_gated": int(out.theta_gated.sum()),
        "eur_gated": float(out.loc[out.theta_gated, "weight"].sum()),
        "weighted_theta_parc": float((w * out.theta_parc.fillna(1.0)).sum()),
        "by_bucket": out.groupby("theta_bucket").weight.sum().round(0).to_dict(),
        "by_basis": out.groupby("theta_basis").weight.sum().round(0).to_dict(),
        "components_wired": "theta_parc + theta_interval (see interval_mode)",
    })

    # θ_interval: simple / extended / off (default off — no money move until basis allowed)
    from isze_pricing.theta_interval import attach_interval

    out, irep = attach_interval(out, cfg)
    report["interval"] = irep
    if "theta" not in out.columns:
        out["theta"] = out["theta_parc"].fillna(1.0)
    return out, report
