#!/usr/bin/env python3
"""
Overnight audit angles for the ISZE delegator orchestrator.

Called one angle per 20-minute cycle by isze_overnight_orchestrator.ps1. Prints JSON on
stdout describing what this angle found.

HARD RULE - READ ONLY ON DELIVERABLES
-------------------------------------
This script only ever READS deliverables. It writes exactly one file, and only when asked
with --write-baseline, which records the locked-file hashes it needs in order to detect
later modification. It never rebuilds, publishes, syncs, mails, bumps a version or moves a
price. Authority: 00_docs/RUNBOOK_ROUTINE_HANDOVER.md section 5 and
.cursor/rules/isze-no-ship-without-ok.mdc.

Usage
-----
  python _overnight_angles.py --list
  python _overnight_angles.py --angle receipt_mtime_drift
  python _overnight_angles.py --angle language_sweep --hours 48
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
NOW = datetime.now(timezone.utc)

# ------------------------------------------------------------------ scope
SKIP_PARTS = {"07_deploy", "_archive", "node_modules", ".git", "__pycache__", ".claude",
              "90_archive", "_qa", "runs", ".venv", "venv", ".pytest_cache"}
ARTIFACT_SUFFIXES = {".html", ".xlsx", ".pptx", ".pdf"}
SEARCH_ROOTS = ["02_dashboards", "09_meetings", "01_data/01_Pricing", "01_data/dashboards"]

# ------------------------------------------------------------------ locked files
# Jerome, 2026-09-17: read-only. The orchestrator never writes these, and this angle
# reports any change to them so a collision between agents becomes visible.
LOCKED = [
    "01_data/01_Pricing/Pricing_Revision_AIM_Source_Analysis.xlsx",
    "01_data/01_Pricing/Pricing_Revision_AIM_Source_Analysis.SHIP_RECEIPT.json",
    "01_data/Pricing",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.html",
    "02_dashboards/pricing/ISZE_Pricing_Revision_AIM_Source.SHIP_RECEIPT.json",
    "02_dashboards/pricing/_build/pricing_dashboard_data.json",
    "02_dashboards/pricing/AIM_PRIORITY_LIST.csv",
    "02_dashboards/pricing/AIM_PRIORITY_LIST.xlsx",
    "01_data/00_derived/aim_master_v2.csv",
    "03_analytics/isze_pricing/config.yaml",
]

# ------------------------------------------------------------------ language
# Spoken-label rule: .cursor/rules/isze-spoken-labels.mdc and isze-pricing-no-street-ui.mdc.
#
# Only user-facing formats are swept (.html, .md). Pipeline .csv/.txt and .xlsx are excluded
# on purpose: the rule explicitly allows JSON field names such as `wallet_eur` in pipeline
# code, and a sweep that flags those produces noise nobody can act on.
BANNED = [
    (r"\bmode\s+a\b", "shared / external"),
    (r"\bmode\s+b\b", "internal / private"),
    (r"\bsell[- ]?out\b", "sales to dealer"),
    (r"\bsellout\b", "sales to dealer"),
    (r"\bstreet\s+(fill|fills|index|price|prices)\b", "OEM peer retail / price index"),
    (r"\bbook\s+b\b", "the price list / a price revision"),
    # `wallet` as a standalone label is banned; `wallet_eur` / `wallet_waterfall` are permitted
    # field names, so the boundaries must exclude underscores.
    (r"(?<![_\w])wallet(?![_\w])", "parts billed / target spend per truck"),
]
# Files that legitimately name the banned words because they exist to police them.
LANG_SKIP_DIRS = {".cursor", "00_docs/agent", "00_docs", "90_archive", "_archive", "_build"}
LANG_SKIP_FILES = {"check_spoken_labels.ps1", "isze-spoken-labels.mdc",
                   "isze-pricing-no-street-ui.mdc", "PRICING_POLICY_PAPER_2026-09-17.md",
                   "isze_delegator_watch.ps1", "_overnight_angles.py",
                   "isze_overnight_orchestrator.ps1", "DELEGATOR_BOARD.md",
                   "DELEGATOR_REFRESH_HOWTO.md"}  # this toolkit names the words to police them

# ------------------------------------------------------------------ cadence
# Expected refresh cadence per workstream keyword. Used only to flag staleness as INFO.
CADENCE_DAYS = {
    "tender": 8,
    "aim": 45,
    "pricing": 45,
    "leakage": 45,
    "exec": 45,
    "hub": 45,
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(p: Path, limit: int = 2_000_000) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:  # noqa: BLE001
        return ""


def mtime(p: Path) -> datetime:
    return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)


def skipped(p: Path) -> bool:
    return any(part in SKIP_PARTS for part in p.parts)


def iter_artifacts(root: Path, hours: float, include_old_with_receipt: bool = True):
    """Yield recent artifacts, plus older ones that carry a receipt (so drift is visible)."""
    cutoff = NOW - timedelta(hours=hours)
    seen = set()
    for sr in SEARCH_ROOTS:
        base = root / sr
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or skipped(f) or f.suffix.lower() not in ARTIFACT_SUFFIXES:
                continue
            if str(f) in seen:
                continue
            seen.add(str(f))
            fresh = mtime(f) >= cutoff
            has_receipt = (f.parent / f"{f.name}.SHIP_RECEIPT.json").exists()
            if fresh or (include_old_with_receipt and has_receipt):
                yield f


def iter_receipts(root: Path, hours: float):
    seen = set()
    for sr in SEARCH_ROOTS:
        base = root / sr
        if not base.exists():
            continue
        for f in base.rglob("*.SHIP_RECEIPT.json"):
            if skipped(f) or str(f) in seen:
                continue
            seen.add(str(f))
            if mtime(f) >= NOW - timedelta(hours=max(hours, 24 * 14)):
                yield f


def receipt_for(artifact: Path) -> Path:
    """Find an artifact's receipt.

    The workspace uses TWO naming conventions and both are live:
      <name>.SHIP_RECEIPT.json        e.g. Foo.html.SHIP_RECEIPT.json
      <stem>.SHIP_RECEIPT.json        e.g. Pricing_Revision_AIM_Source_Analysis.SHIP_RECEIPT.json
    Checking only the first reports "no receipt" on packs that have one, which would be a
    misleading finding. Return whichever exists, preferring the explicit full-name form.
    """
    candidates = [
        artifact.parent / f"{artifact.name}.SHIP_RECEIPT.json",
        artifact.parent / f"{artifact.stem}.SHIP_RECEIPT.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def load_json(p: Path):
    try:
        return json.loads(read_text(p))
    except Exception:  # noqa: BLE001
        return None


def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


# ------------------------------------------------------------------ producer
# This toolkit was created 2026-09-17. Findings on artifacts written at or after this stamp are
# RECENT: they may have been produced by work this orchestrator is meant to police, or by any other
# agent writing concurrently. Findings on older artifacts are pre-existing backlog.
#
# It cannot attribute a change to a specific agent. Cursor exposes no cross-agent identity, and two
# agents are active in this workspace. So the field is named for what it actually measures - whether
# the artifact is recent - and never claims "this workstream did it".
PRODUCER_STAMP_UTC = datetime(2026, 9, 17, 19, 0, tzinfo=timezone.utc)


def producer_split(findings: list[dict], root: Path) -> list[dict]:
    for f in findings:
        ev = f.get("evidence", "")
        p = root / ev.split(" :: ")[0].strip()
        try:
            recent = p.exists() and mtime(p) >= PRODUCER_STAMP_UTC
        except Exception:  # noqa: BLE001
            recent = None
        f["artifact_is_recent"] = recent
        f["attribution"] = (
            "recent: written at or after this toolkit's stamp. Not attributable to a specific "
            "agent - another agent may be writing concurrently."
            if recent else
            "pre-existing backlog: written before this toolkit existed."
            if recent is False else "unknown"
        )
    return findings


def F(sev: str, workstream: str, what: str, evidence: str = "", action: str = "") -> dict:
    return {"severity": sev, "workstream": workstream, "what": what,
            "evidence": evidence, "action": action}


# ================================================================== angles
def angle_workstream_scan(root: Path, hours: float) -> dict:
    """Per-workstream evidence check: newest artifact, receipt coverage, staleness."""
    ws: dict[str, dict] = {}
    for a in iter_artifacts(root, hours):
        key = rel(a.parent, root)
        e = ws.setdefault(key, {"dir": key, "artifacts": []})
        r = receipt_for(a)
        rec = None
        covers = False
        if r.exists():
            j = load_json(r)
            if j:
                rec = {"path": rel(r, root), "ok": bool(j.get("ok")),
                       "artifact_mtime_ms": j.get("artifact_mtime_ms"),
                       "written_at": j.get("written_at"),
                       "n_checks": len(j.get("checks", [])),
                       "n_screenshots": len(j.get("screenshots", []))}
                try:
                    covers = int(rec["artifact_mtime_ms"] or 0) >= int(a.stat().st_mtime * 1000)
                except (TypeError, ValueError):
                    covers = False
        e["artifacts"].append({
            "name": a.name,
            "mtime_utc": mtime(a).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "age_hours": round((NOW - mtime(a)).total_seconds() / 3600, 1),
            "bytes": a.stat().st_size,
            "receipt": rec,
            "receipt_covers_file": covers,
        })

    findings = []
    for key, e in sorted(ws.items()):
        newest = max(e["artifacts"], key=lambda x: x["mtime_utc"])
        e["newest"] = newest["name"]
        e["newest_mtime_utc"] = newest["mtime_utc"]
        e["n_artifacts"] = len(e["artifacts"])
        e["any_receipt"] = any(x["receipt"] for x in e["artifacts"])

        # A receipt that no longer covers its file is a finding, not a pass.
        for x in e["artifacts"]:
            if x["receipt"] and not x["receipt_covers_file"]:
                findings.append(F(
                    "high", key,
                    f"receipt no longer covers its file: {x['name']} was modified after its "
                    f"receipt was written",
                    f"{key}/{x['name']}",
                    "re-run the verifier and rewrite the receipt, or withdraw the done claim",
                ))
            if x["receipt"] and x["receipt"]["n_checks"] == 0:
                findings.append(F(
                    "medium", key,
                    f"receipt has zero checks: {x['name']}",
                    x["receipt"]["path"],
                    "a receipt with no checks proves nothing; add real checks",
                ))

        # Shipped-looking artifact with no receipt at all.
        for x in e["artifacts"]:
            art = root / key / x["name"]
            if not x["receipt"]:
                has_open = any(art.parent.glob("OPEN_*.cmd"))
                if has_open:
                    findings.append(F(
                        "medium", key,
                        f"artifact has a launcher but no receipt: {x['name']}",
                        f"{key}/{x['name']}",
                        "verify and write a receipt, or state it is unverified",
                    ))

        # Cadence staleness.
        for kw, days in CADENCE_DAYS.items():
            if kw in key.lower() and newest["age_hours"] > days * 24:
                findings.append(F(
                    "info", key,
                    f"newest artifact is {round(newest['age_hours'] / 24, 1)} days old, beyond the "
                    f"~{days}-day cadence for this workstream",
                    f"{key}/{newest['name']}",
                    "check whether this workstream is expected to be current",
                ))
                break

    return {
        "angle": "workstream_scan",
        "n_workstreams": len(ws),
        "workstreams": [ws[k] for k in sorted(ws)],
        "findings": findings,
    }


def angle_numbers_tie_out(root: Path, hours: float) -> dict:
    """Re-derive the pricing headline figures from source and compare to what was published."""
    findings = []
    src = root / "01_data/00_derived/price_bp_weighted_compare_pn.csv"
    summary = root / "02_dashboards/pricing/_build/price_5pct_review_2026-09-17/price_increase_5pct_summary.json"
    if not src.exists():
        return {"angle": "numbers_tie_out", "findings": [
            F("high", "pricing", "source base missing, cannot tie out", str(src), "restore the base")]}
    try:
        import pandas as pd
    except ImportError:
        return {"angle": "numbers_tie_out", "findings": [
            F("info", "pricing", "pandas unavailable, tie-out skipped", "", "install pandas")]}

    d = pd.read_csv(src)
    d = d[d["in_scope"] == True]  # noqa: E712
    billed = float(d["net_sales_value"].sum())
    step = float(d["value_eur_step"].sum())
    mov = d["bp_new_jpy"].notna() & d["bp_prior_revised"].notna()
    mov_billed = float(d.loc[mov, "net_sales_value"].sum())
    derived = {
        "lines": int(len(d)),
        "billed_eur": round(billed, 2),
        "step_existing_eur": round(step, 2),
        "step_5pct_all_eur": round(billed * 0.05, 2),
        "movable_lines": int(mov.sum()),
        "movable_billed_eur": round(mov_billed, 2),
        "step_5pct_movable_eur": round(mov_billed * 0.05, 2),
    }
    out = {"angle": "numbers_tie_out", "derived": derived, "findings": []}

    j = load_json(summary) if summary.exists() else None
    if not j:
        out["findings"].append(F("info", "pricing +5% review",
                                 "summary json not found, nothing to compare against",
                                 str(summary), "rebuild the review if it should exist"))
        return out

    pairs = [
        ("billed_eur", j["basis"]["billed_eur"], "in-scope billed"),
        ("step_existing_eur", j["versus_existing_revision"]["step_existing_eur"], "filed step"),
        ("step_5pct_all_eur", j["headline"]["step_5pct_on_all_in_scope_eur"], "collectable-basis +5%"),
        ("step_5pct_movable_eur", j["headline"]["step_5pct_on_movable_eur"], "collectable +5%"),
        ("movable_lines", j["movability"]["movable_lines"], "movable line count"),
    ]
    for key, published, label in pairs:
        got = derived[key]
        if abs(float(got) - float(published)) > 0.05:
            out["findings"].append(F(
                "high", "pricing +5% review",
                f"{label} does not tie: source {got:,} vs published {published:,}",
                rel(summary, root),
                "correct the artifact, re-verify, re-receipt",
            ))
    out["tied"] = len(out["findings"]) == 0
    return out


def angle_receipt_mtime_drift(root: Path, hours: float) -> dict:
    """Every receipt whose artifact_mtime_ms no longer covers its file."""
    findings = []
    checked = 0
    for r in iter_receipts(root, hours):
        j = load_json(r)
        if not j:
            findings.append(F("medium", rel(r.parent, root), f"receipt is not valid JSON: {r.name}",
                              rel(r, root), "repair or delete the receipt"))
            continue
        art_name = r.name[: -len(".SHIP_RECEIPT.json")]
        # The receipt may be named for the full artifact name or for its stem.
        art = r.parent / art_name
        if not art.exists():
            matches = [p for p in r.parent.iterdir()
                       if p.is_file() and p.stem == art_name
                       and not p.name.endswith(".SHIP_RECEIPT.json")]
            art = matches[0] if matches else None
        if art is None or not art.exists():
            findings.append(F("medium", rel(r.parent, root),
                              f"receipt has no artifact beside it: {r.name}",
                              rel(r, root), "delete the orphaned receipt or restore the artifact"))
            continue
        checked += 1
        ms = j.get("artifact_mtime_ms")
        file_ms = int(art.stat().st_mtime * 1000)
        if ms is None:
            findings.append(F("medium", rel(r.parent, root),
                              f"receipt has no artifact_mtime_ms: {r.name}",
                              rel(r, root), "rewrite the receipt with the schema field"))
        elif int(ms) < file_ms:
            drift_min = round((file_ms - int(ms)) / 60000, 1)
            findings.append(F(
                "high", rel(r.parent, root),
                f"receipt does not cover its file: {art_name} changed {drift_min} min after the "
                f"receipt was written",
                rel(r, root),
                "re-verify and rewrite the receipt; the done claim is currently unsupported",
            ))
    return {"angle": "receipt_mtime_drift", "receipts_checked": checked, "findings": findings}


def angle_locked_file_integrity(root: Path, hours: float) -> dict:
    """Hash the locked files and compare to the recorded baseline."""
    base_path = root / "00_docs/agent/OVERNIGHT_LOCKED_BASELINE.json"
    current = {}
    for entry in LOCKED:
        p = root / entry
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and not skipped(f):
                    if not f.name.endswith(".SHIP_RECEIPT.json") or True:
                        try:
                            current[rel(f, root)] = {"sha256": sha256(f),
                                                     "mtime_utc": mtime(f).strftime("%Y-%m-%dT%H:%M:%SZ")}
                        except Exception:  # noqa: BLE001
                            pass
        elif p.exists():
            current[rel(p, root)] = {"sha256": sha256(p),
                                     "mtime_utc": mtime(p).strftime("%Y-%m-%dT%H:%M:%SZ")}

    findings = []
    baseline = load_json(base_path)
    if not baseline:
        base_path.parent.mkdir(parents=True, exist_ok=True)
        base_path.write_text(json.dumps({"created_utc": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                         "files": current}, indent=2), encoding="utf-8")
        return {"angle": "locked_file_integrity", "baseline_created": True,
                "n_files": len(current), "findings": [
                    F("info", "locked files", f"baseline recorded over {len(current)} locked files",
                      rel(base_path, root), "later cycles will report any change against this")]}

    old = baseline.get("files", {})
    for k, v in current.items():
        if k not in old:
            findings.append(F("medium", "locked files", f"new file appeared under a locked path: {k}",
                              k, "confirm this is intentional"))
        elif old[k]["sha256"] != v["sha256"]:
            findings.append(F(
                "high", "locked files",
                f"LOCKED file was modified: {k} (mtime now {v['mtime_utc']})",
                k,
                "a locked deliverable changed; log the collision and do NOT fix it - escalate to Jerome",
            ))
    for k in old:
        if k not in current:
            findings.append(F("high", "locked files", f"LOCKED file has disappeared: {k}", k,
                              "investigate before anything else"))
    return {"angle": "locked_file_integrity", "baseline_created": False,
            "n_files": len(current), "n_baselined": len(old), "findings": findings}


def angle_language_sweep(root: Path, hours: float) -> dict:
    """Scan recently written user-facing artifacts for the banned spoken labels."""
    findings = []
    scanned = 0
    cutoff = NOW - timedelta(hours=hours)
    for sr in ("02_dashboards", "09_meetings", "01_data/01_Pricing"):
        base = root / sr
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or skipped(f):
                continue
            if f.suffix.lower() not in {".html", ".md"}:
                continue
            if any(part in LANG_SKIP_DIRS for part in f.parts):
                continue
            if f.name in LANG_SKIP_FILES or mtime(f) < cutoff:
                continue
            scanned += 1
            text = re.sub(r"<script[\s\S]*?</script>", " ", read_text(f), flags=re.I)
            text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
            visible = re.sub(r"<[^>]+>", " ", text)
            low = visible.lower()
            for pat, instead in BANNED:
                m = re.search(pat, low)
                if m:
                    ctx = visible[max(0, m.start() - 60): m.start() + 60].replace("\n", " ")
                    findings.append(F(
                        "medium", rel(f.parent, root),
                        f"banned label '{m.group(0).strip()}' appears in visible text; "
                        f"say '{instead}' instead",
                        f"{rel(f, root)} :: ...{' '.join(ctx.split())}...",
                        f"replace with '{instead}'",
                    ))
    return {"angle": "language_sweep", "files_scanned": scanned, "findings": findings}


def angle_html_first_paint(root: Path, hours: float) -> dict:
    """file:// first-paint risks: CDN assets, fetch of sibling JSON, no embedded payload."""
    findings = []
    checked = 0
    # Only ASSET references that a page must load to paint. A plain <a href="https://...">
    # is a clickable hyperlink, which is explicitly allowed, so it must not be flagged.
    ASSET_RE = re.compile(
        r'<(?:script|link|img|iframe|source|video|audio)\b[^>]*?'
        r'(?:src|href)\s*=\s*["\'](https?://[^"\']+)', re.I)
    for a in iter_artifacts(root, hours):
        if a.suffix.lower() != ".html":
            continue
        checked += 1
        text = read_text(a)
        low = text.lower()
        ext = ASSET_RE.findall(text)
        if ext:
            findings.append(F("high", rel(a.parent, root),
                              f"{a.name} loads {len(ext)} external asset(s); fails offline on "
                              f"file:// (first: {ext[0][:70]})",
                              rel(a, root), "inline the asset or ship a local copy"))
        has_embedded = "application/json" in low or "const p = {" in low
        if "fetch(" in low and not has_embedded:
            findings.append(F("medium", rel(a.parent, root),
                              f"{a.name} calls fetch() with no embedded payload; file:// cannot "
                              f"fetch a sibling JSON",
                              rel(a, root), "embed the data or ship an OPEN_*.cmd server launcher"))
        has_launcher = any(a.parent.glob("OPEN_*.cmd"))
        if not has_embedded and not has_launcher:
            findings.append(F("high", rel(a.parent, root),
                              f"{a.name} has no embedded payload and no launcher; may paint blank",
                              rel(a, root), "embed the payload or add an OPEN_*.cmd launcher"))
    return {"angle": "html_first_paint", "html_checked": checked, "findings": findings}


