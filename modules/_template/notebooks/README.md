# Notebooks

Two per module, named after the module slug:

- `<slug>_walkthrough.ipynb` — the lecture. Builds the figures, prints every
  number the module README and outline quote.
- `<slug>_internals.ipynb` — the technical companion. Validates the library
  against its own installed source and measures the method's behavior
  independently of what its documentation promises.

Conventions (the full list is in [CONTRIBUTING.md](../../../CONTRIBUTING.md#notebook-conventions)):
`RANDOM_STATE = 42`; splits stated explicitly; figures written to
`figures_generated/` (git-ignored) and hand-promoted to `../figures/`; commit
with outputs after *Restart & Run All*; first cell is an unpinned
`%pip install -q …` for Colab — leave it unpinned.

Delete this file once the two notebooks exist.
