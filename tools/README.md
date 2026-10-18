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
| [`srag_51_course_study.py`](srag_51_course_study.py) | 50 select | full Gold, frozen candidate protocol | external checkpoints, validation selection and one canonical predictor; test evaluated only after freezing | — | |
| [`srag_52_course_balance.py`](srag_52_course_balance.py) | 50 select | registered temporal training partition only | verified external resampling caches; matched balancing candidate configurations | — | |
| [`srag_53_sample_balance_search.py`](srag_53_sample_balance_search.py) | 50 compare | exact committed training sample, full temporal validation/test | independent XGBoost tuning per balancing strategy, frozen finalists and audited aggregate evidence | — | |
| [`srag_54_sample_family_search.py`](srag_54_sample_family_search.py) | 50 select | same committed sample and temporal validation/test; optional audited plain XGBoost checkpoints | family-specific hyperparameter search by validation log loss, frozen finalists and scoped aggregate evidence | — | |
| [`srag_60_model.py`](srag_60_model.py) | 60 model | the committed sample | `gold/model_metrics.json` (`--metrics`) + `MODEL.md` (`--card`) — also the importable contract the method modules share (below) | `--check-card` ✓ | `model-card-generated` |
| [`srag_61_balance.py`](srag_61_balance.py) | 60 diagnose | the committed sample and fixed model configuration | a separate temporal comparison of the reference, class weights, undersampling and restricted SMOTENC; recorded predictions and metrics under the requested output directory | — | |
| [`srag_62_pfi.py`](srag_62_pfi.py) | 60 diagnose | the committed sample and reference model configuration | the historical permutation experiment, protocol and ranking under the requested output directory; importable plot builders | — | |
| [`srag_63_course_reference.py`](srag_63_course_reference.py) | 60 load | the finalized full-training selection and fitted artifact | nothing — a verified raw-input predictor, without fitting or fallback | — | |
| [`srag_64_course_evidence.py`](srag_64_course_evidence.py) | 60 document | the frozen full-training study and saved predictions | public aggregate evidence, after independently recomputing validation and test metrics | — | |
| [`srag_70_explain.py`](srag_70_explain.py) | 70 explain | nothing (import-only) | nothing — the shared kernels of the explanation methods (below) | — | |
| [`srag_71_global_effects.py`](srag_71_global_effects.py) | 70 explain | fixed predictor and typed explanation frames | nothing — empirical PDP/ICE, numeric ALE, pairwise H and weighted surface decomposition | — | |
| [`srag_72_pfi_presentation.py`](srag_72_pfi_presentation.py) | 70 present | the global experiment, generated module-10 teaching window and current lecture assets | separate aggregate and teaching-window payloads, or a standalone static package outside the repository | `--check` | |
| [`srag_73_teaching_demo.py`](srag_73_teaching_demo.py) | 70 demonstrate | an already fitted predictor, full temporal-test inputs/outcomes, internal receiver positions and recorded global protocol | nothing (import-only): returns the teaching window for explicit notebook promotion | — | |
| [`srag_74_metric_comparison.py`](srag_74_metric_comparison.py) | 70 compare | recorded Brier, log loss and AUC scores, plus freshly reproduced probability MAE on the same permutations | nothing (import-only): returns recomputed summaries, rankings and agreement for walkthrough §8 | — | |
| [`srag_75_pfi_figures.py`](srag_75_pfi_figures.py) | 70 illustrate | the validated log-loss presentation payload | notebook-generated ranking, equations, repeat trace and dependence figures for explicit promotion | — | |
| [`srag_76_course_pfi.py`](srag_76_course_pfi.py) | 70 explain | the sole finalized full-training predictor and complete temporal test | verified external PFI checkpoints and aggregate repeated log-loss results, without retraining | — | |
| [`srag_pfi_walkthrough.py`](srag_pfi_walkthrough.py) | compatibility | a fitted model, evaluation inputs/outcomes and supplied row orders | nothing — forwards the historical `trace_feature` interface to the phase-70 PFI kernel | — | |
| [`check_notebooks.py`](check_notebooks.py) | repo-wide | `modules/*/notebooks/*.ipynb` | (exit status: the CONTRIBUTING conventions) | — | `notebook-conventions` |
| [`check_numbers.py`](check_numbers.py) | repo-wide | module prose + the printing cells | (exit status) — o conferidor prosa↔célula, rodado à mão | — | |
| [`sapians.py`](sapians.py) | repo-wide | [`sapians.mplstyle`](sapians.mplstyle) + [`fonts/`](fonts/) | nothing (import-only): the course's visual identity — colours, fonts, figure sizes, numbers in Portuguese | — | |

