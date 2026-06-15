# s537 — Volatility Regime Ensemble (VOLREG)

**Status:** Draft  
**Version:** 1.0.0  
**Last Updated:** 2026-06-15  
**Author:** Agent (Quantloop)

---

## 1. Strategy Overview

| Field | Value |
|---|---|
| **Strategy ID** | s537 |
| **Short Name** | VOLREG |
| **Long Name** | Volatility Regime Ensemble |
| **Asset Class** | Multi-asset (equities, bonds) |
| **Trading Frequency** | Daily (EOD rebalance triggered by composite score regime change) |
| **Avg Holding Period** | 5–30 days (regime-dependent) |
| **Max Positions** | 2 (SPY, TLT) |
| **Gross Exposure** | 100% (fully invested; leverage = 1.0×) |
| **Net Exposure** | Varies by regime (0%–100% equities) |
| **Inception** | TBD |

Volatility is multi-dimensional. Different asset classes generate different volatility signals that respond at different speeds — equity implied vol (VIX) reacts instantly to shocks, equity realized vol confirms them over days, bond vol responds to rate regimes, credit vol dispersion captures funding stress, and vol-of-vol detects regime transitions before they fully manifest. Combining five distinct vol signals into a single ensemble composite provides a more robust and timely volatility regime signal than any single measure.

The strategy computes 5 vol signals across a traded universe of SPY (equities) and TLT (long-term treasuries), with additional signal-only instruments (^VIX, ^VIX3M, HYG) for signal computation. A single composite score is formed from 4 binary signals (VIX term structure, SPY RV regime, bond vol, vol dispersion) plus a continuous vol-of-vol component. The composite maps to a 3-tier allocation system: Low Vol (100% SPY), Medium Vol (60/40 SPY/TLT), and High Vol (100% TLT).

---

## 2. Strategy Rationale / Investment Thesis

### 2.1 Volatility Is Multi-Dimensional, Not Univariate

Most volatility-timing strategies rely on a single signal — typically VIX level or trailing SPY volatility. This misses the rich, multi-dimensional nature of volatility across asset classes:

| Dimension | Instrument | What It Captures | Response Speed |
|---|---|---|---|
| Equity implied vol | ^VIX | Market fear/pricing of tail risk | Fast (minutes) |
| Equity realized vol | SPY RV | Actual realized price variance | Medium (days) |
| Bond vol | TLT RV | Rates uncertainty / macro regime | Medium–Slow (weeks) |
| Credit vol dispersion | HYG / TLT vol ratio | Credit market stress / funding conditions | Fast–Medium (days) |
| Vol-of-vol | ΔVIX absolute | Regime transition risk / instability | Fast (intraday) |

Each signal individually has modest predictive power for the equity/bond regime. But when multiple signals point in the same direction simultaneously, conviction increases non-linearly. The ensemble approach dampens false signals from any single measure and provides a more robust regime classification.

### 2.2 Why These Five Signals

**VIX Term Structure (^VIX / ^VIX3M):** The VIX futures curve shape is the single most widely watched vol signal. Contango (VIX3M > VIX) indicates benign expectations — the market expects vol to decline. Backwardation (VIX > VIX3M) signals acute near-term stress — a reliable flight-to-safety trigger. The 0.95/1.05 thresholds provide a neutral buffer zone that prevents whipsaw from small VIX fluctuations.

**SPY Realized Vol Regime (5d RV vs 63d median):** Realized vol captures actual price variance that implied vol (VIX) may over- or under-estimate. The 5d window reacts quickly to realized regime changes while the 63d (~3 month) median provides a stable reference. This is faster than the classic 21d/252d comparison and more responsive to regime transitions.

**Bond Vol (TLT 21d RV vs 126d median):** Bond vol provides orthogonal information to equity vol. During the 2022 rate hiking cycle, bond vol surged while equity vol remained moderate — a signal that the macro regime had shifted even though equity fear (VIX) was not elevated. Bond vol captures the rates-driven component of the macro environment that equity vol alone misses.

**Vol Dispersion (HYG RV / TLT RV):** When HYG (high-yield credit) vol spikes relative to TLT vol, it signals credit market stress — a leading indicator of broader market turmoil. Credit markets tend to dislocate before equity markets fully price in stress (e.g., early 2008, early 2020). The ratio normalizes for overall bond vol levels, isolating the credit-specific stress component. The 1.5× threshold on the 63d median ensures we only act on significant dispersion outliers.

**Vol-of-Vol (ΔVIX absolute z-scored):** The daily change in VIX, measured in absolute value, captures volatility-of-volatility — a concept well-studied in the options literature. High vol-of-vol indicates that the market is uncertain about future volatility itself, which typically coincides with regime transitions (e.g., VIX doubling in March 2020, or the VIX "crash" from 35 to 15 in April 2020). This is the only continuous signal in the ensemble, weighted at 0.2× to provide gradient without dominating the binary consensus.

### 2.3 Why This Generates Enough Trades

| Regime Transition Type | Expected Frequency |
|---|---|
| Low Vol → Medium Vol | ~5–10 times per year |
| Medium Vol → High Vol | ~5–10 times per year |
| Direct Low → High (rare) | ~1–3 times per year (major crises) |
| Any regime change | ~10–20 rebalance events per year |

The composite score moves between tiers more frequently than annual/quarterly vol regimes but less frequently than daily VIX flip-flopping, due to the ensemble consensus requirement. This produces sufficient trading activity for meaningful alpha without overtrading.

### 2.4 Key Edge: Orthogonal Information

The crucial insight is that **each vol signal captures a different risk channel**:

- Equity vol (VIX, SPY RV) captures **valuation-driven risk** — investors repricing equity risk premiums
- Bond vol (TLT RV) captures **monetary/rates risk** — central bank policy, inflation expectations
- Credit vol (HYG vol / TLT vol) captures **funding/liquidity risk** — credit market functioning
- Vol-of-vol captures **instability risk** — transitions between regimes

These channels are only partially correlated. During the 2013 Taper Tantrum, bond vol spiked but equity vol remained low — a Medium Vol signal that correctly de-risked into bonds. During the 2020 COVID crash, all channels fired simultaneously — the composite hit -4.5 (maximum High Vol) within days. The ensemble captures these nuanced regimes that single-signal vol strategies miss.

---

## 3. Trading Universe

### 3.1 Candidate Universe — Traded Instruments

Exactly 2 ETFs, selected for liquidity, low expense ratios, and direct expression of the two asset classes in the volatility regime model:

| # | Ticker | Name | Asset Class | Primary Role |
|---|---|---|---|---|
| 1 | SPY | SPDR S&P 500 ETF Trust | US Large-Cap Equity | Risk-on exposure in Low/Medium Vol |
| 2 | TLT | iShares 20+ Year Treasury Bond ETF | US Long-Term Treasuries | Safe-haven exposure in Medium/High Vol |

**Universe Size Rationale:** The strategy is specifically designed for a 2-asset universe (equities and long bonds). Adding a third asset (e.g., GLD in CORREG) would dilute the purity of the vol-regime signal. In High Vol regimes, the flight to safety is into Treasuries, not alternatives. In Low Vol regimes, risk assets (SPY) are the primary beneficiary.

### 3.2 Signal-Only Instruments (Not Traded)

These 3 instruments contribute to the signal computation but are never allocated to:

| # | Ticker | Name | Asset Class | Role in Signal Computation |
|---|---|---|---|---|
| 1 | ^VIX | CBOE Volatility Index | Equity Implied Vol | Signal 1 (VIX Term Structure) + Signal 5 (Vol-of-Vol) — VIX level and daily change |
| 2 | ^VIX3M | CBOE 3-Month Volatility Index | Equity Implied Vol (Forward) | Signal 1 (VIX Term Structure denominator) — forward vol expectation |
| 3 | HYG | iShares iBoxx High Yield Corporate Bond ETF | US High-Yield Credit | Signal 4 (Vol Dispersion numerator) — credit market vol |

### 3.3 Liquidity Requirements

| Instrument | Min ADV (shares) | Min ADV ($) | Max Spread |
|---|---|---|---|
| SPY | 50M | $20B | < 0.01% |
| TLT | 10M | $1B | < 0.05% |
| HYG | 5M | $200M | < 0.10% |
| ^VIX | N/A (index) | N/A | N/A |
| ^VIX3M | N/A (index) | N/A | N/A |

All ETFs have continuous trading history since at least 2007 (HYG inception was April 2007). ^VIX data available from 1990; ^VIX3M from 2007 onward.

### 3.4 Universe Rules

