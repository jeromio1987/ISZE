# -*- coding: utf-8 -*-
"""Build EQ-Hit session pack for 2026-09-19 23:00 — queue only, no AIM apply."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ISZE / "01_data" / "00_derived"
INBOX = ISZE / "01_data" / "90_INBOX"
PRICING = ISZE / "01_data" / "01_Pricing"
STAMP = "20260919"
TZ = ZoneInfo("Europe/Brussels")

EQ_STATUSES = ("needs_eq", "conflict_needs_eq", "eq_last_resort")
STATUS_ORDER = {s: i for i, s in enumerate(EQ_STATUSES)}


def norm_pn(s: object) -> str:
    s = str(s or "").strip().upper()
    if not s or s.lower() in ("nan", "none"):
        return ""
    if s.isdigit():
        return s.zfill(10)
    return s


def main() -> dict:
    residual = pd.read_csv(
        D / "pricing_not_on_aim_spine_residual_AFTER_4signal_agree2_3_20260919.csv",
        dtype=str,
    )
    residual["pn"] = residual["pn"].map(norm_pn)
    residual = residual[residual["pn"] != ""].drop_duplicates("pn", keep="first")

    sig = pd.read_csv(D / "pricing_not_on_aim_4signal_20260919.csv", dtype=str, low_memory=False)
    sig["pn"] = sig["pn"].map(norm_pn)
    sig = sig[sig["pn"] != ""].drop_duplicates("pn", keep="first")

    dim_cols = [c for c in sig.columns if c.startswith("dim_")]
    keep_sig = [
        "pn",
        "description",
        "billed_eur",
        "step_eur",
        "hs6",
        "fig_key",
        "key_no",
        "list_eur",
        "price_class",
        "status",
        "agree_n",
        "strong_n",
        "proposed_aim_l1",
        "proposed_aim_l2",
        "proposed_aim_l3",
        "method",
        "notes",
        "eq_used",
        "n_signals",
        *dim_cols,
    ]
    keep_sig = [c for c in keep_sig if c in sig.columns]

    master = pd.read_csv(
        D / "aim_master_v2.csv",
        dtype=str,
        usecols=["part_number", "fig_no", "fig_key", "key_no", "aim_source", "has_aim"],
    )
    master["pn"] = master["part_number"].map(norm_pn)
    master = master.drop_duplicates("pn", keep="first")

    spine = pd.read_csv(
        D / "_audit_cls_spine.csv",
        dtype=str,
        usecols=["pn", "fig_no", "weight_kg", "hs6"],
    )
    spine["pn"] = spine["pn"].map(norm_pn)
    spine = spine.drop_duplicates("pn", keep="first")

    prior_path = INBOX / "_EQ_HIT_DOUBT_PASS_RESULTS_20260918.csv"
    prior = pd.DataFrame()
    if prior_path.exists():
        prior = pd.read_csv(prior_path, dtype=str)
        prior["pn"] = prior["pn"].map(norm_pn)
        prior = prior.drop_duplicates("pn", keep="first")
        prior = prior.rename(
            columns={
                "eq_status": "prior_eq_status",
                "eq_total": "prior_eq_total",
                "eq_fig_name": "prior_eq_fig_name",
                "eq_part_name": "prior_eq_part_name",
                "eq_catalog": "prior_eq_catalog",
                "verdict": "prior_eq_verdict",
                "proposed_l1": "prior_eq_proposed_l1",
                "proposed_l2": "prior_eq_proposed_l2",
                "proposed_l3": "prior_eq_proposed_l3",
                "notes": "prior_eq_notes",
            }
        )
        prior_cols = [
            "pn",
            "prior_eq_status",
            "prior_eq_total",
            "prior_eq_fig_name",
            "prior_eq_part_name",
            "prior_eq_catalog",
            "prior_eq_verdict",
            "prior_eq_proposed_l1",
            "prior_eq_proposed_l2",
            "prior_eq_proposed_l3",
            "prior_eq_notes",
        ]
        prior = prior[[c for c in prior_cols if c in prior.columns]]

    # Live residual ∩ EQ-needed statuses (agree2/3 already removed from residual)
    q = residual[["pn"]].merge(sig[keep_sig], on="pn", how="inner")
    q = q[q["status"].isin(EQ_STATUSES)].copy()

    # Prefer master fig_no / key when present
    q = q.merge(
        master[["pn", "fig_no", "fig_key", "key_no", "aim_source", "has_aim"]].rename(
            columns={"fig_key": "fig_key_master", "key_no": "key_no_master"}
        ),
        on="pn",
        how="left",
    )
    q = q.merge(
        spine[["pn", "fig_no", "weight_kg", "hs6"]].rename(
            columns={"fig_no": "fig_no_spine", "hs6": "hs6_spine"}
        ),
        on="pn",
        how="left",
    )
    if not prior.empty:
        q = q.merge(prior, on="pn", how="left")

    q["fig_no"] = q["fig_no"].fillna("").replace("", pd.NA)
    q["fig_no"] = q["fig_no"].fillna(q["fig_no_spine"]).fillna("")
    q["fig_key"] = q["fig_key"].fillna("").replace("", pd.NA)
    q["fig_key"] = q["fig_key"].fillna(q["fig_key_master"]).fillna("")
    q["key_no"] = q["key_no"].fillna("").replace("", pd.NA)
    q["key_no"] = q["key_no"].fillna(q["key_no_master"]).fillna("")
    q["hs6"] = q["hs6"].fillna("").replace("", pd.NA)
    q["hs6"] = q["hs6"].fillna(q["hs6_spine"]).fillna("")
    q["weight_kg"] = q["weight_kg"].fillna("")

    q["billed_eur"] = pd.to_numeric(q["billed_eur"], errors="coerce").fillna(0.0)
    q["step_eur"] = pd.to_numeric(q["step_eur"], errors="coerce").fillna(0.0)
    q["list_eur"] = pd.to_numeric(q["list_eur"], errors="coerce")

    q["_status_rank"] = q["status"].map(STATUS_ORDER).fillna(99)
    q = q.sort_values(["billed_eur", "_status_rank"], ascending=[False, True]).reset_index(drop=True)
    q["rank"] = range(1, len(q) + 1)
    q = q.drop(columns=["_status_rank", "fig_no_spine", "fig_key_master", "key_no_master", "hs6_spine"], errors="ignore")

    # Column order for humans
    front = [
        "rank",
        "pn",
        "description",
        "billed_eur",
        "step_eur",
        "status",
        "method",
        "notes",
        "hs6",
        "fig_key",
        "fig_no",
        "key_no",
        "weight_kg",
        "list_eur",
        "price_class",
        "proposed_aim_l1",
        "proposed_aim_l2",
        "proposed_aim_l3",
        "agree_n",
        "strong_n",
        "eq_used",
        "n_signals",
        "aim_source",
        "has_aim",
    ]
    prior_front = [c for c in q.columns if c.startswith("prior_eq_")]
    dim_front = [c for c in q.columns if c.startswith("dim_")]
    ordered = [c for c in front if c in q.columns] + prior_front + dim_front
    ordered += [c for c in q.columns if c not in ordered]
    q = q[ordered]

    # Write CSV / JSON
    INBOX.mkdir(parents=True, exist_ok=True)
    PRICING.mkdir(parents=True, exist_ok=True)
    csv_path = INBOX / f"_EQ_HIT_SESSION_{STAMP}_queue.csv"
    json_path = INBOX / f"_EQ_HIT_SESSION_{STAMP}_queue.json"
    q.to_csv(csv_path, index=False, encoding="utf-8-sig")

    buckets = []
    for st in EQ_STATUSES:
        sub = q[q["status"] == st]
        buckets.append(
            {
                "status": st,
                "pn_count": int(len(sub)),
                "billed_eur": round(float(sub["billed_eur"].sum()), 2),
                "step_eur": round(float(sub["step_eur"].sum()), 2),
            }
        )

    payload = {
        "session": f"EQ_HIT_SESSION_{STAMP}",
        "as_of_local": datetime.now(TZ).isoformat(timespec="seconds"),
        "timezone": "Europe/Brussels",
        "fire_local": f"2026-09-19T23:00:00+02:00",
        "eq_url": "https://isuzu.snaponepc.com/epc/#/",
        "source_residual": str(
            D / "pricing_not_on_aim_spine_residual_AFTER_4signal_agree2_3_20260919.csv"
        ),
        "source_4signal": str(D / "pricing_not_on_aim_4signal_20260919.csv"),
        "aim_apply": False,
        "note": "Lookup / scrape results only. Do not patch aim_master until Jerome says apply.",
        "queue_pn_count": int(len(q)),
        "queue_billed_eur": round(float(q["billed_eur"].sum()), 2),
        "queue_step_eur": round(float(q["step_eur"].sum()), 2),
        "buckets": buckets,
        "rows": json.loads(q.to_json(orient="records", date_format="iso")),
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Excel worklist
    xlsx_path = PRICING / f"EQ_HIT_SESSION_{STAMP}.xlsx"
    overview = pd.DataFrame(
        [
            {"metric": "session", "value": f"EQ_HIT_SESSION_{STAMP}"},
            {"metric": "fire_local", "value": "2026-09-19 23:00 Europe/Brussels"},
            {"metric": "queue_pn_count", "value": len(q)},
            {"metric": "queue_billed_eur", "value": round(float(q["billed_eur"].sum()), 2)},
            {"metric": "queue_step_eur", "value": round(float(q["step_eur"].sum()), 2)},
            {"metric": "eq_url", "value": "https://isuzu.snaponepc.com/epc/#/"},
            {"metric": "aim_apply", "value": "NO — results to inbox only"},
            {
                "metric": "source",
                "value": "post-agree2/3 residual ∩ needs_eq|conflict_needs_eq|eq_last_resort",
            },
        ]
    )
    bucket_df = pd.DataFrame(buckets)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        overview.to_excel(writer, sheet_name="Overview", index=False)
        bucket_df.to_excel(writer, sheet_name="Buckets", index=False)
        q.to_excel(writer, sheet_name="Queue", index=False)

    # Brief
    brief_path = INBOX / f"_EQ_HIT_SESSION_{STAMP}_BRIEF.md"
    top5 = q.head(5)[["rank", "pn", "description", "billed_eur", "status"]]
    top_lines = "\n".join(
        f"| {int(r.rank)} | `{r.pn}` | {str(r.description)[:48]} | {float(r.billed_eur):,.0f} | {r.status} |"
        for r in top5.itertuples(index=False)
    )
    bucket_lines = "\n".join(
        f"| {b['status']} | {b['pn_count']} | {b['billed_eur']:,.2f} |" for b in buckets
    )
    brief = f"""# EQ-Hit session — 19 Sep 2026, 23:00 local

