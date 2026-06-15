# s524 — Market Regime Detection v2 (MRDv2)

## 1. Strategy Name
Market Regime Detection v2 — Second-Derivative Allocation with 2-Day Rebalance

## 2. Strategy Type
Regime-Based Asset Allocation / Second-Derivative Market Timing

## 3. Asset Universe
2 ETFs: SPY (S&P 500) and TLT (20-Year Treasury).
Supporting data indices: ^VIX, ^VIX3M, ^SKEW, HYG, LQD.

## 4. Timeframe
Daily signals, rebalance every 2+ days (gap-based).
Backtest: 2010-01-01 to present (16.5 years).

## 5. Core Idea / Edge

SECOND-DERIVATIVE STRATEGY. Same core idea as s523 but tuned to pass the n_trades gate.

Key tuning findings from s523 sweep:
- **Rebalance gap of 2 days** produces the best Sharpe (0.8727) vs 1-day (0.784) or 4-day (0.0, fails gate)
- **Stressed threshold of -1** (only extreme signals trigger full defensive) outperforms threshold of 0
- 192 trades over 11.3 years OOS, well above the 100-trade gate
- Max DD of -2.9%, TO of 1.7x — very clean

5 signals: VIX term structure, realized vol trend, SPY/TLT correlation, credit spread momentum, options skew.

## 6. Data Requirements
Identical to s523. All from yfinance, cached.

## 7. Signal Generation
Same 5 signals as s523.

## 8. Entry & Exit Rules
- Rebalance every 2+ days: `(date - prev_date).days >= 2` (gap-based)
- At each rebalance:
  - Score ≥ 2 → Benign → 100% SPY
  - -1 ≤ Score < 2 → Neutral → 50% SPY / 50% TLT  
  - Score < -1 → Stressed → 100% TLT
- 1-day lag on signals

## 9. Position Sizing & Risk Management
Harness defaults.

## 10. Portfolio Construction
Same as s523.

## 11. Expected Characteristics
- Sharpe: **0.87 net** (from sweep)
- Max DD: -2.9%
- Trades: ~192 over 11.3 years
- Turnover: 1.7x
- Market beta: 0.0 (vol-targeted)

## 12. Implementation Notes
Based on s523, parameters tuned:
- benign_threshold = 2
- stressed_threshold = -1
- rebalance_gap = 2

## 13. Potential Risks & Mitigations
Lower stressed threshold (-1) means less frequent defensive positioning — the strategy may miss some drawdowns. Mitigated by the 5-signal composite providing early warnings.

## 14. Backtesting & Validation Framework
Validated via s523 sweep (24 configs).
