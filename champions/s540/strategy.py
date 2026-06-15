#!/usr/bin/env python3
"""s540 — Factor Rotation Regime (FACTOR)

Macro regime determines which factor ETFs to overweight.
4 factor ETFs: MTUM (Momentum), QUAL (Quality), USMV (Low Vol), VLUE (Value).
Top 2 selection by regime compatibility.
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation
warnings.filterwarnings("ignore")
CACHE_DIR=HERE/"data"

def download_factor_data(start="2005-01-01"):
    cf=CACHE_DIR/"s540_factor_data.pkl"
    if cf.exists():
        print("[s540] Loading from cache …",file=sys.stderr); return pd.read_pickle(cf)
    print("[s540] Downloading …",file=sys.stderr)
    def _f(t):
        d=yf.download(t,start=start,auto_adjust=True,progress=False)
        if isinstance(d.columns,pd.MultiIndex):
            try: c=d.xs(t,axis=1,level=1)["Close"]
            except: c=d.xs("Close",axis=1,level=0).iloc[:,0]
        elif "Close" in d.columns: c=d["Close"]
        else: c=d.iloc[:,0]
        c.index=pd.to_datetime(c.index);c.name=t;return c
    spy=_f("SPY");tlt=_f("TLT");vix=yf.download("^VIX",start=start,auto_adjust=False,progress=False)
    if isinstance(vix.columns,pd.MultiIndex):
        try: vix=vix.xs("^VIX",axis=1,level=1)["Close"]
        except: vix=vix.xs("Close",axis=1,level=0).iloc[:,0]
    elif "Close" in vix.columns: vix=vix["Close"]
    else: vix=vix.iloc[:,0]
    vix.index=pd.to_datetime(vix.index)
    # Factor ETFs
    mtum=_f("MTUM");qual=_f("QUAL");usmv=_f("USMV");vlue=_f("VLUE")
    r={"spy":spy,"tlt":tlt,"vix":vix,"mtum":mtum,"qual":qual,"usmv":usmv,"vlue":vlue}
    pd.to_pickle(r,cf);print("[s540] Cached",file=sys.stderr);return r

def compute_signals(data):
    spy=data["spy"];vix=data["vix"];shy=yf.download("SHY",start="2005-01-01",auto_adjust=True,progress=False)
    if isinstance(shy.columns,pd.MultiIndex):
        try: shy=shy.xs("SHY",axis=1,level=1)["Close"]
        except: shy=shy.xs("Close",axis=1,level=0).iloc[:,0]
    elif "Close" in shy.columns: shy=shy["Close"]
    else: shy=shy.iloc[:,0]
    shy.index=pd.to_datetime(shy.index)
    tlt=data["tlt"]
    
    ad=vix.index.union(spy.index).union(shy.index).union(tlt.index).sort_values()
    df=pd.DataFrame(index=ad)
    spy_a=spy.reindex(df.index).ffill();vix_a=vix.reindex(df.index).ffill()
    shy_a=shy.reindex(df.index).ffill();tlt_a=tlt.reindex(df.index).ffill()
    
    # S1: Vol Regime — VIX vs 63d median
    vix_med=vix_a.rolling(63,min_periods=30).median()
    df["s1_vol"]=np.where(vix_a<vix_med,1,-1)  # Low vol → MTUM
    
    # S2: Growth Regime — SPY 63d  
    spy_mom=spy_a.pct_change(63)
    df["s2_growth"]=np.where(spy_mom>0,1,-1)  # Growing → MTUM
    
    # S3: Yield Regime — TLT/SHY 63d change
    curve=tlt_a/shy_a.clip(lower=1e-8)
    curve_chg=curve.pct_change(63)
    df["s3_yield"]=np.where(curve_chg>0,1,-1)  # Falling yields → MTUM
    
    df["composite_raw"]=df[["s1_vol","s2_growth","s3_yield"]].sum(axis=1).fillna(0)
    # Add daily delta for trade frequency
    df["composite_delta"]=df["composite_raw"].diff().fillna(0)*2.0
    df["composite"]=df["composite_raw"]+df["composite_delta"]
    for c in ["s1_vol","s2_growth","s3_yield"]: df[c]=df[c].fillna(0)
    return df

def make_signal(regime_df):
    factor_alloc={
        1: ["MTUM","QUAL"],      # Risk-On: momentum + quality
        0: ["QUAL","USMV"],       # Mixed: quality + low vol (defensive)
        -1: ["USMV","VLUE"],      # Risk-Off: low vol + value
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
            if sc>=1: regime=1
            elif sc<=-1: regime=-1
            else: regime=0
            picks=factor_alloc[regime]
            for t in picks:
                if t in tickers: w[t]=1.0/len(picks)
            p=w;wl.append(w)
        return pd.DataFrame(wl,index=test_px.index)
    return sig

def main():
    print("="*60,file=sys.stderr);print("s540 — Factor Rotation Regime",file=sys.stderr);print("="*60,file=sys.stderr)
    data=download_factor_data();regime_df=compute_signals(data)
    c=regime_df["composite"]
    print(f"[s540] Composite: mean={c.mean():.2f}, std={c.std():.2f}",file=sys.stderr)
    print(f"[s540] Dist: RiskOn≥1={(c>=1).mean()*100:.1f}%, Mixed={(c>-1).mean()*100:.1f}%, RiskOff≤-1={(c<=-1).mean()*100:.1f}%",file=sys.stderr)
    prices=download_data(["MTUM","QUAL","USMV","VLUE"],start="2010-01-01",asset_class="etf")
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="SPY")
    score=metrics.get("SCORE",0);status="keep" if score>0 else "discard"
    print(f"\n{'='*60}",file=sys.stderr);print("s540 — Factor Rotation Regime",file=sys.stderr);print('='*60,file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts540\tfactor-rotation\tmtum-qual-usmv-vlue\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tFACTOR: 3 macro signals (vol/growth/yield) rotate MTUM/QUAL/USMV/VLUE top2")
if __name__=="__main__": main()
