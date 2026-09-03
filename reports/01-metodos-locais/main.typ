#import "@preview/sapians:0.3.0": *
#import "figuras.typ": *

#show: sapians-article.with(
  title: "Um paciente, cinco perguntas",
  abstract: [
    Este relatório explica, para um único paciente, o modelo de óbito por
    COVID do curso, treinado sobre a base de vigilância SRAG/SIVEP-Gripe.
    Usa os cinco métodos locais agnósticos de modelo estudados nos módulos
    01 a 05: perfis ceteris paribus, ICE, LIME, contrafactuais e SHAP.
    Agnóstico de modelo porque explica por fora, sem abrir a caixa; local
    porque explica uma predição sobre uma pessoa, e não o modelo inteiro.
    Em vez de cinco estudos avulsos, o mesmo paciente, escolhido por uma
    regra, atravessa os cinco, e cada método é julgado por uma pergunta
    clínica que deveria responder.

    Dois achados organizam o texto. O primeiro é que a ficha do SIVEP
    desliga campos: quando ela declara que não há fator de risco, as
    comorbidades nem chegam a ser apresentadas a quem preenche. Mexer numa
    variável de cada vez produz então fichas que o formulário não
    permitiria, e nesta base essa quantidade não é estimada, é contada. O
    segundo é que o modelo aprendeu com os anos em que se morria muito mais
    e prevê num mundo em que se morre menos, e a mesma queda reaparece nos
    cinco métodos. Todo número em prosa é impresso por uma célula de caderno
    versionada, e a nota que o acompanha diz onde essa célula vive.
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
#show figure.caption: it => block(width: 100%, above: 1.8mm)[
  #set text(size: 7.6pt, fill: sapians-muted-dark)
  #set par(justify: true, leading: 0.56em)
  #align(left)[
    #text(weight: "bold", fill: sapians-text-dark)[#it.supplement #context it.counter.display(it.numbering).]
    #h(0.5mm)#it.body
  ]
]

// Hierarquia de títulos: o template fixa 10 pt para tudo, e o nível 2 vinha
// menor que o corpo. Um título nunca é menor que o texto que ele encabeça.
#show heading.where(level: 1): it => [
  #v(3.2mm)
  #text(size: 10.5pt, weight: "bold", fill: sapians-text-dark)[#it.body]
  #v(1.4mm)
]
#show heading.where(level: 2): it => [
  #v(2.4mm)
  #text(size: 9.2pt, weight: "bold", fill: sapians-terracotta)[#it.body]
  #v(0.9mm)
]

#let sp-tab(fonte: none, ..args) = block(width: 100%, above: 2.6mm, below: 3mm, breakable: false)[
  #set text(size: 7.4pt)
  #set par(leading: 0.55em)
  // Booktabs: filete grosso no topo e no pé, fino sob o cabeçalho, e nada
  // mais. Sem linha vertical e sem malha, como em IEEE, Elsevier e ACM.
  #block(stroke: (top: 0.9pt + sapians-text-dark, bottom: 0.9pt + sapians-text-dark))[
    #table(
      stroke: (x, y) => (top: if y == 1 { 0.4pt + sapians-muted-dark } else { 0pt }),
      fill: none,
      inset: (x: 2.2mm, y: 1.5mm),
      align: left,
      ..args
    )
  ]
  #if fonte != none [#v(1mm) #text(size: 6.6pt, fill: sapians-muted-dark)[Fonte: #fonte]]
]

= 1. Introdução

Um método de interpretabilidade *agnóstico de modelo* explica o modelo
por fora. Não abre a caixa: não lê coeficientes, não percorre árvores,
não olha pesos. Faz o que qualquer usuário faria: muda o que entra e
observa o que sai. Por isso serve igualmente para uma regressão
logística e para o comitê de árvores deste relatório.

