# PFI lesson — final teaching sequence

The lesson retains Raschka's conceptual sequence and the original source images.
[Molnar's chapter](https://christophm.github.io/interpretable-ml-book/feature-importance.html)
guides the interpretation. Numerical examples come from real processed SRAG
records and the fixed reference XGBoost. They do not reuse the original wine
example's illustrative accuracy values.

## The consolidated presentation

| Route | Purpose |
|---|---|
| `cover` | Introduce the predictive-reliance question, lecturer and course. |
| `61` | Locate PFI in the original dimensionality-reduction map. |
| `62` | Show separate Age and low-oxygen shuffles on the original real teaching records, restoring original inputs before each experiment. |
| `63` | Interpret the full-test ranking, difference, ratio and permutation SD. |
| `65` | Distinguish importance from a feature-selection study. |
| `66` | Summarize Bronze/Silver/Gold, cohort, admissible inputs and Unknown categories. |
| `66-selection` | Explain the temporal split, recorded model selection and fixed XGBoost before the code. |
| `67` | Receive an already fitted predictor. |
| `68` | Calculate original Brier with observed outcomes. |
| `69` | Copy original evaluation inputs and permute only the chosen column. |
| `70` | Predict with the same model and inspect a recorded full-test shuffle. |
| `71` | Display the explicit repeat loop and trace every recorded shuffle, running mean and sample SD. |
| `73` | Explain the strengths and interpretation limits using Molnar. |
| `dependence-results` | Use one heart-disease/diabetes example to compare individual, joint and subgroup shuffles; explain the chosen operation next to the real graph. |
| `thanks` | Close with a discussion question, source credit and acknowledgement. |

The original context, mechanism, ranking and selection comparison retain their
content. The data/model block is now compact and uses the same typography,
spacing and white surface as the rest. Additional preprocessing and selection
details remain in the technical sheet and presenter notes, hidden from the
projected view.

The browser view uses a single white canvas, consistent column grids and
bottom navigation. Type and figure sizes respond to both viewport width and
height. Supplementary reference links and source banners are hidden from the
stage; attribution stays on the closing screen. Narrow screens switch to a
scrolling reading layout.

There is no appendix in this presentation. The earlier impurity, OOB and
column-removal discussions are not in its navigation. Original source assets
are preserved for provenance. Old direct hashes redirect to a relevant current
screen rather than reopening removed material.

## A trace that explains the repetitions

The repeat screen defines the RNG, declares the recorded repeat count and shows
its `for` loop. Automatic code emphasis follows copying/shuffling, prediction
and appending the Brier result. A dot appears only after that result is recorded.
The slider, pause/replay and next-repeat controls support discussion of one
iteration. The completed mean and SD match the Age ranking before rounding.
The repeat count is a protocol choice, not a universal requirement or evidence
that Monte Carlo convergence has been established.

The [executed notebook](../../notebooks/srag_pfi_ranking.ipynb) prints every
repeat and its running readout in §11. The
[executable source](../../../../tools/srag_pfi_walkthrough.py) reproduces the
recorded permutations. Each repeat copies the original evaluation matrix;
outcomes and all nonselected inputs remain fixed. Original loss is shared.
Brier degrades upward, so its difference is permuted minus original error.
The classifier's default accuracy score is not substituted for Brier.

## One final dependence example

The final example removes categorical-association statistics and separate
subgroup screens from the main flow. Its graph retains the recorded individual,
joint and subgroup diagnostics. The selector changes the explanatory question,
movement diagram, procedure and numerical reading together.

The default joint example takes both values from the same donor row. It preserves
the observed heart-disease/diabetes pairs. This is our complementary diagnostic,
not Molnar's subgroup procedure. Relationships with other inputs can still break.

The subgroup option follows Molnar: separate by a related feature, shuffle inside
each group, keep the predictor fixed and compare with that group's original loss.
Here diabetes defines the groups and heart disease is shuffled. The overall
summary weights group errors by record counts; it is checked against full-test
error in every repeat (§14). This restriction is based on diabetes alone, not
full conditional PFI given all other inputs. Shared Unknown states are described
in the technical audit without being interpreted as clinical correlation.

Joint versus summed individual importance does not prove interaction or
redundancy. The scores answer different questions. The graph reports shuffle
SD conditional on the fitted model and evaluation records, not a population
interval. The historical test has already been inspected; this explanation is
exploratory. PFI is neither causal attribution nor an effect-direction plot.

## Evidence and primary references

- [Technical sheet](../../PFI.md): numerical scopes, data treatment and reproduction.
- [Evidence notebook](../../notebooks/srag_pfi_ranking.ipynb): existing mechanism/ranking audit, complete repeat trace, recorded model-selection cards and additional dependence diagnostics.
- [Raschka's original lecture](https://sebastianraschka.com/pdf/lecture-notes/stat451fs21/13_feat-sele__slides.pdf).
- [Molnar's chapter](https://christophm.github.io/interpretable-ml-book/feature-importance.html).
- [Molnar's subgroup example](https://christophm.github.io/interpretable-ml-book/feature-importance.html#group-wise-pfi-example).
- [scikit-learn: permutation algorithm](https://scikit-learn.org/stable/modules/permutation_importance.html).
