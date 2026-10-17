# Módulo 06 — Permutation Feature Importance

[![Walkthrough — Open In Colab](https://img.shields.io/badge/walkthrough-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/06-pfi/notebooks/pfi_walkthrough.ipynb)
[![Internals — Open In Colab](https://img.shields.io/badge/internals-open%20in%20Colab-F9AB00?logo=googlecolab)](https://colab.research.google.com/github/wbendinelli/interpretable-ml-lectures/blob/main/modules/06-pfi/notebooks/pfi_internals.ipynb)

*Autor do módulo: [William Bendinelli](https://github.com/wbendinelli) — SCC5819 (ICMC-USP). Material de estudo em português; apresentação interativa em inglês.*

**Permutation Feature Importance (PFI)** — Molnar, capítulo 23 na edição
usada pela disciplina — sobre a [referência histórica XGBoost](../00-dataset/MODEL.md).
Os módulos anteriores explicavam predições e atribuições; aqui a pergunta é
global: **quanto o erro desse modelo muda quando embaralhamos uma entrada?**
O preditor continua fixo, e a importância depende do erro escolhido e dos
registros avaliados.

**Comparação concluída na amostra:** o [estudo de balanceamento](../00-dataset/COURSE_STUDY.md)
mantém a amostra de treino e ajusta os hiperparâmetros de cada estratégia por
log loss de validação; a configuração original continuou sendo a melhor
opção registrada sob esse critério. A execução com treino completo foi
interrompida antes da seleção. Os números e a apresentação abaixo
continuam identificados com a referência histórica. Os cadernos adicionais
da PFI de outra referência, listados ao final, só apresentam resultados quando recebem o
agregado completo do modelo finalizado; não reaproveitam as importâncias antigas.

![Erro original e erro após permutar as entradas de maior PFI no teste temporal](figures/antes-depois-top10.png)

## Objetivos de aprendizagem

Ao fim deste módulo você deve conseguir:

1. Seguir o experimento: avaliar os dados originais, copiar a matriz,
   permutar uma coluna, prever com o mesmo modelo e medir o novo erro.
2. Ler log loss, diferença, razão e ranking, distinguindo uma permutação
   isolada da média das repetições.
3. Explicar o que o desvio padrão entre embaralhamentos cobre e por que
   ele não é um intervalo de confiança populacional.
4. Distinguir permutação marginal, conjunta e dentro de subgrupos,
   delimitando a pergunta respondida por cada uma.

## Por que explicar este modelo

A série usa a coorte hospitalizada de COVID com desfechos fechados do
SIVEP-Gripe/SRAG, tratada pelo módulo 00. A separação é temporal: treino
até 2022, validação em 2023 e avaliação histórica em 2024. O modelo de
referência não recebe pesos de classe nem reamostragem; o estudo de
balanceamento é separado e não o substitui (walkthrough §1).

O teste contém **16.142 registros**, incluindo **2.945 óbitos**, e o
log loss original é **0,4090** (walkthrough §1–§2). A PFI pergunta de quais
entradas esse desempenho depende. Como o teste já havia sido observado,
esta é uma explicação **exploratória**, não uma nova seleção de modelo.

## O que o módulo mostra

- **Protocolo e erro original** (§1–§2): fonte, tratamento, separação
  temporal, escolha do modelo e leitura do erro de probabilidades.
- **Uma coluna por vez** (§3): idade e saturação baixa, sempre restaurando
  a matriz original antes do experimento seguinte. O notebook exibe o
  código que realmente executa a operação.
- **Repetição e ranking** (§4–§5): antes/depois, distribuição dos erros,
  variação da posição e escalas de diferença e razão. A média usa
  **50 permutações por entrada**, com semente **42** (walkthrough §1).
- **Um exemplo de dependência** (§6): cardiopatia e diabetes, comparadas
  individualmente, movidas como par e permutadas dentro dos estados de
  diabetes. As operações têm perguntas diferentes.
- **Leitura final** (§7): o vínculo com Molnar e os limites da conclusão.
- **Sensibilidade à métrica** (§8): comparar Brier, log loss, MAE e AUC nas
  mesmas previsões e conferir também o exemplo de dependência.

**O caso.** A animação mostra **oito fichas receptoras reais**, conservadas
do exemplo histórico, como uma janela da **primeira permutação global**.
Os doadores vêm de todo o teste temporal, usando a ordem registrada com
semente **42**; não embaralhamos apenas as linhas visíveis. As fichas foram
selecionadas pelos primeiros registros adultos de cada desfecho, sem escolher
pelas previsões. O gráfico usa o erro **global**: referência, média e desvio
padrão das **50 repetições**, com a primeira repetição identificada à parte.
A perda das fichas receptoras fica apenas na auditoria do caderno e não
estima desempenho global (walkthrough §3).

Os valores originais são reais; a ficha permutada é uma combinação artificial
usada para testar o modelo. A idade recebida de outro registro não passa a
ser a idade observada daquela pessoa. Outras entradas e o desfecho permanecem
fixos. Idade usa anos decimais, e Unknown permanece uma categoria explícita.

## O que o módulo conclui, e como isso é medido

Para preparar a fala, abra o [guia do professor em português](lecture/pfi-interactive/teacher-guide.html):
conferência dos valores, leitura do log loss com uma ficha real e roteiro de cada tela.
Seu texto editável está no [roteiro da aula](lecture/outline.md).

**A escolha da métrica da aula.** O
[estudo Brier, log loss, MAE e AUC](lecture/metric-comparison.html) conserva
modelo, teste e ordens. Brier e log loss têm as mesmas dez entradas no
topo; idade e saturação baixa permanecem nas primeiras posições. AUC
compartilha nove dessas dez e muda mais as posições inferiores
(walkthrough §8). O estudo inclui o exemplo final de dependência e
documenta a escolha de log loss adotada na apresentação. As outras
métricas permanecem no estudo como análise de sensibilidade.

MAE usa aqui probabilidades contínuas contra o desfecho binário, sem corte.
Ele pode ser calculado, mas não é a referência principal para a qualidade
das probabilidades: a perda absoluta procura a mediana do desfecho, e pode
preferir previsões extremas. O walkthrough inclui comparadores constantes
para tornar essa limitação visível (§8). A recomendação para conduzir a
aula é log loss, por adequação à classificação e vínculo com Molnar;
Brier e AUC permanecem conferências complementares.

- **Idade lidera o ranking de aumento médio do log loss neste protocolo.**
  Sua diferença é **0,0846**, com desvio padrão **0,0027** entre os
  embaralhamentos. Para saturação baixa, a diferença é **0,0121**, com
  desvio padrão **0,0009** (walkthrough §4–§5). Isso descreve dependência
  preditiva do modelo avaliado, não relevância causal ou clínica.
- **Diferença e razão dão o mesmo ranking neste experimento.** O erro
  original positivo é comum às entradas. O notebook calcula as duas
  escalas com precisão completa antes de arredondar a leitura (§5).
- **A dispersão é condicional ao modelo e aos registros.** As repetições
  variam as ordens das colunas; não reamostram pacientes nem treinam
  novos modelos. O notebook diferencia SD, erro de Monte Carlo e
  bigodes de boxplot (§4–§5).
- **O tratamento da dependência muda a pergunta.** O par conjunto
  preserva cardiopatia/diabetes entre si, mas pode romper relações com
  outras entradas. O embaralhamento de cardiopatia dentro dos estados
  de diabetes mantém esse agrupamento, sem implementar a distribuição
  condicional dada toda a ficha. A agregação por tamanho dos grupos é
  conferida em cada repetição (§6).

## O que a literatura propõe fazer a respeito

Molnar apresenta a PFI condicional e a abordagem por subgrupos para
lidar com entradas dependentes. Este módulo implementa o exemplo por
estados de diabetes; a permutação conjunta é um diagnóstico complementar.
Ambos conservam limitações, explicitadas no walkthrough §6–§7. O capítulo
norteia a interpretação; a sequência visual adapta a aula de Raschka.
[Molnar, capítulo 23](https://christophm.github.io/interpretable-ml-book/feature-importance.html).

## Aula

- **[Apresentação interativa](lecture/pfi-interactive/index.html#slide-cover)** —
  sequência em inglês, com motion, fichas didáticas reais e resultados globais.
- **[Roteiro vivo](lecture/outline.md)** — o que dizer, para onde apontar
  e as perguntas que delimitam cada conclusão.

Para abrir a versão canônica, sirva a raiz do repositório por HTTP:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

Depois abra `http://127.0.0.1:8765/modules/06-pfi/lecture/pfi-interactive/index.html`.
As fontes são as já compartilhadas pelo repositório. Para um pacote
independente, use o [exportador documentado](../../tools/README.md#a-sequência).
O caminho antigo da apresentação no módulo 00 redireciona para esta versão.

## Cadernos

- **[pfi_walkthrough.ipynb](notebooks/pfi_walkthrough.ipynb)** — a aula:
  reconstrói o preditor, confere as permutações registradas, produz as
  figuras e imprime os resultados citados aqui.
- **[pfi_internals.ipynb](notebooks/pfi_internals.ipynb)** — o companheiro
  técnico: verifica as fórmulas e os invariantes do mecanismo, incluindo
  preservação de tipos, matriz original, pares e subgrupos.
- **[srag_course_pfi_walkthrough.ipynb](notebooks/srag_course_pfi_walkthrough.ipynb)** —
  leitura da nova PFI do preditor congelado: perdas, diferença, razão,
  dispersão e dependência. Exibe pendência enquanto a execução estiver incompleta.
- **[srag_course_pfi_internals.ipynb](notebooks/srag_course_pfi_internals.ipynb)** —
  confere a integridade do novo agregado e recalcula resumos e posições;
  não apresenta a leitura do agregado como reprodução das previsões individuais.

As figuras promovidas ficam em `figures/`. A execução gera arquivos em
`figures_generated/` dentro de uma área temporária; não modifica as
cópias versionadas. Ambos os cadernos devem ser executados por inteiro,
com kernel novo, antes de salvar os outputs no git.

## Configuração e proveniência

O módulo importa o contrato de dados/modelo de `srag_60_model` e os núcleos
`permutar_colunas` e `trace_pfi` de `srag_70_explain`. Uma única implementação
serve aos cadernos atuais e ao wrapper histórico `srag_pfi_walkthrough`.
São declarados métrica, semente, número de repetições, separação temporal
e direção da diferença. O log loss é calculado com probabilidades de óbito,
sem um limiar de classificação.

O módulo 00 permanece a fonte dos dados, da seleção e dos registros
[de ranking](../00-dataset/gold/pfi_ranking.json) e
[de evidência anterior](../00-dataset/notebooks/srag_pfi_ranking.ipynb).
Eles não são copiados para criar uma segunda base. O
[payload agregado](lecture/pfi-interactive/data/pfi-aggregates.json) contém
o ranking, os traces e o protocolo. Os
[resultados da seleção](lecture/pfi-interactive/data/model-selection.json)
separam os finalistas históricos, escolhidos por AUC, da revisão de
balanceamento e tuning somente do XGBoost, escolhida por log loss. Essa
projeção é validada contra os registros do módulo 00 e impressa no
walkthrough §1. Na apresentação, **Model results** mostra as perdas de
validação e teste; **Data split** preserva a origem da amostra e os períodos.
A
[janela didática](lecture/pfi-interactive/data/pfi-teaching-records.json)
é projetada da [evidência deste módulo](evidence/pfi_teaching_demo.json),
gerada por [srag_73_teaching_demo](../../tools/srag_73_teaching_demo.py)
no walkthrough §3. O internals §5 confere a primeira ordem global e as
previsões por transporte independente. As fichas e previsões originais
coincidem com o registro histórico; somente as previsões permutadas passam
a usar os doadores do teste inteiro. O exemplo manual anterior permanece
no módulo 00 para documentar a correção, sem apagar seus números.

O arquivo separado inclui valores clínicos, desfechos e previsões individuais,
além dos valores permutados e do protocolo global. Não exporta identificadores,
posições ou desfechos dos doadores. A ausência de nomes e identificadores
não significa anonimização.

## Referências

- Molnar, C. *Interpretable Machine Learning*, capítulo 23 —
  [Permutation Feature Importance](https://christophm.github.io/interpretable-ml-book/feature-importance.html).
  (Definição, interpretação, dependência e limites.)
- Molnar, C.
  [Group-wise PFI example](https://christophm.github.io/interpretable-ml-book/feature-importance.html#group-wise-pfi-example).
  (Permutação dentro de subgrupos.)
- Raschka, S. *STAT451 — Feature Selection*,
  [slides da aula](https://sebastianraschka.com/pdf/lecture-notes/stat451fs21/13_feat-sele__slides.pdf)
  e [vídeo conceitual](https://www.youtube.com/watch?v=VUvShOEFdQo).
  (Referência da sequência didática; nossos resultados são do SRAG.)
- scikit-learn.
  [Permutation feature importance](https://scikit-learn.org/stable/modules/permutation_importance.html).
  (Algoritmo, avaliação e cautelas.)
