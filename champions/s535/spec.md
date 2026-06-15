# s535 — Dollar/Global Macro Regime (USDCYCLE)

**Status:** Draft  
**Version:** 1.0.0  
**Last Updated:** 2026-06-15  
**Author:** Agent (Quantloop)

---

## 1. Strategy Overview

| Field | Value |
|---|---|
| **Strategy ID** | s535 |
| **Short Name** | USDCYCLE |
| **Long Name** | Dollar/Global Macro Regime |
| **Asset Class** | Multi-asset (equities, bonds, commodities, EM) |
| **Trading Frequency** | Daily (EOD rebalance triggered by daily regime update) |
| **Avg Holding Period** | 5–30 days (regime-dependent) |
| **Max Positions** | 4 |
| **Gross Exposure** | 100% (fully invested; leverage = 1.0×) |
| **Net Exposure** | Varies by regime (30%–70% equities) |
| **Inception** | TBD |

The USD cycle is the most powerful single macro force in cross-asset markets. A strengthening USD suppresses EM equities (EEM), commodities (DBC), and gold (GLD), while supporting US bonds (TLT). A weakening USD does the opposite. This strategy classifies the USD regime into four tiers and allocates across SPY + TLT + GLD + EEM accordingly, using a composite score that blends four binary 20-day trend signals with a daily z-scored dollar-change momentum component.

---

## 2. Strategy Rationale / Investment Thesis

### 2.1 The Dollar Cycle as the Dominant Macro Force

The US Dollar Index (DX-Y / UUP) drives capital flows across every major asset class:

- **Strong USD environment** — Capital flows into USD-denominated safe havens. US bonds benefit as foreign buyers park cash in Treasuries. EM equities suffer as dollar-denominated debt becomes more expensive to service. Commodities (priced in USD) decline as purchasing power shifts. Gold struggles as the dollar alternative loses appeal.
- **Weak USD environment** — Capital rotates out of the dollar. EM equities rally on easier financing conditions and commodity-export tailwinds. Gold appreciates as a dollar hedge. Commodities rise on reflation. US bonds underperform as inflation expectations rise and dollar hedging unwinds.

### 2.2 Why Four Assets

| Asset | Ticker | Role in Strong USD | Role in Weak USD |
|---|---|---|---|
| US Equities | SPY | Minimal defensive holding (large-cap US earns domestically) | Core risk-on holding |
| US Long Bonds | TLT | Primary safe haven (rate differential + foreign buying) | Reduce / zero (inflation headwind) |
| Gold | GLD | Weak — dollar strength suppresses gold | Hedge — dollar weakness lifts gold |
| EM Equities | EEM | Zero — debt burden crushes EM | High conviction — capital inflows |

### 2.3 Why 20-Day Binary Signals + Daily Z-Score

- **20-day binary signals** provide regime classification based on established momentum. They filter out daily noise and identify persistent trends.
- **Daily z-scored delta** adds a continuous intensity component that allows the composite score to react intra-regime — a dollar that is already "strong" but accelerating further pushes allocation deeper into defensive, while a dollar that is "strong" but weakening triggers an early shift toward balanced.
- **Key insight:** The dollar regime changes more frequently than inflation regimes but less often than pure risk appetite oscillators. The hybrid approach generates enough trading activity (estimated 40–80 rebalance events per year) without overtrading.

---

## 3. Trading Universe

### 3.1 Candidate Universe

Exactly 4 ETFs, selected for liquidity, low expense ratios, and pure-factor exposure:

| # | Ticker | Name | Asset Class | Primary Role |
|---|---|---|---|---|
| 1 | SPY | SPDR S&P 500 ETF Trust | US Large-Cap Equity | Core equity exposure |
| 2 | TLT | iShares 20+ Year Treasury Bond ETF | US Long-Term Treasuries | Safe-haven / rate hedge |
| 3 | GLD | SPDR Gold Shares | Physical Gold | Dollar hedge / inflation hedge |
| 4 | EEM | iShares MSCI Emerging Markets ETF | EM Equity | High-beta risk-on |

### 3.2 Signal-Only Instruments (not traded)

| # | Ticker | Name | Data Used |
|---|---|---|---|
| 1 | UUP | Invesco DB USD Index Bullish Fund | 20-day momentum, daily return |
| 2 | DBC | Invesco DB Commodity Index Tracking Fund | 20-day momentum (confirmation signal) |

### 3.3 Liquidity Requirements

All four traded ETFs have:
- Average daily volume > 1M shares
- Average daily dollar volume > $50M
- Bid-ask spread < 0.05%
- Options listed (for potential future hedging)

