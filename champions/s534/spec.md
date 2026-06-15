# s534 — Macro Quadrant Regime Classifier (MACRO4)

## 1. Strategy Name
Macro Quadrant Regime Classifier — 2×2 Growth × Inflation Allocation Matrix

## 2. Strategy Type
Regime-Based Asset Allocation / Macro Thematic

## 3. Asset Universe
3 ETFs: SPY (S&P 500), TLT (20-Year Treasury), GLD (Gold).
Supporting: DBC (Commodities), TIP (TIPS), SHY (Short Treasury).

## 4. Timeframe
Daily signals, discrete 4-quadrant rebalance every 2+ days. 11.3 years OOS.

## 5. Core Idea / Edge
**Thematic Regime: Four macro quadrants defined by Growth × Inflation intersection. Each has a historically optimal asset allocation.**

| | Stable Inflation | Rising Inflation |
|---|---|---|
| **High Growth** | Goldilocks → 100% SPY | Overheat → 50% SPY + 50% GLD |
| **Low Growth** | Recession → 70% TLT + 30% SPY | Stagflation → 50% GLD + 30% TLT + 20% SPY |

Growth: SPY 63d momentum + DBC 63d momentum (z-scored composite)
Inflation: TIP/SHY 63d change + DBC 63d momentum (z-scored composite)

## 6. Performance Achieved
- **SCORE: 0.891** (strong #2)
- Gross SR: 0.996 (near 1.0)
- Max DD: -5.1%
- Trades: 153 (passes gate)
- Turnover: 1.6x
- Beta: 0.0 (vol-targeted)
- Unique: uses GLD as primary position (not just signal input)

## 7. Key Differentiator
This is the only regime strategy using a 3-asset allocation (SPY+TLT+GLD). The 2×2 framework is the most conceptually complete model — explicitly modeling both growth and inflation forces. It's likely decorrelated from both vol-based (s524) and risk-appetite-based (s532) strategies.

## 8. Risks
- Stagflation allocation tested minimally (brief 2022 episode)
- Growth proxy (SPY momentum) has circularity — mitigated by DBC commodity signal
- GLD vol requires careful position sizing
