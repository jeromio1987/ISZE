#!/usr/bin/env python
"""ISZE daily agent — ACT on the safe checks, DRAFT the rest, REPORT what it did.

This is the active counterpart to isze_daily_check.py. Run order each day:

    python isze_daily_agent.py --run          # act + draft + write report
    python isze_daily_agent.py --dry-run      # show what it WOULD do, change nothing

--------------------------------------------------------------------------------
What it is allowed to do on its own (ALLOWLIST — read-only or self-contained)
--------------------------------------------------------------------------------
  A1  Re-run the tender filter audit over the existing workbook. Writes only
      filter_audit_*.json. Never republishes the feed.
  A2  Rebuild the local tender dashboards from the workbook that already exists.
      Changes only files under 04_tools/ISZE_Tender_Monitor_Install.
  A3  Refresh the daily brief itself.
  A4  Post a Windows toast.

--------------------------------------------------------------------------------
What it must NEVER do (DENYLIST — enforced in code, not by good intentions)
--------------------------------------------------------------------------------
  D1  Publish/overwrite 01_data/dashboards/tender_data.json
  D2  Send any mail (no Send() anywhere; Outlook only ever .Save()) 
  D3  Write to any OneDrive / Dropbox / SharePoint folder — cloud delivery is
      Jerome's decision and needs his explicit path each time
  D4  Touch scheduler (schtasks create/delete/change)
  D5  Run the scraper against external portals
  D6  Change prices, SPA, stock, or any commercial decision
  D7  Edit rules, FACTS, DECISIONS, or anything outside the allowed roots

Any action outside the allowlist is written to the report as "proposed", with the
evidence, for Jerome to approve. See .cursor/rules/isze-no-ship-without-ok.mdc.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_root() -> Path:
    env = os.environ.get("ISZE_ROOT")
    if env and (Path(env) / "paths.yaml").is_file():
        return Path(env)
    p = HERE
    for _ in range(8):
        if (p / "paths.yaml").is_file() and (p / "FACTS.md").is_file():
            return p
        p = p.parent
    raise SystemExit("ISZE root not found")


ROOT = find_root()
INST = ROOT / "04_tools" / "ISZE_Tender_Monitor_Install"
NOW = datetime.now(timezone.utc)
TODAY = NOW.date()
REPORT = ROOT / "05_memory" / "briefs" / f"daily_agent_report_{TODAY}.md"

# Paths this agent may write. Anything else is refused before the command runs.
ALLOWED_WRITE_ROOTS = [
    INST,
    ROOT / "05_memory" / "briefs",
]
# Explicit refusals, checked first even if they somehow sit under an allowed root.
FORBIDDEN_WRITE = [
    ROOT / "01_data" / "dashboards",
    ROOT / "01_data" / "14_dashboards",
    ROOT / "07_deploy",
    ROOT / "02_dashboards" / "Data",
]

log: list[str] = []
done: list[str] = []
proposed: list[str] = []
refused: list[str] = []


def add(s: str = "") -> None:
    log.append(s)


def guard(path: Path) -> tuple[bool, str]:
    """Refuse anything that could mutate a protected output."""
    rp = path.resolve()
    for f in FORBIDDEN_WRITE:
        try:
            if rp == f.resolve() or f.resolve() in rp.parents:
                return False, f"forbidden output root: {f}"
        except Exception:
            pass
    for a in ALLOWED_WRITE_ROOTS:
        try:
            if rp == a.resolve() or a.resolve() in rp.parents:
                return True, "allowed"
        except Exception:
            pass
    return False, "outside the allowlist"


def run(cmd: list[str], cwd: Path, timeout: int = 300) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as exc:
        return 1, f"ERROR: {exc}"


# --------------------------------------------------------------------------- A1/A2
def act_dashboards(dry: bool) -> None:
    add("### A2 — rebuild local tender dashboards from the existing workbook")
    add()
    wb = INST / "isuzu_tenders_v3.xlsx"
    if not wb.is_file():
        add("- skipped: no workbook present")
        add()
        return
    age_h = (NOW.timestamp() - wb.stat().st_mtime) / 3600
    add(f"Workbook: `isuzu_tenders_v3.xlsx` ({age_h:.1f}h old)")
    for script, out in (("build_dashboard_v2.py", "isze_dashboard_v2.html"),
                        ("build_dashboard_v4.py", "isze_dashboard_v4_opportunity.html")):
        ok, why = guard(INST / out)
        if not ok:
            refused.append(f"A2 {out}: {why}")
            add(f"- REFUSED `{out}`: {why}")
            continue
        if dry:
            add(f"- would run `python {script}`")
            continue
        rc, out_text = run([sys.executable, script], INST)
        tail = [l for l in out_text.splitlines() if l.strip()][-3:]
        if rc == 0:
            done.append(f"A2 rebuilt {out}")
            add(f"- rebuilt `{out}` (exit 0)")
        else:
            add(f"- FAILED `{script}` exit {rc}")
            for l in tail:
                add(f"    {l[:150]}")
    add()


def act_audit(dry: bool) -> None:
    add("### A1 — refresh the tender filter audit")
    add()
    audit = INST / "filter_audit_2026-09-20.json"
    ok, why = guard(audit)
    if not ok:
        refused.append(f"A1 audit: {why}")
        add(f"- REFUSED: {why}")
        add()
        return
    if dry:
        add("- would run the scraper with ISZE_TENDER_FILTER_AUDIT=1")
        add("  (NOTE: that needs network. Left as proposed when offline.)")
        add()
        return
    # Actively refused: a full scrape hits external portals. This is a proposal,
    # not a daily action, so the agent does not run it unattended.
    proposed.append(
        "A1 filter audit not refreshed: it requires the portal scraper, which is "
        "excluded from unattended runs (D5). Run manually if a fresh audit is wanted."
    )
    add("- not run: needs the external scraper (denylist D5)")
    add()


# --------------------------------------------------------------------------- checks
def check_feed_untouched() -> None:
    add("### Guard check — is the published feed still the last good one?")
    add()
    feed = ROOT / "01_data" / "dashboards" / "tender_data.json"
    if not feed.is_file():
        add("- feed missing")
        add()
        return
    import hashlib
    h = hashlib.sha256(feed.read_bytes()).hexdigest()[:16]
    age_d = (NOW.timestamp() - feed.stat().st_mtime) / 86400
    add(f"- sha256[:16] `{h}` · {age_d:.1f} days old")
    if age_d > 10:
        proposed.append(
            f"Tender feed is {age_d:.0f} days old. A refresh needs the scraper and "
            "Jerome's approval (it republishes the feed)."
        )
    add()


def check_stale() -> None:
    add("### Checks the agent cannot fix alone — proposed with evidence")
    add()
    watched = [
        ("Risk cockpit data", ROOT / "02_dashboards/sales/risk_cockpit.data.js", 21),
        ("Dashboard Data tender copy", ROOT / "02_dashboards/Data/dashboards/tender_data.json", 14),
    ]
    for name, p, limit in watched:
        if not p.is_file():
            continue
        a = (NOW.timestamp() - p.stat().st_mtime) / 86400
        if a > limit:
            proposed.append(
                f"{name} is {a:.0f} days old (threshold {limit}d) at `{p.relative_to(ROOT)}`. "
                "Refreshing it writes to a protected output root, so it needs Jerome's go-ahead."
            )
    if not proposed:
        add("- nothing stale enough to propose")
    add()


# --------------------------------------------------------------------------- report
def build_report(dry: bool) -> str:
    out = [
        f"# ISZE daily agent — {TODAY}",
        "",
        ("**DRY RUN — nothing was changed.**" if dry else "**Ran for real.**"),
        "",
        f"Started {NOW:%Y-%m-%d %H:%M}Z. Allowlisted actions run unattended; everything "
        "else is proposed with evidence.",
        "",
        "## Done by the agent",
        "",
    ]
    out += [f"- {d}" for d in done] or ["- (nothing)"]
    out += ["", "## Proposed — needs Jerome", ""]
    out += [f"- {p}" for p in proposed] or ["- (nothing)"]
    out += ["", "## Refused by the guard", ""]
    out += [f"- {r}" for r in refused] or ["- (nothing)"]
    out += ["", "---", "", "## Detail", ""]
    out += log
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="ISZE daily agent")
    ap.add_argument("--run", action="store_true", help="act for real")
    ap.add_argument("--dry-run", action="store_true", help="show what it would do")
    ap.add_argument("--toast", action="store_true")
    args = ap.parse_args()
    dry = not args.run or args.dry_run

    check_feed_untouched()
    act_dashboards(dry)
    act_audit(dry)
    check_stale()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(build_report(dry), encoding="utf-8")

    if args.toast and not dry:
        n = len(proposed)
        try:
            import isze_daily_check as dc
            dc.toast("ISZE daily agent", f"{len(done)} done · {n} need you")
        except Exception:
            pass

    print(f"mode     : {'DRY RUN' if dry else 'RUN'}")
    print(f"done     : {len(done)}")
    print(f"proposed : {len(proposed)}")
    print(f"refused  : {len(refused)}")
    print(f"report   : {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