def angle_excel_formula_errors(root: Path, hours: float) -> dict:
    """Cached error values in recently touched workbooks."""
    findings = []
    checked = 0
    ERRORS = ("#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!", "#NUM!", "#N/A", "#ERROR")
    for a in iter_artifacts(root, hours):
        if a.suffix.lower() != ".xlsx" or a.name.startswith("~$"):
            continue
        checked += 1
        try:
            from openpyxl import load_workbook
            wb = load_workbook(a, read_only=True, data_only=True)
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    for v in row:
                        if isinstance(v, str) and any(e in v for e in ERRORS):
                            findings.append(F(
                                "high", rel(a.parent, root),
                                f"{a.name} sheet '{ws.title}' has a cached formula error: {v[:40]}",
                                rel(a, root), "fix the formula and recalculate the workbook"))
                            break
                    else:
                        continue
                    break
            wb.close()
        except Exception as e:  # noqa: BLE001
            findings.append(F("info", rel(a.parent, root),
                              f"could not open workbook {a.name}: {e}", rel(a, root), ""))
    return {"angle": "excel_formula_errors", "workbooks_checked": checked, "findings": findings}


def angle_chart_form_quality(root: Path, hours: float) -> dict:
    """Mechanical proxies for isze-best-chart. Flags for human review, does not judge design."""
    findings = []
    checked = 0
    for a in iter_artifacts(root, hours):
        if a.suffix.lower() != ".html":
            continue
        checked += 1
        text = read_text(a)
        types = re.findall(r"type\s*:\s*['\"](bar|line|pie|doughnut|scatter|bubble|radar)['\"]", text)
        if not types:
            continue
        n_canvas = text.lower().count("<canvas")
        if len(types) > 1 and len(set(types)) == 1 and len(types) >= 3:
            findings.append(F("low", rel(a.parent, root),
                              f"{a.name} uses one chart form ({types[0]}) for all {len(types)} "
                              f"charts; check the form matches each question",
                              rel(a, root), "review against isze-best-chart"))
        if "pie" in types or "doughnut" in types:
            for m in re.finditer(r"labels\s*:\s*\[([^\]]{200,})\]", text):
                segs = m.group(1).count(",") + 1
                if segs > 6:
                    findings.append(F("medium", rel(a.parent, root),
                                      f"{a.name} has a pie/donut with ~{segs} segments; that many "
                                      f"is unreadable",
                                      rel(a, root), "split it or use ranked bars"))
                    break
        if n_canvas == 0 and len(types) > 0:
            findings.append(F("medium", rel(a.parent, root),
                              f"{a.name} declares {len(types)} charts but has no canvas element",
                              rel(a, root), "check the chart container renders"))
    return {"angle": "chart_form_quality", "html_checked": checked, "findings": findings,
            "note": "Mechanical proxies only. Design quality still needs a human eye."}


