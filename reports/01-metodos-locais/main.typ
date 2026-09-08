#import "@preview/sapians:0.3.0": *
#import "figuras.typ": *

#show: sapians-article.with(
  title: "Um paciente, cinco perguntas",
  abstract: [
    Cinco métodos locais de interpretabilidade (perfis ceteris paribus,
    ICE, LIME, contrafactuais e SHAP) aplicados a um único paciente e a um
    único modelo: um XGBoost que prevê óbito hospitalar por COVID a partir
    da ficha de SRAG do SIVEP-Gripe. O paciente, escolhido por uma regra
    escrita antes de olhar, atravessa os cinco. Cada método é julgado por
    duas coisas: a pergunta clínica que deveria responder, e o preço que
    cobra para responder, medido em quantos pacientes impossíveis ele
    precisa fabricar pelo caminho.
  ],
  authors: (
    (name: "William Bendinelli", affiliation: "Instituto de Ciências Matemáticas e de Computação · USP"),
  ),
  lang: "pt",
  kicker: "SCC5819 · Tópicos em Inteligência Artificial",
  journal: "ICMC-USP · Universidade de São Paulo",
  abstract-title: "Resumo",
  keywords-title: "Palavras-chave",
  keywords: (
    "interpretabilidade", "SRAG/SIVEP-Gripe", "ceteris paribus", "ICE",
    "LIME", "contrafactuais", "SHAP",
  ),
)


// Corpo com respiro: o template traz um corpo menor, pensado para artigo.
// Um texto que precisa ensinar pede letra e entrelinha mais folgadas.
#set text(size: 9pt)
// Parágrafo à moda de periódico: recuo de primeira linha em vez de espaço
// entre parágrafos, e sem recuo no que abre uma seção. Separa melhor e
// ocupa menos página.
#set par(leading: 0.62em, spacing: 0.62em,
         first-line-indent: (amount: 1.1em, all: false))

// Legenda no padrão de periódico: menor que o corpo, alinhada à esquerda,
// com o rótulo em negrito destacando o número da figura.
// O vão entre a figura e a legenda é `figure.gap`, e só ele: um `above:`
// no bloco da legenda é inerte, porque o bloco não faz fronteira com a
// figura, o gap faz. Verificado variando os dois e medindo a página.
#set figure(gap: 1.8mm)
#show figure.caption: it => block(width: 100%)[
  #set text(size: 7.6pt, fill: sapians-muted-dark)
  #set par(justify: true, leading: 0.56em)
  #align(left)[
    #text(weight: "bold", fill: sapians-text-dark)[#it.supplement #context it.counter.display(it.numbering).]
    #h(0.5mm)#it.body
  ]
]

// Hierarquia de títulos: o template fixa 10 pt para tudo, e o nível 2 vinha
// menor que o corpo. Um título nunca é menor que o texto que ele encabeça.
// `sticky: true` cola o título ao parágrafo seguinte, como o heading
// nativo do Typst faz: um título nunca fica sozinho no pé de uma coluna.
// O `below` tem de ser MAIOR que o `leading`, ou o título encosta na linha
// que encabeça. Bloco adjacente a parágrafo tem precedência sobre
// `par.spacing` (não colapsa pelo maior), então o valor escrito aqui é o
// valor aplicado. Os valores abaixo foram calibrados medindo o PNG, não
// pela aritmética de caixa: o vão de caixa não vira vão óptico na mesma
// proporção. Sem dígitos neste comentário de propósito — o verificador de
// números lê o fonte inteiro, comentário incluído.
#show heading.where(level: 1): it => block(
  sticky: true, above: 5.0mm, below: 2.6mm,
  text(size: 10.5pt, weight: "bold", it.body),
)
#show heading.where(level: 2): it => block(
  sticky: true, above: 3.8mm, below: 2.8mm,
  text(size: 9.2pt, weight: "bold", fill: sapians-terracotta, it.body),
)

#let sp-tab(fonte: none, cabecalho: (), ..args) = block(width: 100%, above: 2.6mm, below: 4mm, breakable: true)[
  #set text(size: 7.4pt)
  #set par(leading: 0.55em)
  // Booktabs: filete grosso no topo e no pé, fino sob o cabeçalho, e nada
  // mais. Sem linha vertical e sem malha, como em IEEE, Elsevier e ACM.
  // breakable: true + table.header faz o cabeçalho repetir se a tabela
  // atravessar uma coluna ou página. Os dois table.hline abrem e fecham
  // a tabela no lugar de um block(stroke: ...) por fora.
  #table(
    stroke: (x, y) => (top: if y == 1 { 0.4pt + sapians-muted-dark } else { 0pt }),
    fill: none,
    inset: (x: 2.2mm, y: 1.5mm),
    align: left,
    table.hline(stroke: 0.9pt + sapians-text-dark),
    table.header(..cabecalho),
    ..args,
    table.hline(stroke: 0.9pt + sapians-text-dark),
  )
  #if fonte != none [#v(1mm) #text(size: 6.6pt, fill: sapians-muted-dark)[Fonte: #fonte]]
]

= 1. Introdução

Um método de interpretabilidade *agnóstico de modelo* explica o modelo
por fora. Não abre a caixa: não lê coeficientes, não percorre árvores,
não olha pesos. Faz o que qualquer usuário faria: muda o que entra e
observa o que sai. Por isso serve igualmente para uma regressão
logística e para o comitê de árvores deste relatório.
Quatro dos cinco
métodos aqui são assim de ponta a ponta; o quinto, o SHAP, é agnóstico
na definição, mas para árvores existe uma implementação que percorre a
árvore, e é ela que este relatório usa.

*Local* é a outra metade do nome. Um método global descreve o modelo
inteiro, o que ele faz em média sobre a população toda; um método local
explica *uma* predição, sobre *um* paciente. É a diferença entre "o que
este modelo faz em geral" e "por que ele disse isto sobre esta pessoa".

O modelo aqui prevê óbito hospitalar por COVID a partir de variáveis
disponíveis na admissão da ficha de Síndrome Respiratória Aguda Grave
(SRAG), com duas exceções declaradas: a coinfecção viral, que é resultado
de laboratório, e o marcador de caso nosocomial. No teste
de 2024 ele faz AUC 0,7644.#footnote[Módulo 00: a AUC do modelo do curso
no teste de 2024, lido uma vez só e depois de a escolha estar fechada.]
Isso se lê assim: sorteie ao acaso um paciente que morreu e outro que
sobreviveu, e o modelo dá risco maior ao que morreu nessa fração das
vezes, com um empate valendo meio acerto. Uma AUC diz o quanto o modelo
*ordena*; não diz se os riscos que ele imprime estão no nível certo, nem
em quem, nem por quê. Para um comitê
que decide sobre um paciente, essa é a distância entre uma estatística e
uma resposta.

