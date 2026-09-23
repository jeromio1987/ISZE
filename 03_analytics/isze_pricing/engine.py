"""
ISZE Pricing Engine v1 — allocation core.

Implements the spec in ISZE_Pricing_Spec_v1.md. Granularity-agnostic: the same
engine runs on distributor x category cells (what pricing_action_map.json gives)
or on PN-level rows (what 01_data/00_derived + the PR00 list give inside ISZE).

Design constraint: this file never needs to see raw billing. It takes a frame with
  weight, zone, capture, and a street-position reading, and returns per-row deltas
  that satisfy the weighted-index target exactly.

No elasticity coefficient is used anywhere (roadmap C1: not quotable at ISZE level).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------- parameters
def params_from_config(cfg: dict) -> "Params":
    """Build Params from the allocation block of config.yaml.

    Single source of truth: config.yaml. The defaults below exist only so the
    module is importable and testable standalone.
    """
    from .theta import require_list

    a = cfg["allocation"]

    def _opt_float(key: str):
        v = a.get(key, None)
        if v is None or v == "" or (isinstance(v, float) and pd.isna(v)):
            return None
        return float(v)

    return Params(
        target=float(a["target"]),
        cap=_opt_float("cap"),
        cap_top50=_opt_float("cap_top50"),
        floor=float(a["floor"]),
        policy_premium=a["policy_premium"],
        min_n=a["min_n"], pos_gain=a["pos_gain"],
        tier_limit=dict(a["tier_limit"]), theta_delta=dict(a["theta_delta"]),
        # a bare string here would degrade to a set of characters and hold
        # every line flat without raising -- see require_list
        require_basis=require_list(a.get("require_basis"),
                                   "allocation.require_basis"),
        theta_veto=dict(a.get("theta_veto", {"enabled": False})),
    )


@dataclass
class Params:
    target: float = 0.03          # weighted increase on net-to-DB
    # None = no per-line upper ceiling (Jerome 2026-09-20: 8% cap deleted)
    cap: float | None = None
    cap_top50: float | None = None
    floor: float = -0.12          # per-line floor

    # how far each evidence tier may move a line
    tier_limit: dict = field(default_factory=lambda: {
        "T1_ks_observed": 0.10,
        "T2_ks_derived": 0.06,
        "T3_eucon": 0.06,
        "T4_coarse": 0.03,
        "T5_none": 0.00,
    })

    # Target genuine premium over IAM street. POLICY DIAL, not a measurement.
    # Deriving it from KS observed listings was tried and rejected: n=1..2 per
    # category and the KS genuine listing is a retailer asking price on a
    # different denominator than PR00 x 1.785. It inverted the brake decision.
    # per-category mapping: {"default": {...}, "by_category": {cat: {...}}}
    policy_premium: dict = field(default_factory=lambda: {
        "default": {"value": 1.40, "basis": "placeholder"}, "by_category": {}})
    require_basis: list = field(default_factory=lambda: ["oem_benchmark",
                                                        "iam_derived"])
    theta_veto: dict = field(default_factory=lambda: {"enabled": False})

    # minimum benchmark observations before a category may move at all
    min_n: int = 3

    # theta buckets -> delta contribution
    theta_delta: dict = field(default_factory=lambda: {
        "declining": -0.02, "stable": 0.0, "growing": 0.03})

    # sensitivity of delta_pos to the premium gap
    pos_gain: float = 0.35


# ---------------------------------------------------------------- index solve
def solve_base(w: np.ndarray, d_ex_base: np.ndarray, cap: np.ndarray,
               floor: np.ndarray, target: float, tol: float = 1e-12) -> float:
    """Find b such that the w-weighted mean of clip(b + d_ex_base, floor, cap) == target.

    clip(b + d) is non-decreasing in b, so the weighted mean is monotone and
    bisection is exact. Solving *after* clipping is the whole point: clamping
    outliers changes the index, so base and caps must be solved jointly or the
    declared weighted increase silently drifts off target.
    """
    w = w / w.sum()

    def weighted(b: float) -> float:
        return float(np.dot(w, np.clip(b + d_ex_base, floor, cap)))

    lo, hi = -1.0, 1.0
    if weighted(lo) > target or weighted(hi) < target:
        # target unreachable inside the cap/floor envelope
        return float("nan")
    for _ in range(200):
        mid = (lo + hi) / 2
        if weighted(mid) < target:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


# ---------------------------------------------------------------- components
def premium_for(cat: str, p: Params) -> tuple[float, str, float]:
    """Target premium for one category.

    Returns (excess_fraction, basis, max_premium_pct).
      excess_fraction 0.30 == +30% above benchmark (Jerome language).
      Internal config may still store value as ratio 1.30; we prefer
      max_premium_pct when present.

    Provenance travels with the number: a premium nobody has benchmarked
    is a guess, and the engine must be able to tell the difference.
    """
    e = p.policy_premium.get("by_category", {}).get(
        cat, p.policy_premium.get("default", {"value": 1.30,
                                              "basis": "placeholder",
                                              "max_premium_pct": 30}))
    basis = str(e["basis"])
    if "max_premium_pct" in e and e["max_premium_pct"] is not None:
        pct = float(e["max_premium_pct"])
        return pct / 100.0, basis, pct
    ratio = float(e["value"])
    return ratio - 1.0, basis, (ratio - 1.0) * 100.0


def street_position(row, p: Params) -> tuple[float, str, float]:
    """Return (premium_gap, evidence_tier, tier_limit).

    isze_premium is already an excess fraction
      (street/IAM - 1), e.g. 0.30 = +30% above IAM.
    premium_gap = observed excess − allowed excess (from brand-quality %).
    Positive = priced above where policy says genuine should sit.
    """
    isze_prem = row.get("isze_premium")
    tier = row.get("evidence_tier", "T5_none")
    n = row.get("evidence_n", 0)

    if isze_prem is None or (isinstance(isze_prem, float) and np.isnan(isze_prem)):
        return 0.0, "T5_none", 0.0
    if n is None or n < p.min_n:
        return 0.0, "T5_none", 0.0        # thin evidence == no evidence

    target_excess, basis, _pct = premium_for(row.get("cat", ""), p)
    if basis not in p.require_basis:
        # no benchmarked target for this category -> hold, do not guess
        return 0.0, "T5_none", 0.0
    return float(isze_prem) - target_excess, tier, p.tier_limit.get(tier, 0.0)


def sign_rule(zone: str, premium_gap: float, tier: str) -> tuple[float, str]:
    """Two-gate rule from spec section 7. Returns (multiplier, reason_code)."""
    if tier == "T5_none":
        return 0.0, "NO_EVIDENCE_HOLD"
    if zone == "raise":
        return 1.0, "CAPTIVE_RAISE"
    if zone == "contested":
        if premium_gap < -0.05:
            return 1.0, "CONTESTED_BELOW_MARKET"
        if premium_gap > 0.15:
            return -1.0, "CONTESTED_ABOVE_MARKET"
        return 0.0, "CONTESTED_AT_PARITY"
    # zone == defend
    if premium_gap > 0.15:
        return -1.0, "DEFEND_CUT"
    if premium_gap < -0.05:
        # cheap and still losing -> price is not the problem
        return 0.0, "CHEAP_AND_LOSING_INVESTIGATE"
    return 0.0, "DEFEND_HOLD"


def run(df: pd.DataFrame, p: Params | None = None) -> tuple[pd.DataFrame, dict]:
    """df needs: weight, zone, isze_premium, accepted_premium, evidence_tier,
    theta_bucket, is_top50 (optional)."""
    p = p or Params()
    out = df.copy()

    gaps, tiers, limits = [], [], []
    for _, r in out.iterrows():
        g, t, lim = street_position(r, p)
        gaps.append(g); tiers.append(t); limits.append(lim)
    out["premium_target"] = [premium_for(r.get("cat", ""), p)[0]
                             for _, r in out.iterrows()]
    out["premium_basis"] = [premium_for(r.get("cat", ""), p)[1]
                            for _, r in out.iterrows()]
    out["max_premium_pct"] = [premium_for(r.get("cat", ""), p)[2]
                              for _, r in out.iterrows()]
    out["premium_gap"] = gaps
    out["evidence_tier"] = tiers
    out["tier_limit"] = limits
    # Jerome-facing: observed excess as %
    out["isze_premium_pct"] = out["isze_premium"] * 100.0
    out["premium_gap_pp"] = out["premium_gap"] * 100.0

    mults, reasons = zip(*(sign_rule(r.zone, r.premium_gap, r.evidence_tier)
                           for _, r in out.iterrows()))
    out["sign"] = mults
    out["reason_code"] = reasons

    # delta_pos: scaled by how far off tolerated premium, bounded by evidence tier
    raw = -out["premium_gap"] * p.pos_gain
    out["d_pos"] = np.where(out["sign"] == 0, 0.0,
                            np.clip(raw, -out["tier_limit"], out["tier_limit"]))
    # a negative sign must not produce an increase, and vice versa
    out["d_pos"] = np.where(np.sign(out["d_pos"]) != out["sign"], 0.0, out["d_pos"])

    out["d_theta"] = out["theta_bucket"].map(p.theta_delta).fillna(0.0)

    # theta veto: an adverse street reading blocks a momentum increase even
    # when it is too thin to justify a cut. Asymmetric on purpose.
    v = p.theta_veto or {}
    if v.get("enabled"):
        adverse = ((out.get("evidence_n", 0) >= p.min_n)
                   & out["isze_premium"].notna()
                   & (out["isze_premium"] > v.get("premium_above", 0.60)))
        out["theta_vetoed"] = adverse & (out["d_theta"] > 0)
        out["d_theta"] = np.where(out["theta_vetoed"], 0.0, out["d_theta"])
    else:
        out["theta_vetoed"] = False

    out["d_ex_base"] = out["d_pos"] + out["d_theta"]
    # No binding per-line upper ceiling (cap / cap_top50 may be None → ∞).
    hi_default = np.inf if p.cap is None else float(p.cap)
    hi_top50 = np.inf if p.cap_top50 is None else float(p.cap_top50)
    if "is_top50" in out.columns:
        out["cap_eff"] = np.where(out["is_top50"], hi_top50, hi_default)
    else:
        out["cap_eff"] = hi_default
    out["floor_eff"] = p.floor

    base = solve_base(out["weight"].to_numpy(float), out["d_ex_base"].to_numpy(float),
                      out["cap_eff"].to_numpy(float), out["floor_eff"].to_numpy(float),
                      p.target)
    out["delta_base"] = base
    out["delta"] = np.clip(base + out["d_ex_base"], out["floor_eff"], out["cap_eff"])

    w = out["weight"] / out["weight"].sum()
    out["index_contribution_bp"] = w * out["delta"] * 10_000
    out["revenue_delta_eur"] = out["weight"] * out["delta"]

    finite_cap = np.isfinite(out["cap_eff"].to_numpy(float))
    summary = {
        "rows": len(out),
        "base_eur": float(out["weight"].sum()),
        "delta_base": float(base),
        "weighted_increase": float((w * out["delta"]).sum()),
        "revenue_delta_eur": float(out["revenue_delta_eur"].sum()),
        "n_capped": int(
            (finite_cap & (out["delta"].to_numpy(float)
                           >= out["cap_eff"].to_numpy(float) - 1e-9)).sum()
        ),
        "n_floored": int((out["delta"] <= out["floor_eff"] + 1e-9).sum()),
        "n_zero_evidence": int((out["evidence_tier"] == "T5_none").sum()),
        "n_unbenchmarked_premium": int(
            (~out["premium_basis"].isin(p.require_basis)).sum()),
        "n_theta_vetoed": int(out["theta_vetoed"].sum()),
    }
    # theta provenance, when a momentum source has been attached. The engine
    # does not own theta semantics -- it reports what came in, so a run can
    # never look wired when it is not.
    if "theta_basis" in out.columns:
        summary["n_theta_unwired"] = int((out["theta_basis"] == "unwired").sum())
        summary["n_theta_moving"] = int((out["theta_bucket"] != "stable").sum())
    return out, summary


# ---------------------------------------------------------------- adapter
def from_action_map(path: Path) -> pd.DataFrame:
    """Build an engine frame from pricing_action_map.json (distributor x category).

    isze_premium  <- ks_derived, else eucon      (ISZE street vs IAM street)
    accepted_prem <- ks_observed                 (what the market pays for genuine)
    """
    j = json.loads(Path(path).read_text(encoding="utf-8"))
    ev = j["price_evidence"]

    rows = []
    for c in j["cells"]:
        e = ev.get(c["cat"], {})
        # Eucon is the primary position measure: ISZE street vs competitor
        # average, one consistent methodology, PN-level underneath.
        # KS series are corroboration only -- different denominators.
        isze_prem, tier, n = np.nan, "T5_none", 0
        if "eucon" in e:
            isze_prem = e["eucon"]["med_street_delta_pct"]
            tier, n = "T3_eucon", e["eucon"]["n"]
        elif "ks_derived" in e:
            isze_prem = e["ks_derived"]["med_premium_pct"]
            tier, n = "T2_ks_derived", e["ks_derived"]["n"]

        rows.append({
            "db": c["db"], "cat": c["cat"], "label": c["label"],
            "weight": float(c["captured"]), "zone": c["zone"],
            "capture": c["capture"], "gap_eur": c["gap"],
            "isze_premium": isze_prem, "evidence_n": n,
            "evidence_tier": tier,
            # Neutral default. theta.attach() overwrites this from the corrected
            # car park; left alone, the frame is still valid and simply carries
            # no momentum signal.
            "theta_bucket": "stable",
            "is_top50": False,
        })
    df = pd.DataFrame(rows)
    return df[df["weight"] > 0].reset_index(drop=True)
