#!/usr/bin/env python3
"""s524 — Market Regime Detection v2 (MRDv2)

Champion tuned config from s523 sweep:
  - discrete allocation (Benign/Neutral/Stressed)
  - benign_threshold=2, stressed_threshold=-1
  - rebalance_gap=2 (every 2+ days)
  
Achieved SCORE=0.8727, SR=0.8727, DD=-2.9%, 192 trades, TO=1.7x
"""

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

CACHE_DIR = HERE / "data"


def download_regime_data(start="2005-01-01"):
    """Download all data needed for regime signals. Cache as pickle."""
    cache_file = CACHE_DIR / "s523_regime_data.pkl"

    if cache_file.exists():
        print("[s524] Loading regime data from cache …", file=sys.stderr)
        return pd.read_pickle(cache_file)

    print("[s524] Downloading all regime data …", file=sys.stderr)

    spy_ohlcv = yf.download("SPY", start=start, auto_adjust=True, progress=False)
    if isinstance(spy_ohlcv.columns, pd.MultiIndex):
        spy_ohlcv = spy_ohlcv.xs("SPY", axis=1, level=1)
    spy_ohlcv.columns = [c.lower() for c in spy_ohlcv.columns]
    spy_ohlcv.index = pd.to_datetime(spy_ohlcv.index)

    def _fetch_index(ticker):
        df = yf.download(ticker, start=start, auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            close = df.xs(ticker, axis=1, level=1)["Close"]
        else:
            close = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
        close.index = pd.to_datetime(close.index)
        return close

    vix = _fetch_index("^VIX")
    try:
        vix3m = _fetch_index("^VIX3M")
    except Exception:
        vix3m = vix.copy()
    skew = _fetch_index("^SKEW")

    etf_data = yf.download(
        ["SPY", "TLT", "HYG", "LQD"],
        start=start, auto_adjust=True, progress=False,
    )
    if isinstance(etf_data.columns, pd.MultiIndex):
        etf_close = etf_data.xs("Close", axis=1, level=0)
    else:
        etf_close = etf_data[["SPY", "TLT", "HYG", "LQD"]]
    etf_close.columns = [c.strip().upper() for c in etf_close.columns]
    etf_close.index = pd.to_datetime(etf_close.index)

    result = {
        "spy_ohlcv": spy_ohlcv,
        "vix": vix, "vix3m": vix3m, "skew": skew,
        "spy": etf_close["SPY"], "tlt": etf_close["TLT"],
        "hyg": etf_close["HYG"], "lqd": etf_close["LQD"],
    }
    pd.to_pickle(result, cache_file)
    print(f"[s524] Cached to {cache_file}", file=sys.stderr)
    return result


def compute_regime_signals(data):
    """Compute all 5 regime signals. Returns DataFrame with signal values.
    Same as s523 — reused via cache.
    """
    spy_c = data["spy"]
    tlt = data["tlt"]
    hyg = data["hyg"]
    lqd = data["lqd"]
    vix = data["vix"]
    vix3m = data["vix3m"]
    skew = data["skew"]

    all_dates = spy_c.index.union(tlt.index).sort_values()
    df = pd.DataFrame(index=all_dates)

    # Signal 1: VIX Term Structure
    vix_a = vix.reindex(df.index).ffill()
    vix3m_a = vix3m.reindex(df.index).ffill()
    vix_ratio = vix_a / vix3m_a.clip(lower=1e-6)
    df["signal_1_vix_ts"] = np.where(vix_ratio < 1.0, 1, -1)

    # Signal 2: Realized Vol Trend
    spy_rets = spy_c.reindex(df.index).pct_change()
    rv_5 = spy_rets.rolling(5, min_periods=3).std() * np.sqrt(252)
    rv_21 = spy_rets.rolling(21, min_periods=10).std() * np.sqrt(252)
    rv_ratio = (rv_5 / rv_21.clip(lower=1e-8)).rolling(5, min_periods=3).mean()
    df["signal_2_rv_trend"] = np.where(rv_ratio < 1.0, 1, -1)

    # Signal 3: SPY/TLT Correlation
    spy_r = spy_c.reindex(df.index).pct_change()
    tlt_r = tlt.reindex(df.index).pct_change()
    corr_20 = spy_r.rolling(20, min_periods=10).corr(tlt_r)
    df["signal_3_corr"] = np.where(corr_20 < 0.1, 1, -1)

    # Signal 4: Credit Spread Momentum
    hy_lq = hyg.reindex(df.index) / lqd.reindex(df.index).clip(lower=1e-8)
    ma_10 = hy_lq.rolling(10, min_periods=5).mean()
    ma_30 = hy_lq.rolling(30, min_periods=15).mean()
    df["signal_4_credit"] = np.where(ma_10 > ma_30, 1, -1)

    # Signal 5: Options Skew
    skew_a = skew.reindex(df.index).ffill()
    df["signal_5_skew"] = np.where(skew_a.diff(20) < 5.0, 1, -1)

    # Composite
    signal_cols = [c for c in df.columns if c.startswith("signal_")]
    df["composite"] = df[signal_cols].sum(axis=1).fillna(0.0)
    for c in signal_cols:
        df[c] = df[c].fillna(0)

    return df


def make_signal(regime_df, benign_threshold=2, stressed_threshold=-1, rebalance_gap=2):
    """Factory: signal_fn with tuned params."""
    def regime_signal(train_px, test_px, **kw):
        tickers = list(test_px.columns)
        weights_list = []
        prev_weights = None

        reg_aligned = regime_df.reindex(test_px.index).ffill()

        for i, date in enumerate(test_px.index):
            is_rebal = (i == 0) or (date - test_px.index[i - 1]).days >= rebalance_gap
            if not is_rebal and prev_weights is not None:
                weights_list.append(prev_weights.copy())
                continue

            if i == 0:
                prior = reg_aligned.index[reg_aligned.index < date]
                score = reg_aligned.loc[prior[-1], "composite"] if len(prior) > 0 else 0.0
            else:
                prev_date = test_px.index[i - 1]
                score = reg_aligned.loc[prev_date, "composite"] if prev_date in reg_aligned.index else 0.0

            w = pd.Series(0.0, index=tickers)
            if score >= benign_threshold:
                spy_w = 1.0
            elif score < stressed_threshold:
                spy_w = 0.0
            else:
                spy_w = 0.5

            w["SPY"] = spy_w
            if "TLT" in tickers:
                w["TLT"] = 1.0 - spy_w

            prev_weights = w
            weights_list.append(w)

        return pd.DataFrame(weights_list, index=test_px.index)
    return regime_signal


def main():
    print("=" * 60, file=sys.stderr)
    print("s524 — Market Regime Detection v2 (Champion)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    data = download_regime_data()
    regime_df = compute_regime_signals(data)

    print(f"[s524] Regime composite: mean={regime_df['composite'].mean():.2f}, "
          f"std={regime_df['composite'].std():.2f}", file=sys.stderr)
    comp = regime_df["composite"]
    print(f"[s524] Regime distribution: Benign≥2={(comp>=2).mean()*100:.1f}%, "
          f"Neutral={(comp>= -1).mean()*100:.1f}%, Stressed<-1={(comp<-1).mean()*100:.1f}%",
          file=sys.stderr)

    prices = download_data(["SPY", "TLT"], start="2010-01-01", asset_class="etf")
    print(f"[s524] Prices: {len(prices)} days", file=sys.stderr)

    signal_fn = make_signal(regime_df, benign_threshold=2, stressed_threshold=-1, rebalance_gap=2)

    metrics = run_evaluation(
        prices=prices, signal_fn=signal_fn,
        cost_bps=10, asset_class="etf",
        n_trials=1, beta_ticker="SPY",
    )

    print(f"\n{'='*60}", file=sys.stderr)
    print("s524 — Market Regime Detection v2", file=sys.stderr)
    print(f"Params: benign≥2, stressed<-1, gap=2d", file=sys.stderr)
    print('='*60, file=sys.stderr)
    for k in ["SCORE", "sharpe_net", "sharpe_gross", "deflated_sharpe", "sortino",
              "max_dd_pct", "ann_turnover", "n_trades", "win_rate", "beta_spy", "oos_years"]:
        print(f"{k:20s} {metrics.get(k, 'N/A')}", file=sys.stderr)

    score = metrics.get("SCORE", 0)
    status = "keep" if score > 0 else "discard"
    print(f"\nLEDGER_ROW\ts524\tregime-detection\tspy-tlt\t"
          f"{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t"
          f"{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t"
          f"2\t{status}\t"
          f"MRDv2: 5-signal composite, benign≥2/stressed<-1, gap=2d rebalance")


if __name__ == "__main__":
    main()
