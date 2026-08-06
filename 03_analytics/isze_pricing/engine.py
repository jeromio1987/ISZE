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
    a = cfg["allocation"]
    return Params(
        target=a["target"], cap=a["cap"], cap_top50=a["cap_top50"],
        floor=a["floor"], policy_premium=a["policy_premium"],
        min_n=a["min_n"], pos_gain=a["pos_gain"],
        tier_limit=dict(a["tier_limit"]), theta_delta=dict(a["theta_delta"]),
        require_basis=list(a.get("require_basis", [])),
    )


@dataclass
class Params:
    target: float = 0.03          # weighted increase on net-to-DB
    cap: float = 0.08             # per-line ceiling
    cap_top50: float = 0.05       # tighter ceiling inside a DB's top-50 basket
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
def premium_for(cat: str, p: Params) -> tuple[float, str]:
    """Target premium and its provenance for one category.

    Provenance travels with the number on purpose. A premium nobody has
    benchmarked is a guess, and the engine must be able to tell the difference.
    """
    e = p.policy_premium.get("by_category", {}).get(
        cat, p.policy_premium.get("default", {"value": 1.40,
                                              "basis": "placeholder"}))
    return float(e["value"]), str(e["basis"])


def street_position(row, p: Params) -> tuple[float, str, float]:
    """Return (premium_gap, evidence_tier, tier_limit).

    premium_gap = ISZE premium over IAM street  minus  the policy target premium.
    Positive = priced above where policy says genuine should sit.

    The target is a stated policy dial, not a measurement. Genuine parts carry a
    legitimate premium, so parity with IAM is the wrong target -- but the data is
    far too thin to estimate the tolerated premium, so it is set explicitly and
    defended as a decision instead of dressed up as a finding.
    """
    isze_prem = row.get("isze_premium")
    tier = row.get("evidence_tier", "T5_none")
    n = row.get("evidence_n", 0)

    if isze_prem is None or (isinstance(isze_prem, float) and np.isnan(isze_prem)):
        return 0.0, "T5_none", 0.0
    if n is None or n < p.min_n:
        return 0.0, "T5_none", 0.0        # thin evidence == no evidence

    target, basis = premium_for(row.get("cat", ""), p)
    if basis not in p.require_basis:
        # no benchmarked target for this category -> hold, do not guess
        return 0.0, "T5_none", 0.0
    return float(isze_prem) - (target - 1.0), tier, p.tier_limit.get(tier, 0.0)


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
    out["premium_gap"] = gaps
    out["evidence_tier"] = tiers
    out["tier_limit"] = limits

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

    out["d_ex_base"] = out["d_pos"] + out["d_theta"]
    out["cap_eff"] = np.where(out.get("is_top50", False), p.cap_top50, p.cap)
    out["floor_eff"] = p.floor

    base = solve_base(out["weight"].to_numpy(float), out["d_ex_base"].to_numpy(float),
                      out["cap_eff"].to_numpy(float), out["floor_eff"].to_numpy(float),
                      p.target)
    out["delta_base"] = base
    out["delta"] = np.clip(base + out["d_ex_base"], out["floor_eff"], out["cap_eff"])

    w = out["weight"] / out["weight"].sum()
    out["index_contribution_bp"] = w * out["delta"] * 10_000
    out["revenue_delta_eur"] = out["weight"] * out["delta"]

    summary = {
        "rows": len(out),
        "base_eur": float(out["weight"].sum()),
        "delta_base": float(base),
        "weighted_increase": float((w * out["delta"]).sum()),
        "revenue_delta_eur": float(out["revenue_delta_eur"].sum()),
        "n_capped": int((out["delta"] >= out["cap_eff"] - 1e-9).sum()),
        "n_floored": int((out["delta"] <= out["floor_eff"] + 1e-9).sum()),
        "n_zero_evidence": int((out["evidence_tier"] == "T5_none").sum()),
        "n_unbenchmarked_premium": int(
            (~out["premium_basis"].isin(p.require_basis)).sum()),
    }
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
            "theta_bucket": "stable",   # not yet wired - needs UIO x interval
            "is_top50": False,
        })
    df = pd.DataFrame(rows)
    return df[df["weight"] > 0].reset_index(drop=True)
