# s547 — NEXTWAVE: Thematic Institutional Rotation

## 1. Strategy Name
**NEXTWAVE** — Thematic Momentum Capturing Predicted Institutional Rotation

## 2. Strategy Type
Multi-Factor / Thematic Cross-Sectional Momentum

## 3. Asset Universe
S&P 100 constituents (~92 stocks with clean data via yfinance). Full ticker list in strategy.py.

## 4. Timeframe
Biweekly rebalance (gap >= 10 trading days). Medium-term holding period of 2–4 weeks per position.

## 5. Core Idea / Edge
The Q1 2026 13F season reveals a decisive institutional rotation:
- **Into:** AI infrastructure (power/grid, memory/storage, optical networking, energy, utilities), AI platform businesses (cloud/AWS/Azure), defense/government AI, and healthcare AI
- **Out of:** Traditional SaaS/software (threatened by AI agent disruption), consumer discretionary with AI risk, travel/lodging, China internet

This creates a **predictable cross-sectional drift** as institutional capital flows from disrupted sectors into beneficiary sectors over multi-week horizons. By combining a **thematic relevance score** (capturing which stocks benefit from the predicted rotation) with **medium-term momentum** (capturing actual institutional accumulation), we identify stocks with both fundamental tailwinds and price confirmation.

The edge should persist because: (a) institutional rebalancing happens over weeks, not days; (b) 13F data is backward-looking (45-day lag), so the rotation is still in progress when filings are public; (c) the AI infrastructure theme has a multi-year investment cycle ahead.

## 6. Data Requirements
- Daily adjusted close for S&P 100 tickers (via yfinance)
- No fundamental or alternative data needed. Sector/theme assignments are hardcoded based on public business descriptions.

## 7. Signal Generation
**Composite Score = momentum_zscore + theme_weight × theme_score_normalized**

Where:
- **momentum_zscore**: Cross-sectional z-score of trailing N-day return (N = lookback parameter [126, 189, 252] days)
- **theme_score**: Hardcoded thematic relevance score for each S&P 100 ticker (-2 to +3 scale)
  - +3: AI infrastructure beneficiary (power/grid, memory/storage, AI platforms, energy, utilities, defense AI)
  - +2: Healthcare AI, industrial AI
  - +1: High-quality defensive, financials
  - 0: Neutral/mixed
  - -1: Moderate AI disruption risk
  - -2: High AI disruption risk (traditional SaaS, legacy tech)
- **theme_score_normalized**: theme_score divided by 3 (to map [-2,+3] to [-0.67, +1.0])
- **theme_weight**: How much to weight the theme signal vs momentum [0.0, 0.3, 0.5]

## 8. Entry & Exit Rules
**Entry (Rebalance day):**
1. Candidate pool: All S&P 100 tickers with non-NaN momentum_zscore and known theme_score
2. Rank by composite_score descending
3. Long: Top N positions (N = n_positions parameter, tested at [5, 8])
4. Short: Bottom N positions
5. Tiebreaker: Higher momentum_zscore wins (theme score is secondary)
6. Fallback: If fewer than N candidates on long side, fill remaining with zero weight (no forced positions). Same for short side.

**Exit:** Positions are held until the next rebalance date. No intra-period stops.

## 9. Position Sizing & Risk Management
- Equal-weight each position (1/N of portfolio per side)
- Gross long = gross short = N × (1/N) = 1.0, total gross = 2.0
- Volatility targeting and drawdown gates handled by harness (10% vol target, 20%/30% DD halve/flat)

## 10. Portfolio Construction
Two separately managed portfolios: long book and short book. Each position gets weight = ±1/n_positions. The harness applies vol targeting on top.

## 11. Expected Characteristics
- **Holding period:** ~10-20 trading days (biweekly rebalance)
- **Turnover:** ~10-20x annualized (full portfolio turns every 2 weeks)
- **Win rate:** ~55-60% (thematic momentum tends to be higher than pure reversal)
- **Sharpe target:** 0.4-0.7 net (S&P 100 cross-sectional strategies have ceiling ~0.55, but theme scoring should add 0.1-0.2)
- **Market correlation:** Low to moderate (long/short hedges beta)

## 12. Implementation Notes
- `n_positions` parameter controls how many stocks to long/short
- `momentum_lookback` controls the return calculation window
- Must use `gap-based rebalance` (`(date - prev_date).days >= N`) — fixed-interval rebalance fails the turnover gate
- Theme scores are hardcoded and must be validated against the S&P 100 ticker list
- Use cross-sectional z-score within the S&P 100 universe (not absolute return)

## 13. Potential Risks & Mitigations
- **Overfitting theme scores:** The hardcoded scores are a reflection of Q1 2026 13F data. Test with theme_weight=0 as baseline (pure momentum) to isolate the theme signal value.
- **Regime shift:** If the Iran conflict de-escalates fully, energy/defense scores lose relevance. Mitigated by momentum component adapting to new regime.
- **AI disruption accelerating:** If SaaS disruption is faster than expected, shorts could rally on short-covering. Mitigated by equal-weight position sizing.
- **Concentration risk:** 5 positions per side means 10% per position. Mitigated by vol targeting in harness.

## 14. Backtesting & Validation Framework
- Walk-forward: expanding window, 5-year train, 252-day test, 21-day embargo
- Parameter sweep: n_positions × momentum_lookback × theme_weight (2 × 3 × 3 = 18 combos, within 27 limit)
- Baseline: theme_weight=0.0 tests pure momentum on S&P 100
- Validation: Compare theme_weight>0 vs theme_weight=0 to isolate theme signal value
