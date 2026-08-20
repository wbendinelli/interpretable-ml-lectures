# Interpretable ML — Lecture Materials

This repository contains lecture materials on machine learning interpretability, prepared by William Bendinelli (PhD student) for a graduate course at the Institute of Mathematics and Computer Sciences, University of São Paulo (ICMC-USP), Brazil, taught by Prof. Dr. André Ponce de Leon de Carvalho. The materials follow the structure and terminology of the course's reference book, Christoph Molnar's [*Interpretable Machine Learning*](https://christophm.github.io/interpretable-ml-book/), and use it as the primary citation for concepts and definitions.

![The six steps of LIME, on real data](modules/01-lime/figures/lime_walkthrough_combined.png)

## Modules

| Module | Topic |
|---|---|
| [01 — LIME](modules/01-lime/) | Local Interpretable Model-agnostic Explanations |

Each module is self-contained and includes its own notebooks, figures, and lecture outline. Future modules (SHAP, PDP, ICE, and others) will be added under `modules/` following the same layout.

## Getting started

**Run in Colab.** The simplest way to explore a module is to open its notebook directly in Google Colab, using the badge at the top of the module's README. No local setup is required.

**Run locally.** To run the notebooks on your own machine:

```bash
pip install -r requirements.txt
jupyter notebook
```

Then open the notebook(s) inside the module of interest (e.g. `modules/01-lime/notebooks/`).

## Reproducibility

Every notebook fixes its random seeds (`random_state=42` throughout) and states its data splits explicitly. The committed figures and printed numbers were generated with Python 3.12, `scikit-learn` 1.9.0, `lime` 0.2.0.1, `numpy` 2.4.6, and `matplotlib` 3.11.1; other versions may shift sampling-sensitive results slightly (the notebooks say where, and by how much, that matters).

## Citing

If you use this material, please cite it via the metadata in [`CITATION.cff`](CITATION.cff) (GitHub renders a "Cite this repository" button from it).

## References

- Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). ["Why Should I Trust You?": Explaining the Predictions of Any Classifier](https://arxiv.org/abs/1602.04938). *KDD 2016*.
- Molnar, C. *Interpretable Machine Learning: A Guide for Making Black Box Models Explainable*. [christophm.github.io/interpretable-ml-book](https://christophm.github.io/interpretable-ml-book/).
- The [`lime`](https://github.com/marcotcr/lime) reference implementation by Marco Tulio Ribeiro.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.
