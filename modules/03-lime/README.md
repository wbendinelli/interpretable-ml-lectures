# Module 03 — LIME

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/03-lime/notebooks/lime_walkthrough.ipynb)

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

Four results, each measured in `lime_internals.ipynb` rather than asserted. One restates a published theorem and checks it against this run; one is a limitation the literature names and this module quantifies; one is our own measurement of direction against level; and the last is a claim of ours that **did not survive replication**, kept here for that reason.

- **A local fit's direction is trustworthy; its level is not.** For this patient the fit's gradient points 4° from the direction the model's probability actually changes (cosine 0.997 in the plotted plane) — but g(x) = 0.50 against the model's f(x) = 0.58, a *stable bias*, σ ≈ 0.003 across runs. Drawing the conventional P=0.5 contour would place this patient on the malignant side of her own explanation in 5 of 8 runs, so the figures draw the fit **through the patient** instead. Across all 30 features the direction is only moderately aligned (cosine 0.57 for the committed run, 0.60 averaged over eight), so the ranking of the smaller coefficients deserves much less confidence than the leading one.

- **LIME's proximity kernel is nearly inert at the default width — which is where the level bias comes from.** This is a published result, not one of ours: Garreau and von Luxburg (2020) prove that at a wide bandwidth the kernel is "equivalent to give weight 1 to every perturbed sample". What this module contributes is the verification. Refitting with the kernel weights deleted entirely moves g(x) by a median 0.002 across six patients spanning the confidence range (up to 0.013 for the most confident of them), leaves every selected feature in place, and leaves the coefficient direction aligned at cosine 0.9999; the half-weight contour sits at 4.84σ, so 42% of all 569 real patients carry a weight above 0.5. Repeating the deletion across four datasets and three model classes (§11b), the selected features survive 92–100% of the time — with one honest qualification the single-dataset version hides: because ν = 0.75√p grows with the number of features, inertness is dimension-dependent, and in a four-feature control the kernel does bite. With the default ν = 0.75√p the "local" fit is very nearly a *global* linear approximation of f over the perturbation cloud, and a global fit explaining a third of the variance shrinks its predictions toward that cloud's mean of ≈0.48 — which is why g(x) lands near 0.5 almost regardless of which patient is being explained. Worth stating plainly: the wide default is deliberate, because a narrow bandwidth drives every coefficient to zero. It is a design trade-off, not a defect.

- **LIME's neighborhood is not made of possible patients.** Molnar lists sampling that ignores feature correlation among LIME's limitations; this module measures what it costs here. Drawing each feature independently from its own marginal breaks the correlations that make a tumour measurable: about three quarters of the synthetic patients carry at least one negative measurement, and the perimeter-to-radius ratio — 6.22–7.67 in real data — spans roughly 1.8 to 21.5 in the cloud. The consequence is not only cosmetic. Because those perturbations are detectable as out-of-distribution, Slack et al. (2020) were able to build a classifier that behaves differently on them and so hides its racial bias from LIME.

- **R² does not measure explanation quality — and our attempt to say what it *does* measure failed.** On this dataset with this model, R² tracks how *confident* the prediction was (Spearman ρ = +0.612, p ≈ 4×10⁻¹⁶ over 143 test patients). Two candidate mechanisms were tested and both are measurably false: the model essentially never saturates where LIME samples (2 of 5,000 draws, against 71% of held-out real patients), and the kernel weights are nearly uniform for everyone. Replication then removed the finding itself. Under one common protocol (55 patients, 2,000 samples), the correlation is +0.70 for our setting, weakens to +0.27 and +0.17 (n.s.) when the model is swapped for a gradient boosting machine and a logistic regression, and vanishes at **−0.07 (n.s.)** on an unrelated dataset (wine). The literature offers no rescue either: Velmurugan et al. (2020) evaluate LIME and SHAP fidelity across three process-mining datasets — with a perturbation-based measure rather than LIME's own R² — and report "no pattern or trend of faithfulness with regards to … the initial probability", with one of their settings running the other way entirely. So the honest statement is not "R² measures confidence" — it is that **you cannot know in advance what R² is correlated with in your own setting**, which is a stronger reason for the practical rule, not a weaker one: **do not rank explanations by R².**

