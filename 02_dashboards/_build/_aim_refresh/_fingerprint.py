import hashlib, json, os, sys, csv
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

LIVE = "01_data/00_derived/aim_master_v2.csv"
B1 = "01_data/00_derived/aim_master_v2.csv.bak_pre_export_aim_eq_20260924_20260924_142051"

def stat(p):
    rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
    def n(r, k): return (r.get(k) or "").strip()
    return {
        "rows": len(rows),
        "has_aim": sum(1 for r in rows if n(r, "has_aim") == "1"),
        "literal_unknown": sum(1 for r in rows if n(r, "aim_l1").lower() == "unknown"),
        "blank_l1": sum(1 for r in rows if n(r, "aim_l1") == ""),
        "real_l1": sum(1 for r in rows if n(r, "aim_l1") and n(r, "aim_l1").lower() != "unknown"),
        "stamp_export_aim_eq": sum(1 for r in rows if "export_aim_eq_20260924" in n(r, "aim_source")),
        "bytes": os.path.getsize(p),
        "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
    }

now = stat(LIVE)
pre = stat(B1)
print("BEFORE (backup 14:20:51)"); print(json.dumps(pre, indent=1))
print("AT BUILD TIME (live now)"); print(json.dumps(now, indent=1))
json.dump({"before_backup": pre, "live_at_build": now},
          open("02_dashboards/_build/_aim_refresh/master_fingerprint.json", "w", encoding="utf-8"), indent=1)

# overlay and pair, read only
for p in ["01_data/00_derived/aim_pn_classification_20260920.csv",
          "01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260924.csv",
          "01_data/00_derived/AIM_Master_PN_Categories_Figkey_20260921.csv"]:
    st = os.stat(p)
    print(os.path.basename(p), st.st_size,
          hashlib.sha256(open(p, "rb").read()).hexdigest()[:16],
          __import__("datetime").datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"))
