#import "@preview/sapians:0.3.0": *

#show: sapians-article.with(
  title: "Um paciente, cinco perguntas",
  abstract: [
    Este relatório explica um modelo de óbito por COVID treinado sobre
    a base SRAG / SIVEP-Gripe (2019--2024) com os cinco métodos locais dos
    módulos 01--05 do curso: perfis ceteris paribus, ICE, LIME,
    contrafactuais e SHAP. Em vez de cinco estudos avulsos, um único
    paciente escolhido por regra atravessa os cinco, e cada método é
    julgado por uma pergunta clínica que ele deveria responder. Dois fios
    atravessam o texto. O primeiro é o das *cercas*: a ficha do SIVEP
    desliga campos condicionalmente, então perturbar features de forma
    independente fabrica pacientes que não podem existir --- e nesta base
    essa conta é derivável, não estimada. O segundo é a *deriva de
    regime*: o modelo aprendeu letalidades de 2020--2022 e prevê num
    mundo de 2024. Todo número citado aqui é impresso por uma célula de
    caderno versionada, e a sentença que o carrega nomeia o módulo de
    origem.
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


// Corpo com respiro: o template traz 8,8 pt; um texto que precisa ensinar
// pede linha mais folgada.
#set text(size: 9.5pt)
#set par(leading: 0.72em)

#show heading.where(level: 2): it => [
  #v(1.8mm)
  #text(size: 8.4pt, weight: "bold", fill: sapians-terracotta)[#it.body]
  #v(0.5mm)
]

#let sp-tab(fonte: none, ..args) = block(width: 100%, above: 2mm, below: 2.4mm, breakable: false)[
  #set text(size: 7.2pt)
  #align(center)[#table(stroke: stroke-light, fill: (_, row) => if row == 0 { sapians-code-bg } else { none }, inset: (x: 1.8mm, y: 1.2mm), ..args)]
  #if fonte != none [#v(0.8mm) #text(size: 6.4pt, fill: sapians-muted-dark)[Fonte: #fonte]]
]

= 1. Introdução

O modelo que este relatório explica prevê óbito hospitalar por COVID a
partir de 40 variáveis de admissão da ficha de Síndrome Respiratória
Aguda Grave (SRAG). Ele foi escolhido por um protocolo pré-registrado
entre seis candidatos e faz AUC 0,7644 no teste de 2024 (módulo 00,
`SELECTION.md`). Esse número é tudo o que um relatório de desempenho
entrega --- e ele não diz *em quem* o modelo acerta, nem *por quê*. Para
um comitê que decide sobre um paciente, a diferença entre uma AUC e uma
explicação é a diferença entre uma estatística e uma resposta.

Os cinco métodos locais do curso existem para essa pergunta. Cada um a
responde de um jeito, e cada um cobra um preço diferente. Este relatório
os apresenta na ordem em que foram estudados --- ceteris paribus (módulo
01), ICE (módulo 02), LIME (módulo 03), contrafactuais (módulo 04) e SHAP
(módulo 05) --- mas com uma restrição que muda a leitura: *é sempre o
mesmo paciente*. O `gold_id` 1276776 é escolhido por uma regra e não por
conveniência, e os cinco métodos são cinco perguntas feitas sobre ele.

Dois fios atravessam as cinco seções.

O primeiro é a tese organizadora do repositório: a ficha do SIVEP
*desliga campos condicionalmente*, então as features são conjuntamente
restritas, e todo método que perturba, varre ou permuta features de forma
independente fabrica pacientes que não podem existir. O `ROADMAP.md`
chama isso de "cercas". A novidade desta base é que a cerca é
*derivável* --- o portão de comorbidade tem 0,00% de contradição nos
seis anos (módulo 00) ---, então "isto poderia inflar a conta" vira um
número exato, medido pela mesma função em todos os módulos.

O segundo é a deriva de regime. A letalidade observada cai de 31,4% no
treino (início até 2022) para 18,2% no teste de 2024 (módulo 00,
`gold/MANIFEST.md` §2.4), e o modelo carrega a lembrança do mundo antigo.
A deriva aparece na calibração, aparece nas curvas ICE, aparece no
ranking do SHAP --- é o mesmo achado, visto por cinco instrumentos.

A regra de evidência do repositório vale aqui sem desconto: *todo número
em prosa é impresso por uma célula de caderno versionada*, e a sentença
ou legenda que o carrega nomeia o módulo em que a célula vive. O script
`tools/check_numbers.py`, rodado sobre este arquivo, é o teste de
aceitação dessa regra.

= 2. O caso: a base, o Ouro e o modelo

A fonte é o SIVEP-Gripe, o sistema de vigilância de SRAG do Ministério da
Saúde. São 4.109.567 notificações e 194 colunas entre 2019 e 2024
(módulo 00), num extrato congelado do banco de 26/06/2025, e o
tratamento é um
medalhão de três camadas cuja fronteira é um teste de pertencimento
(módulo 00): o *Bronze* é o download intocado; o *Prata* afirma
fatos sobre o registro --- tipos, domínios, os três estados do vazio, 226
derivadas com proveniência, num contrato de 194 de 194 colunas com regra
e 84 checagens de qualidade (módulo 00) no arcabouço de @kahn2016; o
*Ouro* faz escolhas de tarefa.

A separação não é estética. Enquanto o alvo não é escolhido, nada no
tratamento depende do que se quer prever, e um único Prata serve a todos
os módulos do curso. É o Ouro que decide, com dono e data, cinco coisas:
o alvo (óbito nos casos fechados), a coorte (hospitalizados com COVID em
definição ampla), a janela (a partir de 26/02/2020), o split (temporal) e
a codificação (módulo 00, `GOLD.md`). A coorte sai de um funil cujas
contagens *não comutam*, e por isso é publicado na ordem em que os
filtros correm:

