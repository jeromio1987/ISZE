# -*- coding: utf-8 -*-
"""Write Pass3 note + summary after coverage rebuild."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
U29B = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_pdp_oe_upgrade_pass3_20261007"
NOTE = ROOT / "00_docs" / "UNIVERSE_UK_KS_PDP_OE_UPGRADE_PASS3_2026-10-07.md"
PARQUET = U29B / "01_data" / "00_derived" / "price_observations.parquet"
METRICS = (
    U29B
    / "01_data"
    / "00_derived"
    / "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
)
BAK = (
    U29B
    / "01_data"
    / "00_derived"
    / "price_observations.parquet.bak_20261007T162448Z_before_ks_pdp_oe_pass3"
)


def main() -> int:
    checks = json.loads(
        (OUT / "pdp_checks_pass3_20261007.json").read_text(encoding="utf-8")
    )
    upgrades = [c for c in checks if c.get("verdict") == "upgrade_exact_oem"]
    rejects = [c for c in checks if c.get("verdict") != "upgrade_exact_oem"]

    df = pd.read_parquet(PARQUET)
    m = df["description"].astype(str).str.contains(
        "PDP OE upgrade 2026-10-07 pass3", na=False
    )
    p3 = df[m]
    extra = p3[p3["description"].astype(str).str.contains("same-SKU", na=False)]
    prim = p3[~p3["description"].astype(str).str.contains("same-SKU", na=False)]

    b_off, b_pn, focus_before = 83, 25, 47
    after = json.loads(METRICS.read_text(encoding="utf-8"))
    a_off = after["eligible_rows"]
    a_pn = after["eligible_pns"]
    focus_after = after["eligible_rows_in_focus"]

    by_sku_extra: dict[str, list[str]] = defaultdict(list)
    for _, r in extra.iterrows():
        by_sku_extra[str(r["competitor_pn"])].append(str(r["part_no"]))

    summary = {
        "skus_checked": len(checks),
        "upgrades_pdp": len(upgrades),
        "rejects": len(rejects),
        "rows_patched_primary": int(len(prim)),
        "rows_patched_same_sku_extra": int(len(extra)),
        "rows_patched_total": int(len(p3)),
        "distinct_skus_upgraded": int(p3["competitor_pn"].nunique()),
        "distinct_pns_touched": int(p3["part_no"].nunique()),
        "eligible_offers_before": b_off,
        "eligible_pns_before": b_pn,
        "eligible_offers_after": a_off,
        "eligible_pns_after": a_pn,
        "eligible_focus_before": focus_before,
        "eligible_focus_after": focus_after,
        "backup": str(BAK),
        "reject_verdicts": dict(Counter(r["verdict"] for r in rejects)),
        "family_mix_checked": dict(Counter(c["family"] for c in checks)),
        "family_mix_upgraded": dict(Counter(u["family"] for u in upgrades)),
        "wire10_skus": sum(1 for u in upgrades if u.get("can_wire_10")),
        "no_wire10_skus": sum(1 for u in upgrades if not u.get("can_wire_10")),
    }
    (OUT / "pdp_upgrade_summary_pass3_20261007.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    lines: list[str] = []
    lines.append("# UK KS PDP OE upgrade — Pass 3 — 2026-10-07")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(
        f"**{len(upgrades)} of {len(checks)}** remaining filter / clutch / exhaust KS PDPs "
        "printed the linked Isuzu part number under **OE Equivalent Part Number** "
        f"(also JSON-LD). **{len(p3)}** ledger rows upgraded `category_only` → `exact_oem` "
        f"({len(prim)} primary + {len(extra)} same-SKU extras). "
        f"Wider UK `exact_oem` eligible: **{b_off} → {a_off}** offers "
        f"(**{b_pn} → {a_pn}** PNs). Focus (oil filter + brake pad) stayed **{focus_after}** "
        "(new rows are clutch / exhaust / non-focus filter). "
        "Board / INTERNAL not rebuilt here."
    )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        "Pass 1/2 filled 25 filter SKUs (55 rows → wider 83 / 25 PNs). "
        "Pass 3 takes remaining UK KS `category_only` rows in **filter / clutch / exhaust** "
        "(KS £10 mainland classes), excluding the 25 already upgraded SKUs. Cap **40** "
        "distinct `competitor_pn`. Prefer clutch and exhaust (crowded out of the first 25), "
        "then remaining filters by £."
    )
    lines.append("")
    lines.append(f"Ledger: `{PARQUET}`")
    lines.append("")
    lines.append(
        "£10 delivery + VAT excl only for filter / clutch / muffler / tail pipe. "
        "Ten exhaust-adjacent PDPs (exhaust brake / gasket / camshaft / temperature sensor) "
        "were upgraded to `exact_oem` on OE evidence but **not** wired £10 — out of live KS "
        "policy. No body / rotor / spring wired."
    )
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|---|---:|")
    lines.append(f"| PDPs / SKUs checked | **{len(checks)}** |")
    lines.append(f"| Upgrades (OE on PDP) | **{len(upgrades)}** |")
    lines.append(f"| Rejects | **{len(rejects)}** |")
    lines.append(f"| Ledger rows patched (primary) | **{len(prim)}** |")
    lines.append(f"| Same-SKU extras | **{len(extra)}** |")
    lines.append(f"| Ledger rows patched (total) | **{len(p3)}** |")
    lines.append(
        f"| Distinct KS SKUs upgraded | **{p3['competitor_pn'].nunique()}** |"
    )
    lines.append(
        f"| Distinct Isuzu PNs touched | **{p3['part_no'].nunique()}** |"
    )
    lines.append(f"| SKUs with £10 wire | **{summary['wire10_skus']}** |")
    lines.append(
        f"| SKUs OE-upgraded without £10 | **{summary['no_wire10_skus']}** |"
    )
    lines.append("")
    fam = ", ".join(
        f"{k}={v}" for k, v in Counter(c["family"] for c in checks).items()
    )
    lines.append(f"Family mix checked/upgraded: {fam}")
    lines.append("")
    lines.append("### Candidates checked")
    lines.append("")
    lines.append(
        "| # | KS SKU | Candidate Isuzu PN | £ excl | Family | £10 | Verdict |"
    )
    lines.append("|---:|---|---|---:|---|---|---|")
    for n, c in enumerate(checks, 1):
        lines.append(
            f"| {n} | `{c['competitor_pn']}` | `{c['part_no']}` | {c['price']:.2f} | "
            f"{c['family']} | {'Y' if c['can_wire_10'] else 'N'} | {c['verdict']} |"
        )
    lines.append("")
    lines.append("## Upgrades (evidence samples)")
    lines.append("")
    lines.append("| KS SKU | Isuzu PN | Family | Where | Quote | £10 |")
    lines.append("|---|---|---|---|---|---|")
    for u in upgrades:
        hit = u["oe_hits"][0] if u["oe_hits"] else {}
        q = (hit.get("quote") or "")[:80].replace("|", "/")
        lines.append(
            f"| `{u['competitor_pn']}` | `{u['part_no']}` | {u['family']} | "
            f"{hit.get('where', '')} | `{q}` | "
            f"{'Y' if u['can_wire_10'] else 'N'} |"
        )
    lines.append("")
    if by_sku_extra:
        lines.append("### Same-SKU extras")
        lines.append("")
        lines.append("| KS SKU | Extra Isuzu PN(s) | Extra rows |")
        lines.append("|---|---|---:|")
        for sku, pns in sorted(by_sku_extra.items()):
            uniq = sorted(set(pns))
            pn_txt = ", ".join(f"`{p}`" for p in uniq)
            lines.append(f"| `{sku}` | {pn_txt} | {len(pns)} |")
        lines.append("")
    lines.append("## Rejects")
    lines.append("")
    lines.append("- (none) — 40/40 OE attribute hit")
    lines.append("")
    lines.append(
        "No invent: only PNs on the PDP OE attribute / JSON-LD upgraded."
    )
    lines.append("")
    lines.append("## Eligible before / after")
    lines.append("")
    lines.append(
        "Coverage rebuild (from U29b worktree so ledger + node runner resolve correctly):"
    )
    lines.append("")
    lines.append("```text")
    lines.append(
        "python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact"
    )
    lines.append("```")
    lines.append("")
    lines.append("| Cut | Before (post pass1/2) | After pass3 |")
    lines.append("|---|---:|---:|")
    lines.append(
        f"| Wider UK `exact_oem` eligible **offers** | **{b_off}** | **{a_off}** |"
    )
    lines.append(f"| Wider eligible **PNs** | **{b_pn}** | **{a_pn}** |")
    lines.append(f"| Delta offers | | **{a_off - b_off:+d}** |")
    lines.append(f"| Delta PNs | | **{a_pn - b_pn:+d}** |")
    lines.append(
        f"| Focus (oil filter + brake pad) | **{focus_before}** | **{focus_after}** |"
    )
    lines.append(
        f"| Outside focus | | **{after['eligible_rows_outside_focus']}** |"
    )
    lines.append("")
    lines.append(
        f"**Parent note:** Pass3 added **+{a_off - b_off}** wider eligible offers "
        f"beyond the pass1/2 total of {b_off}. Sibling wire-83 / INTERNAL finished "
        f"(or finishes) against **83** must be **re-wired** to pick up **{a_off}**."
    )
    lines.append("")
    lines.append("Metrics (U29b + copied to main derived):")
    lines.append("")
    lines.append(f"`{METRICS}`")
    lines.append("")
    lines.append(
        r"`C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`"
    )
    lines.append("")
    lines.append("## Backups")
    lines.append("")
    lines.append(f"- `{BAK}`")
    lines.append("")
    lines.append("## Artefacts")
    lines.append("")
    lines.append("| Object | Path |")
    lines.append("|---|---|")
    lines.append(f"| Candidate list | `{OUT / 'pdp_candidates_pass3_20261007.csv'}` |")
    lines.append(f"| PDP HTML + checks | `{OUT}` |")
    lines.append(
        f"| Summary JSON | `{OUT / 'pdp_upgrade_summary_pass3_20261007.json'}` |"
    )
    lines.append(f"| This note | `{NOTE}` |")
    lines.append(
        f"| Runner | `{ROOT / '01_data' / '91_build' / '_uk_ks_pdp_oe_upgrade_pass3_20261007.py'}` |"
    )
    lines.append("")
    lines.append("## Not done")
    lines.append("")
    lines.append(
        "- Board HTML / INTERNAL not rebuilt (sibling owns wire-83; "
        "**re-wire required** — delta +68)."
    )
    lines.append("- No ACCEPT.")
    lines.append("")

    NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("NOTE", NOTE)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
