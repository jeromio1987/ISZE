import sys, re, collections
sys.stdout.reconfigure(encoding="utf-8")
h = open("ISUZU_UNIVERSE_3_0_SHOWCASE.html", encoding="utf-8", errors="replace").read()
for w in ["Proposed analytical sequence", "Illustrative design",
          "Proposed feedback mechanism", "no measured causal"]:
    print("%-30s %d" % (w, h.count(w)))
print()
c = collections.Counter(re.findall(r'>([^<>]{6,70})<', h))
for k, v in c.most_common(30):
    t = " ".join(k.split())
    if t and not t.startswith(("&", "{", "//")):
        print("%4d  %s" % (v, t))
