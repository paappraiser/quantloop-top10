# s544 — Aggregated Stock Reversal Pressure (CROWD)

## 1. Strategy Name
Crowd Wisdom — Aggregated Individual Stock Reversal for Market Timing

## 2. Strategy Type
Market Timing / Aggregated Microstructure / Non-Standard

## 3. Asset Universe
SPY + TLT. Signal derived from ~200 liquid stocks (S&P 200).
Supporting: yfinance download of stock universe.

## 4. Timeframe
Daily, discrete 3-tier rebalance every 2+ days. 11.3 years OOS.

## 5. Core Idea / Edge
**The average of individual stock reversal signals predicts market direction.**

This is completely different from both cross-sectional LS (which ranks stocks against each other) and pure market timing (which uses market-level data). Instead:
1. For each stock, compute a simple 5-day reversal signal (z-score of 5d return)
2. Average the z-scores across ALL stocks → "aggregated reversal pressure"
3. When the average is strongly positive (many stocks oversold and bouncing) → market is likely to rally → long SPY
4. When the average is strongly negative (many stocks overbought and rolling over) → market is likely to fall → long TLT

The logic: individual stock reversals are partly idiosyncratic (noise) and partly systematic (the market's tendency to mean-revert). By aggregating, the idiosyncratic noise cancels out and the systematic reversal signal emerges.

This is inspired by "crowd wisdom" / ensemble methods — aggregating many weak signals into a stronger one.

## 6. Signals
For each stock in universe:
- 5-day return → z-score over 252d → clip to [-3, +3]
- Average across all stocks → "crowd_signal"
- Also compute: % of stocks with extreme reversal (> 1.5 sigma) — "breadth_signal"

Composite = crowd_signal * 0.7 + breadth_signal * 0.3

3-tier allocation:
- Composite ≥ 0.5 → SPY oversold at stock level → market rally → 100% SPY
- Composite ≤ -0.5 → SPY overbought at stock level → market fall → 100% TLT
- Between → 50% SPY, 50% TLT

## 7. Performance Target
- SR target: 0.30-0.60 (noisy but genuinely non-standard)
- Should have positive skew (catches bounce-backs after selloffs)
- Trades: 100-200 (daily changes in aggregate)
- Zero lookahead bias by construction (uses only past data per stock)
