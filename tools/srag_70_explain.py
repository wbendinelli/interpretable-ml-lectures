"""Fase 70 — os núcleos que os métodos de explicação compartilham.

Aqui moram as funções que os módulos 01–05 copiavam célula a célula: a
varredura ceteris paribus (`perfil_cp`), o feixe de curvas ICE
(`curvas_ice`) e a família de distâncias de Gower que os módulos 01 e 04
usam para medir "quão distante do dado real este ponto ficou". Uma
definição, um comportamento, cinco módulos.

Isso NÃO esconde o método do aluno. A regra combinada é a inversa: os
**walkthroughs exibem o fonte** com

    print(inspect.getsource(E.perfil_cp))

antes de usar a função — o estudante lê exatamente o código que rodou, e
não uma paráfrase. Os *internals*, que já pressupõem o método lido, só
chamam. O que a fase 70 elimina é a DIVERGÊNCIA entre cópias (o módulo 01
já corrigiu um bug de recontagem que a cópia do 02 não tinha), não a
leitura.

As dependências pesadas ficam de fora: além de numpy/pandas, este módulo
só importa `srag_60_model` (que também só puxa numpy/pandas). O caminho
contrário é PROIBIDO — a fase 60 é lida por hooks de pre-commit num venv
mínimo e não pode depender de nada da fase 70.

A calibração (`ece`) NÃO mora aqui: ela pertence ao estudo de seleção e
continua em `srag_50_selection.py`.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import srag_60_model as M

# Colunas de contexto que as varreduras carregam junto das 40 features:
# `gate_impossible` precisa delas para recontar as cercas, e `ano_onset` /
# `gold_id` identificam a linha de origem no painel ICE.
CONTEXTO_CP: tuple[str, ...] = (
    "fator_risc_portao",
    "n_crit2",
    "n_crit3",
    "meses_desde_mar2020",
)
CONTEXTO_ICE: tuple[str, ...] = CONTEXTO_CP + ("ano_onset", "gold_id")


def _colunas(extra: tuple[str, ...]) -> list[str]:
    return list(dict.fromkeys(list(M.FEATURES) + list(extra)))


def perfil_cp(
    modelo,
    base_paciente: pd.Series,
    feature: str,
    grade,
    *,
    categorias: dict,
) -> tuple[pd.DataFrame, np.ndarray]:
    """A varredura ceteris paribus de UM paciente — o núcleo do módulo 01.

    Congela todas as colunas do paciente, repete a linha uma vez por ponto
    da `grade` e move só `feature`. Devolve `(linhas, p)`: o frame inteiro
    (com as colunas de contexto, para `gate_reasons` recontar as cercas) e
    a probabilidade prevista em cada ponto.

    `categorias` é `{coluna: pd.Index de níveis}` — tipicamente
    `{c: g[c].cat.categories for c in M.CATEGORICAS}`. O re-cast é
    obrigatório: a lista de Series perde o dtype `category` no caminho, e
    o XGBoost com categóricas nativas recusa uma coluna `object`.

    Uma feature numérica varrida vira `float32`, o dtype da coluna no
    Ouro. (O caderno-walkthrough castava só `idade_anos` e o *internals*
    qualquer numérica; medido em 2026-09-01 sobre as 20 chamadas reais dos
    dois cadernos, as duas regras dão previsão e `gate_impossible`
    idênticas bit a bit — a regra geral fica.)
    """
    cols = _colunas(CONTEXTO_CP)
    linhas = pd.DataFrame([base_paciente[cols].copy() for _ in grade]).reset_index(
        drop=True
    )
    linhas[feature] = grade
    if feature in M.NUMERICAS:
        linhas[feature] = linhas[feature].astype("float32")
    for c in M.CATEGORICAS:
        linhas[c] = pd.Categorical(linhas[c], categories=categorias[c])
    x = linhas[list(M.FEATURES)].copy()
    for c in M.BOOLEANAS:
        x[c] = x[c].astype(bool)
    return linhas, modelo.predict_proba(x)[:, 1]


def curvas_ice(
    modelo,
    pacientes: pd.DataFrame,
    feature: str,
    grade,
    *,
    categorias: dict,
    cols: list[str] | None = None,
) -> tuple[pd.DataFrame, np.ndarray]:
    """O mesmo perfil, para um painel inteiro — o núcleo do módulo 02.

    Repete cada paciente `len(grade)` vezes (`index.repeat`, que preserva a
    ordem do painel), varre `feature` com `np.tile` e devolve `(rep, P)`
    com `P` de forma `(n_pacientes, n_pontos)`: cada linha é uma curva ICE,
    e a média das linhas é o PDP.

    `cols` default carrega as 40 features mais o contexto das cercas mais
    `ano_onset`/`gold_id` — é o que os dois cadernos do módulo 02 montavam.
    """
    if cols is None:
        cols = _colunas(CONTEXTO_ICE)
    n, k = len(pacientes), len(grade)
    rep = pacientes.loc[pacientes.index.repeat(k), cols].reset_index(drop=True)
    rep[feature] = np.tile(grade, n)
    if feature in M.NUMERICAS:
        rep[feature] = rep[feature].astype("float32")
    for c in M.CATEGORICAS:
        rep[c] = pd.Categorical(rep[c], categories=categorias[c])
    x = rep[list(M.FEATURES)].copy()
    for c in M.BOOLEANAS:
        x[c] = x[c].astype(bool)
    return rep, modelo.predict_proba(x)[:, 1].reshape(n, k)


# --------------------------------------------------------------------------
# Gower — "quão distante do dado real?", a régua dos módulos 01 e 04.
# --------------------------------------------------------------------------
def faixas_de(base: pd.DataFrame, num_cols) -> dict:
    """Amplitude (max − min) de cada coluna numérica, com 0 virando 1,0.

    É o denominador que torna comparáveis idade em anos e doses em contagem.
    O `or 1.0` protege a coluna constante de virar divisão por zero.
    """
    return {c: float(base[c].max() - base[c].min()) or 1.0 for c in num_cols}


def gower_matriz(
    linhas: pd.DataFrame,
    ref: pd.DataFrame,
    num_cols,
    cat_cols,
    faixas: dict | None = None,
) -> np.ndarray:
    """Matriz `(len(linhas), len(ref))` de distâncias de Gower normalizadas.

    Numéricas entram como |Δ| sobre a amplitude; categóricas como 0/1 de
    desigualdade; a soma é dividida por `len(num_cols) + len(cat_cols)`, de
    modo que a distância máxima é 1,0. Sem `faixas`, elas saem de `ref`.
    """
    if faixas is None:
        faixas = faixas_de(ref, num_cols)
    dists = np.zeros((len(linhas), len(ref)))
    for c in num_cols:
        dists += (
            np.abs(linhas[c].to_numpy()[:, None] - ref[c].to_numpy()[None, :])
            / faixas[c]
        )
    for c in cat_cols:
        dists += (
            linhas[c].astype(str).to_numpy()[:, None]
            != ref[c].astype(str).to_numpy()[None, :]
        ).astype(float)
    return dists / (len(num_cols) + len(cat_cols))


def gower_ao_vizinho(
    linhas: pd.DataFrame,
    base: pd.DataFrame,
    num_cols,
    cat_cols,
    *,
    amostra_base: int = 4000,
    random_state: int = 42,
) -> np.ndarray:
    """Distância de Gower de cada linha ao seu vizinho REAL mais próximo.

    A pergunta do módulo 01: uma varredura fabrica um ponto distante de
    tudo o que existe? A referência é uma amostra de `amostra_base` linhas
    de `base`, sorteada com `np.random.default_rng(random_state)` — dita,
    não escolhida. Devolve um array de tamanho `len(linhas)`.

    A distância NÃO vê contradição lógica: trocar um nível de categoria
    custa sempre a mesma fração da métrica, possível ou não. Quem vê é
    `srag_60_model.gate_impossible` — é essa a lição da célula.
    """
    rng = np.random.default_rng(random_state)
    idx = rng.choice(len(base), size=min(amostra_base, len(base)), replace=False)
    ref = base.iloc[idx]
    faixas = faixas_de(base, num_cols)
    dists = np.zeros((len(linhas), len(ref)))
    for c in num_cols:
        dists += (
            np.abs(linhas[c].to_numpy()[:, None] - ref[c].to_numpy()[None, :])
            / faixas[c]
        )
    for c in cat_cols:
        dists += (
            linhas[c].astype(str).to_numpy()[:, None]
            != ref[c].astype(str).to_numpy()[None, :]
        ).astype(float)
    return dists.min(axis=1) / (len(num_cols) + len(cat_cols))


def gower_par(
    pac: pd.Series,
    frame: pd.DataFrame,
    num_cols,
    cat_cols,
    faixas: dict | None = None,
) -> np.ndarray:
    """Gower do paciente a CADA linha do frame — a régua do módulo 04.

    Mesma família de métrica que `gower_ao_vizinho`, outra pergunta: ali o
    vizinho real mais próximo de um ponto fabricado; aqui o custo `d` de
    cada candidato a contrafactual, o termo de proximidade da perda de
    Wachter. O paciente entra como escalar (`float(pac[c])`,
    `str(pac[c])`), nunca como frame de uma linha — reindexar mudaria os
    dtypes. Sem `faixas`, elas saem de `frame`; o módulo 04 passa as do
    Ouro inteiro, que é a referência certa.
    """
    if faixas is None:
        faixas = faixas_de(frame, num_cols)
    d = np.zeros(len(frame))
    for c in num_cols:
        d += np.abs(frame[c].to_numpy(dtype=float) - float(pac[c])) / faixas[c]
    for c in cat_cols:
        d += (frame[c].astype(str).to_numpy() != str(pac[c])).astype(float)
    return d / (len(num_cols) + len(cat_cols))
