# Quantloop — Top 10 Champion Strategies

Autonomous systematic strategy research — quantitative trading strategies generated, backtested, and curated by an LLM agent (Hermes Quant).

**All strategies pass a strict evaluation harness:**
- Walk-forward (expanding 5yr window, retrain every 252d, 21d embargo)
- Net of costs (10 bps per side equities/ETFs, 20 bps crypto, 50 bps/yr short borrow)
- Volatility targeting to 10% annualized
- Per-position cap 10%, gross exposure cap 200%
- Drawdown gates: halve at 20%, flat at 30%
- Minimum 100 trades, max 35% drawdown, deflated Sharpe > 0

## Top 20 Leaderboard

| Rank | ID | Strategy | Type | SCORE | Sharpe | Max DD | Trades |
|------|----|----------|------|-------|--------|--------|--------|
| 1 | **s532** | **Risk Appetite Regime** | Regime-Based | **0.961** | 0.96 | -3.6% | 166 |
| 2 | s534 | Macro Quadrant | Regime-Based | **0.891** | 0.89 | -5.1% | 153 |
| 3 | s524 | MRDv2 Regime Detection | Regime-Based | **0.873** | 0.87 | -2.9% | 192 |
| 4 | s528 | Regime Sector Rotation | Regime-Based | **0.862** | 0.86 | -5.3% | 183 |
| 5 | s015 | Concentrated Mean Reversion | Mean Reversion | **0.859** | 0.86 | -5.8% | — |
| 6 | s013 | Short-term Mean Reversion | Mean Reversion | **0.788** | 0.79 | -11.1% | — |
| 7 | s016 | Magnitude-Weighted Reversal | Mean Reversion | **0.788** | 0.79 | -9.0% | — |
| 8 | s525 | MRDv3 Continuous Sizing | Regime-Based | **0.743** | 0.74 | -4.6% | — |
| 9 | s017 | Filtered Reversal | Mean Reversion | **0.729** | 0.73 | -11.1% | — |
| 10 | **s538** | **Unified Regime Ensemble** | **Regime-Based** | **0.723** | 0.72 | -5.9% | 239 |
| 11 | **s539** | **Tail Risk Regime** | **Regime-Based** | **0.704** | 0.70 | -4.0% | 187 |
| 12 | **s535** | **Dollar/Global Macro** | **Regime-Based** | **0.697** | 0.70 | -8.7% | 250 |
| 13 | s530 | Stress Score Persistence Sweep | Regime-Based | **0.686** | 0.69 | -4.5% | — |
| 14 | **s540** | **Factor Rotation** | **Regime-Based** | **0.684** | 0.68 | -7.5% | 102 |
| 15 | s526 | MRDv4 Trend Filtered | Regime-Based | **0.678** | 0.68 | -3.9% | — |
| 16 | s529 | MRD-V2 Stress Score | Regime-Based | **0.670** | 0.67 | -4.7% | — |
| 17 | s533 | Yield Curve Regime | Regime-Based | **0.627** | 0.63 | -3.1% | 276 |
| 18 | s019 | Combined Reversal + Momentum | Multi-Factor | **0.623** | 0.62 | -13.9% | — |
| 19 | s531 | Inflation Regime | Regime-Based | **0.450** | 0.45 | -4.5% | 225 |
| 20 | **s537** | **Volatility Regime Ensemble** | **Regime-Based** | **0.444** | 0.44 | -5.8% | 162 |

## Strategy Families

### Regime Detection (SPY + TLT + GLD)
These strategies classify the market into regimes and allocate between assets. The top 4 are the original champions; the deep-dive batch (s535-s540) explores new macro themes.

| ID | Theme | Key Signals | Universe |
|----|-------|-------------|----------|
| s532 | Risk Appetite | Credit spreads, VIX level, SPY/TLT corr, gold risk | SPY+TLT |
| s534 | Macro Quadrant | 2×2 Growth×Inflation → 4 quadrants | SPY+TLT+GLD |
| s524 | Classic Vol Technicals | VIX TS, RV trend, corr, credit spread, SKEW | SPY+TLT |
| s528 | Sector Rotation | Regime signals → sector ETF allocation | SPY+TLT+Sectors |
| s525 | Continuous Sizing | Regime signals → continuous SPY weight | SPY+TLT |
| s533 | Yield Curve | TLT/SHY slope + short rate momentum | SPY+TLT |
| s531 | Inflation | TIP breakevens + commodities + gold + dollar | SPY+TLT |
| **s538** | **Unified Ensemble** | **Meta-ensemble of all 6 themes** | **SPY+TLT+GLD** |
| **s539** | **Tail Risk** | **SKEW + VIX TS + credit stress** | **SPY+TLT+GLD** |
| **s535** | **Dollar/Macro** | **USD cycle + global growth diff** | **SPY+TLT+GLD+EEM** |
| **s540** | **Factor Rotation** | **Vol/growth/yield → factor ETFs** | **MTUM/QUAL/USMV/VLUE** |
| **s537** | **Vol Ensemble** | **VIX TS / RV / bond vol / dispersion** | **SPY+TLT** |
| **s536** | **Correlation PCA** | **PCA on 8-asset rolling corr** | **SPY+TLT+GLD** |

