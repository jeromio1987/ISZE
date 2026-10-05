"""PR10 conflict resolution.

Policy:
  TAKE_THEIRS  -> git checkout --theirs  (main wins: newer vintage / newer build)
  TAKE_DELETION-> git rm                 (the PR deliberately removed the file)
  MERGE        -> hand-resolved, keep both sides

Safety: read-only on the main tree. Operates only on the PR worktree.
Nothing is committed.
"""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run(*args):
    r = subprocess.run(list(args), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("FAILED: %s\n%s" % (" ".join(args), r.stderr.strip()))
    return r


# ---- 1. Delegates (PR deletes, main only modified) -------------------------
DELEGATES = [
    "02_dashboards/Data/14_dashboards/dealer_sellout_aim_gps.json",
    "02_dashboards/Data/90_INBOX/IDS_2026/_EXPORT/IDS_2026_dealer_compare.html",
    "02_dashboards/Data/90_INBOX/IDS_2026/reports/dashboard/IDS_2026_dealer_compare.html",
]

# ---- 2. Merged by hand ----------------------------------------------------
MERGED = [
    ".cursor/rules/isze-pricing-no-street-ui.mdc",
    "03_analytics/Isuzu/prism/.gitignore",
    "03_analytics/Isuzu/prism/CHANGELOG.md",
    "03_analytics/Isuzu/prism/scripts/build_dealer_sellout_aim_gps.py",
    "04_tools/ISZE_Tender_Monitor_Install/_source_health.json",
    "04_tools/db_sales_review/build_deck.py",
    "04_tools/db_sales_review/build_full_deck.py",
    "04_tools/ids_dealer_ranking/build_ids_country_packs_v13.py",
    "00_docs/ISZE_OS_DATA_MAP.yaml",
    "00_docs/ISZE_ROADMAP.md",
    "00_docs/agent/STATE_PACKET.md",
    "02_dashboards/ops/ISZE_Action_Ledger.html",
    "02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html",
]

# ---- 3. Everything else unmerged -> take main ------------------------------
out = run("git", "diff", "--name-only", "--diff-filter=U").stdout
unmerged = [l.strip() for l in out.splitlines() if l.strip()]

take_theirs = [f for f in unmerged if f not in DELEGATES and f not in MERGED]

print("unmerged total : %d" % len(unmerged))
print("delegates      : %d" % len([f for f in unmerged if f in DELEGATES]))
print("hand-merged    : %d" % len([f for f in unmerged if f in MERGED]))
print("take theirs    : %d" % len(take_theirs))
print()
print("TAKE-THEIRS FILES:")
for f in sorted(take_theirs):
    print("   %s" % f)

if "--apply" not in sys.argv:
    print("\n(dry run; pass --apply to execute)")
    sys.exit(0)

print("\n--- applying ---")
for f in sorted(take_theirs):
    run("git", "checkout", "--theirs", "--", f)
    run("git", "add", "--", f)
    print("  theirs   %s" % f)

for f in DELEGATES:
    run("git", "rm", "--", f)
    print("  deleted  %s" % f)

print("\nremaining unmerged (expect only the hand-merged set):")
out = run("git", "diff", "--name-only", "--diff-filter=U").stdout
rem = [l.strip() for l in out.splitlines() if l.strip()]
for f in rem:
    print("   %s" % f)
print("count: %d" % len(rem))
