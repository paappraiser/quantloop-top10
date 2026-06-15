#!/usr/bin/env python3
"""s529 — Market Regime V2: HMM + Stress Score (Dual Architecture)

Two architectures that both improve on the V1 vote-counting composite (s524):

Architecture A (HMM):
  3-state GaussianHMM trained on [rv21, rv_ratio, skew_21, kurt_21, vts, spy_tlt_corr].
  Expanding window, retrain per fold. States labelled by vol. 5-day persistence filter.

Architecture B (Stress Score):
  Rolling 252d z-score of same features → stress composite → sigmoid SPY weight.
  5-day median smoothing. Parameter-free.

Both get: 200d MA trend filter, vol targeting via harness.
"""
import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import yfinance as yf
from hmmlearn.hmm import GaussianHMM
from scipy.special import expit

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation, print_ledger_row

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

CACHE_DIR = HERE / "data"

# ── Constants ──────────────────────────────────────────────────────────────
ASSET_TICKERS = ["SPY", "TLT"]
INDEX_TICKERS = {"^VIX": "VIX", "^VIX3M": "VIX3M", "^SKEW": "SKEW"}
ETF_TICKERS = ["SPY", "TLT", "GLD", "HYG", "LQD"]

START_DATE = "2005-01-01"
TRADE_START = "2010-01-01"
MIN_TRAIN_DAYS = 504  # ~2 years for HMM warmup
PERSISTENCE_DAYS = 5  # must confirm regime for this many days
VOL_TARGET = 0.10


# ══════════════════════════════════════════════════════════════════════════
# Data & Feature Engineering
# ══════════════════════════════════════════════════════════════════════════


