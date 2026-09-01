# Aula — ICE no modelo COVID (forma viva)

> Reescrita 2026-09-01 sobre o modelo do curso. Figuras em `../figures/`;
> todo número abaixo é impresso por `ice_walkthrough.ipynb` ou
> `ice_internals.ipynb`. A aula da era Breast Cancer vive no histórico
> do git.

**Objetivos.** Ao final, a turma deve saber construir um feixe com regra
declarada; aplicar o teste do capítulo ("mesmo curso?"); separar nível
de forma com o c-ICE e localizar o efeito com o d-ICE; e contar o
impossível por feixe, prevendo a conta pela cerca.

---

## 1. Do CP ao feixe (7 min)

A definição do capítulo ("one line per instance") e o aviso na mesma
página: overcrowding. A resposta declarada: **200 pacientes, 40 por ano,
semente 42** — estratificar por ano é o que deixa o regime visível;
sortear sem estrato o afogaria no desbalanceio (2020–22 domina). As três
variantes do capítulo = os passos da aula.

## 2. O feixe, e o teste que falha de propósito (12 min)

`ice_passo_1_feixe.png`. O teste do capítulo: curvas no mesmo curso ⇒
sem interação ⇒ PDP basta. **O que apontar:** o feixe estratifica por
COR. Aos 80 anos: 0,48 (2020) vs 0,32 (2023–24); o PDP diz 0,407 — de
ninguém. A heterogeneidade tem nome nesta base: regime (letalidade
31,4% → 18,2% entre treino e teste).

*Prompt de discussão:* o PDP é a curva que um relatório executivo
publicaria. O que ele faria um gestor de 2024 concluir sobre idade — e
sobre qual população essa conclusão vale?

## 3. Centrado: nível × forma (8 min)

`ice_passo_2_centrado.png` — o c-ICE do capítulo ("easier to compare").
**O que apontar:** ancoradas na idade 0, as curvas mostram só a forma:
ganho 0→100 de 0,23 (p10) a 0,62 (p90); correlação mediana 0,965 com a
média. Forma quase paralela, nível não — para idade, o PDP acerta a
forma e erra o nível de todos ao mesmo tempo (internals §2: quando o
PDP não mente).

## 4. Quem são as linhas, vezes 200 (10 min)

O contraste entre feixes (walkthrough passo 3): idade 0/10.200 pontos
impossíveis; doses 252/1.400 — **18%, e a conta era derivável antes de
medir**: 42 pacientes pré-campanha × 6 doses varridas; tosse 54%
(internals §3). A escolha da feature varrida decide se o feixe é
retrato ou fábula — e a régua é a mesma `gate_impossible` dos módulos
00–01.

## 5. A derivada: onde o efeito mora (8 min)

`ice_passo_4_derivada.png` — o d-ICE ("spot ranges where predictions
change"). **O que apontar:** o pico é PEDIÁTRICO — 0,023/ano aos 10
anos, herança da coorte pré-COVID (bronquiolite) — contra 0,003 de
mediana no miolo 40–54 e máximo 0,014 pós-55. Sair da primeira infância
mexe mais com o modelo que envelhecer no meio da vida.

*Objeção que vem:* "isso é efeito biológico?" — Não necessariamente: é
o modelo lendo uma coorte onde SRAG pediátrica tem outra composição
etiológica. A advertência causal do cap. 12 vale dobrada em derivadas.

## 6. Fechamento (5 min)

O feixe é um compromisso público: cada linha é um paciente nomeável — o
último método do curso em que isso é verdade. O LIME (módulo 03) troca a
grade por vizinhos sintéticos, e a mesma pergunta ("quem são as
linhas?") passa a ter resposta pior. Gancho armado.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo.
