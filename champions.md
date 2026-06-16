# Champions — Top Quantitative Strategies

| Rank | ID | Name | SCORE | Sharpe | Max DD | Trades | Turnover | Description |
|------|-----|------|-------|--------|--------|--------|----------|-------------|
| **1** | **s542** | **QQQ/SPY Dispersion** | **1.182** | **1.182** | **-4.4%** | **163** | **1.5×** | **QQQ/SPY ratio z-score (252d) mean reversion. Buy QQQ cheap vs SPY, sell overextended. Pure stat-arb on correlated ETFs. CHAMPION.** |
| **2** | **s575** | **Alt-Asset Trend (ALTTREND)** | **1.065** | **1.065** | **-14.0%** | **187** | **1.2×** | **TS momentum (lb=126) on 7 alt asset managers (BAM/KKR/APO/BX/ARES/CG/TPG). AUM persistence + fee leverage. Second-highest SR ever.** |
| **3** | **s546** | **Post-Earnings Drift (EARNPEAD)** | **0.988** | **0.988** | **-8.5%** | **340** | **12.4×** | **Cross-sectional PEAD on S&P 100. Top5/bottom5 by earnings surprise, 21d hold. #3 overall — pure event-driven edge.** |
| **4** | **s532** | **Risk Appetite Regime (RISKREG)** | **0.961** | **0.961** | **-3.6%** | **166** | **1.4×** | **4-signal risk gauge (credit, VIX, SPY/TLT corr, gold). Former overall champion.** |
| **5** | **s578** | **Alt-MOM (lb=252)** | **1.057** | **1.057** | **-13.5%** | **189** | **1.0×** | **TS momentum lb=252 on 7 alt asset managers. Highest turnover-adjusted alt variant.** |

## Full Leaderboard (all keepers, SR > 0.6)

| ID | Theme | SCORE | SR | Gross | DD | Trades | TO | Universe |
|----|-------|-------|----|-------|-----|--------|----|----------|
| **s542** | **QQQ/SPY Dispersion** | **1.182** | 1.182 | 1.328 | -4.4% | 163 | 1.5× | QQQ+SPY |
| **s575** | **Alt-Asset Trend (ALTTREND)** | **1.065** | 1.065 | 1.124 | -14.0% | 187 | 1.2× | Alt-asset mgrs (7) |
| **s578** | **Alt-MOM (lb=252)** | **1.057** | 1.057 | 1.109 | -13.5% | 189 | 1.0× | Alt-asset mgrs (7) |
| **s581** | **Alt-GAP (gap=7)** | **1.034** | 1.034 | 1.073 | -14.7% | 177 | 0.7× | Alt-asset mgrs (7) |
| **s582** | **Alt-GAP (gap=10)** | **1.034** | 1.034 | 1.073 | -14.7% | 177 | 0.7× | Alt-asset mgrs (7) |
| **s580** | **Alt-GAP (gap=5)** | **1.031** | 1.031 | 1.071 | -14.7% | 188 | 1.2× | Alt-asset mgrs (7) |
| **s577** | **Alt-MOM (lb=189)** | 0.963 | 0.963 | 1.019 | -16.4% | 189 | 1.2× | Alt-asset mgrs (7) |
| **s532** | **Risk Appetite** | 0.961 | 0.961 | 1.097 | -3.6% | 166 | 1.4× | SPY+TLT |
| **s566** | **All Asset-Mgr Trend** | 0.949 | 0.949 | 1.003 | -14.5% | 482 | 2.7× | Asset mgrs (12) |
| **s574** | **Alt-MOM (lb=84)** | 0.944 | 0.944 | 0.989 | -15.2% | 230 | 1.2× | Alt-asset (7) |
| **s562** | **HC-MOM (momentum-wtd)** | 0.915 | 0.915 | 0.969 | -17.5% | 531 | 3.8× | Holding cos (22) |
| **s545** | **Full Hold-Co Trend** | 0.909 | 0.909 | 0.967 | -19.3% | 905 | 4.2× | Holding cos (22) |
| **s534** | **Macro Quadrant** | 0.891 | 0.891 | 0.996 | -5.1% | 153 | 1.6× | SPY+TLT+GLD |
| **s541** | **Nasdaq Regime** | 0.876 | 0.876 | 1.021 | -4.7% | 202 | 1.9× | QQQ+TLT |
| **s524** | **MRDv2** | 0.873 | 0.873 | 1.012 | -2.9% | 192 | 1.7× | SPY+TLT |
| **s528** | **Sector Rotation** | 0.862 | 0.862 | — | -5.3% | 183 | — | Sectors |
| **s543** | **Tech Vol Stress** | 0.817 | 0.817 | 1.035 | -5.5% | 323 | 3.3× | QQQ+TLT |
| **s525** | **MRDv3 Continuous** | 0.743 | 0.743 | — | -4.6% | — | — | SPY+TLT |
| **s538** | **Unified Ensemble** | 0.723 | 0.723 | 0.881 | -5.9% | 239 | 2.1× | SPY+TLT+GLD |
| **s539** | **Tail Risk** | 0.704 | 0.704 | 0.900 | -4.0% | 187 | 3.3× | SPY+TLT+GLD |
| **s540** | **Factor Rotation** | 0.684 | 0.684 | 0.839 | -7.5% | 102 | 4.2× | MTUM/QUAL/USMV/VLUE |
| **s535** | **Dollar/Macro** | 0.697 | 0.697 | 0.824 | -8.7% | 250 | 3.6× | SPY+TLT+GLD+EEM |
| **s533** | **Yield Curve** | 0.627 | 0.627 | 0.855 | -3.1% | 276 | 2.9× | SPY+TLT |

## Earlier Academic Anomaly Champions (pre-s500 batch)

| ID | Name | SR | Gross | DD | TO | Description |
|----|------|----|-------|-----|-----|-------------|
| s548 | Volume-Confirmed 52W High | **0.994** | 1.025 | — | 0.9× | 52W ratio × volume proxy (avg abs daily return), n=3/side, gap=5. Highest cross-sectional equity SR ever. |
| s372 | Pure 52W High (G&H 2004) | 0.544 | 0.586 | — | — | gap=10, n=8, pure 52W ratio signal |
| s385 | MAX Effect (Bali 2011) | 0.446 | 0.494 | — | 2.1× | Short stocks with extreme positive daily returns |
| s313 | Weekly Pattern Reversal | 0.425 | — | — | — | Buy Mon 5d losers, short Fri 5d winners |
| s101 | Corrected Weekly Reversal | 0.353 | 0.524 | -19.2% | 11.2× | 5d reversal on S&P 100, 5/5, weekly (post-bugfix baseline) |