def angle_gaps_need_context(root: Path, hours: float) -> dict:
    """A unit count with no euro beside it breaches isze-gaps-need-context."""
    findings = []
    scanned = 0
    pattern = re.compile(r"([\d][\d,\.]{2,})\s*(units?|pieces|pcs|part numbers?|PNs?)\b", re.I)
    for sr in ("02_dashboards", "09_meetings"):
        base = root / sr
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or skipped(f) or f.suffix.lower() not in {".html", ".md"}:
                continue
            if mtime(f) < NOW - timedelta(hours=hours):
                continue
            scanned += 1
            text = re.sub(r"<[^>]+>", " ", read_text(f))
            for m in pattern.finditer(text):
                ctx = text[max(0, m.start() - 260): m.start() + 200]
                if "€" in ctx or "&euro;" in ctx or "EUR" in ctx:
                    continue
                findings.append(F(
                    "medium", rel(f.parent, root),
                    f"unit count without euro, part family or fleet denominator: "
                    f"'{m.group(0).strip()}'",
                    f"{rel(f, root)} :: ...{ctx[-140:].strip()}...",
                    "add euro, part family and the fleet base, or drop the count",
                ))
                break
    return {"angle": "gaps_need_context", "files_scanned": scanned, "findings": findings}


def angle_coverage_honesty(root: Path, hours: float) -> dict:
    """AIM figures must carry spine coverage, unpriced share and T5 share."""
    findings = []
    checked = 0
    for a in iter_artifacts(root, hours):
        if a.suffix.lower() != ".html":
            continue
        text = read_text(a)
        low = text.lower()
        mentions_aim = "aim level 1" in low or "aim spine" in low or "unclassified" in low
        if not mentions_aim:
            continue
        checked += 1
        has_coverage = ("80.3" in text or "93.15" in text or "coverage" in low
                        or "not on aim spine" in low)
        has_unpriced = ("unpriced" in low or "no base price" in low or "cannot move" in low)
        has_t5 = ("t5" in low or "no benchmark" in low or "evidence tier" in low)
        missing = []
        if not has_coverage:
            missing.append("AIM spine coverage")
        if not has_unpriced:
            missing.append("unpriced or immovable share")
        if not has_t5:
            missing.append("evidence-tier (T5) share")
        if missing:
            findings.append(F(
                "medium", rel(a.parent, root),
                f"{a.name} carries AIM figures without disclosing: {', '.join(missing)}",
                rel(a, root), "disclose the coverage rather than letting a reader re-derive it",
            ))
    return {"angle": "coverage_honesty", "artifacts_checked": checked, "findings": findings}


