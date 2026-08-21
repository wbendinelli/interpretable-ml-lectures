# Lecture Outline — ICE

Figures referenced by file name in `../figures/`. Every number below is printed
by `ice_walkthrough.ipynb` or `ice_internals.ipynb`; markers like
`(internals §6)` point into the latter.

**Learning objectives.** By the end, students should be able to state how a
ceteris paribus curve, an ICE plot and a PDP relate; measure whether a PDP is
hiding disagreement instead of assuming it; use centred and derivative ICE for
the questions each answers; and recognise a negative result as a result.

---

## 1. This lecture has an unusual shape — say so first

**Open by warning them.** This module set out to demonstrate two things and
demonstrated neither. Both measurements came back negative, and the lecture
keeps them.

Say why up front, or the room will spend forty minutes waiting for the payoff
and leave thinking the class was a dead end. The payoff is that ICE is what told
us — without the bundle we would have shown a partial dependence plot and had no
idea whether it was a fair summary or a mirage. Here it is fair. That is worth
knowing and only measurable one way.

## 2. Nothing new is computed

State the relationship immediately, in Molnar's own words: *"ICE plots are CP
plots containing all CP curves for an entire dataset."* One CP curve per patient,
drawn together. The PDP is their average (Friedman 2001), so all three objects
come from the same three lines of code from module 01.

Point out that the interesting move is therefore not computational. It is that a
bundle can be *inspected for disagreement* and an average cannot.

## 3. The bundle — `ice_step_1_bundle.png`

143 curves, 120 grid points, 17,160 calls to the model. Patient #67's curve is
in blue; find module 01's profile inside the bundle so the continuity is
visible.

**Tell them what to look at, because the instinct is wrong.** Not the average —
the spread around it. Do the thin lines differ? Does any of them run the other
way?

## 4. First prediction, and its failure — `ice_step_2_flat.png`

State the prediction *before* the figure, with its reasoning, so the failure is
honest rather than a reveal: module 03 measures 71% of held-out real patients
sitting in a saturated prediction, and a saturated patient has nowhere to move,
so most of these curves should be flat.

Then the numbers. Median curve range **0.199**. Flat curves: **0 of 143** — and
concede immediately that the smallest range in the sample is 0.105, twice the
threshold, so that zero was set by our choice of 0.05 rather than by the data.
The median is the honest headline.
Borderline patients move 0.206, confident ones 0.195, and the correlation
between confidence and movement is **−0.09**.

**Explain the error rather than moving past it.** Saturation describes patients
at *their own* feature values. This sweep drags `worst perimeter` from 50 to 251
— the entire observed range — which is a big enough move to pull anyone across
the region where the forest changes its mind. Saturation is about where the
patients are, not about where you can push them.

The companion does find flat curves, up to 43%, but only for weak features whose
median range is 0.055 for everybody (internals §2). Those are flat because the
feature does nothing to anyone, which is a different fact.

## 5. Centred ICE — `ice_step_3_centred.png`

$$\text{ICE}^{(i)}_{\text{centred}}(z) = \hat{f}\big(z, \mathbf{x}^{(i)}_{-j}\big)
  - \hat{f}\big(a, \mathbf{x}^{(i)}_{-j}\big)$$

Usually sold as the fix for the problem we just failed to find. Keep it anyway,
because it answers a clean and different question: not where each patient sits,
but how far each one moves. A patient pinned at 0.98 becomes comparable with one
at 0.11.

What it shows here: the curves stay together, and **all 143 end lower than they
started**.

## 6. Second prediction, and its failure — `ice_step_4_disagreement.png`

This is the argument ICE was invented for. Goldstein et al. (2015) proposed it
because a PDP averages away disagreement — half up and half down averages flat.

Measure it rather than assert it. At the point where the PDP is **steepest**,
which is where a misleading summary would do the most damage, the share of
moving patients going the other way is **0%**. Across the ten features the
forest leans on most: median 0%, worst case 4% (internals §2). Disagreement
appears only in the flat tails, where nothing is happening for anyone.

Say the conclusion plainly: **on this model the PDP is an honest summary.**