Plain English brief for tonight. **No AIM master apply** from this session.

## What this is

A one-shot lookup pass on Snap-on EQ (Isuzu EPC) for part numbers that are still
**Not on AIM** after the this-morning agree2 / agree3 apply, and that the
five-signal scorer marked as needing EQ.

Live site: https://isuzu.snaponepc.com/epc/#/

## Scope (queue)

| Bucket | PNs | Billed € (L12M) |
|--------|----:|----------------:|
{bucket_lines}
| **Total** | **{len(q)}** | **{float(q['billed_eur'].sum()):,.2f}** |

Tools / MX2 were already stripped before the 4signal score. Agree2 / agree3 rows
are already on `aim_master_v2` and are **not** in this queue.

Ranked by billed € descending. Each row carries description, HS6, figure key /
figure no / key no, weight kg, list €, price class, billed / step €, dimension
labels, five-signal status / method / notes, proposed AIM levels (where any),
and any prior EQ verdict from 18 Sep.

## Top 5 by billed €

| Rank | PN | Description | € | Status |
|-----:|----|-------------|--:|--------|
{top_lines}

## Files

| What | Path |
|------|------|
| This brief | `{brief_path}` |
| Queue CSV | `{csv_path}` |
| Queue JSON | `{json_path}` |
| Excel worklist | `{xlsx_path}` |
| Open pack | `{INBOX / f'OPEN_EQ_HIT_SESSION_{STAMP}.cmd'}` |
| 23:00 runner | `{ISZE / '01_data' / '91_build' / f'run_eq_hit_session_{STAMP}.ps1'}` |
| Agent wake prompt | `{ISZE / '00_docs' / 'agent' / f'EQ_HIT_SESSION_{STAMP}_PROMPT.md'}` |
| Results (written tonight) | `{INBOX / f'_EQ_HIT_SESSION_{STAMP}_RESULTS.csv'}` |
| Session log | `{INBOX / f'_EQ_HIT_SESSION_{STAMP}_log.txt'}` |

