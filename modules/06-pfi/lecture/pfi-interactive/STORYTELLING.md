# PFI lesson — teaching sequence

The lesson follows Raschka’s conceptual sequence and uses
[Molnar’s PFI chapter](https://christophm.github.io/interpretable-ml-book/feature-importance.html)
for interpretation. The adapted HTML, schematic row diagrams and empirical
SRAG figures are distinguished from the linked original lecture.

## Presentation flow

| Route | Purpose |
|---|---|
| `cover` | Introduce the question: how much does this predictor rely on an input? |
| `61` | Locate PFI in the feature-selection context, distinguishing an importance measure from subset search. |
| `62` | Animate separate Age and low-oxygen shuffles on symbolic rows; restore original symbols before the next input. Show measured full-test errors alongside, with their separate scope stated. |
| `63` | Read the real SRAG ranking, loss difference, loss ratio and shuffle SD. |
| `65` | Distinguish explaining the fixed predictor from fitting candidate feature subsets. |
| `66` | Summarize Bronze/Silver/Gold, admissible inputs and explicit Unknown categories. |
| `66-selection` | Explain temporal fitting, recorded validation selection and the fixed reference XGBoost. |
| `67` | Receive an already fitted predictor. |
| `68` | Calculate original Brier against observed outcomes. |
| `69` | Copy original evaluation inputs and move only the selected column; symbolic target/other-column values stay fixed. |
| `70` | Inspect a recorded full-test Age shuffle, evaluated by the same predictor. |
| `71` | Follow the explicit repeat loop, recorded dataset-level errors and running mean/sample SD. |
| `73` | Explain strengths and interpretation limits using Molnar. |
| `dependence-results` | Contrast individual, joint and subgroup shuffles in a single empirical example. |
| `thanks` | Close with a question about interpreting reliance. |

The browser uses a single white surface, common typographic hierarchy and
bottom navigation. Narrow screens flow vertically rather than shrinking a
desktop canvas into unreadable text. Motion reveals the explanation in place;
reduced-motion preferences show completed views. No original-image mode,
video toolbar or appendix remains. Old direct hashes map to current screens.

## Keep symbolic and empirical scopes clear

The symbolic positions show how a column exchange works. They contain no
patient attributes, outcomes, probabilities, classifications or subset error.
The loss bars beside them come from the complete temporal evaluation, recorded
before this animation was built. The Brier explanation uses its equation and
measured aggregate errors. It does not pretend to calculate error from symbols.

The selected input changes; the predictor and outcomes stay fixed. Each repeat
copies the original matrix. The Age trace and ranking use the same original
loss and the same full-precision final summary. The displayed decimal precision
does not alter calculations. Code emphasis follows shuffle, prediction and
error registration; a trace point appears when that result is registered.
The repeat count is a protocol choice, not proof of Monte Carlo convergence.

The [walkthrough](../../notebooks/pfi_walkthrough.ipynb) and
[internals](../../notebooks/pfi_internals.ipynb) provide module evidence.
The [exporter](../../../../tools/srag_72_pfi_presentation.py) checks the
presentation against the recorded scientific source. The
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
