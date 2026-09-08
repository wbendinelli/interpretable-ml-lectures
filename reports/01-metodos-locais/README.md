# reports/01-metodos-locais/ — o relatório do curso (módulos 00 a 05)

`relatorio-00-05.pdf` é o relatório de disciplina de **SCC5819 — Interpretable
Machine Learning** (ICMC-USP, Prof. André C. P. L. F. de Carvalho), escrito por
William Bendinelli. Ele explica o **modelo do curso** — o XGBoost de óbito por
COVID do [módulo 00](../../modules/00-dataset/) — com os cinco métodos locais dos
módulos 01 a 05, sob a forma "um paciente, cinco perguntas": o mesmo `gold_id`
atravessa ceteris paribus, ICE, LIME, contrafactuais e SHAP, e cada método é
julgado por uma pergunta clínica que deveria responder.

Dois fatos organizam o texto. O primeiro: a ficha do SIVEP desliga campos, e
por isso mexer numa variável de cada vez produz fichas que o formulário não
permitiria — nesta base essa quantidade é contada, não estimada. O segundo: o
modelo aprendeu com os anos em que se morria muito mais e prevê num mundo em
que se morre menos, e a mesma queda reaparece nos cinco métodos.

O texto é escrito para **ensinar**, não para provar: nenhum termo aparece antes
da frase que o define, cada parágrafo carrega uma afirmação e a consequência
dela, e os ponteiros de módulo vivem em nota de rodapé em vez de dentro da
frase.

## Arquivos

| Arquivo | O que é |
|---|---|
| `main.typ` | a fonte, em Typst, sobre `@preview/sapians:0.3.0` |
| `figuras.typ` | os dois diagramas desenhados no próprio Typst: o funil da §3 e o protocolo de seleção da §2 |
| `references.bib` | as referências citadas, copiadas dos READMEs dos módulos |
| `gerar_figuras.py` | regera as sete figuras de medição: roda os cinco walkthroughs fora da árvore com `SAPIANS_ESCALA_TEXTO` e recorta o cabeçalho (ver `figuras/README.md`) |
| `recortar_figuras.py` | a detecção do cabeçalho, importada por `gerar_figuras.py`; não rode sozinho depois dele |
| `figuras/` | as sete PNG derivadas que o `main.typ` referencia |
| `check_numbers_exempt.txt` | as isenções do teste de números, uma por linha, com o motivo |
| `relatorio-00-05.pdf` | o artefato compilado — datado de **2026-09-08** |

Os **diagramas** (o funil da §3 e o protocolo de seleção da §2) são desenhados em
Typst em `figuras.typ`, e não em SVG: os SVGs de módulo foram feitos para o
README, em Georgia serifada sobre fundo bege, e entravam na página como um
retângulo de outra tipografia. Regra adotada: nenhum número dentro do desenho —
a figura ensina o mecanismo, os números ficam na prosa.

As figuras de **medição** são cópias derivadas em `figuras/`, produzidas por
`gerar_figuras.py`: o script roda os cinco walkthroughs de novo, fora da árvore
do git, com `SAPIANS_ESCALA_TEXTO` (1,5; 1,35 nos cadernos 01 e 05, onde 1,5 não
cabe), para que o rótulo de eixo continue legível depois que o Typst encolhe a
figura para os 170 mm da coluna, e recorta o cabeçalho (kicker e manchete), que
a legenda do artigo já faz. Uma delas, a dependência do SHAP, fica na escala do
caderno, porque o rótulo da barra de cor não cabe no canvas em escala maior. Os
cadernos e `modules/*/figures/` não mudam. Regerar uma figura de módulo só
aparece aqui depois de rodar o script de novo — ver `figuras/README.md`.

## Como compilar

Da **raiz do repositório**:

```bash
typst compile --root . --font-path tools/fonts \
  reports/01-metodos-locais/main.typ \
  reports/01-metodos-locais/relatorio-00-05.pdf
```

