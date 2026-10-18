# Módulo 06 — Partial Dependence Plot (PDP)

[![Walkthrough — Open In Colab](https://img.shields.io/badge/walkthrough-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/06-pdp/notebooks/pdp_walkthrough.ipynb)
[![Internals — Open In Colab](https://img.shields.io/badge/internals-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/06-pdp/notebooks/pdp_internals.ipynb)

*Autor: [William Bendinelli](https://github.com/wbendinelli) — SCC5819 (ICMC-USP). Material de estudo em português.*

Depois das atribuições locais do SHAP, retomamos as curvas ICE para perguntar como o preditor responde, em média, ao valor de uma entrada. Este é o estudo do capítulo 19 de Molnar sobre a mesma amostra SRAG/COVID e o mesmo XGBoost da série.

![Resultado principal do estudo Partial Dependence Plot (PDP)](figures/pdp-idade.png)

## Objetivos de aprendizagem

1. Construir o PDP como média de previsões após substituir uma entrada.
2. Reconhecer a igualdade entre PDP e média de ICE no mesmo fundo.
3. Auditar categorias impostas contra a definição da coorte.
4. Comparar fundos e distinguir dispersão entre fichas de incerteza da média.

## Por que explicar este modelo

O [módulo da base](../00-dataset/MODEL.md) estabelece o contrato SRAG/COVID e a receita histórica do XGBoost. O modelo é reconstruído sobre **200.000 registros de treino**, com treino até **2022**, validação em **2023** e teste em **2024**. O teste contém **16.142 registros**, com **2.945 óbitos**; o log loss reconstruído é **0,409020** (walkthrough §1).

O painel de explicação sorteia **512 fichas** do teste, após ordenar por `gold_id`, com semente **42**; suas primeiras **256 fichas** formam o fundo compartilhado. O alvo não orienta o sorteio. As análises do teste já observado são exploratórias. Não há nova seleção de modelo ou de intervenções clínicas (walkthrough §1).

## O que o módulo mostra

- **§1:** Contrato e reconstrução do preditor histórico, sem nova seleção.
- **§2:** Idade: matriz ICE, média marginal e dispersão entre fichas.
- **§3:** Saturação baixa: categorias nativas e auditoria da coorte.
- **§4:** Sensibilidade da curva ao fundo amostrado e ao teste completo.

**O caso.** O mesmo preditor da série e a amostra Gold commitada. As perturbações são avaliações artificiais da função, não novos registros observados. A saída explicada é a probabilidade de óbito. A seleção hospitalar, as restrições do formulário e a dependência entre entradas limitam a leitura.

## O que o módulo conclui, e como isso é medido

- **O código reproduz a biblioteca.** A integração manual e o cálculo `brute` do scikit-learn diferem no máximo em **3,6263×10⁻⁸** na média de probabilidades; as previsões individuais coincidem (internals §2). A precisão de acumulação é explicitada.

- **A substituição pode sair do recorte SRAG.** No fundo de **256 fichas**, impor saturação baixa como `nao` ou `desconhecido` gera **16 fichas fora da coorte** em cada cenário; impor `sim` não gera essas violações (walkthrough §3). A mudança não é um paciente observado.

- **O fundo importa.** A maior diferença entre a curva do fundo e a do teste inteiro nesta grade é **0,4474 p.p.** (walkthrough §4). Isso mede aproximação de integração nesta execução, sem validar extrapolações.

- **PDP plano não prova ausência de uso.** No controle multiplicativo, o PDP tem amplitude **0,00000000**, enquanto a maior amplitude ICE é **2,0000** (internals §3).

## Auditoria frente ao livro e ao código

**Parecer: cálculo e aplicação coerentes com o capítulo, sob a referência declarada.** A redução traduzida de `run.pdp` de iml coincide com a média explícita; o scikit-learn também confere a integração e as ICE (internals §2 e §4). A grade quantílica é uma escolha do curso, enquanto o padrão do PDP de iml é equidistante. A faixa das ICE descreve dispersão, não incerteza da média. As violações de elegibilidade ao impor saturação continuam visíveis (walkthrough §3).

A auditoria corrigiu o truncamento de valores fracionários quando uma intervenção recebe uma coluna inteira. As idades usadas neste estudo já são ponto flutuante; as medições publicadas permanecem válidas (internals §4).

**Síntese da base.** A integridade da amostra Gold é conferida por SHA256. O teste temporal completo, o painel e o fundo têm seus tamanhos, óbitos, previsões médias, quantis de idade, estados de saturação, ausências e elegibilidade impressos lado a lado; identificadores únicos e separação treino/teste também são verificados (walkthrough §5). A aplicação usa a amostra commitada do projeto, não a extração bruta inteira. Usar o teste observado como referência torna a leitura exploratória; não há seleção de modelo nessa etapa.

**Escopo da conferência.** Foram lidos o texto, os exemplos executáveis do livro e a implementação de iml nas revisões fixadas nas referências abaixo. O pacote R não foi executado nesta auditoria: os internals identificam as traduções para Python e distinguem concordância de algoritmo de reprodução nativa. Controles sintéticos e verificações algébricas sustentam o cálculo; plausibilidade clínica e efeitos causais não são certificados por esses controles.

**Figuras.** Os cadernos usam o perfil SAPIANS Global / VITA: branco, preto SAPIANS, cinzas neutros, linhas e marcadores distintos, superfícies planas e títulos com peso moderado. A procedência dos papéis visuais e a reprodução tipográfica estão no [guia das ferramentas](../../tools/README.md#perfil-global-sapians--vita).

## Aula

- [Roteiro da aula](lecture/outline.md): leitura das figuras, perguntas e limites.
- Próximo estudo na sequência do livro: [ALE](../07-ale/README.md).

## Cadernos

- [Walkthrough](notebooks/pdp_walkthrough.ipynb): aplicação e figuras com resultados impressos.
- [Internals](notebooks/pdp_internals.ipynb): cálculos independentes, controles e condições de validade.

As figuras publicadas em `figures/` são cópias explícitas das saídas do walkthrough e do internals. Cada execução escreve os novos arquivos em `figures_generated/` dentro de uma pasta temporária externa ao repositório; os caminhos de trabalho não são gravados nas saídas.

## Configuração e limites

Integração empírica explícita na probabilidade de óbito, sem interpolação. A idade usa **21 pontos** entre os quantis de **2% e 98%** do painel; os quantis estão definidos no código e os limites da grade são impressos (walkthrough §2). A faixa das ICE é de quantis **10 e 90**, não um intervalo de confiança. Na comparação com scikit-learn, forçamos `method="brute"`, `response_method="predict_proba"` e `custom_values`, para que biblioteca e núcleo recebam a mesma grade (internals §2).

Os núcleos estão em [srag_71_global_effects.py](../../tools/srag_71_global_effects.py), e o walkthrough mostra o código executado. Não adicionamos dependências: a aplicação usa a pilha fixada em [requirements.lock](../../requirements.lock). A referência histórica permanece a mesma adotada pela PFI; adotar outro preditor exige recalcular os resultados.

## Referências

- Molnar, C. *Interpretable Machine Learning* — [cap. 19: Partial Dependence Plot (PDP)](https://christophm.github.io/interpretable-ml-book/pdp.html). (Mecanismo e limites da interpretação.)
- Friedman, J. H. (2001). [Greedy Function Approximation: A Gradient Boosting Machine](https://doi.org/10.1214/aos/1013203451). (Dependência parcial.)
- scikit-learn. [partial_dependence](https://scikit-learn.org/stable/modules/generated/sklearn.inspection.partial_dependence.html). (Integração brute e previsões individuais.)

- [Fonte do capítulo no GitHub](https://github.com/christophM/interpretable-ml-book/blob/8f470c85e5ed4ebd69de74425cb9832f1bdc25eb/manuscript/pdp.qmd), revisão `8f470c85e5ed4ebd69de74425cb9832f1bdc25eb`.
- [Implementação de iml](https://github.com/giuseppec/iml/blob/4818c8f81dea2e76318857fbc3d50bc78cdd22f6/R/FeatureEffect.R), revisão `4818c8f81dea2e76318857fbc3d50bc78cdd22f6`.
