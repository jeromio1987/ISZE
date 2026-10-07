"""Compare the constructed panel against the consolidated KPI master workbook.

Read-only inputs:
  01_data/90_INBOX/_kpi_panel_20261007/kpi_panel.csv   (primary submissions)
  01_data/11_planning/KPI Master File august 2026.xlsx (sheet 'Parts Handling')

For each master distributor x metric, the panel is reduced to the latest
primary submission for July 2026. Writes:
  master_vs_panel.csv   (one row per distributor x metric, both values, verdict)
  master_vs_panel.md    (readable summary)
"""
from __future__ import annotations

import csv
import re
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")
import openpyxl  # noqa: E402

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_kpi_panel_20261007")
MASTER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\11_planning\KPI Master File august 2026.xlsx")
PANEL = OUT / "kpi_panel.csv"
JUL = "2026-07"

# block title cell, header row, first/last data row, July-26 column (AC=29)
BLOCKS = {
    "Days of Parts in Stock": dict(title=1, hdr=3, a=4, b=25, col=29),
    "First Fill Rate": dict(title=28, hdr=30, a=31, b=52, col=29),
    "Back Order Lines": dict(title=55, hdr=57, a=58, b=79, col=29),
    "Parts Sales DB to DLR": dict(title=82, hdr=84, a=85, b=107, col=29),
}
PANEL_METRIC = {
    "Days of Parts in Stock": "Days or Months of Parts in Stock (MOS)",
    "First Fill Rate": "First Fill Rate",
    "Back Order Lines": "Back Order Lines",
    "Parts Sales DB to DLR": "Parts Sales DB to DLR",
}
# master name -> panel distributor name(s)
# NOTE: the master's row labelled "Imotors" carries Portugal's numbers
# (A7/A34 match NunoMachado's Portugal April-July exactly), so it maps to Portugal.
MAP = {
    "AIOS": ["AIOS"], "BL ehf": ["BL"], "GasanZammit": ["Malta"],
    "Imotors": ["Portugal"], "IBX (BENELUX)": ["IBX"],
    "IBX (BE LUX)": ["IBX"], "IBX (NL)": ["Isuzu OE / Netherlands"],
    "IMF ( Finland )": ["Finland & Baltics"], "IMF": ["Finland & Baltics"],
    "ISD": ["ISD"], "Isuzu Danmark": ["Denmark"], "Isuzu Ireland": ["Isuzu Ireland"],
    "Isuzu Polska": ["Isuzu Polska"], "Isuzu Rom Auto": ["Romania"],
    "Isuzu Sverige": ["Isuzu Nordic (IM Nordic)"], "ITUK": ["ITUK"], "IUK": ["IUK"],
    "KIMA": ["KIMA"], "Loutsios Group": ["Loutsios"], "MIDI": ["MIDI"],
    "Petros Petropoulos": ["Greece"], "RSA": ["RSA"], "UMI": ["UMI"],
    "UTI": ["UTI"], "WAE": ["WAE"],
}


def norm(v) -> str:
    return "" if v is None else str(v).strip().replace("\xa0", "").replace(" ", "")


def to_num(s: str):
    s0 = s
    s = s.replace("€", "").replace("\xa0", "").replace(" ", "")
    if not s or s.upper() in ("N/D", "N/A", "NA", "-", "--", "ISZE"):
        return None
    scale = 1.0
    if re.search(r"(?i)k\s*euro|keuro", s0):
        scale = 1000.0
    s = re.sub(r"(?i)(days|day|months?|items?|pcs\.?|eur|k\s*euro|keuro)", "", s).strip()
    pct = s.endswith("%")
    s = s.rstrip("%").strip()
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s) and not s.startswith("0"):
        s = s.replace(".", "")
    try:
        val = float(s) * scale
    except ValueError:
        return None
    if pct and abs(val) > 1.5:
        val /= 100.0
    return val


def leading_int(s: str):
    """Leading integer of a mixed text value like '262 items / 70 K Euro'."""
    m = re.match(r"\s*(\d[\d.,]*)", s)
    if not m:
        return None
    return to_num(m.group(1))


