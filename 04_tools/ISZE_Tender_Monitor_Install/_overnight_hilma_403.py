#!/usr/bin/env python3
"""Probe HILMA endpoints / headers for 403 (never print key)."""
from __future__ import annotations

import json
from pathlib import Path

import requests

from nordics_keys import get_hilma_key, reload

reload()
key = get_hilma_key()
urls = [
    "https://hns-hilma-prod-apim.azure-api.net/avp/Notices",
    "https://hns-hilma-prod-apim.azure-api.net/avp/notices",
    "https://hns-hilma-prod-apim.azure-api.net/Notices",
    "https://hns-hilma-prod-apim.azure-api.net/search/Notices",
]
out = {}
for u in urls:
    for hdr_name in ["Ocp-Apim-Subscription-Key", "subscription-key"]:
        headers = {hdr_name: key, "Accept": "application/json"}
        try:
            r = requests.get(u, headers=headers, params={"pageSize": 5}, timeout=30)
            print(r.status_code, hdr_name, u, r.text[:120].replace("\n", " "))
            out[f"{u}|{hdr_name}"] = {"http": r.status_code, "snip": r.text[:200]}
        except Exception as e:
            print("ERR", u, e)
Path("_overnight_hilma_403.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
