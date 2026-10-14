# SRAG permutation importance — technical sheet

This is an exploratory explanation of the fixed course model. The interactive
lesson follows Raschka's conceptual sequence and uses Molnar's definitions;
its numerical results come from the SRAG study, rather than Raschka's wine example.

[Open the interactive lesson](lecture/pfi-interactive/index.html#slide-63) ·
[Executed evidence notebook](notebooks/srag_pfi_ranking.ipynb) ·
[Recorded permutation experiment](gold/pfi_ranking.json) ·
[Presentation data](gold/pfi_slide_explainer.json)

## Data, outcome and model

The source is the public SIVEP-Gripe data processed through the course's
Bronze → Silver → Gold pipeline. This experiment concerns the **hospitalized
COVID cohort with closed outcomes**, not every SRAG notification. The
[Gold decisions](GOLD.md), [manifest](gold/MANIFEST.md) and
[model card](MODEL.md) document cohort construction, leakage exclusions,
missing-value handling and model selection.

The target is death (`y_obito = 1`) versus survival (`y_obito = 0`). The reference
XGBoost uses **40 inputs** and a **200,000-record training sample**. Training
ends in **2022**, validation is **2023**, and the temporal test is **2024**.
The test contains **16,142 records**, including **2,945 deaths**
(evidence notebook §1 and §9; model notebook linked in the model card).
This reference uses neither class weights nor resampling. The separate
[class-balancing comparison](notebooks/srag_balance_comparison.ipynb) does not
replace it. Because this historical holdout has already been inspected, the
current explanation is exploratory; it is not a new untouched model-selection test.

Age is a derived input in **decimal years at symptom onset**: elapsed days
between birth and symptom onset, divided by **365.25** (evidence notebook §9;
implementation in [`srag_30_silver.py`](../../tools/srag_30_silver.py)). The
decimal part is a fraction of a year. Low oxygen uses the study's categorical
`saturacao` input. These are real **processed Gold values**, not untouched raw
notification fields.

## The measured experiment

The [experiment code](../../tools/srag_62_pfi.py) keeps the fitted model fixed,
computes the original Brier score, and permutes each input separately. Every
permutation starts from the original evaluation matrix. The records, outcomes
and all other input columns remain unchanged. There is no refitting after a
column shuffle.

There are **50 permutations per input**, with seed **42**. Each permutation
produces a score on the same full temporal test set. The displayed interval is
**mean ± one sample standard deviation**, using `ddof=1`. This describes
variation between shuffles conditional on the fitted model and evaluation
records. It is not a population confidence interval, nor variation caused by
training new models (evidence notebook §1, §3 and §9).

| Input | Original Brier | Permuted Brier, mean ± SD | Difference, mean ± SD | Ratio, mean ± SD |
|---|---:|---:|---:|---:|
| Age | 0.1308 | 0.1543 ± 0.0007 | 0.0234 ± 0.0007 | 1.179 ± 0.006 |
| Low oxygen | 0.1308 | 0.1351 ± 0.0003 | 0.0043 ± 0.0003 | 1.033 ± 0.003 |

All values above are rounded from the full-precision results printed in evidence
notebook §9. Calculations use full precision before display rounding. The slide ranking shows
the **ten** inputs with the largest mean Brier increase. Since the original
error is the same positive constant for every input, difference and ratio
produce the same order. Ratios below **1** are possible when shuffling reduces
error: **1** is a reference, not a lower bound. Their neutral values are **0** and **1**, respectively
(§9). A ratio of **1.179** means about **17.93% more Brier error**; it does
not mean a change in the mortality rate.

The Brier score averages the squared distance between the predicted probability
of death and the observed binary outcome. Lower is better. It evaluates
probabilities without a classification cutoff, and is not a pure calibration
statistic. The **0.50** cutoff in the animation is a teaching convention,
not a selected clinical decision threshold (§9).

## Why the animation uses a selected subset

The animation preserves the original **eight real adult records**, labelled A
through H. It selects the first **four** eligible adult records for each outcome
in the temporal test and restores original dataset order. Actual predictions
come from the reference model reconstructed from its recorded training protocol.
The reconstruction reproduces the original full-test Brier within the notebook's
asserted tolerance (§9).

This is an **outcome-selected teaching subset**, not a random performance sample.
It cannot estimate model performance, prevalence or a typical effect. Both the
original and age-permuted evaluations have **four** class errors at the displayed
cutoff (§9). Unchanged class counts do not imply unchanged probability errors.
A particular shuffle on a small subset can even reduce the Brier error. The
notebook prints these subset errors separately from the full-test results.

The animation starts with original predictions and an empty permuted column.
It shuffles age, evaluates the fixed model, then clears the permuted predictions
while restoring age. It next shuffles low oxygen starting from **all original
inputs**, evaluates, clears and restores again. The experiments never accumulate
column changes. Swapping identical categorical values can leave a record's
prediction unchanged; this is retained rather than replaced with invented motion.

Permuted combinations are experimental inputs; they are not claimed to be newly
observed real patients. The other model inputs are retained even though the
compact table does not display them all. The full-study importance graph uses
the entire temporal test set and repeated shuffles. **It is never computed from
the selected teaching subset.**

The probability-error explanation uses real record H from §9:

| Evaluation of H | Death probability | Observed outcome | Individual squared error |
|---|---:|---:|---:|
| Original | 0.4694 | 1 | 0.2816 |
| Age shuffled | 0.3686 | 1 | 0.3987 |

## Reproduction and source trace

Run the evidence notebook from a fresh kernel using the repository's pinned
Python environment and `requirements.lock`. It writes the generated charts,
LaTeX-rendered equation SVGs and presentation JSON under its temporary
`figures_generated/` directory, leaving the repository unchanged. Section §9
contains both the generating code and the printed checks. Promote outputs to
[`figures/`](figures/) and the presentation JSON to
[`gold/pfi_slide_explainer.json`](gold/pfi_slide_explainer.json) by explicit copy.

The portable lesson lives in [`lecture/pfi-interactive/`](lecture/pfi-interactive/).
Serve the repository root with a local HTTP server, then open the lesson's
`index.html`; its relative links resolve the committed data and figures.
The SVGs retain the scientific plot geometry. Motion reveals the existing
bars, numerical labels and then their SD whiskers in an automatic loop; it does
not invent intermediate measurements. Pointing at a row reveals its original
error, permuted mean and importance with SD.
Choosing a bar changes the numerical reading. Choosing a scale changes the
formula and axis. The difference starts at zero. The ratio also starts at zero,
with a reference line at one: these bars include the original error as well as
its relative increase. This avoids visually identical bars caused by showing
only the increment above one on an automatically rescaled axis. Reduced-motion settings show the completed chart immediately.

The original pages remain available with **View original**. They are attributed
to Sebastian Raschka and distributed with the accompanying source license.
The adaptation and SRAG evidence are identified separately. The repository
version uses the bundled Inter fonts with their existing OFL licenses.

## Cross-slide audit and the teaching sequence

The freshly executed evidence notebook §11 reproduces every recorded Age
permutation using the [executable walkthrough](../../tools/srag_pfi_walkthrough.py).
The maximum absolute discrepancy is **0**, and the global summaries shared by
the mechanism, ranking and code slides agree before rounding (§11).

A single repeat has its own result. The first full-test Age shuffle has a Brier
of **0.1536** and an increase of **0.0228**, whereas the mean over all repeats
is **0.1543**, with a mean increase of **0.0234** (§11). The code slides label
these scopes explicitly and finish at the same mean and SD as the ranking.

The outcome-selected preview is also distinct: its original Brier is **0.3196**
and its Brier after the illustrated Age shuffle is **0.3174** (§11). This small
subset improves slightly under that particular shuffle. This does not contradict
the full-test increase across repeated shuffles. The numerical-scope disclosure
is available in the mechanism slide.

[Teaching notes](lecture/pfi-interactive/STORYTELLING.md) map the adapted slides
to Raschka's original sequence. Each adapted slide links its interpretation to
Molnar, the course book. The conceptual MDI comparison introduces the meaning of
impurity before discussing similarities. It does not claim a measured SRAG
MDI comparison. The evaluation slide keeps the OOB connection optional, then
connects the algorithm to the actual temporal study.

## Interpretation limits and references

PFI measures how much this fitted model's predictive error changes when an
input's association with the remaining data is disrupted. It does not establish
a causal effect on death. Correlated inputs may yield implausible combinations;
interactions and redundant inputs affect the interpretation. A small PFI does
not prove a variable is irrelevant to the clinical phenomenon.

- [Molnar — Permutation Feature Importance](https://christophm.github.io/interpretable-ml-book/feature-importance.html): algorithm, difference, ratio and interpretation limits.
- [Raschka — feature-selection lecture](https://sebastianraschka.com/pdf/lecture-notes/stat451fs21/13_feat-sele__slides.pdf): original sequence and diagrams.
- [scikit-learn — Brier score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html): probability-error definition.
- [scikit-learn — permutation importance](https://scikit-learn.org/stable/modules/permutation_importance.html): fixed-model evaluation and repeated shuffles.
