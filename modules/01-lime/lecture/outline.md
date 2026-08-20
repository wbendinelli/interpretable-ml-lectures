# Lecture Outline — LIME

Approximately 50 minutes. Figures referenced by file name in `../figures/`.

**Learning objectives.** By the end, students should be able to state what LIME
optimizes and name each term; follow the mechanism end to end; say which parts
of a local explanation are trustworthy and cite the measurement that separates
them; and explain why LIME's neighborhood is not made of plausible patients.

---

## 1. Motivation — global accuracy hides the hard cases (~7 min)

Ten-fold cross-validation over all 569 patients: 95.3% accuracy, ROC-AUC 0.989.
Then split by how confident each prediction was:

| Group | Definition | n | Accuracy |
|---|---|---|---|
| Confident | \|P − 0.5\| > 0.30 | 492 (86%) | 99.4% |
| Borderline | \|P − 0.5\| < 0.15 | 34 (6%) | 52.9% |

Where the model is sure it is essentially never wrong; where it hesitates it is
a coin flip. The headline number hides precisely the patients who need a second
opinion.

*Use CV here, not a single split.* On one 143-patient test split the borderline
group has six patients and a 95% CI of 22%–96% — too thin to carry an argument,
and a student who checks will notice.

*Discussion prompt:* which number would you report to a hospital board, and
what would it conceal?

## 2. The objective, term by term (~9 min)

$$\xi(x) = \operatorname*{arg\,min}_{g \in G} \; \mathcal{L}(f, g, \pi_x) + \Omega(g)$$

- **f** — the black box: the 300-tree RandomForest.
- **g** — the interpretable surrogate: a Ridge regression.
- **π_x** — the proximity kernel,
  $\pi_x(z) = \sqrt{\exp(-d(x,z)^2/\nu^2)}$ with $\nu = 0.75\sqrt{30}$,
  distances on the standardized features. Note $\sqrt{\exp(-d^2/\nu^2)}
  = \exp(-d^2/2\nu^2)$: a Gaussian of standard deviation exactly ν.
- **𝓛** — weighted squared error: how unfaithful *g* is to *f*, locally.
- **Ω(g)** — complexity, and it is two things here: only 8 of 30 features are
  kept, and those carry an L2 penalty (Ridge, α = 1).

State plainly that *g* never overrides *f*. The prediction always comes from
the forest; the surrogate only summarizes it.

Flag the configuration choice: we pass `discretize_continuous=False`. The
package default bins features into quartiles and phrases explanations as
intervals — the form in Molnar's figures. Ours stays continuous so the
explanation can be drawn as a line. Students who run LIME with defaults will
see something different and should know why.

## 3. The six steps (~14 min)

`lime_step_1..6.png`; `lime_walkthrough_combined.png` shows all six.
Circles are real patients coloured by true diagnosis; squares are synthetic
neighbors coloured by the model's prediction.

| Step | Shows | Answers |
|---|---|---|
| 1 · black-box model | the decision surface in this slice | what did the model learn? |
| 2 · neighborhood | the scale of "near" | where are we explaining? |
| 3 · perturbation | synthetic neighbors | what data does LIME use? |
| 4 · predictions | *f* on each neighbor | how does the model behave there? |
| 5 · weighting | π_x as square size | which neighbors count? |
| 6 · local fit | the Ridge line | what is the simplest local story? |

Three things to point at, none of them decorative:

- **Step 1.** The boundary is a staircase — a forest splits one feature at a
  time. Patient #67 sits on it. Say that its exact position is seed-dependent
  (0.06σ–0.48σ across 12 forest seeds); do not read precision into it.
- **Step 3.** The squares are not plausible patients. About three quarters of
  them carry a negative measurement, and the perimeter-to-radius ratio, ≈2π in
  any real shape, spans roughly 1.8–21.5. This is the method working as
  designed, and it matters again in §4.
- **Step 4.** The squares do *not* separate along the dashed boundary (68%
  agreement against a 53% baseline). They cannot: each has random values on the
  other 28 features while the contour freezes those at #67's. This is the
  picture of why a 2-D slice cannot decide a 30-D prediction.

## 4. What to trust: direction yes, level no (~12 min)

The core of the lecture. A linear fit offers a **direction** (coefficient
ratios) and a **level** (the intercept). They are not equally reliable, and the
difference is measurable.

- **Direction.** The fit's gradient points within a few degrees of the
  direction the model's probability actually changes (cosine 0.997 in the
  plotted plane, stable to ±1.4° across runs). Across all 30 features it is
  only moderately aligned (cosine ≈ 0.60) — so trust the leading coefficient
  far more than the tail of the ranking.
- **Level.** g(x) = 0.499 ± 0.003 while f(x) = 0.581. That is a *bias*, not
  noise: the intercept is pulled toward the mean prediction of the huge
  off-manifold cloud. Drawing the conventional P = 0.5 contour would place this
  patient on the malignant side of her own explanation, in 5 of 8 runs. That is
  why the figures draw the fit **through the patient** instead.

Then show `lime_step_6b_coefficients.png` — the bar chart is what the library
returns and what practitioners read. Every coefficient is negative here: all
eight selected measurements push toward malignant, and the model still says
benign. The remaining 22 features and the forest's nonlinearity carry the
verdict, and a local linear summary structurally cannot show that.

Close with extrapolation: push the top feature far enough and the fit predicts
a negative probability.

## 5. The R² trap, and an honest loose end (~8 min)

It is tempting to read R² as explanation quality. Across 143 patients it
instead tracks *confidence*: Spearman ρ = +0.61 (p ≈ 4×10⁻¹⁶), mean R² 0.47
borderline versus 0.61 confident.

The intuitive explanation — "the model saturates far from the boundary, so a
line fits easily" — is false, and showing why is the best part of this section:

1. The model never saturates anywhere LIME samples: 0% of the synthetic cloud
   is beyond [0.05, 0.95], against 74% of real patients. The cloud is
   off-manifold (§3), so it never reaches the region where the model is sure.
2. The weighted variance of *f* is identical for borderline and confident
   patients (0.0228 vs 0.0227) — they share one cloud, because
   `sample_around_instance=False` centres it on the dataset, not the patient.
3. The algebra runs the other way: R² = 1 − SSE/SST, so a flatter target
   *shrinks* SST and makes high R² harder.

The natural replacement — that distant patients get more concentrated kernel
weights — also fails: the effective sample size is ~93% of nominal, so weights
are near-uniform for everyone.

**So the correlation is robust and we cannot say why.** Present that as the
result. A PhD audience should see that a measured regularity with a falsified
mechanism is a legitimate finding, and that reporting it beats inventing a
tidy story. The practical rule is unaffected: do not rank explanations by R².

Then Molnar, on what fidelity is for:

> "The learned model should be a good approximation of the machine learning
> model predictions locally, but it does not have to be a good global
> approximation. This kind of accuracy is also called local fidelity."

> "The fidelity measure ... gives us a good idea of how reliable the
> interpretable model is in explaining the black box predictions in the
> neighborhood of the data instance of interest."

Of the limitations he lists, three were measured today: the arbitrary
neighborhood (§2 — and the kernel barely localizes), sampling that ignores
feature correlation (§3), and instability across runs (7/8 features shared
between redraws).

**Closing line:** LIME's value is not that it is never wrong — it is that,
once you measure it, you can say precisely how it is wrong. That is the
difference between an explanation and a reassurance.
