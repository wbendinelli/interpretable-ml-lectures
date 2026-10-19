<!-- Module README template. Keep this section order — it is what makes the
     modules read as one series. Replace every <angle-bracket> placeholder and
     delete the guidance comments. Module numbers here are this repository's
     own, sequential in teaching order (01, 02, 03, …) — not Molnar's chapter
     numbers. Name the chapter the module covers in the opening sentence. -->

# Module <NN> — <Method>

[![Walkthrough — Open In Colab](https://img.shields.io/badge/walkthrough-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/<NN-slug>/notebooks/<slug>_walkthrough.ipynb)
[![Internals — Open In Colab](https://img.shields.io/badge/internals-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/<NN-slug>/notebooks/<slug>_internals.ipynb)

<!-- Byline. Keep it right under the badges when the module backs a seminar
     that was actually delivered — it is what dates the frozen deck. Delete the
     line for a module written purely to study a method. -->
*Module author: <Name or [Name](https://github.com/<handle>)> — seminar presented <YYYY-MM-DD>, SCC5819 (ICMC-USP, <year>).*

<!-- Open with the method, Molnar chapter and question studied on the
     SRAG/COVID reference established in module 00. Declare the explanation
     unit, scale, exemplar or panel and scope; do not assume every method
     explains the same record. -->

![<hero figure alt text>](figures/<hero-figure>.png)

## Learning objectives

<!-- Four numbered objectives. Each one should be checkable: a reader either can
     or cannot do it after the module. -->

1. …
2. …
3. …
4. …

## Why bother explaining this model

<!-- Explain what this method adds to the question about the recorded model.
     Use measurements printed by this module's notebooks and identify their
     population, scale and protocol. Do not copy another case's results. -->

## What this module shows

<!-- Numbered steps of the mechanism, then a bold "The case." paragraph naming
     the instance being explained and every legibility choice made to plot it
     (which features, why this patient), stated as choices. -->

**The case.** …

## What the module concludes, and how it is measured

<!-- One bullet per claim. Every number in these bullets must be printed by a
     committed notebook cell in this module, with its conditioning (n, seed,
     span). Negative or withdrawn results stay in, marked as such. -->

- **<Claim stated as a sentence.>** <The measurement that backs it.>

## What the literature proposes to do about it

<!-- Optional section. If the problems your module measures have a literature of
     proposed fixes, map it here (as module 03 does) — cite a survey where one
     exists, and say explicitly which proposals have NOT been verified in this
     module's setting. Delete the section if there is nothing to map. -->

## Lecture

- **[`lecture/outline.md`](lecture/outline.md)** — what to say, what to point at in each figure, and the objections to be ready for.
<!-- If a deck was delivered, list the PDF here too. Delivered decks are
     historical artifacts: they carry their presenter's name and are not
     retro-edited. -->

## Notebooks

- **`notebooks/<slug>_walkthrough.ipynb`** — the lecture: builds the figures and measures the headline claims.
- **`notebooks/<slug>_internals.ipynb`** — the technical companion: validates the library against its own source and measures the method's behavior independently of its documentation.

Committed figures are in `figures/`. Notebooks generate new copies in
`figures_generated/` inside an external temporary working directory, optionally
chosen with `INTERPRETABLE_ML_WORK`. Published copies are promoted explicitly
after execution and inspection.

Use `SP.aplicar(tema="global")` and the [Global/VITA figure conventions](../../tools/README.md#perfil-global-sapians--vita).
Give every figure a main title through `SP.titulo`, distinct from panel titles,
and inspect the exported hierarchy. Use governed fonts with the documented
fallback; optional Satoshi installation is described in the [font guide](../../tools/fonts/README.md).

## A note on configuration

<!-- Required if the module overrides any package default. Say what was
     overridden, what the default does, and why it matters when comparing these
     outputs to other tutorials. Delete the section only if nothing is
     overridden. -->

## References

<!-- Author-year entries, each with a parenthetical saying what it is being
     cited FOR. Cite Molnar's chapter; never paste the book's figures or
     extended passages (license incompatibility — see CONTRIBUTING). -->

- Molnar, C. *Interpretable Machine Learning* — [<chapter> chapter](https://christophm.github.io/interpretable-ml-book/). (Course reference book.)
