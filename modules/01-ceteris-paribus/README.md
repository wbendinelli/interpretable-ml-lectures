# Module 01 — Ceteris paribus

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/01-ceteris-paribus/notebooks/cp_walkthrough.ipynb)

A worked case study of ceteris paribus profiles — Molnar, *Interpretable Machine Learning*, chapter 12 — on the same RandomForest, the same split and the same patient as module 03, so the course reads as one continuous case.

![Ceteris paribus profiles for the six features the forest leans on most](figures/cp_top_features.png)

## Learning objectives

After working through this module you should be able to:

1. Compute a ceteris paribus profile and say exactly which rows it feeds to the model.
2. Explain why a RandomForest profile is a staircase, and why a step's height is a property of the grid rather than of the model.
3. Measure how much of a profile is made of instances that could not exist, and state the criterion you used.
4. Say why a distance-based out-of-distribution check does not detect that, and what does.

## Why bother with the simplest method in the course

A ceteris paribus profile needs no surrogate, no sampling scheme and no kernel. Hold everything about one patient fixed, move one measurement across a grid, plot the prediction. Nothing is approximated: the curve is the model's own output, computed and not sketched.

That makes it the honest place to introduce the one problem every later method inherits. Freezing 29 measurements while the thirtieth moves builds patients that could not be biopsied — and because the method is otherwise so simple, there is nowhere for the problem to hide.

## What this module shows

Four steps, all on the same patient and the same feature:

1. The profile itself — a staircase, and where its steps fall.
2. How many of the plotted rows are geometrically impossible.
3. Why the general-purpose check for that fails.
4. Molnar's proposed remedy, applied and measured.

**The case.** Test patient #67, P(benign) = 0.581, and `worst perimeter`, the feature LIME ranks first for her in module 03. The sweep runs ±2.5σ around her value, clipped to the range the feature takes in the data. The partner feature that gets frozen — `worst radius` — is not chosen for convenience: it is the feature most correlated with the one being swept (|r| = 0.99), which is exactly the case Molnar warns about.

## What the module concludes, and how it is measured

Four results, each printed by the notebook that states it. Two are the chapter's own warnings, quantified here. One is a check that failed, kept for that reason. One is a bridge to module 03.

- **The staircase is real; its steps are not where you think.** Sweeping `worst perimeter` moves P(benign) by 0.212, in 6 steps larger than 0.01. The largest single step is 0.039 — but that number is an artefact of the grid: at 50 grid points it reads 0.048, at 800 it reads 0.015, because a finer grid cuts the same jump into more pieces. The swing is stable to three decimals at every resolution. Across 12 forest seeds the shape holds (swing 0.116 to 0.181) while the largest step wanders between perimeter 112.1 and 115.1. Quote the swing and the direction; never quote a threshold off one of these plots.

- **Most of the curve is a patient who cannot exist.** Across all 569 real patients the ratio `worst perimeter / worst radius` stays between 6.22 and 7.67 — it must, since the two measure the same object. With her radius frozen, the perimeter can only run 105.6 to 130.2, so **84% of the 200 plotted grid points are geometrically impossible**. Over the six features the forest leans on most the median is 53%; over all 30 it is 13%, rising to 46% for the 14 features that have a partner at |r| > 0.9. The stronger the correlation, the more of the curve is fiction — which is the mechanism, not an accident.

- **The obvious check for that does not work, and the reason generalises.** The natural test is distance: is the manufactured row further from the data than real patients are from each other? Real patients sit within 4.45σ of a nearest neighbour (95th percentile); the sweep never exceeds 2.50σ, so this test rejects **0%** of a curve that geometry rejects at 84%. It is not a bad implementation. Two real rows differ on all 30 coordinates and sit about √(2·30) ≈ 7.75σ apart, while a one-feature sweep moves a few σ no matter how absurd the row it lands on. **A ceteris paribus row is close to the data and impossible at the same time**, and only a constraint that knows something about the domain can see it.

- **The chapter's remedy is cheap here, which is a result about this feature.** Molnar suggests restricting the curve to a realistic interval. Doing that keeps 79% of the swing and the crossing of P = 0.5 survives, so the story does not change. The largest step also falls *inside* the possible range. That is the good case; the point of measuring is that you cannot know which case you are in without checking.

The technical companion adds the bridge: a two-point ceteris paribus slope **is** the finite difference module 03 uses to test LIME's direction. On this patient the signs of LIME's eight coefficients and the corresponding CP slopes agree 8 out of 8 — but the leading feature's slope reads −0.106 at ±1σ and −0.753 at ±0.1σ. Same feature, same patient, magnitudes seven times apart. That is module 03's finding restated: a coefficient hides the scale it was measured at, and a profile shows it.

## Lecture

- **[`lecture/outline.md`](lecture/outline.md)** — the outline the lecture is built from: what to say, what to point at in each figure, and the objections to be ready for.

## Notebooks

- **`notebooks/cp_walkthrough.ipynb`** — the lecture. Builds the profile, measures the impossible fraction two ways, and tests the chapter's remedy.
- **`notebooks/cp_internals.ipynb`** — the technical companion. Checks whether the grid decides the answer, repeats the impossible-fraction measurement over all 30 features, derives why the distance test fails, and connects a CP slope to a LIME coefficient. It refits the forest 12 times, so a full run takes a couple of minutes.

Committed figures are in `figures/`; running the notebooks regenerates them into `notebooks/figures_generated/` (git-ignored), so the canonical figures never change silently.

## A note on configuration

A ceteris paribus plot has two parameters that are almost never reported: how far the sweep goes, and how many points it uses. This module uses ±2.5σ and 200 points, and §2 of the companion shows what each one changes — the resolution changes step heights and nothing else, while the span changes how much of the curve is fiction. Both should be stated whenever one of these plots is shown.

## References

- Molnar, C. *Interpretable Machine Learning* — [Ceteris Paribus chapter](https://christophm.github.io/interpretable-ml-book/ceteris-paribus.html). (Course reference book, chapter 12. The definition used here, the correlation warning, and the range-restriction remedy tested above.)
- Biecek, P., & Burzykowski, T. *Explanatory Model Analysis*. [ema.drwhy.ai](https://ema.drwhy.ai/). (Where the term "ceteris paribus profile" comes from, and the ecosystem that treats it as a building block.)
- Friedman, J. H. (2001). Greedy Function Approximation: A Gradient Boosting Machine. *Annals of Statistics* 29(5), 1189–1232. [doi:10.1214/aos/1013203451](https://doi.org/10.1214/aos/1013203451). (Partial dependence, the average these curves are later aggregated into — module 02.)
- Street, W. N., Wolberg, W. H., & Mangasarian, O. L. (1993). Nuclear feature extraction for breast tumor diagnosis. *IS&T/SPIE 1905*, 861–870. (The [Breast Cancer Wisconsin (Diagnostic)](https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic) dataset, as distributed with scikit-learn.)
