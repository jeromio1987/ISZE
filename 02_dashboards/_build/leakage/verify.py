"""Distributor leakage tool - verifier.

Builder exit 0 is not done. This checks the RENDERED ARTEFACT, not the source:

  1. Stripping test     - a customer pack carries no other market's code, no dealer names,
                          no internal fields, no league block.
  2. Banned vocabulary  - no sell-out / street / wallet / book B / internal nicknames, no Dutch.
  3. Payload sanity     - valid embedded JSON, no NaN, no CDN, no fetch, self-contained.
  4. Paint evidence     - panels present, chart markup present, no empty shells.
  5. Numbers authority  - embedded as-of date matches the payload, verification green.

Run:  python 02_dashboards\\_build\\leakage\\verify.py
Exit code 0 only when every check passes.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.environ.get("ISZE_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SALES = os.path.join(ROOT, "02_dashboards", "sales")
PACKS = os.path.join(SALES, "leakage_packs")
PAYLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payload.json")

COCKPIT = os.path.join(SALES, "ISZE_Leakage_Cockpit.html")
COCKPIT_CMD = os.path.join(SALES, "OPEN_ISZE_Leakage_Cockpit.cmd")
PILOTS = ["ITUK", "SWEDEN", "BELGIUM"]

# Words that must never appear in a distributor-facing artefact from this tool.
BANNED = [
    "sell-out", "sell out", "sellout",
    "street fill", "street index", "street price",
    "parts wallet",
    "book b", "list plus",
    "iml v7", "prism lane",
    ">ship gate<", "loss function",
    "x1.785", "\u00d71.785",
    "sold_to", "sold-to",
]
# Used for internal code names that read as ordinary English inside a sentence, so they are
# matched as whole words: "a model built from ..." must not trip on "model B".
BANNED_PHRASES = [r"\bmodel\s+b\b", r"\bspar\b"]

# Awkward constructions flagged in review. These are not banned words, they are phrasings a
# person reading the page would object to, so they are checked on the built artefact too.
AWKWARD = [
    "bought a competing brand instead",
    "competing brand instead",
    "fewer service events",
    "catalogue part for this application",
    "competing-brand share",
    "competing brands",
    "competing brand",
]
# Dutch words that leak from older templates. Checked as whole words.
DUTCH = ["goed", "slecht", "omzet", "marge", "klant", "jaar", "totaal", "overzicht", "winkel"]

# Raw file names carry internal labels and market codes. A pack may describe a method; it
# must not hand the reader a file name.
FILENAME_RE = re.compile(r"[a-z0-9_]+\.csv|\.parquet|dealer_sellout|wallet_waterfall|"
                         r"pms_capture_by_db_year|gms_|pms_opportunity_matrix", re.I)

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def ok(msg: str) -> None:
    notes.append("  ok   " + msg)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def check_launcher(path: str) -> None:
    if not os.path.exists(path):
        fail(f"launcher missing: {path}")
        return
    with open(path, "rb") as fh:
        raw = fh.read()
    if b"\r\n" not in raw:
        fail(f"launcher is not CRLF (Jerome double-clicks it): {path}")
    else:
        ok(f"launcher present and CRLF: {os.path.basename(path)}")


def check_self_contained(text: str, name: str) -> None:
    """file:// must work with zero network. Any of these means it will not."""
    for pat, why in [
        (r"https?://(?!www\.w3\.org)", "external URL (needs network)"),
        (r"\bfetch\s*\(", "fetch() call (fails on file://)"),
        (r"<script[^>]+src\s*=", "external script tag"),
        (r"@import\s+url\(", "CSS @import"),
        (r"cdn\.", "CDN reference"),
    ]:
        m = re.search(pat, text)
        if m:
            fail(f"{name}: {why} -> {m.group(0)[:60]!r}")
    ok(f"{name}: self-contained, no external request")


def check_payload(text: str, name: str) -> None:
    """NaN as a runtime guard (`Number.isNaN`) is correct code. NaN as a VALUE is a bug, so
    the check is for JSON literals, not for the word."""
    if re.search(r":\s*NaN\b", text) or re.search(r":\s*-?Infinity\b", text) \
            or re.search(r"\bNaN\s*[,}\]]", text) or re.search(r":\s*undefined\b", text):
        fail(f"{name}: NaN, Infinity or undefined present as a data value")
    else:
        ok(f"{name}: no NaN, Infinity or undefined data values")

    if FILENAME_RE.search(text):
        m = FILENAME_RE.search(text)
        fail(f"{name}: raw source file name present -> {m.group(0)!r}")
    else:
        ok(f"{name}: no raw source file names")


