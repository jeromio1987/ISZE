import io, re, collections

f = r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\TASKS_96.txt"
txt = io.open(f, "rb").read().decode("utf-8", errors="replace")
lines = txt.split("\n")

cur = None
d = collections.OrderedDict()
for l in lines:
    m = re.match(r'^([A-Z]+-\d+) \| (.+)$', l)
    if m:
        cur = m.group(1)
    m2 = re.search(r'Proposed owner:\s*([^|]+)', l)
    if m2 and cur:
        d.setdefault(m2.group(1).strip(), []).append(cur)

for owner, tasks in sorted(d.items(), key=lambda kv: -len(kv[1])):
    fams = collections.Counter(t.split("-")[0] for t in tasks)
    print("=== %s (%d) ===" % (owner, len(tasks)))
    print("    families:", dict(fams))
    print("    tasks   :", " ".join(tasks))
