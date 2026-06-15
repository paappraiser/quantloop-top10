# s538 — Unified Regime Ensemble (UNIFIED)

## 1. Strategy Name
Unified Regime Ensemble — Meta-Ensemble of All Regime Themes

## 2. Strategy Type
Regime-Based Asset Allocation / Ensemble Thematic

## 3. Asset Universe
SPY + TLT + GLD. 3-asset portfolio with regime-driven allocation.
Signal imports from all prior regime detection families.

## 4. Timeframe
Daily signals, discrete 4-tier rebalance every 2+ days.
Backtest: 2010-01-01 to present (11.3 years OOS).

## 5. Core Idea / Edge
**Meta-ensemble: combine ALL independently-validated regime themes into one signal.**

Each prior regime strategy (risk appetite, inflation, yield curve, macro quadrant, vol, dollar) captures a different dimension of market state. These dimensions are partially orthogonal — they agree during consensus periods and disagree during transitions. Weighted ensemble provides the most robust regime classification.

6 contributing signals (each normalized to [-1, +1] continuous):
1. **Risk Appetite** (s532): HYG/LQD credit + VIX median + SPY/TLT corr + gold risk → continuous composite
2. **Macro Growth** (s534 growth axis): SPY momentum + DBC momentum
3. **Macro Inflation** (s534 inflation axis): TIP/SHY ratio + DBC
4. **Yield Curve** (s533): TLT/SHY slope + short rate momentum
5. **Dollar Cycle** (s535): UUP momentum + global growth diff
6. **Vol Ensemble** (s537): VIX term structure + vol regime

Each signal is z-scored over 252d then clipped to [-2, +2].
Ensemble = average of all 6 z-scores.
- Score ≥ 0.5 → Risk-On → 100% SPY
- Score ≥ -0.5 → Neutral → 50% SPY, 50% TLT
- Score ≥ -1.5 → Defensive → 30% SPY, 70% TLT
- Score < -1.5 → Crisis → 40% TLT, 40% GLD, 20% SPY

## 6. Performance Target
- SCORE target: > 0.90 (should beat individual regime strategies through diversification)
- Expected Sharpe: 0.80-0.95
- Max DD: -6% to -10%
- Diversity: should have lower vol and higher win rate than any single regime signal

## 7. Key Finding Expected
The ensemble should outperform the average of its components (diversification benefit) but may underperform the single best component in any given period. The value is in the consistency — fewer extreme losses, higher win rate.
