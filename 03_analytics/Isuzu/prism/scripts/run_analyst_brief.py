#!/usr/bin/env python3
"""
Analyst brief — the stack walks to Jerome instead of waiting to be opened.

Deterministic composer (no LLM, no web): reads the verify report, FACTS drift
check, input freshness, defection alerts, dealer leakage, elasticity and
runway headlines, and writes a short brief. Designed for a weekly scheduled
run after run_pipeline_and_verify.ps1, or ad hoc.

Output: memory/briefs/analyst_brief_YYYY-MM-DD.md (+ console 5-liner)
Run from prism/.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    BRIEFS_DIR,
    DERIVED_DIR,
    GPT_SAFE_DIR,
    RAW_SALES_DIR,
    resolve_uio_path,
)

SNAPSHOT = DERIVED_DIR / "metrics_snapshot.json"


def _age_days(p: Path) -> int:
    return (datetime.now() - datetime.fromtimestamp(p.stat().st_mtime)).days


def main() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = BRIEFS_DIR / f"analyst_brief_{today}.md"
    lines: list[str] = [f"# ISZE analyst brief — {today}", ""]
    headline: list[str] = []

    # 1. pipeline + drift status -------------------------------------------------
    drift_rc = subprocess.run(
        [sys.executable, str(PRISM_ROOT / "scripts" / "verify_facts_drift.py")],
        capture_output=True, text=True, cwd=str(PRISM_ROOT),
    ).returncode
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}
    metrics = snap.get("metrics", {})
    v_pass = metrics.get("verify.pass", {}).get("value", "?")
    v_fail = metrics.get("verify.fail", {}).get("value", "?")
    drift_txt = "ALIGNED" if drift_rc == 0 else "DRIFT — open _facts_drift_report.md"
    lines += [
        "## Status",
        f"- Pipeline verify: **{v_pass} pass / {v_fail} fail** "
        f"({metrics.get('verify.generated', {}).get('value', 'unknown')})",
        f"- FACTS drift check: **{drift_txt}**",
        "",
    ]
    if drift_rc != 0:
        headline.append("FACTS drift detected — reconcile before quoting anything")
    if isinstance(v_fail, (int, float)) and v_fail:
        headline.append(f"pipeline has {v_fail} failing checks")

    # 2. input freshness ----------------------------------------------------------
    lines.append("## Input freshness")
    fresh_flags = []
    for label, p, warn_days in [
        ("CY2025 billing", RAW_SALES_DIR / "CY2025.XLSX", 60),
        ("UIO workbook", Path(resolve_uio_path()), 90),
        ("sales_fact.parquet", DERIVED_DIR / "sales_fact.parquet", 45),
        ("gpt_safe export", GPT_SAFE_DIR / "verification_summary.json", 45),
    ]:
        if not p.exists():
            lines.append(f"- {label}: MISSING")
            fresh_flags.append(f"{label} missing")
            continue
        age = _age_days(p)
        flag = " ⚠ stale" if age > warn_days else ""
        lines.append(f"- {label}: {age}d old{flag}")
        if flag:
            fresh_flags.append(f"{label} {age}d old")
    da = DERIVED_DIR / "defection_alerts.csv"
    if da.exists():
        horizon = pd.read_csv(da, usecols=["data_horizon"], nrows=1)["data_horizon"].iloc[0]
        lines.append(f"- Sales data horizon: **{horizon}** (alerts are relative to this, not today)")
    lines.append("")
    if fresh_flags:
        headline.append("; ".join(fresh_flags[:2]))

    # 3. defection alerts ----------------------------------------------------------
    if da.exists():
        d = pd.read_csv(da)
        alerts = d[d["alert"]].sort_values("trailing_12m_rev_eur", ascending=False)
        lines.append(f"## Defection alerts ({len(alerts)})")
        for _, r in alerts.head(8).iterrows():
            rev = (
                f", trailing-12m EUR{r['trailing_12m_rev_eur']:,.0f}"
                if pd.notna(r["trailing_12m_rev_eur"]) else ""
            )
            lines.append(
                f"- [{r['level']}] **{r['entity']}** / {r['pms_category']}: silent "
                f"{int(r['silent_months'])}m (median gap {r['median_gap_months']}m, "
                f"last {r['last_order_month']}{rev})"
            )
        lines.append("")
        big = alerts[alerts["trailing_12m_rev_eur"].fillna(0) > 10000]
        if len(big):
            headline.append(f"{len(big)} defection alert(s) with >EUR10K trailing revenue")

    # 4. dealer leakage ------------------------------------------------------------
    dl = DERIVED_DIR / "dealer_leakage_ituk.csv"
    if dl.exists():
        l = pd.read_csv(dl)
        top = l.groupby("dealer_name")["gap_eur"].sum().sort_values(ascending=False).head(5)
        lines.append(f"## ITUK dealer leakage (benchmark gap EUR{l['gap_eur'].sum():,.0f})")
        lines += [f"- {d}: EUR{v:,.0f}" for d, v in top.items()]
        lines.append("")

    # 5. model headlines -------------------------------------------------------------
    lines.append("## Model headlines")
    for key, label in [
        ("waterfall.network.gps_pct_2025", "Network GPS CY2025 (waterfall identity)"),
        ("waterfall.network.wallet_eur_2025", "Network wallet ceiling CY2025 (EUR)"),
        ("runway.network.wallet_eur_2030", "Network wallet 2030, age-flat (EUR)"),
        ("leakage.ituk.benchmark_gap_eur", "ITUK dealer benchmark gap (EUR)"),
    ]:
        v = metrics.get(key, {}).get("value")
        if v is not None:
            lines.append(f"- {label}: **{v:,.1f}**" if isinstance(v, float) else f"- {label}: **{v:,}**")
    el = DERIVED_DIR / "price_volume_elasticity.csv"
    if el.exists():
        e = pd.read_csv(el)
        strong = e[(~e["low_power"]) & (e["beta_elasticity"] < -0.5)]
        lines.append(
            f"- Elasticity: {len(strong)} categories show negative price response "
            "(adequate n; LOW POWER — direction only)"
        )
    lines.append("")

    # 5-liner --------------------------------------------------------------------
    if not headline:
        headline.append("no red flags; pipeline green, FACTS aligned")
    lines = (
        [lines[0], "", "## TL;DR", *[f"- {h}" for h in headline[:5]], ""]
        + lines[1:]
    )

    BRIEFS_DIR.mkdir(exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"brief -> {out_path}")
    for h in headline[:5]:
        print(f"  TLDR: {h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
