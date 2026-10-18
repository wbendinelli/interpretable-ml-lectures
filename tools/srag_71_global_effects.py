"""Núcleos dos capítulos globais: PDP, ALE, H e decomposição de superfície.

As funções recebem uma função de previsão escalar e DataFrames com os tipos
originais. Não ajustam modelos, não usam o alvo e não gravam artefatos. Os
walkthroughs mostram o fonte; os internals conferem fórmulas, casos conhecidos
e, quando disponível na pilha fixada, a implementação do scikit-learn.
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd


def substituir(base: pd.DataFrame, valores: dict) -> pd.DataFrame:
    """Preserva categorias; promove inteiros se a grade exigir frações."""
    nova = base.copy(deep=True)
    for coluna, valor in valores.items():
        dtype = base[coluna].dtype
        if isinstance(dtype, pd.CategoricalDtype):
            if valor not in dtype.categories:
                raise ValueError(f"Categoria não declarada em {coluna}: {valor}")
            nova[coluna] = pd.Categorical([valor] * len(base), dtype=dtype)
        else:
            if pd.api.types.is_integer_dtype(dtype) and not float(valor).is_integer():
                dtype = np.dtype("float64")
            nova[coluna] = pd.Series(valor, index=base.index, dtype=dtype)
    return nova


def pd_empirica(prever, fundo: pd.DataFrame, pontos: pd.DataFrame) -> np.ndarray:
    """PD_S(z) = média de f(z, X_-S) no mesmo fundo, sem interpolação.

    Uma linha de `pontos` define valores conjuntos de S. Combinações repetidas
    reutilizam a média, preservando a ordem e os pesos das linhas recebidas.
    A distribuição conjunta das colunas complementares permanece intacta.
    """
    if fundo.empty or pontos.empty or not len(pontos.columns):
        raise ValueError("Fundo e pontos precisam de linhas e colunas.")
    cache = {}
    resultado = []
    for valores in pontos.itertuples(index=False, name=None):
        if valores not in cache:
            alterada = substituir(fundo, dict(zip(pontos.columns, valores)))
            cache[valores] = float(np.asarray(prever(alterada), dtype=float).mean())
        resultado.append(cache[valores])
    return np.asarray(resultado)


def ice_empirica(prever, fundo, coluna, grade) -> np.ndarray:
    """Uma linha por registro, uma coluna por ponto da grade."""
    return np.column_stack(
        [prever(substituir(fundo, {coluna: valor})) for valor in grade]
    ).astype(float)


def ale_numerica(prever, base, coluna, *, bins=10) -> tuple[pd.DataFrame, np.ndarray]:
    """ALE numérica por quantis; convenção em degraus do capítulo de Molnar.

    Intervalos (esquerda, direita], incluindo o mínimo no primeiro. Quantis
    repetidos são unidos. Cada registro recebe o acumulado na borda superior
    de seu intervalo; a centralização usa essas atribuições, ponderadas pelas
    contagens, não a média não ponderada das bordas. Não há interpolação.
    Ausências e colunas não numéricas são recusadas explicitamente.
    """
    if (
        isinstance(bins, (bool, np.bool_))
        or not isinstance(bins, (int, np.integer))
        or bins < 1
    ):
        raise ValueError("bins precisa de um inteiro positivo.")
    if not pd.api.types.is_numeric_dtype(base[coluna]) or pd.api.types.is_bool_dtype(
        base[coluna]
    ):
        raise ValueError("ALE deste núcleo aceita somente entrada numérica.")
    valores = base[coluna].to_numpy(dtype=float)
    if not len(valores) or not np.isfinite(valores).all():
        raise ValueError("A entrada ALE precisa de valores finitos e não vazios.")
    bordas = np.unique(np.quantile(valores, np.linspace(0, 1, bins + 1)))
    if len(bordas) == 1:
        tabela = pd.DataFrame(
            {
                "esquerda": bordas,
                "direita": bordas,
                "n": [len(base)],
                "delta": [0.0],
                "ale": [0.0],
            }
        )
        return tabela, np.zeros(len(base))
    grupos = np.searchsorted(bordas[1:-1], valores, side="left")
    linhas = []
    for k, (esquerda, direita) in enumerate(pairwise(bordas)):
        local = base.iloc[np.flatnonzero(grupos == k)]
        if local.empty:
            raise ValueError("Intervalo vazio: reduza bins ou reveja os quantis.")
        alto = prever(substituir(local, {coluna: direita}))
        baixo = prever(substituir(local, {coluna: esquerda}))
        delta = np.asarray(alto, float) - np.asarray(baixo, float)
        linhas.append((esquerda, direita, len(local), float(delta.mean())))
    tabela = pd.DataFrame(linhas, columns=["esquerda", "direita", "n", "delta"])
    acumulado = tabela["delta"].cumsum().to_numpy()
    tabela["ale"] = acumulado - acumulado[grupos].mean()
    return tabela, tabela["ale"].to_numpy()[grupos]


def h_par(prever, fundo, avaliacao, par, *, tolerancia=1e-14) -> dict:
    """H² de Friedman–Popescu nas combinações observadas, com PDs centralizadas.

    O fundo integra o complemento; `avaliacao` define os pontos e sua
    ponderação empírica. Não se troca essa ponderação por uma grade cartesiana.
    Denominador quase nulo retorna NaN, não evidência de ausência de interação.
    H não é truncado: valores acima da unidade devem permanecer auditáveis.
    """
    if len(par) != 2 or par[0] == par[1]:
        raise ValueError("Escolha um par de colunas diferentes.")
    pd_j = pd_empirica(prever, fundo, avaliacao[[par[0]]])
    pd_k = pd_empirica(prever, fundo, avaliacao[[par[1]]])
    pd_jk = pd_empirica(prever, fundo, avaliacao[list(par)])
    j, k, jk = [v - v.mean() for v in (pd_j, pd_k, pd_jk)]
    residuo = jk - j - k
    numerador = float(np.mean(residuo**2))
    denominador = float(np.mean(jk**2))
    h2 = numerador / denominador if denominador > tolerancia else float("nan")
    return {
        "h2": h2,
        "h": float(np.sqrt(h2)),
        "numerador": numerador,
        "denominador": denominador,
        "residuo": residuo,
        "pd_j": j,
        "pd_k": k,
        "pd_jk": jk,
    }


def decompor_superficie(superficie, pesos_j, pesos_k) -> dict:
    """Decomposição ANOVA de uma tabela sob a medida produto declarada.

    A tabela pode ser a PD de um par num modelo maior: nesse caso decompomos
    apenas essa superfície marginalizada, não todas as entradas do preditor.
    Ortogonalidade e parcelas de variância valem sob w_j ⊗ w_k, que não é a
    distribuição conjunta observada de pacientes com entradas dependentes.
    """
    s = np.asarray(superficie, dtype=float)
    wj, wk = np.asarray(pesos_j, float), np.asarray(pesos_k, float)
    if (
        s.ndim != 2
        or wj.ndim != 1
        or wk.ndim != 1
        or s.shape != (len(wj), len(wk))
        or not all(np.isfinite(v).all() for v in (s, wj, wk))
        or (wj < 0).any()
        or (wk < 0).any()
        or wj.sum() <= 0
        or wk.sum() <= 0
    ):
        raise ValueError("Superfície e pesos finitos, não negativos e compatíveis.")
    wj, wk = wj / wj.sum(), wk / wk.sum()
    produto = np.outer(wj, wk)
    f0 = float(wj @ s @ wk)
    fj, fk = s @ wk - f0, wj @ s - f0
    fjk = s - f0 - fj[:, None] - fk[None, :]
    variancias = np.array([wj @ fj**2, wk @ fk**2, np.sum(produto * fjk**2)])
    total = float(np.sum(produto * (s - f0) ** 2))
    return {
        "f0": f0,
        "fj": fj,
        "fk": fk,
        "fjk": fjk,
        "reconstrucao": f0 + fj[:, None] + fk[None, :] + fjk,
        "variancias": variancias,
        "total": total,
        "pesos_j": wj,
        "pesos_k": wk,
    }
