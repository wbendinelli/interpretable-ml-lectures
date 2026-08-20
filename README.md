# Interpretable ML — Lecture Materials

Lecture materials on machine learning interpretability, prepared by William Bendinelli (PhD student) for **SCC5819 — Topics in Artificial Intelligence**, a graduate course at the Institute of Mathematics and Computer Sciences, University of São Paulo (ICMC-USP), Brazil, taught by Prof. Dr. André Carlos Ponce de Leon Ferreira de Carvalho. The materials follow the structure and terminology of the course's reference book, Christoph Molnar's [*Interpretable Machine Learning*](https://christophm.github.io/interpretable-ml-book/).

Each module covers one method, on real data, with every claim measured rather than asserted.

## Modules

| Module | Topic | Status |
|---|---|---|
| 01 — Ceteris paribus | Changing one feature at a time | planned |
| 02 — ICE | Individual conditional expectation curves | planned |
| [03 — LIME](modules/03-lime/) | Local Interpretable Model-agnostic Explanations | available |
| 04 — SHAP | Shapley additive explanations | planned |

The numbering follows the order the methods are taught, from the simplest
intervention on a single feature to game-theoretic attribution. Module 03 is
written first because it is the one being delivered first.

Every module is self-contained: its own notebooks, figures, lecture outline, references, and README. Method-specific citations live in the module that uses them, not here.

## How these materials are built

The same commitments apply to every module, and they are what the repository is for:

- **Real data and real models.** No toy illustrations standing in for the method. If a figure shows a decision boundary, it is the model's actual decision boundary, computed rather than sketched.
- **Every number is measured where it is stated.** Quantitative claims in a lecture are printed by the notebook that makes them, so a student can check any of them.
- **Each module pairs a lecture with a technical companion.** The lecture notebook teaches; a second notebook validates the implementation against the source code of the library being used, and measures the method's behavior independently of what its documentation promises.
- **Limitations are measured, including inconvenient ones.** Where a method's standard framing does not survive testing, the material says so and shows the measurement — even when that undercuts the tidier version of the lesson.

## Getting started

**In Colab.** The simplest route: open a module's notebook directly in Google Colab using the badge at the top of that module's README. No local setup.

**Locally.**

```bash
pip install -r requirements.txt
jupyter notebook
```

Then open the notebooks inside the module of interest (e.g. `modules/03-lime/notebooks/`).

## Reproducibility

Notebooks fix their random seeds (`random_state=42` throughout) and state their data splits explicitly. Committed figures and printed numbers were generated with Python 3.12 and the versions recorded in [`requirements.txt`](requirements.txt); other versions may shift sampling-sensitive results, and the notebooks flag where that matters.

## Citing

Cite via the metadata in [`CITATION.cff`](CITATION.cff) — GitHub renders a "Cite this repository" button from it.

## Reference

Molnar, C. *Interpretable Machine Learning: A Guide for Making Black Box Models Explainable*. [christophm.github.io/interpretable-ml-book](https://christophm.github.io/interpretable-ml-book/)

## License

MIT — see [LICENSE](LICENSE).
