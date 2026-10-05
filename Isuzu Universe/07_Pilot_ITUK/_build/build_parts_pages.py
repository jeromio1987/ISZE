"""Build one self-contained parts page per ITUK pilot-side dealer."""
from __future__ import annotations

import hashlib
import html
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ISZE = Path(__file__).resolve().parents[3]
PAGES = ROOT / "pages"
BUILD = Path(__file__).resolve().parent

sys.path.insert(0, str(BUILD))
sys.path.insert(0, str(ISZE / "03_analytics" / "Isuzu" / "prism"))
sys.path.insert(0, str(ISZE / "01_data" / "91_build"))

from modules.dealer_sales_loader import normalize_pn  # noqa: E402
from db_dlr_commercial_common import STREET_FACTOR, _load_pr00_lookup  # noqa: E402
import pilot_dealers as pd_dealers  # noqa: E402

SALES_PATH = ISZE / "01_data" / "00_derived" / "dealer_sellout_long_ITUK_CY2025.csv"
AIM_PATH = ISZE / "01_data" / "00_derived" / "_releases" / "aim_pn_classification_release_2026-10-04.csv"
BVP_PATH = ISZE / "01_data" / "00_derived" / "bvp_pn_dimension.csv"
PR00_PATH = ISZE / "01_data" / "00_derived" / "pricing_pr00_ie40.parquet"
LOADER_PATH = ISZE / "01_data" / "91_build" / "db_dlr_commercial_common.py"
NORM_PATH = ISZE / "03_analytics" / "Isuzu" / "prism" / "modules" / "dealer_sales_loader.py"
PILOT_PATH = pd_dealers.PILOT_CSV

INPUT_HASH_PREFIXES = {
    "pilot_pairs_proposal.csv": "908c5a5259622d0d",
    "dealer_sellout_long_ITUK_CY2025.csv": "df0764a2d9d11258",
    "aim_pn_classification_release_2026-10-04.csv": "8aad884f49db1a49",
    "pricing_pr00_ie40.parquet": "95d83957e7b15f9a",
    "bvp_pn_dimension.csv": "23f6652dfe9f06c3",
    "db_dlr_commercial_common.py": "d569f7fe128adaa7",
    "dealer_sales_loader.py": "d188f32fb7b13ea1",
}

MONTHS = [f"2025-{m:02d}" for m in range(1, 13)]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
UNC = "Not yet classified"
UNC_KEYS = {"", "unknown", "unknown review"}


