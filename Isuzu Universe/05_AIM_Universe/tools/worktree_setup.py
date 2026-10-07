"""U28 task 4 - set up a fresh worktree so the baseline checks can actually run.

The problem this solves
-----------------------
BASE-ENGINE and BASE-BROWSER run the supplied review against the frozen v03
reference and the review pack in `06_Working/AIM_v03_HANDOFF_20260922`. A git
worktree does not carry the ignored folders - `payload/`, `reference/` and
`06_Working/` are all outside version control - so in a fresh worktree those two
checks printed NOT RUN instead of running. That is an incomplete run being read
as a clean one, which is the fault BASE-05 exists to expose.

What it copies
--------------
From the main clone, into the worktree, exactly the folders the checks need:

    Isuzu Universe/05_AIM_Universe/payload/
    Isuzu Universe/05_AIM_Universe/reference/
    Isuzu Universe/06_Working/AIM_v03_HANDOFF_20260922/

Every file is copied and every file's SHA-256 is compared with the source. The
count is printed, and a mismatch stops the script rather than leaving a
half-copied worktree that looks ready.

What it deliberately does NOT do
--------------------------------
It does not open the frozen v03 file beyond hashing it, does not read or print
the restricted payload, and does not touch the main clone's working tree. It only
reads from the main clone and writes into the worktree.

Usage
-----
    python tools/worktree_setup.py --from C:\\Users\\jerom\\Desktop\\claude\\ISZE
    python tools/worktree_setup.py --from <main clone> --check

    --check does not copy; it reports what is present and what is missing, and
    exits non-zero when a required folder is absent.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # .../Isuzu Universe/05_AIM_Universe

# (relative to the main clone's `Isuzu Universe`, relative to the worktree's
#  `Isuzu Universe`). The third element is what the checks need it for.
FOLDERS = [
    ("05_AIM_Universe/payload", "05_AIM_Universe/payload",
     "the authorised local payload the INTERNAL build and several tests read"),
    ("05_AIM_Universe/reference", "05_AIM_Universe/reference",
     "the frozen v03 reference BASE-ENGINE and BASE-BROWSER run against"),
    ("06_Working/AIM_v03_HANDOFF_20260922", "06_Working/AIM_v03_HANDOFF_20260922",
     "the supplied review pack the two baseline checks execute"),
]

# The frozen reference. Hashed, never opened beyond that.
FROZEN = "05_AIM_Universe/reference/ISZE_AIM_Pricing_Decisions_v03_FROZEN.html"
FROZEN_SHA256 = "7494cea1955be820d0082eef15473610945663fbefc7a06d7969c15822423e14"

TREES = Path("Isuzu Universe")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def files_under(base: Path):
    if not base.exists():
        return []
    out = []
    for current, _dirs, names in os.walk(base):
        for name in names:
            out.append(Path(current) / name)
    return sorted(out)


def report(main: Path, worktree: Path, do_copy: bool) -> int:
    main_tree = main / TREES
    work_tree = worktree / TREES
    if not main_tree.exists():
        print("STOP: the main clone has no 'Isuzu Universe' folder: " + str(main_tree))
        return 2

    matched = copied = 0
    problems = []
    missing_sources = []

    for src_rel, dst_rel, why in FOLDERS:
        src = main_tree / src_rel
        dst = work_tree / dst_rel
        if not src.exists():
            missing_sources.append((src_rel, why))
            continue
        src_files = files_under(src)
        if do_copy:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        for f in src_files:
            rel = f.relative_to(src)
            target = dst / rel
            if not target.exists():
                problems.append("MISSING in worktree: %s" % (dst_rel / rel))
                continue
            if sha256_of(f) == sha256_of(target):
                matched += 1
            else:
                problems.append("HASH MISMATCH: %s" % (dst_rel / rel))
        copied += 0 if not do_copy else len(src_files)
        print("%-46s %3d file(s) %s" % (src_rel, len(src_files),
                                        "copied" if do_copy else "checked"))

    frozen_src = main_tree / FROZEN
    if frozen_src.exists():
        got = sha256_of(frozen_src)
        if got != FROZEN_SHA256:
            problems.append("the frozen v03 reference in the main clone does not match the recorded "
                            "checksum: %s" % got)
        else:
            print("%-46s %s" % ("frozen v03 reference", "checksum matches"))

    print("")
    for rel, why in missing_sources:
        print("ABSENT IN THE MAIN CLONE: %s  (%s)" % (rel, why))
    for p in problems:
        print("  " + p)
    print("matched %d file(s)%s" % (matched, ", copied %d" % copied if do_copy else ""))

    if missing_sources:
        print("RESULT: BLOCKED - the main clone does not carry %d required folder(s), so the two "
              "baseline checks cannot run in this worktree." % len(missing_sources))
        return 3
    if problems:
        print("RESULT: INCOMPLETE - %d file(s) the checks need are not in this worktree. Run the "
              "same command without --check to copy them." % len(problems))
        return 1
    print("RESULT: OK - the worktree can run BASE-ENGINE and BASE-BROWSER instead of printing NOT RUN.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="main", required=True,
                    help="the main clone that carries the ignored folders")
    ap.add_argument("--worktree", default=str(ROOT.parent.parent),
                    help="the worktree to prepare (default: the one this file is in)")
    ap.add_argument("--check", action="store_true",
                    help="report only; copy nothing")
    args = ap.parse_args()
    return report(Path(args.main).resolve(), Path(args.worktree).resolve(), not args.check)


if __name__ == "__main__":
    sys.exit(main())
