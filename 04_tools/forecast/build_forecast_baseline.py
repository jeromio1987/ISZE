"""P5.2 + P5.5 — baseline forecast candidates + rolling backtest.

Reads  : demand_series.parquet
Writes : forecast_candidates.parquet, backtest_report.parquet (+ meta)

Deterministic only — Holt linear trend + seasonal naive + naive + parc-proxy.
No statsmodels dependency. Spec: 00_docs/P5_FORECAST_BUILD_PLAN.md §5.2, §5.5.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.paths import DERIVED_DIR, ISZE_ROOT  # noqa: E402

BUILDER_VERSION = "p5.2-v1"
SERIES_SRC = DERIVED_DIR / "demand_series.parquet"
OUT_CAND = DERIVED_DIR / "forecast_candidates.parquet"
OUT_BACK = DERIVED_DIR / "backtest_report.parquet"
OUT_META = DERIVED_DIR / "forecast_baseline.meta.json"
HORIZON = 6
MIN_HISTORY = 6
BACKTEST_MIN = 12


def _month_index(ym: str) -> int:
    y, m = ym.split("-")
    return int(y) * 12 + int(m)


def _index_to_ym(idx: int) -> str:
    y, m = divmod(idx - 1, 12)
    return f"{y:04d}-{m + 1:02d}"


def _next_months(last_ym: str, n: int) -> list[str]:
    start = _month_index(last_ym) + 1
    return [_index_to_ym(start + i) for i in range(n)]


def _holt_forecast(y: np.ndarray, alpha: float = 0.3, beta: float = 0.1, steps: int = 6) -> np.ndarray:
    if len(y) == 0:
        return np.zeros(steps)
    level = float(y[0])
    trend = float(y[1] - y[0]) if len(y) > 1 else 0.0
    for val in y[1:]:
        prev_level = level
        level = alpha * val + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    return np.array([max(0.0, level + (h + 1) * trend) for h in range(steps)])


def _seasonal_naive(y: np.ndarray, months: list[str], steps: int = 6) -> np.ndarray:
    if len(y) < 13:
        return np.full(steps, float(y[-1]) if len(y) else 0.0)
    by_m: dict[int, list[float]] = {}
    for v, ym in zip(y, months):
        m = int(ym.split("-")[1])
        by_m.setdefault(m, []).append(float(v))
    avgs = {m: float(np.mean(vals)) for m, vals in by_m.items()}
    last_ym = months[-1]
    ly, lm = map(int, last_ym.split("-"))
    out = []
    cy, cm = ly, lm
    for _ in range(steps):
        cm += 1
        if cm > 12:
            cm = 1
            cy += 1
        out.append(avgs.get(cm, float(y[-1])))
    return np.array(out)


def _linear_trend(y: np.ndarray, steps: int = 6) -> np.ndarray:
    if len(y) < 3:
        base = float(y[-1]) if len(y) else 0.0
        return np.full(steps, base)
    x = np.arange(len(y), dtype=float)
    coef = np.polyfit(x, y.astype(float), 1)
    future_x = np.arange(len(y), len(y) + steps, dtype=float)
    return np.maximum(0.0, np.polyval(coef, future_x))


def _naive(y: np.ndarray, steps: int = 6) -> np.ndarray:
    base = float(y[-1]) if len(y) else 0.0
    return np.full(steps, base)


def _parc_boost(y: np.ndarray, db_total: np.ndarray, steps: int = 6) -> np.ndarray:
    base = _linear_trend(y, steps)
    if len(y) < 3 or len(db_total) < 3:
        return base
    ratio = float(np.mean(y[-3:])) / max(float(np.mean(db_total[-3:])), 1.0)
    db_fc = _linear_trend(db_total, steps)
    return np.maximum(0.0, db_fc * ratio)


def _wape(actual: np.ndarray, pred: np.ndarray) -> float:
    denom = float(np.sum(np.abs(actual)))
    if denom <= 0:
        return float("nan")
    return float(np.sum(np.abs(actual - pred)) / denom * 100.0)


def _best_model(wapes: dict[str, float]) -> str:
    valid = {k: v for k, v in wapes.items() if pd.notna(v)}
    if not valid:
        return "naive"
    return min(valid, key=valid.get)


def build_candidates(ds: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    ds = ds.sort_values(["db_code", "category", "year_month"])
    db_totals = (
        ds.groupby(["db_code", "year_month"], as_index=False)["units_sold"]
        .sum()
        .rename(columns={"units_sold": "db_units"})
    )
    db_totals_map: dict[str, dict[str, float]] = {}
    for db, g in db_totals.groupby("db_code"):
        db_totals_map[db] = dict(zip(g["year_month"], g["db_units"]))

    rows: list[dict] = []
    for (db, cat), g in ds.groupby(["db_code", "category"]):
        g = g.sort_values("year_month")
        months = g["year_month"].tolist()
        y = g["units_sold"].astype(float).values
        rev = g["revenue"].astype(float).values
        if len(months) == 0:
            continue
        last_ym = months[-1]
        fut = _next_months(last_ym, HORIZON)
        db_series = np.array([db_totals_map.get(db, {}).get(m, 0.0) for m in months])

        fc = {
            "ets": _holt_forecast(y, steps=HORIZON),
            "arima": _linear_trend(y, steps=HORIZON),
            "naive": _naive(y, steps=HORIZON),
            "parc": _parc_boost(y, db_series, steps=HORIZON),
        }
        if len(y) >= 13:
            fc["ets"] = _seasonal_naive(y, months, HORIZON)

        avg_rev_per_unit = float(np.nansum(rev) / max(np.nansum(y), 1.0))
        sparse = bool(g["sparse_flag"].iloc[0]) if "sparse_flag" in g.columns else len(y) < 3

        for model, vals in fc.items():
            for i, (ym, u) in enumerate(zip(fut, vals)):
                rows.append(
                    {
                        "db_code": db,
                        "category": cat,
                        "forecast_month": ym,
                        "horizon_step": i + 1,
                        "model": model,
                        "units_forecast": round(float(u), 2),
                        "revenue_forecast": round(float(u) * avg_rev_per_unit, 2),
                        "sparse_flag": sparse,
                        "history_months": len(months),
                        "last_seen": last_ym,
                    }
                )

    out = pd.DataFrame(rows)
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder_version": BUILDER_VERSION,
        "series": int(ds[["db_code", "category"]].drop_duplicates().shape[0]),
        "candidate_rows": int(len(out)),
        "horizon_months": HORIZON,
        "models": ["ets", "arima", "naive", "parc"],
        "note": "ets=Holt/seasonal-naive; arima=linear trend proxy (no statsmodels)",
    }
    return out, meta


def build_backtest(ds: pd.DataFrame) -> pd.DataFrame:
    ds = ds.sort_values(["db_code", "category", "year_month"])
    rows: list[dict] = []
    for (db, cat), g in ds.groupby(["db_code", "category"]):
        g = g.sort_values("year_month")
        months = g["year_month"].tolist()
        y = g["units_sold"].astype(float).values
        if len(y) < BACKTEST_MIN + 1:
            continue
        wapes: dict[str, list[float]] = {m: [] for m in ("ets", "arima", "naive", "parc")}
        for t in range(BACKTEST_MIN, len(y)):
            train_y = y[:t]
            train_m = months[:t]
            actual = y[t]
            preds = {
                "ets": float(_holt_forecast(train_y, steps=1)[0]),
                "arima": float(_linear_trend(train_y, steps=1)[0]),
                "naive": float(_naive(train_y, steps=1)[0]),
                "parc": float(_parc_boost(train_y, train_y, steps=1)[0]),
            }
            if len(train_y) >= 13:
                preds["ets"] = float(_seasonal_naive(train_y, train_m, steps=1)[0])
            for m, p in preds.items():
                if actual > 0 or p > 0:
                    wapes[m].append(abs(actual - p) / max(abs(actual), 1.0) * 100.0)
        row = {
            "db_code": db,
            "category": cat,
            "history_months": len(y),
            "nonzero_months": int((y > 0).sum()),
        }
        for m, ws in wapes.items():
            row[f"wape_{m}"] = round(float(np.mean(ws)), 2) if ws else None
        row["best_model"] = _best_model({m: row.get(f"wape_{m}") for m in wapes})
        row["wape_best"] = row.get(f"wape_{row['best_model']}")
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    if not SERIES_SRC.is_file():
        print(f"MISSING: {SERIES_SRC}", file=sys.stderr)
        return 1
    ds = pd.read_parquet(SERIES_SRC)
    cand, meta = build_candidates(ds)
    back = build_backtest(ds)

    OUT_CAND.parent.mkdir(parents=True, exist_ok=True)
    cand.to_parquet(OUT_CAND, index=False)
    back.to_parquet(OUT_BACK, index=False)

    meta["backtest_series"] = int(len(back))
    meta["backtest_wape_median"] = (
        round(float(back["wape_best"].median()), 2) if not back.empty and back["wape_best"].notna().any() else None
    )
    meta["outputs"] = {
        "forecast_candidates": str(OUT_CAND.relative_to(ISZE_ROOT)),
        "backtest_report": str(OUT_BACK.relative_to(ISZE_ROOT)),
    }
    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"wrote {OUT_CAND} ({len(cand):,} rows)")
    print(f"wrote {OUT_BACK} ({len(back):,} series, median WAPE={meta['backtest_wape_median']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
