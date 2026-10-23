# Decision brief: when to change the shooting scout

AI-assisted synthesis of the existing study, October 22, 2026. This is a proposed staff workflow, not a report of work performed for an NBA team. No film was reviewed for this brief.

**Decision:** use the January forecast to prioritize a shooting review, while retaining the prior-history estimate as the principal comparison. A hot raw percentage alone is weak evidence for a new coverage rule.

![Prior forecasts, updated probabilities and early observed rates with uncertainty](../figures/shooter_updates.png)

**Evidence:** the updated forecast improves held-out log loss by 0.00402 relative to the early percentage, but only 0.00019 relative to prior history alone. The latter 95% player-bootstrap interval is −0.000342 to −0.000040. There are 46,184 later attempts from 312 evaluated players; three forecasted players have no later attempts. These numbers support a modest predictive improvement in this backtest, not an estimate of points saved by a defensive scheme.

**Proposed next step:** review players with meaningful changes in both the forecast and their opportunity mix. Check corner share, catch-and-shoot versus pull-up opportunities where legitimately available, and whether the offensive role has changed. The public table already supports a corner-share check; the other tags require additional data or actual film coding. Select a review rule before looking at subsequent shooting results, and compare its usefulness against reviewing the highest-volume players.

**What would change the recommendation:** failure to improve on prior history in a new locked chronological backtest, subgroup miscalibration, or systematic role changes that make the historical prior inappropriate. A posterior interval for latent skill does not describe the full range of a player's percentage over the next ten attempts.

**Interview defense:** explain the distinction between an empirical prior, a player-history update and a forecast evaluated on later attempts. The ten largest movers in the chart illustrate shrinkage; selecting those movers after observing early results does not create a representative performance sample.

Sources: [full study](03_when_to_update_a_shooter.md), [forecast table](../results/shooter_forecasts.csv), [backtest summary](../results/shooter_summary.json), and [execution limits](../VALIDATION_CURRENT.md).
