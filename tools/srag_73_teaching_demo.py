"""Gerar a janela de fichas reais de uma repetição da PFI do teste completo.

As mesmas fichas históricas são somente receptores visíveis. Seus doadores
vêm da primeira ordem do experimento global registrado, sorteada sobre todo
o teste. Não há seleção de ordem pelo resultado. Índices, posições e
identificadores dos doadores nunca são exportados. O modelo já ajustado é
recebido; este gerador não seleciona fichas, treina, escreve ou publica.
"""

from __future__ import annotations

import copy
import hashlib

import numpy as np
import pandas as pd
import srag_70_explain as E


def _probability(fitted_model, inputs: pd.DataFrame) -> np.ndarray:
    """Probabilidade da classe óbito, preservando a precisão do preditor."""
    if not np.array_equal(fitted_model.classes_, [0, 1]):
        raise ValueError("O preditor deve ter classes 0 e 1, nesta ordem.")
    prediction = np.asarray(fitted_model.predict_proba(inputs), dtype=np.float64)
    if prediction.shape != (len(inputs), 2):
        raise ValueError("O preditor deve retornar duas probabilidades por ficha.")
    probability = prediction[:, 1]
    if not np.all(np.isfinite(probability) & (probability >= 0) & (probability <= 1)):
        raise ValueError("Probabilidades inválidas na demonstração.")
    return probability