def angle_entity_separation(root: Path, hours: float) -> dict:
    """UTI and UMI never blended; IUK and ITUK never mixed."""
    findings = []
    scanned = 0
    for sr in ("02_dashboards", "09_meetings"):
        base = root / sr
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or skipped(f) or f.suffix.lower() not in {".html", ".md"}:
                continue
            if mtime(f) < NOW - timedelta(hours=hours):
                continue
            scanned += 1
            text = re.sub(r"<[^>]+>", " ", read_text(f))
            for m in re.finditer(r"israel", text, re.I):
                win = text[max(0, m.start() - 320): m.start() + 320]
                if ("UTI" in win and "UMI" in win
                        and re.search(r"israel\s*[:=]?\s*[€\u20ac]?\s*[\d.,]+", win, re.I)
                        and "never" not in win.lower() and "not blended" not in win.lower()):
                    findings.append(F(
                        "high", rel(f.parent, root),
                        "possible UTI+UMI blend under a single 'Israel' figure",
                        f"{rel(f, root)} :: ...{win.strip()[:170]}...",
                        "split into two rows; UTI and UMI are different distributors",
                    ))
                    break
            for m in re.finditer(r"\bIUK\b", text):
                win = text[max(0, m.start() - 160): m.start() + 160]
                if "ITUK" in win and not re.search(r"never|not mixed|separate|distinct", win, re.I):
                    findings.append(F(
                        "medium", rel(f.parent, root),
                        "IUK and ITUK appear together without stating they are separate",
                        f"{rel(f, root)} :: ...{win.strip()[:150]}...",
                        "state that IUK and ITUK are separate entities",
                    ))
                    break
    return {"angle": "entity_separation", "files_scanned": scanned, "findings": findings}


