import json, os
OUT_DIR = r"C:\Users\jerom\Desktop\claude\ISZE\Isuzu Universe\02_Atlas\DISTRIBUTOR_ONE_PAGERS_2026-09"
manifest = json.load(open(os.path.join(OUT_DIR, "_build_manifest.json"), encoding="utf-8"))
manifest = sorted(manifest, key=lambda r: r["name"])

rows = "".join(
    f'<tr><td>{r["name"]}</td><td><a href="{r["file"]}.html">HTML</a></td>'
    f'<td><a href="{r["file"]}.pdf">PDF</a></td><td class="code">{r["code"]}</td></tr>'
    for r in manifest
)

html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Distributor one-pagers -- index (internal)</title>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; margin: 20px; color: #1E2124; background: #fff; }}
h1 {{ color: #24282C; }}
.note {{ color: #6B7078; font-size: 13px; margin-bottom: 16px; }}
table {{ border-collapse: collapse; width: 100%; max-width: 700px; }}
th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #E4E5E7; }}
th {{ background: #24282C; color: #fff; }}
td.code {{ color: #B9BDC3; font-size: 11px; }}
a {{ color: #D71920; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style></head><body>
<h1>Distributor one-pagers -- index (internal)</h1>
<p class="note">Internal navigation only. Do not send this index page to a distributor -- each distributor page names only itself.
Built September 2026 from 01_data/00_derived. {len(manifest)} distributors, calendar 2025 against 2024.</p>
<table><thead><tr><th>Distributor</th><th>HTML</th><th>PDF</th><th>Internal code</th></tr></thead>
<tbody>{rows}</tbody></table>
</body></html>"""

with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(html)

with open(os.path.join(OUT_DIR, "OPEN_DISTRIBUTOR_ONE_PAGERS.cmd"), "w", encoding="utf-8") as fh:
    fh.write('@start "" "%~dp0index.html"\r\n')

print("index + cmd written,", len(manifest), "rows")
