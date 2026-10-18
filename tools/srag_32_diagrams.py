"""Gera os quatro diagramas do módulo 00, com números medidos, em português.

Uso:
    python tools/srag_32_diagrams.py            # escreve os quatro SVGs
    python tools/srag_32_diagrams.py --check    # renderiza em memória e diffa

Saídas, todas em modules/00-dataset/:
    PIPELINE.svg   a jornada inteira: Bronze → Prata → Ouro → estudo → modelo
    FUNIL.svg      a variável-funil e os três estados do vazio
    REGIMES.svg    letalidade e fração COVID por ano — a base muda de regime
    SELECTION.svg  o estudo pré-registrado que escolheu o modelo do curso

Estrutura e contagens vêm das tabelas de tools/srag_30_silver.py, do
PROFILE.json e dos três JSON do Ouro (counts, selection_metrics,
model_metrics). O gerador não abre microdados, não refaz treinamento e não
introduz métricas: as taxas e os escores vêm dos registros versionados.

O desenho usa os papéis neutros SAPIANS/VITA documentados em tools/README.md,
com tipografia Satoshi e fallbacks explícitos. Textos são nativos e cada SVG
inclui título e descrição acessíveis. A seleção por AUC permanece histórica;
as comparações posteriores por log loss não substituem a referência das aulas.
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


# Papéis visuais da fundação SAPIANS/VITA; sem dependência de renderização.
INK = "#212322"
MUTED = "#606460"
BORDER = "#D9DCDA"
CANVAS = "#F2F3F3"
WHITE = "#FFFFFF"


def svg_start(height: int, title: str, description: str) -> list[str]:
    return [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 {height}" '
            'role="img" aria-labelledby="title desc" '
            'font-family="Satoshi, Inter, Arial, sans-serif">'
        ),
        f'<title id="title">{esc(title)}</title>',
        f'<desc id="desc">{esc(description)}</desc>',
        f'<rect width="1180" height="{height}" fill="{WHITE}"/>',
    ]


def text(
    p: list[str],
    x: float,
    y: float,
    label: str,
    size: int = 18,
    color: str = INK,
    weight: int = 400,
    anchor: str = "start",
) -> None:
    p.append(
        f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{color}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{esc(label)}</text>'
    )


def box(
    p: list[str],
    x: float,
    y: float,
    width: float,
    height: float,
    fill: str = CANVAS,
    stroke: str = BORDER,
) -> None:
    p.append(
        f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
        f'rx="8" fill="{fill}" stroke="{stroke}"/>'
    )


def heading(p: list[str], title: str, subtitle: str) -> None:
    text(p, 36, 35, "SAPIANS  /  DADOS DO CURSO", 14, MUTED, 500)
    text(p, 36, 78, title, 30, weight=500)
    text(p, 36, 110, subtitle, 17, MUTED)


def render_pipeline(m: dict) -> str:
    o, s, mo = m["ouro"], m["sel"], m["modelo"]
    sp, par = o["splits"], mo["params"]
    p = svg_start(
        1070,
        "Da notificação ao preditor das aulas",
        "Cinco etapas: origem preservada, tratamento, tarefa Gold, "
        "seleção histórica por AUC e referência explicada nas aulas. "
        "As comparações posteriores não substituem automaticamente a referência.",
    )
    heading(
        p,
        "Da notificação ao preditor das aulas",
        "Origem, decisões e referência publicada · números dos registros versionados",
    )
    rows = [
        (
            "BRONZE",
            "Preservar a origem",
            [
                f"{br(m['n_linhas'])} notificações · {br(m['n_cols'])} campos na união da série",
                f"Anos {m['anos'][0]}–{m['anos'][-1]} · extração {o['extracao']}",
                "Arquivos anuais preservados; a unidade é a notificação, não a pessoa.",
            ],
        ),
        (
            "SILVER",
            "Tratar a forma e registrar as regras",
            [
                f"{br(m['n_cols'] + m['derivadas'])} colunas = {br(m['n_cols'])} originais + {br(m['derivadas'])} derivadas",
                f"{br(m['portoes'])} portões no contrato · {br(m['familias'])} famílias de campos",
                "Estados do vazio e anomalias ficam explícitos; a linha não é reparada em silêncio.",
            ],
        ),
        (
            "GOLD",
            "Definir a tarefa retrospectiva",
            [
                f"{br(o['n'])} notificações elegíveis · {br(o['n_features'])} entradas do modelo",
                "Coorte hospitalizada + definição COVID ampla + desfecho registrado de cura ou óbito",
                f"Treino elegível: {br(sp['train']['n'])} · amostra usada: {br(o['amostra']['treino_amostrado'])}",
            ],
        ),
        (
            "SELEÇÃO",
            "Registrar a escolha histórica por AUC",
            [
                f"Validação {o['ano_val']}: {br(sp['val']['n'])} notificações · líder {s['lider']}",
                f"AUC de validação: {dec(s['val'][s['lider']]['auc'])} · teste histórico: {o['ano_teste']}",
                "O teste é excluído da função de escolha; suas leituras atuais são exploratórias.",
            ],
        ),
        (
            "REFERÊNCIA",
            "Explicar o preditor adotado nas aulas",
            [
                f"XGBoost · {br(par['n_estimators'])} árvores · profundidade {par['max_depth']} · taxa {num(par['learning_rate'])}",
                f"Teste {o['ano_teste']}: AUC {dec(mo['xgb_test']['auc'])} · Brier {dec(mo['xgb_test']['brier'])}",
                "As explicações locais e globais escolhem exemplares e apoios conforme cada método.",
            ],
        ),
    ]
    for i, (label, title, lines) in enumerate(rows):
        y = 145 + i * 160
        box(p, 36, y, 1108, 140)
        box(p, 56, y + 21, 172, 36, INK, INK)
        text(p, 142, y + 45, label, 16, WHITE, 500, "middle")
        text(p, 250, y + 34, title, 22, weight=500)
        for j, line in enumerate(lines):
            text(p, 250, y + 64 + j * 26, line, 17, MUTED)
        if i < len(rows) - 1:
            p.append(
                f'<path d="M142 {y + 144} v10 m-5 -5 l5 5 5 -5" '
                f'fill="none" stroke="{MUTED}" stroke-width="2"/>'
            )
    text(
        p,
        36,
        989,
        "Leitura: README → manifesto Gold → caderno do modelo → módulos de método.",
        19,
        weight=500,
    )
    text(
        p,
        36,
        1020,
        "Comparações posteriores por log loss: COURSE_STUDY.md. Não há substituição automática do modelo.",
        17,
        MUTED,
    )
    text(
        p,
        36,
        1048,
        "Fontes: PROFILE.json · contrato Silver · gold/counts.json · selection_metrics.json · model_metrics.json",
        14,
        MUTED,
    )
    return "\n".join(p + ["</svg>"]) + "\n"


def render_funil(m: dict) -> str:
    p = svg_start(
        810,
        "Vazio, ignorado e não aplicável são estados diferentes",
        "Esquema da regra de aplicabilidade das comorbidades. FATOR_RISC "
        "igual a 1 ou S habilita o bloco segundo o contrato. O valor vazio "
        "gera ausente ou não aplicável conforme o portão. Código 9 gera "
        "ignorado; os demais valores não vazios permanecem preenchidos.",
    )
    heading(
        p,
        "O mesmo vazio pode ter significados diferentes",
        "Exemplo do contrato Silver · aplicabilidade e valor são verificados separadamente",
    )
    box(p, 36, 150, 352, 160)
    text(p, 60, 184, "PORTÃO  /  FATOR_RISC", 17, weight=500)
    text(p, 60, 222, "1 ou S → bloco aplicável", 20, weight=500)
    text(p, 60, 255, "Outros valores → não aplicável", 17, MUTED)
    text(p, 60, 283, "Regra do contrato, não diagnóstico clínico.", 15, MUTED)
    box(p, 470, 150, 674, 160)
    text(p, 494, 184, f"{len(S.COMORBIDITIES)} CAMPOS DE COMORBIDADES", 17, weight=500)
    for j, line in enumerate(
        [
            "CARDIOPATI · DIABETES · ASMA · RENAL · OBESIDADE…",
            "O valor original permanece disponível.",
            "Cada campo recebe sua classificação em uma coluna _estado.",
        ]
    ):
        text(p, 494, 220 + j * 31, line, 18, MUTED)
    p.append(
        f'<path d="M404 230 h48 m-8 -6 l8 6 -8 6" fill="none" stroke="{INK}" stroke-width="2"/>'
    )
    text(p, 36, 358, "Quando o campo está vazio", 21, weight=500)
    states = [
        (
            "nao_aplicavel",
            "Vazio + portão desligado",
            "Não é ausência de um campo",
            "considerado aplicável pela regra.",
        ),
        (
            "ausente",
            "Vazio + portão habilitado",
            "O campo era aplicável,",
            "mas não tem valor registrado.",
        ),
        (
            "ignorado",
            "Código 9 explícito",
            "Há um registro de ignorado;",
            "não é o mesmo que uma célula vazia.",
        ),
    ]
    for i, (name, rule, l1, l2) in enumerate(states):
        x = 36 + i * 376
        box(p, x, 382, 356, 179, WHITE)
        text(p, x + 20, 418, name, 22, weight=500)
        text(p, x + 20, 454, rule, 17, weight=500)
        text(p, x + 20, 495, l1, 17, MUTED)
        text(p, x + 20, 522, l2, 17, MUTED)
    text(p, 808, 358, "Quando há código explícito", 21, weight=500)
    box(p, 36, 592, 1108, 132)
    text(
        p, 60, 627, "Preservar primeiro; decidir a codificação depois.", 23, weight=500
    )
    text(
        p,
        60,
        663,
        "Silver separa esses estados. Gold declara quais são fundidos nas entradas do modelo.",
        19,
        MUTED,
    )
    text(
        p,
        60,
        694,
        "Outro valor não vazio fica como preenchido; o domínio é verificado separadamente.",
        18,
        MUTED,
    )
    text(
        p,
        36,
        763,
        "Fonte: srag_30_silver.py · missing_state e GATES · leitura: Silver walkthrough §3 e internals §4",
        16,
        MUTED,
    )
    text(
        p,
        36,
        790,
        "O esquema explica a regra de tratamento; não representa uma contagem ou um efeito sobre o desfecho.",
        16,
        MUTED,
    )
    return "\n".join(p + ["</svg>"]) + "\n"


def render_regimes(m: dict) -> str:
    p = svg_start(
        710,
        "A composição das notificações muda entre os anos",
        "Dois painéis de barras com a mesma escala percentual. "
        "O primeiro mostra óbitos divididos por curas mais óbitos; "
        "o segundo mostra o código COVID dividido por todas as notificações. "
        "São denominadores distintos, calculados do perfil por ano da base bruta.",
    )
    heading(
        p,
        "A composição das notificações muda entre os anos",
        "Perfil da série bruta · proporções descritivas, com denominadores distintos",
    )
    configs = [
        ("Óbitos / (curas + óbitos)", "letalidade", INK, 36),
        ("COVID / notificações", "covid", MUTED, 616),
    ]
    for title, key, color, x0 in configs:
        text(p, x0 + 8, 164, title, 22, weight=500)
        bx, by, scale = x0 + 52, 480, 3.25
        for v in range(0, 81, 20):
            y = by - v * scale
            p.append(
                f'<line x1="{bx - 8}" y1="{y:g}" x2="{x0 + 526}" y2="{y:g}" stroke="{BORDER}"/>'
            )
            text(p, bx - 17, y + 5, f"{v}%", 14, MUTED, anchor="end")
        for i, r in enumerate(m["regimes"]):
            x = bx + i * 79
            height = r[key] * scale
            p.append(
                f'<rect x="{x:g}" y="{by - height:g}" width="46" height="{height:g}" fill="{color}"/>'
            )
            value = dec(r[key], 2 if r[key] < 1 else 1) + "%"
            text(p, x + 23, by - height - 12, value, 16, color, 500, "middle")
            text(p, x + 23, by + 28, r["ano"], 16, MUTED, anchor="middle")
    text(p, 36, 560, "Notificações no arquivo de cada ano", 18, weight=500)
    for i, r in enumerate(m["regimes"]):
        x = 36 + i * 186
        text(p, x, 594, r["ano"], 16, MUTED)
        text(p, x, 623, br(r["n"]), 20, weight=500)
    text(
        p,
        36,
        667,
        "Essas proporções descrevem os registros disponíveis; não isolam efeitos do ano nem estimam risco populacional.",
        17,
        MUTED,
    )
    text(
        p,
        36,
        696,
        "Fonte: PROFILE.json · EVOLUCAO 1/2 e CLASSI_FIN 5 · leitura: Silver internals §1",
        15,
        MUTED,
    )
    return "\n".join(p + ["</svg>"]) + "\n"


def render_selection(m: dict) -> str:
    o, s = m["ouro"], m["sel"]
    leader = s["lider"]
    p = svg_start(
        920,
        "A seleção histórica escolheu XGBoost pela AUC de validação",
        "Partições temporais e placar da seleção histórica. As barras "
        "mostram AUC na validação, com eixo iniciado em 0,50. "
        "A avaliação histórica de teste é apresentada separadamente e "
        "não constitui um novo teste independente.",
    )
    heading(
        p,
        "A seleção histórica escolheu XGBoost pela AUC",
        "Registro de seleção por discriminação · comparações posteriores por log loss estão em COURSE_STUDY.md",
    )
    blocks = [
        (
            "TREINO",
            f"Até {o['corte']}",
            f"{br(o['amostra']['treino_amostrado'])} notificações amostradas",
        ),
        (
            "VALIDAÇÃO",
            o["ano_val"],
            f"{br(o['splits']['val']['n'])} notificações · define a escolha",
        ),
        (
            "TESTE HISTÓRICO",
            o["ano_teste"],
            f"{br(o['splits']['test']['n'])} notificações · já observado",
        ),
    ]
    for i, (label, year, detail) in enumerate(blocks):
        x = 36 + i * 376
        box(p, x, 145, 356, 125)
        text(p, x + 20, 176, label, 16, MUTED, 500)
        text(p, x + 20, 214, year, 25, weight=500)
        text(p, x + 20, 246, detail, 16, MUTED)
    text(p, 36, 319, f"Placar de validação · {o['ano_val']}", 23, weight=500)
    text(
        p,
        36,
        348,
        "AUC maior é melhor · eixo truncado em 0,50 · cada barra representa o finalista da família",
        17,
        MUTED,
    )
    bx, ex, top, gap = 278, 964, 396, 53
    amin, amax = 0.5, 0.8

    def px(value: float) -> float:
        return bx + (value - amin) / (amax - amin) * (ex - bx)

    for j in range(7):
        v = amin + j * 0.05
        x = px(v)
        p.append(f'<line x1="{x:g}" y1="378" x2="{x:g}" y2="695" stroke="{BORDER}"/>')
        text(p, x, 724, dec(v, 2), 15, MUTED, anchor="middle")
    for i, name in enumerate(s["ordem"]):
        y = top + i * gap
        auc = s["val"][name]["auc"]
        color = INK if name == leader else MUTED
        label = name + (" · escolhido" if name == leader else "")
        text(p, bx - 22, y + 13, label, 19, color, 500, "end")
        text(
            p,
            bx - 22,
            y + 35,
            f"{br(s['n_iter'][name])} de {br(s['espaco'][name])} "
            + ("configuração" if s["espaco"][name] == 1 else "configurações"),
            14,
            MUTED,
            anchor="end",
        )
        width = max(0, px(auc) - bx)
        if width:
            p.append(
                f'<rect x="{bx}" y="{y - 4}" width="{width:g}" height="25" rx="2" fill="{color}"/>'
            )
        else:
            p.append(f'<circle cx="{bx}" cy="{y + 8}" r="4" fill="{color}"/>')
        text(p, px(auc) + 12, y + 15, dec(auc), 19, color, 500)
    box(p, 36, 759, 1108, 109)
    text(
        p,
        60,
        792,
        f"Teste histórico do escolhido: AUC {dec(s['teste'][leader]['auc'])}",
        22,
        weight=500,
    )
    text(
        p,
        60,
        825,
        "O código exclui o teste da função de escolha. Isso não apaga as leituras anteriores desse período.",
        18,
        MUTED,
    )
    text(
        p,
        60,
        852,
        "A referência das aulas permanece identificada; uma comparação posterior não a substitui em silêncio.",
        17,
        MUTED,
    )
    text(
        p,
        36,
        901,
        "Fonte: gold/selection_metrics.json · protocolo e regras: SELECTION.md · contexto atual: README",
        15,
        MUTED,
    )
    return "\n".join(p + ["</svg>"]) + "\n"


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
