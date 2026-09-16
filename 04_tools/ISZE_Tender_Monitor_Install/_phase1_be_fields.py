# -*- coding: utf-8 -*-
import json
import os
import sys
import uuid
import requests

sys.stdout.reconfigure(encoding="utf-8")

# Public front-end value from https://www.publicprocurement.be/env.config.js.
# Kept out of git: set BE_BOSA_CLIENT_SECRET in the environment.
CLIENT_SECRET = os.environ.get("BE_BOSA_CLIENT_SECRET", "")
if not CLIENT_SECRET:
    raise SystemExit(
        "BE_BOSA_CLIENT_SECRET unset - read it from "
        "https://www.publicprocurement.be/env.config.js and export it "
        "(or add it to nordics_api_keys.env)"
    )

s = requests.Session()
token = s.post(
    "https://www.publicprocurement.be/auth/realms/supplier/protocol/openid-connect/token",
    data={
        "grant_type": "client_credentials",
        "client_id": "frontend-public",
        "client_secret": CLIENT_SECRET,
    },
    timeout=30,
).json()["access_token"]
hdr = {
    "Authorization": f"Bearer {token}",
    "BelGov-Trace-Id": str(uuid.uuid4()),
    "Accept": "application/json",
    "Content-Type": "application/json",
}
r = s.post(
    "https://www.publicprocurement.be/api/sea/search/publications",
    headers=hdr,
    json={
        "terms": "voertuig",
        "cpvCodes": ["34131000", "50110000", "50118000"],
        "withActiveSubmissionDeadline": True,
        "page": 1,
        "pageSize": 2,
    },
    timeout=45,
)
j = r.json()
print("total", j.get("totalCount"))
p = j["publications"][0]
print("top keys:", sorted(p.keys()))
# print useful fields
interesting = {}
for k in sorted(p.keys()):
    v = p[k]
    if isinstance(v, (str, int, float, bool)) or v is None:
        interesting[k] = v
    elif isinstance(v, dict):
        interesting[k] = {kk: (vv if not isinstance(vv, (list, dict)) else type(vv).__name__) for kk, vv in list(v.items())[:20]}
    elif isinstance(v, list):
        interesting[k] = f"list[{len(v)}]"
print(json.dumps(interesting, ensure_ascii=False, indent=2)[:3000])
# dossier keys
d = p.get("dossier") or {}
print("dossier keys", sorted(d.keys()))
for k in ("referenceNumber", "reference", "titles", "title", "descriptions", "organisation", "organizations"):
    if k in d:
        print(k, json.dumps(d[k], ensure_ascii=False)[:400])
# notice fields
for k in ("publicationDate", "dispatchDate", "tenderSubmissionDeadline", "submissionDeadline", "noticeId", "id", "referenceNumber", "shortLink", "url", "formType", "noticeSubtype"):
    if k in p:
        print("p."+k, p[k])
# dig for deadline
for k, v in p.items():
    if "deadline" in k.lower() or "submission" in k.lower() or "title" in k.lower() or "link" in k.lower() or "reference" in k.lower():
        print("FIELD", k, json.dumps(v, ensure_ascii=False)[:300])
# save one full sample
with open("_phase1_be_sample_publication.json", "w", encoding="utf-8") as f:
    json.dump(p, f, ensure_ascii=False, indent=2)
print("saved sample")
