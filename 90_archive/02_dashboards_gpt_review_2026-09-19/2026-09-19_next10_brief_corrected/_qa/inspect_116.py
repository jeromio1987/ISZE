import json, re, os
p = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_tmp_bpr_aim_prism_ids.json"
t = open(p, encoding="utf-8", errors="replace").read()
i = t.find('116')
idx = t.find('"generated_at": "2026-08-25T17:19:54Z"')
print("size", len(t))
print(repr(t[max(0, idx - 900):idx + 260]))
print("---- file mtime:", os.path.getmtime(p))