O `--font-path tools/fonts` é obrigatório: o corpo do texto é Inter e o
monoespaçado é JetBrains Mono, ambos vindos de `tools/fonts/` (não do sistema).
Sem ele o Typst cai em outra família e a paginação muda. Para conferir que a
fonte foi encontrada:

```bash
typst fonts --font-path tools/fonts | grep -i inter
```

O pacote de estilo é o `sapians` 0.3.0, em
`~/Library/Application Support/typst/packages/preview/sapians/0.3.0`. A versão
0.1.0 não serve: ela fixa "SAPIANS RESEARCH ARTICLE" no cabeçalho e um nome de
periódico no rodapé, sem parâmetro. A 0.3.0 expõe `kicker`, `journal`, `lang`,
`abstract-title` e `keywords-title`, que é o que põe a disciplina no topo.

## A regra de evidência, e como re-checá-la

Vale aqui a regra dura do [CLAUDE.md](../../CLAUDE.md): **todo número em prosa é
impresso por uma célula de caderno versionada**, e — porque este texto vive
fora dos módulos — a sentença ou a legenda que carrega o número **nomeia o
módulo** de origem, na forma `(módulo 03, walkthrough §4)` ou
`(módulo 00, MODEL.md)`. O ponteiro precisa estar na mesma linha da fonte, ou a
até duas linhas dela.

Desde a reescrita de 2026-09-03 esse ponteiro vive numa **nota de rodapé**, e
não no corpo da frase:

```typ
a ficção chega a 30,6% dos vizinhos.#footnote[Módulo 03, walkthrough §4.]
```

Funciona porque o verificador lê o **fonte**, onde "módulo 03" continua na mesma
linha, e o leitor lê o **PDF**, onde a frase está limpa. Atenção a uma armadilha
real: se a quebra de linha separar `Módulo` de `03`, o casamento falha e o
número reprova mesmo estando documentado. Mantenha os dois na mesma linha.

O teste de aceitação:

```bash
python3 tools/check_numbers.py \
  --prose reports/01-metodos-locais/main.typ \
  --exempt reports/01-metodos-locais/check_numbers_exempt.txt
```

Ele tem de terminar com `MISS/SEM-PONTEIRO 0`. `MISS` é número apontado que
nenhuma célula daquele módulo imprime; `SEM-PONTEIRO` é número sem módulo
declarado por perto. Os dois são bug: ou a célula existe e o ponteiro entra, ou
o número sai da prosa.

`check_numbers_exempt.txt` **não é um silenciador**: é registro de decisão, uma
linha por token (`<token-cru><TAB><motivo>`). Hoje ele está **vazio**, e isso é
um resultado: a versão anterior precisava de 11 isenções, e a reescrita
didática cortou a prosa que as carregava. Todos os números do relatório são
impressos por célula, sem exceção.

Há três lugares para o ponteiro, e a ordem de preferência é esta: **dentro da
frase**, quando ele cabe sem soar burocrático ("o paciente que a regra do
módulo 00 escolhe"); numa **nota de rodapé**, quando a nota tem algo a dizer
sobre o que a célula mediu; e em lugar nenhum, quando o número sai junto. Uma
nota que só diz `Módulo 00, MODEL.md.` é endereço, não escrita: nesse caso o
número não estava ganhando o espaço dele.

## O PDF é um artefato datado

`relatorio-00-05.pdf` é o relatório como recompilado em **2026-09-08**, depois da
revisão da junta (as versões de 2026-09-03 e 2026-09-04 vivem no histórico do
git), sobre o
modelo do curso adotado em 2026-09-01 (800 árvores, profundidade 4, lr 0,05) e
sobre o paciente que a regra escolhe nele (`gold_id` 1276776). Recompilar sobre
módulos alterados produz outro documento: se os números dos cadernos mudarem, o
caminho é re-rodar o `check_numbers.py`, corrigir a prosa e registrar o valor
antigo — nunca trocar dígitos em silêncio.
