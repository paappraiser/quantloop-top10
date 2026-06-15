#!/usr/bin/env python3
"""s536 — Cross-Asset Correlation Regime (CORREG)

PCA on 8-asset rolling correlation matrix → 4 regime quadrants.
8-asset universe: SPY, TLT, GLD, DBC, EEM, HYG, SHY, UUP.
Allocation on SPY+TLT+GLD with 4-tier discrete allocation.

Regime quadrants:
  Q1 (PC1>0, PC2>0): Risk-On + Growth     → 100% SPY
  Q2 (PC1>0, PC2<0): Risk-On + Inflation   → 60% SPY, 40% GLD
  Q3 (PC1<0, PC2>0): Risk-Off + Defensive  → 100% TLT
  Q4 (PC1<0, PC2<0): Risk-Off + Stress     → 60% TLT, 30% GLD, 10% SPY
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation
warnings.filterwarnings("ignore")
CACHE_DIR=HERE/"data"

PCA_TICKERS = ["SPY","TLT","GLD","DBC","EEM","HYG","SHY","UUP"]

def download_pca_data(start="2005-01-01"):
    cf=CACHE_DIR/"s536_pca_data.pkl"
    if cf.exists():
        print("[s536] Loading from cache …",file=sys.stderr); return pd.read_pickle(cf)
    print("[s536] Downloading PCA data …",file=sys.stderr)
    result={}
    for t in PCA_TICKERS:
        d=yf.download(t,start=start,auto_adjust=True,progress=False)
        if isinstance(d.columns,pd.MultiIndex):
            try: c=d.xs(t,axis=1,level=1)["Close"]
            except: c=d.xs("Close",axis=1,level=0).iloc[:,0]
        elif "Close" in d.columns: c=d["Close"]
        else: c=d.iloc[:,0]
        c.index=pd.to_datetime(c.index);c.name=t
        result[t.lower()]=c
        print(f"  {t}: {len(c)} days",file=sys.stderr)
    pd.to_pickle(result,cf);print("[s536] Cached",file=sys.stderr);return result

def compute_signals(data):
    # Build a single DataFrame of all returns
    rets_list=[]
    for t in PCA_TICKERS:
        px=data[t.lower()].copy()
        px.name=t
        rets_list.append(px.pct_change().rename(t))
    rets=pd.concat(rets_list,axis=1).dropna(how="all")
    
    dates=rets.index.sort_values()
    df=pd.DataFrame(index=dates)
    
    n_assets=len(PCA_TICKERS)
    lookback=60
    min_periods=40
    
    pc1_s=pd.Series(0.0,index=dates)
    pc2_s=pd.Series(0.0,index=dates)
    
    for i in range(lookback,len(dates)):
        window=rets.iloc[i-lookback:i]
        window=window.dropna(how="any",axis=0)
        if len(window)<min_periods:
            continue
        # Correlation matrix (remove scale)
        corr=window.corr().values
        # Handle NaN
        if np.isnan(corr).any():
            corr=np.nan_to_num(corr)
        # Eigen decomposition
        try:
            eigvals,eigvecs=np.linalg.eigh(corr)
        except np.linalg.LinAlgError:
            continue
        
        # PC1 and PC2 scores for the current date (dot product of latest return with eigenvectors)
        latest=window.iloc[-1].values
        pc1=np.dot(latest,eigvecs[:,-1])  # largest eigenvalue
        pc2=np.dot(latest,eigvecs[:,-2])  # second largest
        pc1_s.iloc[i]=pc1
        pc2_s.iloc[i]=pc2
    
    # Z-score normalize PCs
    m1=pc1_s.rolling(252,min_periods=60).mean()
    s1=pc1_s.rolling(252,min_periods=60).std().clip(lower=1e-6)
    m2=pc2_s.rolling(252,min_periods=60).mean()
    s2=pc2_s.rolling(252,min_periods=60).std().clip(lower=1e-6)
    
    df["pc1_z"]=((pc1_s-m1)/s1).fillna(0).clip(-3,3)
    df["pc2_z"]=((pc2_s-m2)/s2).fillna(0).clip(-3,3)
    
    # Quadrant
    df["quadrant"]=0
    df.loc[(df["pc1_z"]>0)&(df["pc2_z"]>0),"quadrant"]=0  # Q1: Risk-On+Growth
    df.loc[(df["pc1_z"]>0)&(df["pc2_z"]<=0),"quadrant"]=1  # Q2: Risk-On+Inflation
    df.loc[(df["pc1_z"]<=0)&(df["pc2_z"]>0),"quadrant"]=2  # Q3: Risk-Off+Defensive
    df.loc[(df["pc1_z"]<=0)&(df["pc2_z"]<=0),"quadrant"]=3  # Q4: Risk-Off+Stress
    
    # Regime strength (distance from origin)
    df["strength"]=np.sqrt(df["pc1_z"]**2+df["pc2_z"]**2)
    
    print(f"[s536] PC1: mean={pc1_s.mean():.6f}, var ratio ≈ {eigvals[-1]/eigvals.sum():.2f}" if i>=lookback else "",file=sys.stderr)
    for q in range(4):
        names=["Q1: Risk-On+Growth","Q2: Risk-On+Infl","Q3: Risk-Off+Def","Q4: Risk-Off+Stress"]
        print(f"       {names[q]}: {(df['quadrant']==q).mean()*100:.1f}%",file=sys.stderr)
    
    return df

def make_signal(regime_df):
    allocs={
        0: {"SPY":1.0,"TLT":0.0,"GLD":0.0},  # Q1: max risk
        1: {"SPY":0.6,"TLT":0.0,"GLD":0.4},  # Q2: equities + gold
        2: {"SPY":0.0,"TLT":1.0,"GLD":0.0},  # Q3: max defensive
        3: {"SPY":0.1,"TLT":0.6,"GLD":0.3},  # Q4: bonds + gold
    }
    def sig(train_px,test_px,**kw):
        tickers=list(test_px.columns);wl=[];p=None;prev_q=-1
        reg=regime_df.reindex(test_px.index).ffill()
        for i,date in enumerate(test_px.index):
            is_r=(i==0) or (date-test_px.index[i-1]).days>=2
            if not is_r and p is not None: wl.append(p.copy());continue
            if i==0: prior=reg.index[reg.index<date]
            if i==0:
                if len(prior)>0:
                    q=int(reg.loc[prior[-1],"quadrant"])
                else: q=0
            else: q=int(reg.loc[test_px.index[i-1],"quadrant"]) if test_px.index[i-1] in reg.index else 0
            # Only rebalance if quadrant changed (regime inertia)
            if q==prev_q and p is not None:
                wl.append(p.copy());continue
            w=pd.Series(0.0,index=tickers)
            a=allocs.get(q,allocs[0])
            for t in tickers: w[t]=a.get(t,0.0)
            p=w;prev_q=q;wl.append(w)
        return pd.DataFrame(wl,index=test_px.index)
    return sig

def main():
    print("="*60,file=sys.stderr);print("s536 — Cross-Asset Correlation Regime (PCA)",file=sys.stderr);print("="*60,file=sys.stderr)
    data=download_pca_data();regime_df=compute_signals(data)
    prices=download_data(["SPY","TLT","GLD"],start="2010-01-01",asset_class="etf")
    print(f"[s536] Prices: {len(prices)} days, tickers: {list(prices.columns)}",file=sys.stderr)
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="SPY")
    score=metrics.get("SCORE",0);status="keep" if score>0 else "discard"
    print(f"\n{'='*60}",file=sys.stderr);print("s536 — Cross-Asset Correlation Regime",file=sys.stderr);print('='*60,file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts536\tcorrelation-regime\tspy-tlt-gld\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tCORREG: PCA on 8-asset 60d rolling corr matrix, 4 quadrants SPY+TLT+GLD")
if __name__=="__main__": main()