Os cinco métodos locais do curso existem para essa pergunta, e aqui
todos caem sobre o mesmo modelo, sob uma restrição que muda a leitura: é
sempre *o mesmo paciente*. Na ordem em que foram estudados: o perfil
ceteris paribus (e se a idade fosse outra?), o ICE
(os outros pacientes respondem igual?), o LIME (por que esta predição,
localmente?), os contrafactuais (o que teria de mudar?) e o SHAP (quanto
cada variável pesou?).

Dois fatos atravessam as cinco seções. O primeiro: a ficha do SIVEP
desliga campos. As treze comorbidades só aparecem preenchidas nos
registros em que o campo de fator de risco diz que há algum; onde ele
está em branco, o bloco inteiro está em branco junto, e não por descuido:
a pergunta não chegou a ser feita. Então mexer numa variável de cada
vez, deixando as outras paradas, que é o que os cinco métodos fazem,
produz fichas que o formulário não permitiria, e nesta base dá para
*contar* quantas. Uma regra dessas é uma *cerca*; uma linha que a
atravessa é um *paciente impossível*.

O segundo: o mundo mudou no meio. O modelo aprendeu com os anos de 2020
a 2022, quando se morria muito mais, e prevê em 2024, quando a letalidade
da coorte já caíra de 31,4% para 18,2%.#footnote[Módulo 00: a letalidade
observada de cada split, treino contra teste, dentro da coorte que o
modelo enxerga.] Isso é a *deriva de
regime*, e ela deixa marca em cinco lugares deste relatório: na base, na
calibração do modelo, nas curvas do ICE, no posto do SHAP e nos
contrafactuais. Um achado só, visto por cinco instrumentos.

Vale aqui a regra de evidência do repositório: todo número em prosa é
impresso por uma célula de caderno versionada, e as notas de rodapé deste
texto dizem onde cada uma vive.

= 2. O caso: a base, o tratamento e o modelo

A fonte é o SIVEP-Gripe, o sistema com que o Ministério da Saúde vigia a
Síndrome Respiratória Aguda Grave: cada internação por SRAG no país vira
uma ficha, e também cada óbito por SRAG, mesmo sem internação. São
4.109.567 notificações entre 2019 e
2024.#footnote[Módulo 00: a contagem de fichas do extrato congelado que
serve a todo o curso; ele é datado porque a ficha muda entre versões.]

O tratamento tem três camadas, e a fronteira entre elas é uma pergunta
que se faz a cada valor. O *Bronze* é o dado como foi baixado, byte a
byte, nunca alterado: esse valor veio assim da fonte? O *Prata* afirma
fatos sobre o registro, o tipo de cada campo, os valores que ele admite e
os três jeitos diferentes de um campo estar vazio: esse valor está
determinado pelo registro sozinho? O *Ouro* faz as escolhas da tarefa,
com dono e data, o alvo, a coorte, a janela, a divisão treino/teste e a
codificação: esse valor depende do que se quer prever?

A separação não é estética. Enquanto o alvo não é escolhido, nada no
tratamento depende do que se quer prever, e um único Prata serve a todos
os módulos do curso. Trocar de alvo não refaz a limpeza.

Aqui o alvo é o óbito entre os casos já fechados, e a coorte é a dos
hospitalizados com COVID. Ela sai de um funil de seis filtros, publicado
na ordem em que os filtros correm, porque as contagens não comutam: cada
"restam tantos" só significa alguma coisa se estiver dito o que saiu
antes. Ao fim do funil resta a coorte sobre a qual os cinco métodos
trabalham.

A divisão entre treino, validação e teste é temporal, e não sorteada,
porque a população não é estacionária: em tempo normal a SRAG tem duas
pontas, um pico pediátrico de casos e um pico idoso de óbitos, e sob
COVID o peso se desloca inteiro para o idoso. Sortear linhas misturaria os
regimes entre treino e teste, e o modelo seria avaliado nos mesmos anos
em que aprendeu. A queda de letalidade sumiria da avaliação em vez de
aparecer nela, e o número medido ficaria melhor do que o de uso. O
treino vai até 2022, a validação é 2023 e o teste é 2024.

Na fronteira dessa divisão está o achado que os cinco módulos vão
explicar: a letalidade observada da coorte cai quase pela metade do
treino para o teste. Para este relatório não é um incômodo a corrigir, é
o objeto: é o mundo tendo mudado enquanto os dados eram coletados, e são
cinco métodos apontados para essa mudança. Para uso clínico seria outra
coisa, porque a validação temporal revela a deriva e não a conserta.

== O modelo, escolhido por protocolo

O modelo do curso não foi escolhido por gosto. Antes de qualquer leitura
do teste, um protocolo foi escrito e versionado: vence a maior AUC na
validação de 2023, com modelos dentro de um erro-padrão bootstrap
tratados como empatados e a calibração servindo de primeiro desempate, e
o teste é lido uma vez, depois da escolha, sem poder desfazê-la. Aqui não
houve empate, então quem escolheu foi a AUC sozinha, e vale dizer o
limite: um critério de discriminação é cego para o nível do risco, que é
exatamente a dimensão em que o vencedor falha. Seis famílias concorreram, do modelo constante ao
XGBoost, e venceu o XGBoost, com os hiperparâmetros que o próprio estudo
ajustou. A regressão logística fica ao lado como termo de comparação, e
a distância entre as duas é o problema que este curso existe para
resolver.

#figure(
  scope: "parent",
  placement: auto,
  fig-selecao(),
  caption: [
    O protocolo que escolheu o modelo do curso: os candidatos aprendem no
    treino, a escolha acontece na validação, e o teste é lido uma vez,
    depois dela. A barreira do meio é código, não promessa: a função que
    escolhe o modelo levanta uma exceção se enxergar o teste. A figura
    ensina o desenho do estudo; o placar com todos os candidatos vive no
    módulo 00.
  ],
)

No teste de 2024 o modelo prevê 0,2154 de risco médio de óbito onde se
observa 0,1824.#footnote[Módulo 00: o risco médio que o modelo prevê no
teste de 2024, ao lado da letalidade que de fato se observou nesse ano.]
Essa diferença entre o que o modelo espera em média e o que de fato
aconteceu é a *calibração-in-the-large*, o degrau mais fraco da
calibração: o modelo prevê cerca de um quinto de óbitos a mais do que
ocorreram. É a deriva de regime por dentro do modelo, que aprendeu
letalidades antigas e encontrou outro mundo.

