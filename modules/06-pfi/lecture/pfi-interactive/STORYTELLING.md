# PFI lesson — teaching sequence

The lesson follows Raschka’s conceptual sequence and uses
[Molnar’s PFI chapter](https://christophm.github.io/interpretable-ml-book/feature-importance.html)
for interpretation. The adapted HTML, real teaching-record animations and empirical
SRAG figures are distinguished from the linked original lecture.

## Presentation flow

| Route | Purpose |
|---|---|
| `cover` | Introduce the question: how much does this predictor rely on an input? |
| `61` | Locate PFI in the feature-selection context, distinguishing an importance measure from subset search. |
| `62` | Animate separate Age and low-oxygen shuffles on real teaching records; compare probabilities and Brier for those records, then distinguish the full-test result. Restore original inputs before the next column. |
| `63` | Read the real SRAG ranking, loss difference, loss ratio and shuffle SD. |
| `65` | Distinguish explaining the fixed predictor from fitting candidate feature subsets. |
| `66` | Summarize Bronze/Silver/Gold, admissible inputs and explicit Unknown categories. |
| `66-selection` | Explain temporal fitting, recorded validation selection and the fixed reference XGBoost. |
| `67` | Receive an already fitted predictor. |
| `68` | Calculate original Brier against observed outcomes. |
| `69` | Copy original evaluation inputs and show the recorded Age swap on the same teaching rows; other inputs and observed outcomes stay fixed. |
| `70` | Inspect a recorded full-test Age shuffle, evaluated by the same predictor. |
| `71` | Follow the explicit repeat loop, recorded dataset-level errors and running mean/sample SD. |
| `73` | Explain strengths and interpretation limits using Molnar. |
| `dependence-results` | Contrast individual, joint and subgroup shuffles in a single empirical example. |
| `thanks` | Close with a question about interpreting reliance. |

The browser uses a single white surface, common typographic hierarchy and
compact navigation at the lower right. Narrow screens flow vertically rather than shrinking a
desktop canvas into unreadable text. Motion reveals the explanation in place;
reduced-motion preferences show completed views. No original-image mode,
video toolbar or appendix remains. Old direct hashes map to current screens.

## Separate the teaching subset from global evaluation

The table contains recorded real SRAG teaching rows, their observed outcomes
and probabilities before and after each shown swap. The adjacent comparison
uses the Brier of these same rows. Their outcome-based selection serves the
explanation; it does not estimate prevalence or predictive performance in
the complete test. No row was selected for its prediction or correctness.

The full-test reading is shown separately, using the complete temporal
evaluation and repeated permutations. A single swap in the teaching subset
can reduce its Brier while the mean full-test error increases. These are
different evaluations. The browser replays the recorded probabilities and
calculates the displayed subset loss from them; it does not execute XGBoost.

Age is in decimal years. Low oxygen is categorical. A donor with the same
category can leave a recipient’s value and prediction unchanged. The original
and permuted predictions stay beside the same observed outcome, making the
comparison visible. Classification marks use the stated teaching threshold;
Brier uses probabilities continuously.

The selected input changes; the predictor and outcomes stay fixed. Each repeat
copies the original matrix. The Age trace and ranking use the same original
loss and the same full-precision final summary. The displayed decimal precision
does not alter calculations. Code emphasis follows shuffle, prediction and
error registration; a trace point appears when that result is registered.
The repeat count is a protocol choice, not proof of Monte Carlo convergence.

The [walkthrough](../../notebooks/pfi_walkthrough.ipynb) and
[internals](../../notebooks/pfi_internals.ipynb) provide module evidence.
The [exporter](../../../../tools/srag_72_pfi_presentation.py) checks the
separate aggregate and teaching-record projections against the recorded
scientific source. The
[method sheet](method.html) records the study’s temporal and loss conventions.

## One final dependence example

The default joint option moves heart disease and diabetes from the same donor
row. Their observed pairs stay intact; relationships with other inputs can
still break. This is a complementary diagnostic, not Molnar’s subgroup method.

The subgroup option follows Molnar: separate records by the related input,
shuffle heart disease within each diabetes category, retain the fitted model,
and compare with each group’s original loss. The combined summary weights
group errors by group size. This restriction uses diabetes alone; it is not
full conditional PFI given every other input. The selector changes the
operation, procedure and numerical reading together.

Joint versus summed individual importance does not prove interaction or
redundancy. The quantities answer different questions. Unknown states are
explicit missing-information categories, not clinical negatives. Shuffle SD
is conditional on the fitted predictor and observed evaluation data, not a
population interval. The inspected historical test makes this explanation
exploratory. PFI establishes neither causality nor an effect’s direction.

## Figure and source origins

The PFI notebook in module 00 generated the ranking/equations in its mechanism
section, checked the recorded repeat trace in its cross-slide audit and
generated the dependence graph in its diagnostic section. The exported SVGs
preserve that scientific geometry. This module validates the presentation
projection and owns the teaching sequence; module 00 remains the dataset and
recorded experimental provenance.

- [Molnar’s subgroup example](https://christophm.github.io/interpretable-ml-book/feature-importance.html#group-wise-pfi-example).
- [scikit-learn: permutation algorithm](https://scikit-learn.org/stable/modules/permutation_importance.html).
- [Source provenance](fontes/provenance.json).
