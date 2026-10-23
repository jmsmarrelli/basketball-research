import json, sqlite3, unittest
import numpy as np
import pandas as pd
import pytest
from scipy.special import expit
from src.common import ROOT, shots, TEAM, logloss
from src.shooter_updates import posterior
from src.three_point_defense import prepare, FEATURES


class ResearchChecks(unittest.TestCase):
    @pytest.mark.requires_raw
    def test_binary_scoring(self):
        for season in [2023, 2024, 2025]:
            d = shots(season)
            self.assertEqual(d.GAME_ID.nunique(), 1230)
            self.assertTrue(d.points.isin([0, 2, 3]).all())
            self.assertTrue(d.date.min().year == season)
            self.assertTrue(d.date.max().year == season + 1)
            self.assertFalse(d.team.eq(d.opponent).any())

    @pytest.mark.requires_raw
    def test_sql_totals_and_prior_frame(self):
        with sqlite3.connect(ROOT / "data/research.sqlite") as c:
            count = c.execute("SELECT COUNT(*) FROM shots").fetchone()[0]
            self.assertEqual(count, 657388)
            rows = c.execute(
                "SELECT prior_attempts, prior_makes, made FROM player_history_before_shot WHERE player_id=201939 ORDER BY date,game_id,game_event_id LIMIT 5"
            ).fetchall()
            made = 0
            for i, (n, m, y) in enumerate(rows):
                self.assertEqual(n, i)
                self.assertEqual(m, made)
                made += y

    def test_posterior_updates(self):
        previous = pd.DataFrame({"PLAYER_ID": [1] * 4, "made": [1, 0, 1, 0]})
        early = pd.DataFrame({"PLAYER_ID": [1] * 3 + [2], "made": [1, 1, 0, 1]})
        p = posterior(previous, early, 2, 3, 0.5)
        self.assertEqual(p.loc[1, "alpha"], 5)
        self.assertEqual(p.loc[1, "beta"], 5)
        self.assertAlmostEqual(p.loc[2, "posterior_mean"], 0.5)
        self.assertGreater(p.loc[1, "posterior_mean"], p.loc[1, "prior_forecast"])

    def test_future_results_not_used_in_context_features(self):
        # Deliberately small test fixture; no synthetic rows enter research outputs.
        previous = pd.DataFrame({'PLAYER_ID': [1, 1, 2, 2], 'made': [1, 0, 0, 1],
                                 'three': [True]*4, 'heave': [False]*4})
        current = pd.DataFrame({'PLAYER_ID': [1, 2, 3], 'made': [1, 0, 1],
                                'three': [True]*3, 'heave': [False]*3,
                                'corner': [True, False, False], 'SHOT_DISTANCE': [22, 26, 29]})
        a, _ = prepare(current, previous)
        current["made"] = 1 - current.made
        b, _ = prepare(current, previous)
        np.testing.assert_array_equal(a[FEATURES], b[FEATURES])

    def test_second_shot_accounting(self):
        s = json.loads((ROOT / "results/second_shot_summary.json").read_text())
        p = pd.read_csv(ROOT / "results/second_shot_phase.csv")
        self.assertEqual(int(p.attempts.sum()), s["eligible_shots"])
        self.assertGreater(s["coverage_of_shot_chart"], 0.95)
        self.assertAlmostEqual(
            s["mix_component"] + s["within_zone_component"], s["ppa_gap"], places=10
        )
        self.assertEqual(s["ambiguous_link_rows_excluded"], 0)
        self.assertEqual(s["window_end"], "2025-01-31")

    def test_held_out_forecasts(self):
        p = pd.read_csv(ROOT / "results/shooter_forecasts.csv")
        self.assertTrue((p.early_attempts >= 30).all())
        self.assertTrue((p.low90 < p.posterior_mean).all())
        self.assertTrue((p.high90 > p.posterior_mean).all())
        self.assertTrue(p.posterior_mean.between(0, 1).all())
        s = json.loads((ROOT / "results/shooter_summary.json").read_text())
        self.assertEqual(int(p.later_attempts.sum()), s["evaluation_attempts"])

    def test_serialized_model_probabilities(self):
        a = json.loads((ROOT / "models/three_point_context.json").read_text())
        x = np.array([[0.0, 1.0, 23.0, 529.0]])
        z = (x - np.array(a["mean"])) / np.array(a["scale"])
        p = expit(z @ np.array(a["coefficient"]) + a["intercept"])
        self.assertTrue(np.all((p > 0) & (p < 1)))
        self.assertEqual(a["fit_season"], "2024-25")
        self.assertEqual(a["test_season"], "2025-26")

    def test_loss_penalizes_wrong_confidence(self):
        self.assertGreater(logloss([0, 1], [0.9, 0.1]), logloss([0, 1], [0.5, 0.5]))


if __name__ == "__main__":
    unittest.main()
