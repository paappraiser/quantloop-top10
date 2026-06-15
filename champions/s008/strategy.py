#!/usr/bin/env python3
"""s008 — VIX-Regime Filtered Trend Following on 12-ETF Universe."""

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import yfinance as yf

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


def trend_with_vix_filter(
    train_px: pd.DataFrame,
    test_px: pd.DataFrame,
    lookback: int = 252,
    vol_target_asset: float = 0.15,
    noise_threshold: float = 0.005,
    vix_threshold: float = 30.0,
) -> pd.DataFrame:
    """Trend following with VIX regime filter: flatten when VIX > threshold."""
    all_px = pd.concat([train_px, test_px])
    tickers = list(all_px.columns)
    weights_list = []

    # Download VIX data
    try:
        vix_raw = yf.download("^VIX", start=all_px.index[0].strftime("%Y-%m-%d"),
                              end=all_px.index[-1].strftime("%Y-%m-%d"), auto_adjust=True, progress=False)
        if isinstance(vix_raw.columns, pd.MultiIndex):
            vix_close = vix_raw.xs("Close", axis=1, level=0).iloc[:, 0]
        else:
            vix_close = vix_raw["Close"]
    except Exception:
        vix_close = pd.Series(0.0, index=all_px.index)

    for i, date in enumerate(test_px.index):
        if i > 0 and (test_px.index[i - 1] - test_px.index[max(0, i - 5)]).days < 4:
            if weights_list:
                weights_list.append(weights_list[-1].copy())
            else:
                weights_list.append(pd.Series(0.0, index=tickers))
            continue

        # VIX filter: flatten if VIX > threshold
        vix_level = vix_close.reindex([date]).ffill().iloc[0] if date in vix_close.index else 0.0
        if vix_level > vix_threshold:
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
    print("s008: VIX-Regime Filtered Trend Following", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    prices = download_data(TICKERS, start="2007-01-01", asset_class=ASSET_CLASS)

    metrics = run_evaluation(
        prices=prices,
        signal_fn=trend_with_vix_filter,
        cost_bps=COST_BPS,
        asset_class=ASSET_CLASS,
        n_trials=8,
        beta_ticker="SPY",
        lookback=252,
        vol_target_asset=0.15,
        noise_threshold=0.005,
        vix_threshold=30.0,
    )

    score = metrics.get("SCORE", 0)
    n_trades = metrics.get("n_trades", 0)
    status = "keep" if score > 0 and n_trades >= 100 else "discard"

    print_ledger_row(
        strategy_id="s008",
        family="trend-following",
        universe="multi-asset",
        metrics=metrics,
        n_params=1,
        status=status,
        description=f"trend-following with VIX>30 flat filter on 12-ETF universe, lookback=252",
    )

    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
