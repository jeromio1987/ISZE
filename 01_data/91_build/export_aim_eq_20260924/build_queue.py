"""Build the EQ lookup queue for the parts in 01_data/EXPORT.XLSX (IE40 PR00 extract).

Reads the export, joins the live AIM master for context, and writes a queue the
browser scraper can consume. Read-only: touches no derived file.

Run:  python 01_data/91_build/export_aim_eq_20260924/build_queue.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data" / "91_build" / "export_aim_eq_20260924"
DER = ROOT / "01_data" / "00_derived"
EXPORT = ROOT / "01_data" / "EXPORT.XLSX"


def pn_key(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.upper()


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.fillna("").astype(str).str.replace("\u00a0", "").str.replace(" ", "").str.replace(",", "."),
        errors="coerce",
    )


def is_known(l1: str) -> bool:
    v = (l1 or "").strip().lower()
    return v not in ("", "nan", "none", "null", "unknown", "unknown review")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    x = pd.read_excel(EXPORT)
    x["pn"] = pn_key(x["Newest P/N"])
    x["pn_source"] = pn_key(x["P/N"])

    m = pd.read_csv(DER / "aim_master_v2.csv", dtype=str, low_memory=False)
    m["pn"] = pn_key(m["part_number"])
    m = m.drop_duplicates("pn", keep="first").set_index("pn")

    x["on_master"] = x["pn"].isin(m.index)
    got = m.reindex(x["pn"])

    x["cur_aim_l1"] = got["aim_l1"].fillna("").to_numpy()
    x["cur_aim_l2"] = got["aim_l2"].fillna("").to_numpy()
    x["cur_aim_l3"] = got["aim_l3"].fillna("").to_numpy()
    x["cur_aim_source"] = got["aim_source"].fillna("").to_numpy()
    x["master_fig_key"] = got["fig_key"].fillna("").to_numpy()
    x["master_description"] = got["description"].fillna("").to_numpy()

    # Figure key straight off the price extract beats the master where both exist.
    # Fig No. is an integer in the extract, so pad to three digits ("11" -> "011")
    # to match the EPC spelling ("011-001").
    fig_no = pd.to_numeric(x["Fig No."], errors="coerce")
    key_no = x["Key No."].fillna("").astype(str).str.strip().str.upper()
    fk_export = (
        fig_no.map(lambda v: f"{int(v):03d}" if pd.notna(v) else "")
        + "-"
        + key_no
    )
    fk_export = fk_export.where(~fk_export.str.startswith("-"), "")
    x["fig_key_export"] = fk_export
    x["fig_key"] = x["fig_key_export"].where(x["fig_key_export"] != "", x["master_fig_key"])

    x["list_eur"] = num(x["Price"])
    x["pr00_value_eur"] = num(x["Value"])
    x["needs_aim"] = ~x["cur_aim_l1"].map(is_known)

    q = x[x["needs_aim"]].copy()
    q = q.sort_values(["pr00_value_eur", "list_eur"], ascending=False).reset_index(drop=True)
    q["rank"] = range(1, len(q) + 1)

    cols = [
        "rank", "pn", "pn_source", "Description", "list_eur", "pr00_value_eur",
        "Price Condition Type", "ABC Code", "Country of Origin", "Commodity Code",
        "Fig No.", "Key No.", "fig_key", "fig_key_export", "master_fig_key",
        "on_master", "cur_aim_l1", "cur_aim_l2", "cur_aim_l3", "cur_aim_source",
        "master_description", "Sales Org",
    ]
    q[cols].to_csv(OUT / "queue.csv", index=False, encoding="utf-8-sig")

    (OUT / "queue.json").write_text(
        json.dumps(q["pn"].tolist(), ensure_ascii=False), encoding="utf-8"
    )

    meta = {
        "built_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source_file": str(EXPORT),
        "export_rows": int(len(x)),
        "export_unique_pn": int(x["pn"].nunique()),
        "already_known_aim": int((~x["needs_aim"]).sum()),
        "queue_pn": int(len(q)),
        "queue_on_master": int(q["on_master"].sum()),
        "queue_not_on_master": int((~q["on_master"]).sum()),
        "queue_pr00_value_eur": round(float(q["pr00_value_eur"].sum()), 2),
    }
    (OUT / "queue.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(json.dumps(meta, indent=2))
    print("\ntop 10 by PR00 value")
    print(q[["rank", "pn", "Description", "list_eur", "fig_key", "on_master"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
