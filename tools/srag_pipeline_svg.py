"""Gera os três diagramas do módulo 00, com números medidos, em português.

Uso:
    python tools/srag_pipeline_svg.py            # escreve os três SVGs
    python tools/srag_pipeline_svg.py --check    # renderiza em memória e diffa

Saídas, todas em modules/00-dataset/:
    PIPELINE.svg  o mapa Bronze → Prata → Ouro
    FUNIL.svg     a variável-funil e os três estados do vazio
    REGIMES.svg   letalidade e fração COVID por ano — a base muda de regime

Estrutura e contagens vêm dos mesmos artefatos commitados que o contrato de
cobertura lê — as tabelas de tools/srag_silver.py e o PROFILE.json medido —
então não podem divergir do código sem o diff acusar. Números que exigiram
a base completa (a recontagem de influenza, as taxas de inconsistência) são
achados citados, impressos por células de notebook, e o subtítulo diz isso.
Nada aqui abre um parquet.

As três faixas seguem a regra do medalhão que o módulo defende: Bronze é o
download, intocado; Prata afirma fatos sobre o registro; Ouro faz escolhas
de tarefa — e as faz visivelmente pendentes: as caixas do Ouro são
tracejadas porque as decisões (alvo, coorte, split) são do William e do
curso, não deste repositório.
"""

from __future__ import annotations

import json
import pathlib
import sys

import srag_silver as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILE = ROOT / "modules/00-dataset/PROFILE.json"
OUT_DIR = ROOT / "modules/00-dataset"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def medidas() -> dict:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    anos = sorted(profile)
    cols = sorted({c for y in profile.values() for c in y})
    linhas = sum(next(iter(profile[y].values()))["n_rows"] for y in anos)
    classes = {
        f: sum(1 for c in cols if S.class_of(c) == f) for f in S.CLASS_PRECEDENCE
    }
    regimes = []
    for ano in anos:
        ev = dict(profile[ano]["EVOLUCAO"]["top"])
        cl = dict(profile[ano]["CLASSI_FIN"]["top"])
        n = profile[ano]["EVOLUCAO"]["n_rows"]
        cura = int(ev.get("1", 0)) + int(ev.get("1.0", 0))
        obito = int(ev.get("2", 0)) + int(ev.get("2.0", 0))
        covid = int(cl.get("5", 0)) + int(cl.get("5.0", 0))
        regimes.append(
            {
                "ano": ano,
                "n": n,
                "letalidade": 100 * obito / (cura + obito),
                "covid": 100 * covid / n,
            }
        )
    return {
        "anos": anos,
        "n_cols": len(cols),
        "n_linhas": linhas,
        "classes": classes,
        "portoes": len(S.GATES),
        "rejeitados": len(S.GATES_REJECTED),
        "familias": len(S.FAMILIES),
        "year_gated": len(S.YEAR_GATED),
        "leakage_derivadas": 36 + 2 + 1,  # _obito*, dias_*, caso_srag_ms
        "regimes": regimes,
    }


