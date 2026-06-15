# s536 — Cross-Asset Correlation Regime (CORREG)

**Status:** Draft  
**Version:** 1.0.0  
**Last Updated:** 2026-06-15  
**Author:** Agent (Quantloop)

---

## 1. Strategy Overview

| Field | Value |
|---|---|
| **Strategy ID** | s536 |
| **Short Name** | CORREG |
| **Long Name** | Cross-Asset Correlation Regime |
| **Asset Class** | Multi-asset (equities, bonds, commodities) |
| **Trading Frequency** | Daily (EOD rebalance triggered by regime change) |
| **Avg Holding Period** | 5–30 days (regime-dependent) |
| **Max Positions** | 3 (SPY, TLT, GLD) |
| **Gross Exposure** | 100% (fully invested; leverage = 1.0×) |
| **Net Exposure** | Varies by regime (10%–100% equities) |
| **Inception** | TBD |

Cross-asset correlations are not static — they cluster into distinct regimes (low-vol, risk-on, stress, crisis). By computing the rolling correlation structure of 8 major asset classes and reducing to principal components (PCA), we identify which regime we are in. Each regime has a distinct allocation. The key innovation: PCA is performed on the **correlation matrix** (not covariance), removing scale effects and focusing purely on structural relationships between assets.

---

## 2. Strategy Rationale / Investment Thesis

### 2.1 Correlation Structure Encodes the Macro Regime

Asset class correlations are driven by the prevailing macro regime:

- **Risk-On / Growth (Q1):** All risk assets move together, bonds diverge. Equities, EM, commodities, and credit all rally. TLT either falls (inflation concerns) or is flat. The first PC loads positively on SPY, EEM, DBC, HYG and negatively on TLT, SHY.
- **Risk-On / Inflation (Q2):** Risk assets rally but commodities (DBC, GLD) lead. TLT sells off on rising inflation expectations. The second PC captures the growth/inflation tension — positive loading on commodities, negative on bonds.
- **Risk-Off / Defensive (Q3):** Flight to quality. TLT and SHY rally. SPY and EEM decline. HYG credit spreads widen. GLD can be flat or slightly up (real rate hedge). UUP strengthens. The first PC flips sign — now positively loaded on bonds, negatively on risk.
- **Risk-Off / Stress (Q4):** Everything sells off except UUP. Correlations compress toward 1.0. TLT may rally initially (flight to quality) then sell off (liquidity crunch). This is the crisis regime — the second PC captures the panic bid for dollars.

### 2.2 Why PCA on Correlations (Not Covariances)

| Aspect | Covariance PCA | Correlation PCA |
|---|---|---|
| Scale sensitivity | Dominated by high-vol assets (e.g., EEM, HYG) | All assets contribute equally |
| Interpretation | Factor loadings mix vol and correlation | Pure structural relationships |
| Stability | Changes when vol changes even if relationships are stable | Stable representation of relational structure |
| **Our choice** | ❌ | ✅ **CORREG** |

Using correlations removes the scaling effect of asset-specific volatilities (e.g., HYG naturally has higher vol than SHY). This focuses PCA on detecting **structural shifts in how assets co-move** — the true signal of a regime change.

### 2.3 Why 8 Assets for Signal, 3 for Allocation

The 8-asset signal universe spans the major forces:

| Force | Assets |
|---|---|
| Equities (US) | SPY |
| Equities (EM) | EEM |
| Bonds (long) | TLT |
| Bonds (short) | SHY |
| Commodities | DBC |
| Gold | GLD |
| Credit | HYG |
| Dollar | UUP |

Allocation is restricted to SPY, TLT, and GLD — the most liquid, low-cost, and directly tradeable expressions of the regime view. EEM, DBC, HYG, SHY, and UUP contribute to regime detection but are not traded due to higher costs, tracking error, or directional complexity.

### 2.4 Why This Generates Enough Trades

Regime transitions happen more frequently than individual asset trends:
- PC1 sign changes (risk-on ↔ risk-off) occur ~8–15 times per year
- PC2 sign changes (growth ↔ inflation / stress) occur ~10–20 times per year
- Combined quadrant transitions: ~15–30 rebalance events per year
- This is sufficient for meaningful alpha without overtrading

---

## 3. Trading Universe

### 3.1 Candidate Universe — Traded Instruments

Exactly 3 ETFs, selected for liquidity, low expense ratios, and pure-factor exposure:

| # | Ticker | Name | Asset Class | Primary Role |
|---|---|---|---|---|
| 1 | SPY | SPDR S&P 500 ETF Trust | US Large-Cap Equity | Core equity exposure |
| 2 | TLT | iShares 20+ Year Treasury Bond ETF | US Long-Term Treasuries | Safe-haven / rate hedge |
| 3 | GLD | SPDR Gold Shares | Physical Gold | Dollar hedge / inflation hedge |

### 3.2 Signal-Only Instruments (Not Traded)

These 5 assets contribute to the correlation matrix and PCA but are never allocated to:

| # | Ticker | Name | Asset Class | Role in Correlation Matrix |
|---|---|---|---|---|
| 1 | DBC | Invesco DB Commodity Index Tracking Fund | Broad Commodities | Captures commodity cycle in PC2 (inflation/growth) |
| 2 | EEM | iShares MSCI Emerging Markets ETF | EM Equity | High-beta risk-on exposure for PC1 |
| 3 | HYG | iShares iBoxx High Yield Corporate Bond ETF | US High-Yield Credit | Credit cycle sensitivity for PC1 and PC2 |
| 4 | SHY | iShares 1-3 Year Treasury Bond ETF | US Short-Term Treasuries | Rate-neutral safe-haven for PC1 |
| 5 | UUP | Invesco DB USD Index Bullish Fund | US Dollar | Dollar direction for PC2 (stress/crisis) |

### 3.3 Liquidity Requirements

All eight ETFs have:
- Average daily volume > 500K shares
- Average daily dollar volume > $20M
- Bid-ask spread < 0.10%
- Continuous trading history since at least 2008

