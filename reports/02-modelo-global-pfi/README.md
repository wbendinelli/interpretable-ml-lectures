# Dos registros à importância global

**SAPIANS · SCC5819 · William Bendinelli · edição viva em português**

Este relatório reúne o percurso do dataset aos métodos de interpretação,
incluindo a Permutation Feature Importance (PFI). Seu papel é explicar o que
foi feito, de qual modelo cada resultado depende e onde termina a evidência.
Ele sintetiza os cadernos dos módulos; não calcula resultados próprios.

**Estado desta edição:** a busca no treino completo foi interrompida por
decisão de escopo antes da seleção final. O estudo atual do módulo 00 mantém
a amostra de treino registrada e compara estratégias de balanceamento do
XGBoost, com ajuste de hiperparâmetros por estratégia e escolha pelo log loss
de validação. A comparação foi concluída e conferida: a configuração original
sem balanceamento permaneceu com a menor perda de validação entre os candidatos
registrados (módulo 00, walkthrough do balanceamento com ajuste §3).
A referência histórica continua identificando os resultados já publicados;
a comparação nova não substitui automaticamente o modelo das aulas.

O [relatório entregue sobre os métodos locais](../01-metodos-locais/README.md)
e seu PDF permanecem preservados. Este texto é uma nova edição, com escopo
mais amplo e correções explicitadas, sem recompilar o documento histórico.

## A pergunta que organiza o estudo

Temos registros reais de vigilância e um desfecho registrado. Construímos
um modelo para estimar esse desfecho e, depois, investigamos seu comportamento.
Três perguntas precisam permanecer separadas:

- **Sobre os dados:** quem entrou no estudo, quais informações foram
  transformadas e quais registros ficaram de fora?
- **Sobre o modelo:** com quais dados ele aprendeu, como foi escolhido e
  como se comporta em um período posterior?
- **Sobre a explicação:** qual aspecto do modelo o método mede e quais
  conclusões esse resultado sustenta?

Descrever o comportamento de um modelo não comprova utilidade clínica nem efeito
causal. E um bom desempenho médio não dispensa a avaliação das probabilidades,
dos subgrupos e da disponibilidade das entradas no instante de uso pretendido.

## O percurso dos dados pertence ao módulo da base

A procedência, a limpeza, a definição da tarefa, a amostragem e a seleção do
modelo são responsabilidade do [módulo 00](../../modules/00-dataset/README.md).
Os módulos de interpretação reutilizam esse contrato; não devem apresentar
outra versão da população ou uma divisão de dados implícita.

**Bronze** preserva os arquivos de origem. **Silver** padroniza representações,
interpreta datas, deriva campos e torna problemas rastreáveis. **Gold** faz
as escolhas da tarefa: coorte, alvo, entradas e partições temporais. Padronizar
códigos não significa corrigir clinicamente todos os registros. O catálogo
de qualidade documenta problemas que permanecem.

A coorte registrada contém **1.282.970 registros de hospitalização**;
as entradas do modelo são **40** (módulo 00, walkthrough do modelo §1 e
internals do modelo §1). Esses valores descrevem a coorte e o contrato de
entradas, não o número de registros que efetivamente participaram do ajuste
da referência amostrada. Também não demonstram que cada registro corresponde
a uma pessoa distinta.

O recorte exige hospitalização e os critérios clínicos declarados no funil,
COVID pela definição ampla adotada e início de sintomas a partir de
26/02/2020. Não é a totalidade de todas as notificações de SRAG, nem uma
coorte composta exclusivamente por confirmações de PCR. A definição ampla
considera as marcações laboratoriais e a classificação final especificadas
no [código da Silver](../../tools/srag_30_silver.py).

### O desfecho precisa ser chamado pelo que foi codificado

A receita Gold inclui apenas `EVOLUCAO = 1` e `EVOLUCAO = 2`, e define
`y_obito = (EVOLUCAO == 2)`. O primeiro estado registra cura; o segundo,
óbito. `EVOLUCAO = 3` registra óbito por outras causas e é excluído desta
tarefa, assim como os estados sem a evolução admitida pela receita.

Portanto, a expressão histórica “casos fechados” é insuficiente se sugerir
que todos os desfechos conhecidos foram incluídos. O estudo não pode chamar
esse alvo de mortalidade por todas as causas. A exclusão de outros óbitos
é uma escolha de população e desfecho, não evidência de sobrevivência.
Qualquer revisão dessa escolha exige medir suas consequências no módulo da
base antes de reconstruir o modelo.

