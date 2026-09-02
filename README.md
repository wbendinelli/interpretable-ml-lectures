# Interpretable ML — Lecture Materials

[![CI](https://github.com/wbendinelli/interpretable-ml-lectures/actions/workflows/ci.yml/badge.svg)](https://github.com/wbendinelli/interpretable-ml-lectures/actions/workflows/ci.yml)
[![canary](https://github.com/wbendinelli/interpretable-ml-lectures/actions/workflows/canary.yml/badge.svg)](https://github.com/wbendinelli/interpretable-ml-lectures/actions/workflows/canary.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Lecture materials on machine learning interpretability, prepared by William Bendinelli for **SCC5819 — Topics in Artificial Intelligence**, a graduate course at the Institute of Mathematics and Computer Sciences, University of São Paulo (ICMC-USP), Brazil, taught by Prof. Dr. André Carlos Ponce de Leon Ferreira de Carvalho. The materials follow the structure and terminology of the course's reference book, Christoph Molnar's [*Interpretable Machine Learning*](https://christophm.github.io/interpretable-ml-book/).

Each module covers one method, on real data, with every claim measured rather than asserted.

## Modules

| Module | Topic | Status |
|---|---|---|
| [00 — Dataset](modules/00-dataset/) | The SRAG base: dictionary, quality assessment, Bronze→Silver treatment | available |
| [01 — Ceteris paribus](modules/01-ceteris-paribus/) | Changing one feature at a time | available |
| [02 — ICE](modules/02-ice/) | Individual conditional expectation curves | available |
| [03 — LIME](modules/03-lime/) | Local Interpretable Model-agnostic Explanations | available |
| [04 — Counterfactuals](modules/04-counterfactual/) | What would have to change — and what is actually within reach | available |
| [05 — SHAP](modules/05-shap/) | Shapley additive explanations, exact via TreeSHAP | available |

The full method plan — every applicable Molnar chapter mapped onto the SRAG
base, with the compute constraints and the order — is [ROADMAP.md](ROADMAP.md).

The numbering follows the order the methods are taught, from the simplest
intervention on a single feature to game-theoretic attribution — chapters 12,
13, 14, 15 and 18 of Molnar for modules 01–05. All five run on the SRAG/COVID
course model that module 00 establishes; the earlier Breast Cancer Wisconsin
versions of 01–03 live in the git history. The full chapter map is
[ROADMAP.md](ROADMAP.md).

Every module is self-contained: its own notebooks, figures, lecture outline, references, and README. Method-specific citations live in the module that uses them, not here. Modules 01–05 share one dataset, one model, one split and one patient — the committed SRAG/COVID sample, the XGBoost chosen by module 00's pre-registered selection study, the temporal split train ≤2022 / val 2023 / test 2024, and the rule-picked exemplar patient (|p − 0.5| minimal on the test split; see [`MODEL.md`](modules/00-dataset/MODEL.md)) — so the series reads as one continuous case. Every module refits that model from the committed sample, so "one model, one patient" is guaranteed by code, not by discipline.

Module 00 is the base: **SRAG / SIVEP-Gripe**, 4,109,567 notifications of severe acute respiratory syndrome across 2019–2024. It is not a method module — it is the dataset the later modules explain, treated once, with the treatment's evidence and its gaps both on the record, and the model those modules explain, chosen by protocol.

## Repository map

| Path | What it is |
|---|---|
| [`modules/`](modules/) | one module per method — notebooks, figures, lecture outline, README |
| [`modules/_template/`](modules/_template/) | the starting point for a new module |
| [`tools/`](tools/) | the SRAG pipeline scripts and the notebook checker — the table of what each reads and writes is [`tools/README.md`](tools/README.md) |
| [`requirements.txt`](requirements.txt) / [`requirements.lock`](requirements.lock) | the pinned stack — human-readable pins, and the full hash-locked resolution |
| [`CHANGELOG.md`](CHANGELOG.md) | repository-level changes, dated |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | the evidence bar, notebook conventions, how to add a module |
| [`CLAUDE.md`](CLAUDE.md) | operating manual for coding agents (and a fine crib sheet for humans) |

## How these materials are built

The same commitments apply to every module, and they are what the repository is for:

- **Real data and real models.** No toy illustrations standing in for the method. If a figure shows a decision boundary, it is the model's actual decision boundary, computed rather than sketched.
- **Every number is measured where it is stated.** Quantitative claims in a lecture are printed by the notebook that makes them, so a student can check any of them.
- **Each module pairs a lecture with a technical companion.** The lecture notebook teaches; a second notebook validates the implementation against the source code of the library being used, and measures the method's behavior independently of what its documentation promises.
- **Limitations are measured, including inconvenient ones.** Where a method's standard framing does not survive testing, the material says so and shows the measurement — even when that undercuts the tidier version of the lesson.

## Getting started

**In Colab.** The simplest route: open a module's notebook directly in Google Colab using the badge at the top of that module's README. No local setup — but know the trade-off: **Colab ignores `requirements.txt` entirely** and installs whatever the notebook's unpinned `%pip` cell resolves to that day, so sampling-sensitive third decimals may differ from the committed outputs. The conclusions hold; the bytes may not.

**Locally** (the route the committed numbers were produced on):

```bash
pip install -r requirements.txt          # the pins, human-readable
# or, for an exact environment down to every transitive dependency:
pip install --require-hashes -r requirements.lock
jupyter notebook
```

Then open the notebooks inside the module of interest (e.g. `modules/03-lime/notebooks/`).

## Reproducibility

Notebooks fix their random seeds (`random_state=42` throughout) and state their data splits explicitly. Committed figures and printed numbers were generated with Python 3.12 and the versions recorded in [`requirements.txt`](requirements.txt) — fully resolved, transitive dependencies included, with hashes in [`requirements.lock`](requirements.lock), which is what CI installs. Other versions may shift sampling-sensitive results, and the notebooks flag where that matters.

CI executes the walkthrough notebooks on that pinned stack on every pull request — the heavier `_internals` companions run when a PR touches them, and weekly otherwise — and checks that a run writes nothing into the repository tree. It deliberately does *not* diff outputs: BLAS and platform differences alone move third decimals between a Linux runner and the Apple Silicon machine the committed outputs came from. A weekly [canary](.github/workflows/canary.yml) runs the same notebooks on the newest Python and unpinned latest packages, so drift shows up as a failing scheduled job rather than as a surprise months later.

## Contributing

Corrections, replications and clarity edits are welcome. The habit that keeps the material checkable: if a change states a number, it also adds the notebook cell that prints it. [CONTRIBUTING.md](CONTRIBUTING.md) has the setup guide, the evidence bar and the module template.

## Citing

Cite via the metadata in [`CITATION.cff`](CITATION.cff) — GitHub renders a "Cite this repository" button from it.

## Reference

Molnar, C. *Interpretable Machine Learning: A Guide for Making Black Box Models Explainable*. [christophm.github.io/interpretable-ml-book](https://christophm.github.io/interpretable-ml-book/)

## License

MIT — see [LICENSE](LICENSE).
