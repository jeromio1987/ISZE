import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

FILES = ["02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html",
         "02_dashboards/sales/Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html"]

for f in FILES:
    raw = open(f, encoding="utf-8", errors="ignore").read()
    print("=" * 6, f)
    for m in re.finditer(r"sell-?out", raw, re.I):
        # is it visible text or inside a script?
        before = raw[:m.start()]
        in_script = before.rfind("<script") > before.rfind("</script>")
        in_style = before.rfind("<style") > before.rfind("</style>")
        in_attr = raw[max(0, m.start() - 60):m.start()].rfind("=") > raw[max(0, m.start() - 60):m.start()].rfind(">")
        ctx = " ".join(re.sub(r"<[^>]+>", " ", raw[max(0, m.start() - 110): m.start() + 90]).split())
        where = "script" if in_script else ("style" if in_style else ("attr" if in_attr else "VISIBLE TEXT"))
        print(f"   [{where}] ...{ctx[:150]}")
