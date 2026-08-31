# Changelog

Notable changes to the repository as a whole. Module-level content changes are
tracked in the git history under their `docs(NN-slug)`/`fix(NN-slug)` scopes.

## 2026-08-31 — the local stack takes its credentials from the environment

The Postgres password was hardcoded in `compose.yaml` and `load.py`. The stack
binds to 127.0.0.1 and the value was deliberately trivial, but a secret scanner
flagged it and was right to: a reader cannot tell "local dev" from "leaked" by
looking, and CI should not learn to ignore that check. Credentials now come from
a git-ignored `.env`, with `.env.example` as the template; compose fails loudly
when the variable is unset rather than falling back to a default.

## 2026-08-31 — Silver, and the Ministry's own script as the reference

`tools/srag_silver.py` turns Bronze into Silver without dropping a row: every
input record leaves either in the table or in a quarantine, and the module
asserts it. Across all six years that is 4,109,567 = 4,109,560 + 7, where the
seven are structurally shifted rows — a coded column holding a date, every field
after `HOSPITAL` off by one. They had been documented as fourteen unrelated
column anomalies; they are one defect, detected once as a row-level rule.

The reference is the Ministry's own cleaning script (MIT,
gitlab.com/cgcovid/dados-publicos, authored inside CGCOVID/DEDT/SVSA/MS). What
it settles is adopted and cited by line; six departures are recorded in the
module's DEVIATIONS, each because that script exists to count surveillance cases
for the weekly bulletin, and a filter that is right for counting is wrong for a
dataset that will be modelled and explained:

- `filter(caso_srag == 1)` becomes a column. The filter drops 40.3% of records,
  including 892,168 with `CLASSI_FIN=5` — it selects on symptom fields being
  filled, not on disease.
- The official cohort criterion is `HOSPITAL==1 | EVOLUCAO==2`, so membership
  depends on the outcome. `coorte_hospitalizado` drops the second clause; in
  2021 that is 10,322 records that qualified only by dying.
- Dates are ISO in the published data, not the `%d/%m/%Y` the script parses;
  `DT_VGM` and `DT_RT_VGM` genuinely are dd/mm/yyyy and are parsed as such.
- `replace_na(0)` is followed for the 18 laboratory checkboxes, which is their
  documented domain, and not for `EVOLUCAO` (0 merges "unknown" with "did not
  die") nor for the influenza subtype fields, where 0 is not a valid code.
- Neonates symptomatic on their day of birth get age 0 rather than NA.

Two measured results worth recording. Normalising `^(-?\d+)\.0+$` *before*
inferring any domain recovers all 519,518 of 2020's COVID-positive checkboxes,
which a literal comparison against `'1'` would have discarded silently. And
separating the three readings of an empty cell shows that `CARDIOPATI` is
genuinely absent in **11.9%** of 2021 records, not the 56.1% reported until now
— 44.2% is a field the system never presented, gated by `FATOR_RISC`.

## 2026-08-31 — profile every column, in every year

Five rounds of review found the same defect in my own findings each time: a
number measured on 2021 and stated as if it held for all six years. The worst
instance would have shipped — the laboratory checkbox columns hold `'1'` in five
years and `'1.0'` in 2020, so a rule written as a literal comparison would have
discarded 519,518 COVID-positive records while leaving the row count intact.

The fix is structural rather than a promise to be careful:

- `tools/srag_profile.py` profiles all 194 columns across every year, and
  **takes no year parameter** — a caller cannot ask for one year, so a finding
  cannot be scoped to one by accident. It also **does not normalise**: values
  are reported raw, because normalising is what hid the 2020 defect.
- `modules/00-dataset/PROFILE.md` and `.json` are the committed result. Every
  claim about a column in this repository should cite a year and agree with it.
- The headline: **75 of 194 columns change value shape between years.** These
  had been surfacing one at a time, one per audit. `EVOLUCAO` is `int.0` and
  `iso-date` in 2020; `AMOSTRA` carries dates; `CO_MU_INTE` carries text; and
  `RAIOX_RES` is `int.0` in all six years, which is why `_norm`'s `\.0$` never
  touched it.

Also: `pandas`, `pyarrow`, `pypdf` and `duckdb` were missing from both
`requirements.txt` and the lock, so `build_srag_dictionary.py` — already
committed — could not run in the repository's own pinned environment. Now
pinned with hashes.

## 2026-08-30 — a data quality framework for the SRAG base

Molnar's book offers no data-preparation guidance, so the treatment is anchored
externally: **Kahn et al. (2016)** for the quality taxonomy (the standard for
secondary use of EHR data, which is what these notifications are), the
Databricks **medallion** pattern for the layers, and **pandera**-style schema
checks in committed Python rather than Great Expectations — GE finds exactly
the same defects but writes its report to an uncommitted directory by default,
and this repository's premise is that every claim is reviewable in a diff. The
report layout is modelled on GE's Data Docs without reusing its Apache-2.0 code.

- `tools/srag_quality.py` + `modules/00-dataset/QUALITY.md`: 21 checks across
  the six Kahn cells, run over all six years.
- What it found beyond the earlier pass: negative ages (`-1`, `-9`) in five of
  six years; dates leaked into `UTI` as well as `EVOLUCAO`; invalid
  `SUPORT_VEN`, `CRITERIO` and `FATOR_RISC` values; and 21,997 rows in 2021
  sharing a person-event key, 1,854 of whose groups disagree on the outcome.
- Two findings about the dictionary itself: the published data uses ISO
  `YYYY-MM-DD` where the official dictionary declares `DD/MM/AAAA`, and
  `DT_INTERNA` mixes bare dates with full timestamps in the same column.
  Parsing with the documented format silently yields NaT for every row, which
  made the three date-ordering checks pass on nothing until it was caught; with
  a correct parse they compare 82-100% of rows and find no violation at all.

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
