#!/usr/bin/env python3
"""s534 — Macro Quadrant Regime Classifier (MACRO4)

2×2 growth × inflation macro regime:
  - Growth: SPY 63d momentum + DBC 63d momentum
  - Inflation: TIP/SHY ratio 63d change + DBC 63d momentum

4 quadrants:
  - Goldilocks (G>0, I≤0) → 100% SPY
  - Overheat (G>0, I>0) → 50% SPY, 50% GLD
  - Recession (G≤0, I≤0) → 70% TLT, 30% SPY
  - Stagflation (G≤0, I>0) → 50% GLD, 30% TLT, 20% SPY

Uses 3-asset universe: SPY, TLT, GLD.
"""

import sys
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
from harness import download_data, run_evaluation

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

CACHE_DIR = HERE / "data"


def download_macro_data(start="2005-01-01"):
    """Download macro quadrant data. Cache as pickle."""
    cache_file = CACHE_DIR / "s534_macro_data.pkl"

    if cache_file.exists():
        print("[s534] Loading macro data from cache …", file=sys.stderr)
        return pd.read_pickle(cache_file)

    print("[s534] Downloading macro quadrant data …", file=sys.stderr)

    def _fetch(ticker):
        df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            try:
                close = df.xs(ticker, axis=1, level=1)["Close"]
            except (KeyError, ValueError):
                close = df.xs("Close", axis=1, level=0).iloc[:, 0]
        elif "Close" in df.columns:
            close = df["Close"]
        else:
            close = df.iloc[:, 0]
        close.index = pd.to_datetime(close.index)
        close.name = ticker
        return close

    spy = _fetch("SPY")
    tlt = _fetch("TLT")
    gld = _fetch("GLD")
    dbc = _fetch("DBC")
    tip = _fetch("TIP")
    shy = _fetch("SHY")

    result = {"spy": spy, "tlt": tlt, "gld": gld, "dbc": dbc, "tip": tip, "shy": shy}
    pd.to_pickle(result, cache_file)
    print(f"[s534] Cached to {cache_file}", file=sys.stderr)
    return result


def compute_signals(data):
    """Compute growth and inflation scores, then assign quadrant.

    Returns DataFrame with growth_score, infl_score, quadrant_label.
    """
    spy = data["spy"]
    dbc = data["dbc"]
    tip = data["tip"]
    shy = data["shy"]

    all_dates = spy.index.union(dbc.index).union(tip.index).union(shy.index).sort_values()
    df = pd.DataFrame(index=all_dates)

    spy_r = spy.reindex(df.index).ffill()
    dbc_r = dbc.reindex(df.index).ffill()
    tip_r = tip.reindex(df.index).ffill()
    shy_r = shy.reindex(df.index).ffill()

    # ── Growth Score ────────────────────────────────────────────────────
    # SPY 63d momentum
    spy_mom = spy_r.pct_change(63)
    df["growth_spy"] = spy_mom

    # DBC 63d momentum (industrial commodity demand)
    dbc_mom = dbc_r.pct_change(63)
    df["growth_dbc"] = dbc_mom

    # Combined growth score: z-score normalize and average
    spy_z = (spy_mom - spy_mom.rolling(252, min_periods=60).mean()) / \
            spy_mom.rolling(252, min_periods=60).std().clip(lower=1e-6)
    dbc_z = (dbc_mom - dbc_mom.rolling(252, min_periods=60).mean()) / \
            dbc_mom.rolling(252, min_periods=60).std().clip(lower=1e-6)

    df["growth_z_score"] = (spy_z.fillna(0) + dbc_z.fillna(0)) / 2

    # Binary growth regime
    df["growth_high"] = np.where(df["growth_z_score"] > 0, 1, 0)

    # ── Inflation Score ─────────────────────────────────────────────────
    # TIP/SHY ratio change (inflation expectations via short-dated real yields)
    tip_shy = tip_r / shy_r.clip(lower=1e-8)
    tip_shy_chg = tip_shy.pct_change(63)
    df["infl_tip_shy"] = tip_shy_chg

    # DBC also proxies inflation pressure
    # z-score combine
    tip_z = (tip_shy_chg - tip_shy_chg.rolling(252, min_periods=60).mean()) / \
            tip_shy_chg.rolling(252, min_periods=60).std().clip(lower=1e-6)

    df["infl_z_score"] = (tip_z.fillna(0) + dbc_z.fillna(0)) / 2

    # Binary inflation regime
    df["infl_rising"] = np.where(df["infl_z_score"] > 0, 1, 0)

    # ── Quadrant Assignment ─────────────────────────────────────────────
    # 0 = Goldilocks, 1 = Overheat, 2 = Recession, 3 = Stagflation
    df["quadrant"] = 0
    df.loc[(df["growth_high"] == 1) & (df["infl_rising"] == 0), "quadrant"] = 0  # Goldilocks
    df.loc[(df["growth_high"] == 1) & (df["infl_rising"] == 1), "quadrant"] = 1  # Overheat
    df.loc[(df["growth_high"] == 0) & (df["infl_rising"] == 0), "quadrant"] = 2  # Recession
    df.loc[(df["growth_high"] == 0) & (df["infl_rising"] == 1), "quadrant"] = 3  # Stagflation

    return df


