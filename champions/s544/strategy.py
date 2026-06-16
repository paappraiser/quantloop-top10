#!/usr/bin/env python3
"""s544 — Aggregated Stock Reversal Pressure (CROWD).

Compute 5-day reversal z-score for ~200 stocks, average them,
use the aggregate as SPY/TLT market-timing signal.

S&P 200 proxy: 200 liquid stock tickers from yfinance.
Download once, cache, then compute daily signal.
"""
import sys,warnings; from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
HERE=Path(__file__).resolve().parent.parent.parent; sys.path.insert(0,str(HERE))
from harness import download_data,run_evaluation
warnings.filterwarnings("ignore"); CACHE_DIR=HERE/"data"

# S&P 200 proxy — 200 liquid stocks from S&P 500
SP200 = ["AAPL","MSFT","AMZN","GOOGL","GOOG","META","BRK-B","JPM","JNJ","V",
"PG","XOM","UNH","MA","HD","CVX","MRK","ABBV","PEP","KO",
"PFE","AVGO","TMO","CRM","COST","DIS","ABT","DHR","NFLX","WMT",
"INTC","BMY","NKE","T","AMD","PYPL","LOW","CVS","MS","C",
"CAT","IBM","HON","UNP","RTX","BA","GE","GS","MMM","AXP",
"AMGN","GILD","FIS","CHTR","SYK","BLK","ISRG","MDT","VZ","ADP",
"TXN","AMAT","ANTM","BKNG","LRCX","TMUS","UPS","ADSK","CMCSA","QCOM",
"MU","SPGI","NEE","TGT","EL","CI","PLD","SO","DUK","AEP",
"LMT","GD","NOC","EW","REGN","VRTX","ILMN","NOW","CL","ECL",
"BDX","APD","ITW","ETN","EMR","PNC","USB","TFC","WFC","BK",
"AIG","MET","PRU","ALL","TRV","CB","SCHW","ICE","CME","MCO",
"ZTS","WM","RSG","EOG","OXY","COP","PSX","VLO","MPC","HES",
"FANG","SLB","HAL","BAX","DOW","DD","LIN","SHW","PPG","ECL",
"WBA","KR","SYY","MDLZ","KMB","GIS","HSY","CLX","K","CPB",
"CAG","SJM","MKC","TSLA","NIO","RIVN","LCID","F","GM","STLA",
"UAL","DAL","AAL","LUV","SAVE","JBHT","CSX","NSC","UPSS","EXPD",
"DRI","MCD","SBUX","DNKN","YUM","CMG","WING","DPZ","PZZA","BLMN",
"BBWI","BBY","HD","LOW","SHLD","ROST","TJX","BURL","DG","DLTR",
"AMZN","WMT","TGT","COST","BJ","WAG","RAD","CVS","WBA","MCK",
"ABC","CAH","HCA","UHS","THC","CYH","LPNT","DVA","FMS","CND"]

def get_sp200_prices(start="2010-01-01"):
    """Download SP200 stock close prices. Cache as parquet for speed."""
    cache_file=CACHE_DIR/"s544_sp200.parquet"
    if cache_file.exists():
        print("[s544] Loading SP200 from cache …",file=sys.stderr)
        return pd.read_parquet(cache_file)
    print("[s544] Downloading 200 stocks (this will take a minute) …",file=sys.stderr)
    data=yf.download(SP200,start=start,auto_adjust=True,progress=False,group_by="ticker",threads=True)
    if isinstance(data.columns,pd.MultiIndex):
        close=data.xs("Close",axis=1,level=1)
    else:
        close=data["Close"]
    close.index=pd.to_datetime(close.index)
    close.to_parquet(cache_file)
    print(f"[s544] Cached {close.shape}",file=sys.stderr)
    return close

def compute_signals(stock_prices):
    """Compute aggregated reversal pressure from all stocks."""
    rets=stock_prices.pct_change()
    
    # 5-day reversal z-score for each stock
    rev_5=rets.rolling(5,min_periods=3).mean()*5  # Cumulative 5d return
    mu=rev_5.rolling(252,min_periods=60).mean()
    sigma=rev_5.rolling(252,min_periods=60).std().clip(lower=1e-6)
    z_scores=((rev_5-mu)/sigma).clip(-3,3)
    
    # Average across stocks
    df=pd.DataFrame(index=stock_prices.index)
    df["avg_z"]=z_scores.mean(axis=1,skipna=True).fillna(0)
    
    # Also compute breadth: % stocks with extreme reversal (>|1.5| sigma)
    extremes=(z_scores.abs()>1.5).sum(axis=1,skipna=True)
    total=z_scores.notna().sum(axis=1)
    df["breadth"]=(extremes/total.fillna(1)).fillna(0)
    
    # Composite = average z * direction + breadth amplification
    # When avg_z is positive, stocks are reversing up (oversold bounce) → bullish
    # When avg_z is negative, stocks are reversing down (overbought selloff) → bearish
    df["composite_raw"]=df["avg_z"]+df["breadth"]*np.sign(df["avg_z"])*0.5
    df["delta"]=df["composite_raw"].diff().fillna(0)*2.0
    df["composite"]=df["composite_raw"]+df["delta"]
    
    print(f"[s544] Avg z-score: mean={df['avg_z'].mean():.3f}, std={df['avg_z'].std():.3f}",file=sys.stderr)
    print(f"[s544] Extreme breadth: mean={df['breadth'].mean():.3f}",file=sys.stderr)
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
            if sc>=0.3: spy_w=1.0    # Stocks reversing up → bullish
            elif sc<=-0.3: spy_w=0.0  # Stocks reversing down → bearish
            else: spy_w=0.5
            w["SPY"]=spy_w
            if "TLT" in tickers: w["TLT"]=1.0-spy_w
            p=w;wl.append(w)
        return pd.DataFrame(wl,index=test_px.index)
    return sig

def main():
    print("="*60,file=sys.stderr);print("s544 — Aggregated Stock Reversal Pressure",file=sys.stderr);print("="*60,file=sys.stderr)
    print("[s544] This will take 2-5 minutes…",file=sys.stderr)
    stock_prices=get_sp200_prices()
    regime_df=compute_signals(stock_prices)
    prices=download_data(["SPY","TLT"],start="2010-01-01",asset_class="etf")
    signal_fn=make_signal(regime_df)
    metrics=run_evaluation(prices=prices,signal_fn=signal_fn,cost_bps=10,asset_class="etf",n_trials=1,beta_ticker="SPY")
    score=metrics.get("SCORE",0);status="keep" if score>0 else "discard"
    print(f"\n{'='*60}",file=sys.stderr);print("s544 — Crowd Wisdom Reversal",file=sys.stderr);print('='*60,file=sys.stderr)
    for k in ["SCORE","sharpe_net","sharpe_gross","deflated_sharpe","sortino","max_dd_pct","ann_turnover","n_trades","win_rate","beta_spy","oos_years"]:
        print(f"{k:20s} {metrics.get(k,'N/A')}",file=sys.stderr)
    print(f"\nLEDGER_ROW\ts544\tcrowd-reversal\tspy-tlt\t{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t0\t{status}\tCROWD: aggregated 5d reversal z-score across 200 stocks for SPY/TLT timing")
if __name__=="__main__": main()
