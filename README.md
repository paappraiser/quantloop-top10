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
| 10 | s530 | Stress Score Persistence Sweep | Regime-Based | **0.686** | 0.69 | -4.5% | — |
| 11 | s526 | MRDv4 Trend Filtered | Regime-Based | **0.678** | 0.68 | -3.9% | — |
| 12 | s529 | MRD-V2 Stress Score | Regime-Based | **0.670** | 0.67 | -4.7% | — |
| 13 | s533 | Yield Curve Regime | Regime-Based | **0.627** | 0.63 | -3.1% | 276 |
| 14 | s019 | Combined Reversal + Momentum | Multi-Factor | **0.623** | 0.62 | -13.9% | — |
| 15 | s531 | Inflation Regime | Regime-Based | **0.450** | 0.45 | -4.5% | 225 |
| 16 | s018 | Short-term Reversal (200 stocks) | Mean Reversion | **0.439** | 0.44 | -12.5% | — |
| 17 | s010 | 50/200 MA Crossover | Trend Following | **0.410** | 0.41 | -17.3% | — |
| 18 | s008 | VIX-Filtered Trend | Trend Following | **0.359** | 0.36 | -15.9% | — |
| 19 | s101 | Weekly Reversal S&P 100 | Mean Reversion | **0.353** | 0.35 | -19.2% | — |
| 20 | s006 | Enhanced Trend (12-ETF) | Trend Following | **0.317** | 0.32 | -16.3% | — |

## Strategy Families

### Regime Detection (SPY + TLT + GLD)
These strategies classify the market into regimes and allocate between SPY (equities) and TLT (bonds), with s534 adding GLD (gold).

| ID | Theme | Key Signals | Universe |
|----|-------|-------------|----------|
| s532 | Risk Appetite | Credit spreads, VIX level, SPY/TLT corr, gold risk | SPY+TLT |
| s534 | Macro Quadrant | 2×2 Growth×Inflation → 4 quadrants | SPY+TLT+GLD |
| s524 | Classic Vol Technicals | VIX TS, RV trend, corr, credit spread, SKEW | SPY+TLT |
| s528 | Sector Rotation | Same regime signals → sector ETF allocation | SPY+TLT+Sectors |
| s525 | Continuous Sizing | Same regime signals → continuous SPY weight | SPY+TLT |
| s533 | Yield Curve | TLT/SHY slope + short rate momentum | SPY+TLT |

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
    ├── s530/               # Stress Score Persistence Sweep
    ├── s526/               # MRDv4 Trend Filtered
    ├── s529/               # MRD-V2 Stress Score
    ├── s533/               # Yield Curve Regime
    ├── s019/               # Combined Reversal + Momentum
    ├── s531/               # Inflation Regime
    ├── s018/               # Short-term Reversal (200 stocks)
    ├── s010/               # 50/200 MA Crossover
    ├── s008/               # VIX-Filtered Trend
    ├── s101/               # Weekly Reversal S&P 100
    └── s006/               # Enhanced Trend (12-ETF)
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

- **Regime detection dominates**: 6 of top 10 are regime-classification strategies
- **Risk appetite is the strongest single dimension**: Multi-dimensional risk gauge (credit + vol + correlation + safe-haven) beats pure vol technicals by 10%
- **Discrete allocation is critical**: The harness per-position cap (10%) kills continuous allocation on 2-asset portfolios — only extreme discrete weights (0/100, 100/0) create detectable turnover
- **Mean reversion on S&P 100 is the only stock-level strategy family that works**: All 4 mean-reversion champions exploit 5-day reversal patterns

## Disclaimer

For research and education only. Nothing here is financial advice. Backtests overstate live performance — expect degradation from regime shifts, capacity constraints, and implementation shortfall.
