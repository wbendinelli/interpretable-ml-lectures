# ROADMAP — every method in Molnar, on one base

The course applies the methods of Molnar's *Interpretable Machine Learning*
(3rd edition — chapter numbers verified against the live book; modules
01–03 already cite chapters 12–14) to a single dataset: the SRAG /
SIVEP-Gripe base that module 00 treats, documents and contracts.

## The organizing thesis

Module 00 measured the structure that makes this base a good *argument*,
not just a case: the notification form disables fields conditionally
(34 confirmed gates; the comorbidity funnel holds at 0.00% contradiction
across six years), so features are **jointly constrained**. Every method
that perturbs, sweeps or permutes features *independently* — ceteris
paribus, ICE, LIME, PDP, marginal Shapley, permutation importance,
anchors — manufactures patients that cannot exist: a comorbidity flag
raised while `FATOR_RISC` says there are none, a subtype without a
positive screening. The chapters built to escape that assumption — ALE,
and SHAP in its conditional form — are where the course lands.

The base also carries three named traps the modules will reuse:

- **A redundancy that is exact**: `COD_IDADE` = `TP_IDADE` +
  `zfill(NU_IDADE_N, 3)` at 100.00% — importance splits arbitrarily
  between them, by construction (the 20 exceptions in 4.1M, all negative
  ages, are printed by QUALITY.md's `conf-comp-cod-idade` check).
- **Calendars in disguise**: 21 columns are 100% empty in some year; a
  model told nothing about time can still read the year off the form
  revision.
- **Regime drift as signal**: lethality 29.0% → 8.6% across 2020–2024 —
  an explanation that surfaces "year" is *correct*, and the modules get
  to say so.

## The map

Status: ✅ available (on Breast Cancer Wisconsin — see flag 2) ·
🔜 planned · ⛔ not applicable to this base.

| Molnar ch. | Method | Status | The study on SRAG | Constraints at 4.1M × 418 |
|---:|---|---|---|---|
| 6 | Linear regression | 🔜 | baseline on the cohort; comorbidity multicollinearity destabilizes coefficients — measured, not asserted | trivial |
| 7 | Logistic regression | 🔜 | the first model of the target; coefficients vs the funnel | trivial |
| 8 | GLM / GAM | 🔜 | non-linear age effect on death — the U-shape the regimes move | term selection needs care |
| 9 | Decision tree | 🔜 | native missingness handling vs the three states | fine |
| 10 | Decision rules | 🔜 | rules over checkboxes; year leakage temptation | feature pre-selection |
| 11 | RuleFit | 🔜 | rule generation on subsample | subsample |
| 12 | Ceteris paribus | ✅→rewrite | sweep one comorbidity with 140 frozen: count impossible patients via the gates | cheap |
| 13 | ICE | ✅→rewrite | heterogeneity by regime — curves colored by year | subsample patients |
| 14 | LIME | ✅→rewrite | perturbation vs the funnel (the BCW module already measured ~75% impossible synthetics under the same scheme) | explain a sample |
| 15 | Counterfactuals | 🔜 | "what would have to change" under gate constraints — immutables (age, year) declared | per-instance |
| 16 | Anchors | 🔜 | IF-THEN over checkboxes; same sampling risk as LIME | subsample |
| 17 | Shapley values | 🔜 | exact is 2^418; the approximation choice IS the lesson | approximation only |
| 18 | SHAP | 🔜 (module 04) | TreeSHAP on the course model; interventional vs path-dependent on the funnel | efficient |
| 19 | PDP | 🔜 | average effect vs the off-manifold grid ends | background subsample |
| 20 | ALE | 🔜 | **the remedy chapter** — local conditioning respects the funnel; unordered checkboxes need an ordering choice | quantile bins, fine |
| 21 | Feature interaction (H) | 🔜 | age × year, vaccine × regime | ~87k pairs — restrict + subsample |
| 22 | Functional decomposition | theory | read with 19–21 | — |
| 23 | Permutation importance | 🔜 | permuting one member of an exact pair (`COD_IDADE`) — the arbitrariness, shown | holdout subsample |
| 24 | LOFO | 🔜 | p refits — the costliest chapter; grouped features (families!) as the fix | heavy: group + subsample |
| 25 | Global surrogates | 🔜 | fidelity (R²) read with module 03's own skepticism | subsample |
| 26 | Prototypes & criticisms | 🔜 | who is a typical 2021 patient; Gower distance over mixed types | O(N²) — coresets |
| 27–30 | Learned features / saliency / TCAV / adversarial | ⛔ | image- and NN-specific | — |
| 31 | Influential instances | 🔜 | the seven quarantined rows vs actually influential ones | deletion diagnostics: sample |
| 32 | Evaluation of interpretability | theory | the repo's own evidence bar, formalized | — |

Seventeen method modules planned beyond the three that exist; four
chapters excluded with the reason stated.

## Stages

1. **Silver complete** — done (PR #14): 194/194 columns ruled, contract
   asserted, three falsifications on the record.
2. **External validation + this map + the Gold menu** — this PR.
3. **Postgres/Metabase loader for Silver** — next PR, so the treatment is
   browsable.
4. **Gold decisions** — William + professor pick target, cohort, split
   (the menu is [`modules/00-dataset/GOLD.md`](modules/00-dataset/GOLD.md));
   then `tools/srag_gold.py` materializes them with a manifest.
5. **The course model module** — one model, one split, one patient,
   shared by every method module (the BCW series' RandomForest + patient
   #67 pattern, on SRAG).
6. **Method modules** in the table's order of dependency: interpretable
   models first (6–11), the rewrites (12–14), then the model-agnostic
   arc (19, 20, 23, 18, 17, 15, 16, 21, 24, 25, 26, 31).

## Module conventions (constraints already in force)

Numbering is this repository's own, sequential; each module names its
chapter in its README. Structure from `modules/_template/`: README with
the fixed section order, `lecture/outline.md`, two notebooks
(`<slug>_walkthrough`, `<slug>_internals`), `RANDOM_STATE = 42`, figures
promoted by explicit copy, outputs committed after a fresh-kernel run,
and a hand-added row in the root README table. Every number in prose is
printed by a committed cell in the same module.

## Two flags, recorded so they are not silently resolved

1. **The COVID requirement was never confirmed with the professor.**
   William would rather study mental health; nothing in the repository
   forces COVID (modules 01–03 run on an American breast-tumour dataset
   today). The base keeps all SRAG etiologies precisely so this stays a
   Gold-level cut, not a foundation-level commitment. Asking is cheaper
   than rewriting.
2. **Modules 01–03 still run on Breast Cancer Wisconsin.** The decision
   to rewrite them onto SRAG is recorded (2026-08-30); the rewrite slots
   into stage 6 as chapters 12–14, after the course model exists — not
   before, or they would each invent their own.