A capacidade de *ordenar* pacientes não sofre junto, e a distinção é a
lição. A AUC é uma medida de posto, invariante a qualquer reescala
monótona do risco, então um desvio de nível não a toca. O módulo 00 mede
0,7564 na validação de 2023, com erro-padrão bootstrap de 0,0039, contra
0,7644 no teste de 2024: a diferença é da ordem de dois erros-padrão, e
não na direção de piorar. Por ano de início a série vai de 0,7890 em 2020
a 0,7680 em 2024, com o fundo em
2022, dentro do treino.#footnote[Módulo 00, internals do modelo §2: a AUC
por ano de início. O erro-padrão vem do bootstrap pareado do estudo de
seleção, em `SELECTION.md`.]
O que a deriva estraga é o nível, não a ordem, e é por isso que uma
recalibração conserta o primeiro sem custar nada do segundo.

== As quatro impossibilidades

Quatro regras proíbem combinações de valores nesta base, e são as quatro
cercas: uma vem do formulário, uma do calendário da campanha, e duas da
definição de coorte que este curso escolheu. De cada uma se mede a mesma
coisa: a fração da amostra que está *em cima* da fronteira, aquela para
quem uma única perturbação já cai do lado impossível.

*O portão do funil.* As treze comorbidades só aparecem preenchidas nos
registros em que o campo de fator de risco diz que há algum; onde ele
está em branco, o bloco inteiro está em branco junto. A ficha oferece um
"não" explícito, mas ele nunca foi usado: em seis anos de base, o valor
"não" não aparece uma única vez. O vazio, portanto, não diz que o
paciente não tem comorbidade; diz que a pergunta não foi respondida.
Marcar uma comorbidade nesse estado contradiz um portão que, medido nos
seis anos da base, nunca foi contrariado.

*A pré-campanha.* A campanha de vacinação tem data de início, e quem
adoeceu antes dela quase certamente não tinha dose alguma. As exceções
existem e a base as registra sem corrigir, porque houve voluntários de
ensaio clínico e brasileiros vacinados no exterior. A cerca trata a regra
como quase-certeza, não como lei: a linha que ela barra é a de quem
adoeceu antes da campanha e tem contagem de doses positiva, e aumentar
essa contagem atravessa a fronteira.

*O critério-2 por um fio.* A coorte deste curso reproduz o filtro do
script do Ministério: entra quem foi hospitalizado e marcou tosse ou dor
de garganta, e ao menos um entre falta de ar, queda de saturação e
desconforto respiratório. Quem entrou marcando *um só* dos dois sintomas
do primeiro grupo está por um fio: desligar esse sintoma o tira do
filtro, e sem o filtro ele não estaria nesta coorte. É o estado mais
comum da amostra, de longe. A ressalva importa: a definição clínica de
SRAG em vigor durante toda a janela é mais larga, porque basta síndrome
gripal, dois de oito sintomas com a febre entre eles, mais um sinal de
gravidade, que inclui a pressão persistente no tórax e a cianose. A cerca
é da coorte que construímos, não da definição de caso do país.

*O critério-3 por um fio.* O mesmo, no segundo grupo, com três sintomas
em vez de dois e bem menos gente pendurada nele.

Perturbar uma linha através de qualquer dessas fronteiras fabrica um
paciente que não pode existir. Os cinco módulos fazem essa conta pela
*mesma* função que conta o impossível (`gate_impossible`), o que torna
os números idênticos por construção. Quem é esse paciente, e por que uma
regra o escolheu, é a próxima seção.


= 3. O paciente e as três cercas

== Quem é o paciente

O paciente deste relatório não foi escolhido a dedo. Ele veio de uma regra
escrita antes de olhar: entre todos os pacientes do ano de teste, aquele
cuja predição cai mais perto da fronteira da decisão, que este relatório
fixa em meia probabilidade por convenção de exposição e não por ser um
ponto de operação clínico, com o identificador
servindo de desempate.

O escolhido, pela regra do módulo 00, é um homem de 90 anos, do Sudeste,
que adoeceu na semana 34 de 2024, com uma dose de vacina antes do sintoma
e cardiopatia declarada. Ele é o *paciente-regra*, e as cinco perguntas
deste relatório são feitas sobre ele.

Estar em cima da fronteira não é acaso conveniente: é a condição que torna
as cinco respostas comparáveis. É ali que a reta local do LIME não degenera
numa constante e que as forças do SHAP se cancelam de forma legível. Um
paciente confortavelmente de um lado só esconderia o que cada método faz
quando é obrigado a decidir.

Dois outros aparecem, cada um com uma razão declarada. Os módulos 01 e 03
usam um segundo, escolhido pela mesma regra mas restrito a quem está exposto
às três cercas, chamado aqui de *vulnerável*: ele existe para mostrar que a
quantidade de ficção que um método fabrica depende de *quem* está sendo
explicado. O módulo 04 precisa de um terceiro, com predição bem mais alta,
porque contrafactual pede alguém com o que perder.

Nas figuras de ponto deste relatório, *a forma diz de onde o ponto veio;
a cor diz o que ele é*. Círculo é paciente real, colorido pelo desfecho
*observado*: azul sobreviveu, terracota morreu. Quadrado é vizinho
*sintético*, colorido pela *predição do modelo*. O X escuro é o paciente
sendo explicado. No tracejado, escuro e longo é a fronteira do modelo,
cinza e médio a vizinhança que um método construiu, claro e curto só
andaime de eixo.

A cor carrega mais um eixo em duas das figuras, e vale dizer qual antes
que elas apareçam. Em barras que varrem uma grade de valores, azul é o
ponto que podia existir e cinza o que a cerca barra: ali a cor é
*possibilidade*, não desfecho. O cinza é de propósito, porque um ponto
barrado não é um desfecho ruim, é um não-ponto — e é o cinza, não o azul,
que carrega o sentido, já que o par de desfecho deste relatório é
azul contra terracota. E quando dois modelos
dividem o mesmo painel, a cor separa os instrumentos, azul para o comitê
de árvores e âmbar para a logística. Três eixos, portanto, e cada figura
diz na legenda com qual deles está pintando.

A ficha do SIVEP não é um formulário plano: ela *desliga campos*. Onde o
campo de fator de risco está em branco, as treze comorbidades abaixo dele
estão em branco junto. O vazio que sobra ali não é dado faltante. É
informação: diz que a pergunta não foi feita.

Por isso o tratamento separa três leituras do vazio: *não se aplica* (o
portão desligou o campo), *ausente* (o campo estava aberto e ficou em
branco) e *ignorado* (alguém registrou que não sabe). Fundir as três
transforma resposta em buraco: o dado faltante cresce sem que nada tenha
se perdido, e quem imputa por cima inventa comorbidade num paciente a
quem a pergunta nunca foi feita.#footnote[Módulo 00: fundir os três estados infla o dado faltante por 1,8× a 5,7× conforme o ano.]