def build_teaching_demo(
    fitted_model,
    full_inputs: pd.DataFrame,
    full_target: np.ndarray,
    receiver_positions: np.ndarray,
    historical_preview: dict,
    full_rows: list[dict],
    experiment: dict,
) -> dict:
    """Janela das mesmas fichas na primeira permutação GLOBAL registrada.

    As ordens são reproduzidas com o protocolo e conferidas pelo hash do
    estudo antes das novas previsões. Cada entrada é permutada a partir da
    matriz completa original; as trocas nunca se acumulam. Preservamos
    float32, categorias nativas, demais entradas e alvos. As posições dos
    receptores/doadores são usadas somente aqui e não aparecem na saída.
    """
    protocol = experiment["protocol"]
    full_target = np.asarray(full_target)
    receiver_positions = np.asarray(receiver_positions)
    historical_rows = historical_preview["rows"]
    if len(full_inputs) != protocol["n_evaluation"]:
        raise ValueError("A matriz precisa incluir todo o teste registrado.")
    if full_target.shape != (len(full_inputs),) or not np.all(
        np.isin(full_target, [0, 1])
    ):
        raise ValueError("Um desfecho binário original é necessário por ficha.")
    if (
        receiver_positions.shape != (len(historical_rows),)
        or len(receiver_positions) != 8
        or receiver_positions.dtype.kind not in "iu"
        or len(np.unique(receiver_positions)) != len(receiver_positions)
        or np.any((receiver_positions < 0) | (receiver_positions >= len(full_inputs)))
    ):
        raise ValueError("Indique as posições das oito mesmas fichas receptoras.")
    if full_inputs["idade_anos"].dtype != np.dtype("float32"):
        raise ValueError("Idade deve preservar o float32 da matriz original.")
    if not isinstance(full_inputs["saturacao"].dtype, pd.CategoricalDtype):
        raise TypeError("Saturação deve preservar categorias nativas.")
    case_inputs = full_inputs.iloc[receiver_positions]
    case_target = full_target[receiver_positions]
    for feature in ("idade_anos", "saturacao"):
        if not np.array_equal(
            case_inputs[feature].to_numpy(), [row[feature] for row in historical_rows]
        ):
            raise ValueError("As entradas visíveis devem ser as fichas históricas.")
    if not np.array_equal(case_target, [row["y_obito"] for row in historical_rows]):
        raise ValueError("Não altere os desfechos das fichas históricas.")
    threshold = float(historical_preview["threshold"])
    if not 0 < threshold < 1:
        raise ValueError("O limiar deve estar entre zero e um.")
    original_inputs = full_inputs.copy(deep=True)
    original_target = full_target.copy()
    # Sorteio sobre TODO o teste, sem consultar desfechos ou perdas.
    rng = np.random.default_rng(protocol["permutation_seed"])
    orders = [rng.permutation(len(full_inputs)) for _ in range(protocol["repeats"])]
    orders_hash = hashlib.sha256(np.asarray(orders).tobytes()).hexdigest()
    if orders_hash != protocol["permutation_orders_sha256"]:
        raise ValueError("As ordens precisam reproduzir o experimento registrado.")
    order = orders[0]
    original_probability = _probability(fitted_model, full_inputs)
    case_original_probability = original_probability[receiver_positions]
    if not np.array_equal(
        case_original_probability, [row["p_original"] for row in historical_rows]
    ):
        raise ValueError(
            "O preditor deve reproduzir as previsões originais históricas."
        )
    original_loss = float(np.mean((original_probability - full_target) ** 2))
    np.testing.assert_allclose(
        original_loss, experiment["original"]["brier"], rtol=0, atol=1e-15
    )
    rows = [
        {
            key: row[key]
            for key in (
                "record",
                "idade_anos",
                "saturacao",
                "y_obito",
                "p_original",
                "class_original",
                "correct_original",
                "brier_original",
            )
        }
        for row in historical_rows
    ]
    rounds = []
    for feature, cell, label in (
        ("idade_anos", "age", "Age"),
        ("saturacao", "oxygen", "Low oxygen"),
    ):
        changed = E.permutar_colunas(full_inputs, feature, order)
        pd.testing.assert_frame_equal(
            changed.drop(columns=feature), full_inputs.drop(columns=feature)
        )
        assert changed.dtypes.equals(full_inputs.dtypes)
        full_probability = _probability(fitted_model, changed)
        full_loss = (full_probability - full_target) ** 2
        full_single_brier = float(full_loss.mean())
        registered = next(
            row for row in experiment["rows"] if row["feature"] == feature
        )
        np.testing.assert_allclose(
            full_single_brier,
            registered["metrics"]["brier"]["after"][0],
            rtol=0,
            atol=1e-15,
        )
        probability = full_probability[receiver_positions]
        predicted = (probability >= threshold).astype(int)
        correct = predicted == case_target
        loss = (probability - case_target) ** 2
        for i, row in enumerate(rows):
            row["p_after_" + cell] = float(probability[i])
            row["class_after_" + cell] = int(predicted[i])
            row["correct_after_" + cell] = bool(correct[i])
            row["brier_after_" + cell] = float(loss[i])
        full_test = next(row for row in full_rows if row["feature"] == feature)
        rounds.append(
            {
                "feature": feature,
                "label": label,
                "cell": cell,
                "values": case_inputs[feature].tolist(),
                "shuffled_values": changed.iloc[receiver_positions][feature].tolist(),
                "probability": probability.tolist(),
                "predicted": predicted.tolist(),
                "correct": correct.tolist(),
                "individual_brier": loss.tolist(),
                "sample_brier_mean": float(loss.mean()),
                "full_test_single_brier": full_single_brier,
                "full_test": copy.deepcopy(full_test),
            }
        )
    pd.testing.assert_frame_equal(full_inputs, original_inputs)
    np.testing.assert_array_equal(full_target, original_target)
    return {
        "preview": {
            "rows": rows,
            "rounds": rounds,
            "permutation_seed": int(protocol["permutation_seed"]),
            "displayed_repeat": 1,
            "evaluation_n": len(full_inputs),
            "permutation_scope": "full temporal test",
            "permutation_orders_sha256": orders_hash,
            "threshold": threshold,
            "age_unit": historical_preview["age_unit"],
            "selection": {
                "records_per_outcome": historical_preview["selection"][
                    "records_per_outcome"
                ],
                "rule": (
                    "Same first four adult temporal-test receiver records per outcome, then "
                    "original dataset order. The displayed receivers are selected by outcome; "
                    "neither predictions nor shuffle losses select them. Donor values come "
                    "from the full-test permutation, not a shuffle restricted to these rows."
                ),
            },
            "scope": (
                "Eight unchanged real SRAG receivers are a window into repeat 1 of the "
                "registered full temporal-test permutation. Donor values are drawn from "
                "all evaluation rows; no donor identifier, position, or outcome is exported. "
                "Age and low oxygen are permuted separately, restoring original inputs "
                "before each. Global errors and PFI use all test rows; these selected "
                "receivers do not estimate population performance."
            ),
        }
    }
