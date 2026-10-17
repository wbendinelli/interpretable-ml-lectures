# Guia do professor — PFI no modelo SRAG/COVID

Este roteiro acompanha, em português, as **quinze telas da apresentação em
inglês**. Os números dos títulos abaixo são a ordem da aula; `cover`,
`61`, `62` etc. são os identificadores de navegação, preservados para
manter os links. O roteiro serve para preparar a fala, não para colocar
todo este texto nos slides.

A pergunta que conduz a aula é: **de qual informação este modelo depende
para manter o desempenho nesta avaliação?** Primeiro vemos a operação;
depois explicamos o cálculo e o código; por fim delimitamos a conclusão.
Molnar, capítulo 23, orienta a teoria; sua visão geral dos métodos situa a
PFI no mapa inicial. Raschka inspira a sequência visual dos exemplos
seguintes.

As medições deste roteiro são impressas pelo
[`pfi_walkthrough.ipynb`](../notebooks/pfi_walkthrough.ipynb), indicado
abaixo como `walkthrough §N`. As verificações independentes estão em
[`pfi_internals.ipynb`](../notebooks/pfi_internals.ipynb).

## 1. Capa — Permutation Feature Importance

**Tela `cover`. Objetivo:** apresentar o tema e o autor em uma capa
simples, apenas com título e nome. A pergunta que conduz a aula fica na fala.

**Fala sugerida:** “Já temos um modelo treinado. Agora queremos entender
de quais informações seu desempenho depende. Para isso, vamos embaralhar
uma variável por vez, manter o modelo fixo e observar quanto muda seu erro
nos dados de teste.”

**O que apontar:** o título. Pronunciar *Permutation Feature Importance*
e traduzir como importância de uma variável por permutação. Usar **PFI**
a partir daqui. Não começar pelo ranking ou pela lista de parâmetros.

**Conclusão e ponte:** “A ideia é simples; precisamos entender bem o que
mudamos e o que mantemos fixo. Primeiro, onde esse método se encaixa?”

## 2. O mapa — Where does PFI fit?

**Tela `61`. Objetivo:** localizar a PFI pelas categorias de interpretação
apresentadas por Molnar, antes de mostrar o experimento.

**Fala sugerida:** “Já temos um modelo e queremos entender como ele usa
as informações. No livro de Molnar, podemos localizar a PFI por estas
categorias. Ela é post-hoc: a explicação acontece depois do treinamento.
É model-agnostic: não precisamos examinar a estrutura interna do modelo;
usamos suas previsões. É global: avaliamos o comportamento no conjunto
de dados, em vez de explicar uma única previsão. E mede feature
importance: a importância de uma variável segundo uma definição explícita.
Na PFI, essa definição é a mudança no erro de previsão quando embaralhamos
a variável, mantendo o modelo fixo.”

**O que apontar:** acompanhar o percurso **Interpretability → Post-hoc →
Model-agnostic → Global → Feature importance → PFI**. Traduzir os termos
conforme eles aparecem: interpretação; depois do treinamento; independente
da estrutura interna do modelo; visão do conjunto; importância das
variáveis; importância por permutação. O percurso é uma seleção didática
das categorias do livro, não a reprodução de todo o seu mapa de métodos.

**Cuidado de leitura:** estes blocos situam o método; não são as etapas
do algoritmo. Global significa resumir o modelo nos dados avaliados, não
uma conclusão universal sobre pacientes ou sobre o mundo. Model-agnostic
não significa que a importância seja igual para qualquer modelo. A PFI
explica um modelo já treinado e não seleciona nem remove colunas
automaticamente. Não estamos apresentando redução de dimensionalidade
como objetivo desta análise.

