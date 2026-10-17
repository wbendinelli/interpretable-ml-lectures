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

**Tela `cover`. Objetivo:** apresentar o tema e a pergunta que conduz a aula,
com título, subtítulo, nome e disciplina, seguindo a hierarquia da capa do LIME.

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

**Por que este mapa?** Uma medida de importância pode apoiar a seleção de variáveis, que pode reduzir o número de entradas do modelo. Nesta aula, porém, queremos interpretar um modelo já treinado. Por isso usamos o mapa de interpretação do Molnar para situar a PFI. Essa ligação basta como contexto; a comparação com seleção será discutida no slide 5.

**Fala sugerida:** “Já temos um modelo e queremos entender como ele usa
as informações. No livro de Molnar, podemos localizar a PFI por estas
categorias. Ela é post-hoc: a explicação acontece depois do treinamento.
É model-agnostic: não precisamos examinar a estrutura interna do modelo;
usamos suas previsões. É global: avaliamos o comportamento no conjunto
de dados, em vez de explicar uma única previsão. E mede feature
importance: a importância de uma variável segundo uma definição explícita.
Na PFI, essa definição é a mudança no erro de previsão quando embaralhamos
a variável, mantendo o modelo fixo.”

**O que cada bloco representa:**

Leia cada bloco como resposta a uma pergunta.