## Lecture

- **[`lecture/slides.pdf`](lecture/slides.pdf)** — the 20-slide deck as delivered, in three acts: *build* the method at face value, *break* three things it taught, *rebuild* what survives. It opens directly on the method; the motivation in the outline's §1 is spoken, not projected.
- **[`lecture/outline.md`](lecture/outline.md)** — the outline the deck is built from: what to say, what to point at in each figure, and the objections to be ready for.

## Notebooks

- **`notebooks/lime_walkthrough.ipynb`** — the lecture. Builds the six steps, shows what LIME actually returns (the coefficient chart), and measures direction, level, and fidelity.
- **`notebooks/lime_internals.ipynb`** — the technical companion, which proves what the lecture asserts. It reproduces the package's perturbation, kernel and `highest_weights` selection from scratch and checks them against the installed source (`lime_tabular.py`, `lime_base.py`) — including the detail that the local model is fitted in *standardized* space, a trap that silently changes the selected features (8/8 agreement done right, 5/8 done wrong). It also runs the instance search, measures the off-manifold sampling and the R²-versus-confidence relationship, and quantifies instability. Its sweep fits one explanation per test patient (143 × 5,000 samples), so a full run takes a few minutes.

Committed figures are in `figures/`; running the notebooks regenerates them into `notebooks/figures_generated/` (git-ignored), so the canonical figures never change silently.

## A note on configuration

The notebooks pass `discretize_continuous=False`, overriding the package default. With the default, LIME bins each feature into quartiles and phrases explanations as intervals ("`worst perimeter` > 120") — the form used in Molnar's book and most tutorials. Turning it off keeps features continuous, which is what allows the explanation to be drawn as a line. Same algorithm, different presentation; worth knowing before comparing these outputs to others.

## References

- Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). ["Why Should I Trust You?": Explaining the Predictions of Any Classifier](https://arxiv.org/abs/1602.04938). *KDD 2016*. (The original LIME paper.)
- Molnar, C. *Interpretable Machine Learning* — [LIME chapter](https://christophm.github.io/interpretable-ml-book/lime.html). (Course reference book. Of the limitations he lists, three are measured here: neighborhood definition, sampling that ignores feature correlation, and instability across runs.)
- Garreau, D., & von Luxburg, U. (2020). [Explaining the Explainer: A First Theoretical Analysis of LIME](https://proceedings.mlr.press/v108/garreau20a.html). *AISTATS 2020*. (The bandwidth result verified above; see also *Looking Deeper into Tabular LIME*, 2020.)
- Slack, D., Hilgard, S., Jia, E., Singh, S., & Lakkaraju, H. (2020). [Fooling LIME and SHAP: Adversarial Attacks on Post hoc Explanation Methods](https://dl.acm.org/doi/10.1145/3375627.3375830). *AIES 2020*. (What off-manifold sampling costs, taken to its conclusion.)
- Velmurugan, M., Ouyang, C., Moreira, C., & Sindhgatta, R. (2020). [Evaluating Explainable Methods for Predictive Process Analytics: A Functionally-Grounded Approach](https://arxiv.org/abs/2012.04218). (Finds no consistent relationship between explanation fidelity and prediction probability, and one setting where it runs opposite to ours — part of why the finding above is presented as withdrawn. Note their fidelity measure is a perturbation MAPE, not LIME's R²; the same authors' CAiSE 2021 paper, [*Evaluating Fidelity of Explainable Methods for Predictive Process Analytics*](https://doi.org/10.1007/978-3-030-79108-7_8), extends this line.)
- Alvarez-Melis, D., & Jaakkola, T. (2018). [On the Robustness of Interpretability Methods](https://arxiv.org/abs/1806.08049). (Instability across runs.)
- [`marcotcr/lime`](https://github.com/marcotcr/lime) — the reference implementation validated in `lime_internals.ipynb`.
- Street, W. N., Wolberg, W. H., & Mangasarian, O. L. (1993). Nuclear feature extraction for breast tumor diagnosis. *IS&T/SPIE 1905*. (The [Breast Cancer Wisconsin (Diagnostic)](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic) dataset, as distributed with scikit-learn.)
