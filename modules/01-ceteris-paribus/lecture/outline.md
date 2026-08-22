# Lecture Outline — Ceteris paribus

Figures referenced by file name in `../figures/`. Every number below is printed
by `cp_walkthrough.ipynb` or `cp_internals.ipynb`; markers like `(internals §4)`
point into the latter.

**Learning objectives.** By the end, students should be able to compute a
ceteris paribus profile and name the rows it feeds the model; explain why a
forest profile is a staircase and why a step height belongs to the grid;
measure the fraction of a profile that could not exist; and say why the obvious
check for that fails.

---

## 1. Why start with the simplest thing in the course

Open by saying what this method does *not* have: no surrogate, no sampling
distribution, no kernel, no hyperparameter that decides the answer. Hold one
patient fixed, move one measurement, plot the output. The curve is the model's
own, computed rather than approximated.

Then say why that matters for the next three modules. Because nothing is
approximated, any problem you find is not the approximation's fault — it is in
the *question*. And the question here contains one assumption that every later
method also makes.

*Discussion prompt before the first figure:* if you change a patient's tumour
perimeter and leave the radius alone, what have you built?

## 2. The definition, and the whole implementation

$$\text{CP}_j(z) = \hat{f}\big(z, \mathbf{x}_{-j}\big)$$

Three lines of code: tile the patient, overwrite one column with the grid,
predict. Show it. The brevity is the point — there is no machinery to blame
later.

State the two parameters nobody reports: the **span** of the sweep and the
**resolution** of the grid. This module uses ±2.5σ and 200 points — and say the
next part out loud, because the code clips the grid to the observed range: on
this feature the sweep is actually **−1.88σ to +2.5σ**, not symmetric. §2 of the
companion measures what each parameter does. Promise to come back to it.

## 3. The profile — `cp_step_1_profile.png`

**Say this before anything else about the shape.** It is a staircase because a
forest is piecewise constant. Between splits, moving the measurement does
literally nothing; the model's answer lives entirely in the jumps.

Numbers to have ready: the swing is **0.212**, in **6** steps larger than 0.01,
and the largest single step is 0.039, across the grid interval running from
perimeter 115.1 to 115.8 (we quote it by its left edge, 115.1).

**Then take the last number back, out loud.** At the same ±2.5σ span, 50 grid
points make that step read 0.094 and 800 make it read 0.023 (internals §2). A
step height is a property of the spacing — a finer grid cuts the same jump into
more pieces. The swing, by contrast, is identical to three decimals at every
resolution *and* at every span: ±1σ, ±2.5σ and ±5σ all give 0.212. Widening the
sweep buys no signal at all; the only number it moves is the impossible fraction
of §4, from 64% at ±1σ to 84% at ±2.5σ (88% at ±5σ).

And refit the forest: across 12 seeds the swing runs 0.116 to 0.181 and the
largest step wanders between perimeter 112.1 and 115.1 (internals §3). Then
disclose where the headline sits: this lecture's forest is seed 42 and swings
**0.212**, above all twelve refits (max 0.181, median 0.161). The number on the
slide is an upper-tail draw of the seed, not a typical forest. So the rule is
**quote the swing and the direction, never a threshold** — and quote the swing
with its seed. Someone in the room has written "the cut-off is 115" in their
notes; make them cross it out.

## 4. The measurement — `cp_step_2_impossible.png`

The core of the lecture. Set it up as a constraint, not an opinion.

Across all 569 patients, `worst perimeter / worst radius` lies between **6.22
and 7.67**. Say what that is with care, because a doctoral room will test it.
The ratio is *dimensionless* — a shape factor, so it does not drift with tumour
size the way a ratio with units would — and a convex closed contour has a floor
at 2π ≈ 6.283. But the band is measured, not derived. Its upper edge is a sample
maximum, and 11 of the 569 patients sit *below* 2π, the lowest at 6.224.

