# tools/

**The tens digit is the phase, the units digit is the order inside it.**
Reading order is numeric order: `10` fetches, `20` describes, `30`
transforms, `40` decides the task, `50` selects the model, `60` fits and
measures it, `70` holds the explanation kernels and presentation export.
`check_notebooks.py`, `check_numbers.py` and `sapians.py` are repo-wide,
not pipeline phases. `srag_pfi_walkthrough.py` keeps its published import
name as a compatibility wrapper; the permutation implementation lives in
phase 70.

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
| [`srag_61_balance.py`](srag_61_balance.py) | 60 diagnose | the committed sample and fixed model configuration | a separate temporal comparison of the reference, class weights, undersampling and restricted SMOTENC; recorded predictions and metrics under the requested output directory | — | |
| [`srag_62_pfi.py`](srag_62_pfi.py) | 60 diagnose | the committed sample and reference model configuration | the historical permutation experiment, protocol and ranking under the requested output directory; importable plot builders | — | |
| [`srag_70_explain.py`](srag_70_explain.py) | 70 explain | nothing (import-only) | nothing — the shared kernels of the explanation methods (below) | — | |
| [`srag_72_pfi_presentation.py`](srag_72_pfi_presentation.py) | 70 present | the global experiment, generated module-06 teaching window and current lecture assets | separate aggregate and teaching-window payloads, or a standalone static package outside the repository | `--check` | |
| [`srag_73_teaching_demo.py`](srag_73_teaching_demo.py) | 70 demonstrate | an already fitted predictor, full temporal-test inputs/outcomes, internal receiver positions and recorded global protocol | nothing (import-only): returns the teaching window for explicit notebook promotion | — | |
| [`srag_74_metric_comparison.py`](srag_74_metric_comparison.py) | 70 compare | recorded Brier, log loss and AUC scores, plus freshly reproduced probability MAE on the same permutations | nothing (import-only): returns recomputed summaries, rankings and agreement for walkthrough §8 | — | |
| [`srag_75_pfi_figures.py`](srag_75_pfi_figures.py) | 70 illustrate | the validated log-loss presentation payload | notebook-generated ranking, equations, repeat trace and dependence figures for explicit promotion | — | |
| [`srag_pfi_walkthrough.py`](srag_pfi_walkthrough.py) | compatibility | a fitted model, evaluation inputs/outcomes and supplied row orders | nothing — forwards the historical `trace_feature` interface to the phase-70 PFI kernel | — | |
| [`check_notebooks.py`](check_notebooks.py) | repo-wide | `modules/*/notebooks/*.ipynb` | (exit status: the CONTRIBUTING conventions) | — | `notebook-conventions` |
| [`check_numbers.py`](check_numbers.py) | repo-wide | module prose + the printing cells | (exit status) — o conferidor prosa↔célula, rodado à mão | — | |
| [`sapians.py`](sapians.py) | repo-wide | [`sapians.mplstyle`](sapians.mplstyle) + [`fonts/`](fonts/) | nothing (import-only): the course's visual identity — colours, fonts, figure sizes, numbers in Portuguese | — | |

Layer rule of thumb: fetch → profile/dictionary/quality read Bronze and
never write into it; `srag_30_silver.py` is the one Bronze→Silver
transformation and the single source of the column contract;
`srag_40_gold.py` is where task choices live, all of them explicit.

## A sequência

The executable chain, 10 → 70. Only **10–40** need the private Bronze
under `~/Documents/srag-data`; **50 and 60** run on the committed sample
(`modules/00-dataset/gold/gold_covid_obito_sample.parquet`), which is why
CI can re-check them; **70** holds importable kernels, while **72** checks
and exports the PFI presentation; **73** builds its real global-repeat window.
The diagnostic studies **61–62** also use
the committed sample and do not replace the selected reference model.

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

The diagnostic studies are explicit runs, separate from selecting the course
model. Their output destination is required; use a temporary directory rather
than writing generated experiments into tracked paths:

