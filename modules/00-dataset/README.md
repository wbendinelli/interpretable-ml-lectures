# Módulo 00 — a base SRAG / SIVEP-Gripe

**4.109.567 notificações** de Síndrome Respiratória Aguda Grave, **194
colunas**, **2019–2024** — os microdados públicos do Ministério da Saúde que
servem de base para todos os módulos deste curso. Este módulo não explica
modelo nenhum: ele **entende, trata e documenta a base**, uma vez, para que
os ~20 módulos de interpretabilidade que vêm depois compartilhem o mesmo
chão e nenhum precise reinventar (nem esconder) uma limpeza.

A regra de ouro do repositório vale dobrado aqui: **todo número citado em
prosa é impresso por uma célula de notebook commitada**. Quando uma medição
contradisse o texto, o texto mudou e o valor antigo ficou registrado como
corrigido — este módulo carrega várias dessas correções, de propósito.

## O mapa

![Bronze → Prata → Ouro](PIPELINE.svg)

A arquitetura é o **medalhão** (Databricks), com uma regra que decide onde
cada coisa mora:

| Camada | O que é | O teste |
|---|---|---|
| **Bronze** | o download, byte a byte, nunca alterado | "é o que foi publicado?" |
| **Prata** | fatos sobre o registro: tipos, domínios, estados do vazio, derivadas | "esse valor é determinado pelo registro sozinho?" |
| **Ouro** | escolhas de tarefa: alvo, coorte, exclusões, split | "esse valor depende do que queremos prever?" |

`idade_anos` e `covid_caso` são determinados pelo registro → Prata.
`y_obito` e a lista de exclusão dependem da tarefa → Ouro. As caixas do
Ouro no mapa são **tracejadas** porque essas decisões estão abertas — o
cardápio delas, com evidência e recomendação, é o [`GOLD.md`](GOLD.md).

## A lição central: um vazio não é uma coisa só

![A variável-funil](FUNIL.svg)

A ficha do SIVEP **desliga campos** condicionalmente: quando `FATOR_RISC`
não declara fator de risco, as 13 comorbidades nem são apresentadas.
Medimos esse portão nos seis anos: **0,00% de contradição, sem uma exceção**
— nenhum registro marca comorbidade com o portão fechado. Por isso o Prata
separa três leituras do vazio e nunca as funde:

- `nao_aplicavel` — o campo foi desligado pelo funil. **Não é dado
  faltante**; é a maior fatia (CARDIOPATI 2023: 55,0% dos registros).
- `ausente` — o campo estava habilitado e ficou em branco (24,0% dos
  habilitados). Isto sim é ausência.
- `ignorado` — código 9, alguém registrou que não sabe. Informação.

Tratar todo vazio como ausência infla a estatística de dado faltante por
**1,8× a 5,7× conforme o ano** (internals §4) — e imputar por cima disso
inventa pacientes clinicamente impossíveis. Essa mesma estrutura é o
argumento do curso inteiro: os métodos que perturbam features de forma
independente (capítulos 12–14, 19, 23 do Molnar…) tropeçam exatamente aqui,
e o [`ROADMAP.md`](../../ROADMAP.md) organiza os módulos em torno disso.

O precedente virou regra geral (a **regra-G**): um predicado de habilitação
só é adotado se a contradição ficar ≤ 0,05% em **cada** um dos seis anos.
**34 portões passaram; 14 predicados documentados no dicionário foram
rejeitados com o número que os rejeitou** — dois deles contraditos 100% das
vezes. O `build()` re-mede cada portão adotado em cada ano que processa e
se recusa a rodar se o limite gravado quebrar.

## A base muda de problema no meio da série

![Os regimes](REGIMES.svg)

| Ano | Registros | Letalidade bruta | Fração COVID |
|---|---:|---:|---:|
| 2019 | 48.961 | 12,1% | 0,0% |
| 2020 | 1.206.920 | 29,0% | 59,8% |
| 2021 | 1.745.672 | 28,9% | 70,2% |
| 2022 | 560.577 | 19,0% | 42,9% |
| 2023 | 279.453 | 9,9% | 18,0% |
| 2024 | 267.984 | 8,6% | 11,6% |

Letalidade bruta = óbitos ÷ (curas + óbitos), sem `9-Ignorado` e sem
vazios; fração COVID = `CLASSI_FIN = 5` sobre os registros do ano. A idade
mediana vai de 5,8 anos (2019) a 60,7 (2020) e volta a 8,0 (2024,
internals §6): em tempo normal SRAG é doença pediátrica — bronquiolite —
e sob COVID virou doença de idoso. Um modelo treinado na série inteira aprende, entre outras
coisas, **em que ano o paciente adoeceu**. Isso não é defeito: é contexto
que o Ouro declara e que os módulos de interpretabilidade vão revelar.

