# Strategy Specification — s546

## 1. Strategy Name
**EARNPEAD** — Cross-Sectional Post-Earnings Announcement Drift

## 2. Strategy Type
Cross-sectional long/short factor — earnings surprise (SUE / standardized unexpected earnings)

## 3. Asset Universe
S&P 100 constituents (~92 tickers with yfinance symbol coverage). Excludes tickers that fail to download (e.g. MMC). Universe is static (current S&P 100 membership), which introduces mild survivorship bias.

## 4. Timeframe
Daily rebalance (position entry on earnings events, position exit by holding-period expiry). Walk-forward evaluation 2015–2026.

## 5. Core Idea / Edge
Bernard & Thomas (1989) — post-earnings announcement drift (PEAD). Stocks with large positive earnings surprises outperform stocks with large negative surprises over the subsequent 21 trading days. The edge persists because:
- Underreaction to earnings information (investors anchor on prior expectations)
- Transaction costs limit arbitrage
- Uncertainty about earnings quality delays full price discovery

This strategy exploits the cross-sectional variation: on each earnings date, rank reporting stocks by percentage earnings surprise. Go long the top 5, short the bottom 5. The long/short structure hedges market beta.

## 6. Data Requirements
- **Prices**: Daily adjusted close for all S&P 100 constituents (yfinance, auto_adjust=True)
- **Earnings**: `yfinance.Ticker.earnings_dates` — provides EPS estimate, reported EPS, and Surprise(%) for last ~25 quarters
- **Date range**: 2015-01-01 to present (requires ~10+ years for walk-forward splits)

## 7. Signal Generation
For each trading day `t` in the test period:
1. Collect all earnings events where the earnings date = `t`
2. For each such event, compute `surprise_pct = Surprise(%) / 100` (already percentage points from yfinance)
3. Sort events by `surprise_pct` descending
4. **Long side**: Select the top `n_positions` stocks with the highest positive surprise
5. **Short side**: Select the bottom `n_positions` stocks with the lowest (most negative) surprise
6. Minimum threshold: need ≥ 4 reporting stocks on a given day to form a portfolio (otherwise skip)
7. If < `n_positions` stocks have positive surprise, only long those with positive surprise (vice versa for shorts)

**Holding period**: Each position is held for `hp_days` (=21) trading days, then closed.

**Position management**: Positions are opened at the close on the earnings date. They remain open for exactly `hp_days` trading days, then closed at the close.

**Weighting**: Equal-weight across all active positions. Gross exposure = 2 * n_positions * (1 / total_active) ≈ 2.0 when fully deployed. (Vol targeting in harness scales this.)

## 8. Entry & Exit Rules
**Entry:**
- Candidate pool: All S&P 100 stocks that reported quarterly earnings on date `t` with a non-null Surprise(%) value
- Count: Top 5 by surprise_pct → long; Bottom 5 by surprise_pct → short
- Tiebreaker: If equal surprise_pct, prefer higher absolute EPS estimate (more analyst coverage)
- Fallback: If fewer than 4 stocks report on a day, skip (no portfolio formed that day). If fewer than 5 have positive/negative surprise, use whatever is available.

**Exit:**
- Each position is closed exactly `hp_days` (=21) trading days after entry
- Positions are marked for exit at the close; weight goes to 0 the following day

**Rebalance frequency:** Continuous — new positions opened as earnings events occur, old positions closed as they expire. No scheduled rebalance, only event-driven.

## 9. Position Sizing & Risk Management
Default harness risk plumbing applies:
- Volatility targeting to 10% annualized (portfolio level)
- Per-position cap 10% of NAV
- Max gross exposure 200%
- 20% drawdown → halve exposure; 30% drawdown → flat until recovery

Within these constraints, the strategy uses equal-weight across active positions. When fewer positions than max are active, weights are correspondingly larger to fill the available risk budget.

## 10. Portfolio Construction
- Long and short positions are entered simultaneously from the same cross-sectional ranking
- Net exposure is approximately zero (equal number of long and short positions, equal-weight)
- The portfolio is naturally market-neutral (no explicit beta targeting, but the LS structure hedges directional exposure)
- As positions age, the portfolio contains a mix of entries from recent and prior earnings dates

## 11. Expected Characteristics
| Metric | Expected Value |
|--------|---------------|
| Holding period | 21 trading days |
| Annual turnover | ~6-8× (5 new long + 5 new short per earnings date cluster) |
| Win rate (trade-level) | ~55-57% |
| Sharpe target (net) | 0.8–1.5 |
| Market beta | Near zero |
| % days with positions | ~20-25% (only trades on earnings dates) |
| Typical positions per day | 5-15 (overlapping cohorts) |

## 12. Implementation Notes
- **Earnings data source**: yfinance `Ticker.earnings_dates` returns tz-aware timestamps. Convert to tz-naive for matching with prices index.
- **Surprise(%) normalization**: yfinance provides Surprise(%) as percentage points (e.g., 3.46 means 3.46%). Divide by 100 for proportional surprise. Values > 2 indicate already-divided (edge case from yfinance changes).
- **Position tracking**: Use a dictionary mapping `(ticker, entry_date) -> exit_date` to manage overlapping cohorts.
- **Walk-forward compatibility**: The signal_fn receives the full test period at once. Iterate day-by-day, maintaining state across the loop.
- **Lookahead bias trap**: Only use earnings data whose date is ≤ current processing date. Do NOT use future earnings events.
- **Price alignment**: The prices DataFrame index may differ slightly from earnings date timestamps due to timezone. Use `.date()` comparison for matching.

## 13. Potential Risks & Mitigations
- **Earnings data gap**: yfinance only provides ~25 quarters of earnings history (~6 years). The first ~5 years of the backtest (2015–2019) will have zero positions, reducing the effective test period.
  - Mitigation: Accept the shorter effective sample. The remaining data (2020–2026) provides ~800 trading days with active positions.
- **Concentration risk**: During a single earnings season, many stocks report in a short window, creating a cohort with correlated returns.
  - Mitigation: The 21-day holding period staggers entries across dates, reducing single-day concentration.
- **Regime dependency**: PEAD may weaken during high-volatility regimes or structural market changes.
  - Mitigation: The walk-forward framework provides out-of-sample testing across different market regimes.
- **Survivorship bias**: Using current S&P 100 constituents introduces survivorship bias.
  - Mitigation: S&P 100 is the most stable large-cap index; turnover is minimal (~2-3% annually).

## 14. Backtesting & Validation Framework
- **Walk-forward**: Expanding window, 5-year initial train, retrain every 252 days, 21-day embargo
- **Universe**: S&P 100 (static membership)
- **Cost model**: 10 bps per side (equity)
- **Benchmark**: SPY for beta calculation
- **Parameter budget**: 2 parameters (n_positions ∈ {5, 10}, hp_days ∈ {10, 21}) → 4 combinations, well within the 27-combo limit
- **Validation plan**:
  1. Primary run: n_positions=5, hp_days=21 (the champion from exploration)
  2. Sensitivity: test n_positions=10, hp_days=10
  3. Check year-by-year consistency
  4. Check market beta and correlation to existing champions
