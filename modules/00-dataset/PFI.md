# SRAG permutation importance — technical sheet

This sheet preserves the recorded experiment and its historical teaching
demonstration with real processed records. The current method module is
[06 — PFI](../06-pfi/README.md). Its distributable browser lesson uses aggregate
SRAG results and a separately scoped real-record demonstration, reproduced
from this evidence in the module 06 walkthrough.
Raschka guides the conceptual sequence and Molnar guides the interpretation.

The current animation displays the same receiver records from the first
full-test permutation. The manual teaching swap documented below is retained
as historical evidence; it is not the current animation protocol.

[Open the current interactive lesson](../06-pfi/lecture/pfi-interactive/index.html#slide-63) ·
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

## Historical demonstration: why it used a selected subset

The historical study animation preserves the original **eight real adult records**, labelled A
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

The current lesson lives in [module 06](../06-pfi/lecture/pfi-interactive/README.md).
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

The original pages are linked in the source provenance rather than redistributed
in the current runtime. There is no visible “View original” control. The
adaptation, original source and SRAG evidence are identified separately. The
repository version uses the bundled Inter fonts with their existing OFL licenses.

## Cross-slide audit and the teaching sequence

The freshly executed evidence notebook §11 reproduces every recorded Age
permutation using the [executable walkthrough](../../tools/srag_pfi_walkthrough.py).
The maximum absolute discrepancy is **0**, and the global summaries shared by
the mechanism, ranking and code slides agree before rounding (§11).

A single repeat has its own result. Every per-repeat error, cumulative mean and cumulative SD displayed by the code
animation is printed in §11. Its visible loop declares and generates the recorded
orders; copying/shuffling, prediction and error registration are highlighted in
sequence. The slider and next-repeat controls permit one-at-a-time inspection.
The repeat count is a protocol choice, not a universal PFI requirement.

The first full-test Age shuffle has a Brier
of **0.1536** and an increase of **0.0228**, whereas the mean over all repeats
is **0.1543**, with a mean increase of **0.0234** (§11). The code slides label
these scopes explicitly and finish at the same mean and SD as the ranking.

The outcome-selected preview is also distinct: its original Brier is **0.3196**
and its Brier after the illustrated Age shuffle is **0.3174** (§11). This small
subset improves slightly under that particular shuffle. This does not contradict
the full-test increase across repeated shuffles. These historical preview
values and their scope remain in the evidence notebook §11; the current
browser mechanism uses symbols and does not display subset performance.

[Teaching notes](../06-pfi/lecture/pfi-interactive/STORYTELLING.md) map the adapted slides
to Raschka's original sequence. Molnar, the course book, guides its interpretation;
references and presenter notes remain outside the projected content. The main lesson now summarizes the actual data
pipeline, input treatment, temporal selection and final fitted XGBoost before
the code in two compact screens. The final presentation omits impurity, OOB and column removal. No measured SRAG
MDI comparison or column-drop study is claimed.

## Data provenance and model-selection screens

Notebook §13 reads and prints the committed Gold counts, selection results and
reference-model settings. It distinguishes the **1,282,970**-record Gold cohort
from the **200,000**-record uniform training sample, and prints the complete
validation and temporal-test sizes. The **six** candidate families were compared
under **73** declared search configurations. Highest validation AUC selected
XGBoost, without a technical tie. The **200** paired validation bootstrap
resamples belonged to the tie protocol, not to the PFI whiskers (§13).

The presentation shows the actual treatment of unknown categorical states and
native categorical XGBoost inputs. It identifies exclusions and preserves the
retrospective scope. Training ends before validation, and the selected predictor
is not refitted on validation. The separate balancing comparison did not replace
this reference. The historical test is already observed, so the later PFI and
dependence diagnostics are exploratory.

## Input association matrices before choosing a dependence example

The input-only diagnostic in [the ranking notebook](notebooks/srag_pfi_ranking.ipynb)
§16 examines the same historical temporal test used for PFI. It does not include
the outcome or predictions. Numeric inputs use separate Pearson and Spearman
matrices; categorical inputs and booleans use Cramér's V. These coefficients
describe different relationships and are not ranked together on a common scale.

The categorical sensitivity view excludes explicitly documented absence codes
for each pair and reports its retained record count. Structural states such as
Not applicable remain; False values already produced by Gold processing cannot
recover the original distinction between missing and negative declarations.
Comparing these views changes the evaluated records as well as the coding.
Undefined associations are marked unavailable, not replaced by zero. Numeric
versus categorical comparisons are outside these matrices. Pairwise associations
are exploratory diagnostics, not proof of independence, clinical redundancy,
causality or model reliance.

Notebook §17 records a reproducible display window for categorical shuffling:
heart disease changes while diabetes remains fixed. Both unrestricted and
subgroup donor orders operate on the full test and start from its original
inputs. Displaying only selected receivers does not preserve the full-test
contingency counts inside that window. The preview exports no identifiers,
outcomes or predictions; its notebook output records aggregate counts and
hashes. It illustrates the operation without adding a new performance result.

Notebook §18 compares alternative categorical examples on the full temporal
test. Its recorded distributions and donor flows support a local teaching
laboratory: fixed groups retain their records while an input's values are
redistributed. The original conditional category frequencies remain visible as
a reference. Unrestricted shuffling can change those frequencies; restricting
donors to the same observed group preserves the full pair table exactly.
This does not preserve every relation with the remaining inputs or imply that
predictions and loss are unchanged. The absence-code sensitivity describes
only the original association on a different subset; it is not a second
permutation experiment. Example choice considers field meaning, missingness
and visual clarity rather than maximizing an association coefficient. The
laboratory exports only aggregates and does not compute new PFI values.

Notebook §19 extends the exploratory candidate review with signed Pearson
correlations for clinically interpretable pairs. Recorded Yes/No fields use
one/zero coding, exclude other states separately for each pair and report the
retained and excluded record counts. For two binary inputs this is phi; its
absolute value is checked against uncorrected Cramér's V on the same binary
contingency table. Numeric/binary pairs use the equivalent point-biserial
correlation. Nominal categories are never assigned arbitrary ordinal codes.
The age/dose comparison also retains the adult sensitivity view. Dose counts
and the vaccination declaration carry their documented Gold-processing limits;
these record associations are not independent measures of vaccination coverage.
The output contains aggregates only, uses no outcome or prediction, and does
not select a lecture example automatically from the largest coefficient.

## Dependence: book-based subgroup approach and measured comparisons

The presentation uses one final dependence example. The association calculations
below remain part of its technical audit and are not separate lecture slides.
Notebook §14 uses the same real temporal test and fixed predictor. The categorical
heart-disease/diabetes contingency table gives **Cramér's V = 0.611** when unknown
states are retained. Restricting to records where both fields are Yes/No gives
**V = 0.247** on **7,762** records. **6,859** records have Unknown in both fields
(§14). This is nominal association, not Pearson correlation. The subsets differ;
the comparison is descriptive and does not isolate a clinical dependence or a
causal missingness effect.

The subgroup option of the final example follows Molnar's **subgroup approach**. Partition by
diabetes, shuffle heart disease within each category, predict with the fixed
model, compare against that subgroup's original Brier and repeat. Diabetes,
outcomes and all other inputs remain in their original rows. Every repeat begins
from the original evaluation matrix. The recorded group results are:

| Diabetes subgroup | Records | Mean extra Brier × 1,000 | Sample SD × 1,000 |
|---|---:|---:|---:|
| Unknown | 7,985 | 0.028 | 0.055 |
| No | 4,930 | 0.100 | 0.116 |
| Yes | 3,227 | 0.065 | 0.167 |

An additional overall summary weights each group's error by its record count.
The notebook verifies this equals full-test error in every repeat. This only
conditions the shuffle on diabetes; it does not sample heart disease conditional
on every other input. Dependencies with the remaining inputs can still break.

The same final screen compares that aggregate with marginal and joint diagnostics.
Joint shuffling uses the same row permutation for both columns and preserves
their observed pair distribution. It is shown as a complementary experiment,
not as Molnar's subgroup procedure. A selector displays the chosen shuffle
question, movement and steps alongside the graph. The measured results are:

| Shuffle question | Mean extra Brier × 1,000 | Sample SD × 1,000 |
|---|---:|---:|
| Heart disease alone | 0.367 | 0.050 |
| Diabetes alone | 0.423 | 0.071 |
| Both together | 0.940 | 0.098 |
| Heart disease within diabetes, aggregated | 0.057 | 0.060 |

These results use **50** repeats with seed **42**, the same original Brier and
full temporal test as the earlier ranking (§14). The figure's scale multiplies
Brier differences by **1,000** for readability; it does not change the metric.
The SD is shuffle dispersion conditional on this model and these records,
not a population interval or a significance test. The scores answer different
questions. Joint-versus-summed importance alone does not prove redundancy or
interaction, and the subgroup result is not a uniquely correct importance.

The notebook asserts that all nonselected columns, dtypes, targets and original
inputs remain unchanged, and checks preservation of the pair table for every
joint and subgroup repeat. New figure
[pfi-dependence.svg](figures/pfi-dependence.svg) is generated in §14; all
presentation values come from the exported evidence JSON.

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
