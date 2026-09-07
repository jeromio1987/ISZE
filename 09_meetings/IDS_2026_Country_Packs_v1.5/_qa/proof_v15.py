import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
v14 = Path(r"C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_Country_Packs_v1.4")
print("v1.4 exists", v14.is_dir(), "INDEX", (v14 / "INDEX.md").is_file())
print("v1.5 INDEX", (root / "INDEX.md").is_file())
bads = []
for html in sorted(root.glob("*/IDS_2026_dealer_compare_*.html")):
    t = html.read_text(encoding="utf-8")
    m = re.search(r"const DATA = (\{.*?\});\s*\n", t)
    if not m:
        bads.append((html.parent.name, "NO_DATA"))
        continue
    data = json.loads(m.group(1))
    c = data["countries"][0]
    pr = data["country_profiles"][c]
    n_dealers = len(data["dealers"])
    n_ex = sum(1 for d in data["dealers"] if d.get("excluded_from_average"))
    zeros_in_avg = [
        d["name"]
        for d in data["dealers"]
        if not d.get("excluded_from_average")
        and d.get("total_pct") in (0, 0.0)
    ]
    flags = {
        "v15": "v1.5" in t,
        "midi4": 'id="btn-midi4"' in t,
        "changelog": 'data-tab="changelog"' in t or "Changelog</button>" in t,
        "carto": "carto" in t.lower(),
        "apikey": "api key" in t.lower() or "apikey" in t.lower(),
        "dutch": bool(re.search(r"\b(goed|slecht)\b", t, re.I)),
        "weak": "Weak sector" in t,
        "midi_ch": "MIDI_CH" in t,
        "uti": "UTI" in t and c.startswith("Israel"),
        "leaflet": "L.map" in t and len(t) > 500_000,
        "notes": 'data-tab="notes"' in t,
        "meeting": 'id="f-meeting"' in t,
        "open": (html.parent / f"OPEN_IDS_2026_{html.parent.name}.cmd").is_file(),
    }
    pct = round(pr["total_pct"] * 100, 1) if pr.get("total_pct") is not None else None
    print(
        f"{c}: {pct}% {pr.get('avg_basis_count')} of {pr.get('dealer_count')} "
        f"excl={pr.get('excluded_from_average_count')} zeros_in_avg={len(zeros_in_avg)} {flags}"
    )
    if c == "Switzerland":
        xs = [d["name"] for d in data["dealers"] if d.get("excluded_from_average")]
        print("  CH out:", xs)
    if zeros_in_avg:
        bads.append((c, "ZEROS_IN_AVG", zeros_in_avg))
    if (
        not flags["v15"]
        or flags["midi4"]
        or flags["changelog"]
        or flags["carto"]
        or flags["apikey"]
        or flags["dutch"]
        or flags["weak"]
        or not flags["open"]
        or not flags["notes"]
        or not flags["leaflet"]
    ):
        bads.append((c, "FLAGS", {k: v for k, v in flags.items() if (k in ("midi4", "changelog", "carto", "apikey", "dutch", "weak") and v) or (k in ("v15", "open", "notes", "leaflet") and not v)}))
print("BADS", bads)
