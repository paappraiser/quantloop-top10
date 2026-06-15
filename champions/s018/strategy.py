#!/usr/bin/env python3
"""s018 — Short-term reversal on ~200 large-cap US stocks."""

import sys, json, os
from pathlib import Path
import pandas as pd
import numpy as np

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation, print_ledger_row

# Top 200 US stocks by market cap (most liquid names)
TICKERS = [
    "AAPL","MSFT","AMZN","GOOGL","GOOG","META","BRK.B","JPM","V","PG",
    "JNJ","HD","MA","UNH","COST","DIS","NVDA","ADBE","CRM","NFLX",
    "PYPL","PEP","KO","ABBV","TMO","WMT","CVX","XOM","MRK","PFE",
    "ABT","BAC","AVGO","CMCSA","CSCO","INTC","AMD","NKE","T","VZ",
    "TXN","QCOM","AMGN","MDT","HON","UPS","BMY","LOW","SBUX","CAT",
    "GE","IBM","BA","MMM","F","GM","C","WFC","AXP","GS",
    "MS","SCHW","BLK","SPGI","DE","UNP","RTX","LMT","ISRG","SYK",
    "EL","MDLZ","CL","COP","EQIX","PLD","AMT","CCI","SO","DUK",
    "NEE","AEP","GILD","BSX","ADP","ITW","ETN","EMR","ROST","TJX",
    "VRTX","REGN","SCHW","ICE","MCO","CB","MMC","AON","APD","DHR",
    "ZTS","CI","HUM","ANTM","CVS","MCK","ABC","WBA","KMB","GIS",
    "K","CAG","CPB","SJM","HSY","CLX","CHD","KDP","MNST","DEO",
    "BUD","STZ","BF.B","KO","PEP","PM","MO","TAP","DAL","AAL",
    "UAL","LUV","FDX","JBHT","EXPD","CHRW","NSC","CSX","CNI","CP",
    "WMT","COST","TGT","DLTR","DG","ROST","TJX","LOW","HD","BBY",
    "AMZN","EBAY","ETSY","CPRT","KMX","AZO","ORLY","AAP","TSLA",
    "RCL","CCL","NCLH","WYNN","MGM","CZR","LVS","WY","DHI","LEN",
    "PHM","NVR","DOV","SWK","SNA","PH","IR","TT","OTIS","CARR",
    "JCI","ALLE","MAS","DRI","YUM","MCD","SBUX","CMG","DPZ","QSR",
    "BA","GD","NOC","LMT","RTX","TXT","COL","HII","LHX","HEI",
]
TICKERS = sorted(set([t.replace(".", "-") for t in TICKERS]))
ASSET_CLASS = "equity"
COST_BPS = 10


def reversal_signal(
    train_px, test_px, lookback=5, n_long=15, n_short=15,
):
    """Short-term reversal on 200 stocks, 15/15 equal-weight, weekly."""
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
        if len(hist) < lookback + 2:
            weights_list.append(pd.Series(0.0, index=tickers))
            continue

        ret = hist.iloc[-1] / hist.iloc[-lookback-1] - 1.0
        ret = ret.dropna()
        ret = ret[np.isfinite(ret)]

        valid = ret.index[ret.notna()]
        if len(valid) < n_long + n_short:
            if len(valid) < 2:
                weights_list.append(pd.Series(0.0, index=tickers))
                continue
            n_actual = max(len(valid)//2, 1)
        else:
            n_actual = n_long

        ranked = ret[valid].sort_values()
        weights = pd.Series(0.0, index=tickers)
        weights[ranked.index[:n_actual]] = 1.0/n_actual
        weights[ranked.index[-n_actual:]] = -1.0/n_actual
        weights_list.append(weights)

    return pd.DataFrame(weights_list, index=test_px.index)


def main():
    print("="*60, file=sys.stderr)
    print("s018: Reversal on 200 stocks (15/15 positions)", file=sys.stderr)
    print("="*60, file=sys.stderr)

    prices = download_data(TICKERS, start="2010-01-01", asset_class=ASSET_CLASS)
    print(f"[s018] Got {prices.shape[1]} tickers", file=sys.stderr)

    metrics = run_evaluation(
        prices=prices, signal_fn=reversal_signal,
        cost_bps=COST_BPS, asset_class=ASSET_CLASS,
        n_trials=18, beta_ticker="SPY",
        lookback=5, n_long=15, n_short=15,
    )

    score = metrics.get("SCORE", 0)
    n_trades = metrics.get("n_trades", 0)
    status = "keep" if score > 0 and n_trades >= 100 else "discard"
    print_ledger_row("s018", "mean-reversion", "sp200", metrics, 1, status,
                     "short-term reversal on 200 stocks, 15/15, weekly, equal-weight")
    print("\nDone.", file=sys.stderr)


if __name__ == "__main__":
    main()
