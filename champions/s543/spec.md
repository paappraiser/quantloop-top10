# s543 — Tech Vol Stress Regime (VXNDIVERGE)

## 1. Strategy Name
VXN/VIX Divergence — Nasdaq-Specific Volatility Regime

## 2. Strategy Type
Regime-Based Asset Allocation / Volatility Divergence

## 3. Asset Universe
QQQ (Nasdaq-100) + TLT (20-Year Treasury).
Supporting: ^VIX, ^VXN (Nasdaq Volatility Index).

## 4. Timeframe
Daily, discrete 3-tier rebalance every 2+ days. 11.3 years OOS.

## 5. Core Idea / Edge
**When Nasdaq volatility (VXN) rises relative to SPX volatility (VIX), it signals tech-specific stress that predicts QQQ underperformance.**

VXN and VIX normally move together (correlation > 0.90). When VXN spikes relative to VIX, it means the options market is pricing disproportionate tail risk in tech stocks — a signal to reduce QQQ exposure. When VXN falls relative to VIX, tech stress is easing.

This is genuinely different from VIX-based regime signals because it isolates the TECH component of vol from the broad market component.

3 signals:
1. **VXN/VIX ratio** — 20d change. If rising → tech stress → defensive
2. **VIX level** — vs its own 63d median (same as champion)
3. **QQQ/TLT correlation** — 20d rolling (same as champion)

## 6. Performance Target
- SR target: 0.50-0.80
- Should catch tech-specific drawdowns (2022 rate hikes, regulatory shocks)
- Low correlation to SPY+TLT regime strategies
