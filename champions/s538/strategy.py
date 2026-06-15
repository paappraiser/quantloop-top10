#!/usr/bin/env python3
"""s538 — Unified Regime Ensemble (UNIFIED)

Meta-ensemble combining ALL independently-validated regime themes:
  - Risk Appetite (s532)
  - Growth (s534)
  - Inflation (s534)
  - Yield Curve (s533)
  - Dollar Cycle (s535)
  - Vol Ensemble (s537)

Each signal z-scored over 252d, clipped to [-2, +2], averaged.
4-tier allocation on SPY+TLT+GLD.
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation
warnings.filterwarnings("ignore")
CACHE_DIR=HERE/"data"

def download_ensemble_data(start="2005-01-01"):
    cf=CACHE_DIR/"s538_ensemble_data.pkl"
    if cf.exists():
        print("[s538] Loading from cache …",file=sys.stderr); return pd.read_pickle(cf)
    print("[s538] Downloading ensemble data …",file=sys.stderr)
    def _f(t,aa=True):
        d=yf.download(t,start=start,auto_adjust=aa,progress=False)
        if isinstance(d.columns,pd.MultiIndex):
            try: c=d.xs(t,axis=1,level=1)["Close"]
            except: c=d.xs("Close",axis=1,level=0).iloc[:,0]
        elif "Close" in d.columns: c=d["Close"]
        else: c=d.iloc[:,0]
        c.index=pd.to_datetime(c.index);c.name=t;return c
    
    # All tickers needed across all 6 signal groups
    result={}
    for t in ["SPY","TLT","GLD","EEM","HYG","LQD","DBC","UUP","TIP","SHY"]:
        result[t.lower()]=_f(t)
    for t in ["^VIX","^VIX3M","^SKEW"]:
        result[t.lower().replace("^","")]=_f(t,aa=False)
    pd.to_pickle(result,cf);print("[s538] Cached",file=sys.stderr);return result

def compute_signals(data):
    spy=data["spy"];tlt=data["tlt"];gld=data["gld"];eem=data["eem"]
    hyg=data["hyg"];lqd=data["lqd"];dbc=data["dbc"];uup=data["uup"]
    tip=data["tip"];shy=data["shy"];vix=data["vix"];vix3m=data["vix3m"]
    
    ad = (spy.index.union(tlt.index).union(gld.index).union(eem.index)
          .union(hyg.index).union(lqd.index).union(dbc.index).union(uup.index)
          .union(tip.index).union(shy.index).union(vix.index).union(vix3m.index)
          .sort_values())
    df=pd.DataFrame(index=ad)
    
    # Align all series
    spy_a=spy.reindex(df.index).ffill();tlt_a=tlt.reindex(df.index).ffill()
    gld_a=gld.reindex(df.index).ffill();hyg_a=hyg.reindex(df.index).ffill()
    lqd_a=lqd.reindex(df.index).ffill();dbc_a=dbc.reindex(df.index).ffill()
    uup_a=uup.reindex(df.index).ffill();tip_a=tip.reindex(df.index).ffill()
    shy_a=shy.reindex(df.index).ffill();vix_a=vix.reindex(df.index).ffill()
    vix3m_a=vix3m.reindex(df.index).ffill()
    
    # ═══════════════════════════════════════════════════════════════
    # 1. RISK APPETITE SIGNAL (s532)
    # ═══════════════════════════════════════════════════════════════
    hy_lq=hyg_a/lqd_a.clip(lower=1e-8)
    ma10=hy_lq.rolling(10,min_periods=5).mean()
    ma30=hy_lq.rolling(30,min_periods=15).mean()
    s1_credit=np.where(ma10>ma30,1,-1)
    vix_med=vix_a.rolling(63,min_periods=30).median()
    s1_vix=np.where(vix_a<vix_med,1,-1)
    spy_r=spy_a.pct_change();tlt_r=tlt_a.pct_change()
    corr20=spy_r.rolling(20,min_periods=10).corr(tlt_r)
    s1_corr=np.where(corr20<0,1,-1)
    gld_21d=gld_a.pct_change(21)
    s1_gold=np.where(gld_21d>-0.02,1,-1)
    df["sig_risk"]=pd.Series((s1_credit+s1_vix+s1_corr+s1_gold)/4.0, index=df.index).fillna(0)
    
    # ═══════════════════════════════════════════════════════════════
    # 2. GROWTH SIGNAL (s534 growth axis)
    # ═══════════════════════════════════════════════════════════════
    spy_mom_z=(spy_a.pct_change(63)/spy_a.pct_change(63).rolling(252).std().clip(lower=1e-6)).fillna(0)
    dbc_mom_z=(dbc_a.pct_change(63)/dbc_a.pct_change(63).rolling(252).std().clip(lower=1e-6)).fillna(0)
    df["sig_growth"]=((spy_mom_z.clip(-2,2)+dbc_mom_z.clip(-2,2))/2).fillna(0)
    
    # ═══════════════════════════════════════════════════════════════
    # 3. INFLATION SIGNAL (s534 inflation axis)
    # ═══════════════════════════════════════════════════════════════
    tip_shy=tip_a/shy_a.clip(lower=1e-8)
    tip_z=(tip_shy.pct_change(63)/tip_shy.pct_change(63).rolling(252).std().clip(lower=1e-6)).fillna(0)
    df["sig_infl"]=((tip_z.clip(-2,2)+dbc_mom_z.clip(-2,2))/2).fillna(0)
    
    # ═══════════════════════════════════════════════════════════════
    # 4. YIELD CURVE SIGNAL (s533)
    # ═══════════════════════════════════════════════════════════════
    curve=tlt_a/shy_a.clip(lower=1e-8)
    s4_slope=np.where(curve.pct_change(10)>0,1,-1)
    curve_med=curve.rolling(252,min_periods=100).median()
    s4_level=np.where(curve>curve_med,1,-1)
    s4_rate=np.where(shy_a.pct_change(10)<=0,1,-1)
    # Daily curve change z
    curve_d=curve.pct_change().fillna(0)
    cz=((curve_d-curve_d.rolling(252).mean())/curve_d.rolling(252).std().clip(lower=1e-6)).fillna(0).clip(-2,2)
    df["sig_yc"]=pd.Series((s4_slope+s4_level+s4_rate)/3.0+cz*0.1, index=df.index).fillna(0)
    
    # ═══════════════════════════════════════════════════════════════
    # 5. DOLLAR CYCLE SIGNAL (s535)
    # ═══════════════════════════════════════════════════════════════
    s5_dollar=np.where(uup_a.pct_change(20)<0,1,-1)
    s5_commodity=np.where(dbc_a.pct_change(20)>0,1,-1)
    eem_a=eem.reindex(df.index).ffill()
    em_spy=eem_a/spy_a.clip(lower=1e-8)
    s5_global=np.where(em_spy.pct_change(20)>0,1,-1)
    uup_daily=(-1*uup_a.pct_change().fillna(0)).fillna(0)
    uz=((uup_daily-uup_daily.rolling(252).mean())/uup_daily.rolling(252).std().clip(lower=1e-6)).fillna(0).clip(-2,2)
    df["sig_dollar"]=pd.Series((s5_dollar+s5_commodity+s5_global)/3.0+uz*0.1, index=df.index).fillna(0)
    
    # ═══════════════════════════════════════════════════════════════
    # 6. VOL ENSEMBLE SIGNAL (s537)
    # ═══════════════════════════════════════════════════════════════
    vix_ratio=vix_a/vix3m_a.clip(lower=1e-6)
    s6_vix=np.where(vix_ratio<0.95,1,np.where(vix_ratio>1.05,-1,0)).astype(float)
    rv5=spy_r.rolling(5,min_periods=3).std()*np.sqrt(252)
    rv63_med=rv5.rolling(63,min_periods=30).median()
    s6_rv=np.where(rv5<rv63_med,1,-1)
    dvix=vix_a.diff().abs()
    vov=((dvix-dvix.rolling(252).mean())/dvix.rolling(252).std().clip(lower=1e-6)).fillna(0).clip(-2,2)*-1
    df["sig_vol"]=pd.Series((s6_vix+s6_rv)/2.0+vov*0.15, index=df.index).fillna(0)
    
    # ═══════════════════════════════════════════════════════════════
    # ENSEMBLE: z-score normalize each signal, average
    # ═══════════════════════════════════════════════════════════════
    sig_cols=["sig_risk","sig_growth","sig_infl","sig_yc","sig_dollar","sig_vol"]
    for sc in sig_cols:
        mu=df[sc].rolling(252,min_periods=60).mean()
        sigma=df[sc].rolling(252,min_periods=60).std().clip(lower=1e-6)
        df[sc]=(df[sc]-mu)/sigma
    
    df["ensemble_raw"]=df[sig_cols].mean(axis=1).fillna(0).clip(-3,3)
    
    # Add daily delta (regime change momentum) for trade frequency
    df["ensemble_delta"]=df["ensemble_raw"].diff().fillna(0)*3.0
    df["ensemble"]=df["ensemble_raw"]+df["ensemble_delta"]
    
    print(f"[s538] Ensemble raw: mean={df['ensemble_raw'].mean():.3f}, std={df['ensemble_raw'].std():.3f}",file=sys.stderr)
    print(f"[s538] Ensemble (with delta): mean={df['ensemble'].mean():.3f}, std={df['ensemble'].std():.3f}",file=sys.stderr)
    return df

def make_signal(regime_df):
    allocs={
        "risk_on":   {"SPY":1.0,"TLT":0.0,"GLD":0.0},
        "neutral":   {"SPY":0.5,"TLT":0.5,"GLD":0.0},
        "defensive": {"SPY":0.3,"TLT":0.7,"GLD":0.0},
    }
    def sig(train_px,test_px,**kw):
        tickers=list(test_px.columns);wl=[];p=None
        reg=regime_df.reindex(test_px.index).ffill()
        for i,date in enumerate(test_px.index):
            is_r=(i==0) or (date-test_px.index[i-1]).days>=2
            if not is_r and p is not None: wl.append(p.copy());continue
            if i==0: prior=reg.index[reg.index<date];sc=reg.loc[prior[-1],"ensemble"] if len(prior)>0 else 0.0
            else: sc=reg.loc[test_px.index[i-1],"ensemble"] if test_px.index[i-1] in reg.index else 0.0
            w=pd.Series(0.0,index=tickers)
            if sc>=0.3: k="risk_on"
            elif sc>-0.3: k="neutral"
            else: k="defensive"
            a=allocs[k]
            for t in tickers: w[t]=a.get(t,0.0)
            p=w;wl.append(w)
        return pd.DataFrame(wl,index=test_px.index)
    return sig

def main():
    print("="*60,file=sys.stderr);print("s538 — Unified Regime Ensemble",file=sys.stderr);print("="*60,file=sys.stderr)
    data=download_ensemble_data();regime_df=compute_signals(data)
    c=regime_df["ensemble"]
    print(f"[s538] Dist: RiskOn≥0.5={(c>=0.5).mean()*100:.1f}%, Neutral={(c>-0.5).mean()*100:.1f}%, Defensive={(c>-1.5).mean()*100:.1f}%, Crisis≤-1.5={(c<=-1.5).mean()*100:.1f}%",file=sys.stderr)
    prices=download_data(["SPY","TLT","GLD"],start="2010-01-01",asset_class="etf")
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="SPY")
    score=metrics.get("SCORE",0);status="keep" if score>0 else "discard"
    print(f"\n{'='*60}",file=sys.stderr);print("s538 — Unified Regime Ensemble",file=sys.stderr);print('='*60,file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts538\tunified-ensemble\tspy-tlt-gld\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tUNIFIED: meta-ensemble 6 themes (risk/growth/infl/YC/dollar/vol)+daily delta, 3-tier SPY+TLT+GLD")
if __name__=="__main__": main()