### 3.4 Universe Rules

| Rule | Detail |
|---|---|
| **Maximum positions** | 3 (hard limit — SPY, TLT, GLD) |
| **Minimum positions** | 1 (may go to 100% SPY or 100% TLT; GLD only held in Q2 and Q4) |
| **Addition criteria** | None — universe is fixed |
| **Removal criteria** | Only if an ETF is delisted, merged, or has structural tracking error > 2%/yr |
| **Rebalance trigger** | Regime quadrant change (PC1 or PC2 sign change — see Section 8) |
| **Sector constraints** | N/A — each ETF represents a distinct macro factor |

---

## 4. Data Sources & Processing

### 4.1 Primary Data Sources

| Data | Source | Ticker | Priority |
|---|---|---|---|
| Daily OHLCV — SPY | Yahoo Finance | SPY | Primary |
| Daily OHLCV — TLT | Yahoo Finance | TLT | Primary |
| Daily OHLCV — GLD | Yahoo Finance | GLD | Primary |
| Daily OHLCV — DBC | Yahoo Finance | DBC | Primary |
| Daily OHLCV — EEM | Yahoo Finance | EEM | Primary |
| Daily OHLCV — HYG | Yahoo Finance | HYG | Primary |
| Daily OHLCV — SHY | Yahoo Finance | SHY | Primary |
| Daily OHLCV — UUP | Yahoo Finance | UUP | Primary |

### 4.2 Data Requirements

| Requirement | Value |
|---|---|
| Minimum lookback | 252 trading days (1 year) — needed for stable 60d rolling correlations |
| Recommended lookback | 756 trading days (3 years) for robust PCA with warm-start |
| Correlation window | 60 trading days rolling (~3 months) |
| PCA recalculation | Daily (each EOD, recompute full 60d correlation matrix → eigen-decompose) |
| Data freshness | EOD data must include the most recent close |
| Adjustments | Split/dividend-adjusted close prices only |

### 4.3 Data Quality Rules

| Check | Action |
|---|---|
| Missing price for any signal asset | Exclude that asset from correlation matrix; compute PCA on remaining assets (minimum 6 required) |
| Missing price for any traded asset | Skip rebalance, hold prior allocation |
| Stale price (>1 day old) | Skip rebalance, log warning |
| Zero or negative price | Skip rebalance, flag critical error |
| >5% single-day gap (suspect split/dividend) | Verify adjusted close; if confirmed, proceed |
| All 8 assets must have valid data for full PCA | If fewer than 6 assets have data, entire strategy holds |

### 4.4 Fallback Data Chain

1. **Primary:** Yahoo Finance (via yfinance or equivalent)
2. **Secondary:** Alpaca Market Data (if available)
3. **Tertiary:** Cached last-known prices (max 2 days stale)
4. **Final fallback:** Hold current allocation — do not rebalance

---

## 5. Signals — Specification

### 5.1 Signal Architecture Overview

The strategy uses a **single composite signal** derived from the eigenstructure of the 8×8 rolling correlation matrix:

1. **Rolling correlation matrix** — 60 trading days, 8 assets → 28 unique pairwise correlations
2. **PCA decomposition** — extract eigenvalues and eigenvectors
3. **PC1 score** — first principal component (z-scored) = "risk-on/off" factor
4. **PC2 score** — second principal component (z-scored) = "growth/inflation" factor
5. **Regime quadrant** — determined by signs of z-scored PC1 and PC2

All signals recomputed daily at EOD.

### 5.2 Step 1 — Rolling Correlation Matrix

**Purpose:** Capture the current structural relationships between all 8 assets.

**Calculation:**

```
For each pair of assets (i, j) over the trailing 60 trading days [t-59, t]:
    r_ij = Pearson correlation coefficient(returns_i[0:60], returns_j[0:60])

Where:
    returns[t] = ln(close[t] / close[t-1])

Result: R(t) = 8×8 symmetric correlation matrix
Diagonal elements = 1.0
Off-diagonal ∈ [-1.0, +1.0]
```

**Edge case — insufficient history:** If fewer than 21 trading days of data exist for any asset (minimum for meaningful correlation), exclude that asset from the matrix. If fewer than 6 assets remain, do not compute PCA — hold prior regime.

**Edge case — constant returns:** If an asset has zero variance over the 60-day window (identical close every day — practically impossible but handled), set its correlation with all other assets to 0.0 and flag a warning.

**Edge case — missing data within window:** If one or more days are missing within the 60-day window, compute correlations using pairwise-complete observations (minimum 15 overlapping observations required per pair). If fewer than 15, set correlation to 0.0.

### 5.3 Step 2 — PCA Decomposition

**Purpose:** Reduce the 28-dimensional correlation structure to 2 interpretable factors.

**Calculation:**

```
R(t) = 8×8 correlation matrix

# Eigen-decomposition
eigenvalues, eigenvectors = eigendecompose(R(t))

# Sort by descending eigenvalue
idx = argsort(eigenvalues, descending=True)
eigenvalues = eigenvalues[idx]
eigenvectors = eigenvectors[:, idx]  # columns are eigenvectors

# Variance explained
var_explained_k = eigenvalues[k] / sum(eigenvalues)

# First two PCs
PC1_eigenvector = eigenvectors[:, 0]   # 8×1 loading vector
PC2_eigenvector = eigenvectors[:, 1]   # 8×1 loading vector

# Project current returns onto PC loadings
current_returns = 8-element vector of today's returns for each asset
PC1_raw = dot(current_returns, PC1_eigenvector)
PC2_raw = dot(current_returns, PC2_eigenvector)
```

**Expected variance decomposition:**
- PC1: ~30–40% of total variance (risk-on/off factor)
- PC2: ~12–20% of total variance (growth/inflation factor)
- PC3–PC8: remaining ~45–55% (idiosyncratic noise — discarded)

