#!/usr/bin/env python3
"""s547 — NEXTWAVE: Thematic Institutional Rotation on S&P 100.

Captures the predicted institutional rotation from Q1 2026 13F analysis:
  Long:  AI infrastructure beneficiaries (power, memory, AI platforms, energy, defense)
  Short: AI-disrupted sectors (SaaS, legacy tech, consumer discretionary)

Combines medium-term momentum with thematic relevance scores.
"""
import sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))

from harness import download_data, run_evaluation, print_ledger_row

warnings.filterwarnings("ignore")

# ── S&P 100 Universe (from s546, cleaned) ────────────────────────────
SP100_TICKERS = [
    'AAPL','MSFT','AMZN','GOOGL','GOOG','META','BRK-B','JPM','V','PG',
    'XOM','UNH','MA','HD','CVX','LLY','MRK','ABBV','COST','PEP',
    'KO','ADBE','WMT','CRM','BAC','NFLX','DIS','CSCO','TMO','ACN',
    'ABT','AXP','AVGO','CMCSA','DHR','GE','INTC','INTU','MDT','NEE',
    'AMD','AMGN','BA','CAT','DE','ETN','GILD','GS','HON','IBM',
    'LOW','LMT','MCD','MDLZ','MMM','MO','MS','NKE','ORCL','PFE',
    'PM','QCOM','RTX','SBUX','SO','SPGI','SYK','T','TGT','TXN',
    'UBER','UNP','UPS','USB','VZ','WFC','CI','COP','DUK',
    'ELV','F','GD','GM','ISRG','PLD','PNC','SCHW','SLB',
    'SYY','TMUS','ZTS'
]

# ── Thematic Relevance Scores ────────────────────────────────────────
# Scale: -2 (high disruption risk) to +3 (strong AI infrastructure beneficiary)
# Based on Q1 2026 13F analysis of top hedge fund positioning
THEME_SCORES = {
    # AI Infrastructure / Power / Energy / Grid (+3)
    'AVGO': 3, 'AMD': 3, 'QCOM': 3, 'TXN': 3,          # semiconductors
    'MU': 3,                                               # memory bottleneck
    'ETN': 3, 'GE': 3,                                     # electrical/grid
    'MSFT': 3, 'AMZN': 3, 'META': 3,                       # AI platform beneficiaries
    'UBER': 3,                                              # platform/AI logistics
    'CVX': 3, 'XOM': 3, 'COP': 3,                          # energy
    'NEE': 3, 'SO': 3, 'DUK': 3,                           # utilities (AI power demand)
    'ISRG': 3,                                              # healthcare AI / robotics
    'SPGI': 3,                                              # data moat / ratings duopoly

    # Defensive AI / Healthcare / Defense (+2)
    'LMT': 2, 'RTX': 2, 'GD': 2, 'NOC': 2,                 # defense
    'LLY': 2, 'MRK': 2, 'ABBV': 2, 'UNH': 2,               # pharma
    'AMGN': 2, 'ABT': 2, 'MDT': 2, 'SYK': 2,               # healthcare
    'ELV': 2, 'CI': 2, 'ZTS': 2,                            # managed care/vet
    'CAT': 2, 'DE': 2, 'HON': 2, 'MMM': 2,                 # industrial
    'BA': 2,                                                 # aerospace

    # High Quality / Neutral (+1)
    'BRK-B': 1, 'JPM': 1, 'BAC': 1, 'WFC': 1, 'GS': 1, 'MS': 1,
    'V': 1, 'MA': 1, 'AXP': 1,
    'PG': 1, 'KO': 1, 'PEP': 1, 'COST': 1, 'WMT': 1,
    'HD': 1, 'LOW': 1,
    'UNP': 1, 'UPS': 1,
    'MSI': 1, 'BLK': 1,
    'TMO': 1, 'DHR': 1,
    'PM': 1, 'MO': 1,
    'TMUS': 1, 'VZ': 1, 'T': 1,

    # Mixed / No Clear Signal (0)
    'GILD': 0, 'MDLZ': 0, 'SYY': 0,
    'PNC': 0, 'SCHW': 0, 'USB': 0,
    'PLD': 0, 'SLB': 0,
    'ACN': 0, 'CMCSA': 0,
    'PFE': 0, 'TGT': 0, 'F': 0, 'GM': 0,

    # Moderate AI Disruption Risk (-1)
    'ORCL': -1, 'CSCO': -1, 'IBM': -1, 'INTC': -1,
    'NKE': -1, 'SBUX': -1, 'MCD': -1, 'DIS': -1,
    'NFLX': -1,
    'CMCSA': -1,
    'TGT': -1,

    # High AI Disruption Risk (-2)
    'CRM': -2,      # Salesforce - SaaS per-seat model threatened
    'ADBE': -2,     # Adobe - creative SaaS under AI pressure
    'INTU': -2,     # Intuit - tax/financial SaaS (Atreides exited entirely)
}