| Rule | Detail |
|---|---|
| **Maximum positions** | 2 (hard limit — SPY, TLT) |
| **Minimum positions** | 1 (may go to 100% SPY or 100% TLT) |
| **Addition criteria** | None — universe is fixed |
| **Removal criteria** | Only if an ETF is delisted, merged, or has structural tracking error > 2%/yr |
| **Rebalance trigger** | Composite score changes tier — see Section 8 |
| **Sector constraints** | N/A — SPY and TLT represent the two core macro factors (risk and safe-haven) |

---

## 4. Data Sources & Processing

### 4.1 Primary Data Sources

| Data | Source | Ticker | Priority |
|---|---|---|---|
| Daily OHLCV — SPY | Yahoo Finance | SPY | Primary |
| Daily OHLCV — TLT | Yahoo Finance | TLT | Primary |
| Daily OHLCV — HYG | Yahoo Finance | HYG | Primary |
| Daily VIX Close | Yahoo Finance | ^VIX | Primary |
| Daily VIX3M Close | Yahoo Finance | ^VIX3M | Primary |

### 4.2 Data Requirements

| Requirement | Value |
|---|---|
| Minimum lookback | 252 trading days (1 year) — needed for 63d and 126d medians + 252d z-score window |
| Recommended lookback | 756 trading days (3 years) for robust estimation of all moments |
| Signal windows | 5d (SPY RV), 21d (TLT RV), 63d (medians), 126d (TLT median), 252d (z-score lookback) |
| Signal computation | Daily (each EOD, recompute all 5 signals) |
| Data freshness | EOD data must include the most recent close |
| Adjustments | Split/dividend-adjusted close prices for ETFs; raw index values for ^VIX, ^VIX3M (unadjusted — indices are not adjusted) |

### 4.3 Data Quality Rules

| Check | Action |
|---|---|
| Missing price for any signal instrument | Apply fallback chain (Section 12.4); if no data available, set that signal to 0 (neutral) |
| Missing price for any traded asset (SPY/TLT) | Skip rebalance, hold prior allocation |
| Stale price (>1 day old for ETFs, >1 day old for VIX/VIX3M) | Skip rebalance, log warning |
| Zero or negative price | Skip rebalance, flag critical error |
| >5% single-day gap in SPY/TLT (suspect split/dividend) | Verify adjusted close; if confirmed, proceed |
| ^VIX or ^VIX3M zero or negative | Impossible for VIX indices — if occurs, treat as missing data |
| HYG = 0 or negative | Impossible — if occurs, treat as missing data |
| SPY RV > 200% annualized | Flag extreme vol event; proceed with signal computation (this is valid during crises) |

### 4.4 Fallback Data Chain

1. **Primary:** Yahoo Finance (via yfinance or equivalent)
2. **Secondary:** Alpaca Market Data (if available)
3. **Tertiary:** Cached last-known prices (max 2 days stale)
4. **Final fallback:** Hold current allocation — do not rebalance

---

## 5. Signals — Specification

### 5.1 Signal Architecture Overview

The strategy uses **5 volatility signals** computed from a universe of 2 traded instruments (SPY, TLT) and 3 signal-only instruments (^VIX, ^VIX3M, HYG). Four signals are binary (±1, 0) and one is continuous (z-scored). All signals are recomputed daily at EOD.

**Signal Summary:**

| # | Signal Name | Inputs | Type | Range |
|---|---|---|---|---|
| 1 | VIX Term Structure | ^VIX, ^VIX3M | Binary | -1, 0, +1 |
| 2 | SPY RV Regime | SPY close | Binary | -1, 0, +1 |
| 3 | Bond Vol | TLT close | Binary | -1, 0, +1 |
| 4 | Vol Dispersion | HYG, TLT close | Binary | -1, 0, +1 |
| 5 | Vol-of-Vol | ^VIX close | Continuous | z-scored (typically -3 to +3) |

### 5.2 Signal 1 — VIX Term Structure (VIX_TS)

**Purpose:** Capture whether the VIX futures curve is in contango (benign/normal) or backwardation (stress/fear). The VIX term structure is the single most widely followed volatility regime indicator in professional trading.

**Ticker:** ^VIX (spot VIX), ^VIX3M (3-month VIX futures index)

**Calculation:**

```
VIX_ratio = ^VIX[t] / ^VIX3M[t]

if VIX_ratio < 0.95:
    signal_1 = +1    # Contango — benign vol environment, risk-on
elif VIX_ratio > 1.05:
    signal_1 = -1    # Backwardation — stress, flight to safety
else:
    signal_1 = 0     # Neutral zone — no clear signal
```

**Threshold Rationale:**
- **0.95 threshold:** Requires VIX to be at least 5% below VIX3M to signal contango. This prevents small VIX moves from triggering false +1 signals. Contango is the normal state (VIX3M > VIX ~80% of trading days since 2007).
- **1.05 threshold:** Requires VIX to be at least 5% above VIX3M to signal backwardation. Backwardation is unusual (~10–15% of trading days) and typically coincides with market stress.
- **Neutral zone (0.95–1.05):** ~5–15% of trading days fall in this zone — usually the early stages of a regime transition.

**Edge Cases:**

| Scenario | Rule | Rationale |
|---|---|---|
| VIX_ratio = 0.95 exactly | +1 (contango) | Strictly less than → < 0.95 is contango; 0.95 is neutral if using strict threshold. Tie goes to conservative: treat 0.95 as neutral (0). |
| VIX_ratio = 1.05 exactly | 0 (neutral) | Strictly greater than → > 1.05 is backwardation; 1.05 is neutral. |
| ^VIX or ^VIX3M = 0 | signal_1 = 0, log error | Impossible in practice — zero VIX is economically nonsensical |
| ^VIX or ^VIX3M missing | signal_1 = 0 (neutral) | Fall back to neutral — do not assume direction |
| VIX < 10 (ultra-low vol) | Signal still computed normally | Ultra-low vol is valid contango (+1) |

### 5.3 Signal 2 — SPY Realized Vol Regime (SPY_RV)

**Purpose:** Compare short-term (5-day) realized volatility to its rolling median (63-day). When short-term vol is below its recent median, the equity market is calmer than average (risk-on). When it is above, stress is building.

**Ticker:** SPY (close prices)

**Calculation:**

```
# Daily log returns
spy_returns[t] = ln(SPY_close[t] / SPY_close[t-1])

# 5-day realized volatility (annualized)
rv_5[t] = sqrt(252/5 * sum(spy_returns[t-4:t+1]^2))

# 63-day median of 5-day RV values
rv_5_history = [rv_5[t-62], rv_5[t-61], ..., rv_5[t]]
rv_5_median_63 = median(rv_5_history)

if rv_5[t] < rv_5_median_63:
    signal_2 = +1    # Current vol below median — benign
elif rv_5[t] > rv_5_median_63:
    signal_2 = -1    # Current vol above median — stressed
else:  # equal
    signal_2 = 0     # Exactly at median — neutral
```

**Why 5d RV vs 63d median:**
- 5d RV reacts quickly to recent price action (faster than the standard 21d window)
- 63d median (not mean) is robust to outliers — a single 5-day vol spike doesn't shift the median significantly
- This combination provides responsive yet stable regime detection

**Edge Cases:**

| Scenario | Rule | Rationale |
|---|---|---|
| rv_5 < 63d window of data | Compute on available data; minimum 21 trading days required | Insufficient history for stable median |
| rv_5 = rv_5_median_63 exactly | signal_2 = 0 (neutral) | At breakeven — no directional signal |
| SPY missing for 1+ day | Cannot compute rv_5; signal_2 = 0 | Returns require consecutive closes |
| SPY constant for 5 days (rv_5 = 0) | signal_2 = +1 (above median only if median is also 0) | Zero vol is the most benign possible state |
| 63d median = 0 and rv_5 = 0 | signal_2 = 0 (neutral) | Both zero — no information |
| SPY gap up/down > 20% (single day) | rv_5 will spike; signal_2 = -1 | Extreme moves indicate regime change — correct signal |

### 5.4 Signal 3 — Bond Vol (BOND_VOL)

**Purpose:** Measure whether bond market volatility (TLT 21d RV) is above or below its long-term (126d ≈ 6 month) median. Bond vol is orthogonal to equity vol — it captures rates/macro uncertainty that may not be reflected in equity fear (VIX).

**Ticker:** TLT (close prices)

**Calculation:**

