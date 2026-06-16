#!/usr/bin/env python3
"""Wave 3: Alt-Asset Manager TS Momentum — deep-dive lookback sweep.

s565 (SR 1.1284) discovered that TS momentum on alt asset managers 
(BAM, KKR, APO, BX, ARES, CG, TPG) with lb=42 is exceptional.

This wave:
1. Sweeps lookbacks on alt-asset universe (21 to 378)
2. Tests equal-weight vs momentum-weighted on alt universe
3. Tests rebalance gaps on alt universe
4. Tests volatility filter (cap positions by trailing vol)
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
QL = HERE.parent
sys.path.insert(0, str(QL))

from harness import download_data, run_evaluation, print_ledger_row

# ── Alt asset manager universe ───────────────────────────────────────────
ALT_ASSET = ["BAM", "KKR", "APO", "BX", "ARES", "CG", "TPG"]

print("=" * 72)
print("HC-MOM WAVE 3: Alt-Asset TS Momentum Deep Dive")
print(f"Universe: {ALT_ASSET}")
print("=" * 72)

prices = download_data(ALT_ASSET, start="2005-01-01")
alt_valid = [t for t in ALT_ASSET if t in prices.columns and prices[t].notna().sum() > 500]
print(f"Valid alt tickers: {alt_valid}")
prices = prices[alt_valid]

# ── Signal factories ──────────────────────────────────────────────────────

def make_tsm(lookback=42, gap=4, weighting="equal"):
    """Time-series momentum signal.
    
    Parameters
    ----------
    lookback : int
        Lookback in trading days.
    gap : int
        Min calendar days between rebalances.
    weighting : str
        'equal' or 'strength' (momentum-weighted).
    """
    def signal_fn(train_px, test_px, **kwargs):
        all_px = pd.concat([train_px, test_px])
        weights_list = []
        prev_w = None
        for i, date in enumerate(test_px.index):
            if i > 0 and (date - test_px.index[i-1]).days < gap:
                weights_list.append(prev_w.copy())
                continue
            hist = all_px.loc[:date]
            if len(hist) < lookback + 10:
                w = pd.Series(0.0, index=test_px.columns)
                weights_list.append(w)
                prev_w = w
                continue
            ret = hist.pct_change(lookback).iloc[-1].dropna()
            positive = ret[ret > 0]
            if len(positive) == 0:
                w = pd.Series(0.0, index=test_px.columns)
            elif weighting == "strength":
                weights = positive / positive.sum()
                w = pd.Series(0.0, index=test_px.columns)
                w[weights.index] = weights.values
            else:  # equal
                w = pd.Series(0.0, index=test_px.columns)
                w[positive.index] = 1.0 / len(positive)
            weights_list.append(w)
            prev_w = w
        return pd.DataFrame(weights_list, index=test_px.index)
    return signal_fn


# ── Config grid ──────────────────────────────────────────────────────────

configs = []

# Lookback sweep on alt universe, equal-weight, gap=4
config_id = 571
for lb in [21, 42, 63, 84, 126, 168, 189, 252, 378]:
    configs.append({
        "id": config_id,
        "family": "alt-mom",
        "desc": f"ALT-MOM: lookback={lb}, eq-wt, gap=4 (weekly), alt-asset",
        "lookback": lb,
        "gap": 4,
        "weighting": "equal",
    })
    config_id += 1

# Gap sweep on alt universe, lookback=42, equal-weight
for gap in [5, 7, 10]:
    configs.append({
        "id": config_id,
        "family": "alt-mom-gap",
        "desc": f"ALT-GAP: lookback=42, eq-wt, gap={gap}d, alt-asset",
        "lookback": 42,
        "gap": gap,
        "weighting": "equal",
    })
    config_id += 1

# Weighting sweep on alt universe, lookback=42, gap=4
for wt in ["strength", "equal"]:
    configs.append({
        "id": config_id,
        "family": "alt-mom-weight",
        "desc": f"ALT-WT: lookback=42, weighting={wt}, gap=4, alt-asset",
        "lookback": 42,
        "gap": 4,
        "weighting": wt,
    })
    config_id += 1

# Total unique tests
n_tests = len(configs)
print(f"\nTesting {n_tests} configurations...\n")

# ── Run ──────────────────────────────────────────────────────────────────
results = []

for cfg in configs:
    print(f"s{cfg['id']:03d}: {cfg['desc']}")
    
    fn = make_tsm(
        lookback=cfg["lookback"],
        gap=cfg["gap"],
        weighting=cfg["weighting"],
    )
    
    try:
        m = run_evaluation(
            prices, fn, cost_bps=10,
            n_trials=600 + n_tests,
        )
        
        score = m.get("SCORE", 0)
        sr = m.get("sharpe_net", 0)
        dd = m.get("max_dd_pct", 0)
        to = m.get("ann_turnover", 0)
        trades = m.get("n_trades", 0)
        
        status = "keep" if score > 0 else "discard"
        print(f"  → SCORE={score:.4f} SR={sr:.4f} DD={dd:.1f}% TO={to:.1f} trades={trades} → {status}\n")
        
        results.append({**cfg, "score": score, "sr": sr, "dd": dd, "to": to, "trades": trades, "status": status, "m": m})
        
    except Exception as e:
        print(f"  → ERROR: {e}\n")
        results.append({**cfg, "score": 0, "sr": 0, "dd": 0, "to": 0, "trades": 0, "status": "crash", "m": {}})

# ── Summary ──────────────────────────────────────────────────────────────
print("=" * 72)
print("WAVE 3 SUMMARY — Alt-Asset TS Momentum Lookback Sweep")
print("=" * 72)
print(f"{'ID':>5s} {'Score':>7s} {'SR':>7s} {'DD':>7s} {'TO':>5s} {'Tr':>5s} {'Status':>8s}  Description")
print("-" * 72)

keepers = []
for r in sorted(results, key=lambda x: x['score'], reverse=True):
    print(f"{r['id']:5d} {r['score']:7.4f} {r['sr']:7.4f} {r['dd']:6.1f}% {r['to']:4.1f}× {r['trades']:4d} {r['status']:>8s}  {r['desc']}")
    if r['status'] == 'keep':
        keepers.append(r)

print(f"\nKeepers: {len(keepers)}")
if keepers:
    best = max(keepers, key=lambda x: x['score'])
    print(f"\nBEST: s{best['id']:03d} — SCORE={best['score']:.4f} SR={best['sr']:.4f} DD={best['dd']:.1f}%")
    print(f"      {best['desc']}")
    
    # Top 5
    print(f"\nTOP 5:")
    for i, r in enumerate(sorted(keepers, key=lambda x: x['score'], reverse=True)[:5]):
        print(f"  {i+1}. s{r['id']:03d}: {r['desc']} → SR {r['sr']:.4f} DD {r['dd']:.1f}% TO {r['to']:.1f}×")

print(f"\n{'─' * 72}")
print("COMPARISON:")
print(f"  s542 (QQQ/SPY dispersion) — SR 1.1819 ← GLOBAL CHAMPION")
print(f"  s565 (alt-asset, lb=42)   — SR 1.1284 ← best so far")

# Ledger rows
print("\n--- LEDGER ROWS ---")
for r in results:
    if r['status'] in ('keep', 'discard'):
        print_ledger_row(
            f"s{r['id']:03d}", r['family'], "alt-asset-mgr",
            r['m'], 1, r['status'], r['desc'][:100],
        )

print("\nDone.")
