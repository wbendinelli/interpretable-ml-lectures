# Changelog

Notable changes to the repository as a whole. Module-level content changes are
tracked in the git history under their `docs(NN-slug)`/`fix(NN-slug)` scopes.

## 2026-09-01 — module 03 (LIME) rewritten onto the COVID model

- **03-lime** completes the CP → ICE → LIME arc on the course model (BCW
  version in git history). The module is two runs with the same patient:
  naive (no `categorical_features`: 4,999/5,000 synthetic neighbours
  carry a fabricated encoding — the prediction wrapper's silent rounding
  gets a counter) and correct (0 fabricated — and the JOINT fences
  remain: 30.6% impossible neighbours for the rule patient, 79.2% for
  the vulnerable one, same `gate_impossible` as modules 00–02). Measured
  surprises kept as lessons: the two patients' clouds are IDENTICAL
  (the Gaussian is centred on the training mean, verified against the
  pinned lime source), the generator erases the meses×doses correlation
  (+0.61 real → −0.00 synthetic), the respectable knobs rescue one
  patient by geography and worsen the other, a narrow kernel yields the
  perfect empty explanation (R² 0.00, error 0.00), and the CP↔LIME
  bridge only works regionally — the pointwise staircase slope flips
  sign with step size.
- ci.yml timing comments re-measured after the rewrite (lime_internals
  283.8 s → 50 s: the module now runs on the committed sample, no
  network).

## 2026-09-01 — modules 01 and 02 rewritten onto the COVID model

- **01-ceteris-paribus** and **02-ice** now run on the course model (the
  BCW versions live in git history, pointed to from each README). The
  substantive change is announced, not hidden: impossibility moved from
  an empirical envelope to DERIVABLE fences (the funnel gate at 0.00%
  over six years, the vaccination calendar, the cohort definition),
  counted by the shared `gate_impossible` so modules print identical
  numbers by construction.
- Measured teaching moments that replaced the BCW ones: whether a sweep
  is fiction depends on WHO (the rule-picked exemplar is immune to two
  fences; a rule-picked vulnerable patient turns every sweep fictional);
  Molnar's grid restriction REMOVES the dose question for pre-campaign
  patients (amplitude 0.151 → 0.000, 6/7 impossible); XGBoost `hist`
  without subsampling is seed-DETERMINISTIC (12 seeds, correlation
  1.0000 — the BCW seed-instability lesson inverts; with subsample 0.8
  it returns at 0.979); the ICE bundle stratifies by regime (0.48 vs
  0.32 at age 80, PDP says 0.407 — describing nobody) and the ICE
  derivative peaks in the PEDIATRIC tail (0.023/yr at age 10), the
  bronchiolitis inheritance; sweeping a fenced feature costs fiction at
  bundle scale (doses 18%, tosse 54%, idade 0%).
- One real bug found by module 01's first run and fixed in the shared
  tool: `gate_impossible` read the frozen n_crit diagnostics, letting a
  swept symptom flip pass unflagged — criteria are now recounted from
  the swept symptom columns.
- New figures promoted; BCW figures removed; PT module docs join the
  codespell exclusion.

## 2026-09-01 — the course model: one XGBoost, one rule-picked patient

- **00-dataset:** the model the five method modules explain.
  `tools/srag_model.py` (features, params, fit, metrics, the exemplar as
  a RULE — |p−0.5| minimal on test, tie by gold_id — and
  `gate_impossible()`, the single function all modules count
  impossibilities with). The committed artifact is the deterministic
  Gold SAMPLE (val/test whole, train 200k seed 42, 4.0 MB), never a
  model binary: every module refits in seconds and explains the same
  object by construction. MODEL.md is generated (`--card`) from
  `gold/model_metrics.json`.
