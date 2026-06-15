# s529 — Market Regime V2: HMM + Stress Score

## 1. Strategy Name
Market Regime Detection V2 — Dual Architecture (MRD-HMM / MRD-SS)

## 2. Strategy Type
ML-based Regime Detection / Market Timing

## 3. Asset Universe
SPY (S&P 500) and TLT (20yr Treasury), with auxiliary ETFs for signal construction: GLD, HYG, LQD, VIX, VIX3M, SKEW

## 4. Timeframe
Daily data 2005-today. Walk-forward evaluation 2010-2026. Retrain every 252 days with 21-day embargo.

## 5. Core Idea / Edge
Replace the V1 vote-counting composite (s524) with two complementary architectures:
- **Architecture A (HMM)**: A 3-state Gaussian Hidden Markov Model learns regime states directly from market features (vol, skew, kurtosis, cross-asset relationships). The HMM captures the joint distribution of market features without arbitrary thresholds.
- **Architecture B (Stress Score)**: A rolling z-score composite of the same features, mapped to SPY allocation via sigmoid function. Parameter-free and more transparent.

Both architectures add a **5-day persistence filter** to prevent whipsawing — the #1 problem identified in V1. The filter requires 5 consecutive days of the same regime signal before acting on it.

## 6. Data Requirements
- SPY OHLCV (for features and trading)
- TLT, GLD, HYG, LQD (daily close)
- VIX (^VIX), VIX3M (^VIX3M), SKEW (^SKEW) — daily close
- All from yfinance, cached
- Minimum 20 years (2005-today) for feature computation

## 7. Signal Generation

### Features (computed on SPY daily log returns)
- ret_5, ret_21: 5d/21d rolling mean return (annualized ×252)
- rv5, rv21, rv63: 5d/21d/63d realized vol (annualized ×√252)
- rv_ratio: rv5 / rv21 (vol trend)
- skew_21: 21d rolling skewness
- kurt_21: 21d rolling excess kurtosis
- vts: VIX / VIX3M ratio
- credit_ratio: HYG/LQD price ratio, 10d change
- spy_tlt_corr: 20d rolling correlation

### Architecture A — HMM (3-state GaussianHMM)
- Input features: [rv21, rv_ratio, skew_21, kurt_21, vts, spy_tlt_corr]
- Expanding window training from 504d minimum, retrain every fold (252d)
- States labeled by mean rv21: low=Benign, mid=Neutral, high=Stressed
- 5-day persistence filter: confirm state before acting

### Architecture B — Stress Score
- Rolling 252d z-score for each feature
- Stress = mean([rv21_z, rv_ratio_z, -skew_21_z, kurt_21_z, vts_z, spy_tlt_corr_z])
- Sigmoid mapping: spy_w = 1 - expit(stress × 1.5)
- 5-day rolling median smoothing

### Shared post-processing
-- 200d MA trend filter modulates exposure
-- Volatility targeting (10% ann.) via harness
-- Cost model at 10 bps per side

## 8. Entry & Exit Rules
- Signals computed daily using data available at T-1
- Trade at next available close (harness handles shift)
- Persistence filter: new regime must hold 5 consecutive days before action
- Trend filter: if SPY < 200d MA, halve/quarter exposure based on regime conviction

## 9. Position Sizing & Risk Management
- Volatility targeting to 10% annualized (harness handles this)
- Weights: SPY weight = f(regime) × vol_target_scale
- TLT weight = 1.0 - SPY weight
- Trend filter reduces SPY weight: Bull×0.5, Neutral×0.25, Bear→0 when SPY < 200d MA

## 10. Portfolio Construction
Single portfolio of SPY+TLT. Regime determines the allocation split. Vol targeting sets the overall risk level. Trend filter provides downside protection.

## 11. Expected Characteristics
- Target: Sharpe > 0.87 (beat V1 champion s524)
- Target: DD < -5% (lower than V1's -2.9% due to persistence filter lag)
- Turnover: 2-4× annually (persistence filter reduces trading)
- Trades: 100-200 over 11 years
- Beta: near zero to SPY
- Holding period: 2-10 days per regime

## 12. Implementation Notes
- hmmlearn.GaussianHMM with n_components=3, covariance_type="full"
- HMM can produce different state orderings each refit — re-sort by mean rv21 after each fit
- Use expanding window (all available history) for HMM training, not rolling
- First ~504 days have NaN features — exclude from training, use buy-and-hold
- All features must be point-in-time: rolling windows use only past data
- For Architecture B, apply rolling z-score normalization (252d window) for stationary inputs

## 13. Potential Risks & Mitigations
- **HMM instability**: GaussianHMM can converge to different local optima each run. Mitigation: fixed random state, re-label states by vol.
- **Persistence filter lag**: 5-day confirmation means missing first 5 days of a regime shift. Mitigation: test persistence 1-10 days in sensitivity analysis.
- **Feature lookahead**: All rolling windows must use expanding data only — no full-sample standardization.
- **Overfitting**: HMM has many parameters (transition matrix, emission means/covs). Mitigation: only 3 states, 6 features, expanding window training.

## 14. Backtesting & Validation Framework
- Walk-forward via harness: expanding window, 252d retrain, 21d embargo
- Both architectures tested on same folds for fair comparison
- Sensitivity analysis: persistence filter 1-10 days, vol target 5-20%
- Compare vs Buy & Hold SPY and 60/40 SPY/TLT benchmarks
- Report best architecture as s529 champion