```bash
python3 tools/srag_61_balance.py --output /tmp/srag-balance-study
python3 tools/srag_62_pfi.py --output /tmp/srag-pfi-study
python3 tools/srag_72_pfi_presentation.py --check
python3 tools/srag_72_pfi_presentation.py --output-dir /tmp/srag-pfi-presentation
```

The recorded global studies remain under module 00; the PFI lecture and its
executed notebooks live in [`modules/06-pfi/`](../modules/06-pfi/README.md).
The current teaching window is generated in walkthrough §3 by
`srag_73_teaching_demo.build_teaching_demo`. The function receives a fitted
predictor and full test matrix, reproduces the registered permutation orders
and evaluates the first order. Internal receiver positions select the same
historical teaching rows; donor values come from the entire evaluation.
Internals §5 independently reconstructs the model and checks the transport,
probabilities and first global errors.

Promote the generated teaching window explicitly to
[`modules/06-pfi/evidence/pfi_teaching_demo.json`](../modules/06-pfi/evidence/pfi_teaching_demo.json).
The old manual subset example stays unchanged in module 00 for audit.
The exporter projects this teaching evidence and the global study through
typed field allowlists into separate runtime files. It checks squared
probability losses, protocol hashes and the first global errors against the
original PFI record. The slide error chart uses global original loss,
repeated mean and sample SD; selected receiver loss is a notebook audit only.

The teaching file contains individual receiver values/outcomes/predictions
and received input values. Permuted records are artificial combinations,
rather than newly observed patient records. The aggregate JSON contains no
individual rows. Source identifiers, dates, location fields, donor positions
and donor outcomes are excluded; removing identifiers alone does not
establish anonymization. Exporting prepares a folder without publishing it.

## What phases 60 and 70 export

`srag_60_model.py` is the contract the method modules import as `M`:
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
(modules 01 and 04). Module 06 uses `permutar_colunas` and `trace_pfi`:
column movement and repeated error evaluation start from the original matrix,
preserve input types and retain the already fitted predictor. The walkthrough
shows the executed source; the internals check its behavior independently.

`srag_pfi_walkthrough.trace_feature` forwards to this shared implementation.
It preserves the older notebook's interface without maintaining a second
permutation algorithm. The historical study orchestrator `srag_62_pfi.py`
retains its filename and recorded-output format; it is not a new method module.

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

## A identidade visual

`sapians.py` é a identidade visual do curso em um import. Nos cadernos são
duas linhas na célula de setup:

```python
import sapians as SP
SP.aplicar()          # registra as fontes, aplica o estilo, cria figures_generated/
```

