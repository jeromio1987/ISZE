#!/usr/bin/env python3
"""
FACTS drift check — fails loudly when FACTS.md headline figures diverge from
the live pipeline.

Compares prism/data/facts_anchor.yaml (the pinned FACTS.md values) against
Data/derived/metrics_snapshot.json (computed truth). Run after every pipeline
rebuild — manual reconciliation failed within five days of FACTS.md's
creation; this makes the reconcile step structural.

Exit 0 = aligned. Exit 1 = drift (or snapshot/anchor missing).
Report: Data/derived/_facts_drift_report.md
Run from prism/.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR  # noqa: E402

ANCHOR = PRISM_ROOT / "data" / "facts_anchor.yaml"
SNAPSHOT = DERIVED_DIR / "metrics_snapshot.json"
REPORT = DERIVED_DIR / "_facts_drift_report.md"


def main() -> int:
    if not SNAPSHOT.exists():
        print("FAIL: metrics_snapshot.json missing — run build_metrics_snapshot.py first")
        return 1
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    anchors = yaml.safe_load(ANCHOR.read_text(encoding="utf-8"))["anchors"]
    metrics = snap["metrics"]

    lines = [
        "# FACTS drift report",
        "",
        f"**Checked:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"**Snapshot as-of:** {snap.get('as_of')}",
        "",
        "| Anchor | FACTS value | Pipeline value | Drift | Status |",
        "|---|---|---|---|---|",
    ]
    n_drift = 0
    n_missing = 0
    for a in anchors:
        key = a["key"]
        facts_val = float(a["facts_value"])
        tol = float(a.get("tol_pct", 0.5))
        entry = metrics.get(key)
        if entry is None or entry.get("value") is None:
            n_missing += 1
            lines.append(f"| {key} | {facts_val} | MISSING | — | MISSING |")
            continue
        try:
            pipe_val = float(entry["value"])
        except (TypeError, ValueError):
            n_missing += 1
            lines.append(f"| {key} | {facts_val} | {entry['value']} | — | NON-NUMERIC |")
            continue
        if facts_val == 0:
            drift_pct = 0.0 if pipe_val == 0 else 100.0
        else:
            drift_pct = abs(pipe_val - facts_val) / abs(facts_val) * 100
        ok = drift_pct <= tol
        if not ok:
            n_drift += 1
        lines.append(
            f"| {key} | {facts_val:g} | {pipe_val:g} | {drift_pct:.2f}% | "
            f"{'ok' if ok else 'DRIFT'} |"
        )

    status = "ALIGNED" if (n_drift == 0 and n_missing == 0) else "DRIFT DETECTED"
    lines += [
        "",
        f"**Result: {status}** — {n_drift} drifted, {n_missing} missing, "
        f"{len(anchors) - n_drift - n_missing} aligned.",
        "",
        "On DRIFT: decide which side is right. If the pipeline changed "
        "legitimately, update FACTS.md **and** facts_anchor.yaml together, then "
        "re-export Data/gpt_safe. Never leave them disagreeing.",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"facts-drift: {status} ({n_drift} drift, {n_missing} missing) -> {REPORT.name}")
    return 0 if status == "ALIGNED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
