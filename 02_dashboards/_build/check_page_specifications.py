"""Compare a page against the standing specifications Jerome has already given.

Root cause R2 in the ISZE agent error register (18-19 Sep 2026): his instructions
live in rule files scoped to one folder, so the session that repeats the mistake
never loads them. The specifications are listed once, in machine-readable form, in

    04_tools/workspace/page_specifications.json

and this is the check that reads them. Every row in that file cites where the
specification comes from, so a row can always be argued with.

READ THIS BEFORE TRUSTING A RESULT
Four of the checks below are text searches over the built HTML. A text search
cannot tell a real defect from a legitimate sentence - a page that explains the
rule ("a pickup is not a truck", "the band is on the weighted base-price index")
contains the same words as a page that breaks it. So:

  FAIL   is only returned where the test is falsifiable without judgement:
         a number outside the sourced set, or the one named mislabel.
  REPORT is returned everywhere a human has to read the sentence. It is printed
         with the matched text so the read takes seconds, but it never fails a
         build, because a guard that fires on a legitimate sentence is worse than
         no guard - Jerome cannot get past it.

Each specification's check may carry a "manual_review" note. Those are printed
verbatim so the reader knows exactly what the tool could not decide.

USAGE
  python check_page_specifications.py --path 02_dashboards/sales/ISZE_PMS_Tonnage_Evolution.html
  python check_page_specifications.py --dir 02_dashboards/sales --dir 02_dashboards/pricing
  python check_page_specifications.py --dir 02_dashboards/sales --gate
      --gate exits 1 only on a FAIL, never on a REPORT.
"""
from __future__ import annotations

import argparse
import html as htmlmod
import json
import re
import sys
from pathlib import Path

# The search runs over the stripped visible text AND the raw file, because a page
# often builds its wording in JavaScript and a sentence assembled there is still
# on the page. The raw half is marked so a hit reported from it is not presented
# as reader-facing prose.
RAW_MARKER = "\n<!--RAW SOURCE-->\n"

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SPEC_FILE = ROOT / "04_tools" / "workspace" / "page_specifications.json"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

# Folders that hold scratch copies rather than deliverables.
SKIP_DIR_PARTS = {"_qa", "_build", "_working", "_archive", "90_archive", "_audit", "Data"}


def visible_text(path: Path) -> tuple[str, list[str]]:
    """Return (searchable text, notes). Script and style are stripped from the
    visible half; the raw file follows after a marker. Duplicates across the two
    halves are collapsed by each checker's seen-set."""
    notes: list[str] = []
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = htmlmod.unescape(text)
    text = " ".join(text.split())
    if not text.strip():
        notes.append("no visible text found after stripping script and style")
    return text + RAW_MARKER + raw, notes


def near(text: str, start: int, end: int, pad: int = 70) -> str:
    s = max(0, start - pad)
    e = min(len(text), end + pad)
    snippet = " ".join(text[s:e].split())
    if RAW_MARKER.strip() in snippet or "<!--RAW SOURCE-->" in snippet:
        return "(from the page source, built in script) " + snippet.replace("<!--RAW SOURCE-->", "")
    if start > text.find("<!--RAW SOURCE-->"):
        return "(from the page source) " + snippet
    return snippet


# --------------------------------------------------------------------------- #
# Check types
# --------------------------------------------------------------------------- #

def check_numeric_vocabulary(spec: dict, text: str) -> list[dict]:
    """A measure printed beside a subject must be one of the sourced values.

    The window is deliberately small. A first version read a measure from
    anywhere in the following 400 characters, which is wide enough to pick up a
    number from the next table cell and fail a legitimate page.
    """
    c = spec["check"]
    subject = re.compile(c["subject_pattern"])
    measure = re.compile(c["measure_pattern"])
    allowed = {int(v) for v in c["allowed_values"]}
    window_chars = int(c.get("window_chars", 120))
    out = []
    seen = set()
    for s in subject.finditer(text):
        window = text[s.start(): s.start() + window_chars]
        for m in measure.finditer(window):
            raw = m.group(1).replace(",", "").replace(".", "")
            try:
                value = int(raw)
            except ValueError:
                continue
            # A figure of 200000 written as 200.000 parses to 200000; a figure of
            # 50,000 parses the same way. Small numbers (a share, a count) are not
            # what this row is about, so ignore anything under 1,000.
            if value < 1000:
                continue
            if value not in allowed:
                snippet = near(text, s.start(), s.start() + window_chars)
                key = (spec["id"], value)
                if key in seen:
                    continue
                seen.add(key)
                out.append({
                    "status": "FAIL",
                    "line": snippet,
                    "message": c["message"],
                    "detail": f"found {value:,} against allowed {sorted(allowed)}",
                })
    return out


def check_basis_cooccurrence(spec: dict, text: str) -> list[dict]:
    """A trigger phrase must appear with its basis named somewhere on the page."""
    c = spec["check"]
    trigger = re.compile(c["trigger_pattern"])
    if not trigger.search(text):
        return []
    out = []
    forbidden = c.get("forbidden_pattern")
    if forbidden and re.search(forbidden, text):
        m = re.search(forbidden, text)
        out.append({
            "status": "FAIL",
            "line": near(text, m.start(), m.end()),
            "message": c["forbidden_message"],
            "detail": "matched the forbidden form",
        })
    basis = any(re.search(b, text) for b in c.get("basis_patterns", []))
    if not basis:
        m = trigger.search(text)
        out.append({
            "status": "REPORT",
            "line": near(text, m.start(), m.end()),
            "message": c["message"],
            "detail": "no basis phrase found on the page",
        })
    return out


