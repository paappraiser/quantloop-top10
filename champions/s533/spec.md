# s533 — Yield Curve Regime Classifier (YCREG) v3

## 1. Strategy Name
Yield Curve Regime Classifier — Bond Market's Economic Outlook

## 2. Strategy Type
Regime-Based Asset Allocation / Rate Cycle Thematic

## 3. Asset Universe
2 ETFs: SPY (S&P 500) and TLT (20-Year Treasury).
Supporting: SHY (1-3yr Treasury).

## 4. Timeframe
Daily signals, discrete 3-tier rebalance every 2+ days. 11.3 years OOS.

## 5. Core Idea / Edge
**Thematic Regime: The yield curve slope and its direction predict whether equities or bonds will lead.**

Three regimes:
- **Steepening** (TLT rising faster than SHY) → Bond market expects growth → bullish for equities
- **Neutral** → Balanced backdrop
- **Flattening/Inverted** → Bond market expects slowdown → defensive

3 signals at 10d lookback + daily Δcurve z-score:
1. **Slope momentum** — TLT/SHY ratio 10d change
2. **Slope level** — TLT/SHY ratio vs 252d median
3. **Short rate regime** — SHY 10d momentum (inverted: falling = accommodative)
4. **Daily Δcurve** — daily change in TLT/SHY ratio z-scored

## 6. Performance Achieved
- **SCORE: 0.627**
- Gross SR: 0.855 (high gross edge)
- Max DD: -3.1% (cleanest drawdowns of any regime classifier)
- Trades: 276 (passes gate comfortably)
- Turnover: 2.9x
- Beta: 0.0

## 7. Signal Generation
Composite = sum(3 binary 10d) + daily_curve_z * 0.15
- Score ≥ 1.0 → Steepening → 100% SPY
- Score ≤ -1.0 → Flattening → 100% TLT
- Else → Neutral → 50% SPY / 50% TLT

## 8. Key Characteristic
The yield curve has the most persistent edge of all macro themes. High gross SR (0.855) suggests the signal quality is strong but costs and implementation frictions reduce net. The -3.1% DD makes it a strong diversifier.

## 9. Risks
- Zero-lower-bound periods (2010-2015) suppress curve variation
- SHY has ex-dividend dates causing small daily jumps (negligible at 10d horizon)
- Rate shocks (2022) move signals rapidly through all 3 tiers