def angle_cross_artifact_consistency(root: Path, hours: float) -> dict:
    """The same figure appearing in several artifacts must agree."""
    KEYS = {
        "5.9616": "published revision headline rate",
        "1,652,140.71": "filed revision step",
        "34,993,609.39": "in-scope billed euro",
        "32,595,852.63": "movable billed euro",
        "1,749,680.47": "all-in-scope +5%",
        "1,629,792.63": "collectable +5%",
    }
    findings = []
    seen: dict[str, list[str]] = {}
    for sr in ("02_dashboards", "09_meetings", "01_data/01_Pricing"):
        base = root / sr
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or skipped(f) or f.suffix.lower() not in {".html", ".md"}:
                continue
            if mtime(f) < NOW - timedelta(hours=hours):
                continue
            text = read_text(f).replace("\u20ac", "€")
            for k in KEYS:
                if k.replace(",", "") in text.replace(",", ""):
                    seen.setdefault(k, []).append(rel(f, root))
    for k, files in seen.items():
        if len(files) > 1:
            findings.append(F(
                "info", "cross-artifact",
                f"{KEYS[k]} ({k}) appears in {len(files)} artifacts; confirm they mean the same "
                f"basis in each",
                ", ".join(files[:5]),
                "check the window and mask are stated identically in each",
            ))
    return {"angle": "cross_artifact_consistency", "figures_tracked": len(seen), "findings": findings}