*Local* é a outra metade do nome. Um método global descreve o modelo
inteiro, o que ele faz em média sobre a população toda; um método local
explica *uma* predição, sobre *um* paciente. É a diferença entre "o que
este modelo faz em geral" e "por que ele disse isto sobre esta pessoa".

O modelo aqui prevê óbito hospitalar por COVID a partir das variáveis de
admissão da ficha de Síndrome Respiratória Aguda Grave (SRAG). No teste
de 2024 ele faz AUC 0,7644.#footnote[Módulo 00: a AUC do modelo do curso
no teste de 2024, lido uma vez só e depois de a escolha estar fechada.]
Isso se lê assim: tome um paciente que morreu e outro que sobreviveu, e
o modelo ordena os dois corretamente nessa fração das vezes. Uma AUC diz
o quanto o modelo acerta; não diz em quem, nem por quê. Para um comitê
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
desliga campos. Quando ela registra que não há fator de risco, as treze
comorbidades nem chegam a ser apresentadas a quem preenche; não ficam em
branco por descuido, não são feitas. Então mexer numa variável de cada
vez, deixando as outras paradas, que é o que os cinco métodos fazem,
produz fichas que o formulário não permitiria, e nesta base dá para
*contar* quantas. Uma regra dessas é uma *cerca*; uma linha que a
atravessa é um *paciente impossível*.

O segundo: o mundo mudou no meio. O modelo aprendeu com os anos de 2020
a 2022, quando se morria muito mais, e prevê em 2024, quando a
letalidade observada já caíra quase pela metade. Isso é a *deriva de
regime*, e ela reaparece nos cinco métodos: na calibração, nas curvas do
ICE, no ranking do SHAP. Um achado só, visto por cinco instrumentos.

Vale aqui a regra de evidência do repositório: todo número em prosa é
impresso por uma célula de caderno versionada, e as notas de rodapé deste
texto dizem onde cada uma vive.

= 2. O caso: a base, o tratamento e o modelo

A fonte é o SIVEP-Gripe, o sistema com que o Ministério da Saúde vigia a
Síndrome Respiratória Aguda Grave: cada internação por SRAG no país vira
uma ficha. São 4.109.567 notificações entre 2019 e
2024.#footnote[Módulo 00: a contagem de fichas do extrato congelado que
serve a todo o curso; ele é datado porque a ficha muda entre versões.]

O tratamento tem três camadas, e a fronteira entre elas é uma pergunta.
O *Bronze* é o dado como foi baixado, byte a byte, nunca alterado: é o
que foi publicado? O *Prata* afirma fatos sobre o registro, o tipo de
cada campo, os valores que ele admite e os três jeitos diferentes de um
campo estar vazio: esse valor está determinado pelo registro sozinho? O
*Ouro* faz as escolhas da tarefa, com dono e data: o alvo, a coorte, a
janela, a divisão treino/teste e a codificação. Esse valor depende do que
se quer prever?

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
porque a população não é estacionária: em tempo normal a SRAG é doença
de criança, e sob COVID é doença de idoso. Sortear linhas ensinaria ao
modelo em que ano o paciente adoeceu. O treino vai até 2022, a validação
é 2023 e o teste é 2024.

Na fronteira dessa divisão está o achado que os cinco módulos vão
explicar: a letalidade observada cai quase pela metade do treino para o
teste. Não é um incômodo a corrigir: é o mundo tendo mudado enquanto os
dados eram coletados.

== O modelo, escolhido por protocolo

O modelo do curso não foi escolhido por gosto. Antes de qualquer leitura
do teste, um protocolo foi escrito e versionado: vence a maior AUC na
validação de 2023, e o teste é lido uma vez, depois da escolha, sem
poder desfazê-la. Seis famílias concorreram, do modelo constante ao
XGBoost, e venceu o XGBoost, com os hiperparâmetros que o próprio estudo
ajustou. A regressão logística fica ao lado como termo de comparação, e
a distância entre as duas é o problema que este curso existe para
resolver.

