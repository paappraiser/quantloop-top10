#!/usr/bin/env python3
"""s546 — Cross-Sectional PEAD (EARNPEAD) on S&P 100.

Long top 5 earnings-surprise stocks, short bottom 5, hold 21 trading days.
Equal-weight, event-driven rebalance.
"""
import sys, warnings, time, pickle
from pathlib import Path
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))

from harness import download_data, run_evaluation, print_ledger_row

warnings.filterwarnings("ignore")
CACHE_DIR = HERE / "data"
CACHE_DIR.mkdir(exist_ok=True)

# ── S&P 100 Universe ─────────────────────────────────────────────────
SP100_TICKERS = [
    'AAPL','MSFT','AMZN','GOOGL','GOOG','META','BRK-B','JPM','V','PG',
    'XOM','UNH','MA','HD','CVX','LLY','MRK','ABBV','COST','PEP',
    'KO','ADBE','WMT','CRM','BAC','NFLX','DIS','CSCO','TMO','ACN',
    'ABT','AXP','AVGO','CMCSA','DHR','GE','INTC','INTU','MDT','NEE',
    'AMD','AMGN','BA','CAT','DE','ETN','GILD','GS','HON','IBM',
    'LOW','LMT','MCD','MDLZ','MMM','MO','MS','NKE','ORCL','PFE',
    'PM','QCOM','RTX','SBUX','SO','SPGI','SYK','T','TGT','TXN',
    'UBER','UNP','UPS','USB','VZ','WFC','CI','COP','DUK',
    'ELV','F','GD','GM','ISRG','PLD','PNC','SCHW','SLB',
    'SYY','TMUS','ZTS'
]

# ═══════════════════════════════════════════════════════════════════════
# DATA: Download earnings for all S&P 100 tickers
# ═══════════════════════════════════════════════════════════════════════

def download_earnings(tickers, start='2010-01-01'):
    """Download earnings_dates for all tickers.
    
    Returns: dict[ticker] -> DataFrame with columns:
        EPS Estimate, Reported EPS, Surprise(%), ticker
        Index = earnings date (tz-naive, date only)
    """
    cache_file = CACHE_DIR / 's546_earnings.pkl'
    
    if cache_file.exists():
        print("[s546] Loading earnings from cache …", file=sys.stderr)
        return pd.read_pickle(cache_file)
    
    print("[s546] Downloading earnings data …", file=sys.stderr)
    all_earnings = {}
    
    for i, t in enumerate(tickers):
        if i % 20 == 0:
            print(f"  [{i}/{len(tickers)}]", file=sys.stderr)
        
        try:
            stock = yf.Ticker(t)
            eds = stock.earnings_dates
            if eds is not None and len(eds) > 0:
                eds = eds.copy()
                # Normalize index to tz-naive date
                if eds.index.tz is not None:
                    eds.index = eds.index.tz_convert(None)
                # Keep only dates >= start
                start_dt = pd.Timestamp(start)
                eds = eds[eds.index >= start_dt]
                eds['ticker'] = t
                all_earnings[t] = eds
        except Exception as e:
            pass
        
        time.sleep(0.1)
    
    print(f"[s546] Got earnings for {len(all_earnings)}/{len(tickers)} tickers", file=sys.stderr)
    pd.to_pickle(all_earnings, cache_file)
    print(f"[s546] Earnings cached to {cache_file}", file=sys.stderr)
    return all_earnings


def precompute_earnings_df(earnings_dict):
    """Convert earnings dict to a single DataFrame for fast lookup.
    
    Returns: DataFrame with MultiIndex (date, ticker), columns = [surprise_pct]
    """
    rows = []
    for ticker, eds in earnings_dict.items():
        for idx, row in eds.iterrows():
            surprise = row.get('Surprise(%)', np.nan)
            if pd.isna(surprise):
                continue
            # Normalize: yfinance gives percentage points
            surprise_pct = float(surprise) / 100.0
            # Handle edge case where value is already a fraction
            if abs(surprise_pct) > 2.0:
                surprise_pct = surprise_pct / 100.0
            
            rows.append({
                'date': idx.date() if hasattr(idx, 'date') else pd.Timestamp(idx).date(),
                'ticker': ticker,
                'surprise_pct': surprise_pct,
                'abs_surprise': abs(surprise_pct),
            })
    
    df = pd.DataFrame(rows)
    if len(df) == 0:
        return pd.DataFrame()
    
    df = df.set_index(['date', 'ticker']).sort_index()
    return df


