#!/usr/bin/env python3
import re
from pathlib import Path

js = Path("_overnight_dk_main.js").read_text(encoding="utf-8")
patterns = [
    r"Bekendtgoerelse.{0,60}",
    r"[\"']/[^\"']*soeg[^\"']*[\"']",
    r"[\"']/[^\"']*bekendt[^\"']*[\"']",
    r"[\"']/[^\"']*[Ss]earch[^\"']*[\"']",
    r"[\"']/[^\"']*annonce[^\"']*[\"']",
    r"baseUrl:\s*\{[^}]{0,400}\}",
]
for pat in patterns:
    hits = list(dict.fromkeys(re.findall(pat, js, flags=re.I | re.S)))[:30]
    print("---", pat[:50], "n=", len(hits))
    for h in hits[:20]:
        print(" ", h[:160].replace("\n", " "))

# Extract environmentConfig.variables.baseUrl block
m = re.search(r"variables:\s*\{.*?baseUrl:\s*\{(.*?)\}\s*,", js, flags=re.S)
if m:
    print("BASEURL BLOCK", m.group(1)[:800])
