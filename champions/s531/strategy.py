#!/usr/bin/env python3
"""s531 — Inflation Regime Classifier (INFLREG) v5

Key insight: 2-asset portfolio with per-position cap of 10% means ONLY
discrete allocation (SPY-only / TLT-only / hybrid) creates turnover.
Continuous allocation gets uniformly capped at [0.1, 0.1] → zero turnover.

Return to discrete allocation with 20d binary signals. Match the pattern
that made s524 successful: extreme position switches.

4 binary signals (20d lookback) + daily breakeven z:
- Rising inflation → TLT-heavy
- Falling inflation → SPY-heavy
- Neutral → 50/50
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

def download_infl_data(start="2005-01-01"):
    cache_file = CACHE_DIR / "s531_infl_data.pkl"
    if cache_file.exists():
        print("[s531] Loading from cache …", file=sys.stderr)
        return pd.read_pickle(cache_file)
    print("[s531] Downloading …", file=sys.stderr)
    def _f(t):
        d = yf.download(t, start=start, auto_adjust=True, progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            try: c = d.xs(t, axis=1, level=1)["Close"]
            except (KeyError, ValueError): c = d.xs("Close", axis=1, level=0).iloc[:, 0]
        elif "Close" in d.columns: c = d["Close"]
        else: c = d.iloc[:, 0]
        c.index = pd.to_datetime(c.index); c.name = t; return c
    r = {"tip":_f("TIP"),"tlt":_f("TLT"),"dbc":_f("DBC"),"gld":_f("GLD"),"uup":_f("UUP"),"spy":_f("SPY")}
    pd.to_pickle(r, cache_file); print(f"[s531] Cached", file=sys.stderr); return r

def compute_signals(data):
    tip,tlt_i,dbc,gld,uup = data["tip"],data["tlt"],data["dbc"],data["gld"],data["uup"]
    ad = tip.index.union(tlt_i.index).union(dbc.index).union(gld.index).union(uup.index).sort_values()
    df = pd.DataFrame(index=ad)
    be = tip.reindex(df.index).ffill() / tlt_i.reindex(df.index).ffill().clip(lower=1e-8)
    dbc_r = dbc.reindex(df.index).ffill(); gld_r = gld.reindex(df.index).ffill(); uup_r = uup.reindex(df.index).ffill()
    df["s1"] = np.where(be.pct_change(20) > 0, 1, -1)
    df["s2"] = np.where(dbc_r.pct_change(20) > 0, 1, -1)
    df["s3"] = np.where(gld_r.pct_change(20) > 0, 1, -1)
    df["s4"] = np.where(uup_r.pct_change(20) < 0, 1, -1)
    # Daily breakeven movement adds high-frequency signal
    be_d = be.pct_change().fillna(0)
    be_z = ((be_d - be_d.rolling(252, min_periods=60).mean()) / be_d.rolling(252, min_periods=60).std().clip(lower=1e-6)).fillna(0).clip(-3,3)
    binary = df[["s1","s2","s3","s4"]].sum(axis=1).fillna(0)
    df["composite"] = binary + be_z * 0.15
    for c in ["s1","s2","s3","s4"]: df[c] = df[c].fillna(0)
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
            if sc >= 1.0: spy_w = 0.0   # Rising inflation → TLT
            elif sc <= -1.0: spy_w = 1.0  # Falling inflation → SPY
            else: spy_w = 0.5
            w["SPY"] = spy_w
            if "TLT" in tickers: w["TLT"] = 1.0 - spy_w
            p = w; wl.append(w)
        return pd.DataFrame(wl, index=test_px.index)
    return sig

def main():
    print("="*60, file=sys.stderr); print("s531v5 — Inflation Regime (INFLREG)", file=sys.stderr); print("="*60, file=sys.stderr)
    data = download_infl_data(); regime_df = compute_signals(data)
    c = regime_df["composite"]
    print(f"[s531] Composite: mean={c.mean():.2f}, std={c.std():.2f}", file=sys.stderr)
    print(f"[s531] Dist: SPY≥1={(c>=1).mean()*100:.1f}%, TLT≤-1={(c<=-1).mean()*100:.1f}%, Neut={((c>-1)&(c<1)).mean()*100:.1f}%", file=sys.stderr)
    prices = download_data(["SPY","TLT"], start="2010-01-01", asset_class="etf")
    signal_fn = make_signal(regime_df)
    metrics = run_evaluation(prices=prices, signal_fn=signal_fn, cost_bps=10, asset_class="etf", n_trials=1, beta_ticker="SPY")
    score = metrics.get("SCORE",0); status = "keep" if score > 0 else "discard"
    print(f"\n{'='*60}", file=sys.stderr); print("s531v5 — Inflation Regime Classifier", file=sys.stderr); print('='*60, file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}", file=sys.stderr)
    print(f"\nLEDGER_ROW\ts531\tinflation-regime\tspy-tlt\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tINFLREGv5: 4 binary(20d)+daily BE, discrete 3-tier alloc, gap=2d")
if __name__ == "__main__": main()
