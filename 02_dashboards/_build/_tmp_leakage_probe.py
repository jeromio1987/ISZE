"""Throwaway: run the leakage review builder into a QA path and dump the payload
it computes now, so every changed figure can be listed before a live rebuild."""
import json
import pathlib
import sys
import traceback

SRC = pathlib.Path(__file__).with_name("build_db_leakage_review.py")
QA = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_qa\leakage_probe")
QA.mkdir(parents=True, exist_ok=True)

src = SRC.read_text(encoding="utf-8")
src = src.replace(
    r'OUT_HTML = os.path.join(ROOT, r"02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html")',
    'OUT_HTML = r"' + str(QA / "probe.html") + '"',
)
src = src.replace(
    r'OUT_CMD = os.path.join(ROOT, r"02_dashboards\sales\OPEN_ISZE_DB_Leakage_Review.cmd")',
    'OUT_CMD = r"' + str(QA / "probe.cmd") + '"',
)
assert "probe.html" in src and "probe.cmd" in src, "redirect failed"

payload = {}
g = {"__name__": "__main__", "__file__": str(SRC)}
try:
    exec(compile(src, str(SRC), "exec"), g)
except Exception:  # noqa: BLE001
    print("PROBE_HTML_FAILED (payload still captured)")
    traceback.print_exc()
payload = g.get("PAYLOAD", {})

if not payload:
    print("PROBE_NO_PAYLOAD")
    raise SystemExit(1)

(QA / "probe_payload.json").write_text(json.dumps(payload), encoding="utf-8")

try:
    old_raw = pathlib.Path(
        r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_DB_Leakage_Review_CY2025.html"
    ).read_text(encoding="utf-8")
    import re

    old = json.loads(re.search(r"var DATA = (\{.*?\});\n", old_raw).group(1))
except Exception as exc:  # noqa: BLE001
    print("OLD_PAYLOAD_UNREADABLE", exc)
    old = {}

oi = {r["db"]: r for r in old.get("dbs", [])}
ni = {r["db"]: r for r in payload.get("dbs", [])}
KEY_DBS = ("IUK", "ITUK", "IRELAND", "UTI", "GREECE", "PORTUGAL")

print("\n== NETWORK ==")
for k in ("gap", "exp", "act", "rep_cy", "rep_rows_cy", "over_cy", "pull_cy", "dealer_cy"):
    print(f"  {k:14s} old={old.get('nw',{}).get(k)}  new={payload.get('nw',{}).get(k)}")

print("\n== PER DB (rep_cy total / dealer cap / demand gap) ==")
for db in KEY_DBS:
    a, b = oi.get(db, {}), ni.get(db, {})
    if not a or not b:
        continue
    f = lambda r: (
        (r.get("rep", {}).get("cy") or {}).get("total"),
        (r.get("dealer", {}).get("cy") or {}).get("cap"),
        (r.get("demand", {}).get("cy") or {}).get("gap"),
    )
    print(f"  {db:9s} old={f(a)}  new={f(b)}")

print("\n== CHANGED DB RECORDS (any field) ==")
for db in sorted(set(oi) | set(ni)):
    if json.dumps(oi.get(db), sort_keys=True) != json.dumps(ni.get(db), sort_keys=True):
        print("  ", db)