#figure(
  scope: "parent",
  placement: auto,
  fig-funil(),
  caption: [
    A variável-funil: o campo de fator de risco governa se as
    comorbidades abaixo dele chegam a ser perguntadas. A figura diz quais
    respostas são possíveis, não quantos pacientes caem em cada
    ramo.
  ],
)

Como as features são *conjuntamente restritas*, todo método que perturba
uma feature de cada vez fabrica pacientes que não podem existir. As
quatro regras da seção anterior viram três cercas nos módulos, porque o
critério-2 e o critério-3 são a mesma cerca lida em dois grupos de
sintomas: a definição da coorte.

#sp-tab(columns: (auto, 1fr),
  cabecalho: ([*cerca*], [*o que ela proíbe*]),
  [portão do funil], [marcar comorbidade onde o campo de fator de risco ficou em branco],
  [calendário da campanha], [dar uma dose a quem adoeceu antes de a campanha começar],
  [definição da coorte], [apagar o único sintoma que fez o paciente entrar na coorte],
  fonte: [módulo 00, `MODEL.md`; a mesma função nos módulos 01 a 05])

E a cerca não é vista pela geometria. A distância de Gower compara duas
fichas célula a célula, pondo números e categorias na mesma escala; por
ela o ponto impossível fica mais perto de um paciente real do que o
paciente real mediano fica do vizinho dele. Trocar um nível de categoria
custa o mesmo, seja a troca possível ou impossível: nenhum limiar sobre
essa distância pega a contradição.

= 4. Ceteris paribus: e se a idade fosse outra?

Congela-se o paciente, escolhe-se uma variável e uma *grade* (a lista de
valores que ela vai assumir) e plota-se a predição em cada valor. Sem
modelo intermediário, sem sorteio, sem aproximação: a curva *é* a saída do
modelo @molnar2025, e é por não aproximar nada que o método mais simples
do curso expõe o problema que todos os seguintes herdam.

Um modelo de árvores não lê a idade como um valor que escorre: ele
pergunta se a idade passou de um corte, depois se passou do seguinte.
Entre dois cortes ele não muda de opinião, então a predição fica parada e
pula de uma vez. A curva vira uma *escadaria*.

E a escadaria se lê errado com facilidade. Numa grade grossa, a altura
de um degrau é propriedade da grade: cada salto visível soma vários
saltos verdadeiros, e pedir a predição em idades mais próximas parte o
degrau grande em degraus menores. Mas o refino tem fim. A partir de
certo passo os degraus param de encolher, e a altura que sobra é do
modelo.#footnote[Módulo 01: em quatro refinos da grade de idade a amplitude
fica em 0,4809 e o maior salto cai de 0,1387 para 0,0852, e aí não cede
mais.] A amplitude, do ponto mais alto ao mais baixo, não se move em
refino nenhum. Leia posições de corte primeiro, e só leia altura de
degrau depois que refinar a grade tiver parado de mudá-la.

#figure(
  scope: "parent",
  placement: auto,
  image("/reports/01-metodos-locais/figuras/cp_passo_1b_modelos.png", width: 100%),
  caption: [
    O mesmo paciente em dois modelos, na idade e nas doses: a escadaria
    do modelo do curso contra a rampa da logística, com a cor separando
    os instrumentos e não os desfechos. Atenção à direção do painel
    direito: as duas curvas sobem com as doses, e nenhuma das duas mede
    efeito de vacina. Na campanha brasileira as doses foram primeiro para
    os idosos, os imunocomprometidos e os portadores de comorbidade, e as
    adicionais só para eles, de modo que a contagem de doses é, nesta
    ficha, um marcador de fragilidade. O perfil prevê, não intervém.
  ],
)

A logística não tem interações, e o efeito disso é a forma: ela desenha
a mesma curva em S para *todo* paciente. O resto da ficha entra somando,
e uma soma feita antes de a conta virar probabilidade desliza a curva ao
longo do eixo em vez de levantá-la. Dois pacientes diferem em *onde* ela
sobe, não em como sobe, e no trecho que o gráfico mostra isso muda a
altura e a inclinação ao mesmo tempo. O modelo do curso desenha uma
curva com forma própria por paciente, e é daí que sai o ganho que nenhum
coeficiente global exibe. Nas doses os dois discordam de ponta a
ponta#footnote[Módulo 01, walkthrough §1b: a fig. 12.5 do livro, refeita. Nas doses a logística sobe 0,217 e o modelo do curso termina 0,044 abaixo.],
e aí mora uma armadilha: dizer que o modelo do curso "desce nas doses" é ler a ponta do
gráfico, não o paciente, porque perto do próprio paciente a inclinação é
*positiva*.

*A resposta, e o preço.* Para a pergunta do título o método responde
direto, lendo a curva de idade no valor que interessa. E responde barato:
sem sorteio no caminho, repetir a conta devolve a mesma curva. O preço é
que a resposta vale para uma linha fabricada, e quanto dela é ficção
depende de quem se explica: para o paciente-regra nenhuma das oito
variáveis de maior peso fabrica um impossível; para o vulnerável, que
está em cima das três cercas ao mesmo tempo, as três varreduras que o
caderno tenta caem fora ponto a ponto. A concentração da ficção é
propriedade da coorte, não do método.


= 5. ICE: os outros respondem igual?

O ICE desenha um perfil ceteris paribus por paciente, todos no mesmo
eixo @goldstein2015. Esse conjunto de curvas é o *feixe*, e o que ele
acrescenta é heterogeneidade: o modelo trata todos do mesmo jeito? A
leitura do capítulo é de olho nu: se as curvas seguem o mesmo curso, não
há interação *óbvia* naquela variável, e a média delas, o *PDP*, resume
bem. A inversa não vale, e Goldstein et al. propõem por isso um teste
formal: um feixe que parece paralelo num sorteio de duzentas curvas não
prova ausência de interação. Aqui isso não pesa, porque a leitura de olho
nu *falha*, e é a falha que serve de evidência.

Uma curva por paciente significa que, com a base inteira, o gráfico vira
uma mancha preta: é o amontoamento (*overcrowding*) de que o capítulo
avisa. Por isso se sorteia um subconjunto, e a regra do sorteio se
declara.#footnote[Módulo 02: o feixe sorteia 200 pacientes, 40 por ano,
com semente 42.]
A *semente* é o número que fixa o sorteio: quem rodar o caderno de novo
obtém as mesmas curvas, e é isso que torna a figura reproduzível.
*Estratificar por ano* é tirar a mesma quantidade de pacientes de cada
ano; sem estrato, 2020--2022 dominaria a amostra e o regime sumiria no
desbalanceio.

