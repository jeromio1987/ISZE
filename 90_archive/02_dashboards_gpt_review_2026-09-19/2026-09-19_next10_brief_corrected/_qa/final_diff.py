"""Exact diff of every edited file against its verified backup, so the change set is proven,
not asserted. Prints every changed line pair (bounded), and a count."""
import difflib, hashlib, os

BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
SUF = ".bak_pre_defectfix_20260919"

FROZEN = {
    "01_ISZE_Exec_Aftersales_Paper.html": "40BE6EB05307AE2216BC1A07DA344805C35501672106AB3984AE0334D036E79D",
    "02_ISZE_Leakage_Cockpit.html": "0F689A436C1A2296DEEE5DA1E88920C2708AB218D64B30F12A07BC6001A2FBEE",
    "03_Warranty_Commercial_Review.html": "90ADFD7EED34A3C05F1F4CD0D3C6B300627582AA7EA2B8A327AF57B335568B8F",
    "04_ISZE_AIM_Classification_Paper.html": "B305CE3238AEE0F2372E3D43E131DDDDBC85D412C94F6E07A2C0AA49FFBEF565",
    "07_ISZE_Pricing_Revision_AIM_Source.html": "7879C4A64FC32F5759B6E7D1F383AE6DA6279426FFA7AE9148DF77D3A50590C5",
    "10_Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html": "43F14636136347C806850B6BD3DFFE91251D71C11E06554AE945BF7320D0712B",
}

for fn, sha in FROZEN.items():
    a = open(os.path.join(BASE, fn + SUF), "rb").read()
    b = open(os.path.join(BASE, fn), "rb").read()
    ok = hashlib.sha256(a).hexdigest().upper() == sha
    la = a.decode("utf-8").split("\r\n")
    lb = b.decode("utf-8").split("\r\n")
    d = list(difflib.unified_diff(la, lb, lineterm="", n=0))
    added = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
    removed = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
    print("=" * 100)
    print(f"{fn}   backup==frozen:{ok}   +{added} / -{removed} lines   ({len(a)} -> {len(b)} bytes)")
    for x in d[2:]:
        if x.startswith(("+", "-")):
            print("   " + (x[:230] + (" ..." if len(x) > 230 else "")))
