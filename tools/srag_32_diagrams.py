"""Gera os quatro diagramas do módulo 00, com números medidos, em português.

Uso:
    python tools/srag_32_diagrams.py            # escreve os quatro SVGs
    python tools/srag_32_diagrams.py --check    # renderiza em memória e diffa

Saídas, todas em modules/00-dataset/:
    PIPELINE.svg   a jornada inteira: Bronze → Prata → Ouro → estudo → modelo
    FUNIL.svg      a variável-funil e os três estados do vazio
    REGIMES.svg    letalidade e fração COVID por ano — a base muda de regime
    SELECTION.svg  o estudo pré-registrado que escolheu o modelo do curso

Estrutura e contagens vêm dos mesmos artefatos commitados que o contrato de
cobertura lê — as tabelas de tools/srag_30_silver.py, o PROFILE.json medido e
os três JSON do Ouro (counts, selection_metrics, model_metrics) — então não
podem divergir do código sem o diff acusar. Achados que exigiram a base
completa (a recontagem de influenza, as idades negativas) são citados,
impressos por células de notebook, e os subtítulos dizem isso. Nada aqui
abre um parquet, e nenhuma métrica é digitada: toda AUC, contagem e taxa
sai de um JSON commitado.

A jornada do PIPELINE tem cinco estações porque as cinco escolhas do Ouro
foram decididas em 2026-09-01 (GOLD.md) e o modelo do curso saiu de um
estudo pré-registrado (SELECTION.md), adotado em MODEL.md: as caixas do
Ouro são sólidas — não há mais pendência a desenhar — e a linha continua
até o modelo que os módulos 01–05 explicam.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import srag_30_silver as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "modules/00-dataset"
PROFILE = OUT_DIR / "PROFILE.json"
COUNTS = OUT_DIR / "gold/counts.json"
SELECAO = OUT_DIR / "gold/selection_metrics.json"
MODELO = OUT_DIR / "gold/model_metrics.json"

# As 10 colunas de escrituração/diagnóstico do MANIFEST §2.5. A lista é
# estrutura; a contagem de features sai da subtração, não do teclado.
ESCRITURACAO = frozenset(
    {
        "ano_onset",
        "fator_risc_portao",
        "gold_id",
        "n_crit2",
        "n_crit3",
        "raiox_res",
        "rt_pcr_confirmado",
        "split",
        "tomo_res",
        "y_obito",
    }
)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def br(n: int) -> str:
    """Milhar com ponto — a convenção pt-BR que a prosa do módulo usa."""
    return f"{n:,}".replace(",", ".")


def dec(x: float, casas: int = 4) -> str:
    """Decimal com vírgula, casas fixas."""
    return f"{x:.{casas}f}".replace(".", ",")


def num(x: float) -> str:
    """Número curto, sem zeros à direita: 0.05 → 0,05; 800.0 → 800."""
    return f"{x:g}".replace(".", ",")


def ouro(n_prata: int) -> dict:
    """O que o Ouro materializou, lido de gold/counts.json."""
    c = json.loads(COUNTS.read_text(encoding="utf-8"))
    funil = dict(c["funil"])
    corte, ano_val, ano_teste = c["decisoes"]["split"].split(":")[1].split("/")
    return {
        "n": c["n_gold"],
        "obitos": c["obitos"],
        "letalidade": c["letalidade_pct"],
        "funil": funil,
        "splits": c["splits"],
        "decisoes": c["decisoes"],
        "amostra": c["amostra"],
        "extracao": c["extracao"],
        "n_colunas": len(c["features"]),
        "n_features": len(set(c["features"]) - ESCRITURACAO),
        "deslocadas": n_prata - funil["prata (sem linhas deslocadas)"],
        "corte": corte,
        "ano_val": ano_val,
        "ano_teste": ano_teste,
    }


def selecao() -> dict:
    """O estudo pré-registrado, lido de gold/selection_metrics.json."""
    s = json.loads(SELECAO.read_text(encoding="utf-8"))
    val = {r["modelo"]: r for r in s["placar"] if r["split"] == "val"}
    teste = {r["modelo"]: r for r in s["placar"] if r["split"] == "test"}
    boot = {r["modelo"]: r for r in s["bootstrap"]}
    lider = s["escolha"]["vencedor"]
    return {
        "val": val,
        "teste": teste,
        "boot": boot,
        "lider": lider,
        "log": s["escolha"]["log"],
        "n_iter": s["n_iter"],
        "espaco": {
            k: math.prod(len(v) for v in e.values()) for k, e in s["espacos"].items()
        },
        # a regra 2 usa o menor EP do Δ entre os desafiantes: é a faixa mais
        # estreita em que ainda caberia um empate técnico.
        "ep": min(b["delta_ep"] for k, b in boot.items() if k != lider),
        "reamostras": boot[lider]["reamostras"],
        "conseq": s["consequencia"],
        "ordem": sorted(val, key=lambda k: -val[k]["auc"]),
    }


def modelo() -> dict:
    """O modelo adotado, lido de gold/model_metrics.json."""
    mm = json.loads(MODELO.read_text(encoding="utf-8"))

    def linha(nome: str, split: str) -> dict:
        return next(r for r in mm[nome] if r["split"] == split)

    return {
        "xgb_val": linha("xgb", "val"),
        "xgb_test": linha("xgb", "test"),
        "logit_val": linha("logit", "val"),
        "logit_test": linha("logit", "test"),
        "params": mm["xgb_params"],
    }


def medidas() -> dict:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    anos = sorted(profile)
    cols = sorted({c for y in profile.values() for c in y})
    linhas_ano = {a: next(iter(profile[a].values()))["n_rows"] for a in anos}
    linhas = sum(linhas_ano.values())
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

    def formas(c: str) -> set:
        """Conjuntos de formas observadas, por ano em que a coluna tem dado."""
        return {
            frozenset(profile[a][c]["shapes"])
            for a in anos
            if c in profile[a] and profile[a][c]["shapes"]
        }

    # '1' num ano, '1.0' no outro: o ano em que a forma float esconde mais
    # positivos de PCR_SARS2 de uma regra literal.
    pcr = {
        a: dict(profile[a]["PCR_SARS2"]["top"]).get("1.0", 0)
        for a in anos
        if "PCR_SARS2" in profile[a]
    }
    pcr_ano = max(pcr, key=lambda a: pcr[a])
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
        "derivadas": len(S.derived_catalogue()),
        "regimes": regimes,
        "muda_forma": sum(1 for c in cols if len(formas(c)) > 1),
        "pcr_ano": pcr_ano,
        "pcr_n": pcr[pcr_ano],
        "ano_pico": max(linhas_ano, key=lambda a: linhas_ano[a]),
        "n_pico": max(linhas_ano.values()),
        "ouro": ouro(linhas),
        "sel": selecao(),
        "modelo": modelo(),
    }


# --------------------------------------------------------------------------
# PIPELINE.svg — a jornada inteira, Bronze → Prata → Ouro → estudo → modelo
# --------------------------------------------------------------------------
def render_pipeline(m: dict) -> str:
    cls, o, s, mo = m["classes"], m["ouro"], m["sel"], m["modelo"]
    sp, par, cq = o["splits"], mo["params"], s["conseq"]
    hoje, venc = cq["xgb_params_hoje"], cq["xgb_params_vencedor"]

    def trio(d: dict) -> str:
        return f"{num(d['learning_rate'])} / {d['max_depth']} / {d['n_estimators']}"

    W = 1180
    y0, alt, vao = 98, 142, 32
    H = y0 + 5 * alt + 4 * vao + 18

    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'font-family="Georgia, serif" font-size="14">'
    )
    p.append(f'<rect width="{W}" height="{H}" fill="#faf7f2"/>')
    p.append(
        f'<text x="{W / 2}" y="34" text-anchor="middle" font-size="22" fill="#222">'
        "SRAG / SIVEP-Gripe — do download bruto ao modelo do curso</text>"
    )
    p.append(
        f'<text x="{W / 2}" y="58" text-anchor="middle" font-size="13" fill="#666">'
        "Bronze intocado → Prata afirma fatos → Ouro escolhe (decidido "
        "2026-09-01) → o estudo mede → o modelo é adotado</text>"
    )
    p.append(
        f'<text x="{W / 2}" y="78" text-anchor="middle" font-size="11.5" '
        'fill="#8a8177">gerado de PROFILE.json, gold/counts.json, '
        "gold/selection_metrics.json e gold/model_metrics.json — nenhuma "
        "métrica digitada</text>"
    )

    def faixa(
        k: int,
        cor: str,
        nome: str,
        sub: list[str],
        destaque: str,
        rodape: str,
        cartoes: list[tuple[str, list[str]]],
    ) -> None:
        y = y0 + k * (alt + vao)
        p.append(
            f'<rect x="20" y="{y}" width="1140" height="{alt}" rx="12" '
            'fill="#ffffff" stroke="#b8b0a4" stroke-width="1.4"/>'
        )
        p.append(
            f'<rect x="32" y="{y + 12}" width="228" height="{alt - 24}" rx="9" '
            f'fill="{cor}" fill-opacity="0.11" stroke="{cor}" stroke-width="1.3"/>'
        )
        p.append(
            f'<text x="146" y="{y + 34}" text-anchor="middle" font-size="18.5" '
            f'font-weight="bold" fill="{cor}">{esc(nome)}</text>'
        )
        for j, ln in enumerate(sub):
            p.append(
                f'<text x="146" y="{y + 54 + j * 16}" text-anchor="middle" '
                f'font-size="11.5" fill="#6b6b6b">{esc(ln)}</text>'
            )
        p.append(
            f'<text x="146" y="{y + 100}" text-anchor="middle" font-size="15.5" '
            f'font-weight="bold" fill="#2a2a2a">{esc(destaque)}</text>'
        )
        p.append(
            f'<text x="146" y="{y + 119}" text-anchor="middle" font-size="11" '
            f'fill="#6b6b6b">{esc(rodape)}</text>'
        )
        for i, (titulo, linhas) in enumerate(cartoes):
            x = 278 + i * 295
            p.append(
                f'<rect x="{x}" y="{y + 14}" width="281" height="{alt - 28}" '
                f'rx="8" fill="{cor}" fill-opacity="0.05" stroke="{cor}" '
                'stroke-opacity="0.45" stroke-width="1.2"/>'
            )
            p.append(
                f'<text x="{x + 13}" y="{y + 34}" font-size="13" '
                f'font-weight="bold" fill="{cor}">{esc(titulo)}</text>'
            )
            for j, ln in enumerate(linhas):
                p.append(
                    f'<text x="{x + 13}" y="{y + 55 + j * 17}" font-size="12" '
                    f'fill="#3a3a3a">{esc(ln)}</text>'
                )
        if k < 4:
            p.append(
                f'<path d="M 146 {y + alt + 4} L 146 {y + alt + vao - 8}" '
                'stroke="#8a8177" stroke-width="3" fill="none" '
                'marker-end="url(#arr)"/>'
            )

    faixa(
        0,
        "#7a6a55",
        "Bronze",
        ["o download, byte a byte,", "nunca alterado"],
        f"{m['n_cols']} colunas × {len(m['anos'])} anos",
        f"reexportação de {o['extracao'].replace('-', '/')}",
        [
            (
                "um layout, seis arquivos",
                [
                    f"{br(m['n_linhas'])} notificações, {m['anos'][0]}–{m['anos'][-1]}",
                    f"pico em {m['ano_pico']}: {br(m['n_pico'])} linhas",
                    "um só layout, nenhuma coluna renomeada",
                    "S3 do dadosabertos, script MIT do MS",
                ],
            ),
            (
                "o que o perfil mediu",
                [
                    f"{m['muda_forma']} colunas mudam de forma entre anos",
                    "('1' vs '1.0' — a regra literal perde",
                    f"{br(m['pcr_n'])} positivos de PCR_SARS2 em {m['pcr_ano']})",
                    f"{m['year_gated']} colunas 100% vazias em algum ano",
                ],
            ),
            (
                "sujeira, mantida visível",
                [
                    f"{o['deslocadas']} linhas deslocadas (UTI carrega",
                    "nome de hospital) → quarentena",
                    "datas como 1695-06-14 02:32:37,74…",
                    "20 idades declaradas negativas",
                ],
            ),
        ],
    )

    faixa(
        1,
        "#2e7d52",
        "Prata (Silver)",
        ["fatos sobre o registro —", "nenhuma escolha de tarefa"],
        f"{br(m['n_linhas'])} × {m['n_cols'] + m['derivadas']}",
        f"{o['deslocadas']} linhas em quarentena, contadas",
        [
            (
                f"contrato: {m['familias']} famílias",
                [
                    f"{m['n_cols']}/{m['n_cols']} colunas com regra escrita",
                    "COLUMNS.md gerado e verificado no build",
                    "pre-commit re-renderiza e diffa",
                    "normalise() antes de ler um domínio",
                ],
            ),
            (
                f"portões: {m['portoes']} confirmados, {m['rejeitados']} fora",
                [
                    "regra-G: ≤0,05% de contradição, cada ano",
                    "build() re-mede e se recusa se divergir",
                    "3 estados do vazio, nunca fundidos",
                    "84 checagens Kahn: o que falha é doc.",
                ],
            ),
            (
                f"{m['derivadas']} colunas derivadas",
                [
                    "semana MMWR, etiologia completa (2,1×),",
                    "fabricante de vacina, IBGE, idade",
                    (
                        f"ok {cls['ok']} · vazamento {cls['leakage']} · "
                        f"year-gated {cls['year_gated']}"
                    ),
                    (
                        f"código-nome {cls['code_pair']} · texto "
                        f"{cls['free_text']} · id {cls['identifier']}"
                    ),
                ],
            ),
        ],
    )

    faixa(
        2,
        "#b58a3e",
        "Ouro (Gold)",
        ["as cinco escolhas de tarefa,", "decididas em 2026-09-01"],
        f"{br(o['n'])} × {o['n_features']} features",
        f"alvo y_obito · {dec(o['letalidade'], 2)}% de óbitos",
        [
            (
                "alvo e vazamento",
                [
                    "óbito nos casos fechados → y_obito",
                    f"{br(o['obitos'])} óbitos em {br(o['n'])} linhas",
                    "EVOLUCAO é rótulo, nunca feature",
                    (
                        f"exclusão gerada: {cls['leakage']} cruas + "
                        f"{m['leakage_derivadas']} derivadas"
                    ),
                ],
            ),
            (
                "coorte e janela",
                [
                    f"{br(o['funil']['coorte_hospitalizado'])} hospitalizados",
                    (
                        f"{br(o['funil']['covid_caso (definição ampla)'])} "
                        "com COVID (definição ampla)"
                    ),
                    (
                        f"{br(o['funil']['casos fechados (EVOLUCAO 1 ou 2)'])} "
                        f"fechados → {br(o['n'])}"
                    ),
                    f"janela desde {o['decisoes']['inicio'][:10]}",
                ],
            ),
            (
                "split temporal",
                [
                    (
                        f"treino ≤ {o['corte']}: {br(sp['train']['n'])} "
                        f"({dec(sp['train']['letalidade_pct'], 1)}%)"
                    ),
                    (
                        f"validação {o['ano_val']}: {br(sp['val']['n'])} "
                        f"({dec(sp['val']['letalidade_pct'], 1)}%)"
                    ),
                    (
                        f"teste {o['ano_teste']}: {br(sp['test']['n'])} "
                        f"({dec(sp['test']['letalidade_pct'], 1)}%)"
                    ),
                    "os três vazios viram categoria declarada",
                ],
            ),
        ],
    )

    faixa(
        3,
        "#4a7fb5",
        "Estudo de seleção",
        ["protocolo pré-registrado,", "escolha só na validação"],
        f"{len(s['n_iter'])} candidatos · {sum(s['n_iter'].values())} configs",
        f"vencedor: {s['lider']}",
        [
            (
                "o critério, escrito antes",
                [
                    f"primário: AUC-ROC na validação {o['ano_val']}",
                    "empate: 1 EP de bootstrap pareado",
                    (
                        f"({s['reamostras']} reamostras, semente "
                        f"{o['decisoes']['semente']})"
                    ),
                    "consequência declarada na regra 8",
                ],
            ),
            (
                "o zoo e o orçamento",
                [
                    "dummy · lpm · logit · árvore ·",
                    "floresta · xgb — três matrizes de X",
                    (
                        f"{sum(s['n_iter'].values())} configurações medidas "
                        f"de {br(sum(s['espaco'].values()))}"
                    ),
                    (
                        f"xgb: {s['n_iter']['xgb']} de {s['espaco']['xgb']} · "
                        f"árvore: {s['n_iter']['arvore']} de "
                        f"{s['espaco']['arvore']}"
                    ),
                ],
            ),
            (
                "o teste ficou lacrado",
                [
                    "pick_model levanta exceção se vir",
                    "uma linha de split == test",
                    (
                        "lido uma vez, depois de escolhido: "
                        f"{dec(s['teste'][s['lider']]['auc'])}"
                    ),
                    "nenhum candidato a 1 EP do líder",
                ],
            ),
        ],
    )

    faixa(
        4,
        "#8a6d9b",
        "Modelo do curso",
        ["o objeto que os módulos", "01–05 explicam"],
        f"AUC teste {dec(mo['xgb_test']['auc'])}",
        f"XGBoost {trio(par)}",
        [
            (
                "XGBoost tunado",
                [
                    (
                        f"{par['n_estimators']} árvores, profundidade "
                        f"{par['max_depth']}, lr {num(par['learning_rate'])}"
                    ),
                    (
                        f"min_child_weight {par['min_child_weight']} · "
                        f"reg_lambda {num(par['reg_lambda'])}"
                    ),
                    (
                        f"categóricas nativas, {par['tree_method']}, "
                        f"semente {par['random_state']}"
                    ),
                    (
                        f"AUC val {dec(mo['xgb_val']['auc'])} · Brier "
                        f"{dec(mo['xgb_test']['brier'])} no teste"
                    ),
                ],
            ),
            (
                "logística de contraste",
                [
                    "linear em log-odds, o baseline",
                    "interpretável que o curso compara",
                    (
                        f"AUC val {dec(mo['logit_val']['auc'])} · teste "
                        f"{dec(mo['logit_test']['auc'])}"
                    ),
                    "mesmo Ouro, mesma amostra, outra forma",
                ],
            ),
            (
                "a consequência, cumprida",
                [
                    f"XGB_PARAMS na data: {trio(hoje)}",
                    f"vencedor adotado: {trio(venc)}",
                    "o modelo do curso mudou (MODEL.md)",
                    "módulos 01–05 re-sincronizados depois",
                ],
            ),
        ],
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


# --------------------------------------------------------------------------
# SELECTION.svg — o estudo pré-registrado, em uma figura
# --------------------------------------------------------------------------
def render_selection(m: dict) -> str:
    o, s = m["ouro"], m["sel"]
    sp, am = o["splits"], o["amostra"]
    lider = s["lider"]
    auc_lider = s["val"][lider]["auc"]
    auc_teste = s["teste"][lider]["auc"]

    W, H = 1180, 816
    amin, amax = 0.50, 0.78
    bx0, bx1 = 262, 1000
    y_top, alt_lin, alt_bar = 428, 42, 22

    def px(auc: float) -> float:
        return bx0 + (auc - amin) / (amax - amin) * (bx1 - bx0)

    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        'font-family="Georgia, serif" font-size="14">'
    )
    p.append(f'<rect width="{W}" height="{H}" fill="#faf7f2"/>')
    p.append(
        f'<text x="{W / 2}" y="36" text-anchor="middle" font-size="22" fill="#222">'
        "O estudo que escolheu o modelo do curso</text>"
    )
    p.append(
        f'<text x="{W / 2}" y="58" text-anchor="middle" font-size="13" fill="#666">'
        "gerado de gold/selection_metrics.json · protocolo pré-registrado em "
        "2026-09-01, antes de qualquer leitura do teste</text>"
    )

    # ---- painel 1: o protocolo temporal ------------------------------------
    p.append(
        '<rect x="20" y="78" width="1140" height="262" rx="12" fill="#ffffff" '
        'stroke="#b8b0a4" stroke-width="1.4"/>'
    )
    p.append(
        '<text x="42" y="106" font-size="16" font-weight="bold" fill="#2a2a2a">'
        "1 · O protocolo temporal — cada ano do Ouro tem um papel só</text>"
    )

    def bloco(x: int, w: int, cor: str, titulo: str, linhas: list[str]) -> None:
        p.append(
            f'<rect x="{x}" y="124" width="{w}" height="104" rx="9" fill="{cor}" '
            f'fill-opacity="0.10" stroke="{cor}" stroke-width="1.8"/>'
        )
        p.append(
            f'<text x="{x + 14}" y="148" font-size="14" font-weight="bold" '
            f'fill="{cor}">{esc(titulo)}</text>'
        )
        for j, ln in enumerate(linhas):
            peso = ' font-weight="bold"' if j == len(linhas) - 1 else ""
            cor_ln = cor if j == len(linhas) - 1 else "#3a3a3a"
            p.append(
                f'<text x="{x + 14}" y="{170 + j * 18}" font-size="12"{peso} '
                f'fill="{cor_ln}">{esc(ln)}</text>'
            )

    bloco(
        48,
        452,
        "#4a7fb5",
        f"TREINO — início até {o['corte']}",
        [
            f"{br(sp['train']['n'])} linhas · {br(sp['train']['obitos'])} óbitos",
            f"letalidade {dec(sp['train']['letalidade_pct'], 1)}%",
            (
                f"{br(am['treino_amostrado'])} amostradas para o estudo "
                f"(semente {o['decisoes']['semente']})"
            ),
        ],
    )
    bloco(
        540,
        232,
        "#2e7d52",
        f"VALIDAÇÃO — {o['ano_val']}",
        [
            f"{br(sp['val']['n'])} linhas",
            (
                f"{br(sp['val']['obitos'])} óbitos · "
                f"{dec(sp['val']['letalidade_pct'], 1)}%"
            ),
            "a seleção acontece AQUI",
        ],
    )
    bloco(
        856,
        256,
        "#c03434",
        f"TESTE — {o['ano_teste']}",
        [
            f"{br(sp['test']['n'])} linhas",
            (
                f"{br(sp['test']['obitos'])} óbitos · "
                f"{dec(sp['test']['letalidade_pct'], 1)}%"
            ),
            "lido UMA vez, depois de escolhido",
        ],
    )

    for x1, x2 in ((500, 532), (776, 806), (822, 850)):
        p.append(
            f'<path d="M {x1} 176 L {x2} 176" stroke="#8a8177" stroke-width="2.5" '
            'fill="none" marker-end="url(#arrS)"/>'
        )

    # a barreira anti-teste, com cadeado
    p.append(
        '<path d="M 809 94 v -6 a 5 5 0 0 1 10 0 v 6" stroke="#c03434" '
        'stroke-width="2" fill="none"/>'
    )
    p.append('<rect x="805" y="94" width="18" height="14" rx="2.5" fill="#c03434"/>')
    p.append('<circle cx="814" cy="101" r="2" fill="#faf7f2"/>')
    p.append(
        '<line x1="814" y1="114" x2="814" y2="262" stroke="#c03434" '
        'stroke-width="2" stroke-dasharray="6,5"/>'
    )
    p.append(
        '<text x="814" y="290" text-anchor="middle" font-size="12" '
        'font-weight="bold" fill="#c03434">barreira anti-teste</text>'
    )
    p.append(
        '<text x="814" y="308" text-anchor="middle" font-size="11.5" '
        'fill="#8a5050">pick_model levanta exceção se vir split == test</text>'
    )

    # eixo do tempo
    p.append(
        '<path d="M 48 252 L 1116 252" stroke="#b8b0a4" stroke-width="1.5" '
        'fill="none" marker-end="url(#arrS)"/>'
    )
    p.append('<text x="1122" y="256" font-size="10.5" fill="#8a8177">tempo</text>')
    for x, rot in ((274, "2020 · 2021 · 2022"), (656, "2023"), (984, "2024")):
        p.append(
            f'<text x="{x}" y="272" text-anchor="middle" font-size="11.5" '
            f'fill="#6b6b6b">{esc(rot)}</text>'
        )

    # ---- painel 2: o placar de validação ------------------------------------
    p.append(
        '<rect x="20" y="356" width="1140" height="440" rx="12" fill="#ffffff" '
        'stroke="#b8b0a4" stroke-width="1.4"/>'
    )
    p.append(
        '<text x="42" y="384" font-size="16" font-weight="bold" fill="#2a2a2a">'
        f"2 · O placar de validação — a AUC de {o['ano_val']} escolhe, e só "
        "ela</text>"
    )
    p.append(
        '<text x="42" y="404" font-size="11.5" fill="#8a8177">barras = AUC na '
        f"validação {o['ano_val']} · losango = AUC no teste {o['ano_teste']}, "
        "lido depois da escolha</text>"
    )
    p.append('<text x="1012" y="406" font-size="10" fill="#8a8177">Δ vs líder</text>')
    p.append(
        '<text x="1012" y="419" font-size="10" fill="#8a8177">'
        "(bootstrap pareado)</text>"
    )

    y_fim = y_top + len(s["ordem"]) * alt_lin
    grade = [amin + 0.05 * i for i in range(6)]
    for v in grade:
        p.append(
            f'<line x1="{px(v):.1f}" y1="420" x2="{px(v):.1f}" y2="{y_fim + 4}" '
            'stroke="#ded8ce" stroke-width="1" stroke-dasharray="3,4"/>'
        )
        p.append(
            f'<text x="{px(v):.1f}" y="{y_fim + 26}" text-anchor="middle" '
            f'font-size="11" fill="#8a8177">{dec(v, 2)}</text>'
        )

    # a faixa de empate: 1 EP do líder, onde nenhum candidato entrou
    p.append(
        f'<rect x="{px(auc_lider - s["ep"]):.1f}" y="420" '
        f'width="{px(auc_lider) - px(auc_lider - s["ep"]):.1f}" '
        f'height="{y_fim - 416}" fill="#b58a3e" fill-opacity="0.35"/>'
    )
    p.append(
        f'<text x="{px(auc_lider - s["ep"]) - 10:.1f}" y="416" text-anchor="end" '
        'font-size="11" fill="#9a7a33">faixa de empate: 1 EP = '
        f"{dec(s['ep'])} →</text>"
    )

    for i, nome in enumerate(s["ordem"]):
        topo = y_top + i * alt_lin
        auc = s["val"][nome]["auc"]
        largura = px(auc) - bx0
        campeao = nome == lider
        if campeao:
            cor, opac = "#8a6d9b", "0.85"
        elif nome == "dummy":
            cor, opac = "#8a8177", "0.45"
        else:
            cor, opac = "#4a7fb5", "0.55"
        p.append(
            f'<rect x="{bx0}" y="{topo + 5}" width="{largura:.1f}" '
            f'height="{alt_bar}" rx="3" fill="{cor}" fill-opacity="{opac}"/>'
        )
        if largura >= 60:
            p.append(
                f'<text x="{px(auc) - 10:.1f}" y="{topo + 22}" text-anchor="end" '
                f'font-size="12.5" font-weight="bold" fill="#ffffff">'
                f"{dec(auc)}</text>"
            )
        else:
            p.append(
                f'<text x="{bx0 + 10}" y="{topo + 22}" font-size="12.5" '
                f'font-weight="bold" fill="{cor}">{dec(auc)}</text>'
            )
        n_busca = s["n_iter"][nome]
        plural = "configuração" if s["espaco"][nome] == 1 else "configurações"
        rodape = f"{n_busca} de {s['espaco'][nome]} {plural}"
        p.append(
            f'<text x="250" y="{topo + 18}" text-anchor="end" font-size="14" '
            f'font-weight="bold" fill="{cor if campeao else "#3a3a3a"}">'
            f"{esc(nome)}</text>"
        )
        p.append(
            f'<text x="250" y="{topo + 33}" text-anchor="end" font-size="10.5" '
            f'fill="#8a8177">{esc(rodape + (" · vencedor" if campeao else ""))}'
            "</text>"
        )
        if campeao:
            cy = topo + 5 + alt_bar / 2
            xt = px(auc_teste)
            p.append(
                f'<path d="M {xt:.1f} {cy - 8} L {xt + 8:.1f} {cy} '
                f'L {xt:.1f} {cy + 8} L {xt - 8:.1f} {cy} z" fill="#8a6d9b" '
                'stroke="#ffffff" stroke-width="1.2"/>'
            )
            p.append(
                f'<line x1="{xt + 10:.1f}" y1="{cy}" x2="1006" y2="{cy}" '
                'stroke="#8a6d9b" stroke-width="1" stroke-dasharray="3,3"/>'
            )
            p.append(
                f'<text x="1012" y="{topo + 13}" font-size="11" fill="#8a6d9b">'
                f"teste {o['ano_teste']}</text>"
            )
            p.append(
                f'<text x="1012" y="{topo + 28}" font-size="12.5" '
                f'font-weight="bold" fill="#8a6d9b">{dec(auc_teste)}</text>'
            )
        else:
            b = s["boot"][nome]
            eps = abs(b["delta_lider"]) / b["delta_ep"]
            p.append(
                f'<text x="1012" y="{topo + 13}" font-size="11" fill="#6b6b6b">'
                f"−{dec(abs(b['delta_lider']))}</text>"
            )
            p.append(
                f'<text x="1012" y="{topo + 28}" font-size="11" fill="#8a8177">'
                f"{dec(eps, 1)} EP do líder</text>"
            )

    p.append(
        f'<text x="{(bx0 + bx1) / 2}" y="{y_fim + 46}" text-anchor="middle" '
        'font-size="11.5" fill="#6b6b6b">AUC-ROC — eixo truncado em 0,50, a '
        "AUC de acaso; o dummy é exatamente o zero deste eixo</text>"
    )
    veredito = (
        f"O teste ({o['ano_teste']}) foi lido uma vez, depois da escolha: AUC "
        f"{dec(auc_teste)} — não podia mudar o vencedor, e não mudou."
    )
    rodapes = [f"• {ln}" for ln in s["log"]] + [veredito]
    for j, ln in enumerate(rodapes):
        p.append(
            f'<text x="42" y="{748 + j * 18}" font-size="12.5" fill="#2a2a2a">'
            f"{esc(ln)}</text>"
        )

    p.append(
        '<defs><marker id="arrS" markerWidth="10" markerHeight="8" refX="8" '
        'refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#8a8177"/>'
        "</marker></defs>"
    )
    p.append("</svg>")
    return "\n".join(p) + "\n"


SAIDAS = {
    "PIPELINE.svg": render_pipeline,
    "FUNIL.svg": render_funil,
    "REGIMES.svg": render_regimes,
    "SELECTION.svg": render_selection,
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
        print(f"os {len(SAIDAS)} SVGs estão atuais")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
