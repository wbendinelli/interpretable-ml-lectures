# Módulo 01 — Ceteris paribus

[![Walkthrough — Open In Colab](https://img.shields.io/badge/walkthrough-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/01-ceteris-paribus/notebooks/cp_walkthrough.ipynb)
[![Internals — Open In Colab](https://img.shields.io/badge/internals-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/01-ceteris-paribus/notebooks/cp_internals.ipynb)

*Autor do módulo: [William Bendinelli](https://github.com/wbendinelli) — SCC5819 (ICMC-USP, 2026).*

Perfis ceteris paribus — Molnar, cap. 12 — sobre **o modelo do curso**:
o XGBoost de óbito por COVID do módulo 00, os dois pacientes-por-regra
que os módulos 02–05 herdam ([MODEL.md](../00-dataset/MODEL.md)). O
método mais simples do curso — *"one of the simplest analysis one can
do"*, diz o capítulo — e por isso o lugar onde o problema que todos os
métodos posteriores herdam não tem onde se esconder. A versão Breast
Cancer vive no histórico do git.

![Perfis ceteris paribus do paciente-regra — top-8 features por ganho](figures/cp_top_features.png)

## Objetivos de aprendizagem

Ao fim deste módulo você deve conseguir:

1. Calcular um perfil ceteris paribus e dizer exatamente que linhas ele
   entrega ao modelo.
2. Explicar por que o perfil de uma floresta é uma escadaria — e por que
   a altura de um degrau é propriedade da grade, não do modelo.
3. Contar quantos pontos de um perfil são pacientes impossíveis — e,
   nesta base, **derivar** a conta em vez de estimá-la.
4. Dizer o que o remédio de Molnar (restringir a grade) faz de verdade —
   e quando ele remove a pergunta em vez de respondê-la.

## O que o módulo mostra

1. **A escadaria é da grade** (passo 1): refinar do passo 10 ao passo 1
   move a amplitude de 0,288 para 0,331 e desmonta o maior degrau
   (0,202 — artefato de resolução, internals §1). Leia posições de
   corte, nunca alturas de degrau.
2. **O mesmo perfil, dois modelos** (passo 1b — a fig. 12.5 do livro):
   a rampa da logística é mais agressiva que a escadaria (amplitude
   0,718 vs 0,330 na idade) — sem interações, o coeficiente global vale
   igual para todo paciente; e no perfil de doses os dois **discordam de
   direção** (a logística sobe, carregando o confundimento de
   quem-se-vacinou; o XGBoost desce de leve — o módulo 05 dá a esse
   confundimento um número).
3. **Se a varredura fabrica ficção depende de quem** (passo 2): o
   paciente-regra é imune a duas cercas e cai na terceira; o vulnerável
   — mesma regra |p−0,5|, restrita ao estado vulnerável — transforma
   toda varredura em ficção (diabetes 1/1, doses 6/6). Na amostra:
   37,3% atrás do portão, 29,7% pré-campanha, 79,6% com o critério por
   um fio.
4. **A distância não vê contradição lógica** (passo 3): o ponto
   impossível fica a Gower 0,043 do dado real — mais perto que o
   possível (0,130). `gate_impossible` vê; a geometria, não.
5. **O remédio de Molnar, medido** (passo 4): pós-campanha, a grade
   restrita preserva a curva; pré-campanha, ela a **remove** (amplitude
   0,151 → 0,000, 6/7 pontos impossíveis) — restringir funciona dizendo
   quando não perguntar.

## O que o módulo conclui, e como isso é medido

- **A limitação que o capítulo nomeia vira contagem derivável.** Molnar
  avisa (fig. 12.3 do livro) que mover uma feature com as outras paradas
  cria combinações irreais; na era BCW isso era um envelope empírico com
  piso geométrico, furado por 11 pacientes. Aqui as cercas são exatas —
  portão do funil (0,00% de contradição em seis anos), calendário da
  campanha, definição da coorte — centralizadas em `M.gate_impossible`
  e idênticas nos módulos 02–05 por construção.
- **A lição da semente inverteu** (internals §2): sem subsampling, o
  XGBoost `hist` é determinístico — 12 sementes, correlação 1,0000
  entre perfis; ligada a aleatoriedade (subsample 0,8), 0,9791. O
  fantasma do RandomForest da era BCW não mora aqui; a instabilidade
  mudou de endereço (grade e composição do treino).
- **A inclinação local do perfil é o objeto que o LIME estima** — e a
  ponte honesta é regional, não pontual (módulo 03, internals §6: a
  inclinação pontual da escadaria troca de sinal com o passo).

## Aula

[`lecture/outline.md`](lecture/outline.md) — a forma viva da aula.

## Notebooks

- [`notebooks/cp_walkthrough.ipynb`](notebooks/cp_walkthrough.ipynb) — a
  aula: o método termo a termo, a escadaria, os dois modelos, as três
  cercas com os dois pacientes, Gower e o remédio medido. Amostra
  commitada, sem rede, ~10 s.
- [`notebooks/cp_internals.ipynb`](notebooks/cp_internals.ipynb) — o
  companheiro que prova: a grade (o degrau é dela), os dois regimes de
  semente, a ficção feature a feature e a ponte para o LIME. ~20 s.

As figuras commitadas estão em `figures/`; rodar os notebooks as
regenera em `notebooks/figures_generated/` (git-ignorado).

## Referências

- Molnar, C. *Interpretable Machine Learning*, 3ª ed. — [cap. 12 (Ceteris Paribus)](https://christophm.github.io/interpretable-ml-book/ceteris-paribus.html). (Livro-texto: a definição, a comparação entre modelos da fig. 12.5, a limitação das combinações irreais e a advertência causal.)
- Base, modelo, pacientes e cercas: módulo 00 ([MODEL.md](../00-dataset/MODEL.md), [GOLD.md](../00-dataset/GOLD.md), [gold/MANIFEST.md](../00-dataset/gold/MANIFEST.md)).
