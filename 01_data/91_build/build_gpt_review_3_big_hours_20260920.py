"""Build multi-hour GPT review pack (exactly 5 deliverable files)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data/15_gpt_safe/gpt_review_3_big_2026-09-20"
OUT.mkdir(parents=True, exist_ok=True)


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        return f"(missing on disk: {rel})\n"
    return p.read_text(encoding="utf-8", errors="replace")


def write(name: str, text: str) -> None:
    path = OUT / name
    path.write_text(text, encoding="utf-8", newline="\n")
    kb = path.stat().st_size / 1024
    print(f"  {name:30s} {kb:8.1f} KB")


print("Building multi-hour GPT review pack…")

# ---------------------------------------------------------------------------
# 00 ASK — hour-scale work order
# ---------------------------------------------------------------------------
write(
    "00_ASK.md",
    """# Multi-hour GPT review — work order

**Prepared:** 2026-09-20 · Internal / private · **Expected effort: 4–6 hours of careful work**
**Folder:** `01_data/15_gpt_safe/gpt_review_3_big_2026-09-20/`
**Deliverables:** five files only. No line-level billing is included on purpose.

This is not a skim. Jerome wants a review that takes **hours**: recompute from the tables,
reconcile contradictions between documents, and pressure every open decision with evidence.
If you finish in under an hour, you did not do the job.

---

## Files

| File | Role | Size class |
|------|------|------------|
| `00_ASK.md` | This work order | short |
| `01_PRICING.md` | Full pricing programme brief + policy paper | large |
| `02_PARTS_FAMILY.md` | Classification switch + Japanese codes corpus | very large |
| `03_AFTERSALES_CEILING.md` | GPS/PMS ceiling + opportunity + open decisions | large |
| `04_DATA_TABLES.csv` | Checkable multi-table extract (`table` column) | large |

---

## Session plan (do in order, do not skip)

### Block 1 — Pricing (90–120 minutes)

Read `01_PRICING.md` and every `table=pricing_stack` / related rows in `04_DATA_TABLES.csv`.

Required outputs:
1. Recompute (or verify arithmetic of) whole-book, Japan, Thailand, PR00/UTI/UMI/CIS weighted increases from the stated recipe. Say PASS/FAIL per figure.
2. CONFIRM/REJECT/UNKNOWN on every numbered claim in §C of the pricing brief.
3. Rank the open decisions by commercial damage if left unanswered (top 5, with one sentence each).
4. Explicitly state whether flat +5% paper and the measured ~5.96% step may be combined (yes/no + why).
5. Flag any number in the policy paper that conflicts with the stack JSON / CSV.

### Block 2 — Parts family & Japanese codes (120–180 minutes)

Read all of `02_PARTS_FAMILY.md` (Parts I–V). Use `table=jp_codes`, `classification`, `benchmark_*` in the CSV.

Required outputs:
1. Independent verdict on **switch today?** — with the mtime/staleness argument tested against the brief’s own evidence.
2. For the claim table in the settled-position section: mark each major claim CONFIRMED / CORRECTED / STILL OPEN as you read it; list any new contradiction between Part II, Part III, Part IV, Part V.
3. Re-state in your own words why ZKK cannot be a chart axis (cite euro shares / fragmentation).
4. Separate verdicts for ZUK meaning, HKK usability, EPLE usability.
5. Name the single highest-ROI next build step (not “rebuild everything”).

### Block 3 — Aftersales ceiling & opportunity (90–120 minutes)

Read `03_AFTERSALES_CEILING.md`. Recompute from CSV tables `wallet_*`, `opportunity_*`, `gps_*`, `n35_share`, `capture_*`.

Required outputs:
1. Rebuild the network 2025 maths: ceiling, captured, coverage %, flat-€250 count and share — from CSV only. Compare to the brief.
2. Confirm ITUK / UTI / UMI rows separately (never blend Israel).
3. Produce your own top-10 opportunity ranking (category and category×market) from the CSV; say if oil-filter-as-hero would be wrong.
4. Portugal 0.6364 vs shipment mix: what Jerome must answer before any ceiling rebuild.
5. CONFIRM/REJECT/UNKNOWN on every numbered claim in §D of the aftersales brief.

### Block 4 — Cross-programme synthesis (30–45 minutes)

Required outputs:
1. Three contradictions that cut **across** pricing / classification / ceiling (not inside one file).
2. Three forcing decisions for Jerome — one per programme — worded so a yes/no or a single number closes them.
3. **What not to do this week** (hard stop list).
4. Agent-error pattern: where earlier agents clearly failed, in plain English.

