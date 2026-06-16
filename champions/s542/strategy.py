#!/usr/bin/env python3
"""s542 — QQQ/SPY Ratio Mean Reversion (DISPERSION)."""
import sys,warnings; from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
HERE=Path(__file__).resolve().parent.parent.parent; sys.path.insert(0,str(HERE))
from harness import download_data,run_evaluation
warnings.filterwarnings("ignore"); CACHE_DIR=HERE/"data"

def download_data_542(start="2005-01-01"):
    cf=CACHE_DIR/"s542_data.pkl"
    if cf.exists(): print("[s542] Loading from cache …",file=sys.stderr); return pd.read_pickle(cf)
    print("[s542] Downloading …",file=sys.stderr)
    def _f(t):
        d=yf.download(t,start=start,auto_adjust=True,progress=False)
        if isinstance(d.columns,pd.MultiIndex):
            try: c=d.xs(t,axis=1,level=1)["Close"]
            except: c=d.xs("Close",axis=1,level=0).iloc[:,0]
        elif "Close" in d.columns: c=d["Close"]
        else: c=d.iloc[:,0]
        c.index=pd.to_datetime(c.index);c.name=t;return c
    r={t.lower():_f(t) for t in ["QQQ","SPY"]}
    pd.to_pickle(r,cf);print("[s542] Cached",file=sys.stderr);return r

def compute_signals(data):
    qqq=data["qqq"];spy=data["spy"]
    ad=qqq.index.union(spy.index).sort_values()
    df=pd.DataFrame(index=ad)
    qqq_a=qqq.reindex(df.index).ffill();spy_a=spy.reindex(df.index).ffill()
    ratio=qqq_a/spy_a.clip(lower=1e-8)
    ratio_z=(ratio-ratio.rolling(252,min_periods=100).mean())/ratio.rolling(252,min_periods=100).std().clip(lower=1e-6)
    df["ratio_z"]=ratio_z.fillna(0).clip(-3,3)
    # Daily delta for trade frequency
    df["delta"]=df["ratio_z"].diff().fillna(0)*2.0
    df["composite"]=df["ratio_z"]+df["delta"]
    return df

def make_signal(regime_df):
    def sig(train_px,test_px,**kw):
        tickers=list(test_px.columns);wl=[];p=None
        reg=regime_df.reindex(test_px.index).ffill()
        for i,date in enumerate(test_px.index):
            is_r=(i==0) or (date-test_px.index[i-1]).days>=2
            if not is_r and p is not None: wl.append(p.copy());continue
            if i==0: prior=reg.index[reg.index<date];z=reg.loc[prior[-1],"composite"] if len(prior)>0 else 0.0
            else: z=reg.loc[test_px.index[i-1],"composite"] if test_px.index[i-1] in reg.index else 0.0
            w=pd.Series(0.0,index=tickers)
            if z>=1.0: q_w=0.0;s_w=1.0  # QQQ overextended → long SPY/short QQQ
            elif z<=-1.0: q_w=1.0;s_w=0.0  # QQQ oversold → long QQQ/short SPY
            else: q_w=0.5;s_w=0.5
            w["QQQ"]=q_w;w["SPY"]=s_w
            p=w;wl.append(w)
        return pd.DataFrame(wl,index=test_px.index)
    return sig

def main():
    print("="*60,file=sys.stderr);print("s542 — QQQ/SPY Ratio Mean Reversion",file=sys.stderr);print("="*60,file=sys.stderr)
    data=download_data_542();regime_df=compute_signals(data)
    print(f"[s542] Ratio z: mean={regime_df['ratio_z'].mean():.2f}, std={regime_df['ratio_z'].std():.2f}",file=sys.stderr)
    prices=download_data(["QQQ","SPY"],start="2010-01-01",asset_class="etf")
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="SPY")
    score=metrics.get("SCORE",0);status="keep" if score>0 else "discard"
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts542\tqqq-spy-dispersion\tqqq-spy\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tDISPERSION: QQQ/SPY ratio z-score mean reversion (252d), 3-tier alloc")
if __name__=="__main__": main()