No teste de 2024 o modelo prevê 0,2154 de risco médio de óbito onde se
observa 0,1824.#footnote[Módulo 00: o risco médio que o modelo prevê no
teste de 2024, ao lado da letalidade que de fato se observou nesse ano.]
Essa diferença entre o que o modelo espera em média e o que de fato
aconteceu é o *erro de calibração*: a deriva de regime por dentro do
modelo, que aprendeu letalidades antigas e encontrou outro mundo. A
capacidade de ordenar pacientes sofre junto, embora menos.

== As quatro impossibilidades

Quatro regras da ficha proíbem combinações de valores, e são as quatro
cercas desta base. De cada uma se mede a mesma coisa: a fração da
amostra que está *em cima* da fronteira, aquela para quem uma única
perturbação já cai do lado impossível.

*O portão do funil.* A ficha desliga as treze comorbidades quando o
campo de fator de risco declara que não há nenhum. Marcar uma
comorbidade num paciente nesse estado contradiz um portão que, medido
nos seis anos da base, nunca foi contrariado.

*A pré-campanha.* A campanha de vacinação tem data de início. Quem
adoeceu antes dela não pode ter tomado dose nenhuma, e aumentar a
contagem de doses inventa uma vacina que ainda não existia.

*O critério-2 por um fio.* A definição de SRAG exige ao menos um sintoma
de cada um de dois grupos: tosse ou dor de garganta; falta de ar, queda
de saturação ou desconforto respiratório. Quem entrou marcando *um só*
dos dois sintomas do primeiro grupo está por um fio: desligar esse
sintoma o tira da definição de caso, e um paciente fora da definição não
estaria na base. É o estado mais comum da amostra, de longe.

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
cuja predição cai mais perto da fronteira da decisão, com o identificador
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

A legenda vale em todas as figuras deste relatório: *a forma diz de onde o
ponto veio; a cor diz o que ele é*. Círculo é paciente real, colorido pelo
desfecho *observado*: azul sobreviveu, terracota morreu. Quadrado é
vizinho *sintético*, colorido pela *predição do modelo*. O X escuro é o
paciente sendo explicado. No tracejado, escuro e longo é a fronteira do
modelo, cinza e médio a vizinhança que um método construiu, claro e curto
só andaime de eixo.

A ficha do SIVEP não é um formulário plano: ela *desliga campos*. Quando
o campo de fator de risco declara que o paciente não tem nenhum, as treze
comorbidades abaixo dele nem chegam a ser apresentadas a quem preenche. O
vazio que sobra ali não é dado faltante. É informação: diz que a pergunta
não foi feita, e diz por quê.

Por isso o tratamento separa três leituras do vazio: *não se aplica* (o
portão desligou o campo), *ausente* (o campo estava aberto e ficou em
branco) e *ignorado* (alguém registrou que não sabe). Fundir as três
transforma resposta em buraco: o dado faltante cresce sem que nada tenha
se perdido, e quem imputa por cima dá comorbidade a quem declarou não ter
nenhuma.

#figure(
  scope: "parent",
  placement: auto,
  fig-funil(),
  caption: [
    A variável-funil: o campo de fator de risco governa se as
    comorbidades abaixo dele chegam a ser perguntadas. A figura diz quais
    respostas são possíveis, não quantos pacientes caem em cada
    ramo.#footnote[Módulo 00: fundir os três estados infla o dado
    faltante por 1,8× a 5,7× conforme o ano.]
  ],
)

Como as features são *conjuntamente restritas*, todo método que perturba
uma feature de cada vez fabrica pacientes que não podem existir. Três
cercas atravessam os módulos.

#sp-tab(columns: (auto, 1fr),
  [*cerca*], [*o que ela proíbe*],
  [portão do funil], [marcar comorbidade em quem declarou não haver fator de risco],
  [calendário da campanha], [dar uma dose a quem adoeceu antes de a campanha começar],
  [definição da coorte], [apagar o único sintoma que fez o paciente entrar na coorte],
  fonte: [módulo 00, `MODEL.md`; a mesma função nos módulos 01 a 05])

