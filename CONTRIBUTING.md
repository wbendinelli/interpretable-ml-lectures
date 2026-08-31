# Contributing

This is a working repository: one module per interpretability method, each
studied deeply enough that every claim in it can be checked. The page below is
the practical how-to — it is also what CI enforces on every pull request, so
nobody has to nitpick by hand.

Corrections and replications from anyone are welcome. The most valuable thing
you can send is a measurement showing that something here is wrong.

## Your first contribution

1. **Fork** the repository and clone your fork.
2. **Set up the environment** (Python 3.12 — the committed numbers were produced on it):

   ```bash
   uv venv --python 3.12 .venv
   VIRTUAL_ENV="$PWD/.venv" uv pip install -r requirements.txt
   .venv/bin/jupyter notebook
   ```

   To reproduce the committed outputs exactly, install the full locked stack
   instead: `uv pip install --require-hashes -r requirements.lock`. Plain
   `pip install -r requirements.txt` inside a 3.12 virtualenv works just as
   well if you'd rather not use `uv`.

3. **Run a walkthrough notebook** end to end (e.g. `modules/03-lime/notebooks/lime_walkthrough.ipynb`) to see the format working.
4. **Branch, change, open a pull request.** CI runs the notebooks and checks links and formatting on every PR — if something is off, the robot says exactly what, before anyone else even looks.

One heads-up: the first cell of every notebook is `%pip install -q …` with no
version pins. That is on purpose — it is what makes the Colab badge work, and
in a prepared venv it is a no-op. Leave it as is (no `-U`, no versions).

## The evidence bar

The one idea that makes this material worth publishing — everything in it can
be checked, not just believed:

1. **A number stated in prose is printed by a committed notebook cell in the
   same module**, so any reader can re-run it.
2. **Numbers carry their conditioning** — sample size, seed, span — so they
   can be compared honestly.
3. **When a claim turns out wrong, the text is corrected and a note of the
   old value stays.** Corrections are part of the material, not something to
   hide — the LIME module keeps several of its own, and they are some of its
   best teaching moments.

Two practical notes: quotes from the literature are verbatim with section
pointers, and we cite and link Molnar's book rather than pasting its figures.

## Notebook conventions

- Two notebooks per module: `<slug>_walkthrough.ipynb` (the lecture) and
  `<slug>_internals.ipynb` (the companion that checks the method against its
  own library).
- `RANDOM_STATE = 42`; data splits stated explicitly.
- Figures go to `figures_generated/` (git-ignored); the committed copies live
  in `modules/NN-slug/figures/` and are promoted by hand, so a committed
  figure never changes silently.
- Commit notebooks **with outputs**, after *Restart & Run All* in a fresh
  kernel — that is what makes the numbers checkable. In practice:

  ```bash
  PIP_DISABLE_PIP_VERSION_CHECK=1 jupyter nbconvert --to notebook \
    --execute --inplace modules/NN-slug/notebooks/<name>.ipynb
  ```

- Keep outputs deterministic: no timestamps, no `%%time`, no progress bars.

(CI verifies all of this automatically — the list is here so the robot's
messages make sense, not so anyone memorizes it.)

## Adding a new module

Module numbers are **this repository's own**, sequential in teaching order —
`01`, `02`, `03`, … — not Molnar's chapter numbers. Each module README names
the chapter it covers, so the mapping is stated where it matters rather than
encoded in a directory name. Start from [`modules/_template/`](modules/_template/):

```
modules/NN-slug/
├── README.md
├── figures/
├── lecture/
│   └── outline.md
└── notebooks/
    ├── <slug>_walkthrough.ipynb
    └── <slug>_internals.ipynb
```

When it lands, add its row to the module table in the [root README](README.md#modules) —
that table is maintained by hand.

Two things that help the series read as one continuous case: keeping the
shared setup where it fits (Breast Cancer Wisconsin dataset,
`RandomForestClassifier(n_estimators=300, min_samples_leaf=3, random_state=42)`,
test patient #67), and noting in the README when a module overrides a package
default, so readers comparing with other tutorials know why outputs differ.

A note on dependencies: the pins in `requirements.txt` are what make the
committed numbers reproducible, so version bumps travel together with a full
re-run of the notebooks and a regenerated `requirements.lock`. Dependabot only
watches GitHub Actions here, where a bump changes no printed number.

Delivered slide decks are historical records — they keep their presenter's
name and are not retro-edited; the living, editable form of a lecture is its
`lecture/outline.md`.

## Contact

Questions, suggestions, or anything you'd rather raise privately:
[@wbendinelli](https://github.com/wbendinelli). Commit style follows the
existing history (`docs(03-lime): …`, `fix(03-lime): …`); look at `git log`
and copy the shape.