# --------------------------------------------------------------------------
# PIPELINE.svg
# --------------------------------------------------------------------------
def render_pipeline(m: dict) -> str:
    W, H = 1180, 760
    lane_w, gap, x0, y0 = 350, 40, 20, 84
    xs = [x0, x0 + lane_w + gap, x0 + 2 * (lane_w + gap)]

    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'font-family="Georgia, serif" font-size="14">'
    )
    p.append(f'<rect width="{W}" height="{H}" fill="#faf7f2"/>')
    p.append(
        f'<text x="{W / 2}" y="34" text-anchor="middle" font-size="22" fill="#222">'
        "SRAG / SIVEP-Gripe — o tratamento, do Bronze ao Ouro</text>"
    )
    p.append(
        f'<text x="{W / 2}" y="56" text-anchor="middle" font-size="13" fill="#666">'
        f"{m['n_linhas']:,} notificações · {m['anos'][0]}–{m['anos'][-1]} · estrutura e "
        "contagens geradas do contrato; achados citados são impressos por células</text>"
    )

    def faixa(i: int, titulo: str, sub: str, tracejada: bool = False) -> None:
        x = xs[i]
        dash = ' stroke-dasharray="7,5"' if tracejada else ""
        p.append(
            f'<rect x="{x}" y="{y0}" width="{lane_w}" height="{H - y0 - 20}" rx="10" '
            f'fill="#ffffff" stroke="#b8b0a4" stroke-width="1.5"{dash}/>'
        )
        p.append(
            f'<text x="{x + lane_w / 2}" y="{y0 + 30}" text-anchor="middle" '
            f'font-size="19" fill="#1c1c1c" font-weight="bold">{esc(titulo)}</text>'
        )
        p.append(
            f'<text x="{x + lane_w / 2}" y="{y0 + 50}" text-anchor="middle" '
            f'font-size="12.5" fill="#777">{esc(sub)}</text>'
        )

    def caixa(
        i: int,
        y: int,
        h: int,
        titulo: str,
        linhas: list[str],
        cor: str = "#2e7d52",
        tracejada: bool = False,
    ) -> int:
        x = xs[i] + 16
        w = lane_w - 32
        dash = ' stroke-dasharray="6,4"' if tracejada else ""
        p.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" '
            f'fill="{cor}" fill-opacity="0.09" stroke="{cor}" stroke-width="1.4"{dash}/>'
        )
        p.append(
            f'<text x="{x + 12}" y="{y + 22}" font-size="13.5" font-weight="bold" '
            f'fill="{cor}">{esc(titulo)}</text>'
        )
        for j, ln in enumerate(linhas):
            p.append(
                f'<text x="{x + 12}" y="{y + 42 + j * 17}" font-size="12" '
                f'fill="#3a3a3a">{esc(ln)}</text>'
            )
        return y + h + 12

    # ---- Bronze -----------------------------------------------------------
    faixa(0, "Bronze", "o download, byte a byte, nunca alterado")
    y = y0 + 68
    y = caixa(
        0,
        y,
        78,
        f"{m['n_cols']} colunas × 6 arquivos anuais",
        [
            "reexportação de 26/06/2025, um layout",
            f"{m['n_linhas']:,} linhas, ~2,2 GB de parquet",
        ],
        "#7a6a55",
    )
    y = caixa(
        0,
        y,
        112,
        "o que o perfil mediu",
        [
            "75 colunas mudam de forma entre anos",
            "('1' vs '1.0' — uma regra literal perde",
            "519.518 positivos de PCR_SARS2 em 2020)",
            f"{m['year_gated']} colunas 100% vazias em algum ano",
        ],
        "#7a6a55",
    )
    y = caixa(
        0,
        y,
        112,
        "sujeira, mantida visível",
        [
            "7 linhas deslocadas (UTI carrega nome",
            "de hospital) → quarentena, nenhuma some",
            "datas como 1695-06-14 02:32:37,74…",
            "20 linhas com idade declarada negativa",
        ],
        "#7a6a55",
    )
    y = caixa(
        0,
        y,
        95,
        "procedência",
        [
            "S3 do dadosabertos (o portal caiu;",
            "o bucket ficou de pé)",
            "referência: o script MIT do Ministério",
        ],
        "#7a6a55",
    )

    # ---- Prata ------------------------------------------------------------
    faixa(1, "Prata (Silver)", "fatos sobre o registro — nenhuma escolha de tarefa")
    y = y0 + 68
    y = caixa(
        1,
        y,
        95,
        f"contrato: {m['familias']} famílias, 194/194 com regra",
        [
            "COLUMNS.md gerado + verificado no build;",
            "pre-commit re-renderiza e diffa",
            "normalise() antes de ler qualquer domínio",
        ],
    )
    y = caixa(
        1,
        y,
        95,
        f"portões: {m['portoes']} confirmados, {m['rejeitados']} rejeitados",
        [
            "regra-G: ≤0,05% de contradição, cada ano",
            "build() re-mede e se recusa se divergir",
            "3 estados do vazio, nunca fundidos",
        ],
    )
    y = caixa(
        1,
        y,
        95,
        "224 colunas derivadas (→ 418)",
        [
            "semana MMWR (100,00% vs SEM_PRI),",
            "catálogo de etiologia completo (2,1×),",
            "fabricante de vacina, IBGE, idade",
        ],
    )
    cls = m["classes"]
    y = caixa(
        1,
        y,
        132,
        "toda coluna com classe",
        [
            f"ok {cls['ok']} · par nome-código {cls['code_pair']} · texto livre {cls['free_text']}",
            f"year-gated {cls['year_gated']} · identificador {cls['identifier']} · vazamento {cls['leakage']}",
            "84 checagens Kahn — as que falham são",
            "documentação (RES_AN⇢agente: 9–20%/ano)",
            "invariante: 4.109.560 + 7 = tudo",
        ],
        "#4a7fb5",
    )

    # ---- Ouro -------------------------------------------------------------
    faixa(2, "Ouro (Gold)", "escolhas de tarefa — abertas de propósito", tracejada=True)
    y = y0 + 68
    y = caixa(
        2,
        y,
        95,
        "alvo (decisão: William + curso)",
        [
            "candidatos: óbito · UTI · ventilação",
            "EVOLUCAO é rótulo, nunca feature",
            "GOLD.md põe o cardápio com evidência",
        ],
        "#c03434",
        tracejada=True,
    )
    y = caixa(
        2,
        y,
        95,
        f"exclusão por vazamento — gerável ({cls['leakage']}+{m['leakage_derivadas']})",
        [
            f"{cls['leakage']} colunas cruas classe vazamento +",
            f"{m['leakage_derivadas']} derivadas (_obito*, dias_*, caso_srag_ms)",
            "gerada de COLUMN_CLASS, não digitada",
        ],
        "#c03434",
        tracejada=True,
    )
    y = caixa(
        2,
        y,
        95,
        "coorte e anos",
        [
            "coorte_hospitalizado vs SRAG inteira",
            "vs covid_caso — a deriva de regime é",
            "contexto: letalidade 29→8,6%",
        ],
        "#c03434",
        tracejada=True,
    )
    y = caixa(
        2,
        y,
        112,
        "codificação e split",
        [
            "3 estados do vazio → categorias, nunca",
            "imputados em silêncio; colunas year-gated",
            "são calendários disfarçados; proposta de",
            "split temporal no GOLD.md",
        ],
        "#c03434",
        tracejada=True,
    )

    ay = H / 2
    for i in (0, 1):
        x1 = xs[i] + lane_w
        x2 = xs[i + 1]
        p.append(
            f'<path d="M {x1 + 4} {ay} L {x2 - 10} {ay}" stroke="#8a8177" '
            'stroke-width="2.5" fill="none" marker-end="url(#arr)"/>'
        )
    p.append(
        '<defs><marker id="arr" markerWidth="10" markerHeight="8" refX="8" refY="4" '
        'orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#8a8177"/></marker></defs>'
    )
    p.append("</svg>")
    return "\n".join(p) + "\n"


