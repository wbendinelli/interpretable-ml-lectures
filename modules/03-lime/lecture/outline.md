# Lecture Outline — LIME

Figures referenced by file name in `../figures/`. Every number below is printed
by `lime_walkthrough.ipynb` or `lime_internals.ipynb`; markers like
`(internals §3)` point into the latter.

**Learning objectives.** By the end, students should be able to state what LIME
optimizes and name each term; follow the mechanism end to end; say which parts
of a local explanation are trustworthy and cite the measurement that separates
them; and explain why LIME's neighborhood is not made of plausible patients.

---

## 1. Motivation — global accuracy hides the hard cases

Ten-fold cross-validation over all 569 patients: 95.3% accuracy, ROC-AUC 0.989.
Then split by how confident each prediction was:

| Group | Definition | n | Accuracy |
|---|---|---|---|
| Confident | \|P − 0.5\| > 0.30 | 492 (86%) | 99.4% |
| Borderline | \|P − 0.5\| < 0.15 | 34 (6%) | 52.9% |

The bands leave a deliberate gap: the 43 patients (8%) in between are neither
clearly confident nor clearly borderline, and are left out so the contrast is
not blurred by where the definition happens to cut.

Where the model is sure it is essentially never wrong; where it hesitates it is
a coin flip. The headline number hides precisely the patients who need a second
opinion.

*Use CV here, not a single split.* On one 143-patient test split the borderline
group has six patients, four of them correct — an exact (Clopper–Pearson) 95%
interval of 22%–96%. Too thin to carry an argument, and a student who checks
will notice.

*Discussion prompt:* which number would you report to a hospital board, and
what would it conceal?

## 2. The objective, term by term

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

## 3. The case, and the six steps

**Say this before the first figure — it is the first thing anyone asks.** The
patient is test #67 and the axes are `worst perimeter` and `worst texture`.
Neither choice is arbitrary, and neither is a property of the data:

- **Why her.** She sits on the decision boundary. That is required, not
  convenient: the distance from a patient to the fit's P = 0.5 contour is
  |g(x) − 0.5| ⁄ ‖w‖, so a confidently classified patient has that contour
  *forced* far away and the figure degenerates into two unrelated lines. Three
  other test patients qualify equally well (internals §3) — she is not special.
- **Why these axes.** They are her rank-1 and rank-**3** LIME features. Rank 2
  is skipped because across the dataset the rank-2 feature correlates with
  rank 1 at a median of 0.98; plotting the top two would collapse the real
  patients onto a near 1-D ribbon with no structure to show.

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

What to point at, step by step:

- **Step 1.** The boundary is a staircase — a forest splits one feature at a
  time. Patient #67 sits on it. Its position is seed-dependent: refitting the
  forest under 12 seeds moves it between 0.06σ and 0.48σ from her, median
  0.29σ, with this notebook's seed at 0.08σ. Do not read precision into it.
- **Step 2.** The dashed ellipse is labelled "±1.2σ reference (not LIME's
  kernel)" — say why. LIME's real neighborhood is far wider than the frame: the
  median synthetic neighbor sits about 6σ away in 30-D and still carries about
  a third of the maximum weight, giving an effective sample size near 93% of
  the draws. Plant that number; §4 and §5 both cash it in.
- **Step 3.** The squares are not plausible patients. About three quarters
  carry a negative measurement, and the perimeter-to-radius ratio — necessarily
  ≈2π in any closed shape, and 6.22–7.67 in real data — spans roughly 1.8–21.5.
  This is the method working as designed, and it returns in §5.
- **Step 4.** The squares do *not* separate along the dashed boundary: 68%
  agreement against a 53% majority baseline. They cannot. Each has random
  values on the other 28 features, while the contour freezes those at #67's.
  This is the picture of why a 2-D slice cannot decide a 30-D prediction.
- **Step 5.** Size and opacity encode the weights. Point out that they vary
  less than students expect — the visual foreshadows the ESS ≈ 93% fact from
  Step 2, and §4 shows what follows from it.
- **Step 6.** The line passes *through* the patient rather than at P = 0.5. Do
  not gloss over that; it is the subject of §4.

## 4. What to trust: direction yes, level no

The core of the lecture. A linear fit offers a **direction** (the coefficient
ratios) and a **level** (the intercept). They are not equally reliable, and the
difference is measurable.

**Direction — good.** The fit's gradient points 4° from the direction in which
the model's probability actually changes; cosine 0.997 in the plotted plane,
stable to ±1.4° across runs. Across all 30 features it is only moderately
aligned — cosine 0.57 for the committed run, 0.60 averaged over eight — so
trust the leading coefficient far more than the tail of the ranking.