#v(1mm)
E a cerca não é vista pela geometria. A distância de Gower compara duas
fichas célula a célula, pondo números e categorias na mesma escala; por
ela o ponto impossível fica mais perto de um paciente real do que o
paciente real mediano fica do vizinho dele. Trocar um nível de categoria
custa o mesmo, seja a troca possível ou impossível: nenhuma checagem por
distância pega a contradição.

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

E a escadaria se lê errado com facilidade. A altura de um degrau é
propriedade da grade que você escolheu, não do modelo: pedir a predição
em idades mais próximas parte o degrau grande em degraus menores sem que
nada mude dentro do modelo. O que não se move é a amplitude, do ponto
mais alto ao mais baixo.#footnote[Módulo 01: refinando a grade em quatro
passos, a amplitude do perfil de idade fica em 0,4809 e o maior salto
cai de 0,1387 para 0,0852.] Leia posições de corte; nunca alturas de
degrau.

#figure(
  scope: "parent",
  placement: auto,
  image("/reports/01-metodos-locais/figuras/cp_passo_1b_modelos.png", width: 100%),
  caption: [
    O mesmo paciente em dois modelos, na idade e nas doses: a escadaria
    do modelo do curso contra a rampa da logística. Nenhuma das curvas
    diz o que aconteceria se este paciente tomasse mais uma dose; o
    perfil prevê, não intervém.#footnote[Módulo 01, walkthrough §1b: a
    fig. 12.5 do livro, refeita. Nas doses a logística sobe 0,217 e o
    modelo do curso termina 0,044 abaixo.]
  ],
)

A logística desenha a mesma curva para *todo* paciente, mudando só a
altura, porque não tem interações. O modelo do curso desenha uma curva
por paciente, e é daí que sai o ganho que nenhum coeficiente global
exibe. Nas doses os dois discordam de ponta a ponta, e aí mora uma
armadilha: dizer que o modelo do curso "desce nas doses" é ler a ponta do
gráfico, não o paciente, porque perto do próprio paciente a inclinação é
*positiva*.

*A resposta, e o preço.* Para a pergunta do título o método responde
direto, lendo a curva de idade no valor que interessa. E responde barato:
sem sorteio no caminho, repetir a conta devolve a mesma curva. O preço é
que a resposta vale para uma linha fabricada, e quanto dela é ficção
depende de quem se explica: para o paciente-regra nenhuma das oito
variáveis de maior peso fabrica um impossível; para o vulnerável, a mesma
varredura é ficção do começo ao fim. A concentração da ficção é
propriedade da coorte, não do método.


= 5. ICE: os outros respondem igual?

O ICE desenha um perfil ceteris paribus por paciente, todos no mesmo
eixo @goldstein2015. Esse conjunto de curvas é o *feixe*, e o que ele
acrescenta é heterogeneidade: o modelo trata todos do mesmo jeito? O
teste do capítulo é de olho nu: se todas as curvas seguem o mesmo curso, não há
interação, e a média delas, o *PDP*, basta.

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
    fabricada.#footnote[Módulo 02, walkthrough §1: aos 80 anos o feixe vale 0,481 em 2020 e 0,303 em 2024, e o PDP reporta 0,400.]
  ],
)

Está aí a lição do PDP: a média fica entre duas populações e não descreve
nenhuma. *Centrar* as curvas confirma: subtraído de cada uma o valor que
ela tem no início da grade, todas partem do zero e sobra só a forma,
quase paralela, com os pacientes subindo do mesmo jeito de níveis muito
diferentes. O PDP acerta a forma e erra o nível de todos ao mesmo tempo,
o modo de mentir mais educado que existe.