- Measured against the design's pre-registration: XGB test AUC 0.7575
  on the sample (expected ~0.757), 0.7674 full — the price of sampling
  is −0.0099 and it is printed; logistic 0.7246; calibration gap 0.216
  predicted vs 0.182 observed = the regime-drift finding. The image
  trap cell lands inverted, as measured in design: the ABSENCE of a
  tomography record predicts death (9-Ignorado deadliest), and the
  with-image model uses the proxy (+0.006 AUC, mid-ranking gain) —
  the "why not let the weight be zero" answer, printed.
- ci.yml: walkthrough timeout 15→30 min; the measured-timing comment
  block re-measured, not estimated. `*.parquet binary` in
  .gitattributes.

## 2026-09-01 — one Silver table, and tools/ reads in layer order

- **00-dataset:** the Silver is now ONE parquet (4,109,567 × 420, zstd,
  streamed year by year with a schema guard) instead of six per-year
  files plus quarantine banks: the 7 shifted rows travel in the single
  table under the `linha_deslocada` flag, catalogued like every other
  derived column, and the row invariant is a `count(*)` instead of an
  accounting exercise. `build()` is untouched — only the packaging
  moved. The Postgres loader collapses six tables + a union view into
  one `silver.srag` (verified against the running stack), and the
  derived catalogue grows 224 → 226 (the `ano` and `linha_deslocada`
  columns), cascading through COLUMNS.md, the three diagrams (whose
  count is now computed, not typed), and the READMEs.
- **tools:** renamed to a single `srag_<noun>` convention in layer order
  (`srag_fetch`, `srag_profile`, `srag_dictionary`, `srag_silver`,
  `srag_quality`, `srag_columns`, `srag_diagrams`, `srag_gold`) — which
  also heals the walkthrough's broken link to `tools/srag_columns.py`,
  a name that did not exist until now. `tools/README.md` documents what
  each script reads and writes; the root README stops describing tools/
  as a single checker (wrong for eight files).
## 2026-09-01 — the Gold exists, and every choice in it is a flag

- **00-dataset:** `tools/srag_gold.py` builds `gold_covid_obito.parquet`
  (1,282,970 × 50: 40 model features + bookkeeping + diagnostics) from
  the Silver, with **every task decision a required CLI flag** — running
  it bare prints the GOLD.md menu and exits. The committed
  `gold/MANIFEST.md` is a pure function of `counts.json` + the decisions
  (hook-verified): the funnel in filter order, the NA each boolean fill
  absorbed, the three-state fold declared and undone via the
  `fator_risc_portao` diagnostic, and the decisions the menu never
  anticipated. The funnel reproduces the design's pre-registered numbers
  step by step (the one-row cohort difference is the quarantined 2023
  row, noted in the manifest).
- **00-dataset:** GOLD.md's five decision sections now carry their
  "Decidido 2026-09-01 — William" blocks; the closing section describes
  what was materialized instead of promising a tool.

## 2026-09-01 — xgboost joins the pinned stack; shap tried and rejected

- **build:** `xgboost==3.4.1` pinned for the course model. The lock diff
  contains only additions (xgboost + its nvidia-nccl marker dep), verified
  against the falsification criterion: no existing pin moved. `shap` was
  spiked and rejected — against numpy 2.4.6 the resolver walks numba back
  to 0.53.1 (2021), which fails to build on Python 3.12; module 05 will
  use xgboost's native `pred_contribs` (exact TreeSHAP) instead, with the
  runtime evidence in the PR. macOS needs `brew install libomp`.

## 2026-08-31 — every derived column gets a definition label

- **00-dataset:** the 224 derived columns now carry definition labels
  (Portuguese, like the raw labels in DICTIONARY.md) with provenance —
  the Ministry's script line for the official catalogue, "deste módulo"
  for ours. `derived_catalogue()` builds the list from the same tables
  `build()` uses, COLUMNS.md renders it, and `write_year()` asserts the
  built Silver's extra columns are exactly the catalogue: a derived
  column without a label now fails the build, the same way a raw column
  without a rule does. `silver.contrato` in Postgres grows 194 → 418
  rows, so the labels are browsable in Metabase next to the data.