**Level — biased.** g(x) = 0.499 ± 0.003 while f(x) = 0.581. Derive this rather
than assert it. The chain is short, and it is the hardest moment in the lecture:

1. The kernel barely localizes (ESS ≈ 93%, from Step 2). Refitting with the
   weights **removed entirely** changes almost nothing: g(x) moves by about
   0.002 and the two coefficient vectors align at cosine 0.9999.
2. So the fit is effectively a *global* linear approximation of *f* over the
   perturbation cloud.
3. The cloud's mean prediction is ≈0.48, and the fit explains about a third of
   the variance. A poor fit necessarily shrinks its predictions toward the
   target mean — that is what a low R² *is*.
4. Therefore g(x) ≈ 0.5 for almost any patient. The intercept carries
   information about the cloud, not about her.

That is why the figures draw the fit through the patient. The conventional
P = 0.5 contour would place her on the malignant side of her own explanation,
in 5 of 8 runs.

**Anticipate these three — they will come.**

- *"If the kernel barely localizes, why is the direction local at all?"* It
  largely is not. It is a global gradient that happens to align well here. Say
  so. What survives is that a global linear fit can still recover a useful
  direction when *f* varies smoothly along the features that matter; locality
  is not what earns it.
- *"The plotted axes are her own top LIME features — isn't cosine 0.997
  circular?"* Partly, yes. That is why the 30-D figure (0.57) is reported
  beside it, and why the honest claim is about the leading coefficient rather
  than the whole ranking.
- *"Why not `sample_around_instance=True`?"* It would centre the cloud on her
  rather than on the dataset, which is arguably what "local" ought to mean. We
  use the package default so the material describes LIME as people actually
  run it. A good exam question, and an easy experiment to assign.

Then show `lime_step_6b_coefficients.png` — the bar chart is what the library
returns and what practitioners read. Every coefficient is negative here: all
eight selected measurements push toward malignant, and the model still says
benign. The remaining 22 features and the forest's nonlinearity carry the
verdict, and a local linear summary structurally cannot show that.

Close with extrapolation: push the top feature far enough and the fit predicts
a negative probability.

## 5. The R² trap, and an honest loose end

It is tempting to read R² as explanation quality. Across 143 patients it
instead tracks *confidence*: Spearman ρ = +0.61 (p ≈ 4×10⁻¹⁶), mean R² 0.47
borderline against 0.61 confident.

The intuitive explanation — "the model saturates far from the boundary, so a
line fits easily" — is false, and showing why is the best part of this section:

1. The model essentially never saturates where LIME samples: 2 of 5,000 draws
   fall outside [0.05, 0.95], against 71% of held-out real patients. The cloud
   is off-manifold (Step 3), so it never reaches the region where the model is
   sure.
2. The weighted variance of *f* is identical for borderline and confident
   patients (0.0228 vs 0.0227) — they share one cloud, because
   `sample_around_instance=False` centres it on the dataset, not the patient.
3. The algebra runs the other way: R² = 1 − SSE/SST, so a flatter target
   *shrinks* SST and makes a high R² harder.

The natural replacement — that distant patients get more concentrated kernel
weights — fails for the reason already established in §4: the weights are
near-uniform for everyone.

**So the correlation is robust and we cannot say why.** Present that as the
result. A PhD audience should see that a measured regularity with a falsified
mechanism is a legitimate finding, and that reporting it beats inventing a tidy
story. The practical rule is unaffected: do not rank explanations by R².

Then Molnar, on what fidelity is for:

> "The learned model should be a good approximation of the machine learning
> model predictions locally, but it does not have to be a good global
> approximation. This kind of accuracy is also called local fidelity."

> "The fidelity measure ... gives us a good idea of how reliable the
> interpretable model is in explaining the black box predictions in the
> neighborhood of the data instance of interest."

Of the limitations he lists, three were measured today: the arbitrary
neighborhood (Step 2 — and we found the kernel barely localizes at all),
sampling that ignores feature correlation (Step 3), and instability across runs
(7 of 8 features shared between redraws).

**Return to the board.** The opening question was which number to report. The
answer this lecture supports is not 95.3% alone, but 95.3% together with: on
the 6% of patients where the model hesitates it is right about half the time,
and here is a tool that tells you which patient you are looking at — along with
how much of what it says you should believe.

LIME's value is not that it is never wrong. It is that, once you measure it,
you can say precisely how it is wrong — and that is the difference between an
explanation and a reassurance.
