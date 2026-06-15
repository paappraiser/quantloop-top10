# s528 — Regime-Based Sector Rotation

## 1. Strategy Name
Regime-Based Sector Rotation (SRR)

## 2. Strategy Type
Regime-Aware Cross-Sectional Momentum / Sector Rotation

## 3. Asset Universe
4 sector SPDR ETFs: XLK (Tech), XLF (Financials), XLE (Energy), XLU (Utilities)
XLE is included as a data ticker but excluded from all allocation rules (commodity-driven, uncorrelated to equity regime).
Regime signal data: SPY, TLT, HYG, LQD, VIX, VIX3M, SKEW.

## 4. Timeframe
Daily regime signals, weekly sector rotation (gap-based ≥4 days).
Backtest: 2010-01-01 to present.

## 5. Core Idea / Edge
Use the 5-signal regime composite (s524) to determine market regime, then allocate to sectors that lead in each regime.

**Benign (composite ≥ 2):** Cyclicals lead in expansion → 50% XLK + 50% XLF.
**Neutral (0 to 2):** Let momentum decide — top 2 of XLK/XLF/XLU by trailing 3-month return.
**Stressed (< 0):** Defensives hold up → 100% XLU.

XLE (Energy) is excluded from all regimes — commodity-driven returns are uncorrelated to the equity regime signal and add noise.

This combines regime timing (second derivative) with cross-sectional rotation (first derivative).

## 6. Data Requirements
- All regime data (SPY, TLT, HYG, LQD, VIX, VIX3M, SKEW) — same as s523
- Sector ETFs: XLK, XLF, XLE, XLU
- All from yfinance, cached

## 7. Signal Generation
Same 5-signal composite as s524:
- sig1: VIX/VIX3M < 1.0 → +1 (forward vol expectations normal)
- sig2: 5d/21d RV ratio SMA5 < 1.0 → +1 (short-term vol below medium-term)
- sig3: 20d SPY/TLT correlation < 0.1 → +1 (risk-on regime — stocks and bonds decoupled)
- sig4: HYG/LQD 10d MA > 30d MA → +1 (credit markets healthy)
- sig5: SKEW diff(20) < 5.0 → +1 (tail risk not spiking)
- composite = sum of 5 signals ∈ [-5, +5]

## 8. Entry & Exit Rules
- Weekly rebalance: (date - prev_date).days >= 4
- Yesterday's composite score determines today's allocation
- **Benign (≥2):** 50% XLK + 50% XLF
- **Neutral (0 to 2):** top 2 of XLK/XLF/XLU by 3-month momentum
- **Stressed (< 0):** 100% XLU
- XLE never allocated

## 9. Position Sizing & Risk Management
- Equal-weight within positions
- Gross exposure = 100% (long only)
- Harness handles vol-targeting and DD gates

## 10. Portfolio Construction
Single long-only portfolio of sector ETFs. Regime determines which sectors.

## 11. Expected Characteristics
- Target: Sharpe 0.40-0.50 net
- Max DD: -15 to -20%
- Turnover: 5-7× annually
- Trades: 100-200 over 11 years
- Beta to SPY: ~0.5-0.7 (long-only)
- XLE never used

## 12. Implementation Notes
- Regime composite from cached s523 data (pickle)
- Sector prices via harness download_data()
- 3-month momentum precomputed for Neutral regime ranking
- Neutral ranking pool: XLK, XLF, XLU only — XLE excluded
- In the edge case where all 3 neutral candidates have NaN momentum, equal-weight them

## 13. Potential Risks & Mitigations
- **Only 3 actively traded sectors** — limited diversification. Mitigation: each regime concentrates in 1-2 sectors by design.
- **Weekly rebalance** — 4-day gap may miss rapid regime changes. Mitigation: s524 uses gap=2d; if this were tightened the sector rotation would generate more trades.
- **Long-only** — no hedging during stressed periods. Mitigation: XLU does hold up better than equities (negative beta to SPY during downturns).
- **3-month momentum in Neutral** — mean-reversion risk. If all 3 sectors have negative momentum, you're buying the least-bad. Mitigation: could go to cash in that case, but this adds complexity.

## 14. Backtesting & Validation Framework
- Standard walk-forward via harness
- Single run with s524's regime thresholds (not re-optimized)
- Compare vs equal-weight sectors and buy-and-hold SPY