Layer rule of thumb: fetch → profile/dictionary/quality read Bronze and
never write into it; `srag_30_silver.py` is the one Bronze→Silver
transformation and the single source of the column contract;
`srag_40_gold.py` is where task choices live, all of them explicit.

## A comparação atual na amostra

O executor `53` mantém a amostra registrada e compara original, pesos,
redução e SMOTENC restrito com configurações próprias de XGBoost. Cada
estratégia recebe a mesma lista declarada de candidatos; o menor log loss
de validação escolhe os finalistas e o vencedor. A referência conserva os
hiperparâmetros originais, reconstruídos com o pré-processamento declarado;
não se presume igualdade com as previsões antigas.

```bash
python tools/srag_53_sample_balance_search.py --prepare --data modules/00-dataset/gold/gold_covid_obito_sample.parquet --output-dir /estudos/balanceamento-amostra
python tools/srag_53_sample_balance_search.py --search --data modules/00-dataset/gold/gold_covid_obito_sample.parquet --output-dir /estudos/balanceamento-amostra
python tools/srag_53_sample_balance_search.py --finalize --data modules/00-dataset/gold/gold_covid_obito_sample.parquet --output-dir /estudos/balanceamento-amostra
python tools/srag_53_sample_balance_search.py --evaluate --data modules/00-dataset/gold/gold_covid_obito_sample.parquet --output-dir /estudos/balanceamento-amostra
python tools/srag_53_sample_balance_search.py --export --output-dir /estudos/balanceamento-amostra --output modules/00-dataset/gold/sample_balance_search.json
```

A preparação registra os dados, a grade, as fontes e o ambiente antes dos
ajustes. A busca retoma candidatos íntegros e prepara cada reamostragem uma
vez. A finalização exige a conclusão do orçamento inteiro. A avaliação compara
os finalistas já congelados e a referência no teste exploratório, sem reescolher
o modelo. A exportação recalcula as métricas a partir das previsões locais
antes de publicar o agregado; não exporta os arrays individuais ou os modelos.

Essa é uma busca finita de parâmetros do XGBoost. A receita de pesos, a
proporção da reamostragem e a semente permanecem declaradas, sem otimização
irrestrita de todas as etapas e sem recalibração posterior.

O [agregado concluído](../modules/00-dataset/gold/sample_balance_search.json)
é lido pelo [walkthrough](../modules/00-dataset/notebooks/srag_sample_balance_walkthrough.ipynb)
e pelo [internals](../modules/00-dataset/notebooks/srag_sample_balance_internals.ipynb).
O resultado e a definição de elegível estão em
[COURSE_STUDY.md](../modules/00-dataset/COURSE_STUDY.md).

## Famílias selecionadas por log loss na mesma amostra

O executor `54` compara as famílias sem pesos ou reamostragem, com preparação
aprendida somente no treino. Usa os espaços e orçamentos declarados por família,
seleciona pelo log loss de validação em precisão integral e congela todos os
finalistas antes da avaliação exploratória no teste. Constante e OLS são
referências sem tuning; OLS conserva o clipping declarado. Não há recalibração.

```bash
python tools/srag_54_sample_family_search.py --prepare --data modules/00-dataset/gold/gold_covid_obito_sample.parquet --output-dir /estudos/familias-amostra
python tools/srag_54_sample_family_search.py --search --data modules/00-dataset/gold/gold_covid_obito_sample.parquet --output-dir /estudos/familias-amostra
python tools/srag_54_sample_family_search.py --finalize --data modules/00-dataset/gold/gold_covid_obito_sample.parquet --output-dir /estudos/familias-amostra
python tools/srag_54_sample_family_search.py --evaluate --data modules/00-dataset/gold/gold_covid_obito_sample.parquet --output-dir /estudos/familias-amostra
python tools/srag_54_sample_family_search.py --export --data modules/00-dataset/gold/gold_covid_obito_sample.parquet --output-dir /estudos/familias-amostra --output modules/00-dataset/gold/sample_family_search.json
```

