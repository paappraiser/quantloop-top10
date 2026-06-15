#!/usr/bin/env python3
"""s019 — Combined short-term reversal + long-term momentum on S&P 100."""

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


def combo_signal(
    train_px, test_px, rev_lookback=5, mom_lookback=252,
    n_long=8, n_short=8,
):
    """Combined reversal + momentum signal.

    Score = z-score(5-day reversal) + z-score(12-month momentum).
    This pairs two independent anomalies for a more robust signal.
    """
    all_px = pd.concat([train_px, test_px])
    tickers = list(all_px.columns)
    weights_list = []

    for i, date in enumerate(test_px.index):
        if i > 0:
            prev = test_px.index[i-1]
            if (date - prev).days < 4:
                if weights_list:
                    weights_list.append(weights_list[-1].copy())
                else:
                    weights_list.append(pd.Series(0.0, index=tickers))
                continue

        hist = all_px.loc[:date]
        if len(hist) < max(rev_lookback, mom_lookback) + 2:
            weights_list.append(pd.Series(0.0, index=tickers))
            continue

        # Reversal score: positive when stock went DOWN (long cheap, short expensive)
        rev_ret = hist.iloc[-1] / hist.iloc[-rev_lookback-1] - 1.0
        # Momentum score: positive when stock went UP
        mom_ret = hist.iloc[-1] / hist.iloc[-mom_lookback-1] - 1.0

        # Compute z-scores cross-sectionally
        def zscore(s):
            s = s.dropna()
            s = s[np.isfinite(s)]
            if len(s) < 5:
                return pd.Series(0.0, index=s.index)
            return (s - s.mean()) / s.std()

        z_rev = zscore(-rev_ret)  # negative reversal = positive score (want to buy losers)
        z_mom = zscore(mom_ret)   # positive momentum = positive score

        # Combined score (average)
        common = z_rev.index.intersection(z_mom.index)
        if len(common) < n_long + n_short:
            weights_list.append(pd.Series(0.0, index=tickers))
            continue

        score = (z_rev[common] + z_mom[common]) / 2.0
        ranked = score.sort_values()

        weights = pd.Series(0.0, index=tickers)
        weights[ranked.index[:n_short]] = -1.0 / n_short  # lowest score → short
        weights[ranked.index[-n_long:]] = 1.0 / n_long    # highest score → long
        weights_list.append(weights)

    return pd.DataFrame(weights_list, index=test_px.index)


def main():
    print("="*60, file=sys.stderr)
    print("s019: Reversal + Momentum Composite (S&P 100)", file=sys.stderr)
    print("="*60, file=sys.stderr)

    prices = download_data(TICKERS, start="2010-01-01", asset_class=ASSET_CLASS)

    metrics = run_evaluation(
        prices=prices, signal_fn=combo_signal,
        cost_bps=COST_BPS, asset_class=ASSET_CLASS,
        n_trials=19, beta_ticker="SPY",
        rev_lookback=5, mom_lookback=252, n_long=8, n_short=8,
    )

    score = metrics.get("SCORE", 0)
    n_trades = metrics.get("n_trades", 0)
    status = "keep" if score > 0 and n_trades >= 100 else "discard"
    print_ledger_row("s019", "multi-factor", "sp100", metrics, 2, status,
                     "combined 5d reversal + 12m momentum on S&P 100, z-score composite, 8/8, weekly")
    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