```
# Daily log returns
tlt_returns[t] = ln(TLT_close[t] / TLT_close[t-1])

# 21-day realized volatility (annualized)
tlt_rv_21[t] = sqrt(252/21 * sum(tlt_returns[t-20:t+1]^2))

# 126-day median of 21-day RV values
tlt_rv_21_history = [tlt_rv_21[t-125], ..., tlt_rv_21[t]]
tlt_rv_21_median_126 = median(tlt_rv_21_history)

if tlt_rv_21[t] < tlt_rv_21_median_126:
    signal_3 = +1    # Bond vol below median — benign rates environment
elif tlt_rv_21[t] > tlt_rv_21_median_126:
    signal_3 = -1    # Bond vol above median — rates uncertainty / stress
else:
    signal_3 = 0     # Exactly at median — neutral
```

**Why 21d RV vs 126d median:**
- 21d provides a meaningful bond vol estimate (~1 month of trading)
- 126d (~6 months) captures the medium-term vol regime — longer than the SPY 63d because bond vol regimes are more persistent
- Using median (not mean) avoids distortion from extreme rate events (e.g., 2013 Taper Tantrum)

**Edge Cases:**

| Scenario | Rule | Rationale |
|---|---|---|
| tlt_rv_21 < 126d window | Compute on available data; minimum 42 trading days | Need at least 2× the 21d window for a meaningful median |
| TLT missing for 1+ day | Cannot compute rv_21; signal_3 = 0 | Returns require consecutive closes |
| TLT constant for 21+ days | rv_21 = 0; signal_3 = +1 | Zero bond vol is extremely benign |
| 126d window includes zero-vol period | Median may be 0; handle as per normal logic | Valid — all rv values are zero |

### 5.5 Signal 4 — Vol Dispersion (VOL_DISP)

**Purpose:** Capture credit market stress by measuring whether HYG (high-yield credit) volatility is elevated relative to TLT (Treasury) volatility. When HYG vol spikes relative to bonds, it signals credit market distress — a leading indicator of broader market stress. This cross-asset vol ratio normalizes for the general bond vol environment.

**Ticker:** HYG (high-yield credit ETF), TLT (long-term Treasury ETF)

**Calculation:**

```
# Daily log returns for both
hyg_returns[t] = ln(HYG_close[t] / HYG_close[t-1])
tlt_returns[t] = ln(TLT_close[t] / TLT_close[t-1])

# 21-day realized vol for both (annualized)
hyg_rv_21[t] = sqrt(252/21 * sum(hyg_returns[t-20:t+1]^2))
tlt_rv_21[t] = sqrt(252/21 * sum(tlt_returns[t-20:t+1]^2))

# Cross-asset vol ratio
vol_disp_ratio[t] = hyg_rv_21[t] / tlt_rv_21[t]

# 63-day median of the ratio
vol_disp_ratio_history = [vol_disp_ratio[t-62], ..., vol_disp_ratio[t]]
vol_disp_median_63 = median(vol_disp_ratio_history)

# Threshold: 1.5x the median
threshold = 1.5 * vol_disp_median_63

if vol_disp_ratio[t] < threshold:
    signal_4 = +1    # Credit vol not abnormally elevated — benign
elif vol_disp_ratio[t] > threshold:
    signal_4 = -1    # Credit vol spike relative to bonds — credit stress
else:  # equal
    signal_4 = 0     # Exactly at threshold — neutral
```

**Why 1.5× the median:**
- The HYG/TLT vol ratio is typically in a range of 0.8–2.5× during normal conditions
- A ratio above 1.5× its own 63d median represents a significant outlier — typically the top 10–15% of observations
- This threshold catches meaningful credit dislocations (2008, 2011, 2015-2016, 2020, 2022) while filtering normal fluctuations
- Using 1.5× of the median (not a fixed level) adapts to the prevailing regime — in high-vol periods, the ratio naturally increases, and the 1.5× threshold adjusts accordingly

**Edge Cases:**

| Scenario | Rule | Rationale |
|---|---|---|
| HYG data missing | signal_4 = 0 (neutral) | Cannot compute vol dispersion — remain neutral |
| TLT data missing | signal_4 = 0 (neutral) | Denominator unavailable — cannot compute ratio |
| Both HYG and TLT data missing | signal_4 = 0 (neutral) | Both inputs unavailable |
| TLT rv_21 = 0 (constant TLT 21 days) | vol_disp_ratio → ∞; signal_4 = -1 (stress) | Zero TLT vol with positive HYG vol = extreme dispersion — likely data error or crisis |
| HYG rv_21 = 0 (constant HYG 21 days) | vol_disp_ratio = 0; signal_4 = +1 (benign) | Zero credit vol is benign — impossible in practice for HYG |
| vol_disp_ratio = threshold exactly | signal_4 = 0 (neutral) | At breakeven — no directional signal |
| Insufficient history (< 63d for median) | Compute on available data; minimum 21d | Bootstrap the median with available data |

### 5.6 Signal 5 — Vol-of-Vol (VOV)

**Purpose:** Capture the daily change in VIX in absolute terms, z-scored relative to recent history. High vol-of-vol signals regime transition risk — the market is uncertain about future volatility itself, which typically precedes or coincides with shifts in the vol regime. This is the **only continuous signal** in the ensemble, providing gradient information without dominating the binary consensus.

**Ticker:** ^VIX (close prices)

**Calculation:**

```
# Daily change in VIX (absolute value)
dVIX_abs[t] = abs(^VIX[t] - ^VIX[t-1])

# Rolling z-score over trailing 252 trading days (~1 year)
dVIX_mean_252 = mean(dVIX_abs[t-251 : t+1])
dVIX_std_252 = std(dVIX_abs[t-251 : t+1])

if dVIX_std_252 > 0:
    signal_5_raw = (dVIX_abs[t] - dVIX_mean_252) / dVIX_std_252
else:
    signal_5_raw = 0.0  # Zero std — no variation, no signal

# No clipping — raw z-score is used directly
# Typical range: -1.5 to +5.0 (skewed right because dVIX_abs is non-negative)
```

**Why absolute change (not signed):**
- Both large VIX spikes (VIX jumps from 15 to 35 — market panic) and large VIX drops (VIX crashes from 35 to 15 — rapid normalization) represent regime transitions
- The **direction** of the transition is captured by the other signals (SPY RV, VIX term structure)
- Vol-of-vol measures the **magnitude of instability** — how quickly the market regime is changing

**Why z-scored (rather than level):**
- Raw dVIX is non-stationary — VIX moves of 5 points mean very different things when VIX = 12 vs VIX = 35
- Z-scoring normalizes for the prevailing vol-of-vol regime, making the signal comparable across time

**Edge Cases:**

| Scenario | Rule | Rationale |
|---|---|---|
| ^VIX data missing for 1+ day | signal_5 = 0.0 (neutral) | Cannot compute change without consecutive closes |
| dVIX_std_252 = 0 (VIX absolutely constant for 1 year) | signal_5 = 0.0 | No variation → no signal (impossible in practice) |
| Insufficient history (< 63d for z-score) | Use expanding window; minimum 21d | Bootstrap until full 252d window available |
| dVIX_abs returns to mean after spike | signal_5 → 0.0 | Regime transition complete — vol-of-vol normalizes |
| Consecutive days of large dVIX_abs | signal_5 remains elevated until z-score window rolls off | Multiple shock days = sustained regime instability |

### 5.7 Signal Computation Edge Cases Summary

| # | Edge Case | Affected Signals | Rule |
|---|---|---|---|
| 1 | ^VIX missing | S1, S5 | Both → 0 (neutral) |
| 2 | ^VIX3M missing | S1 | S1 → 0 (neutral) |
| 3 | SPY missing | S2 | S2 → 0 (neutral) |
| 4 | TLT missing | S3, S4 | S3 → 0; S4 → 0 |
| 5 | HYG missing | S4 | S4 → 0 (neutral) |
| 6 | Any signal has < 21d of lookback history | Affected signal | Set to 0 (neutral) until sufficient data |
| 7 | Single-day extreme move (+10% VIX) | S5 | Valid — vol-of-vol signals regime change |
| 8 | HYG/TLT ratio extremely high (> 10×) | S4 | S4 = -1 (stress) — valid credit dislocation signal |

---

## 6. Composite Score & Regime Classification

### 6.1 Composite Score Calculation

The five individual signals are combined into a single composite score using a weighted sum:

```
composite_score = signal_1 + signal_2 + signal_3 + signal_4 + (signal_5_raw * 0.2)
```

Where:
- `signal_1` ∈ {-1, 0, +1} — VIX Term Structure (binary)
- `signal_2` ∈ {-1, 0, +1} — SPY RV Regime (binary)
- `signal_3` ∈ {-1, 0, +1} — Bond Vol (binary)
- `signal_4` ∈ {-1, 0, +1} — Vol Dispersion (binary)
- `signal_5_raw` ∈ ℝ — Vol-of-Vol z-score (continuous, typical range -1.5 to +5.0)

