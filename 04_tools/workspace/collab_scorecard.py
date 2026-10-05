"""Weekly Claude / Cursor scorecard -> ISZE\\05_memory\\briefs\\

Three numbers on how the Claude/Cursor split works, from logs that already exist:
  1 Briefs      docs\\cursor_briefs\\ (and _done\\): waiting, with Cursor, reported, checked, first-check verdict
  2 Not landed  git + gh for ISZE, Private, myPENS: open files, PRs, unpushed, behind, extra copies, old branches
  3 Corrections Jerome's corrective messages per 10, per tool, per ISO week (UTC)

Claude Code deletes transcripts after 30 days, so every run appends to scorecard_history.csv.
Never prints message text. Always exits 0.

Usage:
  python collab_scorecard.py [--from 2026-09-06T00:00:00Z] [--to 2026-10-05T18:00:00Z] [--no-write]
Default window: the last full ISO week (UTC).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Same pattern as C:\Users\jerom\.claude\hooks\jvdp-retro.js line 27 (JS \b is ASCII-only, hence re.ASCII).
CORRECTIVE = re.compile(
    r"\b(nee|niet|fout|verkeerd|stop|geen|opnieuw|klopt niet|dat is niet|waarom|wrong|no,|actually|don'?t"
    r"|revert|undo|why (did|are) you|i said|zoals ik zei)\b",
    re.IGNORECASE | re.ASCII,
)

CLAUDE_SKIP_PREFIXES = (
    "<system-reminder>",
    "<command-name>",
    "<local-command",
    "<scheduled-task",
    "<task-notification",
    "<command-message>",
    "Caveat:",
)
CURSOR_SKIP_PREFIXES = (
    "Perform any necessary follow-up actions",
    "Briefly inform the user about the task result",
    "CLAIM-CHECK:",
    "You are the forked subagent",
    "STOP: BRIEF_CHECKLIST",
    "STOP - ",
    "Execute the selected diff-tab",
)
PLAN_CUT = "Implement the plan as specified"
USER_QUERY = re.compile(r"<user_query>(.*?)</user_query>", re.DOTALL)
TIMESTAMP = re.compile(r"<timestamp>(.*?)</timestamp>", re.DOTALL)
CURSOR_TS = re.compile(
    r"^\s*\w+,\s*(\w{3})\w*\s+(\d{1,2}),\s*(\d{4}),\s*(\d{1,2}):(\d{2})\s*([AP]M)\s*\(UTC([+-]\d{1,2})(?::?(\d{2}))?\)"
)
MONTHS = {m: i for i, m in enumerate(("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec").split(), 1)}

DENMARK_CARVE_OUT = (
    "09_meetings/DENMARK_FY2027_BPR/OPEN_Danmark_BPR.cmd",
    "09_meetings/DENMARK_FY2027_BPR/_build/build_dk_bpr.py",
)
VERIFIED = re.compile(r"^#+\s*VERIFIED")
VERDICT = re.compile(r"^Verdict: (LANDED|PARTLY|NOT LANDED)$")
FOLLOW_UP = re.compile(r"^[A-Z]\d+[a-z]$")
BRIEF_NAME = re.compile(r"^20.*_.*\.md$")


# ---------------------------------------------------------------- paths


def git(args: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def resolve_roots() -> tuple[Path, Path]:
    """I = parent of the shared git dir (so a worktree resolves to the main clone), W = I's parent."""
    r = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], HERE)
    common = Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else HERE.parents[1] / ".git"
    isze = common.resolve().parent
    return isze, isze.parent


# ---------------------------------------------------------------- time


def parse_iso(s: str) -> datetime:
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def week_start(d: datetime) -> datetime:
    d = d.astimezone(timezone.utc)
    monday = d.date() - timedelta(days=d.weekday())
    return datetime(monday.year, monday.month, monday.day, tzinfo=timezone.utc)


def week_key(d: datetime) -> str:
    y, w, _ = d.astimezone(timezone.utc).isocalendar()
    return f"{y}-W{w:02d}"