**Edge case — degenerate correlation matrix:** If R(t) is not positive semi-definite (numerical issues, highly correlated subsets), apply nearest-PSD correction (Higham, 1988 algorithm) before eigen-decomposition. Log the correction.

**Edge case — equal eigenvalues:** If PC1 and PC2 eigenvalues are within 0.01 of each other (near-degenerate), warn of ambiguous rotation. This can happen in crisis when correlations compress toward 1.0.

### 5.4 Step 3 — Z-Scoring

**Purpose:** Normalize PCs to standard normal for sign-based quadrant classification.

**Calculation:**

```
# Rolling moments over trailing 252 trading days (~1 year)
mu_PC1 = mean(PC1_raw[t-251 : t+1])
sigma_PC1 = std(PC1_raw[t-251 : t+1])

mu_PC2 = mean(PC2_raw[t-251 : t+1])
sigma_PC2 = std(PC2_raw[t-251 : t+1])

# Z-scores
PC1_z = (PC1_raw[t] - mu_PC1) / sigma_PC1
PC2_z = (PC2_raw[t] - mu_PC2) / sigma_PC2
```

**Edge case — insufficient history:** If fewer than 63 observations are available for z-score moments, fall back to:
```
PC1_z = PC1_raw[t] / (estimated_sigma)   # estimated_sigma = sqrt(trace(R)/8) or 1.0 if unavailable
PC2_z = PC2_raw[t] / (estimated_sigma)
```

**Edge case — zero volatility:** If sigma_PC1 == 0 (PC1 constant for 252 days), set PC1_z = 0.0. Same for PC2.

### 5.5 Step 4 — Quadrant Classification

**Purpose:** Map the 2D PC space into 4 discrete regimes.

**Calculation:**

```
if PC1_z >= 0 and PC2_z >= 0:
    regime = Q1  # "Risk-On + Growth"
elif PC1_z >= 0 and PC2_z < 0:
    regime = Q2  # "Risk-On + Inflation"
elif PC1_z < 0 and PC2_z >= 0:
    regime = Q3  # "Risk-Off + Defensive"
else:  # PC1_z < 0 and PC2_z < 0
    regime = Q4  # "Risk-Off + Stress"
```

**Boundary definition:**

| Boundary | PC1_z == 0 | PC2_z == 0 |
|---|---|---|
| Q1 boundary | PC1_z ≥ 0 AND PC2_z ≥ 0 | PC1_z ≥ 0 |
| Q2 boundary | PC1_z ≥ 0 AND PC2_z < 0 | PC2_z < 0 |
| Q3 boundary | PC1_z < 0 AND PC2_z ≥ 0 | PC1_z < 0 |
| Q4 boundary | PC1_z < 0 AND PC2_z < 0 | PC2_z < 0 |

**Important:** Exact zero on either axis is assigned to the "positive" or "non-negative" quadrant. Specifically:
- PC1_z == 0.0 → treated as Q1 or Q2 (depends on PC2 sign)
- PC2_z == 0.0 → treated as Q1 or Q3 (depends on PC1 sign)
- PC1_z == 0.0 AND PC2_z == 0.0 → treated as Q1 (default risk-on/growth)

**Rationale for zero handling:** Zero PC means the current projection is at the long-term mean — neither strongly positive nor negative. The default is to treat this as continuation of the prevailing regime (whichever was last), but for initial classification, it defaults to the optimistic quadrant (Q1).

### 5.6 Additional Metrics (Monitoring Only)

These are not used for quadrant classification but are available for risk monitoring and performance analysis:

- **PC1 dominance:** `eigenvalues[0] / sum(eigenvalues)` — fraction of variance captured by PC1. Higher values (>0.5) suggest a single dominant factor (crisis). Lower values (<0.25) suggest diversified/no clear regime.
- **Correlation dispersion:** Standard deviation of the 28 off-diagonal correlation coefficients. Higher values (>0.4) suggest diverse relationships. Lower values (<0.1) suggest correlation compression (crisis).
- **Regime confidence:** `max(abs(PC1_z), abs(PC2_z))` — distance from origin. Higher values (>1.5) indicate strong regime signal. Lower values (<0.5) indicate noisy/transitional state.

---

## 6. Composite Score & Regime Classification

### 6.1 Composite Score / No Composite Needed

Unlike strategies that blend multiple independent signals, CORREG has a **single signal** — the (PC1_z, PC2_z) pair from PCA. The "composite score" is the 2D vector:

```
composite_vector = (PC1_z, PC2_z)
```

The regime classification is purely geometric:

| Quadrant | Condition | Regime Name |
|---|---|---|
| Q1 | PC1_z ≥ 0, PC2_z ≥ 0 | Risk-On + Growth |
| Q2 | PC1_z ≥ 0, PC2_z < 0 | Risk-On + Inflation |
| Q3 | PC1_z < 0, PC2_z ≥ 0 | Risk-Off + Defensive |
| Q4 | PC1_z < 0, PC2_z < 0 | Risk-Off + Stress |

### 6.2 No Score Thresholds (Geometric, Not Metric)

There are no composite-score thresholds. The regime is determined **entirely by the signs** of the two z-scored PCs. This is a quadrant-based system, not a threshold-based one.

### 6.3 Regime Strength (Secondary Metric)

While not used for classification, the **Mahalanobis distance** of the (PC1_z, PC2_z) vector from the origin provides a measure of regime conviction:

```
regime_strength = sqrt(PC1_z**2 + PC2_z**2)
```

| regime_strength | Interpretation |
|---|---|
| 0.0 – 0.5 | Weak / transitional — regime is not well-defined |
| 0.5 – 1.0 | Moderate — regime is present but noisy |
| 1.0 – 2.0 | Strong — clear regime signal |
| > 2.0 | Extreme — very high conviction regime |

When `regime_strength < 0.5`, the regime classification is considered **noisy**. See Section 12.2 for tiebreaker rules in this zone.

### 6.4 Regime Classification Edge Cases

