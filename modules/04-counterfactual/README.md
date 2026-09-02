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
degenera): um paciente de 32 anos — não um idoso —, 4 doses, com
síndrome de Down, doença neurológica, imunodepressão e doença renal.

## O que o módulo mostra

A perda de Wachter, **enumerada** (o espaço cabe: 113 mudanças simples,
6.129 pares — internals §1 confirma o ótimo sem recorte), com os cinco
critérios do capítulo operacionalizados um a um:

1. **O que a busca livre quer** (§2): a melhor mudança única é
   `saturacao → nao` — apagar do prontuário a saturação baixa, que é
   consequência da doença (p 0,793 → 0,571); logo atrás vêm `idade → 10`
   (dos 32 aos 10 anos) e recuar o calendário para o mês 6, que cai na
   cerca. E `imunodepre → desconhecido` e `out_morbi → desconhecido`
   entram nas dez: apagar o registro derruba a p quase tanto quanto
   curar (a armadilha da documentação do módulo 00). Só 3,5% dos 113
   movimentos cai na cerca: quem parte de um paciente real fabrica pouca
   ficção — contra 30,6% do LIME, pela mesma régua. E nenhuma mudança
   única, sozinha, cruza 0,5.
2. **A fronteira inteira** (§3): o passo 2 é a perda de Wachter vista
   por completo — validade × proximidade, cada ponto um candidato, sem
   escolher λ. Os melhores "válidos" pedem que ele volte ao mês 6 da
   pandemia sem nenhuma dose, ou que apague a saturação e vire criança:
   *podem existir* (plausibilidade ≠ alcançabilidade). E o primeiro
   mostra um par escapando de uma cerca de que o movimento simples não
   escapava — recuar o calendário sozinho é pré-campanha; recuá-lo com
   zero doses, não. Por que "curar" passa na cerca é medido nos
   internals §3: o portão é unidirecional no dado real, 0,54% declaram
   fator sem nomear comorbidade.
3. **O efeito Rashomon, impresso** (§4): dos 68 candidatos válidos,
   três histórias com features **disjuntas** — recue o calendário para o
   mês 6 e zere as doses (p→0,199); apague a saturação e vire criança de
   10 anos (p→0,316); cure a imunodepressão e o desconforto respiratório
   (p→0,452). Três receitas sem ingrediente em comum, todas "válidas" —
   qual você contaria ao paciente?
4. **As alavancas reais, no teste inteiro** (§5): com o que uma pessoa
   controla (doses para cima + declaração), o paciente do módulo não tem
   contrafactual — os dois candidatos acionáveis que ele tem deixam a p
   em 0,793, onde ela já estava (o módulo 05 §5 mede a atribuição
   positiva das doses). Dos 624 pacientes com p ≥ 0,5, **30,3% têm
   contrafactual acionável e 69,7% não têm** — e a fração cai com o
   risco: 35% na banda 0,5–0,6, **0% no p ≥ 0,7**, onde nenhum dos 19
   tem saída. Quem mais precisaria de uma saída é quem não tem nenhuma.
5. **Três filtros, três tabelas** (§6, formato do capítulo): o candidato
   **mais próximo** em Gower é o acionável que não cruza (0,0042); o
   mais eficaz está oito vezes mais longe (0,0339) e é absurdo.
   *Existir, estar perto, estar ao alcance* — e só o terceiro olha para
   o paciente real.

## O que o módulo conclui, e como isso é medido

- **A clareza do método tem preço, e ele é medido.** O cap. 15 diz, com
  razão, que a interpretação é limpa — "no additional assumptions and no
  magic in the background". O que o módulo acrescenta: sem uma lista de
  alavancas, o "smallest change" sem mágica devolve *"apague do
  prontuário a saturação baixa"* e, logo atrás, *"volte a ter 10 anos"*.
  A ausência de suposições no método empurra as suposições para
  o desenho do espaço de busca — onde ficam visíveis, que é onde devem
  estar.
- **Exaustão vence genética quando o espaço cabe.** Cobertura completa,
  determinismo, custo de milissegundos; o recorte de legibilidade do
  walkthrough não esconde ótimo (internals §1). NSGA-II (Dandl et al.,
  2020) é o que faríamos se não coubesse; DiCE não roda no stack pinado
  (decisão com critério de falsificação no PR do pin).
- **A resposta mais importante é "não há X".** 69,7% do alto risco do
  teste — e todos os 19 da banda de maior risco — não tem contrafactual
  acionável, em nenhum limiar razoável (internals §4: 0,5 → 30,3%,
  0,3 → 1,1%). Um método de explicação que só sabe prescrever precisa
  saber dizer isso.

Todos os números acima são do modelo do curso adotado em 2026-09-01 (800
árvores, profundidade 4, lr 0,05 — módulo 00, SELECTION.md); a versão
anterior deste módulo os media no modelo de 400 árvores / profundidade 5,
e a regra "p mais próximo de 0,8" caía em outro paciente (gold_id
1267430, de 81 anos). O deslocamento é de condicionamento, não de
falsificação; as afirmações que a medição derrubou estão listadas abaixo.

### O que ficou registrado como corrigido

A barra de evidência (regra 3) manda o valor antigo ficar no registro
quando a medição derruba a prosa. As deste re-sync:

- **A busca livre não pede mais "rejuvenesça 71 anos".** A prosa dizia
  que a melhor mudança única era `idade → 10` no paciente de 81 anos
  (p 0,804 → 0,480); a regra "p ≈ 0,8" agora cai num paciente de 32 anos
  e a melhor mudança única é `saturacao → nao` (walkthrough §2,
  p 0,793 → 0,571). A lição — a menor mudança é algo que ninguém pode
  fazer — sobreviveu; o exemplo mudou de figura.
- **Nenhuma mudança única cruza mais o limiar.** Antes havia 1; mede 0
  (walkthrough §2). A busca só encontra contrafactual válido em
  profundidade 2.
- **O gradiente por banda é mais duro do que a prosa dizia.** Dizia
  43% → 25% → 3%; mede 35% → 15% → **0%** (walkthrough §5). Na banda de
  maior risco não é "quase ninguém": é ninguém — 19 pacientes, nenhuma
  saída. O "97% na banda de maior risco" desta página vira 100%.
- **As frações de cobertura caíram.** 36% com contrafactual acionável e
  64% sem, sobre 902 pacientes, medem agora 30,3% e 69,7% sobre 624
  (walkthrough §5); por limiar, 0,4 → 16,2% mede 9,3%, e 0,3 → 2,5% mede
  1,1% (internals §4).
- **Subir doses não aumenta mais a p deste paciente.** A prosa dizia que
  aumentava (0,829); mede 0,793 → 0,793 — não cruza e não move a
  previsão na terceira casa (walkthrough §5). O que continua de pé é a
  resposta "não há contrafactual acionável para ele".
- **O contrafactual mais eficaz está oito vezes mais longe, não dez.**
  Gower 0,0400 → **0,0339**, contra os 0,0042 do acionável, que não se
  moveu (walkthrough §6).

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