def parse_cursor_ts(s: str) -> datetime | None:
    m = CURSOR_TS.match(s)
    if not m:
        return None
    mon, day, year, hh, mm, ampm, off_h, off_m = m.groups()
    if mon[:3].title() not in MONTHS:
        return None
    hour = int(hh) % 12 + (12 if ampm.upper() == "PM" else 0)
    sign = -1 if off_h.startswith("-") else 1
    offset = timedelta(hours=abs(int(off_h)), minutes=int(off_m or 0)) * sign
    local = datetime(int(year), MONTHS[mon[:3].title()], int(day), hour, int(mm), tzinfo=timezone(offset))
    return local.astimezone(timezone.utc)


# ---------------------------------------------------------------- M3 corrections


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return " ".join(b.get("text") or "" for b in content if isinstance(b, dict) and b.get("type") == "text")


def iter_jsonl(path: Path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except ValueError:
                    continue
    except OSError:
        return


def claude_messages(scan_start: datetime):
    """(utc time, text) for every counted Jerome message in Claude Code transcripts."""
    root = Path.home() / ".claude" / "projects"
    if not root.is_dir():
        return None
    out = []
    for path in root.glob("*/*.jsonl"):
        if "AppData-Local-Temp" in str(path):
            continue
        try:
            if datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) < scan_start:
                continue
        except OSError:
            continue
        for rec in iter_jsonl(path):
            if rec.get("type") != "user":
                continue
            msg = rec.get("message")
            if not isinstance(msg, dict) or msg.get("role") != "user":
                continue
            if rec.get("entrypoint") not in ("claude-desktop", "cli"):
                continue
            if rec.get("isMeta") or rec.get("isSidechain"):
                continue
            text = text_of(msg.get("content")).strip()
            if not text or text.startswith(CLAUDE_SKIP_PREFIXES) or "[Request interrupted by user" in text:
                continue
            ts = rec.get("timestamp")
            if not ts:
                continue
            try:
                out.append((parse_iso(ts), text))
            except ValueError:
                continue
    return out


def cursor_messages(scan_start: datetime):
    """(utc time, text) for every counted Jerome message in Cursor agent transcripts."""
    root = Path.home() / ".cursor" / "projects"
    if not root.is_dir():
        return None
    out = []
    for path in root.glob("*/agent-transcripts/**/*.jsonl"):
        if "subagents" in path.parts:
            continue
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        except OSError:
            continue
        if mtime < scan_start:
            continue
        for rec in iter_jsonl(path):
            if rec.get("role") != "user":
                continue
            msg = rec.get("message")
            raw = text_of(msg.get("content")) if isinstance(msg, dict) else ""
            m = USER_QUERY.search(raw)
            if not m:
                continue
            text = m.group(1).strip()
            if not text or text.startswith(CURSOR_SKIP_PREFIXES):
                continue
            if PLAN_CUT in text:
                text = text[: text.index(PLAN_CUT)].strip() or "Implement the plan"
            ts_m = TIMESTAMP.search(raw)
            when = parse_cursor_ts(ts_m.group(1)) if ts_m else None
            out.append((when or mtime, text))
    return out


def is_correction(text: str) -> bool:
    return len(text) < 600 and bool(CORRECTIVE.search(text))


def tally(messages, start: datetime, end: datetime) -> tuple[int, int]:
    n = hits = 0
    for when, text in messages:
        if start <= when < end:
            n += 1
            hits += is_correction(text)
    return n, hits


def per10(n: int, hits: int) -> str:
    return f"{hits * 10 / n:.1f}" if n else "-"


# ---------------------------------------------------------------- M1 briefs


