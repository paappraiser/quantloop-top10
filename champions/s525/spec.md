# s525 — Market Regime Detection v3 — Continuous Sizing (MRDv3)

## 1. Strategy Name
Market Regime Detection v3 — Continuous Sizing (MRDv3)

## 2. Strategy Type
Regime-Based Asset Allocation / Continuous Second-Derivative Market Timing

## 3. Asset Universe
2 ETFs: SPY (S&P 500) and TLT (20-Year Treasury).
Supporting data indices: ^VIX, ^VIX3M, ^SKEW, HYG, LQD.

## 4. Timeframe
Daily signals, daily rebalance.
Backtest: 2010-01-01 to present.

## 5. Core Idea / Edge
Same 5-signal regime detection composite as s523/s524, but position sizing is continuous:
  spy_weight = (composite + 5) / 10

Instead of 3 discrete regimes, this smoothly scales from 100% TLT (composite=-5) to 100% SPY (composite=+5).

Why this might improve over discrete:
- No cliff edges at regime boundaries — smooth transitions reduce whipsaws
- More responsive to changing conditions — partial allocation adjustments capture gradual regime shifts
- More trades → passes n_trades gate easily

## 6-14. Identical to s523/s524 otherwise.

## Results from sweep
- cont=True, gap=1d: SCORE=0.743, SR=0.743, DD=-4.6%, 250 trades, TO=2.1x
- Lower Sharpe than s524 champion (0.873) but simpler parameterization
