# PFI lesson — teaching sequence

The opening map follows selected categories from
[Molnar’s methods overview](https://christophm.github.io/interpretable-ml-book/overview.html).
[His PFI chapter](https://christophm.github.io/interpretable-ml-book/feature-importance.html)
guides the method and interpretation. Raschka inspires the visual sequence of
the following examples. The adapted HTML, real teaching-record animations and empirical
SRAG figures are distinguished from the linked original lecture.

## Presentation flow

| Route | Purpose |
|---|---|
| `cover` | Introduce the topic, guiding question, speaker and course. |
| `61` | Locate PFI through selected Molnar categories: post-hoc, model-agnostic, global, feature importance. Distinguish this context from the algorithm’s steps or automatic feature selection. |
| `62` | Show fixed real receivers within the first full-test Age or low-oxygen permutation. Compare their predictions and read the global original error, repeated mean and shuffle SD. Restore original inputs before the next column. |
| `63` | Read the real SRAG ranking, loss difference, loss ratio and shuffle SD. |
| `65` | Pair three supported ranking conclusions with their limits: predictive performance versus causality, loss magnitude versus effect direction, and near-zero importance versus scientific relevance or automatic removal. Use a shared icon and a short topic label for each pair, assertive wording for the supported result and quoted examples of unsupported claims. Keep the explanations in the Portuguese guide. |
| `66` | Summarize Bronze/Silver/Gold, admissible inputs and explicit Unknown categories. |
| `66-selection` | Explain temporal fitting, recorded validation selection and the fixed reference XGBoost. |
| `67` | Receive an already fitted predictor. |
| `68` | Calculate original log loss against observed outcomes. |
| `69` | Copy the full evaluation matrix and show its first registered Age permutation through the fixed receiver window; other inputs and outcomes stay fixed. |
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

## Locating the method

The opening route is Interpretability → Post-hoc → Model-agnostic → Global →
Feature importance → PFI. These labels describe the kind of explanation, not
successive algorithm operations. It is a didactic selection from Molnar’s
categories, not a reproduction of every branch in the book. Global describes
a summary over the evaluation data, not a universal statement or an individual
prediction. PFI measures a fitted model’s reliance under the stated shuffle and
loss; it does not automatically remove or select inputs. The source is
[the overview manuscript](https://github.com/christophM/interpretable-ml-book/blob/master/manuscript/overview.qmd),
with the operation defined in the PFI chapter.

## A visible window into the global experiment

The table shows the original real SRAG receivers and their predictions after
the first registered permutation of the full temporal test. Donor values come
from the entire evaluation, including rows outside the visible window.
The selected receivers stay fixed when the feature changes.

The adjacent error chart is global: original log loss, mean permuted log loss and
sample shuffle SD across the recorded repetitions. The first repetition is
identified separately; it is not the mean. Receiver losses are retained in
the notebook audit, rather than used as the presentation’s error estimate.
This outcome-selected window illustrates transport and prediction, not
population prevalence or performance. A receiver can improve while the
global error increases.

Age uses decimal years. Low oxygen is categorical, with Unknown explicit.
Original values are observed; shuffled records are artificial combinations
of real input values. A received age is not the recipient’s new observed age.
A category can land on the same value and leave the prediction unchanged.
Classification marks use the teaching cutoff; log loss measures probability
error continuously.

Each repeat starts from the original full matrix. The predictor and outcomes
stay fixed. The Age trace and ranking share the original global loss and
full-precision final summary. Code emphasis follows shuffle, prediction and
error registration; a trace point appears when the error is registered.
Repeat count is a protocol choice, not proof of Monte Carlo convergence.

## One code example across the walkthrough

The code sequence receives a trained predictor and the original evaluation
inputs and outcomes from the recorded study. Imports come first, the
baseline is calculated next, and reproducible row orders are created before
the shuffle loop. The evaluation excerpt continues that same loop; its
indentation is meaningful. The final screen follows all recorded repeats
and calculates the mean loss increase and sample SD after the loop.

`feature` selects the column to shuffle, not the inputs supplied to the
predictor. Every prediction still receives the full input matrix. This is
a worked example for one selected feature, not an outer loop over the whole
ranking or a standalone program that acquires data and trains a model.
The Portuguese guide names the required inputs, explains class ordering and
row alignment, and connects each excerpt to the next one. For a different
feature, start again from the original evaluation matrix.

The model-results view separates the new family comparison selected by
validation log loss from the within-XGBoost balancing search. Their
aggregate sources are validated independently; historical AUC selection
remains in the study record and speaking guide. The inspected temporal
test remains exploratory and does not choose the family winner.

The [walkthrough](../../notebooks/pfi_walkthrough.ipynb) generates the
[teaching evidence](../../evidence/pfi_teaching_demo.json) with
[srag_73_teaching_demo](../../../../tools/srag_73_teaching_demo.py).
The [internals](../../notebooks/pfi_internals.ipynb) independently reconstructs
the predictor, transports the full-test inputs and checks the first global
errors. The [exporter](../../../../tools/srag_72_pfi_presentation.py) validates
the separate teaching and aggregate projections. The old manual subset
shuffle remains in the module 00 record to document the correction; its
values do not describe the current animation.

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

The module 06 walkthrough generates the current log-loss equations, ranking,
repeat trace and dependence figures. The historical global experiment remains
recorded in module 00; the metric comparison and generated receiver window
are independently checked in module 06. This module validates the presentation
projection and owns the teaching sequence and its generated receiver window;
module 00 remains the dataset and global experimental provenance.

- [Molnar’s subgroup example](https://christophm.github.io/interpretable-ml-book/feature-importance.html#group-wise-pfi-example).
- [scikit-learn: permutation algorithm](https://scikit-learn.org/stable/modules/permutation_importance.html).
- [Source provenance](fontes/provenance.json).