## O que o tratamento garante (e como se verifica)

1. **Nenhuma linha some.** Bronze = Prata + quarentena, linha a linha:
   4.109.567 = 4.109.560 + 7. As 7 em quarentena são linhas fisicamente
   deslocadas (a coluna `UTI` carrega nome de hospital); uma varredura
   independente confirmou que **não há oitava** — toda célula com cara de
   data em coluna codificada está numa dessas 7 linhas.
2. **Normalização antes de qualquer domínio.** 2020 escreve `'1.0'` onde
   os outros anos escrevem `'1'`; `RAIOX_RES` chega como `2.0000000000`
   nos seis anos. Uma regra literal perderia 519.518 positivos de
   `PCR_SARS2` em 2020 **sem mudar a contagem de linhas** — o jeito mais
   silencioso de destruir dado.
3. **194/194 colunas com regra, e isso é verificado, não prometido.** O
   [`COLUMNS.md`](COLUMNS.md) é gerado das tabelas do código e **o build
   falha** se uma coluna ficar sem regra, se as 13 famílias deixarem de
   particionar o esquema, ou se a lista de colunas year-gated divergir da
   medição. Um hook de pre-commit re-renderiza e diffa.
4. **Sujeira fica visível, nunca é reparada em silêncio.** Datas como
   `1695-06-14 02:32:37.742690304` (literal no parquet de 2020), 20
   idades negativas, `CS_GESTANT = 0` nos seis anos — tudo flagrado por
   checagem, nada sobrescrito.
5. **224 colunas derivadas** (Prata = 418): 32 datas parseadas (seis datas
   de dose escondem dd/mm/aaaa sem prefixo `DT_`), 18 checkboxes, 47
   estados do vazio, o catálogo oficial de etiologia completo (20 `_caso`,
   20 `_obito`, 40 `_unico`), fabricante de vacina harmonizado, referencial
   IBGE (com as regiões administrativas do DF reconhecidas como
   pseudo-códigos DATASUS, não marcadas inválidas), idade ciente da
   unidade, e a semana epidemiológica **MMWR** — verificada em 100,00%
   contra o gabarito `SEM_PRI` da própria base, nos seis anos.

### Correções registradas (barra de evidência, regra 3)

O Prata da manhã de 2026-08-31 foi falsificado três vezes à tarde, por
medição, e os valores antigos ficam no registro:

- **A semana era ISO.** `se_primeiro_sinto` usava `isocalendar().week`;
  o SIVEP usa a semana MMWR (domingo). ISO concorda com o gabarito em só
  ~86% — **1 registro em cada 7 estava na semana errada**.
- **Influenza subcontada 2,1×.** O catálogo derrubava `PCR_FLUASU = 3`
  ("não subtipado") e nunca consumia `TP_FLU_AN`/`TP_FLU_PCR`: 33.668
  casos onde a definição oficial conta **71.808**.
- **Sete datas eram texto.** As seis datas de dose e `VG_DTRES` não têm
  prefixo `DT_` e ficaram sem parse no primeiro Prata.

## Validação externa: reproduzir a Fiocruz

O [notebook de validação](notebooks/srag_infogripe_validation.ipynb)
reconstrói a série semanal nacional do **InfoGripe** (Fiocruz/PROCC + FGV +
MS) a partir do nosso Prata. A série pública congela em 2019, e nessa
janela o ajuste **identifica a definição de caso deles** (a pré-2021 exige
febre: mediana semanal de 3,5% contra 8,2% sem febre) e fecha em
**correlação 0,9997** nas semanas estáveis — mediana de 28 casos/semana de
diferença (3,3%), 27 UFs com correlação mediana 0,997. O repositório
autoritativo (`gitlab.fiocruz.br/marcelo.gomes/infogripe`) está com acesso
anônimo bloqueado em 2026-08; criar conta lá é o caminho de upgrade para
validar os anos pandêmicos.

## Documentos gerados (nunca editados à mão)