def download_all_data():
    """Download all required data, cache to pickle."""
    cache_file = CACHE_DIR / "s529_data.pkl"
    if cache_file.exists():
        print("[s529] Loading cached data …", file=sys.stderr)
        return pd.read_pickle(cache_file)

    print("[s529] Downloading all data …", file=sys.stderr)

    # SPY OHLCV for return/vol features
    spy = yf.download("SPY", start=START_DATE, auto_adjust=True, progress=False, group_by="ticker")
    if isinstance(spy.columns, pd.MultiIndex):
        spy = spy.xs("SPY", axis=1, level=0)
    spy.columns = [c.lower() for c in spy.columns]
    spy.index = pd.to_datetime(spy.index)
    spy_close = spy["close"]

    # Index data (VIX, VIX3M, SKEW)
    def _fetch(ticker):
        df = yf.download(ticker, start=START_DATE, auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            return df.xs(ticker, axis=1, level=1)["Close"]
        return df["Close"] if "Close" in df.columns else df.iloc[:, 0]

    vix = _fetch("^VIX")
    vix3m = _fetch("^VIX3M") if yf.download("^VIX3M", start=START_DATE, auto_adjust=False, progress=False).shape[0] > 0 else vix.copy()
    skew = _fetch("^SKEW")

    # ETF close prices (use group_by='ticker' for consistent MultiIndex: level 0=ticker, level 1=price)
    etf_raw = yf.download(ETF_TICKERS, start=START_DATE, auto_adjust=True, progress=False, group_by="ticker")
    if isinstance(etf_raw.columns, pd.MultiIndex):
        etf_close = etf_raw.xs("Close", axis=1, level=1)
    else:
        etf_close = etf_raw[ETF_TICKERS]
    etf_close.columns = [c.strip().upper() for c in etf_close.columns]

    result = {
        "spy_close": spy_close,
        "vix": vix, "vix3m": vix3m, "skew": skew,
        "tlt": etf_close["TLT"],
        "gld": etf_close["GLD"],
        "hyg": etf_close["HYG"],
        "lqd": etf_close["LQD"],
    }
    pd.to_pickle(result, cache_file)
    print(f"[s529] Cached to {cache_file}", file=sys.stderr)
    return result


def compute_features(data):
    """Compute all features on SPY log returns. Returns a DataFrame indexed by date."""
    spy_c = data["spy_close"]
    log_rets = np.log(spy_c / spy_c.shift(1))

    df = pd.DataFrame(index=spy_c.index)

    # ── Return features ──
    df["ret_5"] = log_rets.rolling(5).mean() * 252
    df["ret_21"] = log_rets.rolling(21).mean() * 252

    # ── Volatility features ──
    df["rv5"] = log_rets.rolling(5).std() * np.sqrt(252)
    df["rv21"] = log_rets.rolling(21).std() * np.sqrt(252)
    df["rv63"] = log_rets.rolling(63).std() * np.sqrt(252)
    df["rv_ratio"] = df["rv5"] / df["rv21"].clip(lower=1e-8)

    # ── Distribution shape ──
    df["skew_21"] = log_rets.rolling(21).skew()
    df["kurt_21"] = log_rets.rolling(21).kurt()

    # ── Cross-asset features ──
    vix = data["vix"].reindex(df.index).ffill()
    vix3m = data["vix3m"].reindex(df.index).ffill()
    df["vts"] = vix / vix3m.clip(lower=1e-6)  # VIX / VIX3M

    hyg = data["hyg"].reindex(df.index).ffill()
    lqd = data["lqd"].reindex(df.index).ffill()
    hy_lq = hyg / lqd.clip(lower=1e-8)
    df["credit_ratio"] = hy_lq.diff(10)

    tlt = data["tlt"].reindex(df.index).pct_change()
    df["spy_tlt_corr"] = log_rets.rolling(20, min_periods=10).corr(tlt)

    # ── Trend filter (200d MA) ──
    df["trend_filter"] = np.where(spy_c > spy_c.rolling(200).mean(), 1, 0)

    # ── HMM feature subset ──
    hmm_features = ["rv21", "rv_ratio", "skew_21", "kurt_21", "vts", "spy_tlt_corr"]
    return df, hmm_features


# ══════════════════════════════════════════════════════════════════════════
# Architecture A — HMM Signal
# ══════════════════════════════════════════════════════════════════════════


def make_hmm_signal(features_df, hmm_columns, persist_days=PERSISTENCE_DAYS, min_train=MIN_TRAIN_DAYS):
    """Factory: HMM-based regime signal.

    Inside each fold:
      1. Compute features point-in-time from precomputed feature DataFrame
      2. Fit 3-state GaussianHMM on train features
      3. Predict test states, label by vol (low=Benign, mid=Neutral, high=Stressed)
      4. Apply persistence filter
      5. Apply trend filter and return SPY weight
    """
    # Pre-normalize features to z-scores for HMM stability
    feat_z = features_df[hmm_columns].copy()
    feat_z = feat_z.rolling(252, min_periods=63).apply(
        lambda x: (x.iloc[-1] - x.mean()) / x.std() if x.std() > 1e-8 else 0.0,
        raw=False,
    )
    feat_z = feat_z.fillna(0.0)

    trend = features_df["trend_filter"]

    def hmm_regime_signal(train_px, test_px, **kw):
        tickers = list(test_px.columns)
        # Align features to fold dates
        train_feat = feat_z.loc[train_px.index].dropna()
        test_feat = feat_z.loc[test_px.index]
        train_trend = trend.reindex(train_px.index).ffill().fillna(1)
        test_trend = trend.reindex(test_px.index).ffill().fillna(1)

        # Need enough train data
        if len(train_feat) < min_train // 2:
            # Fallback: equal weight
            w = pd.Series(0.5, index=tickers)
            return pd.DataFrame([w] * len(test_px), index=test_px.index)

        # Fit HMM
        try:
            hmm = GaussianHMM(
                n_components=3, covariance_type="full",
                random_state=42, n_iter=200, tol=1e-4,
            )
            hmm.fit(train_feat.values)

            # Predict states
            train_states = hmm.predict(train_feat.values)
            test_states = hmm.predict(test_feat.fillna(0).values)
        except Exception as e:
            print(f"[s529.HMM] Fit failed: {e}", file=sys.stderr)
            w = pd.Series(0.5, index=tickers)
            return pd.DataFrame([w] * len(test_px), index=test_px.index)

        # Label states by mean rv21 during train period
        train_rv21 = features_df["rv21"].reindex(train_px.index)
        state_rv = pd.Series(train_states, index=train_feat.index).groupby(
            lambda x: x
        ).apply(lambda s: train_rv21.loc[s.index].mean())
        # state_rv is a Series where the index is state number (0,1,2)

        # Sort states by mean vol
        # Build a mapping from state number → label
        state_vols = {}
        for s in range(3):
            mask = train_states == s
            if mask.sum() > 0:
                state_vols[s] = train_rv21.loc[train_feat.index[mask]].mean()
            else:
                state_vols[s] = float("inf")

        sorted_states = sorted(state_vols.keys(), key=lambda s: state_vols[s])

        # Make arrays for persistence filter
        # 0=Benign (low vol), 1=Neutral, 2=Stressed (high vol)
        label_map = {sorted_states[i]: i for i in range(3)}
        test_labels = np.array([label_map.get(s, 1) for s in test_states])

        # ── Apply persistence filter ──
        confirmed = np.zeros_like(test_labels)
        current = test_labels[0]
        streak = 1
        confirmed[0] = current
        for i in range(1, len(test_labels)):
            if test_labels[i] == current:
                streak += 1
            else:
                streak = 1
                current = test_labels[i]
            if streak >= persist_days:
                confirmed[i] = current
            else:
                confirmed[i] = confirmed[i - 1]

        # ── Build weights ──
        weights_list = []
        for i in range(len(test_px)):
            regime = confirmed[i]
            tf = test_trend.iloc[i] if i < len(test_trend) else 1

            # Base SPY weight by regime
            if regime == 0:  # Benign
                base_w = 1.0
            elif regime == 2:  # Stressed
                base_w = 0.0
            else:  # Neutral
                base_w = 0.5

            # Trend filter modulation (DOCX Table)
            if regime == 0:  # Bull
                spy_w = base_w if tf == 1 else base_w * 0.5
            elif regime == 1:  # Neutral
                spy_w = base_w * 0.5 if tf == 1 else base_w * 0.25
            else:  # Bear
                spy_w = 0.0  # flat regardless

            w = pd.Series(0.0, index=tickers)
            w["SPY"] = spy_w
            if "TLT" in tickers:
                w["TLT"] = 1.0 - spy_w
            weights_list.append(w)

        return pd.DataFrame(weights_list, index=test_px.index)

    return hmm_regime_signal


# ══════════════════════════════════════════════════════════════════════════
# Architecture B — Stress Score Signal
# ══════════════════════════════════════════════════════════════════════════


def make_stress_signal(features_df, hmm_columns, smooth_days=5):
    """Factory: rolling stress score → sigmoid SPY weight.

    Stress = mean([rv21_z, rv_ratio_z, -skew_21_z, kurt_21_z, vts_z, corr_z])
    SPY weight = 1 - expit(stress × 1.5)
    Smoothed with rolling median.
    """
    # Rolling z-scores (fixed 252d window)
    feat_z = features_df[hmm_columns].copy()
    for col in hmm_columns:
        mean_ = feat_z[col].rolling(252, min_periods=63).mean()
        std_ = feat_z[col].rolling(252, min_periods=63).std().clip(lower=1e-8)
        feat_z[col] = (feat_z[col] - mean_) / std_

    # Stress composite (negate skew since positive skew is good)
    stress = (
        feat_z["rv21"]
        + feat_z["rv_ratio"]
        - feat_z["skew_21"]  # negated: positive skew = good = low stress
        + feat_z["kurt_21"]
        + feat_z["vts"]
        + feat_z["spy_tlt_corr"]
    ) / 6.0

    # Sigmoid SPY weight
    raw_spy_w = 1.0 - expit(stress * 1.5)

    # Smooth with rolling median
    smooth_w = raw_spy_w.rolling(smooth_days, min_periods=1, center=False).median()

    trend = features_df["trend_filter"]

    def stress_signal(train_px, test_px, **kw):
        tickers = list(test_px.columns)
        # Align to fold dates
        spy_w = smooth_w.reindex(test_px.index).ffill().fillna(0.5)
        tf = trend.reindex(test_px.index).ffill().fillna(1)

        weights_list = []
        for i, date in enumerate(test_px.index):
            base_w = float(spy_w.iloc[i])

            # Classify regime from stress score for trend filter logic
            # Using original (non-smoothed) stress for regime classification
            s = float(stress.reindex(test_px.index).ffill().fillna(0).iloc[i])
            if s < -0.5:
                regime = 0  # Benign
            elif s > 0.5:
                regime = 2  # Stressed
            else:
                regime = 1  # Neutral

            t = float(tf.iloc[i]) if i < len(tf) else 1

            # Trend filter modulation
            if regime == 0 and t == 1:
                spy_weight = base_w
            elif regime == 0 and t == 0:
                spy_weight = base_w * 0.5
            elif regime == 1 and t == 1:
                spy_weight = base_w * 0.5
            elif regime == 1 and t == 0:
                spy_weight = base_w * 0.25
            else:  # Bear
                spy_weight = 0.0

            w = pd.Series(0.0, index=tickers)
            w["SPY"] = spy_weight
            if "TLT" in tickers:
                w["TLT"] = 1.0 - spy_weight
            weights_list.append(w)

        return pd.DataFrame(weights_list, index=test_px.index)

    return stress_signal


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════


def main():
    print("=" * 60, file=sys.stderr)
    print("s529 — Market Regime V2 (HMM + Stress Score)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # 1. Data
    data = download_all_data()

    # 2. Features
    print("[s529] Computing features …", file=sys.stderr)
    features_df, hmm_cols = compute_features(data)
    print(f"[s529] Feature shape: {features_df.shape}, HMM features: {hmm_cols}", file=sys.stderr)

    # 3. Prices for trading
    prices = download_data(ASSET_TICKERS, start=TRADE_START, asset_class="etf")
    print(f"[s529] Prices: {prices.shape}, {list(prices.columns)}", file=sys.stderr)

    # 4. Architecture A — HMM
    print("\n" + "=" * 60, file=sys.stderr)
    print("Architecture A: HMM Regime Detection", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    hmm_signal = make_hmm_signal(features_df, hmm_cols)
    metrics_a = run_evaluation(
        prices=prices, signal_fn=hmm_signal,
        cost_bps=10, asset_class="etf",
        n_trials=1, beta_ticker="SPY",
    )

    print(f"\n{'='*60}", file=sys.stderr)
    print("Architecture A — HMM Results", file=sys.stderr)
    print('='*60, file=sys.stderr)
    for k in ["SCORE", "sharpe_net", "sharpe_gross", "deflated_sharpe", "sortino",
              "max_dd_pct", "ann_turnover", "n_trades", "win_rate", "beta_spy", "oos_years"]:
        print(f"{k:20s} {metrics_a.get(k, 'N/A')}")

    # 5. Architecture B — Stress Score
    print("\n" + "=" * 60, file=sys.stderr)
    print("Architecture B: Stress Score Regime Detection", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    stress_signal = make_stress_signal(features_df, hmm_cols)
    metrics_b = run_evaluation(
        prices=prices, signal_fn=stress_signal,
        cost_bps=10, asset_class="etf",
        n_trials=1, beta_ticker="SPY",
    )

    print(f"\n{'='*60}", file=sys.stderr)
    print("Architecture B — Stress Score Results", file=sys.stderr)
    print('='*60, file=sys.stderr)
    for k in ["SCORE", "sharpe_net", "sharpe_gross", "deflated_sharpe", "sortino",
              "max_dd_pct", "ann_turnover", "n_trades", "win_rate", "beta_spy", "oos_years"]:
        print(f"{k:20s} {metrics_b.get(k, 'N/A')}")

    # 6. Pick winner
    score_a = metrics_a.get("SCORE", 0)
    score_b = metrics_b.get("SCORE", 0)
    winner = "hmm" if score_a >= score_b else "stress"
    best = metrics_a if score_a >= score_b else metrics_b

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Winner: Architecture {winner.upper()} (SCORE={best.get('SCORE', 0):.4f})", file=sys.stderr)
    print('='*60, file=sys.stderr)

    # 7. LEDGER rows
    score = best.get("SCORE", 0)
    status = "keep" if score > 0 else "discard"
    print_ledger_row("s529", f"regime-detection-{winner}", "spy-tlt",
                     best, 3, status,
                     f"MRD-V2: {winner.upper()} architecture. Dual-arch comparison. "
                     f"A HMM={score_a:.4f}, B Stress={score_b:.4f}. "
                     f"Persistence={PERSISTENCE_DAYS}d, trend filter, vol targeting, {len(hmm_cols)} features")


if __name__ == "__main__":
    main()