O [dicionário](../../modules/00-dataset/DICTIONARY.md), o
[funil](../../modules/00-dataset/gold/MANIFEST.md#1-o-funil-na-ordem-em-que-os-filtros-correm)
e o [código Gold](../../tools/srag_40_gold.py) permitem conferir essa definição.
O encerramento incompleto pode ser seletivo; a análise dos casos admitidos
não garante generalização a todos os notificados.

### Coorte, partições e amostra são objetos diferentes

No protocolo registrado, o módulo 00 separa os dados pelo início dos sintomas:
treino até 2022, validação em 2023 e teste em 2024. Dentro da coorte, são
**1.242.680**, **24.148** e **16.142** registros, respectivamente
(módulo 00, walkthrough do modelo §1). São períodos distintos, não uma
divisão aleatória em proporções convencionais.

A referência usada pelos módulos de método foi ajustada com uma amostra
uniforme de **200.000 registros do treino elegível**, sem reposição;
validação e teste permaneceram completos (módulo 00, internals do modelo §1).
A amostra não é outro teste, não é seleção da classe majoritária e não é um
balanceamento das classes. O restante do treino elegível não passa a integrar
os conjuntos de avaliação.

O estudo atual reutiliza essa amostra como origem comum das estratégias.
Pesos alteram a contribuição das linhas no ajuste; redução e síntese alteram
somente o conjunto usado para treinar. Validação e teste permanecem completos,
sem balanceamento ou registros sintéticos. O protocolo precisa manter
explícitos o contrato de dados, a regra de seleção e o modelo ao qual cada
previsão pertence.

A tentativa de ampliação para o treino completo permanece identificada como
interrompida, com protocolo e checkpoints preservados. Ela não produziu uma
seleção final. Usar todo o treino elegível pode ser um estudo futuro, mas não
é requisito para explicar PFI ou para comparar balanceamento na amostra.

## Escolher e avaliar são etapas diferentes

O estudo histórico registrado compara famílias de modelos e configurações usando a
validação temporal. O critério primário é a AUC de validação. AUC mede a
capacidade de ordenar os registros por risco; não mede, sozinha, se uma
probabilidade estimada está no nível correto.

O [protocolo atual](../../modules/00-dataset/COURSE_STUDY.md) mantém a família
XGBoost e a amostra de treino, compara as estratégias pelo menor **log loss
de validação** e mantém AUC, Brier e calibração como avaliações complementares.
Essa é uma mudança de protocolo, não uma reprodução idêntica da seleção
histórica entre famílias. A busca foi concluída, com **30 configurações por
estratégia e 120 ajustes no total** (módulo 00, walkthrough do balanceamento
com ajuste §2; internals §2). As probabilidades foram avaliadas sem
recalibração nesta rodada; comparar
calibradores exigiria uma separação adicional e explícita dos papéis dos dados.

A comparação anterior, executada por `tools/srag_61_balance.py`, mantém os
hiperparâmetros do XGBoost fixos. Ela responde ao que acontece quando alteramos
o tratamento das classes sob aquela configuração. A busca nova permite
ajustar os hiperparâmetros separadamente no XGBoost sem balanceamento, com
pesos, com redução da classe majoritária e com SMOTENC restrito. O espaço
controlado de busca e seu orçamento constam no protocolo anterior à
execução. O melhor ajuste encontrado de cada estratégia participa da comparação
final na validação; o teste não decide o vencedor.

| Melhor configuração de cada estratégia | Log loss — validação | Log loss — teste histórico | Fonte |
|---|---:|---:|---|
| Sem balanceamento, configuração original | **0,4209** | **0,4090** | módulo 00, walkthrough do balanceamento com ajuste §3–§4 |
| Pesos de classe | 0,4813 | 0,4668 | módulo 00, walkthrough do balanceamento com ajuste §3–§4 |
| Redução da majoritária | 0,4989 | 0,4841 | módulo 00, walkthrough do balanceamento com ajuste §3–§4 |
| SMOTENC restrito | 0,4675 | 0,4498 | módulo 00, walkthrough do balanceamento com ajuste §3–§4 |

Fonte: módulo 00, walkthrough do balanceamento com ajuste §3–§4.
Menor é melhor; a escolha foi feita na validação. Os resultados sustentam
manter a referência sob o objetivo registrado. Ajustar pesos e redução não
as fez superar o original; isso não demonstra que toda forma de balanceamento
ou recalibração pioraria as probabilidades. A configuração original também
apresenta desvio de calibração, mostrado junto às contagens no walkthrough §6.

As perguntas são distintas: manter a configuração fixa ajuda a estudar o
efeito da estratégia sob essa condição; ajustar por estratégia compara as
melhores opções encontradas no espaço declarado. A busca atual não escolhe
entre todas as famílias de modelo nem demonstra que seu resultado vale para
qualquer dataset, período ou orçamento de ajuste.

A PFI da aula usa log loss, que avalia probabilidades em relação aos
desfechos registrados. Usar AUC para seleção e log loss para a explicação
na referência histórica não constitui uma igualdade entre métricas: são
critérios que respondem a perguntas distintas e devem ser nomeados em cada
resultado. A nova escolha de log loss não reclassifica retrospectivamente
o vencedor histórico como se ele tivesse sido escolhido por outro critério.

A função da seleção histórica excluiu o teste de sua escolha. Entretanto,
o período já havia sido observado em outro estudo: a guarda no código não
demonstra que aquele teste fosse desconhecido. Ele também foi reutilizado
em explicações e análises de sensibilidade. Portanto, a descrição histórica
“teste lido uma vez” não caracteriza a evidência atual; as avaliações desse
período são exploratórias. O teste não recupera independência porque o
modelo, a métrica ou a apresentação mudaram.

A referência histórica registrada não usa pesos de classe nem reamostragem
das classes. O estudo anterior de balanceamento permanece uma comparação
separada; as configurações ajustadas da nova execução foram comparadas sob
seu próprio protocolo. Uma
futura adoção precisa registrar o objetivo da mudança e seus efeitos sobre
discriminação e calibração, em vez de chamar balanceamento de correção
obrigatória de uma base desbalanceada.

Fontes: [protocolo de seleção](../../modules/00-dataset/SELECTION.md),
[modelo registrado](../../modules/00-dataset/MODEL.md),
[estudo de balanceamento](../../modules/00-dataset/notebooks/srag_balance_comparison.ipynb).

## O que os métodos já estudados acrescentam

Os módulos têm numeração própria. A chegada à PFI do **cap. 23** de Molnar
não significa que todos os capítulos anteriores tenham sido implementados.
O [mapa de cobertura](../../ROADMAP.md) distingue o que existe do que continua
planejado. A sequência global agora inclui PDP, ALE, interação e decomposição
antes da PFI; os cadernos dos respectivos módulos registram as aplicações.

| Módulo | Método implementado | Pergunta e limite principal |
|---|---|---|
| [01](../../modules/01-ceteris-paribus/README.md) | Ceteris paribus — cap. 12 | Como a previsão muda ao variar uma entrada, mantendo as demais fixas? A ficha modificada pode sair do domínio estudado. |
| [02](../../modules/02-ice/README.md) | ICE — cap. 13 | Essa resposta é semelhante entre registros? As curvas mostram heterogeneidade, mas dependem dos registros e do modelo avaliados. |
| [03](../../modules/03-lime/README.md) | LIME — cap. 14 | Que aproximação simples descreve uma previsão em uma vizinhança declarada? Fidelidade e conclusões dependem da vizinhança construída. |
| [04](../../modules/04-counterfactual/README.md) | Contrafactuais — cap. 15 | Que alterações declaradas mudam uma decisão do modelo? Possibilidade no modelo não demonstra viabilidade clínica nem efeito de intervenção. |
| [05](../../modules/05-shap/README.md) | Shapley e SHAP — cap. 17 e cap. 18 | Como atribuir a diferença entre a previsão e uma referência? Atribuição não é causalidade, e sua interpretação depende do jogo e da referência. |
| [06](../../modules/06-pdp/README.md) | PDP — cap. 19 | Qual é a resposta média ao impor uma entrada em todas as fichas do fundo? A média pode esconder heterogeneidade e incluir combinações fora da coorte. |
| [07](../../modules/07-ale/README.md) | ALE — cap. 20 | Como acumular diferenças locais da idade? Janelas ocupadas e centralização por contagens delimitam a curva; proximidade local não garante viabilidade clínica. |
| [08](../../modules/08-feature-interaction/README.md) | Interação — cap. 21 | Onde a resposta conjunta deixa de ser aditiva na escala explicada? H exige ler também o resíduo, o denominador e a distribuição de referência. |
| [09](../../modules/09-functional-decomposition/README.md) | Decomposição — cap. 22 | Como repartir e reconstruir a superfície idade × saturação sob uma medida produto? A identidade de variâncias não é automaticamente válida na conjunta observada nem decompõe o preditor inteiro. |
| [10](../../modules/10-pfi/README.md) | PFI — cap. 23 | Quanto a perda muda quando uma entrada é embaralhada? Mede dependência preditiva sob o protocolo, não o efeito da variável sobre uma pessoa. |

O modelo e o contrato de dados podem ser compartilhados sem que toda análise
use o mesmo exemplar. O módulo de contrafactuais declara uma regra própria
de escolha; a PFI avalia um conjunto. A nova edição não repete a promessa de
um único paciente como se ela cobrisse todos os experimentos do repositório.

As restrições do formulário são um diagnóstico comum. Uma perturbação pode
contradizer o registro de origem, o filtro da coorte ou uma regra temporal.
Isso deve ser descrito pela restrição efetivamente verificada; não basta
chamar toda combinação fora do recorte de biologicamente impossível.

## Da explicação individual à importância global

Na PFI já temos um modelo ajustado. Calculamos sua perda nos dados de
avaliação e guardamos esse valor como referência. Depois copiamos as entradas,
embaralhamos uma variável entre os registros, fazemos novas previsões com o
mesmo modelo e recalculamos a perda. As outras entradas e os desfechos não
são embaralhados. O modelo não aprende novamente.

Cada variável começa da matriz original. Repetimos o procedimento para
examinar a variação entre ordens aleatórias. A diferença de perdas compara
quanto foi acrescentado; a razão compara a perda permutada à original. A
razão sem mudança tem referência um, enquanto a diferença sem mudança tem
referência zero. Uma permutação isolada pode inclusive melhorar a perda.

O resultado depende do modelo ajustado, do conjunto avaliado, da métrica e
da forma de perturbar. Ele permite ordenar deteriorações medidas do desempenho.
Não informa sozinho se aumentar a idade aumenta o risco, não fornece uma
variação percentual da probabilidade de óbito e não identifica causas.
Uma importância pequena também não demonstra irrelevância científica nem
autoriza exclusão automática de uma entrada.

Quando as entradas dependem entre si, o embaralhamento marginal pode produzir
combinações pouco sustentadas pelos dados. O módulo estuda cardiopatia e
diabetes individualmente, como par movido junto e por embaralhamento dentro
dos estados de diabetes. Essas operações têm perguntas diferentes. Mover
o par preserva sua relação interna, mas pode romper relações com o resto da
ficha. Restringir a permutação por diabetes não reproduz uma distribuição
condicional dada toda a ficha.

O desvio padrão entre embaralhamentos descreve a variabilidade das ordens
para aquele modelo e aquele conjunto. Ele não inclui a incerteza de treinar
outro modelo nem constitui, por si só, intervalo de confiança populacional.

Fontes: [walkthrough PFI](../../modules/10-pfi/notebooks/pfi_walkthrough.ipynb),
[verificação independente](../../modules/10-pfi/notebooks/pfi_internals.ipynb)
e [capítulo de Molnar](https://christophm.github.io/interpretable-ml-book/feature-importance.html).

## O que a auditoria mudou na redação

Esta edição preserva a rastreabilidade das correções, sem reescrever o
relatório entregue:

- **“Casos fechados”** passa a ser acompanhado dos códigos admitidos e da
  exclusão de outros óbitos. A questão é a definição do alvo, não um ajuste
  cosmético do nome.
- **“Um paciente em todos os métodos”** é substituído pela unidade de análise
  efetivamente usada: previsão individual, conjunto de curvas ou avaliação
  global, conforme o experimento.
- **“Teste lido uma vez”** não é tomado como garantia de independência.
  A função de seleção não usa o teste, mas o período já havia sido
  observado; sua avaliação continua exploratória.
- **“Desempenho próximo torna os modelos equivalentes”** não é adotado.
  Proximidade de métricas não comprova igualdade de previsões, explicações
  ou ranking de importância.
- **“Disponível na admissão”** não é presumido para todo campo retido.
  A exclusão de UTI e ventilação reduz problemas conhecidos, mas não
  substitui uma auditoria completa do instante de disponibilidade.
- **“A deriva causou o desvio de calibração”** não é tratada como causalidade
  demonstrada. A mudança temporal observada é contexto e hipótese explicativa;
  a avaliação precisa distinguir a medição da interpretação.
- **A troca de Brier por log loss na aula** é mantida como uma mudança de
  métrica identificada, apoiada na análise de sensibilidade do módulo 10.
  Números das duas métricas não são intercambiáveis.
- **O erro das fichas visíveis não é o erro global.** A animação atual
  mostra uma janela da permutação feita no teste inteiro; os indicadores
  globais vêm desse teste e das repetições, não de uma perda calculada
  somente sobre a pequena seleção didática.

A verificação da implementação da receita Gold também faz parte da revisão:
flags de escolha não podem apenas entrar no manifesto; precisam ser
executadas ou rejeitadas quando não suportadas. Essa verificação pertence ao
módulo da base, não a uma explicação que disfarce o comportamento nos slides.

As fontes `tools/srag_51_course_study.py` e `tools/srag_52_course_balance.py`
preservam o estudo interrompido no treino completo, acompanhado pelo
[walkthrough](../../modules/00-dataset/notebooks/srag_course_study_walkthrough.ipynb)
e pelo [internals](../../modules/00-dataset/notebooks/srag_course_study_internals.ipynb)
da base. Seu registro `gold/course_study_v2.json` deve comunicar a interrupção,
sem converter resultados parciais em uma seleção concluída.

O executor novo é `tools/srag_53_sample_balance_search.py`. O
[agregado concluído](../../modules/00-dataset/gold/sample_balance_search.json),
o [walkthrough do balanceamento com ajuste](../../modules/00-dataset/notebooks/srag_sample_balance_walkthrough.ipynb)
e seu [internals](../../modules/00-dataset/notebooks/srag_sample_balance_internals.ipynb)
registram o protocolo atual e os resultados medidos no módulo da base.
Protocolos e artefatos dos estudos não são intercambiáveis. Modelos
treinados e caches permanecem fora do repositório; as fontes e a evidência
agregada identificada ficam versionadas. Concluir a comparação não significa
trocar automaticamente o artefato usado pelas aulas.

## O que foi concluído e o que depende de adoção

| Entrega | Critério de conclusão |
|---|---|
| Contrato de população e desfecho | Mantido e documentado no módulo da base, com distinção entre elegibilidade e amostra. |
| Comparação na amostra | Grade concluída; finalistas e vencedor congelados pelo menor log loss de validação. |
| Avaliação temporal | Validação e teste completos, sem reamostragem; teste já observado identificado como exploratório. |
| Estudos anteriores | Comparação com parâmetros fixos preservada; busca completa identificada como interrompida antes da seleção. |
| Interpretação e PFI | Referência histórica mantida. Qualquer troca futura exige recalcular os experimentos afetados. |
| Conferência do relatório | Afirmações quantitativas vinculadas às saídas dos notebooks responsáveis. |
| Apresentação | Conserva a referência histórica; uma mudança de artefato exige dados, gráficos, exemplos e guia reconciliados. |

O estudo na amostra sustenta manter a referência sob o critério registrado,
sem afirmar que ela seja a melhor solução para qualquer objetivo. A escolha
dentro da comparação não atualiza a apresentação automaticamente. Adotar
outra referência exige uma decisão
explícita e a recomputação dos experimentos, figuras e textos que dependem dela.

## Como conferir esta edição

Os números históricos acima apontam para o módulo proprietário e seus
cadernos. O teste de evidência do repositório também aceita este arquivo:

```bash
python3 tools/check_numbers.py \
  --prose reports/02-modelo-global-pfi/README.md
```

A aceitação exige ausência de valores sem fonte. A conferência textual não
substitui a execução dos cadernos, a revisão dos condicionamentos ou a
validação científica das conclusões. Os gráficos novos são produzidos no
módulo da base; este relatório não gera outro conjunto de estimativas.
Nenhum novo PDF foi exportado.
