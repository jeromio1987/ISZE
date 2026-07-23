"""UTI + ITUK PMS family study — IML v7 intervals, FY billing, cover capped at 100%."""
from __future__ import annotations

import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from uti_iml_fy_engine import (  # noqa: E402
    ALL_CATS,
    BRAKE_CATS,
    CLUTCH_CATS,
    FILTER_CATS,
    cap_pct,
    compute_uti_fy,
    family_cover,
    load_ituk_iml,
    load_sales,
)

OUT = OUT_DIR / "ITUK_UTI_PMS_Study_CappedCapture_FY_IML.html"
OUT_LEGACY = OUT_DIR / "ITUK_UTI_PMS_Study_CappedCapture_v1.html"
FY_LABEL = 2025  # FY2025 = Apr 2024 – Mar 2025

LABELS = {
    "oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
    "urea_filter": "Urea filter", "brake_pad": "Brake pad", "brake_shoe": "Brake shoe",
    "brake_rotor": "Brake rotor", "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch pressure plate", "clutch_kit": "Clutch kit",
    "clutch_booster": "Clutch booster", "release_bearing": "Release bearing",
    "pilot_bearing": "Pilot bearing",
}

BVP_MIX = {
    "suspension": (8.3, 37.0),
    "cab": (42.6, 43.6),
    "electrical": (23.0, 100.0),
}


def bar_html(label: str, true_pct: float, css: str) -> str:
    capped = min(true_pct, 100.0)
    over = ""
    if true_pct > 100.01:
        over = f'<div class="overshoot">+ ({true_pct:.1f}%)</div>'
        inner = '<span class="pct">100%</span>'
        w = 100
    else:
        inner = f'<span class="pct">{capped:.1f}%</span>'
        w = capped
    return (
        f'<div class="row"><div class="label">{label}</div>'
        f'<div class="track"><div class="bar {css}" style="width:{w:.1f}%">{inner}</div>{over}</div></div>'
    )