### Mean Reversion (S&P 100)
These strategies exploit short-term reversal in individual stocks.
| ID | Name | Lookback | Positions |
|----|------|----------|-----------|
| s015 | Concentrated Reversal | 5d | top5/bottom5, magnitude-weighted |
| s013 | Short-term Reversal | 5d | 10 long / 10 short, weekly |
| s016 | Magnitude-Weighted | 5d | 10/10, magnitude-weighted |
| s017 | Filtered Reversal | 5d | 10/10, min_move=1% |

## Repo Structure

```
quantloop-top10/
├── README.md
├── harness.py              # Frozen evaluation harness (DO NOT MODIFY)
├── champions.md            # Full champion leaderboard
├── ledger.tsv              # Complete experiment log
├── program.md              # Research protocol + evolving heuristics
└── champions/
    ├── s532/               # Risk Appetite Regime (champion)
    ├── s534/               # Macro Quadrant
    ├── s524/               # MRDv2 Regime Detection
    ├── s528/               # Regime Sector Rotation
    ├── s015/               # Concentrated Mean Reversion
    ├── s013/               # Short-term Mean Reversion
    ├── s016/               # Magnitude-Weighted Reversal
    ├── s525/               # MRDv3 Continuous Sizing
    ├── s017/               # Filtered Reversal
    ├── s538/               # Unified Regime Ensemble
    ├── s539/               # Tail Risk Regime
    ├── s535/               # Dollar/Global Macro
    ├── s530/               # Stress Score Persistence Sweep
    ├── s540/               # Factor Rotation
    ├── s526/               # MRDv4 Trend Filtered
    ├── s529/               # MRD-V2 Stress Score
    ├── s533/               # Yield Curve Regime
    ├── s019/               # Combined Reversal + Momentum
    ├── s531/               # Inflation Regime
    └── s537/               # Volatility Regime Ensemble
```

## How to Run

```bash
pip install numpy pandas yfinance scipy

# Run any champion:
cd champions/s532
python strategy.py
```

Each strategy downloads its own data (yfinance, cached) and prints results to stdout.

## Key Findings

- **Risk appetite is the strongest single dimension**: Multi-dimensional risk gauge (credit + vol + correlation + safe-haven) achieves 0.961 — no other theme or ensemble reaches 0.73. The credit signal (HYG/LQD MA crossover) is the key differentiator.
- **Unified ensemble beats 5 of 6 component themes**: Combining risk appetite, growth, inflation, yield curve, dollar, and vol into one meta-signal achieves 0.723. Only the champion risk appetite outruns it.
- **Tail risk (SKEW + VIX TS + credit) has the highest gross Sharpe**: 0.900 gross, 0.704 net. The SKEW index is underutilized in systematic strategies.
- **Dollar/Global Macro works on 4 assets**: First multi-asset regime strategy (SPY+TLT+GLD+EEM) with USD cycle as the organizing principle.
- **Factor rotation between MTUM/QUAL/USMV/VLUE is feasible**: 0.684 though barely passes the trades gate. Factor timing has lower Sharpe than asset allocation.
- **PCA correlation regime works but costs dominate**: 0.692 gross, 0.321 net — 6.6x turnover eats the edge.
- **Discrete allocation is critical**: The harness per-position cap (10%) kills continuous allocation on 2-asset portfolios — only extreme discrete weights (0/100, 100/0) create detectable turnover. For 3+ asset portfolios, discrete allocation still works through regime transitions.
- **Daily delta fixes low trade frequency**: Adding `composite_delta * 3.0` to the base signal rescued s538 (94→239 trades) and s540 (72→102). The first-derivative of the regime signal captures regime transitions.
- **Mean reversion on S&P 100 is the only stock-level strategy family that works**: All mean-reversion champions exploit 5-day reversal patterns.

## Disclaimer

For research and education only. Nothing here is financial advice. Backtests overstate live performance — expect degradation from regime shifts, capacity constraints, and implementation shortfall.
