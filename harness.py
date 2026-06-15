#!/usr/bin/env python3
"""harness.py — Frozen evaluation harness for quantloop strategies.

FIXED. NEVER MODIFY after setup. If a genuine bug is found, fix it, note in
ledger.tsv, and mark earlier rows stale — but NEVER change the protocol,
costs, gates, or metric.
"""

import hashlib
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Cost model (bps per side) ─────────────────────────────────────────────
COST_BPS = {
    "equity": 10,  # 5 bps commission + 5 bps slippage
    "etf": 10,
    "crypto": 20,
    "future": 10,
}

SHORT_BORROW_BPS_PA = 50  # 50 bps/yr on shorts for hard-to-borrow names

# ── Risk plumbing defaults ────────────────────────────────────────────────
VOL_TARGET = 0.10  # 10% annualised
MAX_POS_PCT = 0.10  # per-position cap
MAX_GROSS_EXP = 2.00  # 200% gross exposure
DD_HALVE = 0.20  # drawdown → halve exposure
DD_FLAT = 0.30  # drawdown → flat until recovery


def _td365() -> float:
    """Trading days per year approximation."""
    return 252.0


def _ann_factor() -> float:
    """Annualisation factor for daily returns."""
    return np.sqrt(252.0)


# ══════════════════════════════════════════════════════════════════════════
# Data layer
# ══════════════════════════════════════════════════════════════════════════


def download_data(
    tickers: list[str],
    start: str = "2010-01-01",
    end: str | None = None,
    asset_class: str = "equity",
) -> pd.DataFrame:
    """Download daily OHLCV for *tickers*, cache to parquet, return adjusted close."""
    cache_key = hashlib.md5(
        "-".join(sorted(tickers)).encode()
        + f"_{start}_{end or 'today'}".encode()
    ).hexdigest()[:12]
    cache_path = DATA_DIR / f"{cache_key}.csv"

    if cache_path.exists():
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        print(f"[harness] Loaded {len(tickers)} tickers from cache ({cache_path.name})", file=sys.stderr)
        return df

    print(f"[harness] Downloading {len(tickers)} tickers from yfinance …", file=sys.stderr)
    data = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )

    # Handle MultiIndex columns (yfinance >=0.2.50 returns MultiIndex for multiple tickers)
    if isinstance(data.columns, pd.MultiIndex):
        close = data.xs("Close", axis=1, level=1)
    elif len(tickers) == 1:
        close = data["Close"].to_frame(tickers[0])
    else:
        close = data["Close"]

    close.columns = [str(c).strip().upper() for c in close.columns]
    close = close.dropna(how="all", axis=1).ffill(limit=5).dropna(how="all", axis=1)
    close.to_csv(cache_path)
    print(f"[harness] Cached to {cache_path}", file=sys.stderr)
    return close


# ══════════════════════════════════════════════════════════════════════════
# Walk-forward splitter with embargo
# ══════════════════════════════════════════════════════════════════════════


def walk_forward_splits(
    dates: pd.DatetimeIndex,
    train_years: float = 5.0,
    retrain_days: int = 252,
    embargo_days: int = 21,
    min_test_days: int = 63,
) -> list[tuple[pd.DatetimeIndex, pd.DatetimeIndex]]:
    """Generate (train_idx, test_idx) pairs with expanding window + embargo.

    Each fold:
      - train: oldest N years up to *train_start*, then expanding every *retrain_days*
      - test: *retrain_days* trading days starting *embargo_days* after train end
    """
    n = len(dates)
    splits = []
    train_end = int(train_years * 252)  # approx trading days

    while train_end + embargo_days + min_test_days < n:
        test_start = train_end + embargo_days
        test_end = min(test_start + retrain_days, n)

        train_idx = dates[:train_end]
        test_idx = dates[test_start:test_end]

        if len(test_idx) >= min_test_days * 0.5:  # allow partial last fold
            splits.append((train_idx, test_idx))

        train_end += retrain_days

    return splits


# ══════════════════════════════════════════════════════════════════════════
# Risk & cost application
# ══════════════════════════════════════════════════════════════════════════