#figure(
  scope: "parent",
  placement: auto,
  image("/reports/01-metodos-locais/figuras/ice_passo_1_feixe.png", width: 100%),
  caption: [
    Olhe a rampa de intensidade: quanto mais escura a curva, mais letal o
    regime em que o paciente adoeceu, e as de 2020 correm por cima das de
    2024, então o teste do capítulo falha de propósito. A figura não mostra
    efeito da idade: cada ponto é a predição numa linha
    fabricada.
  ],
)

Está aí a lição do PDP: a média fica entre duas populações e não descreve
nenhuma.#footnote[Módulo 02, walkthrough §1: aos 80 anos o feixe vale 0,481 em 2020 e 0,303 em 2024, e a média do feixe, que é o PDP desta amostra estratificada e não o da coorte, reporta 0,400.]
*Centrar* as curvas confirma: subtraído de cada uma o valor que
ela tem no início da grade, todas partem do zero e sobra só a forma,
quase paralela, com os pacientes subindo do mesmo jeito de níveis muito
diferentes. O PDP acerta a forma e erra o nível de todos ao mesmo tempo,
o modo de mentir mais educado que existe.

A *derivada* é a inclinação da curva, e numa escadaria ela não existe em
cada ponto: o que o caderno desenha é a diferença entre dois pontos
vizinhos da grade, que aqui distam dois anos, dividida por esse
intervalo. Lida assim, ela diz quanto a predição muda por um ano a mais,
na grade usada. Ela acha o efeito onde ninguém procurava, num pico
pediátrico. E aqui é biologia, ao contrário do resto desta seção: a
mortalidade pediátrica por COVID desenha um U, com o meio da infância
protegido e o risco voltando a subir na adolescência. No treino a
letalidade observada vai de 3,49% entre 4 e 8 anos a 13,89% entre 16 e
20.#footnote[Módulo 02, walkthrough §4: a letalidade observada por faixa
etária no treino, ao lado do pico da derivada. Não é herança de coorte
antiga: esta coorte é só COVID e começa em fevereiro de 2020.] A ressalva
é o denominador: são algumas centenas de pacientes por faixa contra
dezenas de milhares no miolo adulto, a região mais rala da base.

*A resposta, e o preço.* Não, os outros não respondem igual, e a
diferença é o ano em que adoeceram. O preço é que a ficção se multiplica
por duzentas curvas e continua contável: o feixe de idade não tem um
ponto impossível, o de doses fabrica 18% e o de tosse,
54%.#footnote[Módulo 02: 252 dos 1.400 pontos do feixe de doses caem
antes de a campanha começar, uma fração derivável antes mesmo de medida.]
A variável varrida decide se o feixe é retrato ou fábula.

= 6. LIME: por que esta predição, localmente?

O LIME @ribeiro2016 não abre o modelo. Ele fabrica vizinhos artificiais
em volta do paciente, pergunta ao modelo o que ele prevê em cada um, dá
mais peso aos mais parecidos e ajusta uma reta simples nesse conjunto.
Essa reta é o *substituto*: imita o modelo complicado só ali perto, e
seus coeficientes são a explicação. O *kernel* decide o peso de cada
vizinho conforme a distância, e a largura dele define o tamanho de "ali
perto".

O substituto nunca passa por cima do modelo. A predição continua vindo do
XGBoost; a reta só a resume.

#figure(
  scope: "parent",
  placement: auto,
  image("/reports/01-metodos-locais/figuras/lime_passo_a_passo.png", width: 100%),
  caption: [
    Os seis passos do método sobre um corte ceteris paribus do modelo do
    curso: fronteira, vizinhança, perturbação, predições, pesos e reta. Só
    o painel D consulta o modelo. A figura não mostra uma vizinhança de
    pacientes: cada coluna da nuvem é sorteada sozinha.
  ],
)

Três surpresas estão na figura. A nuvem não está centrada no paciente: o
gerador, com as contínuas não discretizadas e o sorteio no seu padrão, a
centra na média do treino, e o paciente fica a vários desvios do centro
da própria "vizinhança". O kernel descarta quase tudo,
e sobram poucos vizinhos com peso apreciável. E é nesse deserto que a
reta é ajustada.

A vizinhança tem dois defeitos, e só um tem conserto fácil. Declarar
quais colunas são discretas conserta a *gramática*: a nuvem para de
produzir códigos que não existem na ficha e doses negativas, e nada
avisava, porque a função que entrega os vizinhos ao modelo arredonda em
silêncio. Não conserta a *biologia*: cada coluna continua sorteada
sozinha, a correlação entre calendário e doses some, e os vizinhos
impossíveis continuam lá, quase um terço dos do paciente-regra e quatro
em cada cinco dos do vulnerável.#footnote[Módulo 03, walkthrough §4: a
contagem de impossíveis reprova 30,6% dos vizinhos sorteados em torno do
paciente-regra e 79,2% dos do vulnerável.]

*A resposta, e o preço.* O LIME dá um ranking com sinal, e o topo dele é
firme entre sementes: no módulo 03, dez delas dão o mesmo top-5, sem
troca de sinal no top-8. O preço é o R²: ele mede o quanto a reta
reproduz a nuvem ponderada, que é a *fidelidade local* no sentido de
Ribeiro, e não a fidelidade *ao paciente*, o quanto a explicação acerta
neste caso. Por ser normalizado pela variância da nuvem, o R² pode ir a
zero justamente onde o erro no paciente é zero: com kernel estreito o
substituto degenera na constante certa e entrega R² zero com erro zero, a
explicação vazia perfeita; na largura padrão da biblioteca, R² e erro
sobem juntos.#footnote[Módulo 03, walkthrough §5: o kernel estreito mede R²
0,00 com erro 0,00, e o da largura padrão, R² 0,68 com erro 0,028.]
Nenhuma largura compra as duas, e o capítulo é franco: definir a
vizinhança certa é problema em aberto @molnar2025. A regra que sobra é
dura: não ranqueie explicações por R². A amostragem fora da variedade
abre ainda um ataque @slack2020: os vizinhos sorteados não se parecem
com pacientes reais, então dá para treinar um detector que os reconheça.
Um modelo montado com esse detector responde aos vizinhos com uma cara
inocente e segue enviesado nos pacientes de verdade, e o LIME explica a
cara, não o modelo.


= 7. Contrafactuais: o que teria de mudar?

Os três métodos anteriores perguntam "o que pesou?". O contrafactual
inverte: qual é a menor mudança que muda a saída? Com isso, as cercas
deixam de ser diagnóstico de método doente e viram *restrição de busca*.