## 2026-08-31 — the Silver, browsable

- **00-dataset:** the Postgres loader gains four indexes per yearly Silver
  table (NU_NOTIFIC, SG_UF, se_primeiro_sinto, covid_caso) and
  `silver.contrato` — the 194 columns with family, class, domain and gate,
  straight from the contract tables, browsable in Metabase next to the
  data. Verified against the running stack: 4,109,560 rows in silver.srag,
  194 in the contract.

## 2026-08-31 — the map, the Gold menu, the roadmap, and Fiocruz agreement

- **00-dataset:** `PIPELINE.svg` — the Bronze→Silver→Gold map, generated by
  `tools/srag_pipeline_svg.py` from the contract tables (structure and
  counts cannot drift from the code; quoted findings cite notebook cells).
  Gold's lane is dashed: its decisions are open by design.
- **00-dataset:** `GOLD.md` — the decision menu (target, cohort, leakage
  exclusion, split, encoding), each option with measured evidence printed
  by internals §7, a recommendation, and an owner. The leakage exclusion
  is generable from the class annotations and changes with the target.
- **00-dataset:** external validation against Fiocruz's published InfoGripe
  series: the public CSV freezes at 2019, and on that window our
  reproduction identifies their fever-inclusive case definition by fit and
  reaches correlation 0.9997 on stable weeks (median gap 28 cases/week,
  3.3%; 27 UFs at median 0.997). The authoritative GitLab is login-gated
  as of 2026-08 — recorded as the upgrade path, not hidden.
- **ROADMAP.md** — every Molnar chapter mapped onto the base: 17 method
  modules planned beyond the existing three, 4 excluded as image/NN-only,
  compute constraints at 4.1M×418 stated per method, and the organizing
  thesis: the feature-independence assumption is the comorbidity funnel.
- **Language:** module 00's README, GOLD.md and the ROADMAP are written in
  Portuguese by decision (2026-08-31) — they are study material, in the
  language William studies in. Two more generated diagrams join the map:
  FUNIL.svg (the three readings of a blank) and REGIMES.svg (lethality and
  COVID share per year, computed from the committed PROFILE.json).

## 2026-08-31 — every column has a rule: the contract, and three falsifications

- **00-dataset:** all 194 columns now carry a family rule — `COLUMNS.md`,
  generated and asserted (13 families partition the schema, no column
  unruled, `year_gated` re-derived from PROFILE.json), enforced by a
  pre-commit hook. Gates follow a stated rule: 34 enabling predicates
  confirmed at ≤0.05% contradiction in every year, 14 rejected with the
  worst-year number — two contradicted 100% of the time. `build()`
  re-measures every gate on every year and refuses to run on drift.
- **00-dataset:** three falsifications of the morning's Silver, measured
  before fixing: the epidemiological week was derived as ISO where SIVEP
  uses MMWR (`SEM_PRI` agrees 100.00% with MMWR in all six years, ~86%
  with ISO — one record in seven in the wrong week); the influenza
  catalogue dropped `PCR_FLUASU = 3` and never consumed `TP_FLU_AN`/
  `TP_FLU_PCR`, undercounting influenza 2.1x (33,668 → 71,808); seven
  dd/mm/yyyy dates (six dose fields, `VG_DTRES`) sat unparsed behind
  non-`DT_` names.
- **00-dataset:** quality grows 21 → 84 checks and the Kahn grid's two
  empty cells close (computational, relational — the pinned IBGE table,
  with Brasília's administrative regions recognised as DATASUS
  pseudo-codes rather than flagged invalid). Checks expected to fail are
  the documentation: `RES_AN` positive with no agent identified runs at
  9–20% every year since 2020.
