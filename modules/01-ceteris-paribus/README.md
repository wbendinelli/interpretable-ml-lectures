# Módulo 01 — Ceteris paribus

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/01-ceteris-paribus/notebooks/cp_walkthrough.ipynb)

Um estudo de caso de perfis ceteris paribus — Molnar, *Interpretable
Machine Learning*, cap. 12 — sobre **o modelo do curso**: o XGBoost de
óbito por COVID do módulo 00, o mesmo paciente-regra e a mesma amostra
([MODEL.md](../00-dataset/MODEL.md)) que os módulos 02–05 usam, para o
curso se ler como um caso contínuo. A versão anterior deste módulo rodava
sobre o Breast Cancer Wisconsin e vive no histórico do git; o que mudou de
substância está dito abaixo.

![Perfis ceteris paribus do paciente-regra — top-8 features por ganho](figures/cp_top_features.png)

## Objetivos de aprendizagem

Ao fim deste módulo você deve conseguir:

1. Calcular um perfil ceteris paribus e dizer exatamente que linhas ele
   entrega ao modelo.
2. Explicar por que o perfil de um XGBoost é uma escadaria, e por que a
   altura de um degrau é propriedade da grade, não do modelo.
3. Contar quantos pontos de um perfil são pacientes que não podem existir —
   e, nesta base, **derivar** essa conta em vez de estimá-la.
4. Explicar por que a checagem genérica (distância) não vê contradição
   lógica, e o que o remédio de Molnar (restringir a grade) faz de verdade.

## Por que começar pelo método mais simples

O perfil não precisa de sub-rogado, amostragem nem kernel: congele tudo de
um paciente, mova uma variável, plote a predição. Nada é aproximado — e por
isso o problema que todos os métodos seguintes herdam não tem onde se
esconder: **congelar 39 variáveis enquanto a quadragésima anda fabrica
pacientes impossíveis**.

A mudança de substância em relação à era BCW: lá, "impossível" era um
envelope empírico com piso geométrico, e 11 pacientes o furavam. Aqui as
cercas são **exatas**: o portão do funil (0,00% de contradição em seis
anos), o calendário da vacinação (nenhuma dose antes de 17/01/2021) e a
própria definição da coorte. O impossível deixou de ser estimado.

## O que o módulo mostra

Quatro passos e um painel, todos impressos por células:

1. **O perfil é uma escadaria** — e o degrau é da grade: a amplitude
   converge (0,288 → 0,331 do passo 10 ao passo 1), o maior degrau (0,202)
   é artefato de resolução (internals §1).
2. **Se a varredura fabrica ficção depende de quem**: o paciente-regra é
   imune a duas cercas e cai na terceira (o critério-2 dele está por um
   fio); o paciente vulnerável — escolhido pela mesma regra |p−0,5|,
   restrita ao estado vulnerável — transforma toda varredura em ficção
   (diabetes→sim: 1/1; doses: 6/6). Na amostra, 37,3% está atrás do
   portão, 29,7% é pré-campanha, 79,6% tem o critério-2 por um fio
   (na base cheia: 38,1 / 34,5 / 78,8%).
3. **A distância não vê contradição lógica**: o ponto impossível
   (diabetes=sim sem fator de risco declarado) fica a Gower 0,043 do dado
   real — mais perto que o ponto possível (0,130). `gate_impossible` vê;
   a geometria, não.
4. **O remédio de Molnar, medido**: para o paciente pré-campanha, a curva
   de doses tem amplitude 0,151 na grade cheia e **0,000 na restrita**
   (6/7 pontos impossíveis) — restringir não encolhe a pergunta, remove:
   para 29,7% da amostra a varredura de doses não existe.

## O que os internals estabelecem

- **A semente não é mais o fantasma**: sem subsampling, o XGBoost `hist` é
  determinístico — 12 sementes, correlação 1,0000 entre perfis; ligada a
  aleatoriedade (subsample 0,8), 0,9791. A lição do BCW inverte: aqui a
  instabilidade mora na grade e na composição do treino.
- A ficção da varredura é concentrada: comorbidades, doses e sintomas-fio;
  as demais features têm varredura logicamente segura — e enganosa por
  outra razão (imutabilidade — assunto do módulo 04).
- A inclinação local do perfil é o objeto que o LIME estima: os sinais
  locais das quatro numéricas ficam impressos para o módulo 03 comparar.

## Aula

[`lecture/outline.md`](lecture/outline.md) — a forma viva da aula.

## Notebooks

- [`notebooks/cp_walkthrough.ipynb`](notebooks/cp_walkthrough.ipynb) — os
  quatro passos e o painel, na amostra commitada, sem rede.
- [`notebooks/cp_internals.ipynb`](notebooks/cp_internals.ipynb) — grade,
  sementes (os dois regimes), a ficção feature a feature e a ponte para o
  LIME.

## Referências

- Molnar, C. *Interpretable Machine Learning*, 3ª ed., cap. 12 (Ceteris
  Paribus) — [christophm.github.io/interpretable-ml-book](https://christophm.github.io/interpretable-ml-book/).
- A base, o modelo, o paciente e as cercas: módulo 00
  ([MODEL.md](../00-dataset/MODEL.md), [GOLD.md](../00-dataset/GOLD.md),
  [gold/MANIFEST.md](../00-dataset/gold/MANIFEST.md)).
