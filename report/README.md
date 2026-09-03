# report/ — o relatório do curso (módulos 00 a 05)

`relatorio-00-05.pdf` é o relatório de disciplina de **SCC5819 — Interpretable
Machine Learning** (ICMC-USP, Prof. André C. P. L. F. de Carvalho), escrito por
William Bendinelli. Ele explica o **modelo do curso** — o XGBoost de óbito por
COVID do [módulo 00](../modules/00-dataset/) — com os cinco métodos locais dos
módulos 01 a 05, sob a forma "um paciente, cinco perguntas": o mesmo `gold_id`
atravessa ceteris paribus, ICE, LIME, contrafactuais e SHAP, e cada método é
julgado por uma pergunta clínica que deveria responder.

Dois fios atravessam o texto: as **cercas** (a ficha do SIVEP desliga campos
condicionalmente, então perturbar features de forma independente fabrica
pacientes que não podem existir — e nesta base a conta é derivável) e a
**deriva de regime** (o modelo aprendeu letalidades de 2020–2022 e prevê num
mundo de 2024).

## Arquivos

| Arquivo | O que é |
|---|---|
| `main.typ` | a fonte, em Typst, sobre o pacote local `sapians:0.1.0` |
| `references.bib` | as referências citadas, copiadas dos READMEs dos módulos |
| `check_numbers_exempt.txt` | as isenções do teste de números, uma por linha, com o motivo |
| `relatorio-00-05.pdf` | o artefato compilado — datado de **2026-09-02** |

As figuras **não são copiadas** para cá: o `.typ` referencia os PNG e SVG
commitados dos módulos por caminho absoluto à raiz do repositório
(`/modules/03-lime/figures/...`), que é o que o `--root .` da compilação
resolve. Mover ou regerar uma figura de módulo muda o relatório na próxima
compilação — por construção.

## Como compilar

Da **raiz do repositório**:

```bash
typst compile --root . --font-path tools/fonts report/main.typ report/relatorio-00-05.pdf
```

O `--font-path tools/fonts` é obrigatório: o corpo do texto é Inter e o
monoespaçado é JetBrains Mono, ambos vindos de `tools/fonts/` (não do sistema).
Sem ele o Typst cai em outra família e a paginação muda. Para conferir que a
fonte foi encontrada:

```bash
typst fonts --font-path tools/fonts | grep -i inter
```

O pacote de estilo é o `sapians` instalado no cache local do Typst
(`~/Library/Application Support/typst/packages/local/sapians/0.1.0`), fonte em
`~/Documents/sapians-latex/packages/typst/`. Sem ele o import falha.

## A regra de evidência, e como re-checá-la

Vale aqui a regra dura do [CLAUDE.md](../CLAUDE.md): **todo número em prosa é
impresso por uma célula de caderno versionada**, e — porque este texto vive
fora dos módulos — a sentença ou a legenda que carrega o número **nomeia o
módulo** de origem, na forma `(módulo 03, walkthrough §4)` ou
`(módulo 00, MODEL.md)`. O ponteiro precisa estar na mesma linha da fonte, ou a
até duas linhas dela.

O teste de aceitação:

```bash
python3 tools/check_numbers.py --prose report/main.typ \
  --exempt report/check_numbers_exempt.txt
```

Ele tem de terminar com `MISS/SEM-PONTEIRO 0`. `MISS` é número apontado que
nenhuma célula daquele módulo imprime; `SEM-PONTEIRO` é número sem módulo
declarado por perto. Os dois são bug: ou a célula existe e o ponteiro entra, ou
o número sai da prosa.

`check_numbers_exempt.txt` **não é um silenciador**: é registro de decisão, uma
linha por token (`<token-cru><TAB><motivo>`). As categorias usadas aqui são as
três legítimas para um texto como este:

- **valor antigo preservado pela regra 3** da barra de evidência — o relatório
  cita, em §10, medições que a re-sincronização derrubou, e nenhuma célula
  atual as imprime;
- **número de documento gerado** do módulo 00 (`COLUMNS.md`) que não passa por
  célula;
- **número da literatura citada**, reproduzido do `GOLD.md` (decisão 3) — é
  medição do artigo, não nossa.

## O PDF é um artefato datado

`relatorio-00-05.pdf` é o relatório como entregue em **2026-09-02**, sobre o
modelo do curso adotado em 2026-09-01 (800 árvores, profundidade 4, lr 0,05) e
sobre o paciente que a regra escolhe nele (`gold_id` 1276776). Recompilar sobre
módulos alterados produz outro documento: se os números dos cadernos mudarem, o
caminho é re-rodar o `check_numbers.py`, corrigir a prosa e registrar o valor
antigo — nunca trocar dígitos em silêncio.