#sp-tab(columns: (auto, 1fr, auto),
  [*\#*], [*Filtro*], [*Restam*], [0], [Prata (sem linhas deslocadas)], [4.109.560], [1], [coorte hospitalizada], [2.428.695], [2], [caso COVID (definição ampla)], [1.364.487],
  [3], [casos fechados], [1.283.801], [4], [início a partir de 26/02/2020], [1.283.745], [5], [idade presente], [1.282.973], [6], [idade até 120 anos], [1.282.970],
  fonte: [módulo 00, `gold/MANIFEST.md` §1])

#v(1mm)
O Ouro final tem 1.282.970 internações e 40 features (módulo 00,
`gold/MANIFEST.md` §1 e §2.5). O split é temporal porque a população não
é estacionária --- treino até 2022, validação em 2023, teste em 2024 ---
e a assimetria de tamanho é consequência da epidemia, não do desenho:

#sp-tab(columns: (auto, auto, auto, auto),
  [*split*], [*n*], [*óbitos*], [*letalidade*], [treino (≤ 2022)], [1.242.680], [390.769], [31,4%],
  [validação (2023)], [24.148], [4.572], [18,9%], [teste (2024)], [16.142], [2.945], [18,2%],
  fonte: [módulo 00, `gold/MANIFEST.md` §2.4])

#v(1mm)
Essa queda pela metade na fronteira do split é o achado que os cinco
módulos vão explicar, não um incômodo a corrigir (módulo 00,
`gold/MANIFEST.md` §2.4).

== O modelo, escolhido por protocolo

O modelo do curso não foi escolhido por gosto. Um protocolo foi
pré-registrado antes de qualquer leitura do teste: o critério primário é
a maior AUC na validação de 2023; modelos dentro de um erro-padrão
bootstrap pareado ficam empatados e vão a desempate por calibração,
parcimônia e determinância; o teste é lido uma vez, depois da escolha, e
não pode mudá-la (módulo 00, `SELECTION.md`). Seis candidatos --- o
constante, o modelo linear de probabilidade, a logística, a árvore, a
floresta e o XGBoost --- foram buscados em 73 configurações declaradas.

#figure(
  scope: "parent",
  placement: top,
  image("/modules/00-dataset/SELECTION.svg", width: 100%),
  caption: [
    O estudo inteiro numa figura: três anos com um papel cada, a barreira
    que impede o teste de entrar na escolha, e o placar de validação que
    elegeu o XGBoost com 0,7564 contra 0,7403 da floresta --- a faixa de
    empate fica vazia, porque nenhum candidato está a menos de um
    erro-padrão bootstrap (0,0018) do líder (módulo 00, `SELECTION.md`).
  ],
)

O vencedor foi o XGBoost tunado --- 800 árvores, profundidade 4,
`learning_rate` 0,05, `min_child_weight` 100, `reg_lambda` 5,0,
categóricas nativas, semente 42 (módulo 00, `MODEL.md`). A regra 8 do
protocolo foi acionada: como o vencedor divergia dos parâmetros em vigor,
o modelo do curso mudou e os cinco módulos de método foram
re-sincronizados. A logística fica ao lado como *baseline* interpretável,
e a distância entre as duas é o problema que o curso existe para
resolver.

#sp-tab(columns: (auto, auto, auto, auto, auto, auto),
  [*modelo*], [*split*], [*AUC*], [*Brier*], [*prev.*], [*obs.*],
  [XGBoost], [val], [0,7564], [0,1356], [0,2209], [0,1893], [XGBoost], [teste], [0,7644], [0,1308], [0,2154], [0,1824],
  [logística], [val], [0,7206], [0,1550], [0,2764], [0,1893], [logística], [teste], [0,7246], [0,1452], [0,2419], [0,1824],
  fonte: [módulo 00, `MODEL.md`])

#v(1mm)
A tabela contém o achado central do relatório em duas colunas. No teste
de 2024, o modelo prevê 0,2154 de óbito médio onde se observa 0,1824
(módulo 00, `MODEL.md`): o *gap de calibração* é a deriva de regime
reaparecendo dentro do modelo, que aprendeu letalidades de 2020--2022 e
encontrou outro mundo. A discriminação sofre junto, embora menos: por ano
de início, a AUC vai de 0,7890 em 2020 a 0,7680 em 2024, com fundo em
0,7451 em 2022 (módulo 00). Na base cheia o modelo faz 0,7680; a amostra
commitada de 240.290 linhas que os módulos de método usam custa apenas
0,0036 de AUC (módulo 00).

== As quatro impossibilidades

O Ouro carrega o que é preciso para contar ficção. A ficha do módulo 00
desliga as 13 comorbidades quando `FATOR_RISC` não declara fator de
risco, a campanha
de vacinação tem data de início, e a coorte tem definição de caso. Cada
uma dessas estruturas é uma cerca, e a fração da amostra em *estado
vulnerável* a cada uma está medida (módulo 00, `MODEL.md`):

#sp-tab(columns: (1fr, auto),
  [*restrição*], [*fração vulnerável*], [critério-2 por um fio], [79,60%], [portão do funil], [37,27%],
  [pré-campanha], [29,67%], [critério-3 por um fio], [24,67%],
  fonte: [módulo 00, `MODEL.md`])

#v(1mm)
Perturbar uma linha através de uma dessas fronteiras fabrica um paciente
que não pode existir. Os cinco módulos fazem essa conta pela *mesma*
função (`gate_impossible`), o que torna os números idênticos por
construção e não por disciplina (módulo 00, `MODEL.md`).

