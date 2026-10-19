import json
from pathlib import Path
H = Path(__file__).parent
D = json.loads((H / "payload6.json").read_text(encoding="utf-8"))
pn = sorted({p[0] for p in D["parts"]})
print("n", len(pn), "lengths", {len(p) for p in pn})
def b36(n):
    s = "0123456789abcdefghijklmnopqrstuvwxyz"; out = ""
    while True:
        n, r = divmod(n, 36); out = s[r] + out
        if n == 0: return out
prev = 0; parts = []
for p in pn:
    v = int(p); parts.append(b36(v - prev)); prev = v
enc = ",".join(parts)
half = len(parts) // 2
(H / "_pn_a.txt").write_text(",".join(parts[:half]), encoding="ascii"); (H / "_pn_b.txt").write_text(",".join(parts[half:]), encoding="ascii")
print("encoded chars", len(enc), "half", half, "first", parts[:5])
# self-check decode
v = 0; back = []
for t in enc.split(","):
    v += int(t, 36); back.append(str(v).zfill(10))
assert back == pn
print("decode ok")
