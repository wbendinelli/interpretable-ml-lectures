# Lecture Outline — LIME

Approximately 50 minutes. Figures referenced by their file names in `../figures/`.

**Learning objectives.** By the end, students should be able to state what LIME
optimizes and name each term; follow the mechanism end to end; read a local fit
off a plot and say what its R² does and does not tell them; and name two
structural limitations visible in the figures themselves.

---

## 1. Motivation — global accuracy hides the hard cases (~8 min)

The RandomForest reaches 95.1% test accuracy and 0.993 ROC-AUC. Then split the
143 test patients by how confident the prediction was:

| Group | Definition | Share | Accuracy |
|---|---|---|---|
| Confident | P outside [0.2, 0.8] | 127 / 143 (89%) | 99.2% |
| Borderline | P within [0.35, 0.65] | 6 / 143 (4%) | 66.7% |

The headline number is carried almost entirely by the easy cases. The 4% where
the model hesitates are exactly the patients a clinician would ask about — and,
as the lecture will show, the ones where explanations are hardest to trust.

*Discussion prompt:* if you had to report one number to a hospital board, which
would it be, and what would it hide?

## 2. The objective, term by term (~10 min)

$$\xi(x) = \operatorname*{arg\,min}_{g \in G} \; \mathcal{L}(f, g, \pi_x) + \Omega(g)$$

- **f** — the black box: the 300-tree RandomForest.
- **g** — the interpretable surrogate from a family *G*: a Ridge regression.
- **π_x** — the proximity kernel weighting each perturbed sample:
  $\pi_x(z) = \sqrt{\exp(-d(x,z)^2/\nu^2)}$, with $\nu = 0.75\sqrt{30}$ and
  $d$ computed on the 30 standardized features.
- **𝓛** — weighted squared error: how unfaithful *g* is to *f*, locally.
- **Ω(g)** — the complexity penalty; here, concretely, only the 8
  highest-weight features of 30 enter the surrogate.

Emphasize that *g* never overrides *f*. It summarizes it. The prediction under
discussion always comes from the forest.

## 3. The six steps (~15 min)

One figure per step, all in the same fixed window (`lime_step_1..6.png`;
`lime_walkthrough_combined.png` shows all six together).

| Step | Shows | Answers |
|---|---|---|
| 1 · black-box model | the real decision surface | what did the model learn? |
| 2 · local neighborhood | the region we will explain within | where, exactly, are we explaining? |
| 3 · perturbation | synthetic neighbors | what data does LIME actually use? |
| 4 · predictions | the forest's score on each neighbor | how does *f* behave around here? |
| 5 · proximity weighting | π_x as dot size | which neighbors count most? |
| 6 · local fit | the Ridge line | what is the simplest local story? |

Two things to point at explicitly:

- **Step 1.** The boundary is a staircase, not a smooth curve — a forest splits
  one feature at a time. Our patient (#67, P = 0.581, correctly predicted
  benign) sits right on it.
- **Step 6.** The straight line meets the staircase at the patient and departs
  from it further out, and their *slopes differ*: the forest is deciding this
  case mostly on `worst perimeter` alone, while the linear fit spreads credit
  across both axes because it cannot bend. That single picture contains both
  the idea and its price.

## 4. How much of this should we believe? (~10 min)

Separate two numbers that students routinely conflate:

- the **prediction**, always from the forest (P = 0.581);
- the **fidelity** R² ≈ 0.36, which says how well the straight-line summary
  tracks the forest across the weighted neighborhood.

Then the counter-intuitive result, and the heart of the lecture. Across all 143
patients, R² tracks *confidence*, not insight — Spearman ρ = +0.57
(p ≈ 8×10⁻¹⁴):

| Group | Mean R² |
|---|---|
| Borderline (\|P−0.5\| < 0.15) | 0.45 |
| Confident (\|P−0.5\| > 0.3) | 0.60 |

The mechanism is mechanical: far from the boundary the model is saturated, and
a straight line reproduces "almost constant" beautifully. The highest-R²
patient in this dataset scores **0.86** — with a fit whose decision line lies
**7.2σ** away from her. It is an excellent explanation of a region where
nothing is happening.

*Takeaway to state plainly:* a high R² can certify vacuity. Read it together
with the geometry, never alone.

Finish with the extrapolation demo: push the strongest feature far enough and
the linear fit predicts a negative probability. The surrogate is licensed only
near the point.

## 5. When not to trust it (~7 min)

Molnar, on what fidelity means:

> "The learned model should be a good approximation of the machine learning
> model predictions locally, but it does not have to be a good global
> approximation. This kind of accuracy is also called local fidelity."

> "The fidelity measure ... gives us a good idea of how reliable the
> interpretable model is in explaining the black box predictions in the
> neighborhood of the data instance of interest."

Two limitations he singles out, both measured in `lime_internals.ipynb` and
both visible in our own figures:

1. **Neighborhood choice** — unresolved, and we simply used the package
   default. The median neighbor sits several σ away yet still carries about a
   third of the maximum weight, so "local" spans a large slice of the space.
2. **Instability** — every call resamples, so the feature set wobbles across
   runs (7/8 shared here) even while the leading feature holds.

Worth adding, because it is visible in step 3: LIME perturbs each feature
independently, breaking real correlations and generating patients that could
not exist. Mild here (r = 0.35 between our axes), severe for a pair like
`worst area` / `worst perimeter` (r = 0.98).

**Closing line:** LIME's value is not that it is never wrong — it is that it
tells you, case by case, how much to trust it.
