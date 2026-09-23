-- One event is one shot. The unique index rejects accidental double counting.
DROP VIEW IF EXISTS opponent_splits;
CREATE VIEW opponent_splits AS
SELECT season, opponent,
       CASE WHEN date < printf('%d-01-01', season + 1) THEN 'early' ELSE 'late' END AS split,
       COUNT(*) AS attempts, SUM(made) AS makes,
       1.0 * SUM(made) / COUNT(*) AS three_point_percentage,
       AVG(corner) AS corner_share
FROM shots
WHERE three = 1 AND heave = 0
GROUP BY season, opponent, split;

-- The preceding frame excludes the current shot's outcome from its features.
DROP VIEW IF EXISTS player_history_before_shot;
CREATE VIEW player_history_before_shot AS
SELECT season, game_id, game_event_id, player_id, player_name, date, made,
       COUNT(*) OVER history AS prior_attempts,
       COALESCE(SUM(made) OVER history, 0) AS prior_makes
FROM shots
WHERE three = 1 AND heave = 0
WINDOW history AS (
    PARTITION BY player_id
    ORDER BY date, game_id, game_event_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
);
