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

O registro explícito da fonte reduz diferenças visuais entre ambientes.
O CI executa os cadernos na pilha fixada; não compara as figuras byte a byte
com os PNGs publicados. Uma comparação visual exige também a mesma fonte,
sua versão e as demais condições de renderização. Depender da instalação
do sistema pode introduzir diferenças:

- **Mac:** Inter e JetBrains Mono podem estar instaladas — ou não.
- **CI Linux / Colab:** sem registro explícito, o matplotlib pode selecionar
  DejaVu Sans quando a família solicitada não está instalada.
- **Qualquer um deles:** uma versão diferente da mesma família muda as
  métricas e move o texto por frações de pixel.

Empacotadas e registradas por caminho absoluto
(`font_manager.fontManager.addfont`, em `tools/sapians.py`), essas fontes
são selecionadas após retirar entradas concorrentes das famílias Inter e
JetBrains Mono da lista em memória. A mesma regra vale para Satoshi quando
uma instalação local é informada. A busca de fontes tem seu cache em memória
limpo; fontes e caches permanentes do sistema não são alterados.
Com o registro habilitado,
`SP.aplicar()` **falha alto** se algum arquivo empacotado sumir. Isso não
garante sozinho igualdade de pixels entre plataformas ou perfis.

Essa prioridade corrige um caso observado na vistoria: uma Inter-Medium.otf
instalada podia ser escolhida antes da Inter-Medium.ttf versionada, mesmo
após `addfont`. O SVG com texto nativo permanecia igual, enquanto os rótulos
do PNG mudavam. A reprodução com a fonte versionada recuperou os PNGs
publicados da PFI sem alterar os dados nem o estilo aprovado.

Custo: ~2,1 MB no repositório, uma vez. Os arquivos não mudam — se um dia
mudarem, é bump deliberado com re-execução de todos os cadernos, como
qualquer pin.

## Opção global com fonte local

O perfil Global / VITA permite uma instalação explícita de Satoshi e
registra a família usada. Seus arquivos não são redistribuídos aqui.
A lista de famílias do texto é `Satoshi, Inter`: a marca usa Satoshi,
enquanto símbolos ausentes nela, como Δ, φ e º, usam a Inter versionada.
Esse fallback por glifo segue o mecanismo de
[fontes do Matplotlib](https://matplotlib.org/stable/users/explain/fonts.html).
Sem Satoshi informada, a família do perfil é Inter.
A reprodução byte a byte das novas figuras exige a mesma opção; veja
o [contrato do perfil global](../README.md#perfil-global-sapians--vita).
O perfil histórico continua usando somente os arquivos OFL empacotados.

## A licença

A OFL 1.1 permite uso, modificação e redistribuição livres, desde que as
fontes não sejam vendidas isoladamente e **o texto da licença acompanhe os
arquivos** — é exatamente por isso que os dois `OFL-*.txt` moram aqui, ao
lado dos binários. A licença MIT do repositório **não** cobre este
diretório. Figuras (PNG/PDF) produzidas com as fontes não carregam
obrigação adicional.
