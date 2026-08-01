from pathlib import Path
import re

sales = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html").read_text(encoding="utf-8")
since_path = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\since_2026-06-01\Dealer_Sellout_AIM_GPS_ITUK_UTI_2025.html")
since = since_path.read_text(encoding="utf-8")
since2 = since.replace(
    '<canvas id="chartMix" height="260"></canvas>',
    '<div style="height:280px"><canvas id="chartMix"></canvas></div>',
)
since2 = since2.replace(
    '<canvas id="chartPms" height="260"></canvas>',
    '<div style="height:280px"><canvas id="chartPms"></canvas></div>',
)
m = re.search(r"(<script>\s*function initCharts\(\)[\s\S]*?</script>)", sales)
m2 = re.search(r"(<script>\s*function initCharts\(\)[\s\S]*?</script>)", since2)
if not m or not m2:
    raise SystemExit(f"sync failed sales={bool(m)} since={bool(m2)}")
since2 = since2[: m2.start()] + m.group(1) + since2[m2.end() :]
since_path.write_text(since2, encoding="utf-8")
print("since_ sellout charts synced")
