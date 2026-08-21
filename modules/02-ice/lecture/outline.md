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

Then the numbers. Median curve range **0.199**. Flat curves: **0 of 143**.
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

That is the slide that converts a negative result into a finding. The
instrument is not blind; the model has nothing to hide.

## 8. Where the structure actually is — derivative ICE

Curve *shapes* agree, which is why §6 comes back at zero. Curve *slopes* do
not: the spread of per-patient derivatives runs **0.64 to 2.53** times the mean
slope, and 18–55% of patients have a slope of the opposite sign to the mean
where the model moves fastest (internals §3).

The lesson for practice: raw ICE and d-ICE answer different questions, and on
this model only the second one finds anything. Plotting only the first would
have you conclude there is no heterogeneity at all.

## 9. The bill from module 01, multiplied — `ice_step_5_impossible.png`

Same criterion as module 01, applied to every row this plot generates: **88% of
17,160 rows are geometrically impossible**, and there is **no patient** for whom
less than half the curve is fiction.

Put the three modules on one line, because this is the thread of the course:

| | rows synthesised | impossible |
|---|---|---|
| 01 · one CP curve | 200 | 84% |
| 02 · this ICE plot | 17,160 | 88% |
| 03 · LIME's cloud | 5,000 | 76% |

Three methods, three sampling schemes, one habit: asking the model about
patients that could not be biopsied. Nothing in the sequence relaxes it.

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
- *"So is ICE useless here?"* No — it is the only thing that licensed the PDP.
  And d-ICE did find patient-to-patient structure that raw ICE missed. The
  method earned its place; the phenomenon it hunts happens to be absent.