def make_signal(regime_df):
    """Factory: signal_fn with 4-quadrant allocation (SPY, TLT, GLD)."""
    quad_alloc = {
        0: {"SPY": 1.0, "TLT": 0.0, "GLD": 0.0},    # Goldilocks → max equities
        1: {"SPY": 0.5, "TLT": 0.0, "GLD": 0.5},    # Overheat → equities + gold
        2: {"SPY": 0.3, "TLT": 0.7, "GLD": 0.0},    # Recession → bonds + defensive equity
        3: {"SPY": 0.2, "TLT": 0.3, "GLD": 0.5},    # Stagflation → gold + bonds + small equity
    }

    def macro_signal(train_px, test_px, **kw):
        tickers = list(test_px.columns)
        # Map available tickers to quadrant allocation
        weights_list = []
        prev_weights = None
        prev_quadrant = -1

        reg = regime_df.reindex(test_px.index).ffill()

        for i, date in enumerate(test_px.index):
            is_rebal = (i == 0) or (date - test_px.index[i - 1]).days >= 2
            if not is_rebal and prev_weights is not None:
                weights_list.append(prev_weights.copy())
                continue

            if i == 0:
                prior = reg.index[reg.index < date]
                if len(prior) > 0:
                    quadrant = int(reg.loc[prior[-1], "quadrant"])
                else:
                    quadrant = 2  # default to Recession on no data
            else:
                quadrant = int(reg.loc[test_px.index[i - 1], "quadrant"]) \
                    if test_px.index[i - 1] in reg.index else 2

            # Get target allocation for this quadrant
            target = quad_alloc.get(quadrant, quad_alloc[2])

            # Build weights for available tickers
            w = pd.Series(0.0, index=tickers)
            for t in tickers:
                if t in target:
                    w[t] = target[t]

            # If GLD not in tickers, redistribute to SPY/TLT
            if "GLD" not in tickers and quadrant in (1, 3):
                gld_w = target.get("GLD", 0)
                if gld_w > 0:
                    # Redistribute gold weight proportionally to SPY/TLT
                    spy_target = target.get("SPY", 0)
                    tlt_target = target.get("TLT", 0)
                    total_st = spy_target + tlt_target
                    if total_st > 0:
                        w["SPY"] = spy_target + gld_w * (spy_target / total_st)
                        if "TLT" in tickers:
                            w["TLT"] = tlt_target + gld_w * (tlt_target / total_st)
                    else:
                        w["SPY"] = 0.5
                        if "TLT" in tickers:
                            w["TLT"] = 0.5

            prev_weights = w
            prev_quadrant = quadrant
            weights_list.append(w)

        return pd.DataFrame(weights_list, index=test_px.index)
    return macro_signal


def main():
    print("=" * 60, file=sys.stderr)
    print("s534 — Macro Quadrant Regime (MACRO4)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    data = download_macro_data()
    regime_df = compute_signals(data)

    print(f"[s534] Quadrant distribution:", file=sys.stderr)
    for q, name in [(0, "Goldilocks"), (1, "Overheat"), (2, "Recession"), (3, "Stagflation")]:
        pct = (regime_df["quadrant"] == q).mean() * 100
        print(f"       {name}: {pct:.1f}%", file=sys.stderr)

    # Primary universe: SPY + TLT + GLD (3-asset)
    prices = download_data(["SPY", "TLT", "GLD"], start="2010-01-01", asset_class="etf")
    print(f"[s534] Prices: {len(prices)} days, tickers: {list(prices.columns)}", file=sys.stderr)

    signal_fn = make_signal(regime_df)

    metrics = run_evaluation(
        prices=prices, signal_fn=signal_fn,
        cost_bps=10, asset_class="etf",
        n_trials=1, beta_ticker="SPY",
    )

    score = metrics.get("SCORE", 0)
    status = "keep" if score > 0 else "discard"

    print(f"\n{'='*60}", file=sys.stderr)
    print("s534 — Macro Quadrant Regime Classifier", file=sys.stderr)
    print("2×2 (Growth×Inflation) → Goldilocks/Overheat/Recession/Stagflation", file=sys.stderr)
    print("3-asset: SPY + TLT + GLD", file=sys.stderr)
    print('='*60, file=sys.stderr)
    for k in ["SCORE", "sharpe_net", "sharpe_gross", "deflated_sharpe", "sortino",
              "max_dd_pct", "ann_turnover", "n_trades", "win_rate", "beta_spy", "oos_years"]:
        print(f"{k:20s} {metrics.get(k, 'N/A')}", file=sys.stderr)

    print(f"\nLEDGER_ROW\ts534\tmacro-quadrant-regime\tspy-tlt-gld\t"
          f"{metrics.get('SCORE',0)}\t{metrics.get('sharpe_net',0)}\t"
          f"{metrics.get('max_dd_pct',0)}\t{metrics.get('ann_turnover',0)}\t"
          f"0\t{status}\t"
          f"MACRO4: 2×2 growth×inflation quadrant classifier, SPY+TLT+GLD, gap=2d")


if __name__ == "__main__":
    main()