- **00-dataset:** the dictionary generator's prose-anchor bug is fixed at
  the root (a field name must carry an underscore and end its table row):
  28 labels recover, including the full `PCR_FLUASU` subtype domain whose
  value 3 the catalogue had been dropping. `srag_quality` had kept a
  private copy of the broken pre-fix normalisation; it is single-sourced
  now. Silver: 418 columns, 4,109,567 = 4,109,560 + 7, every year green.

## 2026-08-31 — the derived-variable catalogue, in full

- **00-dataset:** Silver now implements the Ministry's derived-variable
  catalogue in full — 141 derived columns against the 8 it had, including the
  etiology cascade with the `_obito` and co-detection-free `_unico` variants,
  `regiao`, `se_primeiro_sinto` and the investigation flags. Transcribed from
  the official R script, not the derived-variable PDF, which gives
  `adenovirus_caso` the VSR criterion.
- **00-dataset:** `soma_casos` sums the nine primitive agent flags rather than
  every `_caso` column. Summing the composites too counted a single
  metapneumovirus twice — once as `metapneumo_caso`, once inside `ovr_caso` —
  and marked the row as a co-detection on its own, zeroing the `_unico`
  variants of every agent inside `ovr`.
- **00-dataset:** the treatment notebook is split into `walkthrough` (one year,
  narrated, runs on every PR) and `internals` (all six years in a single pass).
  Measuring one year and asserting six was the recurring error; the split makes
  it structural rather than a matter of care.
- **00-dataset:** percentages state their denominator. `Series.mean()` on a
  nullable boolean silently drops the NAs from the denominator, which had the
  notebook reporting the 2021 COVID share as 73.1% — the share among records
  with an etiology filled — where the question was 70.2%.

## 2026-08-31 — security bump: pyarrow 23.0.1, pypdf 6.15.0

Two high-severity advisories against the pinned stack: a use-after-free in
pyarrow reading IPC files, and an infinite loop in pypdf on a non-terminated
inline image. The repository's policy of moving Python pins once per offering is
about version churn, not about sitting on a fix — but the discipline it demands
still applies, so every generated artefact was regenerated and diffed.

`PROFILE.md`, `PROFILE.json`, `DICTIONARY.md` and `QUALITY.md` are **byte-identical**
after the bump: pypdf 6.15 extracts the same text from the Ministry's PDF, and
pyarrow 23 reads the parquet the same way.

The Silver parquet bytes **do** change — all six files — because pyarrow also
*writes* them and a major bump moves metadata and compression defaults. Values
are unchanged, verified against the figures the notebook prints. Worth recording
as a property of the stack: parquet byte-stability holds only within a pyarrow
version, which is what the lock is for.

Modules 01-03 import neither package, so their notebooks were not affected.

## 2026-08-31 — the Silver walkthrough notebook

`modules/00-dataset/notebooks/srag_silver_walkthrough.ipynb` walks the treatment
and prints the evidence for each decision. It imports `tools/srag_silver.py`
rather than restating it, so the ~20 modules that will consume the same data
cannot drift from the code that produced it. Runs in Colab: the first cell is
the unpinned `%pip`, the data is fetched from the Ministry's public S3 bucket,
and the repository is cloned when the import is not already on the path.

The central demonstration is two lines of output:

    regra ingênua  == '1' :         0 registros
    após normalise()      :   519,518 registros

## 2026-08-31 — Silver materialised, and a loader bug that only bit on re-run

`tools/srag_silver.py` now writes one parquet per year plus its quarantine,
sorted by `NU_NOTIFIC`, and `load.py` carries both into the `silver` schema. The
invariant is checkable in SQL against the database, not only in the Python that
produced it: `bronze=4109567, silver=4109560, quarentena=7`.

`load.py` dropped each yearly table before the union view that depends on it,
so the **first** run succeeded (no view yet) and every run after it failed with
`cannot drop table ... because other objects depend on it`. The views are now
dropped first. Worth recording because a review flagged this as *probable* from
reading the code; running it twice is what turned probable into confirmed.

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
