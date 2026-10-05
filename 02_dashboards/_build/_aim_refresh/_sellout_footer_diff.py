import hashlib, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

A = "02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html"
B = "02_dashboards/_build/_aim_refresh/before/sales__Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html"
a = open(A, encoding="utf-8", errors="ignore").read()
b = open(B, encoding="utf-8", errors="ignore").read()
print("bytes", len(b), "->", len(a))

# normalise the footer before comparing, so any other difference shows up
def strip_footer(t):
    t = re.sub(r"<footer[\s\S]*?</footer>", "<footer/>", t, count=1)
    return t

na, nb = strip_footer(a), strip_footer(b)
print("same after footer normalised:", na == nb)
if na != nb:
    # find the first difference
    for i, (x, y) in enumerate(zip(na, nb)):
        if x != y:
            print("first diff at", i)
            print("  before:", repr(nb[i-120:i+160]))
            print("  after :", repr(na[i-120:i+160]))
            break
    print("len norm before/after", len(nb), len(na))

m = re.search(r"<footer[\s\S]*?</footer>", a)
print("new footer:", " ".join(m.group(0).split())[:220] if m else "NONE")