Os tokens são cópia verbatim de
[`sapians-latex`](https://github.com/wbendinelli/sapians-latex) `@ 4c10f27`
(`packages/typst/src/tokens.typ`, `packages/python/sapians.mplstyle`,
`packages/python/sapians_plots/theme.py`); as convenções de figura vêm de
`examples/lime-lecture/make_figures.py` do mesmo repositório. A direção é
uma só: identidade nasce lá, é copiada para cá.

### Uma cor, um significado

A regra que faz a série inteira ser legível: quem aprendeu "terracota =
óbito" no módulo 01 lê a barra terracota do módulo 05 do mesmo jeito — e
está certo.

| Constante | Hex | O significado, no curso inteiro |
|---|---|---|
| `SP.AZUL` | `#315B86` | sobrevida · φ<0 · classe 0 · a série primária |
| `SP.TERRACOTA` | `#C96F3F` | o polo adverso e o acento: óbito · φ>0 · impossível · fabricado · a anotação apontada · o kicker |
| `SP.SAGE` | `#4E8752` | possível · válido · acionável |
| `SP.AMBAR` | `#D9822B` | o segundo braço de comparações que **não** são sobre classe (logística de referência, interventional, rodada ingênua) |
| `SP.ESCURO` | `#161311` | o objeto do modelo: fronteira p=0,5, ✕ do paciente, média/PDP |
| `SP.CINZA` | `#6D675F` | nosso construto: anel do kernel, anotações, eixos |
| `SP.CINZA_CLARO` | `#A9A498` | sintético sem classe · neutro/desconhecido |

Também: `CATEGORICA` / `BINARIA` / `SEQ_AZUL` / `SEQ_TERRACOTA` /
`DIVERGENTE`, os colormaps `CMAP_INTENSIDADE` e `CMAP_DIVERGENTE`, e
`rampa(n)`. `CORES_ANO` dá os cinco anos da coorte do escuro (2020, o
regime mais letal) ao claro; `CORES_GRUPO` dá as seis famílias de
`srag_60_model.GRUPO_DE_FEATURE` — uma **taxonomia**, não uma semântica,
por isso nenhuma delas usa uma cor semântica sólida. Traço também é
vocabulário: `L_FRONTEIRA` (a fronteira do modelo), `L_KERNEL` (o kernel
que nós desenhamos), `L_REF` (andaime). Forma é procedência:
`MARCADOR_REAL` círculo = paciente real, `MARCADOR_SINTETICO` quadrado =
vizinho sintético, `MARCADOR_PACIENTE` ✕ = o paciente explicado.

### Três tamanhos, um jeito de salvar

`SP.SLOT` (9,6×5,4) para o gráfico padrão, `SP.FAIXA` (12×4) para barras
horizontais e séries largas, `SP.PAINEL` (12×8) para small multiples. Só
esses três — é o que faz figuras irmãs terem o mesmo aspecto.

```python
fig, ax = plt.subplots(figsize=SP.SLOT)
...
SP.titulo(fig, "Sobrevida cai 18 p.p. entre a 2ª e a 3ª dose", "§4 · doses")
SP.salvar(fig, "04_doses")     # figures_generated/04_doses.png, dpi 150
```

`SP.titulo` escreve o **achado**, não o nome do gráfico, com `fig.text` e
não `ax.set_title` (o `set_title` alinha ao eixo, e figuras irmãs com
rótulos de larguras diferentes começam o título em x diferentes).
`SP.salvar` aplica `tight_layout(rect=...)` reservando a banda do título,
salva **sem** `bbox_inches` (que deixaria o aspecto divergir do `figsize`)
e apaga o metadado `Software` do PNG — sem isso o arquivo muda a cada bump
do matplotlib e o diff mente sobre o que mudou.

### A escala de texto, opt-in

`SAPIANS_ESCALA_TEXTO` multiplica `font.size`, `axes.titlesize`,
`axes.labelsize`, `xtick`/`ytick.labelsize` e `legend.fontsize`. Ausente, o
fator é 1,0 e nenhum rcParam muda: os PNGs commitados continuam
byte-idênticos. Hoje só um chamador a define,
`reports/01-metodos-locais/gerar_figuras.py`, porque a figura sai do
caderno (9,6 a 12 pol.) para uma coluna de artigo de 170 mm e o rótulo de
eixo encolheria a 4 pt. `SP.titulo` (kicker e manchete) não lê a variável:
esse texto é recortado fora pelo relatório de qualquer forma.

### Números em português

`SP.pt(1234.567)` → `1.234,57`; `SP.pt(0.92, 2, sinal=True)` → `+0,92`;
`SP.pt_int(1282970)` → `1.282.970`; `SP.pct(0.373)` → `37,3%`;
`SP.pt_sig(1.05e-05)` → `1,05×10⁻⁵`; `SP.tabela(df)` formata todo float e
todo inteiro do quadro. `NaN` sai como `NA`. O menos é o hífen ASCII, não
o U+2212: a prosa é conferida por regex.

### Por que as fontes vão empacotadas

[`tools/fonts/`](fonts/) carrega quatro pesos de Inter e dois de JetBrains
Mono (~2,1 MB) sob a licença OFL 1.1. Não é preferência: a figura precisa
sair byte-idêntica no Mac do autor, no runner Linux do CI e no Colab, e o
Linux/Colab não têm Inter instalada — o matplotlib cairia no DejaVu Sans
sem erro nenhum e todo glifo mudaria. Registradas por caminho absoluto,
`SP.aplicar()` falha alto se um arquivo sumir. Detalhes e procedência em
[`fonts/README.md`](fonts/README.md).