### 3.4 Universe Rules

| Rule | Detail |
|---|---|
| **Maximum positions** | 4 (hard limit — all four always held) |
| **Minimum positions** | 4 (no cash — always fully invested) |
| **Addition criteria** | None — universe is fixed |
| **Removal criteria** | Only if an ETF is delisted, merged, or has a structural tracking error > 2%/yr |
| **Rebalance trigger** | Daily regime signal update (see Section 6) |
| **Sector constraints** | N/A — each ETF represents a distinct asset class |

---

## 4. Data Sources & Processing

### 4.1 Primary Data Sources

| Data | Source | Ticker | Priority |
|---|---|---|---|
| Daily OHLCV — SPY | Yahoo Finance | SPY | Primary |
| Daily OHLCV — TLT | Yahoo Finance | TLT | Primary |
| Daily OHLCV — GLD | Yahoo Finance | GLD | Primary |
| Daily OHLCV — EEM | Yahoo Finance | EEM | Primary |
| Daily OHLCV — UUP | Yahoo Finance | UUP | Primary |
| Daily OHLCV — DBC | Yahoo Finance | DBC | Primary |

### 4.2 Data Requirements

| Requirement | Value |
|---|---|
| Minimum lookback | 252 trading days (1 year) for z-score calculation |
| Recommended lookback | 504 trading days (2 years) for stable z-score |
| Recalculation window | 20 trading days for binary signals |
| Z-score rolling window | 63 trading days (~3 months) for UUP daily returns |
| Data freshness | EOD data must include the most recent close |
| Adjustments | Split/dividend-adjusted close prices only |

### 4.3 Data Quality Rules

| Check | Action |
|---|---|
| Missing price for any ticker | Skip rebalance, hold prior allocation |
| Stale price (>1 day old) | Skip rebalance, log warning |
| Zero or negative price | Skip rebalance, flag critical error |
| >5% single-day gap (suspect split/dividend) | Verify adjusted close; if confirmed, proceed |
| All four tickers must have valid data | If any missing, entire strategy holds |

### 4.4 Fallback Data Chain

1. **Primary:** Yahoo Finance (via yfinance or equivalent)
2. **Secondary:** Alpaca Market Data (if available)
3. **Tertiary:** Cached last-known prices (max 2 days stale)
4. **Final fallback:** Hold current allocation — do not rebalance

---

## 5. Signals — Specification

### 5.1 Signal Architecture Overview

The strategy uses **5 signal components**:
- **4 binary signals** (each ∈ {−1, +1}), computed from 20-day momentum
- **1 continuous signal** (UUP daily return z-scored, range −3 to +3)

All signals are recomputed daily at EOD.

### 5.2 Signal 1 — DOLLAR Trend (Binary: ±1)

**Purpose:** Detect the primary direction of the USD cycle.

**Instrument:** UUP (USD Index Bullish Fund)

**Calculation:**
```
UUP_20d_return = (UUP_close[t] / UUP_close[t-20]) - 1
DOLLAR = +1  if UUP_20d_return < 0   (UUP falling → weak dollar)
DOLLAR = -1  if UUP_20d_return >= 0  (UUP rising → strong dollar)
```

**Interpretation:**
- **+1 (weak dollar):** Dollar declining over the past 20 days → risk-on tilt
- **−1 (strong dollar):** Dollar rising over the past 20 days → defensive tilt

**Edge case — exact zero:** If UUP_20d_return == 0 exactly (flat over 20 days), treat as strong dollar (−1). Rationale: flat dollar favors incumbents (US assets); the regime is not clearly weak.

### 5.3 Signal 2 — COMMODITY Confirmation (Binary: ±1)

**Purpose:** Confirm dollar weakness with commodity price strength. Commodities are priced in USD — when the dollar falls, commodity prices should rise. This signal catches regime changes that the dollar signal alone might miss (e.g., a sudden commodity surge on supply shock that precedes dollar movement).

**Instrument:** DBC (Commodity Index Tracking Fund)

**Calculation:**
```
DBC_20d_return = (DBC_close[t] / DBC_close[t-20]) - 1
COMMODITY = +1  if DBC_20d_return >= 0  (commodities rising → confirms weak dollar)
COMMODITY = -1  if DBC_20d_return < 0   (commodities falling → contradicts weak dollar)
```

**Interpretation:**
- **+1:** Commodities rising → confirms the weak-dollar/risk-on narrative
- **−1:** Commodities falling → contradicts weak-dollar thesis; may indicate deflationary pressure

