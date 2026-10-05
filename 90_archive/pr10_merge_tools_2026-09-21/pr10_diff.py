"""Read-only: for a file, show base->ours and base->theirs diffs."""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

files = sys.argv[1].split(",")
ctx = sys.argv[2] if len(sys.argv) > 2 else "6"

for f in files:
    print("#" * 100)
    print("# FILE: %s" % f)
    for label, a, b in (("BASE->OURS(PR branch)", ":1:" + f, ":2:" + f),
                        ("BASE->THEIRS(main)", ":1:" + f, ":3:" + f)):
        print("=" * 90)
        print("= %s" % label)
        print("=" * 90)
        r = subprocess.run(
            ["git", "diff", "--no-color", "-U" + ctx, a, b],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        body = r.stdout
        if len(body) > 14000:
            body = body[:14000] + "\n...[truncated]..."
        print(body)
