#!/usr/bin/env python3
"""s013 — Short-Term Mean Reversion on S&P 100 stocks."""

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


def reversal_signal(
    train_px: pd.DataFrame,
    test_px: pd.DataFrame,
    lookback: int = 5,
    n_long: int = 10,
    n_short: int = 10,
) -> pd.DataFrame:
    """Short-term mean reversion signal.

    Last week's losers become this week's winners (and vice versa).
    Long the n_long worst performers over lookback, short the n_short best performers.
    Weekly rebalance.
    """
    all_px = pd.concat([train_px, test_px])
    tickers = list(all_px.columns)
    weights_list = []

    for i, date in enumerate(test_px.index):
        # Weekly rebalance
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

        # Short-term return
        ret = hist.iloc[-1] / hist.iloc[-lookback - 1] - 1.0
        ret = ret.dropna()
        ret = ret[np.isfinite(ret)]

        valid = ret.index[ret.notna()]
        if len(valid) < n_long + n_short:
            weights_list.append(pd.Series(0.0, index=tickers))
            continue

        # Reverse ranking: worst performers → long, best performers → short
        ranked = ret[valid].sort_values()
        longs = ranked.index[:n_long]    # worst → long (expected to bounce)
        shorts = ranked.index[-n_short:] # best → short (expected to drop)

        weights = pd.Series(0.0, index=tickers)
        weights[longs] = 1.0 / n_long
        weights[shorts] = -1.0 / n_short
        weights_list.append(weights)

    result = pd.DataFrame(weights_list, index=test_px.index)
    return result


def main():
    print("=" * 60, file=sys.stderr)
    print("s013: Short-Term Mean Reversion (S&P 100)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    prices = download_data(TICKERS, start="2010-01-01", asset_class=ASSET_CLASS)
    print(f"[s013] Got {prices.shape[1]} tickers", file=sys.stderr)

    metrics = run_evaluation(
        prices=prices,
        signal_fn=reversal_signal,
        cost_bps=COST_BPS,
        asset_class=ASSET_CLASS,
        n_trials=13,
        beta_ticker="SPY",
        lookback=5,
        n_long=10,
        n_short=10,
    )

    score = metrics.get("SCORE", 0)
    n_trades = metrics.get("n_trades", 0)
    status = "keep" if score > 0 and n_trades >= 100 else "discard"

    print_ledger_row(
        strategy_id="s013",
        family="mean-reversion",
        universe="sp100",
        metrics=metrics,
        n_params=1,
        status=status,
        description="short-term mean reversion on S&P 100 stocks, 5-day reversal, weekly rebalance",
    )

    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
