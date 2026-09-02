# tools/

**The tens digit is the phase, the units digit is the order inside it.**
Reading order is numeric order: `10` fetches, `20` describes, `30`
transforms, `40` decides the task, `50` selects the model, `60` fits and
measures it, `70` holds the explanation kernels. `check_notebooks.py`
keeps no number — it is repo-wide, not a pipeline phase.

Scripts marked ✓ are generators with a `--check` mode enforced by
pre-commit: they re-render their committed output and fail on drift.

| Script | Phase | Reads | Writes | Check mode | Hook |
|---|---|---|---|---|---|
| [`srag_10_fetch.sh`](srag_10_fetch.sh) | 10 acquire | S3 (dadosabertos) | `~/Documents/srag-data/INFLUD*.parquet` + official PDFs | — | |
| [`srag_11_fetch_ibge.py`](srag_11_fetch_ibge.py) | 10 acquire | IBGE Localidades API | [`modules/00-dataset/reference/municipios_ibge.csv`](../modules/00-dataset/reference/municipios_ibge.csv) (pinned snapshot) | — | |
| [`srag_20_profile.py`](srag_20_profile.py) | 20 describe | Bronze (all six years — no year parameter, on purpose) | `PROFILE.md` + `PROFILE.json` | — | |
| [`srag_21_dictionary.py`](srag_21_dictionary.py) | 20 describe | official PDF + Bronze schema | `DICTIONARY.md` | — | |
| [`srag_22_quality.py`](srag_22_quality.py) | 20 describe | Bronze | `QUALITY.md` (84 Kahn checks) | — | |
| [`srag_30_silver.py`](srag_30_silver.py) | 30 transform | Bronze | **one** `silver.parquet` (4,109,567 × 420, quarantine as the `linha_deslocada` flag) — also the importable contract: `FAMILIES`, `DOMAINS`, `GATES`, `COLUMN_CLASS`, `derived_catalogue()` | — | |
| [`srag_31_columns.py`](srag_31_columns.py) | 30 transform | the contract tables + `PROFILE.json` (never a parquet) | `COLUMNS.md` — asserts 194/194 ruled and the derived catalogue both ways | `--check` ✓ | `columns-generated` |
| [`srag_32_diagrams.py`](srag_32_diagrams.py) | 30 transform | the contract tables + `PROFILE.json` + the gold/model/selection JSONs | `PIPELINE.svg`, `FUNIL.svg`, `REGIMES.svg`, `SELECTION.svg` | `--check` ✓ | `diagrams-generated` |
| [`srag_40_gold.py`](srag_40_gold.py) | 40 decide | Silver | `gold_covid_obito.parquet` (git-ignored) + `gold/MANIFEST.md` (`--manifest`) + `gold/counts.json` — every task decision a required flag | `--check-manifest` ✓ | `gold-manifest-generated` |
| [`srag_50_selection.py`](srag_50_selection.py) | 50 select | the committed sample | `gold/selection_metrics.json` (`--search`, the pre-registered study) + `SELECTION.md` (`--card`) — also home to `ece`, the calibration measure the study needs | `--check-card` ✓ | `selection-card-generated` |
| [`srag_60_model.py`](srag_60_model.py) | 60 model | the committed sample | `gold/model_metrics.json` (`--metrics`) + `MODEL.md` (`--card`) — also the importable contract the method modules share (below) | `--check-card` ✓ | `model-card-generated` |
| [`srag_70_explain.py`](srag_70_explain.py) | 70 explain | nothing (import-only) | nothing — the shared kernels of the explanation methods (below) | — | |
| [`check_notebooks.py`](check_notebooks.py) | repo-wide | `modules/*/notebooks/*.ipynb` | (exit status: the CONTRIBUTING conventions) | — | `notebook-conventions` |

Layer rule of thumb: fetch → profile/dictionary/quality read Bronze and
never write into it; `srag_30_silver.py` is the one Bronze→Silver
transformation and the single source of the column contract;
`srag_40_gold.py` is where task choices live, all of them explicit.

## A sequência

