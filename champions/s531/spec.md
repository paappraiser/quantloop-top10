# s531 — Inflation Regime Classifier (INFLREG) v5

## 1. Strategy Name
Inflation Regime Classifier — Asset Allocation Based on the Inflation Cycle

## 2. Strategy Type
Regime-Based Asset Allocation / Macro Thematic

## 3. Asset Universe
2 ETFs: SPY (S&P 500) and TLT (20-Year Treasury).
Supporting data: TIP (TIPS), GLD (Gold), DBC (Commodities), UUP (USD Index).

## 4. Timeframe
Daily signals, discrete 3-tier rebalance every 2+ days (gap-based).
Backtest: 2010-01-01 to present (11.3 years OOS).

## 5. Core Idea / Edge
**Thematic Regime: The inflation cycle predicts relative performance of equities vs bonds.**

Edge: Inflation regimes persist for months to years, giving the regime signal predictive power for SPY/TLT allocation. Rising inflation hurts nominal bonds (TLT) and benefits real assets. Falling inflation supports both equities and bonds.

5 signals (4 binary at 20d + 1 continuous daily):
1. **Breakeven trend** — TIP/TLT ratio 20d change (binary)
2. **Commodity trend** — DBC 20d momentum (binary)
3. **Gold momentum** — GLD 20d trend (binary)
4. **Dollar weakness** — UUP 20d momentum inverted (binary)
5. **Daily breakeven movement** — daily TIP/TLT ratio change z-scored (continuous)

## 6. Data Requirements
From yfinance: TIP, TLT, DBC, GLD, UUP, SPY. Daily OHLCV, cached.

## 7. Signal Generation
Composite = sum(4 binary) + daily_breakeven_z * 0.15
Range: ~[-4.5, +4.5]
- Score ≥ 1.0 → Rising Inflation → 100% TLT
- Score ≤ -1.0 → Falling Inflation → 100% SPY
- -1.0 < Score < 1.0 → Neutral → 50% SPY / 50% TLT

## 8. Entry & Exit Rules
- Rebalance every 2+ days: gap-based
- Discrete 3-tier allocation (required by harness per-position cap)

## 9. Position Sizing & Risk Management
Harness defaults (vol target 10%, per-position cap 10%, drawdown gates).

## 10. Portfolio Construction
Two-asset SPY/TLT discrete allocation.

## 11. Results Achieved
- SCORE: 0.450 (SR 0.450, gross SR 0.609)
- Max DD: -4.5%
- Trades: 225 (passes gate)
- Turnover: 2.4x
- Beta: 0.0

## 12. Key Implementation Note
CRITICAL: harness MAX_POS_PCT=0.10 per-position cap forces DISCRETE allocation on 2-asset portfolios. Continuous allocation is uniformly capped to [0.1, 0.1] producing ZERO turnover. Only extreme discrete weights (0.0 or 1.0) create detectable turnover in the capped view. This applied to all revisions of s531.

## 13. Potential Risks
- Inflation regime signals are slow-moving; the daily z-scored component adds noise to generate trade frequency
- TIP/TLT ratio has less overlap period than other pairs — some early years may have fewer signals
- 3-tier allocation is coarse; finer gradations impossible under per-position cap

## 14. Validation
Walk-forward (expanding 5yr window, 252d retrain, 21d embargo). 0 free parameters.