| Scenario | PC1_z | PC2_z | Classification | Rationale |
|---|---|---|---|---|
| PC1_z == 0 exactly | 0.0 | +0.8 | Q1 (Risk-On + Growth) | Zero PC1 = mean risk-on/off → default risk-on |
| PC2_z == 0 exactly | +0.5 | 0.0 | Q1 (Risk-On + Growth) | Zero PC2 = mean growth/inflation → default growth |
| Both zero | 0.0 | 0.0 | Q1 (Risk-On + Growth) | Origin = completely neutral → default optimistic |
| regime_strength < 0.5 | Any | Any | Hold prior regime | Noisy — do not rebalance on weak signal (see Section 12.2) |

---

## 7. Allocation Rules

### 7.1 Target Allocation by Regime

#### Regime Q1 — Risk-On + Growth (PC1_z ≥ 0, PC2_z ≥ 0)

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Equities | SPY | 100% | Maximum risk-on — equities lead in growth regime |
| US Long Bonds | TLT | 0% | Bonds sell off or underperform in growth environment |
| Gold | GLD | 0% | Gold has no bid when risk appetite is high and growth is strong |
| **Total** | | **100%** | |

**Character:** Maximum equity exposure. Zero bonds, zero gold. Pure growth-leaning portfolio.

**Macro rationale:** In Q1, correlation structure shows risk assets moving together and bonds diverging. The economy is growing, inflation expectations are manageable, and equities benefit from rising earnings. TLT is a headwind (rates rising or feared to rise). GLD lacks urgency as a hedge.

---

#### Regime Q2 — Risk-On + Inflation (PC1_z ≥ 0, PC2_z < 0)

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Equities | SPY | 60% | Core risk-on |
| Gold | GLD | 40% | Inflation hedge — commodities and gold lead |
| US Long Bonds | TLT | 0% | Bonds destroyed by rising inflation / rates |
| **Total** | | **100%** | |

**Character:** Equities with heavy gold hedge. Zero bonds. Inflation-protected tilt.

**Macro rationale:** In Q2, PC1 is positive (risk-on) but PC2 is negative (inflationary pressure). The correlation matrix shows commodities and gold loading heavily on PC2. TLT declines as breakeven inflation widens. SPY can still rally but gold outperforms. This is the "commodity bull, bond bear" regime.

**Allocation justification for SPY (60%) vs GLD (40%):**
- SPY is the core risk-on asset but is threatened by rising rates / input costs
- GLD provides inflation protection and benefits from real rate compression
- GLD weight (40%) is higher than typical to reflect that PC2 < 0 is specifically an inflation signal
- TLT at 0% because negative PC2 means negative TLT loading on the growth factor

---

#### Regime Q3 — Risk-Off + Defensive (PC1_z < 0, PC2_z ≥ 0)

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Long Bonds | TLT | 100% | Maximum safe-haven — flight to quality |
| US Equities | SPY | 0% | Equities decline in risk-off |
| Gold | GLD | 0% | Gold is neutral-to-negative in defensive regime (real yields may rise) |
| **Total** | | **100%** | |

**Character:** Maximum bond exposure. Zero equities, zero gold. Pure defensive-flight portfolio.

**Macro rationale:** In Q3, PC1 is negative (risk-off) but PC2 is positive (growth expectations still alive). The correlation matrix shows TLT and SHY loading positively, risk assets loading negatively. This is a "flight to quality" regime where investors sell equities and buy Treasuries. Gold is ambiguous — it can rally or fall depending on real rate direction. The safest allocation is 100% TLT.

**Why not gold in Q3:** In a defensive regime with positive PC2 (growth still present), real yields may rise (nominals fall less than breakevens). Rising real yields are negative for gold. TLT is the unambiguous safe haven.

---

#### Regime Q4 — Risk-Off + Stress (PC1_z < 0, PC2_z < 0)

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Long Bonds | TLT | 60% | Core safe-haven |
| Gold | GLD | 30% | Crisis hedge — dollar debasement / tail risk |
| US Equities | SPY | 10% | Minimal equity — token defensive positioning |
| **Total** | | **100%** | |

**Character:** Heavy bonds, meaningful gold, token equities. Crisis portfolio.

**Macro rationale:** Q4 is the most dangerous regime. Both PCs are negative: risk-off (PC1 < 0) AND stress/inflation/panic (PC2 < 0). The correlation matrix shows correlations compressing toward 1.0. UUP loads positively (dollar strength) in the stress scenario. TLT may initially rally (flight to quality) but can sell off in a liquidity crunch. Gold provides the ultimate hedge against debasement (the dollar-bid scenario). A small SPY position (10%) prevents complete whipsaw if the regime rapidly transitions back to Q1.

**Allocation justification for TLT (60%) / GLD (30%) / SPY (10%):**
- TLT is the primary safe haven but carries rate-spike tail risk in crises
- GLD at 30% hedges the dollar-debasement scenario (e.g., 2008 post-Lehman gold surge, COVID gold rally)
- SPY at 10% maintains a toehold in equities — prevents total whipsaw if the regime flips to Q1
- This is the only regime holding 3 assets

### 7.2 Allocation Edge Cases

| Scenario | Action |
|---|---|
| Regime Q1 with regime_strength < 0.5 | Hold prior regime (see Section 12.2) |
| Single-asset allocation = 100% | Full concentration — execute as single buy/sell |
| Allocation goes to 0% | Sell entire position; do not maintain residual holdings |
| GLD allocation changed (Q2 → Q4) | Full rebalance — sell GLD if going from 40% to 30%, or buy if reverse |
| First-ever classification (cold start) | Classify immediately and execute full rebalance (see Section 12.6) |

### 7.3 Prohibited States

| State | Reason |
|---|---|
| Cash holdings > 0% | Always fully invested — no cash buffer |
| Leverage > 1.0× | No margin — gross notional = NAV |
| Short positions | No short selling — all positions long only |
| Derivatives | No options, futures, or swaps |
| EM (EEM) allocation | Signal-only — never allocate to EM directly |
| Commodity (DBC) allocation | Signal-only — never allocate to commodities directly |
| Credit (HYG) allocation | Signal-only — never allocate to credit directly |

