# GOLD.md — the decision menu

Silver states facts; Gold makes task choices. This file is the menu of
those choices, each with the measured evidence, a recommendation, and an
owner. **None of them is taken here.** Until they are, no module trains a
model on this base — and that abstention is what lets ~20 modules share
one Silver.

Every number below is printed by a committed notebook cell: the per-year
table lives in [internals §7](notebooks/srag_silver_internals.ipynb), the
population profile in internals §1, and the leakage classes in
[`COLUMNS.md`](COLUMNS.md), which is generated and asserted.

## Decision 1 — the target

Owner: **William + the course**. Three candidates, with their rates inside
the hospitalized cohort (internals §7):

| Candidate | Definition | Rate 2020 → 2024 | What to watch |
|---|---|---|---|
| Death | `EVOLUCAO == 2` on closed cases | 27.2% → 6.7% | 7–11% of records never close (`EVOLUCAO` blank/9): "closed cases" is itself a cohort choice, and it censors differently by year |
| ICU admission | `UTI == 1` | 29.6% → 27.6% | the most stable rate across regimes; but `UTI` blank is 4–15% and `DT_ENTUTI` is gated on it |
| Invasive ventilation | `SUPORT_VEN == 1` | 14.9% → 9.6% | three-valued field (invasive/non-invasive/none); collapsing it is already a modelling choice |

Recommendation: **death on closed cases**, because it is the outcome the
official product counts (every `_obito` variant exists to be compared
against), and because its regime drift (27.2% → 6.7%) is the course's
teaching material, not a nuisance. Whatever is chosen: `EVOLUCAO` is the
label and never a feature — it heads the leakage class.

## Decision 2 — the cohort

Owner: **William + the course**.

| Option | Size (6 years) | For | Against |
|---|---|---|---|
| `coorte_hospitalizado` | 2,428,696 (59.1% of records) | the MS case definition minus its outcome circularity (`caso_srag_ms` admits 24,475 rows only because the patient died) | drops non-hospitalized notifications |
| full SRAG | 4,109,567 | nothing dropped | mixes notification pathways; symptom fields drive membership elsewhere anyway |
| `covid_caso` only | 723,677 in 2020 → 31,986 in 2024 | the pandemic question | the base's own etiology is broader, and the course decision (recorded 2026-08-31) was to keep the base whole and treat COVID's atypicality as context |

Recommendation: **`coorte_hospitalizado`**, with the year kept as an
explicit column so regime is modelled or stratified, never hidden.

## Decision 3 — the leakage exclusion

Owner: **convention — proposed default, generated, not typed.**

The class annotations make this list *generable*: 11 raw columns carry
`class = leakage` in `COLUMNS.md` (`EVOLUCAO`, `DT_EVOLUCA`, `DT_ENCERRA`,
`UTI`, `DT_ENTUTI`, `DT_SAIDUTI`, `SUPORT_VEN`, `CLASSI_FIN`, `CLASSI_OUT`,
`CRITERIO`, `VG_ENC`), and 39 derived columns inherit it (the 36 `_obito*`
variants, `dias_uti`, `dias_ate_internacao`, `caso_srag_ms`). If the target
is ICU or ventilation instead of death, the list *changes* — `UTI` becomes
the label, and everything downstream of admission moves — which is exactly
why the exclusion must be derived from the target choice, not copied.

Measured and deliberately **not** on the list: `DT_DIGITA` — 63–69% of
cases close *after* data entry in every year, so entry date does not
encode the outcome.

## Decision 4 — years and split

Owner: **William + the course**.

The population is not stationary: lethality 29.0% → 8.6%, COVID share
70.2% → 11.6%, median age 5 → 60 → 7 across the regimes (module README;
internals §1). Options:

1. **Temporal holdout** — train ≤ 2023, test 2024. Honest deployment
   analogy; the drift becomes a finding the interpretability modules can
   show. *(Recommended.)*
2. Within-year stratified splits — i.i.d. illusion, but useful for
   method-mechanics modules that need it.
3. Regime-restricted (e.g. 2023–2024 only) — rejected once already for
   the base (decision recorded: keep the base raw), but available per
   module if a question demands it.

## Decision 5 — encoding

Owner: **convention — proposed defaults.**

- The three missing states are **categories**, never silently imputed:
  `nao_aplicavel` is information (the funnel), not absence.
- Checkboxes enter as booleans (`_marcado`); the `_caso` flags are
  facts and may enter; `_unico` variants are for surveillance-style
  counting, not features.
- `year_gated` columns are calendars in disguise (21 of them): excluded
  by default, or kept only with the year explicitly present so the model
  cannot use form-availability as a proxy.
- `code_pair`: keep the code side (joinable), drop the name side.
- `free_text` and `identifier`: excluded. `FAB_*` enters through
  `_fabricante` (8-value vocabulary), never raw.
- Age: `idade_anos` (date-derived). `NU_IDADE_N` without `TP_IDADE` is a
  known trap; `COD_IDADE` is an exact identity of the other two — one of
  the redundancy pairs the importance-based modules will feature.

## What Gold will materialize

One parquet per decision-set, named for its choices (e.g.
`gold_obito_hosp_2019-2023_train.parquet`), built by a `tools/srag_gold.py`
that takes the decisions as explicit arguments and writes a manifest of
them next to the data. That tool is written **after** decisions 1–4 are
made — writing it before would be deciding by default.
