# Modules

One module per interpretability method, in teaching order. **Module numbers
are this repository's own** — sequential, `01` onward — and each module README
names the chapter of Molnar's *Interpretable Machine Learning* it covers, so
the mapping is stated in prose rather than encoded in a directory name.

- [`00-dataset/`](00-dataset/) — the shared case: SRAG / SIVEP-Gripe
  microdata. It teaches no method; it establishes and documents the data every
  other module works on.
- [`01-ceteris-paribus/`](01-ceteris-paribus/) — ceteris paribus profiles (Molnar ch. 12).
- [`02-ice/`](02-ice/) — individual conditional expectation curves (Molnar ch. 13).
- [`03-lime/`](03-lime/) — LIME (Molnar ch. 14).
- [`04-counterfactual/`](04-counterfactual/) — counterfactual explanations (Molnar ch. 15).
- [`05-shap/`](05-shap/) — Shapley values and SHAP (Molnar chs. 17–18).
- [`06-pdp/`](06-pdp/) — partial dependence plots (Molnar ch. 19).
- [`07-ale/`](07-ale/) — accumulated local effects (Molnar ch. 20).
- [`08-feature-interaction/`](08-feature-interaction/) — pairwise interaction and H (Molnar ch. 21).
- [`09-functional-decomposition/`](09-functional-decomposition/) — decomposition of a joint PD surface under a declared product measure (Molnar ch. 22).
- [`10-pfi/`](10-pfi/) — permutation feature importance, a global error-based explanation (Molnar ch. 23).
- [`_template/`](_template/) — the starting point for a new module; see
  [Adding a new module](../CONTRIBUTING.md#adding-a-new-module).

Modules 01–05 share one dataset, one model, one split and one patient —
the committed SRAG/COVID sample, the XGBoost that module 00's pre-registered
selection study chose, the temporal split (train ≤2022 / val 2023 / test
2024) and the rule-picked exemplar patient, all documented in
[`00-dataset/MODEL.md`](00-dataset/MODEL.md) — so the series reads as a
single continuous case rather than five unrelated demos. Each module refits
the model from the committed sample through `tools/srag_60_model.py`, so the
sharing is enforced by code. The authoritative status list is the
[module table in the root README](../README.md#modules).

Modules 06–09 keep the same predictor and use declared samples of the temporal
test for global effects. They move from the mean of ICE curves to local
differences, non-additivity and an explicitly scoped surface decomposition.

Module 10 shares that dataset, reference model and temporal split, but measures
global predictive reliance over evaluation records rather than attributing a
single patient's prediction. Module 00 keeps the source data/model contracts and
historical permutation records; module 10 owns the current PFI notebooks,
figures, outline and interactive lecture.