def apply_costs(
    returns: pd.Series,
    turnover: pd.Series,
    cost_bps: float = 10.0,
) -> pd.Series:
    """Apply round-trip costs proportional to turnover."""
    return returns - (turnover * cost_bps / 10_000)


def vol_target_weights(
    weights: pd.DataFrame,
    returns: pd.DataFrame,
    half_life: int = 63,
) -> pd.DataFrame:
    """Scale portfolio-level gross exposure to vol target."""
    if weights.empty:
        return weights

    # Portfolio realised vol (EWMA)
    port_rets = (weights * returns).sum(axis=1, min_count=1)
    ewma_var = port_rets.ewm(span=half_life, min_periods=21).var()
    ewma_vol = np.sqrt(ewma_var * _td365())
    ewma_vol = ewma_vol.clip(lower=0.01)  # avoid div-by-zero

    scale = VOL_TARGET / ewma_vol
    scaled = weights.multiply(scale, axis=0)

    # Per-position cap
    gross = scaled.abs().sum(axis=1)
    scaled = scaled.div(gross.where(gross > 0, 1.0), axis=0).mul(scaled.abs().sum(axis=1), axis=0)

    # Exposure cap
    for t in scaled.index:
        row = scaled.loc[t]
        gross_t = row.abs().sum()
        if gross_t > MAX_GROSS_EXP:
            scaled.loc[t] = row * (MAX_GROSS_EXP / gross_t)
        for col in scaled.columns:
            pos = scaled.loc[t, col]
            if abs(pos) > MAX_POS_PCT:
                scaled.loc[t, col] = np.sign(pos) * MAX_POS_PCT

    # Drawdown gates — use vol-targeted returns, not raw signal returns
    port_vol_scaled = (scaled.shift(1) * returns).sum(axis=1, min_count=1).fillna(0)
    cum = (1.0 + port_vol_scaled).cumprod()
    dd = cum / cum.cummax() - 1.0
    max_dd_fold = dd.min()  # max drawdown during this fold (most negative)
    if max_dd_fold <= -DD_FLAT:
        scaled = scaled * 0.0  # flat for entire fold
    elif max_dd_fold <= -DD_HALVE:
        scaled = scaled * 0.5

    return scaled


def compute_turnover(weights: pd.DataFrame) -> pd.Series:
    """Daily turnover = sum of absolute weight changes (one-way)."""
    return weights.diff().abs().sum(axis=1, min_count=1).fillna(0.0)


# ══════════════════════════════════════════════════════════════════════════
# Metrics
# ══════════════════════════════════════════════════════════════════════════


def deflated_sharpe(sharpe: float, n_trials: int, T: int) -> float:
    """Bailey & López de Prado deflated Sharpe ratio.

    Accounts for the number of independent trials run.
    """
    if n_trials <= 1:
        return sharpe
    # Approximate: E[max Z] ~ sqrt(2 log N) for standard normal max over N iid
    # More precise: use the CDF of the max of N normals
    from scipy import stats

    # Expected maximum Sharpe under null (Gaussian)
    # Using approximation from B&LdP
    gamma = np.euler_gamma
    z_max = (1 - gamma) * stats.norm.ppf(1 - 1.0 / n_trials) + gamma * stats.norm.ppf(
        1 - 1.0 / (n_trials * np.e)
    )
    # Standard error of Sharpe
    se_sharpe = np.sqrt(1.0 / T)
    return (sharpe - z_max * se_sharpe) / se_sharpe


