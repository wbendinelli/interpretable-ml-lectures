// Figuras desenhadas no próprio Typst, com os tokens do sapians.
//
// Por que aqui e não em SVG: os SVGs de módulo foram desenhados para o
// README (Georgia serifada, fundo bege, 1180x816 em paisagem) e entram na
// página do relatório como um retângulo de outra tipografia. Estes desenhos
// usam a fonte e a paleta do documento.
//
// Regra: nenhum número dentro do desenho. A figura ensina o mecanismo; os
// números vivem na prosa, onde a barra de evidência os alcança.

#import "@preview/sapians:0.3.0": *

#let _caixa(titulo, corpo, destaque: false) = block(
  width: 100%,
  fill: if destaque { sapians-card-bg } else { sapians-paper },
  stroke: if destaque { stroke-accent } else { stroke-light },
  radius: radius-sm,
  inset: (x: 2.6mm, y: 2.2mm),
)[
  #text(size: 7.6pt, weight: "bold", fill: if destaque { sapians-terracotta } else { sapians-text-dark })[#titulo]
  #v(0.9mm)
  #text(size: 6.9pt, fill: sapians-muted-dark)[#corpo]
]

#let _seta(rotulo) = align(center)[
  #v(3.5mm)
  #text(size: 6.2pt, fill: sapians-muted-dark)[#rotulo]
  #v(-1.2mm)
  #text(size: 12pt, fill: sapians-terracotta)[→]
]

// ---------------------------------------------------------------------------
// A variável-funil: um campo decide se outros treze chegam a existir.
#let fig-funil() = block(width: 100%, breakable: false)[
  #grid(
    columns: (1.05fr, 13mm, 1.15fr),
    align: top,
    _caixa(
      [O portão],
      [O campo de fator de risco pergunta, uma vez só: este paciente tem
       algum? A resposta governa o bloco inteiro que vem depois.],
      destaque: true,
    ),
    _seta[habilita],
    _caixa(
      [As treze comorbidades],
      [Cardiopatia, diabetes, asma, doença renal, obesidade, doença
       hepática, doença neurológica e as demais. Quando o portão diz que não
       há fator de risco, nenhuma delas é apresentada a quem preenche.],
    ),
  )

  #v(2.6mm)
  #align(center)[#text(size: 12pt, fill: sapians-terracotta)[↓]]
  #v(1.4mm)
  #align(center)[#text(size: 6.4pt, fill: sapians-muted-dark)[
    e então cada comorbidade guarda, além do valor, em que estado ela ficou
  ]]
  #v(2.2mm)

  #grid(
    columns: (1fr, 1fr, 1fr),
    column-gutter: 3mm,
    align: top,
    _caixa(
      [não se aplica],
      [O portão disse não, e o campo nunca chegou a ser apresentado.
       *Isto não é dado faltante:* é a ficha registrando uma decisão.],
      destaque: true,
    ),
    _caixa(
      [ausente],
      [O campo estava habilitado e ficou em branco. Este sim é o vazio que
       a estatística chama de dado faltante.],
    ),
    _caixa(
      [ignorado],
      [Alguém registrou, de forma explícita, que não sabe. É informação
       sobre o preenchimento, não ausência de informação.],
    ),
  )
]

// ---------------------------------------------------------------------------
// O protocolo que escolheu o modelo do curso. A figura ensina o desenho do
// estudo; o placar de validação, com todos os candidatos, vive no módulo 00.
#let _ano(rotulo, periodo, papel, destaque: false) = block(
  width: 100%,
  fill: if destaque { sapians-card-bg } else { sapians-paper },
  stroke: if destaque { stroke-accent } else { stroke-light },
  radius: radius-sm,
  inset: (x: 2.6mm, y: 2.2mm),
)[
  #text(size: 6.2pt, weight: "bold", tracking: 0.08em,
        fill: if destaque { sapians-terracotta } else { sapians-muted-dark })[#upper(rotulo)]
  #v(0.7mm)
  #text(size: 7.4pt, weight: "bold", fill: sapians-text-dark)[#periodo]
  #v(0.8mm)
  #text(size: 6.9pt, fill: sapians-muted-dark)[#papel]
]

#let fig-selecao() = block(width: 100%, breakable: false)[
  #grid(
    columns: (1fr, 7mm, 1fr, 9mm, 1fr),
    align: top,
    _ano([treino], [até 2022],
      [Os candidatos aprendem aqui. Seis famílias de modelo, cada uma buscada
       em configurações declaradas antes do estudo começar.]),
    _seta[],
    _ano([validação], [2023],
      [A escolha acontece aqui, e só aqui. Vence a maior área sob a curva;
       quem estiver a menos de um erro-padrão do líder vai a desempate.],
      destaque: true),
    align(center)[
      #v(2mm)
      #block(width: 0pt, height: 20mm,
             stroke: (left: (paint: sapians-terracotta, thickness: 1.1pt, dash: "dashed")))[]
    ],
    _ano([teste], [2024],
      [Lido uma única vez, depois de o vencedor já estar escolhido. Não podia
       mudar a decisão, e não mudou.]),
  )
  #v(2.2mm)
  #align(center)[#text(size: 6.4pt, fill: sapians-terracotta)[
    a barreira: a função que escolhe o modelo levanta uma exceção se enxergar o teste
  ]]
]