# Normalize to [-1, +1] range
MAX_THEME = 3.0
MIN_THEME = -2.0


def _theme_score_normalized(ticker: str) -> float:
    """Map theme score to [-1, +1] range."""
    raw = THEME_SCORES.get(ticker, 0.0)
    if raw >= 0:
        return raw / MAX_THEME
    return raw / abs(MIN_THEME)


# ── Signal Function ──────────────────────────────────────────────────
def make_signal(
    n_positions: int = 5,
    momentum_lookback: int = 252,
    theme_weight: float = 0.3,
    gap: int = 10,
):
    """Factory: returns a signal_fn for harness.run_evaluation.

    Parameters
    ----------
    n_positions : int
        Number of stocks to go long and short (5 or 8).
    momentum_lookback : int
        Trailing window for return calculation (126, 189, or 252).
    theme_weight : float
        How much to weight theme score vs momentum (0.0 = pure momentum).
    gap : int
        Minimum calendar days between rebalances.
    """
    def signal_fn(train_px: pd.DataFrame, test_px: pd.DataFrame, **kw) -> pd.DataFrame:
        """Generate position weights for test period.

        Uses train_px to compute momentum lookback (min periods),
        then applies to test_px for signal generation.
        """
        tickers = list(test_px.columns)
        all_px = pd.concat([train_px, test_px])
        all_rets = all_px.pct_change()

        # Pre-compute momentum: trailing N-day return for every date
        # Need at least momentum_lookback/2 periods to avoid cold-start NaNs
        # Use train period to compute lookback norms, then slide forward
        # For each test date, compute rank using rolling lookback

        def compute_weights(date_idx: pd.DatetimeIndex) -> pd.DataFrame:
            """Compute weights for each date in date_idx, one at a time."""
            w_rows = []
            prev_date = None

            for i, date in enumerate(date_idx):
                # Gap-based rebalance: skip if within gap days of last trade
                if prev_date is not None and (date - prev_date).days < gap:
                    if w_rows:
                        w_rows.append(w_rows[-1].copy())
                    else:
                        w_rows.append(pd.Series(0.0, index=tickers))
                    continue

                # Get price slice up to this date
                px_slice = all_px.loc[:date].iloc[-(momentum_lookback + 5):]
                if len(px_slice) < momentum_lookback // 2:
                    w_rows.append(pd.Series(0.0, index=tickers))
                    continue

                # Momentum: ratio of close at t vs close at t-lookback
                # Use the latest available close
                latest = px_slice.iloc[-1]
                past = px_slice.iloc[0]
                raw_mom = (latest / past - 1.0).replace([np.inf, -np.inf], np.nan)

                # Cross-sectional z-score
                mom_mean = raw_mom.mean()
                mom_std = raw_mom.std()
                if isinstance(mom_std, (int, float, np.floating)):
                    mom_std = max(mom_std, 1e-6)
                else:
                    mom_std = mom_std.where(mom_std > 1e-6, 1e-6)
                mom_z = (raw_mom - mom_mean) / mom_std

                # Theme scores
                theme_norm = pd.Series(
                    {t: _theme_score_normalized(t) for t in tickers},
                    index=tickers,
                )

                # Composite score
                composite = mom_z + theme_weight * theme_norm

                # Select top/bottom N
                valid = composite.dropna()
                if len(valid) < 2:
                    w_rows.append(pd.Series(0.0, index=tickers))
                    continue

                long_idx = valid.nlargest(n_positions).index
                short_idx = valid.nsmallest(n_positions).index

                w = pd.Series(0.0, index=tickers)
                n_long = len(long_idx)
                n_short = len(short_idx)
                if n_long > 0:
                    w[long_idx] = 1.0 / n_long
                if n_short > 0:
                    w[short_idx] = -1.0 / n_short

                w_rows.append(w)
                prev_date = date

            if not w_rows:
                return pd.DataFrame(0.0, index=date_idx, columns=tickers)

            return pd.DataFrame(w_rows, index=date_idx)

        return compute_weights(test_px.index)

    return signal_fn


