"""QA for deep sales-to-dealer pack."""
import json
import re
from pathlib import Path

root = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
html = (root / "02_dashboards/sales/Next_Analyses_Sales_to_Dealer_SixDB.html").read_text(
    encoding="utf-8"
)
payload = json.loads(
    (root / "01_data/14_dashboards/next_analyses_sales_to_dealer.json").read_text(
        encoding="utf-8"
    )
)
cmd = root / "02_dashboards/sales/OPEN_Next_Analyses_Sales_to_Dealer_SixDB.cmd"
spec = root / "00_docs/sales-to-dealer-analytics-framework_deeplayers.md"

checks = []

def ok(name, cond, detail=""):
    checks.append((bool(cond), name, detail))
    print(("PASS" if cond else "FAIL"), name, detail)

ok("spec exists", spec.exists())
ok("OPEN cmd", cmd.exists())
ok("no CDN", len(re.findall(r"src=['\"]https?://", html)) == 0)
ok("canvases", html.count("<canvas") >= 5, str(html.count("<canvas")))
ok("table rows", html.count("<tr>") >= 20, str(html.count("<tr>")))
ok("core selected", 'value="core" selected' in html)
ok("gps selected", 'value="gps" selected' in html)
ok("IUK=LCV label", ("IUK=LCV" in html) or ("IUK = LCV" in html))
# Affirmative only: "IUK = CV". Negation / "never label … as trucks" is OK.
bad_iuk = re.search(r"\bIUK\s*=\s*CV\b", html, re.I)
ok("no IUK=CV label", bad_iuk is None, bad_iuk.group(0) if bad_iuk else "")
ok("IUK not-trucks reminder present", "not CV/trucks" in html or "Never label IUK as trucks" in html)
ok("no NaN payload", "NaN" not in json.dumps(payload))
ok("IUK channel LCV", payload["uio_channel"]["IUK"] == "LCV")
ok("default focus core", payload.get("default_focus") == "core")

core = payload["gates"]["core"]
overall = payload["gates"]["overall"]
ok(
    "core rank present",
    len(core["rank"]) == 6,
    str([r["distributor_code"] for r in core["rank"]]),
)

shares = {
    r["distributor_code"]: r.get("consumables_share_of_std_proxy") for r in core["gap"]
}
ok(
    "consumables shares transparent",
    all(v is not None for v in shares.values()),
    str({k: round(100 * v, 1) for k, v in shares.items()}),
)

iuk_top25 = next(
    r for r in payload["pn_concentration"] if r["distributor_code"] == "IUK"
).get("std_top25_consumables_qty_share")
ok(
    "IUK top25 consumables qty high",
    iuk_top25 is not None and iuk_top25 > 0.2,
    f"{100 * (iuk_top25 or 0):.1f}%",
)

oil = next(x for x in payload["pms_expected_vs_actual"] if x["pms_category"] == "oil_filter")
air = next(x for x in payload["pms_expected_vs_actual"] if x["pms_category"] == "air_filter")
# air expected ~ half oil for same DB (air factor 0.5)
ok(
    "PMS air ~0.5 oil expected ITUK",
    abs((air["ITUK_expected"] or 0) / (oil["ITUK_expected"] or 1) - 0.5) < 0.02,
    f"oil={oil['ITUK_expected']} air={air['ITUK_expected']}",
)
ok(
    "IUK oil expected = UIO * 1.0 LCV",
    abs((oil["IUK_expected"] or 0) - 47783) < 1,
    str(oil["IUK_expected"]),
)

iuk_gps = next(r for r in core["gps"] if r["distributor_code"] == "IUK")
ok("IUK gps channel LCV", iuk_gps.get("uio_channel") == "LCV")

# EUR ranking order stable; qty inflation still gated
ok(
    "rank orders comparable",
    [r["distributor_code"] for r in core["rank"]]
    == [r["distributor_code"] for r in overall["rank"]],
    "same order (EUR ranking not bolt-driven); qty top25 still consumables-heavy",
)

failed = [c for c in checks if not c[0]]
print("---")
print(f"{len(checks)-len(failed)}/{len(checks)} passed")
raise SystemExit(1 if failed else 0)
