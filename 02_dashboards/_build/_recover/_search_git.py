"""Read-only: search every git object for the destroyed builder.

Filters by size first, so only plausible candidates are read. Changes nothing.
"""
import subprocess

REPO = r"C:\Users\jerom\Desktop\claude\ISZE"
TARGET = 76251


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True).stdout


raw = git("cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype) %(objectsize)")
objs = [line.split() for line in raw.decode("utf-8", "replace").splitlines() if line.strip()]
blobs = [(o, int(s)) for o, t, s in objs if t == "blob"]
print("total blobs:", len(blobs))

# size band around the destroyed file; the builder was 76,251 bytes
band = [(o, s) for o, s in blobs if 60_000 <= s <= 100_000]
print("blobs in 60-100 KB band:", len(band))

hits = []
for oid, size in band:
    data = git("cat-file", "-p", oid)
    if b"build_db_leakage_review" in data or b"ISZE_DB_Leakage_Review_CY2025" in data:
        hits.append((oid, size, data[:80]))

print("candidate hits:", len(hits))
for oid, size, head in hits:
    print(" ", oid, size)
    print("   ", repr(head[:70]))

# also check the two dangling commits and every commit message for the builder
commits = [o for o, t, s in objs if t == "commit"]
print("commits:", len(commits))
found = 0
for c in commits:
    tree = git("ls-tree", "-r", "--name-only", c)
    if b"build_db_leakage_review.py" in tree:
        found += 1
        print("  builder present in commit", c.decode())
print("commits containing the builder:", found)
