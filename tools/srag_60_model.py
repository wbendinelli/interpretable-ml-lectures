"""O modelo do curso: um XGBoost, uma logística, um paciente — por regra.

Uso:
    python3 tools/srag_60_model.py --metrics  # regenera gold/model_metrics.json
    python3 tools/srag_60_model.py --card     # regenera modules/00-dataset/MODEL.md

Os cinco módulos de método explicam O MESMO modelo por construção, não
por disciplina: todos refazem o fit a partir da amostra commitada
(`modules/00-dataset/gold/gold_covid_obito_sample.parquet`), que é
determinística (val e test inteiros; treino 200k, semente 42). Um binário
commitado ficaria soldado à versão do xgboost e seria ininspecionável; a
amostra é diffável, e o refit leva segundos.

O paciente-exemplo não é um índice mágico (o "#67" da era BCW): é uma
REGRA — |p − 0,5| mínimo no teste, empate por gold_id — aplicada ao
modelo-da-amostra, o mesmo que os módulos usam. O internals confere se o
modelo cheio escolheria o mesmo.

`gate_impossible()` centraliza as quatro contagens de impossibilidade
(portão do funil, pré-campanha, critérios da coorte) para que os cinco
módulos imprimam números idênticos por construção; `gate_reasons()`
devolve as MESMAS cercas abertas motivo a motivo, que é o que os módulos
03, 04 e 05 imprimem lado a lado.

Este arquivo é a fase 60 e é lido pelo hook `model-card-generated` num
venv mínimo (pandas + pyarrow): fora numpy/pandas/json/pathlib/sys, nada
entra no topo — `srag_40_gold` é import preguiçoso, e importar
`srag_70_explain` (a fase 70, os núcleos de explicação) daqui é proibido.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
AMOSTRA = ROOT / "modules/00-dataset/gold/gold_covid_obito_sample.parquet"
COUNTS_JSON = ROOT / "modules/00-dataset/gold/counts.json"
METRICS_JSON = ROOT / "modules/00-dataset/gold/model_metrics.json"
MODEL_MD = ROOT / "modules/00-dataset/MODEL.md"

CAMPANHA = pd.Timestamp("2021-01-17")
MESES_CAMPANHA = (CAMPANHA - pd.Timestamp("2020-03-01")).days / 30.44

NUMERICAS: tuple[str, ...] = (
    "idade_anos",
    "n_doses_antes_do_sintoma",
    "meses_desde_mar2020",
    "semana_epi",
)
BOOLEANAS: tuple[str, ...] = ("vacina_covid_declarada", "coinfeccao_outro_virus")
CATEGORICAS: tuple[str, ...] = (
    "cs_sexo",
    "cs_raca",
    "cs_escol_n",
    "cs_zona",
    "cs_gestant",
    "puerpera",
    "cardiopati",
    "hematologi",
    "sind_down",
    "hepatica",
    "asma",
    "diabetes",
    "neurologic",
    "pneumopati",
    "imunodepre",
    "renal",
    "obesidade",
    "out_morbi",
    "febre",
    "tosse",
    "garganta",
    "dispneia",
    "desc_resp",
    "saturacao",
    "diarreia",
    "vomito",
    "dor_abd",
    "fadiga",
    "perd_olft",
    "perd_pala",
    "outro_sin",
    "regiao",
    "capital_interior",
    "nosocomial",
)

# As quatro famílias das categóricas, como FATIAS de CATEGORICAS — nunca
# como literais reeditados: uma coluna inserida no meio da tupla move a
# fatia junto, e o `assert` abaixo reprova qualquer desalinhamento no
# import. Os módulos 01-05 liam `CATEGORICAS[5:18]` a olho; o índice mágico
# some daqui para o mesmo lugar onde a tupla mora.
DEMOGRAFIA: tuple[str, ...] = CATEGORICAS[:5]
COMORBIDADES: tuple[str, ...] = CATEGORICAS[5:18]
SINTOMAS: tuple[str, ...] = CATEGORICAS[18:31]
CONTEXTO: tuple[str, ...] = CATEGORICAS[31:34]
assert DEMOGRAFIA + COMORBIDADES + SINTOMAS + CONTEXTO == CATEGORICAS

FEATURES: tuple[str, ...] = NUMERICAS + BOOLEANAS + CATEGORICAS  # 40

# A que família cada uma das 40 features pertence — o dicionário que os
# módulos 04 (walkthrough e internals) montavam à mão, idêntico nos dois.
# As numéricas e booleanas são atribuídas uma a uma porque o agrupamento
# delas é semântico, não posicional: `coinfeccao_outro_virus` conta como
# comorbidade e as duas colunas de vacina como "dose".
# `semana_epi` entra como "tempo" (os cadernos não a listavam porque ela
# fica fora do cardápio de movimentos do módulo 04 — atrelada a
# `meses_desde_mar2020`); a chave a mais não muda nenhuma conta, e fecha a
# promessa do nome: TODAS as 40 features têm grupo.
GRUPO_DE_FEATURE: dict[str, str] = {
    **{c: "demografia" for c in DEMOGRAFIA},
    **{c: "comorbidade" for c in COMORBIDADES},
    **{c: "sintoma" for c in SINTOMAS},
    **{c: "contexto" for c in CONTEXTO},
    "idade_anos": "demografia",
    "meses_desde_mar2020": "tempo",
    "semana_epi": "tempo",
    "n_doses_antes_do_sintoma": "dose",
    "vacina_covid_declarada": "dose",
    "coinfeccao_outro_virus": "comorbidade",
}
assert set(GRUPO_DE_FEATURE) == set(FEATURES)

# Escolhidos pelo estudo pré-registrado de 2026-09-01 (SELECTION.md):
# vencedor da busca com seleção na validação 2023, teste 2024 lido uma vez.
# Sem subsample/colsample (default 1.0): a determinância de semente dos
# módulos 01/02 depende disso.
XGB_PARAMS = {
    "n_estimators": 800,
    "max_depth": 4,
    "learning_rate": 0.05,
    "min_child_weight": 100,
    "reg_lambda": 5.0,
    "tree_method": "hist",
    "enable_categorical": True,
    "eval_metric": "auc",
    "random_state": 42,
    "n_jobs": -1,
}
LOGIT_PARAMS = {"max_iter": 2000, "solver": "lbfgs"}


def load_gold(path: pathlib.Path | None = None) -> pd.DataFrame:
    """A amostra commitada por default; o Ouro completo quando apontado."""
    g = pd.read_parquet(path or AMOSTRA)
    faltam = [c for c in FEATURES if c not in g.columns]
    if faltam:
        raise ValueError(f"Gold sem as features: {faltam}")
    # pd.concat entre partes anuais rebaixa categoria->object quando os
    # níveis diferem entre anos; o dtype é imposto aqui, uma vez, para
    # todos os consumidores
    for c in CATEGORICAS:
        g[c] = g[c].astype("category")
    return g


def design_matrix(g: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    """(X para o XGBoost, X para a logística, y).

    O XGBoost recebe as categóricas nativas. A logística recebe one-hot
    (drop_first) e a semana vira seno/cosseno — uma rampa 1..53 com salto
    em dezembro seria pior que a sazonalidade contínua. A assimetria é
    declarada no MODEL.md.
    """
    x_xgb = g[list(FEATURES)].copy()
    for c in BOOLEANAS:
        x_xgb[c] = x_xgb[c].astype(bool)

    x_log = g[list(NUMERICAS + BOOLEANAS)].copy()
    x_log["semana_sin"] = np.sin(2 * np.pi * g["semana_epi"] / 52.0)
    x_log["semana_cos"] = np.cos(2 * np.pi * g["semana_epi"] / 52.0)
    x_log = x_log.drop(columns=["semana_epi"])
    for c in BOOLEANAS:
        x_log[c] = x_log[c].astype(int)
    dummies = pd.get_dummies(g[list(CATEGORICAS)], drop_first=True, dtype=np.int8)
    x_log = pd.concat([x_log, dummies], axis=1)

    y = g["y_obito"].to_numpy()
    return x_xgb, x_log, y


def fit_models(g: pd.DataFrame):
    """(xgb, logit_pipeline), treinados no split de treino de `g`."""
    import xgboost as xgb
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    x_xgb, x_log, y = design_matrix(g)
    tr = (g["split"] == "train").to_numpy()

    modelo_xgb = xgb.XGBClassifier(**XGB_PARAMS)
    modelo_xgb.fit(x_xgb[tr], y[tr])

    logit = Pipeline(
        [
            ("imputa", SimpleImputer(strategy="median")),
            ("escala", StandardScaler()),
            ("logit", LogisticRegression(**LOGIT_PARAMS)),
        ]
    )
    logit.fit(x_log[tr], y[tr])
    return modelo_xgb, logit


def predict_proba(modelo, g: pd.DataFrame) -> np.ndarray:
    """Probabilidade de óbito, cuidando de qual matriz cada modelo espera."""
    x_xgb, x_log, _ = design_matrix(g)
    if modelo.__class__.__module__.startswith("xgboost"):
        return modelo.predict_proba(x_xgb)[:, 1]
    return modelo.predict_proba(x_log)[:, 1]


def metrics(modelo, g: pd.DataFrame, split: str) -> dict:
    from sklearn.metrics import brier_score_loss, roc_auc_score

    m = (g["split"] == split).to_numpy()
    p = predict_proba(modelo, g[m])
    y = g.loc[m, "y_obito"].to_numpy()
    return {
        "split": split,
        "n": int(m.sum()),
        "obitos": int(y.sum()),
        "auc": round(float(roc_auc_score(y, p)), 4),
        "brier": round(float(brier_score_loss(y, p)), 4),
        "previsto_medio": round(float(p.mean()), 4),
        "observado": round(float(y.mean()), 4),
    }


def pick_exemplar(modelo, g: pd.DataFrame, split: str = "test") -> pd.Series:
    """|p − 0,5| mínimo no split, empate por gold_id — regra, não índice."""
    m = (g["split"] == split).to_numpy()
    sub = g[m].reset_index(drop=True)
    p = predict_proba(modelo, sub)
    ordem = np.lexsort((sub["gold_id"].to_numpy(), np.abs(p - 0.5)))
    escolhido = sub.iloc[ordem[0]].copy()
    escolhido["p_obito"] = float(p[ordem[0]])
    return escolhido


def pick_vulneravel(modelo, g: pd.DataFrame, split: str | None = None) -> pd.Series:
    """O segundo paciente dos módulos 01 e 03 — a MESMA regra, outro recorte.

    A regra dita, palavra por palavra: entre as linhas que já estão em
    ESTADO VULNERÁVEL às três cercas ao mesmo tempo — sem fator de risco
    declarado (portão), início antes de a campanha existir (calendário) e
    critério-2 por um fio (`n_crit2 == 1`) —, aquela com |p − 0,5| mínimo,
    empate por `gold_id`. É o `pick_exemplar` aplicado a um subconjunto, e
    não um índice escolhido a dedo.

    `split=None` (o default) varre a amostra inteira, que é o que os três
    cadernos faziam em linha: o estado vulnerável é raro, e restringi-lo ao
    teste mudaria o paciente. Passar `"test"` restringe, para quem quiser a
    simetria com `pick_exemplar`.
    """
    base = g if split is None else g[(g["split"] == split).to_numpy()]
    vulneraveis = base[
        (~base["fator_risc_portao"].astype(bool))
        & (base["meses_desde_mar2020"] < MESES_CAMPANHA)
        & (base["n_crit2"] == 1)
    ].reset_index(drop=True)
    p = predict_proba(modelo, vulneraveis)
    ordem = np.lexsort((vulneraveis["gold_id"].to_numpy(), np.abs(p - 0.5)))
    escolhido = vulneraveis.iloc[ordem[0]].copy()
    escolhido["p_obito"] = float(p[ordem[0]])
    return escolhido


def paciente_2021(modelo, g: pd.DataFrame) -> pd.Series:
    """A mesma regra, restrita a 2021 — o mesmo método sob outro regime."""
    sub = g[(g["split"] == "train") & (g["ano_onset"] == 2021)].reset_index(drop=True)
    p = predict_proba(modelo, sub)
    ordem = np.lexsort((sub["gold_id"].to_numpy(), np.abs(p - 0.5)))
    escolhido = sub.iloc[ordem[0]].copy()
    escolhido["p_obito"] = float(p[ordem[0]])
    return escolhido


GATE_REASONS: tuple[str, ...] = ("portao", "pre_campanha", "fora_coorte")


def gate_reasons(rows: pd.DataFrame) -> pd.DataFrame:
    """As três impossibilidades, uma coluna booleana cada — a decomposição.

    `gate_impossible` responde "esta linha pode existir?"; esta função
    responde POR QUE não, e é dela que saem os números que os módulos 03,
    04 e 05 imprimem lado a lado (portão / pré-campanha / fora da coorte).
    Os três motivos, medidos no módulo 00:

    - `portao`: comorbidade "sim" com `fator_risc_portao` False contradiz
      um portão medido em 0,00% nos seis anos;
    - `pre_campanha`: qualquer dose antes de a campanha existir
      (início < 2021-01-17);
    - `fora_coorte`: sem critério-2 (tosse/garganta) ou sem critério-3
      (dispneia/saturação/desconforto), a linha nem seria SRAG.

    O quadro é montado a partir de arrays NumPy com `index=rows.index`
    explícito, nunca de Series alinhadas: os frames perturbados que os
    módulos constroem à mão podem ter índice repetido, e um `pd.concat`
    por eixo 1 sobre índice repetido faz produto cartesiano em silêncio.
    """
    n_linhas = len(rows)

    alguma_sim = np.zeros(n_linhas, dtype=bool)
    for c in COMORBIDADES:
        alguma_sim |= (rows[c].astype(str) == "sim").to_numpy()
    portao = alguma_sim & ~rows["fator_risc_portao"].astype(bool).to_numpy()

    pre_campanha = (rows["meses_desde_mar2020"] < MESES_CAMPANHA).to_numpy() & (
        rows["n_doses_antes_do_sintoma"] > 0
    ).to_numpy()

    # Os critérios da coorte são RECONTADOS dos sintomas quando as colunas
    # estão presentes — uma varredura que muda `tosse` tem de mover a cerca
    # junto; ler o n_crit2 congelado deixaria o flip do sintoma-fio passar
    # (bug pego pelo módulo 01 na primeira rodada).
    def _conta(cols: tuple[str, ...], fallback: str) -> np.ndarray:
        presentes = [c for c in cols if c in rows.columns]
        if len(presentes) == len(cols):
            return sum(
                (rows[c].astype(str) == "sim").to_numpy().astype(int) for c in presentes
            )
        return rows[fallback].to_numpy()

    n2 = _conta(("tosse", "garganta"), "n_crit2")
    n3 = _conta(("dispneia", "saturacao", "desc_resp"), "n_crit3")
    fora_coorte = (n2 < 1) | (n3 < 1)

    return pd.DataFrame(
        {"portao": portao, "pre_campanha": pre_campanha, "fora_coorte": fora_coorte},
        index=rows.index,
    )


def gate_impossible(rows: pd.DataFrame) -> pd.Series:
    """True onde uma linha (real ou perturbada) contradiz o que não tem como existir.

    As três fontes exatas, medidas no módulo 00:
    - o portão do funil: comorbidade "sim" com `fator_risc_portao` False
      contradiz um portão medido em 0,00% nos seis anos;
    - o calendário: qualquer dose antes de a campanha existir
      (início < 2021-01-17);
    - a definição da coorte: sem critério-2 (tosse/garganta) ou sem
      critério-3 (dispneia/saturação/desconforto), a linha nem seria SRAG.

    É o OU das colunas de `gate_reasons` — uma definição, dois formatos.
    """
    return gate_reasons(rows).any(axis=1)


# --------------------------------------------------------------------------
# model_metrics.json, gerado — função pura da amostra commitada.
# --------------------------------------------------------------------------
def sha256_projecao_canonica(g: pd.DataFrame) -> str:
    """Hash de conteúdo de uma projeção CSV canônica — os bytes do parquet
    não são estáveis entre versões do pyarrow, então nunca são comparados.

    Delega para `srag_40_gold.sha256_amostra` (colunas ordenadas, float32
    arredondado a 4 casas antes do CSV): a receita vivia duplicada aqui,
    agora há uma fonte só. Import local — `srag_40_gold` só entra em memória
    quando esta função roda de fato (em `--metrics`), não em `--card`/
    `--check-card`, que é o caminho que o hook `model-card-generated`
    executa no venv mínimo (pandas+pyarrow, sem xgboost/sklearn); e
    `srag_40_gold` por sua vez só puxa `srag_30_silver`, que só puxa
    numpy/pandas/pyarrow — nada mais pesado entra.
    """
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import srag_40_gold

    return srag_40_gold.sha256_amostra(g)


def resumo_paciente(row: pd.Series) -> str:
    """Frase PT de um paciente: idade, sexo, região, início, doses, comorbidades.

    idade_anos é arredondada ao ano mais próximo (a coluna carrega meses);
    sexo e região saem crus da coorte; as comorbidades são as mesmas 13
    colunas que `gate_impossible` varre por "sim" (`COMORBIDADES`), na
    ordem em que aparecem — não em ordem alfabética.
    """
    comorbidades = [c for c in COMORBIDADES if str(row[c]) == "sim"]
    lista = ", ".join(comorbidades) if comorbidades else "nenhuma"
    return (
        f"{round(float(row['idade_anos']))} anos, {row['cs_sexo']}, "
        f"{row['regiao']}, início em {int(row['ano_onset'])} "
        f"(semana {int(row['semana_epi'])}), "
        f"{int(row['n_doses_antes_do_sintoma'])} dose(s) antes do sintoma, "
        f"comorbidades: {lista}"
    )


def compute_metrics() -> dict:
    """Refaz `gold/model_metrics.json` inteiro a partir da amostra commitada.

    Única fonte de verdade: `gold/gold_covid_obito_sample.parquet` (via
    `load_gold`/`fit_models`) e `gold/counts.json` para `treino_total` — o
    tamanho do treino CHEIO não é recuperável da amostra (o treino nela é
    subamostrado a 200 mil das 1,24 M linhas), então esse único número vem
    do manifesto, não da amostra.

    `xgb_params` deliberadamente NÃO inclui `n_jobs`: controla paralelismo
    da máquina, não o modelo ajustado, e não é uma das colunas que o model
    card imprime.
    """
    g = load_gold()
    xgb, logit = fit_models(g)

    counts = json.loads(COUNTS_JSON.read_text(encoding="utf-8"))

    ex = pick_exemplar(xgb, g)
    p21 = paciente_2021(xgb, g)
    n = len(g)

    impossibilidades = {
        "portão do funil (sem fator de risco declarado)": round(
            100 * float((~g["fator_risc_portao"].astype(bool)).sum()) / n, 2
        ),
        "pré-campanha (nenhuma dose pode existir)": round(
            100 * float((g["meses_desde_mar2020"] < MESES_CAMPANHA).sum()) / n, 2
        ),
        "critério-2 por um fio (só tosse OU só garganta)": round(
            100 * float((g["n_crit2"] == 1).sum()) / n, 2
        ),
        "critério-3 por um fio": round(100 * float((g["n_crit3"] == 1).sum()) / n, 2),
    }

    return {
        "amostra": {
            "bytes": AMOSTRA.stat().st_size,
            "n": n,
            "sha256_projecao_canonica": sha256_projecao_canonica(g),
            "treino_amostrado": int((g["split"] == "train").sum()),
            "treino_total": counts["splits"]["train"]["n"],
        },
        "exemplar": {
            "gold_id": int(ex["gold_id"]),
            "p_obito": float(ex["p_obito"]),
            "resumo": resumo_paciente(ex),
        },
        "impossibilidades": impossibilidades,
        "linhas_reais_impossiveis": int(gate_impossible(g).sum()),
        "logit": [metrics(logit, g, s) for s in ("val", "test")],
        "paciente_2021": {
            "gold_id": int(p21["gold_id"]),
            "p_obito": float(p21["p_obito"]),
        },
        "xgb": [metrics(xgb, g, s) for s in ("val", "test")],
        "xgb_params": {k: v for k, v in XGB_PARAMS.items() if k != "n_jobs"},
    }


# --------------------------------------------------------------------------
# O model card, gerado — função pura de model_metrics.json.
# --------------------------------------------------------------------------
def render_card(mm: dict) -> str:
    L = [
        "# MODEL.md — o modelo do curso",
        "",
        "Gerado por `tools/srag_60_model.py --card` de `gold/model_metrics.json`.",
        "Não editar à mão. Os cinco módulos de método explicam ESTE modelo:",
        "todos refazem o fit da amostra commitada (determinística), então",
        '"um modelo, um paciente" é garantia de código, não de disciplina.',
        "",
        "## O que é",
        "",
        f"- **XGBoost** {mm['xgb_params']['n_estimators']} árvores,",
        (
            f"  profundidade {mm['xgb_params']['max_depth']}, lr"
            f" {mm['xgb_params']['learning_rate']},"
            f" min_child_weight {mm['xgb_params']['min_child_weight']},"
            f" reg_lambda {mm['xgb_params']['reg_lambda']},"
        ),
        (
            f"  `hist`, categóricas nativas, semente"
            f" {mm['xgb_params']['random_state']} — o modelo que os"
        ),
        "  métodos explicam. A escolha destes parâmetros está em",
        "  [`SELECTION.md`](SELECTION.md): protocolo pré-registrado,",
        "  seis candidatos, seleção na validação, teste lido uma vez.",
        "- **Regressão logística** (imputação mediana + padronização +",
        "  one-hot; semana como seno/cosseno) — o baseline interpretável.",
        "- **40 features** do Ouro (manifesto §2.5); alvo `y_obito`;",
        "  split temporal treino ≤2022 / val 2023 / teste 2024.",
        "- Treinado na **amostra commitada** (val e teste inteiros; treino"
        f" {mm['amostra']['treino_amostrado']:,} de".replace(",", ".")
        + f" {mm['amostra']['treino_total']:,}".replace(",", ".")
        + ").",
        "",
        "## Métricas",
        "",
        "| modelo | split | n | AUC | Brier | previsto médio | observado |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for nome in ("xgb", "logit"):
        for m in mm[nome]:
            L.append(
                f"| {nome} | {m['split']} | {m['n']:,} | {m['auc']} | "
                f"{m['brier']} | {m['previsto_medio']} | {m['observado']} |".replace(
                    ",", "."
                )
            )
    L += [
        "",
        "O gap de calibração no teste (previsto acima do observado) é o",
        "**achado da deriva de regime**, não um defeito a esconder: o modelo",
        "aprendeu letalidades de 2020–22 e o mundo de 2024 é outro — é",
        "exatamente o que os módulos de método vão explicar.",
        "",
        "## O paciente-exemplo",
        "",
        "Regra: |p − 0,5| mínimo no teste, empate por `gold_id` — aplicada ao",
        "modelo-da-amostra, o que os módulos usam.",
        "",
        (
            f"- `gold_id` = {mm['exemplar']['gold_id']}, p(óbito) ="
            f" {mm['exemplar']['p_obito']:.3f}"
        ),
        f"- {mm['exemplar']['resumo']}",
        (
            f"- Segundo paciente (mesma regra em 2021): `gold_id` ="
            f" {mm['paciente_2021']['gold_id']}, p ="
            f" {mm['paciente_2021']['p_obito']:.3f}"
        ),
        "",
        "## As quatro impossibilidades (gate_impossible)",
        "",
        "| restrição | fração da amostra em estado vulnerável |",
        "|---|---:|",
    ]
    for nome, val in mm["impossibilidades"].items():
        L.append(f"| {nome} | {val}% |")
    L += [
        "",
        "Perturbar uma linha através de uma dessas fronteiras fabrica um",
        "paciente que não pode existir — a conta que os módulos 01–05 fazem,",
        "todos pela MESMA função, para imprimirem números idênticos por",
        "construção.",
        "",
        "## Limites declarados",
        "",
        "- Imagem (RAIOX/TOMO) fora das features; a célula-armadilha do",
        "  walkthrough mede o que o modelo teria aprendido (a AUSÊNCIA do",
        "  registro prediz óbito — qualidade de documentação vazando).",
        "- `UTI`/`SUPORT_VEN` fora — campos do episódio inteiro, preenchidos",
        "  no encerramento; a justificativa medida e referenciada está no",
        "  [`GOLD.md`](GOLD.md) (decisão 3).",
        "- Sem pesos de classe (manifesto §2.7).",
        "- O delta amostra→cheio está no internals do modelo.",
    ]
    return "\n".join(L).rstrip("\n") + "\n"


def _le_metrics() -> dict | None:
    if not METRICS_JSON.exists():
        print(
            f"{METRICS_JSON} não existe — rode"
            " `python3 tools/srag_60_model.py --metrics` primeiro",
            file=sys.stderr,
        )
        return None
    return json.loads(METRICS_JSON.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if "--metrics" in argv:
        mm = compute_metrics()
        METRICS_JSON.write_text(
            json.dumps(mm, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"{METRICS_JSON}")
        return 0
    if "--card" in argv:
        mm = _le_metrics()
        if mm is None:
            return 1
        MODEL_MD.write_text(render_card(mm), encoding="utf-8")
        print(f"{MODEL_MD}")
        return 0
    if "--check-card" in argv:
        mm = _le_metrics()
        if mm is None:
            return 1
        problemas = []
        em_disco = MODEL_MD.read_text(encoding="utf-8") if MODEL_MD.exists() else ""
        if em_disco != render_card(mm):
            problemas.append("MODEL.md divergiu de model_metrics.json")
        xgb_params_hoje = {k: v for k, v in XGB_PARAMS.items() if k != "n_jobs"}
        if xgb_params_hoje != mm["xgb_params"]:
            problemas.append(
                "XGB_PARAMS (tools/srag_60_model.py) divergiu de"
                " model_metrics.json['xgb_params'] — rode --metrics e --card"
                " após mudar XGB_PARAMS"
            )
        if problemas:
            for p in problemas:
                print(p, file=sys.stderr)
            return 1
        print("MODEL.md em dia")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
