import os, re, sys, struct, zlib, json
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"C:\Users\jerom\Desktop\claude\ISZE")

def png_stats(p):
    """width, height, unique-ish colour count, share of non-background pixels."""
    d = open(p, "rb").read()
    w = struct.unpack(">I", d[16:20])[0]
    h = struct.unpack(">I", d[20:24])[0]
    # decode IDAT
    idat = b""
    i = 8
    while i < len(d):
        ln = struct.unpack(">I", d[i:i+4])[0]
        typ = d[i+4:i+8]
        if typ == b"IDAT":
            idat += d[i+8:i+8+ln]
        i += 12 + ln
    raw = zlib.decompress(idat)
    bpp = 4 if d[25] == 6 else 3
    stride = w * bpp + 1
    # unfilter (first filter byte per row, filters 0..4)
    prev = bytearray(w * bpp)
    colours = set()
    for y in range(h):
        row = bytearray(raw[y*stride:(y+1)*stride])
        f = row[0]
        line = bytearray(row[1:])
        if f == 1:
            for x in range(bpp, len(line)):
                line[x] = (line[x] + line[x-bpp]) & 255
        elif f == 2:
            for x in range(len(line)):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(len(line)):
                a = line[x-bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(len(line)):
                a = line[x-bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x-bpp] if x >= bpp else 0
                pp = a + b - c
                pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        prev = line
        if y % 7 == 0:
            for x in range(0, len(line), bpp * 11):
                colours.add(bytes(line[x:x+bpp]))
    return w, h, len(colours)

QA = "02_dashboards/_build/_aim_refresh/_qa"
shots = sorted(f for f in os.listdir(QA) if f.endswith(".png"))
print("screenshots on disk:", len(shots))
empty = []
for f in shots:
    p = os.path.join(QA, f)
    sz = os.path.getsize(p)
    try:
        w, h, c = png_stats(p)
    except Exception as e:
        w, h, c = 0, 0, -1
    flag = ""
    if c < 25:
        flag = "  <-- LOOKS EMPTY/FLAT"
        empty.append(f)
    print(f"   {f:70} {sz/1024:8.0f} KB  {w}x{h}  colours~{c}{flag}")
print()
print("flat/empty screenshots:", empty if empty else "none")
