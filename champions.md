# Champions — Top Quantitative Strategies

| Rank | ID | Name | SCORE | Sharpe | Max DD | Trades | Turnover | Description |
|------|-----|------|-------|--------|--------|--------|----------|-------------|
| **1** | **s532** | **Risk Appetite Regime (RISKREG)** | **0.961** | **0.961** | **-3.6%** | **166** | **1.4×** | **4-signal risk gauge (credit spread MA crossover, VIX vs 63d median, SPY/TLT corr, gold risk proxy). 3-tier Risk-On/Neutral/Risk-Off allocation. NEW CHAMPION — beats old champ s524 by 10%.** |
| 2 | s534 | Macro Quadrant (MACRO4) | 0.891 | 0.891 | -5.1% | 153 | 1.6× | 2×2 Growth×Inflation quadrant classifier. 3-asset (SPY+TLT+GLD). Goldilocks→SPY, Overheat→SPY+GLD, Recession→TLT+SPY, Stagflation→GLD+TLT+SPY. Unique thematic framework. |
| 3 | s524 | MRDv2 Regime Detection | 0.873 | 0.873 | -2.9% | 192 | 1.7× | Classic 5-signal composite (VIX TS, RV trend, SPY/TLT corr, credit spread, SKEW). Benign≥2/Stressed<-1, gap=2d. Former champion. |
| 4 | s533 | Yield Curve Regime (YCREG) | 0.627 | 0.627 | -3.1% | 276 | 2.9× | 3-signal yield curve (slope momentum 10d, slope level vs 252d median, short rate regime) + daily Δcurve z-score. Discrete 3-tier allocation. Cleanest drawdowns. |
| 5 | s531 | Inflation Regime (INFLREG) | 0.450 | 0.450 | -4.5% | 225 | 2.4× | 4 binary signals (20d breakeven, commodities, gold, dollar) + daily breakeven z. Discrete 3-tier allocation. Unique inflation cycle thematic. |

## Regime Detection Family (SPY+TLT)

| ID | Params | SCORE | SR | DD | Trades | Theme |
|----|--------|-------|----|----|--------|-------|
| **s532** | 3-tier RO/Neutral/Roff, credit+VIX+corr+gold | **0.961** | 0.961 | -3.6% | 166 | **Risk Appetite (NEW CHAMPION)** |
| **s534** | 4-quadrant G×I, SPY+TLT+GLD, 3-asset | **0.891** | 0.891 | -5.1% | 153 | **Macro Quadrant** |
| s524 | disc, ben=2, str=-1, 5-sig, gap=2d | 0.873 | 0.873 | -2.9% | 192 | Classic MRDv2 (former champ) |
| s528 | Regime sector rotation (XLE excl) | 0.862 | 1.022 | -5.3% | — | Sector Rotation |
| s533 | 3-sig(10d)+daily Δcurve, disc 3-tier | **0.627** | 0.627 | -3.1% | 276 | **Yield Curve** |
| s525 | MRDv3 continuous sizing | 0.743 | 0.743 | -4.6% | — | Continuous sizing |
| s529 | MRD-V2 Stress Score | 0.670 | 0.789 | -4.7% | — | Rolling z-score |
| s531 | 5-sig(4×binary+daily), disc 3-tier | **0.450** | 0.450 | -4.5% | 225 | **Inflation Regime** |

## Multi-Asset Trend Following

| ID | Name | Score | Max DD | Description |
|----|------|-------|--------|-------------|
| s010 | 50/200 MA Crossover | 0.410 | -17.3% | 12-ETF universe, vol-scaled |
| s008 | VIX-Filtered Trend | 0.359 | -15.9% | 12-ETF trend, flat when VIX>30 |
| s006 | Enhanced Trend | 0.317 | -16.3% | 12-ETF trend, 252d lookback |

## Mean Reversion Family (S&P 100)

| ID | Name | SCORE | DD | Description |
|----|------|-------|----|-------------|
| s275 | Dual Confirmation | 0.394 | — | 5d+10d must agree, 8/side |
| s229 | Gap Weekly Reversal | 0.358 | -21.1% | 10 long/10 short, 5d lookback |
| s101 | Weekly Reversal | 0.353 | -19.2% | 5/5 equal-weight, 5d lookback |

## Academic Anomaly Champions

| ID | Name | SCORE | Gross SR | DD | Description |
|----|------|-------|----------|----|-------------|
| s372 | 52-Week High Effect | 0.544 | 0.586 | -15.2% | Strongest anomaly |
| s385 | MAX Effect | 0.446 | 0.494 | -18.2% | Short lottery-demand stocks |
| s313 | Weekly Pattern Reversal | 0.425 | — | — | Mon/Wed/Fri pattern |