== O paciente

O paciente do relatório vem de regra, não de índice: no módulo 00, o
menor |p − 0,5| no teste, com desempate por identificador. É o `gold_id`
1276776, com
p(óbito) = 0,500 --- 90 anos, masculino, Sudeste, início na semana 34 de
2024, uma dose antes do sintoma, cardiopatia (módulo 00, `MODEL.md`).

A escolha não é arbitrária: um paciente em cima da fronteira é o único em
que a reta local do LIME não degenera, e é aquele em que as forças do
SHAP se cancelam de forma legível. Os módulos 01 e 03 usam um segundo
paciente pela mesma regra, restrita ao estado vulnerável às três cercas
--- o *vulnerável* ---, exatamente para mostrar que a quantidade de
ficção que um método fabrica depende de *quem* está sendo explicado. O
módulo 04 precisa de um terceiro, escolhido por p mais próximo de 0,8:
contrafactual pede alguém com o que perder.

= 3. O paciente e as cercas

Antes das cinco perguntas, uma legenda e uma tese.

A legenda é do curso e vale em todas as figuras deste relatório: *a forma
diz de onde o ponto veio; a cor diz o que ele é* (módulo 03, célula
"Ferramentas de desenho"). Círculo é paciente real da base, e a cor é o
desfecho *observado*: azul sobreviveu, terracota morreu. Quadrado é
vizinho *sintético*, e a cor é a *predição do modelo*, na mesma
escala --- cinza-claro enquanto o modelo ainda não foi consultado. O
marcador em X, escuro, é o paciente sendo explicado. E há três trabalhos
diferentes para
o tracejado, com três traços diferentes: escuro e longo é a fronteira do
modelo, cinza e médio é o anel do kernel (um construto nosso, não do
modelo), claro e curto é andaime de eixo. Já aconteceu de uma sala ler
uma janela de eixo como se fosse uma vizinhança.

A tese é o que dá unidade ao relatório. A ficha do SIVEP não é um
formulário plano: ela *desliga campos condicionalmente*. Quando
`FATOR_RISC` diz que não há fator de risco (módulo 00), as 13
comorbidades nem são apresentadas ao digitador --- e o vazio resultante
não é dado faltante, é
informação. O portão foi medido nos seis anos com 0,00% de contradição
(módulo 00), e é por isso que o Prata separa três leituras do vazio
(`nao_aplicavel`, `ausente`, `ignorado`) em vez de fundi-las.

#figure(
  scope: "parent",
  placement: top,
  image("/modules/00-dataset/FUNIL.svg", width: 100%),
  caption: [
    A variável-funil. Tratar os três estados do vazio como uma coisa só
    infla a estatística de dado faltante por 1,8× a 5,7× conforme o ano
    (módulo 00), e imputar por cima inventa pacientes clinicamente
    impossíveis. É esta estrutura --- e não uma preferência estética --- que
    transforma "perturbação independente" num problema contável.
  ],
)

A consequência é a frase que organiza o curso: como as features são
*conjuntamente restritas*, todo método que perturba, varre ou permuta
features de forma independente --- ceteris paribus, ICE, LIME, Shapley
marginal, PDP, importância por permutação --- fabrica pacientes que não
podem existir (`ROADMAP.md`, "A tese organizadora").

Três cercas concretas aparecem em todos os módulos:

#sp-tab(columns: (auto, 1fr),
  [*cerca*], [*o que ela proíbe*],
  [portão do funil], [marcar uma comorbidade num registro que declarou não haver fator de risco],
  [calendário da campanha], [uma dose de vacina antes de a campanha existir],
  [definição da coorte], [um sintoma-fio removido de quem só entrou na coorte por ele],
  fonte: [módulo 00, `MODEL.md`; a mesma função nos módulos 01 a 05])

#v(1mm)
Duas propriedades tornam essa contagem incomum. Primeiro, ela é
*derivável*: não é um envelope empírico com piso geométrico, é a regra
do formulário lida no dado. Segundo, ela *não é vista pela geometria*:
no módulo 01, o ponto impossível fica a distância de Gower 0,0037 de um
paciente real --- mais perto que o ponto possível (0,1287) e mais perto do
que o paciente real mediano fica do vizinho dele (0,0046). Uma checagem
genérica de plausibilidade por distância não pegaria a contradição:
mudar um nível de categoria custa o mesmo, seja ele impossível ou não.

= 4. Ceteris paribus: e se a idade fosse outra?

O perfil ceteris paribus é o método mais simples do curso. Congela-se o
paciente, move-se uma variável ao longo de uma grade e plota-se a
predição. Não há substituto, kernel nem amostragem: a curva *é* a saída
do modelo, avaliada em linhas que se constroem copiando o paciente e
trocando uma célula @molnar2025. É por não aproximar nada que ele é o lugar certo
para expor o problema que todos os métodos seguintes herdam.

O mecanismo tem uma consequência que se lê errado com facilidade. O
perfil de um modelo de árvores é uma *escadaria*, e a altura de um
degrau é propriedade da grade, não do modelo: refinar do passo 10 ao
passo 1 deixa a amplitude intacta em 0,4809 nos quatro passos, enquanto o
maior salto aparente desmonta de 0,1387 para 0,0852 e então não cede mais
(módulo 01, internals §1). Leia posições de corte; nunca alturas de
degrau.

