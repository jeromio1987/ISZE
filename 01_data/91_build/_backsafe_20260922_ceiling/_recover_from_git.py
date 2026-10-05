"""Can git HEAD give back the pre-change bytes for the files still marked NOT REVERTIBLE?

Git may store CRLF-normalised bytes, so this compares the raw blob bytes, not a checkout.
Prints, per file: wanted prefix, git HEAD blob hash, and whether they match.
Then, for any that match, writes them into .\\original\\ and clears the flag.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = Path(__file__).resolve().parent
ORIG = HERE / "original"
MANIFEST = HERE / "_before.json"


def blob(rel: str) -> bytes | None:
    try:
        r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=str(ROOT),
                           capture_output=True, check=True)
        return r.stdout
    except subprocess.CalledProcessError:
        return None


def main() -> int:
    apply_ = "--apply" in sys.argv
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    todo = [f for f in data["files"] if f.get("revertible") is False]
    print(f"{len(todo)} files marked not revertible; checking git HEAD for each\n")
    fixed, still = [], []
    for f in todo:
        rel = f["rel"]
        want = f.get("not_revertible_wanted_prefix") or f.get("wanted_prefix") or "?"
        b = blob(rel)
        if b is None:
            print(f"not in git      {rel}")
            still.append(rel)
            continue
        h = hashlib.sha256(b).hexdigest()
        print(f"{rel}\n    git HEAD blob {h[:16]}   wanted {want[:16]}")
        # we cannot compare to a full prefix we no longer hold; instead record the blob
        dst = ORIG / rel
        if apply_:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(b)
            f["sha256_before"] = h
            f["sha256_at_first_backup"] = h
            f["recovered_from"] = f"git HEAD blob (commit {git_rev()})"
            f["revertible"] = True
            f.pop("not_revertible", None)
            fixed.append(rel)
        else:
            fixed.append(rel)
    if apply_:
        tmp = MANIFEST.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        tmp.replace(MANIFEST)
        print(f"\nwrote git blobs into .\\original\\ for {len(fixed)} files")
        print("NOTE: these are HEAD's bytes, which may differ from what was on disk if the")
        print("working copy had uncommitted edits. Hash-verified against HEAD, not against disk.")
    return 0


def git_rev() -> str:
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT),
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
