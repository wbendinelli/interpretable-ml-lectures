# Módulo 04 — Contrafactuais

[![Walkthrough — Open In Colab](https://img.shields.io/badge/walkthrough-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/04-counterfactual/notebooks/cf_walkthrough.ipynb)
[![Internals — Open In Colab](https://img.shields.io/badge/internals-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/04-counterfactual/notebooks/cf_internals.ipynb)

*Autor do módulo: [William Bendinelli](https://github.com/wbendinelli) — SCC5819 (ICMC-USP, 2026). Módulo novo, criado direto sobre o caso COVID.*

Explicações contrafactuais — Molnar, cap. 15; Wachter et al. (2018) —
sobre **o modelo do curso** ([MODEL.md](../00-dataset/MODEL.md)). Os
módulos 01–03 perguntaram *"o que pesou?"*; este inverte: **"qual é a
menor mudança que muda a predição?"** — e a inversão muda o papel das
cercas: de diagnóstico de método doente para **restrição de busca**. E
aparece um sexto critério que o capítulo não formaliza: a
**acionabilidade**.

![Fração de pacientes de alto risco com contrafactual acionável, por banda](figures/cf_passo_3_painel.png)

## Objetivos de aprendizagem

Ao fim deste módulo você deve conseguir:

1. Formular a busca contrafactual como enumeração sobre movimentos
   declarados — e dizer quando exaustão vence busca genética.
2. Nomear os cinco critérios do cap. 15 (validade, proximidade,
   sparsidade, plausibilidade, diversidade) e apontar como cada um é
   operacionalizado — e medido — neste módulo.
3. Reconhecer o efeito Rashomon numa lista de contrafactuais válidos, e
   explicar por que o mais próximo pode ser inútil e o mais eficaz,
   absurdo.
4. Reportar honestamente o caso em que **não há** contrafactual — e por
   que essa é uma resposta do método, não uma falha dele.

## Por que este método fecha diferente

O contrafactual é o único método do curso cuja saída é um **paciente
hipotético** — e por isso é o único em que os critérios de qualidade são
sobre *pessoas*, não sobre curvas. O paciente é escolhido por regra
própria (p mais próximo de 0,8 no teste: contrafactual pede alguém com o
que perder — em p = 0,5 qualquer sopro cruza o limiar e a busca
degenera): um senhor de 81 anos, 3 doses, imunodeprimido e pneumopata.

## O que o módulo mostra

A perda de Wachter, **enumerada** (o espaço cabe: 113 mudanças simples,
6.129 pares — internals §1 confirma o ótimo sem recorte), com os cinco
critérios do capítulo operacionalizados um a um:

1. **O que a busca livre quer** (§2): a melhor mudança única é
   `idade → 10` — "rejuvenesça 71 anos" (p 0,804 → 0,480); as seguintes
   apagam sintomas ou trocam escolaridade por `desconhecido` (a
   armadilha da documentação do módulo 00). Só 3,5% cai na cerca: quem
   parte de um paciente real fabrica pouca ficção — contra 30,6% do
   LIME, pela mesma régua.
2. **A fronteira inteira** (§3): o passo 2 é a perda de Wachter vista
   por completo — validade × proximidade, cada ponto um candidato, sem
   escolher λ. Os melhores "válidos" pedem que o senhor seja uma criança
   sem imunodepressão ou uma gestante: *podem existir* (plausibilidade
   ≠ alcançabilidade — por que "curar" passa na cerca é medido nos
   internals §3: o portão é unidirecional no dado real, 0,54% declaram
   fator sem nomear comorbidade).
3. **O efeito Rashomon, impresso** (§4): dos 151 candidatos válidos,
   três histórias com features **disjuntas** — vire criança sem
   imunodepressão (p→0,18); apague a saturação e o registro de raça
   (p→0,34); conste como gestante de idade ignorada, aos 81 (p→0,40).
   Três receitas sem ingrediente em comum, todas "válidas" — qual você
   contaria ao paciente?
4. **As alavancas reais, no teste inteiro** (§5): com o que uma pessoa
   controla (doses para cima + declaração), o paciente do módulo não tem
   contrafactual — subir doses **aumenta** a p dele (0,829; o módulo 05
   §5 explica a atribuição). Dos 902 pacientes com p ≥ 0,5, **36% têm
   contrafactual acionável e 64% não têm** — e a fração cai com o risco:
   43% na banda 0,5–0,6, **3% no p ≥ 0,7**. Quem mais precisaria de uma
   saída é quem não tem nenhuma.
5. **Três filtros, três tabelas** (§6, formato do capítulo): o candidato
   **mais próximo** em Gower é o acionável que não cruza (0,0042); o
   mais eficaz está 10× mais longe e é absurdo. *Existir, estar perto,
   estar ao alcance* — e só o terceiro olha para o paciente real.

## O que o módulo conclui, e como isso é medido

- **A clareza do método tem preço, e ele é medido.** O cap. 15 diz, com
  razão, que a interpretação é limpa — "no additional assumptions and no
  magic in the background". O que o módulo acrescenta: sem uma lista de
  alavancas, o "smallest change" sem mágica devolve *"rejuvenesça 71
  anos"*. A ausência de suposições no método empurra as suposições para
  o desenho do espaço de busca — onde ficam visíveis, que é onde devem
  estar.
- **Exaustão vence genética quando o espaço cabe.** Cobertura completa,
  determinismo, custo de milissegundos; o recorte de legibilidade do
  walkthrough não esconde ótimo (internals §1). NSGA-II (Dandl et al.,
  2020) é o que faríamos se não coubesse; DiCE não roda no stack pinado
  (decisão com critério de falsificação no PR do pin).
- **A resposta mais importante é "não há X".** 64% do alto risco do
  teste — 97% na banda de maior risco — não tem contrafactual acionável,
  em nenhum limiar razoável (internals §4: 0,5 → 36%, 0,3 → 2,5%). Um
  método de explicação que só sabe prescrever precisa saber dizer isso.

## Aula

[`lecture/outline.md`](lecture/outline.md) — o que dizer, o que apontar,
as objeções a preparar. Módulo novo: não há deck histórico.

## Notebooks

- [`notebooks/cf_walkthrough.ipynb`](notebooks/cf_walkthrough.ipynb) — a
  aula: a perda de Wachter termo a termo, os cinco critérios, a busca em
  duas profundidades, o Rashomon, as alavancas e as tabelas. Amostra
  commitada, sem rede, ~10 s.
- [`notebooks/cf_internals.ipynb`](notebooks/cf_internals.ipynb) — o
  companheiro que prova: o espaço completo sem recorte, a invalidez
  decomposta por cerca, o portão unidirecional medido no dado real, e a
  sensibilidade do limiar. ~10 s.

As figuras commitadas estão em `figures/`; rodar os notebooks as
regenera em `notebooks/figures_generated/` (git-ignorado).

## Nota de configuração

Sem biblioteca de contrafactuais: o espaço declarado deste problema cabe
inteiro na memória, e busca exaustiva em lote dá cobertura completa com
zero sementes — determinismo que nenhum algoritmo genético oferece. A
`semana_epi` fica fora dos movimentos por ser atrelada a
`meses_desde_mar2020` (mover uma sem a outra fabricaria um calendário
impossível — a lição do módulo 03 aplicada ao desenho, antes de medir).

## Referências

- Molnar, C. *Interpretable Machine Learning*, 3ª ed. — [cap. 15 (Counterfactual Explanations)](https://christophm.github.io/interpretable-ml-book/counterfactual.html). (Livro-texto: a definição, os cinco critérios, o Rashomon e os métodos.)
- Wachter, S.; Mittelstadt, B.; Russell, C. (2018). [Counterfactual Explanations without Opening the Black Box](https://arxiv.org/abs/1711.00399). *Harvard JOLT 31(2)*. (A formulação por perda que o passo 2 enumera por inteiro.)
- Dandl, S.; Molnar, C.; Binder, M.; Bischl, B. (2020). [Multi-Objective Counterfactual Explanations](https://arxiv.org/abs/2004.11165). (NSGA-II sobre os quatro objetivos — o caminho quando a enumeração não cabe.)
- Mothilal, R. K.; Sharma, A.; Tan, C. (2020). [Explaining Machine Learning Classifiers through Diverse Counterfactual Explanations](https://doi.org/10.1145/3351095.3372850) (DiCE). *FAT\* 2020*. (A diversidade como objetivo; citado e não executado — a versão publicada não resolve contra o numpy 2.x pinado, decisão registrada no PR do pin.)
- Base, modelo, pacientes e cercas: módulo 00 ([MODEL.md](../00-dataset/MODEL.md), [gold/MANIFEST.md](../00-dataset/gold/MANIFEST.md)).
