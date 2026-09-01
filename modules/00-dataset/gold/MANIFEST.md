# O Ouro — gold_covid_obito

Gerado por `tools/srag_gold.py` a partir do Prata (banco congelado de
26-06-2025). Não editar à mão: este texto é função pura de
`counts.json` + das decisões, e o hook `gold-manifest-generated`
re-renderiza e compara.

O Prata afirma fatos; aqui ficam as **escolhas de tarefa**, cada uma
com dono, data e a evidência que a sustenta. O cardápio de onde elas
vieram é o [GOLD.md](../GOLD.md).

## 1. O funil, na ordem em que os filtros correm

A ordem importa: as contagens abaixo não comutam.

| # | Filtro | Restam | Saem |
|--:|---|---:|---:|
| 0 | prata (sem linhas deslocadas) | 4.109.560 | — |
| 1 | coorte_hospitalizado | 2.428.695 | 1.680.865 |
| 2 | covid_caso (definição ampla) | 1.364.487 | 1.064.208 |
| 3 | casos fechados (EVOLUCAO 1 ou 2) | 1.283.801 | 80.686 |
| 4 | DT_SIN_PRI >= 2020-02-26 | 1.283.745 | 56 |
| 5 | idade presente | 1.282.973 | 772 |
| 6 | idade <= 120 | 1.282.970 | 3 |

Das 7 linhas em quarentena, **0** satisfariam coorte ∧ COVID — o
descarte não esconde caso nenhum (medido no desenho, 2026-09-01).

## 2. As decisões, uma a uma

### 2.1 Alvo — óbito nos casos fechados
`y_obito = (EVOLUCAO == 2)`, exigido `EVOLUCAO ∈ {1,2}` no funil.
**Decidido 2026-09-01 — William.** Os registros que nunca fecham saem
do Ouro (contados no funil) e a censura difere por ano — "casos
fechados" já é uma escolha de coorte, dita aqui. `EVOLUCAO` e as 39
derivadas de classe `leakage` nunca entram como feature → COLUMNS.md.

### 2.2 Coorte — hospitalizado ∧ COVID (definição ampla)
`coorte_hospitalizado` usa HOSPITAL = 1 sem o `∨ EVOLUCAO = 2` oficial
(a definição oficial admite 24.475 linhas *porque o paciente morreu*
→ DEVIATIONS). `covid_caso` é a definição ampla; quem quiser o recorte
estrito tem `rt_pcr_confirmado` = 792.269 registros.
**Decidido 2026-09-01 — William.** (A contagem da coorte difere em 1
do internals §7, que mede o Bronze pré-quarentena: a linha deslocada
de 2023 satisfazia o critério com os campos fora do lugar.)

### 2.3 Janela — a partir de 2020-02-26
Primeiro caso confirmado no Brasil (26/02/2020, MS). **Não existe
corte oficial** — o script do Ministério não filtra por data (lido
linha a linha); o evento Fiocruz que se costuma lembrar é o InfoGripe
passando a incluir COVID no boletim na SE 15 (21/04/2020), anotado
aqui como referência, não usado como filtro.
**Decidido 2026-09-01 — William.**

### 2.4 Split temporal
`temporal:2022-12-31/2023/2024` por DT_SIN_PRI. **Decidido 2026-09-01 — William.**

| split | n | óbitos | letalidade |
|---|---:|---:|---:|
| train | 1.242.680 | 390.769 | 31.4% |
| val | 24.148 | 4.572 | 18.9% |
| test | 16.142 | 2.945 | 18.2% |

Os conjuntos de avaliação são pequenos e completos: a assimetria é
consequência da epidemia, não do desenho, e a letalidade cai quase à
metade na fronteira do split — o achado central que os módulos 01–05
explicam, não um incômodo a corrigir.

### 2.5 Features — 40 colunas de modelo