A ideia vem de #cite(<wachter2018>, form: "prose"): a menor mudança na
ficha que leva o modelo à saída desejada, sem abrir a caixa. A perda que
eles escrevem pesa duas coisas, chegar à saída e ficar perto do
original. Como a saída é um paciente hipotético, o campo foi somando
exigências depois, e o capítulo de Molnar as reúne @molnar2025:
*validade*, a mudança cruza mesmo o limiar; *proximidade*, o hipotético
fica perto do real; *esparsidade*, mudam poucas coisas;
*plausibilidade*, ele poderia existir; *diversidade*, há mais de um
caminho.

O módulo não usa biblioteca, e a razão é uma boa lição de engenharia: o
espaço de mudanças declarado cabe inteiro na memória, então o caderno
enumera todas em vez de otimizar a perda de Wachter. Isso compra
cobertura completa, determinismo sem semente e custo de milissegundos. O
paciente aqui não é o paciente-regra: o módulo 04 pede alguém com o que
perder, e caiu num paciente de 32 anos, com quatro doses, síndrome de
Down, doença neurológica, imunodepressão, doença renal e outras
morbidades. Foram Down e imunodepressão que o puseram entre os grupos
prioritários da campanha, e daí as quatro doses.

#figure(
  scope: "parent",
  placement: auto,
  align(center, image("/reports/01-metodos-locais/figuras/cf_passo_3_painel.png", width: 85%)),
  caption: [
    Cada barra é uma banda de risco, e a altura é a fração de pacientes
    dessa banda para quem algum movimento ao alcance de uma pessoa cruza
    o limiar: olhe o gradiente, que desce conforme o risco sobe. Barra
    nenhuma não é paciente condenado, nem a figura mede eficácia: é o
    método sem o que prescrever.
  ],
)

O gradiente é a leitura difícil da figura: a fração com saída cai banda a
banda conforme o risco sobe, e some na última, onde há dezenove pacientes
só, poucos demais para separar "nenhuma saída" de
"poucas".#footnote[Módulo 04, walkthrough §5: dos 624 pacientes de alto risco, 30,3% têm contrafactual acionável, e a fração cai conforme o risco sobe.]
A direção é clara; a ponta é frágil. E a busca livre explica por quê: a
melhor mudança única que ela encontra é a saturação baixa passar a "não",
isto é, supor um paciente que nunca ficou hipoxêmico, e isso é
*consequência* da doença, não alavanca; atrás dela vêm voltar a ter 10
anos e recuar o calendário para os primeiros meses da pandemia.

Três histórias sem um ingrediente em comum levam o paciente para o lado
certo do limiar, e param em predições bem diferentes: o efeito Rashomon
impresso, explicações diferentes e igualmente válidas para o mesmo caso.
Qual delas se contaria ao paciente?

*A resposta, e o preço.* A resposta honesta é *não neste modelo*: os dois
candidatos ao alcance deste paciente não movem a predição, e não poderiam
mover muito, porque a única família que o estudo declara acionável é a
contagem de doses, uma exposição do passado, indisponível a quem já está
internado. O espaço de variáveis não contém um único tratamento: a
ventilação e a UTI saíram como vazamento, e os campos de antiviral da
ficha nunca entraram. Um modelo sem alavanca não tem contrafactual
acionável por construção, e é isso que a figura mede, não o prognóstico
deste paciente, para quem oxigênio, antiviral precoce e leito continuam
existindo fora do modelo. Um método que só sabe prescrever precisa saber
dizer de onde vem o seu silêncio.

O preço tem duas partes. Válido não é alcançável: os melhores candidatos
passam na cerca, mas pedem uma máquina do tempo, e é bom lembrar que a
máquina do tempo levaria a um lugar pior: em 2020, sem vacina e com
hospitais saturados, um jovem imunodeprimido morria mais, não menos. E a
plausibilidade se decide sobre o candidato inteiro, não sobre o
movimento: recuar o calendário sozinho cai na cerca da campanha, recuá-lo
com zero doses não cai.

= 8. SHAP: quanto cada feature pesou?

O SHAP @lundberg2017 responde repartindo, e a regra de partilha vem de um
teorema que Lloyd Shapley provou em 1953, sobre como repartir o ganho de
um jogo cooperativo. A predição deste paciente é o resultado
da partida; o ganho é a diferença entre ela e a predição média, a de quem
nada sabe sobre ele; os jogadores são os valores das variáveis. O valor
de Shapley reparte esse ganho entre eles de forma que a soma feche. Em
árvores, o TreeSHAP @lundberg2020 faz a conta em tempo polinomial e sem
sorteio, e o modelo do curso já a traz pronta (`pred_contribs`), que é a
variante *path-dependent*: exata para a função-valor que ela adota, a que
preenche as ausências seguindo as frequências dos próprios caminhos da
árvore. Todos os φ desta seção vêm dela.
Aqui cai a única exceção do relatório. O valor de Shapley é agnóstico de
modelo, e existe uma versão dele que trata qualquer modelo como caixa
fechada, o KernelSHAP @lundberg2017. O TreeSHAP não é: ele percorre as
árvores. Troca-se a generalidade pela conta exata e barata, e a troca
fica dita em vez de escondida.

Antes da figura, a escala. As contribuições vivem na *margem*: o número
que o modelo soma por dentro e que só depois vira probabilidade. É aí que
somar as contribuições das 800 árvores do módulo 00 faz sentido, porque o
modelo é aditivo *na margem*, e só nela. A ligação que transforma margem
em probabilidade é uma curva, e a curva de uma soma não é a soma das
curvas: somar probabilidades não fecharia em ponto nenhum do eixo, não só
nas pontas.

#figure(
  scope: "parent",
  placement: auto,
  image("/reports/01-metodos-locais/figuras/shap_passo_1_waterfall.png", width: 100%),
  caption: [
    Um cabo de guerra que empata: a idade empurra para cima, a vacinação
    declarada e o calendário freiam, e o que se olha é a soma, que cai
    exatamente sobre a margem deste paciente. A figura não é um
    contrafactual: reparte o que já aconteceu.
  ],
)

Que a soma feche é o que separa o SHAP dos outros quatro métodos: aqui
não há ajuste que possa sair bom ou ruim, como o R² do LIME. As parcelas
fecham porque um axioma manda, a eficiência, e a garantia vira
verificação, conferida linha a linha no teste inteiro.#footnote[Módulo 05,
internals §1: as 40 contribuições mais a base reproduzem a margem com
desvio máximo 1,05×10⁻⁵ nas 16.142 linhas do teste.]

