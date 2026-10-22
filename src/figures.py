import json
import numpy as np
import pandas as pd
import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".cache/matplotlib")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from .common import ROOT

NAVY = "#172D45"
BLUE = "#176B87"
ORANGE = "#B64A24"
GRAY = "#66727C"
LIGHT = "#DDE3E8"
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.labelcolor": NAVY,
        "text.color": NAVY,
        "axes.edgecolor": LIGHT,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.titleweight": "bold",
        "axes.titlesize": 15,
        "xtick.color": GRAY,
        "ytick.color": NAVY,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "svg.fonttype": "none",
        "svg.hashsalt": "basketball-portfolio",
        "savefig.facecolor": "white",
    }
)


def save(fig, name, caption):
    fig.text(0.06, 0.025, caption, fontsize=9, color=GRAY, ha="left")
    fig.savefig(
        ROOT / f"figures/{name}.png",
        dpi=180,
        bbox_inches="tight",
        metadata={"Software": None},
    )
    fig.savefig(
        ROOT / f"figures/{name}.svg",
        bbox_inches="tight",
        metadata={"Creator": None, "Date": None, "Description": caption},
    )
    svg = ROOT / f"figures/{name}.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)


def run():
    z = pd.read_csv(ROOT / "results/second_shot_zones.csv")
    z = z[~z.zone.isin(["Backcourt", "Unclassified"])]
    order = [
        "Restricted area",
        "Paint outside restricted area",
        "Midrange",
        "Corner three",
        "Above-break three",
    ]
    labels = [
        "Restricted area",
        "Other paint",
        "Midrange",
        "Corner three",
        "Above-break three",
    ]
    fig, ax = plt.subplots(1, 2, figsize=(12, 5.4))
    fig.subplots_adjust(left=0.18, right=0.96, bottom=0.2, top=0.83, wspace=0.35)
    for i, (metric, title) in enumerate(
        [
            ("share", "Where the attempts came from"),
            ("points_per_attempt", "Points per attempt"),
        ]
    ):
        p = z.pivot(index="zone", columns="phase", values=metric).loc[order]
        y = np.arange(len(p))
        ax[i].hlines(y, p["First shot"], p["Later shot"], color=LIGHT, lw=4)
        ax[i].scatter(
            p["First shot"], y, s=65, color=BLUE, label="First shot", zorder=3
        )
        ax[i].scatter(
            p["Later shot"], y, s=65, color=ORANGE, label="Later shot", zorder=3
        )
        ax[i].set_yticks(y, labels if i == 0 else [""] * len(y))
        ax[i].invert_yaxis()
        ax[i].set_title(title, loc="left", pad=15)
        ax[i].grid(axis="x", alpha=0.2)
        if i == 0:
            ax[i].xaxis.set_major_formatter(PercentFormatter(1))
            ax[i].set_xlim(0, 0.56)
            ax[i].legend(
                loc="lower left", bbox_to_anchor=(0, -0.22), ncol=2, frameon=False
            )
        else:
            ax[i].set_xlim(0.65, 1.5)
    save(
        fig,
        "second_shot_mix",
        "2024-25 through January 31. Complete linked shooting possessions; free throws excluded.",
    )
    summary = json.loads((ROOT / "results/second_shot_summary.json").read_text())
    fig, ax = plt.subplots(figsize=(9.3, 5))
    fig.subplots_adjust(left=0.27, right=0.92, bottom=0.22, top=0.82)
    vals = [
        summary["mix_component"] * 100,
        summary["within_zone_component"] * 100,
        summary["ppa_gap"] * 100,
    ]
    ax.barh([2, 1, 0], vals, color=[BLUE, ORANGE, NAVY], height=0.52)
    ax.set_yticks(
        [2, 1, 0],
        [
            "Different shot locations",
            "Different results within zones",
            "Observed difference",
        ],
    )
    ax.axvline(0, color=GRAY, lw=0.8)
    for y, v in zip([2, 1, 0], vals):
        ax.text(
            v + (0.3 if v >= 0 else -0.3),
            y + (0.28 if y == 0 else 0),
            f"{v:+.1f}",
            va="center",
            ha="left" if v >= 0 else "right",
            fontweight="bold",
        )
    lo, hi = np.array(summary["ppa_gap_ci"]) * 100
    ax.errorbar(
        vals[-1],
        0,
        xerr=[[vals[-1] - lo], [hi - vals[-1]]],
        fmt="none",
        color=NAVY,
        capsize=5,
    )
    ax.set_xlim(-9, 10)
    ax.set_xlabel("Later minus first: points per 100 field goal attempts")
    ax.set_title("The location gain mostly disappears within zones", loc="left", pad=18)
    save(
        fig,
        "second_shot_decomposition",
        "Symmetric shot-mix decomposition. Error bar: 95% game-cluster bootstrap interval for the total.",
    )
    c = pd.read_csv(ROOT / "results/second_shot_coverage.csv")
    fig, ax = plt.subplots(figsize=(9.3, 4.6))
    fig.subplots_adjust(left=0.1, right=0.94, bottom=0.22, top=0.8)
    ax.bar(c.month, c.coverage, color=[BLUE] * 4 + [GRAY] * 3)
    ax.axhline(0.95, ls="--", color=ORANGE, lw=1)
    ax.set_ylim(0, 1.07)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title(
        "Possession linkage is not complete for the whole season", loc="left", pad=18
    )
    for i, r in c.iterrows():
        ax.text(i, r.coverage + 0.025, f"{r.coverage:.1%}", ha="center", fontsize=10)
    save(
        fig,
        "second_shot_coverage",
        "Share of all shot-chart attempts in complete linked possessions. Main analysis stops after January.",
    )
    t = pd.read_csv(ROOT / "results/defense_teams.csv")
    fig, ax = plt.subplots(figsize=(9.3, 6))
    fig.subplots_adjust(left=0.12, right=0.94, bottom=0.2, top=0.82)
    ax.axhline(0, color=LIGHT)
    ax.axvline(0, color=LIGHT)
    for _, r in t.iterrows():
        color = ORANGE if r.team in ["PHX", "SAS", "NOP"] else BLUE
        ax.scatter(r.early_residual * 100, r.late_residual * 100, color=color, s=30)
        ax.annotate(
            r.team,
            (r.early_residual * 100, r.late_residual * 100),
            xytext={
                "ATL": (8, 8),
                "ORL": (-27, 6),
                "HOU": (6, 1),
                "IND": (-26, -10),
                "MIA": (-23, 9),
                "DET": (-25, -10),
                "PHX": (6, -10),
            }.get(r.team, (4, 4)),
            textcoords="offset points",
            fontsize=9,
            color=color,
        )
    ax.set_xlabel("Before January 1: made minus expected (percentage points)")
    ax.set_ylabel("January 1 onward (percentage points)")
    ax.set_title("Early shooting residuals did not persist", loc="left", pad=18)
    save(
        fig,
        "defense_repeatability",
        "2025-26 regular season. Expectations account for prior shooter results, distance, and corner location.",
    )
    v = pd.read_csv(ROOT / "results/defense_validation.csv")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    fig.subplots_adjust(left=0.37, right=0.93, bottom=0.23, top=0.82)
    y = np.arange(len(v))
    ax.scatter(v.log_loss, y, s=85, color=[GRAY, ORANGE, BLUE, NAVY])
    ax.set_yticks(
        y,
        [
            "Prior-season league rate",
            "Early opponent percentage",
            "Shot-context baseline",
            "Baseline + team residual",
        ],
    )
    ax.invert_yaxis()
    ax.set_xlim(v.log_loss.min() - 0.0007, v.log_loss.max() + 0.0009)
    for i, r in v.iterrows():
        ax.text(r.log_loss + 0.00013, i, f"{r.log_loss:.5f}", va="center", fontsize=10)
    ax.set_xlabel("Log loss on later games; lower is better")
    ax.set_title("Test the scouting shortcut on later games", loc="left", pad=18)
    save(
        fig,
        "defense_validation",
        "54,257 three-point attempts, January-April 2026. Tuning used only 2024-25 outcomes.",
    )
    c = pd.read_csv(ROOT / "results/defense_calibration.csv")
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    fig.subplots_adjust(left=0.13, right=0.92, bottom=0.2, top=0.83)
    ax.plot([0.15, 0.5], [0.15, 0.5], color=LIGHT, ls="--")
    ax.scatter(
        c.predicted,
        c.observed,
        s=30 + 300 * c.attempts / c.attempts.max(),
        color=BLUE,
        alpha=0.8,
    )
    for _, r in c.iloc[::2].iterrows():
        ax.annotate(
            f"n={r.attempts:,}",
            (r.predicted, r.observed),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )
    ax.set_xlabel("Average predicted make probability")
    ax.set_ylabel("Observed make rate")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("Calibration of the shot-context baseline", loc="left", pad=18)
    save(
        fig,
        "defense_calibration",
        "Held-out January-April 2026 attempts. Bubble area reflects sample size; no defender-distance data.",
    )
    p = pd.read_csv(ROOT / "results/shooter_forecasts.csv")
    q = p.nlargest(10, "forecast_change").sort_values("forecast_change")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    fig.subplots_adjust(left=0.23, right=0.96, bottom=0.22, top=0.85)
    for i, (_, r) in enumerate(q.iterrows()):
        ax.plot([r.prior_forecast, r.posterior_mean], [i, i], color=LIGHT, lw=4)
        ax.plot([r.low90, r.high90], [i, i], color=BLUE, lw=1.5)
    ax.scatter(
        q.prior_forecast,
        np.arange(len(q)),
        color=GRAY,
        s=30,
        label="Prior forecast",
        zorder=3,
    )
    ax.scatter(
        q.posterior_mean,
        np.arange(len(q)),
        color=BLUE,
        s=60,
        label="Updated forecast",
        zorder=4,
    )
    ax.scatter(
        q.early_rate,
        np.arange(len(q)),
        color=ORANGE,
        s=45,
        marker="x",
        label="Early percentage",
        zorder=4,
    )
    ax.set_yticks(np.arange(len(q)), q.player)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Three-point make probability")
    ax.set_title("How far should a hot start move the forecast?", loc="left", pad=18)
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(-0.17, -0.3),
        ncol=3,
        frameon=False,
        fontsize=10,
    )
    save(
        fig,
        "shooter_updates",
        "Largest upward forecast changes as of January 1, 2026. Lines: 90% posterior intervals; 30+ early attempts.",
    )
    v = pd.read_csv(ROOT / "results/shooter_validation.csv")
    fig, ax = plt.subplots(figsize=(10, 4.7))
    fig.subplots_adjust(left=0.37, right=0.94, bottom=0.23, top=0.82)
    ax.scatter(v.log_loss, np.arange(len(v)), s=85, color=[GRAY, ORANGE, NAVY, BLUE])
    ax.set_yticks(
        np.arange(len(v)),
        [
            "Prior-season league rate",
            "Early-season percentage",
            "Previous-history forecast",
            "Updated Bayesian forecast",
        ],
    )
    ax.invert_yaxis()
    ax.set_xlim(v.log_loss.min() - 0.0008, v.log_loss.max() + 0.0012)
    for i, r in v.iterrows():
        ax.text(r.log_loss + 0.0002, i, f"{r.log_loss:.5f}", va="center", fontsize=10)
    ax.set_xlabel("Log loss on later attempts; lower is better")
    ax.set_title("A hot-start percentage is a poor forecast", loc="left", pad=18)
    save(
        fig,
        "shooter_validation",
        "46,184 held-out attempts from 312 players. Backtest cutoff: January 1, 2026.",
    )
    q = (
        p[p.team_at_cutoff.isin(["PHX", "SAS", "NOP"]) & p.early_attempts.ge(60)]
        .nlargest(12, "early_attempts")
        .sort_values("posterior_mean")
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.subplots_adjust(left=0.25, right=0.95, bottom=0.2, top=0.83)
    y = np.arange(len(q))
    ax.hlines(y, q.low90, q.high90, color=BLUE, lw=2)
    ax.scatter(q.posterior_mean, y, color=BLUE, s=45, label="January forecast")
    ax.scatter(
        q.later_rate, y, color=ORANGE, marker="x", s=45, label="Later observed rate"
    )
    ax.set_yticks(y, q.player + " (" + q.team_at_cutoff + ")")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Three-point make rate")
    ax.set_title("A January scouting sheet, then the later results", loc="left", pad=18)
    ax.legend(
        frameon=False, loc="lower left", bbox_to_anchor=(0, -0.28), ncol=2, fontsize=10
    )
    save(
        fig,
        "shooter_team_sheet",
        "Team at the January cutoff. Intervals describe latent probability, not a prediction interval for later FG%.",
    )
    from tools.feature_charts import main as feature_charts
    feature_charts()
    return 9


if __name__ == "__main__":
    print(run())