1. **Post-hoc — Quando fazemos a explicação?**

   **Depois do treinamento.** Primeiro construímos o modelo; depois investigamos seu comportamento.

   No nosso caso, o XGBoost já está treinado. Durante a PFI, ele permanece fixo: não aprende novamente quando embaralhamos uma variável. [Molnar — teoria da PFI](https://christophm.github.io/interpretable-ml-book/feature-importance.html#theory)

2. **Model-agnostic — Precisamos examinar o interior do modelo?**

   **Não precisamos conhecer suas árvores, coeficientes ou pesos internos.** Podemos fornecer entradas e observar suas previsões.

   Isso permite aplicar a PFI a diferentes tipos de modelo. Mas atenção: *agnostic* descreve como acessamos o modelo. **A importância obtida continua sendo específica daquele modelo, dos dados e da métrica escolhida.** Outro modelo pode produzir outro ranking. [Documentação do scikit-learn](https://scikit-learn.org/stable/modules/permutation_importance.html)

3. **Global — Estamos explicando uma pessoa ou o conjunto?**

   **O resultado resume o comportamento no conjunto avaliado.**

   A pergunta é: “Quanto o desempenho muda quando alteramos essa informação nas fichas avaliadas?”. Isso ajuda a fazer a ponte com o LIME: lá, o foco era explicar uma previsão individual; aqui, é avaliar a importância das variáveis no conjunto. [Molnar — métodos locais e globais](https://christophm.github.io/interpretable-ml-book/overview.html)

4. **Feature importance — Que aspecto queremos entender?**

   Queremos avaliar **quais variáveis são importantes segundo um critério definido**. Diferentes métodos podem definir importância de maneiras diferentes.

   Isso também é diferente de perguntar se aumentar a idade aumenta a previsão de óbito. Uma pergunta trata de **importância**; a outra, do **efeito da variável sobre a previsão**. [Molnar — importância e efeitos](https://christophm.github.io/interpretable-ml-book/overview.html)

5. **Permutation Feature Importance — Qual é o nosso critério?**

   Comparamos o erro antes e depois de embaralhar uma variável.

   Por exemplo: redistribuímos as idades entre as fichas, mantemos as demais informações e os desfechos, fazemos novas previsões com o mesmo modelo e recalculamos o erro. **O aumento do erro mede a importância por permutação.** Molnar recomenda avaliar isso em dados que não participaram do treinamento; na nossa apresentação, usamos o teste. [Molnar — procedimento da PFI](https://christophm.github.io/interpretable-ml-book/feature-importance.html#theory)

**O que fica para o slide 5:** No slide 2, explicar o significado dos blocos e o propósito do percurso. Reservar para o slide 5 a diferença entre interpretar o modelo e selecionar suas entradas. Não abrir aqui uma revisão dos métodos de redução de dimensionalidade nem de LOFO.

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
na mortalidade; agora vamos separar o que podemos e o que não podemos concluir do ranking.”

## 5. Conclusões do ranking — What can we conclude from the ranking?

**Tela `65`. Objetivo:** distinguir o que aprendemos com o ranking e o
que ele não permite concluir sozinho. O slide apresenta as conclusões
em pares; as explicações abaixo servem de apoio para a fala.

**Como apresentar o quadro:** “Vamos ler por temas. À esquerda, o que o
experimento sustenta. À direita, exemplos de afirmações que essa medida,
sozinha, não autoriza.” As frases entre aspas na coluna da direita são
exemplos de conclusões indevidas, não citações de Molnar. Usar o ícone e
o título de cada grupo como ponto de apoio; não ler uma coluna inteira
antes de passar à outra.

**Fala para impacto preditivo e causalidade:** “Mais acima neste ranking
significa que o erro piorou mais quando embaralhamos aquela variável.
Isso descreve o desempenho deste modelo. Não demonstra uma causa do
óbito.”

**Fala para perda e risco:** “O valor da importância mede uma mudança na
perda de previsão. Ele não mede uma mudança no risco de morrer e não
mostra se aumentar a variável faz a previsão subir ou descer.”

**Fala para pouca mudança no erro:** “Quando a diferença de perdas é
próxima de zero, o erro médio quase não mudou após o embaralhamento.
Isso, sozinho, não torna a variável cientificamente irrelevante nem
decide sua retirada.” Neste grupo, próximo de zero se refere à
**diferença** entre perdas; na **razão**, a referência de nenhuma mudança
é um. O significado é o mesmo: comparar a perda após a permutação com
a perda original.

**Posição no ranking e causalidade.** Podemos comparar o aumento de erro
produzido pelas permutações, neste modelo, nos dados avaliados e com a
perda escolhida. Essa é uma conclusão sobre desempenho preditivo. A
permutação altera a informação fornecida ao modelo; não é um experimento
que muda a idade real de pacientes e observa o que acontece com sua
saúde. Esse procedimento, sozinho, não identifica um efeito causal da
variável sobre o desfecho. Uma variável no topo não é, por isso, a
principal causa do óbito nem a mais importante em qualquer contexto.

**Magnitude da perda e direção do efeito.** A PFI informa quanto a perda
de previsão mudou após o embaralhamento. Ela não informa se valores
maiores da variável aumentam ou diminuem a previsão de óbito. Um aumento
percentual da perda também não representa um aumento percentual do risco
de morrer. Na nossa aula, a interpretação é sempre sobre log loss.
O método pode incluir efeitos e interações diferentes em um único
resumo; não descrevemos essas relações apenas pelo ranking.

**Pouca mudança no erro e relevância da variável.** O embaralhamento pouco
mudou o erro médio neste experimento. Isso não prova ausência de
informação útil, irrelevância científica ou clínica, nem ausência de
efeitos em todas as fichas. Também não mede com que frequência o modelo
usa internamente a variável: ele pode usá-la sem melhorar suas previsões.
Conhecimento científico deve ser considerado conforme o objetivo do
estudo. O ranking, sozinho, não impõe a inclusão nem a exclusão da
variável no preditor.

Se quisermos estudar remoção, precisamos avaliar os conjuntos candidatos
e o desempenho dos modelos resultantes sob um protocolo de seleção.
Esse é um estudo adicional; o ranking não valida automaticamente um
modelo reduzido. Como já inspecionamos o teste temporal, reutilizá-lo
para escolher entradas o tornaria parte da seleção, não uma nova
confirmação independente.

**O que apontar:** ler os pares de conclusões, uma linha por vez.
Primeiro, desempenho e causalidade; depois, magnitude e direção; por
fim, importância próxima de zero e relevância ou remoção. Evitar traduzir
PFI baixa como “o modelo quase não usa essa variável”.

**O que fica para o exemplo de dependência:** como a relação entre
entradas muda a interpretação da permutação. As fortalezas e os cuidados
gerais do método ficam no apoio para a fala, sem uma tela de revisão.
Aqui delimitamos a leitura do ranking.
**Referências:** [Molnar, interpretação e vantagens da PFI](https://christophm.github.io/interpretable-ml-book/feature-importance.html#strengths)
e [limitações de interpretação](https://christophm.github.io/interpretable-ml-book/feature-importance.html#limitations)
fundamentam a leitura do ranking. A distinção com seleção é explicitada
em [Molnar, LOFO: relação com seleção](https://christophm.github.io/interpretable-ml-book/lofo.html#strengths).

**Conclusão e ponte:** “Essas conclusões se referem ao modelo e aos dados
que avaliamos. Vamos conhecer agora de onde vieram esses dados e como
chegamos ao modelo explicado.”

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

**O que apontar em Data split:** os períodos, a amostragem somente do treino
e o símbolo de preditor fixo. Em **Model results**, ler primeiro a comparação
entre famílias selecionadas pelo menor log loss de validação; depois, a
comparação separada das estratégias de balanceamento dentro do XGBoost.

**Fala sobre a escolha:** “A seleção histórica usava AUC, que avalia a
ordenação dos riscos. Preservamos esse registro e fizemos uma rodada por
log loss, que avalia as probabilidades atribuídas aos desfechos. Os parâmetros
foram selecionados na validação, com preparação aprendida somente no treino.
Constante e OLS são referências sem tuning; as demais famílias têm grades
e orçamentos declarados. A tabela apresenta a melhor configuração encontrada
em cada família, não a melhor possibilidade universal daquele algoritmo”
(walkthrough §1; módulo 00, walkthrough de famílias §2–§5).

Não atribuir toda diferença frente à tabela antiga somente à métrica: a
preparação histórica também difere do pipeline atual ajustado só no treino.
Os resultados da busca não substituem silenciosamente o objeto explicado
pelas telas de PFI.

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

**Pré-requisitos do exemplo:** o modelo treinado, `x_eval` com todas as
entradas do teste e `y_eval` com os desfechos na mesma ordem vêm do estudo
registrado. `feature` é o nome da coluna que será embaralhada, não uma
idade, peso ou hiperparâmetro. O modelo continua recebendo todas as entradas.
Os imports aparecem primeiro; o exemplo completo confere a ordem das
classes, os tamanhos e os índices, quando disponíveis. Garantir a
correspondência de cada registro com seu desfecho faz parte da preparação.
O código mostra a PFI
de uma entrada escolhida; para montar o ranking, aplicamos o procedimento
separadamente às demais entradas, sempre a partir do teste original.

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
`[:, 1]` seleciona a probabilidade da classe na segunda posição; o
exemplo confere que `model.classes_` é `[0, 1]` e a definição do alvo
estabelece que a classe positiva representa óbito registrado. A conversão
para `float64` mantém a precisão usada no cálculo da perda do estudo.

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

Antes do laço, `rng` cria o gerador com a semente registrada, e `orders`
guarda as ordens de linha. O laço percorre essas ordens. A tela seguinte
mostra a continuação indentada desse mesmo laço: somente embaralhar não
produz uma importância; ainda precisamos prever e medir a perda.

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

No trecho ampliado desta tela, `enumerate(orders, 1)` acrescenta o número
da repetição para acompanhar a execução; o experimento continua o mesmo.
`shuffled` guarda temporariamente os valores reordenados que serão
atribuídos à coluna da cópia.
`errors` guarda uma perda global por ordem. Só depois do laço calculamos
as diferenças, a média e o SD amostral (`ddof=1`). O exemplo completo
reúne os trechos e declara os dados de entrada necessários; não é um
programa autônomo de aquisição de dados ou de treinamento.

**Conclusão e ponte:** “Já sabemos como o ranking foi calculado. Agora
vamos investigar o que acontece quando as entradas estão relacionadas.”

## 13. Entradas dependentes — Dependent inputs: shuffling within groups

**Tela `dependence-results`. Objetivo:** explicar como a permutação livre
altera a relação entre idade e cardiopatia e como restringir os doadores
preserva as distribuições etárias dentro dos grupos. A idade continua
numérica no modelo; as faixas aparecem somente no desenho.

**Escopo antes de começar:** são **8.888** registros do teste **2024** com
idade válida e cardiopatia registrada como Sim/Não. Ficam fora **7.254** dos
**16.142** registros do teste. O mesmo XGBoost recebe as **40 entradas**,
sem novo treinamento. O log loss original deste recorte é **0,5042**;
o **0,4090** anterior descreve o teste completo (internals §8–§9).

**Roteiro para apresentar:**

1. **Definir os papéis.** “Embaralhamos idade. Cardiopatia define quem pode
   doar a idade.” Os grupos são Cardiopatia = Não e Cardiopatia = Sim,
   não os desfechos, as faixas etárias ou as células do gráfico.
2. **Ler o original.** Cada linha tem sua própria distribuição de idades.
   A área da bolha conta fichas; o percentual divide pelo total da linha:
   **3.502** sem cardiopatia e **5.386** com cardiopatia. Pearson entre idade
   contínua e cardiopatia binária é **0,353**, uma associação moderada neste
   recorte. Não caracteriza perfis jovens com cardiopatia como impossíveis
   (internals §8–§9).
3. **Embaralhar livremente.** “Uma ficha pode receber a idade de qualquer
   outra ficha deste recorte, inclusive de outro grupo.” Cardiopatia,
   os demais dados e os desfechos ficam nas suas linhas. As distribuições
   das duas linhas se aproximam, alterando a relação observada.
4. **Restaurar e restringir.** “Recuperamos as entradas originais. Agora a
   idade só circula entre fichas do mesmo estado de cardiopatia.” Mostrar
   primeiro o grupo Não e depois o Sim. As contagens por faixa são
   preservadas, mas os valores individuais podem mudar, inclusive dentro
   da mesma faixa. Não aplicamos uma permutação sobre a outra.
5. **Ler o erro da execução animada.** O log loss vai de **0,5042** para
   **0,5422** na livre e para **0,5397** na restrita. São resultados da
   primeira ordem registrada, partindo separadamente do original
   (internals §9).
6. **Ler a PFI repetida.** Em **50 repetições**, semente **42**, a PFI por
   diferença é **0,0355 ± 0,0024** na livre e **0,0334 ± 0,0021** na restrita.
   As perdas médias são **0,5397** e **0,5376**. O ± mostra SD amostral entre
   permutações (`ddof=1`), com modelo e coorte fixos, não intervalo de
   confiança ou variação entre treinamentos (internals §8–§9).

**Pergunta provável — “Bolhas iguais significam previsões iguais?”**
Não necessariamente. O gráfico agrega as idades em faixas e não identifica
qual ficha recebeu cada idade. A nova combinação com as demais entradas
pode mudar a previsão, mesmo com as distribuições por cardiopatia preservadas.
Os pacotes animados resumem fluxos reais entre faixas; não são pessoas
identificadas trocando idades nem representam todos os fluxos do sorteio.

**Pergunta provável — “O procedimento por grupo corrigiu a PFI?”**
Ele preservou a distribuição da idade dentro de cada estado de cardiopatia.
A diferença média entre as PFI é **0,0021**, com SD pareado **0,0032**;
não demonstramos grande correção ou superioridade de um procedimento
(internals §8–§9). Outras dependências ainda podem ser rompidas.

**Conclusão e ponte:** “Ao restringir quem doa a idade, preservamos essa
relação por grupo. A idade continua importante, mas o resultado depende
também da regra de permutação.” A abordagem adapta os subgrupos de Molnar,
sem condicionar em todas as outras entradas ou estabelecer causalidade.

Fonte: [evidência de idade e cardiopatia](../evidence/pfi_age_cardiopathy.json),
produzida por [internals §9](../notebooks/pfi_internals.ipynb), reutilizando
os vetores da §8. O [exemplo de diabetes](../evidence/pfi_diabetes_subgroups.json)
permanece documentado com seu próprio recorte e valores (internals §7).
Referência: [Molnar, abordagem por subgrupos](https://christophm.github.io/interpretable-ml-book/feature-importance.html#group-wise-pfi-example).

## 14. Encerramento — Thank you

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

## Apoio para a fala: fortalezas e limitações

Este conteúdo foi retirado da sequência projetada por repetir pontos já
explicados. A PFI liga a importância à mudança do erro, resume a avaliação
no conjunto e mantém o modelo treinado. Precisamos conhecer os desfechos,
repetir os embaralhamentos e delimitar modelo, perda, dados e procedimento.

Dependência entre entradas pode permitir substituição de informações e
criar combinações pouco plausíveis após a troca. As interações podem
contribuir para a importância de mais de uma entrada; as importâncias
não são, em geral, parcelas que somamos para decompor o desempenho
(walkthrough §7).

Se houver pergunta sobre calibração: “Log loss avalia erro probabilístico.
Não é uma estatística exclusiva de calibração e não substitui sua curva.”
Os limites de causalidade, direção do efeito e seleção de entradas
continuam na discussão do ranking.

Referência: [Molnar, fortalezas](https://christophm.github.io/interpretable-ml-book/feature-importance.html#strengths)
e [limitações](https://christophm.github.io/interpretable-ml-book/feature-importance.html#limitations).

## Apoio para perguntas: as outras operações de dependência

O registro técnico também conserva diabetes embaralhada sozinha e a permutação
conjunta de cardiopatia e diabetes. Elas não são necessárias para a explicação
principal desta tela. No diagnóstico conjunto, as duas respostas vêm da mesma
linha doadora: o par permanece intacto, mas muda de ficha. Relações com outras
entradas ainda podem ser rompidas. Essa é uma pergunta complementar, diferente
da abordagem por subgrupos de Molnar. Comparar a importância conjunta com a soma
das individuais não isola interação, redundância ou causalidade (walkthrough §6).

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
