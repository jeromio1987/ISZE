"""
Upload missing GPS data files to GitHub repo jeromio1987/isuzu-docs
Handles both regular files (<25MB) and large files (>25MB) via Git Data API
"""
import base64
import json
import os
import sys
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


BASE = _find_isze_root()
DERIVED = os.path.join(BASE, "01_data", "00_derived")
PRISM_DATA = os.path.join(BASE, "03_analytics", "Isuzu", "prism", "data")

# Files to upload: (local_path, repo_path)
FILES = [
    # GPS output files
    (os.path.join(DERIVED, "gps_spu_by_family.csv"),        "Data/derived/gps_spu_by_family.csv"),
    (os.path.join(DERIVED, "gps_spu_pms.csv"),              "Data/derived/gps_spu_pms.csv"),
    (os.path.join(DERIVED, "gps_master.csv"),                "Data/derived/gps_master.csv"),
    (os.path.join(DERIVED, "gps_clean_all_fy.csv"),         "Data/derived/gps_clean_all_fy.csv"),
    (os.path.join(DERIVED, "gps_clean_all_fy_v2.csv"),      "Data/derived/gps_clean_all_fy_v2.csv"),
    (os.path.join(DERIVED, "gps_clean_projection.csv"),     "Data/derived/gps_clean_projection.csv"),
    (os.path.join(DERIVED, "gps_json_vs_raw_audit.csv"),    "Data/derived/gps_json_vs_raw_audit.csv"),
    # Reference / calculation inputs
    (os.path.join(PRISM_DATA, "distributor_master_mapping.csv"), "Data/derived/distributor_master_mapping.csv"),
    (os.path.join(DERIVED, "network_percentile.csv"),        "Data/derived/network_percentile.csv"),
    (os.path.join(DERIVED, "pms_summary_by_db.csv"),        "Data/derived/pms_summary_by_db.csv"),
    (os.path.join(DERIVED, "pms_opportunity_matrix.csv"),   "Data/derived/pms_opportunity_matrix.csv"),
    (os.path.join(DERIVED, "bvp_pn_dimension.csv"),         "Data/derived/bvp_pn_dimension.csv"),
    # Sales fact (large - generated from parquet)
    (os.path.join(DERIVED, "sales_fact.csv"),               "Data/derived/sales_fact.csv"),
]


def get_sha(repo_path):
    """Get SHA of existing file (needed for update)."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{repo_path}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def upload_small(local_path, repo_path, sha=None):
    """Upload file <= 25MB via Contents API."""
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")
    payload = {
        "message": f"Add {os.path.basename(repo_path)} — GPS data upload",
        "content": content,
    }
    if sha:
        payload["sha"] = sha
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{repo_path}"
    r = requests.put(url, headers=HEADERS, json=payload)
    return r.status_code, r.json().get("content", {}).get("name", r.text[:120])


def upload_large(local_path, repo_path):
    """Upload file > 25MB via Git Data API (blob → tree → commit → update ref)."""
    print(f"  Using Git Data API for large file...")

    # Step 1: Create blob
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")
    blob_url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/blobs"
    blob_r = requests.post(blob_url, headers=HEADERS, json={"content": content_b64, "encoding": "base64"})
    if blob_r.status_code not in (200, 201):
        return blob_r.status_code, f"Blob creation failed: {blob_r.text[:200]}"
    blob_sha = blob_r.json()["sha"]
    print(f"  Blob created: {blob_sha[:10]}...")

    # Step 2: Get HEAD commit SHA + tree SHA
    ref_url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/refs/heads/main"
    ref_r = requests.get(ref_url, headers=HEADERS)
    if ref_r.status_code != 200:
        # Try master branch
        ref_url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/refs/heads/master"
        ref_r = requests.get(ref_url, headers=HEADERS)
    commit_sha = ref_r.json()["object"]["sha"]

    commit_url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits/{commit_sha}"
    commit_r = requests.get(commit_url, headers=HEADERS)
    tree_sha = commit_r.json()["tree"]["sha"]

    # Step 3: Create new tree
    tree_url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees"
    tree_r = requests.post(tree_url, headers=HEADERS, json={
        "base_tree": tree_sha,
        "tree": [{"path": repo_path, "mode": "100644", "type": "blob", "sha": blob_sha}]
    })
    new_tree_sha = tree_r.json()["sha"]

    # Step 4: Create commit
    new_commit_url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits"
    new_commit_r = requests.post(new_commit_url, headers=HEADERS, json={
        "message": f"Add {os.path.basename(repo_path)} — GPS sales data (large file)",
        "tree": new_tree_sha,
        "parents": [commit_sha]
    })
    new_commit_sha = new_commit_r.json()["sha"]

    # Step 5: Update ref
    update_r = requests.patch(ref_url, headers=HEADERS, json={"sha": new_commit_sha})
    return update_r.status_code, f"Large file uploaded via Git Data API"


def main():
    print(f"\n{'='*60}")
    print(f"GPS Data Upload — jeromio1987/isuzu-docs")
    print(f"{'='*60}\n")

    ok, failed = 0, 0
    for local_path, repo_path in FILES:
        name = os.path.basename(local_path)

        if not os.path.exists(local_path):
            print(f"  SKIP {name} — file not found locally")
            continue

        size_mb = os.path.getsize(local_path) / 1024 / 1024
        print(f"Uploading {name} ({size_mb:.1f} MB) → {repo_path}")

        sha = get_sha(repo_path)
        if sha:
            print(f"  File exists in repo (SHA: {sha[:10]}...) — updating")

        try:
            if size_mb > 25:
                status, msg = upload_large(local_path, repo_path)
            else:
                status, msg = upload_small(local_path, repo_path, sha)

            if status in (200, 201):
                print(f"  ✓ OK ({status})")
                ok += 1
            else:
                print(f"  ✗ FAILED ({status}): {msg}")
                failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
        print()

    print(f"\n{'='*60}")
    print(f"Done: {ok} uploaded, {failed} failed")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
