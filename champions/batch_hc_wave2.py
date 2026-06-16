#!/usr/bin/env python3
"""Wave 2 refinement: Holding-Company TS Momentum — refinement variants.

Builds on s545 champion (SR 0.9086). Tests:
  s561: Multi-lookback ensemble (42+63+126 all positive)
  s562: Momentum-weighted (weight by ret strength, not equal)
  s563: Biweekly rebalance (gap=2)
  s564: Sub-universe — pure holding cos only (BRK, MKL, FFH, BN, L)
  s565: Sub-universe — alt asset managers only
  s566: Sub-universe — all asset managers (alt + trad)
  s567: Regime-filtered — only trade when 200d MA is rising
  s568: MACD-style EMA crossover signal
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
QL = HERE.parent
sys.path.insert(0, str(QL))

from harness import download_data, run_evaluation, print_ledger_row

# ── Universe tiers ────────────────────────────────────────────────────────
ALL_TICKERS = sorted([
    "BRK-B", "MKL", "FFH", "BN", "L",
    "BAM", "KKR", "APO", "BX", "ARES", "CG", "TPG",
    "BLK", "TROW", "STT", "IVZ", "BEN",
    "JEF", "HLI", "RJF",
    "SFTBY", "PROSY", "NPSNY",
])

PURE_HOLDING = ["BRK-B", "MKL", "FFH", "BN", "L"]
ALT_ASSET = ["BAM", "KKR", "APO", "BX", "ARES", "CG", "TPG"]
ALL_ASSET = ALT_ASSET + ["BLK", "TROW", "STT", "IVZ", "BEN"]

print("=" * 72)
print("HC-MOM WAVE 2: Refinements on s545 champion (SR 0.9086)")
print("=" * 72)

# ── Data ──────────────────────────────────────────────────────────────────
prices = download_data(ALL_TICKERS, start="2005-01-01")
valid = [c for c in prices.columns if prices[c].notna().sum() > 500]
prices = prices[valid]
print(f"Valid tickers: {len(valid)}")

# ══════════════════════════════════════════════════════════════════════════
# Signal factories
# ══════════════════════════════════════════════════════════════════════════

def make_ensemble_lookback(lookbacks=(42, 63, 126), gap=4):
    """Multi-lookback ensemble: trade when ALL lookbacks agree positive."""
    def signal_fn(train_px, test_px, **kwargs):
        all_px = pd.concat([train_px, test_px])
        weights_list = []
        prev_w = None
        for i, date in enumerate(test_px.index):
            if i > 0 and (date - test_px.index[i-1]).days < gap:
                weights_list.append(prev_w.copy())
                continue
            hist = all_px.loc[:date]
            max_lb = max(lookbacks)
            if len(hist) < max_lb + 10:
                w = pd.Series(0.0, index=test_px.columns)
                weights_list.append(w)
                prev_w = w
                continue
            # Check ALL lookbacks agree positive
            agreement = pd.Series(True, index=test_px.columns)
            for lb in lookbacks:
                ret = hist.pct_change(lb).iloc[-1]
                agreement = agreement & (ret > 0)
            active = agreement.dropna()
            active = active[active]
            if len(active) > 0:
                w = pd.Series(0.0, index=test_px.columns)
                w[active.index] = 1.0 / len(active)
            else:
                w = pd.Series(0.0, index=test_px.columns)
            weights_list.append(w)
            prev_w = w
        return pd.DataFrame(weights_list, index=test_px.index)
    return signal_fn


def make_momentum_weighted(lookback=42, gap=4):
    """Weight positions by momentum strength instead of equal-weight."""
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
            if len(positive) > 0:
                # Weight proportional to momentum strength
                weights = positive / positive.sum()
                w = pd.Series(0.0, index=test_px.columns)
                w[weights.index] = weights.values
            else:
                w = pd.Series(0.0, index=test_px.columns)
            weights_list.append(w)
            prev_w = w
        return pd.DataFrame(weights_list, index=test_px.index)
    return signal_fn


def make_macd_signal(fast=12, slow=26, signal=9, gap=4):
    """MACD-style: EMA crossover on each ticker, long when MACD > signal."""
    def signal_fn(train_px, test_px, **kwargs):
        all_px = pd.concat([train_px, test_px])
        weights_list = []
        prev_w = None
        for i, date in enumerate(test_px.index):
            if i > 0 and (date - test_px.index[i-1]).days < gap:
                weights_list.append(prev_w.copy())
                continue
            hist = all_px.loc[:date]
            if len(hist) < slow + signal + 10:
                w = pd.Series(0.0, index=test_px.columns)
                weights_list.append(w)
                prev_w = w
                continue
            ema_fast = hist.ewm(span=fast, min_periods=fast).mean()
            ema_slow = hist.ewm(span=slow, min_periods=slow).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=signal, min_periods=signal).mean()
            # Positive signal: MACD above signal line
            signal_pos = macd.iloc[-1] > macd_signal.iloc[-1]
            active = signal_pos[signal_pos].dropna()
            if len(active) > 0:
                w = pd.Series(0.0, index=test_px.columns)
                w[active.index] = 1.0 / len(active)
            else:
                w = pd.Series(0.0, index=test_px.columns)
            weights_list.append(w)
            prev_w = w
        return pd.DataFrame(weights_list, index=test_px.index)
    return signal_fn


def make_regime_filtered(lookback=42, gap=4):
    """Regime-filtered: only trade when 200d MA of SPY is rising (bull market).
    
    This adds a macro trend filter to avoid holding through secular bears.
    """
    def signal_fn(train_px, test_px, **kwargs):
        # Download SPY for regime filter
        try:
            spy_all = download_data(["SPY"], start="2005-01-01")
            spy_col = spy_all.columns[0]
        except:
            spy_all = None
        
        all_px = pd.concat([train_px, test_px])
        weights_list = []
        prev_w = None
        for i, date in enumerate(test_px.index):
            if i > 0 and (date - test_px.index[i-1]).days < gap:
                weights_list.append(prev_w.copy())
                continue
            
            # Check regime: is SPY 200d MA rising?
            if spy_all is not None:
                spy_hist = spy_all.loc[:date]
                if len(spy_hist) >= 250:
                    sma200 = spy_hist[spy_col].rolling(200).mean()
                    if len(sma200.dropna()) >= 2:
                        rising = sma200.iloc[-1] > sma200.iloc[-2]
                    else:
                        rising = True
                else:
                    rising = True
            else:
                rising = True
            
            if not rising:
                # Bear regime — stay flat
                weights_list.append(prev_w.copy() if prev_w is not None else pd.Series(0.0, index=test_px.columns))
                prev_w = weights_list[-1]
                continue
            
            # Normal signal
            hist = all_px.loc[:date]
            if len(hist) < lookback + 10:
                w = pd.Series(0.0, index=test_px.columns)
                weights_list.append(w)
                prev_w = w
                continue
            
            ret = hist.pct_change(lookback).iloc[-1].dropna()
            positive = ret[ret > 0]
            if len(positive) > 0:
                w = pd.Series(0.0, index=test_px.columns)
                w[positive.index] = 1.0 / len(positive)
            else:
                w = pd.Series(0.0, index=test_px.columns)
            weights_list.append(w)
            prev_w = w
        return pd.DataFrame(weights_list, index=test_px.index)
    return signal_fn


# ══════════════════════════════════════════════════════════════════════════
# Config grid
# ══════════════════════════════════════════════════════════════════════════

configs = [
    # s561: Multi-lookback ensemble
    {
        "id": 561, "family": "hc-mom-ensemble", "variant": "42+63+126",
        "desc": "HC-ENSEMBLE: 42+63+126 lookback agreement, long-only, weekly",
        "fn": make_ensemble_lookback((42, 63, 126), gap=4),
    },
    # s562: Momentum-weighted
    {
        "id": 562, "family": "hc-mom-weight", "variant": "weighted",
        "desc": "HC-WEIGHT: mom lb=42, momentum-weighted, weekly",
        "fn": make_momentum_weighted(lookback=42, gap=4),
    },
    # s563: Biweekly rebalance
    {
        "id": 563, "family": "hc-mom-biweekly", "variant": "gap2",
        "desc": "HC-BIW: mom lb=42, long-only, biweekly rebalance (gap=2)",
        "fn": make_momentum_weighted(lookback=42, gap=2),  # equal-weight but gap=2
    },
    # Actually s563 should use equal-weight not momentum-weighted
    {"id": 563, "family": "hc-mom-biweekly", "variant": "gap2",
     "desc": "HC-BIW: mom lb=42, long-only, equal-wt, biweekly rebalance (gap=2)",
     "fn_maker": lambda: make_ensemble_lookback((42,), gap=2)},
    
    # s564: Sub-universe — pure holding cos only
    {
        "id": 564, "family": "hc-mom-sub", "variant": "pure-hold",
        "desc": "HC-SUB-PURE: mom lb=42, BRK+MKL+FFH+BN+L only",
        "universe": PURE_HOLDING,
    },
    # s565: Sub-universe — alt asset managers only
    {
        "id": 565, "family": "hc-mom-sub", "variant": "alt-asset",
        "desc": "HC-SUB-ALT: mom lb=42, alt asset mgrs only",
        "universe": ALT_ASSET,
    },
    # s566: Sub-universe — all asset managers
    {
        "id": 566, "family": "hc-mom-sub", "variant": "all-asset",
        "desc": "HC-SUB-AM: mom lb=42, all asset mgrs (alt+trad)",
        "universe": ALL_ASSET,
    },
    # s567: Regime-filtered by 200d MA
    {
        "id": 567, "family": "hc-mom-regime", "variant": "ma200",
        "desc": "HC-REGIME: mom lb=42, SPY 200d MA filter, long-only",
        "fn": None,  # special
    },
    # s568: MACD-style signal
    {
        "id": 568, "family": "hc-mom-macd", "variant": "macd",
        "desc": "HC-MACD: EMA crossover (12/26/9), long-only",
        "fn": None,
    },
    # s569: Highest lookback (252d) on pure holding cos — best diversification
    {
        "id": 569, "family": "hc-mom-sub", "variant": "pure-252",
        "desc": "HC-SUB-PURE-252: mom lb=252, BRK+MKL+FFH+BN+L only",
        "universe": PURE_HOLDING,
        "lb": 252,
    },
    # s570: Higher rebalance frequency on champion
    {
        "id": 570, "family": "hc-mom-freq", "variant": "gap3",
        "desc": "HC-FREQ: mom lb=42, long-only, equal-wt, gap=3d rebalance",
    },
]

# ── Run batch ─────────────────────────────────────────────────────────────
n_trials_total = len(configs)
batch_results = []

# Fix the configs for those that need special handling
# s563 override
configs[3] = {"id": 563, "family": "hc-mom-biweekly", "variant": "gap2",
              "desc": "HC-BIW: mom lb=42, long-only, equal-wt, biweekly rebalance (gap=2)"}

for cfg in configs:
    print(f"\n{'─' * 60}")
    print(f"s{cfg['id']:03d}: {cfg['desc']}")
    print(f"{'─' * 60}")
    
    # Determine universe
    uni = cfg.get("universe", valid)
    if isinstance(uni, list):
        uni = [t for t in uni if t in prices.columns]
    
    # Determine signal function
    if cfg.get("fn_maker"):
        fn = cfg["fn_maker"]()
    elif cfg["id"] == 561:  # ensemble
        fn = make_ensemble_lookback((42, 63, 126), gap=4)
    elif cfg["id"] == 562:  # momentum-weighted
        fn = make_momentum_weighted(lookback=42, gap=4)
    elif cfg["id"] == 563:  # biweekly rebalance
        fn = make_ensemble_lookback((42,), gap=2)
    elif cfg["id"] == 567:  # regime-filtered
        fn = make_regime_filtered(lookback=42, gap=4)
    elif cfg["id"] == 568:  # MACD
        fn = make_macd_signal(fast=12, slow=26, signal=9, gap=4)
    elif cfg["id"] == 570:  # gap=3
        fn = make_ensemble_lookback((42,), gap=3)
    elif cfg.get("id") in (564, 565, 566, 569):
        # Sub-universe variants: TS momentum on subset
        lb = cfg.get("lb", 42)
        fn = make_ensemble_lookback((lb,), gap=4)
    else:
        fn = make_ensemble_lookback((42,), gap=4)
    
    try:
        m = run_evaluation(
            prices[uni] if isinstance(uni, list) and len(uni) > 0 else prices,
            fn, cost_bps=10,
            n_trials=580 + n_trials_total,
        )
        
        score = m.get("SCORE", 0)
        sr = m.get("sharpe_net", 0)
        dd = m.get("max_dd_pct", 0)
        to = m.get("ann_turnover", 0)
        trades = m.get("n_trades", 0)
        
        status = "keep" if score > 0 else "discard"
        print(f"  → SCORE={score:.4f} SR={sr:.4f} DD={dd:.1f}% TO={to:.1f} trades={trades} → {status}")
        
        batch_results.append({**cfg, "score": score, "sr": sr, "dd": dd, "to": to, "trades": trades, "status": status, "m": m, "universe_name": cfg.get("universe", "all")})
        
    except Exception as e:
        print(f"  → ERROR: {e}")
        batch_results.append({**cfg, "score": 0, "sr": 0, "dd": 0, "to": 0, "trades": 0, "status": "crash", "m": {}})

# ── Summary ───────────────────────────────────────────────────────────────
print("\n" + "=" * 72)
print("HC-MOM WAVE 2 SUMMARY")
print("=" * 72)
print(f"{'ID':>5s} {'Score':>7s} {'SR':>7s} {'DD':>7s} {'TO':>5s} {'Tr':>5s} {'Status':>8s}  Description")
print("-" * 72)
for r in batch_results:
    print(f"{r['id']:5d} {r['score']:7.4f} {r['sr']:7.4f} {r['dd']:6.1f}% {r['to']:4.1f}× {r['trades']:4d} {r['status']:>8s}  {r['desc']}")

# Champion comparison
print(f"\n{'─' * 72}")
print("COMPARISON WITH PRIOR CHAMPIONS:")
print(f"  s545 (HC-MOM)     — SR 0.9086 (holding co TS mom, lb=42)")
print(f"  s542 (DISPERSION) — SR 1.1819 (QQQ/SPY ratio mrev)  ← GLOBAL CHAMPION")
print(f"  s524 (REGIME)     — SR 0.873  (regime detection)")
print(f"  s532 (RISK-APP)   — SR 0.961  (risk appetite)")

# Ledger rows
print("\n--- LEDGER ROWS ---")
for r in batch_results:
    if r['status'] in ('keep', 'discard'):
        print_ledger_row(
            f"s{r['id']:03d}",
            r['family'],
            f"holding-co-{r.get('universe_name', 'all')}",
            r['m'],
            1,
            r['status'],
            r['desc'][:100],
        )

print("\nDone.")
