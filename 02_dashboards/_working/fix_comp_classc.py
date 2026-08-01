"""Collapse duplicated Class C Autodoc tables + add stale banner."""
from pathlib import Path
import re

p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\ISZE_Competitiveness_Dashboard.html")
t = p.read_text(encoding="utf-8")
pat = re.compile(
    r"<div class='src-note' style='margin-top:12px'><strong>Class C · Autodoc &lt; 75% PR00</strong>.*?</table></div>",
    re.S,
)
matches = list(pat.finditer(t))
print("Class C blocks found:", len(matches))
if len(matches) <= 1:
    print("nothing to collapse")
else:
    first = matches[0].group(0)
    banner = (
        "<div style='margin:14px 0 8px;padding:12px 14px;border-left:4px solid #B45309;"
        "background:#FEF8F0;color:#7C2D12;font-size:13px;line-height:1.45'>"
        "<strong>Autodoc Class C scrape is frozen</strong> (Cloudflare-retired). "
        "Min prices of €2.34 and 0% ratios are not usable for decisions — "
        "use the heatmap and Live Scraper Intel (KS) instead. Table kept for archive only."
        "</div>"
    )
    # remove all, insert banner+first once after first match position of first
    t2 = pat.sub("", t)
    # insert after hdr-sub competitiveness area — find first leftover marker near heatmap
    # Put after the first occurrence of "COMPARE VS" block end or after legend — simpler: after opening heatmap page
    anchor = "<!-- CLASS_C_ARCHIVE -->"
    if anchor not in t2:
        # place before closing of heatmap page if possible
        # Find 'page-heatmap' section end isn't easy; insert where first block was
        insert_at = matches[0].start()
        # After removals, positions shift — use a stable nearby string
        marker = "<div class='src-note' style='margin-top:12px'><strong>Class C"
        # Already removed. Insert after IAM scrape note in hdr-sub is wrong.
        # Insert right before Live Scraper tab page
        needle = '<div class="tab-page" id="page-scraper">'
        idx = t2.find(needle)
        if idx < 0:
            raise SystemExit("page-scraper not found")
        # Prefer keep archive on heatmap page: find page-heatmap
        hm = t2.find('id="page-heatmap"')
        # find a spot: after legend or after first tbl-wrap of segments
        spot = t2.find("<!-- END_HEATMAP_MAIN -->")
        if spot < 0:
            # insert just before page-scraper, still visible only if we put inside heatmap
            # Find end of page-heatmap
            # Look for id="page-heatmap" ... next tab-page
            m = re.search(r'(id="page-heatmap"[\s\S]*?)(<div class="tab-page" id="page-scraper">)', t2)
            if not m:
                raise SystemExit("heatmap page bounds not found")
            block = banner + first
            t2 = t2[: m.start(2)] + block + t2[m.start(2) :]
        else:
            t2 = t2[:spot] + banner + first + t2[spot:]
    p.write_text(t2, encoding="utf-8")
    left = len(pat.findall(t2))
    print("remaining Class C blocks:", left)
