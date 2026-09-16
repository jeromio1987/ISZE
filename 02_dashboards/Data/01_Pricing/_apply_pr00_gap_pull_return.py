"""Apply Jerome's SAP PR00 gap-pull return into IE40 + year history + enquiry + gap list.

Does NOT re-parse the big EXPORT_ZPR1 / Price_file xlsx — patches derived tables only.
Re-run after any full `build_pricing_enquiry_tables.py` rebuild of pricing_pr00_ie40
(or call apply_pr00_gap_pull_return from that builder).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DER = ISZE / "01_data" / "00_derived"
RETURN_CSV = DER / "pricing_pr00_gap_pull_return_20260812.csv"
RETURN_META = DER / "pricing_pr00_gap_pull_return_20260812.meta.json"
GAP_CSV = DER / "no_pr00_gap_cy2025_ranked.csv"
GAP_META = DER / "no_pr00_gap_cy2025_ranked.meta.json"
SOURCE_TAG = "SAP_Pull_PN_Validity_List_PR00_return_20260812.xlsx"


def norm_pn(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        digits = str(int(value))
    else:
        digits = re.sub(r"\D", "", str(value).strip())
    if len(digits) < 8:
        return None
    return digits.zfill(10)


def load_ok_fills() -> pd.DataFrame:
    ret = pd.read_csv(RETURN_CSV)
    ret["part_number"] = ret["part_number"].map(norm_pn)
    ret = ret[(ret["status"] == "ok") & ret["part_number"].notna()].copy()
    ret["price_eur"] = pd.to_numeric(ret["price_eur"], errors="coerce")
    ret = ret[ret["price_eur"] > 0]
    ret["window_label"] = ret["window_label"].astype(str)
    return ret


def apply_to_ie40(fills: pd.DataFrame) -> dict:
    """Upsert Window_2025 prices into pricing_pr00_ie40.parquet (current list)."""
    path = DER / "pricing_pr00_ie40.parquet"
    pr00 = pd.read_parquet(path)
    w25 = fills[fills["window_label"] == "2025"].copy()
    if w25.empty:
        return {"updated": 0, "appended": 0}

    # one price per PN (max if dups)
    w25 = (
        w25.sort_values("price_eur", ascending=False)
        .drop_duplicates("part_number", keep="first")
    )
    price_map = dict(zip(w25["part_number"], w25["price_eur"]))
    vs_map = dict(zip(w25["part_number"], w25["valid_from"]))
    ve_map = dict(zip(w25["part_number"], w25["valid_to"]))

    updated = 0
    mask = pr00["part_number"].isin(price_map)
    for idx in pr00.index[mask]:
        pn = pr00.at[idx, "part_number"]
        pr00.at[idx, "sp_eur"] = float(price_map[pn])
        # keep existing valid_start/end (may be open-ended 9999-12-31 as datetime64[us])
        pr00.at[idx, "price_condition"] = "PR00"
        cur = pr00.at[idx, "currency"]
        if cur is None or (isinstance(cur, float) and pd.isna(cur)) or str(cur).strip() == "":
            pr00.at[idx, "currency"] = "EUR"
        pr00.at[idx, "source_file"] = SOURCE_TAG
        updated += 1

    existing = set(pr00.loc[mask, "part_number"])
    to_add = [pn for pn in price_map if pn not in existing]
    if to_add:
        desc = {}
        if GAP_CSV.exists():
            g = pd.read_csv(GAP_CSV)
            g["pn"] = g["part_number"].map(norm_pn)
            desc = dict(zip(g["pn"], g.get("description", pd.Series(dtype=str))))
        rows = []
        for pn in to_add:
            rows.append(
                {
                    "sales_org": "IE40",
                    "part_number": pn,
                    "newest_pn": pn,
                    "description": desc.get(pn) or "",
                    "price_condition": "PR00",
                    "sp_eur": float(price_map[pn]),
                    "currency": "EUR",
                    "valid_start": pd.Timestamp(vs_map.get(pn)).as_unit("us"),
                    "valid_end": pd.Timestamp("9999-12-31").as_unit("us"),
                    "country_of_origin": "",
                    "fig_no": None,
                    "key_no": None,
                    "is_superseded_row": False,
                    "source_file": SOURCE_TAG,
                }
            )
        add_df = pd.DataFrame(rows)
        add_df["valid_start"] = add_df["valid_start"].astype("datetime64[us]")
        add_df["valid_end"] = add_df["valid_end"].astype("datetime64[us]")
        if str(pr00["valid_start"].dtype) != "datetime64[us]":
            pr00["valid_start"] = pr00["valid_start"].astype("datetime64[us]")
        if str(pr00["valid_end"].dtype) != "datetime64[us]":
            pr00["valid_end"] = pr00["valid_end"].astype("datetime64[us]")
        pr00 = pd.concat([pr00, add_df], ignore_index=True)

    pr00.to_parquet(path, index=False)
    pr00.to_parquet(DER / "pricing_parts_master.parquet", index=False)
    return {"updated": updated, "appended": len(to_add), "pn_filled": len(price_map)}


def apply_to_year_history(fills: pd.DataFrame) -> dict:
    """Patch Material/Price_EUR on pricing_pr00_ie40_{year}.parquet."""
    out = {}
    for year in ("2023", "2024", "2025"):
        path = DER / f"pricing_pr00_ie40_{year}.parquet"
        if not path.exists():
            out[year] = {"skipped": True}
            continue
        hist = pd.read_parquet(path)
        mat_col = "Material" if "Material" in hist.columns else "part_number"
        price_col = "Price_EUR" if "Price_EUR" in hist.columns else "sp_eur"
        # normalize key as zero-padded string without mutating Material dtype yet
        hist["_pn"] = hist[mat_col].map(norm_pn)
        sub = fills[fills["window_label"] == year].copy()
        sub = (
            sub.sort_values("price_eur", ascending=False)
            .drop_duplicates("part_number", keep="first")
        )
        price_map = dict(zip(sub["part_number"], sub["price_eur"]))
        updated = 0
        mask = hist["_pn"].isin(price_map)
        for idx in hist.index[mask]:
            pn = hist.at[idx, "_pn"]
            hist.at[idx, price_col] = float(price_map[pn])
            updated += 1
        existing = set(hist.loc[mask, "_pn"].dropna())
        to_add = [pn for pn in price_map if pn not in existing]
        hist = hist.drop(columns=["_pn"])
        if to_add:
            # keep Material dtype consistent (int64 in year extracts)
            mat_is_int = pd.api.types.is_integer_dtype(hist[mat_col])
            add_rows = []
            for pn in to_add:
                row = {c: None for c in hist.columns}
                row[mat_col] = int(pn) if mat_is_int and pn.isdigit() else pn
                row[price_col] = float(price_map[pn])
                if "list_year" in hist.columns:
                    row["list_year"] = int(year)
                add_rows.append(row)
            hist = pd.concat([hist, pd.DataFrame(add_rows)], ignore_index=True)
            if mat_is_int:
                hist[mat_col] = pd.to_numeric(hist[mat_col], errors="coerce").astype("Int64")
        hist.to_parquet(path, index=False)
        out[year] = {"updated": updated, "appended": len(to_add), "pn_filled": len(price_map)}
    return out


def rebuild_enquiry() -> None:
    import sys

    sys.path.insert(0, str(ISZE / "01_data" / "91_build"))
    from build_pricing_enquiry_tables import build_enquiry_view

    build_enquiry_view()


def refresh_gap_list(fills: pd.DataFrame) -> dict:
    """Close Spec C4 rows that now have usable Window_2025 PR00; keep remaining."""
    gap = pd.read_csv(GAP_CSV)
    gap["pn"] = gap["part_number"].map(norm_pn)
    closed_pns = set(
        fills.loc[fills["window_label"] == "2025", "part_number"]
    )
    # also treat as closed if IE40 now has usable price
    pr00 = pd.read_parquet(DER / "pricing_pr00_ie40.parquet")
    usable = set(
        pr00.loc[pr00["sp_eur"].fillna(0) > 0, "part_number"].astype(str)
    )
    closed = closed_pns | (set(gap["pn"]) & usable)

    remaining = gap[~gap["pn"].isin(closed)].copy()
    # stamp closed prices on a side file for audit
    closed_df = gap[gap["pn"].isin(closed)].copy()
    price_map = (
        fills[fills["window_label"] == "2025"]
        .sort_values("price_eur", ascending=False)
        .drop_duplicates("part_number")
        .set_index("part_number")["price_eur"]
        .to_dict()
    )
    closed_df["pr00_sp_eur_filled"] = closed_df["pn"].map(price_map)
    closed_df["fill_source"] = SOURCE_TAG
    closed_path = DER / "no_pr00_gap_cy2025_closed_20260812.csv"
    closed_df.drop(columns=["pn"], errors="ignore").to_csv(closed_path, index=False)

    remaining = remaining.drop(columns=["pn"])
    remaining = remaining.sort_values("cy2025_eur", ascending=False).reset_index(drop=True)
    remaining["rank"] = range(1, len(remaining) + 1)
    remaining.to_csv(GAP_CSV, index=False)

    meta = {}
    if GAP_META.exists():
        meta = json.loads(GAP_META.read_text(encoding="utf-8"))
    meta.update(
        {
            "updated": "2026-08-12",
            "closed_by_pr00_pull": len(closed_df),
            "remaining_pn": len(remaining),
            "remaining_eur": float(remaining["cy2025_eur"].sum()) if len(remaining) else 0.0,
            "closed_audit_csv": str(closed_path),
            "note": (
                "Closed PNs filled from Jerome SAP PR00 pull return; "
                "#N/A PNs remain on ranked list (no PR00 in SAP)."
            ),
        }
    )
    GAP_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {
        "closed": len(closed_df),
        "remaining": len(remaining),
        "remaining_eur": meta["remaining_eur"],
        "closed_audit": str(closed_path),
    }


def main() -> None:
    fills = load_ok_fills()
    print(f"ok fill rows: {len(fills)} · unique PN: {fills['part_number'].nunique()}")
    ie40 = apply_to_ie40(fills)
    print("IE40:", ie40)
    hist = apply_to_year_history(fills)
    print("history:", hist)
    rebuild_enquiry()
    gap = refresh_gap_list(fills)
    print("gap:", gap)

    # verify: how many former gap PNs now have enquiry PR00
    closed = pd.read_csv(DER / "no_pr00_gap_cy2025_closed_20260812.csv")
    closed["pn"] = closed["part_number"].map(norm_pn)
    enq = pd.read_parquet(
        DER / "pricing_pn_enquiry.parquet",
        columns=["part_number", "sp_eur_pr00_ie40"],
    )
    hit = enq[enq["part_number"].isin(closed["pn"])]
    usable = hit["sp_eur_pr00_ie40"].fillna(0) > 0
    print(
        f"verify enquiry: closed PNs in enquiry={len(hit)} "
        f"with usable PR00={int(usable.sum())}"
    )

    if RETURN_META.exists():
        meta = json.loads(RETURN_META.read_text(encoding="utf-8"))
    else:
        meta = {}
    meta["applied_to_ie40"] = ie40
    meta["applied_to_history"] = hist
    meta["gap_refresh"] = gap
    meta["applied_at"] = "2026-08-12"
    RETURN_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