# --------------------------------------------------------------------------
# FUNIL.svg — a lição central do módulo, desenhada
# --------------------------------------------------------------------------
def render_funil(m: dict) -> str:
    W, H = 1180, 620
    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        'font-family="Georgia, serif" font-size="14">'
    )
    p.append(f'<rect width="{W}" height="{H}" fill="#faf7f2"/>')
    p.append(
        f'<text x="{W / 2}" y="36" text-anchor="middle" font-size="22" fill="#222">'
        "A variável-funil — por que um vazio não é uma coisa só</text>"
    )
    p.append(
        f'<text x="{W / 2}" y="58" text-anchor="middle" font-size="13" fill="#666">'
        "portão medido em 0,00% de contradição nos seis anos · exemplo impresso: "
        "CARDIOPATI 2023, walkthrough §3.2</text>"
    )

    # portão
    p.append(
        '<rect x="60" y="110" width="300" height="120" rx="10" fill="#2e7d52" '
        'fill-opacity="0.10" stroke="#2e7d52" stroke-width="2"/>'
    )
    p.append(
        '<text x="210" y="140" text-anchor="middle" font-size="16" font-weight="bold" '
        'fill="#2e7d52">FATOR_RISC</text>'
    )
    p.append(
        '<text x="210" y="163" text-anchor="middle" font-size="12.5" fill="#3a3a3a">'
        '"Paciente tem fator de risco?"</text>'
    )
    p.append(
        '<text x="210" y="184" text-anchor="middle" font-size="12.5" fill="#3a3a3a">'
        "1/S = sim → bloco habilitado</text>"
    )
    p.append(
        '<text x="210" y="205" text-anchor="middle" font-size="12.5" fill="#3a3a3a">'
        "outro → 13 comorbidades desligadas</text>"
    )

    # os treze campos
    p.append(
        '<rect x="470" y="96" width="290" height="148" rx="10" fill="#4a7fb5" '
        'fill-opacity="0.10" stroke="#4a7fb5" stroke-width="2"/>'
    )
    p.append(
        '<text x="615" y="124" text-anchor="middle" font-size="15" font-weight="bold" '
        'fill="#4a7fb5">as 13 comorbidades</text>'
    )
    for j, ln in enumerate(
        [
            "CARDIOPATI · DIABETES · ASMA ·",
            "RENAL · OBESIDADE · PUERPERA ·",
            "HEPATICA · NEUROLOGIC · …",
            "cada uma ganha a coluna _estado",
        ]
    ):
        p.append(
            f'<text x="615" y="{150 + j * 20}" text-anchor="middle" font-size="12" '
            f'fill="#3a3a3a">{esc(ln)}</text>'
        )
    p.append(
        '<path d="M 364 170 L 462 170" stroke="#8a8177" stroke-width="2.5" '
        'fill="none" marker-end="url(#arr2)"/>'
    )
    p.append(
        '<text x="413" y="160" text-anchor="middle" font-size="11.5" fill="#777">habilita</text>'
    )

    # os três estados
    estados = [
        (
            "nao_aplicavel",
            "#b58a3e",
            "o portão disse não: o campo nunca foi",
            "apresentado — NÃO é dado faltante",
            "CARDIOPATI 2023: 55,0% dos registros",
        ),
        (
            "ausente",
            "#c03434",
            "o campo estava habilitado e ficou",
            "em branco — isto sim é faltante",
            "24,0% dos habilitados",
        ),
        (
            "ignorado",
            "#8a6d9b",
            "código 9: alguém registrou de forma",
            "explícita que não sabe",
            "informação, não ausência",
        ),
    ]
    x = 60
    for nome, cor, l1, l2, l3 in estados:
        p.append(
            f'<rect x="{x}" y="300" width="330" height="130" rx="10" fill="{cor}" '
            f'fill-opacity="0.10" stroke="{cor}" stroke-width="2"/>'
        )
        p.append(
            f'<text x="{x + 165}" y="330" text-anchor="middle" font-size="15" '
            f'font-weight="bold" fill="{cor}">{nome}</text>'
        )
        for j, ln in enumerate((l1, l2, l3)):
            peso = ' font-weight="bold"' if j == 2 else ""
            p.append(
                f'<text x="{x + 165}" y="{356 + j * 21}" text-anchor="middle" '
                f'font-size="12"{peso} fill="#3a3a3a">{esc(ln)}</text>'
            )
        x += 365

    # a moral
    p.append(
        '<rect x="60" y="470" width="1060" height="110" rx="10" fill="#1c1c1c" '
        'fill-opacity="0.05" stroke="#1c1c1c" stroke-width="1.2"/>'
    )
    for j, ln in enumerate(
        [
            "Fundir os três estados é o erro mais caro da base: tratar todo vazio como ausência",
            "infla a estatística de dado faltante por um fator de 1,8× a 5,7× conforme o ano (internals §4) —",
            "e imputar por cima disso inventa pacientes. O Prata separa; quem funde é decisão do Ouro, declarada.",
        ]
    ):
        p.append(
            f'<text x="590" y="{502 + j * 24}" text-anchor="middle" font-size="13.5" '
            f'fill="#2a2a2a">{esc(ln)}</text>'
        )

    p.append(
        '<defs><marker id="arr2" markerWidth="10" markerHeight="8" refX="8" refY="4" '
        'orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#8a8177"/></marker></defs>'
    )
    p.append("</svg>")
    return "\n".join(p) + "\n"