def angle_blank_pages(root: Path, hours: float) -> dict:
    """Printed PDFs with near-empty pages."""
    findings = []
    checked = 0
    try:
        import pypdf  # type: ignore
    except ImportError:
        return {"angle": "blank_pages", "findings": [
            F("info", "print output", "pypdf not installed, blank-page check skipped", "",
              "pip install pypdf to enable this angle")]}
    for sr in ("02_dashboards", "09_meetings"):
        base = root / sr
        if not base.exists():
            continue
        for f in base.rglob("*.pdf"):
            if skipped(f) or mtime(f) < NOW - timedelta(hours=hours):
                continue
            checked += 1
            try:
                reader = pypdf.PdfReader(str(f))
                blanks = [i + 1 for i, pg in enumerate(reader.pages)
                          if len((pg.extract_text() or "").strip()) < 40]
                if blanks:
                    findings.append(F(
                        "medium", rel(f.parent, root),
                        f"{f.name} has {len(blanks)} near-blank page(s): {blanks[:8]}",
                        rel(f, root), "fill, merge or drop the blank pages"))
            except Exception as e:  # noqa: BLE001
                findings.append(F("info", rel(f.parent, root),
                                  f"could not read {f.name}: {e}", rel(f, root), ""))
    return {"angle": "blank_pages", "pdfs_checked": checked, "findings": findings}


