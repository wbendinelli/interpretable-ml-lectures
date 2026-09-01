# Aula — Ceteris paribus no modelo COVID (forma viva)

> Reescrita 2026-09-01 sobre o modelo do curso (XGBoost, óbito por COVID,
> módulo 00). A aula da era Breast Cancer vive no histórico do git.

## Arco (50 min)

1. **O método em uma frase** (5 min) — congele o paciente, mova uma
   variável, plote a predição. Nada aproximado: é a saída do modelo.
   Mostrar `cp_passo_1_perfil.png`: a escadaria, e o degrau que muda com a
   grade (amplitude converge 0,288→0,331; o maior degrau, 0,202, é da
   resolução).

2. **A pergunta que ninguém faz** (15 min) — quem são as linhas do
   gráfico? Mostrar os dois pacientes pela mesma regra |p−0,5|: o imune
   (0/1, 0/6 — mas 1/1 no sintoma-fio) e o vulnerável (1/1, 6/6, 1/1).
   As três cercas exatas: portão do funil (0,00% em seis anos), calendário
   (17/01/2021), definição da coorte. `cp_passo_2_impossivel.png`: 37,3%
   atrás do portão, 29,7% pré-campanha, 79,6% critério-2 por um fio.
   **Ponto da aula: no BCW isso era envelope empírico; aqui é derivável.**

3. **Por que a checagem genérica falha** (10 min) — Gower do impossível:
   0,043; do possível: 0,130; mediana dos reais: 0,005. Contradição lógica
   não é distância geométrica — mudar um nível de categoria custa o mesmo,
   impossível ou não.

4. **O remédio, medido** (10 min) — `cp_passo_4_restrito.png`: pós-campanha
   a grade restrita preserva a curva; pré-campanha ela a **remove**
   (0,151 → 0,000, 6/7 impossíveis). Restringir a grade funciona dizendo
   quando não perguntar.

5. **O que carregar** (10 min) — o painel `cp_top_features.png` com a
   fração impossível por feature; a semente que deixou de ser fantasma
   (determinístico sem subsample — internals §2); a inclinação local que o
   LIME vai estimar (módulo 03). ICE (módulo 02) = 200 destes perfis de
   uma vez, com a heterogeneidade que aqui tem nome: regime.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo; os de base
cheia, pelo internals do modelo (módulo 00).
