# Módulo 08 — Feature Interaction

[![Walkthrough — Open In Colab](https://img.shields.io/badge/walkthrough-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/08-feature-interaction/notebooks/interaction_walkthrough.ipynb)
[![Internals — Open In Colab](https://img.shields.io/badge/internals-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/08-feature-interaction/notebooks/interaction_internals.ipynb)

*Autor: [William Bendinelli](https://github.com/wbendinelli) — SCC5819 (ICMC-USP). Material de estudo em português.*

Depois dos efeitos principais, o capítulo 21 de Molnar pergunta onde a resposta do modelo deixa de ser aditiva. Calculamos a estatística H de Friedman–Popescu em pares declarados do mesmo caso SRAG/COVID e examinamos o resíduo, o denominador e a escala.

![Resultado principal do estudo Feature Interaction](figures/interaction-h.png)

## Objetivos de aprendizagem

1. Definir interação como dependência entre efeitos na escala explicada.
2. Construir H e H² a partir de dependências parciais centralizadas.
3. Ler a razão junto do numerador e do denominador.
4. Verificar casos aditivo, multiplicativo e degenerado e a transformação de escala.

## Por que explicar este modelo

O [módulo da base](../00-dataset/MODEL.md) estabelece o contrato SRAG/COVID e a receita histórica do XGBoost. O modelo é reconstruído sobre **200.000 registros de treino**, com treino até **2022**, validação em **2023** e teste em **2024**. O teste contém **16.142 registros**, com **2.945 óbitos**; o log loss reconstruído é **0,409020** (walkthrough §1).

O painel de explicação sorteia **512 fichas** do teste, após ordenar por `gold_id`, com semente **42**; suas primeiras **256 fichas** formam o fundo compartilhado. O alvo não orienta o sorteio. As análises do teste já observado são exploratórias. Não há nova seleção de modelo ou de intervenções clínicas (walkthrough §1).

## O que o módulo mostra

- **§1:** Reconstrução do modelo, fundo e painel.
- **§2:** H nos pares observados e seus termos.
- **§3:** Superfície idade × saturação e resíduo aditivo.
- **§4:** Sensibilidade ao fundo e aos pontos avaliados.

**O caso.** O mesmo preditor da série e a amostra Gold commitada. As perturbações são avaliações artificiais da função, não novos registros observados. A saída explicada é a probabilidade de óbito. A seleção hospitalar, as restrições do formulário e a dependência entre entradas limitam a leitura.

## O que o módulo conclui, e como isso é medido

- **Os pares têm razões diferentes.** Com **64 pontos observados** e fundo de **256 fichas**, H é **0,11656777** para idade × saturação, **0,04823381** para idade × cardiopatia e **0,15279630** para cardiopatia × diabetes, na escala de probabilidade (walkthrough §2).

- **A razão não ordena a magnitude absoluta do resíduo.** O numerador para cardiopatia × diabetes é **0,00000058**, enquanto o de idade × saturação é **0,00013024**; o denominador também é muito menor no primeiro par (walkthrough §2). Não é ranking de importância.

- **Os controles conferem os casos conhecidos.** A função aditiva produz H **0,00000000**, o produto simétrico produz **1,00000000**, e a função constante retorna razão indefinida (internals §2).

- **A escala faz parte da definição.** A transformação logística de um escore aditivo gera H positivo no controle, sem retreino; os valores são impressos lado a lado (internals §3).

## Auditoria frente ao livro e ao código

**Parecer: fórmula de H correta; aplicação exploratória com sensibilidade de amostragem explícita.** A tradução de `h.test` de iml e o laço independente conferem a estatística, com os mesmos PDPs e a mesma centralização (internals §2 e §4). O fundo e os pontos avaliados têm orçamentos separados; isso é uma adaptação da configuração do pacote. O núcleo acrescenta uma tolerância absoluta para denominador quase nulo, mantém a razão indefinida e não trunca H.

A auditoria amplia a sensibilidade para **5 sorteios**, com **256 fichas de fundo** e **128 pontos** por sorteio. H de idade × saturação varia de **0,11934979 a 0,13456697**; idade × cardiopatia, de **0,04120961 a 0,05171211**; cardiopatia × diabetes, de **0,13258071 a 0,15240359** (walkthrough §6). São faixas descritivas de configurações sorteadas, não intervalos de confiança. Uma razão maior pode ter resíduo absoluto menor; a leitura exige numerador e denominador.

**Síntese da base.** A integridade da amostra Gold é conferida por SHA256. O teste temporal completo, o painel e o fundo têm seus tamanhos, óbitos, previsões médias, quantis de idade, estados de saturação, ausências e elegibilidade impressos lado a lado; identificadores únicos e separação treino/teste também são verificados (walkthrough §5). A aplicação usa a amostra commitada do projeto, não a extração bruta inteira. Usar o teste observado como referência torna a leitura exploratória; não há seleção de modelo nessa etapa.

**Escopo da conferência.** Foram lidos o texto, os exemplos executáveis do livro e a implementação de iml nas revisões fixadas nas referências abaixo. O pacote R não foi executado nesta auditoria: os internals identificam as traduções para Python e distinguem concordância de algoritmo de reprodução nativa. Controles sintéticos e verificações algébricas sustentam o cálculo; plausibilidade clínica e efeitos causais não são certificados por esses controles.

**Figuras.** Os cadernos usam o perfil SAPIANS Global / VITA: branco, preto SAPIANS, cinzas neutros, linhas e marcadores distintos, superfícies planas e títulos com peso moderado. A procedência dos papéis visuais e a reprodução tipográfica estão no [guia das ferramentas](../../tools/README.md#perfil-global-sapians--vita).

## Aula

- [Roteiro da aula](lecture/outline.md): leitura das figuras, perguntas e limites.
- Próximo estudo na sequência do livro: [Decomposição funcional](../09-functional-decomposition/README.md).

## Cadernos

- [Walkthrough](notebooks/interaction_walkthrough.ipynb): aplicação e figuras com resultados impressos.
- [Internals](notebooks/interaction_internals.ipynb): cálculos independentes, controles e condições de validade.

As figuras publicadas em `figures/` são cópias explícitas das saídas do walkthrough e do internals. Cada execução escreve os novos arquivos em `figures_generated/` dentro de uma pasta temporária externa ao repositório; os caminhos de trabalho não são gravados nas saídas.

## Configuração e limites

Pares declarados: idade × saturação, idade × cardiopatia e cardiopatia × diabetes. Integramos sobre o fundo compartilhado e avaliamos os PDPs nos **64 primeiros registros** do painel sorteado; não calculamos H numa grade cartesiana artificial. Cada PDP é centralizado nesses mesmos pontos. Denominador abaixo da tolerância explícita retorna `NaN`; não convertemos a degeneração em ausência de interação, nem truncamos H à unidade. A grade do mapa serve apenas à visualização (walkthrough §3).

Os núcleos estão em [srag_71_global_effects.py](../../tools/srag_71_global_effects.py), e o walkthrough mostra o código executado. Não adicionamos dependências: a aplicação usa a pilha fixada em [requirements.lock](../../requirements.lock). A referência histórica permanece a mesma adotada pela PFI; adotar outro preditor exige recalcular os resultados.

## Referências

- Molnar, C. *Interpretable Machine Learning* — [cap. 21: Feature Interaction](https://christophm.github.io/interpretable-ml-book/interaction.html). (Mecanismo e limites da interpretação.)
- Friedman, J. H.; Popescu, B. E. (2008). [Predictive Learning via Rule Ensembles](https://doi.org/10.1214/07-AOAS148). (Estatística H.)

- [Fonte do capítulo no GitHub](https://github.com/christophM/interpretable-ml-book/blob/8f470c85e5ed4ebd69de74425cb9832f1bdc25eb/manuscript/interaction.qmd), revisão `8f470c85e5ed4ebd69de74425cb9832f1bdc25eb`.
- [Implementação de iml](https://github.com/giuseppec/iml/blob/4818c8f81dea2e76318857fbc3d50bc78cdd22f6/R/Interaction.R), revisão `4818c8f81dea2e76318857fbc3d50bc78cdd22f6`.
