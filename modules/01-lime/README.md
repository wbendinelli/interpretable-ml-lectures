# Module 01 — LIME

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/01-lime/notebooks/lime_walkthrough.ipynb)

This module walks through a real case study of Local Interpretable Model-agnostic Explanations (LIME) applied to a RandomForest classifier trained on scikit-learn's Breast Cancer Wisconsin (Diagnostic) dataset (569 patients, 30 features, benign/malignant classification).

![The six steps of LIME](figures/lime_walkthrough_combined.png)

## What this module shows

The walkthrough builds a LIME explanation from the ground up, in six steps, all plotted on the same axis scale so they can be compared directly:

1. The black-box model — the decision surface of the RandomForest.
2. The local neighborhood — the region around the instance being explained.
3. Perturbation — synthetic samples generated around that instance.
4. Model predictions on the neighbors — how the black box scores each perturbed sample.
5. Proximity weighting — how neighbors are weighted by distance to the instance.
6. The local fit — a Ridge regression fit on the weighted neighbors.

The case study then asks how much that local fit can be trusted, and shows both sides of the answer:

- **A reliable case (test patient #48):** P(benign) = 0.253, predicted and truly malignant. Local fidelity R² = 0.65. The explanation is visualized against `worst area` (1218.0) and `worst perimeter` (128.2).
- **A counterexample (test patient #88):** P(benign) = 0.497, predicted malignant but truly benign — the model gets this one wrong. Local fidelity R² = 0.39. This patient sits in a genuine class-overlap region, and the module uses her as a worked example of when *not* to trust the explanation.

## Notebooks

- **`notebooks/lime_walkthrough.ipynb`** — the lecture notebook. Builds the six steps above, discusses how much to trust the local linear fit, and closes with a section on when the explanation is not reliable.
- **`notebooks/lime_internals.ipynb`** — a technical companion notebook. It validates, against the installed source code of the `lime` package (`lime_tabular.py`, `lime_base.py`), that the hand-reproduced perturbation, kernel, and `highest_weights` feature selection match what the package does internally — including the detail that the package fits the local model in standardized space, not raw units. It also documents the systematic search for the didactic instance used in the lecture notebook and demonstrates the instability of LIME explanations under resampling. Note: its instance search runs one explanation per test patient (143 × 5,000 samples), so a full run takes a few minutes.

The committed figures live in `figures/`; running the notebooks regenerates them into `notebooks/figures_generated/` (git-ignored), so the canonical figures never change silently.

LIME has known limitations — explanation instability across runs and sensitivity to the choice of neighborhood — both of which are demonstrated empirically in `notebooks/lime_internals.ipynb`.

## References

- Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). ["Why Should I Trust You?": Explaining the Predictions of Any Classifier](https://arxiv.org/abs/1602.04938). *KDD 2016*. (The original LIME paper.)
- Molnar, C. *Interpretable Machine Learning* — [LIME chapter](https://christophm.github.io/interpretable-ml-book/lime.html). (Course reference book.)
- [`marcotcr/lime`](https://github.com/marcotcr/lime) — the reference implementation validated in `lime_internals.ipynb`.
- Street, W. N., Wolberg, W. H., & Mangasarian, O. L. (1993). Nuclear feature extraction for breast tumor diagnosis. *IS&T/SPIE 1905*. (The [Breast Cancer Wisconsin (Diagnostic)](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic) dataset, as distributed with scikit-learn.)
