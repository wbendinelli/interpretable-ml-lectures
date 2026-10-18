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
  the dataset/model study and the implemented methods of modules 01–10,
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

The delivered report and its reproduction scripts belong to
[revision `509a33a`](https://github.com/wbendinelli/interpretable-ml-lectures/tree/509a33af8b629bcc9369a1e2653b4c4fa5d9f814/reports/01-metodos-locais).
Its numerical evidence must be checked against the notebook outputs in that
revision. The current readings of [LIME](../modules/03-lime/README.md),
[counterfactuals](../modules/04-counterfactual/README.md) and
[SHAP](../modules/05-shap/README.md) include later corrections; they do not
retroactively change the delivered text or figures.

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
committed notebook cells. The delivered report keeps its historical derived
copies in [`01-metodos-locais/figuras/`](01-metodos-locais/figuras/).
Its scripts enlarged labels with `SAPIANS_ESCALA_TEXTO` and cropped the
in-image headline for the article layout.

Those scripts are historical tools. `gerar_figuras.py` expects each notebook's
`figures_generated/` directory, whereas the revised notebooks write to an
external working directory. Both it and `recortar_figuras.py` write directly
to the delivered figure folder. Do not run them to refresh that folder from
the current modules, or delete its figures expecting the scripts to restore
them. Study historical reproduction in a separate checkout of the delivery
revision, preserving the delivered files and keeping any new export separate.
The living report links to the current modules; no replacement PDF or figure
set is generated automatically.