def brief_counts(work: Path, today: date):
    folder = work / "docs" / "cursor_briefs"
    if not folder.is_dir():
        return None
    folders = [folder, folder / "_done"]
    c = dict(written=0, waiting=0, oldest=None, with_cursor=0, reported=0, checked=0,
             landed=0, partly=0, not_landed=0, no_verdict=0, follow_ups=0)
    for f in folders:
        if not f.is_dir():
            continue
        for p in sorted(f.iterdir()):
            if not p.is_file() or not BRIEF_NAME.match(p.name) or p.name.endswith("_REPORT.md"):
                continue
            parts = p.stem.split("_")
            if len(parts) < 2:
                continue
            c["written"] += 1
            if FOLLOW_UP.match(parts[1]):
                c["follow_ups"] += 1
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            status = next((ln[len("Status:"):].strip() for ln in lines if ln.startswith("Status:")), "")
            report = next((d / f"{p.stem}_REPORT.md" for d in folders if (d / f"{p.stem}_REPORT.md").is_file()), None)
            if "WAITING FOR GO" in status:
                c["waiting"] += 1
                try:
                    age = (today - date.fromisoformat(parts[0])).days
                    c["oldest"] = age if c["oldest"] is None else max(c["oldest"], age)
                except ValueError:
                    pass
            if report is None:
                if status.startswith("GO"):
                    c["with_cursor"] += 1
                continue
            rlines = report.read_text(encoding="utf-8", errors="replace").splitlines()
            first = next((i for i, ln in enumerate(rlines) if VERIFIED.match(ln)), None)
            if first is None:
                c["reported"] += 1
                continue
            c["checked"] += 1
            verdict = next((VERDICT.match(ln).group(1) for ln in rlines[first + 1:] if VERDICT.match(ln)), None)
            key = {"LANDED": "landed", "PARTLY": "partly", "NOT LANDED": "not_landed"}.get(verdict, "no_verdict")
            c[key] += 1
    return c


# ---------------------------------------------------------------- M2 not landed


def porcelain_paths(repo: Path) -> list[str] | None:
    r = git(["status", "--porcelain", "-z"], repo)
    if r.returncode != 0:
        return None
    fields = r.stdout.split("\0")
    paths, i = [], 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if entry[0] in "RC" or entry[1] in "RC":
            i += 1  # rename/copy: the next field is the original path
    return paths


def count_lines(r: subprocess.CompletedProcess) -> int | None:
    return len([ln for ln in r.stdout.splitlines() if ln.strip()]) if r.returncode == 0 else None


def int_out(r: subprocess.CompletedProcess) -> int | None:
    try:
        return int(r.stdout.strip()) if r.returncode == 0 else None
    except ValueError:
        return None


def repo_state(name: str, repo: Path, carve_out: tuple[str, ...]) -> dict:
    s: dict = {"name": name, "ok": repo.is_dir() and (repo / ".git").exists()}
    if not s["ok"]:
        return s
    try:
        s["fetch_failed"] = git(["fetch", "--quiet", "origin"], repo, timeout=180).returncode != 0
    except subprocess.TimeoutExpired:
        s["fetch_failed"] = True
    paths = porcelain_paths(repo)
    if paths is None:
        s["ok"] = False
        return s
    paths = [p for p in paths if p.rstrip("/") not in carve_out]
    s["open"] = len(paths)
    cutoff = datetime.now().timestamp() - 3 * 86400
    stale = 0
    for p in paths:
        try:
            if (repo / p).stat().st_mtime < cutoff:
                stale += 1
        except OSError:
            pass
    s["stale"] = stale
    s["unpushed"] = int_out(git(["rev-list", "--count", "--branches", "--not", "--remotes", "--tags"], repo))
    s["behind"] = int_out(git(["rev-list", "--count", "HEAD..@{u}"], repo))
    wt = count_lines(git(["worktree", "list"], repo))
    s["copies"] = None if wt is None else max(wt - 1, 0)
    s["stashes"] = count_lines(git(["stash", "list"], repo))
    r = git(["for-each-ref", "--no-merged", "origin/main", "--format=%(refname) %(committerdate:unix)",
             "refs/remotes/origin"], repo)
    if r.returncode == 0:
        old_cut = datetime.now().timestamp() - 14 * 86400
        old = 0
        for ln in r.stdout.splitlines():
            ref, _, ts = ln.rpartition(" ")
            if not ref or ref == "refs/remotes/origin/HEAD":
                continue
            try:
                old += int(ts) < old_cut
            except ValueError:
                pass
        s["old_branches"] = old
    else:
        s["old_branches"] = None
    return s


