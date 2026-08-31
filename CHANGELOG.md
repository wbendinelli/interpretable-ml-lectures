# Changelog

Notable changes to the repository as a whole. Module-level content changes are
tracked in the git history under their `docs(NN-slug)`/`fix(NN-slug)` scopes.

## 2026-08-30 — module 00: the SRAG dataset

First step of moving the course case from Breast Cancer Wisconsin to the
SIVEP-Gripe SRAG microdata (individual hospitalised-case notifications,
194 fields, 4.1M records over 2019-2024). This lands the acquisition path and
the documentation; the recorte, the treatment pipeline and the notebooks come
next.

- `tools/fetch_srag.sh`: pins the frozen yearly banks (extraction 26/06/2025)
  straight from the S3 bucket. The `dadosabertos.saude.gov.br` portal was
  returning HTTP 500 on every page on both hosts, which also blocks Guaraci's
  `srag_arquivos` discovery — the bucket is a separate service and stayed up.
  Guaraci remains the documented discovery path for the live banks, whose
  filenames carry an extraction date and change weekly.
- `tools/build_srag_dictionary.py` + `modules/00-dataset/DICIONARIO.md`: the
  194 fields with coded values, obligation class and measured fill rate per
  year, generated from the official PDF anchored on the real parquet schema.
  11 published columns are absent from the official dictionary, and the PDF
  spells `CO_DETEC`, `FAB_COV_1` and `FAB_COV_2` differently from the data.
- CI: the `changes` job now declares `pull-requests: read`. `paths-filter`
  lists the PR's files through the API, which the workflow's default
  `contents: read` does not allow.
- `modules/00-dataset/README.md`: what the measurements found — blank is not
  `9-Ignorado`; comorbidity fill tracks age, not documentation quality
  (a Simpson's paradox); the population flips from paediatric to elderly and
  back between regimes; pandemic distortion reaches non-COVID cases too; and
  the fields that leak the outcome.

## 2026-08-30 — the engineering layer

This repository is now where the modules are written; the course repository
[`scc5819/interpretable-ml-lectures`](https://github.com/scc5819/interpretable-ml-lectures)
becomes a one-way publication target. This batch brings over the engineering
that had grown there, adapted to this repository's own numbering and to its
Python 3.12 baseline. No module content changed — the LIME module was already
byte-identical in both repositories.

- `requirements.lock`: full transitive resolution with hashes, generated for
  Python 3.12 (`uv pip compile --universal --generate-hashes`). CI installs it
  with `--require-hashes`; `requirements.txt` stays the human-readable pins.
- CI (`.github/workflows/ci.yml`): link checking, pre-commit, notebook
  execution on the pinned stack with a dirty-tree guard, and `CITATION.cff`
  validation. A PR touching `modules/`, `tools/`, `.github/` or `requirements*`
  must touch `CHANGELOG.md` too (escape hatch: the `no-changelog` label).
  Third-party actions are pinned to commit SHAs.
- `canary.yml`: weekly, non-blocking run of the walkthrough notebooks on the
  newest Python and unpinned latest packages — the early-warning light for
  when the latest stack drifts away from the pinned baseline.
- `.pre-commit-config.yaml` + `tools/check_notebooks.py`: the notebook
  conventions (execution counts 1..N, unpinned `%pip`, no `%%time`) are now
  machine-checked, alongside ruff, codespell, actionlint and yaml/toml lint.
- `dependabot.yml`: GitHub Actions only. The pip ecosystem is deliberately
  unwatched — a package bump moves printed numbers and figures here, so it
  travels as a deliberate PR with a full re-run.
- `.editorconfig` and `.gitattributes`: consistent whitespace rules, and
  `linguist-documentation` so GitHub stops classifying the repository as ~99%
  Jupyter Notebook.
- `modules/_template/`: the starting point for a new module, with the section
  order that makes the modules read as one series.
- `CONTRIBUTING.md`, `AGENTS.md`, and a rewritten `CLAUDE.md` — the operating
  manual, now stating that this repository is the source and publication runs
  one way.

Two things the verification turned up, both recorded rather than papered over:

- All three modules re-run clean on the Python 3.12 locked stack, and every
  committed **PNG** figure reproduces byte-identically. The one **PDF**
  figure (`modules/03-lime/figures/lime_walkthrough_combined.pdf`) does not:
  matplotlib stamps `/CreationDate`, so a re-run differs in exactly 6 bytes
  inside that timestamp, at identical file size. `SOURCE_DATE_EPOCH` pins the
  stamp when a byte-for-byte PDF comparison is wanted — see `CLAUDE.md`.
- `lime_internals` takes 283.8 s on this 3.12 stack against 158.5 s on the
  3.14 stack the course repository pins. The CI timeouts here are set from
  the numbers measured on 3.12, not inherited.

The course repository's board tooling (`schedule.toml`, `render_board.py` and
its test suite) was deliberately left behind: it manages a class calendar with
seminar dates and presenter names, which this repository does not have.
