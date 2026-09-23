import json
import numpy as np
import pandas as pd
from scipy.special import betaln
from scipy.optimize import minimize
from scipy.stats import beta, betabinom
from .common import ROOT, shots, logloss, save_json, paired_loss_ci


def totals(d):
    return d.groupby("PLAYER_ID").made.agg(makes="sum", attempts="size")


def fit_prior(d):
    t = totals(d)

    def objective(v):
        a, b = np.exp(v)
        return -float(
            (betaln(t.makes + a, t.attempts - t.makes + b) - betaln(a, b)).sum()
        )

    fit = minimize(
        objective, np.log([12.0, 22.0]), method="L-BFGS-B", bounds=[(-4, 10), (-4, 10)]
    )
    if not fit.success:
        raise ValueError(fit.message)
    return np.exp(fit.x)


def posterior(previous, early, alpha, beta_, discount):
    a = totals(early).rename(
        columns={"makes": "early_makes", "attempts": "early_attempts"}
    )
    old = totals(previous).rename(
        columns={"makes": "previous_makes", "attempts": "previous_attempts"}
    )
    a = a.join(old).fillna(0)
    a["prior_alpha"] = alpha + discount * a.previous_makes
    a["prior_beta"] = beta_ + discount * (a.previous_attempts - a.previous_makes)
    a["alpha"] = a.prior_alpha + a.early_makes
    a["beta"] = a.prior_beta + a.early_attempts - a.early_makes
    a["prior_forecast"] = a.prior_alpha / (a.prior_alpha + a.prior_beta)
    a["posterior_mean"] = a.alpha / (a.alpha + a.beta)
    a["early_rate"] = a.early_makes / a.early_attempts
    return a


def run():
    years = {y: shots(y) for y in [2023, 2024, 2025]}
    d = {y: v[v.three & ~v.heave].copy() for y, v in years.items()}
    alpha, beta_ = fit_prior(d[2023])
    a24 = d[2024][d[2024].date < "2025-01-01"]
    b24 = d[2024][d[2024].date >= "2025-01-01"]
    tuning = []
    for w in [0, 0.1, 0.25, 0.5, 1]:
        p = posterior(d[2023], a24, alpha, beta_, w)
        p = p[p.early_attempts >= 30]
        f = b24[b24.PLAYER_ID.isin(p.index)]
        tuning.append(
            {
                "history_discount": w,
                "validation_logloss": logloss(
                    f.made, f.PLAYER_ID.map(p.posterior_mean)
                ),
                "attempts": len(f),
            }
        )
    tune = pd.DataFrame(tuning).sort_values("validation_logloss")
    tune.to_csv(ROOT / "results/shooter_tuning.csv", index=False)
    w = float(tune.iloc[0].history_discount)
    early = d[2025][d[2025].date < "2026-01-01"]
    later = d[2025][d[2025].date >= "2026-01-01"]
    p = posterior(d[2024], early, alpha, beta_, w)
    p = p[p.early_attempts >= 30].copy()
    p["low90"] = beta.ppf(0.05, p.alpha, p.beta)
    p["high90"] = beta.ppf(0.95, p.alpha, p.beta)
    # This probability is conditional on a fixed prior forecast, not P(true year-to-year improvement).
    p["prob_above_prior_plus_3pp"] = beta.sf(
        np.minimum(p.prior_forecast + 0.03, 0.999), p.alpha, p.beta
    )
    p["forecast_change"] = p.posterior_mean - p.prior_forecast
    future = totals(later).rename(
        columns={"makes": "later_makes", "attempts": "later_attempts"}
    )
    p = p.join(future)
    p["later_rate"] = p.later_makes / p.later_attempts
    names = early.groupby("PLAYER_ID").PLAYER_NAME.last()
    p["player"] = p.index.map(names)
    p["team_at_cutoff"] = p.index.map(early.groupby("PLAYER_ID").team.last())
    p["early_corner_share"] = p.index.map(early.groupby("PLAYER_ID").corner.mean())
    p["previous_corner_share"] = p.index.map(d[2024].groupby("PLAYER_ID").corner.mean())
    p["corner_share_change"] = p.early_corner_share - p.previous_corner_share
    p["predicted_makes_low90"] = betabinom.ppf(0.05, p.later_attempts, p.alpha, p.beta)
    p["predicted_makes_high90"] = betabinom.ppf(0.95, p.later_attempts, p.alpha, p.beta)
    p["covered"] = p.later_makes.between(
        p.predicted_makes_low90, p.predicted_makes_high90
    )
    p.reset_index().to_csv(ROOT / "results/shooter_forecasts.csv", index=False)
    f = later[later.PLAYER_ID.isin(p.index)].copy()
    league = d[2024].made.mean()
    methods = {
        "Previous-season league rate": np.repeat(league, len(f)),
        "Early-season percentage": f.PLAYER_ID.map(p.early_rate),
        "Previous-history forecast": f.PLAYER_ID.map(p.prior_forecast),
        "Updated Bayesian forecast": f.PLAYER_ID.map(p.posterior_mean),
    }
    rows = [
        {
            "model": n,
            "log_loss": logloss(f.made, v),
            "brier": float(np.mean((f.made - v) ** 2)),
            "attempts": len(f),
        }
        for n, v in methods.items()
    ]
    pd.DataFrame(rows).to_csv(ROOT / "results/shooter_validation.csv", index=False)
    valid = p[p.later_attempts.notna()]
    # Game clusters capture common shooting conditions and shared opponents.
    summary = {
        "prior_alpha": alpha,
        "prior_beta": beta_,
        "history_discount": w,
        "forecast_date": "2026-01-01",
        "minimum_early_attempts": 30,
        "forecast_players": len(p),
        "evaluated_players": len(valid),
        "players_without_later_attempts": int(p.later_attempts.isna().sum()),
        "evaluation_attempts": len(f),
        "predictive_90_coverage": valid.covered.mean(),
        "updated_vs_raw_loss": paired_loss_ci(
            f, methods["Updated Bayesian forecast"], methods["Early-season percentage"]
        ),
        "updated_vs_prior_loss": paired_loss_ci(
            f,
            methods["Updated Bayesian forecast"],
            methods["Previous-history forecast"],
        ),
    }
    save_json("shooter_summary.json", summary)
    (ROOT / "models/shooter_prior.json").write_text(
        json.dumps(
            {
                "alpha": alpha,
                "beta": beta_,
                "history_discount": w,
                "minimum_early_attempts": 30,
                "prior_fit_season": "2023-24",
                "discount_tuning_season": "2024-25",
                "test_season": "2025-26",
            },
            indent=2,
        )
    )
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
