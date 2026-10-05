import re
B = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\\"
t = open(B + "03_Warranty_Commercial_Review.html", encoding="utf-8", newline="").read()
markup = re.sub(r"<script[^>]*>.*?</script>", "", t, flags=re.S | re.I)
print("canvas ids :", re.findall(r'<canvas id="([^"]+)"', markup))
print("table ids  :", re.findall(r'<table id="([^"]+)"', markup))
print("c9 in markup:", 'id="c9"' in markup)
print("t4 in markup:", 'id="t4"' in markup)
print("new chart code present:", "Position vs the limits" in t)
print("payer strings left in file:", t.count("who actually pays"), t.count("Who pays"))
print("old wp array left:", "price-list and campaign question" in t)
