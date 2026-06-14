"""
Run this once on your Windows machine to make isze_full_dashboard.html
fully self-contained (no internet needed, works via WhatsApp/email).
"""
import urllib.request, os, re

FOLDER = os.path.dirname(os.path.abspath(__file__))
DASHBOARD = os.path.join(FOLDER, 'isze_full_dashboard.html')

CDN = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js'

print("Downloading Chart.js...")
with urllib.request.urlopen(CDN) as r:
    chartjs = r.read().decode('utf-8')
print(f"Downloaded {len(chartjs):,} chars")

html = open(DASHBOARD, encoding='utf-8').read()

# Replace CDN tag with inline script
old = '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js" crossorigin="anonymous"></script>'
new = f'<script>{chartjs}</script>'
html = html.replace(old, new)

out = os.path.join(FOLDER, 'isze_full_dashboard_standalone.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = os.path.getsize(out) // 1024
print(f"Done! Saved: isze_full_dashboard_standalone.html ({size_kb} KB)")
print("Share this file — works offline, no internet needed.")