### 7.4 Position Sizing Rules

- All allocations are **percentage of total portfolio NAV**
- No fractional shares rounding if using whole-share brokerage: round to nearest share, remainder held as cash residual (<0.1% expected)
- In cash-settled environments (paper trading / backtesting): allocations are exact decimals
- If an allocation target is 0%, sell the entire position regardless of rounding considerations

---

## 8. Rebalancing Rules

### 8.1 Rebalance Trigger

**Primary condition:** Regime quadrant changes — i.e., the sign of PC1_z or PC2_z changes.

- **PC1 sign change** (risk-on ↔ risk-off): Always triggers a rebalance. This is the most important regime change signal.
- **PC2 sign change** (growth ↔ inflation/stress): Also triggers a rebalance if PC1 sign is unchanged. This changes allocation within the same risk-on/off polarity.
- **Double sign change** (both PC1 and PC2 change): Full regime flip (e.g., Q1 → Q4 or Q2 → Q3). Always triggers rebalance.

**Secondary condition:** regime_strength crosses 0.5 upward from below. If the system was in "noisy hold" mode (regime_strength < 0.5) and strengthens above 0.5, it re-evaluates and rebalances to the proper quadrant.

**No-change days:** If regime is unchanged and regime_strength ≥ 0.5, do not trade.

### 8.2 Rebalance Frequency

| Metric | Value |
|---|---|
| Maximum rebalances per year | ~260 (daily, but regime changes ~15–30 times/yr) |
| Expected rebalances per year | 15–30 |
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
| Single-day regime flip (Q1 → Q4 → Q1) | Execute both rebalances — the second flips back |
| Regime unchanged 50+ consecutive days | No trades; monitor regime shift only |
| Holiday / non-trading day | Skip; regime assessment resumes next trading day |
| Partial fills on rebalance | Log warning; retry remaining fills next day |
| Regime changes at EOD but market closed | Queue rebalance for next market open |
| regime_strength < 0.5 on regime change day | Apply 2-day confirmation filter (Section 12.2) |

### 8.5 Turnover Controls

No explicit turnover cap — turnover is a natural consequence of regime changes. Historical simulation expected to show:

- **Low turnover months:** 5–15% (stable regime periods with few transitions)
- **High turnover months:** 30–60% (regime oscillation around axes)

---

## 9. Risk Management

### 9.1 Portfolio-Level Risk Limits

| Metric | Limit | Action if Breached |
|---|---|---|
| Max single-asset exposure | 100% (SPY in Q1, TLT in Q3) | Hard limit by construction |
| Min single-asset exposure | 0% (by construction) | N/A — built into allocation model |
| Max equity exposure (SPY) | 100% (Q1) | Hard limit by construction |
| Max bond exposure (TLT) | 100% (Q3) | Hard limit by construction |
| Max gold exposure (GLD) | 40% (Q2) | Hard limit by construction |
| Max net equity exposure | 100% (Q1) | Hard limit by construction |
| Min net equity exposure | 0% (Q3) | Hard limit by construction |

### 9.2 Drawdown Controls

| Drawdown Threshold | Action |
|---|---|
| Portfolio drawdown > 15% (peak-to-trough) | Review regime classification thresholds; consider tightening regime_strength filter |
| Portfolio drawdown > 25% | Full strategy review; potential suspension |
| Any single asset drawdown > 40% | Investigate for structural break (delisting, tracking error, etc.) |

### 9.3 Volatility Controls

- No explicit volatility targeting — the allocations are regime-dependent and implicitly control risk via asset class weights.
- Monitor rolling 63-day portfolio volatility. If it exceeds 25% annualized, flag for review.
- Monitor **PC1 dominance** (eigenvalue ratio). If PC1 dominates > 60% of variance, this indicates a crisis regime where all correlations converge. Consider tightening regime_strength filter to > 1.0 before allowing rebalances.

### 9.4 Correlation Regime Failure Detection

If the following conditions occur simultaneously, the PCA correlation structure may be breaking down:

| Condition | Threshold | Action |
|---|---|---|
| PC1 dominance | > 60% | Flag crisis correlation compression |
| Correlation dispersion | < 0.10 (mean of 28 off-diagonal absolute correlations) | All assets moving as one — regime model loses signal |
| regime_strength | < 0.3 for 10+ consecutive days | Model drift — regime classification unreliable |
| Eigenvalue ratio (λ1/λ2) | > 8.0 | Near-singular matrix — consider halting |

If 2+ conditions met simultaneously: move to 100% TLT (maximum safe haven) until conditions normalize.

### 9.5 Liquidity Risk

All three traded ETFs (SPY, TLT, GLD) are among the most liquid in their asset classes. No position exceeds 5% of average daily dollar volume at any target allocation size under $50M AUM.

### 9.6 Regime-Specific Risk Notes

| Regime | Key Risk | Mitigation |
|---|---|---|
| Q1 — Risk-On + Growth | Sudden risk-off shock (e.g., geopolitical event) | regime_strength filter catches transitional noise; 2-day confirmation reduces whipsaw |
| Q2 — Risk-On + Inflation | Stagflation — both equities and bonds fall | 40% GLD provides inflation hedge; TLT at 0% avoids rate carnage |
| Q3 — Risk-Off + Defensive | Bond selloff on good news (rates spike) | 100% concentration — if rates spike, regime will flip to Q1 or Q2 and rebalance |
| Q4 — Risk-Off + Stress | Liquidity crisis — all assets fall together | 60% TLT limits losses vs pure equity; GLD provides tail hedge; 10% SPY prevents whipsaw |

### 9.7 PCA-Specific Risk

