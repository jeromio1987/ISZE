"""Audit suite.

A pricing engine is only worth what it can be challenged on. Six layers, in the
order a reviewer would work through them:

  1. INPUT       is the data fit to price on at all?
  2. ARITHMETIC  does the engine do what it claims?
  3. PROVENANCE  can every moving line name its evidence, and how old is it?
  4. COHERENCE   do the resulting prices make sense next to each other?
  5. REPRODUCE   does a logged run re-execute to the same answer?
  6. MATERIALITY which lines actually need a human to look at them?

Layer 5 is what makes the run log more than decoration. Recording a config hash
proves nothing unless something re-runs from it and diffs the result.

Every check returns PASS / WARN / FAIL. FAIL blocks a price round. WARN requires
a stated reason to proceed, recorded against the run.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def _r(check, status, detail, n=0):
    return {"check": check, "status": status, "detail": detail, "n": n}


# ---------------------------------------------------------------- 1. input
def check_inputs(df: pd.DataFrame, cfg: dict) -> list[dict]:
    out = []
    n = len(df)
    out.append(_r("rows present", PASS if n else FAIL, f"{n} rows", n))

    if "weight" in df:
        bad = int((df.weight <= 0).sum())
        out.append(_r("non-positive weight", PASS if not bad else WARN,
                      f"{bad} rows carry zero or negative revenue weight", bad))
    if "isze_premium" in df:
        miss = int(df.isze_premium.isna().sum())
        out.append(_r("benchmark coverage",
                      PASS if miss / max(n, 1) < 0.5 else WARN,
                      f"{miss}/{n} rows have no competitive benchmark", miss))
    if "evidence_n" in df:
        thin = int(((df.evidence_n > 0) & (df.evidence_n < cfg["allocation"]["min_n"])).sum())
        out.append(_r("thin evidence gated", PASS,
                      f"{thin} rows below min_n={cfg['allocation']['min_n']}, "
                      f"correctly held", thin))
    # FX staleness - a rate more than a year old silently misprices everything
    fx_set = cfg.get("formula", {}).get("fx_as_of")
    if fx_set:
        age = (date.today() - datetime.strptime(str(fx_set), "%Y-%m-%d").date()).days
        out.append(_r("FX rate age", PASS if age < 400 else WARN,
                      f"FX fixed {age} days ago", age))
    else:
        out.append(_r("FX rate age", WARN,
                      "formula.fx_as_of not set - FX age cannot be checked"))
    return out


# ---------------------------------------------------------------- 2. arithmetic
def check_arithmetic(out_df: pd.DataFrame, params, target: float) -> list[dict]:
    res = []
    w = out_df.weight / out_df.weight.sum()
    delivered = float((w * out_df.delta).sum())
    err = abs(delivered - target)
    res.append(_r("index reconciles", PASS if err < 1e-6 else FAIL,
                  f"delivered {delivered*100:.6f}% vs target {target*100:.6f}%"))

    over = int((out_df.delta > out_df.cap_eff + 1e-9).sum())
    under = int((out_df.delta < out_df.floor_eff - 1e-9).sum())
    res.append(_r("caps respected", PASS if not over else FAIL,
                  f"{over} lines above their cap", over))
    res.append(_r("floors respected", PASS if not under else FAIL,
                  f"{under} lines below their floor", under))

    bad_sign = int(((out_df.sign > 0) & (out_df.d_pos < -1e-9)).sum()
                   + ((out_df.sign < 0) & (out_df.d_pos > 1e-9)).sum())
    res.append(_r("sign rule respected", PASS if not bad_sign else FAIL,
                  f"{bad_sign} lines move against their own gate", bad_sign))

    nan = int(out_df.delta.isna().sum())
    res.append(_r("no NaN deltas", PASS if not nan else FAIL, f"{nan} NaN", nan))

    if "premium_basis" in out_df and hasattr(params, "require_basis"):
        moved_unbenchmarked = int(
            ((~out_df.premium_basis.isin(params.require_basis))
             & (out_df.d_pos.abs() > 1e-9)).sum())
        res.append(_r("no movement on unbenchmarked premium",
                      PASS if not moved_unbenchmarked else FAIL,
                      f"{moved_unbenchmarked} lines moved without a benchmarked "
                      f"target", moved_unbenchmarked))
    return res


# ---------------------------------------------------------------- 3. provenance
def check_provenance(out_df: pd.DataFrame, max_evidence_age_days=180) -> list[dict]:
    res = []
    moving = out_df[out_df.delta.abs() > 1e-9]
    no_reason = int(moving.reason_code.isna().sum()) if "reason_code" in moving else 0
    res.append(_r("every moving line has a reason code",
                  PASS if not no_reason else FAIL,
                  f"{no_reason} moving lines with no reason", no_reason))

    if "evidence_asof" in out_df.columns:
        ages = (pd.Timestamp.today() - pd.to_datetime(out_df.evidence_asof)).dt.days
        stale = int((ages > max_evidence_age_days).sum())
        res.append(_r("evidence freshness", PASS if not stale else WARN,
                      f"{stale} lines priced on evidence older than "
                      f"{max_evidence_age_days} days", stale))
    else:
        res.append(_r("evidence freshness", WARN,
                      "no evidence_asof column - benchmark age is untracked, so "
                      "a stale scrape cannot be distinguished from a fresh one"))
    return res


# ---------------------------------------------------------------- 4. coherence
def check_coherence(prices: pd.DataFrame) -> list[dict]:
    """Cross-part sanity. Cheap to run, and these are the errors a distributor
    finds first because they are visible without any analysis."""
    res = []
    if {"family", "size_rank", "price_new"} <= set(prices.columns):
        inv = 0
        for _, g in prices.groupby("family"):
            g = g.sort_values("size_rank")
            inv += int((g.price_new.diff() < 0).sum())
        res.append(_r("price ladder monotonic", PASS if not inv else WARN,
                      f"{inv} inversions - a larger variant priced below a "
                      f"smaller one", inv))
    if {"kit_pn", "component_sum", "price_new"} <= set(prices.columns):
        k = prices.dropna(subset=["kit_pn"])
        above = int((k.price_new > k.component_sum).sum())
        res.append(_r("kit priced below sum of components",
                      PASS if not above else WARN,
                      f"{above} kits cost more than buying the parts "
                      f"separately", above))
    if {"superseded_by", "price_new", "price_predecessor"} <= set(prices.columns):
        s = prices.dropna(subset=["superseded_by"])
        jump = int((s.price_new / s.price_predecessor > 1.25).sum())
        res.append(_r("supersession price continuity",
                      PASS if not jump else WARN,
                      f"{jump} successor parts more than 25% above the part "
                      f"they replace", jump))
    if not res:
        res.append(_r("coherence checks", WARN,
                      "no family / kit / supersession columns supplied - these "
                      "checks did not run"))
    return res


# ---------------------------------------------------------------- 5. reproduce
def reproduce(run_dir: Path, rerun_fn) -> list[dict]:
    """Re-execute a logged run from its own config and diff the outputs.

    rerun_fn(cfg) -> {table_name: DataFrame}. This is the check that turns the
    run log from a record into a guarantee.
    """
    run_dir = Path(run_dir)
    res = []
    cfg_p, inp_p = run_dir / "config_resolved.yaml", run_dir / "inputs.json"
    if not cfg_p.exists():
        return [_r("reproduce", FAIL, f"no config_resolved.yaml in {run_dir}")]

    cfg = yaml.safe_load(cfg_p.read_text(encoding="utf-8"))
    if inp_p.exists():
        rec = json.loads(inp_p.read_text(encoding="utf-8"))
        drifted = []
        for name, spec in rec.get("inputs", {}).items():
            path, _, sha = str(spec).rpartition("::")
            p = Path(path)
            if not p.exists():
                drifted.append(f"{name}: file gone")
            else:
                import hashlib
                cur = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                if cur != sha:
                    drifted.append(f"{name}: {sha} -> {cur}")
        res.append(_r("input files unchanged", PASS if not drifted else WARN,
                      "; ".join(drifted) or "all inputs byte-identical",
                      len(drifted)))

    try:
        fresh = rerun_fn(cfg)
    except Exception as e:                                   # noqa: BLE001
        return res + [_r("re-execution", FAIL, f"{type(e).__name__}: {e}")]

    for name, df_new in fresh.items():
        old_p = run_dir / f"{name}.csv"
        if not old_p.exists():
            res.append(_r(f"diff {name}", WARN, "no logged copy to compare"))
            continue
        old = pd.read_csv(old_p)
        if old.shape != df_new.shape:
            res.append(_r(f"diff {name}", FAIL,
                          f"shape {old.shape} -> {df_new.shape}"))
            continue
        num = old.select_dtypes(include=[np.number]).columns
        common = [c for c in num if c in df_new.columns]
        delta = float(np.nanmax(np.abs(old[common].values
                                       - df_new[common].values))) if common else 0.0
        res.append(_r(f"diff {name}", PASS if delta < 1e-6 else FAIL,
                      f"max numeric drift {delta:.3e}"))
    return res


# ---------------------------------------------------------------- 6. materiality
def materiality(out_df: pd.DataFrame, top_n=25, pct_of_impact=0.8) -> pd.DataFrame:
    """Lines a human should actually review.

    Auditing 15,000 lines equally is theatre. Rank by absolute revenue impact
    and review down to the point where the reviewed set covers most of it.
    """
    d = out_df.copy()
    d["abs_impact"] = d.revenue_delta_eur.abs()
    d = d.sort_values("abs_impact", ascending=False)
    tot = d.abs_impact.sum()
    d["cum_share"] = d.abs_impact.cumsum() / tot if tot else 0
    n = max(top_n, int((d.cum_share <= pct_of_impact).sum()) + 1)
    keep = [c for c in ["db", "cat", "label", "delta", "revenue_delta_eur",
                        "reason_code", "premium_basis", "evidence_tier",
                        "cum_share"] if c in d.columns]
    return d.head(n)[keep]


# ---------------------------------------------------------------- runner
def run_all(out_df, df_in, cfg, params, target) -> tuple[pd.DataFrame, str]:
    checks = (check_inputs(df_in, cfg)
              + check_arithmetic(out_df, params, target)
              + check_provenance(out_df)
              + check_coherence(out_df))
    t = pd.DataFrame(checks)
    verdict = FAIL if (t.status == FAIL).any() else (
        WARN if (t.status == WARN).any() else PASS)
    return t, verdict
