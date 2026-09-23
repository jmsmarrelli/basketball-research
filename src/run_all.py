import argparse
from .data import fetch, database
from . import second_shots, three_point_defense, shooter_updates, figures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        fetch()
    database()
    for name, module in [
        ("Second shots", second_shots),
        ("Three-point defense", three_point_defense),
        ("Shooter updates", shooter_updates),
    ]:
        print(name, flush=True)
        print(module.run(), flush=True)
    print("Figures:", figures.run())


if __name__ == "__main__":
    main()