| Risk | Description | Mitigation |
|---|---|---|
| Rotation ambiguity | Eigenvectors are identified only up to sign — PC1 loadings can flip sign | Always orient PC1 such that SPY loading is positive (multiply eigenvector by -1 if SPY loading < 0). This ensures consistent interpretation. |
| Lookback sensitivity | 60-day window may be too short in low-vol regimes or too long in fast crises | Fixed at 60 days. Sensitivity analysis can be done in backtest. |
| PCA on small window | 60 days × 8 assets = 60 observations for 8 variables; ratio ~7.5:1 — adequate but not generous | Minimum acceptable ratio is 3:1 (24 days). Below 21 days, skip PCA. |
| Rank deficiency | If assets cluster into fewer groups, correlation matrix becomes near-singular | Nearest-PSD correction applied. If condition number > 1000, warn and use identity matrix as fallback. |

---

## 10. Performance Expectations

### 10.1 Return Targets

| Metric | Target | Notes |
|---|---|---|
| Annualized return | 8–13% | Regime-based rotation premium over static 60/40 |
| Annualized volatility | 10–15% | Multi-asset diversification dampens vol; concentrated regimes increase it |
| Sharpe ratio (RFR=5%) | 0.5–0.8 | Pre-cost; expect after-cost ~0.4–0.7 |
| Max drawdown | <20% | Defensive regimes (Q3, Q4) should limit tail risk vs buy-and-hold SPY |
| Win rate | 50–60% | Regime transitions produce asymmetric bets |
| Profit factor | 1.3–1.7 | Wins larger than losses due to regime persistence |

### 10.2 Benchmark

Primary benchmark: **60/40 portfolio** (60% SPY / 40% TLT, rebalanced monthly)

Secondary benchmark: **Buy-and-hold SPY**

Tertiary benchmark: **Risk-parity** (25% each SPY/TLT/GLD/EEM, rebalanced monthly)

### 10.3 Backtesting Requirements

| Parameter | Value |
|---|---|
| Minimum backtest window | 10 years (2016–2026) |
| Preferred backtest window | 20 years (2006–2026) — includes GFC, taper tantrum, COVID, 2022 rate cycle, 2023 banking crisis |
| Data granularity | Daily OHLCV |
| Cost model | 5 bps per trade, 1 bp daily financing (for leveraged scenarios if applicable) |
| Slippage model | 5 bps per leg |

### 10.4 Key Risk Periods to Test

| Period | Event | Expected Behavior |
|---|---|---|
| 2008 GFC | Correlation compression to 1.0, all risk assets crash | Q4 regime (TLT 60%, GLD 30%, SPY 10%) — protective vs 100% SPY |
| 2011–2012 | Euro crisis, risk-off, TLT rally | Q3 regime (100% TLT) — captures bond rally |
| 2013 Taper Tantrum | Bonds sell off violently, equities dip | Q1 or Q2 regime — TLT at 0% avoids carnage |
| 2015–2016 | China devaluation, commodity crash | Q3 or Q4 — defensive posture |
| 2017 | Synchronized global growth, low vol | Q1 regime (100% SPY) — captures equity rally |
| 2020 COVID | Risk-off spike then V-shaped recovery | Q3 → Q4 → Q1 in rapid succession — test turnover costs |
| 2021 | Reflation trade, commodities surge | Q2 regime (60% SPY, 40% GLD) — captures commodity/gold rally |
| 2022 | Fed hikes, equities and bonds both fall | Q4 regime (TLT 60%, GLD 30%, SPY 10%) — relative protection |
| 2023 | Banking crisis, gold surges | Q4 regime — GLD at 30% captures gold rally |

---

## 11. Implementation Notes

### 11.1 Dependencies

| Library | Version | Purpose |
|---|---|---|
| pandas | ≥1.5 | Data manipulation, rolling windows |
| numpy | ≥1.24 | Numerical computation, linear algebra (eigendecomposition) |
| scipy | ≥1.10 | Nearest-PSD correction (scipy.linalg) |
| yfinance | ≥0.2 | Price data (or alternative data fetcher) |
| python-dotenv | ≥1.0 | Configuration management |

### 11.2 File Structure

```
quantloop/strategies/s536/
  spec.md              ← this file
  signals.py           ← correlation matrix + PCA computation
  regime.py            ← quadrant classification + regime_strength
  allocation.py        ← target allocation by regime
  rebalance.py         ← rebalance execution logic
  backtest.py          ← backtesting harness
  config.yaml          ← strategy parameters
```

### 11.3 Configuration Parameters (config.yaml)

```yaml
strategy:
  id: s536
  name: CORREG

pca:
  correlation_window: 60
  z_score_window: 252
  min_assets: 6
  min_overlap: 15
  spy_loading_sign: positive        # ensure PC1 SPY loading > 0 for consistent interpretation
  nearest_psd: true                 # apply Higham correction if needed

regime:
  strength_threshold: 0.5           # minimum regime_strength to classify
  confirmation_days: 2              # days required for regime change when strength < threshold
  cold_start_override: true         # classify immediately on first run

allocations:
  q1_risk_on_growth:
    SPY: 1.00
    TLT: 0.00
    GLD: 0.00
  q2_risk_on_inflation:
    SPY: 0.60
    TLT: 0.00
    GLD: 0.40
  q3_risk_off_defensive:
    SPY: 0.00
    TLT: 1.00
    GLD: 0.00
  q4_risk_off_stress:
    SPY: 0.10
    TLT: 0.60
    GLD: 0.30

data:
  tickers:
    traded: [SPY, TLT, GLD]
    signal_only: [DBC, EEM, HYG, SHY, UUP]
  min_lookback: 252
  preferred_lookback: 756

risk:
  max_drawdown_review: 0.15
  max_drawdown_suspend: 0.25
  max_volatility_warning: 0.25
  pc1_dominance_warning: 0.60
  corr_dispersion_warning: 0.10
  regime_strength_drift: 0.30

execution:
  slippage_bps: 5
  order_type: market_on_close
```

### 11.4 Pseudo-Code (Daily Run)

