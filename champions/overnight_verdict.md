# Buy-at-Close / Sell-at-Open Overnight Strategy — Full Analysis

**Tested across:** ~160 tickers (77 + 83) | **Data:** 2015–2026 (11.5 years) | **Costs:** 10bps per trade

---

## MU (where this started) — Deep Dive

| Metric | Overnight (gross) | Overnight (net) | Intraday | Full Day |
|--------|:-:|:-:|:-:|:-:|
| Ann Ret | +37.4% | +12.2% | +4.3% | +42.2% |
| Ann Vol | 31.5% | 31.5% | 38.4% | 50.4% |
| Sharpe | **+1.185** | **+0.386** | +0.113 | +0.837 |
| Win Rate | 55.2% | 51.7% | 50.2% | 51.5% |
| T-Stat | +4.00*** | +1.30 | +0.38 | +2.83*** |
| Max DD | -53.7% | -72.0% | -79.9% | -71.7% |
| Cumulative | **40.43x** | — | **0.71x** | 28.96x |

**Massive finding:** MU's cumulative return is 40.43x from overnight gaps, while intraday trading DESTROYED value (0.71x). The stock's entire positive return comes from close-to-open moves. This is the **Overnight Drift Anomaly** (Heston et al 2010).

---

## Across ALL Stocks — The Real Picture

| Metric | Value |
|--------|:-:|
| Mean Sharpe | **-0.80** |
| Median Sharpe | **-0.78** |
| % Positive Sharpe | **14%** (11/77) |
| % Statistically Significant Positive | **2.6%** (only ^VIX + NVDA) |
| % Statistically Significant Negative | **65%** |

**The strategy loses money for 86% of stocks.** Not just "not worth it" — actively destructive.

---

## What Predicts Positive Overnight Edge?

### Volatility is the ONLY predictor

| Quartile | Vol Range | Mean Sharpe | % Positive |
|:--------:|:--------:|:-----------:|:---------:|
| Low (Q1) | 0.6–0.9%/day | **-1.79** | 0% |
| Q2 | 0.9–1.2%/day | **-1.01** | 0% |
| Q3 | 1.2–1.8%/day | **-0.51** | 10% |
| High (Q4) | 1.9–7.9%/day | **+0.05** | **50%** |

### Sector Breakdown

| Group | Count | Mean Sharpe | % Positive | Best (SR) |
|-------|:----:|:-----------:|:---------:|:---------:|
| **High Growth/Momentum** | 19 | **+0.145** | **53%** | MARA (+1.20) |
| Semiconductors | 16 | -0.152 | 38% | NVDA (+0.61) |
| High Beta / Crypto | 5 | -0.114 | 40% | MSTR (+0.32) |
| Mega-cap Tech | 7 | -0.373 | 29% | AMZN (+0.21) |
| Financials | 8 | -0.708 | **0%** | MS (-0.54) |
| Energy/Industrial | 7 | -0.726 | **0%** | BA (-0.35) |
| Healthcare | 7 | -1.203 | **0%** | LLY (-0.53) |
| Consumer Stable | 8 | -1.272 | **0%** | DIS (-0.91) |
| International ETFs | 13 | -1.348 | **0%** | EWZ (-0.52) |
| ETFs (all types) | 18 | **-1.661** | **0%** | SLV (-0.18) |

---

## Crypto/Miners — False Positive

MARA (SR=+1.20), RIOT (SR=+1.16) show enormous overnight edges but they're **NOT alpha**:

| Year | MARA ON Ret | RIOT ON Ret | Context |
|:----:|:----------:|:----------:|:--------|
| 2016 | -54% | -89% | Early cycle valley |
| 2017 | **+287%** | **+89%** | BTC bubble |
| 2020 | **+379%** | **+324%** | COVID/crypto surge |
| 2022 | **-76%** | **-79%** | Crypto winter |
| 2023 | **+112%** | **+85%** | Recovery |

**R² with BTC-USD overnight:** only 7–14%. These are super-levered crypto proxies with lottery-ticket returns. Cannot be size-positioned.

---

## What About Portfolios?

| Portfolio | Tickers | Net Sharpe | Max DD | Years Positive |
|:---------:|:-------:|:---------:|:-----:|:-------------:|
| **Crypto** (MARA, RIOT, MSTR) | 3 | **1.185** | -77.2% | 7/11 |
| **Semis** (NVDA, AMD, MU, AVGO) | 4 | **0.575** | -53.7% | 9/12 |
| ^VIX (not tradeable) | 1 | **+3.249** | -49.9% | — |

The semi portfolio is the closest thing to a real strategy: consistent positive years (9/12), SR=0.58. But -53.7% max DD and 10bps eats 2/3 of gross edge.

---

## Key Patterns Discovered

### 1. The Volatility Tiering Effect (CLEANEST PATTERN)
Overnight edge is a pure function of daily volatility. Low-vol stocks ALWAYS lose money overnight. High-vol stocks sometimes win. The breakpoint is ~1.7%/day daily vol.

### 2. The Overnight Drift Decomposition (MU)
MU's full returns are 100% from overnight gaps. Intraday MU is a zero-sum game. This holds for the semis group generally — the edge is in the gap, not the day session.

### 3. The Cost Wall
At 10bps/trade (5bps spread + 5bps slippage), the annual cost is 10bps × 252 = **25.2% turnover-adjusted**. For a stock with +5% annual overnight edge, costs consume the entire alpha. Only stocks with >15% annual overnight edge survive.

### 4. Zero Predictability
- Overnight return autocorrelation: **near zero at all lags** (no sequential pattern)
- No reliable after-down-day vs after-up-day difference
- Day-of-week patterns exist but vary by stock (no universal pattern)

---

## Verdict

> **❌ Buy-at-close / sell-at-open is NOT a tradeable strategy for most stocks.**

| Question | Answer |
|----------|:------:|
| Does MU have overnight edge? | **Yes** — SR=+1.19 gross, +0.39 net. Real. |
| Can you trade this systematically? | **No** — zero predictability, -72% DD, 10bps kills it |
| Does this work on other stocks? | **Only 14%** — exclusively high-vol names |
| Is there a pattern to find winners? | **Weak** — volatility >1.7%/day is a necessary filter |
| Does the crypto miner edge persist? | **No** — it's just levered crypto exposure, year-to-year is flip-flop |

**The real discovery here isn't the strategy — it's the decomposition.** MU's returns happen entirely in the overnight gap, and intraday trading is value-destructive. That's worth studying further (what drives overnight gaps? news? earnings? market-microstructure?).

---

## Data Files Created

| File | Contents |
|:----|:---------|
| `overnight_test.py` | Phase 1-4: MU deep dive + 77 ticker universe + patterns |
| `overnight_phase5.py` | Phase 5: 83 more tickers + volatility quartile analysis |
| `overnight_phase6.py` | Phase 6: Crypto/miner deep dive + portfolio tests |
| `overnight_verdict.md` | This file — consolidated findings |
