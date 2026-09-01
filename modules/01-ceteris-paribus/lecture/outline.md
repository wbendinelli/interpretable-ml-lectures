# Aula — Ceteris paribus no modelo COVID (forma viva)

> Reescrita 2026-09-01 sobre o modelo do curso. Figuras em `../figures/`;
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

**O que apontar:** a escadaria; a amplitude que converge 0,288 → 0,331
do passo 10 ao 1; o maior degrau (0,202) que é artefato de resolução
(internals §1). Posições de corte são do modelo; alturas de degrau, da
grade.

## 2. Dois modelos, um perfil (8 min) — a fig. 12.5 do livro

`cp_passo_1b_modelos.png`. **O que apontar:** a rampa da logística mais
agressiva que a escadaria (0,718 vs 0,330 na idade — sem interações, o
coeficiente global vale para todos); e o painel de doses onde os dois
**discordam de direção** — a logística sobe (confundimento de
quem-se-vacinou), o XGBoost desce de leve. Semear aqui a pergunta que o
módulo 05 colhe (o φ das doses).

*Objeção que vem:* "então a logística está errada?" — Não: ela responde
com o coeficiente global que tem; o AUC (0,7575 vs 0,7246) diz quanto as
interações compram. Modelos diferentes, perguntas iguais, respostas
comparáveis — é para isso que o CP entre modelos serve.

## 3. A pergunta que ninguém faz (15 min)

Quem são as linhas do gráfico? Os dois pacientes pela mesma regra
|p−0,5|: o imune (0/1, 0/6 — mas 1/1 no sintoma-fio) e o vulnerável
(1/1, 6/6, 1/1). As três cercas exatas: portão do funil (0,00% em seis
anos), calendário (17/01/2021), definição da coorte.
`cp_passo_2_impossivel.png`: 37,3% atrás do portão, 29,7% pré-campanha,
79,6% com o critério-2 por um fio.

**Ponto da aula: no BCW isso era envelope empírico; aqui é derivável.**
E depende de QUEM — um paciente só esconderia o achado.

## 4. Por que a checagem genérica falha (8 min)

Gower do impossível: 0,043; do possível: 0,130; mediana dos reais:
0,005. Contradição lógica não é distância geométrica — mudar um nível
de categoria custa o mesmo, impossível ou não. `gate_impossible` vê; a
geometria, não.

## 5. O remédio, medido (9 min)

`cp_passo_4_restrito.png`: pós-campanha a grade restrita preserva a
curva; pré-campanha ela a **remove** (0,151 → 0,000, 6/7 impossíveis).
Restringir a grade funciona **dizendo quando não perguntar** — para
29,7% da amostra, a varredura de doses não existe.

## 6. O que carregar (5 min)

O painel `cp_top_features.png` com a fração impossível por feature; a
semente que deixou de ser fantasma (determinístico sem subsample —
internals §2; com subsample 0,8, correlação 0,9791); a inclinação local
que o LIME vai estimar — por região, nunca no degrau (módulo 03,
internals §6). ICE (módulo 02) = 200 destes perfis de uma vez.

Fechar com a frase da casa: o CP é honesto sobre o modelo e desonesto
sobre o mundo — e a honestidade que falta se conta, não se lamenta.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo; os de base
cheia, pelo internals do modelo (módulo 00).
