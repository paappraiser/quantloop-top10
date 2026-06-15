#!/usr/bin/env python3
"""s535 — Dollar/Global Macro Regime (USDCYCLE)

USD cycle drives cross-asset allocation across SPY+TLT+GLD+EEM.
4-tier discrete allocation based on 5-signal dollar composite.

Signals (20d binary + daily z-scored continuous):
  1. DOLLAR trend — UUP 20d momentum (inverted: falling USD = +1)
  2. COMMODITY confirmation — DBC 20d momentum (+1 = rising = weak USD)
  3. GLOBAL growth diff — EEM/SPY ratio 20d change (+1 = EM outperforming = weak USD)
  4. SAFE-HAVEN — GLD/TLT ratio 20d change (+1 = gold > bonds = dollar hedging)
  5. Daily UUP z-score — continuous, inverted (falling USD = positive)
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation
warnings.filterwarnings("ignore")
CACHE_DIR=HERE/"data"

def download_dollar_data(start="2005-01-01"):
    cf=CACHE_DIR/"s535_dollar_data.pkl"
    if cf.exists():
        print("[s535] Loading from cache …",file=sys.stderr); return pd.read_pickle(cf)
    print("[s535] Downloading …",file=sys.stderr)
    def _f(t):
        d=yf.download(t,start=start,auto_adjust=True,progress=False)
        if isinstance(d.columns,pd.MultiIndex):
            try: c=d.xs(t,axis=1,level=1)["Close"]
            except: c=d.xs("Close",axis=1,level=0).iloc[:,0]
        elif "Close" in d.columns: c=d["Close"]
        else: c=d.iloc[:,0]
        c.index=pd.to_datetime(c.index);c.name=t;return c
    r={"uup":_f("UUP"),"dbc":_f("DBC"),"eem":_f("EEM"),"gld":_f("GLD"),"spy":_f("SPY"),"tlt":_f("TLT")}
    pd.to_pickle(r,cf);print("[s535] Cached",file=sys.stderr);return r

def compute_signals(data):
    uup=data["uup"];dbc=data["dbc"];eem=data["eem"];gld=data["gld"];spy=data["spy"];tlt=data["tlt"]
    ad=uup.index.union(dbc.index).union(eem.index).union(gld.index).union(spy.index).union(tlt.index).sort_values()
    df=pd.DataFrame(index=ad)
    uup_r=uup.reindex(df.index).ffill();dbc_r=dbc.reindex(df.index).ffill()
    eem_r=eem.reindex(df.index).ffill();gld_r=gld.reindex(df.index).ffill()
    spy_r=spy.reindex(df.index).ffill();tlt_r=tlt.reindex(df.index).ffill()
    
    # S1: DOLLAR trend (inverted: falling USD = +1)
    df["s1_dollar"]=np.where(uup_r.pct_change(20)<0,1,-1)
    # S2: COMMODITY (rising commodities = weak USD = +1)
    df["s2_commodity"]=np.where(dbc_r.pct_change(20)>0,1,-1)
    # S3: GLOBAL growth diff (EM outperforming = weak USD = +1)
    em_spy=eem_r/spy_r.clip(lower=1e-8)
    df["s3_global"]=np.where(em_spy.pct_change(20)>0,1,-1)
    # S4: SAFE-HAVEN (GLD outperforming TLT = dollar hedging = +1)
    gld_tlt=gld_r/tlt_r.clip(lower=1e-8)
    df["s4_safehaven"]=np.where(gld_tlt.pct_change(20)>0,1,-1)
    # S5: Daily UUP z-score (continuous, inverted)
    uup_daily=uup_r.pct_change().fillna(0)
    mu=uup_daily.rolling(252,min_periods=60).mean()
    sig=uup_daily.rolling(252,min_periods=60).std().clip(lower=1e-6)
    df["s5_daily_z"]=((-1*(uup_daily-mu)/sig)).fillna(0).clip(-3,3)
    
    binary=df[["s1_dollar","s2_commodity","s3_global","s4_safehaven"]].sum(axis=1).fillna(0)
    df["composite"]=binary+df["s5_daily_z"]*0.15
    for c in ["s1_dollar","s2_commodity","s3_global","s4_safehaven"]: df[c]=df[c].fillna(0)
    return df

def make_signal(regime_df):
    # 4-tier allocation: [SPY, TLT, GLD, EEM]
    allocs={
        "strong":   {"SPY":0.3,"TLT":0.7,"GLD":0.0,"EEM":0.0},
        "mild_usd": {"SPY":0.4,"TLT":0.4,"GLD":0.1,"EEM":0.1},
        "mild_wk":  {"SPY":0.4,"TLT":0.2,"GLD":0.2,"EEM":0.2},
        "strong_wk":{"SPY":0.5,"TLT":0.0,"GLD":0.2,"EEM":0.3},
    }
    def sig(train_px,test_px,**kw):
        tickers=list(test_px.columns);wl=[];p=None
        reg=regime_df.reindex(test_px.index).ffill()
        for i,date in enumerate(test_px.index):
            is_r=(i==0) or (date-test_px.index[i-1]).days>=2
            if not is_r and p is not None: wl.append(p.copy());continue
            if i==0: prior=reg.index[reg.index<date];sc=reg.loc[prior[-1],"composite"] if len(prior)>0 else 0.0
            else: sc=reg.loc[test_px.index[i-1],"composite"] if test_px.index[i-1] in reg.index else 0.0
            w=pd.Series(0.0,index=tickers)
            if sc>=1.5: k="strong_wk"
            elif sc>=0: k="mild_wk"
            elif sc>=-1.5: k="mild_usd"
            else: k="strong"
            a=allocs[k]
            for t in tickers: w[t]=a.get(t,0.0)
            p=w;wl.append(w)
        return pd.DataFrame(wl,index=test_px.index)
    return sig

def main():
    print("="*60,file=sys.stderr);print("s535 — Dollar/Global Macro Regime",file=sys.stderr);print("="*60,file=sys.stderr)
    data=download_dollar_data();regime_df=compute_signals(data)
    c=regime_df["composite"]
    print(f"[s535] Composite: mean={c.mean():.2f}, std={c.std():.2f}",file=sys.stderr)
    print(f"[s535] Dist: StrongUSD≤-1.5={(c<=-1.5).mean()*100:.1f}%, MildUSD={((c>-1.5)&(c<0)).mean()*100:.1f}%, MildWeak={((c>=0)&(c<1.5)).mean()*100:.1f}%, StrongWeak≥1.5={(c>=1.5).mean()*100:.1f}%",file=sys.stderr)
    prices=download_data(["SPY","TLT","GLD","EEM"],start="2010-01-01",asset_class="etf")
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="SPY")
    score=metrics.get("SCORE",0);status="keep" if score>0 else "discard"
    print(f"\n{'='*60}",file=sys.stderr);print("s535 — Dollar/Global Macro Regime",file=sys.stderr);print('='*60,file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts535\tdollar-regime\tspy-tlt-gld-eem\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tUSDCYCLE: USD cycle 4-signal(20d)+daily, 4-tier alloc SPY+TLT+GLD+EEM")
if __name__=="__main__": main()