## 7. Proving the instrument works — the control

Someone will ask, correctly, whether ICE simply cannot detect disagreement.
Answer with the control model (internals §6): a target built so that the effect
of `worst perimeter` flips sign with `worst texture`, run through the identical
code.

Disagreement at the steepest point: **52%**, against 0% on the cancer forest.
And its PDP swings **0.028** while the median individual patient swings
**0.135** — Goldstein's failure mode reproduced on demand.

**Then state the limit of that control, before someone else does.** One control
at full strength shows the code can catch a *total* sign flip. Dial the same
interaction from zero to full and the disagreement statistic reads **0% up to
half strength** — an interaction that cuts the PDP swing from 0.255 to 0.139 is
invisible to it. So the 0% rules out an interaction as extreme as the control,
not interaction in general. Say the scope; it costs one sentence and buys the
whole argument.

The better summary is **PDP swing ÷ median individual swing**, from numbers we
already had: **1.00** on the cancer forest, the maximally faithful value,
against 0.21 on the control. It does not jump around the way the pointwise
share does — though it, too, sits near 1.00 until the interaction passes half
strength.

## 8. Derivative ICE — and a bug worth showing the room

This section used to claim d-ICE found structure raw ICE missed: "18–55% of
patients slope against the average". **That was a bug**, and it is worth two
minutes of the lecture because it is the same class of error as §1 of module 01.

A forest is piecewise constant, so at any grid point most patients have a
derivative of exactly zero, and `np.sign(0)` is 0, which is not equal to the
sign of the mean. Every patient standing still was counted as disagreeing.
Masked properly the figure is **2–11%**, and d-ICE now *agrees* with raw ICE.

So this forest shows no sign heterogeneity by either instrument — a third
negative finding. What patients do differ in is magnitude: the coefficient of
variation of net change runs **0.20 to 0.47** across the six features. Use that
statistic, not the sd-over-mean ratio, which has a near-zero denominator and
does not reproduce across seeds.

## 9. The bill from module 01, multiplied — `ice_step_5_impossible.png`

Same envelope as module 01, applied to every row this plot generates: **88% of
17,160 rows fall outside it**, and there is **no patient** for whom less than
half the curve does. Across all ten top features the median is **60%**.

**Do not draw the three-module table.** An earlier version of this outline did,
reading 84 / 88 / 76, and it was wrong twice. The 84 and the 88 differ only by
sweep width — module 01's grid over all 143 patients is 84% again, and this
grid on her alone is 88%, so going from one patient to 143 changes the rate by
zero and nothing is "multiplied". And module 03's 76% counts a different thing
("at least one negative measurement"), so the table implied LIME was the
cleanest of the three when it is not.

What is comparable is the habit: every method here evaluates the model on rows
the joint distribution excludes. Quote each number with its grid and its
criterion attached.

**And do not say nothing relaxes it.** Accumulated local effects (Apley & Zhu
2020; Molnar chapter 20) exists precisely to compute an effect without leaving
the joint distribution, by accumulating local differences inside conditional
windows. It is the answer to two lectures' worth of complaint, and the students
should hear its name before they leave.

## 10. Return to the board

Close on what a negative result is worth. The two failures are not the lecture's
weakness — they are the only reason anyone should believe the PDP shown in step
3. A summary you have tested and found faithful is a different object from a
summary you have assumed is faithful, and the difference costs one plot.

Then hand off to module 03: stop moving one feature at a time, move all thirty
at once, and fit a model to the answers.

**Anticipate these three — they will come.**

- *"You only tested one feature."* Ten, in the companion, with the same verdict.
  Say the number rather than the reassurance.
- *"Maybe the sweep range hides it."* Coarser, finer, 5th–95th percentile and
  ±1 SD all give the same result to three decimals (internals §4), because even
  the narrow sweeps span the region where the forest changes its mind.
- *"So is ICE useless here?"* No — it is the only thing that licensed the PDP,
  and the swing ratio of 1.00 is a result, not an absence of one. But be
  straight that d-ICE did **not** add anything on this model once its statistic
  was fixed. The method earned its place; the phenomenon it hunts is absent.
