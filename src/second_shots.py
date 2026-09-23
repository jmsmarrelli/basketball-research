import json, re
import numpy as np
import pandas as pd
from .common import ROOT, shots, cluster_mean_ci, save_json, SEED


def run():
    s = shots(2024)
    raw = pd.read_csv(ROOT / "data/raw/pbpstats_2024.csv", low_memory=False)
    key = [c for c in raw if c not in ["DESCRIPTION", "URL"]]
    # Video rows are event records, not additional possessions.
    poss = raw[key].drop_duplicates().reset_index(drop=True)
    poss["possession_id"] = np.arange(len(poss))
    r = raw.merge(poss, on=key, how="left", validate="many_to_one")
    r["GAME_EVENT_ID"] = pd.to_numeric(
        r.URL.str.extract(r"/\d{10}/(\d+)/", expand=False), errors="coerce"
    )
    links = r[["GAMEID", "GAME_EVENT_ID", "possession_id"]].dropna().drop_duplicates()
    ambiguous = links.duplicated(["GAMEID", "GAME_EVENT_ID"], keep=False)
    bad_events = int(ambiguous.sum())
    links = links.loc[~ambiguous].rename(columns={"GAMEID": "GAME_ID"})
    linked = s.merge(
        links, on=["GAME_ID", "GAME_EVENT_ID"], how="inner", validate="one_to_one"
    )
    counts = linked.groupby("possession_id").size()
    poss["linked_fga"] = poss.possession_id.map(counts).fillna(0).astype(int)
    poss["source_fga"] = poss.FG2A + poss.FG3A
    good = poss.linked_fga.eq(poss.source_fga) & poss.source_fga.gt(0)
    # Retained-ball fouls can create a later shot without an offensive rebound.
    good &= poss.OFFENSIVEREBOUNDS.ge(poss.source_fga - 1)
    poss["eligible"] = good
    d = linked.merge(
        poss[
            [
                "possession_id",
                "eligible",
                "OFFENSIVEREBOUNDS",
                "PERIOD",
                "STARTSCOREDIFFERENTIAL",
                "STARTTYPE",
            ]
        ],
        on="possession_id",
        suffixes=("", "_pos"),
    )
    d = d[d.eligible].sort_values(["possession_id", "GAME_EVENT_ID"]).copy()
    d["attempt_number"] = d.groupby("possession_id").cumcount() + 1
    d["phase"] = np.where(d.attempt_number == 1, "First shot", "Later shot")
    coverage = s[["GAME_ID", "GAME_EVENT_ID", "date"]].merge(
        d[["GAME_ID", "GAME_EVENT_ID"]].assign(matched=1),
        on=["GAME_ID", "GAME_EVENT_ID"],
        how="left",
        validate="one_to_one",
    )
    coverage["matched"] = coverage.matched.fillna(0)
    coverage.assign(month=coverage.date.dt.strftime("%Y-%m")).groupby(
        "month"
    ).matched.agg(attempts="size", matched="sum", coverage="mean").reset_index().to_csv(
        ROOT / "results/second_shot_coverage.csv", index=False
    )
    # The source loses video linkage in late February. Use the last contiguous
    # run of full months above 95% coverage, not a cutoff chosen from effect size.
    cutoff = pd.Timestamp("2025-02-01")
    d = d[d.date < cutoff].copy()
    source_window = s[s.date < cutoff]
    eligible_window = good & (pd.to_datetime(poss.GAMEDATE) < cutoff)
    d["zone"] = d.SHOT_ZONE_BASIC.replace(
        {
            "Left Corner 3": "Corner three",
            "Right Corner 3": "Corner three",
            "Above the Break 3": "Above-break three",
            "In The Paint (Non-RA)": "Paint outside restricted area",
            "Restricted Area": "Restricted area",
            "Mid-Range": "Midrange",
            "Backcourt": "Backcourt",
        }
    )
    inconsistent = (
        d.three
        & ~d.SHOT_ZONE_BASIC.isin(
            ["Left Corner 3", "Right Corner 3", "Above the Break 3", "Backcourt"]
        )
    ) | (
        ~d.three
        & d.SHOT_ZONE_BASIC.isin(
            ["Left Corner 3", "Right Corner 3", "Above the Break 3"]
        )
    )
    d.loc[inconsistent, "zone"] = "Unclassified"
    phase = []
    for name, g in d.groupby("phase"):
        lo, hi = cluster_mean_ci(g, "points")
        phase.append(
            {
                "phase": name,
                "attempts": len(g),
                "points_per_attempt": g.points.mean(),
                "lower": lo,
                "upper": hi,
                "efg": g.points.mean() / 2,
                "three_share": g.three.mean(),
                "rim_share": g.zone.eq("Restricted area").mean(),
            }
        )
    pd.DataFrame(phase).to_csv(ROOT / "results/second_shot_phase.csv", index=False)
    zone = (
        d.groupby(["phase", "zone"])
        .agg(attempts=("made", "size"), makes=("made", "sum"), points=("points", "sum"))
        .reset_index()
    )
    zone["points_per_attempt"] = zone.points / zone.attempts
    zone["share"] = zone.attempts / zone.groupby("phase").attempts.transform("sum")
    zone.to_csv(ROOT / "results/second_shot_zones.csv", index=False)
    # Symmetric Kitagawa decomposition: neither phase is privileged as a reference.
    z = zone.pivot(
        index="zone", columns="phase", values=["share", "points_per_attempt"]
    ).fillna(0)
    w1 = z["share"]["First shot"]
    w2 = z["share"]["Later shot"]
    p1 = z["points_per_attempt"]["First shot"]
    p2 = z["points_per_attempt"]["Later shot"]
    mix = float(((w2 - w1) * (p1 + p2) / 2).sum())
    within = float(((p2 - p1) * (w1 + w2) / 2).sum())
    teams = []
    for team, g in d.groupby("team"):
        later = g[g.attempt_number > 1]
        n = g.possession_id.nunique()
        teams.append(
            {
                "team": team,
                "matched_shooting_possessions": n,
                "later_attempts": len(later),
                "later_field_goal_points_per_100_shooting_possessions": 100
                * later.points.sum()
                / n,
                "later_rim_share": later.zone.eq("Restricted area").mean(),
                "later_ppa": later.points.mean(),
            }
        )
    pd.DataFrame(teams).to_csv(ROOT / "results/second_shot_teams.csv", index=False)
    # Sensitivity: exclude end-of-period shots and large score margins.
    clean = d[
        (d.MINUTES_REMAINING * 60 + d.SECONDS_REMAINING > 24)
        & d.STARTSCOREDIFFERENTIAL.abs().le(15)
    ]
    sensitivity = (
        clean.groupby("phase")
        .points.agg(["size", "mean"])
        .reset_index()
        .to_dict("records")
    )
    # Resample games jointly so first/later estimates retain their within-game dependence.
    g = (
        d.groupby(["GAME_ID", "phase"])
        .points.agg(["sum", "count"])
        .unstack(fill_value=0)
    )
    arr = np.column_stack(
        [
            g["sum"]["First shot"],
            g["count"]["First shot"],
            g["sum"]["Later shot"],
            g["count"]["Later shot"],
        ]
    )
    rng = np.random.default_rng(SEED)
    diff = []
    for _ in range(2000):
        t = arr[rng.integers(0, len(arr), len(arr))].sum(axis=0)
        diff.append(t[2] / t[3] - t[0] / t[1])
    summary = {
        "season": "2024-25",
        "window_start": str(d.date.min().date()),
        "window_end": str(d.date.max().date()),
        "window_games": d.GAME_ID.nunique(),
        "window_shot_chart_fga": len(source_window),
        "inconsistent_zone_labels": int(inconsistent.sum()),
        "source_video_rows": len(raw),
        "unique_possessions": len(poss),
        "source_possession_fga": int(poss.source_fga.sum()),
        "shot_chart_fga": len(s),
        "linked_shots": len(linked),
        "eligible_shots": len(d),
        "eligible_shooting_possessions": int(eligible_window.sum()),
        "ambiguous_link_rows_excluded": bad_events,
        "coverage_of_shot_chart": len(d) / len(source_window),
        "mix_component": mix,
        "within_zone_component": within,
        "ppa_gap": mix + within,
        "ppa_gap_ci": list(np.quantile(diff, [0.025, 0.975])),
        "sensitivity": sensitivity,
    }
    save_json("second_shot_summary.json", summary)
    # Review queue links point to game pages, without copying third-party video.
    examples = (
        d[(d.attempt_number > 1) & d.team.isin(["PHX", "SAS", "NOP"])]
        .groupby("team")
        .head(8)
        .copy()
    )
    examples["game_url"] = examples.GAME_ID.map(
        lambda x: f"https://www.nba.com/game/{x:010d}/play-by-play"
    )
    examples[
        [
            "team",
            "PLAYER_NAME",
            "date",
            "GAME_ID",
            "GAME_EVENT_ID",
            "PERIOD",
            "MINUTES_REMAINING",
            "SECONDS_REMAINING",
            "zone",
            "made",
            "game_url",
        ]
    ].to_csv(ROOT / "results/second_shot_film_queue.csv", index=False)
    d[
        [
            "GAME_ID",
            "GAME_EVENT_ID",
            "possession_id",
            "team",
            "phase",
            "zone",
            "points",
            "date",
        ]
    ].to_csv(ROOT / "data/second_shots_audit.csv.gz", index=False)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
