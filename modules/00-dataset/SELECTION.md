# SELECTION.md — o estudo que escolheu o modelo do curso

Gerado por `tools/srag_selection.py --card` de
`gold/selection_metrics.json`. Não editar à mão.

Amostra commitada: 240.290 linhas — treino 200.000, val 24.148, teste 16.142.

## O protocolo

```
Pré-registrado em 2026-09-01, antes de qualquer leitura do teste.

1. PRIMÁRIO — maior AUC-ROC na VALIDAÇÃO (2023 inteiro). O teste (2024)
   nunca entra na escolha.
2. EMPATE TÉCNICO — modelos dentro de 1 erro-padrão bootstrap pareado
   (200 reamostras, semente 42) da melhor AUC de validação estão empatados.
3. DESEMPATE 1 — calibração: menor |previsto médio − observado| na validação.
4. DESEMPATE 2 — parcimônia: menor número de parâmetros ajustados.
5. DESEMPATE 3 — determinância: sem subamostragem estocástica.
6. O teste é lido UMA vez, depois de escolhido, e não pode mudar a escolha.
   Qualquer leitura adicional é rotulada "exploratória".
7. HIPÓTESE DO AUTOR, registrada antes de medir: o XGBoost vence, por
   ≥ 0,02 de AUC sobre a logística e ≥ 0,01 sobre a floresta.
8. CONSEQUÊNCIA DECLARADA: se o vencedor tunado divergir de XGB_PARAMS,
   o modelo do curso muda; os módulos de método são re-sincronizados em
   PR posterior.
```

## O zoo

| modelo | Molnar | forma | matriz | configurações buscadas |
|---|---|---|---|---:|
| `dummy` | — | constante | linear | 1 de 1 |
| `lpm` | cap. 6 | linear aditivo em p | linear | 1 de 1 |
| `logit` | cap. 7 | linear aditivo em log-odds | linear | 7 de 7 |
| `arvore` | cap. 9 | regras hierárquicas | arvore | 24 de 320 |
| `floresta` | — | ensemble por bagging | arvore | 10 de 24 |
| `xgb` | — | ensemble aditivo por boosting | xgb | 30 de 960 |

Três matrizes, porque as três famílias querem coisas diferentes:
`xgb` recebe as categóricas nativas, `linear` recebe one-hot com
nível base derrubado e a semana em seno/cosseno, `arvore` recebe
one-hot completo e a semana ordinal (MANIFEST §2.8).

## Fora do estudo, de propósito

- **GAM (Molnar cap. 8)** — a idade tem um U que a reta achata;
  escolher os termos suaves É a lição do capítulo, e ela
  não cabe numa linha de placar.
- **Regras de decisão (cap. 10)** — SE-ENTÃO sobre checkboxes é
  exatamente o que o funil torna traiçoeiro; a árvore já entrega
  aqui a versão hierárquica da mesma ideia.
- **RuleFit (cap. 11)** — gera regras e depois faz L1 sobre elas:
  dois capítulos empilhados, com subamostra própria.

Nenhum dos três está fora por qualidade. Cada um vira módulo
próprio — ver [ROADMAP.md](../../ROADMAP.md).

## As buscas

### `dummy` — 1 de 1 configurações

- espaço: `strategy` ∈ ['prior']
- melhor: `{"strategy": "prior"}` → AUC val **0.5**
- pior da busca: AUC val 0.5 — amplitude 0.0

### `lpm` — 1 de 1 configurações

- espaço: sem hiperparâmetros — é o ponto (Molnar cap. 6)
- melhor: `{}` → AUC val **0.7232**
- pior da busca: AUC val 0.7232 — amplitude 0.0

### `logit` — 7 de 7 configurações

- espaço: `C` ∈ [0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0]
- melhor: `{"C": 0.003}` → AUC val **0.7214**
- pior da busca: AUC val 0.7206 — amplitude 0.0008

### `arvore` — 24 de 320 configurações

- espaço: `ccp_alpha` ∈ [0.0, 1e-06, 1e-05, 0.0001]; `criterion` ∈ ['gini', 'log_loss']; `max_depth` ∈ [3, 4, 5, 6, 8, 10, 12, None]; `min_samples_leaf` ∈ [20, 50, 200, 1000, 5000]
- melhor: `{"ccp_alpha": 0.0, "criterion": "log_loss", "max_depth": null, "min_samples_leaf": 200}` → AUC val **0.7041**
- pior da busca: AUC val 0.6373 — amplitude 0.0668

### `floresta` — 10 de 24 configurações

- espaço: `max_depth` ∈ [8, 12, 16]; `max_features` ∈ ['sqrt', 0.3]; `min_samples_leaf` ∈ [5, 20, 50, 200]
- melhor: `{"max_depth": 16, "max_features": "sqrt", "min_samples_leaf": 5}` → AUC val **0.7403**
- pior da busca: AUC val 0.7217 — amplitude 0.0186