Opcionalmente, a preparação recebe `--import-xgb-study /estudos/balanceamento-amostra`.
O reuso exige prova de igualdade do contrato e das métricas dos checkpoints
sem balanceamento do executor `53`. Sem essa opção, todas as configurações
são ajustadas novamente. A importação é registrada antes da busca; nenhum
resultado arredondado da seleção histórica substitui um ajuste ou checkpoint.

O agregado é lido pelo
[walkthrough de famílias](../modules/00-dataset/notebooks/srag_sample_family_walkthrough.ipynb)
e pelo [internals](../modules/00-dataset/notebooks/srag_sample_family_internals.ipynb).
Esta seleção e o balanceamento do XGBoost têm perguntas diferentes, e nenhuma
delas renomeia automaticamente a referência usada nos módulos de explicação.

## O estudo interrompido com treino completo

A decisão de manter a amostra e o registro da interrupção estão em
[COURSE_STUDY.md](../modules/00-dataset/COURSE_STUDY.md). O protocolo completo
permanece reproduzível como estudo distinto; as etapas abaixo não são a
comparação atual.
O runner `51` exige a Gold completa e um diretório de saída externo; a amostra
histórica é recusada. `--prepare` registra os dados, as versões, as grades e a
regra de menor log loss antes dos ajustes. `--plain` e `--balance` usam apenas
validação para comparar; `--finalize` exige todos os candidatos concluídos e
congela o artefato; `--evaluate` aplica esse preditor ao teste já observado.

O helper `52` recebe apenas treino e prepara pesos, redução ou SMOTENC restrito.
Seu cache não contém dados da avaliação. Os artefatos locais não são um novo
serviço nem um registro remoto; são arquivos reprodutíveis do estudo. O modelo
histórico e as medidas antigas não são substituídos por renomeação.

Na pilha fixada, a sequência explícita é a seguinte. Os caminhos de dados,
modelos, previsões individuais e caches devem ficar fora deste repositório;
somente a projeção agregada é promovida aos materiais públicos.

```bash
python tools/srag_51_course_study.py --prepare --data /dados/gold.parquet --output-dir /estudos/curso
python tools/srag_51_course_study.py --plain --data /dados/gold.parquet --output-dir /estudos/curso
python tools/srag_51_course_study.py --balance --data /dados/gold.parquet --output-dir /estudos/curso
python tools/srag_64_course_evidence.py --study-dir /estudos/curso --output /estudos/curso/evidence-checked.json
python tools/srag_51_course_study.py --finalize --data /dados/gold.parquet --output-dir /estudos/curso
python tools/srag_51_course_study.py --evaluate --data /dados/gold.parquet --output-dir /estudos/curso
python tools/srag_64_course_evidence.py --study-dir /estudos/curso --output modules/00-dataset/gold/course_study_v2.json
python tools/srag_76_course_pfi.py --study-dir /estudos/curso --data /dados/gold.parquet --output-dir /estudos/pfi
```

Os estágios de busca retomam candidatos completos do mesmo protocolo; não
devem rodar concorrentemente sobre o mesmo diretório. Um protocolo finalizado
não aceita continuar a busca. Abrir os novos cadernos do estudo lê a evidência
agregada e não dispara novamente os ajustes completos.

O loader `63` é a interface para novas análises. Recebe o diretório da seleção
concluída e retorna o pipeline já ajustado, com verificação de modelo, fontes,
ambiente e esquema. As entradas são as colunas brutas nomeadas, não uma matriz
codificada por outro notebook:

```python
from srag_63_course_reference import load_reference

reference = load_reference("/estudos/curso")
probabilities = reference.predict_proba(raw_inputs)
death_probability = probabilities[:, 1]
provenance = reference.provenance
```