| Documento | O que responde | Gerador |
|---|---|---|
| [`DICTIONARY.md`](DICTIONARY.md) | o que cada campo significa, com domínio oficial e preenchimento medido por ano | [`build_srag_dictionary.py`](../../tools/build_srag_dictionary.py) |
| [`PROFILE.md`](PROFILE.md) / [`PROFILE.json`](PROFILE.json) | que valores cada coluna carrega de fato, em cada ano, sem normalizar | [`srag_profile.py`](../../tools/srag_profile.py) |
| [`COLUMNS.md`](COLUMNS.md) | o contrato: família, regra, semântica do vazio, classe e portão das 194 cruas, e o **label de definição das 224 derivadas** (com proveniência: linha do script do MS, ou deste módulo) — verificado no build nos dois sentidos | [`build_srag_columns.py`](../../tools/build_srag_columns.py) |
| [`QUALITY.md`](QUALITY.md) | as 84 checagens no framework de [Kahn et al. (2016)](https://doi.org/10.13063/2327-9214.1244) — as que falham são documentação | [`srag_quality.py`](../../tools/srag_quality.py) |
| [`PIPELINE.svg`](PIPELINE.svg) · [`FUNIL.svg`](FUNIL.svg) · [`REGIMES.svg`](REGIMES.svg) | os três diagramas desta página | [`srag_pipeline_svg.py`](../../tools/srag_pipeline_svg.py) |
| [`GOLD.md`](GOLD.md) | o cardápio de decisões do Ouro, com evidência e dono | escrito à mão, números apontam células |

Por que Kahn? O livro do Molnar não tem capítulo de preparação de dados —
o capítulo 5 descreve os datasets dele sem enunciar princípio — então o
tratamento se ancora fora: cada checagem é *Conformance* (a representação
obedece à definição?), *Completeness* (os atributos estão presentes?) ou
*Plausibility* (os valores são críveis?), por *Verification* (expectativa
interna) ou *Validation* (referência externa). Deitar os achados na
taxonomia mostrou células vazias — unicidade nunca tinha sido checada, e
depois computacional e relacional — e cada célula vazia virou checagem.

## Notebooks

| Caderno | Pergunta | Escopo |
|---|---|---|
| [`srag_silver_walkthrough`](notebooks/srag_silver_walkthrough.ipynb) | *como* cada família é tratada, com a evidência de cada decisão | 2023, roda em todo PR |
| [`srag_silver_internals`](notebooks/srag_silver_internals.ipynb) | *o que muda entre os anos* — toda afirmação sobre a série | seis anos, uma passagem |
| [`srag_infogripe_validation`](notebooks/srag_infogripe_validation.ipynb) | a Fiocruz obteria os mesmos números? | 2019, roda manual (URL externa) |

A separação walkthrough/internals é deliberada: **medir num ano e afirmar
sobre os seis foi o erro que mais se repetiu** na construção do módulo
(checkboxes, comorbidade, idade, o portão antigênico que é 0,00% em cinco
anos e 6,40% em 2024). Uma afirmação sobre a série tem de morar no caderno
que lê a série.

## Obter os dados e subir o banco local

```bash
bash tools/fetch_srag.sh          # ~265 MB de parquet, direto do S3
python3 tools/srag_silver.py      # constrói o Prata (~/Documents/srag-data/silver)
```

```bash
cd modules/00-dataset/docker
cp .env.example .env              # escolha uma senha; .env é git-ignored
set -a; . .env; set +a
docker compose up -d
python3 load.py                   # Bronze + Prata no Postgres
```

- **Metabase** em `localhost:3000` — explorar e montar gráficos sem SQL.
  A tabela `silver.contrato` traz as **418 colunas documentadas** — as 194
  cruas com família, classe, domínio e portão, e as 224 derivadas com o
  label de definição — ao lado dos dados.
- **Adminer** em `localhost:8080` — cliente SQL direto.
- Os parquet continuam sendo a fonte da verdade; o banco é conveniência.

> Em 2026-08-30 o portal `dadosabertos.saude.gov.br` respondia HTTP 500 em
> todas as páginas; o bucket S3 é serviço separado e ficou de pé — por
> isso o script baixa direto do S3.

## Privacidade

A publicação remove identificadores diretos (nome, CPF, CNS, nome da mãe,
telefone, endereço). **`DT_NASC` permanece** — data de nascimento que,
combinada com município e sexo, é quase-identificador; por isso carrega a
classe `identifier` no contrato e a idade entra pelos derivados. Nenhum
módulo deve publicar recortes que aproximem um indivíduo de identificação.

## Fonte e licença

Ministério da Saúde / SVSA — SIVEP-Gripe, via
[Portal de Dados Abertos do SUS](https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026).
Script de referência: [`gitlab.com/cgcovid/dados-publicos`](https://gitlab.com/cgcovid/dados-publicos)
(MIT). Série de validação: [`FluVigilanciaBR/data`](https://github.com/FluVigilanciaBR/data)
(GPL-3.0).
