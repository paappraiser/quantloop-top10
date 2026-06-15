#!/usr/bin/env python3
"""s015 — Concentrated Short-Term Reversal (5-day, top5/bottom5, magnitude-weighted)."""

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


def concentrated_reversal_signal(
    train_px: pd.DataFrame,
    test_px: pd.DataFrame,
    lookback: int = 5,
    n_long: int = 5,
    n_short: int = 5,
) -> pd.DataFrame:
    """Concentrated short-term mean reversion.

    Same 5-day reversal as s013, but only top/bottom 5 instead of 10.
    Positions are magnitude-weighted: stocks with larger moves get larger allocations.
    Higher conviction = better signal quality, lower turnover.
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

        ret = hist.iloc[-1] / hist.iloc[-lookback - 1] - 1.0
        ret = ret.dropna()
        ret = ret[np.isfinite(ret)]

        valid = ret.index[ret.notna()]
        if len(valid) < n_long + n_short:
            weights_list.append(pd.Series(0.0, index=tickers))
            continue

        # Rank by reversal (sort returns ascending)
        ranked = ret[valid].sort_values()
        short_candidates = ranked.index[-n_short:]
        long_candidates = ranked.index[:n_long]

        # Magnitude-weighted: weight = |return| / sum(|returns|) within each leg
        long_mags = ret[long_candidates].abs()
        short_mags = ret[short_candidates].abs()

        long_total = long_mags.sum()
        short_total = short_mags.sum()

        weights = pd.Series(0.0, index=tickers)

        if long_total > 0:
            for tkr in long_candidates:
                weights[tkr] = abs(ret[tkr]) / long_total
        if short_total > 0:
            for tkr in short_candidates:
                weights[tkr] = -abs(ret[tkr]) / short_total

        weights_list.append(weights)

    result = pd.DataFrame(weights_list, index=test_px.index)
    return result


def main():
    print("=" * 60, file=sys.stderr)
    print("s015: Concentrated Reversal (top5/bottom5, magnitude-weighted)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    prices = download_data(TICKERS, start="2010-01-01", asset_class=ASSET_CLASS)

    metrics = run_evaluation(
        prices=prices,
        signal_fn=concentrated_reversal_signal,
        cost_bps=COST_BPS,
        asset_class=ASSET_CLASS,
        n_trials=15,
        beta_ticker="SPY",
        lookback=5,
        n_long=5,
        n_short=5,
    )

    score = metrics.get("SCORE", 0)
    n_trades = metrics.get("n_trades", 0)
    status = "keep" if score > 0 and n_trades >= 100 else "discard"

    print_ledger_row(
        strategy_id="s015",
        family="mean-reversion",
        universe="sp100",
        metrics=metrics,
        n_params=1,
        status=status,
        description="concentrated mean reversion on S&P 100, 5-day reversal, top5/bottom5, magnitude-weighted",
    )

    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