A *derivada* é a inclinação da curva em cada ponto: quanto a predição
muda por um ano a mais. Ela acha o efeito onde ninguém procurava, num
pico pediátrico. Não é biologia: é o modelo lendo uma coorte em que a
SRAG pediátrica pré-COVID era bronquiolite.

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
gerador padrão a centra na média do treino, e o paciente fica a vários
desvios do centro da própria "vizinhança". O kernel descarta quase tudo,
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
reproduz a nuvem ponderada, não a *fidelidade local*, o quanto a
explicação acerta neste paciente. Com kernel estreito o substituto
degenera na constante certa e entrega R² zero com erro zero, a explicação
vazia perfeita; com kernel largo, R² e erro sobem
juntos.#footnote[Módulo 03, walkthrough §5: o kernel estreito mede R²
0,00 com erro 0,00, e o largo, R² 0,68 com erro 0,028.]
Nenhuma largura compra as duas, e a regra é dura: não ranqueie
explicações por R². A amostragem fora da variedade abre ainda um ataque:
um classificador que detecta as perturbações esconde do LIME o próprio
viés.


= 7. Contrafactuais: o que teria de mudar?

Os três métodos anteriores perguntam "o que pesou?". O contrafactual
inverte: qual é a menor mudança que muda a saída? Com isso, as cercas
deixam de ser diagnóstico de método doente e viram *restrição de busca*.

Como a saída é um paciente hipotético @wachter2018, os critérios de
qualidade são sobre pessoas: *validade*, a mudança cruza mesmo o limiar;
*proximidade*, o hipotético fica perto do real; *esparsidade*, mudam
poucas coisas; *plausibilidade*, ele poderia existir; *diversidade*, há
mais de um caminho.

O módulo não usa biblioteca, e a razão é uma boa lição de engenharia: o
espaço de mudanças declarado cabe inteiro na memória, então o caderno
enumera todas em vez de otimizar a perda de Wachter. Isso compra
cobertura completa, determinismo sem semente e custo de milissegundos. O
paciente aqui não é o paciente-regra: o módulo 04 pede alguém com o que
perder, e caiu num paciente de 32 anos, com quatro doses, síndrome de
Down, doença neurológica, imunodepressão e doença renal.

#figure(
  scope: "parent",
  placement: auto,
  image("/reports/01-metodos-locais/figuras/cf_passo_3_painel.png", width: 100%),
  caption: [
    Cada barra é uma banda de risco, e a altura é a fração de pacientes
    dessa banda para quem algum movimento ao alcance de uma pessoa cruza
    o limiar: olhe o gradiente, que desce conforme o risco sobe. Barra
    nenhuma não é paciente condenado, nem a figura mede eficácia: é o
    método sem o que prescrever.#footnote[Módulo 04, walkthrough §5: dos
    624 pacientes de alto risco, 30,3% têm contrafactual acionável, e a
    fração cai conforme o risco sobe.]
  ],
)

O gradiente é a leitura difícil da figura: quem mais precisaria de uma
saída é exatamente quem não tem nenhuma. E a busca livre explica: a
melhor mudança única que ela encontra é apagar do prontuário a saturação
baixa, *consequência* da doença e não alavanca; atrás dela vêm voltar a
ter 10 anos e recuar o calendário para o começo da pandemia.

Três histórias sem um ingrediente em comum levam o paciente para o lado
certo do limiar, e param em predições bem diferentes: o efeito Rashomon
impresso, explicações diferentes e igualmente válidas para o mesmo caso.
Qual delas se contaria ao paciente?

*A resposta, e o preço.* A resposta honesta é *não há*: os dois
candidatos ao alcance deste paciente não movem a predição. Um método que
só sabe prescrever precisa saber dizer isso. O preço tem duas partes.
Válido não é alcançável: os melhores candidatos passam na cerca, mas
pedem uma máquina do tempo. E a plausibilidade se decide sobre o
candidato inteiro, não sobre o movimento: recuar o calendário sozinho cai
na cerca da campanha, recuá-lo com zero doses não cai.

