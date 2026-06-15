# Strategy: Dual Moving Average Crossover (50/200)

## 1. Strategy Name
Dual MA Crossover Trend (50/200 day)

## 2. Strategy Type
Trend Following — Moving Average Crossover

## 3. Asset Universe
Same 12 ETFs as champion: SPY, EFA, EEM, TLT, AGG, HYG, LQD, SHY, GLD, DBC, DBB, FXE

## 4. Timeframe
Daily, weekly rebalance.

## 5. Core Idea / Edge
The 50/200-day moving average crossover is the most widely used systematic trend signal in institutional asset management. When fast MA > slow MA, the asset is in an uptrend (institutional flows are positive). When fast < slow, it's in a downtrend. The edge comes from the same gradual information diffusion as time-series momentum, but MA crossovers provide smoother, more robust signals by averaging out daily noise.

## 6. Signal
Position = +1 (long) if 50-day MA > 200-day MA, -1 (short) if opposite. 0.2% buffer zone around crossover to reduce whipsaws.

## 7. Expected Characteristics
- Lower turnover than the simple trend (MA crossovers change less frequently)
- More robust signals (less noise)
- Similar Sharpe profile to s008 but potentially better in choppy markets
