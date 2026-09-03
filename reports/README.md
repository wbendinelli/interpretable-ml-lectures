# Reports

Written deliverables built **on top of** the modules: a report reads the
notebooks, cites their measurements and argues something with them. It never
measures anything of its own.

Numbering is this repository's own, sequential from `01`, in the order the
reports were written.

- [`01-metodos-locais/`](01-metodos-locais/) — *Um paciente, cinco perguntas*
  (SCC5819, ICMC-USP). Explains the course model with the five local
  model-agnostic methods of modules 01–05, all on a single rule-picked
  patient. Written in Brazilian Portuguese, typeset in Typst.

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

Reports do not generate figures. They reuse the PNGs committed under
`modules/NN-slug/figures/`, and may keep a derived, reproducible copy — see
[`01-metodos-locais/figuras/`](01-metodos-locais/figuras/) for one that strips
the in-image headline, which a notebook needs and an article does not.