```python
def run_daily():
    prices = fetch_prices([SPY, TLT, GLD, DBC, EEM, HYG, SHY, UUP], lookback=756)

    # Step 1: Compute 60d rolling correlation matrix
    returns = prices.pct_change().dropna()
    recent_returns = returns.tail(60)
    corr_matrix = recent_returns.corr()          # 8×8

    # Step 2: PCA decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(corr_matrix)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Orient PC1: ensure SPY loading is positive
    if eigenvectors[0, 0] < 0:                   # SPY is first asset
        eigenvectors[:, 0] *= -1

    # Step 3: Project current returns
    current_returns = returns.iloc[-1].values     # 8-element vector
    pc1_raw = np.dot(current_returns, eigenvectors[:, 0])
    pc2_raw = np.dot(current_returns, eigenvectors[:, 1])

    # Step 4: Z-score
    pc1_history = compute_rolling_pc1(eigenvectors[:, 0], returns, window=252)
    pc2_history = compute_rolling_pc2(eigenvectors[:, 1], returns, window=252)
    pc1_z = (pc1_raw - pc1_history.mean()) / pc1_history.std()
    pc2_z = (pc2_raw - pc2_history.mean()) / pc2_history.std()

    # Step 5: Regime classification
    regime_strength = np.sqrt(pc1_z**2 + pc2_z**2)
    if regime_strength < 0.5 and has_prior_regime:
        regime = previous_regime                 # Noisy — hold prior
    else:
        regime = classify_quadrant(pc1_z, pc2_z) # Q1/Q2/Q3/Q4

    # Step 6: Target allocation
    targets = get_allocation(regime)

    # Step 7: Rebalance if regime changed
    if regime != previous_regime:
        execute_rebalance(targets)
```

---

## 12. Edge Cases, Tiebreakers & Fallbacks

### 12.1 Signal-Level Edge Cases

| # | Edge Case | Rule | Rationale |
|---|---|---|---|
| 1 | Fewer than 21 days of price history for any asset | Exclude that asset from correlation matrix | Minimum sample for meaningful correlation |
| 2 | Fewer than 6 assets with valid data | Skip PCA; hold prior regime | Insufficient dimension for structural insights |
| 3 | Zero-variance asset (constant price 60 days) | Set all correlations to 0.0 for that asset | No signal → no relationship |
| 4 | Missing observations within 60-day window | Pairwise-complete; minimum 15 overlapping obs | Balances data inclusion vs quality |
| 5 | Correlation matrix not positive semi-definite | Apply nearest-PSD correction (Higham 1988) | Ensures valid eigen-decomposition |
| 6 | PC1 eigenvalue == PC2 eigenvalue (±0.01) | Warn of ambiguous rotation; continue with standard PCA | Near-degenerate — factor rotation is arbitrary |
| 7 | sigma_PC1 == 0 (z-score denominator) | PC1_z = 0.0 | Zero volatility → no meaningful signal |
| 8 | sigma_PC2 == 0 (z-score denominator) | PC2_z = 0.0 | Zero volatility → no meaningful signal |
| 9 | Insufficient history for z-score (<63 obs) | Use raw PC1/PC2 values scaled by sqrt(trace/8) | Bootstrap approximation for cold start |
| 10 | SPY loading on PC1 is negative | Multiply PC1 eigenvector by -1 | Ensures consistent interpretation: PC1 > 0 = risk-on |

### 12.2 Regime Classification Tiebreakers

| # | Scenario | Rule | Rationale |
|---|---|---|---|
| 1 | regime_strength < 0.5 (noisy) | Hold prior regime — do not rebalance | Weak signal means classification is unreliable; avoid whipsaw |
| 2 | regime_strength < 0.5 AND no prior regime (cold start) | Override: classify immediately using quadrant | Must start somewhere; default to Q1 if ambiguous |
| 3 | regime_strength < 0.5 for 10+ consecutive days | Flag model drift warning | May indicate PCA structure has broken down |
| 4 | PC1_z == 0 exactly | Treat as PC1_z ≥ 0 (risk-on) | Zero = at mean; default to optimistic |
| 5 | PC2_z == 0 exactly | Treat as PC2_z ≥ 0 (growth) | Zero = at mean; default to growth |
| 6 | Both PC1_z == 0 AND PC2_z == 0 | Q1 (Risk-On + Growth) | Origin is neutral → default optimistic |

### 12.3 Allocation Edge Cases

| # | Edge Case | Rule | Rationale |
|---|---|---|---|
| 1 | Allocation rounds to 0 but > 0 | Execute sell | Clean slate per regime allocation |
| 2 | SPY → 0% in Q3 | Full liquidation | Risk-off → no equities |
| 3 | TLT → 0% in Q1 and Q2 | Full liquidation | Risk-on / inflation → no bonds |
| 4 | GLD → 0% in Q1 and Q3 | Full liquidation | No inflation or crisis → no gold needed |
| 5 | GLD changes 40% (Q2) → 30% (Q4) | Sell 10% partial | Rebalance to new target |
| 6 | Allocation rounding (whole shares) | Round to nearest; residual cash < 0.1% | Minimizes tracking error |

### 12.4 Data Fallbacks (Priority Order)

| Level | Condition | Action |
|---|---|---|
| 1 | All 8 assets have valid data | Compute full 8×8 correlation matrix and PCA |
| 2 | 1–2 signal-only assets missing data | Compute 7×7 or 6×6 correlation matrix on remaining assets; proceed with PCA |
| 3 | 3+ signal-only assets missing | Minimum 6 assets required; if fewer, hold prior regime |
| 4 | One traded ETF (SPY/TLT/GLD) data missing | Hold prior allocation for that asset; rebalance others if possible |
| 5 | Two+ traded ETFs data missing | Hold entire allocation; do not rebalance |
| 6 | All data missing for 3+ consecutive days | Flag critical alert; maintain last known allocation |
| 7 | Connection failure | Use cached data (max 2 days stale) |

