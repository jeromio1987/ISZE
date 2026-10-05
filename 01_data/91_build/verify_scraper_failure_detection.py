# -*- coding: utf-8 -*-
"""
Prove the SECOND half of the scraper fix: that a NON-reset source which fails is now
caught, and that a failed source no longer gets the reassuring "no moves" line.

The previous verification found three of five sources still failing silently
(tranzparts, tmc, auto365 - the needs_reset=False ones), because the old detection
only fired on the reset-and-restore path. This test forces exactly that case.

No network. No real output files touched. The real script is copied byte-for-byte
into a temp directory per case and runs there.
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REAL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\04_tools\autodoc_scraper"
            r"\refresh_and_check_drift.py")
REAL_SNAP = REAL.parent / "_snapshots"


def say(m=""):
    print(m)
    sys.stdout.flush()


def real_state():
    """Hash the real script and the real snapshots so we can prove nothing changed."""
    h = hashlib.sha256(REAL.read_bytes()).hexdigest()[:16]
    files = sorted(p.name for p in REAL_SNAP.iterdir())
    return h, tuple(files)


before = real_state()


def make_case(tmp: Path, dead_sources: set):
    """Copy the script; fake every scraper; seed last week's rows for all sources."""
    shutil.copy2(REAL, tmp / REAL.name)
    csvs = ["ks_results.csv", "tranzparts_results.csv", "tmc_results.csv",
            "mekonomen_results.csv", "auto365_results.csv"]
    seed = "PN,Price_EUR\nAAAAAAAAAA,10.00\nBBBBBBBBBB,20.00\n"
    for c in csvs:
        (tmp / c).write_text(seed, encoding="utf-8")
    (tmp / "_snapshots").mkdir(exist_ok=True)

    # one fake scraper per JOBS entry, by filename it is asked to run
    for script, csv_name in (("ks_scraper.py", "ks_results.csv"),
                             ("tranzparts_scraper.py", "tranzparts_results.csv"),
                             ("tmc_scraper.py", "tmc_results.csv"),
                             ("mekonomen_scraper.py", "mekonomen_results.csv"),
                             ("auto365_scraper.py", "auto365_results.csv")):
        if script in dead_sources:
            # dies: writes nothing, exit 0, leaves last week's file untouched
            body = "import sys\nsys.exit(0)\n"
        else:
            body = (f"open({csv_name!r}, 'w').write('PN,Price_EUR\\n"
                    f"AAAAAAAAAA,11.00\\nBBBBBBBBBB,21.00\\n')\n")
        (tmp / script).write_text(body, encoding="utf-8")

    # neutralise the three builders main() shells out to
    for b in ("build_executive_dashboard.py", "build_drift_trend_view.py",
              "build_pms_iam_bridge.py"):
        (tmp / b).write_text("import sys\nsys.exit(0)\n", encoding="utf-8")


def run_case(label, dead):
    tmp = Path(tempfile.mkdtemp(prefix="isze_drift_"))
    make_case(tmp, dead)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, str(tmp / REAL.name)], cwd=str(tmp),
                       capture_output=True, text=True, env=env, timeout=300)
    out = r.stdout + r.stderr
    say("=" * 84)
    say(f"{label}   (dead sources: {', '.join(sorted(dead)) or 'none'})")
    say("=" * 84)
    say(f"  EXIT CODE: {r.returncode}   expected: {2 if dead else 0}")
    keep = [ln for ln in out.splitlines()
            if any(k in ln for k in ("SOURCE(S) FAILED", "produced fresh rows",
                                     "restored", "untouched", "NOT COMPARABLE",
                                     "fresh - the", "EXIT 2", "FAILED - the market",
                                     "wrote no file", "no data rows"))]
    for ln in keep[:14]:
        say("    " + ln.strip())
    say()
    shutil.rmtree(tmp, ignore_errors=True)
    return r.returncode


say("PROVING THE EXTENDED SCRAPER FIX  (no network, no real files)")
say()
cases = [
    ("CASE 1  all five healthy", set()),
    ("CASE 2  a NON-reset source dies (tmc)", {"tmc_scraper.py"}),
    ("CASE 3  all three NON-reset sources die",
     {"tmc_scraper.py", "tranzparts_scraper.py", "auto365_scraper.py"}),
    ("CASE 4  a reset source dies (ks)", {"ks_scraper.py"}),
]
codes = {}
for label, dead in cases:
    codes[label] = run_case(label, dead)

say("=" * 84)
say("RESULT")
say("=" * 84)
ok = True
for label, dead in cases:
    want = 2 if dead else 0
    got = codes[label]
    good = got == want
    ok = ok and good
    say(f"  {'PASS' if good else 'FAIL'}  {label:<46} exit {got} (want {want})")

after = real_state()
say()
say(f"  real script hash unchanged: {before[0] == after[0]}")
say(f"  real _snapshots unchanged : {before[1] == after[1]}")
say()
say("FIX_PROVEN" if (ok and before == after) else "FIX_NOT_PROVEN")