#figure(
  scope: "parent",
  placement: top,
  image("/modules/01-ceteris-paribus/figures/cp_passo_1b_modelos.png", width: 100%),
  caption: [
    O mesmo perfil em dois modelos --- a fig. 12.5 do livro, refeita no
    módulo 01. Neste paciente a escadaria varre *mais* que a rampa na
    idade (0,481 contra 0,397), e nas doses os dois discordam ponta a ponta: a
    logística sobe +0,217, monótona, carregando o confundimento de
    quem-se-vacinou, e o XGBoost termina 0,044 abaixo de onde começou
    (módulo 01, walkthrough §1b).
  ],
)

Há três coisas para olhar na figura. A primeira é a forma: a logística
desenha a mesma curva para *todo* paciente, mudando só o nível, porque
não tem interações --- e os quatro pontos de AUC que o XGBoost ganha são
feitos exatamente daquilo que nenhum coeficiente global exibe. A segunda
é a amplitude, e ela contraria a intuição de que a reta é mais agressiva.
A terceira é o painel de doses, e é a mais importante: dizer "o XGBoost
desce nas doses" é ler a ponta, não o paciente. O perfil não é monótono
--- sobe até a segunda dose --- e a inclinação local na vizinhança do
próprio paciente é *positiva*, +0,03542 (módulo 01, internals §4). O
que a figura *não* mostra é efeito de intervenção: nada aqui diz o que
aconteceria se este paciente tomasse mais uma dose.

*A resposta, e o preço.* Para a pergunta 1 o método responde
diretamente, lendo a curva de idade no ponto desejado. E responde barato:
sem semente, sem aproximação --- com subamostragem desligada o XGBoost é
determinístico, e no módulo 01 doze sementes dão correlação 1,0000 entre
perfis (internals §2). O preço é que a resposta vale para uma linha que o
método fabricou. Para este paciente, as oito features de maior ganho dão
0% de varredura impossível (módulo 01, walkthrough §painel) --- ele é
imune a duas cercas. Para o vulnerável, a mesma varredura é ficção
integral: 1 de 1 em diabetes, 6 de 6 em doses. Na amostra, 37,3% dos
pacientes estão atrás do portão, 29,7% são pré-campanha e 79,6% têm o
critério por um fio (módulo 01, walkthrough §2). A concentração da ficção
é propriedade da coorte, não do método --- e um paciente só esconderia
o achado.

= 5. ICE: os outros respondem igual?

O ICE responde desenhando o feixe --- um perfil ceteris paribus por
paciente, todos no mesmo eixo @goldstein2015. O ganho sobre o módulo 01 é
heterogeneidade --- e o teste que o capítulo propõe é de olho nu: se
todas as curvas seguem o mesmo curso, não há interação e a média (o PDP)
basta. A regra de amostragem precisa ser declarada, porque o próprio
capítulo avisa do *overcrowding*; aqui são 200 pacientes, 40 por ano,
semente 42 (módulo 02, walkthrough §1). Estratificar por ano é o que
deixa o regime visível: sortear sem estrato o afogaria no desbalanceio,
já que 2020--2022 domina a base.

#figure(
  scope: "parent",
  placement: top,
  image("/modules/02-ice/figures/ice_passo_1_feixe.png", width: 100%),
  caption: [
    O teste do capítulo falha de propósito: as curvas *não* seguem o mesmo
    curso. Aos 80 anos o feixe vale 0,481 para quem adoeceu em 2020 e
    0,303 para quem adoeceu em 2024, e o PDP reporta 0,400 --- um número
    que não descreve regime nenhum (módulo 02, walkthrough §1).
  ],
)

O que olhar é a rampa de intensidade: quanto mais escura a curva, mais
letal o regime em que o paciente adoeceu. As curvas de 2020 correm por
cima, as de 2024 por baixo, e a separação é grande o bastante para que a
média fique entre duas populações em vez de descrever qualquer uma. O que
a figura mede é a predição do modelo em cada idade da grade, para os 200
pacientes reais do módulo 02. O que ela *não* mede é efeito da idade: um
feixe é uma
coleção de perguntas contrafactuais mal-postas, e a advertência causal do
cap. 12 vale dobrada aqui.

Duas leituras completam o quadro. Centradas na idade zero, as curvas
mostram só a *forma*, e ela é quase paralela: o ganho de 0 a 100 anos vai
de 0,247 no percentil 10 a 0,623 no percentil 90, com correlação mediana
de 0,983 com a média (módulo 02, walkthrough §2). Para idade, portanto, o
PDP acerta a forma e erra o nível de todos ao mesmo tempo --- o modo de
mentir mais educado que existe. E a derivada acha o efeito onde ninguém
procurava: o pico é *pediátrico*, 0,0239 por ano aos 10 anos, contra
mediana de 0,00326 no miolo de 40 a 54 anos (módulo 02, walkthrough §4).
Não é biologia: é o modelo lendo uma coorte em que a SRAG pediátrica
pré-COVID era bronquiolite.

*A resposta, e o preço.* Não, os outros não respondem igual --- e a
diferença é o ano em que adoeceram. O preço é que a ficção se multiplica
por 200 e continua contável. No módulo 02, o feixe de idade é
logicamente seguro (0 de 10.200 pontos impossíveis); o de doses fabrica
252 de 1.400, 18% --- exatamente os 42 pacientes pré-campanha vezes as 6
doses varridas, conta *derivável antes de medida* (módulo 02) ---; e o de
tosse chega a 54% (walkthrough §3 e internals §3 do módulo 02). A escolha
da feature varrida decide
se o feixe é retrato ou fábula. Vale registrar que essas contagens não se
moveram um ponto quando o modelo do curso mudou (módulo 02): a cerca é da
base, não do modelo.

= 6. LIME: por que esta predição, localmente?

