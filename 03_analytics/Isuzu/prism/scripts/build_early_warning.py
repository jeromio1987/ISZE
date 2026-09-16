"""Build the ops Early-Warning priority list.

Answers one question: "who do I act on this cycle, and why?" — collapsing the
risk signal currently scattered across Decision Models -> Defection, Strategic
(triple threat / VOR / geo) and the Customer Risk page into one ranked list.

THREE SIGNALS (each fires ok / watch / act; no euro is ever summed across them
beyond the two that carry real money):

  1. SILENCE       — order rhythm broken vs the entity's own median gap.
                     Source: defection_alerts.csv
  2. CAPTURE SLOPE — PMS capture trending down on a real category.
                     Source: pms_capture_by_db.csv, slope recomputed HERE.
  3. VOR STRESS    — recent 4 weeks of urgent ordering vs the DB's own baseline.
                     Source: vor_seasonality.csv

Concentration (Gini) and price exposure (Eucon/AIM) are NOT signals — they do
not change between refreshes and no move follows from them. They ride along as
context columns only (db_aftersales_risk.risk_score).

--------------------------------------------------------------------------
WHY THE SLOPE IS RECOMPUTED HERE INSTEAD OF READ FROM capture_trajectory.csv
--------------------------------------------------------------------------
Through 2026-08-18 the shared builder
(`modules/strategic_build.build_capture_trajectory()`) regressed through the
partial current year and printed a false 83%-class decline rate into the CSV,
Strategic tab, scorecard PDF, and QBR pack. That partial-year guard is now in
the builder (DECISIONS.md 2026-08-18). This script still recomputes the slope
because Early Warning also applies a **level gate** (latest complete-year
capture ≤ 100%) that Contract 7 does not: ITUK brake_rotor can slope down
while still buying ~198% of modelled demand. Do not read `alert_declining`
from the CSV here.

Note: `trend_slope_pp_per_year` is a MISNOMER in the existing contract — the
values are fractions per year (capture_rate is 0..1), not percentage points.
This script names it `slope_frac_per_year` and derives pp for display.

SILENCE IS NOT DEFECTION WHEN THE CATEGORY IS DEAD. A category silent 26 months
with EUR 0 trailing revenue is not a customer walking away this cycle; it is a
category this DB never really bought. Those are classed `dormant` and ranked
below every live alarm rather than being deleted (they still answer "why is this
zero?").

DEALER GRAIN: ITUK dealer sell-out has its OWN, staler horizon (2025-12) than
distributor billing (2026-03) and carries no revenue column. Dealer rows are
kept, measured against their own horizon, and never given a euro.

Output: <DERIVED_DIR>/early_warning.csv  (one row per entity)
        <DERIVED_DIR>/early_warning_signals.csv  (long: one row per fired signal)
Run:    python scripts/build_early_warning.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import DERIVED_DIR  # noqa: E402
from modules.strategic_build import PMS_CAPTURE_BY_DB_CSV  # noqa: E402

# --- entities that are not ISZE distributors -------------------------------
# TURKEY (incl. AIOS/Anadolu Isuzu) is not an ISZE distributor and must never
# appear in a PRISM ranking; it leaks in via db_aftersales_risk.csv.
EXCLUDE_ENTITIES = {"TURKEY", "UNMAPPED"}

# --- signal thresholds ------------------------------------------------------
# Capture: mirrors the existing contract gate (slope < -0.05/yr, r2 > 0.5) so
# the numbers reconcile with Strategic — the only change is the partial-year
# guard. ACT at the contract gate; WATCH one notch softer.
CAP_ACT_SLOPE, CAP_ACT_R2 = -0.05, 0.5
CAP_WATCH_SLOPE, CAP_WATCH_R2 = -0.02, 0.4

# A declining category that still captures MORE than its modelled demand is not
# a customer walking away — it is the demand model under-predicting, and the
# "decline" is regression toward a ceiling we are still far above. 4.9% of
# DB x category x year rows sit above 1.0 (max 3.03); expected_qty is flat
# across years for those, which is the tell. Example measured 2026-07-17:
# ITUK brake_rotor 2.20 -> 2.19 -> 1.98 = -11pp/yr on EUR 284K, which would
# otherwise headline this page at EUR 313K while still capturing ~198% of
# expected demand. Gate on the level, not just the slope.
CAP_LEVEL_GATE = 1.0

# VOR: calibrated 2026-07-17 against the real 21-DB distribution, not assumed.
# Both a pp delta AND a ratio are required: DBs sitting near a 100% VOR ceiling
# (GREECE .70, ICELAND 1.00, ROMANIA .98 baseline) move large pp on small
# relative change, while a DB like UTI doubling .11 -> .24 is a real regime
# shift worth only +13pp. Either test alone fires on the wrong half.
# At these gates: 3 of 21 DBs ACT, 2 WATCH.
VOR_ACT_DELTA_PP, VOR_ACT_RATIO = 10.0, 1.25
VOR_WATCH_DELTA_PP, VOR_WATCH_RATIO = 5.0, 1.15
VOR_RECENT_WEEKS = 4
VOR_BASE_WEEKS = 52
VOR_MIN_BASE_WEEKS = 12
VOR_MIN_RECENT_ORDERS = 20  # below this the recent window is too thin to read

# Silence: a live alarm needs money on it. Beyond this many silent months with
# zero trailing revenue the category is dead, not defecting.
SILENCE_DORMANT_MONTHS = 12

LEVEL_OK, LEVEL_WATCH, LEVEL_ACT = 0, 1, 2
LEVEL_NAME = {0: "ok", 1: "watch", 2: "act"}


def _fmt_eur(v: float) -> str:
    if v >= 1_000_000:
        return f"EUR {v/1e6:.1f}M"
    if v >= 1_000:
        return f"EUR {v/1e3:.0f}K"
    return f"EUR {v:,.0f}"


def _partial_years(horizon: str) -> set[int]:
    """Years that are not fully billed as of `horizon` (YYYY-MM)."""
    try:
        y, m = (int(x) for x in str(horizon).split("-")[:2])
    except (ValueError, TypeError):
        return set()
    return {y} if m < 12 else set()


# ---------------------------------------------------------------------------
# Signal 1 — silence
# ---------------------------------------------------------------------------
def _silence(derived: Path) -> tuple[pd.DataFrame, dict]:
    fp = derived / "defection_alerts.csv"
    if not fp.exists():
        print("  ! defection_alerts.csv missing — silence signal skipped")
        return pd.DataFrame(), {}
    d = pd.read_csv(fp)
    horizon = str(d["data_horizon"].iloc[0]) if "data_horizon" in d else ""

    # Dealer rows carry no revenue and their own (staler) horizon: the last
    # month any dealer ordered is the dealer-feed horizon.
    dealer_horizon = ""
    if (d["level"] == "dealer").any():
        dealer_horizon = str(d.loc[d["level"] == "dealer", "last_order_month"].max())

    a = d[d["alert"]].copy()
    if a.empty:
        return pd.DataFrame(), {"silence_horizon": horizon, "dealer_horizon": dealer_horizon}

    rev = pd.to_numeric(a["trailing_12m_rev_eur"], errors="coerce")
    a["eur"] = rev.fillna(0.0)
    dormant = (rev.fillna(0.0) <= 0) & (a["silent_months"] > SILENCE_DORMANT_MONTHS)
    a["dormant"] = dormant
    # Live money silent -> act. Zero-revenue but recently silent -> watch.
    # Long-silent and dead -> dormant (ranked below everything live).
    a["level_val"] = np.where(dormant, LEVEL_WATCH, np.where(a["eur"] > 0, LEVEL_ACT, LEVEL_WATCH))

    def _reason(r: pd.Series) -> str:
        cat = str(r["pms_category"]).replace("_", " ")
        gap = r["median_gap_months"]
        base = (
            f"silent {int(r['silent_months'])} mo (median gap {gap:.1f})"
            if pd.notna(gap)
            else f"silent {int(r['silent_months'])} mo"
        )
        if r["dormant"]:
            return f"{cat} dormant — {base}, no revenue in 12 mo"
        money = f", {_fmt_eur(r['eur'])} trailing 12 mo" if r["eur"] > 0 else ""
        return f"{cat} {base}{money}"

    a["reason"] = a.apply(_reason, axis=1)
    a["signal"] = "silence"
    # A dealer row has no revenue -> it must never contribute a euro.
    a.loc[a["level"] == "dealer", "eur"] = 0.0
    out = a[[
        "level", "entity", "distributor_code", "pms_category",
        "signal", "level_val", "eur", "reason", "dormant",
    ]]
    return out, {"silence_horizon": horizon, "dealer_horizon": dealer_horizon}


# ---------------------------------------------------------------------------
# Signal 2 — capture slope (recomputed, partial years excluded)
# ---------------------------------------------------------------------------
def _capture(partial: set[int]) -> tuple[pd.DataFrame, dict]:
    pms = pd.read_csv(PMS_CAPTURE_BY_DB_CSV)
    hist = pms[pms["line_type"] == "total"].copy()
    all_years = sorted(hist["year"].unique())
    clean = hist[~hist["year"].isin(partial)]
    used_years = sorted(clean["year"].unique())
    last_complete = max(used_years) if used_years else None

    rows = []
    n_over_ceiling = 0
    for (dist, cat), g in clean.groupby(["distributor_code", "pms_category"]):
        g = g.sort_values("year")
        if len(g) < 2:
            continue
        caps = g["capture_rate"].astype(float).values
        if not np.isfinite(caps).all() or caps.max() <= 0:
            continue
        slope, _, r, _, _ = stats.linregress(g["year"].astype(float).values, caps)
        r2 = float(r) ** 2
        if slope <= CAP_ACT_SLOPE and r2 >= CAP_ACT_R2:
            lvl = LEVEL_ACT
        elif slope <= CAP_WATCH_SLOPE and r2 >= CAP_WATCH_R2:
            lvl = LEVEL_WATCH
        else:
            continue
        last = g[g["year"] == last_complete]
        latest_cap = float(last["capture_rate"].iloc[0]) if not last.empty else float(caps[-1])
        if latest_cap > CAP_LEVEL_GATE:
            n_over_ceiling += 1
            continue
        # Money on the line = what that category actually billed in the last
        # complete year. Not a gap, not an inference — booked revenue at risk.
        eur = float(last["actual_rev_eur"].sum()) if not last.empty else 0.0
        rows.append({
            "level": "distributor",
            "entity": dist,
            "distributor_code": dist,
            "pms_category": cat,
            "signal": "capture",
            "level_val": lvl,
            "eur": eur,
            "reason": (
                f"{str(cat).replace('_', ' ')} capture {slope*100:+.1f}pp/yr "
                f"to {latest_cap:.0%} (r² {r2:.2f}), {_fmt_eur(eur)} billed CY{last_complete}"
            ),
            "dormant": False,
            "slope_frac_per_year": round(float(slope), 4),
            "trend_r2": round(r2, 4),
            "latest_capture": round(latest_cap, 4),
        })
    print(f"  capture: {n_over_ceiling} declining categories suppressed as over-ceiling "
          f"(> {CAP_LEVEL_GATE:.0%} of modelled demand — model artifact, not defection)")
    # Plain ints, comma-joined — these land in a CSV column and get read back
    # by the page; numpy scalars would serialise as "np.int64(2026)".
    meta = {
        "capture_years_used": ",".join(str(int(y)) for y in used_years),
        "capture_years_dropped": ",".join(
            str(int(y)) for y in sorted(set(all_years) - set(used_years))
        ),
        "capture_last_complete": int(last_complete) if last_complete is not None else "",
    }
    return pd.DataFrame(rows), meta


# ---------------------------------------------------------------------------
# Signal 3 — VOR stress (recent window vs the DB's own baseline)
# ---------------------------------------------------------------------------
def _vor(derived: Path) -> tuple[pd.DataFrame, dict]:
    fp = derived / "vor_seasonality.csv"
    if not fp.exists():
        print("  ! vor_seasonality.csv missing — VOR signal skipped")
        return pd.DataFrame(), {}
    v = pd.read_csv(fp)
    v = v[~v["distributor_code"].isin(EXCLUDE_ENTITIES)].copy()
    v["t"] = v["year"] * 100 + v["week_of_year"]
    v = v.sort_values("t")
    horizon_t = int(v["t"].max())

    rows = []
    for db, g in v.groupby("distributor_code"):
        g = g.sort_values("t")
        recent = g.tail(VOR_RECENT_WEEKS)
        base = g.iloc[:-VOR_RECENT_WEEKS].tail(VOR_BASE_WEEKS)
        if len(base) < VOR_MIN_BASE_WEEKS or recent.empty:
            continue
        n_recent = int(recent["total_order_count"].sum())
        if n_recent < VOR_MIN_RECENT_ORDERS:
            continue
        # Order-count weighted, so a 1-order week cannot swing the read.
        r_pct = recent["vor_count"].sum() / max(n_recent, 1)
        b_orders = int(base["total_order_count"].sum())
        b_pct = base["vor_count"].sum() / max(b_orders, 1)
        delta_pp = (r_pct - b_pct) * 100
        ratio = (r_pct / b_pct) if b_pct > 0 else np.nan
        if delta_pp >= VOR_ACT_DELTA_PP and ratio >= VOR_ACT_RATIO:
            lvl = LEVEL_ACT
        elif delta_pp >= VOR_WATCH_DELTA_PP and ratio >= VOR_WATCH_RATIO:
            lvl = LEVEL_WATCH
        else:
            continue
        rows.append({
            "level": "distributor",
            "entity": db,
            "distributor_code": db,
            "pms_category": "—",
            "signal": "vor",
            "level_val": lvl,
            # VOR carries no euro: vor_seasonality has no revenue column and
            # urgent-order revenue is not "at stake" money. pp only.
            "eur": 0.0,
            "reason": (
                f"VOR {r_pct:.0%} of orders last {len(recent)} wks vs {b_pct:.0%} "
                f"own baseline ({delta_pp:+.0f}pp, {ratio:.2f}×)"
            ),
            "dormant": False,
            "vor_recent_pct": round(float(r_pct), 4),
            "vor_base_pct": round(float(b_pct), 4),
            "vor_delta_pp": round(float(delta_pp), 2),
            "vor_ratio": round(float(ratio), 3) if np.isfinite(ratio) else None,
        })
    return pd.DataFrame(rows), {"vor_horizon": f"{horizon_t//100}-W{horizon_t%100:02d}"}


# ---------------------------------------------------------------------------
def main() -> None:
    derived = Path(DERIVED_DIR)
    print("Building early-warning list…")

    sil, m_sil = _silence(derived)
    partial = _partial_years(m_sil.get("silence_horizon", ""))
    print(f"  partial year(s) excluded from capture slope: {sorted(partial) or 'none'}")
    cap, m_cap = _capture(partial)
    vor, m_vor = _vor(derived)
    meta = {**m_sil, **m_cap, **m_vor}

    signals = pd.concat([df for df in (sil, cap, vor) if not df.empty], ignore_index=True)
    if signals.empty:
        print("  no signals fired — nothing to write")
        return
    signals = signals[~signals["entity"].isin(EXCLUDE_ENTITIES)]
    signals = signals[~signals["distributor_code"].isin(EXCLUDE_ENTITIES)]

    # --- context (never a ranker) -----------------------------------------
    risk_fp = derived / "db_aftersales_risk.csv"
    risk = pd.read_csv(risk_fp) if risk_fp.exists() else pd.DataFrame()
    if not risk.empty:
        risk = risk[~risk["distributor_code"].isin(EXCLUDE_ENTITIES)]
        risk_map = risk.set_index("distributor_code")["risk_score"].to_dict()
    else:
        risk_map = {}

    # --- roll signals up to one row per entity ----------------------------
    out = []
    for (lvl_name, entity), g in signals.groupby(["level", "entity"], sort=False):
        live = g[~g["dormant"]]
        sev = int(g["level_val"].max())
        # An entity whose only alarms are dormant categories is not an ops
        # priority; it sits below every live watch.
        all_dormant = live.empty
        by_sig = {s: int(g.loc[g["signal"] == s, "level_val"].max()) for s in g["signal"].unique()}
        # Exposure = revenue sitting on the alarming categories. Summed over
        # DISTINCT categories, taking the max per category, so a category that
        # fires two signals (silence AND capture on the same brake_pad) counts
        # its revenue once. Not true today; cheap to make structurally safe.
        eur = (
            float(live.groupby("pms_category")["eur"].max().sum()) if not live.empty else 0.0
        )
        order = ["silence", "capture", "vor"]
        reasons = [
            r for s in order
            for r in g.loc[g["signal"] == s].sort_values("eur", ascending=False)["reason"].tolist()
        ]
        dist = g["distributor_code"].iloc[0]
        out.append({
            "level": lvl_name,
            "entity": entity,
            "distributor_code": dist,
            "severity": 0 if all_dormant else sev,
            "severity_name": "dormant" if all_dormant else LEVEL_NAME[sev],
            "n_signals": int(g["signal"].nunique()),
            "eur_exposed": round(eur, 2),
            "sig_silence": by_sig.get("silence", LEVEL_OK),
            "sig_capture": by_sig.get("capture", LEVEL_OK),
            "sig_vor": by_sig.get("vor", LEVEL_OK),
            "why_this_cycle": " · ".join(reasons),
            "risk_score_context": round(float(risk_map.get(dist, np.nan)), 1)
            if dist in risk_map else None,
            "all_dormant": all_dormant,
        })
    ew = pd.DataFrame(out)

    # Rank: live alarms first, then severity, then money, then corroboration.
    # Money outranks corroboration deliberately — two signals agreeing on a
    # EUR 551 category is not a bigger ops problem than one hard signal on
    # EUR 313K. n_signals stays visible as a confidence cue and breaks ties.
    # Dormant-only entities always last.
    ew = ew.sort_values(
        ["all_dormant", "severity", "eur_exposed", "n_signals"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)
    ew.insert(0, "priority", ew.index + 1)

    for k, v in meta.items():
        ew[k] = str(v)

    ew.to_csv(derived / "early_warning.csv", index=False)
    signals.to_csv(derived / "early_warning_signals.csv", index=False)

    n_act = int((ew["severity_name"] == "act").sum())
    n_watch = int((ew["severity_name"] == "watch").sum())
    n_dorm = int((ew["severity_name"] == "dormant").sum())
    print(f"  wrote early_warning.csv          {len(ew)} entities "
          f"({n_act} act, {n_watch} watch, {n_dorm} dormant)")
    print(f"  wrote early_warning_signals.csv  {len(signals)} fired signals")
    print(f"  EUR exposed (live alarms): {_fmt_eur(ew['eur_exposed'].sum())}")
    print(f"  meta: {meta}")


if __name__ == "__main__":
    main()
