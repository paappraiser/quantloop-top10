# Quantloop — Top  Champion Strategies

Autonomous systematic strategy research — quantitative trading strategies generated, backtested, and curated by an LLM agent (Hermes Quant). Top strategies from 550+ iterations across regime detection, trend following, mean reversion, dispersion arbitrage, earnings drift, and alt-asset momentum.

**All strategies pass a strict evaluation harness:**
- Walk-forward (expanding 5yr window, retrain every 252d, 21d embargo)
- Net of costs (10 bps per side equities/ETFs, 20 bps crypto, 50 bps/yr short borrow)
- Volatility targeting to 10% annualized
- Per-position cap 10%, gross exposure cap 200%
- Drawdown gates: halve at 20%, flat at 30%
- Minimum 100 trades, max 35% drawdown, deflated Sharpe > 0

---

## 🏆 Top 5 Champions

| Rank | ID | Strategy | SCORE | Max DD | Trades | TO | Edge |
|------|-----|----------|-------|--------|--------|----|------|
| **1** | **s542** | **QQQ/SPY Dispersion** | **1.182** | -4.4% | 163 | 1.5× | Stat-arb mean reversion on QQQ/SPY ratio |
| **2** | **s575** | **Alt-Asset Trend (ALTTREND)** | **1.065** | -14.0% | 187 | 1.2× | TS mom on 7 alt-asset managers (BAM/KKR/APO/BX/ARES/CG/TPG) |
| **3** | **s546** | **Post-Earnings Drift (EARNPEAD)** | **0.988** | -8.5% | 340 | 12.4× | Cross-sectional PEAD S&P 100, top5/b5 by earnings surprise |
| **4** | **s532** | **Risk Appetite Regime (RISKREG)** | **0.961** | -3.6% | 166 | 1.4× | 4-signal risk gauge (credit+VIX+corr+gold) |
| **5** | **s578** | **Alt-MOM (lb=252)** | **1.057** | -13.5% | 189 | 1.0× | TS mom lb=252 on 7 alt-asset managers |

---

## Strategy Families

### 1. QQQ/SPY Dispersion (SR 1.182 — Overall Champion)

| ID | Variant | SR | DD | TO | Description |
|----|---------|----|-----|-----|-------------|
| **s542** | **DISPERSION** | **1.182** | -4.4% | 1.5× | QQQ/SPY ratio z-score (252d) mean reversion |

A 2-asset stat-arb strategy. When the QQQ/SPY ratio is more than 1 z-score from its 252-day mean, bet on reversion. The edge comes from the structural mean-reverting relationship between Nasdaq-100 and S&P 500 — both respond to similar macro forces but at different speeds. QQQ/SPY ratio is a cointegrated pair on daily data.

- **Entry**: ratio z-score < -1 → long QQQ, short SPY; z-score > +1 → short QQQ, long SPY
- **Exit**: z-score returns toward zero (or flips sign)
- **Portfolio**: 50/50 equal-weight on the two active legs (100% gross each direction)

### 2. Alt-Asset Manager TS Momentum (SR 1.02–1.06)

| ID | Variant | SR | DD | TO | Lookback |
|----|---------|------|-----|-----|----------|
| **s575** | **ALTTREND** | **1.065** | -14.0% | 1.2× | 126d |
| s578 | ALT-MOM | 1.057 | -13.5% | 1.0× | 252d |
| s581 | ALT-GAP | 1.034 | -14.7% | 0.7× | 42d/gap=7 |
| s582 | ALT-GAP | 1.034 | -14.7% | 0.7× | 42d/gap=10 |
| s580 | ALT-GAP | 1.031 | -14.7% | 1.2× | 42d/gap=5 |
| s577 | ALT-MOM | 0.963 | -16.4% | 1.2× | 189d |
| s574 | ALT-MOM | 0.944 | -15.2% | 1.2× | 84d |
| s572 | ALT-MOM | 0.994 | -13.9% | 1.6× | 42d |

**Universe**: BAM, KKR, APO, BX, ARES, CG, TPG — 7 US-listed alternative asset managers.

