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
- [`_template/`](_template/) — the starting point for a new module; see
  [Adding a new module](../CONTRIBUTING.md#adding-a-new-module).

The modules share one dataset, one model, one split and one patient — the
Breast Cancer Wisconsin (Diagnostic) dataset, a RandomForest, and test patient
#67 — so the series reads as a single continuous case rather than four
unrelated demos. The authoritative status list is the
[module table in the root README](../README.md#modules).
