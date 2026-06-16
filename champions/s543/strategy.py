#!/usr/bin/env python3
"""s543 — Tech Vol Stress Regime (VXNDIVERGE). VXN/VIX divergence on QQQ+TLT."""
import sys,warnings; from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
HERE=Path(__file__).resolve().parent.parent.parent; sys.path.insert(0,str(HERE))
from harness import download_data,run_evaluation
warnings.filterwarnings("ignore"); CACHE_DIR=HERE/"data"

def download_data_543(start="2005-01-01"):
    cf=CACHE_DIR/"s543_data.pkl"
    if cf.exists(): print("[s543] Loading from cache …",file=sys.stderr); return pd.read_pickle(cf)
    print("[s543] Downloading …",file=sys.stderr)
    def _f(t,aa=True):
        d=yf.download(t,start=start,auto_adjust=aa,progress=False)
        if isinstance(d.columns,pd.MultiIndex):
            try: c=d.xs(t,axis=1,level=1)["Close"]
            except: c=d.xs("Close",axis=1,level=0).iloc[:,0]
        elif "Close" in d.columns: c=d["Close"]
        else: c=d.iloc[:,0]
        c.index=pd.to_datetime(c.index);c.name=t;return c
    r={}
    for t in ["QQQ","TLT"]: r[t.lower()]=_f(t)
    r["vix"]=_f("^VIX",aa=False)
    try: r["vxn"]=_f("^VXN",aa=False)
    except: r["vxn"]=r["vix"].copy()  # Fallback if VXN unavailable
    pd.to_pickle(r,cf);print("[s543] Cached",file=sys.stderr);return r

def compute_signals(data):
    qqq=data["qqq"];tlt=data["tlt"];vix=data["vix"];vxn=data["vxn"]
    ad=qqq.index.union(tlt.index).union(vix.index).union(vxn.index).sort_values()
    df=pd.DataFrame(index=ad)
    qqq_a=qqq.reindex(df.index).ffill();tlt_a=tlt.reindex(df.index).ffill()
    vix_a=vix.reindex(df.index).ffill();vxn_a=vxn.reindex(df.index).ffill()
    
    # S1: VXN/VIX ratio change (20d) — tech-specific stress
    vxn_vix=vxn_a/vix_a.clip(lower=1e-6)
    df["s1_vxn_ratio"]=np.where(vxn_vix.pct_change(20)<0,1,-1)  # Ratio falling = tech calm = +1
    
    # S2: VIX level vs 63d median
    vix_med=vix_a.rolling(63,min_periods=30).median()
    df["s2_vix"]=np.where(vix_a<vix_med,1,-1)
    
    # S3: QQQ/TLT correlation
    qqq_r=qqq_a.pct_change();tlt_r=tlt_a.pct_change()
    df["s3_corr"]=np.where(qqq_r.rolling(20,min_periods=10).corr(tlt_r)<0,1,-1)
    
    # Daily VXN/VIX z-scored change for trade frequency
    vxn_daily=vxn_vix.pct_change().fillna(0)
    vz=((vxn_daily-vxn_daily.rolling(252).mean())/vxn_daily.rolling(252).std().clip(lower=1e-6)).fillna(0).clip(-3,3)*-1
    
    binary=df[["s1_vxn_ratio","s2_vix","s3_corr"]].sum(axis=1).fillna(0)
    df["composite"]=binary+vz*0.15
    for c in ["s1_vxn_ratio","s2_vix","s3_corr"]: df[c]=df[c].fillna(0)
    return df

def make_signal(regime_df):
    def sig(train_px,test_px,**kw):
        tickers=list(test_px.columns);wl=[];p=None
        reg=regime_df.reindex(test_px.index).ffill()
        for i,date in enumerate(test_px.index):
            is_r=(i==0) or (date-test_px.index[i-1]).days>=2
            if not is_r and p is not None: wl.append(p.copy());continue
            if i==0: prior=reg.index[reg.index<date];sc=reg.loc[prior[-1],"composite"] if len(prior)>0 else 0.0
            else: sc=reg.loc[test_px.index[i-1],"composite"] if test_px.index[i-1] in reg.index else 0.0
            w=pd.Series(0.0,index=tickers)
            if sc>=1.0: q_w=1.0   # Tech calm → max QQQ
            elif sc<=-1.0: q_w=0.0  # Tech stress → TLT
            else: q_w=0.6
            w["QQQ"]=q_w
            if "TLT" in tickers: w["TLT"]=1.0-q_w
            p=w;wl.append(w)
        return pd.DataFrame(wl,index=test_px.index)
    return sig

def main():
    print("="*60,file=sys.stderr);print("s543 — Tech Vol Stress (VXN/VIX divergence)",file=sys.stderr);print("="*60,file=sys.stderr)
    data=download_data_543();regime_df=compute_signals(data)
    c=regime_df["composite"]
    print(f"[s543] Composite: mean={c.mean():.2f}, std={c.std():.2f}",file=sys.stderr)
    prices=download_data(["QQQ","TLT"],start="2010-01-01",asset_class="etf")
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="QQQ")
    score=metrics.get("SCORE",0);status="keep" if score>0 else "discard"
    print(f"\n{'='*60}",file=sys.stderr);print("s543 — Tech Vol Stress",file=sys.stderr);print('='*60,file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts543\ttech-vol-stress\tqqq-tlt\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tVXNDIVERGE: VXN/VIX ratio divergence + VIX level + QQQ/TLT corr, disc 3-tier")
if __name__=="__main__": main()
