#!/usr/bin/env python3
"""Resolve Os.EFORMS_FORM_GROUP_VZ from CZ SPA JS and retry search."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

UA = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://vvz.nipez.cz",
    "Referer": "https://vvz.nipez.cz/",
}
OUT = Path(__file__).with_name("_probe_cz_os_enum.json")


def main() -> None:
    s = requests.Session()
    js = s.get("https://vvz.nipez.cz/static/js/main.e8045595.js", headers=UA, timeout=90).text
    out: dict = {}
    # Find Os={...} or EFORMS_FORM_GROUP
    for label, pat in [
        ("EFORMS_hits", r"EFORMS_FORM_GROUP_[A-Z]+[^,]{0,120}"),
        ("Os_assign", r"Os=\{[^}]{0,2000}\}"),
        ("EFORMS_VZ_val", r'EFORMS_FORM_GROUP_VZ["\']?\s*:\s*["\']?([^,"\'}\s]+)'),
        ("EFORMS_PROFIL_val", r'EFORMS_FORM_GROUP_PROFIL["\']?\s*:\s*["\']?([^,"\'}\s]+)'),
    ]:
        ms = re.findall(pat, js)
        out[label] = ms[:10]
        print(label, ms[:3])

    # Also search string constants that look like enum names used as IRI
    iris = re.findall(r'["\']([A-Za-z0-9_:/#.\-]{0,40}FormGroup[A-Za-z0-9_:/#.\-]{0,40})["\']', js)
    out["FormGroup_iris"] = sorted(set(iris))[:40]
    print("iris", out["FormGroup_iris"][:15])

    # Try values from EFORMS_* captures + common IRI shapes
    candidates = []
    for m in out.get("EFORMS_VZ_val") or []:
        candidates.append(m.strip("'\""))
    for m in out.get("EFORMS_PROFIL_val") or []:
        candidates.append(m.strip("'\""))
    for m in out.get("EFORMS_hits") or []:
        # extract trailing token after :
        if ":" in m:
            candidates.append(m.split(":", 1)[1].strip().strip("'\"").split(",")[0])
    candidates.extend([
        "EFORMS_FORM_GROUP_VZ",
        "EFORMS_FORM_GROUP_PROFIL",
        "eforms_form_group_vz",
        "vz",
        "profil",
    ])
    candidates.extend(out.get("FormGroup_iris") or [])

    tries = []
    for fg in dict.fromkeys([c for c in candidates if c]):
        for form in ("vz", "HLAVNI", "hlavni", None):
            params = {"formGroup": fg, "page": 1, "limit": 5}
            if form:
                params["form"] = form
            r = s.get("https://api.vvz.nipez.cz/api/submissions/search", params=params, headers=UA, timeout=25)
            row = {"params": params, "http": r.status_code, "snip": r.text[:180]}
            tries.append(row)
            if r.status_code == 200:
                print("HIT", params, len(r.content))
                try:
                    data = r.json()
                    row["n"] = len(data) if isinstance(data, list) else list(data.keys())[:10]
                except Exception:
                    pass
                out["hit"] = row
                OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
                print("Wrote", OUT)
                return
            if r.status_code not in (400, 401, 404, 405):
                print("odd", params, r.status_code, r.text[:100])
    out["tries_n"] = len(tries)
    out["tries_tail"] = tries[-10:]
    # show unique error details
    details = sorted({t["snip"][80:180] for t in tries if t.get("snip")})
    out["error_tails"] = details[:8]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("no hit; tries", len(tries))
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