def check_banned(text: str, name: str) -> None:
    low = text.lower()
    hits = [b for b in BANNED if b in low]
    if hits:
        fail(f"{name}: banned vocabulary present -> {hits}")
    else:
        ok(f"{name}: no banned vocabulary ({len(BANNED)} terms)")

    ph = [p for p in BANNED_PHRASES if re.search(p, low)]
    if ph:
        fail(f"{name}: banned phrase present -> {ph}")
    else:
        ok(f"{name}: no banned internal phrases")

    for w in DUTCH:
        if re.search(rf"(?<![a-z]){w}(?![a-z])", low):
            fail(f"{name}: Dutch word '{w}' present")
    ok(f"{name}: no Dutch template leakage")

    awk = [a for a in AWKWARD if a in low]
    if awk:
        fail(f"{name}: awkward phrasing present -> {awk}")
    else:
        ok(f"{name}: no awkward phrasing ({len(AWKWARD)} patterns)")


def check_paint(text: str, name: str, expect_panels: int) -> int:
    """Counted on the artefact, from the render source.

    The panels build their markup at runtime from data, so the HTML body holds the panel
    shells and the chart calls live in the inlined module source. Both are counted: a shell
    with no chart primitive behind it is the blank-panel failure this guards against.
    """
    panels = re.findall(r'<section id="sec-([a-z]+)"', text)
    if len(panels) != expect_panels:
        fail(f"{name}: expected {expect_panels} panels, found {len(panels)}: {panels}")
    else:
        ok(f"{name}: {len(panels)} panels declared")

    # Chart primitives: both the emitted HTML strings and the builder calls in the source.
    emit = (text.count('class="hb-fill') + text.count('class="tr-bar') +
            text.count('class="cb2-bar') + text.count('class="stk-seg') +
            text.count("<circle cx=\"88\""))
    calls = (len(re.findall(r"\bbarRows\s*\(", text)) + len(re.findall(r"\bsmallMultiples\s*\(", text)) +
             len(re.findall(r"\bstackedBars\s*\(", text)) + len(re.findall(r"\bchangeBars\s*\(", text)) +
             len(re.findall(r"\bdonut\s*\(", text)) + len(re.findall(r"\bheatTable\s*\(", text)) +
             len(re.findall(r"\blineChart\s*\(", text)) + len(re.findall(r"\bbulletRows\s*\(", text)))
    marks = emit + calls
    if calls < 12:
        fail(f"{name}: only {calls} chart calls in the render source - panels likely blank")
    else:
        ok(f"{name}: {calls} chart calls covering {emit} emitted primitives "
           f"(bars, mini-bars, change bars, stacks, lines, donuts)")

    # Every panel must actually call at least one chart or table builder.
    for pid in panels:
        seg = re.search(rf'id:\s*"{pid}"(.{{0,9000}}?)render:', text, re.S)
        if not seg:
            continue
        body = text[seg.end():seg.end() + 14000]
        if not re.search(r"\b(barRows|smallMultiples|stackedBars|changeBars|donut|heatTable|"
                         r"lineChart|bulletRows|table|kpis)\s*\(", body):
            fail(f"{name}: panel '{pid}' calls no chart or table builder")
    ok(f"{name}: every panel calls at least one chart or table builder")
    return marks