## How to run (human or agent)

1. Double-click `OPEN_EQ_HIT_SESSION_{STAMP}.cmd` **or** wait for the 23:00 scheduled task.
2. Sign in to Snap-on EQ if the browser asks (session cookie required — scrape cannot run fully unattended without a logged-in browser).
3. Work the Excel / CSV **top-down by €**.
4. Paste the console scraper from `_eq_hit_doubt_console_scraper_20260918.js` (or the overnight agent equivalent) and feed open PNs from the queue JSON.
5. Write hits to `_EQ_HIT_SESSION_{STAMP}_RESULTS.csv` / `.json` under `90_INBOX` only.

## Do not apply until Jerome says

- Do **not** patch `aim_master_v2.csv`.
- Do **not** run `apply_not_on_aim_*` scripts from this session.
- Results stay in the inbox for review. Apply is a separate, explicit ask.

## Honest limit

EQ lookups need a **logged-in** Snap-on browser tab. The 23:00 runner will always
open the pack + EQ URL and leave an agent wake note. Full unattended scrape only
works if Jerome (or an agent with a live session) is already signed in at fire time.

Built: {datetime.now(TZ).isoformat(timespec="seconds")}
"""
    brief_path.write_text(brief, encoding="utf-8", newline="\n")

    return {
        "pn_count": int(len(q)),
        "billed_eur": round(float(q["billed_eur"].sum()), 2),
        "step_eur": round(float(q["step_eur"].sum()), 2),
        "buckets": buckets,
        "csv": str(csv_path),
        "json": str(json_path),
        "xlsx": str(xlsx_path),
        "brief": str(brief_path),
    }


if __name__ == "__main__":
    info = main()
    print(json.dumps(info, indent=2))