def sha256_full(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def family_l1(raw: str | None) -> str:
    s = (raw or "").strip()
    if s.lower() in UNC_KEYS:
        return UNC
    return s


def is_unc_path(l1: str, l2: str, l3: str) -> bool:
    return l1 == UNC


def load_classification() -> pd.DataFrame:
    df = pd.read_csv(AIM_PATH, dtype=str, keep_default_na=False)
    df["key"] = df["part_number"].map(normalize_pn)
    df = df[df["key"].notna()].copy()
    df = df.drop_duplicates("key", keep="first")
    return df.set_index("key")


def load_bvp_keys() -> set[str]:
    df = pd.read_csv(BVP_PATH, dtype=str)
    df = df[df["line_type"].astype(str).str.lower() == "bvp"].copy()
    keys = set()
    for pn in df["part_number"]:
        k = normalize_pn(pn)
        if k:
            keys.add(k)
    return keys


def fmt_int(n: float | int) -> str:
    return f"{int(round(n)):,}"


def fmt_eur_whole(n: float) -> str:
    return f"€{int(round(n)):,}"


def fmt_share(n: float) -> str:
    return f"{n * 100:.1f}%"


def tip(text: str, tip_html: str) -> str:
    return (
        f'<span class="kpi-tip" tabindex="0">{html.escape(text)}'
        f'<span class="tip">{tip_html}</span></span>'
    )


def build_svg_bars(family_rows: list[tuple[str, float, float]]) -> str:
    """family_rows: (name, value_eur, net_units) already ordered with UNC last."""
    if not family_rows:
        return '<p class="muted">No family totals to chart.</p>'
    max_v = max((v for _, v, _ in family_rows), default=0.0) or 1.0
    width = 720
    bar_h = 22
    gap = 10
    label_w = 200
    chart_w = width - label_w - 120
    height = len(family_rows) * (bar_h + gap) + 8
    parts = [
        f'<svg class="fam-chart" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Top-level families by value">'
    ]
    for i, (name, val, units) in enumerate(family_rows):
        y = 4 + i * (bar_h + gap)
        bw = chart_w * (val / max_v)
        parts.append(
            f'<text x="0" y="{y + bar_h * 0.72}" class="bar-label">'
            f"{html.escape(name)}</text>"
        )
        parts.append(
            f'<rect x="{label_w}" y="{y}" width="{bw:.1f}" height="{bar_h}" '
            f'rx="2" class="bar"/>'
        )
        parts.append(
            f'<text x="{label_w + bw + 8:.1f}" y="{y + bar_h * 0.72}" class="bar-val">'
            f"{fmt_eur_whole(val)} · {fmt_int(units)} units</text>"
        )
    parts.append("</svg>")
    return "\n".join(parts)


def render_page(dealer: dict, totals: dict, tree: dict, pn_rows: list[dict]) -> str:
    page_name = str(dealer["page_name"])
    no_price = int(totals["units_without_list_price"])
    value_tip = (
        "Each unit valued at the reference dealer price from the 2026 Isuzu price list; "
        "a reference, not your invoice; returns deducted; "
        f"{fmt_int(no_price)} units have no list price and carry no value."
    )
    bv_share = (
        totals["best_value_units"] / totals["net_units"]
        if totals["net_units"]
        else 0.0
    )

    # family order: by value desc, UNC last
    fam_items = []
    unc_item = None
    for l1, node in tree.items():
        item = (l1, node["value"], node["net"])
        if l1 == UNC:
            unc_item = item
        else:
            fam_items.append(item)
    fam_items.sort(key=lambda x: -x[1])
    if unc_item is not None:
        fam_items.append(unc_item)

    details_html = []
    for l1, _, _ in fam_items:
        l1_node = tree[l1]
        l2_items = sorted(
            ((k, v) for k, v in l1_node["children"].items()),
            key=lambda kv: (-kv[1]["value"], kv[0] == UNC, kv[0]),
        )
        l2_blocks = []
        for l2, l2_node in l2_items:
            l3_items = sorted(
                ((k, v) for k, v in l2_node["children"].items()),
                key=lambda kv: (-kv[1]["value"], kv[0] == UNC, kv[0]),
            )
            l3_blocks = []
            for l3, l3_node in l3_items:
                rows = []
                for pn in sorted(l3_node["parts"], key=lambda r: (-abs(r["net"]), r["pn_display"])):
                    month_cells = "".join(
                        f"<td>{fmt_int(pn['months'][m]) if pn['months'][m] else '—'}</td>"
                        for m in MONTHS
                    )
                    first = pn["first_month"] or "—"
                    last = pn["last_month"] or "—"
                    if first != "—" and first.startswith("2025-"):
                        first = MONTH_LABELS[int(first[5:7]) - 1]
                    if last != "—" and last.startswith("2025-"):
                        last = MONTH_LABELS[int(last[5:7]) - 1]
                    rows.append(
                        "<tr class=\"pn\">"
                        f"<td class=\"pn-code\">{html.escape(pn['pn_display'])}</td>"
                        f"<td>{html.escape(pn['description'])}</td>"
                        f"<td>{html.escape(pn['line'])}</td>"
                        f"<td class=\"num\">{fmt_int(pn['bought'])}</td>"
                        f"<td class=\"num\">{fmt_int(pn['returned'])}</td>"
                        f"<td class=\"num\">{fmt_int(pn['net'])}</td>"
                        f"<td class=\"num\">{fmt_eur_whole(pn['value']) if pn['has_price'] else '—'}</td>"
                        f"{month_cells}"
                        f"<td>{first}</td><td>{last}</td>"
                        "</tr>"
                    )
                table = (
                    '<div class="table-wrap"><table><thead><tr>'
                    "<th>Part number</th><th>Description</th><th>Line</th>"
                    "<th>Bought</th><th>Returned</th><th>Net</th><th>Value</th>"
                    + "".join(f"<th>{lab}</th>" for lab in MONTH_LABELS)
                    + "<th>First</th><th>Last</th>"
                    "</tr></thead><tbody>"
                    + "".join(rows)
                    + "</tbody></table></div>"
                )
                l3_blocks.append(
                    "<details class=\"lvl3\">"
                    f"<summary>{html.escape(l3)} "
                    f"<span class=\"sum\">{fmt_eur_whole(l3_node['value'])} · "
                    f"{fmt_int(l3_node['net'])} net units (returns deducted)</span></summary>"
                    f"{table}</details>"
                )
            l2_blocks.append(
                "<details class=\"lvl2\">"
                f"<summary>{html.escape(l2)} "
                f"<span class=\"sum\">{fmt_eur_whole(l2_node['value'])} · "
                f"{fmt_int(l2_node['net'])} net units (returns deducted)</span></summary>"
                + "".join(l3_blocks)
                + "</details>"
            )
        details_html.append(
            "<details class=\"lvl1\" open>"
            f"<summary>{html.escape(l1)} "
            f"<span class=\"sum\">{fmt_eur_whole(l1_node['value'])} · "
            f"{fmt_int(l1_node['net'])} net units (returns deducted)</span></summary>"
            + "".join(l2_blocks)
            + "</details>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Parts bought from Isuzu Truck UK in 2025 — {html.escape(page_name)}</title>
<style>
:root {{
  --navy:#15233c; --paper:#f7f4ee; --ink:#222; --terra:#c0552d; --line:#d5cfc4;
}}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; padding:0; background:var(--paper); color:var(--ink);
  font-family: Georgia, "Times New Roman", serif; }}