**Why it works**: These firms earn both management fees on AUM (which grows mechanically with asset appreciation) and performance fees on gains. In up-trending markets, AUM growth + performance fees create a self-reinforcing earnings compound. The deal-cycle inertia (3-7 year hold periods) produces multi-year earnings persistence. All 14 tested parameter configurations scored above SR 0.80 — the most robust strategy family tested.

**Mechanics**: Buy all tickers with positive lookback return, equal-weight, long-only. Weekly rebalance. No shorts — short side has no edge here.

### 3. Post-Earnings Announcement Drift (SR 0.988)

| ID | Variant | SR | DD | TO | Description |
|----|---------|------|-----|-----|-------------|
| **s546** | **EARNPEAD** | **0.988** | -8.5% | 12.4× | Top5/bottom5 by surprise%, 21d hold |
| s546 | EARNPEAD | 0.880 | -9.0% | 13.3× | Top10/bottom10 by surprise%, 21d hold |
| s546 | EARNPEAD | 0.449 | -9.3% | 14.7× | Top10/bottom10 by surprise%, 10d hold |

Cross-sectional PEAD (Bernard & Thomas 1989). On each earnings date, rank S&P 100 reporters by percentage earnings surprise. Long top 5, short bottom 5, hold 21 trading days. The edge persists because investors underreact to earnings information and transaction costs limit arbitrage.

### 4. Regime Detection (SR 0.32–0.96)

| ID | Theme | SCORE | SR | Gross SR | DD | Trades | Universe |
|----|-------|-------|----|----------|----|--------|----------|
| **s532** | **Risk Appetite** | **0.961** | 0.961 | 1.097 | -3.6% | 166 | SPY+TLT |
| **s534** | **Macro Quadrant** | **0.891** | 0.891 | 0.996 | -5.1% | 153 | SPY+TLT+GLD |
| s541 | Nasdaq Regime | 0.876 | 0.876 | 1.021 | -4.7% | 202 | QQQ+TLT |
| s524 | MRDv2 | 0.873 | 0.873 | 1.012 | -2.9% | 192 | SPY+TLT |
| s528 | Sector Rotation | 0.862 | 0.862 | — | -5.3% | 183 | Sectors |
| s543 | Tech Vol Stress | 0.817 | 0.817 | 1.035 | -5.5% | 323 | QQQ+TLT |
| s525 | MRDv3 Continuous | 0.743 | 0.743 | — | -4.6% | — | SPY+TLT |
| s538 | Unified Ensemble | 0.723 | 0.723 | 0.881 | -5.9% | 239 | SPY+TLT+GLD |
| s539 | Tail Risk | 0.704 | 0.704 | 0.900 | -4.0% | 187 | SPY+TLT+GLD |
| s535 | Dollar/Global Macro | 0.697 | 0.697 | 0.824 | -8.7% | 250 | SPY+TLT+GLD+EEM |
| s540 | Factor Rotation | 0.684 | 0.684 | 0.839 | -7.5% | 102 | MTUM/QUAL/USMV/VLUE |
| s533 | Yield Curve | 0.627 | 0.627 | 0.855 | -3.1% | 276 | SPY+TLT |
| s537 | Vol Ensemble | 0.444 | 0.444 | 0.568 | -5.8% | 162 | SPY+TLT |
| s531 | Inflation | 0.450 | 0.450 | 0.609 | -4.5% | 225 | SPY+TLT |
| s536 | Correlation PCA | 0.321 | 0.321 | 0.692 | -3.8% | 399 | SPY+TLT+GLD |

These strategies classify markets into regimes and allocate between assets accordingly. The **s532 Risk Appetite** champion uses 4 signals — credit spreads (HYG/LQD MA crossover), VIX vs 63d median, SPY/TLT correlation, and gold — to map Risk-On / Neutral / Risk-Off states for SPY and TLT.

### 5. Holding-Company TS Momentum (SR 0.91)

| ID | Variant | SR | DD | TO | Description |
|----|---------|-----|-----|-----|-------------|
| **s562** | **HC-WEIGHT** | **0.915** | -17.5% | 3.8× | LB=42, momentum-weighted, 22 hold cos |
| **s545** | **HCTREND** | **0.909** | -19.3% | 4.2× | LB=42, equal-weight, 22 hold cos. First discovery. |
| s566 | HC-SUB-AM | 0.949 | -14.5% | 2.7× | LB=42, 12 asset mgrs (alt+trad). Best sub-universe. |

