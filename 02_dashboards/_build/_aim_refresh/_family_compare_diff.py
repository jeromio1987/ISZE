import json, re, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")
import os
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

A = "02_dashboards/sales/ISZE_PMS_Family_Compare.html"
B = "02_dashboards/_build/_aim_refresh/before/sales__ISZE_PMS_Family_Compare.html"
a = open(A, "rb").read()
b = open(B, "rb").read()
print("bytes", len(b), "->", len(a))
print("sha before", hashlib.sha256(b).hexdigest()[:16])
print("sha after ", hashlib.sha256(a).hexdigest()[:16])
print("identical:", hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest())

ta = a.decode("utf-8", errors="ignore")
tb = b.decode("utf-8", errors="ignore")
for needle in ["aim_risk", "AIM high-risk", "high_risk", "No AIM", "aim_bvp_family_risk", "bvp_expose"]:
    print(f"  {needle:22} before={tb.count(needle)} after={ta.count(needle)}")
