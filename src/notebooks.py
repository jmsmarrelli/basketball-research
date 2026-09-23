"""Create and execute the three review notebooks with the current Python environment."""

import os, sys, json
import nbformat as nb
from nbclient import NotebookClient
from .common import ROOT


def run():
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    for key, folder in [
        ("JUPYTER_RUNTIME_DIR", "runtime"),
        ("IPYTHONDIR", "ipython"),
        ("MPLCONFIGDIR", "matplotlib"),
    ]:
        p = cache / folder
        p.mkdir(exist_ok=True)
        os.environ[key] = str(p)
    spec = cache / "jupyter/kernels/research"
    spec.mkdir(parents=True, exist_ok=True)
    (spec / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [
                    sys.executable,
                    "-m",
                    "ipykernel_launcher",
                    "-f",
                    "{connection_file}",
                ],
                "display_name": "Python 3",
                "language": "python",
            }
        )
    )
    os.environ["JUPYTER_PATH"] = str(cache / "jupyter")
    jobs = [
        (
            "01_after_the_miss",
            "second_shots",
            "second_shot_phase",
            "second_shot_mix",
            "second_shot_decomposition",
        ),
        (
            "02_three_point_defense",
            "three_point_defense",
            "defense_validation",
            "defense_validation",
            "defense_repeatability",
        ),
        (
            "03_when_to_update_a_shooter",
            "shooter_updates",
            "shooter_validation",
            "shooter_updates",
            "shooter_validation",
        ),
    ]
    for stem, module, table, fig1, fig2 in jobs:
        article = (ROOT / f"reports/{stem}.md").read_text()
        book = nb.v4.new_notebook(
            metadata={
                "kernelspec": {
                    "name": "python3",
                    "display_name": "Python 3",
                    "language": "python",
                },
                "language_info": {"name": "python", "version": "3.12"},
            }
        )
        book.cells = [
            nb.v4.new_markdown_cell(article.split("##")[0]),
            nb.v4.new_code_cell(
                "from pathlib import Path\nimport os, sys\nroot = Path.cwd()\nif root.name == 'notebooks':\n    root = root.parent\nsys.path.insert(0, str(root))\nos.chdir(root)\nimport pandas as pd\nfrom IPython.display import display, Image\nfrom src import "
                + module
                + "\nsummary = "
                + module
                + ".run()\nsummary"
            ),
            nb.v4.new_markdown_cell(
                "## Results\nThe following table is regenerated from the pinned inputs."
            ),
            nb.v4.new_code_cell(f"pd.read_csv('results/{table}.csv')"),
            nb.v4.new_code_cell(
                f"display(Image(filename='figures/{fig1}.png'))\ndisplay(Image(filename='figures/{fig2}.png'))"
            ),
        ]
        if module == "second_shots":
            book.cells += [
                nb.v4.new_markdown_cell(
                    "## Coverage and review queue\nConfirm the analysis window before using the rates."
                ),
                nb.v4.new_code_cell(
                    "display(pd.read_csv('results/second_shot_coverage.csv'))\ndisplay(pd.read_csv('results/second_shot_film_queue.csv').head(9))"
                ),
            ]
        elif module == "three_point_defense":
            book.cells += [
                nb.v4.new_markdown_cell(
                    "## Inspect all candidate settings and the requested teams"
                ),
                nb.v4.new_code_cell(
                    "display(pd.read_csv('results/defense_tuning.csv').head(8))\nteams = pd.read_csv('results/defense_teams.csv')\nteams[teams.team.isin(['PHX', 'SAS', 'NOP'])]"
                ),
                nb.v4.new_code_cell("pd.read_csv('results/defense_monitoring.csv')"),
            ]
        else:
            book.cells += [
                nb.v4.new_markdown_cell(
                    "## Recalculate an individual forecast\nCompare the posterior formula with the exported value."
                ),
                nb.v4.new_code_cell(
                    "players = pd.read_csv('results/shooter_forecasts.csv')\nr = players.loc[players.player.eq('Collin Gillespie')].iloc[0]\nrecalculated = r.alpha / (r.alpha + r.beta)\nassert abs(recalculated - r.posterior_mean) < 1e-12\nr[['player', 'early_attempts', 'early_rate', 'prior_forecast', 'posterior_mean', 'low90', 'high90', 'later_attempts', 'later_rate']]"
                ),
                nb.v4.new_code_cell("pd.read_csv('results/shooter_tuning.csv')"),
            ]
        book.cells += [
            nb.v4.new_markdown_cell(
                "## Interpretation and limits\nRead the complete accompanying article for denominators, uncertainty, model selection, and the basketball decisions this analysis cannot identify. The results here are historical research, not a claim of team deployment."
            )
        ]
        path = ROOT / f"notebooks/{stem}.ipynb"
        NotebookClient(
            book,
            timeout=600,
            kernel_name="research",
            resources={"metadata": {"path": str(ROOT)}},
        ).execute()
        for cell in book.cells:
            cell.metadata.pop("execution", None)
        nb.write(book, path)
        print(path.name, "executed", flush=True)


if __name__ == "__main__":
    run()