**Edge case — exact zero:** If DBC_20d_return == 0, treat as +1 (commodities flat). Rationale: flat commodities do not contradict dollar weakness.

### 5.4 Signal 3 — GLOBAL Growth Differential (Binary: ±1)

**Purpose:** Measure relative performance of EM vs US equities. EM equities outperform US when global growth expectations are rising and capital flows into riskier markets — conditions associated with a weak USD. Conversely, EM underperformance signals risk-off / strong USD.

**Instrument:** EEM (EM equities) and SPY (US equities), combined as a ratio

**Calculation:**
```
EEM_SPY_ratio[t] = EEM_close[t] / SPY_close[t]
EEM_SPY_ratio_20d_change = (EEM_SPY_ratio[t] / EEM_SPY_ratio[t-20]) - 1
GLOBAL = +1  if EEM_SPY_ratio_20d_change >= 0   (EM outperforming → risk-on / weak dollar)
GLOBAL = -1  if EEM_SPY_ratio_20d_change < 0    (EM underperforming → risk-off / strong dollar)
```

**Interpretation:**
- **+1:** EM outperforming US → capital flowing to risk-on markets, consistent with weak dollar
- **−1:** EM underperforming US → capital flowing to safety, consistent with strong dollar

**Edge case — exact zero:** If EEM_SPY_ratio_20d_change == 0, treat as +1 (EM performing in line with US). Rationale: parity does not indicate risk-off.

### 5.5 Signal 4 — SAFE-HAVEN Flow (Binary: ±1)

**Purpose:** Compare gold vs bond performance to gauge the nature of safe-haven demand. Gold outperforming bonds suggests investors are hedging dollar weakness (gold as dollar alternative). Bonds outperforming gold suggests traditional risk-off (flight to yield, not dollar hedging).

**Instrument:** GLD (gold) and TLT (long bonds), combined as a ratio

**Calculation:**
```
GLD_TLT_ratio[t] = GLD_close[t] / TLT_close[t]
GLD_TLT_ratio_20d_change = (GLD_TLT_ratio[t] / GLD_TLT_ratio[t-20]) - 1
SAFEHAVEN = +1  if GLD_TLT_ratio_20d_change >= 0   (gold outperforming bonds → dollar hedging)
SAFEHAVEN = -1  if GLD_TLT_ratio_20d_change < 0    (bonds outperforming gold → risk-off / strong dollar)
```

**Interpretation:**
- **+1:** Gold outperforming bonds → investors are hedging against dollar weakness; consistent with weak-dollar regime
- **−1:** Bonds outperforming gold → classic risk-off flight to yield; consistent with strong-dollar regime

**Edge case — exact zero:** If GLD_TLT_ratio_20d_change == 0, treat as −1 (bonds and gold performing equally). Rationale: when both are flat, the default assumption is that traditional risk-off dynamics dominate.

### 5.6 Signal 5 — Daily Dollar Change (Continuous: z-scored, range −3 to +3)

**Purpose:** Capture short-term intensity of dollar movement. A large single-day dollar move can shift the composite score meaningfully, allowing the strategy to react to sudden dollar shocks ahead of the 20-day binary signals.

**Instrument:** UUP daily returns

**Calculation:**
```
UUP_daily_return[t] = (UUP_close[t] / UUP_close[t-1]) - 1

# Rolling mean and standard deviation over 63 trading days (~3 months)
mu = mean(UUP_daily_return[t-62 : t+1])
sigma = std(UUP_daily_return[t-62 : t+1])

UUP_z = (UUP_daily_return[t] - mu) / sigma

# Clamp to [-3, +3]
DAILY_DOLLAR_Z = max(-3.0, min(3.0, UUP_z))
```

**Interpretation:**
- **Negative DAILY_DOLLAR_Z:** Dollar falling today (more than usual) → adds positive contribution to composite (leans weak-dollar)
- **Positive DAILY_DOLLAR_Z:** Dollar rising today (more than usual) → adds negative contribution to composite (leans strong-dollar)
- **Near-zero DAILY_DOLLAR_Z:** Dollar move in line with recent volatility → minimal contribution

**Edge case — insufficient data:** If fewer than 21 observations available for z-score (minimum for meaningful standard deviation), fall back to raw daily return scaled by 10:
```
UUP_daily_return_scaled = UUP_daily_return[t] * 10
DAILY_DOLLAR_Z = max(-3.0, min(3.0, UUP_daily_return_scaled))
```