# ═══════════════════════════════════════════════════════════════════════
# SIGNAL FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def make_signal(earnings_df, n_positions=5, hp_days=21):
    """Create the signal function.
    
    Parameters
    ----------
    earnings_df : DataFrame with MultiIndex (date, ticker), column 'surprise_pct'
    n_positions : int — number of positions per side (long and short)
    hp_days : int — holding period in trading days
    """
    
    def signal_fn(train_px, test_px, **kwargs):
        """Generate LS weights for the test period.
        
        For each test date:
        1. Check if any stocks reported earnings on that date
        2. Rank by surprise, long top N, short bottom N
        3. Track active positions with expiry dates
        4. Return weight matrix
        """
        tickers = list(test_px.columns)
        
        weights = pd.DataFrame(0.0, index=test_px.index, columns=tickers)
        
        # Active positions: {(ticker, entry_date): exit_date}
        # Direction: {(ticker, entry_date): 1 or -1}
        active_exit = {}
        active_dir = {}
        
        for i, date in enumerate(test_px.index):
            date_key = date.date() if hasattr(date, 'date') else date
            
            # ── Close expired positions ──
            to_close = [k for k, exit_dt in active_exit.items() if exit_dt <= date]
            for k in to_close:
                del active_exit[k]
                if k in active_dir:
                    del active_dir[k]
            
            # ── Check for new earnings on this date ──
            try:
                day_events = earnings_df.loc[date_key]
            except KeyError:
                day_events = pd.DataFrame()
            
            # Handle single-row result
            if isinstance(day_events, pd.Series):
                day_events = pd.DataFrame({day_events.name: day_events}).T
            
            if isinstance(day_events, pd.DataFrame) and len(day_events) >= 4:
                # Sort by surprise, descending
                day_events = day_events.sort_values('surprise_pct', ascending=False)
                
                # Separate into positive and negative surprise
                pos_surprise = day_events[day_events['surprise_pct'] > 0]
                neg_surprise = day_events[day_events['surprise_pct'] < 0]
                
                # Long: top positive surprise stocks
                # Short: most negative surprise stocks
                long_tickers = pos_surprise.head(n_positions).index.tolist()
                short_tickers = neg_surprise.tail(n_positions).index.tolist()
                
                # Entry at close on earnings date. Exit N trading days later.
                exit_idx = i + hp_days
                if exit_idx < len(test_px.index):
                    exit_date = test_px.index[exit_idx]
                    
                    for t in long_tickers:
                        if t in tickers:
                            key = (t, date)
                            active_exit[key] = exit_date
                            active_dir[key] = 1
                    
                    for t in short_tickers:
                        if t in tickers:
                            key = (t, date)
                            active_exit[key] = exit_date
                            active_dir[key] = -1
            
            # ── Set weights from active positions ──
            n_active = len(active_exit)
            if n_active > 0:
                # Equal weight across all active positions. Accumulate in case
                # the same ticker has multiple overlapping entry dates.
                w = 1.0 / max(n_active, 1)
                
                for (ticker, entry_dt), direction in active_dir.items():
                    if ticker in weights.columns:
                        weights.loc[date, ticker] = weights.loc[date, ticker] + direction * w
        
        return weights
    
    return signal_fn


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60, file=sys.stderr)
    print("s546 — EARNPEAD: Cross-Sectional PEAD on S&P 100", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Download earnings data
    earnings_dict = download_earnings(SP100_TICKERS)
    earnings_df = precompute_earnings_df(earnings_dict)
    print(f"[s546] Earnings events: {len(earnings_df)}", file=sys.stderr)
    
    if len(earnings_df) == 0:
        print("[s546] ERROR: No earnings data collected!", file=sys.stderr)
        return
    
    # Download price data for S&P 100
    prices = download_data(SP100_TICKERS, start='2010-01-01', asset_class='equity')
    print(f"[s546] Prices: {prices.shape}", file=sys.stderr)
    
    # Strategy parameters
    configs = [
        # (n_positions, hp_days, suffix)
        (5, 21, ''),
        (10, 21, '_10pos'),
        (5, 10, '_10d'),
        (10, 10, '_10d_10pos'),
    ]
    
    best_metrics = None
    best_label = ""
    
    for n_pos, hp, suffix in configs:
        label = f"PEAD_n={n_pos}_hp={hp}"
        print(f"\n--- Running {label} ---", file=sys.stderr)
        
        signal_fn = make_signal(earnings_df, n_positions=n_pos, hp_days=hp)
        
        metrics = run_evaluation(
            prices=prices,
            signal_fn=signal_fn,
            cost_bps=10,
            asset_class='equity',
            n_trials=1,
            beta_ticker='SPY',
        )
        
        metrics['n_trades'] = metrics.get('n_trades', 0)
        metrics['ann_turnover'] = metrics.get('ann_turnover', 0)
        
        score = metrics.get('SCORE', 0)
        status = 'keep' if score > 0 else 'discard'
        
        desc = f"EARNPEAD{': Cross-sectional PEAD S&P100, top' + str(n_pos) + '/bottom' + str(n_pos) + ' by surprise, hold ' + str(hp) + 'd, eq-wt'}"
        
        # Print grep-able ledger row
        print(f"\nLEDGER_ROW\ts546{suffix}\tpead-xs\tsp-100\t{score}\t{metrics.get('sharpe_net', 0)}\t{metrics.get('max_dd_pct', 0)}\t{metrics.get('ann_turnover', 0)}\t2\t{status}\t{desc}")
        
        if best_metrics is None or metrics.get('SCORE', 0) > best_metrics.get('SCORE', 0):
            best_metrics = metrics
            best_label = label
    
    # Print summary for the best config
    if best_metrics:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"BEST CONFIG: {best_label}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        for k in ['SCORE', 'sharpe_net', 'sharpe_gross', 'deflated_sharpe', 'sortino',
                   'max_dd_pct', 'ann_turnover', 'n_trades', 'win_rate', 'beta_spy', 'oos_years']:
            print(f"{k:20s} {best_metrics.get(k, 'N/A')}", file=sys.stderr)
    
    print("\nDone.", file=sys.stderr)


if __name__ == '__main__':
    main()