def compute_metrics(
    eq_curve: pd.Series,
    gross_rets: pd.Series | None = None,
    n_trials: int = 1,
    beta_bench: pd.Series | None = None,
    n_trades: int = 0,
    ann_turnover: float = 0.0,
) -> dict:
    """Compute all evaluation metrics from an equity curve (net of costs)."""
    rets = eq_curve.pct_change().dropna()
    gross_rets_used = gross_rets.dropna() if gross_rets is not None else rets

    n = len(rets)
    if n < 20:
        return {"SCORE": 0.0, "error": "too few observations"}

    ann_factor = np.sqrt(252.0)

    # Basic stats
    ann_ret = rets.mean() * 252.0
    ann_vol = rets.std() * ann_factor
    sharpe_net = ann_ret / ann_vol if ann_vol > 1e-10 else 0.0
    sharpe_gross = (
        (gross_rets_used.mean() * 252.0) / (gross_rets_used.std() * ann_factor)
        if gross_rets_used.std() > 1e-10
        else 0.0
    )

    # Sortino
    downside = rets[rets < 0]
    downside_vol = downside.std() * ann_factor if len(downside) > 5 else ann_vol
    sortino = ann_ret / downside_vol if downside_vol > 1e-10 else 0.0

    # Max DD
    cum = (1.0 + rets).cumprod()
    running_max = cum.cummax()
    dd = (cum / running_max - 1.0) * 100.0
    max_dd_pct = float(dd.min())

    # Turnover (annualised) — filled by caller
    turnover_daily = 0.0

    # Win rate
    win_rate = (rets > 0).mean()

    # Beta to SPY
    beta_spy = 0.0
    if beta_bench is not None:
        aligned = pd.concat([rets, beta_bench.pct_change().dropna()], axis=1, join="inner").dropna()
        if len(aligned) > 20:
            cov = aligned.iloc[:, 0].cov(aligned.iloc[:, 1])
            var = aligned.iloc[:, 1].var()
            beta_spy = cov / var if var > 1e-10 else 0.0

    # Deflated Sharpe
    dshr = deflated_sharpe(sharpe_net, n_trials, n)

    # Hard gates
    score = sharpe_net
    if max_dd_pct < -35.0:
        score = 0.0
    if dshr <= 0:
        score = 0.0
    if n_trades < 100:
        score = 0.0  # insufficient trading activity
    if ann_turnover > 50.0:
        score = 0.0  # excessive turnover (intraday churn)

    return {
        "SCORE": round(score, 4),
        "sharpe_net": round(sharpe_net, 4),
        "sharpe_gross": round(sharpe_gross, 4),
        "deflated_sharpe": round(dshr, 4),
        "sortino": round(sortino, 4),
        "max_dd_pct": round(max_dd_pct, 1),
        "ann_ret": round(ann_ret, 4),
        "ann_vol": round(ann_vol, 4),
        "win_rate": round(win_rate, 4),
        "beta_spy": round(beta_spy, 4),
        "oos_years": round(n / 252, 1),
    }


# ══════════════════════════════════════════════════════════════════════════
# Main evaluation runner
# ══════════════════════════════════════════════════════════════════════════