def build_html() -> str:
    iml = load_ituk_iml()
    iml_cat = {c["key"]: c for c in iml["categories"]}
    filt_keys = ["oil_filter", "fuel_filter", "air_filter"]

    sales = load_sales()
    uti = compute_uti_fy(FY_LABEL, sales)
    uti_c = uti["categories"]

    filt_act = sum(iml_cat[k]["actual_sales"] for k in filt_keys)
    filt_exp = sum(iml_cat[k]["expected_demand"] for k in filt_keys)
    ituk_filt_pct = filt_act / filt_exp * 100 if filt_exp else 0

    ituk_families = {
        "Filters": (min(ituk_filt_pct, 100), ituk_filt_pct),
        "Brakes": (iml_cat["brake"]["cover_pct"], iml_cat["brake"]["cover_pct"]),
        "Clutch": (iml_cat["clutch"]["cover_pct"], iml_cat["clutch"]["cover_pct"]),
    }
    uf = family_cover(uti_c, FILTER_CATS)
    ub = family_cover(uti_c, BRAKE_CATS)
    uc = family_cover(uti_c, CLUTCH_CATS)
    uti_families = {
        "Filters": (uf[0], uf[1]),
        "Brakes": (ub[0], ub[1]),
        "Clutch": (uc[0], uc[1]),
    }

    readings = {
        "Filters": (
            f"ITUK {ituk_filt_pct:.1f}% on IML · UTI {uf[1]:.1f}% FY{FY_LABEL} — "
            "both on 1.25×/yr filter schedule; UTI no longer PRISM-saturated."
        ),
        "Brakes": (
            f"ITUK {iml_cat['brake']['cover_pct']:.1f}% · UTI {ub[1]:.1f}% — "
            "IML 0.5×/yr wear; main UTI gap category."
        ),
        "Clutch": (
            f"ITUK {iml_cat['clutch']['cover_pct']:.1f}% · UTI {uc[1]:.1f}% — "
            "IML 0.5×/yr on clutch parc subset; deferred ITUK phase-one."
        ),
    }

    bars = ""
    family_rows = ""
    for fam in ("Filters", "Brakes", "Clutch"):
        ic, it = ituk_families[fam]
        ucap, utrue = uti_families[fam]
        bars += bar_html(f"{fam} — ITUK", it, "ituk")
        bars += bar_html(f"{fam} — UTI", utrue, "uti")
        family_rows += (
            f"<tr><td>{fam}</td><td>{ic:.1f}%</td><td>{it:.1f}%</td>"
            f"<td>{ucap:.1f}%</td><td>{utrue:.1f}%</td><td>{readings[fam]}</td></tr>"
        )

    sub_rows = ""
    for cat in ALL_CATS:
        label = LABELS.get(cat, cat)
        note = " <span class='iml'>(IML)</span>" if cat in filt_keys else ""
        if cat in filt_keys and cat in iml_cat:
            ic, it = iml_cat[cat]["cover_pct"], iml_cat[cat]["cover_pct"]
        else:
            ic, it = 0.0, 0.0
        if cat in uti_c:
            ucap, utrue = cap_pct(uti_c[cat]["total"]["capture"])
            ug_cap, ug_true = cap_pct(uti_c[cat]["genuine"]["capture"])
            ug = f"{ug_cap:.0f}% ({ug_true:.1f}%)" if ug_true > ug_cap else f"{ug_true:.1f}%"
            ig = ug if cat not in filt_keys else (
                f"{cap_pct(uti_c[cat]['genuine']['capture'])[0]:.0f}% "
                f"({cap_pct(uti_c[cat]['genuine']['capture'])[1]:.1f}%)"
            )
        else:
            ucap, utrue, ug, ig = 0.0, 0.0, "—", "—"
        sub_rows += (
            f"<tr><td>{label}{note}</td>"
            f"<td>{ic:.1f}%</td><td>{it:.1f}%</td><td>{ig}</td>"
            f"<td>{ucap:.1f}%</td><td>{utrue:.1f}%</td><td>{ug}</td></tr>"
        )

    bvp_html = ""
    for fam, (bi, bu) in BVP_MIX.items():
        bvp_html += (
            f'<div class="row"><div class="label">{fam.title()} — ITUK</div>'
            f'<div class="track"><div class="bar bvp-bvp" style="width:{bi}%"></div></div>'
            f'<div class="bvp-pct">{bi}% BVP</div></div>'
            f'<div class="row"><div class="label">{fam.title()} — UTI</div>'
            f'<div class="track"><div class="bar bvp-bvp" style="width:{bu}%"></div></div>'
            f'<div class="bvp-pct">{bu}% BVP</div></div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>PMS Study — ITUK vs UTI — FY{FY_LABEL} IML</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#F5F5F5; margin:0; padding:32px; color:#1A1A1A; }}
  .wrap {{ max-width: 980px; margin: 0 auto; background:#fff; border-radius:8px; padding:36px 40px; box-shadow:0 1px 4px rgba(0,0,0,.08); }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .sub {{ color:#666; font-size:13px; margin-bottom:24px; }}
  .note {{ background:#FFF4F4; border-left:4px solid #CC0E1E; padding:12px 16px; font-size:13px; margin-bottom:28px; line-height:1.5; }}
  h2 {{ font-size:15px; margin:32px 0 4px; border-bottom:2px solid #CC0E1E; padding-bottom:6px; }}
  .h2sub {{ font-size:12px; color:#777; margin-bottom:16px; }}
  .row {{ display:flex; align-items:center; gap:12px; margin:10px 0; }}
  .label {{ width:150px; font-size:13px; font-weight:600; flex-shrink:0; }}
  .track {{ flex:1; background:#EEE; border-radius:4px; height:22px; position:relative; }}
  .bar {{ height:22px; border-radius:4px; display:flex; align-items:center; min-width:2px; }}
  .bar.ituk {{ background:#1A3A5C; }}
  .bar.uti {{ background:#CC0E1E; }}
  .bar.bvp-bvp {{ background:#B08D57; }}
  .pct {{ font-size:12px; color:#fff; padding-left:8px; font-weight:600; }}
  .bvp-pct {{ font-size:12px; width:60px; }}
  .overshoot {{ position:absolute; right:-46px; top:0; font-size:11px; color:#CC0E1E; font-weight:700; line-height:22px; }}
  .legend {{ display:flex; gap:20px; font-size:12px; margin-bottom:14px; flex-wrap:wrap; }}
  .sw {{ width:12px; height:12px; border-radius:2px; display:inline-block; }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; margin-top:10px; }}
  th, td {{ text-align:left; padding:6px 10px; border-bottom:1px solid #eee; }}
  th {{ background:#1A3A5C; color:#fff; }}
  tr:nth-child(even) {{ background:#FAFAFA; }}
  .iml {{ color:#888; font-size:10px; }}
  footer {{ margin-top:28px; font-size:11px; color:#999; border-top:1px solid #eee; padding-top:10px; line-height:1.5; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>PMS Study — ITUK vs UTI — Family-level view</h1>
  <div class="sub">FY{FY_LABEL} (Apr {FY_LABEL}–Mar {FY_LABEL + 1}) · <strong>Both: IML v7 schedule</strong> · 100% addressable · cover capped at 100%</div>
  <div class="note">
    <b>Unified methodology.</b> ITUK from <code>iml_v7_ituk_cy2025.yaml</code> (CY2025 billing, IML schedule).
    <strong>UTI recalculated</strong> on the same IML intervals — oil/fuel/air <strong>1.25×/yr</strong> (40,000 km @ 50,000 km/yr),
    brake &amp; clutch <strong>0.5×/yr</strong>, <strong>100% addressable</strong>, UIO {uti['uio']:,} — billing <strong>FY{FY_LABEL}</strong>.
    No PRISM 70% haircut; no calendar-year mix.
  </div>

  <h2>Filters, Brakes, Clutch — cover %</h2>
  <div class="h2sub">Σ actual ÷ Σ expected on IML schedule. Bars capped at 100%.</div>
  <div class="legend">
    <span><i class="sw" style="background:#1A3A5C"></i> ITUK</span>
    <span><i class="sw" style="background:#CC0E1E"></i> UTI FY{FY_LABEL}</span>
  </div>
  {bars}
  <table>
    <tr><th>Family</th><th>ITUK capped</th><th>ITUK true</th><th>UTI capped</th><th>UTI true</th><th>Reading</th></tr>
    {family_rows}
  </table>

  <h2>Suspension, Cab, Electrical — BVP share %</h2>
  <div class="h2sub">Mix metric · FY{FY_LABEL} / CY2025 billing (unchanged source)</div>
  {bvp_html}

  <h2>Sub-category detail — UTI (IML + FY)</h2>
  <table>
    <tr><th>Category</th><th>ITUK</th><th>ITUK true</th><th>ITUK gen</th><th>UTI capped</th><th>UTI true</th><th>UTI genuine</th></tr>
    {sub_rows}
  </table>

  <footer>
    ITUK oil filter <strong>{iml_cat['oil_filter']['cover_pct']}%</strong> · gap <strong>€{iml['headline']['revenue_gap_eur_sum']:,}</strong>.
    UTI FY{FY_LABEL}: filters <strong>{uf[1]:.1f}%</strong>, brakes <strong>{ub[1]:.1f}%</strong>, clutch <strong>{uc[1]:.1f}%</strong>.
    Rebuild: <code>python _build/build_uti_presentation_suite.py</code>
  </footer>
</div>
</body>
</html>"""


def main() -> None:
    html = build_html()
    OUT.write_text(html, encoding="utf-8")
    OUT_LEGACY.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_LEGACY} (legacy alias)")


if __name__ == "__main__":
    main()