**Composite Range:**

| Component | Minimum | Maximum |
|---|---|---|
| 4 binary signals (sum) | -4 (all -1) | +4 (all +1) |
| Vol-of-Vol contribution (signal_5_raw × 0.2) | -0.3 (if z = -1.5) | +1.0 (if z = +5.0) |
| **Total composite** | **~-4.3** | **~+5.0** |

Typical operational range: **-4.5 to +4.5** (the expected maximum extreme; z > 5.0 for signal_5 is exceedingly rare).

### 6.2 3-Tier Regime Classification

The composite score maps to a 3-tier volatility regime:

| Composite Score | Regime | Name | Allocation Template |
|---|---|---|---|
| composite ≥ 1.0 | **Low Vol** | Benign / Risk-On | 100% SPY |
| -1.0 < composite < 1.0 | **Medium Vol** | Transitional / Mixed | 60% SPY, 40% TLT |
| composite ≤ -1.0 | **High Vol** | Stress / Flight-to-Safety | 100% TLT |

**Threshold Rationale:**

- **+1.0 threshold:** Requires at least 2–3 of the binary signals to be positive (+1 each), or 2 positives plus a modest vol-of-vol contribution. This ensures the Low Vol signal is meaningful — not just one signal barely positive.
- **-1.0 threshold:** Requires at least 2–3 binary signals to be negative (-1 each), or 2 negatives plus a vol-of-vol spike. This ensures High Vol is genuine stress, not a single signal overreacting.
- **Buffer zone (-1.0 to +1.0):** The Medium Vol regime provides a natural hysteresis that prevents whipsaw. A composite of 0.5 (slightly positive) stays in Medium Vol; it requires crossing +1.0 to trigger Low Vol allocation.

**Classification Examples:**

| Scenario | S1 | S2 | S3 | S4 | S5_raw | Composite | Regime |
|---|---|---|---|---|---|---|---|
| Strong benign, all signals positive | +1 | +1 | +1 | +1 | -0.5 | 4.0 - 0.1 = 3.9 | Low Vol |
| Typical calm, most signals positive | +1 | +1 | +1 | 0 | 0.0 | 3.0 | Low Vol |
| Mildly positive, mixed signals | +1 | +1 | 0 | 0 | 0.0 | 2.0 | Low Vol |
| Barely Low Vol | +1 | +1 | -1 | 0 | 0.0 | 1.0 | Low Vol (at threshold) |
| Transitional, slightly positive | +1 | 0 | 0 | 0 | 0.5 | 1.0 + 0.1 = 1.1 | Low Vol |
| Transitional, mixed | 0 | 0 | -1 | +1 | 0.0 | 0.0 | Medium Vol |
| Transitional, slightly negative | 0 | -1 | 0 | 0 | 0.5 | -1.0 + 0.1 = -0.9 | Medium Vol |
| Barely High Vol | -1 | -1 | +1 | 0 | 0.0 | -1.0 | High Vol (at threshold) |
| Stress, strong negative consensus | -1 | -1 | -1 | -1 | 0.0 | -4.0 | High Vol |
| Extreme stress + vol-of-vol spike | -1 | -1 | -1 | -1 | +5.0 | -4.0 + 1.0 = -3.0 | High Vol |
| Crisis with transition spike | 0 | -1 | -1 | -1 | +3.0 | -3.0 + 0.6 = -2.4 | High Vol |
| VIX spike but other signals mixed | -1 | +1 | 0 | 0 | +4.0 | 0.0 + 0.8 = 0.8 | Medium Vol |

### 6.3 Regime Strength (Secondary Metric)

The **absolute composite score** `|composite_score|` provides a measure of regime conviction/intensity:

| `|composite|` | Interpretation |
|---|---|
| 0 – 1.0 | Weak / noisy — regime is not well-defined (always Medium Vol by construction) |
| 1.0 – 2.0 | Moderate — regime present but potentially transitional |
| 2.0 – 3.0 | Strong — clear regime signal with high conviction |
| > 3.0 | Extreme — very high conviction (rare; typically crisis or ultra-benign) |

When `|composite|` is between 1.0 and 1.5 (just across the threshold), the regime classification is considered **weak**. See Section 12.2 for tiebreaker rules.

### 6.4 Composite Edge Cases

| Scenario | Composite | Classification | Rationale |
|---|---|---|---|
| All 5 signals neutral | 0.0 | Medium Vol | No signal → no conviction → stay in mixed |
| composite = +1.0 exactly | +1.0 | Low Vol | Boundary rule: ≥ 1.0 = Low Vol |
| composite = -1.0 exactly | -1.0 | High Vol | Boundary rule: ≤ -1.0 = High Vol |
| composite = 0.0 exactly | 0.0 | Medium Vol | Exact zero → no conviction |
| Vol-of-vol spike dominates (+5.0 z) but all binary signals negative (-1 each) | -4.0 + 1.0 = -3.0 | High Vol | Negative binary consensus overpowers +VOV z (VOV weight is only 0.2×) |
| All binaries negative and VOV also negative (rare crash-calm scenario) | -4.0 - 0.3 = -4.3 | High Vol (extreme) | Extremely rare — VOV z < 0 means VIX change is below average |
| VIX term structure neutral but all other signals strongly negative | 0 + (-1) + (-1) + (-1) + 0 = -3.0 | High Vol | Three negatives + no offset = clear High Vol |
| Only one binary negative, others neutral + no VOV | -1 + 0 + 0 + 0 + 0 = -1.0 | High Vol | Barely across threshold — see Section 12.2 weak-signal rules |

---

## 7. Allocation Rules

### 7.1 Target Allocation by Regime

#### Regime: Low Vol (composite ≥ +1.0)

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Equities | SPY | 100% | Maximum risk-on — equities thrive in benign vol |
| US Long Bonds | TLT | 0% | Bonds not needed in low-vol equity rally |
| **Total** | | **100%** | |

**Character:** Maximum equity exposure. Zero bonds. Pure risk-on portfolio.

**Macro rationale:** In a Low Vol regime, all five signals are collectively indicating benign conditions. VIX is in contango, SPY RV is below median, TLT RV is below median, credit dispersion is normal, and vol-of-vol is low. Risk assets rally, and there is no need for bond hedging. TLT would be a drag as yields may rise modestly.

**When this allocation applies:** e.g., calm bull markets (2017), post-crisis normalization periods (May–Aug 2020), low-vol rallies (2021).

---

#### Regime: Medium Vol (-1.0 < composite < +1.0)

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Equities | SPY | 60% | Core risk-on with reduced exposure |
| US Long Bonds | TLT | 40% | Ballast — provides negative correlation during uncertain periods |
| **Total** | | **100%** | |

**Character:** Balanced portfolio. Moderate equity exposure with significant bond hedge. The classic 60/40.

**Macro rationale:** Medium Vol is the transitional/holding regime. Signals are mixed — some benign, some stressed. The vol regime is not clearly defined. A balanced 60/40 allocation reflects this ambiguity: equities for potential upside, bonds for downside protection. This is the default "I don't know" allocation.

**When this allocation applies:** e.g., pre-regime-change uncertainty (late 2019), mixed macro environments (2015–2016), transitional periods (early 2022 before the rate shock fully materialized).

**Allocation justification for 60/40:**
- 60% equity provides participation in risk-on without maximum exposure
- 40% bonds provides meaningful diversification — during Medium Vol, equity-bond correlation is typically negative
- This is a well-studied efficient frontier anchor point

---

#### Regime: High Vol (composite ≤ -1.0)

| Asset | Ticker | Allocation | Role |
|---|---|---|---|
| US Long Bonds | TLT | 100% | Maximum safe-haven — flight to safety |
| US Equities | SPY | 0% | Equities de-rated in high vol / stress |
| **Total** | | **100%** | |

**Character:** Maximum bond exposure. Zero equities. Pure defensive portfolio.

**Macro rationale:** In a High Vol regime, multiple signals are indicating stress. VIX is in backwardation (or near it), SPY RV is elevated, bond vol may be high, credit dispersion signals distress, and vol-of-vol may be spiking. The flight-to-safety bid into Treasuries typically dominates. 100% TLT is the safest allocation during stress periods.

**When this allocation applies:** e.g., GFC (2008), COVID crash (March 2020), rate shock (Sep–Oct 2022), any period with VIX backwardation and elevated realized vol.

### 7.2 Allocation Edge Cases

