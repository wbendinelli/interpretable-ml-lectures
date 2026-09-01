# tools/

One prefix, one layer order. Scripts marked ✓ are generators with a
`--check` mode enforced by pre-commit: they re-render their committed
output and fail on drift.

| Script | Reads | Writes | ✓ |
|---|---|---|---|
| [`srag_fetch.sh`](srag_fetch.sh) | S3 (dadosabertos) | `~/Documents/srag-data/INFLUD*.parquet` + official PDFs | |
| [`srag_fetch_ibge.py`](srag_fetch_ibge.py) | IBGE Localidades API | [`modules/00-dataset/reference/municipios_ibge.csv`](../modules/00-dataset/reference/municipios_ibge.csv) (pinned snapshot) | |
| [`srag_profile.py`](srag_profile.py) | Bronze (all six years — no year parameter, on purpose) | `PROFILE.md` + `PROFILE.json` | |
| [`srag_dictionary.py`](srag_dictionary.py) | official PDF + Bronze schema | `DICTIONARY.md` | |
| [`srag_silver.py`](srag_silver.py) | Bronze | **one** `silver.parquet` (4,109,567 × 420, quarantine as the `linha_deslocada` flag) — also the importable contract: `FAMILIES`, `DOMAINS`, `GATES`, `COLUMN_CLASS`, `derived_catalogue()` | |
| [`srag_quality.py`](srag_quality.py) | Bronze | `QUALITY.md` (84 Kahn checks) | |
| [`srag_columns.py`](srag_columns.py) | the contract tables + `PROFILE.json` (never a parquet) | `COLUMNS.md` — asserts 194/194 ruled and the derived catalogue both ways | ✓ |
| [`srag_diagrams.py`](srag_diagrams.py) | the contract tables + `PROFILE.json` | `PIPELINE.svg`, `FUNIL.svg`, `REGIMES.svg` | ✓* |
| [`srag_gold.py`](srag_gold.py) | Silver | `gold_covid_obito.parquet` (git-ignored) + `gold/MANIFEST.md` + `gold/counts.json` — every task decision a required flag | ✓ |
| [`check_notebooks.py`](check_notebooks.py) | `modules/*/notebooks/*.ipynb` | (exit status: the CONTRIBUTING conventions) | |

\* `srag_diagrams.py --check` exists but has no pre-commit hook yet — run
it by hand when the contract changes.

Layer rule of thumb: fetch → profile/dictionary/quality read Bronze and
never write into it; `srag_silver.py` is the one Bronze→Silver
transformation and the single source of the column contract;
`srag_gold.py` is where task choices live, all of them explicit.