# ── Main ─────────────────────────────────────────────────────────────
def main():
    print("=" * 60, file=sys.stderr)
    print("s547 — NEXTWAVE: Thematic Institutional Rotation", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Download S&P 100 prices
    prices = download_data(SP100_TICKERS, start="2005-01-01", asset_class="equity")

    # Print theme score coverage
    scored = sum(1 for t in SP100_TICKERS if t in THEME_SCORES)
    print(f"[s547] Theme scores assigned: {scored}/{len(SP100_TICKERS)} tickers", file=sys.stderr)

    # Parameter grid: n_positions × momentum_lookback × theme_weight
    # Within 27 combo budget (3 parameters)
    param_grid = [
        (n_pos, lb, tw)
        for n_pos in [5, 8]
        for lb in [126, 189, 252]
        for tw in [0.0, 0.3, 0.5]
    ]

    best_score = -999
    best_params = None
    best_metrics = None
    results = []

    for n_pos, lb, tw in param_grid:
        desc = f"n={n_pos}, lb={lb}, tw={tw:.1f}"
        print(f"\n[─] Testing: {desc}", file=sys.stderr)

        signal_fn = make_signal(
            n_positions=n_pos,
            momentum_lookback=lb,
            theme_weight=tw,
            gap=10,
        )

        # Count existing strategies for deflated Sharpe
        # (use a reasonable estimate)
        n_trials = 547  # s547 is the 547th strategy

        metrics = run_evaluation(
            prices=prices,
            signal_fn=signal_fn,
            cost_bps=10,
            asset_class="equity",
            n_trials=n_trials,
            beta_ticker="SPY",
        )

        score = metrics.get("SCORE", 0.0)
        results.append((n_pos, lb, tw, score, metrics))

        if score > best_score:
            best_score = score
            best_params = (n_pos, lb, tw)
            best_metrics = metrics

    # Print best result
    n_pos, lb, tw = best_params
    print("\n" + "=" * 60, file=sys.stderr)
    print(f"BEST: n={n_pos}, lb={lb}, tw={tw:.1f}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    for k in ["SCORE", "sharpe_net", "sharpe_gross", "deflated_sharpe", "sortino",
              "max_dd_pct", "ann_turnover", "n_trades", "win_rate", "beta_spy", "oos_years"]:
        print(f"{k:20s} {best_metrics.get(k, 'N/A')}")

    # Also print the theme_weight=0 baseline for comparison
    baseline_result = [r for r in results if r[3] == 0.0][0] if any(r[3] == 0.0 for r in results) else None
    if baseline_result:
        print("\n--- Baseline (pure momentum, tw=0.0) ---", file=sys.stderr)
        for k in ["SCORE", "sharpe_net", "sharpe_gross", "deflated_sharpe", "max_dd_pct"]:
            print(f"{k:20s} {baseline_result[4].get(k, 'N/A')}")

    # Print parameter sensitivity table
    print("\n--- Parameter Sensitivity ---")
    print(f"{'n_pos':>6s} {'lb':>5s} {'tw':>5s} {'SCORE':>8s} {'SR':>8s} {'DD':>8s} {'Trades':>8s}")
    for n_pos, lb, tw, score, m in results:
        sr = m.get("sharpe_net", 0)
        dd = m.get("max_dd_pct", 0)
        trades = m.get("n_trades", 0)
        print(f"{n_pos:>6d} {lb:>5d} {tw:>5.1f} {score:>8.4f} {sr:>8.4f} {dd:>8.1f} {trades:>8d}")

    # Ledger row for best
    print_ledger_row(
        strategy_id="s547",
        family="thematic-momentum",
        universe="sp100",
        metrics=best_metrics,
        n_params=3,
        status="keep" if best_score > 0 else "discard",
        description=f"NEXTWAVE: thematic institutional rotation on S&P 100, n={n_pos}, lb={lb}d, theme_w={tw:.1f}, gap=10d. Captures predicted institutional rotation into AI infrastructure.",
    )


if __name__ == "__main__":
    main()
