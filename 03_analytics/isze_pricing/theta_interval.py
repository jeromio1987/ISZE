"""θ_interval — simple / extended modes from service-schedule map.

Authority: chassis_generation_interval_map.yaml (Jerome schedule PDFs).

Modes (config theta.interval.mode):
  off      — all 1.0
  simple   — LCV DBs × interval-linked cats use assumed SCR share
  extended — read lcv_generation_mix_by_db.csv when present; else simple

Live alloc only moves when basis `schedule_assumed_mix` or `schedule_measured_mix`
is in theta.require_basis (default: neither — diagnostic only).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = Path(__file__).resolve().parent / "chassis_generation_interval_map.yaml"


def load_map(path: Path | None = None) -> dict:
    p = path or MAP_PATH
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _scr_share(db: str, m: dict, mix: pd.DataFrame | None) -> tuple[float, str]:
    """Return (share_scr_15k, basis)."""
    if mix is not None and not mix.empty and db in set(mix["distributor_DB"]):
        row = mix.loc[mix["distributor_DB"] == db].iloc[0]
        share = float(row["share_scr_15k"])
        return share, "schedule_measured_mix"

    shares = m.get("simple_lcv_scr_share", {})
    lcv = set(m.get("lcv_dbs", []))
    if db in lcv:
        return float(shares.get(db, shares.get("default_lcv_db", 0.1))), "schedule_assumed_mix"
    return 0.0, "not_lcv"


def theta_interval_factor(share_scr: float, lift: float) -> float:
    """Blend: (1-s)*1.0 + s*lift."""
    s = max(0.0, min(1.0, float(share_scr)))
    return (1.0 - s) * 1.0 + s * float(lift)


def attach_interval(
    df: pd.DataFrame,
    cfg: dict,
    map_path: Path | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Attach theta_interval (+ basis) and composite theta = parc × interval.

    Does not change theta_bucket unless cfg enables apply_to_bucket.
    """
    out = df.copy()
    out["theta_interval"] = 1.0
    out["theta_interval_basis"] = "off"
    tcfg = cfg.get("theta", {})
    icfg = tcfg.get("interval", {})
    mode = str(icfg.get("mode", "off")).lower()
    report: dict = {
        "interval_mode": mode,
        "interval_map": str(MAP_PATH.name),
    }

    if mode in ("", "off", "none", "false", "0"):
        out["theta"] = out.get("theta_parc", pd.Series(1.0, index=out.index)).fillna(1.0)
        report["interval_applied"] = False
        return out, report

    m = load_map(map_path)
    lift = float(m.get("interval_lift_scr_vs_legacy", 4 / 3))
    cats = set(m.get("interval_linked_categories", []))
    lcv = set(m.get("lcv_dbs", []))

    mix = None
    mix_path = ROOT / m.get(
        "extended_mix_file", "01_data/00_derived/lcv_generation_mix_by_db.csv"
    )
    if mode == "extended" and mix_path.exists():
        mix = pd.read_csv(mix_path)
        report["mix_file"] = str(mix_path)
    elif mode == "extended":
        report["mix_file"] = f"MISSING::{mix_path.name} (fell back to simple shares)"

    factors = []
    bases = []
    for db, cat in zip(out["db"], out["cat"]):
        if cat not in cats or db not in lcv:
            factors.append(1.0)
            bases.append("not_interval_linked" if cat not in cats else "not_lcv")
            continue
        share, basis = _scr_share(str(db), m, mix)
        # extended without file still uses assumed shares but keeps assumed basis
        if mode == "simple":
            basis = "schedule_assumed_mix" if basis != "not_lcv" else basis
        factors.append(theta_interval_factor(share, lift))
        bases.append(basis)

    out["theta_interval"] = factors
    out["theta_interval_basis"] = bases
    parc = out.get("theta_parc", pd.Series(1.0, index=out.index)).fillna(1.0)
    out["theta"] = parc * out["theta_interval"]

    # Optional: fold interval into bucket only if allowed bases present
    apply_bucket = bool(icfg.get("apply_to_bucket", False))
    require = set(tcfg.get("require_basis") or [])
    report["interval_applied"] = True
    report["apply_to_bucket"] = apply_bucket
    report["n_interval_gt_1"] = int((out["theta_interval"] > 1.0001).sum())
    report["mean_interval_lcv_linked"] = float(
        out.loc[
            out["theta_interval_basis"].isin(
                ["schedule_assumed_mix", "schedule_measured_mix"]
            ),
            "theta_interval",
        ].mean()
    ) if report["n_interval_gt_1"] else 1.0

    if apply_bucket and "theta_bucket" in out.columns:
        bounds = cfg["allocation"]["theta_bounds"]
        from isze_pricing.theta import bucket

        # re-bucket on composite theta where interval basis allowed
        ok = out["theta_interval_basis"].isin(require) | out["theta_basis"].isin(require)
        # Only remake bucket when interval basis is explicitly allowed
        allow_i = out["theta_interval_basis"].isin(require)
        new_b = [
            bucket(float(th), bounds) if allow else b
            for th, allow, b in zip(out["theta"], allow_i, out["theta_bucket"])
        ]
        out["theta_bucket"] = new_b
        report["n_bucket_moved_by_interval"] = int(allow_i.sum())

    return out, report


def write_diagnostic(cfg: dict, action_map: pd.DataFrame, out_dir: Path) -> Path:
    """Write what simple/extended would do — for Jerome, no alloc side-effect."""
    out_dir.mkdir(parents=True, exist_ok=True)
    # minimal frame
    df = action_map.copy()
    if "weight" not in df.columns:
        df["weight"] = 1.0
    # fake parc=1 for pure interval view
    df["theta_parc"] = 1.0
    df["theta_basis"] = "diagnostic"
    cfg2 = {
        "theta": {
            **cfg.get("theta", {}),
            "interval": {**cfg.get("theta", {}).get("interval", {}), "mode": "simple"},
        },
        "allocation": cfg.get("allocation", {"theta_bounds": {"declining_below": 0.95, "growing_above": 1.10}}),
    }
    framed, rep = attach_interval(df, cfg2)
    path = out_dir / "theta_interval_simple_diagnostic.csv"
    cols = [c for c in ["db", "cat", "label", "weight", "theta_interval", "theta_interval_basis"] if c in framed.columns]
    framed[cols].to_csv(path, index=False)
    (out_dir / "theta_interval_simple_diagnostic.json").write_text(
        __import__("json").dumps(rep, indent=2), encoding="utf-8"
    )
    return path