O que a figura *não* significa é causa. Um φ positivo não diz que
aumentar aquela variável aumentaria a predição, e também não é o que
sobra quando se apaga a variável do modelo. Ele é uma média: monte o
paciente variável por variável, em todas as ordens possíveis, e anote
quanto a predição se move no instante em que *esta* entra. O φ é a média
dessas anotações, contada a partir da predição de quem nada sabe sobre o
paciente. Não é o efeito daquele valor com o resto da ficha parado. E o
modelo dá o caso que quebra: o φ das doses de vacina é *positivo* nos
vacinados. Isso não é efeito de vacina, e o desfecho observado fecha a
questão antes de qualquer explicação: no pós-campanha, dentro de cada
faixa etária, a letalidade cai conforme as doses sobem, e entre os
maiores de 85 anos ela vai de 53,6% com zero doses a 24,3% com
cinco.#footnote[Módulo 05, walkthrough §5: a letalidade observada por
faixa etária e contagem de doses, ao lado do φ que em aparência a
contradiz.] O φ positivo e essa queda convivem, e são três razões
somadas. A
primeira é a repartição entre duas colunas quase colineares: o crédito
protetor vai para a que declara a vacinação, e sobra para a contagem de
doses o papel de marcar *quem* se vacinou. A segunda é justamente quem: a
campanha priorizou idosos, imunocomprometidos e portadores de
comorbidade, e as doses adicionais foram só deles, de modo que a contagem
de doses é, nesta ficha, um marcador de fragilidade que os treze
checkboxes não medem. A terceira é o que falta: o modelo não vê o tempo
desde a última dose, então uma dose tomada há três anos e uma tomada no
mês passado são o mesmo valor. Nada disso mede o que a vacina fez; mede o
que a triagem fez. O antídoto está no
módulo anterior: subir as doses deste paciente quase não move a predição.

#figure(
  scope: "parent",
  placement: auto,
  image("/reports/01-metodos-locais/figuras/shap_passo_5_dependencia.png", width: 100%),
  caption: [
    O painel-armadilha é o da direita: quem não declarou dose recebe
    crédito negativo; as doses declaradas recebem crédito positivo.
    Ele não compara vacinado com não vacinado, nem mede efeito de vacina:
    mostra como o modelo divide crédito entre variáveis que andam juntas.
  ],
)

Duas medições fecham o arco. A primeira liga o SHAP à deriva de regime: a
variável de calendário está entre as primeiras para mover as predições de
2024 e cai para o meio da tabela pelo ganho das divisões (`gain`), a
medida de quanto ela ajudou a construir as árvores. Pela atribuição ela é
terceira; pelo ganho é a
19ª de 40.#footnote[Módulo 05, walkthrough §4: 19ª de 40 pelo ganho do treino, contra a terceira colocação por média |φ| no teste de 2024.]
Importância para prever não é importância para treinar.

A segunda é o preço do condicionamento. Apagar uma variável para medir o
que ela vale tem duas versões: seguir os caminhos que as árvores
percorrem de fato, respeitando as correlações aprendidas, ou apagá-la
mesmo, montando pacientes que são metade este e metade outro. As direções
batem; as magnitudes divergem onde as correlações moram.
O caminho das árvores também cobra o seu: ao respeitar as correlações,
ele pode dar crédito a uma variável que o modelo nem usa, só porque ela
anda junto de uma que usa @molnar2025.

*A resposta, e o preço.* O SHAP responde a última das cinco perguntas com
números que somam, e é a única resposta auditável do relatório. O preço
da variante que usamos é o parágrafo acima: crédito que escorre para
variáveis correlacionadas. O da alternativa intervencional é outro, e foi
contado, pela mesma função que conta o impossível nos outros módulos: os
híbridos que a função-valor dela pressupõe são quase um quarto
impossíveis.#footnote[Módulo 05, walkthrough §7: 23,1% das 2.460
linhas híbridas montadas pela variante intervencional são impossíveis.] A
limitação que o livro-texto enuncia fica contada, em vez de citada.


= 9. As cercas, lado a lado, e a deriva

Os cinco módulos contaram a mesma coisa com cinco instrumentos, e sempre
pela mesma função, escrita uma vez no módulo 00 e importada pelos cinco
cadernos. A tabela compara métodos, não implementações.

#sp-tab(columns: (auto, 1fr, auto, auto),
  cabecalho: ([*método*], [*o que foi contado*], [*sobre quantos*], [*fração*]),
  [módulo 01], [pacientes da amostra para quem marcar comorbidade cairia no portão], [240.290], [37,3%], [módulo 01], [pacientes da amostra que marcaram só um dos dois sintomas do primeiro grupo], [240.290], [79,6%], [módulo 02], [pontos do feixe de doses, onde a cerca é da variável], [1.400], [18%],
  [módulo 03], [vizinhos sorteados em torno do paciente-regra], [5.000], [30,6%], [módulo 03], [os mesmos vizinhos, em torno do vulnerável], [5.000], [79,2%], [módulo 04], [candidatos a contrafactual, uma célula por vez], [113], [3,5%], [módulo 05], [linhas híbridas montadas pela variante intervencional], [2.460], [23,1%],
  fonte: [walkthrough §2 (01), §3 (02), §4 (03), §2 (04) e §7 (05)])

A tabela junta, de propósito, duas contas diferentes. As duas primeiras
linhas medem *exposição da coorte*: quantos pacientes reais já estão em
cima de uma cerca, antes de qualquer método rodar. As outras cinco medem
*ficção do método*: quantos dos pontos que o método fabricou não podem
existir. A primeira conta é do mundo; a segunda é do instrumento. E a
coluna do meio existe para impedir a leitura fácil: os denominadores vão
de uma centena de candidatos a um quarto de milhão de linhas, então as
frações não se comparam entre si. A
tabela não é um ranking de qualidade. A taxa de ficção é propriedade
conjunta de três coisas: o método, a variável perturbada e *quem* está
sendo explicado. O contrafactual fabrica pouco porque parte de um
paciente real e move uma célula por vez. O LIME fabrica muito porque
sorteia todas as colunas de uma vez, e fabrica mais que o dobro no
vulnerável, pelo mesmo gerador, já que a nuvem nem olha para o paciente.

#figure(
  scope: "parent",
  placement: auto,
  image("/reports/01-metodos-locais/figuras/cp_passo_4_restrito.png", width: 100%),
  caption: [
    O que olhar é a cor das barras, e aqui ela é o eixo da
    *possibilidade*, não o do desfecho: azul é a dose que podia ter
    existido, cinza a que a cerca barra. A mesma varredura, na mesma
    grade restrita, sobrevive inteira no paciente pós-campanha e é barrada
    quase toda no pré-campanha, onde só a dose zero podia ter existido. A
    figura não mostra efeito de vacina; mostra em quais pontos a pergunta
    podia ser feita. É assim que o remédio do capítulo funciona, dizendo
    *quando não perguntar*.
  ],
)

== A deriva, vista por cinco instrumentos

