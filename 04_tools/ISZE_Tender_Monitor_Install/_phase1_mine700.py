# -*- coding: utf-8 -*-
import re
import sys
import uuid
import json
import requests

sys.stdout.reconfigure(encoding="utf-8")
s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0"
big = s.get("https://www.publicprocurement.be/assets/700-CuWTD8Ia.js", timeout=120).text
print("len", len(big))

for key in [
    "getBda",
    "searchBda",
    "BdaSearch",
    "bdaSearch",
    "searchPublications",
    "getPublications",
    "getEnterprises",
    "SearchEndpoint",
    "searchNotices",
    "publicationWorkspace",
]:
    idxs = [m.start() for m in re.finditer(key, big)]
    print(key, len(idxs))
    for i in idxs[:3]:
        print(" ", big[i : i + 220].replace("\n", " "))

print("\n--- baseURL ---")
for m in re.finditer(r"baseURL:([^,}]+)", big):
    val = m.group(1)[:100]
    ctx = big[max(0, m.start() - 60) : m.start() + 120].replace("\n", " ")
    if any(x in ctx.lower() for x in ("sea", "api", "env", "vite", "search", "dos")):
        print(val, "|", ctx)

print("\n--- sea strings ---")
for m in re.finditer(r"['\"]([^'\"]*sea[^'\"]{0,100})['\"]", big, re.I):
    t = m.group(1)
    if len(t) < 120 and ("/" in t or t.startswith("sea")):
        print(" ", t)

print("\n--- bda path strings ---")
for m in re.finditer(r"['\"]([^'\"]*bda[^'\"]{0,100})['\"]", big, re.I):
    t = m.group(1)
    if "/" in t and len(t) < 120:
        print(" ", t)

# Find function that calls search with publications
print("\n--- getEnterprises definition context ---")
i = big.find("getEnterprises")
while i != -1 and i < len(big):
    chunk = big[i : i + 500]
    if "function" in chunk or "=>" in chunk or ".get(" in chunk or ".post(" in chunk:
        print(chunk.replace("\n", " ")[:450])
        print("---")
    i = big.find("getEnterprises", i + 1)
    # limit
    if i > 0 and big.find("getEnterprises") == i:
        break
    # only first few interesting
    if big[:i].count("getEnterprises:") + big[:i].count("getEnterprises=") > 3:
        break

# Broader: find '.get("' near publications
print("\n--- .get/.post path literals containing publish/notice/bda/search ---")
for m in re.finditer(r"\.(get|post|put)\(\s*[`'\"]([^`'\"]+)[`'\"]", big, re.I):
    path = m.group(2)
    if any(k in path.lower() for k in ("bda", "notice", "publish", "search", "enterprise", "dossier")):
        print(m.group(1), path)

# Also axios template: .get(`...`)
for m in re.finditer(r"\.(get|post|put)\(\s*`([^`]{1,120})`", big, re.I):
    path = m.group(2)
    if any(k in path.lower() for k in ("bda", "notice", "publish", "search", "enterprise", "dossier", "sea")):
        print(m.group(1), "TPL", path)