The executable chain, 10 → 70. Only **10–40** need the private Bronze
under `~/Documents/srag-data`; **50 and 60** run on the committed sample
(`modules/00-dataset/gold/gold_covid_obito_sample.parquet`), which is why
CI can re-check them; **70** is import-only and runs nothing.

```bash
bash tools/srag_10_fetch.sh          # the six parquets, straight from S3
python3 tools/srag_11_fetch_ibge.py  # the pinned IBGE municipality snapshot

python3 tools/srag_20_profile.py     # PROFILE.md + PROFILE.json
python3 tools/srag_21_dictionary.py  # DICTIONARY.md
python3 tools/srag_22_quality.py     # QUALITY.md

python3 tools/srag_30_silver.py      # the single Silver (~/Documents/srag-data/silver.parquet)
python3 tools/srag_31_columns.py     # COLUMNS.md      (--check to diff instead)
python3 tools/srag_32_diagrams.py    # the four SVGs   (--check to diff instead)

python3 tools/srag_40_gold.py --silver ~/Documents/srag-data/silver.parquet \
    --out ~/Documents/srag-data/gold --coorte hospitalizado --etiologia covid-amplo \
    --alvo obito-casos-fechados --inicio 2020-02-26 --idade todas --idade-maxima 120 \
    --idade-ausente excluir --nosocomial manter --split temporal:2022-12-31/2023/2024 \
    --amostra-treino 200000 --semente 42   # no flags: prints the menu and exits 2
python3 tools/srag_40_gold.py --manifest      # re-render gold/MANIFEST.md

python3 tools/srag_50_selection.py --search   # the pre-registered study
python3 tools/srag_50_selection.py --card     # re-render SELECTION.md
python3 tools/srag_60_model.py --metrics      # re-measure the course model
python3 tools/srag_60_model.py --card         # re-render MODEL.md
```

## What phases 60 and 70 export

`srag_60_model.py` is the contract the five method modules import as `M`:
`FEATURES` / `NUMERICAS` / `BOOLEANAS` / `CATEGORICAS` and its four family
slices `DEMOGRAFIA` / `COMORBIDADES` / `SINTOMAS` / `CONTEXTO` (slices, so
inserting a column moves them and an `assert` catches any drift),
`GRUPO_DE_FEATURE` (all 40 features → family), `fit_models`,
`predict_proba`, `pick_exemplar`, `pick_vulneravel`, `gate_impossible` and
`gate_reasons` (the same fences, decomposed into `portao` /
`pre_campanha` / `fora_coorte`).

`srag_70_explain.py` is the kernels the methods share, imported as `E`:
`perfil_cp` (module 01), `curvas_ice` (module 02) and the Gower family
`faixas_de` / `gower_matriz` / `gower_ao_vizinho` / `gower_par`
(modules 01 and 04).

**The rule the owner chose:** os núcleos dos métodos moram em
`srag_70_explain` e os walkthroughs exibem o fonte com
`inspect.getsource` — uma definição, o aluno lê o código. Internals just
call. What the shared module removes is the divergence between copies,
never the reading.

The dependency runs one way: `srag_70_explain` may import
`srag_60_model`, never the reverse — the `model-card-generated` hook runs
phase 60 in a pandas+pyarrow-only venv, and phase 60 must stay that
light. (`srag_40_gold` is imported lazily inside
`sha256_projecao_canonica` for the same reason.)

The module 00 notebooks keep their unnumbered names
(`srag_silver_walkthrough`, `srag_model_walkthrough`, …): their Colab
badges are public URLs, and a rename would break every link already
handed out.

Naming (decided and applied 2026-09-01): the scripts carry phase numbers.
The rename landed with the modules 01–05 re-sync work, because the
phase-30, -50 and -60 scripts are imported by every notebook under their
old unnumbered names, and renaming them forced the full re-run that work
already paid for. The notebooks' repo-walk sentinel moved to
`tools/README.md` at the same time: with a script-name sentinel, a missed
rename would fall through to the Colab `git clone` of `main` and silently
import the OLD module instead of failing.