O LIME @ribeiro2016 troca a varredura por um substituto. Ele perturba o paciente,
pergunta ao modelo o que prevê em cada vizinho, pesa os vizinhos por
proximidade e ajusta uma reta regularizada nesse conjunto ponderado. O
objetivo tem três termos --- a perda ponderada pelo kernel, a família de
modelos simples e a penalidade de complexidade --- e o mais importante a
dizer em voz alta é que o substituto *nunca passa por cima* do modelo:
a predição continua vindo do XGBoost, a reta só a resume (módulo 03,
walkthrough §objetivo). A análise teórica de @garreau2020 registra que
falta uma heurística fundamentada para a largura do kernel --- o problema
aberto que a medição da seção ilustra.

#figure(
  scope: "parent",
  placement: top,
  image("/modules/03-lime/figures/lime_passo_a_passo.png", width: 100%),
  caption: [
    Os seis passos do LIME sobre um corte ceteris paribus do XGBoost real.
    Três surpresas já estão aqui: a nuvem não é centrada no paciente ---
    ele está a 6,7 desvios do centro dela ---, o kernel descarta quase
    tudo (0,1% dos vizinhos com peso acima de 0,1) e a reta final é
    ajustada nesse deserto, com R² 0,399 (módulo 03, walkthrough §0).
  ],
)

Os painéis A e B mostram a fronteira do modelo no corte e o anel de
meia-altura do kernel, que no módulo 03 mede ±16 anos por ±5,7 meses:
"local" tem esse tamanho. O painel C é o que costuma surpreender --- a nuvem não está
sobre o paciente, porque o gerador default centra a gaussiana na média do
treino, e isso está lido no fonte instalado, não suposto (módulo 03,
internals §1). O painel D é o único momento em que o modelo é consultado;
o E mostra o peso; o F, a reta. O que a figura não mostra é uma
vizinhança de pacientes: mostra um sorteio marginal por feature.

E é essa a contagem que o módulo faz. Na rodada ingênua do módulo 03,
sem declarar categóricas, 4.999 de 5.000 vizinhos carregam pelo menos um
código fabricado, a idade sintética vai a 126,9 anos e
34,3% têm doses negativas --- e nada avisa, porque o *wrapper* de
predição arredonda em silêncio (módulo 03, walkthrough §2). Declarar as
36 discretas zera os códigos fabricados e sobe o R² a 0,65 baixando o
erro no próprio paciente a 0,008 (módulo 03, walkthrough §3). Mas isso
conserta a *gramática*, não a *biologia*: cada coluna continua
sorteada sozinha, a correlação entre calendário e doses é +0,61 no treino
real e −0,004 na nuvem, e 30,6% dos vizinhos do paciente-regra --- 79,2%
dos do vulnerável --- continuam impossíveis (módulo 03, walkthrough §4 e
internals §2).

*A resposta, e o preço.* O LIME dá um ranking com sinal, e o topo dele
é firme: dez sementes produzem o mesmo top-5 (Jaccard 1,00) e nenhuma
troca de sinal no top-8 (módulo 03, walkthrough §6). A areia está uma
posição adiante --- 3 das 8 features do topo somem do top-10 em alguma
semente, e com nuvens menores o mínimo volta a 0,43 (módulo 03, internals
§5). O preço maior, porém, é o R²: com kernel estreito o modelo local
degenera na constante certa e entrega R² 0,00 *com erro 0,00* --- a
explicação vazia perfeita ---; com kernel largo, R² 0,68 e erro 0,028 no
paciente. As duas curvas sobem juntas, não há largura que compre as duas,
e a regra prática é dura: *não ranqueie explicações por R²* (módulo 03,
walkthrough §5). A amostragem fora da variedade, que a contagem de cercas
mede, é também a porta do ataque de @slack2020: um classificador que
detecta as perturbações esconde seu viés do LIME. O survey de @knab2025
mapeia as variantes propostas para cada um desses estágios --- e a regra
prática do repositório é rodar nelas as mesmas medições antes de adotar
qualquer uma.

= 7. Contrafactuais: o que teria de mudar?

Os três métodos anteriores perguntam "o que pesou?". O contrafactual
inverte: qual é a menor mudança que muda a saída? A inversão muda também
o papel das cercas, que deixam de ser diagnóstico de método doente e
viram *restrição de busca*. Este é o único método do curso cuja saída é
um paciente hipotético @wachter2018, e por isso o único em que os critérios de
qualidade são sobre pessoas: validade, proximidade, sparsidade,
plausibilidade e diversidade (módulo 04, walkthrough §1).

O módulo não usa biblioteca. O espaço declarado deste problema cabe
inteiro na memória --- 113 mudanças simples e 6.129 pares ---, então a
perda de Wachter é *enumerada* em vez de otimizada, o que dá cobertura
completa, determinismo e custo de milissegundos (módulo 04, walkthrough
§2). O NSGA-II multiobjetivo de @dandl2020 seria o caminho se o espaço
não coubesse, e a diversidade otimizada de @mothilal2020 fica citada e
não executada, por decisão registrada no PR do pin. O paciente aqui é
outro, escolhido por p mais próximo de 0,8 (módulo 04): 32 anos, quatro
doses, síndrome de Down, doença neurológica, imunodepressão e doença
renal.

#figure(
  scope: "parent",
  placement: top,
  image("/modules/04-counterfactual/figures/cf_passo_3_painel.png", width: 100%),
  caption: [
    No módulo 04, dos 624 pacientes de alto risco no teste, 30,3% têm
    contrafactual acionável e 69,7% não têm --- e a fração cai conforme o
    risco sobe:
    35% na banda 0,5--0,6 e 0% acima de 0,7, onde nenhum dos 19 pacientes
    tem saída (módulo 04, walkthrough §5).
  ],
)

