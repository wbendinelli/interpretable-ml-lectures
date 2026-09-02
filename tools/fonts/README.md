# tools/fonts/ — as fontes empacotadas

Seis arquivos `.ttf` estáticos e as duas licenças que precisam viajar
junto. Nada aqui é código do repositório: são binários de terceiros,
redistribuídos sob a **SIL Open Font License 1.1**.

## Procedência

Copiados verbatim de
[`sapians-latex`](https://github.com/wbendinelli/sapians-latex) —
`assets/fonts/`, commit `4c10f27` (os dois `OFL-*.txt` vieram de `e76f190`
da mesma árvore, onde moram ao lado dos binários; os `.ttf` são
byte-idênticos nos dois commits, conferido por `shasum -a 256`).

| Arquivo | Família | Versão | Upstream | Licença |
|---|---|---|---|---|
| `Inter-Regular.ttf` | Inter | 4.000 (`git-a52131595`) | [rsms/inter](https://github.com/rsms/inter) | [`OFL-Inter.txt`](OFL-Inter.txt) |
| `Inter-Medium.ttf` | Inter | 4.000 | rsms/inter | `OFL-Inter.txt` |
| `Inter-SemiBold.ttf` | Inter | 4.000 | rsms/inter | `OFL-Inter.txt` |
| `Inter-Bold.ttf` | Inter | 4.000 | rsms/inter | `OFL-Inter.txt` |
| `JetBrainsMono-Regular.ttf` | JetBrains Mono | 2.304 | [JetBrains/JetBrainsMono](https://github.com/JetBrains/JetBrainsMono) | [`OFL-JetBrainsMono.txt`](OFL-JetBrainsMono.txt) |
| `JetBrainsMono-Bold.ttf` | JetBrains Mono | 2.304 | JetBrains/JetBrainsMono | `OFL-JetBrainsMono.txt` |

São os **estáticos**, não a fonte variável (`InterVariable.ttf`): o
`font_manager` do matplotlib resolve pesos por arquivo, e um `.ttf`
variável registra um peso só — o que faria `fontweight="bold"` cair
silenciosamente no Regular. Quatro pesos de Inter (400/500/600/700) cobrem
o que o estilo pede: corpo, rótulo de eixo (`axes.labelweight: medium`),
kicker e título. Dois de JetBrains Mono cobrem código e tabelas
monoespaçadas.

## Por que empacotadas, e não instaladas

Porque o número precisa ser conferível e a figura precisa ser a mesma em
todo lugar. As figuras dos cadernos são comparadas byte a byte entre o Mac
do autor, o runner Linux do CI e o Colab (CLAUDE.md, dever 3). Uma fonte
resolvida pelo sistema quebra isso de três jeitos:

- **Mac:** Inter e JetBrains Mono podem estar instaladas — ou não.
- **CI Linux / Colab:** não estão. O matplotlib cai no fallback DejaVu Sans
  sem erro nenhum, e o PNG muda em cada glifo.
- **Qualquer um deles:** uma versão diferente da mesma família muda as
  métricas e move o texto por frações de pixel.

Empacotadas e registradas por caminho absoluto
(`font_manager.fontManager.addfont`, em `tools/sapians.py`), a fonte é a
mesma nos três ambientes e `SP.aplicar()` **falha alto** se algum arquivo
sumir, em vez de degradar em silêncio para o DejaVu.

Custo: ~2,1 MB no repositório, uma vez. Os arquivos não mudam — se um dia
mudarem, é bump deliberado com re-execução de todos os cadernos, como
qualquer pin.

## A licença

A OFL 1.1 permite uso, modificação e redistribuição livres, desde que as
fontes não sejam vendidas isoladamente e **o texto da licença acompanhe os
arquivos** — é exatamente por isso que os dois `OFL-*.txt` moram aqui, ao
lado dos binários. A licença MIT do repositório **não** cobre este
diretório. Figuras (PNG/PDF) produzidas com as fontes não carregam
obrigação adicional.
