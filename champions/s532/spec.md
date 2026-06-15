# s532 — Risk Appetite Regime (RISKREG)

## 1. Strategy Name
Risk Appetite Regime Classifier — Multi-Dimensional Market Risk Gauge

## 2. Strategy Type
Regime-Based Asset Allocation / Risk-On Risk-Off Thematic

## 3. Asset Universe
2 ETFs: SPY (S&P 500) and TLT (20-Year Treasury).
Supporting data: HYG (High-Yield), LQD (Investment Grade), ^VIX, ^VIX3M, GLD.

## 4. Timeframe
Daily signals, discrete 3-tier rebalance every 2+ days. 11.3 years OOS.

## 5. Core Idea / Edge
**Thematic Regime: Market risk appetite is a multi-dimensional state measurable across credit, volatility, correlation, and safe-haven demand.**

Triangulates risk across:
1. **Credit markets** — HYG vs LQD MA crossover (smart money risk gauge)
2. **Equity volatility** — VIX vs 63d median (regime-aware, not level-aware)
3. **Cross-asset regime** — SPY/TLT correlation (flight-to-safety signature)
4. **Safe-haven demand** — Gold as risk proxy (liquidation stress indicator)

Edge: When multiple risk dimensions agree, the signal is more robust than any single indicator. Credit markets lead equity volatility by days to weeks.

## 6. Performance Achieved
- **SCORE: 0.961** — NEW CHAMPION (beats s524 by 10%)
- Sharpe net: 0.961, Gross: 1.097
- Max DD: -3.6%
- Trades: 166 (passes gate)
- Turnover: 1.4x
- Beta SPY: 0.0

## 7. Signal Generation
4 binary signals:
1. **Credit** — HYG/LQD ratio 10d MA > 30d MA → Risk-On (+1)
2. **VIX** — VIX < 63d rolling median → Risk-On (+1)
3. **Corr** — SPY/TLT 20d rolling corr < 0 → Risk-On (+1)
4. **Gold** — GLD 21d return > -2% → Risk-On (+1)

Composite = sum of 4 signals [-4, +4]
- Score ≥ 2 → Risk-On → 100% SPY
- Score ≤ -1 → Risk-Off → 20% SPY / 80% TLT
- Else → Neutral → 60% SPY / 40% TLT

## 8. Key Differentiator vs s524
s524 uses vol technicals (VIX TS, RV trend, skew) to detect regimes.
s532 uses MACRO risk structure (credit, vol level vs median, safe-haven demand).
The credit signal (HYG/LQD) provides orthogonal information — the main reason s532 outperforms.

## 9. Risks
- Gold's dual nature (rises in risk-on inflation AND risk-off safe haven) can dilute signal
- VIX median drifts secularly lower in low-vol regimes
- Credit data may have stale pricing