**Edge case — zero volatility:** If sigma == 0 (completely flat dollar for 63 days, practically impossible but handled), set DAILY_DOLLAR_Z = 0.0.

---

## 6. Composite Score & Regime Classification

### 6.1 Composite Score Formula

```
composite_score = DOLLAR + COMMODITY + GLOBAL + SAFEHAVEN + (DAILY_DOLLAR_Z * 0.15)
```

**Theoretical bounds:**
- **Minimum:** binary sum = −4, DAILY_DOLLAR_Z = +3.0 → −4 + 0.45 = −3.55. But if binary sum = −4 and DAILY_DOLLAR_Z = −3.0 → −4 − 0.45 = −4.45.
- **Maximum:** binary sum = +4, DAILY_DOLLAR_Z = −3.0 → +4 − 0.45 = +3.55. But if binary sum = +4 and DAILY_DOLLAR_Z = +3.0 → +4 + 0.45 = +4.45.

**Practical range:** composite ∈ [−4.45, +4.45], treated as de facto [−4.5, +4.5] for thresholding.

### 6.2 Regime Classification (4-Tier Discrete)

| Regime | Composite Threshold | Label | Primary Sentiment |
|---|---|---|---|
| **Strong USD** | composite ≤ −1.5 | Bearish risk | Dollar strong — all risk assets suppressed |
| **Mild USD** | −1.5 < composite < 0 | Mild defensive | Dollar leaning strong — cautious positioning |
| **Mild Weak USD** | 0 ≤ composite < 1.5 | Mild aggressive | Dollar leaning weak — growth tilt |
| **Strong Weak USD** | composite ≥ 1.5 | Full risk-on | Dollar weak — full EM/commodity/equity exposure |

### 6.3 Threshold Boundaries (Exact)

| Threshold | Operator | Value |
|---|---|---|
| Strong USD upper bound | ≤ | −1.5 |
| Mild USD upper bound | < | 0 |
| Mild Weak USD upper bound | < | 1.5 |
| Strong Weak USD lower bound | ≥ | 1.5 |

### 6.4 Regime Classification Edge Cases

| Scenario | composite | Classification | Rationale |
|---|---|---|---|
| composite == −1.5 exactly | −1.5 | Strong USD | Boundary included in Strong USD (≤ −1.5) |
| composite == 0 exactly | 0.0 | Mild Weak USD | Boundary 0 belongs to "aggressive" side (≥ 0) |
| composite == 1.5 exactly | 1.5 | Strong Weak USD | Boundary included in Strong Weak USD (≥ 1.5) |
| All signals flat / missing | N/A | Hold previous regime | Do not rebalance on data failure |

---

## 7. Allocation Rules

### 7.1 Target Allocation by Regime

#### Regime S (Strong USD) — composite ≤ −1.5

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Long Bonds | TLT | 70% | Primary safe haven |
| US Equities | SPY | 30% | Minimal defensive equity |
| Gold | GLD | 0% | Suppressed by strong dollar |
| EM Equities | EEM | 0% | Crushed by dollar debt burden |
| **Total** | | **100%** | |

**Character:** Defensive. Heavy bonds, minimal equities. Zero EM and zero gold. This is the "flight to quality" portfolio.

#### Regime M− (Mild USD / Mild Defensive) — −1.5 < composite < 0

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Long Bonds | TLT | 40% | Core safe haven |
| US Equities | SPY | 40% | Core equity |
| Gold | GLD | 10% | Token gold — dollar not yet decisively weak |
| EM Equities | EEM | 10% | Token EM — dollar not yet decisively strong |
| **Total** | | **100%** | |

**Character:** Balanced defensive. Bonds and equities share the core. Small satellite positions in gold and EM as early-positioning for a potential regime shift.

#### Regime M+ (Mild Weak USD / Mild Aggressive) — 0 ≤ composite < 1.5

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Equities | SPY | 40% | Core equity |
| EM Equities | EEM | 20% | EM is now attractive — growth tilt |
| Gold | GLD | 20% | Dollar hedge |
| US Long Bonds | TLT | 20% | Reduced — inflation fears weigh on bonds |
| **Total** | | **100%** | |

**Character:** Balanced aggressive. Equities dominate. Gold and EM get meaningful allocations. Bonds reduced to a minority position.

#### Regime W (Strong Weak USD / Full Risk-On) — composite ≥ 1.5

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Equities | SPY | 50% | Core risk-on |
| EM Equities | EEM | 30% | High conviction — dollar weakness fuels EM |
| Gold | GLD | 20% | Dollar hedge / inflation hedge |
| US Long Bonds | TLT | 0% | Zero — dollar weakness and inflation headwind |
| **Total** | | **100%** | |

