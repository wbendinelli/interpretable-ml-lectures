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

Por que sair do perfil único: o agregado do modelo do curso (AUC 0,7644,
Brier 0,1308 no teste; logit de referência 0,7246/0,1452 — walkthrough,
setup) não diz em quem ele acerta, e o mundo debaixo dele muda
(letalidade observada 31,4% no treino → 18,2% no teste). A definição do
capítulo ("one line per instance") e o aviso na mesma página:
overcrowding. A resposta declarada: **200 pacientes, 40 por ano,
semente 42** — estratificar por ano é o que deixa o regime visível;
sortear sem estrato o afogaria no desbalanceio (2020–22 domina). As três
variantes do capítulo = as seções §1 a §4 do walkthrough.

## 2. O feixe, e o teste que falha de propósito (12 min)

`ice_passo_1_feixe.png`. O teste do capítulo: curvas no mesmo curso ⇒
sem interação ⇒ PDP basta. **O que apontar:** o feixe estratifica por
INTENSIDADE — 2020, o tom mais escuro da rampa, corre por cima; 2024,
o mais claro, por baixo. Aos 80 anos: 0,481 (2020) vs 0,317 (2023) e
0,303 (2024); o PDP diz 0,400 — de ninguém. A heterogeneidade tem nome
nesta base: regime (letalidade observada 31,4% → 18,2% entre treino e
teste).

*Prompt de discussão:* o PDP é a curva que um relatório executivo
publicaria. O que ele faria um gestor de 2024 concluir sobre idade — e
sobre qual população essa conclusão vale?

## 3. Centrado: nível × forma (8 min)

`ice_passo_2_centrado.png` — o c-ICE do capítulo ("easier to compare").
**O que apontar:** ancoradas na idade 0, as curvas mostram só a forma:
ganho 0→100 de 0,247 (p10) a 0,623 (p90); correlação mediana 0,983 com
a média. Forma quase paralela, nível não — para idade, o PDP acerta a
forma e erra o nível de todos ao mesmo tempo (internals §2: quando o
PDP não mente).

## 4. Quem são as linhas, vezes 200 (10 min)

O contraste entre feixes (walkthrough §3): idade 0/10.200 pontos
impossíveis; doses 252/1.400 — **18%, e a conta era derivável antes de
medir**: 42 pacientes pré-campanha × 6 doses varridas; tosse 54%
(internals §3). A escolha da feature varrida decide se o feixe é
retrato ou fábula — e a régua é a mesma `gate_impossible` dos módulos
00–01.

## 5. A derivada: onde o efeito mora (8 min)

`ice_passo_4_derivada.png` — o d-ICE ("spot ranges where predictions
change"). **O que apontar:** o pico é PEDIÁTRICO — 0,0239/ano aos 10
anos — contra 0,00326 de mediana no miolo 40–54 e máximo 0,0133 pós-55.
Sair da infância mexe mais com o modelo que envelhecer no meio da vida.

*Objeção que vem:* "isso é efeito biológico?" — Aqui, sim, e é bom saber
responder. Não é herança de coorte pré-COVID: esta coorte é só COVID e
começa em fevereiro de 2020, sem 2019 e sem SRAG de outra etiologia. É o
braço adolescente da curva em U da mortalidade pediátrica por COVID, e o
caderno o mede no treino: letalidade de 3,49% (4–8 anos) a 13,89%
(16–20). A ressalva de verdade é outra: é a região mais rala da base, com
292 a 720 pacientes por faixa contra dezenas de milhares no miolo adulto.

*A resposta que este módulo dava antes, e que não se sustenta:* "é o
modelo lendo uma coorte onde a SRAG pediátrica tem outra composição
etiológica". Não tem: o funil já removeu essa coorte. Mesmo assim a
advertência causal do cap. 12 vale dobrada em derivadas — a curva é a
saída do modelo numa linha fabricada, não o efeito de envelhecer.

## 6. Fechamento (5 min)

O feixe é um compromisso público: cada linha é um paciente nomeável — o
último método do curso em que isso é verdade. O LIME (módulo 03) troca a
grade por vizinhos sintéticos, e a mesma pergunta ("quem são as
linhas?") passa a ter resposta pior. Gancho armado.

## Números citados nesta aula

Todos impressos por células dos dois notebooks deste módulo.

**Re-medidos em 2026-09-02**, no modelo do curso adotado em 2026-09-01
(800 árvores, profundidade 4, lr 0,05 — módulo 00, SELECTION.md), contra
o modelo de 400 árvores / profundidade 5 da versão anterior:
p(óbito) aos 80 anos 0,48 → 0,481 (2020), 0,32 → 0,317/0,303 (2023/2024),
PDP 0,407 → 0,400; ganho 0→100 p10 0,23 → 0,247 e p90 0,62 → 0,623;
correlação curva×média 0,965 → 0,983; derivada 0,023 → 0,0239 (aos 10),
0,003 → 0,00326 (miolo), 0,014 → 0,0133 (pós-55). Deslocamento de
condicionamento: nenhuma afirmação da aula caiu. As contagens de cerca
não se mexeram (idade 0/10.200, doses 252/1.400 = 18%, tosse 54%) — a
cerca é da base, não do modelo.
