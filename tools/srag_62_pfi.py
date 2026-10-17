"""Permutation diagnostics of the fixed course model on a temporal holdout.

Each repeat uses a shared row permutation across the separately perturbed
columns. Repeats change only the permutation, never the model or patient set.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import srag_60_model as M
import srag_70_explain as E
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from xgboost import XGBClassifier

NAMES = {
    "idade_anos": "Idade (anos)",
    "regiao": "Região",
    "cs_sexo": "Sexo",
    "cs_raca": "Raça/cor",
    "cs_escol_n": "Escolaridade",
    "cs_zona": "Zona de residência",
    "cs_gestant": "Gestação",
    "puerpera": "Puerpério",
    "cardiopati": "Cardiopatia",
    "hematologi": "Doença hematológica",
    "sind_down": "Síndrome de Down",
    "hepatica": "Doença hepática",
    "asma": "Asma",
    "diabetes": "Diabetes",
    "neurologic": "Doença neurológica",
    "pneumopati": "Pneumopatia",
    "imunodepre": "Imunodepressão",
    "renal": "Doença renal",
    "obesidade": "Obesidade",
    "out_morbi": "Outras comorbidades",
    "febre": "Febre",
    "tosse": "Tosse",
    "garganta": "Dor de garganta",
    "dispneia": "Dispneia",
    "desc_resp": "Desconforto respiratório",
    "saturacao": "Saturação baixa",
    "diarreia": "Diarreia",
    "vomito": "Vômito",
    "dor_abd": "Dor abdominal",
    "fadiga": "Fadiga",
    "perd_olft": "Perda de olfato",
    "perd_pala": "Perda de paladar",
    "outro_sin": "Outros sintomas",
    "capital_interior": "Capital/interior",
    "nosocomial": "Infecção hospitalar (registro)",
    "meses_desde_mar2020": "Tempo desde março de 2020",
    "semana_epi": "Semana epidemiológica",
    "n_doses_antes_do_sintoma": "Doses antes dos sintomas",
    "vacina_covid_declarada": "Vacinação declarada",
    "coinfeccao_outro_virus": "Coinfecção por outro vírus",
}


def scores(y, p):
    p = np.asarray(p, dtype=np.float64)
    return {
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p)),
        "auc": float(roc_auc_score(y, p)),
    }


def study(output: Path, repeats=50, seed=42, split="test"):
    if (
        isinstance(repeats, bool)
        or not isinstance(repeats, (int, np.integer))
        or repeats < 2
    ):
        raise ValueError("O estudo precisa de ao menos duas repetições inteiras.")
    if split not in {"val", "test"}:
        raise ValueError("A avaliação temporal deve usar val ou test.")
    repeats = int(repeats)
    output.mkdir(parents=True, exist_ok=True)
    gold = M.load_gold()
    x, _, y = M.design_matrix(gold)
    tr = (gold["split"] == "train").to_numpy()
    ev = (gold["split"] == split).to_numpy()
    xe = x.loc[ev].reset_index(drop=True)
    ye = y[ev]
    params = dict(M.XGB_PARAMS)
    protocol = {
        "model": "course XGBoost; no class weights; fixed after fitting",
        "xgb_params": params,
        "split": split,
        "period": 2024 if split == "test" else 2023,
        "status": "exploratory; previously observed temporal holdout",
        "n_train": int(tr.sum()),
        "n_evaluation": len(ye),
        "events": int(ye.sum()),
        "features": list(M.FEATURES),
        "repeats": repeats,
        "permutation_seed": seed,
        "sampling": "all evaluation rows; no subsampling",
        "permutation": "one column at a time; common row order per repeat",
        "sd": "sample standard deviation across permutations; ddof=1",
        "uncertainty": "conditional on fitted model and observed patient set",
        "top10_criterion": "descending mean Brier increase across all features",
        "rank_ties": "average rank among all features in each repeat",
        "boxplot": "median, Q1-Q3, 1.5 IQR whiskers; all repeats shown",
        "before_sd": "zero across these repeats by construction; no resampling",
        "sample_sha256": hashlib.sha256(M.AMOSTRA.read_bytes()).hexdigest(),
        "versions": {
            p: importlib.metadata.version(p)
            for p in ["numpy", "pandas", "scikit-learn", "xgboost"]
        },
    }
    print("Fitting the course reference", flush=True)
    model = XGBClassifier(**params).fit(x.loc[tr], y[tr])
    original_predictions = model.predict_proba(xe)[:, 1]
    original = scores(ye, original_predictions)
    expected = json.loads(M.METRICS_JSON.read_text())["xgb"]
    for entry in expected:
        if entry["split"] == split:
            for name in ["brier", "auc"]:
                assert abs(original[name] - entry[name]) < 5e-5
    rng = np.random.default_rng(seed)
    permutations = [rng.permutation(len(xe)) for _ in range(repeats)]
    order_hash = hashlib.sha256(np.asarray(permutations).tobytes()).hexdigest()
    protocol["permutation_orders_sha256"] = order_hash
    (output / "protocolo.json").write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False) + "\n"
    )
    rows = []
    for j, feature in enumerate(xe.columns):
        after = {name: [] for name in original}
        unchanged = True
        for permutation in permutations:
            perturbed = E.permutar_colunas(xe, feature, permutation)
            predicted = model.predict_proba(perturbed)[:, 1]
            unchanged &= np.array_equal(predicted, original_predictions)
            for name, value in scores(ye, predicted).items():
                after[name].append(value)
        metric_summary = {}
        for name, values in after.items():
            values = np.asarray(values)
            direction = -1 if name == "auc" else 1
            delta = direction * (values - original[name])
            metric_summary[name] = {
                "after": values.tolist(),
                "delta": delta.tolist(),
                "after_mean": float(values.mean()),
                "after_sd": float(values.std(ddof=1)),
                "mean": float(delta.mean()),
                "sd": float(delta.std(ddof=1)),
                "mcse": float(delta.std(ddof=1) / np.sqrt(repeats)),
                "median": float(np.median(delta)),
                "q25": float(np.quantile(delta, 0.25)),
                "q75": float(np.quantile(delta, 0.75)),
                "q05": float(np.quantile(delta, 0.05)),
                "q95": float(np.quantile(delta, 0.95)),
            }
            assert np.isclose(
                metric_summary[name]["after_sd"], metric_summary[name]["sd"]
            )
        rows.append(
            {
                "feature": feature,
                "label": NAMES.get(feature, feature),
                "family": M.GRUPO_DE_FEATURE[feature],
                "identical_predictions": bool(unchanged),
                "metrics": metric_summary,
            }
        )
        print(f"Completed {j + 1}/{len(xe.columns)}: {feature}", flush=True)
    for name in original:
        matrix = np.array([r["metrics"][name]["delta"] for r in rows])
        ranks = pd.DataFrame(matrix).rank(ascending=False, method="average").to_numpy()
        order = np.argsort(-matrix.mean(axis=1), kind="stable")
        for position, index in enumerate(order):
            values = ranks[index]
            rows[index]["metrics"][name]["rank"] = position + 1
            rows[index]["metrics"][name]["rank_repeats"] = values.tolist()
            rows[index]["metrics"][name]["rank_mean"] = float(values.mean())
            rows[index]["metrics"][name]["rank_sd"] = float(values.std(ddof=1))
            rows[index]["metrics"][name]["top10_fraction"] = float(
                np.mean(values <= 10)
            )
    result = {"protocol": protocol, "original": original, "rows": rows}
    (output / "resultados.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    print("Study complete", flush=True)
    return result


def figures(result, destination: Path):
    import matplotlib.pyplot as plt
    import sapians as SP
    from matplotlib.lines import Line2D

    destination.mkdir(parents=True, exist_ok=True)
    baseline = result["original"]["brier"]
    rows = sorted(result["rows"], key=lambda r: r["metrics"]["brier"]["rank"])[:10]
    positions = np.arange(len(rows))
    labels = [r["label"] for r in rows]
    means = np.array([r["metrics"]["brier"]["mean"] for r in rows])
    deviations = np.array([r["metrics"]["brier"]["sd"] for r in rows])
    values = [r["metrics"]["brier"]["delta"] for r in rows]
    repeat_count = result["protocol"]["repeats"]
    rng = np.random.default_rng(42)

    def boxes(ax, selected, yy, select_means, select_sd):
        ax.boxplot(
            selected,
            positions=yy,
            orientation="horizontal",
            widths=0.42,
            patch_artist=True,
            showfliers=False,
            manage_ticks=False,
            boxprops={"facecolor": SP.CINZA_CLARO, "alpha": 0.4},
            medianprops={"color": SP.ESCURO, "linewidth": 1},
            whiskerprops={"color": SP.CINZA, "linewidth": 0.8},
            capprops={"color": SP.CINZA, "linewidth": 0.8},
        )
        for vv, pos in zip(selected, yy):
            ax.scatter(
                vv,
                pos + rng.uniform(-0.13, 0.13, len(vv)),
                color=SP.CINZA,
                s=7,
                alpha=0.3,
                zorder=3,
            )
        ax.errorbar(
            select_means,
            yy,
            xerr=select_sd,
            fmt="o",
            color=SP.AZUL,
            markersize=4,
            capsize=3,
            linewidth=1.2,
            zorder=4,
        )
        ax.axvline(0, **SP.L_REF)

    def save(fig, name):
        previous = SP.FIGDIR
        SP.FIGDIR = destination
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                SP.salvar(
                    fig,
                    name,
                    rect=(
                        0.01,
                        0.18 if name == "antes-depois-top10" else 0.03,
                        0.99,
                        0.84,
                    ),
                )
            # Export the same laid-out figure as scalable vector artwork.
            fig.savefig(destination / f"{name}.svg", facecolor=SP.PAPEL)
        finally:
            SP.FIGDIR = previous

    fig, axes = plt.subplots(1, 2, figsize=SP.PAINEL, sharey=True)
    left, right = axes
    for pos, mean in zip(positions, means):
        left.plot([baseline, baseline + mean], [pos, pos], color=SP.CINZA_CLARO)
    left.scatter(
        np.full(len(rows), baseline), positions, color=SP.CINZA, marker="s", s=20
    )
    left.errorbar(
        baseline + means,
        positions,
        xerr=deviations,
        fmt="o",
        color=SP.AZUL,
        capsize=3,
        markersize=4,
    )
    left.axvline(baseline, **SP.L_REF)
    left.set_yticks(positions, labels)
    left.invert_yaxis()
    left.set_title("Antes e depois da permutação")
    left.set_xlabel("Brier do conjunto · menor é melhor\nEixo ampliado")
    left.set_xlim(baseline - 0.002, baseline + max(means + 2 * deviations) * 1.08)
    boxes(right, values, positions, means, deviations)
    right.set_title("PFI: distribuição do aumento do erro")
    right.set_xlabel("Brier após − Brier original\nMaior: maior dependência do modelo")
    legend = [
        Line2D(
            [],
            [],
            marker="s",
            linestyle="none",
            color=SP.CINZA,
            label="Erro original fixo",
        ),
        Line2D([], [], marker="o", color=SP.AZUL, label="Média ± 1 desvio padrão"),
        Line2D(
            [], [], color=SP.CINZA, label="Caixa: mediana e quartis; bigodes: 1,5 IQR"
        ),
    ]
    fig.legend(handles=legend, loc="lower left", bbox_to_anchor=(0.16, 0.01), ncol=1)
    SP.titulo(
        fig,
        "Permutar uma entrada mostra quanto o erro aumenta",
        "§3 · PFI · TESTE HISTÓRICO 2024 · EXPLORATÓRIO",
    )
    fig.text(
        0.19,
        0.875,
        f"{SP.pt_int(repeat_count)} sorteios por coluna · mesmos registros e modelo · pontos cinza: sorteios individuais",
    )
    fig.subplots_adjust(left=0.19, right=0.985, top=0.82, bottom=0.23, wspace=0.12)
    save(fig, "antes-depois-top10")

    fig2, ax = plt.subplots(figsize=SP.PAINEL)
    boxes(ax, values[1:], positions[1:], means[1:], deviations[1:])
    ax.set_yticks(positions[1:], labels[1:])
    ax.invert_yaxis()
    ax.set_xlabel("PFI em aumento do Brier · mesma escala para todas as linhas")
    SP.titulo(
        fig2,
        "Ampliação das posições abaixo da primeira",
        "§3 · PFI · POSIÇÕES 2–10 · SEM A VARIÁVEL DE MAIOR PFI",
    )
    fig2.text(
        0.19,
        0.875,
        "A primeira posição foi omitida apenas nesta ampliação. Ponto azul e haste: média ± 1 DP.",
    )
    fig2.subplots_adjust(left=0.25, right=0.975, top=0.82, bottom=0.12)
    save(fig2, "pfi-detalhe")

    fig3, ax = plt.subplots(figsize=SP.PAINEL)
    for pos, row in zip(positions, rows):
        ranks = np.array(row["metrics"]["brier"]["rank_repeats"])
        ax.scatter(
            ranks,
            pos + rng.uniform(-0.18, 0.18, len(ranks)),
            color=SP.AZUL,
            s=12,
            alpha=0.3,
        )
        ax.scatter(np.median(ranks), pos, color=SP.ESCURO, marker="D", s=28)
    ax.set_yticks(positions, labels)
    ax.invert_yaxis()
    ax.set_xlabel(
        "Posição entre todas as entradas em cada sorteio · menor é mais importante"
    )
    low = min(min(row["metrics"]["brier"]["rank_repeats"]) for row in rows)
    high = max(max(row["metrics"]["brier"]["rank_repeats"]) for row in rows)
    ax.set_xlim(low - 0.6, high + 0.6)
    ax.set_xticks(range(int(low), int(np.ceil(high)) + 1))
    SP.titulo(
        fig3,
        "O ranking também varia entre permutações",
        "§4 · PFI · MODELO E PACIENTES FIXOS",
    )
    fig3.text(
        0.25,
        0.875,
        "Cada ponto é um sorteio; losango: posição mediana. As linhas seguem o ranking da PFI média.",
    )
    fig3.subplots_adjust(left=0.25, right=0.975, top=0.82, bottom=0.12)
    save(fig3, "ranking-sorteios")
    return [fig, fig2, fig3]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    study(args.output)
