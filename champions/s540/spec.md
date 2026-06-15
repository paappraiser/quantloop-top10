# s540 — Factor Rotation Regime (FACTOR)

## 1. Strategy Name
Factor Rotation Regime — Macro-Driven Factor ETF Rotation

## 2. Strategy Type
Factor Rotation / Multi-Asset Thematic

## 3. Asset Universe
4 factor ETFs: MTUM (Momentum), QUAL (Quality), USMV (Low Volatility), VLUE (Value).
Rebalance to top 2 factors by macro regime compatibility.
Supporting: SPY, TLT, ^VIX, DBC, SHY.

## 4. Timeframe
Daily signals, rebalance every 2+ days.

## 5. Core Idea / Edge
**Thematic Regime: Macro regime determines which equity factor outperforms.**

Academic literature documents that factor performance depends on macro state:
- **Momentum (MTUM)** outperforms in trending/trending-up markets with low vol
- **Quality (QUAL)** is defensive, outperforms in late-cycle and downturns
- **Low Vol (USMV)** outperforms in high-vol and falling markets
- **Value (VLUE)** outperforms in economic recoveries and rising yield environments

3 macro dimension signals (each binary):
1. **Vol Regime**: VIX > 63d median → High Vol → favor USMV (+1), else MTUM (-1)
2. **Growth Regime**: SPY 63d > 0 → Growing → favor MTUM (+1), else QUAL (-1)
3. **Yield Regime**: TLT/SHY ratio 63d > 0 → Falling yields → favor MTUM (+1), else VLUE (-1)

Composite = 3 binary signals [-3, +3]
- Score ≥ 1 → Risk-On regime → Top 2: MTUM + QUAL
- Score = 0 → Mixed → Top 2: QUAL + USMV (defensive bias)
- Score ≤ -1 → Risk-Off regime → Top 2: USMV + VLUE (defensive + value)

## 6. Performance Target
- SCORE target: 0.40-0.60 (factor strategies have lower Sharpe but provide diversification)
- Should beat equal-weight factor basket
- Share of winning months: > 55%
- Trades: 200+

## 7. Risks
- Factor ETF tracking error
- Regime misclassification during regime transitions
- Low liquidity in factor ETFs vs SPY (higher costs)
- Factor crowding (popularity of factor investing may erode edge)
