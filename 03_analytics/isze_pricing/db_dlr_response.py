"""DB→DLR sell-out response proxies (ITUK + UTI) — soft join only.

Reads ``paths.db_dlr_response`` (default
``01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv``).

Honesty rules (Jerome 2026-08-10):
- Rows are ``measure_kind=proxy`` (or ``blocked`` stubs). Not elasticity.
- Price axis = ISZE→DB ASP / list pass-through — lasting basis until invoice
  prices exist (not a near-term ask).
- Never multiply allocation ``delta`` by ``beta``.
- Israel = UTI only — never blend UMI.
- Soft signal = labeled diagnostics / optional warnings on matched cells.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# isze_pricing/ -> 03_analytics/ -> workspace root
REPO = Path(__file__).resolve().parents[2]
DEFAULT_REL = Path("01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv")

# Only these distributors have sell-out proxies in the file.
PROXY_DBS = frozenset({"ITUK", "UTI"})

# Soft warn when cross-section proxy beta is clearly negative and powered.
DEFAULT_ADVERSE_BETA = -0.5


def resolve_path(cfg: dict, repo: Path | None = None) -> Path:
    """Resolve ``paths.db_dlr_response`` relative to workspace root."""
    root = Path(repo) if repo else REPO
    rel = (cfg.get("paths") or {}).get("db_dlr_response") or str(DEFAULT_REL)
    p = Path(rel)
    return p if p.is_absolute() else root / p


def load_db_dlr_response(path: Path) -> pd.DataFrame:
    """Load proxy CSV; empty frame if missing."""
    if not path.is_file():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "beta" in df.columns:
        df["beta"] = pd.to_numeric(df["beta"], errors="coerce")
    if "low_power" in df.columns:
        df["low_power"] = df["low_power"].astype(str).str.lower().isin(
            ("true", "1", "yes")
        )
    return df


def cross_section_proxies(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    m = (
        (df.get("measure_kind") == "proxy")
        & (df.get("method") == "cross_section_lnq_lnp_asp")
        & (df.get("distributor_code").isin(PROXY_DBS))
    )
    return df.loc[m].copy()


def list_shock_exposure(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    m = (
        (df.get("measure_kind") == "proxy")
        & (df.get("method") == "list_shock_exposure_2025_2026")
        & (df.get("distributor_code").isin(PROXY_DBS))
    )
    return df.loc[m].copy()


def attach_soft_signal(
    alloc: pd.DataFrame,
    response: pd.DataFrame,
    *,
    adverse_beta: float = DEFAULT_ADVERSE_BETA,
) -> tuple[pd.DataFrame, dict]:
    """Left-join exact (db, cat) proxy beta onto alloc cells. Does not change delta.

    Join key: ``distributor_code`` ↔ ``db``, ``category`` ↔ ``cat`` (PMS name).
    AIM:* rows stay in the diagnostic export only — no invented AIM→PMS map.
    """
    out = alloc.copy()
    out["db_dlr_proxy_beta"] = pd.NA
    out["db_dlr_proxy_n_pns"] = pd.NA
    out["db_dlr_proxy_low_power"] = pd.NA
    out["db_dlr_proxy_flag"] = ""
    out["db_dlr_list_shock_wtd_pct"] = pd.NA

    report: dict = {
        "wired": True,
        "measure_kind": "proxy",
        "price_basis": "ASP_list_passthrough",
        "joined_to_deltas": False,
        "n_cells_flagged_adverse": 0,
        "n_cells_with_proxy": 0,
        "n_cells_with_list_shock": 0,
        "note": (
            "Soft diagnostic only. ASP/list pass-through proxy — not dealer "
            "invoice elasticity. Do not treat beta as an allocation coefficient."
        ),
    }

    if response.empty or "db" not in out.columns or "cat" not in out.columns:
        report["wired"] = False
        report["note"] = "db_dlr_response missing or empty — soft join skipped"
        return out, report

    xs = cross_section_proxies(response)
    if not xs.empty:
        key = xs.rename(
            columns={
                "distributor_code": "db",
                "category": "cat",
                "beta": "db_dlr_proxy_beta",
                "n_pns": "db_dlr_proxy_n_pns",
                "low_power": "db_dlr_proxy_low_power",
            }
        )
        # Prefer powered rows if duplicates
        key = key.sort_values("db_dlr_proxy_low_power").drop_duplicates(
            ["db", "cat"], keep="first"
        )
        cols = [
            "db",
            "cat",
            "db_dlr_proxy_beta",
            "db_dlr_proxy_n_pns",
            "db_dlr_proxy_low_power",
        ]
        out = out.drop(
            columns=[
                "db_dlr_proxy_beta",
                "db_dlr_proxy_n_pns",
                "db_dlr_proxy_low_power",
            ],
            errors="ignore",
        )
        out = out.merge(key[cols], on=["db", "cat"], how="left")

    shock = list_shock_exposure(response)
    if not shock.empty and "sellout_wtd_sp_pct_chg_2025_2026" in shock.columns:
        sk = shock.rename(
            columns={
                "distributor_code": "db",
                "category": "cat",
                "sellout_wtd_sp_pct_chg_2025_2026": "db_dlr_list_shock_wtd_pct",
            }
        ).drop_duplicates(["db", "cat"], keep="first")
        out = out.drop(columns=["db_dlr_list_shock_wtd_pct"], errors="ignore")
        out = out.merge(
            sk[["db", "cat", "db_dlr_list_shock_wtd_pct"]],
            on=["db", "cat"],
            how="left",
        )

    beta = pd.to_numeric(out["db_dlr_proxy_beta"], errors="coerce")
    low_raw = out["db_dlr_proxy_low_power"]

    def _as_bool_low(v) -> bool:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return True  # missing → treat as low_power (no adverse flag)
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("true", "1", "yes")

    low = low_raw.map(_as_bool_low)
    adverse = beta.notna() & (~low) & (beta < adverse_beta)
    flags = []
    for i in range(len(out)):
        if adverse.iloc[i]:
            flags.append(
                f"PROXY_ADVERSE_CROSS_SECTION beta={beta.iloc[i]:.3f} "
                f"(ASP pass-through; not elasticity; not applied to delta)"
            )
        elif pd.notna(beta.iloc[i]):
            flags.append("PROXY_CROSS_SECTION_ATTACHED")
        else:
            flags.append("")
    out["db_dlr_proxy_flag"] = flags

    report["n_cells_with_proxy"] = int(beta.notna().sum())
    report["n_cells_flagged_adverse"] = int(adverse.sum())
    report["n_cells_with_list_shock"] = int(
        pd.to_numeric(out["db_dlr_list_shock_wtd_pct"], errors="coerce").notna().sum()
    )
    report["adverse_beta_threshold"] = adverse_beta
    return out, report


def summary_markdown(report: dict, response: pd.DataFrame) -> str:
    """Human block for alloc summary.md."""
    lines = [
        "\n\n### DB→DLR response soft signal (ITUK/UTI proxy)\n",
        f"```\n{__import__('json').dumps(report, indent=2)}\n```\n",
        "",
        "Labeled **proxy** only (ASP / list pass-through). "
        "Not joined into allocation deltas. UTI ≠ UMI.\n",
    ]
    xs = cross_section_proxies(response)
    if not xs.empty:
        show = xs[
            [
                c
                for c in (
                    "distributor_code",
                    "category",
                    "n_pns",
                    "beta",
                    "low_power",
                    "reading",
                )
                if c in xs.columns
            ]
        ].copy()
        show = show.sort_values(["distributor_code", "beta"])
        try:
            lines.append("\n#### Cross-section proxies (all AIM + PMS cats)\n")
            lines.append(show.to_markdown(index=False))
            lines.append("\n")
        except Exception:
            lines.append("\n```\n" + show.to_string(index=False) + "\n```\n")
    return "".join(lines)