Universe: diversified holding companies (BRK, MKL, FFH, BN, L, etc.) plus alt asset managers. The all-asset-manager sub-universe (12 tickers including traditional managers like BLK, IVZ, BEN) performs better than the pure hold-co universe but slightly less concentrated than the 7 alt-asset pure play.

### 6. Mean Reversion (S&P 100, SR 0.35–0.86)

| ID | Name | Lookback | Positions | Weighting |
|----|------|----------|-----------|-----------|
| s015 | Concentrated Reversal | 5d | top5/bottom5 | magnitude-weighted |
| s013 | Short-term Reversal | 5d | 10L/10S | equal-weight |
| s016 | Magnitude-Weighted | 5d | 10L/10S | magnitude-weighted |
| s017 | Filtered Reversal | 5d | 10L/10S | min_move=1% |

These are the only stock-level strategy family that consistently passes all gates. They exploit short-term reversal: stocks that went up most in the last 5 days tend to go down next week, and vice versa. Weekly rebalance is critical — daily kills returns through costs.

### 7. Multi-Asset Trend Following (SR 0.14–0.41)

| ID | Strategy | SR | DD | Description |
|----|----------|-----|-----|-------------|
| s010 | 50/200 MA Crossover | 0.410 | -17.3% | 12-ETF universe, vol-scaled |
| s008 | VIX-Filtered Trend | 0.359 | -15.9% | Flat when VIX>30 |
| s006 | Enhanced Trend | 0.317 | -16.3% | 252d lookback |

---

## Top 20 Full Leaderboard

| Rank | ID | Strategy | SCORE | SR | Gross | Max DD | Trades | TO |
|------|----|----------|-------|----|-------|--------|--------|----|
| 1 | **s542** | QQQ/SPY Dispersion | **1.182** | 1.182 | 1.328 | -4.4% | 163 | 1.5× |
| 2 | **s575** | Alt-Asset Trend (lb=126) | **1.065** | 1.065 | 1.124 | -14.0% | 187 | 1.2× |
| 3 | **s578** | Alt-MOM (lb=252) | **1.057** | 1.057 | 1.109 | -13.5% | 189 | 1.0× |
| 4 | **s581** | Alt-GAP (gap=7) | **1.034** | 1.034 | 1.073 | -14.7% | 177 | 0.7× |
| 5 | **s582** | Alt-GAP (gap=10) | **1.034** | 1.034 | 1.073 | -14.7% | 177 | 0.7× |
| 6 | **s580** | Alt-GAP (gap=5) | **1.031** | 1.031 | 1.071 | -14.7% | 188 | 1.2× |
| 7 | **s577** | Alt-MOM (lb=189) | 0.963 | 0.963 | 1.019 | -16.4% | 189 | 1.2× |
| 8 | **s532** | Risk Appetite Regime | **0.961** | 0.961 | 1.097 | -3.6% | 166 | 1.4× |
| 9 | **s566** | All Asset-Mgr Trend | 0.949 | 0.949 | 1.003 | -14.5% | 482 | 2.7× |
| 10 | **s574** | Alt-MOM (lb=84) | 0.944 | 0.944 | 0.989 | -15.2% | 230 | 1.2× |
| 11 | **s562** | HC-WEIGHT | 0.915 | 0.915 | 0.969 | -17.5% | 531 | 3.8× |
| 12 | **s545** | HCTREND | 0.909 | 0.909 | 0.967 | -19.3% | 905 | 4.2× |
| 13 | **s534** | Macro Quadrant | 0.891 | 0.891 | 0.996 | -5.1% | 153 | 1.6× |
| 14 | **s546** | EARNPEAD (5/5, 21d) | **0.988** | 0.988 | 1.131 | -8.5% | 340 | 12.4× |
| 15 | **s541** | Nasdaq Regime | 0.876 | 0.876 | 1.021 | -4.7% | 202 | 1.9× |
| 16 | **s524** | MRDv2 | 0.873 | 0.873 | 1.012 | -2.9% | 192 | 1.7× |
| 17 | **s528** | Sector Rotation | 0.862 | 0.862 | — | -5.3% | 183 | — |
| 18 | **s543** | Tech Vol Stress | 0.817 | 0.817 | 1.035 | -5.5% | 323 | 3.3× |
| 19 | **s525** | MRDv3 Continuous | 0.743 | 0.743 | — | -4.6% | — | — |
| 20 | **s538** | Unified Ensemble | 0.723 | 0.723 | 0.881 | -5.9% | 239 | 2.1× |

