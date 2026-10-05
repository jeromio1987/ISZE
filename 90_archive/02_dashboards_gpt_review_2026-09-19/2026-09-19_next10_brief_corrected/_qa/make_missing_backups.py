"""Create the missing .bak_pre_defectfix_20260919 for files 04 and 07 by reversing the single
badge string that was the only edit to each. Then verify the reconstructed bytes against the
SHA-256 recorded in FROZEN_BASE.md, which proves the reconstruction is byte-exact and that the
edit really was a single string.
"""
import hashlib, json, os

BASE = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected"
SUF = ".bak_pre_defectfix_20260919"

EXPECT = {
    "04_ISZE_AIM_Classification_Paper.html": (
        "B305CE3238AEE0F2372E3D43E131DDDDBC85D412C94F6E07A2C0AA49FFBEF565", 290918,
        "<b>Data status</b> Data verification 153 pass / 1 warn / 0 fail \u00b7 2026-09-19 13:00 UTC</div>",
        "<b>Data status</b> Data verification 143 pass / 0 warn / 0 fail \u00b7 2026-09-18 20:22 UTC</div>",
    ),
    "07_ISZE_Pricing_Revision_AIM_Source.html": (
        "7879C4A64FC32F5759B6E7D1F383AE6DA6279426FFA7AE9148DF77D3A50590C5", 6607203,
        "<b>Data status</b> Extract generated 2026-09-18; data verification 153 pass / 1 warn / 0 fail \u00b7 2026-09-19 13:00 UTC</div>",
        "<b>Data status</b> Extract generated 2026-09-18; data verification 143 pass / 0 warn / 0 fail</div>",
    ),
}

for fn, (sha, nbytes, new_s, old_s) in EXPECT.items():
    p = os.path.join(BASE, fn)
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(new_s) == 1, (fn, "new string count", t.count(new_s))
    reverted = t.replace(new_s, old_s)
    raw = reverted.encode("utf-8")
    got = hashlib.sha256(raw).hexdigest().upper()
    print(f"{fn}")
    print(f"   reverted bytes {len(raw)} (expected {nbytes})  match={len(raw)==nbytes}")
    print(f"   reverted sha   {got}")
    print(f"   frozen  sha    {sha}   match={got==sha}")
    if got != sha or len(raw) != nbytes:
        raise SystemExit("REFUSING to write backup: reconstruction does not match the frozen base")
    with open(p + SUF, "w", encoding="utf-8", newline="") as f:
        f.write(reverted)
    print("   backup written:", os.path.basename(p) + SUF)
