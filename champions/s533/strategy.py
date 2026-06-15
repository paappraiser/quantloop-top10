#!/usr/bin/env python3
"""s533 — Yield Curve Regime (YCREG) v3

Per-position cap of 10% kills continuous allocation on 2-asset portfolios.
Must use DISCRETE allocation (SPY-only / TLT-only / 50-50) to generate
turnover in the capped weights.

Daily Δ yield curve signals but DISCRETE 3-tier allocation.
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
CACHE_DIR = HERE / "data"

def download_yc_data(start="2005-01-01"):
    cache_file = CACHE_DIR / "s533_yc_data.pkl"
    if cache_file.exists():
        print("[s533] Loading from cache …", file=sys.stderr); return pd.read_pickle(cache_file)
    print("[s533] Downloading …", file=sys.stderr)
    def _f(t):
        d = yf.download(t, start=start, auto_adjust=True, progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            try: c = d.xs(t, axis=1, level=1)["Close"]
            except (KeyError, ValueError): c = d.xs("Close", axis=1, level=0).iloc[:,0]
        elif "Close" in d.columns: c = d["Close"]
        else: c = d.iloc[:,0]
        c.index = pd.to_datetime(c.index); c.name = t; return c
    r = {"shy":_f("SHY"),"tlt":_f("TLT"),"spy":_f("SPY")}
    pd.to_pickle(r, cache_file); print(f"[s533] Cached", file=sys.stderr); return r

def compute_signals(data):
    shy, tlt = data["shy"], data["tlt"]
    ad = shy.index.union(tlt.index).sort_values()
    df = pd.DataFrame(index=ad)
    shy_r = shy.reindex(df.index).ffill(); tlt_r = tlt.reindex(df.index).ffill()
    curve = tlt_r / shy_r.clip(lower=1e-8)
    
    # 3 signals at 10d for responsiveness
    df["s1_slope"] = np.where(curve.pct_change(10) > 0, 1, -1)
    med = curve.rolling(252, min_periods=100).median()
    df["s2_level"] = np.where(curve > med, 1, -1)
    df["s3_rate"] = np.where(shy_r.pct_change(10) <= 0, 1, -1)  # falling short rates = accommodative
    
    # Add daily z-scored change for high-frequency component
    curve_d = curve.pct_change().fillna(0)
    cz = ((curve_d - curve_d.rolling(252, min_periods=60).mean()) / curve_d.rolling(252, min_periods=60).std().clip(lower=1e-6)).fillna(0).clip(-3,3)
    
    binary = df[["s1_slope","s2_level","s3_rate"]].sum(axis=1).fillna(0)
    df["composite"] = binary + cz * 0.15
    for c in ["s1_slope","s2_level","s3_rate"]: df[c] = df[c].fillna(0)
    return df

def make_signal(regime_df):
    def sig(train_px, test_px, **kw):
        tickers = list(test_px.columns); wl = []; p = None
        reg = regime_df.reindex(test_px.index).ffill()
        for i, date in enumerate(test_px.index):
            is_r = (i == 0) or (date - test_px.index[i-1]).days >= 2
            if not is_r and p is not None: wl.append(p.copy()); continue
            if i == 0: prior = reg.index[reg.index < date]; sc = reg.loc[prior[-1],"composite"] if len(prior) > 0 else 0.0
            else: sc = reg.loc[test_px.index[i-1],"composite"] if test_px.index[i-1] in reg.index else 0.0
            w = pd.Series(0.0, index=tickers)
            # Steepening/falling rates → SPY; Flattening/rising rates → TLT
            if sc >= 1.0: spy_w = 1.0
            elif sc <= -1.0: spy_w = 0.0
            else: spy_w = 0.5
            w["SPY"] = spy_w
            if "TLT" in tickers: w["TLT"] = 1.0 - spy_w
            p = w; wl.append(w)
        return pd.DataFrame(wl, index=test_px.index)
    return sig

def main():
    print("="*60, file=sys.stderr); print("s533v3 — Yield Curve Regime (YCREG)", file=sys.stderr); print("="*60, file=sys.stderr)
    data = download_yc_data(); regime_df = compute_signals(data)
    c = regime_df["composite"]
    print(f"[s533] Composite: mean={c.mean():.2f}, std={c.std():.2f}", file=sys.stderr)
    print(f"[s533] Dist: SPY≥1={(c>=1).mean()*100:.1f}%, TLT≤-1={(c<=-1).mean()*100:.1f}%, Neut={((c>-1)&(c<1)).mean()*100:.1f}%", file=sys.stderr)
    prices = download_data(["SPY","TLT"], start="2010-01-01", asset_class="etf")
    signal_fn = make_signal(regime_df)
    metrics = run_evaluation(prices=prices, signal_fn=signal_fn, cost_bps=10, asset_class="etf", n_trials=1, beta_ticker="SPY")
    score = metrics.get("SCORE",0); status = "keep" if score > 0 else "discard"
    print(f"\n{'='*60}", file=sys.stderr); print("s533v3 — Yield Curve Regime", file=sys.stderr); print('='*60, file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}", file=sys.stderr)
    print(f"\nLEDGER_ROW\ts533\tyield-curve-regime\tspy-tlt\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tYCREGv3: 3 sig(10d)+daily Δcurve, discrete 3-tier, gap=2d")
if __name__ == "__main__": main()