**Character:** Maximum risk-on. Zero bonds. Maximum EM and equity exposure. Gold held for dollar-hedge and tail-risk protection.

### 7.2 Allocation Edge Cases

| Scenario | Action |
|---|---|
| composite exactly at boundary | Assign to the more defensive regime (per Section 6.4) |
| Composite score temporarily unavailable | Hold last allocation — do not rebalance |
| First-ever signal (no prior regime) | Classify from scratch using current composite |
| Single-asset allocation hits 0% | Sell entire position; do not maintain residual holdings |
| All assets held | Yes — exactly 4 positions always (some may be 0%) |

### 7.3 Prohibited States

| State | Reason |
|---|---|
| Cash holdings > 0% | Always fully invested — no cash buffer |
| Leverage > 1.0× | No margin — gross notional = NAV |
| Short positions | No short selling — all positions long only |
| Derivatives | No options, futures, or swaps |

### 7.4 Position Sizing Rules

- All allocations are **percentage of total portfolio NAV**
- No fractional shares rounding if using whole-share brokerage: round to nearest share, remainder held as cash residual (<0.1% expected)
- In cash-settled environments (paper trading / backtesting): allocations are exact decimals

---

## 8. Rebalancing Rules

### 8.1 Rebalance Trigger

**Condition:** Composite score recalculated daily at EOD.

- **Daily rebalance:** If the regime changes (different tier from previous EOD), execute full rebalance to target allocations.
- **Intra-regime drift:** If composite fluctuates within the same tier but crosses boundaries in either direction, the allocation does NOT change.
- **No-change days:** If regime is unchanged, do not trade.

### 8.2 Rebalance Frequency

| Metric | Value |
|---|---|
| Maximum rebalances per year | ~260 (daily, but regime changes ~40–80 times/yr) |
| Expected rebalances per year | 40–80 |
| Minimum time between rebalances | 1 trading day |
| Cooldown after rebalance | None — can rebalance again next day if regime flips back |

### 8.3 Rebalance Execution

**Order Type:** Market-on-close (MOC) or next-day-open, depending on execution platform.

**Execution Priority:**
1. Sell positions going to 0% (highest priority — free up capital)
2. Reduce overweight positions
3. Add to underweight positions

**Slippage Assumption:** 5 bps per leg (conservative for these highly liquid ETFs).

### 8.4 Rebalance Edge Cases

| Scenario | Action |
|---|---|
| Single-day regime flip (S → W → S) | Execute both rebalances — the second flips back |
| Regime unchanged 50+ consecutive days | No trades; monitor regime shift only |
| Holiday / non-trading day | Skip; regime assessment resumes next trading day |
| Partial fills on rebalance | Log warning; retry remaining fills next day |

### 8.5 Turnover Controls

No explicit turnover cap — turnover is a natural consequence of regime changes. Historical simulation expected to show:
- **Low turnover months:** 10–20% (stable regime periods)
- **High turnover months:** 40–80% (regime oscillation around boundaries)

---

## 9. Risk Management

### 9.1 Portfolio-Level Risk Limits

| Metric | Limit | Action if Breached |
|---|---|---|
| Max single-asset exposure | 70% (TLT in Strong USD) | Hard limit by construction |
| Min single-asset exposure | 0% (by construction) | N/A — built into allocation model |
| Max equity exposure (SPY+EEM) | 80% (Regime W: 50%+30%) | Hard limit by construction |
| Max EM exposure | 30% (Regime W) | Hard limit by construction |
| Max bond exposure | 70% (Regime S: TLT only) | Hard limit by construction |
| Max gold exposure | 20% (Regimes M+ and W) | Hard limit by construction |

### 9.2 Drawdown Controls

| Drawdown Threshold | Action |
|---|---|
| Portfolio drawdown > 15% (peak-to-trough) | Review regime classification thresholds; consider tightening |
| Portfolio drawdown > 25% | Full strategy review; potential suspension |
| Any single asset drawdown > 40% | Investigate for structural break (delisting, tracking error, etc.) |

### 9.3 Volatility Controls

- No explicit volatility targeting — the allocations are regime-dependent and implicitly control risk via asset class weights.
- Monitor rolling 63-day portfolio volatility. If it exceeds 25% annualized, flag for review.

### 9.4 Correlation Regime Detection

