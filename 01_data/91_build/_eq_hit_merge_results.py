"""Merge EQ-Hit UI probe hits into _eq_hit_validation_20260917.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "01_data" / "00_derived"
OUT = DER / "_eq_hit_validation_20260917.json"
PROBE = DER / "_eq_hit_probe_pns.json"


def classify(h: dict, assigned: str) -> tuple[str, str]:
    fig = (h.get("fig_name") or "").upper()
    a = (assigned or "").lower()
    if not h.get("found"):
        return "", "NOT_IN_GLOBAL_SEARCH"
    if "AIR CLEANER" in fig:
        return "Filters (engine air filtration)", (
            "CONFIRMS_MISCLASS" if ("conditioning" in a or "air system" in a) else "OK"
        )
    if "STEERING" in fig:
        return "Steering", "CONFIRMS_MISCLASS" if "steering" not in a else "OK"
    if "BUMPER" in fig:
        return "Body / bumper", (
            "CONFIRMS_MISCLASS" if ("bumper" not in a and "body" not in a) else "OK"
        )
    if "SUSPENSION" in fig:
        return "Suspension", "CONFIRMS_MISCLASS" if "suspension" not in a else "OK"
    if "AXLE" in fig:
        return "Axle / knuckle", (
            "CONFIRMS_MISCLASS" if ("hardware" in a or "> pin" in a) else "OK"
        )
    if "DOOR" in fig or "WINDOW" in fig or "REGULATOR" in fig:
        return "Body / door window regulator", (
            "CONFIRMS_MISCLASS" if "voltage" in a or "starter" in a or "alternator" in a else "OK"
        )
    return h.get("fig_name") or "", "SEE_FIG"


def merge(hits: list[dict]) -> dict:
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    by = {x["pn"]: x for x in probe}
    summary = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {
        "as_of": "2026-09-17",
        "source": "https://isuzu.snaponepc.com/epc/#/",
        "results": [],
    }
    existing = {r["pn"]: r for r in summary.get("results", [])}
    for h in hits:
        if h.get("error"):
            continue
        p = by.get(h["pn"], {})
        eq_supports, verdict = classify(h, p.get("assigned") or "")
        existing[h["pn"]] = {
            **h,
            "description": p.get("description"),
            "assigned": p.get("assigned"),
            "should_be": p.get("should_be"),
            "rule": p.get("rule"),
            "eur": p.get("eur"),
            "eq_supports": eq_supports,
            "verdict": verdict,
        }
    ordered = [existing[p["pn"]] for p in probe if p["pn"] in existing]
    summary.update(
        {
            "results": ordered,
            "n_probed": len(ordered),
            "n_found": sum(1 for r in ordered if r.get("found")),
            "n_confirms_misclass": sum(
                1 for r in ordered if r.get("verdict") == "CONFIRMS_MISCLASS"
            ),
            "n_not_found": sum(1 for r in ordered if not r.get("found")),
            "n_probe_list": len(probe),
            "status": "COMPLETE" if len(ordered) >= len(probe) else "IN_PROGRESS",
            "headline": (
                "EQ locks ACL→AIR CLEANER, drag→STEERING, bumper→FRONT BUMPER, "
                "ball joint→FRONT SUSPENSION, king pin→FRONT AXLE."
            ),
        }
    )
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "n_probed": summary["n_probed"],
        "n_found": summary["n_found"],
        "n_confirms_misclass": summary["n_confirms_misclass"],
        "n_not_found": summary["n_not_found"],
        "remain": len(probe) - summary["n_probed"],
    }


if __name__ == "__main__":
    hits = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.loads(sys.stdin.read())
    if isinstance(hits, dict):
        hits = [hits]
    print(json.dumps(merge(hits)))