Para um método que exija os valores codificados e o estimador interno, use
`reference.encoded_inputs(raw_inputs)` e `reference.estimator`, mantendo os
rótulos de `reference.encoded_feature_names`. Não encaminhe o wrapper novo ao
helper histórico que escolhe a codificação pela classe Python do estimador.
Os módulos históricos só adotam a nova versão depois de recalcular e conferir
suas próprias explicações; o relatório distingue essa migração da seleção.

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
executed notebooks live in [`modules/10-pfi/`](../modules/10-pfi/README.md).
The current teaching window is generated in walkthrough §3 by
`srag_73_teaching_demo.build_teaching_demo`. The function receives a fitted
predictor and full test matrix, reproduces the registered permutation orders
and evaluates the first order. Internal receiver positions select the same
historical teaching rows; donor values come from the entire evaluation.
Internals §5 independently reconstructs the model and checks the transport,
probabilities and first global errors.

Promote the generated teaching window explicitly to
[`modules/10-pfi/evidence/pfi_teaching_demo.json`](../modules/10-pfi/evidence/pfi_teaching_demo.json).
The old manual subset example stays unchanged in module 00 for audit.
The exporter projects this teaching evidence and the global study through
typed field allowlists into separate runtime files. It checks squared
probability losses, protocol hashes and the first global errors against the
original PFI record. The slide error chart uses global original loss,
repeated mean and sample SD; selected receiver loss is a notebook audit only.

The final subgroup slide has its own aggregate companion, projected from
[module 10 internals §7](../modules/10-pfi/notebooks/pfi_internals.ipynb).
It records diabetes shuffling freely and within heart-disease groups on the
same known-response subset. Its own original loss stays separate from the
complete-test baseline. The exporter checks its typed fields, repeated-loss
summaries and subgroup weighting before copying it explicitly.

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
(modules 01 and 04). Module 10 uses `permutar_colunas` and `trace_pfi`:
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

`sapians.py` reúne os perfis visuais e os formatadores do curso. Os cadernos
revisados escolhem o perfil Global na célula de setup:

```python
import sapians as SP
SP.aplicar(tema="global")  # registra fontes, aplica o perfil, cria figures_generated/
```