Do **not** explain that away with order statistics ("`worst X` is the mean of
the three largest values across nuclei, so the perimeter and the radius need not
describe the same nucleus"). The walkthrough falsifies it in the cell after the
envelope: the `mean` block, where both columns average the *same* nuclei, dips
further — minimum 6.175, with 6 of 569 below the floor. The floor is broken
because the perimeter is traced on a digitised contour rather than on a smooth
curve. It is a measurement artefact, not mismatched nuclei.

Call it an **empirical dependence envelope with a geometric floor**. Overselling
it as "geometry" is the one thing in this section that will not survive.

The sweep freezes the radius. So with her radius at 16.97, the perimeter can
only be 105.6 to 130.2 — and **84% of the plotted grid is outside it at the ±2.5σ width we chose** — 64%
at ±1σ, and 88% if you sweep the feature's whole observed range (50 to 251)
instead. Say the width out loud with the number; it is a knob, not a property of
the method. (A 1st–99th percentile band on the same ±2.5σ sweep gives 88% too —
a different quantity that rounds to the same number — so the robust version is
harder on us, not easier.) Point at the grey part of the curve and say what it
is: not noise, not extrapolation error, but the model's opinion about a tumour
that cannot be built.

Then the check that keeps this honest: **the largest step falls inside the
possible range**. The headline of the plot survives. Say that plainly — the
measurement is not a gotcha, and half the value of running it is the cases where
it comes back clean.

Scale it up with `cp_top_features.png`, and resist quoting a median: the six
features split into three at **6–23%** and three at **84–87%**, with nothing in
between. The high group is the radius/perimeter block, where the ratio is
dimensionless and its observed band is only 1.15–1.23 wide, so freezing the
partner really does pin the swept feature. The low group is the concave-points
pair **and `worst area`** — area over radius carries units of length, its band
is 5.05 wide, and it constrains almost nothing, which is why `worst area` lands
at 23% despite |r| = 0.99 with its partner. Say that, rather than "the stronger
the correlation, the more fiction": over the 30 features |r| ranks with the
impossible fraction at only ρ = 0.75 (internals §4), and the pair at |r| = 0.989
gives 24% where the pair at 0.998 gives 87%.

## 5. The check that fails, and the check that works — `cp_step_3_distance.png`

Ask them for the general-purpose test — the one that needs no anatomy. They
will propose distance to the data. Run it. It rejects **0%** of a curve the
envelope rejects 84% of.

**Then take that 0% apart, because it is worthless.** The patient is herself a
row of the dataset, so she is the nearest "real" neighbour at **100%** of the
grid points, and the distance being measured is nothing but the displacement
along the swept axis. Its maximum, 2.500σ, *is* the span we typed. With any
span below the 4.45σ cutoff the test could not have fired. This is the most
useful thing in the module: a statistic that could not have come out any other
way is not evidence, and it looked exactly like evidence.

Fix it and it still does not fire — leave her out and the sweep reaches 3.32σ,
short of the 4.45σ cutoff. But now the verdict is visibly a choice of cutoff:
100% rejected against the median real distance, 21% against the 75th percentile.

**Then the punchline.** Swap the metric for one that knows the covariance and
**Mahalanobis rejects 82%** against the envelope's 84%, with no domain knowledge
at all. Be exact about what matches: the counts, not the sets. The two verdicts
agree point-by-point at **90%** of the grid points — 9 rejected only by
Mahalanobis, 11 only by the envelope, and you can see the gaps in the figure.
Two unrelated criteria landing in the same order of magnitude is the result.
So the lesson is not "you need a domain constraint" — it is
**marginal versus conditional**. These rows are typical under every feature's
own marginal and impossible under the joint; a per-feature standardised metric
sees only marginals, a whitened one sees the joint.

That vocabulary is what the field uses, and it is the doorway to chapter 20:
accumulated local effects exists precisely to compute an effect without ever
leaving the joint distribution. Name it here even if you do not teach it.

Note also, for honesty about novelty: Goldstein et al. (2015) §4.3
"Extrapolation Detection" already makes this point, with a generating process
where each coordinate is unremarkable and the combination has probability zero.

## 6. The remedy, tested — `cp_step_4_restricted.png`

Molnar's advice for correlated features is to restrict the curve to a realistic
interval. Apply it, and report what survives: **79%** of the swing, and the
crossing of P = 0.5 is still there.

So on this feature the remedy costs almost nothing. Say that it is a result
about this feature and not a guarantee — if the interesting behaviour had lived
in the discarded part, restricting would have deleted the finding rather than
cleaned it.

## 7. Return to the board

Answer the opening prompt. What you built when you moved the perimeter and left
the radius alone was a tumour with no possible shape, and the model answered
about it without complaint — because a model has no way to refuse.

Then hand off. A ceteris paribus profile is honest about the model and silent
about whether the question is meaningful. Module 02 stacks 143 of these curves
and asks what their average hides; module 03 moves all thirty features at once
and fits a model to the result, paying the same bill in thirty dimensions.

**Anticipate these three — they will come.**

- *"Isn't this just extrapolation, which every model does?"* No. Extrapolation
  is predicting outside the training range; every value swept here is inside the
  observed range of that feature. The row is impossible because of the
  **combination**, and each coordinate on its own is unremarkable.
- *"Why not just sweep both correlated features together?"* Then it is not
  ceteris paribus any more — and you have to decide how they move together,
  which is a causal claim the data does not contain. The principled answer is
  **accumulated local effects** (Apley & Zhu 2020; Molnar **chapter 20**), which
  accumulates local differences inside conditional windows and so never
  evaluates the model off the joint distribution. M-plots are the other
  alternative and fail differently, by blending correlated effects together.
- *"You picked the most correlated partner. Isn't that stacking the deck?"* Yes,
  deliberately, and the companion reports the whole distribution: 13% median
  over all 30 features against 46% for those with a strong partner. The
  worst case is shown because it is the case Molnar warns about.
