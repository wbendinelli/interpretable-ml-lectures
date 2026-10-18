# Módulo 09 — Functional Decomposition

[![Walkthrough — Open In Colab](https://img.shields.io/badge/walkthrough-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/09-functional-decomposition/notebooks/decomposition_walkthrough.ipynb)
[![Internals — Open In Colab](https://img.shields.io/badge/internals-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/09-functional-decomposition/notebooks/decomposition_internals.ipynb)

*Autor: [William Bendinelli](https://github.com/wbendinelli) — SCC5819 (ICMC-USP). Material de estudo em português.*

No capítulo 22 de Molnar, decompor uma função exige regras que identifiquem seus componentes. Aplicamos ANOVA funcional à superfície de dependência parcial idade × saturação do XGBoost SRAG/COVID, sob pesos produto explícitos. O objeto decomposto é essa superfície marginalizada e discretizada, não o preditor inteiro.

![Resultado principal do estudo Functional Decomposition](figures/decomposition-componentes.png)

## Objetivos de aprendizagem

1. Declarar a função e a medida sobre a qual ela será decomposta.
2. Separar intercepto, efeitos principais e interação com centralização ponderada.
3. Conferir reconstrução, médias condicionais nulas e identidade de variâncias.
4. Distinguir a referência produto da distribuição conjunta observada.

## Por que explicar este modelo

O [módulo da base](../00-dataset/MODEL.md) estabelece o contrato SRAG/COVID e a receita histórica do XGBoost. O modelo é reconstruído sobre **200.000 registros de treino**, com treino até **2022**, validação em **2023** e teste em **2024**. O teste contém **16.142 registros**, com **2.945 óbitos**; o log loss reconstruído é **0,409020** (walkthrough §1).

O painel de explicação sorteia **512 fichas** do teste, após ordenar por `gold_id`, com semente **42**; suas primeiras **256 fichas** formam o fundo compartilhado. O alvo não orienta o sorteio. As análises do teste já observado são exploratórias. Não há nova seleção de modelo ou de intervenções clínicas (walkthrough §1).

## O que o módulo mostra

- **§1:** O preditor histórico e as amostras compartilhadas.
- **§2:** Grade, pesos, componentes e identidade de variâncias.
- **§3:** Visualização e reconstrução da superfície.
- **§4:** Mudança da medida de referência e diagnóstico da conjunta.

**O caso.** O mesmo preditor da série e a amostra Gold commitada. As perturbações são avaliações artificiais da função, não novos registros observados. A saída explicada é a probabilidade de óbito. A seleção hospitalar, as restrições do formulário e a dependência entre entradas limitam a leitura.

## O que o módulo conclui, e como isso é medido

- **A reconstrução é conferida ponto a ponto.** A superfície usa **8 idades representativas** e **3 estados de saturação**; o erro máximo de reconstrução é impresso e verificado por uma tolerância explícita (walkthrough §2; internals §3). Isso não valida uma aproximação do modelo completo.

- **A interação é uma parcela da variância desta superfície.** Sob o produto das marginais discretizadas, sua fração é **0,015341**, e a soma das parcelas de variância coincide com **0,0122997211** (walkthrough §2). Esses valores não descrevem a variância de prognósticos da população hospitalizada.

- **Mudar a referência muda os componentes.** O intercepto passa de **0,22031385** sob o produto das marginais para **0,19829438** sob o produto uniforme; ambas as decomposições recompõem a mesma superfície (walkthrough §4).

- **A distribuição conjunta é outra referência.** A distância de variação total entre a conjunta discretizada do painel e o produto é **0,072266** (walkthrough §4). A identidade de variâncias sob o produto não é transferida à conjunta.

## Auditoria frente ao livro e ao código

**Parecer: decomposição produto correta para a superfície declarada; alcance restrito.** O exemplo inicial do capítulo usa ALE, e o capítulo também desenvolve ANOVA funcional e a extensão para dependência. Aqui escolhemos ANOVA funcional sob medida produto de uma PD conjunta discretizada. Os componentes analíticos da função sintética e os laços independentes conferem as restrições de identificação (internals §2–§4). Não se trata da reprodução da figura ALE do livro ou da decomposição completa do XGBoost.

A auditoria refaz a superfície com **4, 8 e 16 grupos de idade** e fundos de **256 e 512 fichas**. As parcelas mudam com a grade e a integração, embora cada tabela seja reconstruída dentro da tolerância (walkthrough §6). O resultado principal de **0,015341** para a fração de interação continua condicionado à grade e à medida produto originais (walkthrough §2). Não é a fração de variância explicada por interação na população observada.

**Síntese da base.** A integridade da amostra Gold é conferida por SHA256. O teste temporal completo, o painel e o fundo têm seus tamanhos, óbitos, previsões médias, quantis de idade, estados de saturação, ausências e elegibilidade impressos lado a lado; identificadores únicos e separação treino/teste também são verificados (walkthrough §5). A aplicação usa a amostra commitada do projeto, não a extração bruta inteira. Usar o teste observado como referência torna a leitura exploratória; não há seleção de modelo nessa etapa.

**Escopo da conferência.** Foram lidos o texto, os exemplos executáveis do livro e a implementação de iml nas revisões fixadas nas referências abaixo. O pacote R não foi executado nesta auditoria: os internals identificam as traduções para Python e distinguem concordância de algoritmo de reprodução nativa. Controles sintéticos e verificações algébricas sustentam o cálculo; plausibilidade clínica e efeitos causais não são certificados por esses controles.

**Figuras.** Os cadernos usam o perfil SAPIANS Global / VITA: branco, preto SAPIANS, cinzas neutros, linhas e marcadores distintos, superfícies planas e títulos com peso moderado. A procedência dos papéis visuais e a reprodução tipográfica estão no [guia das ferramentas](../../tools/README.md#perfil-global-sapians--vita).

## Aula

- [Roteiro da aula](lecture/outline.md): leitura das figuras, perguntas e limites.
- Próximo estudo na sequência do livro: [PFI](../10-pfi/README.md).

## Cadernos

- [Walkthrough](notebooks/decomposition_walkthrough.ipynb): aplicação e figuras com resultados impressos.
- [Internals](notebooks/decomposition_internals.ipynb): cálculos independentes, controles e condições de validade.

As figuras publicadas em `figures/` são cópias explícitas das saídas do walkthrough e do internals. Cada execução escreve os novos arquivos em `figures_generated/` dentro de uma pasta temporária externa ao repositório; os caminhos de trabalho não são gravados nas saídas.

## Configuração e limites

A idade é discretizada em **8 grupos por quantis**, representados por suas medianas; saturação mantém **3 categorias**. O fundo integra conjuntamente as entradas complementares do preditor. Na grade do par, os pesos são o produto das marginais discretizadas do painel, normalizados explicitamente. A comparação uniforme altera somente esses pesos. Não implementamos ANOVA funcional generalizada para dependência, uma decomposição de todas as entradas, nem interações de ordens superiores. O controle sintético e os laços independentes verificam a decomposição escolhida (internals §2–§3).

Os efeitos principais deste módulo são médias da própria superfície sob os pesos escolhidos. Eles não coincidem automaticamente com os PDPs simples usados no H, que integram sobre o fundo e são centralizados nos pares observados. A fração de variância da interação aqui e o H² do módulo anterior têm definições e ponderações diferentes.

Os núcleos estão em [srag_71_global_effects.py](../../tools/srag_71_global_effects.py), e o walkthrough mostra o código executado. Não adicionamos dependências: a aplicação usa a pilha fixada em [requirements.lock](../../requirements.lock). A referência histórica permanece a mesma adotada pela PFI; adotar outro preditor exige recalcular os resultados.

## Referências

- Molnar, C. *Interpretable Machine Learning* — [cap. 22: Functional Decomposition](https://christophm.github.io/interpretable-ml-book/decomposition.html). (Mecanismo e limites da interpretação.)
- Hooker, G. (2007). [Generalized Functional ANOVA Diagnostics for High-Dimensional Functions of Dependent Variables](https://doi.org/10.1198/106186007X237892). (Por que a distribuição de referência e a dependência importam; a extensão generalizada não é implementada aqui.)

- [Fonte do capítulo no GitHub](https://github.com/christophM/interpretable-ml-book/blob/8f470c85e5ed4ebd69de74425cb9832f1bdc25eb/manuscript/decomposition.qmd), revisão `8f470c85e5ed4ebd69de74425cb9832f1bdc25eb`.
