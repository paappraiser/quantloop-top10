#!/usr/bin/env python3
"""s528 — Regime-Based Sector Rotation

Use the 5-signal regime composite to determine market regime.
Then within each regime, allocate to the best-performing sector ETF.

Benign → long XLK, XLF (cyclical leaders)
Neutral → equal-weight all 4 sectors
Stressed → long XLU (defensive), flat others

Variant: ranked allocation — pick the top N sectors by trailing momentum.
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

# Sector ETFs
SECTOR_TICKERS = ["XLK", "XLF", "XLE", "XLU"]


def download_regime_data(start="2005-01-01"):
    """Reuse s523 cache for regime data, then download sector ETFs."""
    cache_file = CACHE_DIR / "s523_regime_data.pkl"
    if not cache_file.exists():
        print("[s528] Need to build regime data cache first", file=sys.stderr)
        # Quick build
        spy_ohlcv = yf.download("SPY", start=start, auto_adjust=True, progress=False)
        if isinstance(spy_ohlcv.columns, pd.MultiIndex):
            spy_ohlcv = spy_ohlcv.xs("SPY", axis=1, level=1)
        spy_ohlcv.columns = [c.lower() for c in spy_ohlcv.columns]
        spy_ohlcv.index = pd.to_datetime(spy_ohlcv.index)

        def _fetch_index(ticker):
            df = yf.download(ticker, start=start, auto_adjust=False, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                return df.xs(ticker, axis=1, level=1)["Close"]
            return df["Close"] if "Close" in df.columns else df.iloc[:, 0]

        vix = _fetch_index("^VIX")
        try:
            vix3m = _fetch_index("^VIX3M")
        except Exception:
            vix3m = vix.copy()
        skew = _fetch_index("^SKEW")

        etf_data = yf.download(["SPY", "TLT", "HYG", "LQD"], start=start, auto_adjust=True, progress=False)
        if isinstance(etf_data.columns, pd.MultiIndex):
            etf_close = etf_data.xs("Close", axis=1, level=0)
        else:
            etf_close = etf_data[["SPY", "TLT", "HYG", "LQD"]]
        etf_close.columns = [c.strip().upper() for c in etf_close.columns]
        etf_close.index = pd.to_datetime(etf_close.index)

        result = {
            "spy_ohlcv": spy_ohlcv, "vix": vix, "vix3m": vix3m, "skew": skew,
            "spy": etf_close["SPY"], "tlt": etf_close["TLT"],
            "hyg": etf_close["HYG"], "lqd": etf_close["LQD"],
        }
        pd.to_pickle(result, cache_file)
    else:
        print("[s528] Loading regime data from cache …", file=sys.stderr)
        result = pd.read_pickle(cache_file)

    # Download sector ETFs
    print("[s528] Loading sector ETF prices …", file=sys.stderr)
    sector_prices = download_data(SECTOR_TICKERS, start="2010-01-01", asset_class="etf")
    result["sector_prices"] = sector_prices
    return result


def compute_regime_signals(data):
    """Same 5-signal composite as s523."""
    spy_c = data["spy"]; tlt = data["tlt"]; hyg = data["hyg"]; lqd = data["lqd"]
    vix = data["vix"]; vix3m = data["vix3m"]; skew = data["skew"]

    all_dates = spy_c.index
    df = pd.DataFrame(index=all_dates)

    vix_a = vix.reindex(df.index).ffill()
    vix3m_a = vix3m.reindex(df.index).ffill()
    df["sig1_vix"] = np.where(vix_a / vix3m_a.clip(lower=1e-6) < 1.0, 1, -1)

    spy_r = spy_c.reindex(df.index).pct_change()
    df["sig2_rv"] = np.where(
        (spy_r.rolling(5).std() / spy_r.rolling(21).std().clip(lower=1e-8))
        .rolling(5).mean() < 1.0, 1, -1)

    tlt_r = tlt.reindex(df.index).pct_change()
    df["sig3_corr"] = np.where(spy_r.rolling(20, min_periods=10).corr(tlt_r) < 0.1, 1, -1)

    hy_lq = hyg.reindex(df.index) / lqd.reindex(df.index).clip(lower=1e-8)
    df["sig4_credit"] = np.where(
        hy_lq.rolling(10).mean() > hy_lq.rolling(30).mean(), 1, -1)

    skew_a = skew.reindex(df.index).ffill()
    df["sig5_skew"] = np.where(skew_a.diff(20) < 5.0, 1, -1)

    sig_cols = ["sig1_vix", "sig2_rv", "sig3_corr", "sig4_credit", "sig5_skew"]
    df["composite"] = df[sig_cols].sum(axis=1).fillna(0.0)
    for c in sig_cols:
        df[c] = df[c].fillna(0)
    return df


def make_signal(regime_df, sector_prices, lookback_months=3):
    """Factory: allocate to sectors based on regime."""
    lookback_days = lookback_months * 21
    # Precompute sector trailing returns
    sec_rets = sector_prices.pct_change()
    sec_mom = sec_rets.rolling(lookback_days, min_periods=lookback_days // 2).sum()

    def sector_rotation_signal(train_px, test_px, **kw):
        tickers = list(test_px.columns)
        weights_list = []
        prev_weights = None

        reg = regime_df.reindex(test_px.index).ffill()
        mom = sec_mom.reindex(test_px.index).ffill()

        for i, date in enumerate(test_px.index):
            is_rebal = (i == 0) or (date - test_px.index[i - 1]).days >= 2
            if not is_rebal and prev_weights is not None:
                weights_list.append(prev_weights.copy())
                continue

            # Yesterday's regime
            if i == 0:
                prior = reg.index[reg.index < date]
                score = reg.loc[prior[-1], "composite"] if len(prior) > 0 else 0.0
            else:
                score = reg.loc[test_px.index[i-1], "composite"] \
                    if test_px.index[i-1] in reg.index else 0.0

            w = pd.Series(0.0, index=tickers)

            if score >= 2:  # Benign
                # Long cyclical: XLK, XLF
                w["XLK"] = 0.5
                w["XLF"] = 0.5
            elif score < 0:  # Stressed
                # Defensive: XLU
                w["XLU"] = 1.0
            else:  # Neutral: pick best 2 from XLK/XLF/XLU (exclude XLE — commodity-driven)
                neutral_candidates = [t for t in tickers if t != "XLE"]
                if date in mom.index:
                    mom_sorted = mom.loc[date].dropna().sort_values(ascending=False)
                    best2 = [t for t in mom_sorted.index if t in neutral_candidates][:2]
                    for t in best2:
                        w[t] = 0.5 if len(best2) > 0 else 0.0
                else:
                    for t in neutral_candidates:
                        w[t] = 1.0 / len(neutral_candidates)

            prev_weights = w
            weights_list.append(w)

        return pd.DataFrame(weights_list, index=test_px.index)
    return sector_rotation_signal


def main():
    print("="*60, file=sys.stderr)
    print("s528 — Regime-Based Sector Rotation", file=sys.stderr)
    print("="*60, file=sys.stderr)

    data = download_regime_data()
    regime_df = compute_regime_signals(data)
    sec_prices = data["sector_prices"]
    print(f"[s528] Sector prices: {sec_prices.shape}, tickers: {list(sec_prices.columns)}", file=sys.stderr)

    signal_fn = make_signal(regime_df, sec_prices, lookback_months=3)

    metrics = run_evaluation(
        prices=sec_prices, signal_fn=signal_fn,
        cost_bps=10, asset_class="etf",
        n_trials=1, beta_ticker="SPY",
    )

    print(f"\n{'='*60}", file=sys.stderr)
    print("s528 — Regime-Based Sector Rotation", file=sys.stderr)
    print('='*60, file=sys.stderr)
    for k in ["SCORE", "sharpe_net", "sharpe_gross", "deflated_sharpe", "sortino",
              "max_dd_pct", "ann_turnover", "n_trades", "win_rate", "beta_spy", "oos_years"]:
        print(f"{k:20s} {metrics.get(k, 'N/A')}", file=sys.stderr)

    score = metrics.get("SCORE", 0)
    print(f"\nLEDGER_ROW\ts528\tregime-sector-rot\tspy-tlt-sectors\t"
          f"{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t"
          f"{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t"
          f"2\t{'keep' if score > 0 else 'discard'}\t"
          f"Regime-Based Sector Rotation: Benign→XLK+XLF, Stressed→XLU, Neutral→best2 by 3mo momentum")


if __name__ == "__main__":
    main()
