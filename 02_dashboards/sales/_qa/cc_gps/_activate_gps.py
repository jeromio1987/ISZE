from pathlib import Path

src = Path(__file__).resolve().parents[2] / "ISZE_Aftermarket_BI_Command_Center.html"
dst = Path(__file__).with_name("gps_tab.html")
t = src.read_text(encoding="utf-8")
t = t.replace('id="panel-network" class="panel active"', 'id="panel-network" class="panel"')
t = t.replace('id="panel-gps" class="panel"', 'id="panel-gps" class="panel active"')
t = t.replace(
    '<button type="button" class="active" data-tab="network"',
    '<button type="button" data-tab="network"',
)
t = t.replace(
    '<button type="button" data-tab="gps"',
    '<button type="button" class="active" data-tab="gps"',
)
dst.write_text(t, encoding="utf-8")
print(dst)