---

## Hard rules (non-negotiable)

- Do not invent ceilings, capture %, price moves, or ZKK dictionaries.
- Do not blend UMI (1797) and UTI (1799); do not blend IUK and ITUK.
- Banned outward labels: Mode A/B, wallet, street, sell-out, Book B, IML v7, Model B, “AIM v2”.
- Findings need euro + parts family + trucks in service.
- Primary aftersales lens = **total** capture.
- Retired figures: 51.1% and €60.22M.
- Review only — do not instruct a rebuild or a ship.

---

## Return format

Write four sections titled exactly:

`## Block 1 — Pricing`
`## Block 2 — Parts family`
`## Block 3 — Aftersales ceiling`
`## Block 4 — Synthesis`

Under Blocks 1–3, use subheadings for each required output numbered above.
Under Block 4, use the four numbered items.

If a check is impossible from the pack, write **UNKNOWN — missing X**, not a guess.

---

## Paste prompt

> Execute the multi-hour work order in `00_ASK.md`. Work block by block. Recompute from `04_DATA_TABLES.csv`. Challenge every numbered claim. Return the four Block sections exactly as specified. Do not skim.
""",
)

# ---------------------------------------------------------------------------
# 01 PRICING — stack + roadmap + full policy paper REV3
# ---------------------------------------------------------------------------
road = read("00_docs/roadmaps/pricing.md")
idx = road.find("## 2. The decisions")
road_tail = road[idx:] if idx >= 0 else road
policy = read("01_data/92_archive/pricing_papers_superseded_2026-10-02/01_data_90_INBOX/PRICING_POLICY_PAPER_2026-09-19_REV3.md")

write(
    "01_PRICING.md",
    "\n".join(
        [
            "# Project 1 — Price revision (multi-hour brief)",
            "",
            "Read with `04_DATA_TABLES.csv` rows where `table` starts with `pricing_`.",
            "Block-1 checklist is in `00_ASK.md`.",
            "",
            "---",
            "",
            "## A. Measured stack write-up",
            "",
            read("01_data/90_INBOX/PRICING_STACK_APPLIED_2026-09-19.md"),
            "",
            "---",
            "",
            "## B. Pricing roadmap — decisions, queue, closed traps",
            "",
            road_tail,
            "",
            "---",
            "",
            "## C. Claims to CONFIRM / REJECT / UNKNOWN",
            "",
            "1. Whole-book weighted increase **+5.9616%** on 47,617 priced in-scope rows (Jul 2025–Jun 2026).",
            "2. Factor-chain Thailand **−2.45%** was wrong; measured Thailand **+6.31%**.",
            "3. Flat +5% paper (€1.75M) and filed step (€1.65M at 5.9616%) are two proposals — never add.",
            "4. Competitor evidence ~**16.47%** of priced book; +8% cap → at most ~**1.32 points** on whole book.",
            "5. CIS class-factor **+4.85%** vs flat-60%-margin scenario **+31.3%** on same rows — unresolved.",
            "6. ~**12.84%** override rows do not reproduce the price formula.",
            "7. Config JP discount **67.3%** vehicle-parts applied to all Japan; IE may be **73.5%→79.7%**.",
            "8. IML “around **3%**” vs our **5.9616%** is open reconciliation.",
            "9. Margins reading for reference dealer price decided; packs not rewritten; ~**+22.6%** arithmetic consequence.",
            "10. FX **178.5** is applied, not chosen.",
            "",
            "---",
            "",
            "## D. Full pricing policy paper (REV3)",
            "",
            policy,
            "",
        ]
    ),
)

# ---------------------------------------------------------------------------
# 02 PARTS FAMILY — full corpus
# ---------------------------------------------------------------------------
write(
    "02_PARTS_FAMILY.md",
    "\n".join(
        [
            "# Project 2 — Parts family / catalogue / Japanese codes (multi-hour brief)",
            "",
            "Outward: **catalogue product tree** vs **parts family**. Never “AIM v2” to management.",
            "Block-2 checklist is in `00_ASK.md`. CSV tables: `jp_codes`, `classification`, `benchmark_*`.",
            "",
            "---",
            "",
            "## Part I — Switch classification files now?",
            "",
            read("01_data/90_INBOX/GPT_REVIEW_classification_switch_20260920.md"),
            "",
            "---",
            "",
            "## Part II — Settled position (ZKK / ZUK / HKK / EPLE)",
            "",
            read("01_data/90_INBOX/SETTLED_POSITION_JP_CODES_2026-09-20.md"),
            "",
            "---",
            "",
            "## Part III — Full ZKK/ZUK measurement brief",
            "",
            read("01_data/90_INBOX/GPT_REVIEW_ZKK_ZUK_and_AIM_v2_20260920.md"),
            "",
            "---",
            "",
            "## Part IV — Reproducibility audit (independent re-measure)",
            "",
            read("01_data/90_INBOX/REPRODUCIBILITY_AUDIT_JP_CODES_2026-09-20.md"),
            "",
            "---",
            "",
            "## Part V — ZKK code dictionary (code-level fragmentation)",
            "",
            read("01_data/90_INBOX/ZKK_CODE_DICTIONARY_2026-09-20.md"),
            "",
            "---",
            "",
            "## Part VI — HKK system review",
            "",
            read("01_data/90_INBOX/HKK_SYSTEM_REVIEW_2026-09-20.md"),
            "",
        ]
    ),
)

# ---------------------------------------------------------------------------
# 03 AFTERSALES
# ---------------------------------------------------------------------------
dec = read("01_data/90_INBOX/DECISIONS_AWAITING_JEROME_2026-09-19.md")
# keep header + D08/D24/D03 related chunks by including full register — 60KB is fine for hours
warranty = read("01_data/90_INBOX/_warranty_data_what_else_it_carries_20260918.md")
ld_note = read("01_data/90_INBOX/_ld_weight_class_and_wallet_correction_20260918.md")

write(
    "03_AFTERSALES_CEILING.md",
    "\n".join(
        [
            "# Project 3 — Aftersales ceiling & opportunity (multi-hour brief)",
            "",
            "Live published network anchor (ceiling file, 2025): ~**55.7%** on **€55.25M**.",
            "Retired: **51.1%** / **€60.22M**. Israel: UMI 1797 ≠ UTI 1799.",
            "Block-3 checklist is in `00_ASK.md`. Recompute from CSV — do not trust this prose alone.",
            "",
            "---",
            "",
            "## A. Agent verdict (challenge every line)",
            "",
            "1. Ceiling = target spend per truck × trucks in service; coverage = billed ÷ ceiling.",
            "2. ITUK 32.4% vs ~47% was light trucks priced heavy; after split ~45.6% on ~€12.21M; only ITUK moved.",
            "3. Opportunity heroes = clutch/brake euro gaps, not oil-filter method stories.",
            "4. Eight markets on flat €250/truck hold ~40% of ceiling — disclose always.",
            "5. Portugal parc light share 0.6364; shipment mix ~0.69 different; rebuild not authorised.",
            "6. Primary lens = total capture; unit counts alone are not findings.",
            "7. Mileage assumptions can inflate/deflate expected demand (UK light vs UTI heavy).",
            "8. Addressable kept at 100%; clutch AT/MT not measurable from VIN.",
            "9. Fleet-figure pack rebuild approved in principle, not run; new ceiling number separate.",
            "",
            "---",
            "",
            "## B. GPS / PMS alignment (full)",
            "",
            read("00_docs/GPS_PMS_ALIGNMENT_20260917.md"),
            "",
            "---",
            "",
            "## C. GPS truth report (full)",
            "",
            read("00_docs/GPS_PMS_TRUTH_REPORT_20260917.md"),
            "",
            "---",
            "",
            "## D. LD / light-heavy correction note",
            "",
            ld_note,
            "",
            "---",
            "",
            "## E. Warranty — what else the claim files carry (limits)",
            "",
            warranty,
            "",
            "---",
            "",
            "## F. Decisions register (open / decided — ceiling & packs)",
            "",
            dec,
            "",
            "---",
            "",
            "## G. Claims to CONFIRM / REJECT / UNKNOWN",
            "",
            "1. Network 2025 ceiling ≈ €55.253M, captured ≈ €30.76M → ~55.7%.",
            "2. Flat-€250 markets = 8, share ≈ 40.3%.",
            "3. ITUK GPS ≈ 45.6% on ≈ €12.21M.",
            "4. Top gaps clutch disc / brake pad / brake shoe (verify from CSV).",
            "5. Portugal n35_share live file = 0.6364 on imotors_parc_bands.",
            "6. UTI ≠ UMI; IDS Israel = UMI only.",
            "7. Warranty cannot prove maintenance intervals.",
            "8. Rebuilding packs on a re-based ceiling while share-accept is open is wrong.",
            "",
        ]
    ),
)

# ---------------------------------------------------------------------------
# 04 DATA — fat multi-table
# ---------------------------------------------------------------------------
print("  building 04_DATA_TABLES.csv …")
chunks: list[pd.DataFrame] = []


def tag(df: pd.DataFrame, table: str) -> pd.DataFrame:
    out = df.copy()
    out.insert(0, "table", table)
    return out


# wallet all years
ww = pd.read_csv(ROOT / "01_data/00_derived/wallet_waterfall.csv")
ww["rate_per_uio"] = ww["theoretical_wallet_eur"] / ww["uio_units"]
chunks.append(tag(ww, "wallet_all_years"))

w25 = ww[ww["year"] == 2025].copy()
ceil = float(w25["theoretical_wallet_eur"].sum())
capt = float(w25["captured_total_eur"].sum())
flat = w25[(w25["rate_per_uio"] - 250).abs() < 0.05]
rollup = pd.DataFrame(
    [
        {
            "metric": "network_ceiling_eur",
            "value": ceil,
            "note": "sum theoretical_wallet_eur year=2025",
        },
        {
            "metric": "network_captured_total_eur",
            "value": capt,
            "note": "",
        },
        {
            "metric": "network_gps_pct",
            "value": 100 * capt / ceil,
            "note": "captured/ceiling",
        },
        {
            "metric": "fleet_uio_units",
            "value": float(w25["uio_units"].sum()),
            "note": "",
        },
        {
            "metric": "flat250_market_count",
            "value": float(len(flat)),
            "note": ",".join(flat["distributor_code"].astype(str)),
        },
        {
            "metric": "flat250_share_of_ceiling_pct",
            "value": 100 * float(flat["theoretical_wallet_eur"].sum()) / ceil,
            "note": "",
        },
    ]
)
chunks.append(tag(rollup, "wallet_rollup_2025"))

# gps
gps = pd.read_csv(ROOT / "01_data/00_derived/gps_spu_by_distributor.csv")
chunks.append(tag(gps, "gps_spu_by_distributor"))

# opportunity full
om = pd.read_csv(ROOT / "01_data/00_derived/pms_opportunity_matrix.csv")
chunks.append(tag(om, "opportunity_matrix_full"))

# opportunity network by category year
om_net = (
    om.groupby(["year", "pms_category"], as_index=False)
    .agg(
        revenue_gap_eur=("revenue_gap_eur", "sum"),
        tam_eur=("tam_eur", "sum"),
        markets=("distributor_code", "nunique"),
        avg_capture_total=("capture_rate_total", "mean"),
    )
    .sort_values(["year", "revenue_gap_eur"], ascending=[True, False])
)
chunks.append(tag(om_net, "opportunity_network_by_category_year"))

# capture — full file is useful for hours of work
cap = pd.read_csv(ROOT / "01_data/00_derived/pms_capture_by_db_year.csv")
chunks.append(tag(cap, "pms_capture_by_db_year"))

# mix
mix_path = ROOT / "01_data/00_derived/mix_genuine_bvp_pms.csv"
if mix_path.exists():
    chunks.append(tag(pd.read_csv(mix_path), "mix_genuine_bvp_pms"))

# n35 share
share = pd.read_csv(ROOT / "03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv")
chunks.append(tag(share, "n35_share"))

# benchmark tables
bench = ROOT / "01_data/90_INBOX/_classification_benchmark_tables_20260920.csv"
if bench.exists():
    chunks.append(tag(pd.read_csv(bench), "benchmark_tables"))

# pricing stack JSON → flat rows
ps = json.loads(
    (ROOT / "01_data/00_derived/pricing_stack_applied_2026-09-19.json").read_text(
        encoding="utf-8"
    )
)
prows = []
prows.append(
    {
        "section": "whole_book",
        "label": "weighted_increase_pct",
        "value": ps["whole_book"]["weighted_increase"] * 100,
        "rows": ps["method"]["recipe_rows"],
        "note": "reproduces published index",
    }
)
prows.append(
    {
        "section": "whole_book",
        "label": "japan_pct",
        "value": ps["whole_book"]["japan"] * 100,
        "rows": "",
        "note": "",
    }
)
prows.append(
    {
        "section": "whole_book",
        "label": "thailand_pct",
        "value": ps["whole_book"]["thailand"] * 100,
        "rows": "",
        "note": "",
    }
)
prows.append(
    {
        "section": "live_inputs",
        "label": "fx",
        "value": ps["live_inputs"]["fx"],
        "rows": "",
        "note": "applied not chosen",
    }
)
prows.append(
    {
        "section": "live_inputs",
        "label": "discount_J_pct",
        "value": ps["live_inputs"]["discount_live"]["J"] * 100,
        "rows": "",
        "note": "vehicle parts",
    }
)
prows.append(
    {
        "section": "live_inputs",
        "label": "discount_T_pct",
        "value": ps["live_inputs"]["discount_live"]["T"] * 100,
        "rows": "",
        "note": "",
    }
)
prows.append(
    {
        "section": "figure_replaced",
        "label": "earlier_thailand_pct_WRONG",
        "value": ps["figure_replaced"]["earlier_thailand"] * 100,
        "rows": "",
        "note": "factor chain",
    }
)
for src in ps["by_source"]:
    prows.append(
        {
            "section": "by_source",
            "label": src["label"],
            "value": src["weighted_increase"] * 100,
            "rows": src["rows"],
            "billed_eur": src["billed_eur"],
            "weight_share_pct": src["weight_share"] * 100,
            "note": src["source"],
        }
    )
for mkt, body in ps["markets"].items():
    prows.append(
        {
            "section": "by_market",
            "label": mkt,
            "value": body["weighted_increase"] * 100,
            "rows": body["rows"],
            "billed_eur": body["billed_eur"],
            "part_numbers": body.get("part_numbers", ""),
            "japan_pct": (body.get("japan") or 0) * 100
            if isinstance(body.get("japan"), (int, float))
            else "",
            "thailand_pct": (body.get("thailand") or 0) * 100
            if isinstance(body.get("thailand"), (int, float))
            else "",
            "note": body.get("note", ""),
        }
    )
prows.append(
    {
        "section": "proposals",
        "label": "flat_5pct_paper_eur",
        "value": 1749680.47,
        "rows": "",
        "note": "paper only",
    }
)
prows.append(
    {
        "section": "proposals",
        "label": "published_step_eur",
        "value": 1652140.71,
        "rows": "",
        "note": "5.9616% on same base",
    }
)
prows.append(
    {
        "section": "proposals",
        "label": "in_scope_billed_eur",
        "value": 34993609.39,
        "rows": 48653,
        "note": "15872 PNs",
    }
)
prows.append(
    {
        "section": "proposals",
        "label": "competitor_cover_pct",
        "value": 16.47,
        "rows": "",
        "note": "T1-T3",
    }
)
prows.append(
    {
        "section": "proposals",
        "label": "max_points_at_8pct_cap",
        "value": 1.32,
        "rows": "",
        "note": "evidence only ceiling",
    }
)
chunks.append(tag(pd.DataFrame(prows), "pricing_stack"))

# classification / jp claim rows
code_facts = [
    ("jp_codes", "zkk_distinct", 142, "3 chars, 0 blank / 536854"),
    ("jp_codes", "zuk_distinct", 359, "5 chars DDCDD, 0 blank"),
    ("jp_codes", "hkk_distinct", 125, "4 chars"),
    ("jp_codes", "zkk_euro_cover_pct", 88.11, "of spine L12M billed"),
    ("jp_codes", "zkk_hit_eur", 46183083.72, ""),
    ("jp_codes", "spine_l12m_eur", 52414407.82, ""),
    ("jp_codes", "blank_jp_rows", 25689, "not in Japan price file"),
    ("jp_codes", "blank_jp_eur", 6231324, "11.89%"),
    ("jp_codes", "zkk_equals_full_hkk", 0, "of 142"),
    ("jp_codes", "zkk_match_hkk_prefix_live", 5, "of 142"),
    ("jp_codes", "zuk_equals_hkk_or_zkk", 0, "of 359"),
    ("jp_codes", "zkk_114_XC_pct", 77.40, "not 100"),
    ("jp_codes", "zkk_275_share_covered_pct", 46.77, "415 leading nouns"),
    ("jp_codes", "zkk_fragmented_share_pct", 97.86, "46 of 51 large codes"),
    ("jp_codes", "benchmark_purity_published", 82.59, "UNUSABLE blank share"),
    ("jp_codes", "benchmark_purity_jp_desc_zkk", 12.32, "remeasured"),
    ("classification", "gate_pass", 18, "of 18 — not master sync"),
    ("classification", "residual_share_pct", 5.74, "catalogue Other/review"),
    ("classification", "classification_rows", 164667, "file still 2026-09-18 content"),
    ("classification", "true_open_pns", 9164, "master after patches"),
    ("classification", "true_open_l12m_eur", 114516, ""),
    ("classification", "eq_needs_human_pns", 360, "of 744 FOUND"),
    ("classification", "switch_today", 0, "0=do not switch"),
]
chunks.append(
    tag(
        pd.DataFrame(
            [{"domain": a, "metric": b, "value": c, "note": d} for a, b, c, d in code_facts]
        ),
        "classification_jp_claims",
    )
)

# Write as one CSV with heterogeneous columns — use to_csv on concat with sort=False
# Better: write sections sequentially with a blank line? CSV can't. Use long format.
# For GPT, one wide concat is messy. Write a long-format unified frame:

long_rows = []
for df in chunks:
    table = df["table"].iloc[0]
    # melt-ish: store each row as JSON-ish flat via column dump
    for _, row in df.drop(columns=["table"]).iterrows():
        rec = {"table": table}
        for i, (col, val) in enumerate(row.items()):
            if pd.isna(val):
                continue
            rec[f"c{i:02d}_name"] = str(col)
            rec[f"c{i:02d}_val"] = val
        long_rows.append(rec)

# Actually long format with 02d gets huge column count. Simpler: keep native CSVs
# concatenated with a separator row approach — GPT handles better as one file with
# table column and original columns where possible.

# Rebuild: write multiple native tables stacked with only shared meta columns + payload JSON
payload_rows = []
for df in chunks:
    table = str(df["table"].iloc[0])
    body = df.drop(columns=["table"])
    for rec in body.to_dict(orient="records"):
        # stringify nested carefully
        clean = {}
        for k, v in rec.items():
            if pd.isna(v):
                clean[k] = ""
            elif isinstance(v, (float, int)):
                clean[k] = v
            else:
                clean[k] = str(v)
        payload_rows.append({"table": table, "payload_json": json.dumps(clean, default=str)})

out_df = pd.DataFrame(payload_rows)
out_path = OUT / "04_DATA_TABLES.csv"
out_df.to_csv(out_path, index=False)
print(f"  {'04_DATA_TABLES.csv':30s} {out_path.stat().st_size / 1024:8.1f} KB  rows={len(out_df)}")

# Also write a companion readable wide extract for the key small tables as part of SAME file?
# User asked max 5 files — payload_json is analyzable. For hours of work it's OK but painful.
# Better hybrid: write wide files for small tables inline by using separate sections in ONE csv
# with repeating headers — ugly.
# Prefer: dump a "tidy" version where common analysis tables stay wide.

# Rebuild 04 as several wide CSVs joined by blank-line markers in a .txt? Still one file.
# Use Excel? User said files — CSV is fine. GPT can parse payload_json.
# For human/GPT ease, write a second structure: multi-section CSV using comment lines.

lines: list[str] = []
lines.append("# ISZE GPT review data tables — multi-section CSV")
lines.append("# Each section starts with # TABLE=<name> then a normal header row")
lines.append("# Recompute from these sections in Blocks 1–3")
for df in chunks:
    table = str(df["table"].iloc[0])
    body = df.drop(columns=["table"])
    lines.append("")
    lines.append(f"# TABLE={table} rows={len(body)} cols={len(body.columns)}")
    # csv fragment
    frag = body.to_csv(index=False)
    lines.append(frag.rstrip("\n"))

multi = OUT / "04_DATA_TABLES.csv"
multi.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print(f"  rewritten multi-section CSV {multi.stat().st_size / 1024:8.1f} KB")

# cleanup old thin file
old = OUT / "04_LOCKED_NUMBERS.csv"
if old.exists():
    old.unlink()

# remove any rebuild scripts from pack folder
for junk in OUT.glob("_*.py"):
    junk.unlink()
    print(f"  removed {junk.name}")

print("DONE — pack contents:")
total = 0
for p in sorted(OUT.iterdir()):
    if p.is_file():
        total += p.stat().st_size
        print(f"  {p.name:30s} {p.stat().st_size / 1024:8.1f} KB")
print(f"  TOTAL {total / 1024:8.1f} KB  ({total / 1024 / 1024:.2f} MB)")