- If SPY, TLT, GLD, and EEM all decline simultaneously over a 5-day window (>2% each), flag a "correlation-1 event" — this suggests a liquidity crisis where all correlations go to 1, breaking the regime model. Temporarily move to 100% TLT until correlations normalize.

### 9.5 Liquidity Risk

All four traded ETFs are among the most liquid in their categories. No position exceeds 5% of average daily dollar volume at any target allocation size under $50M AUM.

### 9.6 Regime-Specific Risk Notes

| Regime | Key Risk | Mitigation |
|---|---|---|
| Strong USD | Bond selloff (rates spike) | GLD/EEM at 0% limits cross-contagion; TLT has rate risk |
| Mild USD | Regime whipsaw (boundary crossing) | Frequent but small rebalances — limited damage per event |
| Mild Weak USD | EM selloff on sudden dollar reversal | 20% EEM maximum — contained downside |
| Strong Weak USD | Sudden dollar reversal (taper tantrum) | GLD (20%) as hedge; TLT (0%) avoids bond carnage |

---

## 10. Performance Expectations

### 10.1 Return Targets

| Metric | Target | Notes |
|---|---|---|
| Annualized return | 10–14% | Regime-driven tactical allocation premium |
| Annualized volatility | 12–16% | Multi-asset diversification dampens vol |
| Sharpe ratio (RFR=5%) | 0.6–0.9 | Pre-cost; expect after-cost ~0.5–0.8 |
| Max drawdown | <25% | Defensive regimes should limit tail risk |
| Win rate | 55–62% | Regime changes produce asymmetric bets |
| Profit factor | 1.4–1.8 | Wins larger than losses due to trend capture |

### 10.2 Benchmark

Primary benchmark: **60/40 portfolio** (60% SPY / 40% TLT, rebalanced monthly)

Secondary benchmark: **Risk-parity** (25% each SPY/TLT/GLD/EEM, rebalanced monthly)

### 10.3 Backtesting Requirements

| Parameter | Value |
|---|---|
| Minimum backtest window | 10 years (2016–2026) |
| Preferred backtest window | 20 years (2006–2026) — includes GFC, taper tantrum, COVID, 2022 rate cycle |
| Data granularity | Daily OHLCV |
| Cost model | 5 bps per trade, 1 bp daily financing (for leveraged scenarios if applicable) |
| Slippage model | 5 bps per leg |

### 10.4 Key Risk Periods to Test

| Period | Event | Expected Behavior |
|---|---|---|
| 2008 GFC | Dollar surged (risk-off), EM collapsed | Strong USD regime → 70% TLT, 0% EEM — protective |
| 2011–2012 | Euro crisis, dollar strong | Strong USD regime protective |
| 2014–2015 | Fed taper, dollar rally | Strong USD regime protective |
| 2017 | Dollar weakness, EM rally | Weak USD regime → captured EM upside |
| 2020 COVID | Dollar spike then collapse | Regime flip from S → W quickly captured |
| 2021–2022 | Dollar mega-strength (rate hikes) | Strong USD regime protective; GLD/EEM underweighted |
| 2023–2024 | Dollar oscillation | Frequent regime changes — test turnover cost |

---

## 11. Implementation Notes

### 11.1 Dependencies

| Library | Version | Purpose |
|---|---|---|
| pandas | ≥1.5 | Data manipulation |
| numpy | ≥1.24 | Numerical computation |
| yfinance | ≥0.2 | Price data (or alternative data fetcher) |
| python-dotenv | ≥1.0 | Configuration management |

### 11.2 File Structure

```
quantloop/strategies/s535/
  spec.md              ← this file
  signals.py           ← signal computation
  composite.py         ← composite score + regime classification
  allocation.py        ← target allocation by regime
  rebalance.py         ← rebalance execution logic
  backtest.py          ← backtesting harness
  config.yaml          ← strategy parameters
```

### 11.3 Configuration Parameters (config.yaml)

