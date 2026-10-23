import re, sys, openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
bad = []
for ws in wb:
    if ws.title == "Waterfall VP (original)":
        continue
    for row in ws.iter_rows():
        for c in row:
            v = c.value
            if isinstance(v, str) and v.startswith("="):
                g = re.sub(r'"[^"]*"', "", v)
                g = re.sub(r"('[^']+'|[A-Za-z_][A-Za-z0-9_ ]*)!", "", g)
                g = re.sub(r"\$?[A-Z]{1,3}\$?[0-9]+", "", g)
                nums = [n for n in re.findall(r"[0-9]+\.?[0-9]*", g) if n not in ("0", "1")]
                if nums:
                    bad.append((ws.title, c.coordinate, v[:80]))
print(len(bad))
for b in bad:
    print(b)
