# Aula — Ceteris paribus no modelo COVID (forma viva)

> Reescrita 2026-09-02 sobre o modelo do curso adotado em 2026-09-01
> (800 árvores, profundidade 4, lr 0,05 — módulo 00, SELECTION.md) e
> sobre o paciente-regra que veio com ele. Figuras em `../figures/`;
> todo número abaixo é impresso por `cp_walkthrough.ipynb` ou
> `cp_internals.ipynb`; os de base cheia, pelo internals do modelo
> (módulo 00). A aula da era Breast Cancer vive no histórico do git.

**Objetivos.** Ao final, a turma deve saber calcular um perfil e dizer
que linhas ele entrega; explicar a escadaria e o degrau-que-é-da-grade;
derivar (não estimar) a conta de pacientes impossíveis; e dizer o que a
restrição de grade de Molnar faz de verdade.

---

## 1. O método em uma frase (5 min)

A citação do capítulo — "one of the simplest analysis one can do" — e a
definição: congele o paciente, mova uma variável, plote a predição.
Nada aproximado: é a saída do modelo. Avisar já a advertência causal do
capítulo (o nosso modelo lê fichas de vigilância — módulo 00, armadilha
da imagem). Mostrar `cp_passo_1_perfil.png`.

Antes da figura, o porquê de explicar ESTE modelo: no teste a escadaria
faz AUC 0,7644 contra 0,7246 da reta (Brier 0,1308 contra 0,1452,
n = 16.142) — a diferença é feita de interações, e é justamente o que
nenhum coeficiente global mostra.

**O que apontar:** a escadaria; a amplitude que **não** converge porque
nunca se moveu — 0,4809 nos quatro passos; e o degrau, que se move:
0,1387 no passo 10, 0,0852 do passo 5 para baixo (internals §1).
Posições de corte são do modelo; alturas de degrau, da grade.

## 2. Dois modelos, um perfil (8 min) — a fig. 12.5 do livro

`cp_passo_1b_modelos.png`. **O que apontar:** neste paciente é a
**escadaria** que varre mais (0,481 vs 0,397 na idade); a rampa desenha
a mesma forma para todo paciente — sem interações, o coeficiente global
vale para todos, só o nível muda. E o painel de doses, onde os dois
discordam **ponta a ponta** (logística +0,217, monótona, carregando o
confundimento de quem-se-vacinou; XGBoost −0,044) — mas o XGBoost sobe
até a segunda dose e sobe também na vizinhança do próprio paciente
(+0,03542, internals §4). Dizer "o XGBoost desce" é ler a ponta, não o
paciente. Semear aqui a pergunta que o módulo 05 colhe (o φ das doses).

*Objeção que vem:* "então a logística está errada?" — Não: ela responde
com o coeficiente global que tem; o AUC do §1 diz quanto as interações
compram. Modelos diferentes, perguntas iguais, respostas comparáveis —
é para isso que o CP entre modelos serve.

## 3. A pergunta que ninguém faz (15 min)

Quem são as linhas do gráfico? Os dois pacientes pela mesma regra
|p−0,5|: o imune (90 anos, uma comorbidade declarada, início
pós-campanha — 0/1, 0/6, mas 1/1 no sintoma-fio) e o vulnerável
(1/1, 6/6, 1/1). As três cercas exatas: portão do funil (0,00% em seis
anos), calendário (17/01/2021), definição da coorte.
`cp_passo_2_impossivel.png`: 37,3% atrás do portão, 29,7% pré-campanha,
79,6% com o critério-2 por um fio.

**Ponto da aula: no BCW isso era envelope empírico; aqui é derivável.**
E depende de QUEM — um paciente só esconderia o achado.

## 4. Por que a checagem genérica falha (8 min)

Gower do impossível: 0,0037; do possível: 0,1287; mediana dos reais:
0,0046 — o ponto que não pode existir está mais perto de um paciente
real do que o paciente real típico está do vizinho dele. Contradição
lógica não é distância geométrica — mudar um nível de categoria custa o
mesmo, impossível ou não. `gate_impossible` vê; a geometria, não.

## 5. O remédio, medido (9 min)

`cp_passo_4_restrito.png`: pós-campanha a grade restrita preserva a
curva inteira (0,0896 → 0,0896, 0/7); pré-campanha ela a **remove**
(0,0119 → 0,0000, 6/7 impossíveis — sobra um ponto, e um ponto não é
curva). Restringir a grade funciona **dizendo quando não perguntar** —
para 29,7% da amostra, a varredura de doses não existe.

## 6. O que carregar (5 min)

O painel `cp_top_features.png` com a fração impossível por feature — 0%
nas oito para ESTE paciente, que é o achado do passo 2 visto do lado de
quem passa ileso; a semente que deixou de ser fantasma (determinístico
sem subsample — internals §2; com subsample 0,8, correlação 0,9978); a
inclinação local que o LIME vai estimar — por região, nunca no degrau
(módulo 03, internals §6). ICE (módulo 02) = 200 destes perfis de uma
vez.

Fechar com a frase da casa: o CP é honesto sobre o modelo e desonesto
sobre o mundo — e a honestidade que falta se conta, não se lamenta.

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
- A correlação entre sementes com subsample 0,8 — dizia 0,9791, mede
  0,9978 (cp_internals §2).
- As frações da base cheia citadas pelo caderno — dizia 38,07 / 34,51 /
  78,83 / 23,67% e apontava para o internals §6 do modelo; o módulo 00
  mede 38,05 / 34,50 / 78,83 / 23,66% na §5.