```yaml
strategy:
  id: s535
  name: USDCYCLE

signals:
  binary_window: 20
  z_score_window: 63
  z_clamp: 3.0
  z_weight: 0.15

regimes:
  strong_usd:
    threshold: -1.5
    operator: le
  mild_usd:
    lower: -1.5
    upper: 0
    lower_operator: gt
    upper_operator: lt
  mild_weak_usd:
    lower: 0
    upper: 1.5
    lower_operator: ge
    upper_operator: lt
  strong_weak_usd:
    threshold: 1.5
    operator: ge

allocations:
  strong_usd:
    TLT: 0.70
    SPY: 0.30
    GLD: 0.00
    EEM: 0.00
  mild_usd:
    TLT: 0.40
    SPY: 0.40
    GLD: 0.10
    EEM: 0.10
  mild_weak_usd:
    TLT: 0.20
    SPY: 0.40
    GLD: 0.20
    EEM: 0.20
  strong_weak_usd:
    TLT: 0.00
    SPY: 0.50
    GLD: 0.20
    EEM: 0.30

data:
  tickers:
    traded: [SPY, TLT, GLD, EEM]
    signal_only: [UUP, DBC]
  min_lookback: 252
  preferred_lookback: 504

risk:
  max_drawdown_review: 0.15
  max_drawdown_suspend: 0.25
  max_volatility_warning: 0.25
  correlation_1_event_threshold: 0.02

execution:
  slippage_bps: 5
  order_type: market_on_close
```

### 11.4 Pseudo-Code (Daily Run)

```
def run_daily():
    prices = fetch_prices([SPY, TLT, GLD, EEM, UUP, DBC], lookback=504)

    # Compute binary signals
    dollar_binary = compute_20d_momentum_binary(prices['UUP'], direction='falling_is_plus')
    commodity_binary = compute_20d_momentum_binary(prices['DBC'], direction='rising_is_plus')
    em_spy_ratio = prices['EEM'] / prices['SPY']
    global_binary = compute_20d_momentum_binary(em_spy_ratio, direction='rising_is_plus')
    gld_tlt_ratio = prices['GLD'] / prices['TLT']
    safehaven_binary = compute_20d_momentum_binary(gld_tlt_ratio, direction='rising_is_plus')

    # Compute continuous signal
    daily_dollar_z = compute_zscore(prices['UUP'].pct_change(), window=63, clamp=3.0)

    # Composite score
    binary_sum = dollar_binary + commodity_binary + global_binary + safehaven_binary
    composite = binary_sum + (daily_dollar_z * 0.15)

    # Regime classification
    regime = classify_regime(composite)

    # Target allocation
    targets = get_allocation(regime)

    # Rebalance if regime changed
    if regime != previous_regime:
        execute_rebalance(targets)
```

---

## 12. Edge Cases, Tiebreakers & Fallbacks

### 12.1 Signal-Level Edge Cases

| # | Edge Case | Rule | Rationale |
|---|---|---|---|
| 1 | UUP_20d_return == 0 | DOLLAR = −1 (strong dollar) | Flat dollar does not signal weakness |
| 2 | DBC_20d_return == 0 | COMMODITY = +1 | Flat commodities do not contradict weak dollar |
| 3 | EEM_SPY_ratio_20d_change == 0 | GLOBAL = +1 | Parity between EM and US is not risk-off |
| 4 | GLD_TLT_ratio_20d_change == 0 | SAFEHAVEN = −1 | When both safe havens are flat, default to risk-off |
| 5 | sigma == 0 for UUP z-score | DAILY_DOLLAR_Z = 0.0 | Zero volatility means no signal |
| 6 | Insufficient data for z-score (<21 obs) | Fallback: raw_return × 10, clamped | Gives some signal rather than none |
| 7 | All prices flat for 20+ days | All binary signals = 0? No — treat as −1 per edge case rules above | Avoids undefined state |

### 12.2 Composite Score Edge Cases

| # | Edge Case | Rule | Rationale |
|---|---|---|---|
| 1 | composite == −1.5 exactly | Regime = Strong USD | Boundary inclusive on the defensive side |
| 2 | composite == 0 exactly | Regime = Mild Weak USD | Boundary inclusive on the aggressive side |
| 3 | composite == 1.5 exactly | Regime = Strong Weak USD | Boundary inclusive on the aggressive side |
| 4 | composite out of [−4.5, +4.5] range | Clamp to range | Numerical safety; should not occur in practice |
| 5 | NaN composite | Hold previous regime | Not safe to classify without valid composite |

### 12.3 Allocation Edge Cases

| # | Edge Case | Rule | Rationale |
|---|---|---|---|
| 1 | Allocation rounds to 0 but > 0 | Execute sell | Clean slate per regime allocation |
| 2 | TLT → 0% in Regime W | Full liquidation | Dollar weak → bonds are a liability |
| 3 | EEM → 0% in Regime S | Full liquidation | Dollar strong → EM debt burden crushes returns |
| 4 | GLD → 0% in Regime S | Full liquidation | Dollar strong → gold has no bid |
| 5 | SPY allocation varies 30%–50% | Always held | US equities are always part of the portfolio |
| 6 | Allocation rounding (whole shares) | Round to nearest; residual cash < 0.1% | Minimizes tracking error |

