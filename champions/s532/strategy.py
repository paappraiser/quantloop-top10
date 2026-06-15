#!/usr/bin/env python3
"""s532 — Risk Appetite Regime (RISKREG)

4-signal risk appetite classifier:
  1. Credit spread regime (HYG/LQD MA crossover)
  2. VIX level regime (VIX vs 63d median)
  3. SPY/TLT correlation regime (flight-to-safety signature)
  4. Gold as risk proxy (sudden gold drops = liquidation stress)

3-tier allocation: Risk-On / Neutral / Risk-Off.
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


def download_risk_data(start="2005-01-01"):
    """Download risk appetite data. Cache as pickle."""
    cache_file = CACHE_DIR / "s532_risk_data.pkl"

    if cache_file.exists():
        print("[s532] Loading risk data from cache …", file=sys.stderr)
        return pd.read_pickle(cache_file)

    print("[s532] Downloading risk appetite data …", file=sys.stderr)

    def _fetch(ticker, auto_adjust=True):
        df = yf.download(ticker, start=start, auto_adjust=auto_adjust, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            try:
                close = df.xs(ticker, axis=1, level=1)["Close"]
            except (KeyError, ValueError):
                close = df.xs("Close", axis=1, level=0).iloc[:, 0]
        elif "Close" in df.columns:
            close = df["Close"]
        else:
            close = df.iloc[:, 0]
        close.index = pd.to_datetime(close.index)
        close.name = ticker
        return close

    vix = _fetch("^VIX", auto_adjust=False)
    try:
        vix3m = _fetch("^VIX3M", auto_adjust=False)
    except Exception:
        vix3m = vix.copy()
    gld = _fetch("GLD")
    hyg = _fetch("HYG")
    lqd = _fetch("LQD")
    spy = _fetch("SPY")
    tlt = _fetch("TLT")

    result = {"vix": vix, "vix3m": vix3m, "gld": gld,
              "hyg": hyg, "lqd": lqd, "spy": spy, "tlt": tlt}
    pd.to_pickle(result, cache_file)
    print(f"[s532] Cached to {cache_file}", file=sys.stderr)
    return result


def compute_signals(data):
    """Compute 4 risk appetite signals. Returns DataFrame with composite."""
    vix = data["vix"]
    gld = data["gld"]
    hyg = data["hyg"]
    lqd = data["lqd"]
    spy = data["spy"]
    tlt = data["tlt"]

    all_dates = (
        vix.index.union(gld.index).union(hyg.index)
        .union(lqd.index).union(spy.index).union(tlt.index)
        .sort_values()
    )
    df = pd.DataFrame(index=all_dates)

    # Signal 1: Credit Spread Regime (HYG/LQD MA crossover)
    hyg_r = hyg.reindex(df.index).ffill()
    lqd_r = lqd.reindex(df.index).ffill()
    hy_lq = hyg_r / lqd_r.clip(lower=1e-8)
    ma_10 = hy_lq.rolling(10, min_periods=5).mean()
    ma_30 = hy_lq.rolling(30, min_periods=15).mean()
    df["sig1_credit"] = np.where(ma_10 > ma_30, 1, -1)

    # Signal 2: VIX Level Regime (vs 63d rolling median)
    vix_r = vix.reindex(df.index).ffill()
    vix_median = vix_r.rolling(63, min_periods=30).median()
    df["sig2_vix"] = np.where(vix_r < vix_median, 1, -1)

    # Signal 3: SPY/TLT Correlation Regime
    spy_r = spy.reindex(df.index).pct_change()
    tlt_r = tlt.reindex(df.index).pct_change()
    corr_20 = spy_r.rolling(20, min_periods=10).corr(tlt_r)
    df["sig3_corr"] = np.where(corr_20 < 0, 1, -1)

    # Signal 4: Gold Risk Proxy (sharp drops = liquidation)
    gld_r = gld.reindex(df.index).ffill()
    gld_21d = gld_r.pct_change(21)
    df["sig4_gold"] = np.where(gld_21d > -0.02, 1, -1)

    # Composite
    sig_cols = ["sig1_credit", "sig2_vix", "sig3_corr", "sig4_gold"]
    df["composite"] = df[sig_cols].sum(axis=1).fillna(0.0)
    for c in sig_cols:
        df[c] = df[c].fillna(0)

    return df


def make_signal(regime_df):
    """Factory: signal_fn with 3-tier risk allocation."""
    def risk_signal(train_px, test_px, **kw):
        tickers = list(test_px.columns)
        weights_list = []
        prev_weights = None

        reg = regime_df.reindex(test_px.index).ffill()

        for i, date in enumerate(test_px.index):
            is_rebal = (i == 0) or (date - test_px.index[i - 1]).days >= 2
            if not is_rebal and prev_weights is not None:
                weights_list.append(prev_weights.copy())
                continue

            if i == 0:
                prior = reg.index[reg.index < date]
                score = reg.loc[prior[-1], "composite"] if len(prior) > 0 else 0.0
            else:
                score = reg.loc[test_px.index[i - 1], "composite"] \
                    if test_px.index[i - 1] in reg.index else 0.0

            w = pd.Series(0.0, index=tickers)
            if score >= 2:  # Risk-On → max equity
                spy_w = 1.0
            elif score <= -1:  # Risk-Off → defensive
                spy_w = 0.2
            else:  # Neutral → equity-leaning balanced
                spy_w = 0.6

            w["SPY"] = spy_w
            if "TLT" in tickers:
                w["TLT"] = 1.0 - spy_w

            prev_weights = w
            weights_list.append(w)

        return pd.DataFrame(weights_list, index=test_px.index)
    return risk_signal


def main():
    print("=" * 60, file=sys.stderr)
    print("s532 — Risk Appetite Regime (RISKREG)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    data = download_risk_data()
    regime_df = compute_signals(data)

    print(f"[s532] Risk composite: mean={regime_df['composite'].mean():.2f}, "
          f"std={regime_df['composite'].std():.2f}", file=sys.stderr)
    comp = regime_df["composite"]
    print(f"[s532] Regime dist: RiskOn≥2={(comp>=2).mean()*100:.1f}%, "
          f"Neutral={(comp>-1).mean()*100:.1f}%, "
          f"RiskOff≤-1={(comp<=-1).mean()*100:.1f}%", file=sys.stderr)

    prices = download_data(["SPY", "TLT"], start="2010-01-01", asset_class="etf")
    print(f"[s532] Prices: {len(prices)} days, tickers: {list(prices.columns)}", file=sys.stderr)

    signal_fn = make_signal(regime_df)

    metrics = run_evaluation(
        prices=prices, signal_fn=signal_fn,
        cost_bps=10, asset_class="etf",
        n_trials=1, beta_ticker="SPY",
    )

    print(f"\n{'='*60}", file=sys.stderr)
    print("s532 — Risk Appetite Regime", file=sys.stderr)
    print("4 signals: credit spread, VIX level, SPY/TLT corr, gold risk", file=sys.stderr)
    print('='*60, file=sys.stderr)
    for k in ["SCORE", "sharpe_net", "sharpe_gross", "deflated_sharpe", "sortino",
              "max_dd_pct", "ann_turnover", "n_trades", "win_rate", "beta_spy", "oos_years"]:
        print(f"{k:20s} {metrics.get(k, 'N/A')}", file=sys.stderr)

    score = metrics.get("SCORE", 0)
    status = "keep" if score > 0 else "discard"
    print(f"\nLEDGER_ROW\ts532\trisk-appetite-regime\tspy-tlt\t"
          f"{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t"
          f"{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t"
          f"0\t{status}\t"
          f"RISKREG: 4-signal risk composite, 3-tier (RO/Neutral/Roff), gap=2d")


if __name__ == "__main__":
    main()
