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
**resolution** of the grid. This module uses ±2.5σ and 200 points, and §2 of the
companion measures what each one does. Promise to come back to it.

## 3. The profile — `cp_step_1_profile.png`

**Say this before anything else about the shape.** It is a staircase because a
forest is piecewise constant. Between splits, moving the measurement does
literally nothing; the model's answer lives entirely in the jumps.

Numbers to have ready: the swing is **0.212**, in **6** steps larger than 0.01,
and the largest single step is 0.039 at perimeter 115.1.

**Then take the last number back, out loud.** At 50 grid points that step reads
0.048; at 800 it reads 0.015 (internals §2). A step height is a property of the
spacing — a finer grid cuts the same jump into more pieces. The swing, by
contrast, is identical to three decimals at every resolution.

And refit the forest: across 12 seeds the swing runs 0.116 to 0.181 and the
largest step wanders between perimeter 112.1 and 115.1 (internals §3). So the
rule is **quote the swing and the direction, never a threshold**. Someone in the
room has written "the cut-off is 115" in their notes; make them cross it out.

## 4. The measurement — `cp_step_2_impossible.png`

The core of the lecture. Set it up as a constraint, not an opinion.

Across all 569 patients, `worst perimeter / worst radius` lies between **6.22
and 7.67**. It has to: the two measure the same object, and a closed shape has a
perimeter about 2π times its radius. That is not a statistical regularity, it is
geometry.

The sweep freezes the radius. So with her radius at 16.97, the perimeter can
only be 105.6 to 130.2 — and **84% of the plotted grid is outside it**. Point at
the grey part of the curve and say what it is: not noise, not extrapolation
error, but the model's opinion about a tumour that cannot be built.

Then the check that keeps this honest: **the largest step falls inside the
possible range**. The headline of the plot survives. Say that plainly — the
measurement is not a gotcha, and half the value of running it is the cases where
it comes back clean.

Scale it up with `cp_top_features.png`: median **53%** over the six features the
forest leans on most, and in the companion, **46%** over the 14 features with a
partner correlated above 0.9 against 13% over all 30. The stronger the
correlation, the more of the curve is fiction. That is the mechanism.

## 5. The check that fails — `cp_step_3_distance.png`

This is the section that will be new to most of the room, and it is worth the
time.

Ask them for the general-purpose version of the test — the one that works
without knowing any geometry. They will propose distance to the data. Run it.

Real patients sit within **4.45σ** of a nearest neighbour at the 95th
percentile. The sweep never gets beyond **2.50σ**. So the test rejects **0%** of
a curve that geometry rejects at 84%.

**Do not let this land as a bug.** Derive it at the board, it takes one line:
two real rows differ on all 30 coordinates, so they sit about √(2·30) ≈ 7.75σ
apart, while moving one coordinate a few σ moves the row a few σ. A ceteris
paribus row is **close to the data and impossible at the same time**, and no
distance-based detector can separate those.

The sentence to leave them with: distance finds rows that are far from the data;
ceteris paribus produces rows that are near it and absurd. Different failures,
and only the second has a domain answer.

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
  which is a causal claim the data does not contain. Worth saying that this is
  what accumulated local effects (chapter 9) exists to address.
- *"You picked the most correlated partner. Isn't that stacking the deck?"* Yes,
  deliberately, and the companion reports the whole distribution: 13% median
  over all 30 features against 46% for those with a strong partner. The
  worst case is shown because it is the case Molnar warns about.