| Coluna | dtype |
|---|---|
| `asma` | category |
| `capital_interior` | category |
| `cardiopati` | category |
| `coinfeccao_outro_virus` | bool |
| `cs_escol_n` | category |
| `cs_gestant` | category |
| `cs_raca` | category |
| `cs_sexo` | object |
| `cs_zona` | category |
| `desc_resp` | category |
| `diabetes` | category |
| `diarreia` | category |
| `dispneia` | category |
| `dor_abd` | category |
| `fadiga` | category |
| `febre` | category |
| `garganta` | category |
| `hematologi` | category |
| `hepatica` | category |
| `idade_anos` | float32 |
| `imunodepre` | category |
| `meses_desde_mar2020` | float32 |
| `n_doses_antes_do_sintoma` | int8 |
| `neurologic` | category |
| `nosocomial` | category |
| `obesidade` | category |
| `out_morbi` | category |
| `outro_sin` | category |
| `perd_olft` | category |
| `perd_pala` | category |
| `pneumopati` | category |
| `puerpera` | category |
| `regiao` | category |
| `renal` | category |
| `saturacao` | category |
| `semana_epi` | int8 |
| `sind_down` | category |
| `tosse` | category |
| `vacina_covid_declarada` | bool |
| `vomito` | category |

E 10 colunas de escrituração/diagnóstico que **nunca**
entram no X: `y_obito`, `split`, `rt_pcr_confirmado`, `gold_id`,
`ano_onset`, `fator_risc_portao`, `raiox_res`, `tomo_res`, `n_crit2`,
`n_crit3`.

**O que a codificação funde, e por quê.** `desconhecido` =
`nao_aplicavel` ∪ `ausente` ∪ `ignorado`. O módulo 00 mede que esses
vazios são coisas diferentes — e mesmo assim o Ouro os funde: três
níveis por variável são legíveis, cinco × 26 variáveis não. A
compressão é declarada aqui e **desfeita onde importa**:
`fator_risc_portao` viaja no Ouro exatamente para que os módulos
possam contar perturbações que contradizem o portão.

NA absorvidos por cada fill booleano (a decisão nunca é silenciosa):

| Fill | NA absorvidos |
|---|---:|
| capital_interior (RAs do DF → capital) | 28.008 |
| coinfeccao_outro_virus | 0 |
| fator_risc_portao | 0 |
| rt_pcr_confirmado | 0 |
| vacina_covid_declarada | 0 |

### 2.6 Exclusões
Classes `leakage`, `identifier`, `free_text` e o lado-nome dos
`code_pair` — lista **gerada** de COLUMNS.md, nunca digitada. Imagem
(`RAIOX_RES`/`TOMO_RES`) fica fora das features e viaja como
diagnóstico: a célula-armadilha do notebook do modelo mede o que o
modelo teria aprendido. **Decidido 2026-09-01 — William**, com a
explicação registrada (modelo não zera proxy; e o medido é invertido:
a ausência do registro é que prediz óbito).

### 2.7 Sem pesos de classe
Letalidade global de 31.04% não é
desbalanceamento extremo, e reponderar destruiria a história de
calibração que a mudança de regime torna interessante.

### 2.8 Decisões que o cardápio não previu

| Questão | Decisão |
|---|---|
| `NOSOCOMIAL` vazio (14,5% da coorte) | quarto nível `desconhecido`, não fundido no 9 |
| idade ausente | excluir (idade é a feature dominante) |
| idade > 120 anos | excluídas |
| regiões administrativas do DF | contam como `capital` (área urbana da capital; contagem em §2.5) |
| semana epidemiológica | ordinal 1–53; sin/cos só dentro do pipeline logístico |

## 3. Procedência e limites

Coorte final: **1.282.970 internações**. 398.286 óbitos (31.04%).
Prata → COLUMNS.md · qualidade → QUALITY.md (84 checagens) · validação
externa → srag_infogripe_validation (0,9997 em 2019).
Este Ouro **não** trata: `DT_EVOLUCA > DT_ENCERRA` em escala, as datas
de 2020 fora de [1900, 2030], a inconsistência resultado↔checkbox
(9–20% ao ano). Nenhuma toca as 40 features → walkthrough §7.