### `xgb` — 30 de 960 configurações

- espaço: `learning_rate` ∈ [0.03, 0.05, 0.08, 0.15]; `max_depth` ∈ [3, 4, 5, 6, 8]; `min_child_weight` ∈ [1, 5, 20, 100]; `n_estimators` ∈ [200, 400, 800]; `reg_lambda` ∈ [0.5, 1.0, 5.0, 20.0]
- melhor: `{"learning_rate": 0.05, "max_depth": 4, "min_child_weight": 100, "n_estimators": 800, "reg_lambda": 5.0}` → AUC val **0.7564**
- pior da busca: AUC val 0.724 — amplitude 0.0324

### Sondagens (fora do placar)

| sondagem | configuração | AUC val | fit (s) |
|---|---|---:|---:|
| L1 (`saga`) | `{"C": 0.01, "l1_ratio": 1.0, "random_state": 42, "solver": "saga"}` | 0.7217 | 2.5 |
| L1 (`saga`) | `{"C": 0.1, "l1_ratio": 1.0, "random_state": 42, "solver": "saga"}` | 0.7207 | 5.8 |
| L1 (`saga`) | `{"C": 1.0, "l1_ratio": 1.0, "random_state": 42, "solver": "saga"}` | 0.7206 | 7.7 |
| floresta de fábrica | RandomForestClassifier() — só n_jobs e random_state | 0.7219 | 8.5 |

A floresta de fábrica ajusta 11.222.316 nós (ECE 0.1004): o default
cresce até a folha pura, e o preço aparece no custo e na
calibração antes de aparecer na AUC.

O LPM prevê fora de [0,1] — o clip é o achado, não um detalhe de
implementação:

| split | previsões fora de [0,1] | mínimo bruto | máximo bruto |
|---|---:|---:|---:|
| val | 4.999 | -0.4592 | 1.2987 |
| test | 3.818 | -0.4871 | 1.0416 |

## O placar

### val

