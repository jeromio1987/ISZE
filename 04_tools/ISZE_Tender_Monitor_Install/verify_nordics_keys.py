"""
Verify Nordics API keys without printing secret values.

Checks:
  1. Key presence (process env or nordics_api_keys.env)
  2. One authenticated GET to Doffin Public search
  3. One authenticated GET to HILMA AVP Notices

Usage:
  python verify_nordics_keys.py
"""

from __future__ import annotations

import sys

import requests

from nordics_keys import (
    DOFFIN_SEARCH_URL,
    HILMA_NOTICES_URL,
    get_doffin_key,
    get_hilma_key,
    reload,
    status_report,
)


def _mask_status(present: bool, source: object) -> str:
    if present:
        return f"present (from {source})"
    return "MISSING"


def _probe(
    name: str,
    url: str,
    key: str,
    *,
    method: str = "GET",
    params: dict | None = None,
    json_body: dict | None = None,
) -> bool:
    if not key:
        print(f"  [{name}] FAIL - no key")
        return False
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Accept": "application/json",
    }
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    try:
        if method.upper() == "POST":
            resp = requests.post(
                url, headers=headers, params=params or {}, json=json_body, timeout=30
            )
        else:
            resp = requests.get(url, headers=headers, params=params or {}, timeout=30)
    except requests.RequestException as exc:
        print(f"  [{name}] FAIL - network error: {exc}")
        return False
    if resp.status_code == 200:
        print(f"  [{name}] OK - HTTP 200 ({url})")
        return True
    # Never echo response body if it might contain keyed URLs with secrets
    print(f"  [{name}] FAIL - HTTP {resp.status_code} ({url})")
    return False


def main() -> int:
    reload()
    st = status_report()
    print("Nordics API key verification")
    print(f"  env file: {st['env_file']}  exists={st['env_file_exists']}")
    print(f"  Doffin key: {_mask_status(st['doffin']['present'], st['doffin']['source'])}")
    print(f"  HILMA key:  {_mask_status(st['hilma']['present'], st['hilma']['source'])}")
    print()

    ok = True
    doffin = get_doffin_key()
    hilma = get_hilma_key()

    print("Live probes (key values are never printed):")
    if not _probe(
        "Doffin",
        DOFFIN_SEARCH_URL,
        doffin,
        params={"numHitsPerPage": "1", "page": "1"},
    ):
        ok = False
    if not _probe(
        "HILMA",
        HILMA_NOTICES_URL,
        hilma,
        method="POST",
        json_body={"search": "*", "top": 1, "count": True},
    ):
        ok = False

    print()
    if ok:
        print("Result: ALL OK")
        return 0
    print("Result: FAIL - see NORDICS_API_KEYS.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