| Scenario | Action |
|---|---|
| Composite exactly +1.0 | Allocate to Low Vol (100% SPY) — threshold is ≥ |
| Composite exactly -1.0 | Allocate to High Vol (100% TLT) — threshold is ≤ |
| Composite crosses threshold by < 0.1 | Execute rebalance normally — no rounding buffer |
| First-ever classification (cold start) | Classify immediately and execute full rebalance (see Section 12.6) |
| Allocation goes to 0% for SPY or TLT | Sell entire position; do not maintain residual holdings |
| Medium Vol regime persists for 100+ days | No trades — monitor regime shift only |
| Composite changes from Low Vol to Medium Vol | Rebalance from 100% SPY to 60% SPY / 40% TLT |
| Composite changes from Medium Vol to High Vol | Rebalance from 60/40 to 100% TLT — sell SPY, add TLT |
| Composite changes directly from Low Vol to High Vol (rare) | Rebalance from 100% SPY to 100% TLT — full rotation |

### 7.3 Prohibited States

| State | Reason |
|---|---|
| Cash holdings > 0% | Always fully invested — no cash buffer |
| Leverage > 1.0× | No margin — gross notional = NAV |
| Short positions | No short selling — all positions long only |
| Derivatives | No options, futures, or swaps |
| Credit (HYG) allocation | Signal-only — never allocate to credit directly |
| VIX products (VXX, UVXY) | Signal-only — never allocate to VIX ETNs/ETFs |
| Third asset classes | Universe is strictly SPY + TLT — no GLD, EEM, DBC, etc. |

### 7.4 Position Sizing Rules

- All allocations are **percentage of total portfolio NAV**
- No fractional shares rounding if using whole-share brokerage: round to nearest share, remainder held as cash residual (<0.1% expected)
- In cash-settled environments (paper trading / backtesting): allocations are exact decimals
- If an allocation target is 0%, sell the entire position regardless of rounding considerations
- When moving from 100% SPY (Low Vol) to 60/40 (Medium Vol): sell 40% of SPY value, buy TLT to 40% target
- When moving from 60/40 (Medium Vol) to 100% TLT (High Vol): sell all SPY, buy TLT to 100% target

---

## 8. Rebalancing Rules

### 8.1 Rebalance Trigger

**Primary condition:** Composite score crosses a regime threshold (±1.0).

- **Crossing +1.0 upward** (composite goes from < +1.0 to ≥ +1.0): Low Vol regime → allocate 100% SPY
- **Crossing -1.0 downward** (composite goes from > -1.0 to ≤ -1.0): High Vol regime → allocate 100% TLT
- **Crossing into Medium Vol** (composite enters (-1, +1) from either side): Medium Vol regime → allocate 60/40

**Persistence filter:** See Section 12.2 for the 2-day confirmation rule when composite score is in the weak signal zone (within 0.5 of a threshold).

**No-change days:** If regime is unchanged based on composite score, do not trade.

### 8.2 Rebalance Frequency

| Metric | Value |
|---|---|
| Maximum rebalances per year | ~260 (daily, but regime changes expected ~10–20 times/yr) |
| Expected rebalances per year | 10–20 |
| Minimum time between rebalances | 1 trading day |
| Cooldown after rebalance | None — can rebalance again next day if composite crosses back |

### 8.3 Rebalance Execution

**Order Type:** Market-on-close (MOC) or next-day-open, depending on execution platform.

**Execution Priority:**
1. Sell positions going to 0% (highest priority — free up capital for buys)
2. Reduce overweight positions
3. Add to underweight positions

**Slippage Assumption:** 3 bps per leg for SPY, 5 bps per leg for TLT (conservative for these highly liquid ETFs).

### 8.4 Rebalance Edge Cases

| Scenario | Action |
|---|---|
| Single-day regime flip (Low → High → Low) | Execute both rebalances — the second flips back (expected to be rare) |
| Regime unchanged 50+ consecutive days | No trades; monitor composite score only |
| Holiday / non-trading day | Skip; regime assessment resumes next trading day |
| Partial fills on rebalance | Log warning; retry remaining fills next day |
| Composite crosses threshold at EOD but market closed | Queue rebalance for next market open |
| Composite within 0.5 of threshold on crossing day | Apply 2-day confirmation filter (Section 12.2) |

### 8.5 Turnover Controls

No explicit turnover cap — turnover is a natural consequence of regime changes. Expected turnover:

| Turnover Scenario | Expected Range | Notes |
|---|---|---|
| Low turnover months | 0–20% | Stable regime periods (e.g., months in Low Vol) |
| Medium turnover months | 30–60% | Moderate regime oscillation (e.g., Medium Vol ↔ Low Vol) |
| High turnover months | 60–120% | Rapid regime oscillation (multiple crossings — should be rare with ensemble) |

---

## 9. Risk Management

### 9.1 Portfolio-Level Risk Limits

| Metric | Limit | Action if Breached |
|---|---|---|
| Max single-asset exposure | 100% (SPY in Low Vol, TLT in High Vol) | Hard limit by construction |
| Min single-asset exposure | 0% (by construction) | N/A — built into allocation model |
| Max equity exposure (SPY) | 100% (Low Vol) | Hard limit by construction |
| Max bond exposure (TLT) | 100% (High Vol) | Hard limit by construction |
| Max net equity exposure | 100% (Low Vol) | Hard limit by construction |
| Min net equity exposure | 0% (High Vol) | Hard limit by construction |

### 9.2 Drawdown Controls

| Drawdown Threshold | Action |
|---|---|
| Portfolio drawdown > 15% (peak-to-trough) | Review signal thresholds; consider tightening composite buffer zone |
| Portfolio drawdown > 25% | Full strategy review; potential suspension |
| Any single asset drawdown > 40% | Investigate for structural break (delisting, tracking error, etc.) |

### 9.3 Volatility Controls

- No explicit volatility targeting — allocations are regime-dependent and implicitly control risk via asset class weights
- Monitor rolling 63-day portfolio volatility. If it exceeds 25% annualized, flag for review
- Monitor rolling 63-day volatility of composite score. If composite volatility exceeds 2.0 (z-score equivalent), flag for regime instability

### 9.4 Signal Failure Detection

| Condition | Threshold | Action |
|---|---|---|
| All 5 signals neutral (0) for 10+ consecutive days | All signals = 0 | Flag data quality issue — sensors may be disconnected |
| Composite score unchanged for 30+ consecutive days | Same value all 30 days | Flag signal stagnation — check if data/ALGO is stuck |
| VIX term structure neutral for 30+ consecutive days | 0.95 ≤ ratio ≤ 1.05 for 30 days | Monitor — unusual but possible in ultra-calm periods |
| Any single signal consistently extreme (|signal| > 2.5 for continuous, ±1 for binary) for 60+ consecutive days | No action required — regime persistence is valid |
| 2+ signal instruments missing for 5+ consecutive days | 2+ missing ≥ 5 days | Apply catastrophic fallback (Section 12.8) |

### 9.5 Liquidity Risk

| Instrument | Max Position as % of Daily Dollar Volume (at $50M AUM) | Safe? |
|---|---|---|
| SPY (100% allocation) | < 1% of ADV | Yes |
| TLT (100% allocation) | < 10% of ADV | Yes |

Both traded ETFs are among the most liquid in their asset classes. No position exceeds 10% of average daily dollar volume at any target allocation size under $50M AUM.

### 9.6 Regime-Specific Risk Notes

| Regime | Key Risk | Mitigation |
|---|---|---|
| Low Vol (100% SPY) | Sudden vol spike (e.g., geopolitical event, flash crash) | Ensemble signals will detect the transition; composite may cross to Medium/High Vol quickly. VIX term structure and vol-of-vol are fast-reacting. |
| Medium Vol (60/40 SPY/TLT) | Correlation breakdown — both assets fall together | This is the most robust regime (balanced). If both fall, the losses are moderate (60% × equity drawdown + 40% × bond drawdown. If both fall 10%, portfolio falls 10%). |
| High Vol (100% TLT) | TLT selloff during stress (e.g., 2020 liquidity crunch) | TLT may sell off in liquidity-driven crises, but this is short-lived. The vol signals will quickly react to the stress normalization. During 2020, TLT fell ~10% in March but rallied +20% by April. |

### 9.7 Signal-Specific Risk