| modelo | AUC | PR-AUC | lift | Brier | log-loss | ECE | previsto médio | observado | parâmetros | fit (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `dummy` | 0.5 | 0.1893 | 1.0 | 0.1689 | 0.5246 | 0.1243 | 0.3136 | 0.1893 | 1 | 0.0 |
| `lpm` | 0.7232 | 0.3371 | 1.7805 | 0.1552 | 0.5091 | 0.105 | 0.2823 | 0.1893 | 92 | 1.4 |
| `logit` | 0.7214 | 0.3347 | 1.768 | 0.1545 | 0.4646 | 0.0868 | 0.2762 | 0.1893 | 92 | 1.3 |
| `arvore` | 0.7041 | 0.3156 | 1.6668 | 0.1434 | 0.4481 | 0.0354 | 0.2247 | 0.1893 | 1.507 | 2.8 |
| `floresta` | 0.7403 | 0.3616 | 1.9101 | 0.1454 | 0.4563 | 0.0897 | 0.279 | 0.1893 | 2.736.410 | 18.1 |
| `xgb` | 0.7564 | 0.3817 | 2.0159 | 0.1356 | 0.4209 | 0.0316 | 0.2209 | 0.1893 | 20.284 | 8.3 |

### test

| modelo | AUC | PR-AUC | lift | Brier | log-loss | ECE | previsto médio | observado | parâmetros | fit (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `dummy` | 0.5 | 0.1824 | 1.0 | 0.1664 | 0.5192 | 0.1312 | 0.3136 | 0.1824 | 1 | 0.0 |
| `lpm` | 0.726 | 0.3379 | 1.8519 | 0.1475 | 0.4978 | 0.0908 | 0.2573 | 0.1824 | 92 | 1.4 |
| `logit` | 0.7255 | 0.3363 | 1.8434 | 0.1449 | 0.4422 | 0.0674 | 0.2427 | 0.1824 | 92 | 1.3 |
| `arvore` | 0.7163 | 0.3128 | 1.7143 | 0.1386 | 0.4476 | 0.0385 | 0.221 | 0.1824 | 1.507 | 2.8 |
| `floresta` | 0.7476 | 0.3698 | 2.027 | 0.1412 | 0.4464 | 0.0919 | 0.2743 | 0.1824 | 2.736.410 | 18.1 |
| `xgb` | 0.7644 | 0.3888 | 2.131 | 0.1308 | 0.409 | 0.0329 | 0.2154 | 0.1824 | 20.284 | 8.3 |

`fit (s)` não é reivindicação de desempenho — Apple Silicon, pilha
fixada, uma medição só. Está aqui pelo custo RELATIVO entre as
formas, que é o que muda a decisão de quem mantém isto.

## O bootstrap pareado

200 reamostras da validação, as MESMAS para todos os modelos
(reamostra degenerada, com uma classe só, é descartada). O que a
regra 2 usa é `EP do Δ`: dois modelos que erram nos mesmos
pacientes têm diferença mais estável do que os intervalos
individuais sugerem.

| modelo | AUC média | EP | Δ vs líder | EP do Δ |
|---|---:|---:|---:|---:|
| `dummy` | 0.5 | 0.0 | -0.2564 | 0.0039 |
| `lpm` | 0.7232 | 0.0038 | -0.0332 | 0.0026 |
| `logit` | 0.7214 | 0.0038 | -0.035 | 0.0027 |
| `arvore` | 0.7039 | 0.004 | -0.0526 | 0.0034 |
| `floresta` | 0.7404 | 0.0039 | -0.016 | 0.0018 |
| `xgb` (líder) | 0.7564 | 0.0039 | 0.0 | 0.0 |

## A escolha

**Vencedor: `xgb`**, por `pick_model` —
a função levanta exceção se receber uma linha de `split == test`,
então a escolha não vê 2024 nem por acidente de chamada.

- regra 1: xgb lidera a AUC de validação (0,7564)
- regra 2: nenhum modelo dentro de 1 EP (0,0018) do líder — sem empate

Os hiperparâmetros escolhidos:

| modelo | configuração |
|---|---|
| `dummy` | `{"strategy": "prior"}` |
| `lpm` | `{}` |
| `logit` | `{"C": 0.003}` |
| `arvore` | `{"ccp_alpha": 0.0, "criterion": "log_loss", "max_depth": null, "min_samples_leaf": 200}` |
| `floresta` | `{"max_depth": 16, "max_features": "sqrt", "min_samples_leaf": 5}` |
| `xgb` | `{"learning_rate": 0.05, "max_depth": 4, "min_child_weight": 100, "n_estimators": 800, "reg_lambda": 5.0}` |

## A armadilha do k-fold

As mesmas 4 configurações, mesmo orçamento
(150 árvores, lr 0,08), julgadas de dois jeitos.
À esquerda, `cv=5` embaralhado dentro do treino: cada dobra
de validação tem vizinhos temporais na dobra de treino, 2020–2022
misturados. À direita, a validação temporal que este estudo usa.

| configuração | AUC 5-fold embaralhado | AUC val 2023 |
|---|---:|---:|
| `{"learning_rate": 0.08, "max_depth": 7, "n_estimators": 150}` | 0.7573 | 0.7504 |
| `{"learning_rate": 0.08, "max_depth": 5, "n_estimators": 150}` | 0.7558 | 0.752 |
| `{"learning_rate": 0.08, "max_depth": 9, "n_estimators": 150}` | 0.7555 | 0.7441 |
| `{"learning_rate": 0.08, "max_depth": 3, "n_estimators": 150}` | 0.7491 | 0.7434 |

Elas discordam. O 5-fold embaralhado escolheria
`{"learning_rate": 0.08, "max_depth": 7, "n_estimators": 150}`; a validação temporal escolhe
`{"learning_rate": 0.08, "max_depth": 5, "n_estimators": 150}` — o protocolo default do mercado trocaria o
modelo do curso, e a troca seria invisível para quem só olha a
média das dobras.

A melhor AUC embaralhada está 0.0053 acima da melhor AUC
temporal: parte disso é o regime de 2020–22 vazando para dentro
da própria dobra de avaliação.

## O que o mercado faria

| prática | o que custaria aqui | o que este estudo faz |
|---|---|---|
| `RandomizedSearchCV(cv=5` embaralhado`)` | mistura 2020–22 nas dobras | seleção na val 2023 (a armadilha, medida acima) |
| Optuna, 100–500 trials | 500 leituras das mesmas 24k linhas = sobreajuste de seleção | orçamento declarado + EP bootstrap |
| retreinar em treino+val antes do deploy | perderia o único conjunto de seleção honesto | não retreina (o internals mede o que isso custa) |
| early stopping na validação | é busca de `n_estimators` fora do orçamento declarado | `n_estimators` está na grade, contado |
| SMOTE / `class_weight` | destruiria a história de calibração (MANIFEST §2.7) | a prevalência entra como linha do placar: o Dummy |
| espiar o teste "só uma vez" no meio | invalida a estimativa que o teste existe para dar | `pick_model` levanta exceção se vir `split=test` |
| AutoML / stacking | um objeto que nenhum módulo do curso consegue explicar | fora, com o motivo escrito |

## Consequência

A regra 8 do protocolo foi acionada: o vencedor **divergia** do
`srag_model.XGB_PARAMS` em vigor na data do estudo.

- `XGB_PARAMS` na data do estudo: `{"learning_rate": 0.08, "max_depth": 5, "n_estimators": 400}`
- vencedor do estudo, adotado em seguida: `{"learning_rate": 0.05, "max_depth": 4, "n_estimators": 800}`

O modelo do curso mudou — ver [MODEL.md](MODEL.md) — e os
módulos de método são re-sincronizados em PR posterior. A
consequência estava escrita antes de medir, então cumpri-la
não é reação a um número que não agradou.
