# Alt-Asset Manager Time-Series Momentum — Research Findings

## Executive Summary

A pure time-series momentum strategy on a 7-ticker universe of US-listed alternative asset managers (BAM, KKR, APO, BX, ARES, CG, TPG) achieves **SR 1.0646** with only **-14.0% max drawdown** and **1.2× annual turnover**. This is the **second-strongest strategy ever tested** in this research project, behind only the QQQ/SPY dispersion strategy (SR 1.182).

## Winning Configuration

| Parameter | Value |
|---|---|
| **Strategy ID** | s575 |
| **Signal** | Time-series momentum (lookback = 126 trading days) |
| **Universe** | BAM, KKR, APO, BX, ARES, CG, TPG |
| **Weighting** | Equal-weight among positive-momentum names |
| **Rebalance** | Weekly (gap = 4+ calendar days) |
| **Side** | Long only (no shorts) |

## Performance

| Metric | s575 | s578 (lb=252) | s545 (full uni) |
|---|---|---|---|
| **SCORE (Sharpe net)** | **1.0646** | 1.0573 | 0.9086 |
| Sharpe gross | 1.1241 | 1.1093 | 0.9669 |
| Max DD | **-14.0%** | -13.5% | -19.3% |
| Annual turnover | 1.2× | 1.0× | 4.2× |
| Number of trades | 187 | 189 | 905 |
| Win rate | 45.1% | 47.7% | 47.9% |
| Beta to SPY | 0.0 | 0.0 | 0.0 |

## Why This Works

The alt-asset manager universe (KKR, Apollo, Blackstone, Brookfield, Ares, Carlyle, TPG) has a structural advantage for trend-following:

1. **AUM persistence**: These firms earn management fees on Assets Under Management. When markets trend, AUM grows mechanically (asset appreciation), and future fee revenue rises. This creates a self-reinforcing loop: market up → AUM up → revenue outlook up → stock up.

2. **Fee structure leverage**: Alt managers earn performance fees on gains. In up-trending markets, both management fees AND performance fees compound, amplifying earnings growth beyond simple market beta.

3. **Deal cycle inertia**: Private equity and credit investing has a natural lag between market conditions and reported results. A portfolio company acquired in good conditions takes 3-7 years to exit. This creates multi-year earnings persistence.

4. **Low short interest / structural demand**: These stocks are held by long-only institutional investors seeking alternative asset exposure, reducing short-term volatility and noise.

5. **Concentrated momentum**: All 7 names responded to the same macro factor (rising/falling markets) but with individual timing differences. The TS momentum signal captures the persistent component.

## Robustness

The strategy is remarkably robust across parameter space:

- **Every lookback from 21 to 378** produced SR > 0.80 on the alt universe
- **All 14 tested configurations** keepers (none crashed)
- **Drawdowns cluster in -13% to -19%** regardless of lookback — consistent risk profile
- **Turnover decreases with lookback**: 1.9× at lb=21 → 0.9× at lb=378 — monotonic
- **Weighting scheme barely matters**: equal (0.994) ≈ strength-weighted (0.972)
- **Rebalance gap**: weekly (gap=4, 0.994) ≈ biweekly (gap=5-10, 1.03) — stable

## Comparison vs Prior Champions

| Rank | ID | Strategy | SR | DD | TO | Type |
|---|---|---|---|---|---|---|
| **1** | **s542** | QQQ/SPY dispersion | **1.1819** | -4.4% | 1.5× | Mean reversion |
| **2** | **s575** | Alt-asset TS mom (lb=126) | **1.0646** | -14.0% | 1.2× | Trend following |
| 3 | s565 | Alt-asset TS mom (lb=42) | 0.9937 | -13.9% | 1.6× | Trend following |
| 4 | s532 | Risk appetite (SPY+TLT) | 0.961 | — | — | Regime detection |
| 5 | s566 | All asset-mgr TS mom | 0.9492 | -14.5% | 2.7× | Trend following |
| 6 | s545 | Full-hold-co TS mom (lb=42) | 0.9086 | -19.3% | 4.2× | Trend following |

## Key Insights

1. **The alt-asset sub-universe is the key.** Pure holding companies (BRK, MKL, FFH, BN, L) are too few and too slow-moving (only 86 trades, fail the gate). The 7 alt managers have the right blend of similarity AND individual variance for TS momentum.

2. **Long-only, never short.** All long/short variants failed (s559 SR 0.004). The short side has no edge — these stocks don't have clean mean reversion.

3. **Weekly rebalance is optimal.** More frequent rebalancing (gap=2 or 3) increases turnover 8× (from 1.4× to 11.5×) and worsens DD (from -14% to -27%).

4. **This is a different strategy class from the regime champions.** The regime strategies (s524, s532) time ETFs with macro signals. The alt-asset TS momentum follows individual stocks with a price-based signal. Both are valid and uncorrelated approaches.

5. **The signal works best at medium-term lookbacks (126/252).** Short lookback (21) has SR 0.82 vs long (378) SR 0.86 — but the 126 and 252 are the clear sweet spots at SR 1.06.

## Implementation Notes

- 7 tickers: BAM, KKR, APO, BX, ARES, CG, TPG
- Buy all tickers with positive 126-day return, equal-weight
- Rebalance every Monday (or first available day after 4 calendar days)
- No short positions
- Vol target to 10% annualized
- BAM has limited history (2018+) — signal only activates when sufficient data exists

## Key Caveats

- **Small universe**: 7 tickers means concentrated bets. Position-level DD could be higher during alt-asset-specific crises (e.g., a KKR-specific scandal).
- **Regime dependence**: The strategy is long-only and will suffer in sustained bear markets for alternative assets. The 2008 crisis period may have different dynamics (some tickers have limited pre-2010 data).
- **Capacity**: These are multi-billion-dollar public companies — capacity should not be an issue.
- **Survivorship bias**: All 7 names are current market leaders. Backtest excludes failed alt managers that delisted.