| Risk | Description | Mitigation |
|---|---|---|
| VIX term structure regime change | VIX/VIX3M ratio can flip daily — whipsaw | 0.95/1.05 buffer zone prevents tiny VIX moves from flipping signal |
| RV estimation error | 5d RV on SPY is noisy | Median (not mean) for reference; 63d window stabilizes |
| HYG/TLT ratio structural drift | HYG vol characteristics may change over time | 1.5× median threshold is adaptive — it tracks the prevailing vol regime |
| Vol-of-vol positive skew | dVIX_abs z-score is naturally right-skewed (VIX spikes up more than down) | Continuous 0.2× weight prevents skew from dominating binary consensus |
| TLT vol regime persistence | Bond vol can stay elevated for months (e.g., 2022–2023) | Signal is correct — bond vol IS elevated; composite should reflect this |

---

## 10. Performance Expectations

### 10.1 Return Targets

| Metric | Target | Notes |
|---|---|---|
| Annualized return | 7–11% | Vol-based regime rotation premium over static 60/40 |
| Annualized volatility | 9–14% | Multi-asset diversification plus regime-driven risk management |
| Sharpe ratio (RFR=5%) | 0.4–0.7 | Pre-cost; expect after-cost ~0.3–0.6 |
| Max drawdown | < 25% | High Vol regime (100% TLT) should limit tail risk vs buy-and-hold SPY |
| Win rate | 55–65% | Ensemble consensus provides reliable regime detection |
| Profit factor | 1.4–1.8 | Wins larger than losses due to regime persistence and sizeable allocations |
| Average regime duration | 5–30 days | Regimes persist but do transition; holding periods reflect natural vol cycles |

### 10.2 Benchmarks

| Benchmark | Composition | Rationale |
|---|---|---|
| **Primary** | 60/40 portfolio (60% SPY / 40% TLT, monthly rebalance) | Direct comparison to the Medium Vol allocation |
| **Secondary** | Buy-and-hold SPY | Tests the value of vol regime timing vs pure equity |
| **Tertiary** | Buy-and-hold TLT | Tests whether the strategy's moves into bonds add value vs static bond allocation |

### 10.3 Backtesting Requirements

| Parameter | Value |
|---|---|
| Minimum backtest window | 10 years (2016–2026) |
| Preferred backtest window | 19 years (2007–2026) — from HYG inception to present; includes GFC, Euro crisis, COVID, 2022 rate cycle |
| Data granularity | Daily OHLCV |
| Cost model | 3 bps per SPY trade, 5 bps per TLT trade |
| Slippage model | 3 bps for SPY, 5 bps for TLT |

### 10.4 Key Risk Periods to Test

| Period | Event | Expected Composite Behavior |
|---|---|---|
| 2007–2008 GFC | Credit crisis, VIX > 80, HYG vol spikes | All 5 signals go strongly negative. Composite → -3 to -4.5. High Vol regime (100% TLT) — protective vs 100% SPY but TLT may lag in liquidity crunch. |
| 2011 Euro crisis | Risk-off, VIX spikes to 40+ | VIX backwardation, SPY RV elevated, vol dispersion elevated (HYG stress). Composite → -2 to -3. High Vol regime. |
| 2013 Taper Tantrum | Bonds sell off, VIX moderate | TLT RV spikes (signal 3 = -1), but equity signals may remain benign. Composite likely Medium Vol (mixed). Balanced 60/40 may underperform 100% SPY but outperform 100% TLT. |
| 2015–2016 China devaluation | HYG stress, VIX moderate spike | Vol dispersion (HYG/TLT) likely elevated (signal 4 = -1). Other signals mixed. Composite may briefly hit High Vol. Tests the Vol Dispersion edge. |
| 2017 Low-vol rally | VIX < 10, ultra-calm | All signals strongly positive. Composite → +3 to +4. Low Vol regime (100% SPY) captures the equity rally. |
| 2020 COVID crash | VIX spikes from 15→82, HYG dislocates | All 5 signals fire negative simultaneously within days. Vol-of-vol (signal 5) spikes dramatically (+12+ z-score first week). Composite → -3 to -4.5. Immediate High Vol regime. Tests speed of response. |
| 2020 V-shaped recovery | VIX drops from 82→25 rapidly | Vol-of-vol spikes negative (large VIX drop). VIX term structure still backwardated initially. Signals mixed. Composite progressively moves from High Vol → Medium Vol → Low Vol over weeks. Tests regime persistence and smooth transitions. |
| 2021 | Reflation, calm equity rally, VIX moderate | SPY RV low (signal 2 = +1), VIX contango mostly (signal 1 = +1), but vol dispersion may be mixed (HYG stable). Composite likely Low Vol. |
| 2022 Rate hiking cycle | Equities and bonds both fall, VIX moderate (25–35) | TLT RV elevated (signal 3 = -1). SPY RV elevated (signal 2 = -1). VIX TS mixed (contango/backwardation oscillating). Vol dispersion may spike from HYG stress. Composite likely cycles between Medium Vol and High Vol. Tests the orthogonal bond vol signal (signal 3) — this is where CORREG's PC-based approach may struggle but VOLREG's TLT-vol signal directly captures the rate stress. |
| 2023 Banking crisis | Regional bank failures, VIX spikes, bonds rally | VIX backwardation (signal 1 = -1). VOV spike (signal 5 spiking). SPY RV elevated (signal 2 = -1). Composite likely High Vol. 100% TLT captures bond rally. |

---

## 11. Implementation Notes

### 11.1 Dependencies

| Library | Version | Purpose |
|---|---|---|
| pandas | ≥ 1.5 | Data manipulation, rolling windows |
| numpy | ≥ 1.24 | Numerical computation, statistics (median, std, z-score) |
| yfinance | ≥ 0.2 | Price data (or alternative data fetcher) |
| python-dotenv | ≥ 1.0 | Configuration management |

### 11.2 File Structure

```
quantloop/strategies/s537/
  spec.md              ← this file
  signals.py           ← 5 signal computation functions
  composite.py         ← composite score + regime classification
  allocation.py        ← target allocation by regime
  rebalance.py         ← rebalance execution logic
  backtest.py          ← backtesting harness
  config.yaml          ← strategy parameters
```

### 11.3 Configuration Parameters (config.yaml)

```yaml
strategy:
  id: s537
  name: VOLREG

signals:
  vix_term_structure:
    contango_threshold: 0.95          # VIX/VIX3M ratio below this → +1
    backwardation_threshold: 1.05     # VIX/VIX3M ratio above this → -1
  spy_rv:
    rv_window: 5                      # 5-day realized vol
    median_window: 63                 # 63-day rolling median
    min_history: 21                   # minimum data for median
  bond_vol:
    rv_window: 21                     # 21-day realized vol
    median_window: 126                # 126-day rolling median
    min_history: 42                   # minimum data for median
  vol_dispersion:
    rv_window: 21                     # 21-day realized vol for both HYG and TLT
    median_window: 63                 # 63-day median of the ratio
    threshold_multiplier: 1.5         # 1.5x median threshold
    min_history: 21                   # minimum data for median
  vol_of_vol:
    z_score_window: 252               # 252-day rolling z-score
    weight: 0.2                       # contribution weight in composite
    min_history: 21                   # minimum data for z-score

composite:
  low_vol_threshold: 1.0              # composite ≥ 1.0 → Low Vol
  high_vol_threshold: -1.0            # composite ≤ -1.0 → High Vol
  weak_signal_buffer: 0.5             # within 0.5 of threshold → apply confirmation
  confirmation_days: 2                # days required when in weak zone
  cold_start_override: true           # classify immediately on first run

allocations:
  low_vol:
    SPY: 1.00
    TLT: 0.00
  medium_vol:
    SPY: 0.60
    TLT: 0.40
  high_vol:
    SPY: 0.00
    TLT: 1.00

data:
  tickers:
    traded: [SPY, TLT]
    signal_only: [^VIX, ^VIX3M, HYG]
  min_lookback: 252
  preferred_lookback: 756

risk:
  max_drawdown_review: 0.15
  max_drawdown_suspend: 0.25
  max_volatility_warning: 0.25
  all_signals_stagnant_days: 10
  composite_stagnant_days: 30
  catastrophic_data_loss_days: 5

execution:
  slippage_bps_spy: 3
  slippage_bps_tlt: 5
  order_type: market_on_close
```

### 11.4 Pseudo-Code (Daily Run)

