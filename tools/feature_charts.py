"""Rebuild the flagship chart from committed results: python -m tools.feature_charts."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter
from .chart_style import canvas, finish, stat, note, tidy, TEAL, ORANGE, MUTED, PALE

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = pd.read_csv(ROOT / "results/shooter_forecasts.csv")
    q = p.nlargest(10, "forecast_change").sort_values("forecast_change", ascending=False)
    s = json.loads((ROOT / "results/shooter_summary.json").read_text())
    fig = canvas("01 / Shooter evaluation", "How much should a hot start change your mind?",
                 "Ten largest upward Bayesian forecast changes · January 1, 2026 cutoff · minimum 30 early attempts", 9.5)
    ax = fig.add_axes([.22, .235, .48, .49])
    y = np.arange(len(q))
    ax.hlines(y, q.prior_forecast, q.posterior_mean, color=PALE, lw=7)
    ax.hlines(y, q.low90, q.high90, color=TEAL, lw=1.6)
    ax.scatter(q.prior_forecast, y, s=43, facecolors="white", edgecolors=MUTED,
               label="Prior forecast", zorder=3)
    ax.scatter(q.posterior_mean, y, s=68, color=TEAL, label="Updated forecast", zorder=4)
    ax.scatter(q.early_rate, y, s=48, color=ORANGE, marker="x", linewidths=1.8,
               label="Early observed rate", zorder=4)
    ax.set_yticks(y, q.player)
    ax.set_ylim(len(q)-.45, -.6)
    ax.set_xlim(.29, max(.62, q.early_rate.max()+.025))
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_xlabel("Three-point make probability", labelpad=13)
    tidy(ax)
    ax.legend(loc="lower left", bbox_to_anchor=(-.38, 1.06), ncol=3,
              frameon=False, fontsize=10, columnspacing=1.8)
    stat(fig, .765, .69, f"{s['evaluation_attempts']:,}", "later attempts in the backtest")
    stat(fig, .765, .55, f"{s['updated_vs_raw_loss']['difference']:+.5f}", "log loss vs. early raw percentage")
    stat(fig, .765, .41, f"{s['updated_vs_prior_loss']['difference']:+.5f}", "log loss vs. prior history alone")
    note(fig, .765, .30, "A measured update", "The gain over history alone is small. Use the forecast to guide film review, not to certify a new shooting skill.", width=28)
    finish(fig, ROOT / "figures/shooter_updates",
           "Source: results/shooter_forecasts.csv and shooter_summary.json · 312 players evaluated on later attempts.",
           "Thin teal lines: 90% posterior intervals for latent probability. Selected movers are illustrative; lower log loss is better.")


if __name__ == "__main__":
    main()