= 8. SHAP: quanto cada feature pesou?

O SHAP @lundberg2017 responde repartindo, e a regra de partilha vem de um
teorema sobre jogos @shapley1953. A predição deste paciente é o resultado
da partida; o ganho é a diferença entre ela e a predição média, a de quem
nada sabe sobre ele; os jogadores são os valores das variáveis. O valor
de Shapley reparte esse ganho entre eles de forma que a soma feche. Em
árvores, o TreeSHAP @lundberg2020 faz a conta de forma exata em vez de
aproximá-la, e o modelo do curso já a traz pronta (`pred_contribs`).

Antes da figura, a escala. As contribuições vivem na *margem*: o número
que o modelo soma por dentro e que só depois vira probabilidade. É aí que
somar as contribuições das 800 árvores do módulo 00 faz sentido; somar
probabilidades não faria, porque elas saturam nas pontas.

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
aumentar aquela variável aumentaria a predição: diz que, dado o resto do
paciente, aquele valor puxou a predição para cima em relação à média. E o
modelo dá o caso que quebra: o φ das doses de vacina é *positivo* nos
vacinados. Não porque vacina mate. O crédito protetor mora na variável
colinear, a que declara a vacinação, e o que sobra para a contagem de
doses é marcar os grupos priorizados na campanha. O antídoto está no
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
2024 e entre as últimas pelo ganho das divisões (`gain`), a medida de
quanto ela ajudou a construir as árvores. Importância para prever não é
importância para treinar.

A segunda é o preço do condicionamento. Apagar uma variável para medir o
que ela vale tem duas versões: seguir os caminhos que as árvores
percorrem de fato, respeitando as correlações aprendidas, ou apagá-la
mesmo, montando pacientes que são metade este e metade outro. As direções
batem; as magnitudes divergem onde as correlações moram.

*A resposta, e o preço.* O SHAP responde a última das cinco perguntas com
números que somam, e é a única resposta auditável do relatório. O preço é
a segunda versão: os pacientes que ela monta são híbridos, e quase um
quarto deles não pode existir, pela mesma função que conta o impossível
nos outros módulos.#footnote[Módulo 05, walkthrough §7: 23,1% das 2.460
linhas híbridas montadas pela variante intervencional são impossíveis.] A
limitação que o livro-texto enuncia fica contada, em vez de citada.


= 9. As cercas, lado a lado, e a deriva

Os cinco módulos contaram a mesma coisa com cinco instrumentos, e sempre
pela mesma função, escrita uma vez no módulo 00 e importada pelos cinco
cadernos. A tabela compara métodos, não implementações.

#sp-tab(columns: (auto, 1fr, auto),
  [*método*], [*o que foi contado*], [*impossível*],
  [módulo 01], [linhas da amostra barradas pelo portão do funil], [37,3%], [módulo 01], [linhas da amostra que passam no critério por um fio], [79,6%], [módulo 02], [pontos do feixe de doses, onde a cerca é da variável], [18%],
  [módulo 03], [vizinhos sorteados em torno do paciente-regra], [30,6%], [módulo 03], [os mesmos vizinhos, em torno do vulnerável], [79,2%], [módulo 04], [candidatos a contrafactual, uma célula por vez], [3,5%], [módulo 05], [linhas híbridas montadas pela variante intervencional], [23,1%],
  fonte: [walkthrough §2 (01), §3 (02), §4 (03), §2 (04) e §7 (05)])

#v(1mm)
A tabela não é um ranking de qualidade. A taxa de ficção é propriedade
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
    O que olhar é a cor das barras: a mesma varredura de doses, na mesma
    grade restrita, sobrevive inteira no paciente pós-campanha e é barrada
    quase toda no pré-campanha, onde só a dose zero podia ter existido. A
    figura não mostra efeito de vacina; mostra em quais pontos a pergunta
    podia ser feita. É assim que o remédio do capítulo funciona, dizendo
    *quando não perguntar*.
  ],
)

