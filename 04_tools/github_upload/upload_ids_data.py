"""
Upload all IDS 2026 dealer standard files to GitHub repo jeromio1987/isuzu-docs
Target: IDS/ folder in the repo, preserving the subfolder structure.
All files are <25 MB so we use the Contents API only.
"""
import base64
import os
import sys
import time
import requests

TOKEN = os.environ.get("ISZE_GH_TOKEN")
if not TOKEN:
    sys.exit(
        "ERROR: set the ISZE_GH_TOKEN environment variable to a GitHub PAT "
        "with repo access to jeromio1987/isuzu-docs before running this script.\n"
        "PowerShell (current session):  $env:ISZE_GH_TOKEN = 'ghp_...'\n"
        "Persist for your user:         setx ISZE_GH_TOKEN \"ghp_...\""
    )
OWNER = "jeromio1987"
REPO  = "isuzu-docs"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _find_isze_root() -> str:
    """ISZE root = $ISZE_ROOT if set, else nearest parent containing paths.yaml."""
    root = os.environ.get("ISZE_ROOT")
    if root and os.path.exists(os.path.join(root, "paths.yaml")):
        return root
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "paths.yaml")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("Could not locate ISZE root (no paths.yaml found in any parent).")


# Local source folder resolved from ISZE root (works from any script location)
BASE = _find_isze_root()
IDS_LOCAL = os.path.join(BASE, "01_data", "90_INBOX", "IDS_2026")

# Files to skip
SKIP_NAMES = {".gitkeep", ".DS_Store", "Thumbs.db"}


def collect_files():
    """Walk IDS_2026 and return list of (local_path, repo_path)."""
    files = []
    for root, dirs, filenames in os.walk(IDS_LOCAL):
        # Skip hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in filenames:
            if name in SKIP_NAMES or name.startswith("."):
                continue
            local_path = os.path.join(root, name)
            # Relative path from IDS_LOCAL, convert to forward slashes
            rel = os.path.relpath(local_path, IDS_LOCAL).replace("\\", "/")
            repo_path = f"IDS/{rel}"
            files.append((local_path, repo_path))
    return sorted(files, key=lambda x: x[1])


def get_sha(repo_path):
    """Get SHA of existing file (needed for update). Returns None if new."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{repo_path}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def upload_file(local_path, repo_path, sha=None):
    """Upload a single file via the Contents API."""
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")
    name = os.path.basename(local_path)
    action = "Update" if sha else "Add"
    payload = {
        "message": f"{action} {name} — IDS 2026 dealer standards",
        "content": content,
    }
    if sha:
        payload["sha"] = sha
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{repo_path}"
    r = requests.put(url, headers=HEADERS, json=payload, timeout=60)
    return r.status_code


def main():
    print(f"\n{'='*65}")
    print(f"IDS 2026 Upload — jeromio1987/isuzu-docs  →  IDS/")
    print(f"{'='*65}\n")

    files = collect_files()
    total = len(files)
    print(f"Found {total} files to upload.\n")

    ok = skipped = failed = 0

    for i, (local_path, repo_path) in enumerate(files, 1):
        name = os.path.basename(local_path)
        size_kb = os.path.getsize(local_path) / 1024
        print(f"[{i:3}/{total}] {repo_path}  ({size_kb:.0f} KB)")

        sha = get_sha(repo_path)
        if sha:
            print(f"        → exists, updating (SHA {sha[:8]}…)")

        try:
            status = upload_file(local_path, repo_path, sha)
            if status in (200, 201):
                print(f"        ✓ OK")
                ok += 1
            elif status == 422 and sha is None:
                # Already exists but we didn't get the SHA (race condition)
                print(f"        ⚠ Already exists — skipping")
                skipped += 1
            else:
                print(f"        ✗ FAILED (HTTP {status})")
                failed += 1
        except Exception as e:
            print(f"        ✗ ERROR: {e}")
            failed += 1

        # Gentle rate limiting — GitHub allows 5000 requests/hr
        # 2 calls per file (GET sha + PUT) = 624 calls for 312 files
        # No sleep needed, but add a tiny pause every 50 files to be safe
        if i % 50 == 0:
            print(f"\n  … pausing 2s (rate-limit courtesy) …\n")
            time.sleep(2)

    print(f"\n{'='*65}")
    print(f"Done: {ok} uploaded, {skipped} skipped (already up to date), {failed} failed")
    print(f"{'='*65}\n")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