Não são cinco achados, é um só, visto de cinco ângulos. Ele nasce na
base, e em duas contas que não devem ser somadas. No módulo 00, na SRAG
inteira, com todas as etiologias e todas as idades, a letalidade bruta
anual cai de 29,0% em 2020 para 8,6% em 2024, mas a maior parte dessa
queda é troca de população: no mesmo módulo 00, a fração COVID vai de
59,8% a 11,6%, com a SRAG voltando a ser majoritariamente pediátrica.
Dentro da coorte deste relatório, onde essa troca já foi filtrada, a
queda que resta é a do treino para o teste, de 31,4% para 18,2%. É essa
segunda, e só ela, que o modelo herda como desvio de
nível.#footnote[Módulo 00, `MODEL.md`: no teste, o modelo prevê 0,2154
onde se observa 0,1824. A série anual da base inteira está no README do
módulo 00, na tabela dos regimes.] O ICE dá rosto ao erro, com duas alturas para a
mesma idade quando o feixe é estratificado por ano. O SHAP dá um posto: o
calendário é das primeiras variáveis por atribuição e fica no meio da
tabela pelo ganho na construção das árvores. E o contrafactual mostra o
avesso: os melhores candidatos válidos pedem que o paciente volte ao
começo da pandemia, que é um lugar onde ele morreria mais, não menos. É a
deriva aparecendo pelo lado errado, e um bom lembrete de que válido para
o modelo e verdadeiro sobre o mundo são coisas diferentes.

Uma explicação que revela "ano" está, portanto, *correta*. O modelo
aprendeu o regime, e escondê-lo seria pior do que mostrá-lo.

= 10. Limitações, discussão e o que aprendemos

== O que os métodos não dizem

Nenhum dos cinco entrega causalidade. Todos leem um modelo treinado em
fichas de vigilância, e uma ficha registra *documentação* tanto quanto
biologia. O resultado de imagem mostra as duas coisas ao mesmo tempo. Há
sinal clínico verdadeiro: entre os laudos informativos, a letalidade cai
do típico de COVID para o negativo para pneumonia. E há vazamento, mas
ele mora nos níveis não informativos, o ignorado e o campo em branco, que
são os mais letais da tabela inteira, enquanto o não realizado não se
distingue do típico. Quem morre nas primeiras horas não chega a ter laudo
digitado: é gravidade entrando pelo campo vazio, não qualidade de
prontuário. Somar as duas colunas às variáveis renderia 0,0038 de AUC, e
o preço seria um modelo que credita à existência do laudo o que pertence
ao curso da doença.#footnote[Módulo 00, walkthrough do modelo §5: a
célula-armadilha, com a letalidade por nível de laudo ao lado do ganho de
AUC que a imagem traria.]

A mesma lógica explica a exclusão mais discutida do Ouro. Admissão em UTI
e suporte ventilatório são os dois campos clinicamente mais fortes da
ficha, e somá-los subiria bastante a AUC.#footnote[Módulo 00, `GOLD.md`,
decisão 3: com os dois campos, a AUC de teste vai de 0,7644 para 0,8514.]
Ficam fora mesmo assim, e o critério não é o tamanho do ganho: é o
*instante da predição*. Os dois campos resumem o episódio inteiro, e o
suporte ventilatório não tem data nenhuma, enquanto a data de entrada na
UTI existe só numa minoria dos registros. Não dá para saber se a
ventilação veio antes ou depois do instante em que o modelo seria usado,
e é essa impossibilidade que os desqualifica: usá-los é prever a
admissão com informação que ainda não existia. Isso infla o desempenho
aparente sem tornar o modelo utilizável @wolff2019 @moons2019.

Há ainda o confundimento por capacidade instalada: quem foi ventilado
depende de haver leito, e a oferta de leitos era desigual entre as
regiões brasileiras. Mover a ventilação num perfil ceteris paribus não
mostraria efeito de tratamento, mostraria triagem. Aquele número maior
não é um modelo melhor da mesma pergunta; é um modelo de outra pergunta.

A lição principal inverte a direção habitual: em vez de usar o método
para entender os dados, foram os dados que qualificaram o método. Numa
base cuja estrutura de formulário é conhecida, a advertência de Molnar,
de que perturbar variáveis de forma independente cria combinações
irreais, vira contagem.

A segunda lição veio de um acidente. Quando o estudo de seleção trocou os
hiperparâmetros do modelo do curso, os cinco módulos foram
re-sincronizados afirmação por afirmação, e deu para ver *que tipo* de
frase sobrevive. Caíram quase só leituras de ponta e narrativas bonitas;
sobreviveram as contagens de cerca, que não se moveram, porque medem a
base e não o modelo. Vale escrever cada frase sabendo de qual das duas se
trata. E há uma terceira classe, mais escorregadia que as outras: a frase
que descreve uma escolha nossa e se disfarça de fato sobre a ficha ou
sobre a doença. Quase toda cerca deste relatório é assim, e por isso cada
uma diz de onde vem.

O que torna este relatório verificável não é o texto, é a regra: todo
número em prosa é impresso por uma célula versionada, a frase que o
carrega nomeia o módulo, e um script reprova o arquivo quando isso é
quebrado. É barato de manter e caro de fingir. O limite da regra também
vale dito: ela vigia dígitos, e as afirmações mais arriscadas de um texto
como este costumam não ter dígito nenhum.

O próximo capítulo trata do problema vizinho. O ALE não faz média sobre a
distribuição marginal: ele acumula *diferenças* de predição dentro de
janelas que a base de fato ocupa, e é isso que corrige a extrapolação
para fora do envelope dos dados, de que o PDP sofre. Não corrige a cerca,
porque a diferença continua sendo tomada com o resto da ficha parado.
Para restrição lógica o remédio segue sendo o do módulo 01: dizer quando
não perguntar. E a pergunta que abre o curso e o fecha continua a mesma:
*quem são as linhas que você acabou de dar de comer ao modelo?*

= Disponibilidade de código e dados

Os cadernos, as figuras e os documentos de decisão citados nas notas de
rodapé deste relatório são públicos, em
#link("https://github.com/wbendinelli/interpretable-ml-lectures")[`github.com/wbendinelli/interpretable-ml-lectures`].
O módulo 00 traz a base, o modelo e o protocolo de seleção; os módulos 01
a 05 trazem um método por diretório, cada um com um caderno de passo a
passo e um de internals, e com as saídas versionadas junto do código que
as imprimiu. Um ponteiro como "módulo 03, walkthrough §4" se lê ali:
`modules/03-lime/notebooks/lime_walkthrough.ipynb`, seção §4. Os
microdados do SIVEP-Gripe são publicados pelo Ministério da Saúde no
OpenDataSUS; o extrato congelado que serve a todo o curso é o de junho de
2025, e o repositório registra a data porque a ficha muda entre versões.

#bibliography("references.bib", title: [Referências], style: "apa")