---

## Repo Structure

```
Quantloopp Top stratagies/
├── README.md
├── harness.py                 # Frozen evaluation harness (DO NOT MODIFY)
├── champions.md               # Full champion leaderboard
├── ledger.tsv                 # Complete experiment log (all 550+ runs)
├── program.md                 # Research protocol + evolving heuristics
├── alt-asset-mom-findings.md  # Deep dive on alt-asset manager TS mom
├── overnight_verdict.md       # Overnight return anomaly research
└── champions/
    ├── s542/        # QQQ/SPY Dispersion (SR 1.182 — #1 CHAMPION)
    ├── s575/        # Alt-Asset Trend — batch results (SR 1.065)
    ├── s541/        # Nasdaq Regime (QQQ+TLT)
    ├── s546/        # EARNPEAD — PEAD on S&P 100 (SR 0.988)
    ├── s543/        # Tech Vol Stress — VXN/VIX divergence
    ├── s547/        # NEXTWAVE — thematic momentum (SR 0.217)
    ├── s532/        # Risk Appetite Regime (SR 0.961)
    ├── s534/        # Macro Quadrant
    ├── s524/        # MRDv2 Regime Detection
    ├── s528/        # Regime Sector Rotation
    ├── s015/        # Concentrated Mean Reversion
    ├── ... (56+ strategy directories across all families)
    ├── batch_alt_mom.py     # Alt-asset manager batch runner
    ├── batch_hc_mom.py      # Holding-company batch runner
    ├── batch_hc_wave2.py    # Holding-company wave 2 batch
    └── batch_alt_mom.log    # Alt-asset batch output log
```

## How to Run

```bash
pip install numpy pandas yfinance scipy

# Run the #1 champion:
cd champions/s542
python strategy.py

# Run any champion:
cd champions/s532
python strategy.py
```

Each strategy downloads its own data (yfinance, cached) and prints results to stdout.

---

## Key Findings

### What Works
1. **QQQ/SPY Dispersion (SR 1.182)** — Pure stat-arb on a cointegrated ETF pair. Highest Sharpe of any strategy tested.
2. **Alt-Asset Manager TS Momentum (SR 1.02–1.06)** — Robust across all 14 lookback/gap variants. The 7 alt managers (BAM/KKR/APO/BX/ARES/CG/TPG) are uniquely suited for trend following due to AUM persistence and fee leverage.
3. **Post-Earnings Drift (SR 0.988)** — Cross-sectional PEAD is the third-best class. Top5/bottom5 by earnings surprise with 21-day hold outperforms more diversified variants.
4. **Risk Appetite is the strongest regime dimension** — 4-signal risk gauge achieves 0.961. Credit spreads (HYG/LQD) are the key signal.
5. **Volume-confirmed 52-week high (SR 0.994)** — The simplest cross-sectional equity anomaly, dramatically improved by a volume proxy filter.

### What Doesn't
- **Z-score combinations** of multiple signals consistently underperform pure signals
- **All pre-bugfix (pre-s101) daily reversal results are invalid** — a pandas alignment bug inflated them
- **Daily rebalancing** kills all edge through turnover costs
- **Continuous allocation on 2-asset portfolios** fails the trades gate
- **Thematic momentum on S&P 100** (s547, SR 0.217) only adds ~33% to pure momentum

## Disclaimer

For research and education only. Nothing here is financial advice. Backtests overstate live performance — expect degradation from regime shifts, capacity constraints, and implementation shortfall.
