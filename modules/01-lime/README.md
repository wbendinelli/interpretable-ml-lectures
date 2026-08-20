# Module 01 — LIME

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/01-lime/notebooks/lime_walkthrough.ipynb)

A worked case study of Local Interpretable Model-agnostic Explanations (LIME) on a RandomForest trained on scikit-learn's Breast Cancer Wisconsin (Diagnostic) dataset (569 patients, 30 features, benign/malignant).

![The six steps of LIME](figures/lime_walkthrough_combined.png)

## Learning objectives

After working through this module you should be able to:

1. State what LIME optimizes and name each term of its objective.
2. Follow the mechanism end to end: perturb → predict → weight → fit.
3. Say which parts of a local explanation are trustworthy (the direction) and which are not (the level), and cite the measurement that separates them.
4. Explain why the neighborhood LIME builds is not made of plausible patients, and what that costs.

## Why bother explaining this model

Under 10-fold cross-validation over all 569 patients the RandomForest reaches 95.3% accuracy — but that number is carried by the easy cases. Split by confidence: where the model is confident (|P − 0.5| > 0.30, n = 492) it is right **99.4%** of the time; where it hesitates (|P − 0.5| < 0.15, n = 34) it is right **52.9%** of the time, barely better than a coin flip. Those 6% of patients are the ones a clinician would take to a second opinion, and they are what this module is about.

## What this module shows

Six steps, all plotted in the same fixed window so nothing moves between them except what LIME adds:

1. The black-box model — the decision surface of the RandomForest.
2. The local neighborhood — the region around the instance being explained.
3. Perturbation — synthetic samples generated around that instance.
4. Model predictions on the neighbors — how the black box scores each one.
5. Proximity weighting — how neighbors are weighted by distance.
6. The local fit — a Ridge regression on the weighted neighbors.

**The case.** Test patient #67, P(benign) = 0.581, predicted and truly benign, plotted against `worst perimeter` and `worst texture`. She sits on the decision boundary, which is required rather than convenient: the distance from a patient to the fit's P=0.5 contour equals |g(x) − 0.5| ⁄ ‖w‖, so for a confidently classified patient that contour is *forced* far away and the figure degenerates. The two plotted axes are her rank-1 and rank-**3** features — across the dataset the rank-2 feature correlates with rank 1 at a median of 0.98, so a strict "top two" rule would collapse the real patients onto a near 1-D ribbon. Three other test patients meet the same conditions; #67 is used because her plottable second axis sits highest in the ranking. Both points are legibility choices, stated as such in the notebook, not properties of the data.

## What the module concludes, and how it is measured

Three results, each verified in `lime_internals.ipynb` rather than asserted:

- **A local fit's direction is trustworthy; its level is not.** For this patient the fit's gradient points within a few degrees of the direction the model's probability actually changes (cosine 0.997 in the plotted plane) — but g(x) = 0.50 against the model's f(x) = 0.58, a *stable bias* (σ ≈ 0.003 across runs), because the intercept is dragged toward the mean prediction of the perturbation cloud. Drawing the conventional P=0.5 contour would place this patient on the malignant side of her own explanation, so the figures draw the fit **through the patient** instead. Across all 30 features the direction is only moderately aligned (cosine ≈ 0.57), so the ranking of the smaller coefficients deserves much less confidence than the leading one.

- **LIME's neighborhood is not made of possible patients.** Sampling each feature independently breaks the correlations that make a tumour measurable: about three quarters of the synthetic patients carry at least one negative measurement, and the perimeter-to-radius ratio — necessarily ≈2π for any closed shape, and 6.22–7.67 in real data — spans roughly 1.8 to 21.5 in the cloud.

- **R² does not measure explanation quality.** Across the test set it tracks how *confident* the prediction was (Spearman ρ = +0.61, p ≈ 4×10⁻¹⁶; mean R² 0.47 for borderline patients against 0.61 for confident ones). The intuitive explanation — "the model saturates far from the boundary, so a line fits easily" — is measurably false: the model never saturates anywhere LIME samples (0% of the cloud, against 74% of real patients), the weighted variance of f is identical for borderline and confident patients because they share one cloud, and the algebra runs the other way anyway, since a flatter target shrinks SST and makes a high R² *harder*. The obvious replacement — that distant patients get more concentrated kernel weights — fails too: the effective sample size stays near 93% of nominal, so the weights are nearly uniform for everyone. The module reports the correlation as robust and the mechanism as **unresolved**, which is the honest state of it. The practical rule holds regardless: **do not rank explanations by R².**

## Notebooks

- **`notebooks/lime_walkthrough.ipynb`** — the lecture. Builds the six steps, shows what LIME actually returns (the coefficient chart), and measures direction, level, and fidelity.
- **`notebooks/lime_internals.ipynb`** — the technical companion, which proves what the lecture asserts. It reproduces the package's perturbation, kernel and `highest_weights` selection from scratch and checks them against the installed source (`lime_tabular.py`, `lime_base.py`) — including the detail that the local model is fitted in *standardized* space, a trap that silently changes the selected features (8/8 agreement done right, 5/8 done wrong). It also runs the instance search, measures the off-manifold sampling and the R²-versus-confidence relationship, and quantifies instability. Its sweep fits one explanation per test patient (143 × 5,000 samples), so a full run takes a few minutes.

Committed figures are in `figures/`; running the notebooks regenerates them into `notebooks/figures_generated/` (git-ignored), so the canonical figures never change silently.

## A note on configuration

The notebooks pass `discretize_continuous=False`, overriding the package default. With the default, LIME bins each feature into quartiles and phrases explanations as intervals ("`worst perimeter` > 120") — the form used in Molnar's book and most tutorials. Turning it off keeps features continuous, which is what allows the explanation to be drawn as a line. Same algorithm, different presentation; worth knowing before comparing these outputs to others.

## References

- Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). ["Why Should I Trust You?": Explaining the Predictions of Any Classifier](https://arxiv.org/abs/1602.04938). *KDD 2016*. (The original LIME paper.)
- Molnar, C. *Interpretable Machine Learning* — [LIME chapter](https://christophm.github.io/interpretable-ml-book/lime.html). (Course reference book. Of the limitations he lists, three are measured here: neighborhood definition, sampling that ignores feature correlation, and instability across runs.)
- [`marcotcr/lime`](https://github.com/marcotcr/lime) — the reference implementation validated in `lime_internals.ipynb`.
- Street, W. N., Wolberg, W. H., & Mangasarian, O. L. (1993). Nuclear feature extraction for breast tumor diagnosis. *IS&T/SPIE 1905*. (The [Breast Cancer Wisconsin (Diagnostic)](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic) dataset, as distributed with scikit-learn.)
