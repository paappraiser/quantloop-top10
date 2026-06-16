#!/usr/bin/env python3
"""s541 — Nasdaq Regime (QQQREG). Champion risk appetite recipe on QQQ+TLT."""
import sys,warnings; from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
HERE=Path(__file__).resolve().parent.parent.parent; sys.path.insert(0,str(HERE))
from harness import download_data,run_evaluation
warnings.filterwarnings("ignore"); CACHE_DIR=HERE/"data"

def download_data_541(start="2005-01-01"):
    cf=CACHE_DIR/"s541_data.pkl"
    if cf.exists(): print("[s541] Loading from cache …",file=sys.stderr); return pd.read_pickle(cf)
    print("[s541] Downloading …",file=sys.stderr)
    def _f(t,aa=True):
        d=yf.download(t,start=start,auto_adjust=aa,progress=False)
        if isinstance(d.columns,pd.MultiIndex):
            try: c=d.xs(t,axis=1,level=1)["Close"]
            except: c=d.xs("Close",axis=1,level=0).iloc[:,0]
        elif "Close" in d.columns: c=d["Close"]
        else: c=d.iloc[:,0]
        c.index=pd.to_datetime(c.index);c.name=t;return c
    r={}
    for t in ["QQQ","TLT","HYG","LQD","GLD"]: r[t.lower()]=_f(t)
    r["vix"]=_f("^VIX",aa=False)
    try: r["vix3m"]=_f("^VIX3M",aa=False)
    except: r["vix3m"]=r["vix"].copy()
    pd.to_pickle(r,cf);print("[s541] Cached",file=sys.stderr);return r

def compute_signals(data):
    hyg=data["hyg"];lqd=data["lqd"];vix=data["vix"]
    gld=data["gld"];qqq=data["qqq"];tlt=data["tlt"]
    ad=hyg.index.union(lqd.index).union(vix.index).union(gld.index).union(qqq.index).union(tlt.index).sort_values()
    df=pd.DataFrame(index=ad)
    hyg_a=hyg.reindex(df.index).ffill();lqd_a=lqd.reindex(df.index).ffill()
    vix_a=vix.reindex(df.index).ffill();gld_a=gld.reindex(df.index).ffill()
    qqq_a=qqq.reindex(df.index).ffill();tlt_a=tlt.reindex(df.index).ffill()
    hy_lq=hyg_a/lqd_a.clip(lower=1e-8)
    df["s1_credit"]=np.where(hy_lq.rolling(10).mean()>hy_lq.rolling(30).mean(),1,-1)
    vix_med=vix_a.rolling(63,min_periods=30).median()
    df["s2_vix"]=np.where(vix_a<vix_med,1,-1)
    qqq_r=qqq_a.pct_change();tlt_r=tlt_a.pct_change()
    df["s3_corr"]=np.where(qqq_r.rolling(20,min_periods=10).corr(tlt_r)<0,1,-1)
    df["s4_gold"]=np.where(gld_a.pct_change(21)>-0.02,1,-1)
    df["composite"]=df[["s1_credit","s2_vix","s3_corr","s4_gold"]].sum(axis=1).fillna(0)
    for c in ["s1_credit","s2_vix","s3_corr","s4_gold"]: df[c]=df[c].fillna(0)
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
            if sc>=2: q_w=1.0
            elif sc<=-1: q_w=0.0
            else: q_w=0.6
            w["QQQ"]=q_w
            if "TLT" in tickers: w["TLT"]=1.0-q_w
            p=w;wl.append(w)
        return pd.DataFrame(wl,index=test_px.index)
    return sig

def main():
    print("="*60,file=sys.stderr);print("s541 — Nasdaq Regime (QQQ+TLT)",file=sys.stderr);print("="*60,file=sys.stderr)
    data=download_data_541();regime_df=compute_signals(data)
    c=regime_df["composite"]
    print(f"[s541] Composite: mean={c.mean():.2f}, std={c.std():.2f}",file=sys.stderr)
    prices=download_data(["QQQ","TLT"],start="2010-01-01",asset_class="etf")
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="QQQ")
    score=metrics.get("SCORE",0);status="keep" if score>0 else "discard"
    print(f"\n{'='*60}",file=sys.stderr);print("s541 — Nasdaq Regime",file=sys.stderr);print('='*60,file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts541\tqqq-regime\tqqq-tlt\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tQQQREG: champion risk appetite recipe on QQQ+TLT instead of SPY+TLT")
if __name__=="__main__": main()