# --------------------------------------------------------------------------
# REGIMES.svg — a base muda de problema clínico ao longo dos anos
# --------------------------------------------------------------------------
def render_regimes(m: dict) -> str:
    W, H = 1180, 560
    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        'font-family="Georgia, serif" font-size="14">'
    )
    p.append(f'<rect width="{W}" height="{H}" fill="#faf7f2"/>')
    p.append(
        f'<text x="{W / 2}" y="36" text-anchor="middle" font-size="22" fill="#222">'
        "Não é o mesmo problema clínico — os regimes da base</text>"
    )
    p.append(
        f'<text x="{W / 2}" y="58" text-anchor="middle" font-size="13" fill="#666">'
        "calculado do PROFILE.json commitado · letalidade = óbitos ÷ (curas + óbitos) · "
        "COVID = CLASSI_FIN 5 ÷ registros</text>"
    )

    x0, y_base, alt_max = 100, 440, 300
    largura, gap_barra, gap_grupo = 52, 10, 60
    escala = alt_max / 80.0  # 80% no topo

    x = x0
    for r in m["regimes"]:
        h_let = r["letalidade"] * escala
        h_cov = r["covid"] * escala
        p.append(
            f'<rect x="{x}" y="{y_base - h_let:.1f}" width="{largura}" height="{h_let:.1f}" '
            'fill="#c03434" fill-opacity="0.75"/>'
        )
        p.append(
            f'<text x="{x + largura / 2}" y="{y_base - h_let - 8:.1f}" text-anchor="middle" '
            f'font-size="12.5" fill="#c03434" font-weight="bold">{r["letalidade"]:.1f}</text>'
        )
        p.append(
            f'<rect x="{x + largura + gap_barra}" y="{y_base - h_cov:.1f}" width="{largura}" '
            f'height="{h_cov:.1f}" fill="#4a7fb5" fill-opacity="0.75"/>'
        )
        p.append(
            f'<text x="{x + largura + gap_barra + largura / 2}" y="{y_base - h_cov - 8:.1f}" '
            f'text-anchor="middle" font-size="12.5" fill="#4a7fb5" font-weight="bold">'
            f"{r['covid']:.1f}</text>"
        )
        p.append(
            f'<text x="{x + largura + gap_barra / 2}" y="{y_base + 24}" text-anchor="middle" '
            f'font-size="14" fill="#222" font-weight="bold">{r["ano"]}</text>'
        )
        p.append(
            f'<text x="{x + largura + gap_barra / 2}" y="{y_base + 44}" text-anchor="middle" '
            f'font-size="11" fill="#777">{r["n"]:,}</text>'
        )
        x += 2 * largura + gap_barra + gap_grupo

    p.append(
        f'<line x1="{x0 - 20}" y1="{y_base}" x2="{x - 30}" y2="{y_base}" '
        'stroke="#8a8177" stroke-width="1.5"/>'
    )
    p.append(
        '<rect x="880" y="120" width="16" height="16" fill="#c03434" fill-opacity="0.75"/>'
        '<text x="904" y="133" font-size="13" fill="#2a2a2a">letalidade bruta (%)</text>'
    )
    p.append(
        '<rect x="880" y="146" width="16" height="16" fill="#4a7fb5" fill-opacity="0.75"/>'
        '<text x="904" y="159" font-size="13" fill="#2a2a2a">fração COVID (%)</text>'
    )
    for j, ln in enumerate(
        [
            "Um modelo treinado na série inteira aprende, entre",
            "outras coisas, em que ano o paciente adoeceu.",
            "Isso não é defeito — é contexto que o Ouro declara,",
            "e que os módulos de interpretabilidade vão revelar.",
        ]
    ):
        p.append(
            f'<text x="880" y="{196 + j * 20}" font-size="12.5" fill="#555">{esc(ln)}</text>'
        )
    p.append("</svg>")
    return "\n".join(p) + "\n"


SAIDAS = {
    "PIPELINE.svg": render_pipeline,
    "FUNIL.svg": render_funil,
    "REGIMES.svg": render_regimes,
}


def main(argv: list[str]) -> int:
    m = medidas()
    drift = False
    for nome, render in SAIDAS.items():
        texto = render(m)
        alvo = OUT_DIR / nome
        if "--check" in argv:
            existente = alvo.read_text(encoding="utf-8") if alvo.exists() else ""
            if existente != texto:
                print(f"{nome} divergiu do contrato", file=sys.stderr)
                drift = True
            continue
        alvo.write_text(texto, encoding="utf-8")
        print(f"{alvo}")
    if "--check" in argv:
        if drift:
            return 1
        print("os três SVGs estão atuais")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    raise SystemExit(main(sys.argv[1:]))