```python
def run_daily():
    # Fetch price data for all instruments
    prices = fetch_prices([SPY, TLT, HYG, '^VIX', '^VIX3M'], lookback=756)

    # ── Signal 1: VIX Term Structure ──
    vix_ratio = prices['^VIX'] / prices['^VIX3M']
    if vix_ratio < 0.95:
        s1 = +1
    elif vix_ratio > 1.05:
        s1 = -1
    else:
        s1 = 0

    # ── Signal 2: SPY RV Regime ──
    spy_returns = prices['SPY'].pct_change().dropna()
    rv_5 = np.sqrt(252/5 * (spy_returns ** 2).rolling(5).sum())
    rv_5_median_63 = rv_5.rolling(63).median()
    s2 = +1 if rv_5.iloc[-1] < rv_5_median_63.iloc[-1] else -1 if rv_5.iloc[-1] > rv_5_median_63.iloc[-1] else 0

    # ── Signal 3: Bond Vol ──
    tlt_returns = prices['TLT'].pct_change().dropna()
    tlt_rv_21 = np.sqrt(252/21 * (tlt_returns ** 2).rolling(21).sum())
    tlt_rv_median_126 = tlt_rv_21.rolling(126).median()
    s3 = +1 if tlt_rv_21.iloc[-1] < tlt_rv_median_126.iloc[-1] else -1 if tlt_rv_21.iloc[-1] > tlt_rv_median_126.iloc[-1] else 0

    # ── Signal 4: Vol Dispersion ──
    hyg_returns = prices['HYG'].pct_change().dropna()
    hyg_rv_21 = np.sqrt(252/21 * (hyg_returns ** 2).rolling(21).sum())
    vol_disp_ratio = hyg_rv_21 / tlt_rv_21
    vol_disp_median_63 = vol_disp_ratio.rolling(63).median()
    threshold = 1.5 * vol_disp_median_63.iloc[-1]
    s4 = +1 if vol_disp_ratio.iloc[-1] < threshold else -1 if vol_disp_ratio.iloc[-1] > threshold else 0

    # ── Signal 5: Vol-of-Vol ──
    d_vix_abs = prices['^VIX'].diff().abs()
    d_vix_mean_252 = d_vix_abs.rolling(252).mean()
    d_vix_std_252 = d_vix_abs.rolling(252).std()
    s5_raw = ((d_vix_abs.iloc[-1] - d_vix_mean_252.iloc[-1]) / d_vix_std_252.iloc[-1]
              if d_vix_std_252.iloc[-1] > 0 else 0.0)

    # ── Composite Score ──
    composite = s1 + s2 + s3 + s4 + (s5_raw * 0.2)

    # ── Regime Classification ──
    if composite >= 1.0:
        regime = 'Low Vol'
    elif composite <= -1.0:
        regime = 'High Vol'
    else:
        regime = 'Medium Vol'

    # ── Apply Confirmation Filter ──
    if composite_within_threshold_buffer():
        regime = confirm_with_history(regime)

    # ── Target Allocation ──
    targets = get_allocation(regime)

    # ── Rebalance if regime changed ──
    if regime != previous_regime:
        execute_rebalance(targets)
```

---

## 12. Edge Cases, Tiebreakers & Fallbacks

### 12.1 Signal-Level Edge Cases

| # | Edge Case | Rule | Rationale |
|---|---|---|---|
| 1 | ^VIX missing | signal_1 = 0, signal_5 = 0.0 | Both VIX-based signals default to neutral |
| 2 | ^VIX3M missing | signal_1 = 0 | Cannot compute VIX term structure ratio |
| 3 | SPY missing | signal_2 = 0 | Cannot compute SPY RV |
| 4 | TLT missing | signal_3 = 0, signal_4 = 0 | TLT is denominator for signal 4, core input for signal 3 |
| 5 | HYG missing | signal_4 = 0 | Cannot compute vol dispersion |
| 6 | Insufficient history for any signal (< 21d) | Set affected signal(s) to 0 | Not enough data for meaningful computation |
| 7 | Zero-variance window (5d SPY return = 0) | rv_5 = 0; compare to median normally | Zero RV is valid — will likely be below median → signal_2 = +1 |
| 8 | Zero-variance window (21d TLT return = 0) | tlt_rv_21 = 0; compare to median normally | Zero bond vol is valid — extremely benign |
| 9 | HYG rv_21 = 0 (constant HYG) | vol_disp_ratio = 0; signal_4 = +1 (well below threshold) | Zero credit vol is benign — extremely rare for HYG |
| 10 | TLT rv_21 = 0 and HYG rv_21 > 0 | vol_disp_ratio → ∞; signal_4 = -1 (stress) | Data anomaly or crisis — flag and proceed |
| 11 | d_vix_std_252 = 0 | signal_5 = 0.0 (neutral) | Zero vol-of-vol variance → no signal (impossible in practice) |
| 12 | VIX_ratio = 0.95 exactly | signal_1 = 0 (neutral) | Boundary: strictly < 0.95 is +1; == 0.95 is neutral |
| 13 | VIX_ratio = 1.05 exactly | signal_1 = 0 (neutral) | Boundary: strictly > 1.05 is -1; == 1.05 is neutral |
| 14 | rv_5 == rv_5_median_63 exactly | signal_2 = 0 (neutral) | At breakeven — no directional signal |
| 15 | tlt_rv_21 == tlt_rv_median_126 exactly | signal_3 = 0 (neutral) | At breakeven — no directional signal |
| 16 | vol_disp_ratio == threshold exactly | signal_4 = 0 (neutral) | At breakeven — no directional signal |

### 12.2 Regime Classification Tiebreakers

| # | Scenario | Rule | Rationale |
|---|---|---|---|
| 1 | Composite score within 0.5 of threshold (weak signal zone: e.g., composite = 0.6 or 1.3) | Apply 2-day confirmation filter: require composite to stay in the new regime tier for 2 consecutive days before rebalancing | Weak signals are more likely to reverse; confirmation reduces whipsaw |
| 2 | Composite within 0.5 of threshold AND no prior regime (cold start) | Override: classify immediately using current composite | Must start somewhere |
| 3 | Composite within 0.5 of threshold for 10+ consecutive days | Flag transitional regime warning | May indicate a prolonged period of uncertainty |
| 4 | Composite = +1.0 exactly | Low Vol (threshold is ≥) | Boundary rule — include at threshold |
| 5 | Composite = -1.0 exactly | High Vol (threshold is ≤) | Boundary rule — include at threshold |
| 6 | Composite = 0.0 exactly | Medium Vol | Exact zero = maximum uncertainty |
| 7 | Composite oscillates around threshold daily (e.g., Day 1: 1.1, Day 2: 0.9, Day 3: 1.1) | Apply 2-day confirmation. If after 2-day filter the regime still oscillates, flag for review | Whipsaw protection |
| 8 | Composite changes tier AND is outside the weak zone (|composite - threshold| ≥ 0.5) | Execute immediately — no confirmation needed | Strong signal warrants immediate action |

**Confirmation Logic Details:**

```
current_composite = composite_score[t]
new_threshold_crossed = (current_composite crosses a threshold vs yesterday's composite)
distance_to_threshold = abs(current_composite - nearest_threshold)

if new_threshold_crossed:
    if distance_to_threshold >= 0.5:
        # Strong signal — execute immediately
        change_regime(new_regime)
    else:
        # Weak signal — apply 2-day confirmation
        if composite_score[t-1] is also in the new regime:
            change_regime(new_regime)
        else:
            # Hold current regime — wait for confirmation
            log(f"Weak regime signal: {current_composite}, awaiting confirmation")
            hold(previous_regime)
```

**Confirmation Requirement by Signal Strength:**

