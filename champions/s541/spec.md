# s541 — Nasdaq Regime (QQQREG)

## 1. Strategy Name
Nasdaq Regime Detection — Champion Risk Appetite Recipe on QQQ+TLT

## 2. Strategy Type
Regime-Based Asset Allocation / Universe Transfer

## 3. Asset Universe
QQQ (Nasdaq-100) + TLT (20-Year Treasury). Supporting: HYG, LQD, ^VIX, GLD.

## 4. Timeframe
Daily, discrete 3-tier rebalance every 2+ days. 11.3 years OOS.

## 5. Core Idea / Edge
**Universe transfer test: does the champion risk appetite recipe (s532) work on QQQ+TLT?**

The champion s532 (SR 0.961) uses 4 risk appetite signals to allocate between SPY and TLT. This strategy applies the exact same signal structure to QQQ and TLT instead. The question: is the regime detection edge market-wide, or is it SPY-specific?

If s541 achieves SR > 0.80, the regime signals capture a market-wide phenomenon. If it's significantly lower, the risk appetite signal has a specific SPY timing component.

## 6. Signals (identical to s532)
4 binary signals:
1. **Credit Spread** — HYG/LQD ratio 10d/30d MA crossover (+1 = risk-on)
2. **VIX Level** — ^VIX vs 63d rolling median (+1 = VIX low = risk-on)
3. **QQQ/TLT Correlation** — 20d rolling corr < 0 (+1 = normal = risk-on)
4. **Gold Risk** — GLD 21d return > -2% (+1 = normal = risk-on)

Composite = sum of 4 [-4, +4]
- Score ≥ 2 → Risk-On → 100% QQQ
- Score ≤ -1 → Risk-Off → 100% TLT
- Else → Neutral → 60% QQQ, 40% TLT

## 7. Expected Results
- If SR > 0.80: regime signal is market-wide, not SPY-specific
- If SR 0.60-0.80: signal has some Nasdaq-specific timing ability
- If SR < 0.50: signal is SPY-specific