Cada barra é uma banda de risco previsto; a altura é a fração de
pacientes daquela banda para quem existe alguma combinação de movimentos
*ao alcance de uma pessoa* --- subir doses, declarar o que há a
declarar --- que cruze o limiar. O que o painel mede é cobertura de
prescrição, não eficácia clínica. E o que ele *não* significa é que os
pacientes sem barra estejam condenados: significa que, dentro do espaço
de alavancas declarado e no limiar escolhido, o método não tem nada a
prescrever. A objeção do limiar está medida: em 0,5 a cobertura é 30,3%,
em 0,4 cai a 9,3% e em 0,3 a 1,1% (módulo 04, internals §4). O limiar é
decisão de quem opera; a conta acompanha.

O gradiente é a leitura difícil da figura: quem mais precisaria de uma
saída é exatamente quem não tem nenhuma. E a busca livre explica por quê.
A melhor mudança única do mundo é apagar do prontuário a saturação baixa,
que derruba a predição de 0,793 para 0,571 e é *consequência* da doença,
não alavanca; logo atrás vêm voltar a ter 10 anos e recuar o calendário
para o mês 6 da pandemia (módulo 04, walkthrough §2). Dos 68 candidatos
válidos, três histórias com features *disjuntas* levam a predições
diferentes --- 0,199, 0,316 e 0,452 --- sem um ingrediente em comum: é o
efeito Rashomon impresso, e a pergunta que ele deixa é qual dessas
receitas se contaria ao paciente (módulo 04, walkthrough §4).

*A resposta, e o preço.* Para este paciente a resposta honesta é *não
há*: os dois candidatos acionáveis que ele tem deixam a predição em
0,793, onde ela já estava (módulo 04, walkthrough §5). Um método de
explicação que só sabe prescrever precisa saber dizer isso. O preço tem
duas partes. A primeira é que *válido* não é *alcançável*: os melhores
candidatos "existem" --- passam na cerca ---, mas pedem uma máquina do
tempo. A segunda é que a plausibilidade se decide sobre o candidato
inteiro, não sobre o movimento: recuar o calendário sozinho cai na cerca
pré-campanha, e recuá-lo *com zero doses* não cai (módulo 04, walkthrough
§3). Em compensação, este é o método que menos fabrica ficção: só 3,5%
dos 113 movimentos caem na cerca, contra 30,6% dos vizinhos do LIME pela
mesma régua (módulo 04, walkthrough §2). Quem parte de um paciente real
inventa pouco.

= 8. SHAP: quanto cada feature pesou?

O SHAP @lundberg2017 é o único método do curso com uma garantia de
*soma*. O jogo é a predição desta instância, o ganho é a diferença para a
predição média, os jogadores são os valores das features, e o valor de
Shapley @shapley1953 reparte esse ganho pelos jogadores. Em árvores, o
TreeSHAP @lundberg2020 calcula essa repartição de forma exata --- aqui
pelo `pred_contribs` que já mora no XGBoost --- e a
propriedade da eficiência deixa de ser promessa e vira verificação: as
40 contribuições do módulo 00 mais a base reproduzem a margem com desvio
máximo
1,05×10⁻⁵ nas 16.142 linhas do teste, e três refits dão contribuições
bit-idênticas (módulo 05, internals §1).

#figure(
  scope: "parent",
  placement: top,
  image("/modules/05-shap/figures/shap_passo_1_waterfall.png", width: 100%),
  caption: [
    O cabo de guerra que empata (módulo 05): partindo da base −0,79 em
    margem (sigmoide 0,31, a prevalência do treino), a idade empurra +0,92, a
    vacinação declarada freia −0,36, o calendário freia −0,32 e a zona
    desconhecida empurra +0,16 --- e a soma dá exatamente a margem do
    paciente (módulo 05, walkthrough §1).
  ],
)

O que olhar é a soma, não o tamanho das barras: elas fecham porque um
axioma manda, não porque um ajuste foi bom. O que a figura mede é a
contribuição de cada valor *em relação à predição média*, na escala de
margem --- o espaço em que somar as 800 árvores do módulo 00 faz sentido. O que ela
*não* significa é causa, nem contrafactual: um φ positivo não diz que
aumentar a feature aumentaria a predição. O painel de dependência mede
essa armadilha em carne viva: o φ das doses é *positivo* nos vacinados,
+0,08 em três ou mais doses (módulo 05, walkthrough §5). Não porque
vacina mate, mas porque o crédito protetor mora na declaração colinear e
o que sobra para a contagem de doses é marcar os grupos priorizados --- e
o antídoto foi medido no módulo 04, onde subir doses quase não move a
predição.

Duas medições fecham o arco. A primeira liga o SHAP à deriva: `meses` é a
3ª feature por média de |SHAP| e a 19ª por *gain* (módulo 05, walkthrough
§4). Importância para prever 2024 não é importância para construir
árvores em 2020--2022 --- é a deriva do módulo 02 vista pela atribuição.
A segunda é o preço do condicionamento alternativo. O `pred_contribs` é
*path-dependent*; o pacote de referência mudou seu default para o
*interventional*, e medi-lo à mão pelo estimador de permutações de
@strumbelj2014 mostra direções iguais mas magnitudes
diferentes onde as correlações moram --- a idade vai de +0,92 a +1,03 e a
vacinação de −0,36 a −0,51 (módulo 05, walkthrough §6).