== A deriva, vista por cinco instrumentos

Não são cinco achados, é um só, visto de cinco ângulos. Ele nasce na
base: no módulo 00, a letalidade bruta anual cai de 29,0% em 2020 para
8,6% em 2024. O modelo herda a queda como erro de calibração, porque
aprendeu num mundo mais letal e prevê morte demais no
atual.#footnote[Módulo 00, `MODEL.md`: no teste, o modelo prevê 0,2154
onde se observa 0,1824.] O ICE dá rosto ao erro, com duas alturas para a
mesma idade quando o feixe é estratificado por ano. O SHAP dá um posto: o
calendário é das primeiras variáveis por atribuição e das últimas por
ganho na construção das árvores. E o contrafactual mostra o lado
perverso: os melhores candidatos válidos pedem que o paciente volte ao
começo da pandemia.

Uma explicação que revela "ano" está, portanto, *correta*. O modelo
aprendeu o regime, e escondê-lo seria pior do que mostrá-lo.

= 10. Limitações, discussão e o que aprendemos

== O que os métodos não dizem

Nenhum dos cinco entrega causalidade. Todos leem um modelo treinado em
fichas de vigilância, e uma ficha registra *documentação* tanto quanto
biologia. O resultado de imagem demonstra isso: usá-lo melhoraria a AUC,
e o sinal viria invertido, com quem tem exame registrado morrendo menos.
Não é pulmão, é documentação vazando no rótulo.

A mesma lógica explica a exclusão mais discutida do Ouro. Admissão em UTI
e suporte ventilatório são os dois campos clinicamente mais fortes da
ficha, e somá-los subiria bastante a AUC.#footnote[Módulo 00, `GOLD.md`,
decisão 3: com os dois campos, a AUC de teste vai de 0,7644 para 0,8514.]
Ficam fora mesmo assim, e o critério não é o tamanho do ganho: é o
*instante da predição*. A ficha só os preenche no encerramento da
internação, no mesmo ato que digita o desfecho, então usá-los é prever a
admissão com informação que ainda não existia. Isso infla o desempenho
aparente sem tornar o modelo utilizável @wolff2019.

Há ainda o confundimento por capacidade instalada: quem foi ventilado
depende de haver leito, e a oferta de leitos era desigual entre as
regiões brasileiras. Mover a ventilação num perfil ceteris paribus não
mostraria efeito de tratamento, mostraria triagem. Aquele número maior
não é um modelo melhor da mesma pergunta; é um modelo de outra pergunta.

== O que os dados ensinaram sobre os métodos

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
trata.

== O que evitar

- *Prosa editada por busca-e-substituição.* Quando o modelo muda, o
  número muda e a afirmação pode cair junto.
- *Número sem célula que o imprima.* Ou a célula existe, ou o número sai
  da prosa.
- *Ler a figura em vez da célula.* O gráfico sugere onde a curva vira; a
  célula diz onde ela vira.
- *PDP lido como "o" efeito.* A média de um feixe não descreve regime
  nenhum.
- *φ positivo lido como causa.* Ele diz o que o modelo creditou àquele
  valor, não o que aconteceria se o valor mudasse.

O que torna este relatório verificável não é o texto, é a regra: todo
número em prosa é impresso por uma célula versionada, a frase que o
carrega nomeia o módulo, e um script reprova o arquivo quando isso é
quebrado. É barato de manter e caro de fingir. O próximo capítulo é o
remédio direto: o ALE condiciona localmente, dentro da vizinhança que a
base de fato tem, em vez de atravessar o funil inteiro. E a pergunta que
abre o curso e o fecha continua a mesma: *quem são as linhas que você
acabou de dar de comer ao modelo?*

#bibliography("references.bib", title: [Referências], style: "apa")