### 12.4 Data Fallbacks (Priority Order)

| Level | Condition | Action |
|---|---|---|
| 1 | All data valid | Compute signals normally |
| 2 | UUP or DBC data missing | Skip that signal (treat as 0 contribution to binary sum); still compute other signals |
| 3 | One traded ETF data missing | Hold prior allocation for that asset; rebalance others |
| 4 | Two+ traded ETFs data missing | Hold entire allocation; do not rebalance |
| 5 | All data missing for 3+ consecutive days | Flag critical alert; maintain last known allocation |
| 6 | Connection failure | Use cached data (max 2 days stale) |

### 12.5 Regime Whipsaw — Tiebreaker Rules

**Scenario:** composite oscillates around ±1.5 or 0 multiple days in a row, causing regime whipsaw (e.g., Strong USD → Mild USD → Strong USD → Mild USD over 4 days).

**Rule:** Apply a 2-day confirmation filter. A regime change is only executed if the new regime persists for 2 consecutive daily readings.

**Exception:** If the composite crosses two tiers in one day (e.g., from Strong USD directly to Mild Weak USD — composite jumps from −2.0 to +0.5), the 2-day confirmation is waived and the rebalance executes immediately. This prevents lag during violent regime transitions.

### 12.6 First-Run / Cold-Start Rules

| Scenario | Action |
|---|---|
| No prior regime history | Classify immediately from first composite score |
| No z-score history | Use raw return fallback for DAILY_DOLLAR_Z |
| Insufficient 20-day data | Do not trade until 20 days of data accumulated |
| Insufficient 63-day data for z-score | Use raw return fallback with 10× scaling |

### 12.7 Holiday / Weekend Rules

- Signals are computed using the most recent trading day's closing prices
- If today is Monday, the 20-day lookback uses close from 20 trading days prior (which may be ~28 calendar days ago)
- Rebalances are executed on the next trading day following a regime change signal

### 12.8 Catastrophic Fallback

If all data sources fail for 5+ consecutive trading days:
1. Move to 100% TLT (maximum safe haven)
2. Flag critical alert to strategy administrator
3. Resume normal operation when data flow is restored

Rationale: In an extended data blackout, a defensive posture minimizes unknown risk.

---

## 13. References & Related Strategies

### 13.1 Academic / Industry References

- **Dollar and Emerging Markets:** Eichengreen, B. (2004). "The Dollar and the New Bretton Woods System." The dollar cycle's impact on EM capital flows is a well-documented transmission mechanism.
- **Commodities and the Dollar:** Akram, Q.F. (2009). "Commodity Prices, Interest Rates and the Dollar." Shows the inverse relationship between USD and commodity prices.
- **Gold as Dollar Hedge:** Capie, F., Mills, T.C., & Wood, G. (2005). "Gold as a Hedge against the Dollar." Demonstrates gold's role as a dollar alternative.
- **Regime-Switching in Asset Allocation:** Ang, A. & Bekaert, G. (2002). "International Asset Allocation with Regime Shifts." Provides theoretical foundation for regime-based multi-asset allocation.

### 13.2 Related Quantloop Strategies

| Strategy | Relationship |
|---|---|
| s530 — US Inflation Regime (INFLCYCLE) | Complementary — inflation and dollar cycles are related but distinct. s535 focuses on dollar; s530 on inflation. Can be run side-by-side for comparison. |
| s540 — Global Risk Appetite (RISKCYCLE) | Dollar regime is a driver of risk appetite; s535's regime classification feeds into risk-on/risk-off sentiment. |

### 13.3 Symbol Lookup

| Ticker | ISIN | Inception | ER | AUM |
|---|---|---|---|---|
| SPY | US78462F1030 | 1993-01-22 | 0.09% | ~$500B |
| TLT | US4642874322 | 2002-07-22 | 0.15% | ~$40B |
| GLD | US78463V1070 | 2004-11-18 | 0.40% | ~$60B |
| EEM | US4642872342 | 2003-04-07 | 0.68% | ~$20B |
| UUP | US46138H7060 | 2007-02-20 | 0.75% | ~$1.5B |
| DBC | US46138B1026 | 2006-02-03 | 0.89% | ~$3B |

---

## 14. Version History & Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0.0 | 2026-06-15 | Agent (Quantloop) | Initial spec — 14-section template; full signal, regime, allocation, and risk specifications |
| | | | |

---

**END OF SPEC — s535 (USDCYCLE)**
