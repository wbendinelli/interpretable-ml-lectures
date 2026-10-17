# Reports

Written deliverables built **on top of** the modules: a report reads the
notebooks, cites their measurements and argues something with them. It never
measures anything of its own.

Numbering is this repository's own, sequential from `01`, in the order the
reports were written.

- [`01-metodos-locais/`](01-metodos-locais/) — *Um paciente, cinco perguntas*
  (SCC5819, ICMC-USP). Records the local-method study of modules 01–05,
  organized around a rule-picked patient, with a separately declared
  counterfactual exemplar. Written in Brazilian Portuguese, typeset in
  Typst. This is a delivered historical artifact; its PDF and source are
  preserved.
- [`02-modelo-global-pfi/`](02-modelo-global-pfi/) — *Dos registros à
  importância global*. Living synthesis in Brazilian Portuguese, covering
  the dataset/model study and the implemented methods of modules 01–06,
  through Molnar's PFI chapter. It distinguishes the recorded sample-trained
  reference from the new sample-based balancing search with strategy-specific
  tuning. The sample-based comparison is complete and retained the original
  configuration under validation log loss. The full-training execution was
  stopped before selection. The report keeps these studies distinct and does
  not silently replace the predictor used by the method modules.

The second report extends the coverage of the first; it does not overwrite
its delivered PDF. Reaching Molnar's PFI chapter does not mean every preceding
chapter has been implemented: the method coverage is stated in the report and
in [ROADMAP.md](../ROADMAP.md). The living report is currently Markdown;
no new PDF has been generated.

## The evidence bar applies here too

A report lives outside `modules/`, so the rule needs one extra clause: every
number in its prose is printed by a versioned notebook cell **and the sentence
carrying it names the module**, so the checker knows where to look.

```bash
python3 tools/check_numbers.py \
  --prose reports/NN-slug/main.typ \
  --exempt reports/NN-slug/check_numbers_exempt.txt
```

`MISS/SEM-PONTEIRO 0` or the report is wrong. There are three places for that
pointer, in order of preference: inside the sentence, when it fits without
sounding bureaucratic; in a footnote, when the footnote has something to say
about what the cell measured; and nowhere, because the number went too. A
footnote reading only `Módulo 00, MODEL.md.` is an address, not writing.

## Figures

Reports measure nothing of their own, and their figures come from the modules'
committed notebook cells. A report may keep a derived, reproducible copy — see
[`01-metodos-locais/figuras/`](01-metodos-locais/figuras/): its script
re-executes the same walkthrough cells off-tree with `SAPIANS_ESCALA_TEXTO` (an
opt-in knob in `tools/sapians.py`, inert by default) so the in-figure text
survives the shrink to the report column, then strips the in-image headline, which
a notebook needs and an article does not. Notebooks and `modules/*/figures/`
stay untouched.
