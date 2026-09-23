import json
import numpy as np
import pandas as pd
from scipy.special import logit
from scipy.stats import pearsonr
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from .common import ROOT, shots, logloss, paired_loss_ci, save_json, cluster_mean_ci

FEATURES = ["shooter_prior_logit", "corner", "distance", "distance_squared"]


def prepare(current, previous):
    old = previous[previous.three & ~previous.heave]
    league = old.made.mean()
    rates = old.groupby("PLAYER_ID").made.agg(["sum", "count"])
    rates["prior"] = (rates["sum"] + 80 * league) / (rates["count"] + 80)
    d = current[current.three & ~current.heave].copy()
    d["shooter_prior_logit"] = logit(d.PLAYER_ID.map(rates.prior).fillna(league))
    d["distance"] = d.SHOT_DISTANCE.clip(20, 39)
    d["distance_squared"] = d.distance**2
    return d, league


def fit(d, c):
    m = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=2000))
    m.fit(d[FEATURES], d.made)
    return m


def apply_offset(early, late, k):
    g = early.groupby("opponent").agg(
        n=("made", "size"), observed=("made", "mean"), expected=("base", "mean")
    )
    g["offset"] = (g.observed - g.expected) * g.n / (g.n + k)
    return np.clip(late.base + late.opponent.map(g.offset).fillna(0), 0.03, 0.85)


def run():
    s23, s24, s25 = [shots(y) for y in [2023, 2024, 2025]]
    development, league24 = prepare(s24, s23)
    early = development[development.date < "2025-01-01"].copy()
    late = development[development.date >= "2025-01-01"].copy()
    tuning = []
    for c in [0.01, 0.1, 1, 10]:
        m = fit(early, c)
        early["base"] = m.predict_proba(early[FEATURES])[:, 1]
        late["base"] = m.predict_proba(late[FEATURES])[:, 1]
        for k in [0, 250, 500, 1000, 2000, 1e9]:
            tuning.append(
                {
                    "C": c,
                    "offset_prior_attempts": k,
                    "validation_logloss": logloss(
                        late.made, apply_offset(early, late, k)
                    ),
                }
            )
    tune = pd.DataFrame(tuning).sort_values("validation_logloss")
    tune.to_csv(ROOT / "results/defense_tuning.csv", index=False)
    best = tune.iloc[0]
    model = fit(development, best.C)
    test, league25 = prepare(s25, s24)
    test["base"] = model.predict_proba(test[FEATURES])[:, 1]
    a = test[test.date < "2026-01-01"].copy()
    b = test[test.date >= "2026-01-01"].copy()
    b["adjusted"] = apply_offset(a, b, best.offset_prior_attempts)
    early_rates = a.groupby("opponent").made.mean()
    b["raw_early"] = b.opponent.map(early_rates)
    predictions = {
        "Prior-season league rate": np.repeat(league25, len(b)),
        "Early opponent percentage": b.raw_early.to_numpy(),
        "Shot-context baseline": b.base.to_numpy(),
        "Baseline + early team residual": b.adjusted.to_numpy(),
    }
    scores = []
    for label, p in predictions.items():
        scores.append(
            {
                "model": label,
                "log_loss": logloss(b.made, p),
                "brier": float(np.mean((b.made - p) ** 2)),
                "attempts": len(b),
            }
        )
    pd.DataFrame(scores).to_csv(ROOT / "results/defense_validation.csv", index=False)
    teams = []
    for team in sorted(test.opponent.unique()):
        x = a[a.opponent == team]
        y = b[b.opponent == team]
        f = y[["GAME_ID"]].copy()
        f["residual"] = y.made - y.base
        lo, hi = cluster_mean_ci(f, "residual")
        teams.append(
            {
                "team": team,
                "early_attempts": len(x),
                "late_attempts": len(y),
                "early_observed": x.made.mean(),
                "late_observed": y.made.mean(),
                "early_expected": x.base.mean(),
                "late_expected": y.base.mean(),
                "early_residual": (x.made - x.base).mean(),
                "late_residual": (y.made - y.base).mean(),
                "late_residual_low": lo,
                "late_residual_high": hi,
                "early_corner_share": x.corner.mean(),
                "late_corner_share": y.corner.mean(),
            }
        )
    t = pd.DataFrame(teams)
    t.to_csv(ROOT / "results/defense_teams.csv", index=False)
    calibration = (
        b.assign(
            bin=pd.cut(
                b.base, [0, 0.30, 0.33, 0.35, 0.37, 0.39, 0.42, 1], include_lowest=True
            )
        )
        .groupby("bin", observed=True)
        .agg(
            attempts=("made", "size"),
            predicted=("base", "mean"),
            observed=("made", "mean"),
        )
        .reset_index()
    )
    calibration.to_csv(ROOT / "results/defense_calibration.csv", index=False)
    month = (
        b.assign(month=b.date.dt.strftime("%Y-%m"))
        .groupby("month")
        .agg(
            attempts=("made", "size"),
            expected=("base", "mean"),
            observed=("made", "mean"),
        )
        .reset_index()
    )
    month["residual"] = month.observed - month.expected
    month["review_required"] = month.residual.abs() > 0.025
    month.to_csv(ROOT / "results/defense_monitoring.csv", index=False)
    scaler = model.named_steps["standardscaler"]
    lr = model.named_steps["logisticregression"]
    artifact = {
        "features": FEATURES,
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coefficient": lr.coef_[0].tolist(),
        "intercept": float(lr.intercept_[0]),
        "C": float(best.C),
        "offset_prior_attempts": float(best.offset_prior_attempts),
        "shooter_prior_attempts": 80,
        "fit_season": "2024-25",
        "test_season": "2025-26",
        "excluded_distance_feet": 40,
        "prediction_unit": "Observed three-point attempt; conditional analysis, not a pregame forecast",
    }
    (ROOT / "models/three_point_context.json").write_text(
        json.dumps(artifact, indent=2)
    )
    summary = {
        "development_games": development.GAME_ID.nunique(),
        "test_games": test.GAME_ID.nunique(),
        "test_early_attempts": len(a),
        "test_late_attempts": len(b),
        "excluded_test_heaves": int((s25.three & s25.heave).sum()),
        "selected_C": best.C,
        "selected_offset_prior_attempts": best.offset_prior_attempts,
        "raw_repeatability_r": pearsonr(t.early_observed, t.late_observed).statistic,
        "residual_repeatability_r": pearsonr(
            t.early_residual, t.late_residual
        ).statistic,
        "context_vs_league_loss": paired_loss_ci(
            b, b.base, np.repeat(league25, len(b))
        ),
        "offset_vs_context_loss": paired_loss_ci(b, b.adjusted, b.base),
        "raw_early_vs_context_loss": paired_loss_ci(b, b.raw_early, b.base),
    }
    save_json("defense_summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
