# Module 01 — LIME

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/01-lime/notebooks/lime_walkthrough.ipynb)

This module walks through a real case study of Local Interpretable Model-agnostic Explanations (LIME) applied to a RandomForest classifier trained on scikit-learn's Breast Cancer Wisconsin (Diagnostic) dataset (569 patients, 30 features, benign/malignant classification).

![The six steps of LIME](figures/lime_walkthrough_combined.png)

## Learning objectives

After working through this module you should be able to:

1. State what LIME optimizes, and name each term of its objective.
2. Follow the mechanism end to end: perturb → predict → weight → fit.
3. Read a local fit off a plot, and say what its R² does and does *not* tell you.
4. Name two structural limitations of the method that are visible in the figures themselves.

## What this module shows

The walkthrough builds a LIME explanation from the ground up, in six steps, all plotted in the same fixed window so that nothing moves between steps except what LIME adds:

1. The black-box model — the decision surface of the RandomForest.
2. The local neighborhood — the region around the instance being explained.
3. Perturbation — synthetic samples generated around that instance.
4. Model predictions on the neighbors — how the black box scores each perturbed sample.
5. Proximity weighting — how neighbors are weighted by distance to the instance.
6. The local fit — a Ridge regression fit on the weighted neighbors.

**The case:** test patient #67, P(benign) = 0.581, predicted and truly benign, visualized against `worst perimeter` and `worst texture`. She was picked by a systematic search (documented in the internals notebook) requiring that the model classify her correctly, that she sit *near the decision boundary*, and that the two plotted features not be near-duplicates of each other. Exactly one of the 143 test patients satisfies all three. The result is a figure where the real boundary passes 0.08σ from her and the local fit passes 0.04σ — close enough that you can see the straight line standing in for the curved boundary, which is the entire idea of the method.

**The main lesson, which is not the obvious one.** It is tempting to read local fidelity (R²) as an explanation-quality score. Measured across all 143 patients, R² instead tracks how *confident* the prediction is (Spearman ρ = +0.57, p ≈ 8×10⁻¹⁴; mean R² 0.45 for borderline patients versus 0.60 for confident ones). Far from the boundary the model is saturated, and a straight line reproduces "almost constant" very easily. The highest-R² patient in this dataset scores 0.86 — with a local fit whose decision line sits 7.2σ away from her, explaining a region where nothing happens. Our patient's more modest R² ≈ 0.36 is the honest price of standing where an explanation is actually worth having.

## Notebooks

- **`notebooks/lime_walkthrough.ipynb`** — the lecture notebook. Builds the six steps above, discusses how much to trust the local linear fit, and closes with a section on when the explanation is not reliable.
- **`notebooks/lime_internals.ipynb`** — the technical companion, which proves what the lecture asserts. It reproduces the package's perturbation, kernel, and `highest_weights` selection from scratch and checks them against the installed source (`lime_tabular.py`, `lime_base.py`) — including the detail that the local model is fitted in *standardized* space, not raw units, a trap that silently changes the selected features (the notebook shows both versions: 8/8 agreement done right, 5/8 done wrong). It also runs the instance search, measures the R²-versus-confidence relationship above, and quantifies explanation instability across redraws. Its two sweeps call `explain_instance` once per test patient (143 × 5,000 samples), so a full run takes a few minutes.

The committed figures live in `figures/`; running the notebooks regenerates them into `notebooks/figures_generated/` (git-ignored), so the canonical figures never change silently.

## Caveats made explicit

Two limitations are visible in these very figures rather than tucked into a footnote:

- **Off-manifold perturbation.** LIME samples each feature independently, which destroys the correlations in real data and produces synthetic patients that could not exist. The two axes used here correlate at only r = 0.35, so the distortion is mild — but the pair `worst area` / `worst perimeter` correlates at 0.98, and choosing it would have put nearly the whole perturbation cloud off-manifold.
- **Neighborhood width and instability.** The default kernel is wide: the median neighbor sits several σ away and still carries about a third of the maximum weight, so "local" spans a large slice of the data space. And because every call draws a fresh sample, the selected feature set wobbles across runs (7/8 shared, in the committed run) even though the leading feature and the direction of its effect hold steady. Both are limitations Molnar singles out; the internals notebook measures them.

## References

- Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). ["Why Should I Trust You?": Explaining the Predictions of Any Classifier](https://arxiv.org/abs/1602.04938). *KDD 2016*. (The original LIME paper.)
- Molnar, C. *Interpretable Machine Learning* — [LIME chapter](https://christophm.github.io/interpretable-ml-book/lime.html). (Course reference book.)
- [`marcotcr/lime`](https://github.com/marcotcr/lime) — the reference implementation validated in `lime_internals.ipynb`.
- Street, W. N., Wolberg, W. H., & Mangasarian, O. L. (1993). Nuclear feature extraction for breast tumor diagnosis. *IS&T/SPIE 1905*. (The [Breast Cancer Wisconsin (Diagnostic)](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic) dataset, as distributed with scikit-learn.)
