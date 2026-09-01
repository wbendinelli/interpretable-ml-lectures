"""O estudo que escolheu o modelo do curso: seis formas, um protocolo.

Uso:
    # roda as buscas, escreve gold/selection_metrics.json e imprime o
    # bloco MELHORES pronto para colar aqui em cima:
    python3 tools/srag_selection.py --search
    # regenera modules/00-dataset/SELECTION.md do JSON:
    python3 tools/srag_selection.py --card
    python3 tools/srag_selection.py --check-card

O modelo do curso (`tools/srag_model.py`) é um XGBoost com três
hiperparâmetros escritos à mão. Este módulo é a auditoria dessa escolha,
e ele existe para que a auditoria seja verificável em vez de contada:

* o critério é PRÉ-REGISTRADO (`CRITERIO`), com data, hipótese
  registrada e consequência declarada, antes de qualquer número;
* a escolha é feita por uma FUNÇÃO (`pick_model`), não por narrativa —
  e ela levanta exceção se receber uma linha de `split == "test"`;
* o teste (2024) é lido UMA vez, depois de escolhido, pelo placar.

A seleção acontece na validação temporal (2023 inteiro). A alternativa de
mercado — `cv=5` embaralhado sobre 2020–2022 — é medida aqui como
armadilha (`search_kfold`), não descartada por argumento.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import srag_model as M

ROOT = pathlib.Path(__file__).resolve().parent.parent
METRICS_JSON = ROOT / "modules/00-dataset/gold/selection_metrics.json"
SELECTION_MD = ROOT / "modules/00-dataset/SELECTION.md"
SEMENTE = 42

MODELOS = ("dummy", "lpm", "logit", "arvore", "floresta", "xgb")

# A forma da função ajustada — é ISSO que o curso terá de explicar
# depois, e por isso a coluna existe ao lado da AUC.
FORMA: dict[str, str] = {
    "dummy": "constante",
    "lpm": "linear aditivo em p",
    "logit": "linear aditivo em log-odds",
    "arvore": "regras hierárquicas",
    "floresta": "ensemble por bagging",
    "xgb": "ensemble aditivo por boosting",
}
MOLNAR: dict[str, str] = {
    "dummy": "—",
    "lpm": "cap. 6",
    "logit": "cap. 7",
    "arvore": "cap. 9",
    "floresta": "—",
    "xgb": "—",
}
# Qual das três matrizes cada modelo recebe (ver `matrices`).
MATRIZ_DE = {
    "dummy": "linear",
    "lpm": "linear",
    "logit": "linear",
    "arvore": "arvore",
    "floresta": "arvore",
    "xgb": "xgb",
}

# Hiperparâmetros FIXOS: não entram na busca, e cada um que não é óbvio
# vem com o motivo escrito ao lado.
FIXOS: dict[str, dict] = {
    # `l1_ratio=0.0` É a penalidade l2 explícita. O sklearn 1.9 deprecou
    # `penalty=` (sai na 1.10) e avisa a CADA fit; o argumento moderno diz
    # a mesma coisa sem sujar a saída commitada dos notebooks — medido
    # aqui: mesmos coeficientes, mesma norma, que `penalty="l2"`.
    "logit": {"max_iter": 2000, "solver": "lbfgs", "l1_ratio": 0.0},
    "arvore": {"random_state": 42},
    "floresta": {
        "n_estimators": 300,
        "bootstrap": True,
        "n_jobs": -1,
        "random_state": 42,
    },  # n_estimators é orçamento, não hiperparâmetro (Breiman): mais
    # árvores nunca pioram o bagging, só custam — o internals mede a
    # saturação em vez de deixar a grade "escolher" o número
    "xgb": {
        "tree_method": "hist",
        "enable_categorical": True,
        "eval_metric": "auc",
        "subsample": 1.0,
        "colsample_bytree": 1.0,
        "random_state": 42,
        "n_jobs": -1,
    },  # subsample/colsample fixos em 1,0: a determinância de semente
    # (correlação 1,0000 entre 12 sementes; 0,979 com subsample 0,8) é
    # lição dos módulos 01/02 — uma explicação que muda quando a semente
    # muda não é explicação. O custo em AUC da restrição é medido no
    # internals, não presumido zero.
}

# Os espaços de busca, em ordem fixa (a busca é determinística: as
# configurações são ordenadas pelo JSON antes de rodar).
ESPACOS: dict[str, dict[str, list]] = {
    "dummy": {"strategy": ["prior"]},
    "lpm": {},  # sem hiperparâmetros — é o ponto (Molnar cap. 6)
    "logit": {"C": [0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0]},
    "arvore": {
        "max_depth": [3, 4, 5, 6, 8, 10, 12, None],
        "min_samples_leaf": [20, 50, 200, 1000, 5000],
        "ccp_alpha": [0.0, 1e-6, 1e-5, 1e-4],
        "criterion": ["gini", "log_loss"],
    },
    "floresta": {
        "max_depth": [8, 12, 16],
        "min_samples_leaf": [5, 20, 50, 200],
        "max_features": ["sqrt", 0.3],
    },
    "xgb": {
        "n_estimators": [200, 400, 800],
        "max_depth": [3, 4, 5, 6, 8],
        "learning_rate": [0.03, 0.05, 0.08, 0.15],
        "min_child_weight": [1, 5, 20, 100],
        "reg_lambda": [0.5, 1.0, 5.0, 20.0],
    },
}
# O orçamento por modelo, declarado ANTES de olhar: é o que impede a
# busca de virar "mais trials até o número ficar bonito".
N_ITER = {"dummy": 1, "lpm": 1, "logit": 7, "arvore": 24, "floresta": 10, "xgb": 30}

# A armadilha, com orçamento fixo para que a ÚNICA diferença entre as
# quatro configurações seja a profundidade — o que se compara é o
# protocolo de validação, não o tamanho do modelo.
TRAP_XGB: dict[str, list] = {
    "max_depth": [3, 5, 7, 9],
    "n_estimators": [150],
    "learning_rate": [0.08],
}
# A sondagem L1 (`l1_ratio=1.0`, ver o comentário em FIXOS): `saga` é o
# único solver que faz l1 aqui, e é o braço MAIS LENTO do estudo —
# iterativo, 200 mil linhas, minutos por C. É sondagem, não candidato:
# não entra no placar nem na escolha, e existe para responder se a
# esparsidade custa AUC nesta base.
L1_SONDAGEM: dict[str, list] = {
    "l1_ratio": [1.0],
    "solver": ["saga"],
    # `saga` embaralha as linhas e usa `random_state` — sem semente, duas
    # rodadas do MESMO estudo dão AUCs diferentes na 4ª casa (medido). O
    # `lbfgs` do resto do zoo não usa este argumento.
    "random_state": [42],
    "C": [0.01, 0.1, 1.0],
}

# Preenchido colando a saída de --search; --check-card garante que não
# diverge do JSON.
MELHORES: dict[str, dict] = {}

# A tabela estática do card: o que o default de mercado faria com esta
# base, e o que este estudo faz no lugar. Cada linha é uma decisão que
# alguém quererá "corrigir" — está aqui para que a correção tenha de
# passar pelo motivo.
MERCADO: tuple[tuple[str, str, str], ...] = (
    (
        "`RandomizedSearchCV(cv=5` embaralhado`)`",
        "mistura 2020–22 nas dobras",
        "seleção na val 2023 (a armadilha, medida acima)",
    ),
    (
        "Optuna, 100–500 trials",
        "500 leituras das mesmas 24k linhas = sobreajuste de seleção",
        "orçamento declarado + EP bootstrap",
    ),
    (
        "retreinar em treino+val antes do deploy",
        "perderia o único conjunto de seleção honesto",
        "não retreina (o internals mede o que isso custa)",
    ),
    (
        "early stopping na validação",
        "é busca de `n_estimators` fora do orçamento declarado",
        "`n_estimators` está na grade, contado",
    ),
    (
        "SMOTE / `class_weight`",
        "destruiria a história de calibração (MANIFEST §2.7)",
        "a prevalência entra como linha do placar: o Dummy",
    ),
    (
        'espiar o teste "só uma vez" no meio',
        "invalida a estimativa que o teste existe para dar",
        "`pick_model` levanta exceção se vir `split=test`",
    ),
    (
        "AutoML / stacking",
        "um objeto que nenhum módulo do curso consegue explicar",
        "fora, com o motivo escrito",
    ),
)

CRITERIO = """Pré-registrado em 2026-09-01, antes de qualquer leitura do teste.

