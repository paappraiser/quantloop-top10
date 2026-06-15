# s539 — Tail Risk Regime (TAILREG)

## 1. Strategy Name
Tail Risk Regime — Options-Skew and Crash Protection Timing

## 2. Strategy Type
Regime-Based Asset Allocation / Tail Risk Thematic

## 3. Asset Universe
SPY + TLT + GLD. Supporting: ^SKEW, ^VIX, ^VIX3M, HYG, LQD.

## 4. Timeframe
Daily signals, discrete 3-tier rebalance every 2+ days.

## 5. Core Idea / Edge
**Thematic Regime: Options market's assessment of tail risk predicts when to seek crash protection.**

The equity options market prices tail risk through SKEW (implied tail risk), VIX/VIX3M term structure (near-term vs远期 vol), and credit spreads. When these measures spike simultaneously, a protective posture is warranted.

4 signals:
1. **SKEW Regime** — ^SKEW 20d change > 5 points → tail risk rising (binary: +1 = benign, -1 = tail risk)
2. **VIX Curve Steepness** — VIX/VIX3M ratio. Ratio > 1.05 = backwardation (binary: +1 = normal, -1 = stress)
3. **Credit Tail** — HYG/LQD ratio 10d return < -1% = credit stress (binary: +1 = normal, -1 = stress)  
4. **SKEW Rate of Change** — ^SKEW daily change z-scored over 252d (continuous: high = rising tail risk)

Composite = sum(3 binary) + daily_skew_z * 0.15

3-tier allocation:
- Normal (comp ≥ 1): 100% SPY (no tail risk evident)
- Elevated (comp = 0): 50% SPY, 50% TLT  
- Distressed (comp ≤ -1): 30% SPY, 40% TLT, 30% GLD (tail risk protection: bonds + gold)

## 6. Edge
SKEW is an underutilized signal. Most market participants don't systematically incorporate tail risk pricing into allocation. SKEW spikes precede major drawdowns (Aug 2015, Feb 2018, Mar 2020) with 1-4 week lead times.

## 7. Expected Results
- SCORE target: 0.50-0.70
- Low beta to SPY (most of the time in 100% SPY, only switching to defensive when tail risk is elevated)
- DD: -5% to -10%
- Trades: 150-200 transitions (SKEW changes frequently)
