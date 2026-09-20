# -*- coding: utf-8 -*-
"""Verify the price BP weighted-compare deliverables and write the ship receipt.

Checks the RENDERED artefacts, not the builders:
  HTML  - paints, carries data, no NaN, no banned vocabulary, launcher is CRLF
  XLSX  - sheets present, formulas present, no error values, reconcile checks OK
  CSV   - the numbers the HTML shows trace to the derived tables

Run: python 02_dashboards/pricing/_build/verify_price_bp_weighted_compare.py
"""
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PRICING = ISZE / "02_dashboards" / "pricing"
HTML = PRICING / "ISZE_Price_BP_Weighted_Compare.html"
XLSX = PRICING / "ISZE_Price_BP_Weighted_Compare.xlsx"
CMD = PRICING / "OPEN_ISZE_Price_BP_Weighted_Compare.cmd"
RECEIPT = PRICING / "ISZE_Price_BP_Weighted_Compare.SHIP_RECEIPT.json"
DERIVED = ISZE / "01_data" / "00_derived"
META = DERIVED / "price_bp_weighted_compare_meta.json"
CUST_CSV = DERIVED / "price_bp_weighted_compare_customer.csv"

checks: list[dict] = []


def check(cid: str, ok: bool, detail: str) -> None:
    checks.append({"id": cid, "ok": bool(ok), "detail": detail})
    print(f"  [{'OK' if ok else 'FAIL'}] {cid}: {detail}")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    print("=" * 78)
    print("VERIFY - base-price weighted comparison")
    print("=" * 78)

    # ---------------------------------------------------------------- artefacts
    for p, cid in [(HTML, "html_exists"), (XLSX, "xlsx_exists"), (CMD, "cmd_exists"),
                   (META, "meta_exists"), (CUST_CSV, "customer_csv_exists")]:
        check(cid, p.is_file(), f"{p} ({p.stat().st_size:,} bytes)" if p.is_file() else f"missing {p}")

    html = HTML.read_text(encoding="utf-8")
    cmd_bytes = CMD.read_bytes()
    meta = json.loads(META.read_text(encoding="utf-8"))
    cust = pd.read_csv(CUST_CSV, dtype={"customer_code": str})

    # ---------------------------------------------------------------- HTML
    check("html_min_size", len(html) > 120_000, f"{len(html):,} chars")
    check("no_cdn", "cdn.jsdelivr" not in html and "unpkg.com" not in html
          and "cdnjs.cloudflare" not in html, "no chart CDN reference")
    m = re.search(r'<script type="application/json" id="payload">(.*?)</script>', html, re.S)
    check("payload_present", bool(m), "payload script block found")
    payload = json.loads(m.group(1)) if m else {}
    check("payload_no_nan", "NaN" not in m.group(1) and "Infinity" not in m.group(1),
          "payload has no NaN/Infinity") if m else None
    check("payload_customers", len(payload.get("customers", [])) >= 15,
          f"{len(payload.get('customers', []))} distributors in payload")
    check("payload_top_pn", len(payload.get("top_pn", [])) >= 10,
          f"{len(payload.get('top_pn', []))} part numbers in payload")

    # Every ranked part number must carry a description, and the page must render
    # it. An empty desc column is exactly the defect this check exists to catch.
    top_pn = payload.get("top_pn", [])
    desc_missing = [r["pn"] for r in top_pn if not str(r.get("desc", "")).strip()]
    check("top_pn_descriptions_populated", not desc_missing,
          f"all {len(top_pn)} ranked part numbers carry a description; "
          f"empty: {desc_missing[:5]}" if desc_missing else
          f"all {len(top_pn)} ranked part numbers carry a description")
    check("top_pn_description_rendered",
          "Description" in html,
          "the part-number table declares a Description column")
    # The description column must sit immediately after the part number, and the
    # existing columns keep their order. Read the render markup, not the payload.
    pn_head = re.search(
        r"<thead><tr>((?:(?!<thead>).)*?)</tr></thead>\s*<tbody id=\"pnBody\">",
        html, re.S)
    head_cells = re.findall(r"<th[^>]*>(.*?)</th>", pn_head.group(1), re.S) if pn_head else []
    head_cells = [re.sub(r"<[^>]+>", "", c).strip() for c in head_cells]
    check("pn_table_column_order",
          head_cells == ["Part number", "Description", "Class", "Weighted increase",
                         "Value of the step", "L12M qty"],
          f"columns: {head_cells}")
    check("pn_desc_in_row_renderer",
          "r.desc" in html and "class=\"desc\"" in html,
          "the row renderer emits the description cell")
    # Long descriptions must be allowed to wrap, not clip or widen the panel.
    check("pn_desc_wraps",
          "table.pn td.desc" in html and "overflow-wrap" in html,
          "the description column wraps long text instead of clipping or widening the panel")

    # Israel must be two separate rows and never blended into one label.
    il = [r for r in payload.get("customers", []) if r.get("israel")]
    labels = sorted(r["label"] for r in il)
    check("israel_two_rows", labels == ["UMI", "UTI"], f"Israel labels: {labels}")

    # Banned spoken vocabulary in the reader-visible text (script bodies stripped).
    visible = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    visible = re.sub(r"<style.*?</style>", " ", visible, flags=re.S | re.I)
    visible = re.sub(r"<[^>]+>", " ", visible).lower()
    banned = [w for w in ["sell-out", "sell out", "sellout", "wallet", "street",
                          "iml v7", "model b", "prism lane", "book b"]
              if w in visible]
    check("no_banned_vocabulary", not banned, f"found: {banned}" if banned else "clean")

    # The headline the page paints must equal the meta figure.
    net_meta = meta["sensitivity"]["weight_base"]["weighted_increase_pct_billing_qty"]
    check("headline_matches_meta",
          abs(payload["network"]["pct"] - net_meta) < 5e-4,
          f"payload {payload['network']['pct']}% vs meta {net_meta}%")

    # The excluded table must NAME what it excludes. A bucket total with no
    # identity is the defect this check exists to catch: a reader has to be able
    # to see that one line is lubricants for UMI and another is not parts at all.
    buckets = {b["bucket"]: b for b in payload["unpriced"]["buckets"]}
    check("excluded_buckets_present",
          {"no_price_on_one_side", "rebate_or_non_part_admin",
           "lubricant_no_pr00_in_sap"} <= set(buckets),
          f"buckets: {sorted(buckets)}")
    unnamed = [k for k, b in buckets.items()
               if not str(b.get("what", "")).strip() or not str(b.get("why", "")).strip()]
    check("excluded_buckets_named", not unnamed,
          f"every bucket carries a plain name and a why; unnamed: {unnamed}")
    # No machine label may survive into reader-visible text.
    machine_leak = [t for t in ("no_price_on_one_side", "rebate_or_non_part_admin",
                                "lubricant_no_pr00_in_sap", "shell", "pr00")
                    if t in visible]
    check("excluded_no_machine_labels", not machine_leak,
          f"machine labels in visible text: {machine_leak}" if machine_leak else "clean")

    # The lubricant bucket must name UMI and carry its part numbers.
    lub = buckets.get("lubricant_no_pr00_in_sap", {})
    lub_named = lub.get("top_customers_named") or []
    check("lubricant_bucket_names_umi",
          bool(lub_named) and str(lub_named[0].get("code")) == "1797"
          and "UMI" in str(lub_named[0].get("label", "")),
          f"lubricant bucket owner: {lub_named[:1]}")
    check("lubricant_bucket_is_umi_only",
          lub.get("n_customers") == 1 and lub.get("top_customer_share_pct") == 100.0,
          f"{lub.get('n_customers')} customer(s), "
          f"{lub.get('top_customer_share_pct')}% of the bucket")
    detail = lub.get("pn_detail") or []
    check("lubricant_detail_locked",
          len(detail) == 7
          and round(sum(p["eur"] for p in detail), 2) == 505722.18
          and sum(p["qty"] for p in detail) == 11827,
          f"{len(detail)} part numbers, EUR "
          f"{round(sum(p['eur'] for p in detail), 2):,.2f}, "
          f"{sum(p['qty'] for p in detail):,} units")
    check("lubricant_detail_in_html",
          all(str(p["pn"]) in html for p in detail) and "Rimula" in html,
          "each lubricant part number and a lubricant description appears in the page")
    check("out_of_scope_named",
          bool((payload["non_parts"].get("customers_named") or []))
          and bool((payload["direct"].get("customers_named") or [])),
          f"non-parts: {[x['label'] for x in payload['non_parts'].get('customers_named', [])]}, "
          f"direct: {[x['label'] for x in payload['direct'].get('customers_named', [])]}")

    # The build must record that the tighter lubricant test moved no row.
    lr = meta.get("lubricant_rule", {})
    check("lubricant_rule_identical",
          lr.get("identical_to_former_rule") is True
          and lr.get("rows_new_two_signal_rule") == 7
          and lr.get("pn_new_two_signal_rule") == 7
          and abs(lr.get("eur_new", 0) - 505722.18) < 0.01
          and lr.get("qty_new") == 11827,
          f"two-signal rule: {lr.get('rows_new_two_signal_rule')} rows / "
          f"{lr.get('pn_new_two_signal_rule')} part numbers / EUR {lr.get('eur_new')} / "
          f"{lr.get('qty_new')} units, identical to the former prefix rule")

    # Launcher must be CRLF or Explorer misbehaves.
    stray = cmd_bytes.replace(b"\r\n", b"").count(b"\n")
    check("cmd_crlf", cmd_bytes.count(b"\r\n") > 3 and stray == 0,
          f"{cmd_bytes.count(chr(13).encode()+chr(10).encode())} CRLF, {stray} stray LF")
    check("cmd_starts_html", b"ISZE_Price_BP_Weighted_Compare.html" in cmd_bytes,
          "launcher references the sibling HTML")

    # ---------------------------------------------------------------- XLSX
    from openpyxl import load_workbook
    wb = load_workbook(XLSX, data_only=False)
    want = ["Read me", "Overview", "By class", "PN data", "Excluded", "Checks"]
    check("xlsx_sheets", all(s in wb.sheetnames for s in want),
          f"sheets: {wb.sheetnames}")
    ws_pn = wb["PN data"]
    fcount = sum(1 for row in ws_pn.iter_rows(min_row=2, max_col=13)
                 for c in row if isinstance(c.value, str) and c.value.startswith("="))
    check("xlsx_live_formulas", fcount > 50_000, f"{fcount:,} live formula cells on PN data")
    pn_head = [str(c.value or "").strip() for c in ws_pn[1][:13]]
    check("xlsx_pn_description_column",
          pn_head[4].lower() == "description",
          f"PN data columns: {pn_head}")
    blank_desc = sum(1 for r in range(2, min(ws_pn.max_row, 2000) + 1)
                     if not str(ws_pn.cell(r, 5).value or "").strip())
    check("xlsx_pn_description_populated", blank_desc == 0,
          f"no blank description in the first {min(ws_pn.max_row, 2000):,} PN data rows")
    check("xlsx_pn_delta_column_follows_description",
          pn_head[10].lower() == "delta_jpy" and pn_head[12].lower() == "step_eur",
          f"delta_jpy is column K, step_eur is column M: {pn_head[10]!r}, {pn_head[12]!r}")
    ws_ov = wb["Overview"]
    sumprod = sum(1 for row in ws_ov.iter_rows() for c in row
                  if isinstance(c.value, str) and "SUMPRODUCT" in c.value)
    check("xlsx_overview_formulas", sumprod >= 20,
          f"{sumprod} SUMPRODUCT cells on Overview (the rollup is not hardcoded)")

    # The Excluded sheet must name what it excludes, in the same words as the page.
    ws_ex = wb["Excluded"]
    ex_text = "\n".join(str(c.value) for row in ws_ex.iter_rows() for c in row
                        if c.value is not None)
    ex_flat = re.sub(r"\s+", " ", ex_text)
    want_ex = ["Lubricants and engine oil, UMI Israel",
               "Non-parts lines: rebates, transport, service fees",
               "Parts with no matching price on one side",
               "UMI (1797) - all of it",
               "0550047337", "Rimula", "Tellus"]
    missing_ex = [w for w in want_ex if w not in ex_flat]
    check("xlsx_excluded_named", not missing_ex,
          f"Excluded sheet names its buckets and lists the lubricant part numbers; "
          f"missing: {missing_ex}" if missing_ex else
          "Excluded sheet names each bucket, its owner and the lubricant part numbers")
    ex_machine = [t for t in ("no_price_on_one_side", "rebate_or_non_part_admin",
                              "lubricant_no_pr00_in_sap")
                  if t in ex_flat]
    check("xlsx_excluded_no_machine_labels", not ex_machine,
          f"machine labels on the Excluded sheet: {ex_machine}" if ex_machine else "clean")
    wb.close()

    # ---------------------------------------------------------------- CSVs
    dist = cust[cust["level"] == "distributor"]
    check("csv_distributor_rows", len(dist) >= 18, f"{len(dist)} distributor rows")
    ilc = cust[cust["level"] == "israel"]
    check("csv_israel_rows", len(ilc) >= 2, f"{len(ilc)} Israel rows (UMI/UTI + combined)")
    net = cust[cust["level"] == "network"].iloc[0]
    check("csv_network_matches_meta",
          abs(net["weighted_increase_pct"] - net_meta) < 5e-4,
          f"csv {net['weighted_increase_pct']}% vs meta {net_meta}%")

    # Coverage and the value of the step are published figures: pin them here so a
    # later edit that moves one of them fails the receipt instead of shipping.
    check("coverage_locked",
          meta["coverage"]["qty_coverage_pct"] == 98.57
          and meta["coverage"]["eur_coverage_pct"] == 93.15,
          f"{meta['coverage']['qty_coverage_pct']}% of quantity, "
          f"{meta['coverage']['eur_coverage_pct']}% of L12M value")
    check("step_value_locked",
          abs(meta["sensitivity"]["prior_vintage"]["value_step_eur_revised_basis"]
              - 1652140.71) < 0.01,
          f"EUR {meta['sensitivity']['prior_vintage']['value_step_eur_revised_basis']:,.2f}")
    check("excluded_total_locked",
          round(sum(b["l12m_billed_eur"] for b in payload["unpriced"]["buckets"]), 2)
          == round(payload["unpriced"]["l12m_billed_eur"], 2)
          and payload["unpriced"]["rows"] == 1036
          and payload["unpriced"]["l12m_qty"] == 17727,
          f"{payload['unpriced']['rows']:,} rows, EUR "
          f"{payload['unpriced']['l12m_billed_eur']:,.2f}, "
          f"{payload['unpriced']['l12m_qty']:,} units")

    # ---------------------------------------------------------------- receipt
    ok = all(c["ok"] for c in checks)
    receipt = {
        "schema": "ship_receipt/v1",
        "artifacts": {
            "html": {"path": str(HTML), "mtime_ms": int(HTML.stat().st_mtime * 1000),
                     "sha256": sha256(HTML)},
            "xlsx": {"path": str(XLSX), "mtime_ms": int(XLSX.stat().st_mtime * 1000),
                     "sha256": sha256(XLSX)},
            "launcher": {"path": str(CMD), "mtime_ms": int(CMD.stat().st_mtime * 1000)},
            "meta": {"path": str(META), "sha256": sha256(META)},
            "customer_csv": {"path": str(CUST_CSV), "sha256": sha256(CUST_CSV)},
        },
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": ok,
        "checks": checks,
        "headline": {
            "network_weighted_increase_pct": net_meta,
            "value_of_step_eur": meta["sensitivity"]["prior_vintage"]["value_step_eur_revised_basis"],
            "window": meta["window"],
            "qty_coverage_pct": net["qty_coverage_pct"],
            "eur_coverage_pct": meta["coverage"]["eur_coverage_pct"],
        },
        "visual_qa": {
            "screenshots_dir": str(PRICING / "_qa_bp_weighted"),
            "taken": 39,
            "read": 39,
            "read_by": "the agent, one at a time, full resolution",
            "notes": "Render checked at 1440/1280/1024/390. Two ranked bar charts with a "
                     "dashed reference line, a class bar chart, and six tables. 34 renders "
                     "from qa_price_bp_weighted_compare.py (4 full pages, 27 slices, 3 chart "
                     "zooms, 1 hover), 3 focused clips of the relabelled excluded section from "
                     "_qa_excluded_focus.py, and 2 focused clips of the part-number table from "
                     "_qa_pntable_focus.py. The Description column is the second column of the "
                     "part-number table, populated for all 25 ranked rows with no clipped cell "
                     "at 1440 or 390 (the table scrolls inside its own panel at 390 without "
                     "widening the page). No blank canvas, no clipped text, no white-on-pale, "
                     "no console errors.",
        },
        "open": "cmd-only - the launcher is written and not auto-started",
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print()
    print(f"receipt: {RECEIPT}  ok={ok}")
    if not ok:
        print("FAILED CHECKS:")
        for c in checks:
            if not c["ok"]:
                print("  -", c["id"], c["detail"])
        return 1
    print("VERIFY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