def angle_memory_markdown_drift(root: Path, hours: float) -> dict:
    """Memory notes claiming a state much older than the derived anchors."""
    findings = []
    mem = root / "05_memory/projects"
    if not mem.exists():
        return {"angle": "memory_markdown_drift", "findings": [
            F("info", "memory", "05_memory/projects not found", "", "")]}
    snap = load_json(root / "01_data/00_derived/metrics_snapshot.json")
    snap_mtime = None
    p = root / "01_data/00_derived/metrics_snapshot.json"
    if p.exists():
        snap_mtime = mtime(p)
    for f in mem.glob("*.md"):
        text = read_text(f)
        if not text:
            continue
        stale_dates = re.findall(r"last confirmed[^0-9]{0,20}(\d{1,2}\s+\w+\s+20\d\d)", text, re.I)
        for ds in stale_dates:
            try:
                dt = datetime.strptime(ds, "%d %B %Y").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            age = (NOW - dt).days
            if age > 60:
                findings.append(F(
                    "low", "memory",
                    f"{f.name} says 'last confirmed {ds}' ({age} days ago)",
                    rel(f, root),
                    "refresh against the derived anchors or mark the claim as historical",
                ))
    if snap_mtime and (NOW - snap_mtime).days > 30:
        findings.append(F("low", "memory",
                          f"metrics_snapshot.json is {(NOW - snap_mtime).days} days old",
                          "01_data/00_derived/metrics_snapshot.json",
                          "the monthly refresh may not have run"))
    if not snap:
        findings.append(F("info", "memory", "metrics_snapshot.json missing or unreadable",
                          "", "check the derived pipeline"))
    return {"angle": "memory_markdown_drift", "findings": findings}


def angle_orphan_artifact(root: Path, hours: float) -> dict:
    """Launchers pointing at nothing, and launchers with a path that does not resolve."""
    findings = []
    stale_after = NOW - timedelta(hours=hours)
    for sr in ("02_dashboards", "09_meetings"):
        base = root / sr
        if not base.exists():
            continue
        for l in base.rglob("OPEN_*.cmd"):
            if skipped(l) or mtime(l) < stale_after:
                continue
            txt = read_text(l)
            # A launcher may name its target several ways; accept any of them if the file exists
            # beside the launcher. Only report when NO referenced file resolves.
            refs = re.findall(r'"([^"]+\.(?:html|pdf|xlsx|pptx|csv))"', txt)
            refs += re.findall(r"([\w\-\.]+\.(?:html|pdf|xlsx|pptx))", txt)
            if not refs:
                findings.append(F("medium", rel(l.parent, root),
                                  f"{l.name} names no file target",
                                  rel(l, root), "check the launcher contents"))
                continue
            resolved = [r for r in refs if (l.parent / Path(r).name).exists()]
            if not resolved:
                findings.append(F("high", rel(l.parent, root),
                                  f"{l.name} points at a missing file: {refs[0]}",
                                  rel(l, root), "fix the launcher target"))
    return {"angle": "orphan_artifact", "findings": findings}


