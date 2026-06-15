#!/usr/bin/env python3
"""s537 — Volatility Regime Ensemble (VOLREG)

5 vol-based signals on SPY+TLT. Discrete 3-tier allocation.

Signals:
  1. VIX Term Structure (VIX/VIX3M ratio, ternary: +1/-1/0)
  2. SPY RV Regime (5d RV vs 63d median)
  3. Bond Vol (TLT 21d RV vs 126d median)
  4. Vol Dispersion (HYG vol / TLT vol)
  5. Vol-of-Vol (dVIX absolute z-scored, continuous)
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation
warnings.filterwarnings("ignore")

CACHE_DIR = HERE / "data"

def download_vol_data(start="2005-01-01"):
    cache_file = CACHE_DIR / "s537_vol_data.pkl"
    if cache_file.exists():
        print("[s537] Loading from cache …", file=sys.stderr)
        return pd.read_pickle(cache_file)
    print("[s537] Downloading …", file=sys.stderr)
    def _f(t, aa=True):
        d = yf.download(t, start=start, auto_adjust=aa, progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            try: c = d.xs(t, axis=1, level=1)["Close"]
            except (KeyError, ValueError): c = d.xs("Close", axis=1, level=0).iloc[:,0]
        elif "Close" in d.columns: c = d["Close"]
        else: c = d.iloc[:,0]
        c.index = pd.to_datetime(c.index); c.name = t; return c
    vix = _f("^VIX", aa=False)
    try: vix3m = _f("^VIX3M", aa=False)
    except: vix3m = vix.copy()
    hyg = _f("HYG"); spy = _f("SPY"); tlt = _f("TLT")
    r = {"vix":vix,"vix3m":vix3m,"hyg":hyg,"lqd":_f("LQD"),"spy":spy,"tlt":tlt}
    pd.to_pickle(r, cache_file); print("[s537] Cached", file=sys.stderr); return r

def compute_signals(data):
    vix = data["vix"]; vix3m = data["vix3m"]; hyg = data["hyg"]
    lqd = data["lqd"]; spy = data["spy"]; tlt = data["tlt"]
    ad = vix.index.union(vix3m.index).union(hyg.index).union(lqd.index).union(spy.index).union(tlt.index).sort_values()
    df = pd.DataFrame(index=ad)
    
    vix_a = vix.reindex(df.index).ffill()
    vix3m_a = vix3m.reindex(df.index).ffill()
    hyg_a = hyg.reindex(df.index).ffill()
    lqd_a = lqd.reindex(df.index).ffill()
    spy_a = spy.reindex(df.index).ffill()
    tlt_a = tlt.reindex(df.index).ffill()
    
    # Signal 1: VIX Term Structure (ternary)
    vix_ratio = vix_a / vix3m_a.clip(lower=1e-6)
    df["s1_vix_ts"] = np.where(vix_ratio < 0.95, 1, np.where(vix_ratio > 1.05, -1, 0)).astype(float)
    
    # Signal 2: SPY RV Regime (5d vs 63d median)
    spy_r = spy_a.pct_change()
    rv_5 = spy_r.rolling(5, min_periods=3).std() * np.sqrt(252)
    rv_63_med = rv_5.rolling(63, min_periods=30).median()
    df["s2_spy_rv"] = np.where(rv_5 < rv_63_med, 1, -1)
    
    # Signal 3: Bond Vol Regime (TLT 21d vs 126d median)
    tlt_r = tlt_a.pct_change()
    tlt_rv_21 = tlt_r.rolling(21, min_periods=10).std() * np.sqrt(252)
    tlt_rv_126_med = tlt_rv_21.rolling(126, min_periods=60).median()
    df["s3_tlt_rv"] = np.where(tlt_rv_21 < tlt_rv_126_med, 1, -1)
    
    # Signal 4: Vol Dispersion (HYG vol / TLT vol)
    hyg_r = hyg_a.pct_change()
    hyg_rv_21 = hyg_r.rolling(21, min_periods=10).std() * np.sqrt(252)
    vol_disp = hyg_rv_21 / tlt_rv_21.clip(lower=1e-6)
    disp_63_med = vol_disp.rolling(63, min_periods=30).median()
    df["s4_vol_disp"] = np.where(vol_disp < disp_63_med * 1.5, 1, -1)
    
    # Signal 5: Vol-of-Vol (dVIX abs z-scored)
    dvix = vix_a.diff().abs()
    vov_mu = dvix.rolling(252, min_periods=60).mean()
    vov_sig = dvix.rolling(252, min_periods=60).std().clip(lower=1e-6)
    df["s5_vov"] = ((dvix - vov_mu) / vov_sig).fillna(0).clip(-3, 3) * -1  # Inverted: high vol-of-vol = stress
    
    # Composite
    binary = df[["s1_vix_ts","s2_spy_rv","s3_tlt_rv","s4_vol_disp"]].sum(axis=1).fillna(0)
    df["composite"] = binary + df["s5_vov"] * 0.2
    for c in ["s1_vix_ts","s2_spy_rv","s3_tlt_rv","s4_vol_disp"]: df[c] = df[c].fillna(0)
    return df

def make_signal(regime_df):
    def sig(train_px, test_px, **kw):
        tickers = list(test_px.columns); wl = []; p = None
        reg = regime_df.reindex(test_px.index).ffill()
        for i, date in enumerate(test_px.index):
            is_r = (i==0) or (date - test_px.index[i-1]).days >= 2
            if not is_r and p is not None: wl.append(p.copy()); continue
            if i==0: prior=reg.index[reg.index<date]; sc=reg.loc[prior[-1],"composite"] if len(prior)>0 else 0.0
            else: sc=reg.loc[test_px.index[i-1],"composite"] if test_px.index[i-1] in reg.index else 0.0
            w = pd.Series(0.0, index=tickers)
            if sc >= 1.0: spy_w=1.0     # Low Vol → SPX
            elif sc <= -1.0: spy_w=0.0  # High Vol → TLT
            else: spy_w=0.6             # Medium → balanced
            w["SPY"]=spy_w
            if "TLT" in tickers: w["TLT"]=1.0-spy_w
            p=w; wl.append(w)
        return pd.DataFrame(wl, index=test_px.index)
    return sig

def main():
    print("="*60, file=sys.stderr); print("s537 — Volatility Regime Ensemble", file=sys.stderr); print("="*60, file=sys.stderr)
    data=download_vol_data(); regime_df=compute_signals(data)
    c=regime_df["composite"]
    print(f"[s537] Composite: mean={c.mean():.2f}, std={c.std():.2f}", file=sys.stderr)
    print(f"[s537] Dist: LowVol≥1={(c>=1).mean()*100:.1f}%, Med={((c>-1)&(c<1)).mean()*100:.1f}%, HiVol≤-1={(c<=-1).mean()*100:.1f}%", file=sys.stderr)
    prices=download_data(["SPY","TLT"], start="2010-01-01", asset_class="etf")
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="SPY")
    score=metrics.get("SCORE",0); status="keep" if score>0 else "discard"
    print(f"\n{'='*60}",file=sys.stderr); print("s537 — Volatility Regime Ensemble",file=sys.stderr);print('='*60,file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts537\tvol-ensemble\tspy-tlt\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tVOLREG: 5 vol signals (VIX TS, SPY RV, TLT RV, vol disp, vol-of-vol), disc 3-tier")
if __name__=="__main__": main()