1. PRIMÁRIO — maior AUC-ROC na VALIDAÇÃO (2023 inteiro). O teste (2024)
   nunca entra na escolha.
2. EMPATE TÉCNICO — modelos dentro de 1 erro-padrão bootstrap pareado
   (200 reamostras, semente 42) da melhor AUC de validação estão empatados.
3. DESEMPATE 1 — calibração: menor |previsto médio − observado| na validação.
4. DESEMPATE 2 — parcimônia: menor número de parâmetros ajustados.
5. DESEMPATE 3 — determinância: sem subamostragem estocástica.
6. O teste é lido UMA vez, depois de escolhido, e não pode mudar a escolha.
   Qualquer leitura adicional é rotulada "exploratória".
7. HIPÓTESE DO AUTOR, registrada antes de medir: o XGBoost vence, por
   ≥ 0,02 de AUC sobre a logística e ≥ 0,01 sobre a floresta.
8. CONSEQUÊNCIA DECLARADA: se o vencedor tunado divergir de XGB_PARAMS,
   o modelo do curso muda; os módulos de método são re-sincronizados em
   PR posterior."""


# --------------------------------------------------------------------------
# As matrizes. Três, porque as três famílias querem coisas diferentes.
# --------------------------------------------------------------------------
def tree_matrix(g: pd.DataFrame) -> pd.DataFrame:
    """X para árvore e floresta: numéricas cruas, booleanas 0/1, one-hot cheio.

    `drop_first=False` de propósito. A árvore não tem colinearidade para
    sofrer (o nível base escondido não vira coeficiente instável, vira
    regra ilegível), e a legibilidade da regra é o produto do modelo:
    `dispneia_sim <= 0.5` é uma frase que se lê em voz alta; a mesma
    regra com o nível base derrubado não é.

    A semana entra ORDINAL 1–53 — o MANIFEST §2.8 declara o ordinal como
    default fora do pipeline logístico. A árvore corta onde quiser e não
    precisa do seno/cosseno que a logística precisa para não ver um
    degrau em dezembro.
    """
    x = g[list(M.NUMERICAS)].copy()
    for c in M.BOOLEANAS:
        x[c] = g[c].astype(int)
    dummies = pd.get_dummies(g[list(M.CATEGORICAS)], drop_first=False, dtype=np.int8)
    return pd.concat([x, dummies], axis=1)


def matrices(g: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """As três matrizes do estudo, numa passada só sobre o Ouro."""
    x_xgb, x_log, _ = M.design_matrix(g)
    return {"xgb": x_xgb, "linear": x_log, "arvore": tree_matrix(g)}


# --------------------------------------------------------------------------
# O zoo: construir, ajustar, prever.
# --------------------------------------------------------------------------
def _pipeline_linear(final, passo: str):
    """imputa mediana + padroniza + estimador.

    O MESMO pré-processamento de `srag_model.fit_models`, de propósito: a
    logística tunada aqui só é comparável linha a linha com a do modelo
    do curso se a diferença for o hiperparâmetro, não o pipeline. O LPM
    recebe o mesmo tratamento pela mesma razão.
    """
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    return Pipeline(
        [
            ("imputa", SimpleImputer(strategy="median")),
            ("escala", StandardScaler()),
            (passo, final),
        ]
    )


def build(nome: str, params: dict | None = None):
    """O estimador NÃO ajustado: FIXOS[nome] + os hiperparâmetros buscados."""
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.tree import DecisionTreeClassifier
    from xgboost import XGBClassifier

    p = FIXOS.get(nome, {}) | (MELHORES.get(nome, {}) if params is None else params)
    if nome == "dummy":
        return DummyClassifier(**p)
    if nome == "lpm":
        return _pipeline_linear(LinearRegression(**p), "lpm")
    if nome == "logit":
        return _pipeline_linear(LogisticRegression(**p), "logit")
    if nome == "arvore":
        return DecisionTreeClassifier(**p)
    if nome == "floresta":
        return RandomForestClassifier(**p)
    if nome == "xgb":
        return XGBClassifier(**p)
    raise ValueError(f"modelo desconhecido: {nome}")


def _fit_em(nome: str, params: dict | None, x, y) -> tuple[object, float]:
    """Ajusta em (x, y) já fatiados e devolve (modelo, segundos)."""
    modelo = build(nome, params)
    t0 = time.perf_counter()
    modelo.fit(x, y)
    return modelo, time.perf_counter() - t0


def _p(nome: str, modelo, x) -> np.ndarray:
    """p̂ em [0,1] a partir da matriz já fatiada."""
    if nome == "lpm":
        # o clip É o achado: o modelo linear de probabilidade prevê fora
        # de [0,1] e `clip_report` imprime o intervalo bruto que ele
        # produziu antes do aperto
        return np.clip(modelo.predict(x), 1e-6, 1 - 1e-6)
    return modelo.predict_proba(x)[:, 1]


def fit_one(nome: str, g: pd.DataFrame, params: dict | None = None):
    """Ajusta no split de treino de `g`; devolve (modelo, segundos)."""
    x = matrices(g)[MATRIZ_DE[nome]]
    y = g["y_obito"].to_numpy()
    tr = (g["split"] == "train").to_numpy()
    return _fit_em(nome, params, x[tr], y[tr])


def predict(nome: str, modelo, g: pd.DataFrame, mask=None) -> np.ndarray:
    """p̂ de óbito, cuidando de qual matriz cada modelo espera."""
    x = matrices(g)[MATRIZ_DE[nome]]
    if mask is not None:
        x = x[np.asarray(mask)]
    return _p(nome, modelo, x)


def clip_report(nome: str, modelo, g: pd.DataFrame, split: str) -> dict:
    """O intervalo BRUTO das previsões no split, antes de qualquer clip.

    Só é interessante para o LPM (é onde a reta sai de [0,1]), mas a
    implementação é genérica para que a linha do LPM não seja um caso
    especial sem conferência.
    """
    x = matrices(g)[MATRIZ_DE[nome]]
    m = (g["split"] == split).to_numpy()
    bruto = modelo.predict(x[m]) if nome == "lpm" else modelo.predict_proba(x[m])[:, 1]
    return {
        "fora_01": int(((bruto < 0.0) | (bruto > 1.0)).sum()),
        "min": round(float(bruto.min()), 4),
        "max": round(float(bruto.max()), 4),
    }


# --------------------------------------------------------------------------
# As métricas.
# --------------------------------------------------------------------------
def ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    """Erro de calibração esperado: dez faixas de largura igual em [0,1].

    O mesmo espírito da célula de confiabilidade por decil do walkthrough:
    dentro de cada faixa, |média prevista − média observada|, ponderado
    pelo tamanho da faixa. Faixa vazia não conta.
    """
    borda = np.linspace(0.0, 1.0, bins + 1)
    faixa = np.clip(np.digitize(p, borda[1:-1]), 0, bins - 1)
    total = 0.0
    for b in range(bins):
        m = faixa == b
        if not m.any():
            continue
        total += float(m.mean()) * abs(float(p[m].mean()) - float(y[m].mean()))
    return total


def score(y: np.ndarray, p: np.ndarray) -> dict:
    """Discriminação, calibração e o lift sobre a prevalência."""
    from sklearn.metrics import (
        average_precision_score,
        brier_score_loss,
        log_loss,
        roc_auc_score,
    )

    prevalencia = float(y.mean())
    pr_auc = float(average_precision_score(y, p))
    return {
        "auc": round(float(roc_auc_score(y, p)), 4),
        "pr_auc": round(pr_auc, 4),
        "lift_pr": round(pr_auc / prevalencia, 4),
        "logloss": round(float(log_loss(y, p)), 4),
        "brier": round(float(brier_score_loss(y, p)), 4),
        "ece": round(ece(y, p), 4),
        "previsto_medio": round(float(p.mean()), 4),
        "observado": round(prevalencia, 4),
        # `prevalencia` repete `observado` de propósito: no card, uma das
        # duas é a linha de base do lift e a outra é a coluna de
        # calibração — misturar as leituras é como se lê errado
        "prevalencia": round(prevalencia, 4),
    }


def n_params(nome: str, modelo) -> int:
    """Quantos números o ajuste fixou — a coluna da regra 4 (parcimônia)."""
    if nome == "dummy":
        return 1
    if nome in ("lpm", "logit"):
        return int(np.asarray(modelo[-1].coef_).size) + 1
    if nome == "arvore":
        return int(modelo.tree_.node_count)
    if nome == "floresta":
        return int(sum(e.tree_.node_count for e in modelo.estimators_))
    # o dump texto do booster tem uma linha por nó; contar quebras é
    # barato e determinístico (e não puxa dependência nenhuma)
    return int(sum(d.count("\n") for d in modelo.get_booster().get_dump()))


COLUNAS_PLACAR = (
    "modelo",
    "forma",
    "matriz",
    "n_features",
    "n_parametros",
    "split",
    "n",
    "obitos",
    "prevalencia",
    "auc",
    "pr_auc",
    "lift_pr",
    "logloss",
    "brier",
    "ece",
    "previsto_medio",
    "observado",
    "fit_s",
)


def leaderboard(
    modelos: dict[str, object],
    tempos: dict[str, float],
    g: pd.DataFrame,
    splits: tuple[str, ...] = ("val",),
) -> pd.DataFrame:
    """O placar em formato longo: uma linha por (modelo, split)."""
    mats = matrices(g)
    y_todos = g["y_obito"].to_numpy()
    linhas = []
    for nome, modelo in modelos.items():
        x = mats[MATRIZ_DE[nome]]
        for s in splits:
            m = (g["split"] == s).to_numpy()
            y = y_todos[m]
            linhas.append(
                {
                    "modelo": nome,
                    "forma": FORMA[nome],
                    "matriz": MATRIZ_DE[nome],
                    "n_features": int(x.shape[1]),
                    "n_parametros": n_params(nome, modelo),
                    "split": s,
                    "n": int(m.sum()),
                    "obitos": int(y.sum()),
                    "fit_s": round(float(tempos.get(nome, 0.0)), 1),
                    **score(y, _p(nome, modelo, x[m])),
                }
            )
    return pd.DataFrame(linhas)[list(COLUNAS_PLACAR)]


def bootstrap_auc(
    y: np.ndarray,
    predicoes: dict[str, np.ndarray],
    n: int = 200,
    semente: int = SEMENTE,
) -> pd.DataFrame:
    """Bootstrap PAREADO: as mesmas reamostras para todos os modelos.

    O que interessa não é o erro-padrão de cada AUC isolada (que é grande
    e igual para todo mundo), e sim o da DIFERENÇA — dois modelos que
    erram nos mesmos pacientes têm diferença muito mais estável do que os
    intervalos individuais sugerem. Daí `delta_ep`, que é o que a regra 2
    do CRITERIO usa.
    """
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(semente)
    chaves = list(predicoes)
    acumulado: dict[str, list[float]] = {k: [] for k in chaves}
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        yb = y[idx]
        if yb.min() == yb.max():  # reamostra degenerada: AUC indefinida
            continue
        for k in chaves:
            acumulado[k].append(float(roc_auc_score(yb, predicoes[k][idx])))
    aucs = {k: np.asarray(v) for k, v in acumulado.items()}
    lider = max(chaves, key=lambda k: float(aucs[k].mean()))
    linhas = []
    for k in chaves:
        d = aucs[k] - aucs[lider]
        linhas.append(
            {
                "modelo": k,
                "auc_media": round(float(aucs[k].mean()), 4),
                "ep": round(float(aucs[k].std(ddof=1)), 4),
                "delta_lider": round(float(d.mean()), 4),
                "delta_ep": round(float(d.std(ddof=1)), 4),
                "reamostras": len(aucs[k]),
                "lider": bool(k == lider),
            }
        )
    return pd.DataFrame(linhas)


def _num(x: float, casas: int = 4) -> str:
    """Número em português, com vírgula decimal — para as linhas de log."""
    return f"{x:.{casas}f}".replace(".", ",")


def pick_model(placar_val: pd.DataFrame, ep: pd.DataFrame) -> tuple[str, list[str]]:
    """O CRITERIO, executado — devolve (vencedor, log das regras aplicadas).

    A guarda é o ponto do módulo: a escolha não tem como ver 2024 nem por
    acidente de chamada. O teste é lido uma vez, depois, pelo placar.
    """
    if (placar_val["split"] == "test").any():
        raise ValueError(
            "pick_model recebeu linhas de split=test: a escolha nunca vê 2024"
        )
    p = placar_val.sort_values(["auc", "modelo"], ascending=[False, True])
    p = p.reset_index(drop=True)
    eps = ep.set_index("modelo")
    lider = str(p.loc[0, "modelo"])
    melhor = float(p.loc[0, "auc"])
    log = [f"regra 1: {lider} lidera a AUC de validação ({_num(melhor)})"]

    empatados = [lider]
    for _, r in p.iloc[1:].iterrows():
        if melhor - float(r["auc"]) <= float(eps.loc[str(r["modelo"]), "delta_ep"]):
            empatados.append(str(r["modelo"]))
    if len(empatados) == 1:
        vice = str(p.loc[1, "modelo"]) if len(p) > 1 else lider
        folga = float(eps.loc[vice, "delta_ep"])
        log.append(
            f"regra 2: nenhum modelo dentro de 1 EP ({_num(folga)}) do líder"
            " — sem empate"
        )
        return lider, log
    log.append("regra 2: empate técnico entre " + ", ".join(empatados))

    sub = p[p["modelo"].isin(empatados)]
    cal = (sub["previsto_medio"] - sub["observado"]).abs()
    finalistas = sorted(sub.loc[cal == cal.min(), "modelo"].astype(str))
    log.append(
        f"regra 3: calibração — |previsto − observado| mínimo"
        f" ({_num(cal.min())}) em {', '.join(finalistas)}"
    )
    if len(finalistas) == 1:
        return finalistas[0], log

    sub = sub[sub["modelo"].isin(finalistas)]
    minimo = int(sub["n_parametros"].min())
    finalistas = sorted(sub.loc[sub["n_parametros"] == minimo, "modelo"].astype(str))
    log.append(
        f"regra 4: parcimônia — {minimo} parâmetros ajustados em"
        f" {', '.join(finalistas)}"
    )
    if len(finalistas) == 1:
        return finalistas[0], log

    # Regra 5 é, por construção, um no-op declarado: FIXOS trava
    # subsample/colsample em 1,0 e a floresta é o único bagging, então
    # nenhum finalista subamostra. Fica registrado que a regra rodou.
    vencedor = next(m for m in p["modelo"].astype(str) if m in finalistas)
    log.append(
        "regra 5: determinância — nenhum finalista subamostra"
        " (FIXOS trava subsample/colsample em 1,0), a regra não desempata;"
        f" fica o de maior AUC entre os finalistas: {vencedor}"
    )
    return vencedor, log


# --------------------------------------------------------------------------
# As buscas.
# --------------------------------------------------------------------------
def _linha_busca(nome: str, cfg: dict, segundos: float, y, p) -> dict:
    return {
        "modelo": nome,
        "config": json.dumps(cfg, sort_keys=True, default=str),
        "fit_s": round(float(segundos), 1),
        **score(y, p),
    }


def search(
    nome: str,
    g: pd.DataFrame,
    n_iter: int | None = None,
    semente: int = SEMENTE,
    espaco: dict[str, list] | None = None,
) -> pd.DataFrame:
    """Busca de `nome` no espaço declarado: ajusta no treino, mede na val."""
    from sklearn.model_selection import ParameterGrid, ParameterSampler

    g = g[g["split"] != "test"].copy()  # o teste não existe dentro desta função
    espaco = ESPACOS[nome] if espaco is None else espaco
    n_iter = N_ITER[nome] if n_iter is None else n_iter
    grade = list(ParameterGrid(espaco)) if espaco else [{}]
    if len(grade) <= n_iter:
        configs = grade
    else:
        configs = list(ParameterSampler(espaco, n_iter, random_state=semente))
    # ordem por JSON: a amostra depende da semente, a ORDEM não depende
    # de como o dicionário chegou nem da plataforma
    configs.sort(key=lambda c: json.dumps(c, sort_keys=True, default=str))

    x = matrices(g)[MATRIZ_DE[nome]]
    y = g["y_obito"].to_numpy()
    tr = (g["split"] == "train").to_numpy()
    va = (g["split"] == "val").to_numpy()
    x_tr, x_va, y_tr, y_va = x[tr], x[va], y[tr], y[va]

    linhas = []
    if nome == "xgb":
        # n_estimators é um PREFIXO do mesmo modelo: ajustar no teto do
        # grupo e cortar com iteration_range dá exatamente o mesmo
        # resultado de reajustar, de graça. `fit_s` é o do teto e o grupo
        # inteiro o compartilha — está declarado no card.
        grupos: dict[str, list[dict]] = {}
        for cfg in configs:
            resto = {k: v for k, v in cfg.items() if k != "n_estimators"}
            grupos.setdefault(
                json.dumps(resto, sort_keys=True, default=str), []
            ).append(cfg)
        for chave in sorted(grupos):
            grupo = grupos[chave]
            teto = max(int(c["n_estimators"]) for c in grupo)
            modelo, segundos = _fit_em(
                nome, {**grupo[0], "n_estimators": teto}, x_tr, y_tr
            )
            for cfg in grupo:
                p = modelo.predict_proba(
                    x_va, iteration_range=(0, int(cfg["n_estimators"]))
                )[:, 1]
                linhas.append(_linha_busca(nome, cfg, segundos, y_va, p))
    else:
        for cfg in configs:
            modelo, segundos = _fit_em(nome, cfg, x_tr, y_tr)
            linhas.append(
                _linha_busca(nome, cfg, segundos, y_va, _p(nome, modelo, x_va))
            )

    df = pd.DataFrame(linhas)
    df["posto"] = df["auc"].rank(ascending=False, method="min").astype(int)
    return df.sort_values(["posto", "config"]).reset_index(drop=True)


def search_kfold(
    nome: str,
    g: pd.DataFrame,
    grade: dict[str, list],
    k: int = 5,
    semente: int = SEMENTE,
) -> pd.DataFrame:
    """A armadilha, medida: k dobras EMBARALHADAS dentro do treino (≤2022).

    Cada dobra de validação tem vizinhos temporais dentro da dobra de
    treino — 2020, 2021 e 2022 misturados. É o protocolo default do
    mercado (`cv=5`) e ele contesta uma pergunta que ninguém fez: "como
    o modelo se sai num paciente do passado que eu já vi quase igual".
    """
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import ParameterGrid, StratifiedKFold

    g = g[g["split"] == "train"].copy()  # o teste não existe dentro desta função
    x = matrices(g)[MATRIZ_DE[nome]]
    y = g["y_obito"].to_numpy()
    configs = sorted(
        ParameterGrid(grade), key=lambda c: json.dumps(c, sort_keys=True, default=str)
    )
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=semente)
    linhas = []
    for cfg in configs:
        aucs = []
        for i_tr, i_va in skf.split(x, y):
            modelo, _ = _fit_em(nome, cfg, x.iloc[i_tr], y[i_tr])
            aucs.append(float(roc_auc_score(y[i_va], _p(nome, modelo, x.iloc[i_va]))))
        linhas.append(
            {
                "modelo": nome,
                "config": json.dumps(cfg, sort_keys=True, default=str),
                "auc_kfold": round(float(np.mean(aucs)), 4),
                "dobras": k,
            }
        )
    return pd.DataFrame(linhas)


def floresta_de_fabrica(g: pd.DataFrame) -> dict:
    """O que sai da caixa: `RandomForestClassifier()` sem tocar em nada.

    Só semente e `n_jobs` entram — um é reprodutibilidade, o outro é
    paralelismo. Árvores até a folha pura em 200 mil linhas: o custo e a
    calibração desse default são o argumento da linha, não a AUC.
    """
    from sklearn.ensemble import RandomForestClassifier

    g = g[g["split"] != "test"].copy()  # o teste não existe dentro desta função
    x = matrices(g)["arvore"]
    y = g["y_obito"].to_numpy()
    tr = (g["split"] == "train").to_numpy()
    va = (g["split"] == "val").to_numpy()
    modelo = RandomForestClassifier(n_jobs=-1, random_state=SEMENTE)
    t0 = time.perf_counter()
    modelo.fit(x[tr], y[tr])
    segundos = time.perf_counter() - t0
    return {
        "config": "RandomForestClassifier() — só n_jobs e random_state",
        "fit_s": round(segundos, 1),
        "n_parametros": n_params("floresta", modelo),
        **score(y[va], modelo.predict_proba(x[va])[:, 1]),
    }


def search_all(g: pd.DataFrame) -> dict:
    """As seis buscas e as três sondagens. Caro: dezenas de minutos."""
    return {
        "buscas": {nome: search(nome, g) for nome in MODELOS},
        "kfold_trap": {
            "kfold": search_kfold("xgb", g, TRAP_XGB),
            "temporal": search("xgb", g, n_iter=4, espaco=TRAP_XGB),
        },
        "l1_sondagem": search("logit", g, n_iter=3, espaco=L1_SONDAGEM),
        "floresta_default": floresta_de_fabrica(g),
    }


def _limpa(o):
    """Objeto pronto para json.dumps: escalar de numpy vira escalar de Python.

    NÃO arredonda. Toda métrica já sai arredondada em 4 casas de onde é
    medida (`score`, `bootstrap_auc`, `clip_report`, `fit_s`), e uma
    passada cega de `round(x, 4)` aqui em cima destruiria os
    hiperparâmetros pequenos do espaço de busca — `ccp_alpha=1e-06`
    viraria `0.0` no bloco MELHORES que a gente cola de volta, trocando o
    modelo em silêncio.
    """
    if isinstance(o, dict):
        return {str(k): _limpa(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_limpa(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return float(o)
    return o


def run_search() -> dict:
    """Roda o estudo inteiro e devolve o dicionário que vira o JSON."""
    g = M.load_gold()
    res = search_all(g)
    melhores = {n: json.loads(res["buscas"][n].loc[0, "config"]) for n in MODELOS}

    modelos, tempos = {}, {}
    for nome in MODELOS:
        modelos[nome], tempos[nome] = fit_one(nome, g, melhores[nome])

    va = (g["split"] == "val").to_numpy()
    y_va = g.loc[va, "y_obito"].to_numpy()
    predicoes = {n: predict(n, modelos[n], g, va) for n in MODELOS}
    ep = bootstrap_auc(y_va, predicoes)
    placar_val = leaderboard(modelos, tempos, g, ("val",))
    vencedor, log = pick_model(placar_val, ep)

    # A ÚNICA leitura do teste, depois da escolha — os modelos já estão
    # ajustados, nada é reajustado para chegar até aqui.
    placar = leaderboard(modelos, tempos, g, ("val", "test"))

    hoje = {k: M.XGB_PARAMS[k] for k in ("n_estimators", "max_depth", "learning_rate")}
    escolhido = {k: melhores["xgb"].get(k) for k in hoje}
    consequencia = {
        "xgb_params_hoje": hoje,
        "xgb_params_vencedor": escolhido,
        "vencedor_diverge": bool(vencedor != "xgb" or escolhido != hoje),
    }
    return {
        "criterio": CRITERIO,
        "espacos": ESPACOS,
        "n_iter": N_ITER,
        "fixos": FIXOS,
        "buscas": {n: res["buscas"][n].to_dict(orient="records") for n in MODELOS},
        "kfold_trap": {
            "kfold": res["kfold_trap"]["kfold"].to_dict(orient="records"),
            "temporal": res["kfold_trap"]["temporal"].to_dict(orient="records"),
        },
        "l1_sondagem": res["l1_sondagem"].to_dict(orient="records"),
        "floresta_default": res["floresta_default"],
        "bootstrap": ep.to_dict(orient="records"),
        "escolha": {"vencedor": vencedor, "log": log, "melhores": melhores},
        "placar": placar.to_dict(orient="records"),
        "lpm_clip": [
            {"split": s, **clip_report("lpm", modelos["lpm"], g, s)}
            for s in ("val", "test")
        ],
        "consequencia": consequencia,
        "amostra": {
            "n": len(g),
            "treino": int((g["split"] == "train").sum()),
            "val": int((g["split"] == "val").sum()),
            "test": int((g["split"] == "test").sum()),
        },
    }


# --------------------------------------------------------------------------
# O card, gerado — função pura de selection_metrics.json.
# --------------------------------------------------------------------------
def _mil(n) -> str:
    """Milhar com ponto, como no MODEL.md."""
    return f"{int(n):,}".replace(",", ".")


def _espaco_txt(espaco: dict) -> str:
    if not espaco:
        return "sem hiperparâmetros — é o ponto (Molnar cap. 6)"
    return "; ".join(f"`{k}` ∈ {list(v)}" for k, v in espaco.items())


def _tamanho(espaco: dict) -> int:
    total = 1
    for v in espaco.values():
        total *= len(v)
    return total


def _tabela_placar(sm: dict, split: str) -> list[str]:
    linhas = [
        f"### {split}",
        "",
        (
            "| modelo | AUC | PR-AUC | lift | Brier | log-loss | ECE |"
            " previsto médio | observado | parâmetros | fit (s) |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    por_modelo = {r["modelo"]: r for r in sm["placar"] if r["split"] == split}
    for nome in MODELOS:
        r = por_modelo[nome]
        linhas.append(
            f"| `{nome}` | {r['auc']} | {r['pr_auc']} | {r['lift_pr']} |"
            f" {r['brier']} | {r['logloss']} | {r['ece']} |"
            f" {r['previsto_medio']} | {r['observado']} |"
            f" {_mil(r['n_parametros'])} | {r['fit_s']} |"
        )
    return linhas


def render_card(sm: dict) -> str:
    L = [
        "# SELECTION.md — o estudo que escolheu o modelo do curso",
        "",
        "Gerado por `tools/srag_selection.py --card` de",
        "`gold/selection_metrics.json`. Não editar à mão.",
        "",
        (
            f"Amostra commitada: {_mil(sm['amostra']['n'])} linhas —"
            f" treino {_mil(sm['amostra']['treino'])},"
            f" val {_mil(sm['amostra']['val'])},"
            f" teste {_mil(sm['amostra']['test'])}."
        ),
        "",
        "## O protocolo",
        "",
        "```",
    ]
    L += sm["criterio"].strip("\n").split("\n")
    L += [
        "```",
        "",
        "## O zoo",
        "",
        "| modelo | Molnar | forma | matriz | configurações buscadas |",
        "|---|---|---|---|---:|",
    ]
    for nome in MODELOS:
        L.append(
            f"| `{nome}` | {MOLNAR[nome]} | {FORMA[nome]} | {MATRIZ_DE[nome]} |"
            f" {len(sm['buscas'][nome])} de {_tamanho(sm['espacos'][nome])} |"
        )
    L += [
        "",
        "Três matrizes, porque as três famílias querem coisas diferentes:",
        "`xgb` recebe as categóricas nativas, `linear` recebe one-hot com",
        "nível base derrubado e a semana em seno/cosseno, `arvore` recebe",
        "one-hot completo e a semana ordinal (MANIFEST §2.8).",
        "",
        "## Fora do estudo, de propósito",
        "",
        "- **GAM (Molnar cap. 8)** — a idade tem um U que a reta achata;",
        "  escolher os termos suaves É a lição do capítulo, e ela",
        "  não cabe numa linha de placar.",
        "- **Regras de decisão (cap. 10)** — SE-ENTÃO sobre checkboxes é",
        "  exatamente o que o funil torna traiçoeiro; a árvore já entrega",
        "  aqui a versão hierárquica da mesma ideia.",
        "- **RuleFit (cap. 11)** — gera regras e depois faz L1 sobre elas:",
        "  dois capítulos empilhados, com subamostra própria.",
        "",
        "Nenhum dos três está fora por qualidade. Cada um vira módulo",
        "próprio — ver [ROADMAP.md](../../ROADMAP.md).",
        "",
        "## As buscas",
        "",
    ]
    for nome in MODELOS:
        rows = sm["buscas"][nome]
        melhor = min(rows, key=lambda r: (r["posto"], r["config"]))
        pior = max(rows, key=lambda r: (r["posto"], r["config"]))
        amplitude = round(melhor["auc"] - pior["auc"], 4)
        L += [
            (
                f"### `{nome}` — {len(rows)} de"
                f" {_tamanho(sm['espacos'][nome])} configurações"
            ),
            "",
            f"- espaço: {_espaco_txt(sm['espacos'][nome])}",
            f"- melhor: `{melhor['config']}` → AUC val **{melhor['auc']}**",
            f"- pior da busca: AUC val {pior['auc']} — amplitude {amplitude}",
            "",
        ]
    l1 = sm["l1_sondagem"]
    fd = sm["floresta_default"]
    L += [
        "### Sondagens (fora do placar)",
        "",
        "| sondagem | configuração | AUC val | fit (s) |",
        "|---|---|---:|---:|",
    ]
    for r in l1:
        L.append(f"| L1 (`saga`) | `{r['config']}` | {r['auc']} | {r['fit_s']} |")
    L += [
        f"| floresta de fábrica | {fd['config']} | {fd['auc']} | {fd['fit_s']} |",
        "",
        (
            f"A floresta de fábrica ajusta {_mil(fd['n_parametros'])} nós"
            f" (ECE {fd['ece']}): o default"
        ),
        "cresce até a folha pura, e o preço aparece no custo e na",
        "calibração antes de aparecer na AUC.",
        "",
        "O LPM prevê fora de [0,1] — o clip é o achado, não um detalhe de",
        "implementação:",
        "",
        "| split | previsões fora de [0,1] | mínimo bruto | máximo bruto |",
        "|---|---:|---:|---:|",
    ]
    for r in sm["lpm_clip"]:
        L.append(f"| {r['split']} | {_mil(r['fora_01'])} | {r['min']} | {r['max']} |")
    L += ["", "## O placar", ""]
    L += _tabela_placar(sm, "val")
    L += [""]
    L += _tabela_placar(sm, "test")
    L += [
        "",
        "`fit (s)` não é reivindicação de desempenho — Apple Silicon, pilha",
        "fixada, uma medição só. Está aqui pelo custo RELATIVO entre as",
        "formas, que é o que muda a decisão de quem mantém isto.",
        "",
        "## O bootstrap pareado",
        "",
        (
            f"{sm['bootstrap'][0]['reamostras']} reamostras da validação, as"
            " MESMAS para todos os modelos"
        ),
        "(reamostra degenerada, com uma classe só, é descartada). O que a",
        "regra 2 usa é `EP do Δ`: dois modelos que erram nos mesmos",
        "pacientes têm diferença mais estável do que os intervalos",
        "individuais sugerem.",
        "",
        "| modelo | AUC média | EP | Δ vs líder | EP do Δ |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in sm["bootstrap"]:
        marca = " (líder)" if r["lider"] else ""
        L.append(
            f"| `{r['modelo']}`{marca} | {r['auc_media']} | {r['ep']} |"
            f" {r['delta_lider']} | {r['delta_ep']} |"
        )
    L += [
        "",
        "## A escolha",
        "",
        f"**Vencedor: `{sm['escolha']['vencedor']}`**, por `pick_model` —",
        "a função levanta exceção se receber uma linha de `split == test`,",
        "então a escolha não vê 2024 nem por acidente de chamada.",
        "",
    ]
    L += [f"- {linha}" for linha in sm["escolha"]["log"]]
    L += [
        "",
        "Os hiperparâmetros escolhidos:",
        "",
        "| modelo | configuração |",
        "|---|---|",
    ]
    for nome in MODELOS:
        cfg = json.dumps(sm["escolha"]["melhores"][nome], sort_keys=True)
        L.append(f"| `{nome}` | `{cfg}` |")

    kf = {r["config"]: r for r in sm["kfold_trap"]["kfold"]}
    tp = {r["config"]: r for r in sm["kfold_trap"]["temporal"]}
    ordem_k = sorted(kf, key=lambda c: (-kf[c]["auc_kfold"], c))
    ordem_t = sorted(tp, key=lambda c: (-tp[c]["auc"], c))
    dobras = sm["kfold_trap"]["kfold"][0]["dobras"]
    orcamento = json.loads(ordem_k[0])
    L += [
        "",
        "## A armadilha do k-fold",
        "",
        f"As mesmas {len(kf)} configurações, mesmo orçamento",
        (
            f"({orcamento['n_estimators']} árvores, lr"
            f" {_num(orcamento['learning_rate'], 2)}), julgadas de dois jeitos."
        ),
        f"À esquerda, `cv={dobras}` embaralhado dentro do treino: cada dobra",
        "de validação tem vizinhos temporais na dobra de treino, 2020–2022",
        "misturados. À direita, a validação temporal que este estudo usa.",
        "",
        f"| configuração | AUC {dobras}-fold embaralhado | AUC val 2023 |",
        "|---|---:|---:|",
    ]
    for c in ordem_k:
        L.append(f"| `{c}` | {kf[c]['auc_kfold']} | {tp[c]['auc']} |")
    if ordem_k[0] == ordem_t[0]:
        leitura = [
            "As duas escolhem a mesma configuração desta vez — o que NÃO",
            "absolve o protocolo embaralhado: a AUC dele continua inflada, e",
            "a concordância é sorte desta grade, não garantia do método.",
        ]
    else:
        leitura = [
            f"Elas discordam. O {dobras}-fold embaralhado escolheria",
            f"`{ordem_k[0]}`; a validação temporal escolhe",
            f"`{ordem_t[0]}` — o protocolo default do mercado trocaria o",
            "modelo do curso, e a troca seria invisível para quem só olha a",
            "média das dobras.",
        ]
    delta = round(kf[ordem_k[0]]["auc_kfold"] - tp[ordem_t[0]]["auc"], 4)
    L += [""]
    L += leitura
    L += [
        "",
        f"A melhor AUC embaralhada está {delta} acima da melhor AUC",
        "temporal: parte disso é o regime de 2020–22 vazando para dentro",
        "da própria dobra de avaliação.",
        "",
        "## O que o mercado faria",
        "",
        "| prática | o que custaria aqui | o que este estudo faz |",
        "|---|---|---|",
    ]
    L += [f"| {a} | {b} | {c} |" for a, b, c in MERCADO]
    L += [
        "",
        "## Consequência",
        "",
    ]
    c = sm["consequencia"]
    hoje = json.dumps(c["xgb_params_hoje"], sort_keys=True)
    novo = json.dumps(c["xgb_params_vencedor"], sort_keys=True)
    if c["vencedor_diverge"]:
        L += [
            "A regra 8 do protocolo foi acionada: o vencedor **diverge** do",
            "que `srag_model.XGB_PARAMS` traz hoje.",
            "",
            f"- `XGB_PARAMS` de hoje: `{hoje}`",
            f"- vencedor do estudo: `{novo}`",
            "",
            "O modelo do curso muda, e os módulos de método são",
            "re-sincronizados em PR posterior — a consequência estava",
            "escrita antes de medir, então cumpri-la não é reação a um",
            "número que não agradou.",
        ]
    else:
        L += [
            "O vencedor **confirma** `srag_model.XGB_PARAMS`:",
            "",
            f"- `XGB_PARAMS` de hoje: `{hoje}`",
            f"- vencedor do estudo: `{novo}`",
            "",
            "Nada a re-sincronizar. A confirmação vale porque a",
            "consequência oposta estava escrita antes de medir — ver",
            "[MODEL.md](MODEL.md).",
        ]
    return "\n".join(L).rstrip("\n") + "\n"


def _le_metrics() -> dict | None:
    if not METRICS_JSON.exists():
        print(
            f"{METRICS_JSON} não existe — rode"
            " `python3 tools/srag_selection.py --search` primeiro",
            file=sys.stderr,
        )
        return None
    return json.loads(METRICS_JSON.read_text(encoding="utf-8"))


def main(argv: list[str]) -> int:
    if "--search" in argv:
        sm = _limpa(run_search())
        METRICS_JSON.write_text(
            json.dumps(sm, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"{METRICS_JSON}")
        print(f"vencedor: {sm['escolha']['vencedor']}")
        print("\nMELHORES = {")
        for nome in MODELOS:
            print(f"    {nome!r}: {sm['escolha']['melhores'][nome]!r},")
        print("}")
        return 0
    if "--card" in argv:
        sm = _le_metrics()
        if sm is None:
            return 1
        SELECTION_MD.write_text(render_card(sm), encoding="utf-8")
        print(f"{SELECTION_MD}")
        return 0
    if "--check-card" in argv:
        sm = _le_metrics()
        if sm is None:
            return 1
        problemas = []
        em_disco = (
            SELECTION_MD.read_text(encoding="utf-8") if SELECTION_MD.exists() else ""
        )
        if em_disco != render_card(sm):
            problemas.append("SELECTION.md divergiu de gold/selection_metrics.json")
        if MELHORES and MELHORES != sm["escolha"]["melhores"]:
            problemas.append(
                "MELHORES (colado em tools/srag_selection.py) divergiu de"
                " escolha.melhores"
            )
        if problemas:
            for p in problemas:
                print(p, file=sys.stderr)
            return 1
        print("SELECTION.md em dia")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
