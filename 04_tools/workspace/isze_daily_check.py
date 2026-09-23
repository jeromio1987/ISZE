#!/usr/bin/env python
"""ISZE daily brief — what is off, and what needs Jerome.

Aggregates signals that already exist in the workspace; it does not compute new
metrics and does not scrape. Writes a markdown brief to 05_memory/briefs/ and,
optionally, saves an Outlook DRAFT to Jerome. It NEVER sends mail.

Usage:
    python isze_daily_check.py                 # write the brief file
    python isze_daily_check.py --draft         # also save an Outlook draft
    python isze_daily_check.py --quiet         # file only, minimal stdout

Exit code is 0 even when the workspace has failures — this job reports, it does
not judge. The brief itself states the verdict.

Why draft-only: .cursor/rules/isze-no-ship-without-ok.mdc. Jerome sends.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --------------------------------------------------------------------------- root
def find_root() -> Path:
    env = os.environ.get("ISZE_ROOT")
    if env and (Path(env) / "paths.yaml").is_file():
        return Path(env)
    p = Path(__file__).resolve().parent
    for _ in range(8):
        if (p / "paths.yaml").is_file() and (p / "FACTS.md").is_file():
            return p
        p = p.parent
    raise SystemExit("ISZE root not found (set ISZE_ROOT or run inside the tree)")


ROOT = find_root()
NOW = datetime.now(timezone.utc)
TODAY = NOW.date()

# Self-addressed, matching the other self-drafts already in Drafts.
DRAFT_TO = "jerome.van.der.pluym@isuzu-e.com"

OUT_DIR = ROOT / "05_memory" / "briefs"
OUT_FILE = OUT_DIR / f"daily_brief_{TODAY}.md"

lines: list[str] = []
alerts: list[str] = []      # things that need Jerome
notes: list[str] = []       # context worth knowing
verdict = "all clear"


def add(s: str = "") -> None:
    lines.append(s)


# --------------------------------------------------------------------------- helpers
def age_days(p: Path) -> float | None:
    if not p.is_file():
        return None
    m = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    return (NOW - m).total_seconds() / 86400.0


def fmt_age(d: float | None) -> str:
    if d is None:
        return "missing"
    if d < 1:
        return f"{int(d * 24)}h ago"
    return f"{d:.0f}d ago"


def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def run(cmd: list[str], timeout: int = 45) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return r.stdout or ""
    except Exception as exc:
        return f"ERROR: {exc}"


# --------------------------------------------------------------------------- 1. pipeline
def section_pipeline() -> None:
    global verdict
    add("## 1. Pipeline health")
    add()
    rep = ROOT / "01_data" / "00_derived" / "_verification_report.json"
    d = read_json(rep)
    if not d:
        alerts.append("Pipeline: verification report missing or unreadable.")
        add(f"- **{fmt_age(age_days(rep))}** — `_verification_report.json` unreadable")
        add()
        return

    summary = d.get("summary") or {}
    fails = int(summary.get("fail") or 0)
    warns = int(summary.get("warn") or 0)
    passes = int(summary.get("pass") or 0)
    gen = str(d.get("generated_at") or "")[:19]
    add(f"Report generated **{gen}Z** · {passes} pass · {warns} warn · {fails} fail")
    add()

    bad = [c for c in (d.get("checks") or [])
           if str(c.get("status", "")).lower() in ("fail", "warn", "error")]
    if bad:
        # failures first — they are what he acts on
        for c in sorted(bad, key=lambda x: 0 if x.get("status") == "fail" else 1):
            st = str(c.get("status", "")).upper()
            mark = "**FAIL**" if st == "FAIL" else st
            add(f"- {mark} `{c.get('id')}` — {c.get('message')}")
            if st == "FAIL":
                alerts.append(f"Pipeline FAIL: {c.get('id')} — {c.get('message')}")
        add()
    else:
        add("- No warnings or failures.")
        add()

    # freshness of the report itself
    ra = age_days(rep)
    if ra is not None and ra > 2:
        alerts.append(f"Pipeline report is {ra:.0f} days old — the pipeline may not have run.")
        add(f"- ⚠ report is {fmt_age(ra)}; expect a fresh one after each pipeline run")
        add()


# --------------------------------------------------------------------------- 2. attention
def section_attention() -> None:
    add("## 2. Needs your attention")
    add()
    found = False

    drift = sorted((ROOT / "05_memory" / "briefs").glob("automation_drift_*.md"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if drift:
        newest = drift[0]
        add(f"Latest automation drift: **{newest.name}** ({fmt_age(age_days(newest))})")
        try:
            txt = newest.read_text(encoding="utf-8", errors="replace")
            # lines are numbered "  10|1. **[MEDIUM]** ..." in that report
            items = re.findall(r"^\s*\d+\|\s*(\d+)\.\s*\*\*\[(HIGH|MEDIUM|LOW)\]\*\*\s*(.+)$",
                               txt, re.M)
            if not items:
                items = re.findall(r"^\s*\d+\.\s*\*\*\[(HIGH|MEDIUM|LOW)\]\*\*\s*(.+)$", txt, re.M)
                items = [("", a, b) for a, b in items]
            if items:
                found = True
                for _, sev, msg in items[:6]:
                    add(f"- [{sev}] {msg.strip()[:200]}")
                if any(s == "HIGH" for _, s, _ in items):
                    alerts.append("Automation drift has a HIGH item.")
            else:
                add("- (no numbered items parsed from the drift report)")
        except Exception as exc:
            add(f"- could not read drift report: {exc}")
        add()

    integ = ROOT / "01_data" / "00_derived" / "_data_integrity_open_issues.md"
    da = age_days(integ)
    if da is not None:
        found = True
        add(f"Data integrity open issues: {fmt_age(da)} "
            f"(`01_data/00_derived/_data_integrity_open_issues.md`)")
        if da > 14:
            alerts.append(f"Data integrity open issues not refreshed in {da:.0f} days.")
        add()

    facts = ROOT / "01_data" / "00_derived" / "_facts_drift_report.md"
    if facts.is_file():
        found = True
        add(f"FACTS drift report: {fmt_age(age_days(facts))}")
        try:
            t = facts.read_text(encoding="utf-8", errors="replace")
            for m in re.findall(r"^\s*[-*]\s*(.+)$", t, re.M)[:4]:
                add(f"  - {m.strip()[:180]}")
        except Exception:
            pass
        add()

    if not found:
        add("- No drift or integrity reports found to summarise.")
        add()


# --------------------------------------------------------------------------- 3. freshness
CHECK = [
    ("Tender feed", "01_data/dashboards/tender_data.json", 10),
    ("Sales fact", "01_data/00_derived/sales_fact.parquet", 10),
    ("Metrics snapshot", "01_data/00_derived/metrics_snapshot.json", 10),
    ("Exec aftersales paper", "02_dashboards/sales/ISZE_Exec_Aftersales_Paper.html", 21),
    ("Risk cockpit data", "02_dashboards/sales/risk_cockpit.data.js", 21),
    ("Dashboard Data tender copy", "02_dashboards/Data/dashboards/tender_data.json", 14),
]


def section_freshness() -> None:
    add("## 3. Freshness — is anything stale?")
    add()
    add("| Thing | Last touched | Age | Threshold |")
    add("|---|---|---|---|")
    for name, rel, limit in CHECK:
        p = ROOT / rel
        a = age_days(p)
        state = "ok"
        if a is None:
            state = "**missing**"
            alerts.append(f"{name} is missing at {rel}")
        elif a > limit:
            state = f"**stale >{limit}d**"
            alerts.append(f"{name} is {a:.0f} days old (threshold {limit}d): {rel}")
        add(f"| {name} | {fmt_age(a)} | {state} | {limit}d |")
    add()


# --------------------------------------------------------------------------- 4. tenders
def section_tenders() -> None:
    add("## 4. Tender watch")
    add()
    feed = ROOT / "01_data" / "dashboards" / "tender_data.json"
    d = read_json(feed)
    if not d:
        add("- feed unreadable; skipping")
        add()
        return
    ops = d.get("opportunities") or []
    meta = d.get("meta") or {}
    stats = meta.get("stats") or {}
    gen = str(meta.get("generated_at") or "")[:16]

    # Match only on the notice title and buyer. Matching the whole record is a trap:
    # every pickup carries product_segment_label "Pickup / D-Max-shaped", so a
    # whole-record search reports hundreds of phantom Isuzu hits.
    def names_isuzu(o: dict) -> bool:
        text = f"{o.get('title', '')} {o.get('title_raw', '')} {o.get('buyer', '')}"
        return bool(re.search(r"(?i)(isuzu|\bd[-\s]?max\b|\bdmax\b|n[-\s]?series|grafter)", text))

    isuzu = [o for o in ops if names_isuzu(o)]
    soon = []
    for o in ops:
        dl = o.get("deadline_date")
        if not dl:
            continue
        try:
            dd = datetime.fromisoformat(str(dl)[:10]).date()
        except ValueError:
            continue
        if 0 <= (dd - TODAY).days <= 7:
            soon.append((dd, o))

    add(f"Feed generated **{gen}Z** · {len(ops)} opportunities · "
        f"{stats.get('attack', '?')} attack · {stats.get('selective', '?')} selective")
    add()
    if isuzu:
        add(f"**{len(isuzu)} opportunity(ies) naming Isuzu:**")
        for o in isuzu[:10]:
            add(f"- {o.get('country')} · {str(o.get('title'))[:110]}")
        alerts.append(f"{len(isuzu)} tender(s) name Isuzu — review.")
    else:
        add("- No opportunity in the feed names Isuzu or D-Max.")
    add()
    if soon:
        add(f"**{len(soon)} deadline(s) inside 7 days:**")
        for dd, o in sorted(soon, key=lambda t: t[0])[:12]:
            add(f"- {dd} ({(dd - TODAY).days}d) · {o.get('decision')} · {o.get('country')} · "
                f"{str(o.get('title'))[:90]}")
    else:
        add("- No deadline inside 7 days.")
    add()
    lu = int(stats.get("lifecycle_unknown") or 0)
    if lu:
        add(f"- {lu} opportunit(ies) with **unknown lifecycle** — notice documents not yet recovered.")
    add()


# --------------------------------------------------------------------------- 5. tasks
def section_tasks() -> None:
    add("## 5. Scheduled tasks")
    add()
    # /v gives Last Result and Next Run Time; parse by header so column order can change.
    out = run(["schtasks", "/query", "/fo", "CSV", "/v"])
    rows: list[dict] = []
    hdr: list[str] | None = None
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = [x.strip().strip('"') for x in re.split(r'","', line.strip().strip('"'))]
        if hdr is None:
            if any("TaskName" in p for p in parts):
                hdr = parts
            continue
        if len(parts) < 3:
            continue
        rec = dict(zip(hdr, parts))
        name = rec.get("TaskName", "")
        if "ISZE" in name:
            rows.append(rec)

    if not rows:
        add("- ISZE tasks not found, or `schtasks` returned nothing.")
        add()
        return

    add("| Task | Next run | Last run | Last result |")
    add("|---|---|---|---|")
    for rec in rows:
        name = rec.get("TaskName", "").lstrip("\\")
        nxt = rec.get("Next Run Time", "")
        last = rec.get("Last Run Time", "")
        res = rec.get("Last Result", "")
        add(f"| {name} | {nxt} | {last} | {res} |")
        if res not in ("0", ""):
            alerts.append(f"Task {name} last result {res} (not success).")
    add()
    add("_A weekly task cannot run while the machine is asleep, and this laptop has no "
        "wake timer. Missed Mondays are the usual symptom._")
    add()


# --------------------------------------------------------------------------- assemble
def build() -> str:
    section_pipeline()
    section_attention()
    section_freshness()
    section_tenders()
    section_tasks()

    if any(a.startswith("Pipeline FAIL") for a in alerts):
        v = "**Something is failing. See section 1.**"
    elif alerts:
        v = f"**{len(alerts)} thing(s) need a look.**"
    else:
        v = "**Nothing needs you today.**"
    globals()["verdict"] = v

    out = [
        f"# ISZE daily brief — {TODAY}",
        "",
        v,
        "",
        f"Generated {NOW:%Y-%m-%d %H:%M}Z by `isze_daily_check.py`. Read-only digest of "
        "reports that already exist; it computes nothing new and changes nothing.",
        "",
    ]
    if alerts:
        out.append("Checklist for you:")
        out.append("")
        for i, a in enumerate(alerts, 1):
            out.append(f"{i}. {a}")
        out.append("")
    out.extend(lines)
    return "\n".join(out) + "\n"


def draft(text: str) -> str:
    """Save an Outlook draft to Jerome. Never sends."""
    try:
        import win32com.client  # noqa: F401
    except Exception:
        return "skipped: pywin32 not available"
    try:
        import win32com.client as w
        ol = w.Dispatch("Outlook.Application")
        ns = ol.GetNamespace("MAPI")
        subject = f"ISZE daily brief {TODAY}"
        # remove a previous draft with the same subject so only one sits there
        try:
            drafts = ns.GetDefaultFolder(16).Items
            for i in range(drafts.Count, 0, -1):
                it = drafts.Item(i)
                try:
                    if str(it.Subject or "").strip() == subject:
                        it.Delete()
                except Exception:
                    continue
        except Exception:
            pass
        mail = ol.CreateItem(0)
        mail.To = DRAFT_TO
        mail.Subject = subject
        mail.Body = text
        mail.BodyFormat = 1  # plain text
        # Draft only. There is deliberately no Send() call anywhere in this file.
        mail.Save()
        return f"draft saved (NOT sent) to {DRAFT_TO}"
    except Exception as exc:
        return f"draft failed: {exc}"


def toast(title: str, message: str) -> str:
    """Fire a Windows toast. No auth, no modules, no network."""
    try:
        from winrt.windows.ui.notifications import (
            ToastNotificationManager, ToastTemplateType, ToastNotification,
        )
        from winrt.windows.data.xml.dom import XmlDocument
    except Exception:
        # fall back to the PowerShell path, which uses the same WinRT API
        try:
            ps = (
                "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
                "ContentType=WindowsRuntime]|Out-Null;"
                "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
                "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
                "$n=$t.GetElementsByTagName('text');"
                f"$n.Item(0).AppendChild($t.CreateTextNode({title!r}))|Out-Null;"
                f"$n.Item(1).AppendChild($t.CreateTextNode({message!r}))|Out-Null;"
                "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('ISZE')"
                ".Show([Windows.UI.Notifications.ToastNotification]::new($t))"
            )
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                               capture_output=True, text=True, timeout=30)
            return "toast sent" if r.returncode == 0 else f"toast failed: {r.stderr[:120]}"
        except Exception as exc:
            return f"toast unavailable: {exc}"
    try:
        xml = ToastNotificationManager.get_template_content(ToastTemplateType.TOAST_TEXT02)
        texts = xml.get_elements_by_tag_name("text")
        texts.item(0).append_child(xml.create_text_node(title))
        texts.item(1).append_child(xml.create_text_node(message))
        ToastNotificationManager.create_toast_notifier("ISZE").show(ToastNotification(xml))
        return "toast sent"
    except Exception as exc:
        return f"toast failed: {exc}"


def main() -> int:
    ap = argparse.ArgumentParser(description="ISZE daily brief")
    ap.add_argument("--draft", action="store_true",
                    help="also save an Outlook draft (needs Outlook signed in; 2FA makes this unreliable)")
    ap.add_argument("--toast", action="store_true", help="also fire a Windows toast")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    text = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(text, encoding="utf-8")
    # keep a stable "latest" copy so any consumer can watch one path
    latest = OUT_DIR / "daily_brief_LATEST.md"
    latest.write_text(text, encoding="utf-8")

    toast_status = "not requested"
    if args.toast:
        headline = f"{len(alerts)} item(s) need you" if alerts else "nothing needs you"
        toast_status = toast(f"ISZE daily brief {TODAY}", headline)

    draft_status = "not requested"
    if args.draft:
        draft_status = draft(text)

    if not args.quiet:
        print(f"verdict      : {verdict}")
        print(f"alerts       : {len(alerts)}")
        for a in alerts:
            print(f"   - {a}")
        print(f"brief        : {OUT_FILE}")
        print(f"latest       : {latest}")
        print(f"toast        : {toast_status}")
        print(f"outlook      : {draft_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