body {{ padding:24px 20px 64px; max-width:1100px; margin:0 auto; overflow-x:hidden; }}
h1 {{ font-size:1.65rem; color:var(--navy); margin:0 0 4px; line-height:1.25; }}
h2 {{ font-size:1.15rem; color:var(--navy); margin:0 0 12px; }}
.dealer {{ font-size:1.2rem; color:var(--navy); margin:0 0 8px; }}
.source {{ color:#445; font-size:0.95rem; margin:0 0 22px; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:0 0 28px; }}
.kpi {{ background:#fff; border:1px solid var(--line); border-left:4px solid var(--terra);
  padding:14px 14px 12px; min-width:0; }}
.kpi .label {{ font-size:0.78rem; text-transform:uppercase; letter-spacing:0.04em; color:#445; margin:0 0 6px; }}
.kpi .val {{ font-size:1.35rem; color:var(--navy); font-weight:700; }}
.kpi-tip {{ position:relative; cursor:help; border-bottom:1px dotted var(--terra); }}
.kpi-tip .tip {{
  display:none; position:absolute; left:0; top:calc(100% + 8px); z-index:20;
  width:min(320px, 80vw); background:var(--navy); color:var(--paper);
  padding:10px 12px; font-size:0.82rem; line-height:1.35; border-top:3px solid var(--terra);
  box-shadow:0 8px 18px rgba(21,35,60,0.25); font-weight:400;
}}
.kpi-tip:hover .tip, .kpi-tip:focus .tip {{ display:block; }}
.chart-box {{ background:#fff; border:1px solid var(--line); padding:16px 16px 8px; margin:0 0 28px; }}
.fam-chart {{ width:100%; height:auto; display:block; }}
.bar {{ fill:var(--navy); }}
.bar-label {{ font-size:12px; fill:var(--navy); font-family:Georgia,serif; }}
.bar-val {{ font-size:11px; fill:#445; font-family:Georgia,serif; }}
details {{ border:1px solid var(--line); background:#fff; margin:0 0 8px; padding:0; }}
summary {{ cursor:pointer; padding:10px 12px; color:var(--navy); font-weight:700; list-style:none; }}
summary::-webkit-details-marker {{ display:none; }}
summary::before {{ content:"+ "; color:var(--terra); }}
details[open] > summary::before {{ content:"− "; }}
.sum {{ font-weight:400; color:#445; font-size:0.9rem; }}
.lvl2, .lvl3 {{ margin:0 10px 8px; border-color:#e4ddd0; }}
.table-wrap {{ overflow-x:auto; max-height:420px; overflow-y:auto; margin:0 10px 12px; border:1px solid var(--line); }}
table {{ border-collapse:collapse; width:100%; font-size:0.82rem; background:#fff; }}
th, td {{ border-bottom:1px solid var(--line); padding:6px 8px; text-align:left; white-space:nowrap; color:var(--ink); }}
th {{ background:var(--navy); color:var(--paper); position:sticky; top:0; z-index:1; }}
td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
td.pn-code {{ font-family: Consolas, "Courier New", monospace; }}
.limits {{ background:#fff; border:1px solid var(--line); padding:16px 18px; margin-top:28px; }}
.limits ul {{ margin:8px 0 0; padding-left:1.2rem; }}
.limits li {{ margin:4px 0; }}
.note {{ font-size:0.88rem; color:#445; margin:8px 0 0; }}
@media (max-width:700px) {{
  .kpis {{ grid-template-columns:1fr 1fr; }}
  body {{ padding:16px 12px 48px; }}
  h1 {{ font-size:1.35rem; }}
}}
@media (max-width:420px) {{
  .kpis {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body>
<header>
  <h1>Parts bought from Isuzu Truck UK in 2025</h1>
  <p class="dealer">{html.escape(page_name)}</p>
  <p class="source">Isuzu Truck UK sales to this dealer, by part number and month, January to December 2025.</p>
</header>

<section class="kpis" aria-label="Summary figures">
  <div class="kpi"><p class="label">Net units</p><p class="val">{tip(fmt_int(totals['net_units']), 'Purchases minus returns.')}</p></div>
  <div class="kpi"><p class="label">Part numbers bought</p><p class="val">{fmt_int(totals['part_numbers'])}</p></div>
  <div class="kpi"><p class="label">Value at reference dealer price</p><p class="val">{tip(fmt_eur_whole(totals['value_eur']), html.escape(value_tip))}</p></div>
  <div class="kpi"><p class="label">Best Value share of net units</p><p class="val">{fmt_share(bv_share)}</p></div>
</section>
<p class="note">Wherever a net figure is shown, returns are deducted.</p>

<section class="chart-box">
  <h2>Families by value</h2>
  {build_svg_bars(fam_items)}
</section>

<section aria-label="Family drill-down">
  <h2>Parts by family</h2>
  {''.join(details_html)}
</section>

<section class="limits">
  <h2>What this page does not show</h2>
  <ul>
    <li>No truck count, so no capture rate.</li>
    <li>No comparison with other dealers.</li>
    <li>Reference prices, not invoices.</li>
    <li>2025 only.</li>
  </ul>
</section>
</body>
</html>
"""


def empty_node() -> dict:
    return {"net": 0.0, "value": 0.0, "children": {}, "parts": []}


def ensure_path(tree: dict, l1: str, l2: str, l3: str) -> dict:
    if l1 not in tree:
        tree[l1] = empty_node()
    if l2 not in tree[l1]["children"]:
        tree[l1]["children"][l2] = empty_node()
    if l3 not in tree[l1]["children"][l2]["children"]:
        tree[l1]["children"][l2]["children"][l3] = empty_node()
    return tree[l1]["children"][l2]["children"][l3]


def main() -> int:
    # hash check
    paths = {
        "pilot_pairs_proposal.csv": PILOT_PATH,
        "dealer_sellout_long_ITUK_CY2025.csv": SALES_PATH,
        "aim_pn_classification_release_2026-10-04.csv": AIM_PATH,
        "pricing_pr00_ie40.parquet": PR00_PATH,
        "bvp_pn_dimension.csv": BVP_PATH,
        "db_dlr_commercial_common.py": LOADER_PATH,
        "dealer_sales_loader.py": NORM_PATH,
    }
    input_hashes = {}
    for name, path in paths.items():
        full = sha256_full(path)
        prefix = INPUT_HASH_PREFIXES[name]
        if not full.startswith(prefix):
            raise SystemExit(f"hash mismatch {name}: {full[:16]} != {prefix}")
        input_hashes[name] = full

    pd_dealers.assert_pilot_design()
    class_df = load_classification()
    bvp_keys = load_bvp_keys()
    price_lookup = _load_pr00_lookup()

    sales = pd.read_csv(SALES_PATH, dtype={"part_number": str})
    sales = sales[sales["period_grain"].astype(str) == "month"].copy()
    sales["qty"] = pd.to_numeric(sales["qty"], errors="coerce").fillna(0.0)
    sales["period"] = sales["period"].astype(str)

    PAGES.mkdir(parents=True, exist_ok=True)
    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "input_hashes": input_hashes,
        "dealers": [],
    }

    for dealer in pd_dealers.DEALERS:
        dsales = sales[sales["dealer_name"] == dealer["sales_name"]].copy()
        if dsales.empty:
            raise SystemExit(f"no sales rows for {dealer['sales_name']}")

        # aggregate by display part number + key
        dsales["key"] = dsales["part_number"].map(normalize_pn)
        # keep rows even if key is None? Brief says show PN as in sales file.
        # For pricing/class need key; without key treat as unclassified no price.
        pn_agg: dict[str, dict] = {}
        for _, row in dsales.iterrows():
            display = str(row["part_number"]) if pd.notna(row["part_number"]) else ""
            key = row["key"] if pd.notna(row["key"]) else None
            # use display as bucket id plus key
            bucket = display
            if bucket not in pn_agg:
                pn_agg[bucket] = {
                    "pn_display": display,
                    "key": key,
                    "bought": 0.0,
                    "returned": 0.0,
                    "months": {m: 0.0 for m in MONTHS},
                }
            qty = float(row["qty"])
            period = str(row["period"])
            if qty > 0:
                pn_agg[bucket]["bought"] += qty
            elif qty < 0:
                pn_agg[bucket]["returned"] += -qty
            if period in pn_agg[bucket]["months"]:
                pn_agg[bucket]["months"][period] += qty

        tree: dict = {}
        part_rows: list[dict] = []
        net_units = 0.0
        bought_total = 0.0
        returned_total = 0.0
        value_total = 0.0
        no_price_units = 0.0
        bv_units = 0.0
        unc_units = 0.0

        for bucket, agg in pn_agg.items():
            key = agg["key"]
            bought = agg["bought"]
            returned = agg["returned"]
            net = bought - returned
            months = agg["months"]
            # first/last month with a purchase (qty > 0 in that month from raw? or net?)
            # Brief: "first and last month with a purchase" -> positive activity
            active = [m for m in MONTHS if months[m] != 0]
            # prefer months with positive bought contribution: use nonzero months
            first_m = next((m for m in MONTHS if months[m] > 0), None)
            last_m = next((m for m in reversed(MONTHS) if months[m] > 0), None)
            if first_m is None and active:
                first_m = active[0]
                last_m = active[-1]

            # classification
            if key is not None and key in class_df.index:
                crow = class_df.loc[key]
                raw_l1 = str(crow["aim_l1_fixed"])
                raw_l2 = str(crow["aim_l2_fixed"])
                raw_l3 = str(crow["aim_l3_fixed"])
                desc = str(crow["description_norm"] or "").strip() or "-"
            else:
                raw_l1 = raw_l2 = raw_l3 = ""
                desc = "-"

            l1 = family_l1(raw_l1)
            if l1 == UNC:
                l2 = UNC
                l3 = UNC
            else:
                l2 = family_l1(raw_l2) if family_l1(raw_l2) != UNC else "Unspecified"
                l3 = family_l1(raw_l3) if family_l1(raw_l3) != UNC else "Unspecified"
                # if L2/L3 blank but L1 ok - family_l1("") -> UNC; use Unspecified instead for sublevels
                if (raw_l2 or "").strip().lower() in UNC_KEYS:
                    l2 = "Unspecified"
                else:
                    l2 = (raw_l2 or "").strip() or "Unspecified"
                if (raw_l3 or "").strip().lower() in UNC_KEYS:
                    l3 = "Unspecified"
                else:
                    l3 = (raw_l3 or "").strip() or "Unspecified"

            is_bv = bool(key and key in bvp_keys)
            line = "Best Value" if is_bv else "Genuine"
            unit_price = price_lookup.get(key) * STREET_FACTOR if key and key in price_lookup else None
            has_price = unit_price is not None
            value = (net * unit_price) if has_price else 0.0
            if not has_price:
                no_price_units += abs(net) if net != 0 else 0.0
                # brief: "units without a list price" - count net units? or absolute?
                # Expected table: P1 has 1 unit without list price. Use abs(net) for parts with no price that have net != 0
                # Actually if has no price, count the net units magnitude that couldn't be valued
                # Re-read: "A part with no list price gets no value, and its units are counted as units without a list price"
                # Likely sum of |net| or bought for no-price parts. Use abs(net) for consistency with value of net units.

            leaf = ensure_path(tree, l1, l2, l3)
            leaf["net"] += net
            leaf["value"] += value
            tree[l1]["net"] += net
            tree[l1]["value"] += value
            tree[l1]["children"][l2]["net"] += net
            tree[l1]["children"][l2]["value"] += value

            pn_rec = {
                "pn_display": agg["pn_display"],
                "description": desc,
                "line": line,
                "bought": bought,
                "returned": returned,
                "net": net,
                "value": value,
                "has_price": has_price,
                "months": months,
                "first_month": first_m,
                "last_month": last_m,
            }
            leaf["parts"].append(pn_rec)
            part_rows.append(pn_rec)

            net_units += net
            bought_total += bought
            returned_total += returned
            value_total += value
            if is_bv:
                bv_units += net
            if l1 == UNC:
                unc_units += net

        totals = {
            "part_numbers": len(pn_agg),
            "bought": bought_total,
            "returned": returned_total,
            "net_units": net_units,
            "value_eur": round(value_total, 2),
            "units_without_list_price": int(round(no_price_units)),
            "best_value_units": bv_units,
            "not_yet_classified_units": unc_units,
        }

        out_dir = pd_dealers.pages_dir_for(dealer, PAGES)
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path = out_dir / "Parts_2025.html"
        html_path.write_text(render_page(dealer, totals, tree, part_rows), encoding="utf-8")
        cmd_path = out_dir / "OPEN_Parts_2025.cmd"
        cmd_path.write_bytes(b'@echo off\r\nstart "" "%~dp0Parts_2025.html"\r\n')

        manifest["dealers"].append(
            {
                "code": dealer["code"],
                "page_name": dealer["page_name"],
                "folder": out_dir.name,
                "part_numbers": totals["part_numbers"],
                "bought": int(round(totals["bought"])),
                "returned": int(round(totals["returned"])),
                "net_units": int(round(totals["net_units"])),
                "value_eur": totals["value_eur"],
                "units_without_list_price": totals["units_without_list_price"],
                "best_value_units": int(round(totals["best_value_units"])),
                "not_yet_classified_units": int(round(totals["not_yet_classified_units"])),
            }
        )
        print(
            f"{dealer['code']}: pn={totals['part_numbers']} net={totals['net_units']:.0f} "
            f"value={totals['value_eur']:.2f} bv={totals['best_value_units']:.0f} "
            f"unc={totals['not_yet_classified_units']:.0f} noprice={totals['units_without_list_price']}"
        )

    man_path = PAGES / "parts_manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {man_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())