def pr_state(repo_slug: str) -> tuple[int, int | None] | None:
    try:
        r = subprocess.run(
            ["gh", "pr", "list", "--repo", repo_slug, "--state", "open", "--json", "number,createdAt"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        prs = json.loads(r.stdout or "[]")
    except ValueError:
        return None
    now = datetime.now(timezone.utc)
    ages = [(now - parse_iso(p["createdAt"])).days for p in prs if p.get("createdAt")]
    return len(prs), (max(ages) if ages else None)


def reading_set(work: Path) -> str:
    script = work / "docs" / "check_reading_set.py"
    if not script.is_file():
        return "check_reading_set.py: not available"
    try:
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300, cwd=str(work))
    except (OSError, subprocess.TimeoutExpired):
        return "check_reading_set.py: not available"
    line = next((ln.strip() for ln in reversed(r.stdout.splitlines()) if ln.strip().startswith("RESULT")), None)
    return line or "check_reading_set.py: no RESULT line"


# ---------------------------------------------------------------- output


def fmt(v) -> str:
    return "?" if v is None else str(v)


def day_label(d: datetime) -> str:
    return f"{d:%a} {d.day} {d:%b}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="start")
    ap.add_argument("--to", dest="end")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    isze, work = resolve_roots()
    now_utc = datetime.now(timezone.utc)
    end = parse_iso(args.end) if args.end else week_start(now_utc)
    start = parse_iso(args.start) if args.start else week_start(end - timedelta(seconds=1))

    # The 4 full ISO weeks before --to; the last one is "this week" on the scorecard.
    last_full_end = week_start(end)
    weeks = [last_full_end - timedelta(days=7 * k) for k in (4, 3, 2, 1)]
    this_week = weeks[-1]
    scan_start = min(start, weeks[0])

    claude = claude_messages(scan_start)
    cursor = cursor_messages(scan_start)

    lines: list[str] = []
    wk_no = this_week.isocalendar()[1]
    lines.append(
        f"Claude / Cursor scorecard - week {wk_no} ({day_label(this_week)} to "
        f"{day_label(this_week + timedelta(days=6))}), computed {datetime.now():%Y-%m-%d %H:%M}"
    )

    history: list[tuple[str, str, str, str]] = []
    wk = week_key(this_week)

    # 1 Briefs
    b = brief_counts(work, date.today())
    if b is None:
        lines.append("1 Briefs: docs\\cursor_briefs: not available")
    else:
        lines.append(
            f"1 Briefs: {b['written']} written, {b['waiting']} waiting for your go (oldest {fmt(b['oldest'])} days), "
            f"{b['with_cursor']} with Cursor, {b['reported']} reported, {b['checked']} checked."
        )
        lines.append(
            f"  First check: {b['landed']} landed, {b['partly']} partly, {b['not_landed']} not landed, "
            f"{b['no_verdict']} no verdict. Follow-up briefs: {b['follow_ups']}."
        )
        for k, v in b.items():
            if v is not None:
                history.append((wk, f"briefs_{k}", "all", str(v)))

    # 2 Not landed
    repos = [
        ("ISZE", isze, DENMARK_CARVE_OUT, "jeromio1987/ISZE"),
        ("Private", work / "Private", (), "jeromio1987/private"),
        ("myPENS", work / "Projects" / "mypens", (), "jeromio1987/mypens"),
    ]
    states, over, notes = [], [], []
    pr_total, pr_oldest, pr_fail = 0, None, False
    for name, path, carve, slug in repos:
        s = repo_state(name, path, carve)
        states.append(s)
        if not s["ok"]:
            notes.append(f"{name}: not available")
            continue
        if s.get("fetch_failed"):
            notes.append(f"{name}: fetch failed")
        pr = pr_state(slug)
        if pr is None:
            pr_fail = True
        else:
            n, oldest = pr
            pr_total += n
            if oldest is not None:
                pr_oldest = oldest if pr_oldest is None else max(pr_oldest, oldest)
            if oldest is not None and oldest > 7:
                over.append(f"{name}: PR open {oldest} days")
            history += [(wk, "open_prs", name, str(n)), (wk, "oldest_pr_days", name, fmt(oldest))]
        if (s.get("open") or 0) > 25:
            over.append(f"{name}: open ({s['open']})")
        for key, label in (("stale", "stale"), ("unpushed", "unpushed"), ("behind", "behind"),
                           ("copies", "copies"), ("old_branches", "old branches")):
            if (s.get(key) or 0) > 0:
                over.append(f"{name}: {label} ({s[key]})")
        for key in ("open", "stale", "unpushed", "behind", "copies", "stashes", "old_branches"):
            if s.get(key) is not None:
                history.append((wk, key, name, str(s[key])))
    open_txt = {s["name"]: (fmt(s.get("open")) if s["ok"] else "not available") for s in states}
    pr_txt = "PRs: not available" if pr_fail and pr_total == 0 else f"Open PRs {pr_total} (oldest {fmt(pr_oldest)} days)"
    if pr_fail and pr_total:
        pr_txt += " (some repos: PRs: not available)"
    lines.append(f"2 Not landed: ISZE {open_txt['ISZE']} open, Private {open_txt['Private']}, "
                 f"myPENS {open_txt['myPENS']}. {pr_txt}.")
    lines.append(f"  Over the line: {'; '.join(over) or 'nothing'}. Reading set: {reading_set(work)}.")
    if notes:
        lines.append(f"  {'; '.join(notes)}.")

    # 3 Corrections
    def week_vals(msgs, w):
        return tally(msgs, w, w + timedelta(days=7)) if msgs is not None else None

    tools = (("Claude", "claude", claude), ("Cursor", "cursor", cursor))
    this = {}
    for label, scope, msgs in tools:
        if msgs is None:
            this[label] = None
            continue
        for w in weeks:
            n, h = week_vals(msgs, w)
            history += [(week_key(w), "messages", scope, str(n)), (week_key(w), "corrections", scope, str(h)),
                        (week_key(w), "corrections_per10", scope, per10(n, h))]
        this[label] = week_vals(msgs, this_week)

    def now_txt(label):
        v = this[label]
        return f"{label}: not available" if v is None else f"{label} {per10(*v)} ({v[0]} msgs)"

    def trend_txt(label, msgs):
        if msgs is None:
            return f"{label}: not available"
        return f"{label} " + " ".join(per10(*week_vals(msgs, w)) for w in weeks)

    lines.append(f"3 Your corrections per 10 messages this week: {now_txt('Claude')}, {now_txt('Cursor')}.")
    lines.append(f"  Last 4 weeks {trend_txt('Claude', claude)}, {trend_txt('Cursor', cursor)}.")
    lines.append("  Word-pattern count: on 5 Oct about 4 in 10 Claude hits and 7 in 10 Cursor hits were real "
                 "corrections. Read the trend.")

    print("\n".join(lines))

    if args.start:
        print()
        print(f"Corrections in the window {start:%Y-%m-%d %H:%M} to {end:%Y-%m-%d %H:%M} UTC (messages / hits):")
        w = week_start(start)
        while w < end:
            lo, hi = max(w, start), min(w + timedelta(days=7), end)
            cells = []
            for label, _, msgs in tools:
                cells.append(f"{label} {'not available' if msgs is None else '%d / %d' % tally(msgs, lo, hi)}")
            print(f"  {week_key(w)}: {', '.join(cells)}")
            w += timedelta(days=7)
        cells = []
        for label, _, msgs in tools:
            if msgs is None:
                cells.append(f"{label} not available")
            else:
                n, h = tally(msgs, start, end)
                cells.append(f"{label} {n} / {h} = {per10(n, h)} per 10")
        print(f"  total: {', '.join(cells)}")

    if not args.no_write:
        out_dir = isze / "05_memory" / "briefs"
        out_dir.mkdir(parents=True, exist_ok=True)
        y, wn, _ = this_week.isocalendar()
        (out_dir / f"scorecard_{y}-W{wn:02d}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        hist = out_dir / "scorecard_history.csv"
        done_weeks = {row[0] for row in history}
        kept = []
        if hist.is_file():
            with open(hist, encoding="utf-8", newline="") as fh:
                kept = [r for r in csv.reader(fh) if r and r[0] != "week" and r[0] not in done_weeks]
        with open(hist, "w", encoding="utf-8", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["week", "measure", "scope", "value"])
            wr.writerows(kept + [list(r) for r in history])
        print(f"\nWrote {out_dir / f'scorecard_{y}-W{wn:02d}.md'} and {hist.name} ({len(history)} rows).")
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # the scheduled task must never fail on a scorecard error
        print(f"scorecard error: {type(exc).__name__}: {exc}")
    sys.exit(0)
