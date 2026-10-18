# Aula — Ceteris paribus no modelo COVID (forma viva)

**Objetivos.** Construir um perfil do preditor fixo; distinguir resolução da
grade e cortes do modelo; conferir violações das regras auditadas e o que
resta de uma grade após restringi-la. As figuras descrevem previsões, sem
identificar efeitos clínicos.

## 1. O método em uma frase (5 min)

Congele as outras entradas de um registro, substitua uma delas e consulte a
probabilidade. Abrir `cp_passo_1_perfil.png`. O walkthrough imprime o núcleo,
a identidade da amostra e a divisão temporal antes dos resultados.

No teste, XGBoost tem AUC 0,7644 e Brier 0,1308; a logística, 0,7246 e
0,1452 (n = 16.142). A comparação não isola o ganho de interações.

**O que apontar:** amplitude 0,4809 nas quatro grades; maior salto 0,1387
no passo 10 e 0,0852 nos passos mais finos (internals §1). São resultados
conferidos para este perfil. Uma grade diferente pode perder extremos.

## 2. Dois modelos, um perfil (8 min) — a fig. 12.5 do livro

Abrir `cp_passo_1b_modelos.png`. A amplitude da idade neste exemplar é 0,481
no XGBoost e 0,397 na logística. O escore da logística é aditivo; a curva
em probabilidade inclui sua transformação sigmoide.

Em doses, a logística sobe +0,217 ponta a ponta e o XGBoost termina em −0,044.
O segundo não é monótono: a diferença regional no exemplar é +0,03542
(internals §4). Perfil, atribuição e efeito causal têm definições diferentes;
os sinais não quantificam confundimento vacinal.

<a id="3-a-pergunta-que-ninguém-faz-15-min"></a>

## 3. Conferir as combinações avaliadas (15 min)

Abrir `cp_passo_2_impossivel.png`. Os dois exemplares seguem regras declaradas.
Conferir portão do formulário, calendário adotado e elegibilidade da coorte.
Na amostra: 37,3% expostos ao portão, 29,7% ao calendário e 79,6% ao critério-2.
O portão foi auditado na fonte (0,00% de contradição nos anos estudados).

**Pergunta:** o que esses filtros deixam de verificar? Ausência de violação
não demonstra plausibilidade clínica completa ou possibilidade de intervenção.

## 4. Por que a checagem genérica falha (8 min)

Gower do exemplo com violação: 0,0037; sem essa violação: 0,1287; mediana
nos registros reais: 0,0046. A conclusão é restrita: distância pequena não
assegura conformidade com as regras auditadas.

## 5. O remédio, medido (9 min)

Abrir `cp_passo_4_restrito.png`. No exemplar pós-campanha, a amplitude permanece
0,0896, com 0/7 violações. No pré-campanha, 0,0119 → 0,0000, com 6/7 violações:
resta apenas ausência de doses, sem curva de comparação sob essa regra.

## 6. O que carregar (5 min)

Abrir `cp_top_features.png`: 0% de violações nas oito grades para o exemplar;
o resultado não se generaliza a todo registro nem cobre todas as restrições.

O internals §2 usa **150 árvores**, enquanto a referência tem **800**. Ler os
regimes separadamente: sem subamostragem, perfis coincidentes nas sementes
examinadas; com `subsample` e `colsample_bytree` em 0,8, há variação e correlação
mediana 0,9978. Não atribuir essa medida a retreinos do ajuste de referência.

O módulo 02 reúne perfis de vários registros no mesmo painel. O módulo 03
compara diferenças finitas regionais com um ajuste ponderado multivariado;
a concordância de sinal não torna os objetos idênticos.

**Correções de interpretação.** A diferença de AUC não isola interações;
o perfil de doses não identifica confundimento; os filtros não são testes
biológicos; o controle de sementes é uma ablação, não o modelo da aula.

<details>
<summary>Histórico dos números e correções anteriores</summary>

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo; os de base
cheia, pelo internals do modelo (módulo 00).

**Corrigidos nesta revisão** — a afirmação caiu, não só o número:

- A amplitude do perfil converge com a grade — dizia 0,288 → 0,331 do
  passo 10 ao 1, mede 0,4809 nos quatro passos: ela nunca se moveu
  (cp_internals §1). O que se move é o degrau: 0,202 fixo virou 0,1387
  no passo 10 e 0,0852 dali para baixo.
- A rampa da logística é mais agressiva que a escadaria — dizia 0,718
  contra 0,330, mede 0,397 contra 0,481 (cp_walkthrough §1b).
- O XGBoost desce nas doses — dizia "desce de leve", mede um perfil não
  monótono: −0,044 ponta a ponta e +0,03542 de inclinação no próprio
  paciente (cp_walkthrough §1b, cp_internals §4).
- A distância de Gower do ponto impossível — dizia 0,043 (possível
  0,130, mediana dos reais 0,005) quando a célula commitada já imprimia
  0,0491 / 0,1364 / 0,0046; mede 0,0037 / 0,1287 / 0,0046
  (cp_walkthrough §3).

**Deslocados pelo novo modelo e pelo novo paciente-regra** — a
afirmação continua de pé, o número não:

- A amplitude que o remédio remove — dizia 0,151 → 0,000, mede
  0,0119 → 0,0000, ainda com 6/7 pontos impossíveis (cp_walkthrough §4).
- A correlação entre sementes na ablação de 150 árvores com subsample 0,8 — dizia 0,9791, mede
  0,9978 (cp_internals §2).
- As frações da base cheia citadas pelo caderno — dizia 38,07 / 34,51 /
  78,83 / 23,67% e apontava para o internals §6 do modelo; o módulo 00
  mede 38,05 / 34,50 / 78,83 / 23,66% na §5.
</details>
