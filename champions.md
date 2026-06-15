# Champions — Top Quantitative Strategies

| Rank | ID | Name | SCORE | Sharpe | Max DD | Trades | Turnover | Description |
|------|-----|------|-------|--------|--------|--------|----------|-------------|
| **1** | **s532** | **Risk Appetite Regime (RISKREG)** | **0.961** | **0.961** | **-3.6%** | **166** | **1.4×** | **4-signal risk gauge (credit spread MA crossover, VIX vs 63d median, SPY/TLT corr, gold risk proxy). 3-tier Risk-On/Neutral/Risk-Off allocation. CHAMPION.** |
| 2 | s534 | Macro Quadrant (MACRO4) | 0.891 | 0.891 | -5.1% | 153 | 1.6× | 2×2 Growth×Inflation quadrant. 3-asset (SPY+TLT+GLD). Unique thematic framework. |
| 3 | s524 | MRDv2 Regime Detection | 0.873 | 0.873 | -2.9% | 192 | 1.7× | Classic 5-signal composite (VIX TS, RV trend, corr, credit, SKEW). Former champion. |
| 4 | s528 | Regime Sector Rotation | 0.862 | 0.862 | -5.3% | 183 | — | 5-signal regime composite applied to sector ETFs (XLK/XLF/XLU). |
| 5 | s538 | Unified Regime Ensemble | **0.723** | 0.723 | -5.9% | 239 | 2.1× | Meta-ensemble of 6 regime themes (risk appetite, growth, inflation, yield curve, dollar, vol). Daily delta for trade frequency. |

## Deep Dive Regime Strategies (New)

| ID | Theme | SCORE | SR | Gross SR | DD | Trades | Universe |
|----|-------|-------|----|----------|----|--------|----------|
| s538 | **Unified Ensemble** | **0.723** | 0.723 | 0.881 | -5.9% | 239 | SPY+TLT+GLD |
| s539 | **Tail Risk** | **0.704** | 0.704 | 0.900 | -4.0% | 187 | SPY+TLT+GLD |
| s535 | **Dollar/Global Macro** | **0.697** | 0.697 | 0.824 | -8.7% | 250 | SPY+TLT+GLD+EEM |
| s540 | **Factor Rotation** | **0.684** | 0.684 | 0.839 | -7.5% | 102 | MTUM/QUAL/USMV/VLUE |
| s537 | **Vol Ensemble** | **0.444** | 0.444 | 0.568 | -5.8% | 162 | SPY+TLT |
| s536 | **Correlation Regime** | **0.321** | 0.321 | 0.692 | -3.8% | 399 | SPY+TLT+GLD |

## Regime Detection Family (All Keepers)

| ID | Params | SCORE | SR | DD | Trades | Theme |
|----|--------|-------|----|----|--------|-------|
| **s532** | 3-tier RO/Neutral/Roff, credit+VIX+corr+gold | **0.961** | 0.961 | -3.6% | 166 | **Risk Appetite (CHAMPION)** |
| s534 | 4-quadrant G×I, SPY+TLT+GLD, 3-asset | **0.891** | 0.891 | -5.1% | 153 | **Macro Quadrant** |
| s524 | disc, ben=2, str=-1, 5-sig, gap=2d | **0.873** | 0.873 | -2.9% | 192 | Classic MRDv2 |
| s528 | Regime sector rotation | **0.862** | 0.862 | -5.3% | 183 | Sector Rotation |
| s538 | Ensemble of 6 themes + delta | **0.723** | 0.723 | -5.9% | 239 | **Unified Ensemble** |
| s539 | SKEW+VIX+credit tail risk | **0.704** | 0.704 | -4.0% | 187 | **Tail Risk** |
| s535 | USD cycle, 4-asset | **0.697** | 0.697 | -8.7% | 250 | **Dollar/Macro** |
| s525 | Continuous sizing | **0.743** | 0.743 | -4.6% | — | Continuous |
| s540 | Factor rotation | **0.684** | 0.684 | -7.5% | 102 | **Factor** |
| s533 | Yield curve | **0.627** | 0.627 | -3.1% | 276 | **Yield Curve** |
| s531 | Inflation | **0.450** | 0.450 | -4.5% | 225 | **Inflation** |
| s537 | Vol ensemble | **0.444** | 0.444 | -5.8% | 162 | **Vol Ensemble** |
| s536 | PCA correlation | **0.321** | 0.321 | -3.8% | 399 | **Correlation** |

## Multi-Asset Trend Following

| ID | Name | Score | Max DD | Description |
|----|------|-------|--------|-------------|
| s010 | 50/200 MA Crossover | 0.410 | -17.3% | 12-ETF universe, vol-scaled |
| s008 | VIX-Filtered Trend | 0.359 | -15.9% | 12-ETF trend, flat when VIX>30 |
| s006 | Enhanced Trend | 0.317 | -16.3% | 12-ETF trend, 252d lookback |

## Factor Rotation Family (New)

| ID | Name | SCORE | DD | Description |
|----|------|-------|----|-------------|
| s540 | Factor Rotation | 0.684 | -7.5% | 3 macro signals (vol/growth/yield) rotate MTUM/QUAL/USMV/VLUE |
