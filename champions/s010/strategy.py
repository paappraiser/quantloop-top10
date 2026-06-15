#!/usr/bin/env python3
"""s010 — Dual Moving Average Crossover Trend (50/200 day) on 12-ETF universe."""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))

from harness import download_data, run_evaluation, print_ledger_row

TICKERS = [
    "SPY", "EFA", "EEM",
    "TLT", "AGG", "HYG", "LQD", "SHY",
    "GLD", "DBC", "DBB",
    "FXE",
]
ASSET_CLASS = "etf"
COST_BPS = 10


def ma_crossover_signal(
    train_px: pd.DataFrame,
    test_px: pd.DataFrame,
    fast_ma: int = 50,
    slow_ma: int = 200,
    vol_target_asset: float = 0.15,
    noise_threshold: float = 0.0,
) -> pd.DataFrame:
    """Dual MA crossover trend signal.

    Position = +1 if fast_MA > slow_MA (uptrend), -1 if fast_MA < slow_MA (downtrend).
    Vol-scaled per asset, equal-weight allocation.
    """
    all_px = pd.concat([train_px, test_px])
    tickers = list(all_px.columns)
    weights_list = []

    for i, date in enumerate(test_px.index):
        # Weekly rebalance
        if i > 0 and (test_px.index[i - 1] - test_px.index[max(0, i - 5)]).days < 4:
            if weights_list:
                weights_list.append(weights_list[-1].copy())
            else:
                weights_list.append(pd.Series(0.0, index=tickers))
            continue

        hist = all_px.loc[:date]
        if len(hist) < slow_ma + 2:
            weights_list.append(pd.Series(0.0, index=tickers))
            continue

        # Compute MAs
        fast = hist.rolling(fast_ma, min_periods=fast_ma).mean().iloc[-1]
        slow = hist.rolling(slow_ma, min_periods=slow_ma).mean().iloc[-1]

        # Volatility
        returns = hist.pct_change().dropna()
        vol = returns.ewm(span=60, min_periods=21).std().iloc[-1] * np.sqrt(252)

        weights = pd.Series(0.0, index=tickers)

        for tkr in tickers:
            if tkr not in fast.index or tkr not in vol.index:
                continue
            if not np.isfinite(fast[tkr]) or not np.isfinite(slow[tkr]) or not np.isfinite(vol[tkr]):
                continue
            if vol[tkr] < 0.005:
                continue

            # Signal: MA crossover
            if fast[tkr] > slow[tkr]:
                direction = 1.0
            else:
                direction = -1.0

            # Add a slight buffer near the crossover to reduce whipsaws
            pct_diff = abs(fast[tkr] / slow[tkr] - 1.0)
            if pct_diff < 0.002:  # 0.2% buffer zone
                direction = 0.0

            if direction == 0.0:
                continue

            # Vol scaling
            vol_scale = vol_target_asset / vol[tkr]
            vol_scale = np.clip(vol_scale, 0.5, 2.0)

            ew = 1.0 / len(tickers)
            weights[tkr] = direction * ew * vol_scale

        # Normalise
        gross = weights.abs().sum()
        if gross > 0:
            weights = weights / gross

        weights_list.append(weights)

    result = pd.DataFrame(weights_list, index=test_px.index)
    return result


def main():
    print("=" * 60, file=sys.stderr)
    print("s010: Dual MA Crossover Trend (50/200)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    prices = download_data(TICKERS, start="2007-01-01", asset_class=ASSET_CLASS)

    metrics = run_evaluation(
        prices=prices,
        signal_fn=ma_crossover_signal,
        cost_bps=COST_BPS,
        asset_class=ASSET_CLASS,
        n_trials=10,
        beta_ticker="SPY",
        fast_ma=50,
        slow_ma=200,
        vol_target_asset=0.15,
        noise_threshold=0.0,
    )

    score = metrics.get("SCORE", 0)
    n_trades = metrics.get("n_trades", 0)
    status = "keep" if score > 0 and n_trades >= 100 else "discard"

    print_ledger_row(
        strategy_id="s010",
        family="trend-following",
        universe="multi-asset",
        metrics=metrics,
        n_params=1,
        status=status,
        description=f"50/200 day MA crossover on 12-ETF universe, weekly rebalance, vol-scaled",
    )

    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