O default `SP.aplicar()` continua selecionando o perfil histórico `curso`;
essa compatibilidade não foi alterada. Os tokens desse perfil vieram de
[`sapians-latex`](https://github.com/wbendinelli/sapians-latex) `@ 4c10f27`
(`packages/typst/src/tokens.typ`, `packages/python/sapians.mplstyle`,
`packages/python/sapians_plots/theme.py`); as convenções de figura vêm de
`examples/lime-lecture/make_figures.py` do mesmo repositório. A procedência
atual do perfil Global está [abaixo](#perfil-global-sapians--vita).

### Paleta do perfil histórico

A tabela registra o vocabulário do perfil `curso` e dos artefatos produzidos
com ele. Nos gráficos revisados, rótulos, traços e marcadores explicitam as
séries; a seleção de `tema="global"` redefine os papéis neutros e a rampa
de intensidade, sem apagar as constantes clínicas históricas.

| Constante | Hex no perfil `curso` | Significado histórico |
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
`axes.labelsize`, `xtick`/`ytick.labelsize` e `legend.fontsize`. Ausente, não
aplica multiplicação adicional aos tamanhos do perfil escolhido.
`SP.titulo` (kicker e manchete) não lê essa variável.

O consumidor registrado é o script histórico
`reports/01-metodos-locais/gerar_figuras.py`, que ampliava o texto antes de
recortar o cabeçalho para a coluna do artigo. Esse script pertence à revisão
entregue e espera a antiga localização das saídas dos notebooks. Não deve
regenerar as figuras entregues a partir dos cadernos atuais; veja o
[estado dos relatórios](../reports/README.md#figures).

### Números em português

`SP.pt(1234.567)` → `1.234,57`; `SP.pt(0.92, 2, sinal=True)` → `+0,92`;
`SP.pt_int(1282970)` → `1.282.970`; `SP.pct(0.373)` → `37,3%`;
`SP.pt_sig(1.05e-05)` → `1,05×10⁻⁵`; `SP.tabela(df)` formata todo float e
todo inteiro do quadro. `NaN` sai como `NA`. O menos é o hífen ASCII, não
o U+2212: a prosa é conferida por regex.

### Por que as fontes vão empacotadas

[`tools/fonts/`](fonts/) carrega quatro pesos de Inter e dois de JetBrains
Mono (~2,1 MB) sob a licença OFL 1.1. O registro explícito evita depender de
uma instalação do sistema ou de uma substituição silenciosa pelo matplotlib.
Com o registro de fontes habilitado, `SP.aplicar()` falha se um arquivo
empacotado sumir. O perfil Global permite também a instalação local de
Satoshi descrita abaixo. A fonte é uma das condições da reprodução visual;
o CI executa os notebooks, mas não compara PNGs byte a byte. Detalhes e
procedência em [`fonts/README.md`](fonts/README.md).

## Global feature effects

`srag_71_global_effects.py` holds the kernels for modules 06–09. It accepts a
scalar prediction function, preserves native categories when replacing inputs,
and never fits a predictor or uses outcomes. `pd_empirica` integrates over a
shared background; `ale_numerica` uses quantile intervals and count-weighted
step centering; `h_par` evaluates centered PDs at observed pairs and exposes
its numerator and denominator, returning NaN when the latter degenerates.
`decompor_superficie` decomposes a finite table under explicitly supplied
product weights. Its variance identity concerns that table and product
measure, rather than the observed joint population or the full predictor.

The walkthroughs display the kernels they execute. The internals compare PDP
with scikit-learn brute integration and validate the other definitions using
independent calculations, analytic controls and edge cases. Figures are
produced outside the repository and promoted by explicit copy.

## Perfil global SAPIANS / VITA

Os notebooks principais dos métodos, do módulo 01 ao 10, optam por
`SP.aplicar(tema="global")`.
O padrão `SP.aplicar()` conserva o perfil histórico `curso`. Os papéis
do perfil Global vieram de `sapians-xreset`, revisão
`9ba10c63e985be8d12f8019e8ee3b00e2dfe031e`,
`packages/foundation-design-system/src/web/brand.css` e seu README; foram
conferidos com `sapians-design-vita`, revisão
`eaf91b9f92c9ea2b4c6414527f1b943142bf78ed`,
`src/content/design-system.json`. São referências de design, não instruções
operacionais importadas para este repositório.

O perfil usa preto SAPIANS `#212322`, branco, composição `#F2F3F3`, texto
secundário `#606460` e bordas `#D9DCDA`. Figuras científicas usam tons neutros,
traços e marcadores; terracota não é acrescentada como decoração. As cores
clínicas históricas permanecem disponíveis para os artefatos que as utilizam;
sua existência não determina a paleta de cada gráfico revisado.

Cada figura tem um título principal de figura, separado dos títulos dos
painéis. No perfil Global, `SP.titulo` mede e quebra a manchete pela largura
disponível; `SP.salvar` reserva o espaço do cabeçalho e dos subtítulos antes
de ajustar os eixos. A hierarquia visual deve ser conferida na imagem
exportada, inclusive quando a figura usa margens próprias para legendas.

Os diagramas ativos do módulo 00 usam esses mesmos papéis, com texto SVG
nativo e a cadeia explícita `Satoshi, Inter, Arial, sans-serif`. A fonte
efetiva depende do leitor do SVG; para exportação consistente, use a mesma
instalação de fontes. Os diagramas trazem título, descrição acessível,
fonte dos números e contexto da medição. O gerador
`srag_32_diagrams.py --check` confere a figura contra os artefatos registrados;
não refaz os estudos. Tons diferentes não substituem rótulos e escalas.

A UI atual da fundação usa Satoshi. Na adoção do perfil pelos
módulos 06–09, foi usada uma instalação local dos arquivos originais
`Satoshi-Regular.otf`, `Satoshi-Medium.otf` e `Satoshi-Bold.otf`, sem conversão.
Os binários não são redistribuídos neste repositório. Com uma instalação
obtida sob os [termos da Fontshare](https://www.fontshare.com/licenses),
defina `SAPIANS_SATOSHI_DIR` para a pasta desses arquivos antes de abrir o
kernel. A revisão da referência acima identifica os arquivos utilizados.

Sem essa variável, o perfil usa explicitamente a Inter empacotada sob OFL;
o caderno imprime a família selecionada. Essa é a opção do CI e do Colab
sem configuração local de Satoshi. Os valores científicos são os mesmos, mas os pixels e as métricas
tipográficas diferem: comparar PNGs byte a byte exige a mesma opção de
fonte, o mesmo ambiente e a mesma revisão dos arquivos. Uma pasta Satoshi
informada e incompleta produz erro, em vez de cair silenciosamente em outra
família. A configuração é feita antes da primeira figura, em kernel novo.