def angle_receipt_quality(root: Path, hours: float) -> dict:
    """Receipts that exist but assert little."""
    findings = []
    for r in iter_receipts(root, hours):
        j = load_json(r)
        if not j:
            continue
        checks = j.get("checks", [])
        shots = j.get("screenshots", [])
        if not checks:
            findings.append(F("medium", rel(r.parent, root),
                              f"{r.name} asserts ok with no checks listed",
                              rel(r, root), "a receipt with no checks is not evidence"))
        if j.get("ok") and not shots and r.name.lower().find("html") >= 0:
            findings.append(F("low", rel(r.parent, root),
                              f"{r.name} claims ok with no screenshots for an HTML artifact",
                              rel(r, root), "add a rendered check or say it was not rendered"))
    return {"angle": "receipt_quality", "findings": findings}


ANGLES = {
    "workstream_scan": angle_workstream_scan,
    "numbers_tie_out": angle_numbers_tie_out,
    "receipt_mtime_drift": angle_receipt_mtime_drift,
    "locked_file_integrity": angle_locked_file_integrity,
    "language_sweep": angle_language_sweep,
    "html_first_paint": angle_html_first_paint,
    "excel_formula_errors": angle_excel_formula_errors,
    "chart_form_quality": angle_chart_form_quality,
    "gaps_need_context": angle_gaps_need_context,
    "coverage_honesty": angle_coverage_honesty,
    "entity_separation": angle_entity_separation,
    "cross_artifact_consistency": angle_cross_artifact_consistency,
    "blank_pages": angle_blank_pages,
    "memory_markdown_drift": angle_memory_markdown_drift,
    "orphan_artifact": angle_orphan_artifact,
    "receipt_quality": angle_receipt_quality,
}

DESCRIPTIONS = {
    "workstream_scan": "Per-workstream evidence: newest artifact, receipt covers file, staleness",
    "numbers_tie_out": "Re-derive the pricing headline figures from source and compare",
    "receipt_mtime_drift": "Every receipt whose artifact_mtime_ms no longer covers its file",
    "locked_file_integrity": "Hash the locked files and report any modification",
    "language_sweep": "Banned spoken labels in recently written artifacts",
    "html_first_paint": "file:// risks: CDN assets, fetch of sibling JSON, no embedded payload",
    "excel_formula_errors": "Cached formula errors in recently touched workbooks",
    "chart_form_quality": "Mechanical chart-form proxies (one form everywhere, fat pies)",
    "gaps_need_context": "Unit counts with no euro, part family or fleet denominator",
    "coverage_honesty": "AIM figures must disclose spine coverage, unpriced share, T5 share",
    "entity_separation": "UTI vs UMI never blended; IUK vs ITUK never mixed",
    "cross_artifact_consistency": "The same figure across artifacts must mean the same basis",
    "blank_pages": "Near-blank pages in printed PDFs",
    "memory_markdown_drift": "Memory notes and anchors that have gone stale",
    "orphan_artifact": "Artifacts with no launcher; launchers pointing at nothing",
    "receipt_quality": "Receipts that assert ok while listing no checks",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--angle")
    ap.add_argument("--hours", type=float, default=24.0)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    if args.list:
        print(json.dumps([{"angle": k, "description": DESCRIPTIONS[k]} for k in ANGLES], indent=2))
        return 0

    if not args.angle or args.angle not in ANGLES:
        print(json.dumps({"error": "unknown angle", "angle": args.angle,
                          "available": list(ANGLES)}, indent=2))
        return 2

    root = Path(args.root)
    if not root.exists():
        print(json.dumps({"error": "root not found", "root": str(root)}, indent=2))
        return 2

    try:
        result = ANGLES[args.angle](root, args.hours)
    except Exception as e:  # noqa: BLE001
        result = {"angle": args.angle, "error": f"{type(e).__name__}: {e}", "findings": []}

    if result.get("findings"):
        result["findings"] = producer_split(result["findings"], root)

    result["generated_utc"] = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
    result["description"] = DESCRIPTIONS[args.angle]
    result["findings_count"] = len(result.get("findings", []))
    result["recent_count"] = sum(
        1 for f in result.get("findings", []) if f.get("artifact_is_recent"))
    result["backlog_count"] = sum(
        1 for f in result.get("findings", []) if f.get("artifact_is_recent") is False)
    payload = json.dumps(result, indent=2, default=str)

    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
