# Methods and data notes

## Scope

These are retrospective studies completed in September 2026. Dates in scouting sheets describe information cutoffs.

## Input inventory

| File | Rows | Games | Dates |
|---|---:|---:|---|
| shotdetail_2023 | 218,701 | 1,230 | 2023-10-24 to 2024-04-14 |
| shotdetail_2024 | 219,527 | 1,230 | 2024-10-22 to 2025-04-13 |
| shotdetail_2025 | 219,160 | 1,230 | 2025-10-21 to 2026-04-12 |
| pbpstats_2024 | 483,126 video-event rows | 1,230 | 2024-10-22 to 2025-04-13 |

Season names in source filenames identify the starting year. The possession file has 243,782 distinct possessions after removing repetitions across descriptions and video URLs. Shot counts in the two sources differ; no missing events are imputed. The archive revision and hashes are in `data/source_manifest.json`.

The source is an independently maintained archive of NBA data. Validation checks internal consistency, season/game coverage, event uniqueness, home/away identity, shot outcomes, cross-source linkage, SQL totals, and model information cutoffs. It does not independently reconcile every game against an official box score. Direct official-feed requests for an additional spot check returned HTTP 403; those requests were not counted as successful validation.

## Definitions

- **Effective field goal percentage:** field-goal points divided by twice the number of field-goal attempts. It does not include free throws.
- **Later shot:** a second or subsequent linked field goal attempt within an eligible possession, ordered by event identifier. Eligibility requires complete shot linkage and enough offensive rebounds to account for the extra attempts.
- **Shooting possession:** a possession with at least one field goal attempt. The team second-shot table uses this denominator, not all possessions.
- **Three-point residual:** observed make rate minus the average conditional baseline probability. It is not an estimate of pure luck.
- **Log loss:** average negative log probability assigned to the actual outcome. A lower value rewards accurate, appropriately calibrated probabilities. It is not accuracy percentage.
- **Brier score:** average squared difference between make probability and the binary outcome.
- **Posterior interval:** uncertainty about a player's latent make probability within the specified beta-binomial model.
- **Predictive interval:** uncertainty about a future made-shot count, conditional on the actual number of future attempts in this backtest.

## Uncertainty and model selection

The second-shot comparison and paired forecast-loss differences use 2,000 game-cluster bootstrap resamples with seed 20260908. The comparison resamples games jointly across both shot groups or both forecasting methods. It does not treat every shot as an independent game. Confidence intervals condition on the fitted models; they do not rerun model selection inside each resample.

Team residual intervals are marginal and unadjusted for multiple comparisons. Correlations across 30 teams are descriptive. The shooter prior treats estimated hyperparameters as fixed; reported posterior intervals omit hyperparameter uncertainty. Serial dependence across games, schedule effects, and changing roles remain possible sources of error.

The defense model selects regularization and residual shrinkage with later 2024-25 games, then refits the baseline on the whole development season. The shooter model fits its league prior on 2023-24 and selects history discount with the 2024-25 backtest. Both reserve 2025-26 for final evaluation. The January 1 cutoff and 30-attempt shooter threshold are fixed across development and test. The second-shot date restriction follows source-coverage diagnostics and is described separately from predictive validation.

## Maintaining the work

The input archives are pinned. A future data update should receive a new manifest rather than silently replacing these inputs. Compare game counts, missingness, unknown team IDs, shot-value labels, and predictor distributions before scoring. Review monthly calibration alongside sample size; the 2.5 percentage point flag is a review threshold, not proof of model failure. Save a new model artifact and backtest when changing features or tuning rules.

The current model files are research artifacts. There is no hosted prediction service or claim of production monitoring. Their readable parameters and recurring reporting outputs make further implementation possible without representing it as already deployed.

## Source references

- [NBA archive and upstream license](https://github.com/shufinskiy/nba_data)
- [Source field definitions](https://github.com/shufinskiy/nba_data/blob/main/description_fields.md)
- [pbpstats possessions](https://pbpstats.readthedocs.io/en/latest/pbpstats.resources.possessions.html)
- [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html)
- [SciPy beta-binomial distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.betabinom.html)