**Referência para preparar a fala:** [visão geral dos métodos de Molnar](https://christophm.github.io/interpretable-ml-book/overview.html)
e seu [manuscrito no GitHub](https://github.com/christophM/interpretable-ml-book/blob/master/manuscript/overview.qmd)
para as categorias; [capítulo de PFI](https://christophm.github.io/interpretable-ml-book/feature-importance.html)
para a operação e o significado da importância. Raschka continua como
inspiração para os exemplos seguintes; este enquadramento segue Molnar.

**Conclusão e ponte:** “Agora sabemos onde a PFI se encaixa. Vamos ver
como esse embaralhamento funciona, mantendo o mesmo modelo e os mesmos
desfechos.”

## 3. A experiência — The permutation experiment

**Tela `62`. Objetivo:** acompanhar uma ficha, uma previsão e seu erro;
depois distinguir a janela de fichas do resultado global da operação.

**Fala sugerida:** “Esta linha representa uma ficha real. Temos a idade
em anos, o estado registrado de saturação baixa e o desfecho observado.
O modelo recebeu essas informações e as demais entradas do estudo, e
produziu uma probabilidade de óbito. O desfecho é o que aconteceu; a
probabilidade é o que o modelo estimou.”

**O que apontar e acionar:** pausar a animação e ler uma linha inteira.
A coluna *Original* conserva a previsão inicial. Avançar com *Next step*:
os novos valores de idade chegam de linhas do teste completo; o desfecho
e as outras entradas permanecem. A permutação ocorre no teste inteiro,
não somente entre as fichas visíveis. Só depois surgem as novas previsões
dessas fichas. O modelo não foi treinado novamente. Restaurar a tabela e
escolher *Low oxygen*; idade deve voltar ao original antes da nova
experiência.

Apontar o gráfico e dizer: “As barras resumem o teste completo: erro
original e média após permutação, com SD entre as **50** repetições.
A tabela permite acompanhar algumas fichas na primeira dessas
repetições; não é dela que calculamos a barra” (walkthrough §3–§5).
Conferir idade, **0,4090 → 0,4937**, e depois saturação baixa,
**0,4090 → 0,4212** (walkthrough §2, §4). Esses resultados globais são
os mesmos usados no próximo slide.

Abrir *What is log loss?* e dizer: “O modelo fornece uma probabilidade de
óbito. Olhamos qual desfecho aconteceu. Se houve óbito, usamos a
probabilidade de óbito; se houve sobrevida, usamos a probabilidade de
sobrevida. Quanto menos probabilidade o modelo deu ao que ocorreu,
maior a penalidade.” O logaritmo natural transforma essa probabilidade
em uma perda; a média das perdas no teste é o erro global.

**Por que escolhemos log loss?** Nossa pergunta é quanto cada variável
ajuda este modelo a prever probabilidades de óbito. A log loss usa a
probabilidade inteira e dispensa um corte de classificação. Previsões
erradas muito confiantes recebem perdas maiores. A perda individual pode
mudar mesmo que a classe prevista permaneça igual.

Molnar não determina uma perda única. Nos exemplos do
[capítulo de PFI](https://christophm.github.io/interpretable-ml-book/feature-importance.html),
ele usa erro absoluto médio (MAE) para a quantidade de bicicletas alugadas
e log loss para a classificação do sexo dos pinguins. Nossa escolha
acompanha esse exemplo de classificação. O estudo de sensibilidade
conserva as outras métricas como diagnósticos complementares
(walkthrough §8).

Se a pergunta fosse ordenar pacientes por risco, poderíamos usar AUC; se
fosse acertar classes após um corte, acurácia. A métrica define a pergunta
e pode mudar o ranking de PFI. Dizer “importância para a log loss deste
modelo neste teste”.

Log loss não mede exclusivamente calibração. Para discutir calibração,
olhar também a curva de probabilidades previstas versus frequências
observadas, como explica a
[documentação de calibração](https://scikit-learn.org/stable/modules/calibration.html).
Essa média também não corrige o desbalanceamento: cada registro tem o
mesmo peso, e a classe mais frequente contribui com mais registros.
Um desfecho isolado não revela a probabilidade verdadeira daquele paciente.
A perda individual ajuda a entender a conta; a qualidade probabilística
é avaliada no conjunto de previsões e desfechos.

Os sinais ✓ e × usam o corte **0,50**; o log loss usa toda a probabilidade
(walkthrough §3). Portanto, a contagem de erros de classe pode permanecer
igual enquanto o log loss muda. Em saturação baixa, a troca pode trazer o
mesmo estado que uma ficha já tinha. Se nenhuma entrada daquela ficha
mudou, sua previsão também não precisa mudar.

**Cuidado de leitura:** estas **oito fichas** foram escolhidas por
desfecho para tornar a tabela legível, não para representar a frequência
de óbitos do teste (walkthrough §3). São uma janela da primeira permutação
real do teste completo. Seus doadores podem estar fora da janela; por
isso, não precisamos encontrar na tela a origem de todo valor que chega.
Uma ficha pode receber uma idade muito diferente da sua. A idade original
é um dado real; a combinação após a troca é uma entrada artificial criada
para o diagnóstico, não uma correção da ficha clínica.

**Conclusão e ponte:** “A tabela mostrou o mecanismo e o gráfico mostrou
seu saldo global em várias repetições. Agora vamos transformar esse saldo
em importância e comparar as variáveis.”

## 4. O resultado global — From error to importance

**Tela `63`. Objetivo:** ler o ranking como mudança de desempenho, com
referência, unidade e variação explícitas.

**Fala sugerida:** “O gráfico anterior já usou o teste temporal completo.
Agora comparamos as variáveis nesse mesmo teste. Seu log loss original é
**0,4090**. Depois de embaralhar idade, a média das repetições é
**0,4937**. O aumento absoluto é
**0,0846**; em relação ao erro inicial, o aumento é aproximadamente
**20,7%**” (walkthrough §2, §4–§5).

**O que apontar e acionar:** começar em *Difference*. Ler original →
média após permutação → diferença. Mudar para *Ratio*: a divisão produz
aproximadamente **1,2069** vezes o erro inicial. A referência é **1**, que
significa nenhum aumento; abaixo dela houve redução, acima houve aumento
(walkthrough §5). Não há um mínimo matemático de um para a razão. Ela
exige um erro original positivo.

Selecionar saturação baixa e conferir o contraste: erro médio após
permutação **0,4212**, diferença **0,0121**, aumento relativo de
aproximadamente **3,0%** (walkthrough §4–§5). Esses resultados pertencem ao
mesmo teste e ao mesmo modelo. Não são os erros da pequena tabela anterior.

Apontar a haste: a idade tem SD **0,0027** e saturação baixa, **0,0009**
(walkthrough §4). Explicar: “Embaralhamentos diferentes dão resultados
um pouco diferentes. O SD resume essa dispersão.” Não chamá-lo de intervalo
de confiança para futuros pacientes. O treino e o conjunto avaliado
continuaram os mesmos.

**Conclusão e ponte:** “As escalas mostram a mesma mudança de formas
diferentes. Como todas as variáveis compartilham o mesmo erro original,
a ordem do ranking se conserva. Um aumento no erro não é um aumento
na mortalidade; agora vamos separar importância de seleção.”

## 5. O alcance do ranking — Importance and feature selection

**Tela `65`. Objetivo:** evitar a conclusão automática “baixa importância,
então pode remover”.

**Fala sugerida:** “PFI pergunta quanto o modelo atual depende de uma
informação. A coluna continua existindo: redistribuímos seus valores.
Selecionar variáveis é outra decisão: escolher um conjunto, ajustar os
modelos correspondentes e avaliar o desempenho deles.”

**O que apontar:** contrastar os dois caminhos. A existência de outra
variável com informação parecida pode reduzir a importância individual.
Isso não prova irrelevância clínica nem garante que retirar a coluna
seja seguro. Não executar LOFO aqui; ele responde a uma pergunta que
inclui retreinamento.

**Conclusão e ponte:** “O ranking descreve este preditor. Precisamos saber
qual preditor é esse e de quais dados ele veio.”

## 6. Os dados — From real records to model inputs

**Tela `66`. Objetivo:** mostrar o percurso da base até as entradas, sem
transformar a aula em uma leitura de regras de limpeza.

**Fala sugerida:** “Bronze conserva os registros de origem. Silver
organiza tipos, categorias, datas e idade. Gold define a população do
estudo, seu desfecho e a separação temporal. Aqui analisamos registros de
hospitalização por COVID com desfecho encerrado: sobrevida ou óbito.”

**O que apontar:** seguir os ícones Bronze → Silver → Gold e, depois,
coorte → entradas → categorias. Identificadores e desfecho não entram
como preditores. UTI e ventilação também foram excluídas conforme o
protocolo. *Unknown* é um estado registrado à parte; não significa *No*.
A idade decimal vem do intervalo entre nascimento e início dos sintomas,
convertido em anos. Ela não está em dias (walkthrough §1, §3).

**Conclusão e ponte:** “O alvo registra o que aconteceu; as entradas
alimentam a previsão. A organização dos anos define como avaliamos o
modelo.”

## 7. O modelo — Fit, choose, then explain

**Tela `66-selection`. Objetivo:** separar treino, escolha do modelo e
avaliação da importância.

**Fala sugerida:** “Treinamos com dados até **2022**, usamos **2023** para
escolher o modelo e reservamos **2024** para a avaliação temporal. A
referência desta aula é o XGBoost selecionado, sem pesos de classe nem
reamostragem. A comparação de balanceamento não substituiu essa
referência” (walkthrough §1).

**O que apontar:** os três períodos e o símbolo de preditor fixo. A
escolha usou AUC na validação: capacidade de ordenar riscos. A PFI desta
aula usa log loss: erro das probabilidades. São critérios diferentes;
“melhor” precisa sempre indicar o critério e o conjunto avaliado.

Dizer também: “Esse teste já foi examinado durante o estudo. A explicação
é exploratória; não estamos apresentando uma confirmação prospectiva.”
Não sugerir que a separação temporal resolve, sozinha, toda questão de
disponibilidade clínica dos campos.

**Conclusão e ponte:** “O modelo está pronto e sua avaliação está
definida. O código da PFI começa recebendo esse modelo.”

## 8. A entrada do algoritmo — A model fitted before PFI

**Tela `67`. Objetivo:** reconhecer que o treinamento terminou antes do
experimento.

**Fala sugerida:** “Esta linha entrega ao algoritmo um modelo já
ajustado. Esta outra escolhe a variável que vamos testar. Nada aqui
manda aprender novos parâmetros. Vamos usar a mesma regra de previsão
antes e depois da mudança.”

**O que apontar:** `fitted_reference`, a escolha `idade_anos` e o cadeado.
Explicar *fixed predictor* como modelo mantido fixo. Raschka ilustra com
outro tipo de modelo; nossa aplicação usa XGBoost. O mecanismo da PFI
não depende de serem os mesmos algoritmos.

**Conclusão e ponte:** “Antes de mudar uma entrada, precisamos medir
como o modelo já estava errando.”

## 9. A referência — The original error

**Tela `68`. Objetivo:** ligar a previsão probabilística ao erro original
que acompanha toda a análise.

**Fala sugerida:** “Pedimos a probabilidade de óbito para cada registro
original do teste. Depois comparamos essas probabilidades aos desfechos
observados e calculamos o log loss. Guardamos esse resultado como
referência. Não recalculamos uma referência diferente para favorecer
cada variável.”

**O que apontar:** `predict_proba`, a coluna da classe óbito e
`log_loss`. Mostrar que o valor do teste é **0,4090**, o mesmo do
ranking (walkthrough §2). Não confundir `.score()` de um classificador,
que costuma devolver acurácia, com o log loss usado aqui.

**Conclusão e ponte:** “Conhecemos o erro com as informações originais.
Agora vamos romper a correspondência de uma coluna com as fichas.”

## 10. A intervenção no dado — A separate shuffle for each input

**Tela `69`. Objetivo:** entender a cópia, a ordem doadora e a preservação
do desfecho.

**Fala sugerida:** “Fazemos uma cópia do teste original. Uma ordem
aleatória indica de qual linha vem cada idade. Os valores continuam
presentes na coluna do teste inteiro, mas passam a pertencer a outras
fichas. O desfecho não acompanha a idade: continua associado à ficha de
origem.”

**O que apontar:** `x_eval.copy()`, a coluna selecionada, a nova ordem e
os desfechos imóveis. A tabela mostra as mesmas fichas receptoras na
primeira permutação do teste completo, cuja ordem pode trazer doadores de
fora da janela. Não estamos redistribuindo somente as idades visíveis.
Mostrar que `.set_axis(x_eval.index)` alinha os valores às posições de
destino; não restaura sua associação original.

A ordem deve ser aleatória e independente do desfecho. Para testar outra
variável ou outra repetição, voltamos à tabela original. Não embaralhamos
oxigênio sobre uma tabela cuja idade ainda esteja alterada.

**Conclusão e ponte:** “Mudou a associação entre informação e ficha,
não a lista de idades do teste inteiro nem seus desfechos. A pequena
janela pode receber idades que não mostrava antes. Vamos pedir novas
previsões.”

## 11. A nova avaliação — Error after one permutation

**Tela `70`. Objetivo:** acompanhar uma repetição completa e conservar
o sentido do sinal da diferença.

**Fala sugerida:** “O mesmo modelo prevê usando a tabela alterada.
Comparamos suas novas probabilidades com os mesmos desfechos. Para uma
medida de erro, importância é erro após permutar menos erro original:
um resultado positivo significa que perder aquela associação piorou
o desempenho.”

**O que apontar:** nova chamada de `predict_proba`, cálculo de log loss e
registro do erro. Os valores desta tela são da primeira repetição do
teste completo: log loss após permutar idade **0,4914**. Esse resultado
pertence à mesma execução que alimenta a tabela de fichas; não é a média
final **0,4937** das repetições, nem o erro restrito às fichas visíveis
(walkthrough §3–§4).

**Conclusão e ponte:** “Uma ordem aleatória deu um resultado. Para saber
quanto esse resultado depende da ordem escolhida, repetimos.”

## 12. As repetições — Repeat the same experiment

**Tela `71`. Objetivo:** ver de onde vêm a média e o SD do gráfico.

**Fala sugerida:** “A cada passagem pelo laço fazemos uma nova ordem,
partimos das entradas originais, prevemos e guardamos o erro. Cada ponto
representa um embaralhamento de toda a avaliação, não um paciente.”

**O que apontar e acionar:** pausar e usar *Next repeat*. Acompanhar a
linha ativa: copiar e embaralhar → prever → guardar log loss. Depois mover
o controle de repetições para ver a média acumulada. No fim, as **50**
ordens com semente **42** produzem a mesma média e o mesmo SD do ranking
de idade (walkthrough §1, §3–§5). A semente permite reproduzir a sequência;
não torna uma ordem específica clinicamente especial.

Explicar: “O SD amostral usa a dispersão entre as repetições. Não mede o
quanto o modelo mudaria se treinássemos outra vez, nem o quanto o resultado
mudaria numa população futura.” A animação reproduz resultados
registrados pelo Python; o navegador não treina um modelo novo.

**Conclusão e ponte:** “O ranking agora tem uma origem verificável.
Precisamos delimitar o que ele permite afirmar.”

## 13. A interpretação — Predictive reliance, with interpretation limits

**Tela `73`. Objetivo:** transformar cada vantagem ou limite em uma
consequência compreensível.

**Fala sugerida:** “Ganhamos um diagnóstico ligado ao desempenho, usamos
o mesmo modelo e temos uma visão global da avaliação. Mas a resposta
depende do modelo, da medida de erro e dos dados. Um ranking de log loss
pode diferir de um ranking de outra métrica.”

**O que apontar:** associar cada ícone a uma frase. Dependência entre
entradas pode permitir substituição de informações e criar combinações
pouco plausíveis após a troca. Importância alta não informa se a variável
aumenta ou diminui o risco. Não prova causalidade e não explica uma única
previsão individual. As importâncias também não formam, em geral, parcelas
que somamos para decompor o desempenho (walkthrough §7).

Acrescentar se houver pergunta sobre calibração: “log loss avalia erro
probabilístico. Ele se relaciona à calibração, mas não é uma estatística
exclusiva dela; não substitui o gráfico de calibração.”

**Conclusão e ponte:** “Dependência merece uma demonstração concreta.
Vamos observar cardiopatia e diabetes.”

## 14. As entradas relacionadas — Related inputs: change the shuffle

**Tela `dependence-results`. Objetivo:** mostrar que mudar a regra de
permutação muda a pergunta respondida.

**Fala sugerida:** “Embaralhar cardiopatia sozinha rompe sua associação
com diabetes. Se movermos as duas juntas com a mesma ordem doadora,
cada par permanece intacto. Ainda rompemos as associações desse par com
as outras entradas.”

**O que apontar e acionar:** começar em *Both inputs together*, acompanhar
o desenho do par e ler sua barra. Comparar com as permutações individuais.
Dizer que o eixo apresenta log loss adicional multiplicado por **mil**
para tornar valores pequenos legíveis; o SD recebe a mesma escala
(walkthrough §6). Não interpretar a diferença entre a barra conjunta e
a soma das individuais como prova de interação causal ou redundância.

Mudar para *Heart disease within diabetes groups*: “Separamos as fichas
pelos estados originais de diabetes. Embaralhamos cardiopatia apenas
dentro de cada grupo. Diabetes fica fixa. Comparamos o erro com o
original de cada grupo e combinamos as mudanças pelo tamanho dos grupos.”
Esse é o vínculo com a abordagem por subgrupos descrita por Molnar.
Mover o par junto é um diagnóstico complementar, não a mesma operação.

**Conclusão e ponte:** “Restringir a troca por diabetes preserva essa
relação, mas não condiciona em todas as entradas. Essas barras respondem
perguntas diferentes sobre o mesmo modelo. Podemos concluir a aula
nomeando exatamente a pergunta que respondemos.”

## 15. Encerramento — Thank you

**Tela `thanks`. Objetivo:** devolver ao público uma interpretação
curta, correta e aplicável.

**Fala sugerida:** “Mantivemos o modelo, alteramos uma informação,
medimos a mudança do erro e repetimos. Isso mostra de qual informação
este preditor depende para seu desempenho nesta avaliação. Para interpretar
o resultado, precisamos dizer qual modelo, qual erro, quais dados e
qual regra de permutação usamos.”

**O que apontar:** retomar a pergunta da capa e os créditos. Agradecer e
abrir a discussão. Se perguntarem como tornar uma variável clinicamente
relevante, lembrar que a aula avaliou dependência preditiva; essa
relevância exige outras perguntas e evidências.

**Conclusão:** deixar a pergunta completa como frase de referência,
sem acrescentar um novo método no encerramento.

## Preparação: o que foi corrigido e por que o recorte pode melhorar?

Na versão atual, o gráfico da experiência e o ranking compartilham o
mesmo log loss original e as mesmas médias globais das permutações. O gráfico
da experiência **não calcula o log loss apenas das fichas visíveis**.
A tabela mostra uma janela da primeira execução registrada no teste
completo; o gráfico resume todas as repetições. Uma execução não precisa
ser numericamente igual à média de todas elas.

Para entender uma queda do log loss, olhar as perdas individuais: numa ficha
com óbito, uma probabilidade que sobe na direção do desfecho reduz a perda;
numa ficha com sobrevida, o mesmo movimento pode aumentá-la. A média
combina as duas situações. O saldo de poucas fichas numa ordem específica
não determina o saldo de toda a avaliação em várias ordens. Permanecer
com a mesma contagem de erros de classe tampouco fixa o log loss.

**Correção do exemplo anterior:** a ordem manual antiga trocava valores
entre fichas do mesmo desfecho. Por preservar informação do alvo nas
trocas, ela não era uma boa introdução à permutação marginal. Além disso,
o gráfico do recorte e o gráfico global mostravam medidas diferentes, o
que dificultava a comparação entre slides. Agora as mesmas fichas
receptoras exibem valores da primeira permutação do teste inteiro, com
ordem aleatória independente dos desfechos e registro reprodutível
(walkthrough §3). Seus doadores podem vir de outras linhas do teste.
As fichas visíveis continuam escolhidas por desfecho; não devem estimar
prevalência ou desempenho global.

A melhor função desta tabela é explicar o mecanismo, não validar um
ranking. Pausar após a troca, conferir que somente uma entrada mudou e
ler algumas probabilidades. Ler a estimativa de importância no gráfico
global, sem atribuí-la à média da janela. Não escolher novos pacientes ou
procurar uma semente só para obter um resultado visualmente conveniente.

## Respostas curtas para perguntas frequentes

- **“A idade perdeu importância porque o erro de algumas fichas caiu?”**
  Não podemos concluir isso pelo recorte. A PFI global resume as
  repetições no teste completo; uma troca isolada pode ajudar ou prejudicar.
- **“A importância global mudou ao trocar a métrica?”** Mudamos a régua de
  avaliação; o modelo e suas probabilidades permanecem iguais. A estimativa
  global com log loss é aproximadamente
  **20,7%**, calculada com os valores completos, não com os números
  arredondados que aparecem na tela (walkthrough §5). O log loss original
  global é **0,4090** (walkthrough §2). A comparação com as outras métricas
  permanece documentada no estudo de sensibilidade (walkthrough §8).
- **“Um aumento absoluto da perda de 0,0846 significa mais óbitos?”** Não. É a mudança
  média na perda das probabilidades, em unidades de log loss (walkthrough §4).
  Uma porcentagem relativa desse erro também não é uma porcentagem de óbitos.
- **“A razão deve começar em um?”** Um é a referência de nenhum efeito.
  Valores menores são possíveis quando a perda após permutar diminui.
- **“Se a categoria trocada foi igual, o modelo precisa mudar a previsão?”**
  Não. Sem mudança efetiva nas entradas de uma ficha, o mesmo preditor
  recebe a mesma informação.
- **“log loss mede só calibração?”** Não. É uma medida de erro probabilístico;
  avaliar calibração requer olhar também sua relação com a frequência
  observada dos desfechos.
- **“Os bigodes são um intervalo de confiança?”** Aqui, as hastes mostram
  SD entre embaralhamentos. Boxplots, quando presentes nos materiais de
  estudo, usam quartis e uma regra própria de bigodes. Nenhum incorpora
  automaticamente novos treinos ou uma população futura.
- **“Posso remover uma entrada de baixa importância?”** A decisão exige
  um estudo de seleção e avaliação; o ranking do modelo fixo não o substitui.
- **“Permutar o par resolve toda dependência?”** Preserva o par escolhido;
  suas relações com as demais entradas podem mudar.
- **“Os subgrupos implementam a PFI condicional completa?”** Aqui a
  restrição considera diabetes. Não cobre todas as outras entradas.

## Referências da aula

As entradas completas estão no [README do módulo](../README.md#referências):
Molnar, capítulo 23; Raschka, aula de feature selection; e a documentação
oficial do algoritmo de permutation importance do scikit-learn.
