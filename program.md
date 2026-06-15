# program.md — quantloop autonomous strategy research

## Evolving Heuristics

### What works here
- **Multi-dimensional risk appetite gauge is the strongest regime classifier.** 4-signal composite (credit spread MA crossover + VIX vs 63d median + SPY/TLT corr + gold risk proxy) achieves SR 0.961, beating the previous champion by 10%. The credit signal (HYG/LQD) adds orthogonal information to vol-based signals. (n=1: s532 new champion)
- **Macro 2×2 quadrant framework (Growth×Inflation) is robust and decorrelated.** Using SPY+TLT+GLD in 4 macro quadrants (Goldilocks/Overheat/Recession/Stagflation) achieves SR 0.891 with 153 trades. This is the only strategy using GLD as a primary allocation, not just a signal. (n=1: s534)
- **Thematic regime classifiers with DISCRETE 3-tier allocation (SPY/TLT/50-50) all pass the gates.** Yield curve (SR 0.627), Inflation (SR 0.450), Risk appetite (SR 0.961), Macro quadrant (SR 0.891). The common pattern: 3-5 signals at short lookbacks (10-20d) + daily z-scored change component. (n=4: s531-s534)
- **Yield curve signals (TLT/SHY ratio slope + short rate momentum) produce the cleanest drawdowns** at -3.1% DD with high trade frequency (276 trades). The curve is a durable leading indicator. (n=1: s533)
- **Inflation regime signals (breakeven + commodities + gold + dollar) have positive SR** but the lowest of all regime families (0.45). Inflation is a slow-moving macro force that's harder to time. (n=1: s531)
- **Multi-asset trend-following on diversified ETF universes is the only other reliably positive strategy.** Time-series momentum (12-month lookback) on equities+bonds+commodities+FX generates consistent positive Sharpe across 14+ years OOS. (n=4: s003, s004, s006, s007, s008)
- **Weekly rebalance with vol-scaling per asset** is the right implementation pattern for both trend-following and volume regime. (n=+4)

### What fails here
- **Market-wide volume regime timing on a single asset (SPY)** fails the trade count gate — the regime is too persistent (< 32 trades in 11 years). Trade frequency on regime CHANGES is insufficient. (n=6: s502-s509)
- **MACD-style double-smoothing** on regime signals reduces trade count to < 30. Raw delta barely helps — the 21d lookback dominates persistence. (n=2: s502 vs s503)
- **Shorter lookbacks for volume regime (5d, 10d)** destroy signal quality — SR goes from 0.45 to -0.17. The 21d window is the minimum for meaningful volume-price correlation. (n=2: s524, s513)
- **Contrarian volume regime** (long worst, short best) works on individual stocks (S&P 100) but NOT on diversified ETFs. ETF volume accumulation is trending, not mean-reverting. (n=3: s511, s515, s523)
- **Cross-sectional volume regime on individual stocks (S&P 100)** has near-zero net Sharpe. The volume signal is too noisy at the stock level; institutional flow patterns are clearer at the asset-class level. (n=2: s500, s501)
- **Volatility-regime delta ranking** (rank ETFs by CHANGE in volume regime, not level) produces negative Sharpe. The level is more informative than the change. (n=1: s522)
- **Cross-sectional strategies on 9 SPDR sector ETFs consistently fail.** Momentum (s001: Sharpe -0.04), pairs mean-reversion (s002: Sharpe -0.43), and low-volatility (s005: Sharpe -0.41) all have negative or near-zero net Sharpe. Sector ETFs are too tightly correlated for reliable relative-value edge after 10 bps costs. (n=3)
- **Pairs mean-reversion** has negative gross Sharpe (-0.08) before costs. The pairs aren't reliably mean-reverting. (n=1, s002)
- **Dual-momentum's higher turnover** (19× for s007 vs 13× for s006) erodes its gross edge advantage (0.537 vs 0.523). Better gross Sharpe but worse net. (n=2)
- **Cross-sectional low-volatility** anomaly doesn't exist on sector ETFs — defensive sectors don't reliably outperform cyclical ones after costs. (n=1, s005)

### Process lessons
- **CRITICAL: On 2-asset portfolios with per-position cap (MAX_POS_PCT=0.10), continuous allocation generates ZERO turnover.** The 10% cap clips every position to ≤0.1 regardless of signal, so gradually varying weights become constant [0.1,0.1]. Only discrete allocation (0/100, 100/0, 50/50) creates detectable weight changes in the capped weights. This affected all 4 thematic regime strategies — the first 3 revisions of s531 and s533 failed because of continuous allocation. ALWAYS USE DISCRETE ALLOCATION FOR 2-ASSET PORTFOLIOS IN THIS HARNESS. (n=4 strategies, n=3 failed revisions)
- **Thematic regime classifiers need SHORT lookbacks (10-20d) AND a daily-change high-frequency signal component** to generate enough trades. Pure medium-term momentum signals (63d, 252d) on macro variables are too persistent. The successful pattern: 3-5 binary signals at 10-20d lookback + daily z-scored change component. (n=4: s531-s534)
- **Cross-asset volume regime ranking is the key to making "second-derivative" trading work.** Single-asset regime timing doesn't generate enough trades. You need 12+ assets and cross-sectional ranking to get >100 trades in 11 years.
- **The volume regime signal is contrarian on stocks but direct on ETFs.** At the individual stock level, heavy accumulation means the stock is extended (contrarian). At the asset-class level, accumulation means capital flows are trending (momentum). Always test both directions when moving between universes.
- **Add more assets, not more parameters.** The winning strategy has 0 free parameters (equal-weight all components, rank 12+ assets). Adding assets beats tuning. (n=10: s510-s528)
- Always `.shift(1)` signals before computing returns; lookahead bias is the most common silent failure. (seed)
- `DataFrame * Series` in pandas silently creates an outer join on column × index labels — always use `.mul(series, axis=0)` for row-wise multiplication. (harness bug, fixed)
- yfinance >=0.2.50 returns MultiIndex columns even for single tickers — use `.xs("Close", axis=1, level=1)` for multi-ticker and `.xs("Close", axis=1, level=0)` for single-ticker. (harness fix) 
- VIX data can be downloaded separately from yfinance and used as a regime filter. Requires careful index alignment (ffill to match trading dates).
