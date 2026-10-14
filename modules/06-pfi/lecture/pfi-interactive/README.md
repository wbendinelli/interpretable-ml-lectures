# Interactive PFI lesson

This is the canonical browser presentation for [module 06](../../README.md).
It follows Raschka’s conceptual sequence and uses Molnar’s Permutation Feature
Importance chapter to guide interpretation. Its empirical results come from
the recorded SRAG experiment; the row diagrams use symbols rather than patients.

## Run the lesson

From the repository root:

```sh
python -m http.server 8765 --bind 127.0.0.1
```

Open the lesson at
`http://127.0.0.1:8765/modules/06-pfi/lecture/pfi-interactive/index.html`.
An HTTP server is required because the lesson fetches JSON and SVG assets;
opening the HTML directly from the filesystem is unsupported. A GitHub source
page displays the code, rather than running this presentation.

The repository version reuses [the course fonts](../../../../tools/fonts/README.md)
instead of keeping another copy. Serve the repository root so those relative
font paths resolve. Dataset-level data and figures required by the runtime
are bundled within this directory. No trained model or patient file is needed
to display the lecture.

## Read and reproduce

- [Teaching sequence](STORYTELLING.md): purpose and scope of each screen.
- [Aggregate method sheet](method.html): loss, temporal study and algorithm.
- [Walkthrough](../../notebooks/pfi_walkthrough.ipynb) and
  [internals](../../notebooks/pfi_internals.ipynb): executed module evidence.
- [Aggregate JSON](data/pfi-aggregates.json): displayed measurements at full precision.
- [Source provenance](fontes/provenance.json): conceptual sources and figure origins.

The display code is split by responsibility: `lecture.js` owns navigation and
the context map; `pfi-example.js` owns the symbolic shuffle and ranking;
`sequence.js` owns the code walkthrough and recorded repeat trace;
`study.js` owns study slides and diagnostics. The compact slide definitions
keep study and interpretation text separate from their animation controllers.
`presentation-grid.css` is the final layout layer and loads after component
styles; `public-schematic.css` styles symbolic row diagrams.

The browser replays measured dataset-level results. It does not retrain the
predictor, calculate predictions from its symbolic rows or infer intermediate
measurements while animating. Each new column demonstration restores the
original symbols. The diagram’s row positions are not the empirical sample.

## Check or export the static presentation

[The content exporter](../../../../tools/srag_72_pfi_presentation.py) uses an
explicit, typed field allowlist at every level. It projects the scientific
record in module 00, verifies the canonical JSON and checks static resources:

```sh
python tools/srag_72_pfi_presentation.py --check
```

To prepare an independent static folder, choose an absent or empty temporary
directory outside the repository:

```sh
python tools/srag_72_pfi_presentation.py --output-dir /tmp/pfi-static-export
python -m http.server 8766 --bind 127.0.0.1 --directory /tmp/pfi-static-export
```

The exported folder has local copies of the used fonts and their OFL notice.
Only declared runtime assets are copied. No notebooks, research directories,
patient previews, individual predictions, association cross-tabs, subgroup
tables, snapshots or original slide images are exported. This prepares a
reviewable folder; it does not publish it or configure hosting.

Aggregate JSON is generated from the scientific evidence, not manually edited
to make the slide look correct. The module notebook validates this projection.
Figure copies originate in the module 00 PFI notebook’s mechanism, repeat-audit
and dependence sections. Promote regenerated figures explicitly and document
their generating cell, following the repository’s contribution policy.

## Sources and reuse

- [Molnar · Permutation Feature Importance](https://christophm.github.io/interpretable-ml-book/feature-importance.html).
- [Raschka · Feature Selection lecture](https://sebastianraschka.com/pdf/lecture-notes/stat451fs21/13_feat-sele__slides.pdf).
- [Raschka · course repository MIT license](https://github.com/rasbt/stat451-machine-learning-fs21/blob/main/LICENSE).
- [Lecture code notice](fontes/LICENSE-Lecture.txt) and
  [upstream course repository notice](fontes/LICENSE-Raschka.txt).

Raschka’s original PDF is linked as a source. Its pages are not copied into
this package; the upstream repository’s verified MIT license is not presented
as evidence of the external PDF’s license. Molnar’s figures are also linked
through the book rather than reproduced. The lecture’s diagrams and SRAG
aggregate plots are identified separately.