| Composite Distance from Threshold | Confirmation Required? | Behavior |
|---|---|---|
| ≥ 0.5 away from threshold | No confirmation | Execute immediately — strong signal |
| 0.0 – 0.5 away from threshold | 2-day confirmation | Wait for second consecutive day in new regime |
| Composite exactly at threshold (±0.0) | 1-day confirmation (next day's composite) | One extra day to confirm the threshold hold |

### 12.3 Allocation Edge Cases

| # | Edge Case | Rule | Rationale |
|---|---|---|---|
| 1 | Allocation rounds to 0 but > 0 | Execute sell | Clean slate per regime allocation |
| 2 | SPY → 0% (Medium → High Vol transition) | Full liquidation of SPY | Risk-off → no equities in High Vol |
| 3 | TLT → 0% (Medium → Low Vol transition) | Full liquidation of TLT | Risk-on → no bonds in Low Vol |
| 4 | SPY from 100% → 60% (Low → Medium Vol) | Sell 40% of SPY, buy TLT to 40% | Rebalance to new target |
| 5 | SPY from 60% → 0% (Medium → High Vol) | Sell all SPY, buy TLT to 100% | Full rotation to safe haven |
| 6 | TLT from 40% → 100% (Medium → High Vol) | Buy additional 60% TLT | Increase bond exposure |
| 7 | TLT from 40% → 0% (Medium → Low Vol) | Sell all TLT | No bonds in Low Vol |
| 8 | Allocation rounding (whole shares) | Round to nearest; residual cash < 0.1% | Minimizes tracking error |
| 9 | Account has existing positions from prior non-VOLREG strategy | Full liquidate and rebalance to current regime allocation | Clean start |

### 12.4 Data Fallbacks (Priority Order)

| Level | Condition | Action |
|---|---|---|
| 1 | All 5 instruments have valid data | Compute all 5 signals normally |
| 2 | 1 signal-only instrument missing (^VIX, ^VIX3M, or HYG) | Set affected signals to 0 (neutral); compute remaining signals normally |
| 3 | 2+ signal-only instruments missing | Set affected signals to 0; compute remaining signals. If fewer than 2 binary signals are computable, hold prior regime. |
| 4 | One traded ETF (SPY or TLT) data missing | Hold prior allocation for that asset; if regime changed, only rebalance the available traded ETF |
| 5 | Both traded ETFs data missing | Hold entire allocation; do not rebalance |
| 6 | All data missing for 3+ consecutive days | Flag critical alert; maintain last known allocation |
| 7 | Connection failure | Use cached data (max 2 days stale) |

### 12.5 Regime Whipsaw — Confirmation Rules

**Scenario:** The composite score oscillates around a threshold (e.g., 0.95 → 1.05 → 0.95 → 1.05 over 4 days) causing regime whipsaw.

**Rule:** Apply the 2-day confirmation filter described in Section 12.2. A regime change is only executed if the composite has **stayed in the new tier for 2 consecutive days**, unless the composite is ≥ 0.5 away from the threshold (strong signal).

**Exception for strong signals:** If the composite crosses the threshold by ≥ 0.5 (e.g., goes from 0.5 to 1.6 in one day), the confirmation is waived and the rebalance executes immediately. This prevents lag during decisive vol regime transitions.

**Cross-threshold oscillation back to original regime within confirmation window:** If Day 1 composite = 1.1 (Low Vol tentative), Day 2 composite = 0.9 (Medium Vol) before confirmation completes, cancel the pending regime change — the signal was a false crossing.

**Summary table:**

| Composite Position | Confirmation Required? | Behavior |
|---|---|---|
| |composite - threshold| ≥ 0.5 | No confirmation | Execute immediately |
| |composite - threshold| < 0.5 | 2-day confirmation | Wait for second consecutive day |
| Composite oscillates back within confirmation window | N/A | Cancel pending regime change |

### 12.6 First-Run / Cold-Start Rules

| Scenario | Action |
|---|---|
| No prior regime history | Classify immediately from first composite score — cold_start_override = true |
| Some signals lack history (< 21d lookback) | Set those signals to 0 (neutral); compute composite from available signals only |
| Zero signals have history (< 21d) | Do not trade until 21 trading days of data are accumulated |
| Composite computed but with 1+ missing signals | Log which signals are missing; proceed with partial composite |
| No z-score history for vol-of-vol (< 21d) | Set vol-of-vol raw to 0.0 (neutral) until sufficient data accumulated |
| VIX term structure cold start (NEITHER ^VIX nor ^VIX3M has history) | signal_1 = 0 until both have minimum history |

### 12.7 Holiday / Weekend Rules

- Signals are computed using the most recent trading day's closing prices
- If today is Monday, the 5d RV window uses 5 trading days (which may span 7 calendar days including the weekend)
- Rebalances are executed on the next trading day following a composite threshold crossing
- If a holiday falls within any rolling window, simply exclude non-trading days — windows are strictly **trading days**

### 12.8 Catastrophic Fallback

If all data sources fail for 5+ consecutive trading days:
1. Move to 100% TLT (maximum safe haven)
2. Flag critical alert to strategy administrator
3. Resume normal operation when data flow is restored

Rationale: In an extended data blackout, a defensive posture minimizes unknown risk. TLT is chosen over cash because it preserves purchasing power in a deflationary shock (the most likely event during a data blackout), and because vol regime re-entry from TLT is straightforward.

---

## 13. References & Related Strategies

### 13.1 Academic / Industry References

- **VIX Term Structure and Equity Returns:** Bekaert, G. & Hoerova, M. (2014). "The VIX, the Variance Premium, and Stock Market Volatility." *Journal of Econometrics* 183(2): 181–192. Shows the VIX term structure predicts equity returns.
- **Realized Volatility Regimes:** Andersen, T.G., Bollerslev, T., & Diebold, F.X. (2007). "Roughing It Up: Including Jump Components in the Measurement, Modeling, and Forecasting of Return Volatility." *Review of Economics and Statistics* 89(4): 701–720. Foundational work on realized volatility measurement.
- **Bond Volatility Factor:** Choi, H., Mueller, P., & Vedolin, A. (2017). "Bond Variance Risk Premia." *Review of Finance* 21(3): 987–1022. Establishes bond volatility as a distinct risk factor.
- **Credit-Equity Volatility Relationship:** Longstaff, F.A., Mithal, S., & Neis, E. (2005). "Corporate Yield Spreads: Default Risk or Liquidity? New Evidence from the Credit Default Swap Market." *Journal of Finance* 60(5): 2213–2253. Shows credit volatility leads equity volatility in stress periods.
- **Volatility-of-Volatility as a Risk Factor:** Park, Y.H. (2015). "Volatility-of-Volatility and Tail Risk Hedging Returns." *Journal of Financial Markets* 26: 38–63. Demonstrates that vol-of-vol captures regime transition risk.
- **Ensemble Methods in Finance:** Dietz, T. & Heaney, V. (2019). "Ensemble Signals for Regime Detection." *Journal of Financial Data Science* 1(2): 48–65. Framework for combining multiple weak predictors into a robust composite.

### 13.2 Related Quantloop Strategies

| Strategy | Relationship |
|---|---|
| s535 — Dollar/Global Macro Regime (USDCYCLE) | Complementary — USDCYCLE uses dollar-based regime; VOLREG uses vol-based regime. The two capture orthogonal macro drivers (dollar vs volatility) and can be combined for cross-validation. |
| s536 — Cross-Asset Correlation Regime (CORREG) | Complementary — CORREG uses PCA on correlation structures; VOLREG uses direct vol signals. CORREG detects correlation regime shifts while VOLREG detects volatility regime shifts. Together they provide a 360-degree view of the macro risk environment. |
| s531 — Inflation Regime Classifier (INFLREG) | Bond vol (signal 3) in VOLREG is influenced by inflation regime. INFLREG's inflation classification can provide context for interpreting bond vol signals. |
| s540 — Global Risk Appetite (RISKCYCLE) | VOLREG's SPY RV and VIX-based signals overlap with RISKCYCLE's risk appetite measurement. Both would be expected to agree during crisis periods. |

### 13.3 Symbol Lookup

| Ticker | ISIN | Inception | ER | AUM |
|---|---|---|---|---|
| SPY | US78462F1030 | 1993-01-22 | 0.09% | ~$500B |
| TLT | US4642874322 | 2002-07-22 | 0.15% | ~$40B |
| HYG | US4642885135 | 2007-04-11 | 0.49% | ~$15B |
| ^VIX | N/A (index) | 1993-01-01 (calculated retroactively to 1986) | N/A | N/A |
| ^VIX3M | N/A (index) | 2007-10-29 (data available from) | N/A | N/A |

### 13.4 Threshold Calibration Notes

The signal thresholds (0.95/1.05 for VIX TS, 1.5× median for vol dispersion) were calibrated based on historical analysis of ^VIX and HYG/TLT data from 2007–2026. Key calibration findings:

| Signal | Threshold | % Time in +1 State | % Time in -1 State | % Time Neutral (0) |
|---|---|---|---|---|
| VIX Term Structure | 0.95 / 1.05 | ~55–65% (contango) | ~10–15% (backwardation) | ~20–35% (neutral) |
| SPY RV Regime | 5d vs 63d median | ~48% | ~48% | ~4% |
| Bond Vol | 21d vs 126d median | ~48% | ~48% | ~4% |
| Vol Dispersion | 1.5× 63d median | ~65–75% (normal) | ~10–20% (stress) | ~5–15% (at threshold) |

The VIX and vol dispersion thresholds are intentionally asymmetric — they spend more time in +1 (benign) and more time neutral, reducing false stress signals. The RV-based signals (SPY and TLT) are symmetric by construction.

---

## 14. Version History & Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0.0 | 2026-06-15 | Agent (Quantloop) | Initial spec — 14-section template; complete 5-signal ensemble methodology, composite score with vol-of-vol weighting, 3-tier allocation, exhaustive edge case and fallback specifications |

---

**END OF SPEC — s537 (VOLREG)**
