#!/usr/bin/env python3
"""Extract CZ FormGroup enum values from SPA JS and try search."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://vvz.nipez.cz",
    "Referer": "https://vvz.nipez.cz/",
}
OUT = Path(__file__).with_name("_probe_cz_enum.json")


def main() -> None:
    s = requests.Session()
    js = s.get("https://vvz.nipez.cz/static/js/main.e8045595.js", headers=UA, timeout=90).text
    out: dict = {}

    # Find zp={...} style enums
    for label, pat in [
        ("zp_obj", r"zp=\{[^}]{0,800}\}"),
        ("Mp_obj", r"Mp=\{[^}]{0,800}\}"),
        ("FormGroup_assign", r"FormGroup[=:]\{[^}]{0,800}\}"),
        ("VZ_uuid", r'VZ["\']?\s*:\s*["\']([0-9a-fA-F\-]{8,})["\']'),
        ("PROFIL_uuid", r'PROFIL["\']?\s*:\s*["\']([0-9a-fA-F\-]{8,})["\']'),
        ("HLAVNI_uuid", r'HLAVNI["\']?\s*:\s*["\']([0-9a-fA-F\-]{8,})["\']'),
        ("any_uuid_near_VZ", r"VZ[^,]{0,5}([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"),
    ]:
        ms = re.findall(pat, js)
        out[label] = ms[:20]
        print(label, ms[:5])

    # Context lines
    ctx = []
    for m in re.finditer(r".{0,40}\bVZ\b.{0,80}", js):
        ctx.append(m.group(0).replace("\n", " "))
        if len(ctx) >= 20:
            break
    out["VZ_ctx"] = ctx

    # Numeric enum? zp.VZ = 1?
    nums = re.findall(r"\bVZ\s*:\s*(\d+)", js)
    out["VZ_nums"] = nums[:10]
    print("VZ_nums", nums[:10])

    # Try UUID candidates found anywhere near formGroup usage
    uuids = sorted(set(re.findall(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        "\n".join(ctx),
    )))
    out["uuids_in_ctx"] = uuids

    # Broader: find assignment like VZ:"uuid" or VZ:1 in minified zp
    # Look for pattern zp=Object.freeze({VZ:...
    freeze = re.findall(r"Object\.freeze\(\{[^}]{0,400}VZ[^}]{0,400}\}\)", js)
    out["freeze"] = freeze[:5]
    print("freeze", freeze[:2])

    # Try search with discovered values
    candidates = []
    for key in ("VZ_uuid", "PROFIL_uuid", "HLAVNI_uuid", "any_uuid_near_VZ", "VZ_nums"):
        candidates.extend(out.get(key) or [])
    candidates.extend(["VZ", "1", "2", "3"])
    tries = []
    for fg in dict.fromkeys(candidates):  # unique preserve order
        params = {"formGroup": fg, "form": "HLAVNI", "page": 1, "limit": 5}
        r = s.get("https://api.vvz.nipez.cz/api/submissions/search", params=params, headers=UA, timeout=25)
        row = {"params": params, "http": r.status_code, "snip": r.text[:200]}
        tries.append(row)
        print("try", fg, r.status_code)
        if r.status_code == 200:
            break
        # also try without form
        params2 = {"formGroup": fg, "page": 1, "limit": 5}
        r2 = s.get("https://api.vvz.nipez.cz/api/submissions/search", params=params2, headers=UA, timeout=25)
        tries.append({"params": params2, "http": r2.status_code, "snip": r2.text[:200]})
        if r2.status_code == 200:
            print("HIT no-form", fg)
            break
    out["tries"] = tries
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
