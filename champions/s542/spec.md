# s542 — QQQ/SPY Ratio Mean Reversion (DISPERSION)

## 1. Strategy Name
QQQ/SPY Dispersion — Mean-Reverting the Tech vs Market Ratio

## 2. Strategy Type
Statistical Arbitrage / Pairs Mean Reversion

## 3. Asset Universe
QQQ (Nasdaq-100) + SPY (S&P 500).

## 4. Timeframe
Daily, 3-tier rebalance every 2+ days. 11.3 years OOS.

## 5. Core Idea / Edge
**When the ratio of QQQ to SPY reaches extremes, it mean-reverts.**

QQQ and SPY are highly correlated (0.85-0.95) but QQQ has higher beta to tech/growth sentiment. When QQQ rallies much faster than SPY (ratio z-score > 1.0), it's typically overextended and reverts. When QQQ lags badly (ratio z-score < -1.0), it's oversold and bounces.

This is a pure statistical arbitrage on the spread between two highly correlated ETFs. The edge comes from the fact that QQQ's higher vol means it overshoots both directions relative to SPY.

## 6. Signals
QQQ/SPY price ratio, 252d rolling z-score:
- z > 1.0 → QQQ overextended → short QQQ/long SPY
- z < -1.0 → QQQ oversold → long QQQ/short SPY
- Between → neutral 50/50

Entry: ratio z-score crosses ±1.0 threshold
Exit: z-score reverts toward 0

## 7. Expected Results
- SR target: 0.3-0.6 (pairs strategies have lower Sharpe but are decorrelated)
- Should have negative beta (long SPY when QQQ falls, long QQQ when SPY up)
- Trades: 40-80 (ratio changes infrequently)
