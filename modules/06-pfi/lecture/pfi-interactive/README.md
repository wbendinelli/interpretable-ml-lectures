# Interactive PFI lesson

This is the canonical browser presentation for [module 06](../../README.md).
It follows Raschka’s conceptual sequence and uses Molnar’s Permutation Feature
Importance chapter to guide interpretation. Its empirical results come from
the recorded SRAG experiment. The column animation uses real teaching records;
the ranking and repeat trace use the complete temporal test.

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
font paths resolve. The recorded teaching data, dataset-level results and
figures required by the runtime are bundled within this directory. No trained
model or raw dataset is required to display the lecture.

## Read and reproduce

- [Teaching sequence](STORYTELLING.md): purpose and scope of each screen.
- [Method sheet](method.html): teaching subset, loss, temporal study and algorithm.
- [Walkthrough](../../notebooks/pfi_walkthrough.ipynb) and
  [internals](../../notebooks/pfi_internals.ipynb): executed module evidence.
- [Aggregate JSON](data/pfi-aggregates.json): displayed measurements at full precision.
- [Teaching records](data/pfi-teaching-records.json): selected real records,
  recorded original/permuted predictions and the demonstration’s row order.
- [Source provenance](fontes/provenance.json): conceptual sources and figure origins.

The display code is split by responsibility: `lecture.js` owns navigation and
the context map; `pfi-example.js` owns the real-record shuffle and ranking;
`sequence.js` owns the code walkthrough and recorded repeat trace;
`study.js` owns study slides and diagnostics. The compact slide definitions
keep study and interpretation text separate from their animation controllers.
`presentation-grid.css` governs the common layout after component styles;
`navigation.css` refines the compact navigation at the lower right;
`real-records.css` styles the teaching rows and their recorded predictions.

The browser replays predictions and results already measured with the fitted
model. It does not retrain or run the predictor during the animation. Each
new column demonstration restores the original inputs. The Brier comparison
beside the teaching records is calculated from those recorded probabilities
and outcomes. A separate reading gives the full-test repeated-permutation
result; the ranking is not calculated from the teaching subset.

The subset uses the first adult records per observed outcome, then retains
the original dataset order. It is not selected for high confidence or correct
predictions, and it is not a performance sample. Age is in decimal years.
Repeated categories can land on the same value after a shuffle, so a row’s
probability can remain unchanged. Other model inputs and outcomes stay fixed.

## Check or export the static presentation

[The content exporter](../../../../tools/srag_72_pfi_presentation.py) uses an
explicit, typed field allowlist at every level. It projects the scientific
record in module 00 into separate aggregate and teaching-record files,
verifies the canonical data and checks static resources:

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
Only declared runtime assets and the two selected data files are copied.
The teaching file includes age, low-oxygen state, observed outcome and
individual predictions/errors. It excludes source identifiers, dates and
location fields; omission of identifiers does not establish anonymization.
No notebooks, raw datasets, research directories, association cross-tabs,
subgroup tables, snapshots or original slide images are exported. Exporting
prepares a reviewable folder; it does not publish it or configure hosting.

Both data files are generated from the scientific evidence, not manually edited
to make the slide look correct. The aggregate JSON remains free of individual
records; `project_teaching_records` and `validate_teaching_records` check the
separate teaching projection, including squared probability errors and means.
The module notebook prints and validates the same teaching comparison.
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
