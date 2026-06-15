#!/usr/bin/env python3
"""s006 — Enhanced Universe Trend Following (12 ETFs)."""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))

from harness import download_data, run_evaluation, print_ledger_row

# Expanded universe: add bonds, metals, currencies to the original 8
TICKERS = [
    "SPY", "EFA", "EEM",    # equities
    "TLT", "AGG", "HYG", "LQD", "SHY",  # bonds (long, agg, high-yield, corp, short)
    "GLD", "DBC", "DBB",    # commodities (gold, broad, copper)
    "FXE",                    # currencies (euro)
]
ASSET_CLASS = "etf"
COST_BPS = 10


def trend_signal(
    train_px: pd.DataFrame,
    test_px: pd.DataFrame,
    lookback: int = 252,
    vol_target_asset: float = 0.15,
    noise_threshold: float = 0.005,
) -> pd.DataFrame:
    """Time-series momentum (same as s003)."""
    all_px = pd.concat([train_px, test_px])
    tickers = list(all_px.columns)
    weights_list = []

    for i, date in enumerate(test_px.index):
        if i > 0 and (test_px.index[i - 1] - test_px.index[max(0, i - 5)]).days < 4:
            if weights_list:
                weights_list.append(weights_list[-1].copy())
            else:
                weights_list.append(pd.Series(0.0, index=tickers))
            continue

        hist = all_px.loc[:date]
        if len(hist) < lookback + 2:
            weights_list.append(pd.Series(0.0, index=tickers))
            continue

        trailing = hist.iloc[-1] / hist.iloc[-lookback - 1] - 1.0
        trailing = trailing.dropna()

        returns = hist.pct_change().dropna()
        vol = returns.ewm(span=60, min_periods=21).std().iloc[-1] * np.sqrt(252)

        weights = pd.Series(0.0, index=tickers)

        for tkr in tickers:
            if tkr not in trailing.index or tkr not in vol.index:
                continue
            if not np.isfinite(trailing[tkr]) or not np.isfinite(vol[tkr]):
                continue
            if vol[tkr] < 0.005:
                continue

            direction = 1.0 if trailing[tkr] > noise_threshold else (-1.0 if trailing[tkr] < -noise_threshold else 0.0)
            if direction == 0.0:
                continue

            vol_scale = vol_target_asset / vol[tkr]
            vol_scale = np.clip(vol_scale, 0.5, 2.0)

            ew = 1.0 / len(tickers)
            weights[tkr] = direction * ew * vol_scale

        gross = weights.abs().sum()
        if gross > 0:
            weights = weights / gross

        weights_list.append(weights)

    result = pd.DataFrame(weights_list, index=test_px.index)
    return result


def main():
    print("=" * 60, file=sys.stderr)
    print("s006: Enhanced Universe Trend Following (12 ETFs)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    prices = download_data(TICKERS, start="2007-01-01", asset_class=ASSET_CLASS)

    metrics = run_evaluation(
        prices=prices,
        signal_fn=trend_signal,
        cost_bps=COST_BPS,
        asset_class=ASSET_CLASS,
        n_trials=6,
        beta_ticker="SPY",
        lookback=252,
        vol_target_asset=0.15,
        noise_threshold=0.005,
    )

    score = metrics.get("SCORE", 0)
    n_trades = metrics.get("n_trades", 0)
    status = "keep" if score > 0 and n_trades >= 100 else "discard"

    print_ledger_row(
        strategy_id="s006",
        family="trend-following",
        universe="multi-asset",
        metrics=metrics,
        n_params=1,
        status=status,
        description=f"trend-following on 12 ETF universe (equities+bonds+commodities+FX), lookback=252",
    )

    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
