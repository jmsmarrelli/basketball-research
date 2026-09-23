"""Fetch pinned public inputs and build the indexed shot table used by SQL checks."""

from pathlib import Path
import argparse, hashlib, json, sqlite3, tarfile, urllib.request
import pandas as pd
from .common import ROOT, shots


def fetch():
    manifest = json.loads((ROOT / "data/source_manifest.json").read_text())
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    for item in manifest["files"]:
        archive = raw / (item["name"] + ".tar.xz")
        if not archive.exists():
            with urllib.request.urlopen(item["url"], timeout=180) as r:
                archive.write_bytes(r.read())
        if hashlib.sha256(archive.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Checksum mismatch: {archive.name}")
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                if member.isfile() and member.name.endswith(".csv"):
                    # Deliberately do not use extractall on a downloaded archive.
                    with tar.extractfile(member) as f:
                        (raw / Path(member.name).name).write_bytes(f.read())
        print(item["name"], "verified")


def database():
    path = ROOT / "data/research.sqlite"
    with sqlite3.connect(path) as con:
        frames = []
        for season in [2023, 2024, 2025]:
            d = shots(season)
            d["season"] = season
            frames.append(
                d[
                    [
                        "season",
                        "GAME_ID",
                        "GAME_EVENT_ID",
                        "PLAYER_ID",
                        "PLAYER_NAME",
                        "date",
                        "team",
                        "opponent",
                        "three",
                        "corner",
                        "heave",
                        "made",
                        "points",
                    ]
                ].rename(columns=str.lower)
            )
        d = pd.concat(frames)
        d["date"] = d.date.dt.strftime("%Y-%m-%d")
        d.to_sql("shots", con, if_exists="replace", index=False)
        con.execute("CREATE UNIQUE INDEX shot_event ON shots(game_id, game_event_id)")
        con.execute(
            "CREATE INDEX shot_player_date ON shots(player_id, date, game_id, game_event_id)"
        )
        con.execute(
            "CREATE INDEX shot_season_opponent ON shots(season, opponent, date)"
        )
        query = (ROOT / "sql/scouting_queries.sql").read_text()
        con.executescript(query)
        result = pd.read_sql_query("SELECT * FROM opponent_splits", con)
        result.to_csv(ROOT / "results/sql_opponent_splits.csv", index=False)
        for (season, side), g in result.groupby(["season", "split"]):
            expected = d[(d.season == season) & d.three & ~d.heave]
            expected = expected[
                (
                    expected.date.lt(f"{season+1}-01-01")
                    if side == "early"
                    else expected.date.ge(f"{season+1}-01-01")
                )
            ]
            assert int(g.attempts.sum()) == len(expected)
    return len(d)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["fetch", "sql"])
    args = parser.parse_args()
    if args.action == "fetch":
        fetch()
    else:
        print(database(), "shots indexed; SQL totals reconciled")
