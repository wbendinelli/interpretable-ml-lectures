# Módulo 02 — ICE (expectativa condicional individual)

[![Walkthrough — Open In Colab](https://img.shields.io/badge/walkthrough-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/02-ice/notebooks/ice_walkthrough.ipynb)
[![Internals — Open In Colab](https://img.shields.io/badge/internals-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/02-ice/notebooks/ice_internals.ipynb)

*Autor do módulo: [William Bendinelli](https://github.com/wbendinelli) — SCC5819 (ICMC-USP, 2026).*

Curvas ICE — Molnar, cap. 13; Goldstein et al. (2015) — sobre **o modelo
do curso** ([MODEL.md](../00-dataset/MODEL.md)). *"ICE plots display one
line per instance"*: o módulo 01 desenhou um perfil; este desenha o
feixe — as três variantes do capítulo (feixe+PDP, centrado, derivada) —
e ganha o que o CP não tem: **heterogeneidade**, que nesta base tem
nome: **regime**. A versão Breast Cancer vive no histórico do git.

![200 curvas ICE de idade, coloridas por ano de início](figures/ice_passo_1_feixe.png)

## Objetivos de aprendizagem

Ao fim deste módulo você deve conseguir:

1. Construir um feixe ICE com regra de amostragem declarada — e dizer
   por que o capítulo manda declarar (overcrowding).
2. Aplicar o teste de interação do capítulo — "as curvas seguem o mesmo
   curso?" — e ler a resposta desta base.
3. Usar o ICE centrado e a derivada para separar nível, forma e onde o
   efeito mora.
4. Contar, por feixe, quantos pontos são pacientes impossíveis — e
   prever a conta pela cerca antes de medir.

## O que o módulo mostra

1. **O teste do capítulo falha de propósito** (passo 1): as curvas NÃO
   seguem o mesmo curso — o feixe estratifica por regime. Aos 80 anos, a
   média é 0,48 nos pacientes de 2020 e 0,32 nos de 2023–24; o PDP
   reporta 0,407 — um número que não descreve nenhum regime. A regra dos
   200 pacientes (40 por ano, semente 42) é a resposta declarada ao
   overcrowding — e estratificada por ano para o regime não sumir no
   desbalanceio.
2. **Centrado separa nível de forma** (passo 2): ganho 0→100 anos de
   0,23 (p10) a 0,62 (p90), correlação mediana de 0,965 com a média —
   forma quase paralela, níveis muito diferentes. Para idade, o PDP
   acerta a forma e erra o nível de todos ao mesmo tempo: o modo de
   mentir mais educado que existe (internals §2).
3. **A derivada acha o efeito onde ninguém procurava** (passo 4): o pico
   é **pediátrico** — 0,023/ano aos 10 anos (herança da coorte
   pré-COVID: bronquiolite) — contra mediana de 0,003 no miolo 40–54 e
   máximo de 0,014 depois dos 55.
4. **Quem são as linhas, vezes 200** (passo 3): o feixe de idade é
   logicamente seguro (0 de 10.200 pontos); o de doses fabrica 252 de
   1.400 (18% — exatamente os 42 pacientes pré-campanha × 6, previsto
   pela cerca antes de medido); o de tosse, 54% (internals §3). A
   escolha da feature varrida decide se o feixe é retrato ou fábula.

## O que o módulo conclui, e como isso é medido

- **A heterogeneidade que o capítulo promete tem nome e número aqui.**
  *"ICE curves can uncover heterogeneous relationships"* — e o que elas
  descobrem nesta base é o regime: a letalidade caiu de 31,4% para
  18,2% entre treino e teste, e cada aviso do capítulo (overcrowding,
  pontos inválidos por correlação, a média que esconde) vira uma regra
  declarada ou uma contagem impressa.
- **A ficção do congelamento multiplica por 200 — e continua contável.**
  As mesmas cercas do módulo 01 (`gate_impossible`), os mesmos números
  por construção; a contagem por feixe é derivável antes de medida
  (doses: 42 × 6 = 252, e 252 saiu).
- **O feixe é o último método do curso em que cada linha é um paciente
  nomeável** — o LIME (módulo 03) troca a grade por vizinhos sintéticos,
  e a mesma pergunta ("quem são as linhas?") passa a ter resposta pior.

## Aula

[`lecture/outline.md`](lecture/outline.md) — a forma viva da aula.

## Notebooks

- [`notebooks/ice_walkthrough.ipynb`](notebooks/ice_walkthrough.ipynb) —
  a aula: o método e a regra dos 200, o feixe com o PDP, o centrado, as
  duas contagens e a derivada. Amostra commitada, sem rede, ~10 s.
- [`notebooks/ice_internals.ipynb`](notebooks/ice_internals.ipynb) — o
  companheiro que prova: dispersão/amplitude por feature, quando o PDP
  não mente, e o custo da cerca por feixe. ~10 s.

As figuras commitadas estão em `figures/`; rodar os notebooks as
regenera em `notebooks/figures_generated/` (git-ignorado).

## Referências

- Molnar, C. *Interpretable Machine Learning*, 3ª ed. — [cap. 13 (ICE)](https://christophm.github.io/interpretable-ml-book/ice.html). (Livro-texto: as três variantes, o teste de interação e os avisos que este módulo transforma em regra e contagem.)
- Goldstein, A.; Kapelner, A.; Bleich, J.; Pitkin, E. (2015). *Peeking Inside the Black Box: Visualizing Statistical Learning with Plots of Individual Conditional Expectation.* JCGS 24(1). (O artigo original do ICE, incluindo c-ICE e d-ICE.)
- Base, modelo, pacientes e cercas: módulo 00 ([MODEL.md](../00-dataset/MODEL.md), [gold/MANIFEST.md](../00-dataset/gold/MANIFEST.md)).
