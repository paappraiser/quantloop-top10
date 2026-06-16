#!/usr/bin/env python3
"""s545-s550 batch: Holding-Company Time-Series Momentum variants.

Deep-dive batch exploring the HC-MOM discovery (SR 0.84 on TS momentum).
Tests: lookback, trend strength filter, long-only vs L/S, and a regime overlay.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent  # strategies/
QL = HERE.parent  # quantloop root
sys.path.insert(0, str(QL))

from harness import download_data, run_evaluation, print_ledger_row

# ── Universe ──────────────────────────────────────────────────────────────
HOLDING_TICKERS = sorted([
    # Pure holding cos
    "BRK-B", "MKL", "FFH", "BN", "L",
    # Alt asset mgrs
    "BAM", "KKR", "APO", "BX", "ARES", "CG", "TPG",
    # Trad asset mgrs
    "BLK", "TROW", "STT", "IVZ", "BEN",
    # Conglomerates
    "JEF", "HLI", "RJF",
    # Intl holding ADRs
    "SFTBY", "PROSY", "NPSNY",
])

print("=" * 72)
print("HC-MOM BATCH: Holding-Company Time-Series Momentum")
print(f"Universe: {len(HOLDING_TICKERS)} tickers")
print("=" * 72)

# ── Data ──────────────────────────────────────────────────────────────────
prices = download_data(HOLDING_TICKERS, start="2005-01-01")
valid = [c for c in prices.columns if prices[c].notna().sum() > 500]
print(f"Valid tickers: {len(valid)}")
prices = prices[valid]

# ── Signal factory: TS momentum ──────────────────────────────────────────
def make_ts_momentum(lookback=252, min_ret=0.0, long_only=True):
    """Time-series momentum on holding-company universe.
    
    Parameters
    ----------
    lookback : int
        Lookback period in trading days for momentum calculation.
    min_ret : float
        Minimum absolute return threshold to avoid whipsaws (0 = no filter).
    long_only : bool
        If True, only take long positions (no shorts).
    """
    def signal_fn(train_px, test_px, **kwargs):
        all_px = pd.concat([train_px, test_px])
        weights_list = []
        prev_w = None
        
        for i, date in enumerate(test_px.index):
            # Gap-based weekly rebalance
            if i > 0 and (date - test_px.index[i-1]).days < 4:
                weights_list.append(prev_w.copy())
                continue
            
            hist = all_px.loc[:date]
            if len(hist) < lookback + 10:
                w = pd.Series(0.0, index=test_px.columns)
                weights_list.append(w)
                prev_w = w
                continue
            
            # Rolling return over lookback
            ret = hist.pct_change(lookback).iloc[-1]
            ret = ret.dropna()
            
            if long_only:
                # Long only: weight = 1/n for positive, 0 otherwise
                active = ret[ret > min_ret]
                if len(active) > 0:
                    w = pd.Series(0.0, index=test_px.columns)
                    w[active.index] = 1.0 / len(active)
                else:
                    w = pd.Series(0.0, index=test_px.columns)
            else:
                # Long/short: long the top half, short the bottom half
                sorted_ret = ret.sort_values()
                n = len(sorted_ret)
                n_long = max(1, n // 3)
                n_short = max(1, n // 3)
                
                # Filter by min_ret threshold
                longs = sorted_ret.tail(n_long)
                longs = longs[longs > min_ret]
                shorts = sorted_ret.head(n_short)
                shorts = shorts[shorts < -min_ret]
                
                w = pd.Series(0.0, index=test_px.columns)
                if len(longs) > 0:
                    w[longs.index] += 1.0 / (len(longs) + len(shorts)) if (len(longs)+len(shorts)) > 0 else 0
                if len(shorts) > 0:
                    w[shorts.index] -= 1.0 / (len(longs) + len(shorts))
            
            weights_list.append(w)
            prev_w = w
        
        return pd.DataFrame(weights_list, index=test_px.index)
    return signal_fn


# ── Config grid ───────────────────────────────────────────────────────────
configs = []
config_id = 545

# s545: pure TS momentum long-only, lookback sweep
for lb in [42, 63, 126, 189, 252]:
    configs.append({
        "id": config_id, "family": "hc-mom", "variant": "long-only",
        "description": f"HCTREND: TS momentum lb={lb}, long-only, equal-weight, weekly",
        "lookback": lb, "min_ret": 0.0, "long_only": True,
    })
    config_id += 1

# s550-plus: long-only with trend strength filter
for lb in [63, 126, 252]:
    for thresh in [0.03, 0.05, 0.10]:
        configs.append({
            "id": config_id, "family": "hc-mom-filter",
            "variant": "filtered",
            "description": f"HCTREND-F: TS mom lb={lb}, min_ret={thresh:.0%}, long-only, weekly",
            "lookback": lb, "min_ret": thresh, "long_only": True,
        })
        config_id += 1

# Plus a few long/short variants
for lb in [126, 252]:
    configs.append({
        "id": config_id, "family": "hc-mom-ls",
        "variant": "long-short",
        "description": f"HCTREND-LS: TS mom lb={lb}, L/S top/bottom third, weekly",
        "lookback": lb, "min_ret": 0.0, "long_only": False,
    })
    config_id += 1

# ── Run batch ─────────────────────────────────────────────────────────────
results = []
n_trials_total = len(configs)

for cfg in configs:
    print(f"\n{'─' * 60}")
    print(f"s{cfg['id']:03d}: {cfg['description']}")
    print(f"{'─' * 60}")
    
    fn = make_ts_momentum(
        lookback=cfg["lookback"],
        min_ret=cfg["min_ret"],
        long_only=cfg["long_only"],
    )
    
    try:
        # Number of trials for deflated Sharpe = strategies already in ledger + this batch
        # Use a conservative estimate
        n_trials = 560 + n_trials_total
        
        m = run_evaluation(
            prices, fn, cost_bps=10, n_trials=n_trials,
            lookback=cfg["lookback"],
        )
        
        score = m.get("SCORE", 0)
        sr = m.get("sharpe_net", 0)
        dd = m.get("max_dd_pct", 0)
        to = m.get("ann_turnover", 0)
        trades = m.get("n_trades", 0)
        
        # Determine status
        if score > 0 and dd > -35 and trades >= 100 and to <= 50:
            # Gate check within compute_metrics already zeros SCORE
            if score > 0:
                status = "keep"
            else:
                status = "discard"
        else:
            status = "discard"
        
        print(f"  → SCORE={score:.4f} SR={sr:.4f} DD={dd:.1f}% TO={to:.1f} trades={trades} → {status}")
        
        results.append({
            "id": cfg["id"],
            "family": cfg["family"],
            "variant": cfg["variant"],
            "desc": cfg["description"],
            "score": score,
            "sr": sr,
            "dd": dd,
            "to": to,
            "trades": trades,
            "status": status,
            "m": m,
        })
        
    except Exception as e:
        print(f"  → ERROR: {e}")
        results.append({
            "id": cfg["id"],
            "family": cfg["family"],
            "variant": cfg["variant"],
            "desc": cfg["description"],
            "score": 0,
            "sr": 0,
            "dd": 0,
            "to": 0,
            "trades": 0,
            "status": "crash",
            "m": {},
        })

# ── Summary table ─────────────────────────────────────────────────────────
print("\n" + "=" * 72)
print("BATCH SUMMARY — Holding Company Time-Series Momentum")
print("=" * 72)
print(f"{'ID':>5s} {'Score':>7s} {'SR':>7s} {'DD':>7s} {'TO':>6s} {'Trades':>7s} {'Status':>8s}  Variant")
print("-" * 72)
for r in results:
    print(f"{r['id']:5d} {r['score']:7.4f} {r['sr']:7.4f} {r['dd']:6.1f}% {r['to']:5.1f}× {r['trades']:6d} {r['status']:>8s}  {r['desc']}")

# ── Gate summary ──────────────────────────────────────────────────────────
keepers = [r for r in results if r['status'] == 'keep']
discards = [r for r in results if r['status'] == 'discard']
crashes = [r for r in results if r['status'] == 'crash']

print(f"\nKeep: {len(keepers)} | Discard: {len(discards)} | Crash: {len(crashes)}")

if keepers:
    best = max(keepers, key=lambda r: r['score'])
    print(f"\nBest keeper: s{best['id']:03d} — SCORE={best['score']:.4f} SR={best['sr']:.4f} DD={best['dd']:.1f}%")
    print(f"  {best['desc']}")

# Print ledger rows for keepers and notable discards
print("\n--- LEDGER ROWS ---")
for r in results:
    if r['status'] in ('keep', 'discard'):
        # Only log keepers to ledger; discards that passed all gates but scored low
        ledger_status = r['status'] if r['status'] == 'keep' else 'discard'
        print_ledger_row(
            f"s{r['id']:03d}",
            r['family'],
            "holding-co",
            r['m'],
            1,  # n_params: lookback
            ledger_status,
            r['desc'][:100],
        )

print("\nDone.")