def run_evaluation(
    prices: pd.DataFrame,
    signal_fn,
    cost_bps: float = 10.0,
    asset_class: str = "equity",
    n_trials: int = 1,
    beta_ticker: str = "SPY",
    **signal_kwargs,
) -> dict:
    """Run walk-forward evaluation.

    Parameters
    ----------
    prices : pd.DataFrame
        Daily adjusted close, columns = tickers.
    signal_fn : callable
        ``signal_fn(train_prices, test_prices, **signal_kwargs) -> pd.DataFrame``
        Returns position weights (ticker x date) for the test period.
    cost_bps : float
        Round-trip cost in bps per side.
    asset_class : str
        For cost model classification.
    n_trials : int
        Number of strategies tested so far (for deflated Sharpe).
    beta_ticker : str
        Benchmark for beta calculation.
    """
    dates = prices.index.sort_values()
    splits = walk_forward_splits(dates)

    if len(splits) == 0:
        print("[harness] Not enough data for any walk-forward split.")
        return {"SCORE": 0.0, "error": "insufficient data"}

    all_oos_weights = []
    all_gross_rets = []
    all_turnover = []

    for fold, (train_dates, test_dates) in enumerate(splits):
        train_px = prices.loc[train_dates]
        test_px = prices.loc[test_dates]

        # Generate signals
        weights = signal_fn(train_px, test_px, **signal_kwargs)
        if weights is None or weights.empty:
            weights = pd.DataFrame(0.0, index=test_px.index, columns=prices.columns)

        # Align
        weights = weights.reindex(index=test_px.index, columns=prices.columns, fill_value=0.0)

        # Gross returns (before costs)
        rets = test_px.pct_change()
        gross = (weights.shift(1) * rets).sum(axis=1, min_count=1)

        # Turnover
        to = compute_turnover(weights)

        # Costs
        net = apply_costs(gross, to, cost_bps)

        # Vol targeting & risk
        weights_vt = vol_target_weights(weights, rets)
        rets_vt = (weights_vt.shift(1) * rets).sum(axis=1, min_count=1)
        net_vt = apply_costs(rets_vt, compute_turnover(weights_vt), cost_bps)

        all_oos_weights.append(weights_vt)
        all_gross_rets.append(rets_vt)
        all_turnover.append(compute_turnover(weights_vt))

        print(f"[harness] Fold {fold + 1}/{len(splits)}: train {train_dates[0].date()}-{train_dates[-1].date()} | "
              f"test {test_dates[0].date()}-{test_dates[-1].date()} | "
              f"net ret {net_vt.mean() * 252:.2%} ann'd", file=sys.stderr)

    # Combine OOS periods into single equity curve
    oos_weights = pd.concat(all_oos_weights)
    oos_weights = oos_weights[~oos_weights.index.duplicated(keep="first")].sort_index()

    gross_rets = pd.concat(all_gross_rets)
    gross_rets = gross_rets[~gross_rets.index.duplicated(keep="first")].sort_index()

    turnover_s = pd.concat(all_turnover)
    turnover_s = turnover_s[~turnover_s.index.duplicated(keep="first")].sort_index()

    # Net equity curve
    rets_all = (oos_weights.shift(1) * prices.loc[oos_weights.index].pct_change()).sum(
        axis=1, min_count=1
    )
    costs = apply_costs(rets_all, turnover_s, cost_bps)
    eq_curve = (1.0 + costs).cumprod()
    gross_curve = (1.0 + gross_rets).cumprod()

    # Beta benchmark
    try:
        bench = yf.download(beta_ticker, start=dates[0].strftime("%Y-%m-%d"),
                            end=dates[-1].strftime("%Y-%m-%d"), auto_adjust=True, progress=False)
        if isinstance(bench.columns, pd.MultiIndex):
            bench_close = bench.xs("Close", axis=1, level=0).iloc[:, 0]
        else:
            bench_close = bench["Close"] if "Close" in bench.columns else bench.iloc[:, 0]
        bench_rets = bench_close.reindex(oos_weights.index).ffill().pct_change()
    except Exception:
        bench_rets = pd.Series(0.0, index=oos_weights.index)

    # Metrics
    n_trades = int((turnover_s > 0.01).sum())
    ann_turnover = float(turnover_s.mean() * 252)

    metrics = compute_metrics(
        eq_curve, gross_rets, n_trials=n_trials, beta_bench=bench_rets,
        n_trades=n_trades, ann_turnover=ann_turnover,
    )
    metrics["n_trades"] = n_trades
    metrics["ann_turnover"] = round(ann_turnover, 1)
    metrics["oos_years"] = round(len(eq_curve) / 252, 1)

    # Print grep-able summary
    print("\n---")
    for k in ["SCORE", "sharpe_net", "sharpe_gross", "deflated_sharpe", "sortino",
              "max_dd_pct", "ann_turnover", "n_trades", "win_rate", "beta_spy", "oos_years"]:
        print(f"{k:20s} {metrics.get(k, 'N/A')}")

    return metrics


def print_ledger_row(
    strategy_id: str,
    family: str,
    universe: str,
    metrics: dict,
    n_params: int,
    status: str,
    description: str,
) -> None:
    """Print a ledger.tsv row (tab-separated)."""
    score = metrics.get("SCORE", 0.0)
    sharpe = metrics.get("sharpe_net", 0.0)
    max_dd = metrics.get("max_dd_pct", 0.0)
    turnover = metrics.get("ann_turnover", 0.0)

    print(f"\nLEDGER_ROW\t{strategy_id}\t{family}\t{universe}\t{score}\t{sharpe}\t{max_dd}\t{turnover}\t{n_params}\t{status}\t{description}")


if __name__ == "__main__":
    print("harness.py — standalone test", file=sys.stderr)
    print("Import this module and call run_evaluation()", file=sys.stderr)