*A resposta, e o preço.* O SHAP responde a pergunta 5 com números que
somam, e é a única resposta auditável do relatório. O preço aparece
exatamente onde o LIME já havia pagado: o estimador *interventional*
compra sua leitura avaliando o modelo em híbridos, e 23,1% das 2.460
linhas híbridas são pacientes impossíveis pela mesma `gate_impossible`
--- portão 15,4%, dose pré-campanha 8,2% (módulo 05, walkthrough §7). A
limitação que o cap. 18 enuncia como "ignora a dependência entre
features" fica, aqui, contada em vez de citada.

= 9. As cercas, lado a lado, e a deriva

Os cinco módulos mediram a mesma coisa com cinco instrumentos. Como a
contagem sai da mesma função (`gate_impossible`, módulo 00), as frações
são comparáveis --- e a comparação é o resultado mais forte deste
relatório.

#sp-tab(columns: (auto, 1fr, auto),
  [*método*], [*o que foi contado*], [*impossível*],
  [módulo 01], [amostra atrás do portão do funil], [37,3%], [módulo 01], [amostra com o critério por um fio], [79,6%], [módulo 02], [pontos do feixe de doses (252 de 1.400)], [18%],
  [módulo 03], [vizinhos do paciente-regra], [30,6%], [módulo 03], [vizinhos do vulnerável], [79,2%], [módulo 04], [movimentos simples enumerados], [3,5%], [módulo 05], [linhas híbridas do interventional], [23,1%],
  fonte: [walkthrough §2 (01), §3 (02), §4 (03), §2 (04) e §7 (05)])

#v(1mm)
A tabela não é um ranking de qualidade. Ela mostra que a taxa de ficção é
uma propriedade conjunta de três coisas: o método, a feature perturbada e
*quem* está sendo explicado. O contrafactual fabrica pouco porque parte
de um paciente real e move uma célula por vez. O LIME fabrica muito
porque sorteia todas as colunas de uma vez, e fabrica *mais que o dobro*
no vulnerável --- pelo mesmo gerador, já que a nuvem não olha para o
paciente (módulo 03, walkthrough §4). O ICE de idade não fabrica nada e o
de doses fabrica 18% porque a cerca é da feature, não do feixe (módulo
02). E o SHAP paga 23,1% apenas na variante *interventional*: o exato de
caminho não avalia híbrido nenhum (módulo 05).

Uma nota sobre comparar números entre módulos: 79,6% no módulo 01 e 3,6%
na variante local do módulo 03 não se contradizem. São perguntas
diferentes --- flip forçado de um sintoma contra sorteio pela prevalência
--- medidas pela mesma régua (módulo 03, walkthrough §4).

#figure(
  scope: "parent",
  placement: top,
  image("/modules/01-ceteris-paribus/figures/cp_passo_4_restrito.png", width: 100%),
  caption: [
    O remédio do próprio capítulo, medido no módulo 01. Para um paciente
    pós-campanha a grade restrita preserva a curva inteira (amplitude
    0,0896 antes e depois, nenhum ponto impossível); para um pré-campanha,
    ela a *remove* --- no módulo 01, 0,0119 vira 0,0000, com 6 de 7 pontos
    barrados (walkthrough §4). Restringir a grade funciona dizendo *quando
    não perguntar*.
  ],
)

== A deriva, vista por cinco instrumentos

O segundo fio é o mesmo achado aparecendo em cinco lugares. Ele nasce na
base: a letalidade bruta anual vai de 29,0% em 2020 a 8,6% em 2024, e a
fração de casos COVID de 70,2% a 11,6% (módulo 00). Entre os splits, a
letalidade observada cai de 31,4% para 18,2% (módulo 00).

O modelo herda a queda como *erro de calibração*: prevê 0,2154 onde se
observa 0,1824 no teste (módulo 00, `MODEL.md`), e a AUC por ano de
início desce de 0,7890 a 0,7680 (módulo 00). O ICE dá rosto ao número: o
feixe de idade estratifica por ano, e aos 80 anos vale 0,481 para 2020
contra 0,303 para 2024 (módulo 02, walkthrough §1). O SHAP dá um posto: a
feature de calendário é a 3ª por atribuição média e a 19ª por *gain*
(módulo 05, walkthrough §4). E o contrafactual mostra a deriva do lado
perverso --- os melhores candidatos válidos do módulo 04 pedem
literalmente que o paciente volte ao mês 6 da pandemia (módulo 04,
walkthrough §3).

A conclusão a carregar é que uma explicação que revela "ano" está
*correta*. O modelo aprendeu o regime, e negar isso seria pior do que
mostrá-lo.

= 10. Limitações, discussão e o que aprendemos

== O que os métodos não dizem aqui

Nenhum dos cinco entrega causalidade. Todos leem um modelo treinado em
fichas de vigilância, e o modelo lê *documentação* tanto quanto
biologia. A demonstração mais limpa disso está no módulo 00: com o
resultado de imagem como feature, a AUC de teste subiria de 0,7644 para
0,7682, e o sinal seria *invertido* --- a letalidade é 30,5% sem
registro de imagem contra 28,5% com registro (módulo 00). É qualidade de
documentação vazando no rótulo, não pulmão.

