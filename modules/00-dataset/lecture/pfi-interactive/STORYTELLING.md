# PFI lesson — teaching sequence and editorial decisions

The lesson uses Raschka's original slide order as a visual reference. Molnar's
[Permutation Feature Importance chapter](https://christophm.github.io/interpretable-ml-book/feature-importance.html)
guides the interpretation. The original images remain accessible with
**View original**. Adapted numerical results come from SRAG and never reuse the
illustrative accuracy values of the original random-forest slides.

## The sequence under review

| Lesson position | Raschka page | Role in this version | Editorial decision |
|---|---|---|---|
| 4 | 64 | Introduce impurity importance and compare its question with PFI | Explain mixed outcome classes, weighted impurity decreases and predictive error. Agreement between rankings is possible, not assured. |
| 5 | 65 | Separate an importance ranking from a selection study | All model inputs remain available in PFI. A ranking does not itself choose a subset or train a replacement model. |
| 6 | 66 | Identify the evaluation records | Show the study's temporal partitions. Keep the earlier random-forest OOB connection in an optional disclosure. |
| 7 | 67 | Receive the trained model | Make the fitting stage precede the explanation. No fitting occurs inside the PFI loop. |
| 8 | 68 | Record the original loss | Use death probabilities and explicit Brier scoring. Do not substitute the classifier's default accuracy score. |
| 9 | 69 | Permute one original input column | Keep the outcomes and all other inputs fixed. The compact table shows the same original real records as the mechanism slide. |
| 10 | 70 | Evaluate one recorded shuffle | Label it as a single repeat on the full temporal test. Its result need not equal the mean of all repeats. |
| 11 | 71 | Repeat and summarize | Reveal the recorded repeat values, then the mean and sample SD. The completed readout equals the Age bar in the ranking. |

The [technical sheet](../../PFI.md) records the actual numeric scopes and the
executed cross-slide audit. The [notebook](../../notebooks/srag_pfi_ranking.ipynb)
contains the printed evidence and plot generation. The
[walkthrough source](../../../../tools/srag_pfi_walkthrough.py) reproduces the
recorded permutations with the fitted reference, checks preservation of all
other inputs and returns every perturbed error.

## What the comparison does and does not establish

The MDI discussion provides conceptual context. It does not introduce an
unperformed random-forest experiment on SRAG. XGBoost gain is a different
split-based measure and is not labelled random-forest MDI. The lesson measures
permutation changes in Brier for the reference XGBoost.

The OOB explanation uses the trees that excluded a particular record from their
bootstrap training sample. The SRAG holdout explanation instead uses the complete
fitted model on the separate temporal evaluation set. This distinction replaces
the unexplained reference to “Method B” in the earlier video.

The original algorithm illustration calls its rows training examples despite
using validation evaluation in the steps. The adapted version labels evaluation
records explicitly. Its targets remain `y_eval`, avoiding any implication that
`y_val_perm` means shuffling the observed outcomes.

Accuracy and Brier have opposite performance directions. A degradation is an
original-minus-permuted change for accuracy, and a permuted-minus-original change
for Brier. The adapted code uses Brier throughout and labels individual repeats
separately from their mean. It preserves full precision until display formatting.

## Points for the next discussion

Raschka's column-drop page follows this section. It introduces refitting and a
different explanatory question. Its phrase “more accurate” should not be carried
over as a universal superiority claim.

The final pros-and-cons page needs qualified wording. Evaluation outside fitting
does not make overfitting or repeated holdout reuse impossible. Correlated inputs
can create implausible combinations and alter rankings; the direction of this
change is not universally an underestimate. Grouped or conditional approaches
answer related but distinct questions and require their own protocol.

## Primary references

- [Raschka's original lecture](https://sebastianraschka.com/pdf/lecture-notes/stat451fs21/13_feat-sele__slides.pdf).
- [Molnar's course chapter](https://christophm.github.io/interpretable-ml-book/feature-importance.html).
- [scikit-learn: permutation algorithm and relation to MDI](https://scikit-learn.org/stable/modules/permutation_importance.html).
- [scikit-learn: MDI versus PFI example](https://scikit-learn.org/stable/auto_examples/inspection/plot_permutation_importance.html).
- [scikit-learn: random forests and OOB evaluation](https://scikit-learn.org/stable/modules/ensemble.html#forest).
