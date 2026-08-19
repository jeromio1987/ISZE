"""
Forecast-weight scaffold for Book B (Mode B · provisional defaults).

Continues without model-mix / gearbox / market / ambition-% answers.
Does NOT write an official Book B alloc run id — sensitivity is PROVISIONAL / diagnostic only.

Outputs (stamp 20260812):
  01_data/00_derived/forecast_weight_scaffold_20260812.csv (+ .meta.json)
  01_data/00_derived/forecast_weight_sensitivity_provisional_20260812.csv
  01_data/00_derived/apl_overlap_ituk_p700_rg21_20260812.csv
  01_data/00_derived/apl_p700_only_20260812.csv
  01_data/00_derived/apl_rg21_only_20260812.csv
  Copies under 01_data/01_Pricing/
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ROOT / "01_data/00_derived"
PRICING = ROOT / "01_data/01_Pricing"
STAMP = "20260812"

SEEDS = DERIVED / f"apl_pn_list_book_b_seeds_{STAMP}.csv"
UTI_REC = DERIVED / f"uti_p700_recommended_parts_list_{STAMP}.csv"
SALES_FACT = DERIVED / "sales_fact.parquet"
SIM_L12M = DERIVED / "pricing_sim_pr00_l12m.parquet"

OUT_SCAFFOLD = DERIVED / f"forecast_weight_scaffold_{STAMP}.csv"
OUT_SENS = DERIVED / f"forecast_weight_sensitivity_provisional_{STAMP}.csv"
OUT_OVERLAP = DERIVED / f"apl_overlap_ituk_p700_rg21_{STAMP}.csv"
OUT_P700_ONLY = DERIVED / f"apl_p700_only_{STAMP}.csv"
OUT_RG21_ONLY = DERIVED / f"apl_rg21_only_{STAMP}.csv"
OUT_META = DERIVED / f"forecast_weight_scaffold_{STAMP}.meta.json"

# Provisional growth factors (plan midpoints / locked UTI scale) — NOT signed off
GF_RG21_INTERVAL = 1.24  # mid of 1.15–1.33
GF_RG21_FIRST_FAIL = 1.25  # mid of 1.10–1.40
GF_P700_CARRYOVER = 1.05  # mid of ~1.0–1.1
GF_BASE = 1.0
UTI_NETWORK_SCALE = 1.25  # locked 800→1000; only where on_uti_p700_recommended

INTERVAL_FAMS = {"filter", "scr_dpd"}
FIRST_FAIL_FAMS = {"brake", "clutch", "sensor", "turbo", "injector", "belt"}
NEW_ONLY_HINT = re.compile(
    r"\b(ISIM|DCT|ADAS|BSIS|DWS|TSR|TPMS|LED|HARNESS|CONTROLLER|ECU)\b", re.I
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pack_flags(source_packs: str) -> tuple[bool, bool, bool]:
    packs = {p.strip() for p in str(source_packs or "").split("|") if p.strip()}
    return ("ITUK_APL" in packs, "P700" in packs, "RG21_2.2L" in packs)


def fam_set(family_hint: str) -> set[str]:
    return {x.strip() for x in str(family_hint or "").split("|") if x.strip()}


def load_l12m_eur() -> tuple[pd.Series, pd.Series, dict]:
    """Prefer sales_fact rolling L12M net €; fill gaps from sim qty×SP2025."""
    meta: dict = {}
    sf = pd.read_parquet(
        SALES_FACT, columns=["billing_date", "part_number", "net_sales_value"]
    )
    sf["billing_date"] = pd.to_datetime(sf["billing_date"])
    mx = sf["billing_date"].max()
    cut = mx - pd.Timedelta(days=365)
    l12 = sf.loc[sf["billing_date"] >= cut].copy()
    l12["pn"] = l12["part_number"].astype(str).str.strip()
    sales_eur = l12.groupby("pn", sort=False)["net_sales_value"].sum()
    sales_eur = sales_eur[sales_eur > 0]
    meta["sales_l12m_window"] = {
        "from": cut.date().isoformat(),
        "to": mx.date().isoformat(),
        "unique_pn": int(sales_eur.shape[0]),
        "total_eur": float(sales_eur.sum()),
    }

    sim = pd.read_parquet(
        SIM_L12M, columns=["part_number", "qty_l12m", "sp_eur_2025"]
    )
    sim["pn"] = sim["part_number"].astype(str).str.strip()
    sim["sim_eur"] = (
        pd.to_numeric(sim["qty_l12m"], errors="coerce").fillna(0)
        * pd.to_numeric(sim["sp_eur_2025"], errors="coerce").fillna(0)
    )
    sim_eur = sim.groupby("pn", sort=False)["sim_eur"].sum()
    sim_eur = sim_eur[sim_eur > 0]
    meta["sim_l12m"] = {
        "unique_pn": int(sim_eur.shape[0]),
        "total_eur_proxy": float(sim_eur.sum()),
        "definition": "qty_l12m * sp_eur_2025 from pricing_sim_pr00_l12m",
    }
    return sales_eur, sim_eur, meta


def assign_growth(
    *,
    in_ituk: bool,
    in_p700: bool,
    in_rg21: bool,
    on_uti: bool,
    family: str,
    description: str,
    has_l12m: bool,
) -> tuple[float, str, str, str]:
    """
    Returns growth_factor, bucket, seed_status, rule_note.
    seed_status: '' | NEED_SEED | HAS_L12M
    """
    fams = fam_set(family)
    desc = str(description or "")
    notes: list[str] = []
    bucket = "other_gf_1_0"
    gf = GF_BASE

    if in_rg21 and (fams & INTERVAL_FAMS):
        gf = GF_RG21_INTERVAL
        bucket = "rg21_interval"
        notes.append(f"RG21 interval fam→{GF_RG21_INTERVAL}")
    elif in_rg21 and (fams & FIRST_FAIL_FAMS):
        gf = GF_RG21_FIRST_FAIL
        bucket = "rg21_first_failure"
        notes.append(f"RG21 first-fail fam→{GF_RG21_FIRST_FAIL}")
    elif in_p700 and not has_l12m and (
        NEW_ONLY_HINT.search(desc)
        or (not in_ituk and not in_rg21)
        or "accessory" in fams
    ):
        gf = GF_BASE  # weight comes from seed € later, not L12M
        bucket = "p700_new_only_seed"
        notes.append("P700 new-only / no L12M → NEED_SEED")
    elif in_p700 and (in_ituk or has_l12m) and not (in_rg21 and (fams & (INTERVAL_FAMS | FIRST_FAIL_FAMS))):
        gf = GF_P700_CARRYOVER
        bucket = "p700_carryover"
        notes.append(f"P700 carryover→{GF_P700_CARRYOVER}")
    elif in_p700 and not has_l12m:
        gf = GF_BASE
        bucket = "p700_new_only_seed"
        notes.append("P700 no L12M → NEED_SEED")

    if on_uti:
        gf = round(gf * UTI_NETWORK_SCALE, 6)
        notes.append(f"UTI P700 recommended ×{UTI_NETWORK_SCALE}")
        if bucket == "other_gf_1_0":
            bucket = "uti_p700_network_scale"
        else:
            bucket = f"{bucket}+uti_x1_25"

    seed_status = ""
    if has_l12m:
        seed_status = "HAS_L12M"
    elif bucket.startswith("p700_new_only") or (in_p700 and not has_l12m and on_uti):
        seed_status = "NEED_SEED"
    elif in_p700 and not has_l12m:
        seed_status = "NEED_SEED"

    return gf, bucket, seed_status, "; ".join(notes) if notes else "default_1_0"


def main() -> None:
    seeds = pd.read_csv(SEEDS, dtype=str)
    seeds["pn"] = seeds["part_number"].astype(str).str.strip()

    uti = pd.read_csv(UTI_REC, dtype=str)
    uti["pn"] = uti["part_number"].astype(str).str.strip()
    uti_map = uti.drop_duplicates("pn").set_index("pn")
    uti_set = set(uti_map.index)

    sales_eur, sim_eur, l12_meta = load_l12m_eur()

    rows = []
    for r in seeds.itertuples(index=False):
        pn = r.pn
        packs = str(getattr(r, "source_packs", "") or "")
        in_ituk, in_p700, in_rg21 = pack_flags(packs)
        on_uti = pn in uti_set
        fam = str(getattr(r, "family_hint", "") or "")
        desc = str(getattr(r, "description", "") or "")

        l12m = None
        l12m_src = ""
        if pn in sales_eur.index:
            l12m = float(sales_eur.loc[pn])
            l12m_src = "sales_fact_l12m"
        elif pn in sim_eur.index:
            l12m = float(sim_eur.loc[pn])
            l12m_src = "pricing_sim_qty_x_sp2025"

        has_l12m = l12m is not None and l12m > 0
        gf, bucket, seed_status, rule_note = assign_growth(
            in_ituk=in_ituk,
            in_p700=in_p700,
            in_rg21=in_rg21,
            on_uti=on_uti,
            family=fam,
            description=desc,
            has_l12m=has_l12m,
        )

        fw = round(l12m * gf, 4) if has_l12m else None
        seed_ph = "NEED_SEED" if seed_status == "NEED_SEED" else ""

        priority = ""
        if on_uti and pn in uti_map.index:
            priority = str(uti_map.at[pn, "qualitative_priority"] or "")

        flag_parts = [
            "PROVISIONAL_DEFAULTS",
            f"in_ituk={int(in_ituk)}",
            f"in_p700={int(in_p700)}",
            f"in_rg21={int(in_rg21)}",
            f"on_uti_p700_recommended={int(on_uti)}",
            f"l12m_src={l12m_src or 'none'}",
            f"bucket={bucket}",
        ]
        if seed_status:
            flag_parts.append(seed_status)
        if str(getattr(r, "shell_lube_out", "0")) in ("1", "True", "true"):
            flag_parts.append("shell_lube_out")

        rows.append(
            {
                "pn": pn,
                "description": desc,
                "packs": packs,
                "family_hint": fam,
                "priority": priority,
                "l12m_eur": round(l12m, 4) if has_l12m else None,
                "growth_factor": gf,
                "forecast_weight_eur": fw,
                "seed_eur_placeholder": seed_ph if seed_ph else None,
                "on_uti_p700_recommended": int(on_uti),
                "book_b_bucket": bucket,
                "growth_rule_note": rule_note,
                "flags": "|".join(flag_parts),
            }
        )

    sc = pd.DataFrame(rows)

    # --- Overlap / only summaries (unique PN universe from seeds) ---
    sc["in_ituk"] = sc["packs"].fillna("").str.contains("ITUK_APL", regex=False)
    sc["in_p700"] = sc["packs"].fillna("").str.contains("P700", regex=False)
    sc["in_rg21"] = sc["packs"].fillna("").str.contains("RG21_2.2L", regex=False)

    overlap_rows = [
        {
            "slice": "ITUK_only",
            "n_pn": int((sc.in_ituk & ~sc.in_p700 & ~sc.in_rg21).sum()),
        },
        {
            "slice": "P700_only",
            "n_pn": int((sc.in_p700 & ~sc.in_ituk & ~sc.in_rg21).sum()),
        },
        {
            "slice": "RG21_only",
            "n_pn": int((sc.in_rg21 & ~sc.in_ituk & ~sc.in_p700).sum()),
        },
        {
            "slice": "ITUK_and_P700_not_RG21",
            "n_pn": int((sc.in_ituk & sc.in_p700 & ~sc.in_rg21).sum()),
        },
        {
            "slice": "ITUK_and_RG21_not_P700",
            "n_pn": int((sc.in_ituk & sc.in_rg21 & ~sc.in_p700).sum()),
        },
        {
            "slice": "P700_and_RG21_not_ITUK",
            "n_pn": int((sc.in_p700 & sc.in_rg21 & ~sc.in_ituk).sum()),
        },
        {
            "slice": "all_three",
            "n_pn": int((sc.in_ituk & sc.in_p700 & sc.in_rg21).sum()),
        },
        {
            "slice": "on_uti_p700_recommended",
            "n_pn": int(sc.on_uti_p700_recommended.sum()),
        },
        {
            "slice": "universe_unique",
            "n_pn": int(len(sc)),
        },
    ]
    overlap = pd.DataFrame(overlap_rows)

    p700_only = sc.loc[sc.in_p700 & ~sc.in_ituk & ~sc.in_rg21].copy()
    rg21_only = sc.loc[sc.in_rg21 & ~sc.in_ituk & ~sc.in_p700].copy()

    # --- PROVISIONAL sensitivity (rows with L12M only) ---
    w = sc.loc[sc["l12m_eur"].notna() & (sc["l12m_eur"] > 0)].copy()
    sum_l12 = float(w["l12m_eur"].sum())
    sum_fw = float(w["forecast_weight_eur"].sum())
    avg_g = (sum_fw / sum_l12) if sum_l12 else float("nan")

    def share(mask: pd.Series, col: str) -> float:
        sub = w.loc[mask, col].sum()
        tot = w[col].sum()
        return float(sub / tot) if tot else 0.0

    launch_mask = (
        w["on_uti_p700_recommended"].eq(1)
        | w["in_rg21"]
        | w["book_b_bucket"].str.contains("p700|rg21|uti", case=False, na=False)
    )

    sens_rows = [
        {
            "label": "PROVISIONAL_diagnostic",
            "n_pn_with_l12m": int(len(w)),
            "sum_l12m_eur": round(sum_l12, 2),
            "sum_forecast_weight_eur": round(sum_fw, 2),
            "mean_growth_factor_weighted": round(avg_g, 6),
            "book_a_ambition_pct": 3.0,
            "book_a_note": "Locked +3% on past L12M — not overwritten",
            "scenario_book_b_ambition_pct": None,
            "scenario_note": "baseline weight mass",
            "share_l12m_launch_tagged": round(share(launch_mask, "l12m_eur"), 6),
            "share_fw_launch_tagged": round(share(launch_mask, "forecast_weight_eur"), 6),
            "share_l12m_uti_rec": round(share(w.on_uti_p700_recommended.eq(1), "l12m_eur"), 6),
            "share_fw_uti_rec": round(
                share(w.on_uti_p700_recommended.eq(1), "forecast_weight_eur"), 6
            ),
            "share_l12m_rg21": round(share(w.in_rg21, "l12m_eur"), 6),
            "share_fw_rg21": round(share(w.in_rg21, "forecast_weight_eur"), 6),
        }
    ]
    for amb in (4.0, 5.0):
        # Uniform Δ under FW = ambition by construction; report weight shift vs Book A
        sens_rows.append(
            {
                "label": f"PROVISIONAL_ambition_+{amb:g}pct",
                "n_pn_with_l12m": int(len(w)),
                "sum_l12m_eur": round(sum_l12, 2),
                "sum_forecast_weight_eur": round(sum_fw, 2),
                "mean_growth_factor_weighted": round(avg_g, 6),
                "book_a_ambition_pct": 3.0,
                "book_a_note": "Compare only — Book A stays +3% on L12M",
                "scenario_book_b_ambition_pct": amb,
                "scenario_note": (
                    f"DIAGNOSTIC ONLY — not an alloc run. "
                    f"If Book B solved sum(fw*Δ)/sum(fw)={amb:g}%, "
                    f"launch-tagged FW share={share(launch_mask, 'forecast_weight_eur'):.1%} "
                    f"vs L12M share={share(launch_mask, 'l12m_eur'):.1%}; "
                    f"weight mass vs Book A = {avg_g:.3f}× L12M "
                    f"(mean growth_factor on €)."
                ),
                "share_l12m_launch_tagged": round(share(launch_mask, "l12m_eur"), 6),
                "share_fw_launch_tagged": round(share(launch_mask, "forecast_weight_eur"), 6),
                "share_l12m_uti_rec": round(share(w.on_uti_p700_recommended.eq(1), "l12m_eur"), 6),
                "share_fw_uti_rec": round(
                    share(w.on_uti_p700_recommended.eq(1), "forecast_weight_eur"), 6
                ),
                "share_l12m_rg21": round(share(w.in_rg21, "l12m_eur"), 6),
                "share_fw_rg21": round(share(w.in_rg21, "forecast_weight_eur"), 6),
            }
        )
    sens = pd.DataFrame(sens_rows)

    # Drop helper cols from scaffold export
    out_cols = [
        "pn",
        "description",
        "packs",
        "family_hint",
        "priority",
        "l12m_eur",
        "growth_factor",
        "forecast_weight_eur",
        "seed_eur_placeholder",
        "on_uti_p700_recommended",
        "book_b_bucket",
        "growth_rule_note",
        "flags",
    ]
    scaffold = sc[out_cols].copy()

    n_l12m = int(scaffold["l12m_eur"].notna().sum())
    n_need_seed = int((scaffold["seed_eur_placeholder"] == "NEED_SEED").sum())
    n_uti = int(scaffold["on_uti_p700_recommended"].sum())

    meta = {
        "built_utc": utc_now(),
        "stamp": STAMP,
        "status": "PROVISIONAL_defaults_continued_without_mix",
        "book_a": "Locked +3% on past L12M — not overwritten; no new official alloc id",
        "book_b": "Scaffold only; ambition +4/+5 are diagnostic scenarios",
        "inputs": {
            "seeds": str(SEEDS),
            "uti_recommended": str(UTI_REC),
            "sales_fact": str(SALES_FACT),
            "pricing_sim": str(SIM_L12M),
        },
        "outputs": {
            "scaffold": str(OUT_SCAFFOLD),
            "sensitivity": str(OUT_SENS),
            "overlap": str(OUT_OVERLAP),
            "p700_only": str(OUT_P700_ONLY),
            "rg21_only": str(OUT_RG21_ONLY),
        },
        "growth_factor_defaults_provisional": {
            "rg21_interval": GF_RG21_INTERVAL,
            "rg21_first_failure": GF_RG21_FIRST_FAIL,
            "p700_carryover": GF_P700_CARRYOVER,
            "uti_network_scale_when_recommended": UTI_NETWORK_SCALE,
            "base": GF_BASE,
        },
        "l12m": l12_meta,
        "counts": {
            "scaffold_rows": int(len(scaffold)),
            "with_l12m_eur": n_l12m,
            "need_seed": n_need_seed,
            "on_uti_p700_recommended": n_uti,
            "l12m_from_sales_fact": int(
                scaffold["flags"].str.contains("l12m_src=sales_fact_l12m").sum()
            ),
            "l12m_from_sim_fill": int(
                scaffold["flags"].str.contains("l12m_src=pricing_sim_qty_x_sp2025").sum()
            ),
            "sum_l12m_eur": round(sum_l12, 2),
            "sum_forecast_weight_eur": round(sum_fw, 2),
            "mean_growth_factor_weighted": round(avg_g, 6),
        },
        "bucket_counts": scaffold["book_b_bucket"].value_counts().to_dict(),
        "overlap_slices": overlap.to_dict(orient="records"),
        "provisional_one_liners": {
            "plus_4": (
                f"PROVISIONAL +4%: on {n_l12m:,} PNs with L12M EUR "
                f"({sum_l12:,.0f} EUR), mean g={avg_g:.3f}; "
                f"launch-tagged weight share L12M->FW "
                f"{share(launch_mask, 'l12m_eur'):.1%}->{share(launch_mask, 'forecast_weight_eur'):.1%} "
                f"- not an official alloc."
            ),
            "plus_5": (
                f"PROVISIONAL +5%: same weight table; ambition would be "
                f"sum(fw*d)/sum(fw)=5% (diagnostic). UTI-rec FW share="
                f"{share(w.on_uti_p700_recommended.eq(1), 'forecast_weight_eur'):.1%} "
                f"vs L12M {share(w.on_uti_p700_recommended.eq(1), 'l12m_eur'):.1%}."
            ),
        },
        "parked": [
            "per-model-tonnage qty",
            "locked Book B ambition %",
            "Shell / lube",
            "gearbox / market mix of 800→1000",
        ],
    }

    scaffold.to_csv(OUT_SCAFFOLD, index=False)
    sens.to_csv(OUT_SENS, index=False)
    overlap.to_csv(OUT_OVERLAP, index=False)
    p700_only[out_cols].to_csv(OUT_P700_ONLY, index=False)
    rg21_only[out_cols].to_csv(OUT_RG21_ONLY, index=False)
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Mirror under Pricing
    for src in (OUT_SCAFFOLD, OUT_SENS, OUT_OVERLAP, OUT_P700_ONLY, OUT_RG21_ONLY, OUT_META):
        dest = PRICING / src.name
        dest.write_bytes(src.read_bytes())

    print(json.dumps(meta["counts"], indent=2))
    print("one_liners:")
    print(meta["provisional_one_liners"]["plus_4"])
    print(meta["provisional_one_liners"]["plus_5"])
    print("wrote", OUT_SCAFFOLD)


if __name__ == "__main__":
    main()