### 12.5 Regime Whipsaw — Confirmation Rules

**Scenario:** The (PC1_z, PC2_z) vector oscillates around the axes (PC1_z ≈ 0 or PC2_z ≈ 0) multiple days in a row, causing regime whipsaw (e.g., Q1 → Q2 → Q1 → Q2 over 4 days).

**Rule:** Apply a **2-day confirmation filter** when regime_strength < 1.0. A regime change is only executed if the new quadrant persists for 2 consecutive daily readings, unless the regime_strength is ≥ 1.0 (strong signal).

**Exception:** If regime_strength ≥ 1.0, the confirmation is waived and the rebalance executes immediately. This prevents lag during strong, decisive regime transitions.

**Summary table:**

| regime_strength | Confirmation required? | Behavior |
|---|---|---|
| < 0.5 | Hold prior regime | Do not classify — too noisy |
| 0.5 – 1.0 | 2-day confirmation | Wait for second consecutive day |
| ≥ 1.0 | No confirmation | Execute immediately |

### 12.6 First-Run / Cold-Start Rules

| Scenario | Action |
|---|---|
| No prior regime history | Classify immediately from first (PC1_z, PC2_z) — cold_start_override = true |
| No z-score history (<63 obs) | Use raw PC values scaled by sqrt(trace(R)/8) as fallback |
| Insufficient 60-day data (<21 trading days) | Do not trade until 21 days of data accumulated |
| Insufficient 60-day data (21–59 trading days) | Compute correlation on available data; warn in log |
| PC1 sign ambiguous (loading near zero) | If abs(SPY_loading) < 0.1, renormalize PC1 to emphasize SPY |

### 12.7 Holiday / Weekend Rules

- Signals are computed using the most recent trading day's closing prices
- If today is Monday, the 60-day correlation window uses closes from 60 trading days prior (which may be ~84 calendar days ago)
- Rebalances are executed on the next trading day following a regime change signal
- If a holiday falls within the 60-day correlation window, simply exclude non-trading days — the window is strictly 60 trading days

### 12.8 Catastrophic Fallback

If all data sources fail for 5+ consecutive trading days:
1. Move to 100% TLT (maximum safe haven)
2. Flag critical alert to strategy administrator
3. Resume normal operation when data flow is restored

Rationale: In an extended data blackout, a defensive posture minimizes unknown risk. TLT is chosen over cash because it preserves purchasing power in a deflationary shock (the most likely event during a data blackout).

---

## 13. References & Related Strategies

### 13.1 Academic / Industry References

- **Regime-Switching in Correlation Structure:** Ang, A. & Chen, J. (2002). "Asymmetric Correlations of Equity Portfolios." *Journal of Financial Economics* 63(3): 443–494. Demonstrates that correlations are higher in down markets than up markets — foundational for the CORREG regime approach.
- **PCA on Correlation Matrices:** Jolliffe, I.T. (2002). *Principal Component Analysis*, 2nd Edition, Springer. Standard reference for PCA methodology including correlation-based vs covariance-based decomposition.
- **Correlation Regime Detection:** Longin, F. & Solnik, B. (2001). "Extreme Correlation of International Equity Markets." *Journal of Finance* 56(2): 649–676. Shows that international equity correlations increase during extreme market moves.
- **Rolling Correlation Windows:** Bracker, K. & Koch, P.D. (1999). "Economic Determinants of the Correlation Structure Across International Equity Markets." *Journal of Economics and Business* 51(6): 443–471. Provides guidance on window selection for rolling correlation estimation.
- **Nearest Correlation Matrix:** Higham, N.J. (2002). "Computing the Nearest Correlation Matrix — A Problem from Finance." *IMA Journal of Numerical Analysis* 22(3): 329–343. The PSD-correction algorithm used as fallback.
- **Cross-Asset Correlation Regimes:** Kritzman, M., Page, S., & Turkington, D. (2012). "Regime Shifts: Implications for Dynamic Strategies." *Financial Analysts Journal* 68(3): 22–39. Direct intellectual antecedent — uses PCA on asset returns to identify macro regimes.

### 13.2 Related Quantloop Strategies

| Strategy | Relationship |
|---|---|
| s535 — Dollar/Global Macro Regime (USDCYCLE) | Complementary — USDCYCLE uses dollar-based regime; CORREG uses correlation structure. The two can be combined for cross-validation of regime calls. |
| s531 — Inflation Regime Classifier (INFLREG) | Related via PC2 (inflation/growth factor). CORREG's Q2 (inflation) regime complements INFLREG's inflation classification. |
| s530 — US Inflation Regime (INFLCYCLE) | INFLREG/s530 focus on single-factor inflation; CORREG integrates inflation as one of two dimensions. |
| s540 — Global Risk Appetite (RISKCYCLE) | PC1 (risk-on/off) is analogous to RISKCYCLE's risk appetite measure. CORREG adds the second dimension. |

### 13.3 Symbol Lookup

| Ticker | ISIN | Inception | ER | AUM |
|---|---|---|---|---|
| SPY | US78462F1030 | 1993-01-22 | 0.09% | ~$500B |
| TLT | US4642874322 | 2002-07-22 | 0.15% | ~$40B |
| GLD | US78463V1070 | 2004-11-18 | 0.40% | ~$60B |
| DBC | US46138B1026 | 2006-02-03 | 0.89% | ~$3B |
| EEM | US4642872342 | 2003-04-07 | 0.68% | ~$20B |
| HYG | US4642885135 | 2007-04-11 | 0.49% | ~$15B |
| SHY | US4642874579 | 2002-07-22 | 0.15% | ~$20B |
| UUP | US46138H7060 | 2007-02-20 | 0.75% | ~$1.5B |

---

## 14. Version History & Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0.0 | 2026-06-15 | Agent (Quantloop) | Initial spec — 14-section template; full PCA methodology, quadrant regime classification, asset allocation, and risk specifications |

---

**END OF SPEC — s536 (CORREG)**
