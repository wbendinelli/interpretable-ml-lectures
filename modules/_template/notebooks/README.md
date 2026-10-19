# Notebooks

Two per module, named after the module slug:

- `<slug>_walkthrough.ipynb` — the lecture. Builds the figures, prints every
  number the module README and outline quote.
- `<slug>_internals.ipynb` — the technical companion. Validates the library
  against its own installed source and measures the method's behavior
  independently of what its documentation promises.

Follow [CONTRIBUTING.md](../../../CONTRIBUTING.md#notebook-conventions):

- Open with the SAPIANS identity, objectives, method and Molnar chapter.
- Print the data identity, splits, explanatory unit, scale and sampling choices.
- Keep stable `## §N —` sections, a synthesis of the book, one unnumbered
  closing section and references last.
- Fix and declare random seeds. The first code cell is an unpinned
  `%pip install -q …` for Colab; leave it unpinned.
- Resolve an external working directory before generating artifacts. Write
  figures to its `figures_generated/` folder and promote inspected copies
  explicitly to the module's `figures/` folder.
- Use `SP.aplicar(tema="global")`, a main figure title through `SP.titulo`,
  subordinate panel titles and the documented [font selection](../../../tools/fonts/README.md).
- Finish every notebook edit with a full fresh-kernel run and commit outputs.

Delete this file once the two notebooks exist.
