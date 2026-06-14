"""
One-shot GitHub deploy script for Jarvis.
Usage: python deploy_to_github.py <GITHUB_PAT>
The PAT is not stored anywhere — it lives only in memory while this script runs.

NOTE: this currently creates the repo PUBLIC ("private": False) for a tool marked
"not for external distribution". Set "private": True below if you do not want it public.
"""

import sys
import base64
import time
import requests

REPO_NAME = "jarvis-isze"
GITHUB_USER = "jeromio1987"
BASE_URL = "https://api.github.com"

FILES = {
    "app.py": "app.py",
    "pages/1_Stack.py": "pages/1_Stack.py",
    "pages/2_Email_Drafter.py": "pages/2_Email_Drafter.py",
    "pages/3_SPA_Assistant.py": "pages/3_SPA_Assistant.py",
    "pages/4_Opportunity_Radar.py": "pages/4_Opportunity_Radar.py",
    "pages/5_NOx_SPA_Optimizer.py": "pages/5_NOx_SPA_Optimizer.py",
    "pages/6_Competitive_Parts.py": "pages/6_Competitive_Parts.py",
    "utils/__init__.py": "utils/__init__.py",
    "utils/config.py": "utils/config.py",
    "utils/api_clients.py": "utils/api_clients.py",
    "utils/helpers.py": "utils/helpers.py",
    "requirements.txt": "requirements.txt",
    "README.md": "README.md",
    ".gitignore": ".gitignore",
    ".env.example": ".env.example",
}


def get_headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def create_repo(token: str) -> bool:
    print(f"Creating repo {GITHUB_USER}/{REPO_NAME} ...")
    resp = requests.post(
        f"{BASE_URL}/user/repos",
        headers=get_headers(token),
        json={
            "name": REPO_NAME,
            "description": "Jarvis — ISZE Internal AI Tool (Streamlit)",
            "private": False,
            "auto_init": False,
        },
    )
    if resp.status_code == 201:
        print(f"  OK Repo created: {resp.json()['html_url']}")
        return True
    elif resp.status_code == 422:
        print(f"  INFO Repo already exists - continuing with file uploads.")
        return True
    else:
        print(f"  FAIL to create repo: {resp.status_code} {resp.text}")
        return False


def upload_file(token: str, repo_path: str, local_path: str) -> bool:
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    url = f"{BASE_URL}/repos/{GITHUB_USER}/{REPO_NAME}/contents/{repo_path}"

    # Check if file already exists (get its SHA for update)
    sha = None
    check = requests.get(url, headers=get_headers(token))
    if check.status_code == 200:
        sha = check.json().get("sha")

    payload = {
        "message": f"Add {repo_path}",
        "content": content_b64,
    }
    if sha:
        payload["sha"] = sha
        payload["message"] = f"Update {repo_path}"

    resp = requests.put(url, headers=get_headers(token), json=payload)
    if resp.status_code in (200, 201):
        action = "Updated" if sha else "Uploaded"
        print(f"  OK {action}: {repo_path}")
        return True
    else:
        print(f"  FAIL {repo_path}: {resp.status_code} {resp.text}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python deploy_to_github.py <GITHUB_PAT>")
        sys.exit(1)

    token = sys.argv[1]

    if not create_repo(token):
        sys.exit(1)

    time.sleep(1)  # brief pause after repo creation

    print(f"\nUploading {len(FILES)} files...")
    ok = 0
    fail = 0
    for repo_path, local_path in FILES.items():
        if upload_file(token, repo_path, local_path):
            ok += 1
        else:
            fail += 1

    print(f"\n{'='*50}")
    print(f"Done. {ok} uploaded, {fail} failed.")
    if fail == 0:
        print(f"\nRepo URL: https://github.com/{GITHUB_USER}/{REPO_NAME}")
        print("\nNext step: go to https://share.streamlit.io and deploy from this repo.")
    else:
        print("\nCheck errors above and re-run if needed.")
    sys.stdout.flush()

    # Wipe the token variable from memory
    token = None


if __name__ == "__main__":
    main()