def check_phrase_guard(spec: dict, text: str) -> list[dict]:
    """A pattern that must not appear. FAIL only where the guard declares itself
    falsifiable, and never on a sentence that is explaining the rule."""
    c = spec["check"]
    out = []
    seen = set()
    fail_patterns = c.get("fail_patterns", [])
    for rule in c.get("must_not_contain", []):
        for m in re.finditer(rule["pattern"], text):
            sentence = near(text, m.start(), m.end(), pad=110)
            # A sentence that explains the rule is not a violation of it.
            explanatory = re.search(
                r"(?i)\bnot a truck\b|\bis a pickup\b|not the same|never averaged|"
                r"must not be|forbidden|instead of|is not a\b", sentence)
            key = (spec["id"], rule["message"])
            if key in seen:
                continue
            seen.add(key)
            status = "FAIL" if (rule["pattern"] in fail_patterns and not explanatory) else "REPORT"
            out.append({
                "status": status,
                "line": sentence,
                "message": rule["message"],
                "detail": "explanatory sentence, not a breach" if explanatory else "matched",
            })
    return out


def check_manual(spec: dict, text: str) -> list[dict]:
    """Nothing is asserted. The rule and what a person must read are printed."""
    return [{
        "status": "REPORT",
        "line": "(no automatic test for this specification)",
        "message": spec["statement"],
        "detail": spec["check"].get("manual_review", "Read the page against the statement above."),
    }]


CHECKERS = {
    "numeric_vocabulary": check_numeric_vocabulary,
    "basis_cooccurrence": check_basis_cooccurrence,
    "phrase_guard": check_phrase_guard,
    "manual": check_manual,
}


def collect_pages(args) -> list[Path]:
    pages: list[Path] = []
    for p in args.path:
        pages.append(Path(p) if Path(p).is_absolute() else (ROOT / p))
    for d in args.dir:
        base = Path(d) if Path(d).is_absolute() else (ROOT / d)
        if not base.exists():
            print(f"  (no such folder, skipped: {base})")
            continue
        for f in sorted(base.glob("*.html")):
            if f.name.startswith("_"):
                continue
            pages.append(f)
    seen, out = set(), []
    for p in pages:
        rp = str(p.resolve())
        if rp in seen:
            continue
        seen.add(rp)
        out.append(p.resolve())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--path", action="append", default=[])
    ap.add_argument("--dir", action="append", default=[])
    ap.add_argument("--spec", default=str(SPEC_FILE))
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if any FAIL is found; REPORTs never fail the run")
    ap.add_argument("--show-reports", action="store_true",
                    help="print every REPORT, not only the FAILs")
    args = ap.parse_args()

    if not args.path and not args.dir:
        ap.error("give --path and/or --dir")

    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    specs = spec["specifications"]
    print(f"check_page_specifications: {len(specs)} specification(s) from {spec_path.name}")

    pages = collect_pages(args)
    fails, reports, checked = [], [], 0

    for page in pages:
        if any(part in SKIP_DIR_PARTS for part in page.parts):
            continue
        checked += 1
        text, notes = visible_text(page)
        try:
            rel = str(page.relative_to(ROOT))
        except ValueError:
            rel = str(page)
        for s in specs:
            applies = Path(rel).match(s["check"].get("applies_to_glob", "*.html"))
            if not applies:
                continue
            fn = CHECKERS.get(s["check"]["type"])
            if fn is None:
                reports.append((rel, s["id"], "REPORT",
                                f"unknown check type '{s['check']['type']}'", ""))
                continue
            for r in fn(s, text):
                target = fails if r["status"] == "FAIL" else reports
                target.append((rel, s["id"], r["status"], r["message"], r["line"]))
        for n in notes:
            reports.append((rel, "(reader)", "REPORT", n, ""))

    print(f"pages checked: {checked}\n")

    print("================ FAIL (a sourced figure or a named mislabel) ================")
    if fails:
        for rel, sid, _st, msg, line in fails:
            print(f"FAIL  {rel}\n      [{sid}] {msg}\n      ...{line}...")
    else:
        print("none")

    if args.show_reports or not fails:
        print("\n================ REPORT (a person must read the sentence) ================")
        if reports:
            for rel, sid, _st, msg, line in reports:
                print(f"REPORT {rel}\n       [{sid}] {msg}\n       ...{line}...")
        else:
            print("none")

    print("\n================ what this check cannot decide ================")
    for s in specs:
        note = s["check"].get("manual_review")
        if note:
            print(f"  [{s['id']}] {note}")
        elif s["check"]["type"] == "manual":
            print(f"  [{s['id']}] no automatic test at all")

    print(f"\nfailures {len(fails)}, reports {len(reports)}, pages {checked}")
    if args.gate and fails:
        print("PAGE_SPECIFICATIONS: FAIL")
        return 1
    print("PAGE_SPECIFICATIONS: DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
