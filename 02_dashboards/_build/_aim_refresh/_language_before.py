import os, re, sys, json
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")
B = "02_dashboards/_build/_aim_refresh/before/"

FILES = {
    "pricing/ISZE_Pricing_Policy_Paper.html": ["Rebuilt by", "sell-out", "1.785"],
    "sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html": ["sell-out"],
    "hub/ISZE_OS_Hub.html": ["IML v7"],
    "ops/ISZE_OS_Console.html": ["wallet", "Book B"],
    "sales/AIM_Dashboard_CY2026.html": ["street"],
}

for rel, needles in FILES.items():
    a = "02_dashboards/" + rel
    b = B + rel.replace("/", "__")
    for needle in needles:
        for label, p in (("BEFORE", b), ("AFTER ", a)):
            if not os.path.exists(p):
                print(rel, label, "missing"); continue
            t = open(p, encoding="utf-8", errors="ignore").read()
            n = len(re.findall(re.escape(needle), t, re.I))
            print(f"{rel:50} {needle:10} {label} x{n}")
    print()

# show the exact build-note context in the policy paper
p = "02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html"
t = open(p, encoding="utf-8", errors="ignore").read()
m = re.search(r".{400}Rebuilt by.{400}", t, re.S)
if m:
    print("### build-note context (policy paper)")
    print(" ".join(re.sub(r"<[^>]+>", " ", m.group(0)).split()))