def main() -> int:
    ws = openpyxl.load_workbook(MASTER, data_only=True)["Parts Handling"]

    master_raw, master_num = {}, {}
    for block, cfg in BLOCKS.items():
        for r in range(cfg["a"], cfg["b"] + 1):
            d = ws.cell(r, 1).value
            if not d:
                continue
            v = ws.cell(r, cfg["col"]).value
            master_raw[(block, str(d).strip())] = norm(v)
            master_num[(block, str(d).strip())] = to_num(norm(v))

    panel = list(csv.DictReader(PANEL.open(encoding="utf-8")))
    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in panel:
        if row["period"] == JUL:
            by_key[(row["metric"], row["distributor"])].append(row)

    out = []
    for block, cfg in BLOCKS.items():
        pmetric = PANEL_METRIC[block]
        for mdist, pnames in MAP.items():
            key = (block, mdist)
            if key not in master_raw:
                continue
            mraw = master_raw[key]
            mnum = master_num[key]
            rows = []
            for pn in pnames:
                rows.extend(by_key.get((pmetric, pn), []))
            if not rows:
                out.append(dict(metric=block, distributor=mdist, panel_name=";".join(pnames),
                                master_value=mraw, panel_value="",
                                verdict="NOT SUBMITTED in primary files", sources=""))
                continue
            # keep only the latest submission per (source file)
            rows.sort(key=lambda r: r["report_month_source"])
            latest_src = rows[-1]["report_month_source"]
            latest = [r for r in rows if r["report_month_source"] == latest_src]
            vals = sorted({norm(r["value"]) for r in latest})
            srcs = sorted({r["source_file"] for r in latest})
            pv = " | ".join(vals)
            nums = [to_num(v) for v in vals]
            if any(n is None for n in nums):
                nums = [leading_int(v) for v in vals]
            if len(nums) > 1 and all(n is not None for n in nums) \
                    and max(nums) - min(nums) <= 1e-6:
                nums = nums[:1]          # same value written two ways
            pnum = nums[0] if len(nums) == 1 else None
            if mnum is None and pnum is None:
                verdict = "both non-numeric"
            elif mnum is None:
                verdict = "MASTER BLANK/ND - primary has a value"
            elif pnum is None:
                verdict = ("SOURCE CONFLICT" if len(nums) > 1
                           else "primary is text - master has a number")
            elif abs(mnum - pnum) <= max(0.005, abs(pnum) * 0.005):
                verdict = "agree"
            elif block == "Days of Parts in Stock" and pnum and 28 <= mnum / pnum <= 32:
                verdict = "UNIT DIFF: master in days, primary in months"
            elif block == "Days of Parts in Stock" and pnum and abs(mnum - pnum) <= 1:
                verdict = ("two rows in one sheet: monthly MOS vs annual days "
                           "(same number)")
            else:
                verdict = "DISAGREE"
            out.append(dict(metric=block, distributor=mdist, panel_name=";".join(pnames),
                            master_value=mraw, panel_value=pv, verdict=verdict,
                            sources="; ".join(srcs),
                            panel_report_date=latest_src))

    cols = ["metric", "distributor", "panel_name", "master_value", "panel_value",
            "verdict", "panel_report_date", "sources"]
    with (OUT / "master_vs_panel.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)

    from collections import Counter
    c = Counter(r["verdict"] for r in out)
    lines = ["# Consolidated master (Jul-2026) vs primary submissions", ""]
    lines.append("## Master blocks found in `Parts Handling`")
    for block, cfg in BLOCKS.items():
        title = ws.cell(cfg["title"], 1).value
        hdr = [ws.cell(cfg["hdr"], cc).value for cc in range(1, 5)]
        lines.append(f"- `{block}`: title A{cfg['title']}={title!r}; header row {cfg['hdr']} "
                     f"({hdr}); data rows {cfg['a']}-{cfg['b']}; July-26 = column AC")
    lines.append("")
    lines.append("## Verdict counts")
    for k, v in c.most_common():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Every non-agreement")
    lines.append("| metric | master name | master Jul-26 | primary Jul-26 | verdict |")
    lines.append("|---|---|---|---|---|")
    for r in out:
        if r["verdict"] != "agree":
            lines.append(f"| {r['metric']} | {r['distributor']} | {r['master_value'] or '-'} "
                         f"| {r['panel_value'] or '-'} | {r['verdict']} |")
    (OUT / "master_vs_panel.md").write_text("\n".join(lines), encoding="utf-8")

    print("comparisons:", len(out), "| verdicts:", dict(c))
    for r in out:
        if r["verdict"] != "agree":
            print(f"  {r['metric']:24s}|{r['distributor']:18s}| m={r['master_value']!r:18} "
                  f"p={r['panel_value']!r:26} | {r['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