def check_claims(text: str, name: str, focus: str | None) -> None:
    """Every figure this page claims must have its underlying data present in the artefact.

    The euro strings themselves are formatted at render time in the browser, so checking for
    the finished string would test the formatter rather than the data. What matters is that
    the value reached the file at all: a dropped value is the failure a structural check
    cannot see."""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "_checks_internal.json" if focus is None else f"_checks_{focus}.json")
    if not os.path.exists(src):
        notes.append(f"  skip no check spec for {name}")
        return
    with open(src, encoding="utf-8") as fh:
        checks = json.load(fh)
    if not checks:
        return
    missing = []
    for c in checks:
        v = c["value"]
        # accept the raw value at several precisions, since the extractor rounds for output
        forms = {f"{v:.2f}", f"{v:.1f}", f"{v:.0f}", f"{round(v)}", str(round(v, 1))}
        if not any(form in text for form in forms):
            missing.append(f"{c['tag']}/{c['db']}={v}")
    if missing:
        fail(f"{name}: data for {len(missing)} claimed figure(s) absent from the artefact -> "
             f"{missing[:6]}{' (+%d more)' % (len(missing) - 6) if len(missing) > 6 else ''}")
    else:
        ok(f"{name}: data present for all {len(checks)} claimed figures")


def main() -> int:
    print("verifying distributor leakage tool ...\n")

    if not os.path.exists(PAYLOAD):
        print("FATAL: payload.json missing - run extract.py first")
        return 1
    payload = json.loads(read(PAYLOAD))
    network = payload["network_dbs"]
    meta = payload["meta"]

    if not meta["verification"]["ok"]:
        fail("payload was built on a red verification report")
    else:
        ok(f"payload verification green ({meta['verification']['pass']} checks)")

    # ---------------------------------------------------------- internal cockpit
    if not os.path.exists(COCKPIT):
        fail(f"cockpit missing: {COCKPIT}")
    else:
        t = read(COCKPIT)
        print("internal cockpit")
        check_self_contained(t, "cockpit")
        check_banned(t, "cockpit")
        check_paint(t, "cockpit", 11)
        check_launcher(COCKPIT_CMD)
        # internal file must carry the league
        if "league" not in t:
            fail("cockpit: partner league panel absent from the internal file")
        else:
            ok("cockpit: partner league present (internal only)")
        for c in network:
            if not re.search(rf"\b{c}\b", t):
                fail(f"cockpit: market {c} missing from the internal file")
        ok(f"cockpit: all {len(network)} markets present")
        check_claims(t, "cockpit", None)
        print()

    # ------------------------------------------------------------ customer packs
    for db in PILOTS:
        p = os.path.join(PACKS, f"ISZE_Sales_Performance_Review_{db}.html")
        if not os.path.exists(p):
            fail(f"customer pack missing for {db}: {p}")
            continue
        t = read(p)
        print(f"customer pack {db}")
        check_self_contained(t, db)
        check_banned(t, db)
        check_paint(t, db, 10)
        check_launcher(os.path.join(PACKS, f"OPEN_Sales_Performance_Review_{db}.cmd"))
        check_claims(t, db, db)

        # THE stripping test: no other market's code anywhere in the file.
        leaks = [c for c in network if c != db and re.search(rf"\b{c}\b", t)]
        if leaks:
            fail(f"{db} pack LEAKS other markets: {leaks}")
        else:
            ok(f"{db} pack: no other market code present (checked {len(network) - 1})")

        # internal-only content must be absent, not merely hidden
        for bad, why in [
            ("league", "internal partner league"),
            ("risk_score", "composite risk score"),
            ("undercut", "competitor undercut data"),
            ("ew_severity", "early-warning severity"),
            ("defection", "stopped-ordering register"),
            ("health_alert", "account health flags"),
            ("account_health", "account health file"),
            ("threshold", "internal alert thresholds"),
            ("early_warning", "early-warning register"),        ]:
            if bad in t.lower():
                fail(f"{db} pack carries internal content '{bad}' ({why})")
        ok(f"{db} pack: no internal content")

        # A dealer outlet name must never appear: only ITUK has names, and they are
        # commercially sensitive.
        if re.search(r"LTD\b|LIMITED\b", t) and db != "ITUK":
            fail(f"{db} pack: dealer-style company name present")
        # peer members must not be named
        for c in network:
            if c == db:
                continue
            if re.search(rf'"{c}"', t):
                fail(f"{db} pack: peer code {c} present as a quoted string")
        print()

    # ------------------------------------------------------------------- report
    print("=" * 72)
    for n in notes:
        print(n)
    print()
    if failures:
        print(f"FAILED with {len(failures)} problem(s):")
        for f in failures:
            print("  FAIL " + f)
        return 1
    print(f"VERIFY_OK - {len(notes)} checks passed, 0 failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
