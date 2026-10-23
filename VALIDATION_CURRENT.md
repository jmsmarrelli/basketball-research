# Current validation — October 23, 2026

## Raw-source reproduction — October 23, 2026

The four manually downloaded source archives match every SHA-256 checksum and byte count in `data/source_manifest.json` at upstream commit `e829d4678be1e075f99e5d41a1c5f97089be446b`. They were restored locally without changing network permissions. Raw inputs and the derived SQLite database remain excluded from Git.

`python -m src.data fetch` verified and extracted all four local archives. `python -m src.data sql` rebuilt 657,388 shots and reconciled SQL totals. The rebuilt SQL results are byte-identical to the reviewed file. All eight research tests pass, including the two previously blocked source-dependent tests.

A separate reproduction copy ran `python -m src.run_all` successfully, refitting the three analyses and regenerating nine figures. All 17 result files and both model files are byte-identical to the reviewed originals. The full eight-test suite also passes against these freshly reproduced outputs. The reviewed checkout's results and charts were preserved.

This closes the missing-input and missing-SQL validation blockers recorded below. The run used the existing Python 3.14.7 environment; a fresh installation of the declared Python 3.12 environment, notebook re-execution, and browser desktop/mobile certification are still not claimed. Across the previously tested collection, the two formerly failing tests now pass, bringing the cumulative count to 139; other repositories were not rerun for this data-only restoration.

The draft pull request remains unmerged. No default branch, repository visibility, network setting, or deployment configuration was changed.

## Historical validation record

The October 22 entries below document the state before the source archives were restored; their missing-data failures are superseded by the successful October 23 reproduction above.

# Current validation — October 22, 2026

## Connected GitHub review — October 22, 2026

GitHub integration access is verified for `jmsmarrelli`, including repository push permission. The remote `main` commit matched the preserved local base before preparing this review. The completed overhaul is preserved on `feat/portfolio-review-2026-10-22`; publication uses the connected GitHub API because shell Git cannot resolve `github.com`. Original local commits remain intact; the API publication carries their complete final file tree in a review commit based on the verified remote main.

The owner authorizes feature branches and draft pull requests. Merging into `main` requires separate owner approval. Repository visibility, profile settings and Pages deployment configuration are unchanged. Cross-repository links target `main` for eventual publication; review the individual draft PRs until those changes are approved and merged. Merge the navigation hub after its linked study changes.

Fresh Python test rerun: **2 failed, 6 passed in 2.07s**. The two full-source failures are missing raw shot files and the absent `shots` SQL table; this is not a passing full reproduction. The rerun uses the existing Python 3.14 environment, not a fresh Python 3.12 install.

Flagship PNG/SVG exports were rebuilt from saved inputs in this continuation; numerical CSV/JSON inputs remained unchanged. This validates the presentation layer, not a new raw-data fit.

## What changed

Original issue: An outcome-leakage unit test required a missing large raw archive; automated checks were manual full-source only.

Implemented: Made the leakage check use an explicit synthetic unit fixture; marked the two archive-dependent tests; added a separate offline CI job; rebuilt nine figures and three HTML articles.

## Evidence and limits

6 Python tests passed. The full suite also has two failures from absent raw inputs/SQL; the explicit offline subset is 6 passed, 2 deselected. Full reproduction remains blocked.

Six checks pass; two full-source tests fail because raw shot files and rebuilt shots SQL are absent. Forecast models and notebooks were not rerun.

Test/runtime checks used an existing Python 3.14.7 environment (NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.1, scikit-learn 1.9.0, matplotlib 3.11.1, pytest 9.1.1). The older studies specify Python 3.12 and different NumPy/pandas pins. A fresh installation of that pinned environment was not possible offline and is a release gate. R execution used R 4.6.1 with an existing package library. Earlier validation files and executed notebooks describe earlier runs and were preserved; notebooks were not re-executed in this review.

HTML now uses the pinned CommonMark renderer `markdown-it-py==4.2.0` with tables; local and CI use the same renderer. This replaces an unavailable local Python-Markdown package. Generated result CSVs retain full precision; readable article tables round for display only. The seven-project Quarto collection uses its separate Pandoc fallback.

## Earlier local review and publication record

Changes are local to `audit/2026-10-22-portfolio`. No push, merge, repository visibility change or public release occurred. The local PR draft records the intended summary. Publication requires a reachable authenticated GitHub connection and the owner's approval. Read [PROVENANCE.md](PROVENANCE.md) before describing personal authorship or validation in an application.


## Earlier October 22 visual and publication follow-up

The flagship figure pipeline now exports an editorial PNG/SVG design from the same saved results; a new decision brief distinguishes evidence, proposed action and limitations. The five affected research repositories passed 102 tests in total in this follow-up (6 research offline, 15 Spurs research, 18 game management, 19 Western scouting, 44 NBA portfolio). The two raw-input research tests remain deselected, with their earlier failures documented. All 152 fingerprinted CSV/JSON/gzip inputs across those repositories remained byte-identical. Twelve flagship PNG/SVG exports were checked for deterministic regeneration. No additional model fit or data retrieval is implied.

The latest owner instruction authorizes feature branches and pull requests, but requires separate approval for any default-branch merge. Do not change repository visibility. The owner reports that GitHub is connected through ChatGPT; no GitHub repository or PR tools were exposed to this session when checked, so access and remote state remain unverified. Shell networking is still restricted. No further authentication attempt was made.