A mesma lógica explica a exclusão mais discutida do Ouro. `UTI` e
`SUPORT_VEN` são os dois campos clinicamente mais fortes da ficha, e
somá-los levaria a AUC de teste de 0,7644 a 0,8514, com Δ de 0,087 no
bootstrap pareado (módulo 00, `GOLD.md`, decisão 3). Ficam fora mesmo
assim, e o critério não é o tamanho do ganho: é o *instante da
predição*. A ficha só os preenche no encerramento --- `SUPORT_VEN` não
tem data nenhuma, e a data de entrada em UTI existe numa minoria dos
registros ---, o que os põe do lado errado da questão 2.3 do PROBAST
@wolff2019 e do item 9b do TRIPOD+AI @collins2024; @wynants2020 atribuíram
a essa causa parte do alto risco de viés dos modelos de COVID revisados.
Há ainda confundimento por capacidade instalada: @ranzani2021 contaram
36.046 óbitos entre 45.205 ventilados mecanicamente nas primeiras 250 mil
internações brasileiras por COVID, com oferta de leitos de UTI muito
desigual entre regiões --- mover
`suport_ven` num perfil ceteris paribus não mostraria efeito de
tratamento, mostraria triagem. Trabalhos que fazem a pergunta da admissão
sem essas colunas ficam na mesma faixa do nosso modelo: 0,767 no 4C
@knight2020, 0,813 em @baqui2021 sobre o mesmo banco, e o ABC2-SPH
@marcolino2021 as exclui por desenho. Os 0,8514 do módulo 00 não são um
modelo melhor da mesma pergunta; são um modelo de outra pergunta
@vangeloven2020.

== O que os dados ensinaram sobre os métodos

A lição principal é a das cercas, e ela inverte a direção habitual: em
vez de usar o método para entender os dados, foram os dados que
qualificaram o método. Numa base cuja estrutura de formulário é
conhecida, a limitação que Molnar enuncia em prosa --- perturbação
independente cria combinações irreais --- deixa de ser advertência e vira
número. E o número tem endereço: 30,6% no LIME (módulo 03), 18% no feixe
de doses do ICE (módulo 02), 23,1% nos híbridos do SHAP (módulo 05) e
3,5% no contrafactual (módulo 04).

A segunda lição veio de um acidente instrutivo. O estudo de seleção do
módulo 00 trocou os hiperparâmetros do modelo do curso, e os cinco
módulos foram re-sincronizados número a número. A regra 3 da barra de
evidência foi aplicada em dois níveis: uma nota coletiva de
condicionamento por módulo e um registro individual "dizia X, mede Y"
para cada afirmação que a medição derrubou. Caíram quatro afirmações no
módulo 01, nenhuma no módulo 02, quatro no módulo 03, oito no módulo 04 e
uma no módulo 05 (`CHANGELOG.md`, 2026-09-02).

O que essa contagem revela é mais interessante que ela mesma. As
afirmações que caíram foram, quase todas, *leituras de ponta* ou
*narrativas bonitas*: "a amplitude converge com a grade", "a rampa é mais
agressiva que a escadaria", "o XGBoost desce nas doses", "a melhor
mudança é rejuvenescer 71 anos". As que sobreviveram foram as contagens
de cerca --- que não se moveram um ponto sob o novo modelo (módulo 02),
porque medem a base e não o modelo. Um erro de Gower do módulo 01 nem
sequer era do modelo novo: a prosa citava 0,043 onde a célula sempre
imprimira 0,0491, e a discrepância só apareceu quando alguém conferiu
token a token.

Vale registrar também o que o painel das oito features de maior ganho
imprimiu para o paciente-regra: 0% de varredura impossível (módulo 01).
Um resultado nulo, publicado --- e ele é a metade que faltava do achado,
porque é a prova de que a ficção depende de quem se explica.

== O que evitar

- *Prosa editada por busca-e-substituição.* Quando o modelo muda, o
  número muda *e a afirmação pode cair*. Trocar dígitos sem reler a frase
  produz texto que passa a bater com o caderno e continua mentindo.
- *Número sem célula que o imprima.* É a regra dura do repositório: ou
  a célula existe, ou o número sai da prosa.
- *Ler a figura em vez da célula.* Uma afirmação do módulo 05 dizia
  "acima de 70 anos" porque foi lida no gráfico; virou a janela impressa
  de 78 a 90 anos.
- *PDP como "o" efeito.* Aos 80 anos ele reporta 0,400 e não descreve
  regime nenhum (módulo 02).
- *LIME sem declarar categóricas.* Sem isso, 4.999 de 5.000 vizinhos
  carregam código fabricado e nada avisa (módulo 03).
- *Contrafactual plausível mas inalcançável.* Passar na cerca responde
  "isso existe?", nunca "dá para chegar lá daqui?" (módulo 04).
- *φ positivo lido como causa.* O φ das doses é positivo nos vacinados
  (módulo 05); a leitura causal está medida como errada no módulo 04.

== A barra de evidência como método

O que torna este relatório verificável não é o texto: é a regra. Todo
número em prosa é impresso por uma célula versionada; a sentença que o
carrega nomeia o módulo; correções ficam no registro em vez de sumirem
--- e há um script que reprova o texto quando a regra é quebrada. É
barato de manter e caro de fingir.

== O que vem a seguir

O `ROADMAP.md` já nomeia os próximos passos como capítulos-remédio e
capítulos-armadilha. O *ALE* (cap. 20) é o remédio direto para o que
este relatório contou: condicionamento local respeita o funil em vez de
atravessá-lo. O *SHAP condicional* é o remédio do lado da atribuição.
Do lado das armadilhas, o *PDP* (cap. 19) e a *importância por
permutação* (cap. 23) são os próximos a serem medidos com a mesma régua
--- e a segunda tem, nesta base, uma armadilha pronta: um par de colunas
redundante por construção, entre as quais a importância se divide de
forma arbitrária. A pergunta que abre o curso e o fecha continua sendo a
mesma: *quem são as linhas que você acabou de dar de comer ao modelo?*

#bibliography("references.bib", title: [Referências], style: "apa")
