#!/usr/bin/env python3
"""s539 — Tail Risk Regime (TAILREG)

Options market tail risk (SKEW, VIX TS, credit) for crash protection timing.
Discrete 3-tier allocation on SPY+TLT+GLD.
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation
warnings.filterwarnings("ignore")
CACHE_DIR=HERE/"data"

def download_tail_data(start="2005-01-01"):
    cf=CACHE_DIR/"s539_tail_data.pkl"
    if cf.exists():
        print("[s539] Loading from cache …",file=sys.stderr); return pd.read_pickle(cf)
    print("[s539] Downloading …",file=sys.stderr)
    def _f(t,aa=True):
        d=yf.download(t,start=start,auto_adjust=aa,progress=False)
        if isinstance(d.columns,pd.MultiIndex):
            try: c=d.xs(t,axis=1,level=1)["Close"]
            except: c=d.xs("Close",axis=1,level=0).iloc[:,0]
        elif "Close" in d.columns: c=d["Close"]
        else: c=d.iloc[:,0]
        c.index=pd.to_datetime(c.index); c.name=t; return c
    r={"skew":_f("^SKEW",aa=False),"vix":_f("^VIX",aa=False),"vix3m":_f("^VIX3M",aa=False),"hyg":_f("HYG"),"lqd":_f("LQD"),"spy":_f("SPY")}
    pd.to_pickle(r,cf); print("[s539] Cached",file=sys.stderr); return r

def compute_signals(data):
    sk=data["skew"]; vx=data["vix"]; v3=data["vix3m"]; hg=data["hyg"]; lq=data["lqd"]
    ad=sk.index.union(vx.index).union(v3.index).union(hg.index).union(lq.index).sort_values()
    df=pd.DataFrame(index=ad)
    sk_a=sk.reindex(df.index).ffill(); vx_a=vx.reindex(df.index).ffill()
    v3_a=v3.reindex(df.index).ffill(); hg_a=hg.reindex(df.index).ffill(); lq_a=lq.reindex(df.index).ffill()
    # S1: SKEW 20d change
    sk_chg=sk_a.diff(20)
    df["s1_skew"]=np.where(sk_chg<5,1,-1)
    # S2: VIX TS
    vx_r=vx_a/v3_a.clip(lower=1e-6)
    df["s2_vix_ts"]=np.where(vx_r<1.05,1,-1)
    # S3: Credit tail (HYG/LQD 10d return)
    hy_lq=hg_a/lq_a.clip(lower=1e-8)
    hy_lq_10d=hy_lq.pct_change(10)
    df["s3_credit"]=np.where(hy_lq_10d>-0.01,1,-1)
    # S4: SKEW daily change z-scored (continuous, inverted)
    sk_daily=sk_a.diff().fillna(0)
    mu=sk_daily.rolling(252,min_periods=60).mean(); sig=sk_daily.rolling(252,min_periods=60).std().clip(lower=1e-6)
    df["s4_skew_z"]=((sk_daily-mu)/sig).fillna(0).clip(-3,3)*-1
    binary=df[["s1_skew","s2_vix_ts","s3_credit"]].sum(axis=1).fillna(0)
    df["composite"]=binary+df["s4_skew_z"]*0.15
    for c in ["s1_skew","s2_vix_ts","s3_credit"]: df[c]=df[c].fillna(0)
    return df

def make_signal(regime_df):
    def sig(train_px,test_px,**kw):
        tickers=list(test_px.columns); wl=[]; p=None
        reg=regime_df.reindex(test_px.index).ffill()
        for i,date in enumerate(test_px.index):
            is_r=(i==0) or (date-test_px.index[i-1]).days>=2
            if not is_r and p is not None: wl.append(p.copy()); continue
            if i==0: prior=reg.index[reg.index<date]; sc=reg.loc[prior[-1],"composite"] if len(prior)>0 else 0.0
            else: sc=reg.loc[test_px.index[i-1],"composite"] if test_px.index[i-1] in reg.index else 0.0
            w=pd.Series(0.0,index=tickers)
            if sc>=1:     # Normal → SPX
                alloc={"SPY":1.0,"TLT":0.0,"GLD":0.0}
            elif sc==0:   # Elevated → balanced
                alloc={"SPY":0.5,"TLT":0.5,"GLD":0.0}
            else:         # Distressed → protective
                alloc={"SPY":0.3,"TLT":0.4,"GLD":0.3}
            for t in tickers: w[t]=alloc.get(t,0.0)
            p=w; wl.append(w)
        return pd.DataFrame(wl,index=test_px.index)
    return sig

def main():
    print("="*60,file=sys.stderr);print("s539 — Tail Risk Regime",file=sys.stderr);print("="*60,file=sys.stderr)
    data=download_tail_data();regime_df=compute_signals(data)
    c=regime_df["composite"]
    print(f"[s539] Composite: mean={c.mean():.2f}, std={c.std():.2f}",file=sys.stderr)
    print(f"[s539] Dist: Normal≥1={(c>=1).mean()*100:.1f}%, Elevated={(c==0).mean()*100:.1f}%, Distressed≤-1={(c<=-1).mean()*100:.1f}%",file=sys.stderr)
    prices=download_data(["SPY","TLT","GLD"],start="2010-01-01",asset_class="etf")
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="SPY")
    score=metrics.get("SCORE",0);status="keep" if score>0 else "discard"
    print(f"\n{'='*60}",file=sys.stderr);print("s539 — Tail Risk Regime",file=sys.stderr);print('='*60,file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts539\ttail-risk-regime\tspy-tlt-gld\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tTAILREG: SKEW/VIX TS/credit tail risk signals, 3-tier SPY+TLT+GLD")
if __name__=="__main__": main()
