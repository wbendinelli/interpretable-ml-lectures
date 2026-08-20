# Lecture Outline — LIME (DRAFT)

> This is a working draft and will be revised. Suggested timings are approximate and total roughly 50 minutes.

## 1. Motivation — why global accuracy hides the hard cases (~8 min)

- The RandomForest reaches 95.1% test accuracy and 0.993 ROC-AUC overall — a strong-looking model.
- But aggregate accuracy masks how unevenly reliable the model is across cases. Break the 143 test patients down by prediction confidence:

  | Group | Definition | Share of test set | Accuracy |
  |---|---|---|---|
  | Confident cases | P outside [0.2, 0.8] | 127 / 143 (89%) | 99.2% |
  | Boundary cases | P within [0.35, 0.65] | 6 / 143 (4%) | 66.7% |

- The model is nearly perfect where it is confident, and much weaker in the narrow band where it is not. This gap motivates the rest of the lecture: if we only report the 95.1% headline number, we hide exactly the cases where an explanation is most needed — and where it is hardest to trust.

## 2. The LIME equation, term by term (~10 min)

$$\xi(x) = \operatorname*{argmin}_{g \in G} \; L(f, g, \pi_x) + \Omega(g)$$

- **f** — the black box being explained: here, the RandomForest classifier.
- **g** — the interpretable surrogate model, drawn from a family **G** of interpretable models: here, a Ridge regression.
- **π_x** — the proximity kernel, weighting perturbed samples by distance to the instance x:

  $$\pi_x(z) = \sqrt{\exp\left(-\frac{d(x,z)^2}{\nu^2}\right)}, \qquad \nu = 0.75 \cdot \sqrt{30}$$

  Distance d(x, z) is computed on the 30 standardized features.
- **L(f, g, π_x)** — the loss measuring how well g approximates f, weighted by π_x: how unfaithful is the local surrogate to the black box, locally?
- **Ω(g)** — a complexity penalty on g, keeping the explanation interpretable. Here, concretely: only the 8 highest-weight features (of 30) enter the surrogate.
- **ξ(x)** — the explanation itself: the g that minimizes fidelity loss plus complexity, in the neighborhood of x.

## 3. The six steps, with figures (~15 min)

One line per step: what it shows, and what question it answers.

1. **The black-box model** — the RandomForest's decision surface. *What did the model learn overall?*
2. **The local neighborhood** — the region around the instance being explained. *Where, specifically, are we trying to explain the model?*
3. **Perturbation** — synthetic samples drawn around the instance. *What data does LIME actually use to build its explanation?*
4. **Model predictions on the neighbors** — the black box's scores on each perturbed sample. *How does f behave across this neighborhood?*
5. **Proximity weighting** — neighbors weighted by π_x. *Which perturbed samples matter most to the local fit?*
6. **The local fit (Ridge)** — a weighted linear model fit to the neighborhood. *What is the simplest local story that approximates f here?*

All six panels share the same fixed axis window, so the sequence reads as layers accumulating on one scene — nothing moves between steps except what LIME adds.

## 4. How much to trust this? (~10 min)

- The Ridge fit in step 6 is only as good as its local fidelity — the R² of the weighted local regression, not the RandomForest's own accuracy.
- Worked example: test patient #48, P(benign) = 0.253, predicted and truly malignant. The local explanation has R² = 0.65 against `worst area` (1218.0) and `worst perimeter` (128.2).
- A key caveat: because g is linear, it extrapolates. Far enough from the instance, the fitted line can imply a "negative probability" — a reminder that the explanation is a local, not global, description of f.
- Takeaway: point-level fidelity (how well g predicts f(x) at the instance itself) is not the same question as neighborhood R² (how well g tracks f across the whole weighted neighborhood). Both matter, and they can disagree.

## 5. When NOT to trust the explanation (~7 min)

- Counterexample: test patient #88, P(benign) = 0.497 — predicted malignant, but truly benign. The model itself is wrong here. Local fidelity drops to R² = 0.39.
- Patient #88 sits in a genuine class-overlap region: this is not a bug in LIME, it is LIME faithfully reporting that the black box has no clean local structure to explain at this point.
- Molnar, on what fidelity is supposed to mean:

  > "The learned model should be a good approximation of the machine learning model predictions locally...This kind of accuracy is also called local fidelity."

  > "The fidelity measure...gives us a good idea of how reliable the interpretable model is in explaining the black box predictions in the neighborhood of the data instance of interest."

- Limitations Molnar flags, and that the technical notebook (`lime_internals.ipynb`) demonstrates empirically: explanation **instability** across repeated runs, and the **choice of neighborhood** as an open, unresolved problem.

**Closing line:** LIME's value is not that it is never wrong — it is that it tells you, case by case, how much to trust it.
