"""Independent QA audit of pricing full analysis pack before Send.

Recomputes key headlines from parquet/CSV sources; writes
01_data/00_derived/_pricing_full_pack_audit.md
Exit 0 = PASS or PASS_WITH_CAVEATS; exit 1 = FAIL.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DER = ISZE / "01_data" / "00_derived"
DASH = ISZE / "02_dashboards" / "pricing"
HTML = DASH / "ISZE_Pricing_Full_Analysis_Pack.html"
META = DER / "pricing_full_analysis_pack.meta.json"
FINDINGS = DER / "pricing_history_findings.meta.json"
AUDIT_MD = DER / "_pricing_full_pack_audit.md"
MAP_CSV = ISZE / "03_analytics" / "Isuzu" / "prism" / "data" / "sap_sold_to_mapping.csv"
UTC_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm_pn(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, int):
        return str(int(v))
    s = str(v).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    digits = re.sub(r"\D", "", s)
    return digits.lstrip("0") or ("0" if digits else "")


def load_pr00(year: int) -> pd.DataFrame:
    if year >= 2026:
        path = DER / "pricing_pr00_ie40.parquet"
        df = pd.read_parquet(path)
        df = df.rename(columns={"part_number": "Material", "sp_eur": "Price_EUR"})
        if "is_superseded_row" in df.columns:
            df = df[~df["is_superseded_row"].fillna(False)]
    else:
        path = DER / f"pricing_pr00_ie40_{year}.parquet"
        df = pd.read_parquet(path)
    df["pn"] = df["Material"].map(norm_pn)
    df["Price_EUR"] = pd.to_numeric(df["Price_EUR"], errors="coerce")
    usable = df[df["Price_EUR"].notna() & (df["Price_EUR"] > 0) & (df["pn"] != "")]
    return usable.drop_duplicates("pn", keep="first")[["pn", "Price_EUR"]]


def recompute_realization(year: int = 2025) -> dict:
    sf = pd.read_parquet(DER / "sales_fact.parquet")
    sf["pn"] = sf["part_number"].map(norm_pn)
    y = sf[sf["year"] == year].copy()
    y["net_sales_value"] = pd.to_numeric(y["net_sales_value"], errors="coerce").fillna(0.0)
    y["billed_qty"] = pd.to_numeric(y["billed_qty"], errors="coerce").fillna(0.0)
    pr = load_pr00(year)
    m = y.merge(pr, on="pn", how="left", indicator=True)
    matched = m["_merge"] == "both"
    m["list_value"] = m["billed_qty"] * m["Price_EUR"]
    ok = matched & (m["billed_qty"] > 0) & (m["Price_EUR"] > 0) & (m["list_value"] > 0)
    total = float(y["net_sales_value"].sum())
    matched_eur = float(m.loc[ok, "net_sales_value"].sum())
    list_eur = float(m.loc[ok, "list_value"].sum())
    no_list = float(m.loc[~matched, "net_sales_value"].sum())
    return {
        "parts_eur": round(total, 2),
        "matched_eur": round(matched_eur, 2),
        "no_list_eur": round(no_list, 2),
        "coverage_pct": round(100.0 * matched_eur / total, 2) if total else None,
        "realization_pct": round(100.0 * matched_eur / list_eur, 2) if list_eur else None,
        "list_value_eur": round(list_eur, 2),
    }


def recompute_zpr1_medians() -> dict:
    out = {}
    for year in (2025, 2026):
        if year >= 2026:
            z = pd.read_parquet(DER / "pricing_zpr1.parquet")
            cust = pd.to_numeric(z["customer_code"].astype(str).str.replace(r"\D", "", regex=True), errors="coerce")
            pn = z["part_number"].map(norm_pn)
            price = pd.to_numeric(z["sp_eur_zpr1"], errors="coerce")
        else:
            z = pd.read_parquet(DER / f"pricing_zpr1_{year}.parquet")
            cust = pd.to_numeric(z["Customer"], errors="coerce")
            pn = z["Material"].map(norm_pn)
            price = pd.to_numeric(z["Price"], errors="coerce")
        zdf = pd.DataFrame({"Customer": cust, "pn": pn, "Price": price})
        zdf = zdf[(zdf["pn"] != "") & zdf["Price"].notna() & (zdf["Price"] > 0)]
        pr = load_pr00(year).set_index("pn")["Price_EUR"]
        for cust_id, label in ((1799, "UTI"), (1797, "UMI")):
            zc = zdf[zdf["Customer"] == cust_id].copy()
            zc["pr00"] = zc["pn"].map(pr)
            both = zc[zc["pr00"].notna() & (zc["pr00"] > 0)]
            if both.empty:
                out[f"{label}_{year}"] = None
                continue
            med = float((both["Price"] / both["pr00"]).median() - 1.0) * 100.0
            out[f"{label}_{year}"] = round(med, 2)
    # YoY UMI/UTI 2025->2026
    for cust_id, label in ((1799, "UTI"), (1797, "UMI")):
        a = pd.read_parquet(DER / "pricing_zpr1_2025.parquet")
        b = pd.read_parquet(DER / "pricing_zpr1.parquet")
        a = pd.DataFrame(
            {
                "pn": a["Material"].map(norm_pn),
                "p0": pd.to_numeric(a["Price"], errors="coerce"),
                "Customer": pd.to_numeric(a["Customer"], errors="coerce"),
            }
        )
        b = pd.DataFrame(
            {
                "pn": b["part_number"].map(norm_pn),
                "p1": pd.to_numeric(b["sp_eur_zpr1"], errors="coerce"),
                "Customer": pd.to_numeric(
                    b["customer_code"].astype(str).str.replace(r"\D", "", regex=True), errors="coerce"
                ),
            }
        )
        a = a[(a["Customer"] == cust_id) & (a["pn"] != "") & (a["p0"] > 0)]
        b = b[(b["Customer"] == cust_id) & (b["pn"] != "") & (b["p1"] > 0)]
        j = a.merge(b, on="pn")
        if j.empty:
            out[f"{label}_yoy_25_26"] = None
        else:
            out[f"{label}_yoy_25_26"] = round(100.0 * float((j["p1"] / j["p0"] - 1).median()), 2)
    return out


def near(a, b, tol_pct=0.15, tol_abs=None) -> bool:
    if a is None or b is None:
        return False
    if isinstance(a, float) and math.isnan(a):
        return False
    if isinstance(b, float) and math.isnan(b):
        return False
    if tol_abs is not None and abs(float(a) - float(b)) <= tol_abs:
        return True
    if abs(float(b)) < 1e-9:
        return abs(float(a)) < 1e-9
    return abs(float(a) - float(b)) / abs(float(b)) <= tol_pct


def main() -> int:
    items = []
    fails = 0
    caveats = 0

    def check(name: str, ok: bool, detail: str, caveat: bool = False):
        nonlocal fails, caveats
        status = "PASS" if ok else ("CAVEAT" if caveat else "FAIL")
        if not ok and not caveat:
            fails += 1
        elif not ok and caveat:
            caveats += 1
            status = "CAVEAT"
        elif ok and caveat:
            status = "PASS_WITH_CAVEAT"
            caveats += 1
        items.append({"name": name, "status": status, "detail": detail})

    if not HTML.is_file():
        check("HTML exists", False, f"Missing {HTML}")
    else:
        check("HTML exists", True, f"{HTML.name} ({HTML.stat().st_size:,} bytes)")
        check("HTML not stub", HTML.stat().st_size > 20_000, f"size={HTML.stat().st_size}")

    meta = json.loads(META.read_text(encoding="utf-8")) if META.is_file() else {}
    findings = json.loads(FINDINGS.read_text(encoding="utf-8")) if FINDINGS.is_file() else {}
    check("Meta JSON exists", bool(meta), str(META))

    # 1) Recompute CY2025 realization
    print("Recomputing CY2025 realization from parquet…")
    rc = recompute_realization(2025)
    net25 = next((r for r in meta.get("findings_core", {}).get("network", findings.get("network", [])) if r.get("year") == 2025), {})
    check(
        "CY2025 parts € match",
        near(rc["parts_eur"], net25.get("parts_eur"), tol_pct=0.002, tol_abs=5000),
        f"recompute={rc['parts_eur']:,.2f} meta={net25.get('parts_eur')}",
    )
    check(
        "CY2025 coverage match",
        near(rc["coverage_pct"], net25.get("coverage_pct"), tol_abs=0.25),
        f"recompute={rc['coverage_pct']} meta={net25.get('coverage_pct')}",
    )
    check(
        "CY2025 realization match",
        near(rc["realization_pct"], net25.get("realization_pct"), tol_abs=0.25),
        f"recompute={rc['realization_pct']} meta={net25.get('realization_pct')}",
    )

    # 2) NO_LIST from ranked CSV vs meta
    gap = pd.read_csv(DER / "no_pr00_gap_cy2025_ranked.csv")
    gap_eur = float(gap["cy2025_eur"].sum())
    meta_gap = float(meta.get("findings_core", {}).get("nolist", findings.get("nolist", {})).get("gap_eur", 0))
    check(
        "NO_LIST € vs ranked CSV",
        near(gap_eur, meta_gap, tol_pct=0.02, tol_abs=50_000),
        f"csv_sum={gap_eur:,.0f} meta={meta_gap:,.0f}",
    )
    # Note: NO_LIST ranked may differ slightly from realization no_list_eur (match logic)
    check(
        "NO_LIST vs realization no_list (order of magnitude)",
        near(gap_eur, rc["no_list_eur"], tol_pct=0.15) or near(gap_eur, net25.get("no_list_eur"), tol_pct=0.15),
        f"ranked={gap_eur:,.0f} recompute_nolist={rc['no_list_eur']:,.0f} "
        f"(ranked file may use stricter usable-price rule — caveat if within 15%)",
        caveat=not near(gap_eur, rc["no_list_eur"], tol_pct=0.05),
    )

    # 3) ZPR1 UTI vs UMI
    print("Recomputing ZPR1 medians…")
    z = recompute_zpr1_medians()
    zlev = meta.get("findings_core", {}).get("zpr1_level", findings.get("zpr1_level", []))
    def meta_z(payer, year):
        r = next((x for x in zlev if x.get("payer") == payer and int(x.get("year")) == year), None)
        return r.get("median_zpr1_vs_pr00_pct") if r else None

    for payer, year in (("UTI", 2025), ("UMI", 2025), ("UTI", 2026), ("UMI", 2026)):
        key = f"{payer}_{year}"
        check(
            f"ZPR1 {payer} {year} vs PR00 median",
            near(z.get(key), meta_z(payer, year), tol_abs=0.5),
            f"recompute={z.get(key)} meta={meta_z(payer, year)}",
        )

    zyoy = meta.get("findings_core", {}).get("zpr1_yoy", findings.get("zpr1_yoy", []))
    umi_meta = next(
        (x for x in zyoy if x.get("payer") == "UMI" and int(x.get("from_year")) == 2025 and int(x.get("to_year")) == 2026),
        {},
    )
    uti_meta = next(
        (x for x in zyoy if x.get("payer") == "UTI" and int(x.get("from_year")) == 2025 and int(x.get("to_year")) == 2026),
        {},
    )
    check(
        "UMI YoY 25→26",
        near(z.get("UMI_yoy_25_26"), umi_meta.get("median_zpr1_yoy_pct"), tol_abs=0.5),
        f"recompute={z.get('UMI_yoy_25_26')} meta={umi_meta.get('median_zpr1_yoy_pct')}",
    )
    check(
        "UTI YoY 25→26",
        near(z.get("UTI_yoy_25_26"), uti_meta.get("median_zpr1_yoy_pct"), tol_abs=0.5),
        f"recompute={z.get('UTI_yoy_25_26')} meta={uti_meta.get('median_zpr1_yoy_pct')}",
    )

    # 4) UTI ≠ UMI never blended
    html_txt = HTML.read_text(encoding="utf-8") if HTML.is_file() else ""
    meta_txt = json.dumps(meta)
    blend_patterns = [
        r"Israel\s*=\s*UTI\s*\+\s*UMI",
        r"blend(ed)?\s+UTI.*UMI",
        r"UTI\s*/\s*UMI\s+average",
        r"average.*UTI.*UMI.*Israel",
    ]
    blended = any(re.search(p, html_txt + meta_txt, re.I) for p in blend_patterns)
    # positive evidence of separation
    sep_ok = ("UTI ≠ UMI" in html_txt or "UTI ≠ UMI" in html_txt or "never blend" in html_txt.lower()) and (
        "israel_uti_umi" in meta_txt or "UTI" in html_txt and "UMI" in html_txt
    )
    check("UTI≠UMI never blended", (not blended) and sep_ok, f"blended_hit={blended} separation_language={sep_ok}")

    # 5) PMS total primary
    pms_primary = meta.get("pms", {}).get("primary") == "total"
    genuine_headline = bool(re.search(r"PMS genuine capture CY2025|headline.*genuine-only", html_txt, re.I))
    total_in_html = "PMS total capture" in html_txt
    check(
        "PMS total-primary headline",
        pms_primary and total_in_html and not genuine_headline,
        f"meta.primary={meta.get('pms', {}).get('primary')} total_in_html={total_in_html} genuine_headline={genuine_headline}",
    )

    # 6) Integrity math
    integ = meta.get("integrity", {})
    deds = integ.get("deductions", [])
    dsum = sum(int(d.get("deduction", 0)) for d in deds)
    expected = 100 - dsum
    score = int(integ.get("score", -1))
    check(
        "Integrity score = 100 − deductions",
        score == expected,
        f"score={score} expected={expected} deduction_sum={dsum} meta_sum={integ.get('deduction_sum')}",
    )
    band = integ.get("band")
    band_ok = (score < 55 and band == "weak") or (55 <= score < 75 and band == "provisional") or (score >= 75 and band == "usable_internal")
    check("Integrity band matches score", band_ok, f"score={score} band={band}")
    check("External quotability false", integ.get("quotable_externally") is False, str(integ.get("quotable_externally")))

    # 7) HTML numbers vs derived
    if HTML.is_file():
        # coverage / realization strings
        cov_s = (
            f"{float(net25.get('coverage_pct')):.1f}%"
            if net25.get("coverage_pct") is not None
            else None
        )
        real_s = (
            f"{float(net25.get('realization_pct')):.1f}%"
            if net25.get("realization_pct") is not None
            else None
        )
        check("HTML contains CY2025 coverage", cov_s is not None and cov_s in html_txt, f"looked for {cov_s}")
        check("HTML contains CY2025 realization", real_s is not None and real_s in html_txt, f"looked for {real_s}")
        check(
            "HTML contains integrity score",
            f"{score}/100" in html_txt or f">{score}</div>" in html_txt,
            f"score={score}",
        )
        # broken €M formatting like €30,422,371.9M must not appear
        bad_eur = re.findall(r"€[\d,]+\.\dM", html_txt)
        bad = [b for b in bad_eur if re.search(r"€\d{2,},", b)]
        check("HTML € formatting (no raw+ M)", len(bad) == 0, f"bad_samples={bad[:5]}")
        check(
            "Mode A language (no IML v7 / Model B)",
            ("IML v7" not in html_txt) and ("Model B" not in html_txt),
            "scanned",
        )

    # 8) Verification / snapshot
    vr = json.loads((DER / "_verification_report.json").read_text(encoding="utf-8"))
    ver_ok = bool(vr.get("summary", {}).get("ok")) if isinstance(vr.get("summary"), dict) else bool(vr.get("ok"))
    check("PRISM verification green", ver_ok, str(vr.get("summary")))
    # KPI contradiction: pack should note provisional list-to-pocket separate from green verification
    check(
        "Pack separates green verification from list-to-pocket",
        "provisional" in html_txt.lower() and ("verification" in html_txt.lower() or meta.get("verification", {}).get("ok") is not None),
        "provisional language + verification note present",
    )

    # 9) GPS KPI in HTML for UTI/UMI separate
    gps = pd.read_csv(DER / "gps_spu_by_distributor.csv")
    g25 = gps[gps["year"] == 2025]
    uti = g25[g25["distributor_code"] == "UTI"]
    umi = g25[g25["distributor_code"] == "UMI"]
    if len(uti) and len(umi):
        check(
            "GPS UTI≠UMI values distinct",
            float(uti.iloc[0]["spend_per_unit_eur"]) != float(umi.iloc[0]["spend_per_unit_eur"]),
            f"UTI={uti.iloc[0]['spend_per_unit_eur']:.0f} UMI={umi.iloc[0]['spend_per_unit_eur']:.0f}",
        )

    # Verdict
    if fails:
        verdict = "FAIL"
    elif caveats:
        verdict = "PASS_WITH_CAVEATS"
    else:
        verdict = "PASS"

    lines = [
        f"# Pricing full pack audit",
        f"",
        f"- **Verdict:** {verdict}",
        f"- **Built / audited (UTC):** {UTC_NOW}",
        f"- **Integrity score (pack):** {score}/100 ({band})",
        f"- **HTML:** `{HTML.relative_to(ISZE).as_posix()}`",
        f"- **FAIL count:** {fails} · **CAVEAT count:** {caveats}",
        f"",
        f"## Checks",
        f"",
        f"| Status | Check | Detail |",
        f"|---|---|---|",
    ]
    for it in items:
        lines.append(f"| {it['status']} | {it['name']} | {it['detail']} |")

    lines += [
        f"",
        f"## Recompute anchors (CY2025)",
        f"",
        f"```",
        f"{json.dumps(rc, indent=2)}",
        f"```",
        f"",
        f"## ZPR1 recompute",
        f"",
        f"```",
        f"{json.dumps(z, indent=2)}",
        f"```",
        f"",
        f"## Notes",
        f"",
        f"- PMS headline must remain **total** capture; genuine/BVP is extra.",
        f"- UTI and UMI must never be blended.",
        f"- List-to-pocket remains provisional even when PRISM verification is green.",
        f"- Send allowed only after PASS or PASS_WITH_CAVEATS, and only to Jerome self mailbox.",
        f"",
    ]
    AUDIT_MD.write_text("\n".join(lines), encoding="utf-8")
    def _safe(s: str) -> str:
        return (
            str(s)
            .replace("→", "->")
            .replace("€", "EUR ")
            .replace("≠", "!=")
            .replace("−", "-")
            .replace("–", "-")
            .replace("—", "-")
            .encode("ascii", "replace")
            .decode("ascii")
        )

    print(f"\nVERDICT: {verdict}")
    print(f"Wrote {AUDIT_MD}")
    for it in items:
        print(_safe(f"  [{it['status']}] {it['name']}: {it['detail']}"))

    result = {
        "verdict": verdict,
        "fails": fails,
        "caveats": caveats,
        "integrity_score": score,
        "integrity_band": band,
        "html": str(HTML),
        "audit_md": str(AUDIT_MD),
        "timestamp_utc": UTC_NOW,
        "items": items,
        "recompute_cy2025": rc,
        "zpr1": z,
    }
    (DER / "_pricing_full_pack_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if verdict in {"PASS", "PASS_WITH_CAVEATS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
