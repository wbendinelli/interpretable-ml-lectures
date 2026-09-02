#!/usr/bin/env python3
"""check_numbers.py — teste de aceitação da regra dura do CLAUDE.md:

    "Todo número citado na prosa é impresso por uma célula de caderno
    versionada, no mesmo módulo."

Um número sem célula que o imprima é bug: ou a célula existe, ou o número
sai da prosa. Este script varre a prosa de um módulo (README.md e
lecture/outline.md, opcionalmente as células markdown dos próprios
cadernos) atrás de tokens numéricos e verifica se cada um aparece na saída
de alguma célula de código — o "palheiro" — nos dois níveis previstos:

    Tier L (local)  — cadernos do PRÓPRIO módulo (modules/NN-slug/notebooks/).
                       É o caso normal: toda medição vive ao lado da prosa
                       que a cita.
    Tier M (módulo apontado) — cadernos de um módulo IRMÃO, consultados
                       SOMENTE quando a prosa, a até 2 linhas do token,
                       nomeia esse módulo ("módulo 00", "módulo 03" etc.).
                       Sem o ponteiro textual, um valor que por acaso bate
                       com a saída de outro módulo não conta — é bug, não
                       coincidência abençoada. Use --tier-m-report para
                       auditar esses quase-acertos por módulo antes de
                       decidir se merecem virar ponteiro explícito na prosa
                       ou entrar na lista de isenções.

Um número que não bate em nenhum dos dois tiers é MISS. Um token pode
escapar do MISS de duas formas: batendo em algum dos tiers, ou estando
listado no arquivo de isenções do módulo — que não é um silenciador
genérico, é um registro de decisão. As categorias legítimas de isenção
são:

    - valor ANTIGO preservado pela regra 3 da barra de evidência
      (CONTRIBUTING.md): quando uma medição corrige a prosa, o valor
      velho fica registrado como "corrigido", não apagado — e nenhuma
      célula atual o imprime mais.
    - constante de configuração do módulo 00 (ex.: n_estimators=800,
      learning_rate=0,05): decidida e medida em modules/00-dataset/
      SELECTION.md ou MODEL.md, citada aqui só para lembrar a config —
      não é uma medição deste módulo.
    - aritmética de prosa: uma conta feita a partir de dois números que a
      própria prosa já cita e que estão, esses sim, impressos em célula
      (ex.: "39 = 40 − 1", com o 40 impresso alhures).
    - anotação de tempo de execução do caderno (ex.: "~20 s"): a política
      do repositório proíbe %%time/%time (saída precisa ser
      determinística), então não existe nem pode existir célula que
      imprima esse número.

Formato do arquivo de isenções (uma decisão por linha, tabulação entre
campos):

    <token-cru><TAB><motivo>

Comentários começam com "#". O arquivo default de um módulo é
tools/check_numbers_exempt/<nome-do-módulo>.txt (ex.: 03-lime.txt); passe
--exempt para apontar outro.

Extração do palheiro (saídas de célula de código): os cadernos deste
curso alternam entre formatação em inglês (ponto decimal, vírgula de
milhar: "0.7644", "1,282,970") e em português (vírgula decimal, ponto de
milhar: "0,7644", "1.282.970", "37,3%", "1,05×10⁻⁵"). O extrator lê as
duas convenções ao mesmo tempo — ver _core_readings() e
extract_output_numbers() — sem exigir que o módulo escolha uma.

Uso:
    python3 tools/check_numbers.py modules/03-lime [--markdown-cells]
    python3 tools/check_numbers.py modules/03-lime --exempt outro.txt
    python3 tools/check_numbers.py --tier-m-report modules/01-* modules/02-*
    python3 tools/check_numbers.py --dump modules/03-lime/notebooks/lime_walkthrough.ipynb
    python3 tools/check_numbers.py --self-test

Só stdlib, Python 3.12+. Rodado à mão — não é hook de pre-commit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

# --------------------------------------------------------------------------
# Extração de tokens da prosa (README.md / lecture/outline.md)
# --------------------------------------------------------------------------

# Token numérico em PT-BR: milhar separado por '.', decimal por ',' opcional.
_TOKEN_RE = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?")

_ISO_DATE_RE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
_DMY_DATE_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_URL_RE = re.compile(r"https?://\S+")
_DISPLAY_MATH_RE = re.compile(r"\$\$.*?\$\$", re.DOTALL)
_INLINE_MATH_RE = re.compile(r"\$[^$\n]+\$")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
# Abreviação de intervalo de anos, ex. "2023–24": apaga o trecho INTEIRO
# (ano-prefixo + traço + sufixo de 2 dígitos) antes de tokenizar. Apagar só
# o ano-prefixo (casando pelo sufixo isolado, como _YEAR_RANGE_SUFFIX_RE
# fazia sozinho) deixaria o "24" solto, e a regex principal o pegaria como
# uma citação numérica espúria.
_YEAR_RANGE_RE = re.compile(r"\b(?:19|20)\d\d[–-]\d\d\b")
_YEAR_RANGE_SUFFIX_RE = re.compile(r"^[–-]\d\d(?!\d)")
_SECTION_MARK_RE = re.compile(r"§\s*\d+")
_CAP_MARK_RE = re.compile(r"\bcap\.\s*\d+", re.IGNORECASE)
_MIN_SUFFIX_RE = re.compile(r"^\s*min\b", re.IGNORECASE)


def _strip_noise(text: str) -> str:
    """Remove código (cercado/inline), URLs, matemática, comentários HTML e
    datas ISO/DMY antes de tokenizar. A numeração de heading é tratada por
    linha (ver _strip_heading_numbering) porque o resto do heading ainda
    deve ser varrido."""
    text = _FENCED_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _HTML_COMMENT_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _DISPLAY_MATH_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _INLINE_MATH_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _URL_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _ISO_DATE_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _DMY_DATE_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _YEAR_RANGE_RE.sub(lambda m: " " * len(m.group(0)), text)
    return text


@dataclass
class ProseToken:
    raw: str
    value: float
    decimals: int
    line_no: int  # 1-based
    line_text: str
    # Preenchido só por extract_markdown_cell_tokens: se um ponteiro
    # "módulo 0N" está a +-2 linhas *dentro do texto daquela própria
    # célula markdown*.
    near_module00_pointer: bool = False
    pointed: set = field(default_factory=set)


def _strip_heading_numbering(line: str) -> str:
    """Em linhas '^#{1,6} ', apaga só os dígitos de numeração de seção no
    início do texto do heading (ex.: '## 3.2 Foo' -> '## Foo'), mantendo
    o resto do heading intacto."""
    m = _HEADING_RE.match(line)
    if not m:
        return line
    hashes, rest = m.group(1), m.group(2)
    num_m = re.match(r"^[\d.\)]+(\s+)", rest)
    if num_m:
        rest = " " * len(num_m.group(0)) + rest[len(num_m.group(0)) :]
    return f"{hashes} {rest}"


def extract_prose_tokens(text: str) -> list[ProseToken]:
    """Extrai tokens numéricos em formato PT-BR do texto de prosa,
    aplicando as regras de exclusão (anos, inteiros pequenos, abreviação de
    intervalo de anos, marcadores de seção/capítulo, contagens de minuto)."""
    tokens: list[ProseToken] = []
    cleaned = _strip_noise(text)
    lines = cleaned.split("\n")
    for line_idx, line in enumerate(lines, start=1):
        proc_line = _strip_heading_numbering(line)
        for m in _TOKEN_RE.finditer(proc_line):
            raw = m.group(0)
            int_part = m.group(1)
            dec_part = m.group(2)

            # Pula tokens dentro de marcadores §N / cap. N.
            span_start, span_end = m.start(), m.end()
            skip = False
            for marker_re in (_SECTION_MARK_RE, _CAP_MARK_RE):
                for mm in marker_re.finditer(proc_line):
                    if mm.start() <= span_start < mm.end():
                        skip = True
                        break
                if skip:
                    break
            if skip:
                continue

            # Pula "\d+ min" (contagens de minuto, tipo tempo-percentual).
            after = proc_line[span_end:]
            if dec_part is None and _MIN_SUFFIX_RE.match(after):
                continue

            # Pula abreviação de intervalo de anos (token seguido de –NN
            # ou -NN, ex. 2023–24).
            if _YEAR_RANGE_SUFFIX_RE.match(after):
                continue

            # Normaliza o valor.
            int_clean = int_part.replace(".", "")
            if dec_part is not None:
                value = float(f"{int_clean}.{dec_part}")
                decimals = len(dec_part)
            else:
                value = float(int_clean)
                decimals = 0

            # Pula anos soltos 1900-2100 (só quando o token inteiro, sem
            # parte decimal, é um ano de 4 dígitos).
            if (
                dec_part is None
                and re.fullmatch(r"\d{4}", int_part)
                and 1900 <= value <= 2100
            ):
                continue

            # Pula inteiros soltos <= 12 (contagens de capítulo/seção) —
            # só se aplica a inteiros sem separador de milhar/decimal.
            if dec_part is None and "." not in int_part and value <= 12:
                continue

            tokens.append(ProseToken(raw, value, decimals, line_idx, line.rstrip("\n")))
    return tokens


def extract_markdown_cell_tokens(nb_path: Path) -> list[ProseToken]:
    """Extração consultiva: células markdown de um caderno, marcadas com o
    arquivo de origem para o relatório. O ponteiro módulo-00 é checado só
    dentro do texto de cada célula (um ponteiro em outra célula não conta)."""
    try:
        nb = json.loads(nb_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    tokens: list[ProseToken] = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        src = cell.get("source", "")
        text = "".join(src) if isinstance(src, list) else src
        cell_lines = text.split("\n")
        for tok in extract_prose_tokens(text):
            tok.pointed = pointed_modules(cell_lines, tok.line_no)
            tok.near_module00_pointer = bool(tok.pointed)
            tokens.append(tok)
    return tokens


# --------------------------------------------------------------------------
# Palheiro (números nas saídas de célula de código)
# --------------------------------------------------------------------------

# Núcleo de um token numérico: grupos de dígitos separados por '.' ou ',',
# em qualquer combinação — cobre tanto "1.282.970" / "0,7644" (PT) quanto
# "1,282,970" / "0.7644" (EN) no mesmo regex; a convenção é decidida
# depois, token a token, em _core_readings().
_CORE_RE = re.compile(r"-?\d+(?:[.,]\d+)*")
#  Usadas só com .match(text, pos) para casar exatamente a partir de uma
#  posição no meio da string — sem "^", que em modo não-MULTILINE âncora
#  no início absoluto da string (posição 0), não em `pos`.
_SCI_E_RE = re.compile(r"[eE][-+]?\d+")
_SUPERSCRIPT_TRANS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_SCI_UNI_RE = re.compile(r"\s*[×xX]\s*10\s*([⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹]+)")
_PERCENT_RE = re.compile(r"\s*%")


def _core_readings(core: str) -> list[float]:
    """Todas as leituras plausíveis de um núcleo "dígitos e separadores"
    (sem sinal, sem expoente, sem %), tentando as duas convenções:

        EN: vírgula de milhar, ponto decimal.
        PT: ponto de milhar, vírgula decimal.

    Um grupo de milhar tem SEMPRE 3 dígitos; é isso que desambigua "1.234"
    (um separador, grupo de 3 -> pode ser decimal OU milhar: as duas
    leituras voltam) de "0,7644" (um separador, grupo de 4 -> só decimal)
    e de "1.282.970" / "1,282,970" (2+ grupos, todos de 3 -> só milhar).
    "1.234,5" (separadores mistos, milhar seguido de decimal final) casa
    inequivocamente com 1234.5."""
    segs = re.split(r"([.,])", core)
    groups = segs[0::2]
    seps = segs[1::2]

    if not seps:
        return [float(core)]

    if len(seps) == 1:
        left, right = groups
        if len(right) == 3:
            # Ambíguo: decimal (leitura literal) ou grupo único de milhar.
            return [float(f"{left}.{right}"), float(left + right)]
        return [float(f"{left}.{right}")]

    # 2+ separadores.
    if len(set(seps)) == 1 and all(len(g) == 3 for g in groups[1:]):
        # Separador uniforme, todo grupo depois do primeiro com 3 dígitos:
        # milhar sem ambiguidade (PT ponto-milhar ou EN vírgula-milhar).
        return [float("".join(groups))]

    if (
        all(len(g) == 3 for g in groups[1:-1])
        and seps[:-1].count(seps[0]) == len(seps) - 1
    ):
        # Separadores mistos: grupos de milhar (3 dígitos) seguidos de um
        # grupo decimal final de tamanho livre, ex. "1.234,5" / "1,234.5".
        int_part = "".join(groups[:-1])
        return [float(f"{int_part}.{groups[-1]}")]

    # Não deveria ocorrer em saída de caderno bem formada; melhor esforço,
    # tratando todo separador como marca de milhar.
    return [float("".join(groups))]


@dataclass
class HaystackValue:
    value: float
    cell_index: int
    source: str  # texto original casado, para exibir como evidência


def _joined(value) -> str:
    if isinstance(value, list):
        return "".join(value)
    if isinstance(value, str):
        return value
    return ""


def _iter_output_texts(nb: dict):
    """Gera (índice-da-célula, texto) para cada blob de saída de célula de
    código."""
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        for out in cell.get("outputs", []):
            out_type = out.get("output_type")
            text = ""
            if out_type == "stream":
                text = _joined(out.get("text", ""))
            elif out_type in ("execute_result", "display_data"):
                data = out.get("data", {})
                if "text/plain" in data:
                    text = _joined(data["text/plain"])
                else:
                    continue
            elif out_type == "error":
                text = f"{out.get('ename', '')}: {out.get('evalue', '')}"
            else:
                continue
            if text:
                yield idx, text


def _iter_haystack_tokens(text: str):
    """Varre `text` da esquerda pra direita e gera (raw, [valores]) para
    cada token numérico — inclusive as leituras derivadas (mantissa de
    notação científica, leitura em fração de percentual, leitura em milhar
    de um grupo ambíguo). Consome o sufixo científico/percentual junto do
    núcleo para não deixar seus dígitos (o "10" do "×10⁻⁵", o "05" do
    "e-05") serem recasados como tokens à parte."""
    pos = 0
    for m in _CORE_RE.finditer(text):
        if m.start() < pos:
            continue
        core = m.group(0)
        end = m.end()
        raw_end = end

        sign = -1.0 if core.startswith("-") else 1.0
        body = core.removeprefix("-")
        readings = [sign * r for r in _core_readings(body)]

        exp = None
        sci_uni_m = _SCI_UNI_RE.match(text, end)
        if sci_uni_m:
            try:
                exp = int(sci_uni_m.group(1).translate(_SUPERSCRIPT_TRANS))
            except ValueError:
                exp = None
            else:
                raw_end = sci_uni_m.end()
        else:
            sci_e_m = _SCI_E_RE.match(text, end)
            if sci_e_m:
                exp = int(sci_e_m.group(0)[1:])
                raw_end = sci_e_m.end()

        is_percent = False
        pct_m = _PERCENT_RE.match(text, raw_end)
        if pct_m:
            is_percent = True
            raw_end = pct_m.end()

        values: list[float] = []
        if exp is not None:
            values.extend(r * (10.0**exp) for r in readings)
            values.extend(readings)  # mantissa preservada como leitura própria
        elif is_percent:
            for r in readings:
                values.append(r)
                values.append(r / 100.0)
        else:
            values.extend(readings)

        pos = raw_end
        yield text[m.start() : raw_end], values


def extract_output_numbers(nb_path: Path) -> list[HaystackValue]:
    """Extrai todos os valores numéricos das saídas de célula de código de
    um caderno, incluindo as leituras derivadas (mantissa, milhar, fração
    percentual — ver _iter_haystack_tokens)."""
    try:
        nb = json.loads(nb_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    values: list[HaystackValue] = []
    for cell_idx, text in _iter_output_texts(nb):
        for raw, readings in _iter_haystack_tokens(text):
            for v in readings:
                values.append(HaystackValue(abs(v), cell_idx, raw))
    return values


# --------------------------------------------------------------------------
# Casamento
# --------------------------------------------------------------------------


def _quantize_eq(o: float, v: float, d: int) -> bool:
    try:
        q = Decimal(str(o)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    except (ArithmeticError, ValueError):
        return False
    return q == Decimal(str(v))


def match(v: float, d: int, haystack: list[HaystackValue]) -> HaystackValue | None:
    """Devolve o primeiro valor do palheiro que casa com o token de prosa
    (v, d) sob alguma das regras 7-10, ou None."""
    for hv in haystack:
        o = hv.value
        # Regra 7: casamento por arredondamento.
        if _quantize_eq(o, v, d):
            return hv
        # Regra 8: idem com o*100 (prosa em %, célula em fração).
        if _quantize_eq(o * 100, v, d):
            return hv
        # Regra 9: folga de representação em ponto flutuante.
        if abs(o - v) <= 0.6 * (10**-d):
            return hv
        if abs(o * 100 - v) <= 0.6 * (10**-d):
            return hv
        # Regra 10: para d == 0, também casa por conversão para inteiro.
        if d == 0:
            try:
                if int(o) == int(v):
                    return hv
            except (ValueError, OverflowError):
                pass
            try:
                if int(o * 100) == int(v):
                    return hv
            except (ValueError, OverflowError):
                pass
    return None


# --------------------------------------------------------------------------
# Arquivo de isenções
# --------------------------------------------------------------------------


def load_exemptions(path: Path) -> dict[str, str]:
    exemptions: dict[str, str] = {}
    if not path.exists():
        return exemptions
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2:
            raw, reason = parts
        else:
            raw, reason = parts[0].strip(), ""
        exemptions[raw.strip()] = reason.strip()
    return exemptions


# --------------------------------------------------------------------------
# Ponteiro "módulo 0N" na prosa (tier M)
# --------------------------------------------------------------------------

_MODULO_RE = re.compile(r"m[oó]dulo\s*(0\d)\b", re.IGNORECASE)


def pointed_modules(all_lines: list[str], line_no: int) -> set[str]:
    """Números de módulo ("00".."05") citados a +-2 linhas de line_no
    (1-based)."""
    lo = max(1, line_no - 2)
    hi = min(len(all_lines), line_no + 2)
    found: set[str] = set()
    for i in range(lo, hi + 1):
        found.update(m.group(1) for m in _MODULO_RE.finditer(all_lines[i - 1]))
    return found


# --------------------------------------------------------------------------
# Processamento por arquivo
# --------------------------------------------------------------------------


@dataclass
class Row:
    line: int
    raw: str
    verdict: str
    evidence: str


@dataclass
class FileResult:
    path: Path
    rows: list[Row] = field(default_factory=list)


def match_pointed(v: float, d: int, pointed: set, haystacks: dict) -> tuple:
    """Busca só nos módulos irmãos que a prosa aponta. Devolve (hit, módulo)."""
    for num in sorted(pointed):
        hit = match(v, d, haystacks.get(num, []))
        if hit is not None:
            return hit, num
    return None, None


def process_prose_file(
    path: Path,
    haystack_l: list[HaystackValue],
    haystack_m: list[HaystackValue],
    exemptions: dict[str, str],
) -> FileResult:
    text = path.read_text(encoding="utf-8")
    all_lines = text.split("\n")
    tokens = extract_prose_tokens(text)
    result = FileResult(path)

    for tok in tokens:
        if tok.raw in exemptions:
            result.rows.append(Row(tok.line_no, tok.raw, "EXEMPT", exemptions[tok.raw]))
            continue

        hit_l = match(tok.value, tok.decimals, haystack_l)
        if hit_l is not None:
            evidence = f"{hit_l.source} [c{hit_l.cell_index}]"
            result.rows.append(Row(tok.line_no, tok.raw, "OK-L", evidence))
            continue

        # Regra 3: o tier M só é consultado quando um ponteiro "módulo 00"
        # está a +-2 linhas do token. Sem ponteiro, o tier M nem é
        # pesquisado no modo normal (um token cujo valor por acaso bate com
        # uma saída do módulo 00, mas não carrega ponteiro, é MISS aqui —
        # --tier-m-report expõe esses casos à parte como diagnóstico).
        pointed = pointed_modules(all_lines, tok.line_no)
        if pointed:
            hit_m, num = match_pointed(tok.value, tok.decimals, pointed, haystack_m)
            if hit_m is not None:
                evidence = f"{hit_m.source} [c{hit_m.cell_index}] (módulo {num})"
                result.rows.append(Row(tok.line_no, tok.raw, "OK-M", evidence))
                continue
        result.rows.append(Row(tok.line_no, tok.raw, "MISS", ""))

    return result


# --------------------------------------------------------------------------
# Condutor
# --------------------------------------------------------------------------


def collect_haystack(nb_dir: Path) -> list[HaystackValue]:
    values: list[HaystackValue] = []
    if not nb_dir.exists():
        return values
    for nb_path in sorted(nb_dir.glob("*.ipynb")):
        values.extend(extract_output_numbers(nb_path))
    return values


def print_table(file_results: list[FileResult]) -> tuple[int, int, int, int]:
    ok_l = ok_m = exempt = miss = 0
    for fr in file_results:
        if not fr.rows:
            continue
        print(f"\n== {fr.path} ==")
        print(f"{'line':>5}  {'raw':<12} {'verdict':<18} evidence")
        for row in fr.rows:
            print(f"{row.line:>5}  {row.raw:<12} {row.verdict:<18} {row.evidence}")
            if row.verdict == "OK-L":
                ok_l += 1
            elif row.verdict == "OK-M":
                ok_m += 1
            elif row.verdict == "EXEMPT":
                exempt += 1
            elif row.verdict in ("MISS", "M-WITHOUT-POINTER"):
                miss += 1
    return ok_l, ok_m, exempt, miss


def collect_sibling_haystacks(module_dir: Path) -> dict:
    """{ "00": [...], "01": [...], ... } para cada módulo irmão
    modules/NN-* de module_dir, exceto ele mesmo."""
    out: dict = {}
    for d in sorted(module_dir.resolve().parent.glob("[0-9][0-9]-*")):
        if d.resolve() == module_dir.resolve():
            continue
        out[d.name[:2]] = collect_haystack(d / "notebooks")
    return out


def default_exempt_path(module_name: str) -> Path:
    return Path(__file__).parent / "check_numbers_exempt" / f"{module_name}.txt"


def run_module(module_dir: Path, markdown_cells: bool, exempt_file: Path | None) -> int:
    module_name = module_dir.name
    nb_dir = module_dir / "notebooks"
    haystack_l = collect_haystack(nb_dir)
    haystack_m = collect_sibling_haystacks(module_dir)

    if exempt_file is None:
        exempt_file = default_exempt_path(module_name)
    exemptions = load_exemptions(exempt_file)

    prose_files = []
    readme = module_dir / "README.md"
    outline = module_dir / "lecture" / "outline.md"
    if readme.exists():
        prose_files.append(readme)
    if outline.exists():
        prose_files.append(outline)

    file_results = [
        process_prose_file(p, haystack_l, haystack_m, exemptions) for p in prose_files
    ]

    print(f"# {module_name}")
    ok_l, ok_m, exempt, miss = print_table(file_results)
    total = ok_l + ok_m + exempt + miss
    print(
        f"\n{module_name}: {total} tokens, ok-L {ok_l}, ok-M {ok_m}, "
        f"exempt {exempt}, MISS {miss}"
    )

    if markdown_cells:
        md_results: list[FileResult] = []
        if nb_dir.exists():
            for nb_path in sorted(nb_dir.glob("*.ipynb")):
                tokens = extract_markdown_cell_tokens(nb_path)
                fr = FileResult(nb_path)
                for tok in tokens:
                    if tok.raw in exemptions:
                        fr.rows.append(
                            Row(tok.line_no, tok.raw, "EXEMPT", exemptions[tok.raw])
                        )
                        continue
                    hit_l = match(tok.value, tok.decimals, haystack_l)
                    if hit_l is not None:
                        evidence = f"{hit_l.source} [c{hit_l.cell_index}]"
                        fr.rows.append(Row(tok.line_no, tok.raw, "OK-L", evidence))
                        continue
                    if tok.pointed:
                        hit_m, num = match_pointed(
                            tok.value, tok.decimals, tok.pointed, haystack_m
                        )
                        if hit_m is not None:
                            evidence = (
                                f"{hit_m.source} [c{hit_m.cell_index}] (módulo {num})"
                            )
                            fr.rows.append(Row(tok.line_no, tok.raw, "OK-M", evidence))
                            continue
                    fr.rows.append(Row(tok.line_no, tok.raw, "MISS", ""))
                md_results.append(fr)
        print(f"\n-- {module_name}: passe consultivo de células markdown --")
        print_table(md_results)

    return 1 if miss > 0 else 0


def run_tier_m_report(module_dirs: list[Path]) -> int:
    for module_dir in module_dirs:
        module_name = module_dir.name
        nb_dir = module_dir / "notebooks"
        haystack_l = collect_haystack(nb_dir)
        haystacks = collect_sibling_haystacks(module_dir)
        haystack_m = haystacks.get("00", [])

        prose_files = []
        readme = module_dir / "README.md"
        outline = module_dir / "lecture" / "outline.md"
        if readme.exists():
            prose_files.append(readme)
        if outline.exists():
            prose_files.append(outline)

        print(f"# {module_name} (relatório tier-M)")
        for path in prose_files:
            text = path.read_text(encoding="utf-8")
            all_lines = text.split("\n")
            tokens = extract_prose_tokens(text)
            rows = []
            for tok in tokens:
                hit_l = match(tok.value, tok.decimals, haystack_l)
                if hit_l is not None:
                    continue  # OK-L não interessa ao relatório tier-M
                pointed = pointed_modules(all_lines, tok.line_no)
                hit_p, num = match_pointed(tok.value, tok.decimals, pointed, haystacks)
                if hit_p is not None:
                    rows.append(
                        Row(
                            tok.line_no,
                            tok.raw,
                            "OK-M",
                            f"{hit_p.source} [c{hit_p.cell_index}] (módulo {num})",
                        )
                    )
                    continue
                hit_m = match(tok.value, tok.decimals, haystack_m)
                if hit_m is not None:
                    evidence = f"{hit_m.source} [c{hit_m.cell_index}] (módulo 00)"
                    rows.append(
                        Row(tok.line_no, tok.raw, "M-WITHOUT-POINTER", evidence)
                    )
            if rows:
                print(f"\n== {path} ==")
                print(f"{'line':>5}  {'raw':<12} {'verdict':<18} evidence")
                for row in rows:
                    print(
                        f"{row.line:>5}  {row.raw:<12} {row.verdict:<18} {row.evidence}"
                    )
    return 0


# --------------------------------------------------------------------------
# --dump: imprime as saídas de célula de código de um caderno
# --------------------------------------------------------------------------


def iter_output_lines(nb: dict):
    """Gera (índice-da-célula, linha) para cada linha de saída de célula
    de código em nb."""
    for idx, text in _iter_output_texts(nb):
        yield from ((idx, line) for line in text.splitlines())


def dump_notebook(path_arg: str) -> int:
    if path_arg == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path_arg).read_text(encoding="utf-8")
    nb = json.loads(raw)
    for idx, line in iter_output_lines(nb):
        print(f"[c{idx}] {line}")
    return 0


# --------------------------------------------------------------------------
# --self-test: casos unitários embutidos, sem infraestrutura de testes
# --------------------------------------------------------------------------


def _self_test() -> int:
    checks = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal checks
        assert cond, f"self-test falhou: {msg}"
        checks += 1

    # -- _core_readings: as duas convenções, ponto a ponto com o docstring --
    check(_core_readings("1.282.970") == [1282970.0], "milhar PT (2+ grupos de ponto)")
    check(
        _core_readings("1,282,970") == [1282970.0], "milhar EN (2+ grupos de vírgula)"
    )
    check(_core_readings("0,7644") == [0.7644], "decimal PT (vírgula, grupo != 3)")
    check(_core_readings("0.7644") == [0.7644], "decimal EN (ponto, grupo != 3)")
    check(_core_readings("1.234,5") == [1234.5], "PT completo: milhar + decimal")
    check(_core_readings("1,234.5") == [1234.5], "EN completo: milhar + decimal")
    check(
        set(_core_readings("1.234")) == {1.234, 1234.0},
        "grupo único ambíguo de 3 dígitos gera as duas leituras",
    )
    check(
        set(_core_readings("1,234")) == {1.234, 1234.0},
        "idem com vírgula (EN milhar vs. PT decimal)",
    )

    # -- _iter_haystack_tokens: percentual e notação científica --
    tokens = {
        raw: readings for raw, readings in _iter_haystack_tokens("taxa 37,3% de acerto")
    }
    check("37,3%" in tokens, "token percentual capturado por inteiro (com o %)")
    check(
        37.3 in tokens["37,3%"]
        and abs(0.373 - min(tokens["37,3%"], key=lambda x: abs(x - 0.373))) < 1e-9,
        "percentual guarda o valor citado e a fração (/100)",
    )

    sci_uni = dict(_iter_haystack_tokens("p-valor 1,05×10⁻⁵ significativo"))
    check(
        "1,05×10⁻⁵" in sci_uni, "notação científica unicode consumida como um só token"
    )
    vals = sci_uni["1,05×10⁻⁵"]
    check(any(abs(v - 1.05e-05) < 1e-12 for v in vals), "valor científico calculado")
    check(
        any(abs(v - 1.05) < 1e-12 for v in vals),
        "mantissa preservada como leitura própria",
    )

    sci_e = dict(_iter_haystack_tokens("p-valor 1,05e-05 significativo"))
    check("1,05e-05" in sci_e, "notação e/E também consumida como um só token")
    check(
        any(abs(v - 1.05e-05) < 1e-12 for v in sci_e["1,05e-05"]),
        "e-05 calculado igual ao ×10⁻⁵",
    )

    # -- não deixar "10" do "×10" nem o "05" do "e-05" virarem tokens soltos --
    check(
        len(dict(_iter_haystack_tokens("1,05×10⁻⁵"))) == 1,
        "não sobra token espúrio após ×10⁻⁵",
    )
    check(
        len(dict(_iter_haystack_tokens("1,05e-05"))) == 1,
        "não sobra token espúrio após e-05",
    )

    # -- extract_output_numbers fim-a-fim, com um caderno sintético em disco --
    import tempfile

    nb = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["print(0)"],
                "outputs": [
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": [
                            "AUC de teste: 0,7644\n",
                            "n = 1.282.970 pacientes (37,3%)\n",
                        ],
                    }
                ],
            }
        ]
    }
    with tempfile.TemporaryDirectory() as td:
        nb_path = Path(td) / "fake.ipynb"
        nb_path.write_text(json.dumps(nb), encoding="utf-8")
        haystack = extract_output_numbers(nb_path)
        values = [hv.value for hv in haystack]
        check(
            any(abs(v - 0.7644) < 1e-9 for v in values),
            "AUC 0,7644 extraído do caderno sintético",
        )
        check(
            any(abs(v - 1282970.0) < 1e-9 for v in values),
            "milhar PT extraído do caderno sintético",
        )
        check(
            any(abs(v - 37.3) < 1e-9 for v in values),
            "percentual extraído do caderno sintético",
        )

    # -- match(): a prosa PT bate com as leituras do palheiro --
    check(
        match(0.7644, 4, haystack) is not None,
        "match direto: prosa 0,7644 == saída 0,7644",
    )
    check(
        match(1282970.0, 0, haystack) is not None,
        "match direto: prosa 1.282.970 == saída 1.282.970",
    )
    check(
        match(37.3, 1, haystack) is not None, "match direto: prosa 37,3 == saída 37,3%"
    )

    # -- extract_prose_tokens: regras de exclusão continuam valendo --
    toks = extract_prose_tokens("Em 2024 o capítulo 3 media 0,7644 e ainda 2023–24.")
    raws = {t.raw for t in toks}
    check("2024" not in raws, "ano solto continua excluído")
    check("3" not in raws, "inteiro <= 12 continua excluído")
    check("0,7644" in raws, "decimal PT continua extraído")
    check("24" not in raws, "sufixo de intervalo de anos continua excluído")

    print(f"self-test: {checks} verificações passaram")
    return 0


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("module_dirs", nargs="*", type=Path)
    parser.add_argument("--markdown-cells", action="store_true")
    parser.add_argument("--exempt", type=Path, default=None)
    parser.add_argument("--tier-m-report", action="store_true")
    parser.add_argument("--dump", metavar="NOTEBOOK", default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.self_test:
        return _self_test()

    if args.dump is not None:
        return dump_notebook(args.dump)

    if not args.module_dirs:
        print(
            "error: informe ao menos um module_dir (ou use --self-test/--dump)",
            file=sys.stderr,
        )
        return 2

    if args.tier_m_report:
        return run_tier_m_report(args.module_dirs)

    if len(args.module_dirs) != 1:
        print(
            "error: exatamente um module_dir é exigido (a menos que use --tier-m-report)",
            file=sys.stderr,
        )
        return 2

    return run_module(args.module_dirs[0], args.markdown_cells, args.exempt)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
