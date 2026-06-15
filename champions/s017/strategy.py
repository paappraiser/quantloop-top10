#!/usr/bin/env python3
"""s017 — Short-term reversal on S&P 100 with 1% minimum move filter."""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))

from harness import download_data, run_evaluation, print_ledger_row

TICKERS = [
    "AAPL","MSFT","AMZN","GOOGL","META","JPM","JNJ","V","PG","XOM",
    "HD","CVX","PEP","KO","MRK","ABBV","WMT","BAC","PFE","AVGO",
    "TMO","DIS","CSCO","ACN","VZ","NFLX","ADBE","NKE","CMCSA","CRM",
    "TXN","NEE","BMY","UNP","MDT","AMGN","HON","LIN","QCOM","T",
    "UPS","LOW","RTX","COP","SBUX","LMT","INTU","AMAT","SYK","EL",
    "SPGI","BLK","ISRG","CAT","DE","GILD","BSX","ADP","TJX","PLD",
    "DHR","ZTS","SCHW","CB","CI","CL","C","PNC","MDLZ","ITW",
    "EQIX","MMC","SO","DUK","WM","SHW","APD","ETN","GM","FDX",
    "USB","VRTX","MET","PRU","BK","AIG","KMB","TGT","AON","F",
    "MMM","BA","GE","IBM","WFC","INTC","AMD","PYPL","REGN","MS",
    "ICE","GS","AXP","COST",
]
TICKERS = [t.replace(".", "-") for t in TICKERS]
ASSET_CLASS = "equity"
COST_BPS = 10


def reversal_filtered_signal(
    train_px: pd.DataFrame,
    test_px: pd.DataFrame,
    lookback: int = 5,
    n_long: int = 10,
    n_short: int = 10,
    min_move: float = 0.01,
) -> pd.DataFrame:
    """Short-term reversal with minimum move filter.

    Same as s013 (equal-weight 10/10) but only trade stocks that moved > 1%
    in the lookback period. This filters out noisy signals and reduces turnover.
    """
    all_px = pd.concat([train_px, test_px])
    tickers = list(all_px.columns)
    weights_list = []

    for i, date in enumerate(test_px.index):
        if i > 0:
            prev_date = test_px.index[i - 1]
            if (date - prev_date).days < 4:
                if weights_list:
                    weights_list.append(weights_list[-1].copy())
                else:
                    weights_list.append(pd.Series(0.0, index=tickers))
                continue

        hist = all_px.loc[:date]
        if len(hist) < lookback + 2:
            weights_list.append(pd.Series(0.0, index=tickers))
            continue

        ret = hist.iloc[-1] / hist.iloc[-lookback - 1] - 1.0
        ret = ret.dropna()
        ret = ret[np.isfinite(ret)]

        # Filter: only trade stocks with moves > min_move
        ret = ret[ret.abs() > min_move]

        valid = ret.index[ret.notna()]
        if len(valid) < n_long + n_short:
            # If not enough stocks qualify, trade what we can
            if len(valid) < 2:
                weights_list.append(pd.Series(0.0, index=tickers))
                continue
            n_actual = min(len(valid) // 2, n_long)
            n_actual = max(n_actual, 1)
        else:
            n_actual = n_long

        ranked = ret[valid].sort_values()
        longs = ranked.index[:n_actual]
        shorts = ranked.index[-n_actual:]

        weights = pd.Series(0.0, index=tickers)
        weights[longs] = 1.0 / n_actual
        weights[shorts] = -1.0 / n_actual
        weights_list.append(weights)

    return pd.DataFrame(weights_list, index=test_px.index)


def main():
    print("=" * 60, file=sys.stderr)
    print("s017: Filtered Reversal (min 1% move)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    prices = download_data(TICKERS, start="2010-01-01", asset_class=ASSET_CLASS)

    metrics = run_evaluation(
        prices=prices,
        signal_fn=reversal_filtered_signal,
        cost_bps=COST_BPS,
        asset_class=ASSET_CLASS,
        n_trials=17,
        beta_ticker="SPY",
        lookback=5, n_long=10, n_short=10, min_move=0.01,
    )

    score = metrics.get("SCORE", 0)
    n_trades = metrics.get("n_trades", 0)
    status = "keep" if score > 0 and n_trades >= 100 else "discard"
    print_ledger_row(
        strategy_id="s017", family="mean-reversion", universe="sp100",
        metrics=metrics, n_params=1, status=status,
        description="filtered reversal S&P 100, 5-day, 10/10, min_move=1%",
    )
    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
